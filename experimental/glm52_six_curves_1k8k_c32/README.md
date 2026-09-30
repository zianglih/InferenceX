# GLM-5.2: six backend/topology curves at concurrency 1–32 with measured MTP counters

[English](README.md) | [简体中文](README_zh.md)

This manual recipe prepares a **new 36-point run** of three backend selections at TP=EP=DP attention 4 and 8 on one eight-GPU B300 node. Each successful point must save native speculative counters for every measured request. No new benchmark result is included by this script change. The experiment is outside the scheduled InferenceX matrix; scripts do not install packages, allocate nodes, publish results, or delete storage.

The immutable [2026-09-29 bundle](results/2026-09-29-default-six-curves/REPRODUCE.md) remains **24 accepted points, 3,600 successful measured requests and 720 warmups**, with six frontiers. Its client did not save measured speculative counters, so its measured-only MTP acceptance length is **unavailable**. The existing N/A plots and original raw payloads are historical evidence and are not rewritten by this rerun.

## Matrix and fixed workload

| Arm ID | Target MoE runner | Target MoE A2A | Precision selector |
|---|---|---|---|
| `megamoe-w4a4` | `flashinfer_megamoe` | `flashinfer_megamoe` | Backend default; W4A16 selector absent |
| `megamoe-w4a16` | `flashinfer_megamoe` | `flashinfer_megamoe` | `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1` |
| `trtllm-w4a4` | `flashinfer_trtllm` | `none` | Backend default per-tensor NVFP4 W4A4 |

Each arm uses TP=EP=DP attention 4, then 8. Each topology runs client concurrency **32, 1, 2, 4, 8, 16**, in that order, so the largest requested point calibrates first. There are 36 points, 3,780 measured requests, and 756 warmup requests. Each point starts a new server, runs `2C` warmups and `10C` measured requests, then tears down only its recorded process owners before proceeding.

| Setting | Value |
|---|---|
| Target model | GLM-5.2 NVFP4, checkpoint revision `53e0691e21895a3863a606dfd12910c69eba94ab` |
| Nominal input/output | 1,024 / 8,192 tokens, random-range ratio 0.8, client seed 0 |
| Output sampling | 6,553–8,192 requested tokens; exact ordered requested/completed arrays retained |
| Traffic | Infinite request rate, client concurrency 1/2/4/8/16/32 |
| Target dtype/quantization | `bfloat16` / `modelopt_fp4` |
| KV cache | `fp8_e4m3` |
| Speculation | `EAGLE`: steps 3, top-k 1, draft tokens 4; real verification, no acceptance simulation |
| Draft MoE | `flashinfer_trtllm` / `none`, BF16 MoE path |
| Static memory fraction | 0.8 |
| Global chunked prefill | 32,768; resolved local attention budget 8,192 at DP4 or 4,096 at DP8 |
| Graphs | Prefill graphs disabled; configured decode maximum follows client concurrency |
| Server capacity | `max(C, TP)`; low-C clients keep C requests in flight while each DP worker retains at least one server slot |
| Streaming | `stream_interval=30` |

The W4A16 selector also affects eligible dense NVFP4 linears under the pinned SGLang defaults. This is **not an isolated MoE-only precision change**. The recipe does not force a dense backend. Draft BF16 names the draft MoE path; it does not claim every draft tensor is BF16. Review the actual resolved arguments, full startup logs, loaded quantization and native kernel evidence before accepting a run.

No per-token activation flag or environment setting, quantization-fast-math disable flag, combine-dtype override, in-kernel-reduction override, or 4over6 tuning override is injected. SGLang supplies its own single-node MegaMoE NVSHMEM defaults. The child environment starts from the explicit `base_environment`, rejects inherited `SGLANG_*`, `FLASHINFER_*`, `NVSHMEM_*`, `TRTLLM_*`, loader-preload and device overrides, and then adds the required W4A16 selector, source paths, offline settings and owned cache paths. The sole SGLang environment exception is the exact existing image policy `SGLANG_RUST_BUILD_MODE=never`; other values and image build labels are rejected. Preflight records the origin/API of visible optional Rust extensions and explicitly records absent, unselected modules. This workload selects ChunkCache with disabled radix cache and the default HTTP server; it does not force a Cargo build or an unrelated Rust gate. Do not add tuning knobs to `base_environment`.

## Pinned example environment

- SGLang: `9d38e0530a1e35d1756a7fabf044bc39b77209b8`.
- FlashInfer: `a03f2205263d4e691d68e485bff287e37a19b6c3`.
- Image: `lmsysorg/sglang:nightly-dev-cu13-20260930-cae69be5@sha256:0412c5b792cb35706de0359de4a1af52c160d4bdef6ff7530baf9df4e2a7b0b4`.
- Runtime run ID: `glm52-six-curves-measured-mtp-20260930-all36`.
- Owned short TMP: `/tmp/infx-g52-mtp-0930`.

The exact `campaign_contract` must be `glm52-six-curves-measured-mtp-v1`. Legacy configurations are intentionally rejected by this new runner/reader.

`config.example.json` records the intended pins and example absolute paths, not proof of an installed environment. Resolve its Python, source, checkpoint and base-environment fields against the actual prepared node before launch. Use the same installation for all six groups. Record imports, versions, dependency conflicts, native peer/topology checks and setup receipts separately. Readiness and benchmark timeouts are failure guards, not performance estimates.

The runner rechecks tracked source cleanliness, full source commits, package freeze and local recipe/client digests at every case boundary. A source checkout does not by itself prove that all imported package bytes match it; actual preparation and native review remain required.

## Run and collect

From the InferenceX checkout, first review a local plan:

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/run.py \
  --config /absolute/path/to/actual-config.json --plan
```

After setup and ownership review, the sole campaign owner launches once on the prepared node:

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/run.py \
  --config /absolute/path/to/actual-config.json --run
```

The run root and short TMP must be new, exclusive paths. The runner records an owner marker and three real AF_UNIX bind/cleanup probes in the actual TMP, then uses PID plus process-birth identities for child cleanup. Before polling or reaping a tracked leader, it observes same-session descendants, including children of an exited but unreaped leader. This does not prove absence of arbitrary detached descendants outside the observed ownership set. It requires all eight physical GPUs to be idle before each point and after teardown. A successful short socket probe is not proof that every collective took its fast path.

Six tactic namespaces separate backend, precision and topology. Compilation caches are shared within this fresh campaign. The default example has no compilation seed. An explicitly configured seed must pass the existing manifest and compile-only-copy checks; tactic files are never seeded. Per-case cache snapshots are taken at quiescent boundaries, with exact tactic payloads and compilation file-stat inventories. No claim of “no JIT,” “no retuning,” or full compile-payload hashing follows from these snapshots.

Do not mutate inputs or scan live caches during measurement. Collect only sealed, quiescent case directories. Preserve failed cases, command stdout/stderr, ownership records and all terminal receipts. Complete runner and outer-process termination, independent raw/native review, publication, archive verification and storage retention are separate release gates.

## Read results and render six frontiers

Python 3.11+ is required. The full plot additionally needs Matplotlib. Copy the finalized campaign root and all exact case members, then use a new output directory:

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/results.py \
  --run-root /absolute/path/to/collected-run \
  --output /absolute/path/to/new-results
```

While the campaign runs, add `--partial` to validate only finalized cases and write partial tables without a final plot. The full reader rejects an incomplete or misidentified grid, any failed client or incomplete owned cleanup, missing startup probes, modified sealed evidence, differing resolved backend settings, or mismatched same-concurrency ordered request arrays.

The reader can run from a different checkout path. It reconstructs the producer's `PYTHONPATH` from the sealed benchmark command, cross-checks both launch environments and the actual client argv, and compares every other environment field exactly. The six recorded recipe/client source digests (including the pure speculative-metrics reducer) must match this checkout. Keep those source files with any public reproduction bundle; do not rewrite the raw remote paths or infer an unrecorded launch working directory.

Outputs include:

- `raw-metrics.json` / `.csv`: saved latency fields, derived rates, source pins and result/manifest SHA bindings.
- `raw-saved-scalars.json` / `.csv`: every scalar saved in each `result.json`, including scalar outcome fields; exact raw files remain the authority.
- `paired-comparisons.json` / `.csv`: Decimal precision 50 arithmetic with explicit baseline/comparison IDs. There are 36 same-topology backend pairs and 18 same-backend topology pairs; zero baselines have no percentage change.
- `pareto.png` / `.svg`, `plot-points.json`, `frontiers.json`: all 36 points and exactly six independently computed nondominated frontiers.
- `figures/ep4/` and `figures/ep8/`: separate 18-point, three-frontier views with matching coordinates and AL; both standalone views use solid lines/circles. The combined EP8 view retains dashed lines/triangles.
- `RESULTS.md`: a compact English report linked to the complete tables.

The x coordinate is `1000 / saved median_tpot_ms`; the y coordinate is `total_output_tokens / duration / GPU_count`. Duration is the client's complete measured interval from `time.perf_counter()`, not a separately timed decode interval; saved Unix phase endpoints use a different clock. Green `#009E73` is MegaMoE W4A4, orange `#E69F00` is MegaMoE W4A16, and blue `#0072B2` is TRTLLM W4A4. TP=EP=DP4 uses solid lines/circles and TP=EP=DP8 dashed lines/triangles. Every point has its C and measured AL labels; topology appears in every legend entry and machine-readable coordinate record.

Saved ITL measures streamed chunk spacing at interval 30, not per-token TPOT. Measured MTP counters cover only measured requests, as defined below. Saved means, medians, standard deviations and percentiles are retained, not reconstructed from unsaved per-request latency samples. This single sequential campaign does not establish significance, isolated causality, numerical equivalence or response-content equivalence. Whole-run terminal, native calibration and durable preservation reviews are not replaced by the public accounting reader.

## Measured MTP contract

The wrapper explicitly passes `--capture-speculative-metrics` through the shared Bash bridge. Its default is off for other recipes. Native OpenAI-compatible responses must return final `usage.completion_tokens` and `spec_tokens_details` (`spec_verify_ct`, `spec_num_correct_drafts`, `spec_num_proposed_drafts`, native length/rate). Raw records retain canonical measured-request order. Warmup responses are requested with the same format but never enter the aggregate.

- **Acceptance length:** `sum(completion_tokens) / sum(spec_verify_ct)` over measured requests, including the native bonus-token convention.
- **Acceptance rate:** `sum(spec_num_correct_drafts) / sum(spec_num_proposed_drafts)` over those same requests.
- The client saves coverage and raw counters even when unavailable, then exits nonzero. The runner and reader require complete coverage, a positive denominator, exact pure-reducer replay, and completion-token equality with every ordered output length. Partial, missing, malformed or internally inconsistent counters cannot produce an accepted point. No rank-mean, log-window, output-token-weighted estimate, or synthetic AL is substituted.
- CSV/JSON summaries expose measured AL/rate and coverage. Paired AL/rate comparisons recompute ratios from integer counters with Decimal precision 50. Exact per-request details remain in sealed `result.json`.

## Reproduce the historical 24-point bundle

Use its frozen source reader, not the new 36-point reader. From this checkout:

```bash
cd experimental/glm52_six_curves_1k8k_c32/results/2026-09-29-default-six-curves
python3 -B source/experimental/glm52_six_curves_1k8k_c32/results.py \
  --run-root raw --output /absolute/path/to/new-historical-reproduction
```

That command retains the old 24-point contract and never invents measured MTP values. New 36-point results must be saved in a separate result directory after full actual review; do not overwrite this historical release.

## Local behavioral validation

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/check.py
python3 -B experimental/glm52_six_curves_1k8k_c32/check_results.py
python3 -B experimental/glm52_six_curves_1k8k_c32/check_plot.py \
  --output /absolute/path/to/new-synthetic-layout-check
bash -n experimental/glm52_six_curves_1k8k_c32/benchmark_mtp.sh
```

The plot check needs Matplotlib and renders a prominently marked synthetic layout fixture. These checks exercise local process/cache ownership, recipe construction, sealed-reader rejection paths, arithmetic and graph rendering. They do not start a server or make GPU performance claims. The experiment has no scheduled matrix key or runner-pool registration; scheduling it through the normal matrix planner is unsupported.
