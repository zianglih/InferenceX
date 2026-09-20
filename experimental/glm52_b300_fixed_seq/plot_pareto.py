#!/usr/bin/env python3
"""Plot unofficial measured runs using InferenceX's fixed-sequence metric semantics.

Source: SemiAnalysisAI/InferenceX-app@b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9.
See the generated pareto.md for pinned metric, frontier, and label references.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any

from summarize import GROUP_KEYS, SCENARIOS, cell, fmt, number, read_case

APP = "https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/"
PRODUCER = "https://github.com/SemiAnalysisAI/InferenceX/blob/8979f7c4cdd2946a02b459d5e62018e41bc02405/infx/results/fixed_sequence.py#L187-L207"
MODES = {
    "interactivity": ("median_intvty", "Per-request Interactivity (tok/s/user)", True),
    "e2el": ("median_e2el", "End-to-end Latency (s)", False),
}

# Like the website overlay series, pool topology choices within each arm/run.
SERIES_KEYS = tuple(
    key for key in GROUP_KEYS if key not in ("tp", "dp", "ep", "gpu_count")
) + ("parallel_topology",)


def global_frontier(points: list[dict], maximize_x: bool) -> list[dict]:
    """Select non-dominated coordinates, matching the website's global semantics."""
    unique = {(p["x"], p["y"]): p for p in reversed(points)}
    eligible = [
        p
        for (x, y), p in unique.items()
        if math.isfinite(x) and math.isfinite(y) and x > 0
    ]
    survivors = []
    for point in eligible:
        dominated = any(
            other["y"] >= point["y"]
            and (other["x"] >= point["x"] if maximize_x else other["x"] <= point["x"])
            and (other["x"], other["y"]) != (point["x"], point["y"])
            for other in eligible
        )
        if not dominated:
            survivors.append(point)
    return sorted(survivors, key=lambda p: p["x"])


def series_frontier(points: list[dict], maximize_x: bool) -> list[dict]:
    """Match the website's series eligibility, including its E2EL equal-y ties."""
    if maximize_x:
        return global_frontier(points, maximize_x=True)
    # The website's historical E2EL series keeps equal-y observations at
    # increasing x, although only the smallest x is globally non-dominated.
    unique = {(p["x"], p["y"]): p for p in reversed(points)}
    eligible = [
        p
        for (x, y), p in unique.items()
        if math.isfinite(x) and math.isfinite(y) and x > 0
    ]
    return sorted(
        (
            point
            for point in eligible
            if not any(
                other["x"] <= point["x"] and other["y"] > point["y"]
                for other in eligible
            )
        ),
        key=lambda p: p["x"],
    )


def point_from_case(row: dict[str, Any]) -> dict[str, Any]:
    metric = row["metrics"]
    for key in ("median_e2el_ms", "median_tpot_ms"):
        if not number(metric.get(key)) or metric[key] <= 0:
            raise ValueError(f"{row['case']}: missing positive {key}")
    return {
        "case_id": row["case_id"],
        "metadata_file": row["metadata_file"],
        "result_file": row["result_file"],
        **{key: row.get(key) for key in GROUP_KEYS},
        "backend_label": row["backend_label"],
        "concurrency": row["concurrency"],
        "completed": row["completed"],
        "num_prompts": row["num_prompts"],
        "parallel_topology": row["metadata"].get("parallel_topology"),
        "server_max_running_requests": row["metadata"].get(
            "server_max_running_requests"
        ),
        "median_e2el_ms": metric["median_e2el_ms"],
        "median_tpot_ms": metric["median_tpot_ms"],
        "median_e2el": metric["median_e2el_ms"] / 1000,
        "median_intvty": 1000 / metric["median_tpot_ms"],
        "output_throughput": metric["output_throughput"],
        "total_token_throughput": metric["total_token_throughput"],
        "output_tput_per_gpu": metric["output_throughput"] / row["gpu_count"],
    }


def validate_comparison(rows: list[dict], require_aligned: bool) -> None:
    """Keep historical DP1 controls out of the aligned comparison."""
    regimes = set()
    for row in rows:
        aligned = row["tp"] == row["dp"] == row["ep"]
        regimes.add("aligned" if aligned else "historical")
        if require_aligned:
            expected = {
                "parallel_topology": "dp-ep",
                "dp": row["tp"],
                "ep": row["tp"],
                "server_max_running_requests": max(row["concurrency"], row["tp"]),
                "prefill_cuda_graph_policy": "disabled",
                "mem_fraction_static": 0.80,
            }
            for key, value in expected.items():
                if row["metadata"].get(key) != value:
                    raise ValueError(
                        f"{row['case']}: aligned comparison requires {key}={value!r}"
                    )
    if len(regimes) > 1:
        raise ValueError(
            "Historical DP1/EP1 and TP=DP=EP cases must be plotted separately. "
            "Use only aligned run roots with --dp-attention-aligned for the main comparison; "
            "plot the historical baseline in a separate output directory."
        )


def annotate_points(fig: Any, ax: Any, points: list[dict]) -> None:
    """Place full topology labels near observations with nonoverlapping boxes."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.transforms import Bbox

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    occupied = []
    locations = [ax.transData.transform((p["x"], p["y"])) for p in points]
    obstacles = [Bbox.from_bounds(x - 14, y - 14, 28, 28) for x, y in locations]
    font = FontProperties(size=8)
    candidates = sorted(
        ((dx, dy) for dx in range(-180, 181, 30) for dy in range(-150, 151, 25)),
        key=lambda p: p[0] ** 2 + p[1] ** 2,
    )
    for point, (px, py) in zip(points, locations, strict=True):
        label = (
            f"C={point['concurrency']}\nTP{point['tp']}/DP{point['dp']}/EP{point['ep']}"
        )
        width = (
            max(
                renderer.get_text_width_height_descent(s, font, False)[0]
                for s in label.splitlines()
            )
            + 8
        )
        height = 2 * font.get_size_in_points() * fig.dpi / 72 * 1.2 + 8
        best = None
        for dx, dy in candidates:
            box = Bbox.from_bounds(
                px + dx - width / 2, py + dy - height / 2, width, height
            )
            if not (
                ax.bbox.x0 + 3 <= box.x0
                and box.x1 <= ax.bbox.x1 - 3
                and ax.bbox.y0 + 3 <= box.y0
                and box.y1 <= ax.bbox.y1 - 3
            ):
                continue
            overlap = 0.0
            for other in occupied + obstacles:
                intersection = Bbox.intersection(box, other)
                if intersection is not None:
                    overlap += intersection.width * intersection.height
            score = overlap * 10000 + dx * dx + dy * dy
            if best is None or score < best[0]:
                best = (score, dx, dy, box)
        if best is None:
            raise ValueError("No room for point label; increase the figure size")
        _, dx, dy, box = best
        occupied.append(box)
        ax.annotate(
            label,
            (point["x"], point["y"]),
            xytext=(dx * 72 / fig.dpi, dy * 72 / fig.dpi),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=8,
            color=point["color"],
            zorder=6,
            bbox={
                "boxstyle": "round,pad=0.18",
                "fc": "white",
                "ec": "none",
                "alpha": 0.88,
            },
            arrowprops={
                "arrowstyle": "-",
                "color": point["color"],
                "lw": 0.55,
                "alpha": 0.75,
            },
        )


def draw(points: list[dict], output: Path, scenario: str, mode: str) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    field, x_label, maximize_x = MODES[mode]
    projected = [{**p, "x": p[field], "y": p["output_tput_per_gpu"]} for p in points]
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for point in projected:
        groups[tuple(point[key] for key in SERIES_KEYS)].append(point)
    fig, ax = plt.subplots(figsize=(14, 10), dpi=160)
    fig.subplots_adjust(left=0.085, right=0.98, top=0.90, bottom=0.32)
    colors = {"w4a4_trtllm": "#1769aa", "w4a16_megamoe": "#d65f16"}
    legend = []
    series = []
    for values in groups.values():
        p = values[0]
        color = colors[p["backend"]]
        for point in values:
            point["color"] = color
        for tp in sorted({point["tp"] for point in values}):
            topology_points = [point for point in values if point["tp"] == tp]
            ax.scatter(
                [point["x"] for point in topology_points],
                [point["y"] for point in topology_points],
                s=49,
                color=color,
                marker="o" if tp == 4 else "D",
                zorder=4,
                edgecolors="white",
                linewidths=0.7,
            )
        front = series_frontier(values, maximize_x)
        ax.plot(
            [p["x"] for p in front],
            [p["y"] for p in front],
            color=color,
            lw=1.5,
            alpha=0.8,
            zorder=2,
        )
        label = (
            f"{p['backend_label']} · B300 · {p['run_id']}\n"
            f"FI {p.get('flashinfer_version') or '?'} @ {(p.get('flashinfer_commit') or 'image-provided')[:14]} · "
            f"CuTe {p.get('cute_dsl_version') or '?'} · prefill graphs: {p['prefill_cuda_graph_policy']}\n"
            f"Static memory fraction: {p.get('mem_fraction_static') or 'not recorded'}"
        )
        legend.append(Line2D([], [], color=color, lw=1.5, label=label))
        series.append(
            {
                "identity": {key: p[key] for key in SERIES_KEYS},
                "case_ids": [p["case_id"] for p in values],
                "frontier_case_ids": [p["case_id"] for p in front],
            }
        )
    front = global_frontier(projected, maximize_x)
    ax.plot(
        [p["x"] for p in front],
        [p["y"] for p in front],
        ":",
        color="#258347",
        lw=2,
        zorder=3,
    )
    ax.scatter(
        [p["x"] for p in front],
        [p["y"] for p in front],
        s=150,
        facecolors="none",
        edgecolors="#258347",
        lw=1.6,
        zorder=5,
    )
    legend.append(
        Line2D(
            [],
            [],
            color="#258347",
            ls=":",
            marker="o",
            markerfacecolor="none",
            markersize=9,
            label="Global Pareto frontier: observed vertices",
        )
    )
    for tp in sorted({p["tp"] for p in projected}):
        legend.append(
            Line2D(
                [],
                [],
                color="#666666",
                ls="none",
                marker="o" if tp == 4 else "D",
                label=f"TP{tp}; each point labels DP/EP and client C",
            )
        )
    ax.set_xlim(0, max(p["x"] for p in projected) * 1.12)
    ax.set_ylim(0, max(p["y"] for p in projected) * 1.14)
    ax.set_xlabel(
        x_label + ("  → higher is better" if maximize_x else "  ← lower is better"),
        fontsize=12,
    )
    ax.set_ylabel("Output Token Throughput per Chip (tok/s/chip)", fontsize=12)
    ax.grid(alpha=0.19)
    ax.set_axisbelow(True)
    fig.suptitle(
        f"GLM-5.2 NVFP4 + MTP · B300 · {scenario} · UNOFFICIAL",
        fontsize=17,
        fontweight="bold",
        y=0.98,
    )
    fig.text(
        0.085,
        0.927,
        f"InferenceX fixed-sequence metrics · {len(projected)} measured cases · single run per point",
        fontsize=11,
    )
    annotate_points(fig, ax, projected)
    fig.legend(
        handles=legend,
        loc="upper left",
        bbox_to_anchor=(0.079, 0.248),
        ncol=2,
        fontsize=8.5,
        frameon=False,
        handlelength=2.8,
        columnspacing=2,
    )
    ratios = ", ".join(
        str(v) for v in sorted({p["random_range_ratio"] for p in points})
    )
    fig.text(
        0.085,
        0.075,
        f"ISL/OSL caps: {SCENARIOS[scenario][0]}/{SCENARIOS[scenario][1]} tokens; sampled lengths, random-range-ratio={ratios}. All successful cases shown.\n"
        "Colored lines: series frontier guides. Dotted line/rings: global frontier. Lines are not additional measurements.\n"
        "Configurations can differ in precision/backend, topology, FlashInfer/CuTe and prefill graphs; not an isolated kernel speedup.",
        fontsize=9,
        va="top",
        linespacing=1.6,
    )
    name = f"{scenario}_output_per_gpu_vs_{mode}_pareto"
    for suffix in ("png", "svg"):
        fig.savefig(output / f"{name}.{suffix}")
    plt.close(fig)
    return {
        "scenario": scenario,
        "x_field": field,
        "y_field": "output_tput_per_gpu",
        "maximize_x": maximize_x,
        "chart": name,
        "series": series,
        "global_frontier_case_ids": [p["case_id"] for p in front],
    }


def write_report(
    points: list[dict],
    excluded: list[dict],
    charts: list[dict],
    output: Path,
    dp_attention_aligned: bool = False,
) -> None:
    lines = [
        "# Unofficial GLM-5.2 B300: InferenceX metric views",
        "",
        (
            "This comparison requires TP=DP=EP, disabled prefill CUDA graphs, static memory fraction 0.80, and "
            "server max-running-requests=max(client C, TP) for every included case. "
            "Historical DP1/EP1 results are excluded and must be plotted separately. "
            "Point labels always show client concurrency; TP8/C4 therefore remains C=4."
            if dp_attention_aligned
            else "These explicitly selected run roots form a separate reference view; no DP-attention alignment claim is made."
        ),
        "",
        f"**{len(points)} included cases; {sum(p['completed'] for p in points):,}/{sum(p['num_prompts'] for p in points):,} successful/requested requests.** "
        f"Excluded {len(excluded)} discovered cases. Unstarted cases with no metadata are not counted. These counts do not establish a complete planned matrix.",
        "",
        "Each point is one measured run. The workloads are separate: 1k1k and 8k1k specify ISL/OSL caps, with lengths sampled using each case's random-range ratio (0.8 for this experiment). "
        "The server GPU count is the denominator, including TP8 points; DP/EP share those GPUs and are not multiplied again. "
        "Configurations may differ in precision/backend and FlashInfer/CuTe; topology and prefill policy are governed by the alignment checks stated above. This is not an isolated kernel precision speedup or a latency-SLO result.",
        "",
        "## Metric and plotting sources",
        "",
        f"- [InferenceX fixed-sequence producer]({PRODUCER}): `median_e2el = median_e2el_ms / 1000`, `median_intvty = 1000 / median_tpot_ms`, `output_tput_per_gpu = output_throughput / gpu_count`. "
        "Interactivity is the reciprocal of the median TPOT, not the mean request rate; TPOT excludes the first token. E2EL includes TTFT.",
        f"- [Official x metrics]({APP}components/inference/metric-registry.ts#L701-L708) and [fixed-sequence median selection]({APP}components/inference/utils/resolveXAxisField.ts#L37-L67): main plots use `median_intvty` in tok/s/user for per-request interactivity; appendix plots use `median_e2el` in seconds.",
        f"- [Selected output-only y metric]({APP}components/inference/metric-registry.ts#L76-L82): `y_outputTputPerGpu`, tok/s/chip. Total input+output throughput is retained in the table, not substituted for output throughput. "
        "This is a selected website metric; the website's default y selection is a cost metric.",
        f"- [Series frontier algorithms]({APP}lib/chart-utils.ts#L615-L687) and [global frontier]({APP}components/inference/utils/global-pareto.ts#L25-L62) are matched by independent dominance predicates, including their original tie rules. "
        "E2EL minimizes x and maximizes y; interactivity maximizes both. The global frontier pools all included series separately for each workload and x mode. "
        "All successful points remain visible; green rings mark observed frontier coordinates, including coordinate ties.",
        f"- [Official point label toggles]({APP}components/inference/ui/point-label.ts#L4-L12): this static adaptation always shows concurrency and explicit TP/DP/EP. "
        f"[Official grouping]({APP}components/inference/ui/ScatterGraph.tsx#L1080-L1110) pools topology choices within hardware/precision/run. Accordingly, each arm/runtime/run has one curve across TP/DP/EP choices; shape and point labels identify topology. "
        "Colored series lines use straight guides rather than the website's D3 monotone interpolation; the dotted global frontier uses straight observed-vertex segments as on the website. No line claims an additional measurement.",
        "",
    ]
    for chart in charts:
        lines += [
            f"### {chart['scenario']} · {chart['x_field']}",
            "",
            f"![{chart['chart']}]({chart['chart']}.png)",
            "",
            f"[SVG]({chart['chart']}.svg)",
            "",
        ]
    lines += [
        "## Measurements",
        "",
        "| Case | Scenario | Backend | TP/DP/EP | C | Static memory fraction | Success | median_intvty (tok/s/user) | median_e2el (s) | output_tput_per_gpu (tok/s/chip) | output_throughput (tok/s) | total_token_throughput (tok/s) | Raw |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for p in points:
        lines.append(
            "| "
            + " | ".join(
                map(
                    cell,
                    [
                        p["case_id"],
                        p["scenario"],
                        p["backend_label"],
                        f"{p['tp']}/{p['dp']}/{p['ep']}",
                        p["concurrency"],
                        p.get("mem_fraction_static") or "not recorded",
                        f"{p['completed']}/{p['num_prompts']}",
                        fmt(p["median_intvty"]),
                        fmt(p["median_e2el"]),
                        fmt(p["output_tput_per_gpu"]),
                        fmt(p["output_throughput"]),
                        fmt(p["total_token_throughput"]),
                        f"[JSON](<{p['result_file']}>) / [metadata](<{p['metadata_file']}>)",
                    ],
                )
            )
            + " |"
        )
    if excluded:
        lines += ["", "## Excluded cases", ""]
        lines += [
            f"- {cell(p['metadata_file'])}: {'; '.join(p['exclusion_reasons'])}"
            for p in excluded
        ]
    (output / "pareto.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--dp-attention-aligned",
        action="store_true",
        help="Require aligned topology, prefill policy, server cap and static memory fraction 0.80; reject historical DP1/EP1 cases",
    )
    args = parser.parse_args()
    paths = sorted(
        {p.resolve() for root in args.results for p in root.rglob("metadata.json")}
    )
    rows = [read_case(path) for path in paths]
    included = sorted(
        (r for r in rows if r["included"]),
        key=lambda r: (
            r["scenario"],
            r["backend"],
            r["run_id"],
            r["tp"],
            r["dp"],
            r["ep"],
            r["concurrency"],
        ),
    )
    if not included:
        parser.error("no successful measured cases to plot")
    try:
        validate_comparison(included, args.dp_attention_aligned)
    except ValueError as exc:
        parser.error(str(exc))
    points = []
    excluded = [r for r in rows if not r["included"]]
    for index, row in enumerate(included, 1):
        row["case_id"] = f"P{index}"
        try:
            points.append(point_from_case(row))
        except ValueError as exc:
            parser.error(str(exc))
    args.output.mkdir(parents=True, exist_ok=True)
    charts = []
    for mode in MODES:
        for scenario in SCENARIOS:
            selected = [p for p in points if p["scenario"] == scenario]
            if selected:
                charts.append(draw(selected, args.output, scenario, mode))
    for point in points + excluded:
        for key in ("metadata_file", "result_file", "case"):
            if point.get(key):
                point[key] = os.path.relpath(point[key], args.output)
    write_report(points, excluded, charts, args.output, args.dp_attention_aligned)
    (args.output / "pareto.json").write_text(
        json.dumps(
            {
                "artifact_path_base": "directory containing pareto.json",
                "dp_attention_aligned": args.dp_attention_aligned,
                "points": points,
                "excluded": excluded,
                "charts": charts,
            },
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )
    print(f"{len(points)} cases, {len(charts)} figures: {args.output / 'pareto.md'}")


if __name__ == "__main__":
    main()
