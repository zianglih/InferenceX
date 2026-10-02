"""Render accepted GLM plots with deterministic nonoverlapping point labels.

This publication-only wrapper reuses the bundled, unchanged results.figure().
It changes annotation placement and outlines SVG text, preserving data and metrics.
"""
import argparse
import hashlib
import importlib
import json
import math
import sys
from pathlib import Path


def place_labels(fig):
    from matplotlib.text import Annotation, Text
    from matplotlib.transforms import Bbox

    ax = fig.axes[0]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    annotations = [a for a in ax.texts if isinstance(a, Annotation)]
    anchors = [tuple(ax.transData.transform(a.xy)) for a in annotations]
    legend = ax.get_legend().get_window_extent(renderer).padded(5)
    bounds = ax.get_window_extent(renderer).padded(-5)
    scale = fig.dpi / 72
    sizes = []
    for a in annotations:
        a.set_ha('center')
        a.set_va('center')
        a.update_positions(renderer)
        b = Text.get_window_extent(a, renderer)
        sizes.append((b.width + 8, b.height + 8))
    # Place crowded points first. Stable ties preserve original arm/topology order.
    crowded = [sum(math.dist(p, q) < 110 for q in anchors) for p in anchors]
    order = sorted(range(len(annotations)), key=lambda i: (-crowded[i], i))
    obstacles = [legend]
    placements = {}
    radii = (20, 30, 42, 56, 72, 92, 118, 150, 190, 235, 290)
    angles = (90, -90, 0, 180, 45, 135, -45, -135, 25, 155, -25, -155, 65, 115, -65, -115)
    for i in order:
        x, y = anchors[i]
        width, height = sizes[i]
        candidates = []
        for radius in radii:
            for angle in angles:
                theta = math.radians(angle)
                dx, dy = radius * math.cos(theta), radius * math.sin(theta)
                cx, cy = x + dx * scale, y + dy * scale
                box = Bbox.from_bounds(cx - width / 2, cy - height / 2, width, height)
                if not (bounds.x0 <= box.x0 and box.x1 <= bounds.x1
                        and bounds.y0 <= box.y0 and box.y1 <= bounds.y1):
                    continue
                if any(box.overlaps(other) for other in obstacles):
                    continue
                if any(box.padded(5).contains(*point) for point in anchors):
                    continue
                # Prefer short leaders, then vertical space away from curves.
                cost = radius + abs(dx) * .035
                candidates.append((cost, abs(dx), angle, dx, dy, box))
            if candidates:
                break
        if not candidates:
            raise ValueError(f'No collision-free label position: {annotations[i].get_text()}')
        _, _, _, dx, dy, box = min(candidates, key=lambda v: v[:3])
        annotations[i].set_position((dx, dy))
        annotations[i].set_zorder(5)
        obstacles.append(box)
        placements[i] = dict(text=annotations[i].get_text(), xy=list(annotations[i].xy),
                             offset_points=[dx, dy], reserved_box=list(box.extents))
    fig.canvas.draw()
    actual = [Text.get_window_extent(a, renderer).padded(2) for a in annotations]
    if any(a.overlaps(b) for i, a in enumerate(actual) for b in actual[i+1:]):
        raise ValueError('Final text bounding boxes overlap')
    return [placements[i] for i in range(len(annotations))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True,
                        help='Directory containing the seven original source files')
    parser.add_argument('--metrics', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root / 'experimental/glm52_six_curves_1k8k_c32'))
    reader = importlib.import_module('results')
    rows = json.loads(args.metrics.read_bytes())
    if len(rows) != 36 or len({r['case_id'] for r in rows}) != 36:
        raise ValueError('Expected all36 unique accepted metric rows')
    args.output.mkdir(parents=True, exist_ok=False)
    views = {}
    for relative, topology in (('', None), ('figures/ep4', 4), ('figures/ep8', 8)):
        destination = args.output / relative
        destination.mkdir(parents=True, exist_ok=True)
        fig, points = reader.figure(rows, topology)
        layout = place_labels(fig)
        fig.savefig(destination / 'pareto.png', dpi=180)
        import matplotlib
        with matplotlib.rc_context({'svg.fonttype': 'path'}):
            fig.savefig(destination / 'pareto.svg', metadata={'Date': None})
        groups = [g for g in reader.frontiers(rows) if topology is None or g['tp'] == topology]
        for name, value in [('plot-points.json', points), ('frontiers.json', groups)]:
            (destination / name).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
        views[relative or 'combined'] = dict(points=len(points), labels=layout, text_overlap_count=0)
        import matplotlib.pyplot as plt
        plt.close(fig)
    metrics = args.metrics.read_bytes()
    receipt = dict(status='PUBLICATION_LABEL_LAYOUT_ONLY', svg_text='outlined paths', metrics_sha256=hashlib.sha256(metrics).hexdigest(),
                   views=views, limits=['Annotation placement and SVG text outlines only; points/curves/axes/metrics unchanged.',
                                       'Bounding-box checks supplement visual PNG/SVG inspection.'])
    (args.output / 'LAYOUT.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'views': 3, 'labels': 72, 'text_overlaps': 0, 'output': str(args.output)}))


if __name__ == '__main__':
    main()
