"""Synthetic compact-table arithmetic and actual three-frontier rendering checks."""

import argparse
import copy
import json
from pathlib import Path

import render
import results
import run as recipe


def fixture():
    rows = []
    for case in recipe.matrix():
        n = case["measured_requests"]
        rows.append(
            {
                **case,
                "completed": n,
                "measured_spec_covered": n,
                "measured_spec_verify_ct": 100 * n,
                "measured_spec_correct_drafts": 300 * n,
                "measured_spec_proposed_drafts": 500 * n,
                "output_tokens": 400 * n,
                "duration_s": 4 * case["concurrency"],
                "median_tpot_ms": 100.0,
                "output_tok_s": 1000.0,
                "output_tok_s_gpu": 125.0,
                "interactivity_tok_s_user": 10.0,
                "measured_acceptance_length": 4.0,
                "measured_acceptance_rate": 0.6,
                "sglang_commit": "1" * 40,
                "flashinfer_commit": "2" * 40,
                "prompt_format": "DeepSeek-V4.1 chat; reasoning_effort=None",
            }
        )
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = fixture()
    render.validate_table(rows)
    bad = copy.deepcopy(rows)
    bad[0]["measured_acceptance_length"] = 3.0
    try:
        render.validate_table(bad)
    except ValueError:
        pass
    else:
        raise AssertionError("False compact AL accepted")
    args.output.mkdir(parents=True, exist_ok=False)
    results.plot(rows, args.output, topology=8)
    points = json.loads((args.output / "plot-points.json").read_text())
    assert len(points) == 18 and all(
        p["measured_acceptance_length"] == 4.0 for p in points
    )
    groups = json.loads((args.output / "frontiers.json").read_text())
    assert len(groups) == 3 and all(g["tp"] == 8 for g in groups)
    assert (args.output / "pareto.png").read_bytes().startswith(b"\x89PNG")
    svg = (args.output / "pareto.svg").read_text()
    assert svg.count("AL=4.00") == 18
    (args.output / "FIXTURE_ONLY.json").write_text(
        json.dumps({"actual_benchmark": False, "points": 18, "AL": 4.0, "rate": 0.6})
        + "\n"
    )
    print(
        "PASS: synthetic18 table, incorrect-AL rejection, actual PNG/SVG/point metadata"
    )


if __name__ == "__main__":
    main()
