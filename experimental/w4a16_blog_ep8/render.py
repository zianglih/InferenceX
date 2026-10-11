#!/usr/bin/env python3
"""Render one fresh EP4/EP8 model from its compact, validated metrics table."""

import argparse
import json
import math
from pathlib import Path

import results


def place_labels(fig) -> list[dict]:
    """Place crowded labels first without changing any measured coordinate."""
    from matplotlib.text import Annotation, Text
    from matplotlib.transforms import Bbox

    ax = fig.axes[0]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    labels = [label for label in ax.texts if isinstance(label, Annotation)]
    anchors = [tuple(ax.transData.transform(label.xy)) for label in labels]
    bounds = ax.get_window_extent(renderer).padded(-5)
    sizes = []
    for label in labels:
        label.set_ha("center")
        label.set_va("center")
        label.update_positions(renderer)
        box = Text.get_window_extent(label, renderer)
        sizes.append((box.width + 8, box.height + 8))
    crowded = [
        sum(math.dist(point, other) < 110 for other in anchors) for point in anchors
    ]
    order = sorted(range(len(labels)), key=lambda i: (-crowded[i], i))
    obstacles = []
    placements = {}
    radii = (20, 30, 42, 56, 72, 92, 118, 150, 190, 235, 290)
    angles = (
        90,
        -90,
        0,
        180,
        45,
        135,
        -45,
        -135,
        25,
        155,
        -25,
        -155,
        65,
        115,
        -65,
        -115,
    )
    scale = fig.dpi / 72
    for i in order:
        x, y = anchors[i]
        width, height = sizes[i]
        candidates = []
        for radius in radii:
            for angle in angles:
                theta = math.radians(angle)
                dx, dy = radius * math.cos(theta), radius * math.sin(theta)
                box = Bbox.from_bounds(
                    x + dx * scale - width / 2,
                    y + dy * scale - height / 2,
                    width,
                    height,
                )
                if not (
                    bounds.x0 <= box.x0
                    and box.x1 <= bounds.x1
                    and bounds.y0 <= box.y0
                    and box.y1 <= bounds.y1
                ):
                    continue
                if any(box.overlaps(other) for other in obstacles):
                    continue
                if any(box.padded(5).contains(*point) for point in anchors):
                    continue
                candidates.append(
                    (radius + abs(dx) * 0.035, abs(dx), angle, dx, dy, box)
                )
            if candidates:
                break
        if not candidates:
            raise ValueError(
                f"No collision-free label position: {labels[i].get_text()}"
            )
        _, _, _, dx, dy, box = min(candidates, key=lambda value: value[:3])
        labels[i].set_position((dx, dy))
        obstacles.append(box)
        placements[i] = {
            "text": labels[i].get_text(),
            "xy": list(labels[i].xy),
            "offset_points": [dx, dy],
        }
    fig.canvas.draw()
    actual = [Text.get_window_extent(label, renderer).padded(2) for label in labels]
    results.require(
        not any(a.overlaps(b) for i, a in enumerate(actual) for b in actual[i + 1 :]),
        "Final point labels overlap",
    )
    figure_text = [text.get_window_extent(renderer) for text in fig.texts]
    results.require(
        not any(
            a.overlaps(b)
            for i, a in enumerate(figure_text)
            for b in figure_text[i + 1 :]
        ),
        "Figure title or footnotes overlap",
    )
    return [placements[i] for i in range(len(labels))]


def configure_plotting():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "svg.fonttype": "path",
            "svg.hashsalt": "w4a16-blog-ep8",
        }
    )
    return plt


def figure(table: dict):
    rows = results.validate_table(table)
    gpus = results.gpu_count(table["campaign"]["matrix"])
    plt = configure_plotting()
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.subplots_adjust(left=0.10, right=0.97, bottom=0.22, top=0.85)
    points, groups = [], []
    for arm, (label, color) in results.ARMS.items():
        group = [row for row in rows if row["arm_id"] == arm]
        selected = results.frontier(group)
        ax.plot(
            [row["interactivity_tok_s_user"] for row in selected],
            [row["output_tok_s_gpu"] for row in selected],
            color=color,
            linewidth=1.8,
            linestyle="--" if gpus == 8 else "-",
            label=label,
            zorder=2,
        )
        ax.scatter(
            [row["interactivity_tok_s_user"] for row in group],
            [row["output_tok_s_gpu"] for row in group],
            color=color,
            marker="^" if gpus == 8 else "o",
            s=70,
            edgecolor="white",
            linewidth=0.7,
            zorder=4,
        )
        groups.append(
            {"arm_id": arm, "concurrencies": [row["concurrency"] for row in selected]}
        )
        for row in group:
            ax.annotate(
                f"C{row['concurrency']}\nAL={row['acceptance_length']:.2f}",
                (row["interactivity_tok_s_user"], row["output_tok_s_gpu"]),
                xytext=(0, 20),
                textcoords="offset points",
                color=color,
                fontsize=9,
                bbox={
                    "facecolor": "white",
                    "edgecolor": "none",
                    "alpha": 0.9,
                    "pad": 0.6,
                },
                arrowprops={"arrowstyle": "-", "color": color, "lw": 0.65},
                zorder=5,
            )
            points.append(
                {
                    "arm_id": arm,
                    "concurrency": row["concurrency"],
                    "x": row["interactivity_tok_s_user"],
                    "y": row["output_tok_s_gpu"],
                    "acceptance_length": row["acceptance_length"],
                    "acceptance_rate": row["acceptance_rate"],
                }
            )
    ax.set(
        xlabel="Interactivity = 1,000 / median TPOT (output tokens/s/user)",
        ylabel="Whole-interval output throughput (tokens/s/GPU)",
    )
    ax.grid(alpha=0.20)
    ax.margins(x=0.16, y=0.16)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
    model, algorithm, proposals = results.MODELS[table["model_id"]]
    campaign = table["campaign"]
    fig.suptitle(
        f"{model} | {algorithm} | B300 EP{gpus} | Concurrency 1-64",
        y=0.975,
        fontsize=17,
        weight="bold",
    )
    fig.text(
        0.5,
        0.925,
        f"TP = EP = attention DP = {gpus} | Nominal 1,024 input / 8,192 output | ratio 0.8\n"
        f"{len(rows)} fresh points | {sum(row['completed'] for row in rows):,} measured requests",
        ha="center",
        va="top",
        fontsize=11,
        linespacing=1.8,
    )
    fig.text(
        0.5,
        0.09,
        "All points shown; lines connect nondominated points within each backend.",
        ha="center",
        fontsize=10,
    )
    fig.text(
        0.5,
        0.06,
        f"AL = measured completion tokens / verification count, including bonus tokens; "
        f"warmups excluded. Draft proposals per step: {proposals}.",
        ha="center",
        fontsize=9,
    )
    fig.text(
        0.5,
        0.03,
        f"SGLang {campaign['sglang_commit'][:12]} | "
        f"FlashInfer {campaign['flashinfer_commit'][:12]} | Full measured wall interval; no time subtraction.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    placements = place_labels(fig)
    return fig, points, groups, placements


def acceptance_figure(table: dict):
    rows = results.validate_table(table)
    gpus = results.gpu_count(table["campaign"]["matrix"])
    plt = configure_plotting()
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.subplots_adjust(left=0.10, right=0.97, top=0.86, bottom=0.23)
    for arm, (label, color) in results.ARMS.items():
        group = [row for row in rows if row["arm_id"] == arm]
        ax.plot(
            [row["concurrency"] for row in group],
            [row["acceptance_length"] for row in group],
            color=color,
            marker="^" if gpus == 8 else "o",
            linewidth=1.8,
            label=label,
        )
    ax.set_xscale("log", base=2)
    ax.set_xticks(results.CONCURRENCIES, [str(c) for c in results.CONCURRENCIES])
    ax.set(
        xlabel="Concurrency",
        ylabel="Measured acceptance length (tokens / verification step)",
    )
    ax.grid(alpha=0.20)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.15),
        ncol=3,
        frameon=False,
        fontsize=9,
    )
    model, algorithm, _ = results.MODELS[table["model_id"]]
    fig.suptitle(
        f"{model} | {algorithm} | B300 EP{gpus}", fontsize=16, weight="bold", y=0.96
    )
    fig.text(
        0.5,
        0.035,
        "AL = sum of measured completion tokens / sum of verification counts.\n"
        "Includes native bonus tokens; excludes warmups. AL alone is not an output-quality metric.",
        ha="center",
        fontsize=9,
    )
    return fig


def render(table: dict, output: Path) -> dict:
    fig, points, groups, placements = figure(table)
    output.mkdir(parents=True, exist_ok=False)
    fig.savefig(output / "pareto.png", dpi=180)
    fig.savefig(output / "pareto.svg", metadata={"Date": None})
    plt = configure_plotting()
    plt.close(fig)
    al = acceptance_figure(table)
    al.savefig(output / "acceptance-length.png", dpi=180)
    al.savefig(output / "acceptance-length.svg", metadata={"Date": None})
    plt.close(al)
    results.write_json(output / "points.json", points)
    results.write_json(output / "frontiers.json", groups)
    receipt = {
        "schema_version": 1,
        "scope": "compact-table arithmetic and plot replay",
        "model_id": table["model_id"],
        "points": len(points),
        "labels": placements,
        "text_overlap_count": 0,
    }
    results.write_json(output / "REPLAY.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    table = json.loads(args.table.read_text())
    receipt = render(table, args.output)
    print(
        json.dumps(
            {
                "model": receipt["model_id"],
                "points": receipt["points"],
                "output": str(args.output),
            }
        )
    )


if __name__ == "__main__":
    main()
