#!/usr/bin/env python3
"""Render additive three-backend EP4/EP8 views from the published, accepted campaign."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

MANIFEST_SHA = "0158a59b724969ec8bde4edb3a073abf79fbc7d4ede64cdbedc2200e017856a8"
READER = "source/experimental/glm52_six_curves_1k8k_c32/results.py"


def descriptor(path: Path) -> dict:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return {"bytes": path.stat().st_size, "sha256": digest}


def write_json(path: Path, value: object) -> None:
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def verify_bundle(root: Path) -> dict:
    if descriptor(root / "FILES.json")["sha256"] != MANIFEST_SHA:
        raise ValueError("Expected the unchanged accepted six-curve release manifest")
    manifest = json.loads((root / "FILES.json").read_bytes())
    for relative, expected in manifest["files"].items():
        path = root / relative
        if not path.resolve().is_relative_to(root) or descriptor(path) != expected:
            raise ValueError(f"Published payload differs: {relative}")
    return manifest


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
    rows = reader.load(root / "raw", False)
    if rows != reader.read(root / "results/raw-metrics.json"):
        raise ValueError("Verified raw rows differ from the published table")
    accepted_points = reader.read(root / "results/plot-points.json")
    accepted_frontiers = reader.read(root / "results/frontiers.json")
    output.mkdir(parents=True, exist_ok=False)
    summary = []
    for topology in (4, 8):
        selected = [row for row in rows if row["tp"] == topology]
        fig, points = reader.figure(selected)
        ax = fig.axes[0]
        # The inherited renderer creates empty artists for the other topology.
        for line in list(ax.lines):
            if len(line.get_xdata()) == 0:
                line.remove()
        for collection in list(ax.collections):
            if len(collection.get_offsets()) == 0:
                collection.remove()
        # A single-topology view uses the same solid/circle style as EP4.
        if topology == 8:
            from matplotlib.markers import MarkerStyle

            circle = MarkerStyle("o")
            circle_path = circle.get_path().transformed(circle.get_transform())
            for line in ax.lines:
                line.set_linestyle("-")
                line.set_marker("o")
            for collection in ax.collections:
                collection.set_paths([circle_path])
        ax.legend(loc="best", fontsize=10, framealpha=0.96)
        fig._suptitle.set_text(
            f"GLM-5.2 | TP=EP=DP={topology} | Three backends | B300 | Concurrency 4-32"
        )
        fig.texts[1].set_text(
            "Nominal 1,024 input / 8,192 output | ratio 0.8 | 12 accepted points | 1,800 measured requests"
        )
        fig.texts[2].set_text(
            "Three independent backend frontiers; all 12 points shown. This topology view selects half of the accepted 24-point campaign."
        )
        frontiers = [
            item for item in reader.frontiers(selected) if item["tp"] == topology
        ]
        if points != [point for point in accepted_points if point["tp"] == topology]:
            raise ValueError("Additive point coordinates differ from published points")
        if frontiers != [item for item in accepted_frontiers if item["tp"] == topology]:
            raise ValueError("Additive frontiers differ from published membership")
        directory = output / f"ep{topology}"
        directory.mkdir()
        fig.savefig(directory / "pareto.png", dpi=180)
        fig.savefig(directory / "pareto.svg", metadata={"Date": None})
        import matplotlib.pyplot as plt

        plt.close(fig)
        write_json(directory / "plot-points.json", points)
        write_json(directory / "frontiers.json", frontiers)
        summary.append(
            {
                "tp": topology,
                "ep": topology,
                "dp": topology,
                "points": len(selected),
                "frontiers": len(frontiers),
                "measured_requests": sum(row["completed"] for row in selected),
                "warmup_requests": sum(2 * row["concurrency"] for row in selected),
            }
        )
    verify_bundle(root)
    write_json(
        output / "PROVENANCE.json",
        {
            "source": "Existing accepted measurements; no new benchmark runs",
            "manifest": {
                "relative_path": "FILES.json",
                **descriptor(root / "FILES.json"),
            },
            "reader": {"relative_path": READER, **descriptor(root / READER)},
            "published_payloads_rehashed_before_and_after": manifest["file_count"],
            "views": summary,
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
