# Reproduce the six GLM-5.2 frontiers

This selected raw-data bundle contains 36 points, 3,780 measured requests and 756 scheduled warmup requests. Publication, visual inspection and preservation status are tracked separately; PROVENANCE.json records this local preparation stage.

From this directory, use Python 3.11+ with Matplotlib and a new output directory:

```bash
python3 -B source/experimental/glm52_six_curves_1k8k_c32/results.py --run-root raw --output ../regenerated-six-curves
```

All seven measured reader/recipe/client files and two unchanged Python package initializers are included. The initializers keep the bundled infx package authoritative when another infx distribution is installed; the seven measured files and import-origin checks are unchanged. The command rehashes every case member, checks the sealed producer environment and command joins across checkout relocation, and regenerates full JSON/CSV scalar tables, all 54 paired comparisons, point coordinates, six frontiers and PNG/SVG. Remote paths in raw receipts are preserved as evidence; no remote filesystem is needed. Plot byte identity can depend on Python/Matplotlib/fonts; saved numeric coordinates, scalar values, pair arithmetic and frontier membership are the reproducibility targets.

## Environment and methods

- Image: `lmsysorg/sglang:nightly-dev-cu13-20260930-cae69be5@sha256:0412c5b792cb35706de0359de4a1af52c160d4bdef6ff7530baf9df4e2a7b0b4`.
- SGLang: `9d38e0530a1e35d1756a7fabf044bc39b77209b8`; FlashInfer: `a03f2205263d4e691d68e485bff287e37a19b6c3`.
- Checkpoint revision: `53e0691e21895a3863a606dfd12910c69eba94ab`. The exact measured settings, package freeze, launch commands and logs are retained per case.
- One B300 node; each group uses TP=EP=DP attention 4 or 8. MegaMoE W4A4 is green #009E73; MegaMoE W4A16 is orange #E69F00; TRTLLM NVFP4 W4A4 is blue #0072B2. The combined view uses TP4 solid/circle and TP8 dashed/triangle. Both standalone EP4/EP8 views use solid/circle.
- C32 calibrates first, followed by C1/C2/C4/C8/C16 for each group. Each case uses 2C warmups and 10C measured requests, nominal input/output 1,024/8,192, range ratio 0.8 and seed 0. Exact requested/completed arrays remain in the raw case files.
- EAGLE steps 3 / top-k 1 / draft tokens 4; draft TRTLLM/none BF16 MoE path; FP8 E4M3 KV, static memory 0.8, global prefill chunk 32,768, prefill graphs disabled, stream interval 30.
- Measured MTP AL = sum(final completion_tokens) / sum(spec_verify_ct), including native bonus scope; acceptance rate = sum(correct drafts) / sum(proposed drafts). Every measured request must have valid counters and exact ordered output-length joins; warmups are excluded. No lifetime or log-window estimate is used.
- Runtime uses lmsysorg/sglang:nightly-dev-cu13-20260930-cae69be5@sha256:0412c5b792cb35706de0359de4a1af52c160d4bdef6ff7530baf9df4e2a7b0b4 and Torch 2.13.0+cu130, distinct from the September 29 baseline. Both installation pip commands exited 0; the original installer terminal remains failed after the namespace postcheck, followed by a separately accepted validation-only continuation with no reinstall. Preserve the reviewed shared FlashInfer/TorchC helper exception. pip check exited 1 with 14 conflict/missing-dependency lines (13 pre-existing plus the custom FlashInfer version against image SGLang metadata); neither a clean dependency check nor old/new runtime equality is claimed.
- x = 1,000 / saved median TPOT milliseconds; y = output tokens / the client's complete measured perf_counter interval / GPU count. This is not separately timed decode. Unix phase endpoints use a separate clock.
- Current backend defaults are retained. W4A16 selection can affect eligible dense NVFP4 linears as well as MegaMoE experts. Draft BF16 names its MoE path, not every tensor.
- Saved ITL is chunk spacing at stream interval 30. Saved percentiles are retained, not independently reconstructed from unsaved per-request latency samples. Sequential backend/topology/cache history does not establish causality, significance, numerical equivalence or response-content equivalence.
- This selected bundle is not the full source/cache/wheel archive, a whole-container snapshot or proof of installed RECORD byte equality. Preservation, checkpoint retention and owned-node cleanup have independent receipts.

[Complete result report](results/RESULTS.md) · [Saved scalar JSON](results/raw-saved-scalars.json) · [All paired metrics](results/paired-comparisons.csv) · [PNG](results/pareto.png) · [SVG](results/pareto.svg) · [EP4 PNG](results/figures/ep4/pareto.png) · [EP4 SVG](results/figures/ep4/pareto.svg) · [EP8 PNG](results/figures/ep8/pareto.png) · [EP8 SVG](results/figures/ep8/pareto.svg)

The TRTLLM NVFP4 arm supplies no custom per-token-scaling or quantizer-math override. Its selected SGLang helper omits the backend argument; pinned FlashInfer fp4_quantize defaults to CUDA and calls fp4_quantize_sm100 through the SM103 module. CuTeDSL-only math flags do not establish the selected CUDA path’s reciprocal or approximation behavior; no such low-level math claim is made. Fixed checkpoint global scale and runtime vector16 E4M3 block scales are established separately. The W4A16 opt-in also affects eligible dense NVFP4 linears under current defaults; it is not an isolated MoE-only precision change. Draft BF16 describes its MoE path, not every tensor. This reader checks sealed settings and accounting; actual native kernel/tactics/calibration, full terminal and preservation acceptance remain separate reviews.

Case C17 (MegaMoE W4A16, TP=EP=DP4, C8) retained post-case GPU memory [4231, 236413, 4426, 2170, 0, 0, 0, 0] MiB at 2026-09-30T16:16:37Z, with zero utilization and an empty subsequent application query. The producer checks eight GPU rows and no reported applications; the GPU and application queries are sequential. Acceptance under that predicate does not establish zero-memory, atomic or continuous idle, current idle, a causal explanation, or eventual reclamation. Leader exit 0 also does not establish every child exited gracefully.

Warmup counts are scheduled counts: the warmup phase was awaited and its outputs discarded before measurement. Per-warmup success records were not retained. Measured AL is sum(final completion_tokens)/sum(spec_verify_ct), including the native bonus convention, and rate is sum(correct drafts)/sum(proposed drafts), over all measured requests only. Neither statistic is an average of per-request or DP-rank ratios, and no completion_tokens = correct_drafts + spec_verify_ct identity is assumed.

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

## Additional concurrency 2–32 views / 额外的并发 2–32 视图

The full C1–32 figures and all 36-point raw/numeric/source files above are unchanged.
The additional `results/c2-32/` views select C2/C4/C8/C16/C32 from those
same accepted rows: 30 combined points, 15 per topology, 3,720 measured requests
(1,860 per topology). This is a display subset, not a rerun. Frontiers are recomputed
within each of its six backend/topology groups after filtering; exact measured AL
and rate, coordinate definitions, styles and outlined SVG treatment are retained.

From the bundle root, after the full reader command above (or using saved metrics):

```sh
python3 -B publication-layout/render_concurrency_subset.py --source-root source --metrics results/raw-metrics.json --min-concurrency 2 --output ../regenerated-concurrency-2-32
```

[Combined PNG](results/c2-32/pareto.png) · [Combined SVG](results/c2-32/pareto.svg) · [EP4 PNG](results/c2-32/figures/ep4/pareto.png) · [EP4 SVG](results/c2-32/figures/ep4/pareto.svg) · [EP8 PNG](results/c2-32/figures/ep8/pareto.png) · [EP8 SVG](results/c2-32/figures/ep8/pareto.svg)

原 C1–32 全图、36 点 raw/数值/源码完全不变。新三图仅筛选相同测量中的
C2/C4/C8/C16/C32，共30点、每种拓扑15点；3,720个测量请求并非新增测量。
筛选后重新计算各组前沿，保留精确测量 AL、坐标、图例及SVG轮廓文字。
