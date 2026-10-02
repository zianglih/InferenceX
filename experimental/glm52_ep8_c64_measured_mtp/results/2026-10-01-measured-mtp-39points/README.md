# GLM-5.2 measured MTP: EP4 C1–32 and EP8 C1–64

**English** | [中文](README_zh.md)

The three additional EP8 C64 measurements extend the original 36-point campaign to **39 points, 5,700 successful measured requests and zero measured failures**. The 1,140 scheduled warmups are excluded from MTP counters; their discarded outputs do not provide an individual warmup success audit. The original 36 rows and all 13 existing C2–32 files are preserved exactly. There is no EP4 C64 measurement.

## Results

| New EP8 C64 arm | Measured requests | Interval (s) | Output tokens/s/GPU | 1,000 / median TPOT | Measured AL | Acceptance rate |
|---|---:|---:|---:|---:|---:|---:|
| MegaMoE W4A16 | 640 | 657.860377 | 898.231063 | 121.162281 | 3.533377831 | 0.844511100 |
| MegaMoE W4A4 | 640 | 654.374923 | 903.015389 | 122.926009 | 3.474205196 | 0.824809048 |
| TRTLLM W4A4 | 640 | 793.520819 | 744.669340 | 101.320310 | 3.519084691 | 0.839766361 |

Each C64 arm produced 4,727,285 output tokens from 590,968 input tokens. All 640 ordered requested and completed length arrays match across the three arms. The aggregate table retains saved latency tails and all signed regressions. There are 57 matched comparison groups (39 backend and 18 topology), or 1,710 metric rows. C64 contributes three backend pairs and no topology pair.

[39-point metrics](raw-metrics.csv) · [Saved scalars](raw-saved-scalars.csv) · [57 comparisons](paired-comparisons.csv) · [Settings and provenance](PROVENANCE.json)

| View | Points / measured requests | PNG | SVG |
|---|---:|---|---|
| Combined EP4 C1–32 / EP8 C1–64 | 39 / 5,700 | [PNG](pareto.png) | [SVG](pareto.svg) |
| EP4 C1–32 | 18 / 1,890 | [PNG](figures/ep4/pareto.png) | [SVG](figures/ep4/pareto.svg) |
| EP8 C1–64 | 21 / 3,810 | [PNG](figures/ep8/pareto.png) | [SVG](figures/ep8/pareto.svg) |
| Original C2–32, unchanged | 30 / 3,720 | [PNG](c2-32/pareto.png) | [SVG](c2-32/pareto.svg) |

![Combined measured-MTP frontier](pareto.png)

Green/orange/blue identify MegaMoE W4A4/W4A16/TRTLLM W4A4. The combined view uses solid circles for EP4 and dashed triangles for EP8, with six independent frontiers. Topology-specific views show three backend frontiers. Every point is annotated with concurrency and measured AL.

## Replot from public tables

Requires Python 3.11+ and Matplotlib. From this directory, choose absent output paths:

```sh
python3 -B render39.py --bundle . --output /absolute/path/to/new-39-plots
python3 -B render_concurrency_subset.py --source-root source --metrics base36-raw-metrics.json --min-concurrency 2 --output /absolute/path/to/new-original-c2-32-replay
```

The C2–32 replay intentionally uses `base36-raw-metrics.json`. Its minimum-only filter would include C64 if given the combined table. Public reproduction replays aggregate tables and figures; full server/client/setup logs, request arrays, native records, owner ledgers and detailed validators remain local. It cannot revalidate omitted raw evidence. The exported `join39.py` documents the local assembly; rebuilding that join requires local raw evidence and its original source/base locks. Image bytes can vary across rendering environments; coordinates, case identities and nondominated membership must agree.

## Workload and runtime

- Nominal 1,024 input / 8,192 output tokens; length ratio 0.8, seed 0, chat template and infinite request rate. Each point schedules `2C` warmups then `10C` measured requests. The extension runs Mega W4A4, Mega W4A16 and TRT W4A4 serially on the same eight-B300 node.
- TP=EP=DP attention=8 for C64; target `bfloat16` / `modelopt_fp4`, KV `fp8_e4m3`, memory fraction 0.8. Global chunk/max-prefill is 32,768; resolved local chunk is 4,096. Radix/prefill graphs are disabled. Target verification uses width 4, batches 1–8; the logged draft decode/extend captures use widths 1/4, batches 1–8.
- Real EAGLE: 3 steps, top-k 1, 4 draft tokens. Draft MoE is BF16 TRTLLM/none. AL = `sum(completion_tokens)/sum(spec_verify_ct)`; acceptance rate = `sum(correct_drafts)/sum(proposed_drafts)`, warmups excluded. Native bonus semantics are retained; do not assume `completion_tokens = correct_drafts + spec_verify_ct` or average request/rank ratios.
- x = `1000/median_tpot_ms`; y = output tokens / whole measured interval / GPU count. This is not separately timed decode throughput. Saved ITL is streamed chunk spacing at interval 30.
- Extension recipe `d11577979d1b7658fdaa7f5a2a2f8fdb104378f2`; SGLang `9d38e0530a1e35d1756a7fabf044bc39b77209b8`; FlashInfer `a03f2205263d4e691d68e485bff287e37a19b6c3`; Torch `2.13.0+cu130`; checkpoint revision `53e0691e21895a3863a606dfd12910c69eba94ab`.
- Image: `lmsysorg/sglang:nightly-dev-cu13-20260930-cae69be5@sha256:0412c5b792cb35706de0359de4a1af52c160d4bdef6ff7530baf9df4e2a7b0b4`.

## Evidence boundaries

Case/native/array and original inner/outer terminal reviews passed. For the three C64 cases, the benchmark clients returned 0; servers were terminated after measurement and returned -9, with recorded owner cleanup complete. This does not mean graceful server exits or continuous/current GPU-idle proof. Default INFO logs do not provide a direct native rank/PID/config join for every kernel.

The same installed environment and checkpoint are reused without reinstall or cache seed. New C64 run/HOME/TMP/compile/tactic namespaces give a different sequential cache history from the original 36 points. Compilation is shared within the extension, tactics separated by backend; provider/system-default caches are not claimed cold or isolated. W4A16 also affects eligible dense NVFP4 linears. BF16 draft describes the MoE route, not every tensor. No custom per-token, quantizer-fast-math, combine or IKR override is added. TRT's FI quantizer defaults to CUDA; CuTeDSL-only flags do not establish CUDA-path math.

The original failed installation and successful validation continuation remain distinct, with 14 dependency-conflict/missing-dependency lines preserved. The real manual matrix validation failed for its unregistered experimental key; these results do not establish scheduled sweep, eval or reuse eligibility. Historical September 29 measured-only AL remains unavailable. Single serial measurements do not establish quality/numerical equivalence, significance, isolated causality or universal cache hits/dispatch. Local selected archives and durable retention are tracked separately; no whole-container or installed-RECORD equality, tensor SHA, or node-deletion claim is made. DFlash remains held by user decision; the same node is retained.
