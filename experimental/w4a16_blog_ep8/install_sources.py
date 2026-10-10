#!/usr/bin/env python3
"""Install pinned source wheels without resolving or replacing image dependencies.

Run once inside the new, idle benchmark devbox. All output is task-owned and
small receipts are separate from build logs and wheels on persistent storage.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata as md
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import zipfile

from flashinfer_orphans import quarantine_orphaned_flashinfer

FI_SHA = "866c80d0c70a90624b4c2056d12d1543d709609e"
SG_INTEGRATION_BASE = "38114937747fff49d749c3ee6a7e2f240e34530a"
FI_FILES = [
    "flashinfer/moe_ep/cute_dsl/megamoe/bf16_nvfp4/autotune.py",
    "flashinfer/moe_ep/cute_dsl/megamoe/bf16_nvfp4/frontend.py",
    "flashinfer/moe_ep/cute_dsl/megamoe/bf16_nvfp4/megamoe_kernel.py",
    "flashinfer/moe_ep/backends/mega/kernel/sm100/bf16_nvfp4_bf16_cutedsl/config.py",
    "flashinfer/jit/env.py",
]
SG_FILES = [
    "python/sglang/srt/server_args.py",
    "python/sglang/srt/arg_groups/speculative_hook.py",
    "python/sglang/srt/layers/quantization/modelopt_quant.py",
    "python/sglang/srt/speculative/dspark_components/dspark_worker_v2.py",
]


def digest(path: Path) -> dict:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(4 << 20), b""):
            h.update(data)
    return {"bytes": path.stat().st_size, "sha256": h.hexdigest()}


def write(path: Path, value: object) -> None:
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def fi_distribution(name: str) -> bool:
    return normalize(name).startswith("flashinfer-")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Persistent task root containing sources/flashinfer and sources/sglang",
    )
    parser.add_argument(
        "--cuda-version", required=True, help="Expected NVCC major.minor, e.g. 13.0"
    )
    parser.add_argument(
        "--sg-sha",
        required=True,
        help="Exact committed SGLang integration or authorized child PR head",
    )
    parser.add_argument("--sg-rust-exts", default="all")
    parser.add_argument("--max-jobs", type=int, default=16)
    args = parser.parse_args()
    root = args.root.resolve()
    fi, sg = root / "sources/flashinfer", root / "sources/sglang"
    if not re.fullmatch(r"13\.\d+", args.cuda_version):
        raise SystemExit("Expected a CUDA 13 major.minor")
    if not re.fullmatch(r"[0-9a-f]{40}", args.sg_sha):
        raise SystemExit("sg-sha must be an exact 40-character Git commit")
    if args.max_jobs < 1:
        raise SystemExit("max-jobs must be positive")
    if not fi.is_dir() or not sg.is_dir():
        raise SystemExit("Both source checkouts must already exist")
    output = root / "source-install"
    output.mkdir(exist_ok=False)
    wheels, logs, cache = output / "wheels", output / "logs", root / "cache"
    wheels.mkdir()
    logs.mkdir()
    cache.mkdir(exist_ok=False)
    runtime = {
        "SGLANG_CACHE_DIR": str(cache / "sglang"),
        "FLASHINFER_WORKSPACE_BASE": str(cache / "flashinfer"),
        "CUTE_DSL_CACHE_DIR": str(cache / "cute-dsl"),
        "TRITON_CACHE_DIR": str(cache / "triton"),
        "TORCHINDUCTOR_CACHE_DIR": str(cache / "inductor"),
        "TILELANG_CACHE_DIR": str(cache / "tilelang"),
        "CUDA_CACHE_PATH": str(cache / "cuda-driver"),
    }
    env = dict(os.environ)
    for name in list(env):
        if name.startswith(("FLASHINFER_", "CUTE_DSL_")) or name == "PYTHONPATH":
            env.pop(name)
    env.update(runtime)
    env.update(
        PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1", PYTHONNOUSERSITE="1"
    )
    for value in runtime.values():
        Path(value).mkdir(parents=True, exist_ok=False)
    sequence: list[dict] = []

    def run(
        label: str,
        command: list[str],
        *,
        extra: dict | None = None,
        capture: bool = False,
        allow_failure: bool = False,
        timeout: int = 7200,
    ) -> str:
        log = logs / (label + ".log")
        command_env = dict(env, **(extra or {}))
        started = time.time()
        with log.open("xb") as stream:
            result = subprocess.run(
                command,
                cwd=output,
                env=command_env,
                stdout=stream,
                stderr=subprocess.STDOUT,
                timeout=timeout,
                check=False,
            )
        sequence.append(
            {
                "label": label,
                "command": command,
                "returncode": result.returncode,
                "seconds": time.time() - started,
                "log": str(log),
            }
        )
        print(json.dumps(sequence[-1]), flush=True)
        if result.returncode and not allow_failure:
            raise RuntimeError(f"{label} exited {result.returncode}; see {log}")
        return log.read_text() if capture else ""

    def repository(path: Path, expected: str, label: str) -> dict:
        observed = run(
            label + "-head", ["git", "-C", str(path), "rev-parse", "HEAD"], capture=True
        ).strip()
        if observed != expected:
            raise RuntimeError(f"{label}: expected {expected}, observed {observed}")
        run(label + "-clean", ["git", "-C", str(path), "diff", "HEAD", "--exit-code"])
        return {"path": str(path), "sha": observed}

    try:
        write(
            output / "STARTED.json",
            {
                "pid": os.getpid(),
                "started": time.time(),
                "python": sys.executable,
                "cuda_version": args.cuda_version,
                "runtime_environment": runtime,
                "sg_rust_exts": args.sg_rust_exts,
            },
        )
        identities = {
            "flashinfer": repository(fi, FI_SHA, "flashinfer"),
            "sglang": repository(sg, args.sg_sha, "sglang"),
        }
        run(
            "sglang-integration-ancestry",
            [
                "git",
                "-C",
                str(sg),
                "merge-base",
                "--is-ancestor",
                SG_INTEGRATION_BASE,
                args.sg_sha,
            ],
        )
        nvcc = run("nvcc", ["nvcc", "--version"], capture=True)
        if f"release {args.cuda_version}," not in nvcc:
            raise RuntimeError("NVCC version does not match selected image CUDA")
        active = run(
            "gpu-idle",
            ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
            capture=True,
        )
        if active.strip():
            raise RuntimeError("GPU compute processes are present")
        before_code = """import json,torch,platform,importlib.metadata as m
p={'torch':str(torch.__version__),'torch_cuda':torch.version.cuda,'torch_file':torch.__file__,'machine':platform.machine(),
'gpus':[{'name':torch.cuda.get_device_name(i),'capability':list(torch.cuda.get_device_capability(i))} for i in range(torch.cuda.device_count())],
'distributions':{d.metadata['Name']:d.version for d in m.distributions() if d.metadata['Name']}}
assert len(p['gpus'])==8 and all(x['capability']==[10,3] for x in p['gpus']),p['gpus']
print(json.dumps(p))"""
        before = json.loads(
            run("environment-before", [sys.executable, "-c", before_code], capture=True)
            .strip()
            .splitlines()[-1]
        )
        # Torch's linked CUDA runtime and NVCC's toolkit minor may differ in a
        # valid image. Record both; do not force a resolver-driven Torch swap.
        if not before["torch_cuda"]:
            raise RuntimeError("Selected image Torch is not CUDA enabled")
        write(output / "environment-before.json", before)
        run(
            "flashinfer-submodules",
            [
                "git",
                "-C",
                str(fi),
                "submodule",
                "update",
                "--init",
                "--recursive",
                "3rdparty/cutlass",
                "3rdparty/spdlog",
                "3rdparty/cccl",
            ],
        )
        submodules = run(
            "flashinfer-submodule-pins",
            ["git", "-C", str(fi), "submodule", "status", "--recursive"],
            capture=True,
        )
        selected_submodules = [
            line
            for line in submodules.splitlines()
            if any(f" 3rdparty/{x}" in line for x in ("cutlass", "spdlog", "cccl"))
        ]
        if len(selected_submodules) < 3 or any(
            not line.startswith(" ") for line in selected_submodules
        ):
            raise RuntimeError("Required FlashInfer submodule pins are not checked out")
        local_version = "cu" + args.cuda_version.replace(".", "") + ".g" + FI_SHA[:12]
        build = {
            "FLASHINFER_BUILD_NO_PIP": "1",
            "BUILD_NIXL_EP": "0",
            "BUILD_NCCL_EP": "0",
            "CUDA_MAJOR": "13",
            "FLASHINFER_CUDA_ARCH_LIST": "10.3a",
            "FLASHINFER_LOCAL_VERSION": local_version,
            "FLASHINFER_DEV_RELEASE_SUFFIX": "",
            "MAX_JOBS": str(args.max_jobs),
            "FLASHINFER_NVCC_THREADS": "1",
        }
        wheel_command = [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "--no-cache-dir",
            "--wheel-dir",
            str(wheels),
        ]
        if args.sg_rust_exts != "none":
            run(
                "rust-build-python-dependencies",
                [
                    sys.executable,
                    "-c",
                    "import setuptools_rust,setuptools_scm; print('Rust Python build dependencies present')",
                ],
            )
            run("cargo-version", ["cargo", "--version"])
            run("rustc-version", ["rustc", "--version"])
        # Build SG before package mutation so a missing Rust toolchain/dependency
        # is a clear setup error rather than a partly replaced serving install.
        run(
            "build-sglang",
            wheel_command + [str(sg / "python")],
            extra={
                "SGLANG_BUILD_RUST_EXTS": args.sg_rust_exts,
                "MAX_JOBS": str(args.max_jobs),
            },
        )
        run("build-flashinfer-python", wheel_command + [str(fi)], extra=build)
        existing = sorted(
            {
                d.metadata["Name"]
                for d in md.distributions()
                if d.metadata["Name"] and fi_distribution(d.metadata["Name"])
            }
        )
        if existing:
            run(
                "remove-image-flashinfer",
                [sys.executable, "-m", "pip", "uninstall", "-y", *existing],
            )
        # pip leaves generated files behind; namespace remnants are still
        # discoverable as packages and can shadow the new source installation.
        quarantined = quarantine_orphaned_flashinfer(output / "orphaned-flashinfer")
        write(output / "orphaned-flashinfer.json", quarantined)
        # artifacts.py binds this path on import, before the cubin backend's
        # internal temporary environment assignment. Set it before startup.
        build_cubins = fi / "flashinfer-cubin/flashinfer_cubin/cubins"
        if build_cubins.exists() and any(build_cubins.iterdir()):
            raise RuntimeError("Source cubin directory must start empty")
        run(
            "build-flashinfer-cubin",
            wheel_command + [str(fi / "flashinfer-cubin")],
            extra=dict(build, FLASHINFER_CUBIN_DIR=str(build_cubins)),
        )
        selected = []
        for prefix in ("flashinfer_python-", "flashinfer_cubin-", "sglang-"):
            matches = list(wheels.glob(prefix + "*.whl"))
            if len(matches) != 1:
                raise RuntimeError(
                    f"Expected exactly one {prefix} wheel, found {matches}"
                )
            selected.append(matches[0])
        with zipfile.ZipFile(selected[1]) as wheel:
            cubin_count = sum(n.endswith(".cubin") for n in wheel.namelist())
            if not cubin_count:
                raise RuntimeError("Locally built cubin wheel contains no cubins")
        wheel_receipts = [{"name": w.name, **digest(w)} for w in selected]
        write(
            output / "wheels.json",
            {
                "files": wheel_receipts,
                "cubin_files": cubin_count,
                "flashinfer_build_environment": build,
                "removed_distributions": existing,
            },
        )
        run(
            "install-local-wheels",
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                "--force-reinstall",
                *map(str, selected),
            ],
        )
        run("pip-check", [sys.executable, "-m", "pip", "check"], allow_failure=True)
        expected_files = {
            "flashinfer": {name: digest(fi / name) for name in FI_FILES},
            "sglang": {name: digest(sg / name) for name in SG_FILES},
        }
        verify_config = {
            "flashinfer_sha": FI_SHA,
            "sglang_sha": args.sg_sha,
            "sglang_integration_base": SG_INTEGRATION_BASE,
            "flashinfer_version": (fi / "version.txt").read_text().strip()
            + "+"
            + local_version,
            "before": {k: before[k] for k in ("torch", "torch_cuda", "torch_file")},
            "files": expected_files,
            "runtime_environment": runtime,
            "repositories": identities,
        }
        write(output / "verification-input.json", verify_config)
        verifier = Path(__file__).with_name("verify_source_install.py")
        run(
            "verify-installed-sources",
            [
                sys.executable,
                "-B",
                str(verifier),
                str(output / "verification-input.json"),
                str(output / "VERIFIED.json"),
            ],
            timeout=600,
        )
        run(
            "flashinfer-final-clean",
            ["git", "-C", str(fi), "diff", "HEAD", "--exit-code"],
        )
        run("sglang-final-clean", ["git", "-C", str(sg), "diff", "HEAD", "--exit-code"])
        write(output / "runtime-environment.json", runtime)
        write(
            output / "COMPLETE.json",
            {
                "status": "SOURCE_INSTALL_VERIFIED",
                "finished": time.time(),
                "repositories": identities,
                "verification": digest(output / "VERIFIED.json"),
                "wheels": wheel_receipts,
                "commands": sequence,
            },
        )
        print("SOURCE_INSTALL_VERIFIED", flush=True)
    except BaseException as exc:
        write(
            output / "FAILED.json",
            {
                "type": type(exc).__name__,
                "error": str(exc),
                "finished": time.time(),
                "commands": sequence,
            },
        )
        raise


if __name__ == "__main__":
    main()
