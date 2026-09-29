# GLM-5.2: six backend/topology curves at concurrency 4–32

[English](README.md) | [简体中文](README_zh.md)

This manual experiment compares three current backend selections at TP=EP=DP attention 4 and 8 on one eight-GPU B300 node. It is outside the scheduled InferenceX matrix. The recipe does not install packages, allocate a node, publish results, or delete storage. The [2026-09-29 measured results](results/2026-09-29-default-six-curves/results/RESULTS.md) contain **24 accepted points, 3,600 successful measured requests, zero failures and 720 warmups**, with **six Pareto frontiers**. [View the PNG](results/2026-09-29-default-six-curves/results/pareto.png) or [SVG](results/2026-09-29-default-six-curves/results/pareto.svg), [all saved scalars](results/2026-09-29-default-six-curves/results/raw-saved-scalars.csv), [all 36 matched comparisons](results/2026-09-29-default-six-curves/results/paired-comparisons.csv), and the [selected raw-data bundle and reproduction command](results/2026-09-29-default-six-curves/REPRODUCE.md).

The selected publication bundle is separate from full source/cache/wheel archival and checkpoint-retention verification, which remain pending. Node cleanup is on hold while Kimi reuse is considered; the completed benchmark does not imply node deletion.

## Matrix and fixed workload

| Arm ID | Target MoE runner | Target MoE A2A | Precision selector |
|---|---|---|---|
| `megamoe-w4a4` | `flashinfer_megamoe` | `flashinfer_megamoe` | Backend default; W4A16 selector absent |
| `megamoe-w4a16` | `flashinfer_megamoe` | `flashinfer_megamoe` | `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1` |
| `trtllm-w4a4` | `flashinfer_trtllm` | `none` | Backend default per-tensor NVFP4 W4A4 |

Each arm uses TP=EP=DP attention 4, then 8. Each topology runs client concurrency **32, 4, 8, 16**, in that order, so the largest requested point calibrates first. There are 24 points, 3,600 measured requests, and 720 warmup requests. Each point starts a new server, runs `2C` warmups and `10C` measured requests, then tears down only its recorded process owners before proceeding.

| Setting | Value |
|---|---|
| Target model | GLM-5.2 NVFP4, checkpoint revision `53e0691e21895a3863a606dfd12910c69eba94ab` |
| Nominal input/output | 1,024 / 8,192 tokens, random-range ratio 0.8, client seed 0 |
| Output sampling | 6,553–8,192 requested tokens; exact ordered requested/completed arrays retained |
| Traffic | Infinite request rate, client concurrency 4/8/16/32 |
| Target dtype/quantization | `bfloat16` / `modelopt_fp4` |
| KV cache | `fp8_e4m3` |
| Speculation | `EAGLE`: steps 3, top-k 1, draft tokens 4; real verification, no acceptance simulation |
| Draft MoE | `flashinfer_trtllm` / `none`, BF16 MoE path |
| Static memory fraction | 0.8 |
| Global chunked prefill | 32,768; resolved local attention budget 8,192 at DP4 or 4,096 at DP8 |
| Graphs | Prefill graphs disabled; configured decode maximum follows client concurrency |
| Server capacity | `max(C, TP)`; TP8/C4 therefore has server capacity 8 and local capacity 1 |
| Streaming | `stream_interval=30` |

The W4A16 selector also affects eligible dense NVFP4 linears under the pinned SGLang defaults. This is **not an isolated MoE-only precision change**. The recipe does not force a dense backend. Draft BF16 names the draft MoE path; it does not claim every draft tensor is BF16. Review the actual resolved arguments, full startup logs, loaded quantization and native kernel evidence before accepting a run.

No per-token activation flag or environment setting, quantization-fast-math disable flag, combine-dtype override, in-kernel-reduction override, or 4over6 tuning override is injected. SGLang supplies its own single-node MegaMoE NVSHMEM defaults. The child environment starts from the explicit `base_environment`, rejects inherited `SGLANG_*`, `FLASHINFER_*`, `NVSHMEM_*`, `TRTLLM_*`, loader-preload and device overrides, and then adds the required W4A16 selector, source paths, offline settings and owned cache paths. The sole SGLang environment exception is the exact existing image policy `SGLANG_RUST_BUILD_MODE=never`; other values and image build labels are rejected. Preflight records the origin/API of visible optional Rust extensions and explicitly records absent, unselected modules. This workload selects ChunkCache with disabled radix cache and the default HTTP server; it does not force a Cargo build or an unrelated Rust gate. Do not add tuning knobs to `base_environment`.

## Pinned example environment

- SGLang: `9d38e0530a1e35d1756a7fabf044bc39b77209b8`.
- FlashInfer: `a03f2205263d4e691d68e485bff287e37a19b6c3`.
- Image: `lmsysorg/sglang:nightly-dev-cu13-20260929-79cafec0@sha256:0f075735a6bf913a7cc1cd7ece4f526ae8af70fc5b88fdc02d9efe92a61cf3ae`.
- Runtime run ID: `glm52-six-curves-1k8k-c32-20260929-all24`.
- Owned short TMP: `/tmp/infx-g52-6c-0929`.

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

The run root and short TMP must be new, exclusive paths. The runner records an owner marker and three real AF_UNIX bind/cleanup probes in the actual TMP, then uses PID plus process-birth identities for child cleanup. It requires all eight physical GPUs to be idle before each point and after teardown. A successful short socket probe is not proof that every collective took its fast path.

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

The reader can run from a different checkout path. It reconstructs the producer's `PYTHONPATH` from the sealed benchmark command, cross-checks both launch environments and the actual client argv, and compares every other environment field exactly. The five recorded recipe/client source digests must match this checkout. Keep those source files with any public reproduction bundle; do not rewrite the raw remote paths or infer an unrecorded launch working directory.

Outputs include:

- `raw-metrics.json` / `.csv`: saved latency fields, derived rates, source pins and result/manifest SHA bindings.
- `raw-saved-scalars.json` / `.csv`: every scalar saved in each `result.json`, including scalar outcome fields; exact raw files remain the authority.
- `paired-comparisons.json` / `.csv`: Decimal precision 50 arithmetic with explicit baseline/comparison IDs. There are 24 same-topology backend pairs and 12 same-backend topology pairs; zero baselines have no percentage change.
- `pareto.png` / `.svg`, `plot-points.json`, `frontiers.json`: all 24 points and exactly six independently computed nondominated frontiers.
- `RESULTS.md`: a compact English report linked to the complete tables.

The x coordinate is `1000 / saved median_tpot_ms`; the y coordinate is `total_output_tokens / duration / GPU_count`. Duration is the client's complete measured interval from `time.perf_counter()`, not a separately timed decode interval; saved Unix phase endpoints use a different clock. Green `#009E73` is MegaMoE W4A4, orange `#E69F00` is MegaMoE W4A16, and blue `#0072B2` is TRTLLM W4A4. TP=EP=DP4 uses solid lines/circles and TP=EP=DP8 dashed lines/triangles. Every point has its C label; topology appears in every legend entry and machine-readable coordinate record.

Saved ITL measures streamed chunk spacing at interval 30, not per-token TPOT. MTP server-state averages can include warmup. Saved means, medians, standard deviations and percentiles are retained, not reconstructed from unsaved per-request latency samples. This single sequential campaign does not establish significance, isolated causality, numerical equivalence or response-content equivalence. Whole-run terminal, native calibration and durable preservation reviews are not replaced by the public accounting reader.

## Local behavioral validation

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/check.py
python3 -B experimental/glm52_six_curves_1k8k_c32/check_results.py
python3 -B experimental/glm52_six_curves_1k8k_c32/check_plot.py \
  --output /absolute/path/to/new-synthetic-layout-check
bash -n experimental/glm52_six_curves_1k8k_c32/benchmark_mtp.sh
```

The plot check needs Matplotlib and renders a prominently marked synthetic layout fixture. These checks exercise local process/cache ownership, recipe construction, sealed-reader rejection paths, arithmetic and graph rendering. They do not start a server or make GPU performance claims. The experiment has no scheduled matrix key or runner-pool registration; scheduling it through the normal matrix planner is unsupported.
