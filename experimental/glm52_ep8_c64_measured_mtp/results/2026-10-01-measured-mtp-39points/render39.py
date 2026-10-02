#!/usr/bin/env python3
"""Portable table-only rendering: EP4 C1-32 / EP8 C1-64; no raw-evidence acceptance."""
import argparse
import importlib.util
import json
from pathlib import Path

import join39 as join


def render(bundle, output):
    bundle = join.safe(bundle)
    manifest = join.read(bundle / "plot-source-manifest.json")
    required = {"join39.py", "render39.py", "layout_original.py", "raw-metrics.json"}
    required.update("source/" + join.OLD + "/" + n for n in ("run.py", "results.py"))
    join.need(required <= set(manifest["files"]), "Incomplete portable source manifest")
    for rel, expected in manifest["files"].items():
        join.need(not Path(rel).is_absolute() and ".." not in Path(rel).parts, "Unsafe export member")
        join.need(join.desc(bundle / rel) == expected, "Portable source/metrics changed: " + rel)
    rows = join.read(bundle / "raw-metrics.json")
    join.validate_rows(rows, join.BASE_IDS | join.NEW_IDS, 5700)
    reader = join.load_reader(bundle / "source", join.OLD, "plot_base")
    spec = importlib.util.spec_from_file_location("original_layout", bundle / "layout_original.py")
    layout = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(layout)
    output = join.safe(output)
    output.mkdir(parents=True, exist_ok=False)
    views = {}
    for relative, topology in (("", None), ("figures/ep4", 4), ("figures/ep8", 8)):
        destination = output / relative
        destination.mkdir(parents=True, exist_ok=True)
        fig, points = reader.figure(rows, topology)
        scope = "EP4 C1–32 / EP8 C1–64" if topology is None else f"EP{topology} C1–{32 if topology == 4 else 64}"
        fig._suptitle.set_text("GLM-5.2 | MegaMoE and TRTLLM NVFP4 | B300 | " + scope)
        for text in fig.texts:
            value = text.get_text()
            if "shared compiled caches; six isolated tactic namespaces" in value:
                text.set_text(value.replace("shared compiled caches; six isolated tactic namespaces",
                    "base36 + separate fresh-cache EP8 C64 extension; sequential history differs"))
        placements = layout.place_labels(fig)
        fig.savefig(destination / "pareto.png", dpi=180)
        import matplotlib
        with matplotlib.rc_context({"svg.fonttype": "path"}):
            fig.savefig(destination / "pareto.svg", metadata={"Date": None})
        frontiers = [g for g in reader.frontiers(rows) if topology is None or g["tp"] == topology]
        join.write(destination / "plot-points.json", points)
        join.write(destination / "frontiers.json", frontiers)
        views[relative or "combined"] = {"points": len(points), "frontiers": len(frontiers),
            "range": scope, "labels": placements, "text_overlap_count": 0}
        import matplotlib.pyplot as plt
        plt.close(fig)
    result = {"status": "TABLE_ONLY_39_POINT_PLOT_REPLAY", "views": views,
              "metrics": join.desc(bundle / "raw-metrics.json"),
              "plot_source_manifest": join.desc(bundle / "plot-source-manifest.json"),
              "limits": ["Plot replay does not validate raw/native/runtime/terminal/preservation evidence.",
                         "C2–32 is the unchanged existing30-point view, not recomputed from39.",
                         "No EP4 C64 point or seventh pooled frontier is constructed."]}
    join.write(output / "LAYOUT.json", result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    report = render(a.bundle, a.output)
    print(json.dumps({"status": report["status"], "views": {k: v["points"] for k, v in report["views"].items()}}))


if __name__ == "__main__":
    main()
