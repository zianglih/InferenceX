# GLM-5.2 B300: TRT-LLM, MegaMoE and CuTe split MoE

[English](comparison.md) | [中文](comparison_zh.md)

48 completed cases, 16 matched three-arm coordinates and 30,720 successful measured requests. All three full audits passed. The original aligned TRT-LLM and MegaMoE measurements are reused unchanged; only CuTe is newly measured. Historical DP1 and interrupted .85 results are excluded.

Primary axes follow InferenceX: **per-request interactivity = 1000 / median_tpot_ms** (tok/s/user), and **output_throughput / active GPU count** (tok/s/GPU). Both are higher-is-better. Each arm's frontier pools TP4 and TP8; every client C/TP/DP/EP point remains labelled. The dotted green frontier pools all three arms. This is output-only throughput over the benchmark interval, not a separately timed decode-only phase. [Pinned metric, grouping and frontier definitions](SOURCE_METRICS.md).

All arms use TP=DP=EP, DP attention, static memory fraction .80, disabled prefill graphs, server cap=max(client C, TP), and TRT-LLM/none MTP. TP8/C4 still means client C=4. Workload labels are sampled ISL/OSL caps at range ratio .8, request-rate=inf, with one measurement per point. Actual request lengths need not match. Median TPOT is the saved client aggregate, not independently reconstructible without per-request latency arrays. Request success is not an accuracy evaluation or a latency-SLO qualification.

Runtime/precision/backend and FlashInfer source differences are explicit below. TRT/Mega keep the original tested recipe; CuTe uses its separately pinned recipe. This compares complete serving configurations, not an isolated kernel or precision speedup. The Mega/CuTe ratios can be below 1 and changes can be negative.

## Runtime provenance

| Arm | Run | Image | SGLang | Tested InferenceX | FlashInfer version / commit | CuTe | Static memory fraction |
|---|---|---|---|---|---|---|---|
| W4A4 TRT-LLM | c2-w4a4-trtllm-dp-mem80-20260920 | lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | 86b464d794a8804a05e0c95f679d6bb02e120889 | 0.6.18 / image-provided | 4.6.2 | 0.8 |
| W4A16 MegaMoE | c2-w4a16-megamoe-mem80-20260920 | lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | 86b464d794a8804a05e0c95f679d6bb02e120889 | 0.7.0 / ad0a5e5e78e57070ec7c582efe733cb55cd8839f | 4.7.1 | 0.8 |
| W4A16 CuTe split MoE | c2-w4a16-cutedsl-mem80-20260920 | lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | 3433a0c1169a6b162edf91c7ea193196c08a6386 | 0.7.0 / f9dd3c10541e087b716772245a9d033499745048 | 4.7.1 | 0.8 |

## 1k1k

![1k1k](figures/1k1k_output_per_gpu_vs_interactivity_pareto.png)

[SVG](figures/1k1k_output_per_gpu_vs_interactivity_pareto.svg)

## 8k1k

![8k1k](figures/8k1k_output_per_gpu_vs_interactivity_pareto.png)

[SVG](figures/8k1k_output_per_gpu_vs_interactivity_pareto.svg)

## Matched operating points

Ratios are **MegaMoE / CuTe** at identical configured client concurrency and topology. Change (%) = (ratio - 1) × 100; no interpolation or fixed-interactivity matching. TRT-LLM remains the reference column.

| Scenario | TP/DP/EP | C | TRT output/GPU | Mega output/GPU | CuTe output/GPU | Mega/CuTe output × / % | TRT interactivity | Mega interactivity | CuTe interactivity | Mega/CuTe interactivity × / % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1k1k | 4/4/4 | 4 | 132.286 | 128.056 | 119.994 | 1.067 / +6.72% | 141.276 | 137.328 | 133.955 | 1.025 / +2.52% |
| 1k1k | 4/4/4 | 8 | 208.042 | 203.410 | 199.438 | 1.020 / +1.99% | 112.531 | 109.817 | 108.476 | 1.012 / +1.24% |
| 1k1k | 4/4/4 | 16 | 327.841 | 315.064 | 308.876 | 1.020 / +2.00% | 88.190 | 85.373 | 84.482 | 1.011 / +1.05% |
| 1k1k | 4/4/4 | 32 | 489.798 | 526.362 | 472.571 | 1.114 / +11.38% | 66.163 | 71.315 | 63.163 | 1.129 / +12.91% |
| 1k1k | 4/4/4 | 64 | 679.053 | 749.323 | 643.768 | 1.164 / +16.40% | 44.277 | 49.334 | 42.193 | 1.169 / +16.92% |
| 1k1k | 4/4/4 | 128 | 1036.160 | 1072.480 | 917.364 | 1.169 / +16.91% | 33.362 | 34.659 | 29.414 | 1.178 / +17.83% |
| 1k1k | 4/4/4 | 256 | 1235.308 | 1466.501 | 1324.609 | 1.107 / +10.71% | 19.416 | 23.332 | 21.067 | 1.108 / +10.75% |
| 1k1k | 8/8/8 | 4 | 63.806 | 65.905 | 61.015 | 1.080 / +8.01% | 140.017 | 139.197 | 132.888 | 1.047 / +4.75% |
| 8k1k | 4/4/4 | 4 | 118.401 | 107.459 | 107.988 | 0.995 / -0.49% | 138.479 | 120.774 | 124.469 | 0.970 / -2.97% |
| 8k1k | 4/4/4 | 8 | 183.116 | 162.419 | 171.712 | 0.946 / -5.41% | 102.415 | 93.224 | 97.039 | 0.961 / -3.93% |
| 8k1k | 4/4/4 | 16 | 262.413 | 222.772 | 227.677 | 0.978 / -2.15% | 74.674 | 63.508 | 65.858 | 0.964 / -3.57% |
| 8k1k | 4/4/4 | 32 | 362.701 | 304.209 | 334.263 | 0.910 / -8.99% | 49.637 | 41.147 | 46.117 | 0.892 / -10.78% |
| 8k1k | 4/4/4 | 64 | 474.733 | 391.166 | 418.560 | 0.935 / -6.54% | 31.160 | 25.672 | 27.338 | 0.939 / -6.09% |
| 8k1k | 4/4/4 | 128 | 586.492 | 470.625 | 509.864 | 0.923 / -7.70% | 18.873 | 15.073 | 16.455 | 0.916 / -8.40% |
| 8k1k | 4/4/4 | 256 | 694.866 | 550.249 | 584.828 | 0.941 / -5.91% | 11.045 | 8.757 | 9.304 | 0.941 / -5.88% |
| 8k1k | 8/8/8 | 4 | 57.519 | 56.231 | 53.237 | 1.056 / +5.62% | 128.753 | 121.960 | 116.317 | 1.049 / +4.85% |

Output units: tok/s/GPU; interactivity: tok/s/user. Full precision is in the paired JSON and raw tables.

## Audit notes and complete evidence

Zero invariant mismatches does not mean warning-free logs. Original audit notes are retained verbatim below.

[Independent first-case and TP8/C4 calibration, exact raw files and runtime receipts](audits/calibration/index.md).

- w4a4_trtllm: [audit](audits/w4a4_trtllm.md), [JSON](audits/w4a4_trtllm.json), [all printed client results](w4a4_trtllm_raw_client_summaries.md).
  - `1k1k/tp4_conc128`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc128`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc16`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc256`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc32`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc4`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc64`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc8`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp8_conc4`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp8_conc4`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc128`: Review phase-resolved error_label; measured success is not an error-free log claim
  - `8k1k/tp4_conc128`: Review phase-resolved traceback_header; measured success is not an error-free log claim
  - `8k1k/tp4_conc128`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc16`: Review phase-resolved error_label; measured success is not an error-free log claim
  - `8k1k/tp4_conc16`: Review phase-resolved traceback_header; measured success is not an error-free log claim
  - `8k1k/tp4_conc16`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `8k1k/tp4_conc32`: Review phase-resolved error_label; measured success is not an error-free log claim
  - `8k1k/tp4_conc32`: Review phase-resolved traceback_header; measured success is not an error-free log claim
  - `8k1k/tp4_conc32`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `8k1k/tp4_conc4`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `8k1k/tp4_conc64`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `8k1k/tp4_conc8`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp8_conc4`: Review phase-resolved error_label; measured success is not an error-free log claim
  - `8k1k/tp8_conc4`: Review phase-resolved traceback_header; measured success is not an error-free log claim
- w4a16_megamoe: [audit](audits/w4a16_megamoe.md), [JSON](audits/w4a16_megamoe.json), [all printed client results](w4a16_megamoe_raw_client_summaries.md).
  - `1k1k/tp4_conc128`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc128`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc16`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc256`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc32`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc64`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc8`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp8_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp8_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc128`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc128`: Review phase-resolved error_label evidence; successful measurement does not make logs error-free
  - `8k1k/tp4_conc16`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc256`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc32`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc64`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc8`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp8_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp8_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- w4a16_cutedsl: [audit](audits/w4a16_cutedsl.md), [JSON](audits/w4a16_cutedsl.json), [all printed client results](w4a16_cutedsl_raw_client_summaries.md).
  - `1k1k/tp4_conc128`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc128`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc16`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc256`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc32`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc64`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc8`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp8_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp8_conc4`: Review phase-resolved error_label evidence; successful measurement does not make logs error-free
  - `1k1k/tp8_conc4`: Review phase-resolved traceback_header evidence; successful measurement does not make logs error-free
  - `8k1k/tp4_conc128`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc128`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc16`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc256`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc32`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc64`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc8`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp8_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp8_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures

## Appendix

[Complete 48-case raw metric tables](raw_metrics.md) · [Paired values and signed changes](paired_comparison.json) · [Selected plotting metrics and supplementary E2EL figures](figures/pareto.md). Raw case files are preserved under `runs/<run_id>/`; per-run manifests hash original files, including large logs/telemetry retained outside the compact bundle.
