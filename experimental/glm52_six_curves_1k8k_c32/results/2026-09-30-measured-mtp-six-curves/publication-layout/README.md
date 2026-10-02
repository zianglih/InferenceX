# Publication plotting from saved tables

The seven immutable measured source files and two package initializers are retained.
The public wrappers reuse the original reader's plotting functions with saved
`results/raw-metrics.json`; full raw evidence is retained locally.

From the bundle root, using new output directories:

```sh
python3 -B publication-layout/render_publication.py --source-root source --metrics results/raw-metrics.json --output /absolute/path/to/new-full-plots
python3 -B publication-layout/render_concurrency_subset.py --source-root source --metrics results/raw-metrics.json --min-concurrency 2 --output /absolute/path/to/new-c2-32-plots
```

The full view has 36 points; C2/4/8/16/32 has 30. Each command makes combined,
EP4 and EP8 views, recomputes frontiers, and preserves measured AL/rate and point
coordinates. SVG text uses outlines. Existing published figures are byte-unchanged.
Table-based plotting does not replay omitted raw request, native or runtime evidence.
Full evidence replay requires the unchanged local bundle; see ../REPRODUCE.md.

<details><summary>中文</summary>

七份测量源码和两份 package initializer 均保持不变。以上公开绘图命令读取保存的
汇总表，分别生成全36点和 C2/4/8/16/32 的30点视图，不重复验证已移至本地的原始证据。
各自生成总图、EP4 和 EP8，重新计算前沿，保留 measured AL/rate 和坐标；SVG 使用轮廓文字。
完整证据重放需要未修改的本地原完整包。

</details>
