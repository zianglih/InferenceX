# GLM-5.2 curves with MTP acceptance-length labels

**English** | [中文](README_zh.md)

These views reuse the accepted 24-point [original release](../REPRODUCE.md). Every point is labeled with concurrency (`Cn`) and measured-only MTP acceptance length (`AL=N/A`). They introduce no new measurements and leave all 2,520 original payloads and the original `FILES.json` unchanged.

| View | PNG | SVG | Exact coordinates | Frontier membership |
| --- | --- | --- | --- | --- |
| TP=EP=DP4 | [EP4](figures/ep4/pareto.png) | [EP4](figures/ep4/pareto.svg) | [JSON](figures/ep4/plot-points.json) | [JSON](figures/ep4/frontiers.json) |
| TP=EP=DP8 | [EP8](figures/ep8/pareto.png) | [EP8](figures/ep8/pareto.svg) | [JSON](figures/ep8/plot-points.json) | [JSON](figures/ep8/frontiers.json) |
| Combined six curves | [Combined](figures/six-curves/pareto.png) | [Combined](figures/six-curves/pareto.svg) | [JSON](figures/six-curves/plot-points.json) | [JSON](figures/six-curves/frontiers.json) |

Each standalone figure contains three independent backend frontiers and all 12 points at C4, C8, C16 and C32: **1,800 successful measured requests and 360 warmups per topology**, with zero measured failures. The combined view contains all 24 accepted points, 3,600 measured requests and 720 warmups. Lines connect nondominated points within each backend/topology group; they are not a pooled frontier across backends. All plots use English labels.

- MegaMoE W4A4: green `#009E73`.
- MegaMoE W4A16: orange `#E69F00`.
- TRTLLM NVFP4 W4A4: blue `#0072B2`.
- Standalone views retain solid lines and circles. The combined view uses solid/circle for EP4 and dashed/triangle for EP8. TP=EP=DP attention throughout.

The inherited reader computes **x = 1,000 / saved median TPOT in milliseconds** and **y = completed output tokens / the complete measured interval / GPU count**. All coordinates and frontier memberships match the original release exactly. The EP4/EP8 coordinate and frontier JSON files remain byte-identical. Axes scale independently; compare tick values when comparing images.

## Acceptance-length definition and scope

The [metric sidecar](figures/acceptance-length.json) records all 24 cases as `measured_acceptance_length: null` with `status: unavailable`, the missing-counter reason, and exact descriptors for their saved result and before/after server metadata. Every plot point displays **AL=N/A**; this is not zero and no approximate value is substituted.

The desired native aggregate excludes warmup requests:

```text
Measured-only AL = sum(completion_tokens) / sum(spec_verify_ct)
                   over measured requests only
```

The native completion-token convention includes the bonus token. The benchmark client did not request or retain per-request `spec_verify_ct` values, and measurement-boundary counter deltas were not saved. The before snapshot precedes warmups; the after snapshot exposes per-rank cumulative ratios rather than the missing counts. These retained artifacts therefore cannot establish the exact measured-only aggregate. Rounded logging windows and warmup-inclusive rank means are not used as substitutes.

The throughput and latency coordinates remain valid and unchanged. Marking AL unavailable does not alter frontier membership, request totals or the benchmark results. Recovering exact measured-only AL requires a future run that retains the native per-request completion and verification counts, or equivalent correctly bounded counters; this plot update performs no new run.

Nominal lengths are 1,024 input / 8,192 output, ratio 0.8, seed 0. EAGLE uses steps 3 / top-k 1 / draft tokens 4. Backend quantization and fast-math defaults are retained. W4A16 selection also affects eligible dense NVFP4 linears; BF16 describes the draft MoE path, not every draft tensor. Saved ITL is chunk spacing at stream interval 30. Whole-interval throughput is not separately timed decode. Sequential observations do not establish causality, significance or numerical/content equivalence. The [complete report and raw tables](../results/RESULTS.md) retain the original methods and limitations.

## Reproduce using only the public release

Use Python 3.11+ with Matplotlib. From this directory, select a new output directory:

```sh
python3 -B render.py --published-root .. --output ../regenerated-annotated-views
```

The helper verifies all 2,520 original payloads against the pinned original manifest before and after rendering. It validates the complete sealed raw campaign through the unchanged published reader, checks the published metric rows, and reuses its figure/frontier functions. It adds AL labels, deterministic placement with leader lines, view titles and scope footnotes. Label placement rejects overlaps with other labels or point markers. The output contains EP4, EP8 and combined PNG/SVG figures, exact coordinates/frontiers, the AL sidecar and relative input provenance. No network, private evidence path or new benchmark is required.

Rendering used Python 3.14.6, Matplotlib 3.10.6, NumPy 2.5.3 and DejaVu Sans. Image byte identity can depend on Python, Matplotlib and fonts; coordinate, frontier and AL-status JSON are the reproducibility targets. `INPUTS.json` binds the unchanged public inputs. The add-on `FILES.json` covers this directory only, excluding itself, and does not replace the original release manifest. This is a plot/annotation update, with no recipe or runtime change.
