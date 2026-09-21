#!/usr/bin/env python3
"""Launch only the fourteen real-weight recovery4 points after reviewed bootstrap.

No package mutation, cache copy, dummy workload or diagnostic kernel execution.
The two accepted recovery1 cases remain immutable external references.
"""

import argparse
import importlib.util
import json
import signal
import socket
import subprocess
import sys
from pathlib import Path


def bootstrap():
    path = Path(__file__).with_name("bootstrap_megamoe_recovery4.py")
    spec = importlib.util.spec_from_file_location("_recovery4_bootstrap", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def verify(c):
    pkg, b, r, layout = c.modules()
    pkg.safe_ancestors(c.ROOT)
    evidence = c.ROOT / "environment"
    seal = c.validate_seal(evidence, "setup-completed.json")
    boot = c.validate_seal(evidence / "bootstrap", "bootstrap-completed.json")
    c.require(
        seal.get("bootstrap_seal_sha256")
        == c.sha(evidence / "bootstrap/bootstrap-completed.json")
        and seal.get("cache_copied") is False
        and boot.get("task_root") == str(c.ROOT)
        and boot.get("bootstrap_root") == str(c.BOOTSTRAP),
        "Bootstrap lineage differs",
    )
    c.checked_identity(
        json.loads((evidence / "image-receipt.json").read_text()), socket.gethostname()
    )
    c.require(
        Path(__file__).resolve() == evidence / "helpers/continue_megamoe_recovery4.py"
        and Path(c.__file__).resolve()
        == evidence / "helpers/bootstrap_megamoe_recovery4.py",
        "Launch only the sealed campaign-local helpers",
    )
    inputs = b.verified_inputs(c.ROOT, c.RUN)
    c.require(
        c.published_helpers(c.ROOT / "sources/inferencex", b.RELATIVE)
        == json.loads((evidence / "published-helper-binding.json").read_text()),
        "Published helper binding changed",
    )
    c.require(
        layout.resources(b, c.ROOT / "sources/flashinfer")
        == json.loads((evidence / "flashinfer-resource-layout.json").read_text()),
        "Prepared FI resource layout changed",
    )
    c.require(
        c.checkpoint(pkg) == json.loads((evidence / "checkpoint.json").read_text()),
        "Real checkpoint changed",
    )
    c.require(
        c.sha(c.ROOT / "sources/inferencex" / b.RELATIVE / "run_megamoe_recovery3.sh")
        == c.WRAPPER_SHA,
        "Real-weight wrapper changed",
    )
    cache = json.loads((evidence / "cache-origin.json").read_text())
    c.require(
        cache.get("copied") is False
        and cache.get("source_cache") is None
        and cache.get("initial_entries") == []
        and cache.get("path") == str(c.ROOT / "caches/megamoe"),
        "Fresh-cache origin evidence differs",
    )
    # Compare current packages/GPU UUIDs with this node's sealed bootstrap only.
    expected = json.loads((evidence / "runtime-after.json").read_text())
    names = sorted(expected["versions"])
    current = json.loads(
        b.command(
            [sys.executable, "-I", "-c", pkg.PROBE, json.dumps(names)],
            env=pkg.clean_env(),
        )
    )
    c.require(
        current == expected, "Current runtime/GPU identity differs from new bootstrap"
    )
    frozen = b.command(
        [sys.executable, "-I", "-m", "pip", "--isolated", "freeze"], env=pkg.clean_env()
    )
    c.require(
        frozen == (evidence / "packages-after.txt").read_text().strip(),
        "Package inventory drift",
    )
    _, refs = r.old_inputs(b)
    c.require(
        refs == json.loads((evidence / "reused-successful-cases.json").read_text()),
        "Original accepted successes changed",
    )
    return pkg, b, r, inputs


def worker(c):
    b = c.load("campaign_20260921.py")
    result = {"started_at": b.now(), "exit_code": 1}
    child = None

    def interrupted(signum, _frame):
        if child is not None and child.poll() is None:
            child.send_signal(signum)
        raise InterruptedError(f"Worker received signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        pkg, b, r, inputs = verify(c)
        c.idle(b)
        # The first real launch still sees an empty campaign cache. Bootstrap
        # imports used their separate bootstrap cache, never copied into this one.
        c.require(
            not any((c.ROOT / "caches/megamoe").iterdir()),
            "Campaign cache populated before first launch",
        )
        env = b.clean_env() | {
            "CAMPAIGN_TASK_ROOT": str(c.ROOT),
            "CAMPAIGN_MODEL_PATH": inputs["model_path"],
            "CAMPAIGN_RECIPE_ROOT": str(c.ROOT / "sources/inferencex"),
            "CAMPAIGN_RUN_ID": c.RUN,
        }
        child = subprocess.Popen(
            [
                "bash",
                str(
                    c.ROOT
                    / "sources/inferencex"
                    / b.RELATIVE
                    / "run_megamoe_recovery3.sh"
                ),
            ],
            env=env,
        )
        rc = child.wait()
        result["benchmark_exit_code"] = rc
        b.atomic_json(
            c.ROOT / "results" / f"{c.RUN}-benchmark-exit.json",
            {"exit_code": rc, "finished_at": b.now()},
        )
        b.full_matrix = lambda run, recipe, run_id: r.remaining_matrix(
            b, run, recipe, run_id
        )
        result["archives"] = b.archive_run(c.ROOT, inputs, rc)
        result["exit_code"] = 0 if rc == 0 else 1
    except BaseException as error:
        result["error"] = f"{type(error).__name__}: {error}"
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=60)
            except subprocess.TimeoutExpired:
                result["child_cleanup_pending"] = True
    finally:
        result["finished_at"] = b.now()
        b.atomic_json(c.ROOT / "results" / f"{c.RUN}-exit.json", result)
    return result["exit_code"]


def launch(c):
    _, b, _, inputs = verify(c)
    c.idle(b)
    results = c.ROOT / "results"
    c.require(
        not (results / c.RUN).exists() and not list(results.glob(f"{c.RUN}-*")),
        "Already launched or partial launch exists; never reuse a run ID",
    )
    script = c.ROOT / "environment/helpers/continue_megamoe_recovery4.py"
    with (results / f"{c.RUN}-launch.log").open("xb") as log:
        child = subprocess.Popen(
            [sys.executable, "-B", str(script), "worker"],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=b.clean_env(),
        )
    receipt = {
        "started_at": b.now(),
        "pid": child.pid,
        "argv": child.args,
        "helper_sha256": c.sha(script),
        "inputs": inputs,
        "setup_seal_sha256": c.sha(c.ROOT / "environment/setup-completed.json"),
    }
    b.atomic_json(results / f"{c.RUN}-launch.json", receipt)
    print(json.dumps(receipt, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        nargs="?",
        default="plan",
        choices=("plan", "launch", "worker", "status"),
    )
    args = parser.parse_args()
    c = bootstrap()
    if args.action == "plan":
        print(json.dumps(c.plan(), indent=2))
    elif args.action == "launch":
        launch(c)
    elif args.action == "worker":
        return worker(c)
    else:
        b = c.load("campaign_20260921.py")
        b.status(c.ROOT, c.RUN)
    return 0


if __name__ == "__main__":
    sys.exit(main())
