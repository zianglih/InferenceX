#!/usr/bin/env python3
"""Validate and export compact measured results for the EP4/EP8 blog sweeps."""

import argparse
import csv
import hashlib
import itertools
import json
import math
import re
from pathlib import Path

CONCURRENCIES = (1, 2, 4, 8, 16, 32, 64)
ARMS = {
    "megamoe-w4a4": ("MegaMoE W4A4", "#009E73"),
    "megamoe-w4a16": ("MegaMoE W4A16", "#E69F00"),
    "trtllm-w4a4": ("TRTLLM NVFP4 W4A4", "#0072B2"),
}
MODELS = {
    "dsv41": ("DeepSeek-V4.1 Flash", "DSpark", 5),
    "glm52": ("GLM-5.2", "EAGLE / MTP", 3),
}
SCALARS = tuple(
    f"{stat}_{metric}_ms"
    for metric in ("ttft", "tpot", "e2el", "itl")
    for stat in ("mean", "median", "p90", "p99")
)
COUNTERS = (
    "requested",
    "completed",
    "failed",
    "warmup_requested",
    "warmup_completed",
    "warmup_failed",
    "input_tokens",
    "server_input_tokens",
    "output_tokens",
    "spec_completion_tokens",
    "spec_verify_ct",
    "spec_correct_drafts",
    "spec_proposed_drafts",
    "spec_covered",
    "spec_requested",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def number(value, name: str, positive: bool = False) -> float:
    require(type(value) in (int, float) and math.isfinite(value), f"Invalid {name}")
    require(value > 0 if positive else value >= 0, f"Invalid {name}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def gpu_count(topology: dict) -> int:
    count = topology["tp"]
    require(
        type(count) is int
        and count in (4, 8)
        and all(
            type(topology[key]) is int and topology[key] == count
            for key in ("ep", "dp")
        ),
        "Expected TP=EP=attention DP of 4 or 8",
    )
    return count


def validate_campaign(campaign: dict, model_id: str) -> None:
    require(campaign["schema_version"] == 1, "Unsupported campaign schema")
    for key in ("sglang_commit", "flashinfer_commit", "benchmark_commit"):
        require(
            bool(re.fullmatch(r"[0-9a-f]{40}", campaign[key])), f"Missing exact {key}"
        )
    require(
        bool(campaign["run_id"]) and bool(campaign["image"]),
        "Missing run/image identity",
    )
    checkpoint = campaign["models"][model_id]
    require(bool(checkpoint["checkpoint_path"]), "Missing checkpoint path")
    require(bool(checkpoint["checkpoint_revision"]), "Missing checkpoint revision")
    require(bool(checkpoint["prompt_format"]), "Missing prompt-format identity")
    matrix = campaign["matrix"]
    gpu_count(matrix)
    require(
        tuple(matrix["concurrencies"]) == CONCURRENCIES, "Unexpected concurrency matrix"
    )
    require(set(matrix["arms"]) == set(ARMS) and len(matrix["arms"]) == 3, "Wrong arms")
    expected_workload = {
        "input_len": 1024,
        "output_len": 8192,
        "range_ratio": 0.8,
        "seed": 0,
        "warmup_multiplier": 2,
        "measured_multiplier": 10,
        "stream_interval": 30,
    }
    require(
        all(
            campaign["workload"][key] == value
            for key, value in expected_workload.items()
        ),
        "Unexpected workload",
    )


def validate_case(row: dict, model_id: str) -> dict:
    """Validate a measured row; derived values are checked before being normalized."""
    require(model_id in MODELS and row["model_id"] == model_id, "Unexpected model")
    require(row["arm_id"] in ARMS, "Unexpected backend")
    c = row["concurrency"]
    require(type(c) is int and c in CONCURRENCIES, "Unexpected concurrency")
    gpus = gpu_count(row)
    for key in COUNTERS:
        require(
            type(row[key]) is int and row[key] >= 0, f"Invalid integer counter: {key}"
        )
    require(
        row["requested"] == row["completed"] == 10 * c and row["failed"] == 0,
        "Incomplete or failed measured requests",
    )
    require(
        row["warmup_requested"] == row["warmup_completed"] == 2 * c
        and row["warmup_failed"] == 0,
        "Incomplete or failed warmup requests",
    )
    require(
        row["spec_requested"] == row["spec_covered"] == row["completed"],
        "Incomplete measured speculative counters",
    )
    require(
        row["output_tokens"] == row["spec_completion_tokens"] > 0,
        "Speculative completion total differs from measured output",
    )
    require(
        row["input_tokens"] > 0
        and row["server_input_tokens"] > 0
        and row["spec_verify_ct"] > 0,
        "Missing positive token/verification total",
    )
    require(
        row["spec_proposed_drafts"] == MODELS[model_id][2] * row["spec_verify_ct"],
        "Unexpected configured proposal budget",
    )
    require(
        row["spec_correct_drafts"] <= row["spec_proposed_drafts"],
        "Accepted drafts exceed proposed drafts",
    )
    duration = number(row["duration_s"], "measured interval", True)
    for key in SCALARS:
        number(row[key], key, positive=(key == "median_tpot_ms"))
    require(
        bool(re.fullmatch(r"[0-9a-f]{64}", row["request_plan_sha256"])),
        "Missing ordered request-plan digest",
    )
    require(
        bool(re.fullmatch(r"[0-9a-f]{64}", row["ordered_lengths_sha256"])),
        "Missing ordered input/output/server-input length digest",
    )
    require(
        isinstance(row["prompt_format"], str) and bool(row["prompt_format"]),
        "Missing prompt format",
    )
    derived = {
        "output_tok_s": row["output_tokens"] / duration,
        "output_tok_s_gpu": row["output_tokens"] / duration / gpus,
        "interactivity_tok_s_user": 1000 / row["median_tpot_ms"],
        "acceptance_length": row["spec_completion_tokens"] / row["spec_verify_ct"],
        "acceptance_rate": row["spec_correct_drafts"] / row["spec_proposed_drafts"],
    }
    for key, expected in derived.items():
        if key in row:
            require(
                math.isclose(
                    number(row[key], key), expected, rel_tol=1e-9, abs_tol=1e-12
                ),
                f"Derived metric disagrees with measured counters: {key}",
            )
    return {**row, **derived}


def validate_table(table: dict) -> list[dict]:
    require(table["schema_version"] == 1, "Unsupported results schema")
    model_id = table["model_id"]
    require(model_id in MODELS, "Unexpected model")
    campaign = table["campaign"]
    validate_campaign(campaign, model_id)
    rows = [validate_case(row, model_id) for row in table["rows"]]
    keys = [(row["arm_id"], row["concurrency"]) for row in rows]
    expected = set(itertools.product(ARMS, CONCURRENCIES))
    require(
        len(keys) == len(expected) and set(keys) == expected,
        "Expected all 21 distinct model/backend/concurrency points",
    )
    for row in rows:
        require(
            row["tp"] == campaign["matrix"]["tp"],
            "Case topology differs from campaign",
        )
        require(
            row["prompt_format"] == campaign["models"][model_id]["prompt_format"],
            "Prompt format differs from campaign",
        )
    for c in CONCURRENCIES:
        require(
            len({row["request_plan_sha256"] for row in rows if row["concurrency"] == c})
            == 1,
            f"The three C{c} arms used different ordered request plans",
        )
        require(
            len(
                {
                    row["ordered_lengths_sha256"]
                    for row in rows
                    if row["concurrency"] == c
                }
            )
            == 1,
            f"The three C{c} arms have different ordered token lengths",
        )
        for key in ("input_tokens", "output_tokens", "server_input_tokens"):
            require(
                len({row[key] for row in rows if row["concurrency"] == c}) == 1,
                f"The three C{c} arms have different {key}",
            )
    return sorted(
        rows, key=lambda row: (list(ARMS).index(row["arm_id"]), row["concurrency"])
    )


def collect(root: Path, model_id: str) -> dict:
    campaign = json.loads((root / "campaign.json").read_text())
    rows = []
    for arm, c in itertools.product(ARMS, CONCURRENCIES):
        path = root / model_id / f"{arm}-c{c}" / "case.json"
        row = json.loads(path.read_text())
        require(
            (row["arm_id"], row["concurrency"]) == (arm, c),
            f"Case path mismatch: {path}",
        )
        rows.append({**row, "case_sha256": sha256(path)})
    table = {
        "schema_version": 1,
        "model_id": model_id,
        "campaign": campaign,
        "rows": rows,
    }
    table["rows"] = validate_table(table)
    return table


def frontier(rows: list[dict]) -> list[dict]:
    """Maximize both metrics; equal points do not dominate one another."""
    x, y = "interactivity_tok_s_user", "output_tok_s_gpu"
    return sorted(
        [
            p
            for p in rows
            if not any(
                q[x] >= p[x] and q[y] >= p[y] and (q[x] > p[x] or q[y] > p[y])
                for q in rows
            )
        ],
        key=lambda row: (row[x], row["concurrency"]),
    )


def comparisons(rows: list[dict]) -> list[dict]:
    indexed = {(row["arm_id"], row["concurrency"]): row for row in rows}
    pairs = (
        ("megamoe-w4a16", "megamoe-w4a4"),
        ("megamoe-w4a16", "trtllm-w4a4"),
        ("megamoe-w4a4", "trtllm-w4a4"),
    )
    output = []
    for candidate, baseline in pairs:
        for c in CONCURRENCIES:
            a, b = indexed[candidate, c], indexed[baseline, c]
            output.append(
                {
                    "concurrency": c,
                    "candidate": candidate,
                    "baseline": baseline,
                    "throughput_change_pct": 100
                    * (a["output_tok_s_gpu"] / b["output_tok_s_gpu"] - 1),
                    "median_tpot_change_pct": 100
                    * (a["median_tpot_ms"] / b["median_tpot_ms"] - 1),
                    "acceptance_length_change": a["acceptance_length"]
                    - b["acceptance_length"],
                    "acceptance_length_change_pct": 100
                    * (a["acceptance_length"] / b["acceptance_length"] - 1),
                }
            )
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def export(table: dict, output: Path) -> None:
    rows = validate_table(table)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "metrics.json", {**table, "rows": rows})
    write_csv(output / "metrics.csv", rows)
    write_csv(output / "comparisons.csv", comparisons(rows))
    model, algorithm, _ = MODELS[table["model_id"]]
    gpus = gpu_count(table["campaign"]["matrix"])
    note = [
        f"# {model}: {algorithm}, EP{gpus}, concurrency 1-64",
        "",
        (
            f"{len(rows)} measured points; {sum(r['completed'] for r in rows):,} successful measured "
            f"requests; zero measured failures. {sum(r['warmup_completed'] for r in rows):,} "
            "successful warmup requests are excluded."
        ),
        "",
        "| Backend | C | Output tokens/s/GPU | Median TPOT (ms) | AL | Acceptance rate |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    note.extend(
        f"| {ARMS[r['arm_id']][0]} | {r['concurrency']} | {r['output_tok_s_gpu']:.3f} | "
        f"{r['median_tpot_ms']:.4f} | {r['acceptance_length']:.4f} | {r['acceptance_rate']:.4f} |"
        for r in rows
    )
    note.extend(
        [
            "",
            (
                "AL is the measured completion-token sum divided by the verification-count sum, "
                "including native bonus tokens. Acceptance rate uses correct/proposed draft totals. "
                "The compact table retains those exact integer totals and coverage counts."
            ),
            "",
            (
                "Throughput includes the whole measured interval. Interactivity is 1,000 / saved median "
                "TPOT. Saved ITL is chunk spacing at stream interval 30. All signed backend comparisons "
                "are retained in comparisons.csv; a single sweep does not establish statistical significance "
                "or output quality. W4A16 also affects eligible NVFP4 dense linears."
            ),
            "",
            (
                "The plots use only this fresh campaign. Full logs and per-request records remain in "
                "cluster persistent storage; public replay validates compact arithmetic and plotting."
            ),
        ]
    )
    (output / "RESULTS.md").write_text("\n".join(note) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--model", choices=MODELS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    table = collect(args.run, args.model)
    export(table, args.output)
    print(
        json.dumps(
            {
                "model": args.model,
                "points": len(table["rows"]),
                "output": str(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
