#!/usr/bin/env python3
"""Prepare the exact retained stack on the replacement node; never launch a run.

Default ``plan`` is local-only. ``inventory`` performs bounded read-only node
checks. ``apply`` explicitly mutates packages in an exclusive bootstrap root.
The selected node/image is attested by the caller receipt, not inferred here.
"""

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/data/home/ziangli/inferencex-glm52-megamoe-bootstrap-20260921-recovery1")
OLD = Path("/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921")
CAMPAIGN = Path(str(OLD) + "-recovery1")
MODEL = Path("/data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4")
REVISION = "53e0691e21895a3863a606dfd12910c69eba94ab"
FI = "ad0a5e5e78e57070ec7c582efe733cb55cd8839f"
IMAGE = "lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85@sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596"
IDENTITY = {
    "node": "infx-glm52-auto-0921",
    "cluster": "c2",
    "namespace": "ziangli",
    "queue": "earth-non-preempt",
    "image": IMAGE,
}
LOCK = Path(__file__).with_name("megamoe_bootstrap_recovery1_wheels.json")
LOCK_SHA = "321f151aefd7fe9e6a82b7482f112264a3a3dcc6178d27a9869abc728b3b69ac"
REFERENCE_SHAS = {
    "runtime": "acfec88f87392a2bac6dd4286a9df580f931241567f9587cd07fcb79b1fc299a",
    "freeze": "ee786fdd588c17fbcbb5081eb8041172b3f9fa9cb04b6a241ea890f6ce061040",
}
CUTE = tuple(
    "nvidia-cutlass-dsl" + suffix
    for suffix in ("", "-libs-base", "-libs-core", "-libs-cu12", "-libs-cu13")
)
TARGET = dict.fromkeys(CUTE, "4.7.1") | {
    "flashinfer-python": "0.7.0",
    "flashinfer-cubin": None,
    "flashinfer-jit-cache": None,
    "nccl-extensions": "0.1.0",
    "cupti-python": "13.2.0",
    "nvidia-cuda-cupti": "13.2.86",
}
FRESH = dict.fromkeys(CUTE, "4.6.2") | {
    "flashinfer-python": "0.6.18",
    "flashinfer-cubin": "0.6.18",
    "flashinfer-jit-cache": "0.6.18+cu130",
    "nccl-extensions": None,
    "cupti-python": None,
    "nvidia-cuda-cupti": "13.0.85",
}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def read_json(path, limit=16 * 1024 * 1024):
    require(path.is_file() and not path.is_symlink(), f"Not a regular file: {path}")
    require(path.stat().st_size <= limit, f"Unexpectedly large JSON: {path}")
    return json.loads(path.read_text())


def safe_ancestors(path):
    require(path.is_absolute(), "An absolute path is required")
    require(
        not any(p.is_symlink() for p in (path, *path.parents)), f"Symlink path: {path}"
    )


def command(argv, env=None):
    return subprocess.check_output(argv, text=True, env=env).strip()


def idle():
    require(
        not command(
            ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"]
        ),
        "GPU compute processes are active",
    )


def clean_env():
    env = dict(os.environ)
    for key in list(env):
        if key.startswith(("SGLANG_", "FLASHINFER_", "MEGA_", "CAMPAIGN_")) or key in (
            "PYTHONPATH",
            "CUDA_VISIBLE_DEVICES",
            "CUTE_DSL_CACHE_DIR",
            "CUDA_CACHE_PATH",
            "TORCH_EXTENSIONS_DIR",
            "TORCHINDUCTOR_CACHE_DIR",
            "TRITON_CACHE_DIR",
            "XDG_CACHE_HOME",
        ):
            del env[key]
    env.update(
        {
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "FLASHINFER_WORKSPACE_BASE": str(ROOT / "caches/flashinfer"),
            "SGLANG_CACHE_DIR": str(ROOT / "caches/sglang"),
            "CUTE_DSL_CACHE_DIR": str(ROOT / "caches/cute"),
            "CUDA_CACHE_PATH": str(ROOT / "caches/cuda"),
            "TORCH_EXTENSIONS_DIR": str(ROOT / "caches/torch-extensions"),
            "TORCHINDUCTOR_CACHE_DIR": str(ROOT / "caches/torchinductor"),
            "TRITON_CACHE_DIR": str(ROOT / "caches/triton"),
            "XDG_CACHE_HOME": str(ROOT / "caches/xdg"),
            "HF_HOME": str(ROOT / "caches/hf"),
            "FLASHINFER_CUDA_ARCH_LIST": "10.3a",
            "BUILD_NVEP": "0",
            "BUILD_NIXL_EP": "0",
            "BUILD_NCCL_EP": "0",
            "FLASHINFER_BUILD_NO_PIP": "1",
        }
    )
    return env


def normalized_freeze(text):
    entries = {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        if line.startswith("-e "):
            require("#egg=" in line, "Unidentified editable distribution")
            name = line.rsplit("#egg=", 1)[1]
        else:
            name = re.split(r"==|\s+@\s+", line, maxsplit=1)[0]
        name = re.sub(r"[-_.]+", "-", name).lower()
        require(name not in entries, f"Duplicate distribution: {name}")
        entries[name] = line
    return entries


def verify_stack(probe, freeze, reference, reference_freeze, target):
    for key in ("torch_import", "torch_cuda", "nccl", "nvcc"):
        require(probe[key] == reference[key], f"Image runtime drift: {key}")
    for name, version in reference["versions"].items():
        if name not in TARGET:
            require(
                probe["versions"].get(name) == version, f"Image package drift: {name}"
            )
    for name, version in target.items():
        require(
            probe["versions"].get(name) == version, f"Provider version mismatch: {name}"
        )
    actual, expected = normalized_freeze(freeze), normalized_freeze(reference_freeze)
    require(
        {k: v for k, v in actual.items() if k not in TARGET}
        == {k: v for k, v in expected.items() if k not in TARGET},
        "Unrelated package inventory drift",
    )
    gpus = probe["gpu"].splitlines()[1:]
    require(
        len(gpus) == 8 and all("B300" in row for row in gpus),
        "Expected eight visible B300 GPUs",
    )


def inspect_model():
    safe_ancestors(MODEL)
    require(
        (MODEL / "REVISION").read_text().strip() == REVISION,
        "Checkpoint revision mismatch",
    )
    config = MODEL / "config.json"
    require(config.is_file() and not config.is_symlink(), "Checkpoint config is absent")
    # This checkpoint's index is 22,194,492 bytes; other receipts keep 16 MiB.
    index = read_json(MODEL / "model.safetensors.index.json", limit=32 * 1024 * 1024)
    shards = sorted(set(index["weight_map"].values()))
    require(0 < len(shards) <= 1024, "Invalid checkpoint shard inventory")
    records = {}
    for name in shards:
        require(
            isinstance(name, str)
            and Path(name).name == name
            and name not in (".", ".."),
            "Unsafe checkpoint shard name",
        )
        path = MODEL / name
        require(
            path.is_file() and not path.is_symlink() and path.stat().st_size > 0,
            f"Checkpoint shard absent: {name}",
        )
        records[name] = path.stat().st_size
    return {
        "path": str(MODEL),
        "revision": REVISION,
        "config_sha256": sha(config),
        "index_sha256": sha(MODEL / "model.safetensors.index.json"),
        "shard_bytes": records,
        "tensor_payload_sha_verified": False,
    }


def inventory():
    """Bounded read-only inventory; never traverses a compilation cache."""
    result = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "gpu": command(
            [
                "nvidia-smi",
                "--query-gpu=name,uuid,driver_version,memory.total",
                "--format=csv",
            ]
        ),
        "compute_processes": command(
            ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"]
        ),
        "paths": {},
        "old_cases": [],
        "old_finalized_cases": [],
    }
    for path in (
        OLD,
        OLD / "environment",
        OLD / "sources",
        OLD / "caches/megamoe",
        OLD / "archives",
        CAMPAIGN,
        ROOT,
        MODEL,
    ):
        safe_ancestors(path)
        result["paths"][str(path)] = {
            "exists": path.exists(),
            "is_directory": path.is_dir(),
        }
    old_run = OLD / "results/c2-w4a16-megamoe-autotune-20260921"
    for scenario in ("8k1k", "1k1k"):
        for tp, c in [(4, c) for c in (4, 8, 16, 32, 64, 128, 256)] + [(8, 4)]:
            case = old_run / scenario / "w4a16-megamoe" / f"tp{tp}_conc{c}"
            if case.exists():
                safe_ancestors(case)
                files = {}
                for filename in (
                    "metadata.json",
                    "status.json",
                    "result.json",
                    "server.log",
                    "autotune_cache.before.json",
                ):
                    candidate = case / filename
                    require(
                        not candidate.is_symlink(),
                        f"Symlink case artifact: {candidate}",
                    )
                    if candidate.is_file():
                        files[filename] = {"bytes": candidate.stat().st_size}
                log = case / "server.log"
                tail = None
                if log.is_file():
                    with log.open("rb") as stream:
                        stream.seek(max(0, log.stat().st_size - 8192))
                        tail = stream.read(8192).decode("utf-8", errors="replace")
                result["old_cases"].append(
                    {
                        "case": str(case.relative_to(old_run)),
                        "files": files,
                        "server_log_tail_max8192bytes": tail,
                    }
                )
            path = case / "status.json"
            if path.exists():
                safe_ancestors(path)
                result["old_finalized_cases"].append(
                    {
                        "case": str(case.relative_to(old_run)),
                        "status": read_json(path),
                        "status_sha256": sha(path),
                    }
                )
    result["checkpoint"] = inspect_model()
    result["preservation_note"] = (
        "No prior source, result, bootstrap, or cache file changed or removed; cache directory contents not scanned."
    )
    return result


PROBE = r"""
import importlib.metadata as md, json, pathlib, subprocess, sys
import torch
names = json.loads(sys.argv[1]); versions = {}
for name in names:
    try: versions[name] = md.version(name)
    except md.PackageNotFoundError: versions[name] = None
def cmd(x): return subprocess.check_output(x, text=True).strip()
print(json.dumps({'versions': versions, 'torch_import': str(pathlib.Path(torch.__file__).resolve()), 'torch_cuda': torch.version.cuda, 'nccl': list(torch.cuda.nccl.version()), 'nvcc': cmd(['nvcc', '--version']), 'gpu': cmd(['nvidia-smi', '--query-gpu=name,uuid,driver_version,memory.total', '--format=csv'])}))
"""


class Recorder:
    def __init__(self, directory, env):
        self.directory, self.env, self.number = directory, env, 0

    def run(self, argv, label, codes=(0,)):
        self.number += 1
        stem = self.directory / f"{self.number:02d}-{label}"
        write(stem.with_suffix(".command.json"), argv)
        with (
            stem.with_suffix(".stdout").open("xb") as out,
            stem.with_suffix(".stderr").open("xb") as err,
        ):
            result = subprocess.run(
                argv, env=self.env, stdout=out, stderr=err, check=False
            )
        write(stem.with_suffix(".exit.json"), {"exit_code": result.returncode})
        require(
            result.returncode in codes,
            f"Command failed: {label}, exit {result.returncode}",
        )
        return stem.with_suffix(".stdout").read_text().strip()


def clean_source(recorder, source):
    require(
        recorder.run(["git", "-C", str(source), "rev-parse", "HEAD"], "source-head")
        == FI,
        "FlashInfer commit mismatch",
    )
    require(
        not recorder.run(
            [
                "git",
                "-C",
                str(source),
                "status",
                "--porcelain",
                "--untracked-files=normal",
            ],
            "source-status",
        ),
        "Dirty FlashInfer source",
    )
    status_text = recorder.run(
        ["git", "-C", str(source), "submodule", "status", "--recursive"],
        "submodule-status",
    )
    # Uninitialized unrelated optional submodules are allowed, but the three
    # required imports/build headers must be at their recorded gitlink commits.
    for name in ("3rdparty/cutlass", "3rdparty/cccl", "3rdparty/spdlog"):
        rows = [
            row
            for row in status_text.splitlines()
            if len(row.split()) >= 2 and row.split()[1] == name
        ]
        require(
            len(rows) == 1 and not rows[0].startswith(("-", "+", "U")),
            f"Unresolved required submodule: {name}",
        )


def download_wheel(record, destination):
    require(
        record["url"].startswith("https://files.pythonhosted.org/"),
        "Unapproved wheel host",
    )
    require(
        Path(record["filename"]).name == record["filename"], "Unsafe wheel filename"
    )
    partial = destination / (record["filename"] + ".partial")
    final = destination / record["filename"]
    with (
        urllib.request.urlopen(record["url"], timeout=60) as source,
        partial.open("xb") as output,
    ):
        shutil.copyfileobj(source, output)
    require(
        partial.stat().st_size == record["bytes"] and sha(partial) == record["sha256"],
        "Wheel byte/SHA mismatch",
    )
    require(not final.exists(), "Wheel destination already exists")
    partial.rename(final)
    return final


def apply(args, lock):
    require(
        platform.system() == "Linux"
        and platform.machine() == "x86_64"
        and sys.version_info[:2] == (3, 12),
        "Requires Linux x86_64 Python 3.12",
    )
    for path in (ROOT, CAMPAIGN):
        safe_ancestors(path)
        require(not path.exists(), f"Fresh exclusive directory required: {path}")
    identity = read_json(args.image_receipt)
    require(
        all(identity.get(k) == v for k, v in IDENTITY.items()),
        "Replacement node/image/queue receipt differs",
    )
    for key, path in (
        ("runtime", args.reference_runtime),
        ("freeze", args.reference_freeze),
    ):
        require(sha(path) == REFERENCE_SHAS[key], f"Retained reference changed: {key}")
    reference = read_json(args.reference_runtime)
    reference_freeze = args.reference_freeze.read_text()
    observed = inventory()
    require(
        not observed["compute_processes"], "GPU processes active before preparation"
    )
    ROOT.mkdir(parents=True, exist_ok=False)
    evidence = ROOT / "evidence"
    evidence.mkdir()
    commands = evidence / "commands"
    commands.mkdir()
    wheels = ROOT / "wheels"
    wheels.mkdir()
    source = ROOT / "sources/flashinfer-ad0"
    env = clean_env()
    recorder = Recorder(commands, env)
    for original, name in (
        (Path(__file__), "bootstrap.py"),
        (LOCK, "wheel-lock.json"),
        (args.image_receipt, "image-receipt.json"),
        (args.reference_runtime, "reference-runtime.json"),
        (args.reference_freeze, "reference-freeze.txt"),
    ):
        shutil.copyfile(original, evidence / name)
    write(evidence / "inventory-before.json", observed)
    write(
        evidence / "cache-paths.json",
        {
            k: v
            for k, v in env.items()
            if k.endswith(
                (
                    "_CACHE_DIR",
                    "_CACHE_PATH",
                    "_CACHE_HOME",
                    "_WORKSPACE_BASE",
                    "_EXTENSIONS_DIR",
                )
            )
            or k == "HF_HOME"
        },
    )
    try:
        names = sorted(set(reference["versions"]) | set(TARGET))
        before = json.loads(
            recorder.run(
                [sys.executable, "-I", "-c", PROBE, json.dumps(names)], "probe-before"
            )
        )
        frozen_before = recorder.run(
            [sys.executable, "-I", "-m", "pip", "--isolated", "freeze"], "freeze-before"
        )
        write(evidence / "runtime-before.json", before)
        (evidence / "packages-before.txt").write_text(frozen_before + "\n")
        recorder.run(
            [sys.executable, "-I", "-m", "pip", "--isolated", "check"],
            "pip-check-before",
            (0, 1),
        )
        verify_stack(before, frozen_before, reference, reference_freeze, FRESH)
        for record in lock["packages"].values():
            download_wheel(record, wheels)
        source.parent.mkdir()
        recorder.run(["git", "init", str(source)], "git-init")
        recorder.run(
            [
                "git",
                "-C",
                str(source),
                "remote",
                "add",
                "origin",
                "https://github.com/flashinfer-ai/flashinfer.git",
            ],
            "git-origin",
        )
        recorder.run(
            ["git", "-C", str(source), "fetch", "--depth=1", "--no-tags", "origin", FI],
            "git-fetch",
        )
        recorder.run(
            ["git", "-C", str(source), "checkout", "--detach", FI], "git-checkout"
        )
        recorder.run(
            [
                "git",
                "-C",
                str(source),
                "submodule",
                "update",
                "--init",
                "--recursive",
                "--depth=1",
                "3rdparty/cutlass",
                "3rdparty/cccl",
                "3rdparty/spdlog",
            ],
            "git-submodules",
        )
        clean_source(recorder, source)
        idle()
        recorder.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pip",
                "--isolated",
                "uninstall",
                "-y",
                "flashinfer-python",
                "flashinfer-cubin",
                "flashinfer-jit-cache",
            ],
            "remove-old-fi",
        )
        recorder.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-deps",
                "--no-index",
                *[
                    str(wheels / record["filename"])
                    for record in lock["packages"].values()
                ],
            ],
            "install-provider-wheels",
        )
        recorder.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-deps",
                "--no-build-isolation",
                "--no-index",
                "-e",
                str(source),
            ],
            "install-fi-editable",
        )
        after = json.loads(
            recorder.run(
                [sys.executable, "-I", "-c", PROBE, json.dumps(names)], "probe-after"
            )
        )
        frozen_after = recorder.run(
            [sys.executable, "-I", "-m", "pip", "--isolated", "freeze"], "freeze-after"
        )
        write(evidence / "runtime-after.json", after)
        (evidence / "packages-after.txt").write_text(frozen_after + "\n")
        recorder.run(
            [sys.executable, "-I", "-m", "pip", "--isolated", "check"],
            "pip-check-after",
            (0, 1),
        )
        verify_stack(after, frozen_after, reference, reference_freeze, TARGET)
        require(
            all(
                before[k] == after[k]
                for k in ("torch_import", "torch_cuda", "nccl", "nvcc", "gpu")
            ),
            "Image/GPU runtime changed during bootstrap",
        )
        imports = recorder.run(
            [
                sys.executable,
                "-I",
                "-c",
                "import json,flashinfer,cutlass; from cupti import cupti; from flashinfer.moe_ep import Sm100_Bf16_Nvfp4_Bf16_Cutedsl_MegaMoeConfig; print(json.dumps({'flashinfer':flashinfer.__file__,'cutlass':cutlass.__file__,'cupti_timestamp_ok':isinstance(cupti.get_timestamp(),int)}))",
            ],
            "source-imports",
        )
        import_record = json.loads(imports)
        require(
            Path(import_record["flashinfer"]).resolve()
            == source / "flashinfer/__init__.py"
            and import_record["cupti_timestamp_ok"],
            "Source import/CUPTI binding mismatch",
        )
        write(evidence / "source-imports.json", import_record)
        clean_source(recorder, source)
        idle()
        files = {
            str(p.relative_to(evidence)): {"bytes": p.stat().st_size, "sha256": sha(p)}
            for p in evidence.rglob("*")
            if p.is_file()
        }
        write(
            evidence / "bootstrap-completed.json",
            {
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "identity_receipt": IDENTITY,
                "bootstrap_root": str(ROOT),
                "source_commit": FI,
                "source_root": str(source),
                "files": files,
                "wheels": lock["packages"],
                "image_runtime_and_unrelated_packages_preserved": True,
                "benchmark_launched": False,
                "gpu_performance_validated": False,
                "next_step": "Main campaign prepare clones and rebinds its own source in the separate fresh campaign root.",
            },
        )
    except BaseException as error:
        write(
            evidence / "bootstrap-failed.json",
            {
                "error": f"{type(error).__name__}: {error}",
                "failed_at": datetime.now(timezone.utc).isoformat(),
                "partial_evidence_preserved": True,
            },
        )
        raise
    return {
        "prepared": True,
        "receipt": str(evidence / "bootstrap-completed.json"),
        "benchmark_launched": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", nargs="?", default="plan", choices=("plan", "inventory", "apply")
    )
    parser.add_argument("--image-receipt", type=Path)
    parser.add_argument("--reference-runtime", type=Path)
    parser.add_argument("--reference-freeze", type=Path)
    args = parser.parse_args()
    require(sha(LOCK) == LOCK_SHA, "Wheel lock changed")
    lock = read_json(LOCK)
    if args.action == "plan":
        value = {
            "identity": IDENTITY,
            "bootstrap_root": str(ROOT),
            "campaign_root": str(CAMPAIGN),
            "preserved_old_root": str(OLD),
            "model": str(MODEL),
            "flashinfer_commit": FI,
            "packages": TARGET,
            "wheel_lock_sha256": LOCK_SHA,
            "default_remote_or_package_mutations": False,
        }
    elif args.action == "inventory":
        value = inventory()
    else:
        require(
            all((args.image_receipt, args.reference_runtime, args.reference_freeze)),
            "apply requires image receipt and both retained reference files",
        )
        value = apply(args, lock)
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
