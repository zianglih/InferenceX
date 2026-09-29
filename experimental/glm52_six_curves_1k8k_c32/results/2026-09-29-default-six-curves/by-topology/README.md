# GLM-5.2: three backend curves per topology

These additive views select the accepted EP4 and EP8 points from the [original six-curve release](../REPRODUCE.md). They introduce no new measurements and leave the original release and its `FILES.json` unchanged.

| View | PNG | SVG | Exact coordinates | Frontier membership |
| --- | --- | --- | --- | --- |
| TP=EP=DP4 | [EP4](figures/ep4/pareto.png) | [EP4](figures/ep4/pareto.svg) | [JSON](figures/ep4/plot-points.json) | [JSON](figures/ep4/frontiers.json) |
| TP=EP=DP8 | [EP8](figures/ep8/pareto.png) | [EP8](figures/ep8/pareto.svg) | [JSON](figures/ep8/plot-points.json) | [JSON](figures/ep8/frontiers.json) |

Each figure contains three independent backend frontiers and all 12 points at C4, C8, C16 and C32: **1,800 successful measured requests and 360 warmups per topology**, with zero measured failures. The complete campaign remains 24 points, 3,600 measured requests and 720 warmups. Lines connect nondominated points within each backend/topology group; they are not a pooled frontier across backends.

- MegaMoE W4A4: green `#009E73`.
- MegaMoE W4A16: orange `#E69F00`.
- TRTLLM NVFP4 W4A4: blue `#0072B2`.
- EP4: solid lines and circles. EP8: dashed lines and triangles. TP=EP=DP attention throughout.

The inherited reader computes **x = 1,000 / saved median TPOT in milliseconds** and **y = completed output tokens / the complete measured interval / GPU count**. Every coordinate and frontier member in these views exactly matches its corresponding original release entry. The axes auto-scale independently for readability; use their tick values when comparing the two images.

Nominal lengths are 1,024 input / 8,192 output, ratio 0.8, seed 0. EAGLE uses steps 3 / top-k 1 / draft tokens 4. Backend quantization and fast-math defaults are retained. W4A16 selection also affects eligible dense NVFP4 linears; BF16 describes the draft MoE path, not every draft tensor. Saved ITL is chunk spacing at stream interval 30. Whole-interval throughput is not separately timed decode. Sequential observations do not establish causality, significance or numerical/content equivalence. The [complete report and raw tables](../results/RESULTS.md) retain the original methods and limitations.

## Reproduce using only the public release

Use Python 3.11+ with Matplotlib. From this directory, select a new output directory:

```sh
python3 -B render.py --published-root .. --output ../regenerated-by-topology
```

The helper first verifies all 2,520 original payloads against the pinned original manifest. It loads and validates the complete sealed raw campaign through the published reader, checks equality with the published raw metric rows, and reuses its frontier and figure functions. Only the selected topology, empty legend artists, title and view-count text change. It requires exact coordinate/frontier equality and rehashes the original release again after rendering. It writes EP4/EP8 PNG, SVG, coordinates, frontiers and relative input provenance into the new output directory. No network, remote filesystem, private evidence path or new benchmark is required.

Rendering used Python 3.14.6, Matplotlib 3.10.6, NumPy 2.5.3 and DejaVu Sans. Plot byte identity may depend on Python, Matplotlib and fonts; the numeric JSON and frontier membership are the reproducibility targets. `INPUTS.json` binds the unchanged public inputs. `FILES.json` covers this additive folder only, excluding itself; it does not replace the original release manifest.
