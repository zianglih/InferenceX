"""Isolated retained-node MegaMoE campaign; no HAI or provisioning operations.

Prepare on the selected idle node, then launch only after reviewing the receipt::

    python3 campaign_20260921.py prepare --task-root /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921 \
        --recipe-commit FULL_SHA --model-path /data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4 \
        --image-receipt /path/to/caller-image-receipt.json
    python3 TASK_ROOT/sources/inferencex/experimental/glm52_b300_fixed_seq/campaign_20260921.py launch --task-root TASK_ROOT
    python3 TASK_ROOT/sources/inferencex/experimental/glm52_b300_fixed_seq/campaign_20260921.py status --task-root TASK_ROOT

The image receipt must contain image (the exact digest-qualified IMAGE below),
node, cluster, and namespace. The caller supplies actual provisioning evidence;
this script cannot discover a container image digest from inside the container.
Preparation requires the already installed FI/CuTe stack. Only its editable FI
source binding changes; no dependencies are installed. Failed preparation is
retained and refuses retry into the same directory. A launch is never implicit.
For a replacement campaign, pass a fresh --task-root and --run-id on every action.
The default run ID retains the original campaign identity; sealed inputs must match.
"""

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tarfile
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

SG = "6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2"
FI = "ad0a5e5e78e57070ec7c582efe733cb55cd8839f"
MODEL_REVISION = "53e0691e21895a3863a606dfd12910c69eba94ab"
IMAGE = (
    "lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85@sha256:"
    "b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596"
)
RUN_ID = "c2-w4a16-megamoe-autotune-20260921"
RELATIVE = Path("experimental/glm52_b300_fixed_seq")
PACKAGES = (
    "torch",
    "triton",
    "transformers",
    "sglang-kernel",
    "flashinfer-python",
    "flashinfer-cubin",
    "flashinfer-jit-cache",
    "nccl-extensions",
    "cuda-python",
    "cuda-bindings",
    "cuda-core",
    "nvidia-nccl-cu13",
    "nvidia-cutlass-dsl",
    "nvidia-cutlass-dsl-libs-base",
    "nvidia-cutlass-dsl-libs-core",
    "nvidia-cutlass-dsl-libs-cu12",
    "nvidia-cutlass-dsl-libs-cu13",
)


def now():
    return datetime.now(UTC).isoformat()


def validate_run_id(value):
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[a-z0-9][a-z0-9-]{0,127}", value) is None
    ):
        raise ValueError(
            "Run ID must be a lowercase alphanumeric/hyphen slug of 1-128 characters"
        )
    return value


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    with Path(path).open("x") as stream:
        stream.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def atomic_json(path, value):
    path = Path(path)
    partial = path.with_name(path.name + ".partial")
    write_json(partial, value)
    if path.exists():
        raise FileExistsError(path)
    partial.rename(path)


def command(args, **kwargs):
    return subprocess.check_output(args, text=True, **kwargs).strip()


def clean_head(path, expected):
    actual = command(["git", "-C", str(path), "rev-parse", "HEAD"])
    if actual != expected:
        raise ValueError(f"Source pin mismatch: {path}: {actual} != {expected}")
    if command(
        ["git", "-C", str(path), "status", "--porcelain", "--untracked-files=normal"]
    ):
        raise ValueError(f"Dirty source tree: {path}")
    return actual


def idle():
    active = command(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"]
    )
    if active:
        raise RuntimeError(f"GPU compute processes still present: {active}")


def clean_env():
    env = dict(os.environ)
    for name in list(env):
        if name.startswith(
            ("SGLANG_", "FLASHINFER_", "MEGA_", "CAMPAIGN_")
        ) or name in (
            "PYTHONPATH",
            "CUDA_VISIBLE_DEVICES",
            "TORCHINDUCTOR_CACHE_DIR",
            "TRITON_CACHE_DIR",
            "CUTE_DSL_CACHE_DIR",
            "CUDA_CACHE_PATH",
            "TORCH_EXTENSIONS_DIR",
            "XDG_CACHE_HOME",
        ):
            del env[name]
    env["PYTHONNOUSERSITE"] = "1"
    return env


def probe():
    import torch

    versions = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "versions": versions,
        "torch_import": str(Path(torch.__file__).resolve()),
        "torch_cuda": torch.version.cuda,
        "nccl": list(torch.cuda.nccl.version()),
        "nvcc": command(["nvcc", "--version"]),
        "gpu": command(
            [
                "nvidia-smi",
                "--query-gpu=name,uuid,driver_version,memory.total",
                "--format=csv",
            ]
        ),
    }


def require_stack(probe_data):
    versions = probe_data["versions"]
    expected = {"flashinfer-python": "0.7.0", "nccl-extensions": "0.1.0"}
    expected.update(
        {name: "4.7.1" for name in PACKAGES if name.startswith("nvidia-cutlass-dsl")}
    )
    expected.update({"flashinfer-cubin": None, "flashinfer-jit-cache": None})
    for name, value in expected.items():
        if versions.get(name) != value:
            raise ValueError(
                f"Existing stack mismatch: {name}: {versions.get(name)!r} != {value!r}"
            )
    gpu_lines = probe_data["gpu"].splitlines()[1:]
    if len(gpu_lines) != 8 or any("B300" not in line for line in gpu_lines):
        raise ValueError("Campaign requires eight visible B300 GPUs")


def freeze_without_fi(text):
    kept = []
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        if line.startswith("-e "):
            if "#egg=" not in line:
                raise ValueError(f"Unidentified editable package: {line}")
            name = line.rsplit("#egg=", 1)[1]
        else:
            name = re.split(r"==|\s+@\s+", line, maxsplit=1)[0]
        if re.sub(r"[-_.]+", "-", name).lower() != "flashinfer-python":
            kept.append(line)
    return sorted(kept)


def clone(root, name, url, commit):
    path = root / "sources" / name
    path.mkdir(parents=True)
    subprocess.run(["git", "init", str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "remote", "add", "origin", url], check=True)
    subprocess.run(
        ["git", "-C", str(path), "fetch", "--depth=1", "--no-tags", "origin", commit],
        check=True,
    )
    subprocess.run(["git", "-C", str(path), "checkout", "--detach", commit], check=True)
    clean_head(path, commit)
    return path


def resolved_config(recipe):
    values = command(
        [
            "bash",
            "-c",
            'set -eo pipefail; source "$1/config.env"; source "$1/config-megamoe.env"; env',
            "_",
            str(recipe / RELATIVE),
        ],
        env=clean_env(),
    )
    values = dict(line.split("=", 1) for line in values.splitlines() if "=" in line)
    required = {
        "IMAGE": IMAGE,
        "SGLANG_COMMIT": SG,
        "FLASHINFER_COMMIT": FI,
        "MODEL_REVISION": MODEL_REVISION,
        "MEM_FRACTION_STATIC": "0.80",
        "PARALLEL_TOPOLOGY": "dp-ep",
        "PREFILL_CUDA_GRAPH_POLICY": "disabled",
        "SGLANG_FLASHINFER_AUTOTUNE_CACHE": "1",
        "RUN_MEGAMOE": "true",
        "SCENARIOS": "8k1k:8192:1024 1k1k:1024:1024",
        "SWEEP_CASES": "4:256 4:4 4:8 4:16 4:32 4:64 4:128 8:4",
        "SPECULATIVE_NUM_STEPS": "3",
        "SPECULATIVE_EAGLE_TOPK": "1",
        "SPECULATIVE_NUM_DRAFT_TOKENS": "4",
        "CHUNKED_PREFILL_SIZE": "32768",
        "MAX_PREFILL_TOKENS": "32768",
        "RANDOM_RANGE_RATIO": "0.8",
        "PROMPTS_PER_CONCURRENCY": "10",
    }
    for key, value in required.items():
        if values.get(key) != value:
            raise ValueError(f"Resolved recipe {key}: {values.get(key)!r} != {value!r}")
    return required


def inventory(root):
    """Hash regular files, preserving explicit link information for caches."""
    root = Path(root)
    result = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            # Links are recorded but never followed during this inventory.
            result[relative] = {"type": "symlink", "target": os.readlink(path)}
        elif path.is_file():
            result[relative] = {
                "type": "file",
                "bytes": path.stat().st_size,
                "sha256": sha(path),
            }
        elif not path.is_dir():
            raise ValueError(f"Special file cannot be archived: {path}")
    return result


def prepare(args, root):
    run_id = validate_run_id(args.run_id)
    if re.fullmatch(r"[0-9a-f]{40}", args.recipe_commit) is None:
        raise ValueError("--recipe-commit must be a full commit SHA")
    image_receipt = json.loads(args.image_receipt.read_text())
    if image_receipt.get("image") != IMAGE or any(
        not image_receipt.get(key) for key in ("node", "cluster", "namespace")
    ):
        raise ValueError("Image receipt must identify the actual node and exact IMAGE")
    model = args.model_path.resolve(strict=True)
    if (model / "REVISION").read_text().strip() != MODEL_REVISION:
        raise ValueError("Checkpoint revision mismatch")
    if not (model / "config.json").is_file():
        raise ValueError("Checkpoint config is missing")
    idle()
    # A new campaign root is required. Failed preparation remains for inspection.
    root.mkdir(parents=True, exist_ok=False)
    evidence = root / "environment"
    evidence.mkdir()
    shutil.copyfile(args.image_receipt, evidence / "image-receipt.json")
    inputs = {
        "task_root": str(root),
        "model_path": str(model),
        "recipe_commit": args.recipe_commit,
        "sglang_commit": SG,
        "flashinfer_commit": FI,
        "image": IMAGE,
        "run_id": run_id,
    }
    write_json(evidence / "inputs.json", inputs)
    shutil.copyfile(__file__, evidence / "preparation-helper.py")
    env = clean_env()
    before = probe()
    write_json(evidence / "runtime-before.json", before)
    require_stack(before)
    freeze_before = command([sys.executable, "-m", "pip", "freeze"], env=env)
    (evidence / "packages-before.txt").write_text(freeze_before + "\n")
    sg = clone(root, "sglang", "https://github.com/sgl-project/sglang.git", SG)
    fi = clone(
        root, "flashinfer", "https://github.com/flashinfer-ai/flashinfer.git", FI
    )
    recipe = clone(
        root,
        "inferencex",
        "https://github.com/zianglih/InferenceX.git",
        args.recipe_commit,
    )
    checked_helper = recipe / RELATIVE / Path(__file__).name
    if sha(checked_helper) != sha(__file__):
        raise ValueError("Preparation helper differs from the committed recipe")
    write_json(evidence / "resolved-config.json", resolved_config(recipe))
    subprocess.run(
        [
            "git",
            "-C",
            str(fi),
            "submodule",
            "update",
            "--init",
            "--recursive",
            "--depth=1",
            "3rdparty/cutlass",
            "3rdparty/cccl",
            "3rdparty/spdlog",
        ],
        check=True,
    )
    install_env = env | {
        "BUILD_NVEP": "0",
        "BUILD_NIXL_EP": "0",
        "BUILD_NCCL_EP": "0",
        "FLASHINFER_BUILD_NO_PIP": "1",
    }
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-build-isolation",
            "-e",
            str(fi),
        ],
        env=install_env,
        check=True,
    )
    after = probe()
    write_json(evidence / "runtime-after.json", after)
    require_stack(after)
    if before != after:
        raise ValueError("Runtime changed beyond the editable source binding")
    freeze_after = command([sys.executable, "-m", "pip", "freeze"], env=env)
    (evidence / "packages-after.txt").write_text(freeze_after + "\n")
    if freeze_without_fi(freeze_before) != freeze_without_fi(freeze_after):
        raise ValueError("Unapproved dependency change")
    env.update(
        {
            "PYTHONPATH": f"{sg / 'python'}:{fi}:{recipe}",
            "SGLANG_SOURCE_ROOT": str(sg),
            "FLASHINFER_SOURCE_ROOT": str(fi),
            "FLASHINFER_COMMIT": FI,
        }
    )
    with (evidence / "source-imports.log").open("x") as log:
        subprocess.run(
            [sys.executable, str(recipe / RELATIVE / "artifacts.py"), "verify-source"],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    sources = evidence / "sources"
    sources.mkdir()
    for name, commit in (
        ("sglang", SG),
        ("flashinfer", FI),
        ("inferencex", args.recipe_commit),
    ):
        path = root / "sources" / name
        clean_head(path, commit)
        with (sources / f"{name}.tar.gz").open("xb") as stream:
            subprocess.run(
                ["git", "-C", str(path), "archive", "--format=tar.gz", "HEAD"],
                stdout=stream,
                check=True,
            )
        submodules = command(
            ["git", "-C", str(path), "submodule", "status", "--recursive"]
        )
        (sources / f"{name}-submodules.txt").write_text(submodules + "\n")
        for line in submodules.splitlines():
            if line.startswith("-"):
                continue
            # Preserve initialized dependency source bytes as independent git archives.
            revision, relative = line.split()[:2]
            relative_path = Path(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError(f"Unexpected submodule path: {relative}")
            dependency = path / relative_path
            clean_head(dependency, revision)
            filename = f"{name}-submodule-{hashlib.sha256(relative.encode()).hexdigest()[:16]}.tar.gz"
            with (sources / filename).open("xb") as stream:
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(dependency),
                        "archive",
                        "--format=tar.gz",
                        "HEAD",
                    ],
                    stdout=stream,
                    check=True,
                )
    helpers = evidence / "helpers"
    helpers.mkdir()
    for name in ("campaign_20260921.py", "run_megamoe_20260921.sh"):
        shutil.copyfile(recipe / RELATIVE / name, helpers / name)
    (root / "results").mkdir()
    (root / "caches/megamoe").mkdir(parents=True)
    (root / "archives").mkdir()
    write_json(
        evidence / "setup-completed.json",
        {
            "completed_at": now(),
            "inputs": inputs,
            "files": inventory(evidence),
            "runtime_preserved": True,
            "image_evidence_source": "caller-supplied provisioning receipt",
        },
    )
    print(json.dumps({"prepared": True, "root": str(root), "launch_performed": False}))


def verified_inputs(root, run_id=RUN_ID):
    validate_run_id(run_id)
    evidence = root / "environment"
    receipt = json.loads((evidence / "setup-completed.json").read_text())
    for relative, record in receipt["files"].items():
        path = evidence / relative
        if (
            record["type"] != "file"
            or not path.is_file()
            or path.is_symlink()
            or sha(path) != record["sha256"]
        ):
            raise ValueError(f"Preparation evidence changed: {relative}")
    inputs = receipt["inputs"]
    if (
        inputs["task_root"] != str(root)
        or inputs["image"] != IMAGE
        or inputs["run_id"] != run_id
    ):
        raise ValueError("Preparation identity mismatch")
    for name, expected in (
        ("sglang", SG),
        ("flashinfer", FI),
        ("inferencex", inputs["recipe_commit"]),
    ):
        clean_head(root / "sources" / name, expected)
    resolved_config(root / "sources/inferencex")
    if (Path(inputs["model_path"]) / "REVISION").read_text().strip() != MODEL_REVISION:
        raise ValueError("Checkpoint revision changed")
    return inputs


def full_matrix(run, recipe_commit, run_id=RUN_ID):
    validate_run_id(run_id)
    expected = {
        f"{s}/w4a16-megamoe/tp{tp}_conc{c}": (s, tp, c)
        for s in ("8k1k", "1k1k")
        for tp, c in [(4, c) for c in (4, 8, 16, 32, 64, 128, 256)] + [(8, 4)]
    }
    found = {str(p.parent.relative_to(run)) for p in run.rglob("status.json")}
    if found != set(expected):
        raise ValueError(
            f"Incomplete matrix: missing={sorted(set(expected) - found)}, extra={sorted(found - set(expected))}"
        )
    for relative, (scenario, tp, concurrency) in expected.items():
        case = run / relative
        for name in (
            "result.json",
            "metadata.json",
            "status.json",
            "benchmark.log",
            "server.log",
            "server_command.sh",
            "benchmark_command.sh",
            "server_info.before.json",
            "server_info.after.json",
            "packages.json",
            "nvidia-smi.txt",
            "gpu_metrics.csv",
            "gpu_metrics_identity.csv",
            "autotune_cache.before.json",
        ):
            path = case / name
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"{relative}: missing regular raw file {name}")
        meta = json.loads((case / "metadata.json").read_text())
        status = json.loads((case / "status.json").read_text())
        result = json.loads((case / "result.json").read_text())
        fields = {
            "run_id": run_id,
            "scenario": scenario,
            "backend": "w4a16_megamoe",
            "tp": tp,
            "dp": tp,
            "ep": tp,
            "concurrency": concurrency,
            "mem_fraction_static": 0.80,
            "sglang_commit": SG,
            "flashinfer_commit": FI,
            "inferencex_commit": recipe_commit,
            "image": IMAGE,
            "model_revision": MODEL_REVISION,
            "status": "completed",
            "num_prompts": 10 * concurrency,
            "server_max_running_requests": max(concurrency, tp),
            "prefill_cuda_graph_policy": "disabled",
        }
        for key, value in fields.items():
            if meta.get(key) != value:
                raise ValueError(
                    f"{relative}: {key} mismatch: {meta.get(key)!r} != {value!r}"
                )
        if (
            status.get("status") != "completed"
            or status.get("exit_code") != 0
            or status.get("failed") != 0
        ):
            raise ValueError(f"{relative}: failed status")
        if (
            status.get("completed") != 10 * concurrency
            or status.get("expected") != 10 * concurrency
        ):
            raise ValueError(f"{relative}: status count mismatch")
        if (
            result.get("completed") != 10 * concurrency
            or result.get("max_concurrency") != concurrency
        ):
            raise ValueError(f"{relative}: raw client count/concurrency mismatch")
        if not all(
            isinstance(result.get(k), (int, float))
            and math.isfinite(result[k])
            and result[k] > 0
            for k in ("duration", "output_throughput")
        ):
            raise ValueError(f"{relative}: invalid measured throughput/duration")
    return {
        "cases": 16,
        "successful_requests": 10240,
        "gate": "request/provenance; runtime tuning audit is separate",
    }


def seal_tar(path, entries):
    """Atomic tar+SHA pair; partials and conflicting existing output are preserved."""
    checksum = Path(str(path) + ".sha256")
    partial = Path(str(path) + ".partial")
    sha_partial = Path(str(checksum) + ".partial")
    if any(p.exists() or p.is_symlink() for p in (partial, sha_partial)):
        raise FileExistsError(f"Unverified partial archive: {path}")
    if any(p.exists() or p.is_symlink() for p in (path, checksum)):
        if (
            path.is_symlink()
            or checksum.is_symlink()
            or not path.is_file()
            or not checksum.is_file()
            or checksum.read_text() != f"{sha(path)}  {path.name}\n"
        ):
            raise ValueError(f"Conflicting archive/checksum: {path}")
        return {
            "path": str(path),
            "bytes": path.stat().st_size,
            "sha256": sha(path),
            "reused": True,
        }
    with (
        partial.open("xb") as stream,
        tarfile.open(fileobj=stream, mode="w:gz") as archive,
    ):
        for source, name in entries:
            archive.add(source, arcname=name)
    digest = sha(partial)
    with sha_partial.open("x") as stream:
        stream.write(f"{digest}  {path.name}\n")
    if path.exists() or checksum.exists():
        raise FileExistsError(path)
    partial.rename(path)
    sha_partial.rename(checksum)
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": digest,
        "reused": False,
    }


def archive_run(root, inputs, benchmark_code):
    run_id = validate_run_id(inputs["run_id"])
    idle()
    run = root / "results" / run_id
    complete = (
        full_matrix(run, inputs["recipe_commit"], run_id)
        if benchmark_code == 0
        else None
    )
    cache = root / "caches/megamoe"
    if not cache.is_dir():
        raise FileNotFoundError(cache)
    manifest = root / "archives" / f"{run_id}-cache-manifest.json"
    cache_inventory = inventory(cache)
    external_entries = []
    # This is a preservation archive, never automatically extracted. Link targets
    # are explicit so a future restore can validate/rebuild them without guessing.
    for relative, info in cache_inventory.items():
        if info["type"] == "symlink":
            target = (cache / relative).resolve(strict=True)
            if not (
                target.is_relative_to(cache)
                or target.is_relative_to(root / "sources/flashinfer")
            ):
                raise ValueError(
                    f"Cache link escapes campaign cache/FI source: {relative} -> {target}"
                )
            info["resolved_target"] = str(target)
            info["resolved_files"] = (
                inventory(target)
                if target.is_dir()
                else {
                    ".": {
                        "type": "file",
                        "bytes": target.stat().st_size,
                        "sha256": sha(target),
                    }
                }
            )
            if any(item["type"] != "file" for item in info["resolved_files"].values()):
                raise ValueError(
                    f"Nested cache link requires explicit review: {relative}"
                )
            if not target.is_relative_to(cache):
                archive_name = (
                    "source-link-targets/"
                    + hashlib.sha256(relative.encode()).hexdigest()
                )
                info["archived_target"] = archive_name
                external_entries.append((target, archive_name))
    if manifest.exists():
        if json.loads(manifest.read_text()) != cache_inventory:
            raise ValueError("Cache changed since its preservation manifest")
    else:
        write_json(manifest, cache_inventory)
    raw_entries = [(root / "environment", f"{run_id}-environment")]
    if run.exists():
        raw_entries.append((run, run_id))
    for suffix in ("launch.json", "launch.log", "benchmark-exit.json"):
        path = root / "results" / f"{run_id}-{suffix}"
        if path.exists():
            raw_entries.append((path, path.name))
    raw = seal_tar(root / "archives" / f"{run_id}-raw.tar.gz", raw_entries)
    caches = seal_tar(
        root / "archives" / f"{run_id}-caches.tar.gz",
        [(cache, "megamoe"), (manifest, manifest.name), *external_entries],
    )
    result = {
        "archived_at": now(),
        "benchmark_exit_code": benchmark_code,
        "complete_matrix": complete,
        "raw": raw,
        "caches": caches,
        "cache_manifest_sha256": sha(manifest),
    }
    receipt = root / "archives" / f"{run_id}-archives.json"
    if receipt.exists():
        previous = json.loads(receipt.read_text())
        for key in ("benchmark_exit_code", "complete_matrix", "cache_manifest_sha256"):
            if previous[key] != result[key]:
                raise ValueError(f"Existing archive receipt differs: {key}")
        for key in ("raw", "caches"):
            if previous[key]["sha256"] != result[key]["sha256"]:
                raise ValueError(f"Existing {key} archive receipt differs")
        return previous
    atomic_json(receipt, result)
    return result


def worker(root, run_id=RUN_ID):
    validate_run_id(run_id)
    result = {"started_at": now(), "exit_code": 1}
    child = None

    def interrupted(signum, _frame):
        if child is not None and child.poll() is None:
            child.send_signal(signum)
        raise InterruptedError(f"Worker received signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        inputs = verified_inputs(root, run_id)
        before = json.loads((root / "environment/runtime-after.json").read_text())
        if probe() != before:
            raise ValueError("Runtime drift since preparation")
        current_freeze = command(
            [sys.executable, "-m", "pip", "freeze"], env=clean_env()
        )
        if (
            current_freeze
            != (root / "environment/packages-after.txt").read_text().strip()
        ):
            raise ValueError("Package inventory drift since preparation")
        idle()
        env = clean_env() | {
            "CAMPAIGN_TASK_ROOT": str(root),
            "CAMPAIGN_MODEL_PATH": inputs["model_path"],
            "CAMPAIGN_RECIPE_ROOT": str(root / "sources/inferencex"),
            "CAMPAIGN_RUN_ID": inputs["run_id"],
        }
        child = subprocess.Popen(
            [
                "bash",
                str(root / "sources/inferencex" / RELATIVE / "run_megamoe_20260921.sh"),
            ],
            env=env,
        )
        rc = child.wait()
        result["benchmark_exit_code"] = rc
        atomic_json(
            root / "results" / f"{run_id}-benchmark-exit.json",
            {"exit_code": rc, "finished_at": now()},
        )
        result["archives"] = archive_run(root, inputs, rc)
        result["exit_code"] = 0 if rc == 0 else 1
    except BaseException as error:  # noqa: BLE001 - persist exit evidence even on interruption
        result["error"] = f"{type(error).__name__}: {error}"
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=60)
            except subprocess.TimeoutExpired:
                result["child_cleanup_pending"] = True
    finally:
        result["finished_at"] = now()
        atomic_json(root / "results" / f"{run_id}-exit.json", result)
    return result["exit_code"]


def launch(root, run_id=RUN_ID):
    inputs = verified_inputs(root, run_id)
    idle()
    results = root / "results"
    if (results / run_id).exists() or any(results.glob(f"{run_id}-*")):
        raise FileExistsError(
            "Campaign already launched or has partial launch evidence"
        )
    script = root / "sources/inferencex" / RELATIVE / Path(__file__).name
    with (results / f"{run_id}-launch.log").open("xb") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                str(script),
                "worker",
                "--task-root",
                str(root),
                "--run-id",
                run_id,
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
            env=clean_env(),
        )
    receipt = {
        "started_at": now(),
        "pid": process.pid,
        "argv": process.args,
        "helper_sha256": sha(script),
        "inputs": inputs,
    }
    atomic_json(results / f"{run_id}-launch.json", receipt)
    print(json.dumps(receipt, indent=2))


def status(root, run_id=RUN_ID):
    validate_run_id(run_id)
    inputs = json.loads((root / "environment/setup-completed.json").read_text())[
        "inputs"
    ]
    if inputs["task_root"] != str(root) or inputs["run_id"] != run_id:
        raise ValueError("Preparation identity mismatch")
    results = root / "results"
    output = {
        "run_id": run_id,
        "observed_at": now(),
        "finalized_cases": len(list((results / run_id).rglob("status.json"))),
    }
    for name in ("launch", "benchmark-exit", "exit"):
        path = results / f"{run_id}-{name}.json"
        output[name] = json.loads(path.read_text()) if path.is_file() else None
    if output["launch"] and output["exit"] is None:
        pid = output["launch"]["pid"]
        state = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        output["worker_process_state"] = state or "absent"
        output["missing_exit_marker"] = not state or state.startswith("Z")
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("prepare", "launch", "worker", "status", "archive")
    )
    parser.add_argument("--task-root", required=True, type=Path)
    parser.add_argument("--run-id", default=RUN_ID, type=validate_run_id)
    parser.add_argument("--recipe-commit")
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--image-receipt", type=Path)
    args = parser.parse_args()
    root = args.task_root
    if (
        not root.is_absolute()
        or root == Path("/")
        or root.is_relative_to("/workspace")
        or root.is_symlink()
    ):
        parser.error(
            "--task-root must be an absolute, non-symlink persistent task directory outside /workspace"
        )
    root = root.resolve()
    if args.action == "prepare":
        if not all((args.recipe_commit, args.model_path, args.image_receipt)):
            parser.error(
                "prepare requires --recipe-commit, --model-path, and --image-receipt"
            )
        prepare(args, root)
    elif args.action == "launch":
        launch(root, args.run_id)
    elif args.action == "worker":
        return worker(root, args.run_id)
    elif args.action == "status":
        status(root, args.run_id)
    else:
        inputs = verified_inputs(root, args.run_id)
        code = json.loads(
            (root / "results" / f"{args.run_id}-benchmark-exit.json").read_text()
        )["exit_code"]
        print(json.dumps(archive_run(root, inputs, code), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
