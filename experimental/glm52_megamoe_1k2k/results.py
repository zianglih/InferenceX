#!/usr/bin/env python3
"""Verify terminal case bytes and render the four fresh MegaMoE frontiers."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def finite(value, name, positive=False):
    if (
        isinstance(value, bool)
        or not isinstance(value, (float, int))
        or not math.isfinite(value)
    ):
        raise ValueError(f"Invalid {name}: {value}")
    if positive and value <= 0:
        raise ValueError(f"Nonpositive {name}")
    return value


def verify_case(directory):
    manifest = read(directory / "manifest.json")
    files = manifest["files"]
    actual = set()
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Linked evidence: {path}")
        if path.is_file() and path != directory / "manifest.json":
            actual.add(path.relative_to(directory).as_posix())
    if actual != set(files):
        raise ValueError(f"Manifest members differ in {directory}")
    for name, desc in files.items():
        path = directory / name
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Nonlocal manifest member")
        if path.stat().st_size != desc["bytes"] or sha(path) != desc["sha256"]:
            raise ValueError(f"Changed raw evidence: {path}")
    terminal = read(directory / "exit.json")
    if (
        terminal["status"] != "completed"
        or terminal.get("error")
        or terminal.get("postflight_error")
    ):
        raise ValueError(f"Unsuccessful case: {directory}")
    for role in ("server", "benchmark"):
        cleanup = terminal["cleanup"][role]
        if cleanup.get("remaining") or cleanup.get("errors") or cleanup.get("error"):
            raise ValueError(f"Incomplete {role} cleanup")
    if terminal["cleanup"]["benchmark"]["waited_returncode"] != 0:
        raise ValueError("Benchmark client did not exit successfully")
    after_gpu = read(directory / "gpu.after.json")
    if (
        after_gpu["applications"]["returncode"]
        or after_gpu["applications"]["stdout"].strip()
    ):
        raise ValueError("Post-case GPUs not idle")
    settings = read(directory / "settings.json")
    case, config, env = settings["case"], settings["config"], settings["environment"]
    p, tp, c = case["precision"], case["tp"], case["concurrency"]
    if (
        p not in ("w4a4", "w4a16")
        or tp not in (4, 8)
        or c not in (4, 8, 16, 32, 64, 128)
    ):
        raise ValueError("Unexpected precision/topology/concurrency")
    if case["ep"] != tp or case["dp"] != tp or case["case_id"] != directory.name:
        raise ValueError("Topology/case identity differs")
    if (settings["nominal_input"], settings["nominal_output"], settings["ratio"]) != (
        1024,
        2048,
        0.8,
    ):
        raise ValueError("Wrong sampled workload")
    required_env = {
        "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16": str(int(p == "w4a16")),
        "NVSHMEM_REMOTE_TRANSPORT": "none",
        "NVSHMEM_IB_ENABLE_IBGDA": "0",
        "NVSHMEM_DISABLE_LOCAL_ONLY_PROXY": "1",
        "SGLANG_FLASHINFER_AUTOTUNE_CACHE": "1",
    }
    if any(env.get(k) != v for k, v in required_env.items()):
        raise ValueError("Precision/autotune/NVSHMEM environment differs")
    expected = {
        "tp_size": tp,
        "ep_size": tp,
        "dp_size": tp,
        "enable_dp_attention": True,
        "moe_runner_backend": "flashinfer_megamoe",
        "moe_a2a_backend": "flashinfer_megamoe",
        "speculative_moe_runner_backend": "flashinfer_trtllm",
        "speculative_moe_a2a_backend": "none",
        "speculative_algorithm": "EAGLE",
        "speculative_num_steps": 3,
        "speculative_eagle_topk": 1,
        "speculative_num_draft_tokens": 4,
        "kv_cache_dtype": "fp8_e4m3",
        "mem_fraction_static": 0.8,
        "cuda_graph_backend_prefill": "disabled",
        "chunked_prefill_size": 32768 // tp,
        "max_running_requests": max(c, tp),
        "model_path": config["model_path"],
    }
    for when in ("before", "after"):
        info = read(directory / f"server_info.{when}.json")
        mismatch = {k: info.get(k) for k, v in expected.items() if info.get(k) != v}
        if mismatch:
            raise ValueError(f"Resolved settings differ: {mismatch}")
    before, after = (
        read(directory / "source.before.json"),
        read(directory / "source.after.json"),
    )
    if before != after:
        raise ValueError("Sources/packages changed within a point")
    for name in ("sglang", "flashinfer"):
        source = before[name]
        if (
            source["head"]["returncode"]
            or source["diff"]["returncode"]
            or source["diff"]["stdout"].strip()
            or source["head"]["stdout"].strip() != config[name + "_commit"]
            or source["root"] != config[name + "_root"]
        ):
            raise ValueError(f"Recorded {name} source differs from declared pin")
    if before["freeze"]["returncode"] or not before["freeze"]["stdout"].strip():
        raise ValueError("Package freeze failed or is empty")
    log = (directory / "benchmark.log").read_text()
    namespaces = [line for line in log.splitlines() if line.startswith("Namespace(")]
    if len(namespaces) != 1 or not re.search(r"(?:\(|, )seed=0(?:,|\))", namespaces[0]):
        raise ValueError("Actual client did not record seed 0")
    if (
        f"Warming up with {2 * c} requests..." not in log
        or "Warmup completed." not in log
    ):
        raise ValueError("Full warmup was not recorded")
    result = read(directory / "result.json")
    if result["completed"] != 10 * c or result["num_prompts"] != 10 * c:
        raise ValueError("Measured success count differs")
    if result["max_concurrency"] != c or result["request_rate"] != "inf":
        raise ValueError("Traffic differs")
    if result.get("benchmark_outcome", {}).get("status") != "passed":
        raise ValueError("Client outcome is not passed")
    lengths = {}
    for field, total in (
        ("input_lens", "total_input_tokens"),
        ("output_lens", "total_output_tokens"),
    ):
        values = result[field]
        if len(values) != 10 * c or any(type(x) is not int or x <= 0 for x in values):
            raise ValueError(f"Invalid {field}")
        if sum(values) != result[total]:
            raise ValueError(f"Wrong {total}")
        lengths[field] = values
    rate = result["total_output_tokens"] / finite(result["duration"], "duration", True)
    if not math.isclose(
        finite(result["output_throughput"], "output_throughput", True),
        rate,
        rel_tol=1e-9,
    ):
        raise ValueError("Output throughput differs from tokens / full interval")
    tpot = finite(result["median_tpot_ms"], "median_tpot_ms", True)
    row = {
        "case_id": directory.name,
        "precision": p,
        "tp": tp,
        "ep": tp,
        "dp": tp,
        "concurrency": c,
        "completed": result["completed"],
        "duration_s": result["duration"],
        "input_tokens": result["total_input_tokens"],
        "output_tokens": result["total_output_tokens"],
        "output_tok_s": rate,
        "output_tok_s_gpu": rate / tp,
        "interactivity_tok_s_user": 1000 / tpot,
        "result_sha256": files["result.json"]["sha256"],
        "case_manifest_sha256": sha(directory / "manifest.json"),
        "sglang_commit": config["sglang_commit"],
        "flashinfer_commit": config["flashinfer_commit"],
        "image": config["image"],
    }
    for key, value in result.items():
        if key.endswith("_ms"):
            row[key] = finite(value, key)
    return row, lengths, before, config


def load(root, partial):
    expected = {
        (p, tp, c)
        for p in ("w4a4", "w4a16")
        for tp in (4, 8)
        for c in (4, 8, 16, 32, 64, 128)
    }
    rows, lengths, seen, baseline = [], {}, set(), None
    campaign_config = read(root / "config.json")
    for directory in sorted((root / "cases").iterdir()):
        if not directory.is_dir() or not (directory / "manifest.json").exists():
            if partial:
                continue
            raise ValueError(f"Unfinalized case: {directory}")
        row, arrays, source, config = verify_case(directory)
        if config != campaign_config:
            raise ValueError("Case config differs from campaign config")
        key = (row["precision"], row["tp"], row["concurrency"])
        if key not in expected or key in seen:
            raise ValueError("Unexpected/duplicate matrix point")
        seen.add(key)
        if baseline is not None and source != baseline:
            raise ValueError("Source/package/recipe differs across cases")
        baseline = source
        c = row["concurrency"]
        if c in lengths and arrays != lengths[c]:
            raise ValueError(f"Ordered request lengths differ at C{c}")
        lengths[c] = arrays
        rows.append(row)
    if not partial:
        terminal = read(root / "worker-exit.json")
        if (
            seen != expected
            or terminal["status"] != "completed"
            or terminal.get("error")
        ):
            raise ValueError("Full 24-point campaign incomplete")
        if set(terminal["completed"]) != {x["case_id"] for x in rows}:
            raise ValueError("Worker completed IDs differ")
        if sum(x["completed"] for x in rows) != 10080:
            raise ValueError("Full measured count differs")
    return rows


def frontier(rows):
    return sorted(
        (
            r
            for r in rows
            if not any(
                q["interactivity_tok_s_user"] >= r["interactivity_tok_s_user"]
                and q["output_tok_s_gpu"] >= r["output_tok_s_gpu"]
                and (
                    q["interactivity_tok_s_user"] > r["interactivity_tok_s_user"]
                    or q["output_tok_s_gpu"] > r["output_tok_s_gpu"]
                )
                for q in rows
            )
        ),
        key=lambda r: r["interactivity_tok_s_user"],
    )


def plot(rows, out):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 8), layout="constrained")
    styles = [
        ("w4a4", 4, "#0072B2", "o"),
        ("w4a16", 4, "#D55E00", "s"),
        ("w4a4", 8, "#009E73", "^"),
        ("w4a16", 8, "#CC79A7", "D"),
    ]
    for p, tp, color, marker in styles:
        group = [r for r in rows if r["precision"] == p and r["tp"] == tp]
        points = frontier(group)
        ax.scatter(
            [r["interactivity_tok_s_user"] for r in group],
            [r["output_tok_s_gpu"] for r in group],
            color=color,
            marker=marker,
            s=55,
        )
        ax.plot(
            [r["interactivity_tok_s_user"] for r in points],
            [r["output_tok_s_gpu"] for r in points],
            color=color,
            label=f"MegaMoE {p.upper()} · TP=DP=EP={tp}",
        )
        for r in group:
            ax.annotate(
                f"C{r['concurrency']}",
                (r["interactivity_tok_s_user"], r["output_tok_s_gpu"]),
                xytext=(6, 6 if p == "w4a4" else -13),
                textcoords="offset points",
                fontsize=9,
                color=color,
            )
    ax.set(
        xlabel="Interactivity = 1,000 / median TPOT (tokens/s/user)",
        ylabel="Whole-interval output throughput (tokens/s/GPU)",
        title="GLM-5.2 · nominal 1k input / 2k output · ratio 0.8 · B300",
    )
    ax.grid(alpha=0.2)
    ax.margins(0.14)
    ax.legend(loc="best")
    fig.supxlabel(
        "MTP BF16 TRTLLM / none · 3 / 1 / 4 · all points shown; lines connect nondominated points\n"
        f"SG {rows[0]['sglang_commit'][:12]} · FI {rows[0]['flashinfer_commit'][:12]} · shared compiled caches; fresh server per point",
        fontsize=9,
    )
    fig.savefig(out / "pareto.png", dpi=180)
    fig.savefig(out / "pareto.svg")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    rows = load(args.run_root, args.partial)
    if not rows:
        raise ValueError("No finalized measured points")
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "raw-metrics.json").write_text(
        json.dumps(rows, indent=2, allow_nan=False) + "\n"
    )
    keys = list(rows[0]) + sorted(set().union(*(set(r) for r in rows)) - set(rows[0]))
    with (args.output / "raw-metrics.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Fresh MegaMoE 1k/2k results / 全新 MegaMoE 1k/2k 结果",
        "",
        f"Verified finalized points / 已校验完成点数: {len(rows)}/24.",
        "",
        "Nominal lengths 1,024/2,048 with ratio 0.8 sampling; 2C warmup / 10C measured. "
        "Same-C ordered length arrays match across available arms. / 名义长度采用0.8比例采样，同并发的有序长度一致。",
        "",
        "Throughput covers the complete measured wall interval, not separately timed decode. "
        "MTP server-state averages include warmup; no global measured acceptance rate is inferred. "
        "/ 吞吐覆盖完整测量区间；MTP状态包含预热，不推算全局测量接受率。",
        "",
        "| Precision / 精度 | TP=DP=EP | C | Requests | Duration s | Output tok/s | Output tok/s/GPU | 1000/median TPOT |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['precision']} | {r['tp']} | {r['concurrency']} | {r['completed']} | "
            f"{r['duration_s']:.6f} | {r['output_tok_s']:.6f} | {r['output_tok_s_gpu']:.6f} | {r['interactivity_tok_s_user']:.6f} |"
        )
    lines += [
        "",
        "Complete saved scalar latency metrics, source pins and raw SHA bindings are in "
        "[raw-metrics.csv](raw-metrics.csv) and [raw-metrics.json](raw-metrics.json). "
        "/ 全部已保存延迟统计、提交与原始SHA见上述文件。",
        "",
    ]
    if not args.partial:
        plot(rows, args.output)
        lines += ["![Four fresh MegaMoE frontiers](pareto.png)", ""]
    (args.output / "RESULTS.md").write_text("\n".join(lines))
    print(
        json.dumps(
            {"points": len(rows), "partial": args.partial, "output": str(args.output)}
        )
    )


if __name__ == "__main__":
    main()
