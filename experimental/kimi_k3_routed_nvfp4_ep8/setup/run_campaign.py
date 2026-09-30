#!/usr/bin/env python3
"""Render a pure local plan, or explicitly execute a root-approved runtime plan."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from plan import ROOT, build_plan, emit_plan


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--campaign", type=Path, default=ROOT / "campaign.json")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    ap.add_argument("--approval-marker", type=Path)
    ap.add_argument(
        "--approval-sha256", help="Exact SHA256 of root-accepted runtime marker"
    )
    ap.add_argument("--output", type=Path, help="Exclusive dry-plan directory only")
    ap.add_argument(
        "--runtime-project-root", default="/REVIEW_REQUIRED/kimi-k3-project"
    )
    args = ap.parse_args(argv)
    if (args.approval_marker or args.approval_sha256) and not args.execute:
        ap.error("Approval inputs require --execute")
    if args.execute and args.output:
        ap.error(
            "Execution output is the campaign's pinned run_root; --output is dry-plan only"
        )
    planned = build_plan(args.campaign, runtime_project=args.runtime_project_root)
    if args.execute:
        if (
            not args.approval_marker
            or not args.approval_sha256
            or planned["execution_blockers"]
        ):
            print(
                json.dumps(
                    {
                        "status": "EXECUTION_BLOCKED",
                        "execution_implemented": True,
                        "reasons": planned["execution_blockers"]
                        + (
                            ["Explicit accepted approval marker and SHA256 required"]
                            if not args.approval_marker or not args.approval_sha256
                            else []
                        ),
                    }
                ),
                file=sys.stderr,
            )
            return 2
        from execution import execute

        try:
            return execute(
                args.campaign, planned, args.approval_marker, args.approval_sha256
            )
        except Exception as exc:
            print(
                json.dumps(
                    {"status": "EXECUTION_REJECTED_OR_FAILED", "error": repr(exc)}
                ),
                file=sys.stderr,
            )
            return 1
    if args.output:
        receipt = emit_plan(planned, args.output)
        print(
            json.dumps(
                {
                    "status": receipt["status"],
                    "execution_implemented": True,
                    "executed": False,
                    "output": str(args.output),
                    "totals": planned["totals"],
                    "execution_totals": planned["execution_totals"],
                }
            )
        )
    else:
        print(json.dumps(planned, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
