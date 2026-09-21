"""One launch claim, waited campaign, fail-preserving archives. No import effects."""

import os
from pathlib import Path
import signal
import sys
import time
import core

sys.path.insert(0, str(core.HERE / "frozen_campaign"))
import campaign
from owned_history import Registry, proc_info, CAMPAIGN_HISTORY
from owner_ledger import Ledger


def setup_guard(lock, lock_path):
    setup = core.read(core.ROOT / "environment/setup-completed.json")
    core.need(
        setup["status"] == "PREPARED_R7_NO_BENCHMARK" and setup["error"] is None,
        "Preparation not complete",
    )
    core.need(
        core.describe(lock_path) == setup["files"]["activation.json"],
        "Activation changed since preparation",
    )
    for name, expected in setup["files"].items():
        core.need(
            core.describe(core.ROOT / "environment" / name) == expected,
            "Prepared file changed: " + name,
        )
    for name, pin in setup["source_pins"].items():
        core.clean_head(core.ROOT / "sources" / name, pin)
    core.published_equality(core.ROOT / "sources/inferencex")
    layout = core.module("layout.py", "_r7_layout_check")
    observed = layout.resources(core.LayoutBase, core.ROOT / "sources/flashinfer")
    core.need(
        observed == core.read(core.ROOT / "environment/resource-layout.json"),
        "Fresh FI layout differs",
    )
    core.verify_reuse(lock)
    core.native_guard(lock)
    current = core.cmd([core.PYTHON, "-I", "-B", "-m", "pip", "freeze"])
    core.need(
        current == (core.ROOT / "environment/freeze-before.txt").read_text().strip(),
        "Global packages changed since preparation",
    )
    return setup


def owner_record(child):
    return {
        "pid": child.proc.pid,
        "label": child.label,
        "birth": child.birth,
        "known": child.known,
        "at": core.now(),
    }


def launch(lock, lock_path):
    setup_guard(lock, lock_path)
    guard = core.host_guard(lock)
    launchroot = core.ROOT / "launcher"
    launchroot.mkdir()  # one exclusive launch claim, never retried
    core.write(
        launchroot / "intent.json",
        {"lock": core.describe(lock_path), "guard": guard, "at": core.now()},
    )
    persist = Ledger(launchroot, "owner", campaign=True)
    registry = Registry(persist, history_limit=CAMPAIGN_HISTORY)
    argv = [
        core.PYTHON,
        "-B",
        str(core.HERE / "cli.py"),
        "worker",
        "--lock",
        str(lock_path),
        "--lock-sha",
        core.describe(lock_path)["sha256"],
    ]
    with (launchroot / "worker.log").open("xb") as log:
        try:
            child = registry.spawn(
                argv,
                env=core.clean_parent(lock),
                output=log,
                label="campaign-worker",
                new_session=True,
            )
            value = {
                "at": core.now(),
                "argv": argv,
                "owner": owner_record(child),
                "lock": core.describe(lock_path),
            }
            core.write(launchroot / "dispatch.json", value)
            return value
        except BaseException as error:
            core.write(
                launchroot / "launch-failure.json",
                {"error": repr(error), "cleanup": registry.cleanup(), "at": core.now()},
            )
            raise


def matrix_receipt(lock):
    reuse = core.verify_reuse(lock)
    points = []
    for case in campaign.producer.matrix():
        path = core.ROOT / "joins" / Path(case["case"] + ".json")
        join = core.read(path)
        core.need(
            join["status"] == "SEALED_CASE_EVIDENCE_JOIN_NOT_BASE_AUDIT"
            and join["case"] == case["case"]
            and join["run_id"] == core.RUN,
            "Missing finalized join",
        )
        core.need(
            join["measured_requests"] == case["requests"]
            and join["recipe_commit"] == lock["publication"]["commit"],
            "Join protocol mismatch",
        )
        for name, desc in join["raw14"].items():
            core.need(
                core.describe(core.ROOT / "results" / core.RUN / case["case"] / name)
                == desc,
                "Final raw changed",
            )
        import final_join

        core.need(
            final_join.native_manifest(
                core.ROOT / "native-runtime" / core.RUN / case["case"], lock["selected"]
            )
            == join["native"],
            "Final native changed",
        )
        points.append(
            {
                "case": case["case"],
                "join": core.describe(path),
                "requests": case["requests"],
            }
        )
    expected = {c["case"] for c in campaign.producer.matrix()}
    core.need(
        {
            str(p.parent.relative_to(core.ROOT / "results" / core.RUN))
            for p in (core.ROOT / "results" / core.RUN).rglob("status.json")
        }
        == expected,
        "Unexpected raw coordinate",
    )
    return {
        "status": "PRODUCER_COMPLETE_NOT_INDEPENDENT_AUDIT",
        "run_id": core.RUN,
        "cases": points,
        "completed_cases": 14,
        "measured_requests": 7640,
        "reused": reuse,
        "numerical_and_calibration_acceptance_pending": True,
    }


def archive(lock, code):
    # Archive only after owned cleanup and eight-idle; never inspect active cache.
    guard = core.module("guard.py", "_r7_archive_guard")
    guard.ROOT=core.OLD
    idle = guard.idle(lock["runtime_guard"])
    core.write(core.ROOT / "launcher/archive-idle.json", idle)
    old = core.module("archive.py", "_r7_archive_private")
    old.idle = lambda: idle
    old.full_matrix = lambda run, commit, run_id: matrix_receipt(lock)
    original = old.seal_tar

    def seal(path, entries):
        if str(path).endswith("-raw.tar.gz"):
            for relative in ("native-runtime", "joins", "launcher"):
                source = core.ROOT / relative
                if source.exists():
                    entries.append((source, core.RUN + "-" + relative))
        return original(path, entries)

    old.seal_tar = seal
    return old.archive_run(
        core.ROOT,
        {"run_id": core.RUN, "recipe_commit": lock["publication"]["commit"]},
        code,
    )


def worker(lock, lock_path):
    root = core.ROOT / "launcher"
    core.write(
        root / "worker-start.json", {"owner": proc_info(os.getpid()), "at": core.now()}
    )
    terminal = {
        "status": "CAMPAIGN_FAILED",
        "exit_code": 1,
        "error": None,
        "cleanup": [],
        "archive": None,
        "started_at": core.now(),
    }
    persist = Ledger(root, "campaign-owner", campaign=True)
    registry = Registry(persist, history_limit=CAMPAIGN_HISTORY)
    child = None
    code = 1

    def interrupt(sig, frame):
        raise KeyboardInterrupt("Worker interrupted " + str(sig))

    previous = {s: signal.signal(s, interrupt) for s in (signal.SIGINT, signal.SIGTERM)}
    try:
        setup_guard(lock, lock_path)
        core.write(root / "worker-guard.json", core.host_guard(lock))
        campaign.prepare_native_parents(str(core.ROOT))
        env = campaign.campaign_environment(
            core.clean_parent(lock),
            task_root=str(core.ROOT),
            recipe_root=str(core.ROOT / "sources/inferencex"),
            model_path=lock["model_path"],
            helper_root=str(core.HERE),
            activation_path=str(lock_path),
        )
        env["R7_EXECUTION_LOCK_SHA256"] = core.describe(lock_path)["sha256"]
        env["R7_CAMPAIGN_WORKER_PID"] = str(os.getpid())
        wrapper = (
            core.recipe_files(core.ROOT / "sources/inferencex")
            / "run_megamoe_recovery7.sh"
        )
        with (root / "campaign.log").open("xb") as log:
            child = registry.spawn(
                ["bash", str(wrapper)],
                env=env,
                output=log,
                label="campaign",
                new_session=True,
            )
            while child.proc.poll() is None:
                registry.refresh()
                time.sleep(0.25)
            code = child.proc.returncode
    except BaseException as error:
        terminal["error"] = repr(error)
    finally:
        for sig in previous:
            signal.signal(sig, signal.SIG_IGN)
        # Give the shell/case supervisor a chance to run its own finally first.
        if child is not None and child.proc.poll() is None:
            try:
                child.signal_owned(signal.SIGINT)
                child.proc.wait(timeout=70)
            except BaseException as error:
                terminal["orderly_stop_error"] = repr(error)
        terminal["cleanup"] = registry.cleanup()
        terminal["owner_ledger"] = persist.summary()
        try:
            terminal["owner_ledger_verified"] = persist.verify()
        except BaseException as error:
            terminal["owner_ledger_error"] = repr(error)
            code = 1
        if terminal["error"] is not None or any(
            x.get("cleanup_pending", True) for x in terminal["cleanup"]
        ):
            code = 1
        core.write(
            core.ROOT / "results" / f"{core.RUN}-benchmark-exit.json",
            {"exit_code": code, "finished_at": core.now()},
        )
        try:
            terminal["archive"] = archive(lock, code)
        except BaseException as error:
            terminal["archive_error"] = repr(error)
            code = 1
        terminal.update(
            status="CAMPAIGN_COMPLETED_PENDING_INDEPENDENT_AUDIT"
            if code == 0
            else "CAMPAIGN_FAILED",
            exit_code=code,
            finished_at=core.now(),
        )
        core.write(root / "worker-exit.json", terminal)
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    return code
