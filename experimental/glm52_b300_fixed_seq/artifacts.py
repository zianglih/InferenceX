"""Record local experiment provenance and enforce complete request counts."""

import hashlib
import importlib
import importlib.metadata
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def utc_now():
    return datetime.now(UTC).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def snapshot_autotune(case_dir):
    """Freeze only startup tactic JSON, before benchmark requests can change it."""
    source = Path(os.environ["SGLANG_CACHE_DIR"]) / "flashinfer" / "autotune"
    if not source.is_absolute() or not source.is_dir():
        raise SystemExit(f"Missing absolute startup autotune cache: {source}")
    if any(p.is_symlink() for p in (source, *source.parents)):
        raise SystemExit("Autotune cache root must not traverse symbolic links")

    def inventory():
        paths = []
        for base, dirs, names in os.walk(source, followlinks=False):
            for name in dirs + names:
                entry = Path(base) / name
                if entry.is_symlink():
                    raise SystemExit(f"Unexpected autotune cache link: {entry}")
            for name in names:
                entry = Path(base) / name
                if name.endswith(".json"):
                    if not entry.is_file():
                        raise SystemExit(f"Unexpected autotune cache entry: {entry}")
                    paths.append(entry)
        if not paths or len(paths) > 8192:
            raise SystemExit(f"Unexpected autotune JSON count: {len(paths)}")
        if sum(p.stat().st_size for p in paths) > 128 * 1024 * 1024:
            raise SystemExit("Startup autotune JSON exceeds the 128 MiB snapshot limit")
        return sorted(paths)

    paths = inventory()
    records = []
    for path in paths:
        raw = path.read_bytes()
        content = raw.decode("utf-8")
        json.loads(content)
        records.append(
            {
                "path": str(path.relative_to(source)),
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "content": content,
            }
        )
    if inventory() != paths or any(
        hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]
        for path, record in zip(paths, records, strict=True)
    ):
        raise SystemExit("Autotune cache changed during its pre-benchmark snapshot")
    document = {
        "schema_version": 1,
        "created_at_utc": utc_now(),
        "cache_root": str(source),
        "files": records,
    }
    destination = case_dir / "autotune_cache.before.json"
    # Exclusive creation preserves any earlier receipt and fails the case on conflict.
    with destination.open("x") as stream:
        json.dump(document, stream, indent=2)
        stream.write("\n")
    print(f"Recorded {len(records)} startup tactic JSON files: {destination}")


def flashinfer_source_provenance():
    source_root = os.environ.get("FLASHINFER_SOURCE_ROOT")
    expected_commit = os.environ.get("FLASHINFER_COMMIT")
    if source_root is None and expected_commit is None:
        return {}
    if not source_root or not expected_commit:
        raise SystemExit(
            "FLASHINFER_SOURCE_ROOT and FLASHINFER_COMMIT must both be nonempty"
        )
    source_root = Path(source_root).resolve()
    actual_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=source_root, text=True
    ).strip()
    if actual_commit != expected_commit:
        raise SystemExit(
            f"FlashInfer HEAD is {actual_commit}, expected {expected_commit}"
        )
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=source_root,
        text=True,
    ).strip()
    if dirty:
        raise SystemExit(f"FlashInfer source is not clean:\n{dirty}")
    flashinfer = importlib.import_module("flashinfer")
    actual_path = Path(flashinfer.__file__).resolve()
    if actual_path.parent != source_root / "flashinfer":
        raise SystemExit(
            f"FlashInfer import resolved to {actual_path}, expected {source_root / 'flashinfer'}"
        )
    compiler_modules = {
        name: str(Path(importlib.import_module(name).__file__).resolve())
        for name in ("cutlass", "cutlass.cute", "cutlass.cutlass_dsl")
    }
    compiler_version = importlib.metadata.version("nvidia-cutlass-dsl")
    compiler_libraries = {
        distribution.metadata["Name"]: distribution.version
        for distribution in importlib.metadata.distributions()
        if distribution.metadata.get("Name", "").startswith("nvidia-cutlass-dsl-libs-")
    }
    return {
        "flashinfer_source_root": str(source_root),
        "flashinfer_commit": actual_commit,
        "flashinfer_import_path": str(actual_path),
        "flashinfer_import_version": flashinfer.__version__,
        "cute_dsl_compiler": {
            "version": compiler_version,
            "library_versions": compiler_libraries,
            "import_paths": compiler_modules,
        },
    }


def verify_source():
    import sglang

    expected = Path(os.environ["SGLANG_SOURCE_ROOT"]).resolve() / "python" / "sglang"
    actual = Path(sglang.__file__).resolve().parent
    if actual != expected:
        raise SystemExit(f"SGLang import resolved to {actual}, expected {expected}")
    print(f"Verified source import: {actual}")
    provenance = flashinfer_source_provenance()
    if provenance:
        print(json.dumps(provenance, indent=2))
    return provenance


def verify_cutedsl_source():
    provenance = verify_source()
    expected_flashinfer = os.environ["FLASHINFER_EXPECTED_VERSION"]
    expected_compiler = os.environ["CUTE_DSL_EXPECTED_VERSION"]
    if provenance.get("flashinfer_import_version") != expected_flashinfer:
        raise SystemExit(f"CuTe DSL arm requires FlashInfer {expected_flashinfer}")
    if importlib.metadata.version("flashinfer-python") != expected_flashinfer:
        raise SystemExit("FlashInfer package/import versions differ")
    for package in ("flashinfer-cubin", "flashinfer-jit-cache"):
        try:
            importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            continue
        raise SystemExit(f"CuTe DSL source arm requires {package} to be absent")
    for package in (
        "nvidia-cutlass-dsl",
        "nvidia-cutlass-dsl-libs-base",
        "nvidia-cutlass-dsl-libs-core",
        "nvidia-cutlass-dsl-libs-cu12",
        "nvidia-cutlass-dsl-libs-cu13",
    ):
        if importlib.metadata.version(package) != expected_compiler:
            raise SystemExit(f"CuTe DSL arm requires {package}=={expected_compiler}")
    for name in (
        "FLASHINFER_DISABLE_VERSION_CHECK",
        "FLASHINFER_CUBIN_CHECKSUM_DISABLED",
    ):
        if os.environ.get(name):
            raise SystemExit(f"CuTe DSL source arm rejects {name}")


def start(case_dir):
    versions = {}
    for package in (
        "torch",
        "sglang",
        "sglang-kernel",
        "flashinfer-python",
        "flashinfer-cubin",
        "flashinfer-jit-cache",
        "nvidia-cutlass-dsl",
    ):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    integer_fields = {
        "tp": "TP",
        "dp": "DP",
        "ep": "EP",
        "gpu_count": "TP",
        "concurrency": "CONC",
        "server_max_running_requests": "SERVER_MAX_RUNNING_REQUESTS",
        "isl": "ISL",
        "osl": "OSL",
    }
    metadata = {key: int(os.environ[env]) for key, env in integer_fields.items()}
    metadata.update(
        {
            "schema_version": 1,
            "backend": os.environ["BACKEND"],
            "run_id": os.environ["RUN_ID"],
            "scenario": os.environ["SCENARIO"],
            "hardware": os.environ["HARDWARE"],
            "model": os.environ["MODEL"],
            "model_revision": os.environ["MODEL_REVISION"],
            "model_path": str(Path(os.environ["MODEL_PATH"]).resolve()),
            "image": os.environ["IMAGE"],
            "sglang_commit": os.environ["SGLANG_COMMIT"],
            "sglang_source_root": str(Path(os.environ["SGLANG_SOURCE_ROOT"]).resolve()),
            "inferencex_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=Path(__file__).resolve().parents[2],
                text=True,
            ).strip(),
            "status": "running",
            "benchmark_result": "result.json",
            "num_prompts": int(os.environ["CONC"])
            * int(os.environ["PROMPTS_PER_CONCURRENCY"]),
            "num_warmups": 2 * int(os.environ["CONC"]),
            "random_range_ratio": float(os.environ["RANDOM_RANGE_RATIO"]),
            "mem_fraction_static": float(os.environ["MEM_FRACTION_STATIC"]),
            "started_at": utc_now(),
            "versions": versions,
            "environment": {
                key: value
                for key, value in sorted(os.environ.items())
                if key.startswith(("SGLANG_", "FLASHINFER_"))
                or key
                in (
                    "CUDA_VISIBLE_DEVICES",
                    "PYTHONPATH",
                    "PYTHONNOUSERSITE",
                    "PORT",
                    "CUTE_DSL_CACHE_DIR",
                    "CUDA_CACHE_PATH",
                    "TORCH_EXTENSIONS_DIR",
                    "XDG_CACHE_HOME",
                    "TRITON_CACHE_DIR",
                    "TORCHINDUCTOR_CACHE_DIR",
                )
            },
            "parallel_topology": os.environ["PARALLEL_TOPOLOGY"],
            "prefill_cuda_graph_policy": os.environ["PREFILL_CUDA_GRAPH_POLICY"],
            "quality_evaluation": "not_run",
        }
    )
    metadata.update(flashinfer_source_provenance())
    write_json(case_dir / "metadata.json", metadata)


def finish(case_dir, work_status):
    expected = int(os.environ["CONC"]) * int(os.environ["PROMPTS_PER_CONCURRENCY"])
    status = {
        "status": "failed",
        "exit_code": work_status,
        "expected": expected,
        "completed": None,
        "failed": None,
        "finished_at": utc_now(),
    }
    try:
        result = json.loads((case_dir / "result.json").read_text())
        completed = result.get("completed")
        status["completed"] = completed
        if isinstance(completed, int):
            status["failed"] = expected - completed
        if "benchmark_outcome" in result:
            status["benchmark_outcome"] = result["benchmark_outcome"]
        if "errors" in result:
            status["errors"] = result["errors"]
        passed = (
            work_status == 0
            and completed == expected
            and result.get("num_prompts") == expected
            and result.get("max_concurrency") == int(os.environ["CONC"])
            and not any(result.get("errors", []))
        )
        if passed:
            status["status"] = "completed"
        elif work_status == 0:
            status["exit_code"] = 1
    except (OSError, ValueError) as exc:
        status["artifact_error"] = str(exc)
        if work_status == 0:
            status["exit_code"] = 1
    write_json(case_dir / "status.json", status)
    metadata_path = case_dir / "metadata.json"
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        metadata.update(
            {"status": status["status"], "finished_at": status["finished_at"]}
        )
        write_json(metadata_path, metadata)
    print(json.dumps(status, indent=2))
    return status["exit_code"]


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "verify-source":
        verify_source()
    elif action == "verify-cutedsl-source":
        verify_cutedsl_source()
    elif action == "start":
        start(Path(os.environ["CASE_DIR"]))
    elif action == "snapshot-autotune":
        snapshot_autotune(Path(os.environ["CASE_DIR"]))
    elif action == "finish":
        raise SystemExit(finish(Path(os.environ["CASE_DIR"]), int(sys.argv[2])))
    else:
        raise SystemExit(f"Unknown action: {action}")
