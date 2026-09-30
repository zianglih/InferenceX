#!/usr/bin/env python3
"""Read an accepted complete Kimi campaign and render three EP8 frontiers.

This does not accept a draft plan as a measurement. See RESULTS_CONTRACT.md for
the future collection/acceptance adapter contract. No GPU/runtime imports occur.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math

import checkpoint_contract
import source_contract
from decimal import Decimal, localcontext
from pathlib import Path, PurePosixPath


ARMS = {
    "megamoe-w4a4": ("MegaMoE W4A4", "#009E73"),
    "megamoe-w4a16": ("MegaMoE W4A16", "#E69F00"),
    "trtllm-w4a4": ("TRTLLM per-tensor NVFP4 W4A4", "#0072B2"),
}
CS = (4, 8, 16, 32)
CLIENT_COMMIT = "652ac186d88ebcd6ff995afbe7c3094751f0f4a2"
CLIENT_SOURCE_SHA256 = (
    "e853beb13182526044a5388f897f0d21a248c273c140152de3b8baa089165f36"
)
LATENCIES = tuple(
    f"{stat}_{kind}_ms"
    for kind in ("ttft", "tpot", "itl", "e2el")
    for stat in ("mean", "median", "std", "p90", "p99", "p99.9")
)
DERIVED = (
    "output_tokens_per_second",
    "output_tokens_per_second_per_gpu",
    "interactivity_tokens_per_second_per_user",
    "request_throughput",
)
CASE_CHECKS = (
    "request_plan",
    "actual_client_argv",
    "workload_settings",
    "source_runtime",
    "native_backend",
    "owned_postbenchmark_cleanup",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def bad(value):
        raise ValueError(f"Non-finite JSON constant: {value}")

    return json.loads(path.read_bytes(), object_pairs_hook=pairs, parse_constant=bad)


def safe_path(root, relative):
    require(isinstance(relative, str), "Path must be a string")
    rel = PurePosixPath(relative)
    require(
        relative
        and not rel.is_absolute()
        and ".." not in rel.parts
        and str(rel) == relative,
        f"Unsafe relative path: {relative}",
    )
    current = root
    for part in rel.parts:
        current = current / part
        require(not current.is_symlink(), f"Symlink is not accepted: {current}")
    require(current.is_file(), f"Missing regular file: {current}")
    return current


class Evidence:
    def __init__(self, root):
        self.root = root.resolve(strict=True)
        self.bindings = {}

    def bound(self, desc):
        require(
            isinstance(desc, dict) and set(desc) == {"path", "bytes", "sha256"},
            "Descriptor must contain exactly path, bytes, sha256",
        )
        require(type(desc["bytes"]) is int and desc["bytes"] >= 0, "Invalid byte count")
        require(
            isinstance(desc["sha256"], str) and len(desc["sha256"]) == 64,
            "Invalid SHA256",
        )
        p = safe_path(self.root, desc["path"])
        data = p.read_bytes()
        require(
            len(data) == desc["bytes"] and digest(data) == desc["sha256"],
            f"Changed bytes: {desc['path']}",
        )
        old = self.bindings.setdefault(desc["path"], desc)
        require(old == desc, f"Conflicting binding: {desc['path']}")
        return p

    def document(self, desc):
        return read_json(self.bound(desc))


def number(value, name, *, positive=False):
    require(
        type(value) in (int, float) and math.isfinite(value), f"Invalid numeric {name}"
    )
    require(value > 0 if positive else value >= 0, f"Out-of-range {name}")
    return Decimal(str(value))


def close(saved, expected, name):
    actual = number(saved, name)
    require(
        abs(actual - expected)
        <= max(Decimal("1e-9"), abs(expected) * Decimal("1e-10")),
        f"Inconsistent derived scalar {name}",
    )


def options(argv):
    require(
        isinstance(argv, list) and all(isinstance(v, str) for v in argv), "Invalid argv"
    )
    result = {}
    i = 0
    while i < len(argv):
        key = argv[i]
        if key.startswith("--"):
            require(
                key not in result and "=" not in key, f"Duplicate/inline option {key}"
            )
            value = True
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                i += 1
                value = argv[i]
            result[key] = value
        i += 1
    return result


def validate_plan(campaign, plan):
    require(plan["pins"] == campaign["pins"], "Plan/campaign source pins differ")
    require(
        plan.get("local_changes", {}) == campaign.get("local_changes", {}),
        "Plan/campaign local changes differ",
    )
    require(campaign["workload"]["speculation"] == "none", "NOSPEC required")
    expected = {
        "input_length": 1024,
        "output_length": 8192,
        "range_ratio": 0.8,
        "prefix_length": 0,
        "seed": 0,
        "warmup_multiplier": 2,
        "measure_multiplier": 10,
        "ignore_eos": True,
        "use_chat_template": True,
        "stream_interval": 30,
        "intended_cases": 12,
        "warmup_requests": 360,
        "measured_requests": 1800,
    }
    require(
        all(campaign["workload"].get(k) == v for k, v in expected.items()),
        "Changed workload contract",
    )
    require(campaign["workload"]["concurrencies"] == list(CS), "Changed C grid")
    require([a["id"] for a in campaign["arms"]] == list(ARMS), "Changed arm order")
    for arm in campaign["arms"]:
        require(arm["color"] == ARMS[arm["id"]][1], "Changed precision color")
    checkpoint_contract.validate_checkpoint(
        campaign["checkpoint"], campaign["runtime"]["model_path"]
    )
    require(campaign["pins"]["client_inferencex"] == CLIENT_COMMIT, "Wrong client pin")
    cases = plan["cases"]
    require(len(cases) == 12, "Complete 12-case plan required")
    keys = [(c["arm_id"], c["concurrency"]) for c in cases]
    require(
        set(keys) == set(itertools.product(ARMS, CS)) and len(set(keys)) == 12,
        "Duplicate or missing arm/C point",
    )
    for case in cases:
        c = case["concurrency"]
        require(
            case["case_id"] == f"{case['arm_id']}-tp8-ep8-dp1-c{c}", "Case identity"
        )
        require([case[k] for k in ("tp", "ep", "dp")] == [8, 8, 1], "Wrong topology")
        require(
            case["warmup_requests"] == 2 * c and case["measured_requests"] == 10 * c,
            "Wrong request count",
        )
        require(
            case["server_max_running_requests"] == c
            and case["decode_graph_max_bs"] == max(c, 8),
            "Capacity/graph rule changed",
        )
        args = options(case["client_argv"])
        for key, value in {
            "--dataset-name": "random",
            "--num-warmups": str(2 * c),
            "--num-prompts": str(10 * c),
            "--max-concurrency": str(c),
            "--random-input-len": "1024",
            "--random-output-len": "8192",
            "--random-range-ratio": "0.8",
            "--seed": "0",
            "--ignore-eos": True,
            "--use-chat-template": True,
            "--save-result": True,
            "--percentile-metrics": "ttft,tpot,itl,e2el",
            "--metric-percentiles": "90,99,99.9",
        }.items():
            require(args.get(key) == value, f"Client option differs: {key}")
        require(args.get("--request-rate") == "inf", "Infinite offered rate required")
        require(
            not any("speculative" in a for a in case["server_argv"]), "Unexpected draft"
        )
        require(
            not any("SIMULATE_ACC" in k for k in case["environment"]),
            "Simulated acceptance",
        )
    return cases


def verify_review(evidence, desc, status, *, target_key, target_sha):
    review = evidence.document(desc)
    require(review["status"] == status, f"Unaccepted review: {desc['path']}")
    require(review[target_key] == target_sha, "Review/target SHA mismatch")
    require(
        isinstance(review.get("bindings"), list) and review["bindings"],
        "Review must retain its supporting evidence bindings",
    )
    for bound in review["bindings"]:
        evidence.bound(bound)
    return review


def verify_local_changes(evidence, campaign):
    source_contract.check_campaign(campaign)
    changes = campaign.get("local_changes", {})
    require(
        isinstance(changes, dict) and set(changes) <= {"sglang"}, "Local change scope"
    )
    if not changes:
        require(
            "sglang_local_patch" not in campaign["pins"],
            "Patch pin lacks declared bytes",
        )
        return
    change = changes["sglang"]
    require(
        set(change) == {"base_commit", "patch", "files"}
        and change["base_commit"] == campaign["pins"]["sglang"],
        "Patch base/schema",
    )
    patch = change["patch"]
    require(
        campaign["pins"].get("sglang_local_patch") == patch["sha256"],
        "Patch pin mismatch",
    )
    require(
        PurePosixPath(patch["path"]).is_relative_to("artifacts"), "Patch path scope"
    )
    evidence.bound(patch)
    require(
        isinstance(change["files"], dict) and change["files"],
        "Changed source bytes required",
    )
    for relative, desc in change["files"].items():
        require(
            PurePosixPath(relative).is_relative_to("sglang"),
            "Changed source path scope",
        )
        require(
            isinstance(desc, dict) and set(desc) == {"bytes", "sha256"},
            "Changed source descriptor",
        )
        evidence.bound({"path": relative, **desc})


def verify_result(result, requested, case):
    c = case["concurrency"]
    count = 10 * c
    require(
        all(
            type(result[k]) is int
            for k in (
                "num_prompts",
                "completed",
                "max_concurrency",
                "total_input_tokens",
                "total_output_tokens",
            )
        ),
        "Counts/totals must be integers",
    )
    require(
        result["num_prompts"] == count and result["completed"] == count,
        "Incomplete request result",
    )
    require(result["max_concurrency"] == c, "Result concurrency mismatch")
    require(
        result["benchmark_outcome"]
        == {
            "status": "passed",
            "requested": count,
            "completed": count,
            "failed": 0,
            "max_failure_rate": 0.05,
        },
        "Require zero failures, stronger than the client's five-percent gate",
    )
    require(result["request_rate"] == "inf", "Wrong offered request rate")
    require(
        result["burstiness"] == 1 and result["best_of"] == 1, "Traffic/sampling changed"
    )
    args = options(case["client_argv"])
    require(
        result["backend"] == args["--backend"]
        and result["model_id"] == args["--model"],
        "Result backend/model differs from the accepted command",
    )
    require(
        result["tokenizer_id"] == args.get("--tokenizer", args["--model"]),
        "Result tokenizer differs from the accepted command",
    )
    for name, high, low in (("input_lens", 1024, 1), ("output_lens", 8192, 6553)):
        values = result[name]
        require(
            isinstance(values, list)
            and len(values) == count
            and all(type(v) is int and low <= v <= high for v in values),
            f"Invalid {name}",
        )
        require(
            values == requested[name], f"Ordered requested/completed {name} mismatch"
        )
    require(
        sum(result["input_lens"]) == result["total_input_tokens"], "Input sum mismatch"
    )
    require(
        sum(result["output_lens"]) == result["total_output_tokens"],
        "Output sum mismatch",
    )
    if "errors" in result:
        require(
            len(result["errors"]) == count and not any(result["errors"]), "Saved errors"
        )
    for key in LATENCIES:
        number(result[key], key, positive=key == "median_tpot_ms")
    for kind in ("ttft", "tpot", "itl", "e2el"):
        require(
            result[f"median_{kind}_ms"]
            <= result[f"p90_{kind}_ms"]
            <= result[f"p99_{kind}_ms"]
            <= result[f"p99.9_{kind}_ms"],
            f"Percentiles out of order: {kind}",
        )
    duration = number(result["duration"], "duration", positive=True)
    start = number(result["benchmark_start_time_unix"], "start", positive=True)
    end = number(result["benchmark_end_time_unix"], "end", positive=True)
    require(end > start, "Invalid wall-clock interval")
    # perf_counter duration is authoritative; Unix endpoints are separate calls.
    with localcontext() as ctx:
        ctx.prec = 50
        total = Decimal(result["total_output_tokens"]) / duration
        request_rate = Decimal(count) / duration
        close(result["output_throughput"], total, "output_throughput")
        close(result["request_throughput"], request_rate, "request_throughput")
        close(
            result["total_token_throughput"],
            Decimal(result["total_input_tokens"] + result["total_output_tokens"])
            / duration,
            "total_token_throughput",
        )
        derived = {
            "output_tokens_per_second": str(total),
            "output_tokens_per_second_per_gpu": str(total / 8),
            "interactivity_tokens_per_second_per_user": str(
                Decimal(1000) / Decimal(str(result["median_tpot_ms"]))
            ),
            "request_throughput": str(request_rate),
        }
    return derived


def load(root, acceptance="ACCEPTANCE.json", *, allow_synthetic=False):
    evidence = Evidence(Path(root))
    p = safe_path(evidence.root, acceptance)
    raw = p.read_bytes()
    evidence.bound({"path": acceptance, "bytes": len(raw), "sha256": digest(raw)})
    accepted = read_json(p)
    require(
        accepted["schema_version"] == 1
        and accepted["status"] == "ACCEPTED_COMPLETE_CAMPAIGN",
        "Complete acceptance required",
    )
    kind = accepted["data_kind"]
    require(
        kind == "actual" or (allow_synthetic and kind == "synthetic_test_only"),
        "CLI accepts actual evidence only; synthetic fixtures cannot be published",
    )
    campaign = evidence.document(accepted["campaign"])
    plan = evidence.document(accepted["plan"])
    require(
        plan["campaign"]["sha256"] == accepted["campaign"]["sha256"],
        "Plan/campaign mismatch",
    )
    cases = validate_plan(campaign, plan)
    verify_local_changes(evidence, campaign)
    require(
        "checkpoint_acceptance" in accepted, "Custom conversion acceptance is required"
    )
    checkpoint_contract.verify_acceptance(
        campaign["checkpoint"],
        accepted["checkpoint_acceptance"],
        evidence,
        allow_synthetic=allow_synthetic,
    )
    source = evidence.document(accepted["client_source"])
    require(
        accepted["client_source"]["sha256"] == CLIENT_SOURCE_SHA256,
        "Client package manifest differs from pin",
    )
    require(
        source["commit"] == CLIENT_COMMIT and source["files"], "Client source missing"
    )
    vendor = PurePosixPath(accepted["client_source"]["path"]).parent
    for rel, metadata in source["files"].items():
        evidence.bound({"path": str(vendor / rel), **metadata})
    terminal = evidence.document(accepted["terminal"])
    case_ids = [c["case_id"] for c in cases]
    require(
        terminal
        == {
            "status": "completed",
            "waited_returncode": 0,
            "error": None,
            "cleanup_errors": [],
            "remaining_owners": [],
            "completed_case_ids": case_ids,
        },
        "Terminal must record complete ordered cases and actual clean waited exit",
    )
    verify_review(
        evidence,
        accepted["terminal_review"],
        "PASS_ACTUAL_TERMINAL_REVIEW",
        target_key="terminal_sha256",
        target_sha=accepted["terminal"]["sha256"],
    )
    records = accepted["cases"]
    require(
        len(records) == 12 and [r["case_id"] for r in records] == case_ids,
        "Complete ordered acceptance list required",
    )
    rows, raw_results, lengths = [], {}, {}
    for case, record in zip(cases, records, strict=True):
        cid = case["case_id"]
        manifest = evidence.document(record["manifest"])
        require(
            manifest["case_id"] == cid and isinstance(manifest["files"], list),
            "Manifest identity/format",
        )
        files = {}
        parent = PurePosixPath(record["manifest"]["path"]).parent
        seen = set()
        for desc in manifest["files"]:
            rel = PurePosixPath(desc["path"])
            require(
                rel.is_relative_to(parent) and rel != parent and str(rel) not in seen,
                "Manifest scope/duplicate",
            )
            seen.add(str(rel))
            path = evidence.bound(desc)
            if rel.parent == parent:
                files[rel.name] = path
        require(
            {"result.json", "requested-lengths.json", "benchmark.log"} <= files.keys(),
            "Required case bytes absent",
        )
        review = verify_review(
            evidence,
            record["review"],
            "PASS_ACTUAL_CASE_REVIEW",
            target_key="manifest_sha256",
            target_sha=record["manifest"]["sha256"],
        )
        require(
            review["case_id"] == cid
            and review["warmup_requests"] == case["warmup_requests"]
            and all(review["checks"].get(k) is True for k in CASE_CHECKS),
            "Case review incomplete",
        )
        log = files["benchmark.log"].read_text(errors="strict")
        warmup = f"Warming up with {case['warmup_requests']} requests..."
        require(
            log.count(warmup) == 1
            and log.count("Warmup completed.") == 1
            and log.index(warmup) < log.index("Warmup completed."),
            "Warmup evidence missing",
        )
        result = read_json(files["result.json"])
        requested = read_json(files["requested-lengths.json"])
        require(
            kind != "actual"
            or (
                not result.get("SYNTHETIC_TEST_ONLY")
                and not review.get("SYNTHETIC_TEST_ONLY")
            ),
            "Synthetic-marked evidence cannot be relabeled actual",
        )
        axes = verify_result(result, requested, case)
        rows.append(
            {
                "case_id": cid,
                "arm_id": case["arm_id"],
                "concurrency": case["concurrency"],
                "tp": 8,
                "ep": 8,
                "dp": 1,
                "attention_tp": 8,
                "server_max_running_requests": case["server_max_running_requests"],
                "decode_graph_max_bs": case["decode_graph_max_bs"],
                "mega_local_decode_bound": (case["concurrency"] + 7) // 8
                if case["arm_id"].startswith("megamoe")
                else None,
                "mega_local_prefill_bound": 4096
                if case["arm_id"].startswith("megamoe")
                else None,
                "warmup_requests": case["warmup_requests"],
                "measured_requests": case["measured_requests"],
                "derived": axes,
            }
        )
        raw_results[cid], lengths[cid] = result, requested
    # Match the precise ordered workload across all three arms, not only sums.
    for c in CS:
        group = [r for r in rows if r["concurrency"] == c]
        for row in group[1:]:
            require(
                all(
                    lengths[row["case_id"]][k] == lengths[group[0]["case_id"]][k]
                    for k in ("input_lens", "output_lens")
                ),
                f"Cross-arm requested arrays differ at C{c}",
            )
        for field in (
            "backend",
            "model_id",
            "tokenizer_id",
            "best_of",
            "request_rate",
            "burstiness",
        ):
            require(
                len({str(raw_results[r["case_id"]][field]) for r in group}) == 1,
                f"Cross-arm result metadata differs: {field}",
            )
    return {
        "data_kind": kind,
        "rows": rows,
        "raw_results": raw_results,
        "requested_lengths": lengths,
        "bindings": list(evidence.bindings.values()),
        "campaign": campaign,
        "plan": plan,
    }


def frontier(rows):
    def xy(r):
        return tuple(
            Decimal(r["derived"][k])
            for k in (
                "interactivity_tokens_per_second_per_user",
                "output_tokens_per_second_per_gpu",
            )
        )

    selected = []
    for row in rows:
        x, y = xy(row)
        if not any(
            (xx >= x and yy >= y and (xx > x or yy > y))
            for other in rows
            if other is not row
            for xx, yy in [xy(other)]
        ):
            selected.append(row)
    return sorted(selected, key=xy)


def comparisons(data):
    pairs = []
    for c in CS:
        group = {r["arm_id"]: r for r in data["rows"] if r["concurrency"] == c}
        for baseline, candidate in itertools.combinations(ARMS, 2):
            a, b = group[baseline], group[candidate]
            metrics = {}
            with localcontext() as ctx:
                ctx.prec = 50
                for key in LATENCIES + DERIVED:
                    av = (
                        Decimal(str(data["raw_results"][a["case_id"]][key]))
                        if key in LATENCIES
                        else Decimal(a["derived"][key])
                    )
                    bv = (
                        Decimal(str(data["raw_results"][b["case_id"]][key]))
                        if key in LATENCIES
                        else Decimal(b["derived"][key])
                    )
                    metrics[key] = {
                        "baseline": str(av),
                        "candidate": str(bv),
                        "candidate_over_baseline_minus_one_pct": str(
                            (bv / av - 1) * 100
                        )
                        if av
                        else None,
                    }
            pairs.append(
                {
                    "concurrency": c,
                    "baseline": baseline,
                    "candidate": candidate,
                    "metrics": metrics,
                }
            )
    return pairs


def plot(rows, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 8), constrained_layout=True)
    for arm, (label, color) in ARMS.items():
        points = [r for r in rows if r["arm_id"] == arm]
        edge = frontier(points)

        def x(r):
            return float(r["derived"]["interactivity_tokens_per_second_per_user"])

        def y(r):
            return float(r["derived"]["output_tokens_per_second_per_gpu"])

        ax.scatter(
            [x(r) for r in points],
            [y(r) for r in points],
            color=color,
            marker="o",
            s=50,
        )
        ax.plot(
            [x(r) for r in edge],
            [y(r) for r in edge],
            color=color,
            marker="o",
            linestyle="-",
            label=f"{label}; TP8/EP8/DP1",
        )
        offset = {
            "megamoe-w4a4": (6, 8),
            "megamoe-w4a16": (6, -15),
            "trtllm-w4a4": (-6, 18),
        }[arm]
        for row in points:
            ax.annotate(
                f"C{row['concurrency']} · TP8/EP8/DP1",
                (x(row), y(row)),
                xytext=offset,
                textcoords="offset points",
                fontsize=8,
                ha="right" if offset[0] < 0 else "left",
                color=color,
            )
    ax.set_title(
        "Kimi K3 NVFP4 · 1k input / 8k output · concurrency 4–32\nThree EP8 frontiers · no speculative decoding"
    )
    ax.set_xlabel("Interactivity (tokens/s/user) = 1000 / median TPOT (ms)")
    ax.set_ylabel("Whole-interval output throughput (tokens/s/GPU)")
    ax.grid(alpha=0.2)
    ax.margins(x=0.18, y=0.13)
    ax.legend(loc="best")
    fig.text(
        0.5,
        -0.025,
        "8 B300 GPUs · 12 accepted points · 1,800 measured requests · whole interval is not timed decode",
        ha="center",
        fontsize=9,
    )
    for suffix in ("png", "svg"):
        fig.savefig(output / f"pareto.{suffix}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def publish(data, output):
    require(
        data["data_kind"] == "actual",
        "Synthetic test data cannot be rendered/published",
    )
    output = Path(output)
    output.mkdir(parents=False, exist_ok=False)
    write_json(output / "RESULTS.json", data)
    raw = data["raw_results"]
    # Retain every saved scalar, including the client's literal request_goodput: key.
    scalar_keys = sorted(
        {
            k
            for result in raw.values()
            for k, v in result.items()
            if v is None or isinstance(v, (str, int, float, bool))
        }
    )
    with (output / "RAW_METRICS.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["case_id", "arm_id", "concurrency"]
            + scalar_keys
            + list(DERIVED[:3]),
        )
        writer.writeheader()
        for row in data["rows"]:
            result = raw[row["case_id"]]
            writer.writerow(
                {
                    "case_id": row["case_id"],
                    "arm_id": row["arm_id"],
                    "concurrency": row["concurrency"],
                    **{k: result.get(k) for k in scalar_keys},
                    **{k: row["derived"][k] for k in DERIVED[:3]},
                }
            )
    write_json(output / "ORDERED_LENGTHS.json", data["requested_lengths"])
    write_json(output / "COMPARISONS.json", comparisons(data))
    write_json(
        output / "FRONTIERS.json",
        {
            arm: [
                r["case_id"]
                for r in frontier([x for x in data["rows"] if x["arm_id"] == arm])
            ]
            for arm in ARMS
        },
    )
    plot(data["rows"], output)
    (output / "METHODS.md").write_text(
        "# Kimi K3 three-curve results\n\n"
        "All 12 case acceptances and the complete campaign terminal are bound in RESULTS.json. "
        "Each arm uses TP8/EP8/DP1 (attention TP8) and concurrency 4/8/16/32; 2C warmups precede 10C measured requests. "
        "All same-C requested and completed token-length arrays match exactly across arms. "
        "RAW_METRICS.csv preserves every saved scalar; RESULTS.json retains the complete original result objects.\n\n"
        "Throughput uses output tokens divided by the client's monotonic perf_counter duration and eight GPUs. "
        "Unix start/end timestamps are separate observations and do not replace that denominator. "
        "Interactivity is 1000 divided by the saved median TPOT in milliseconds. "
        "Lines connect nondominated points within each arm; all measured points remain visible. "
        "These are three separate frontiers, not one global frontier.\n\n"
        "The 12 same-C pair comparisons retain all 24 saved latency scalars plus four derived metrics. "
        "Signed differences are candidate/baseline minus one; zero baselines produce null. "
        "There are no reconstructed percentiles or significance estimates. "
        "Whole-interval throughput is not timed decode. ITL is stream-interval-30 chunk spacing, not TPOT. "
        "Sequential backend/tactic/compile history can differ; this does not isolate causal effects. "
        "Without saved per-request latency/text, independent percentile and content reconstruction is unavailable. "
        "Source/native/runtime and cleanup acceptance come from the separately bound reviews, not the plot.\n"
    )
    files = [
        {"path": p.name, "bytes": p.stat().st_size, "sha256": digest(p.read_bytes())}
        for p in sorted(output.iterdir())
        if p.is_file()
    ]
    write_json(output / "FILES.json", files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--acceptance", default="ACCEPTANCE.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = load(args.root, args.acceptance)
    publish(data, args.output)


if __name__ == "__main__":
    main()
