#!/usr/bin/env python3
"""Exercise real plot geometry with a clearly marked, non-measured fixture."""

import argparse
import hashlib
import json
from pathlib import Path

import results


def fixture():
    rows = []
    for index, arm in enumerate(("megamoe-w4a4", "megamoe-w4a16", "trtllm-w4a4")):
        for tp in (4, 8):
            for c, x, y in (
                (4, 200, 100),
                (8, 175, 180),
                (16, 150, 330),
                (32, 125, 570),
            ):
                rows.append(
                    {
                        "case_id": f"{arm}-tp{tp}-ep{tp}-dp{tp}-c{c}",
                        "arm_id": arm,
                        "tp": tp,
                        "ep": tp,
                        "dp": tp,
                        "concurrency": c,
                        "interactivity_tok_s_user": x
                        + (25 if tp == 8 else 0)
                        - 4 * index,
                        "output_tok_s_gpu": y
                        * (0.65 if tp == 8 else 1)
                        * (1 - index * 0.08),
                        "sglang_commit": "SYNTHETIC",
                        "flashinfer_commit": "SYNTHETIC",
                    }
                )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rows = fixture()
    fig, points = results.figure(rows)
    ax = fig.axes[0]
    assert len(ax.lines) == 6
    assert len(points) == 24
    assert [list(line.get_xdata()) for line in ax.lines[:1]] == [[125, 150, 175, 200]]
    assert list(ax.lines[0].get_ydata()) == [570, 330, 180, 100]
    assert [line.get_color() for line in ax.lines] == [
        "#009E73",
        "#009E73",
        "#E69F00",
        "#E69F00",
        "#0072B2",
        "#0072B2",
    ]
    assert [line.get_marker() for line in ax.lines] == ["o", "^", "o", "^", "o", "^"]
    assert [line.get_linestyle() for line in ax.lines] == [
        "-",
        "--",
        "-",
        "--",
        "-",
        "--",
    ]
    assert len(ax.get_legend().get_lines()) == 6
    labels = [t.get_text() for t in ax.texts]
    assert sorted(labels) == sorted(["C4", "C8", "C16", "C32"] * 6)
    assert all(len(group["case_ids"]) == 4 for group in results.frontiers(rows))
    fig.suptitle(
        "SYNTHETIC LAYOUT CHECK — no benchmark measurements",
        y=0.965,
        fontsize=20,
        weight="bold",
    )
    # Replace the measured-results subtitle before any image is saved.
    fig.texts[1].set_text(
        "Hand-constructed geometry fixture | six frontiers / 24 labelled points | not campaign results"
    )
    fig.text(
        0.5,
        0.45,
        "SYNTHETIC",
        fontsize=58,
        color="gray",
        alpha=0.18,
        ha="center",
        rotation=20,
    )
    fig.savefig(args.output / "synthetic-pareto.png", dpi=180)
    fig.savefig(args.output / "synthetic-pareto.svg", metadata={"Date": None})
    (args.output / "synthetic-points.json").write_text(
        json.dumps(points, indent=2) + "\n"
    )
    report = {
        "scope": "synthetic rendering behavior; no GPU measurements",
        "checks": 10,
        "points": len(points),
        "frontiers": len(ax.lines),
        "files": {},
    }
    for path in sorted(args.output.iterdir()):
        report["files"][path.name] = {
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    (args.output / "CHECK.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "files"}))


if __name__ == "__main__":
    main()
