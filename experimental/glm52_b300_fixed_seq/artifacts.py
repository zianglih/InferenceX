"""Record local experiment provenance and enforce complete request counts."""

import importlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


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
            "started_at": utc_now(),
            "versions": versions,
            "environment": {
                key: value
                for key, value in sorted(os.environ.items())
                if key.startswith(("SGLANG_", "FLASHINFER_"))
                or key
                in ("CUDA_VISIBLE_DEVICES", "PYTHONPATH", "PYTHONNOUSERSITE", "PORT")
            },
            "prefill_cuda_graph_policy": "latest-default"
            if os.environ["BACKEND"] == "w4a4_trtllm"
            else "disabled",
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
    elif action == "start":
        start(Path(os.environ["CASE_DIR"]))
    elif action == "finish":
        raise SystemExit(finish(Path(os.environ["CASE_DIR"]), int(sys.argv[2])))
    else:
        raise SystemExit(f"Unknown action: {action}")
