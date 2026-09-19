#!/usr/bin/env python3
"""Summarize preserved GLM-5.2 fixed-sequence artifacts without pooling runs."""

from __future__ import annotations

import argparse
import json
import math
import os
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any

BACKENDS = {
    "w4a4_trtllm": "W4A4 TRT-LLM",
    "w4a16_megamoe": "W4A16 MegaMoE",
}
SCENARIOS = {"1k1k": (1024, 1024), "8k1k": (8192, 1024)}
LATENCY_KEYS = [
    f"{percentile}_{metric}_ms"
    for metric in ("ttft", "tpot")
    for percentile in ("median", "p90", "p99")
]
GROUP_KEYS = (
    "run_id",
    "scenario",
    "backend",
    "hardware",
    "tp",
    "dp",
    "ep",
    "gpu_count",
    "model",
    "model_revision",
    "image",
    "sglang_commit",
    "prefill_cuda_graph_policy",
    "random_range_ratio",
    "isl",
    "osl",
)


def number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def read_case(path: Path) -> dict[str, Any]:
    """Keep every case, with a strict zero-failure gate for plotted points."""
    row: dict[str, Any] = {
        "metadata_file": str(path.resolve()),
        "case": str(path.parent.resolve()),
        "included": False,
        "exclusion_reasons": [],
        "metrics": {},
        "observed_token_lengths": {},
        "derived": {},
    }
    reasons = row["exclusion_reasons"]
    try:
        metadata = json.loads(path.read_text())
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a JSON object")
        row["metadata"] = metadata
        for key in GROUP_KEYS + ("concurrency", "num_prompts"):
            row[key] = metadata.get(key)
        if metadata.get("backend") not in BACKENDS:
            reasons.append("unknown backend")
        row["backend_label"] = BACKENDS.get(metadata.get("backend"), "Unknown backend")
        for key in (
            "tp",
            "dp",
            "ep",
            "gpu_count",
            "concurrency",
            "num_prompts",
            "isl",
            "osl",
        ):
            if type(metadata.get(key)) is not int or metadata[key] <= 0:
                reasons.append(f"{key} must be a positive integer")
        for key in ("run_id", "hardware", "model", "image", "sglang_commit"):
            if not metadata.get(key):
                reasons.append(f"missing {key}")
        if metadata.get("status") != "completed":
            reasons.append(f"case status is {metadata.get('status')!r}")
        if SCENARIOS.get(metadata.get("scenario")) != (
            metadata.get("isl"),
            metadata.get("osl"),
        ):
            reasons.append("case scenario and lengths must match 1k1k or 8k1k")
        if "B300" not in str(metadata.get("hardware")):
            reasons.append("hardware is not identified as B300")
        result_path = path.parent / metadata["benchmark_result"]
        row["result_file"] = str(result_path.resolve())
        result = json.loads(result_path.read_text())
        if not isinstance(result, dict):
            raise ValueError("benchmark result must be a JSON object")
        row["metrics"] = {
            key: value
            for key, value in result.items()
            if number(value)
            and key not in ("num_prompts", "max_concurrency", "best_of")
        }
        row["completed"] = result.get("completed")
        for key in ("input_lens", "output_lens"):
            values = result.get(key)
            if (
                isinstance(values, list)
                and values
                and all(number(value) for value in values)
            ):
                row["observed_token_lengths"][key] = {
                    "count": len(values),
                    "min": min(values),
                    "mean": sum(values) / len(values),
                    "max": max(values),
                }
        expected = metadata.get("num_prompts")
        completed = result.get("completed")
        if type(expected) is int and type(completed) is int:
            row["failed"] = expected - completed
        if type(completed) is not int or completed != expected:
            reasons.append(f"completed={completed!r}, expected={expected!r}")
        if result.get("num_prompts") != expected:
            reasons.append("result num_prompts differs from metadata")
        if result.get("max_concurrency") != metadata.get("concurrency"):
            reasons.append("result max_concurrency differs from metadata")
        if any(result.get("errors", [])):
            reasons.append("benchmark result contains request errors")
        outcome = result.get("benchmark_outcome", {})
        if not isinstance(outcome, dict) or (
            outcome and outcome.get("status") != "passed"
        ):
            reasons.append("benchmark_outcome did not pass")
        for key in ("output_throughput", "total_token_throughput", "duration"):
            value = result.get(key)
            if not number(value) or value <= 0:
                reasons.append(f"invalid or missing {key}")
        if not reasons:
            row["included"] = True
            row["derived"] = {
                "output_throughput_per_gpu": result["output_throughput"]
                / metadata["gpu_count"],
                "total_token_throughput_per_gpu": (
                    result["total_token_throughput"] / metadata["gpu_count"]
                ),
            }
            median_tpot = result.get("median_tpot_ms")
            if number(median_tpot) and median_tpot > 0:
                row["derived"]["interactivity_from_median_tpot_tok_s"] = (
                    1000 / median_tpot
                )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        reasons.append(f"cannot read case: {exc}")
    return row


def fmt(value: Any) -> str:
    return f"{value:,.3f}" if number(value) else "—"


def cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def topology(row: dict[str, Any]) -> str:
    return f"TP{row.get('tp')}/DP{row.get('dp')}/EP{row.get('ep')} ({row.get('gpu_count')} GPUs)"


def link(path: str, output: Path, label: str) -> str:
    return f"[{label}](<{os.path.relpath(path, output)}>)"


def write_markdown(rows: list[dict[str, Any]], output: Path, charts: list[str]) -> None:
    included = sorted(
        (row for row in rows if row["included"]),
        key=lambda row: (
            row["scenario"],
            row["tp"],
            row["dp"],
            row["ep"],
            row["backend"],
            row["run_id"],
            row["image"],
            row["sglang_commit"],
            row["concurrency"],
        ),
    )
    lines = [
        "# GLM-5.2 B300 / 1k1k and 8k1k / MTP",
        "",
        f"Included cases: **{len(included)}/{len(rows)} discovered metadata files**. "
        "Only completed cases with every requested benchmark request successful are plotted. "
        "Discovered failed, missing-result, and still-running cases remain in `summary.json` and "
        "the exclusions below. Cases without metadata are not counted; this count does not establish "
        "completion of the planned matrix.",
        "",
        "Measurements are closed-loop synthetic request-rate=inf runs. "
        "Each point is one case, without cross-run averaging or a latency-SLO gate. "
        "1k1k sets input/output caps to 1024/1024 tokens; 8k1k sets them to 8192/1024 tokens. "
        "Lengths are sampled using each case's `random_range_ratio`, not fixed to these caps. "
        "The sampler draws inclusive integer lengths from floor(ratio × cap) to cap; "
        "for chat-template input it first subtracts template overhead, then applies the template "
        "and retokenizes. Raw `input_lens` and `output_lens` retain observed request lengths. "
        "Workloads are plotted in separate figures. "
        "Different topology, GPU count, runtime, backend, or prefill CUDA graph policy configurations are separate series; "
        "comparisons are system configurations, not isolated kernel-precision speedups.",
        "",
        "`output_throughput` counts generated tokens; `total_token_throughput` counts input plus "
        "generated tokens. Both use the benchmark wall duration and are in tok/s. "
        "Per-GPU values divide by metadata `gpu_count` (the GPUs used by that server). "
        "Interactivity is `1000 / median_tpot_ms` in tok/s/user, excludes the first token, "
        "and is not the mean of individual request rates. Latencies retain the raw millisecond "
        "units and names; `median_*_ms` is P50. Missing percentiles are shown as —.",
        "",
        "| Case | Scenario | Backend | Topology | Concurrency | Completed / requested | "
        "output_throughput (tok/s) | total_token_throughput (tok/s) | "
        "output_throughput_per_gpu (tok/s/GPU) | Interactivity (tok/s/user) |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for index, row in enumerate(included, 1):
        row["summary_case_id"] = f"C{index}"
        metric, derived = row["metrics"], row["derived"]
        lines.append(
            "| "
            + " | ".join(
                [
                    row["summary_case_id"],
                    row["scenario"],
                    row["backend_label"],
                    topology(row),
                    str(row["concurrency"]),
                    f"{row['completed']} / {row['num_prompts']}",
                    fmt(metric.get("output_throughput")),
                    fmt(metric.get("total_token_throughput")),
                    fmt(derived.get("output_throughput_per_gpu")),
                    fmt(derived.get("interactivity_from_median_tpot_tok_s")),
                ]
            )
            + " |"
        )
    lines += [
        "",
        "| Case | Scenario | " + " | ".join(LATENCY_KEYS) + " |",
        "|---|---|" + "---:|" * 6,
    ]
    for row in included:
        lines.append(
            "| "
            + row["summary_case_id"]
            + " | "
            + row["scenario"]
            + " | "
            + " | ".join(fmt(row["metrics"].get(key)) for key in LATENCY_KEYS)
            + " |"
        )
    lines += [
        "",
        "## Workload accounting",
        "",
        "| Case | Scenario | random_range_ratio | input_lens min / mean / max (tokens) | output_lens min / mean / max (tokens) |",
        "|---|---|---:|---:|---:|",
    ]
    for row in included:
        observed = row["observed_token_lengths"]
        lines.append(
            "| "
            + " | ".join(
                [
                    row["summary_case_id"],
                    row["scenario"],
                    fmt(row.get("random_range_ratio")),
                    *[
                        " / ".join(
                            fmt(observed.get(key, {}).get(stat))
                            for stat in ("min", "mean", "max")
                        )
                        for key in ("input_lens", "output_lens")
                    ],
                ]
            )
            + " |"
        )
    lines += [
        "",
        "## Provenance",
        "",
        "| Case | Run | Raw results and metadata | Model | Image | SGLang commit | Prefill CUDA graph policy |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in included:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["summary_case_id"],
                    cell(row["run_id"]),
                    link(row["result_file"], output, "raw")
                    + " / "
                    + link(row["metadata_file"], output, "metadata"),
                    cell(row["model"]),
                    cell(row["image"]),
                    cell(row["sglang_commit"]),
                    cell(row.get("prefill_cuda_graph_policy")),
                ]
            )
            + " |"
        )
    lines += [
        "",
        "Metadata retains model revision, installed package versions, and environment settings.",
        "",
        "## Excluded cases",
        "",
    ]
    excluded = [row for row in rows if not row["included"]]
    if excluded:
        lines += ["| Case metadata | Reasons |", "|---|---|"]
        for row in excluded:
            lines.append(
                f"| {link(row['metadata_file'], output, 'metadata')} | "
                f"{cell('; '.join(row['exclusion_reasons']))} |"
            )
    else:
        lines.append(
            "None among discovered cases. This does not prove that every planned case was launched."
        )
    for chart in charts:
        lines += [
            "",
            f"![{chart.replace('_', ' ')}]({chart}.png)",
            "",
            f"[SVG]({chart}.svg)",
        ]
    lines += [
        "",
        "<details><summary>中文</summary>",
        "",
        "仅汇总已经写出 metadata.json 的实验；仅将全部请求成功的完成项纳入图表。"
        "失败、缺失结果和运行中的实验保留在 JSON 与排除列表中。输出吞吐只计算生成 token，"
        "总吞吐同时计算输入与生成 token。延迟保持毫秒单位；median 为 P50。"
        "交互性为 1000 / median_tpot_ms，不包含首个 token，也不代表满足某项延迟 SLO。"
        "1k1k 和 8k1k 表示配置的长度上限，实际长度按 random_range_ratio 采样，并非每个请求都等于上限。"
        "输入还包含聊天模板与重新分词的影响；表中列出实际输入和输出长度。"
        "两种负载分别绘图。不同拓扑、GPU 数量和运行环境分别展示，不能解释为单独改变内核精度的收益。"
        "汇总数量仅代表发现的 metadata 文件，不证明计划矩阵已完成。",
        "",
        "</details>",
        "",
    ]
    (output / "summary.md").write_text("\n".join(lines))


def plot_results(rows: list[dict[str, Any]], output: Path, scenario: str) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["included"] and row["scenario"] == scenario:
            groups[tuple(row.get(key) for key in GROUP_KEYS)].append(row)
    if not groups:
        return []
    plt.rcParams.update({"font.size": 10, "svg.fonttype": "none"})
    series = []
    for index, points in enumerate(groups.values()):
        points.sort(key=lambda row: row["concurrency"])
        first = points[0]
        label = (
            f"{first['backend_label']} · {topology(first)} · {first['run_id']}"
            f" · prefill graphs: {first.get('prefill_cuda_graph_policy') or 'unknown'}"
            f" · length ratio: {first.get('random_range_ratio')}"
        )
        series.append((points, label, plt.get_cmap("tab10")(index % 10)))
    names = []

    def save(fig: Any, name: str) -> None:
        name = f"{scenario}_{name}"
        labels = [textwrap.fill(label, width=115) for _, label, _ in series]
        legend_height = 0.20 * sum(label.count("\n") + 1 for label in labels) + 0.25
        width, height = fig.get_size_inches()
        fig.set_size_inches(width, height + legend_height)
        margin = (legend_height + 0.45) / (height + legend_height)
        isl, osl = SCENARIOS[scenario]
        fig.suptitle(
            f"GLM-5.2 · B300 · {scenario} · input/output caps {isl}/{osl} tokens · MTP",
            fontsize=14,
        )
        fig.tight_layout(rect=(0, margin, 1, 0.94))
        fig.legend(
            [Line2D([], [], color=color, marker="o") for _, _, color in series],
            labels,
            loc="lower center",
            bbox_to_anchor=(0.5, 0.045),
            fontsize=8,
            frameon=False,
        )
        fig.text(
            0.5,
            0.01,
            "Successful cases only · one measurement per point · no latency-SLO filter",
            ha="center",
            fontsize=9,
        )
        for extension in ("png", "svg"):
            fig.savefig(output / f"{name}.{extension}", dpi=180, bbox_inches="tight")
        plt.close(fig)
        names.append(name)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for ax, field, unit in zip(
        axes,
        ("output_throughput", "total_token_throughput", "output_throughput_per_gpu"),
        ("tok/s", "tok/s", "tok/s/GPU"),
        strict=True,
    ):
        for points, label, color in series:
            ax.plot(
                [row["concurrency"] for row in points],
                [
                    row["metrics"].get(field, row["derived"].get(field))
                    for row in points
                ],
                "o-",
                label=label,
                color=color,
            )
        ax.set(
            xlabel="Concurrency (requests)",
            ylabel=f"{field}\n({unit})",
            xscale="log",
            ylim=(0, None),
        )
        ax.grid(alpha=0.2)
    ticks = sorted({row["concurrency"] for points, _, _ in series for row in points})
    for ax in axes:
        ax.set_xscale("log", base=2)
        ax.set_xticks(ticks, [str(tick) for tick in ticks])
    save(fig, "throughput_concurrency")

    fig, ax = plt.subplots(figsize=(10, 6))
    for points, label, color in series:
        points = [
            row
            for row in points
            if "interactivity_from_median_tpot_tok_s" in row["derived"]
        ]
        if not points:
            continue
        ax.plot(
            [row["derived"]["interactivity_from_median_tpot_tok_s"] for row in points],
            [row["derived"]["output_throughput_per_gpu"] for row in points],
            "o-",
            label=label,
            color=color,
        )
        for row in points:
            ax.annotate(
                f"c{row['concurrency']}",
                (
                    row["derived"]["interactivity_from_median_tpot_tok_s"],
                    row["derived"]["output_throughput_per_gpu"],
                ),
                xytext=(4, 5),
                textcoords="offset points",
                fontsize=8,
            )
    ax.set(
        xlabel="1000 / median_tpot_ms (tok/s/user)",
        ylabel="output_throughput_per_gpu (tok/s/GPU)",
        xlim=(0, None),
        ylim=(0, None),
    )
    ax.grid(alpha=0.2)
    save(fig, "throughput_interactivity")

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    for ax, metric in zip(axes, ("ttft", "tpot"), strict=True):
        for points, label, color in series:
            for percentile, style in (("median", "-"), ("p90", "--"), ("p99", ":")):
                field = f"{percentile}_{metric}_ms"
                present = [row for row in points if number(row["metrics"].get(field))]
                if present:
                    ax.plot(
                        [row["concurrency"] for row in present],
                        [row["metrics"][field] for row in present],
                        marker="o",
                        linestyle=style,
                        color=color,
                        label=f"{label} · {percentile}",
                    )
        ax.set(
            xlabel="Concurrency (requests)",
            ylabel=f"{metric.upper()} (ms)",
            xscale="log",
            ylim=(0, None),
        )
        ax.grid(alpha=0.2)
        ax.set_xscale("log", base=2)
        ax.set_xticks(ticks, [str(tick) for tick in ticks])
        ax.legend(
            [
                Line2D([], [], color="black", linestyle=style)
                for style in ("-", "--", ":")
            ],
            ["P50 (median)", "P90", "P99"],
            fontsize=8,
        )
    save(fig, "latency_concurrency")
    return names


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--results",
        type=Path,
        nargs="+",
        required=True,
        help="One or more run roots; recursively reads metadata.json",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Write JSON and Markdown without requiring matplotlib",
    )
    args = parser.parse_args()
    paths = sorted(
        {
            path.resolve()
            for root in args.results
            for path in root.rglob("metadata.json")
        }
    )
    if not paths:
        parser.error("no metadata.json files found; no measurements were summarized")
    rows = [read_case(path) for path in paths]
    args.output.mkdir(parents=True, exist_ok=True)
    charts = []
    if not args.no_plots:
        try:
            for scenario in SCENARIOS:
                charts.extend(plot_results(rows, args.output, scenario))
        except ModuleNotFoundError as exc:
            parser.error(
                f"plotting requires matplotlib ({exc}); use --no-plots for JSON and Markdown only"
            )
    write_markdown(rows, args.output, charts)
    for row in rows:
        for field in ("metadata_file", "result_file", "case"):
            if field in row:
                row[field] = os.path.relpath(row[field], args.output)
    summary = {
        "artifact_path_base": "directory containing summary.json; raw metadata paths retain original runtime provenance",
        "case_count": len(rows),
        "included_case_count": sum(row["included"] for row in rows),
        "excluded_case_count": sum(not row["included"] for row in rows),
        "scenarios": {
            scenario: {
                "isl": lengths[0],
                "osl": lengths[1],
                "case_count": sum(row.get("scenario") == scenario for row in rows),
                "included_case_count": sum(
                    row.get("scenario") == scenario and row["included"] for row in rows
                ),
            }
            for scenario, lengths in SCENARIOS.items()
        },
        "metric_units": {
            "duration": "s",
            "*_ms": "ms",
            "output_throughput": "tok/s",
            "total_token_throughput": "tok/s",
            "request_throughput": "requests/s",
            "output_throughput_per_gpu": "tok/s/GPU",
            "total_token_throughput_per_gpu": "tok/s/GPU",
            "interactivity_from_median_tpot_tok_s": "tok/s/user (1000 / median_tpot_ms)",
        },
        "cases": rows,
        "charts": charts,
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n"
    )
    print(
        f"Included {summary['included_case_count']}/{len(rows)} cases; summary: {args.output / 'summary.md'}"
    )


if __name__ == "__main__":
    main()
