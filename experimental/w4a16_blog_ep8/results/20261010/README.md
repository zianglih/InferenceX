# October 10 EP8 benchmark: complete results

Both models completed all 42 points on eight NVIDIA B300 GPUs: MegaMoE W4A4,
MegaMoE W4A16, and TRTLLM NVFP4 W4A4 at concurrency 1, 2, 4, 8, 16, 32, and 64,
with TP8 / EP8 / attention-DP8 and one model replica. All 7,620 measured requests
and 1,524 excluded warmups succeeded, with zero request failures and complete
native speculative-counter coverage.

The [combined report](REPORT.md) contains both models' plots, all 42 rows of exact
native counters, metric definitions, environment pins, and interpretation limits.
The [reusable recipe](../../README.md) documents setup, runtime settings, and
commands to run and render the study.

| Model | Speculation | Points | Measured / warmup requests |
| --- | --- | ---: | ---: |
| DeepSeek-V4.1 Flash | DSpark, five proposed draft tokens per verification | 21 | 3,810 / 762 |
| GLM-5.2 | EAGLE / MTP, three proposed draft tokens per verification | 21 | 3,810 / 762 |

## DeepSeek-V4.1 Flash

[Pareto PNG](dsv41/figures/pareto.png) · [Pareto SVG](dsv41/figures/pareto.svg) ·
[Acceptance-length PNG](dsv41/figures/acceptance-length.png) · [Acceptance-length SVG](dsv41/figures/acceptance-length.svg)

[Metrics JSON](dsv41/metrics.json) · [Metrics CSV](dsv41/metrics.csv) ·
[All signed backend comparisons](dsv41/comparisons.csv) · [Results summary](dsv41/RESULTS.md)

## GLM-5.2

[Pareto PNG](glm52/figures/pareto.png) · [Pareto SVG](glm52/figures/pareto.svg) ·
[Acceptance-length PNG](glm52/figures/acceptance-length.png) · [Acceptance-length SVG](glm52/figures/acceptance-length.svg)

[Metrics JSON](glm52/metrics.json) · [Metrics CSV](glm52/metrics.csv) ·
[All signed backend comparisons](glm52/comparisons.csv) · [Results summary](glm52/RESULTS.md)

## Measured source and checkpoint pins

| Component | Exact pin |
| --- | --- |
| SGLang | `22250e374abcff99e78e862da647a83b1c2ebe27`; [DSpark compatibility draft #7](https://github.com/zianglih/sglang/pull/7) |
| FlashInfer Python and cubin packages | `866c80d0c70a90624b4c2056d12d1543d709609e`; built from source, no released FlashInfer wheels |
| Benchmark recipe | `9d9e053d072568ecba7ad2543f3ded240d3d76f4`; later publication commits do not change this measured pin |
| Image | `lmsysorg/sglang:nightly-dev-cu13-20261010-961bcf48@sha256:53efab7e8255a47b19edc81a0f1ad37cd6c8341bfe8f448d268700b182b2f03d` |
| V4.1 checkpoint | `nvidia/DeepSeek-V4.1-Flash-NVFP4@3431dde3247c13b5957f682b1e3c6fcae2566079` |
| GLM-5.2 checkpoint | NVFP4 revision `53e0691e21895a3863a606dfd12910c69eba94ab` |

Acceptance length is measured completion tokens divided by native verification
count, including bonus tokens; acceptance rate is correct/proposed draft tokens.
The first prefill token and final output clipping mean these are not interchangeable.
Plans match across backends at each model/concurrency. W4A16 also affects eligible
dense NVFP4 linears. This single synthetic-workload sweep does not establish
statistical significance or output quality.

Full compressed logs, per-request counters, prompt plans, source-build artifacts,
and caches remain in cluster persistent storage. GitHub contains compact tables,
provenance, and plot inputs. This manual recipe remains outside the shared CI
matrix; its unregistered changelog key and validation boundary are documented in
the combined report.
