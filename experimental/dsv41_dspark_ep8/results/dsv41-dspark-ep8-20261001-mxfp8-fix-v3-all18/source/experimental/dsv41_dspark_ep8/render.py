#!/usr/bin/env python3
"""Replay the compact measured table only; this is not a raw-evidence validator."""

import argparse
import json
import math
from pathlib import Path
import re

import results
import run as recipe


def validate_table(rows):
    expected = {c["case_id"]: c for c in recipe.matrix()}
    if not isinstance(rows, list) or len(rows) != len(expected):
        raise ValueError("The compact DSpark table requires all 18 points")
    seen = set()
    for row in rows:
        case = expected.get(row["case_id"])
        if case is None or row["case_id"] in seen:
            raise ValueError("Unknown or duplicate point")
        seen.add(row["case_id"])
        for key in (
            "arm_id",
            "precision",
            "tp",
            "ep",
            "dp",
            "concurrency",
            "moe_runner_backend",
            "moe_a2a_backend",
        ):
            if row[key] != case[key]:
                raise ValueError("Point identity differs: " + key)
        count = case["measured_requests"]
        if row["completed"] != count or row["measured_spec_covered"] != count:
            raise ValueError("Incomplete measured coverage")
        for key in (
            "output_tokens",
            "measured_spec_verify_ct",
            "measured_spec_proposed_drafts",
        ):
            if type(row[key]) is not int or row[key] <= 0:
                raise ValueError("Invalid native integer: " + key)
        correct = row["measured_spec_correct_drafts"]
        if (
            type(correct) is not int
            or not 0 <= correct <= row["measured_spec_proposed_drafts"]
        ):
            raise ValueError("Invalid correct-draft count")
        if row["measured_spec_proposed_drafts"] != 5 * row["measured_spec_verify_ct"]:
            raise ValueError("Wrong configured proposal budget")
        duration = results.finite(row["duration_s"], "duration", True)
        tpot = results.finite(row["median_tpot_ms"], "median TPOT", True)
        expected_values = {
            "output_tok_s": row["output_tokens"] / duration,
            "output_tok_s_gpu": row["output_tokens"] / duration / 8,
            "interactivity_tok_s_user": 1000 / tpot,
            "measured_acceptance_length": row["output_tokens"]
            / row["measured_spec_verify_ct"],
            "measured_acceptance_rate": correct / row["measured_spec_proposed_drafts"],
        }
        for key, value in expected_values.items():
            if not math.isclose(
                results.finite(row[key], key), value, rel_tol=1e-9, abs_tol=1e-12
            ):
                raise ValueError("Compact arithmetic differs: " + key)
        for key in ("sglang_commit", "flashinfer_commit"):
            if not re.fullmatch(r"[0-9a-f]{40}", row[key]):
                raise ValueError("Missing exact source commit")
        if (
            "flashinfer_wheel_commit" in row
            or row.get("flashinfer_python_patch") is not None
        ):
            if not re.fullmatch(
                r"[0-9a-f]{40}", row.get("flashinfer_wheel_commit", "")
            ):
                raise ValueError("Missing exact wheel-provider commit")
            if row.get("flashinfer_python_patch") is None:
                if row["flashinfer_wheel_commit"] != row["flashinfer_commit"]:
                    raise ValueError(
                        "Different FI commits require the reviewed patch descriptor"
                    )
            else:
                recipe.flashinfer_patch_spec(row)
        if row["prompt_format"] != "DeepSeek-V4.1 chat; reasoning_effort=None":
            raise ValueError("Unexpected prompt format")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = validate_table(results.read(args.table))
    args.output.mkdir(parents=True, exist_ok=False)
    results.plot(rows, args.output, topology=8)
    (args.output / "REPLAY.json").write_text(
        json.dumps(
            {
                "status": "COMPACT_TABLE_REPLAYED",
                "points": len(rows),
                "table": recipe.digest(args.table),
                "scope": "Table arithmetic and plot only; original raw/native/terminal acceptance is separate",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
