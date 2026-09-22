"""Backend-union display grouping; metric/frontier functions imported unchanged."""
from plot_pareto import *
from plot_pareto import SERIES_KEYS
COMPARISON_GROUP_KEYS = ("plot_series",)
SERIES_ORDER = ('new_mega', 'original_mega', 'split', 'trtllm')
GROUP_LABELS = {
    'new_mega': 'New MegaMoE · SG26c / proxy off + retained SG6d8 / original proxy',
    'original_mega': 'Original MegaMoE · SG50eeb / historical original configuration',
    'split': 'Split · historical control',
    'trtllm': 'TRT · historical control',
}


def observation_key(point):
    # Display IDs may repeat across original/main figure namespaces. Never
    # rewrite historical IDs; source/run/coordinate forms the unique identity.
    return (point['run_id'], point['scenario'], point['backend'], point['tp'], point['concurrency'])


def four_series(main, original):
    if len(main) != 48 or len(original) != 16:
        raise ValueError('Final plotting requires48 main +16 original references')
    result = []
    for point in main:
        series = {'w4a16_megamoe': 'new_mega', 'w4a16_cutedsl': 'split', 'w4a4_trtllm': 'trtllm'}[point['backend']]
        result.append({**point, 'plot_series': series})
    result.extend({**point, 'plot_series': 'original_mega'} for point in original)
    if len({observation_key(p) for p in result}) != 64:
        raise ValueError('Duplicate actual source/run observation')
    expected = {(scenario, tp, c) for scenario in SCENARIOS for tp, c in [(4,4),(4,8),(4,16),(4,32),(4,64),(4,128),(4,256),(8,4)]}
    for series in SERIES_ORDER:
        values = [p for p in result if p['plot_series'] == series]
        if len(values) != 16 or {(p['scenario'],p['tp'],p['concurrency']) for p in values} != expected:
            raise ValueError('Four series must each contain every16 original coordinate')
    return result


def draw(points: list[dict], output: Path, scenario: str, mode: str) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    field, x_label, maximize_x = MODES[mode]
    projected = [{**p, "x": p[field], "y": p["output_tput_per_gpu"]} for p in points]
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for point in projected:
        groups[tuple(point[key] for key in COMPARISON_GROUP_KEYS)].append(point)
    if set(k[0] for k in groups) != set(SERIES_ORDER) or len(projected) != 32 or any(len(v) != 8 for v in groups.values()):
        raise ValueError("Exactly four complete eight-point series per scenario required")
    fig, ax = plt.subplots(figsize=(18, 13), dpi=160)
    fig.subplots_adjust(left=0.085, right=0.98, top=0.90, bottom=0.32)
    colors = {
        "trtllm": "#1769aa",
        "new_mega": "#d65f16",
        "original_mega": "#258347",
        "split": "#8a4db3",
    }
    legend = []
    series = []
    for series_name in SERIES_ORDER:
        values = groups[(series_name,)]
        p = values[0]
        color = colors[series_name]
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
            f"{GROUP_LABELS[series_name]} · B300\n"
            f"FI {p.get('flashinfer_version') or '?'} @ {(p.get('flashinfer_commit') or 'image-provided')[:14]} · "
            f"CuTe {p.get('cute_dsl_version') or '?'} · prefill graphs: {p['prefill_cuda_graph_policy']}\n"
            f"Static memory fraction: {p.get('mem_fraction_static') or 'not recorded'} · "
            f"image: {p['image'].split('@')[0].partition(':')[2]}"
            + (f" @ {p['image'].split('@')[-1][:19]}" if '@' in p['image'] else '')
        )
        legend.append(Line2D([], [], color=color, lw=1.5, label=label))
        series.append(
            {
                "identity": {key: p[key] for key in COMPARISON_GROUP_KEYS},
                "case_ids": [p["case_id"] for p in values],
                "frontier_case_ids": [p["case_id"] for p in front],
                "observations": [{"case_id": q["case_id"], "key": list(observation_key(q))} for q in values],
                "frontier_observations": [{"case_id": q["case_id"], "key": list(observation_key(q))} for q in front],
                "source_runs": sorted({q["run_id"] for q in values}),
                "sglang_commits": sorted({q["sglang_commit"] for q in values}),
            }
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
    if scenario == "1k1k" and mode == "e2el":
        for point, label in zip(projected, ax.texts, strict=True):
            if point["plot_series"] == "original_mega" and point["tp"] == 8 and point["concurrency"] == 4:
                # Move only this label clear of adjacent text; measured anchor stays fixed.
                label.set_position((-108.0, 7.5))
    for point in projected:
        if point.get("provenance_role") == "retained old Mega":
            ax.scatter([point["x"]], [point["y"]], s=210, marker="s", facecolors="none", edgecolors="#d65f16", linewidths=1.4, zorder=6)
    if any(p.get("provenance_role") == "retained old Mega" for p in projected):
        legend.append(Line2D([], [], color="#d65f16", ls="none", marker="s", markerfacecolor="none", label="Square: retained SG6d8 / original proxy\nOther New Mega: R8 SG26c / disabled proxy"))
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
        "Exactly four colored series frontier guides; no pooled global frontier. Lines are not additional measurements.\n"
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
        "global_frontier_drawn": False,
        "observation_count": len(projected),
        "series_order": list(SERIES_ORDER),
    }
