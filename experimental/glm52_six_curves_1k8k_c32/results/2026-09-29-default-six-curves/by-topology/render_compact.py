#!/usr/bin/env python3
"""Render three accepted GLM views with saved MTP acceptance-length annotations."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

READER = "source/experimental/glm52_six_curves_1k8k_c32/results.py"


def descriptor(path: Path) -> dict:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"bytes": path.stat().st_size, "sha256": digest}


def write_json(path: Path, value: object) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def verify_bundle(root: Path) -> dict:
    if json.loads((root / "PROVENANCE.json").read_bytes())["status"] != "PUBLIC_COMPACT_SUMMARY_AND_PLOTS":
        raise ValueError("Expected compact public summary bundle")
    manifest = json.loads((root / "FILES.json").read_bytes())
    for relative, expected in manifest["files"].items():
        path = root / relative
        if not path.resolve().is_relative_to(root) or descriptor(path) != expected:
            raise ValueError(f"Published payload differs: {relative}")
    return manifest


def acceptance_lengths(root: Path, rows: list[dict]) -> dict:
    """Report the missing evidence for exact measured-only MTP acceptance length."""
    saved = json.loads((root / "by-topology/figures/acceptance-length.json").read_bytes())
    values = saved["values"]
    if {v["case_id"] for v in values} != {r["case_id"] for r in rows}:
        raise ValueError("Acceptance metadata case set differs")
    if any(v["measured_acceptance_length"] is not None or v["status"] != "unavailable"
           or v["display"] != "AL=N/A" for v in values):
        raise ValueError("Historical measured-only AL must remain unavailable")
    return saved


def annotate_acceptance(fig, ax, points: list[dict], metrics: dict[str, dict]) -> None:
    """Place two-line labels with deterministic offsets and readable leader lines."""
    from matplotlib.text import Annotation
    from matplotlib.transforms import Bbox

    old = [text for text in ax.texts if isinstance(text, Annotation)]
    for text in old:
        text.remove()
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    marker_boxes = []
    for point in points:
        x, y = ax.transData.transform((point["x"], point["y"]))
        marker_boxes.append(Bbox.from_bounds(x - 7, y - 7, 14, 14))
    boxes = []
    offsets = [
        (12, 14),
        (-12, 14),
        (12, -30),
        (-12, -30),
        (12, 36),
        (-12, 36),
        (12, -52),
        (-12, -52),
        (48, 8),
        (-48, 8),
        (48, -26),
        (-48, -26),
        (12, 58),
        (-12, 58),
        (12, -74),
        (-12, -74),
    ]
    # Nearby high-throughput points are placed first; subsequent labels avoid them.
    for point in sorted(
        points, key=lambda item: (-item["y"], item["x"], item["case_id"])
    ):
        color = {
            "megamoe-w4a4": "#009E73",
            "megamoe-w4a16": "#E69F00",
            "trtllm-w4a4": "#0072B2",
        }[point["arm_id"]]
        text = f"C{point['concurrency']}\n{metrics[point['case_id']]['display']}"
        annotation = ax.annotate(
            text,
            (point["x"], point["y"]),
            xytext=offsets[0],
            textcoords="offset points",
            color=color,
            fontsize=10,
            linespacing=1.25,
            va="bottom",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.94, "pad": 1.2},
            arrowprops={"arrowstyle": "-", "color": color, "lw": 0.65},
            zorder=5,
        )
        chosen = None
        for dx, dy in offsets:
            annotation.set_position((dx, dy))
            annotation.set_ha("left" if dx > 0 else "right")
            annotation.update_positions(renderer)
            annotation.update_bbox_position_size(renderer)
            box = (
                annotation.get_bbox_patch()
                .get_window_extent(renderer)
                .expanded(1.10, 1.12)
            )
            inside = ax.bbox.contains(box.x0, box.y0) and ax.bbox.contains(
                box.x1, box.y1
            )
            if inside and not any(
                box.overlaps(other) for other in boxes + marker_boxes
            ):
                chosen = box
                break
        if chosen is None:
            raise ValueError(f"No readable label placement: {point['case_id']}")
        boxes.append(chosen)


def render(root: Path, output: Path) -> None:
    manifest = verify_bundle(root)
    if output.exists():
        raise ValueError("Use a new output directory")
    sys.path.insert(0, str((root / READER).parent))
    spec = importlib.util.spec_from_file_location(
        "published_glm_results", root / READER
    )
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    rows = reader.read(root / "results/raw-metrics.json")
    if len(rows) != 24 or len({r["case_id"] for r in rows}) != 24:
        raise ValueError("Expected the 24 saved summary rows")
    accepted_points = reader.read(root / "results/plot-points.json")
    accepted_frontiers = reader.read(root / "results/frontiers.json")
    acceptance = acceptance_lengths(root, rows)
    metrics = {item["case_id"]: item for item in acceptance["values"]}
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "acceptance-length.json", acceptance)
    summary = []
    for topology in (4, 8, None):
        selected = [row for row in rows if topology is None or row["tp"] == topology]
        fig, points = reader.figure(selected)
        ax = fig.axes[0]
        for line in list(ax.lines):
            if len(line.get_xdata()) == 0:
                line.remove()
        for collection in list(ax.collections):
            if len(collection.get_offsets()) == 0:
                collection.remove()
        if topology == 8:
            from matplotlib.markers import MarkerStyle

            circle = MarkerStyle("o")
            circle_path = circle.get_path().transformed(circle.get_transform())
            for line in ax.lines:
                line.set_linestyle("-")
                line.set_marker("o")
            for collection in ax.collections:
                collection.set_paths([circle_path])
        combined = topology is None
        fig.set_size_inches(20 if combined else 17, 12)
        fig.subplots_adjust(left=0.11, right=0.97, bottom=0.27, top=0.86)
        ax.legend(
            loc="upper center",
            bbox_to_anchor=(0.5, -0.13),
            ncol=3,
            fontsize=10,
            frameon=False,
        )
        fig._suptitle.set_text(
            "GLM-5.2 | Six backend/topology curves | B300 | Concurrency 4-32"
            if combined
            else f"GLM-5.2 | TP=EP=DP={topology} | Three backends | B300 | Concurrency 4-32"
        )
        measured = sum(row["completed"] for row in selected)
        fig.texts[1].set_text(
            f"Nominal 1,024 input / 8,192 output | ratio 0.8 | {len(selected)} accepted points | {measured:,} measured requests"
        )
        for text in list(fig.texts[2:]):
            text.remove()
        footnotes = [
            (
                0.12,
                "MTP acceptance length (AL): measured-only value unavailable; native verification counts or boundary deltas were not saved.",
                11,
            ),
            (
                0.09,
                "Measured-only AL is not estimated. Independent frontiers per backend/topology. EAGLE: steps 3 / top-k 1 / draft tokens 4.",
                10,
            ),
            (
                0.065,
                "Draft MoE: BF16 TRTLLM / none | Backend quantization/fast-math defaults | Saved ITL is chunk spacing at stream interval 30.",
                10,
            ),
            (
                0.04,
                f"SG {rows[0]['sglang_commit'][:12]} | FI {rows[0]['flashinfer_commit'][:12]} | shared compiled caches; six isolated tactic namespaces",
                10,
            ),
            (
                0.015,
                "Whole measured interval; not timed decode. Single sequential run; no causal or numerical-equivalence claim.",
                9,
            ),
        ]
        for y, text, size in footnotes:
            fig.text(0.5, y, text, ha="center", fontsize=size, color="#444444")
        annotate_acceptance(fig, ax, points, metrics)
        frontiers = [
            item
            for item in reader.frontiers(selected)
            if topology is None or item["tp"] == topology
        ]
        if points != [
            point
            for point in accepted_points
            if topology is None or point["tp"] == topology
        ]:
            raise ValueError("Additive point coordinates differ from published points")
        if frontiers != [
            item
            for item in accepted_frontiers
            if topology is None or item["tp"] == topology
        ]:
            raise ValueError("Additive frontiers differ from published membership")
        directory = output / ("six-curves" if combined else f"ep{topology}")
        directory.mkdir()
        fig.savefig(directory / "pareto.png", dpi=180)
        fig.savefig(directory / "pareto.svg", metadata={"Date": None})
        import matplotlib.pyplot as plt

        plt.close(fig)
        write_json(directory / "plot-points.json", points)
        write_json(directory / "frontiers.json", frontiers)
        summary.append(
            {
                "view": directory.name,
                "topology": topology,
                "points": len(selected),
                "frontiers": len(frontiers),
                "measured_requests": measured,
                "warmup_requests": sum(2 * row["concurrency"] for row in selected),
            }
        )
    verify_bundle(root)
    write_json(
        output / "PROVENANCE.json",
        {
            "source": "Saved compact aggregate tables; raw evidence retained locally; no new benchmark runs",
            "manifest": {
                "relative_path": "FILES.json",
                **descriptor(root / "FILES.json"),
            },
            "reader": {"relative_path": READER, **descriptor(root / READER)},
            "public_payloads_rehashed_before_and_after": manifest["file_count"],
            "raw_evidence_revalidated": False,
            "views": summary,
            "acceptance_length": {
                "relative_path": "acceptance-length.json",
                **descriptor(output / "acceptance-length.json"),
            },
            "campaign": {
                "points": 24,
                "measured_requests": 3600,
                "warmup_requests": 720,
            },
        },
    )
    print(json.dumps(summary))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--published-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render(args.published_root.resolve(), args.output.absolute())


if __name__ == "__main__":
    main()
