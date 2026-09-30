## Publication annotation layout / 发表图表标注排版

The seven immutable measured source files reproduce the original numeric tables,
points, frontiers and initial images. The final published images use the separate
annotation-only wrapper below. It calls the unchanged `results.figure()` and only
moves point labels, retaining the actual Cn + measured-only AL text and coordinates.
Run both steps from this bundle; each output directory must be absent:

```sh
python3 -B source/experimental/glm52_six_curves_1k8k_c32/results.py --run-root raw --output ../regenerated-six-curves
python3 -B publication-layout/render_publication.py --source-root source --metrics ../regenerated-six-curves/raw-metrics.json --output ../regenerated-publication-layout
```

The second output contains the combined PNG/SVG and `figures/ep4`, `figures/ep8`
views. Compare its six `plot-points.json` / `frontiers.json` files byte-for-byte with
the first output and the saved `results/` files. Numeric equality is mandatory.
SVG text is outlined by the separate wrapper to avoid dependence on viewer fonts.
Exact image bytes can depend on Python, Matplotlib and fonts. Inspect all three
PNGs and SVGs; bounding-box checks do not prove that every leader line is optimal.
The bundled `publication-layout/LAYOUT.json` records the original layout operation.
This step adds no benchmark, numerical, retention or deletion acceptance.

七份原始测量源码保持不变。先复算全部原始结果，再运行独立的标注排版脚本；
第二步只移动标签，不改变测量值、点坐标或前沿。三个视图均需核对 PNG/SVG，
六份点坐标和前沿 JSON 必须逐字节一致。旧的合格报告包及其清单仍单独保留。
