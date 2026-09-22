#!/usr/bin/env python3
"""Explicit local-on-owned-node actions. No transport or implicit binding."""

import argparse
import json
import os
import sys
import uuid
import core

sys.path.insert(0, str(core.HERE / "frozen_campaign"))
import campaign
import lifecycle
from owner_ledger import PosixIO


def check_worker():
    pid = int(os.environ.get("R8_CAMPAIGN_WORKER_PID", "0"))
    record = core.read(core.ROOT / "launcher/worker-start.json")["owner"]
    core.need(
        pid == record["pid"]
        and lifecycle.proc_info(pid)["starttime"] == record["starttime"],
        "Missing live owned campaign worker",
    )
    # The current shell/case must actually descend from that birth-bound worker.
    here = os.getpid()
    seen = set()
    while here not in seen and here > 1 and here != pid:
        seen.add(here)
        here = lifecycle.proc_info(here)["ppid"]
    core.need(here == pid, "Caller not a campaign descendant")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "action",
        nargs="?",
        default="plan",
        choices=(
            "plan",
            "prepare",
            "launch",
            "worker",
            "check-execution",
            "case",
            "join",
        ),
    )
    ap.add_argument("--lock")
    ap.add_argument("--lock-sha")
    ap.add_argument("--case")
    a = ap.parse_args()
    if a.action == "plan":
        print(
            json.dumps(
                {
                    "status": "EXPLICIT_BINDING_REQUIRED",
                    "run_id": core.RUN,
                    "root": str(core.ROOT),
                    "actions": ["prepare", "launch"],
                    "activation_template": "activation.template.json",
                    "remaining": campaign.producer.matrix(),
                    "source_or_package_change": False,
                },
                indent=2,
            )
        )
        return 0
    core.need(a.lock and a.lock_sha, "Explicit SHA-bound lock required")
    lock = core.load_lock(a.lock, a.lock_sha)
    if a.action == "prepare":
        core.prepare(lock, a.lock)
        return 0
    if a.action == "launch":
        print(json.dumps(lifecycle.launch(lock, a.lock)))
        return 0
    if a.action == "worker":
        return lifecycle.worker(lock, a.lock)
    check_worker()
    if a.action == "check-execution":
        lifecycle.setup_guard(lock, a.lock)
        return 0
    if a.action == "join":
        import final_join

        core.need(a.case is not None, "Missing case")
        final_join.create_join(lock, a.case)
        return 0
    lifecycle.setup_guard(lock, a.lock)
    # Case inputs come from the unchanged original shell, then validated again by
    # frozen make_spec. Selected native env is injected into only the actual setsid child.
    env = dict(os.environ)
    binding = dict(
        lock["native_binding"],
        runtime_seal_sha256=core.describe(
            core.ROOT / "environment/setup-completed.json"
        )["sha256"],
    )
    return campaign.run_bound_case(
        env, lock["selected"], binding, nonce=str(uuid.uuid4()), io_factory=PosixIO
    )


if __name__ == "__main__":
    raise SystemExit(main())
