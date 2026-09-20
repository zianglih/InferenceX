# CuTe W4A16 split-MoE raw audit

16 cases; 10240 measured requests; 0 issues; 0 missing coordinates.

First-case independent calibration verified: /Users/ziangli/playground/projects/inferencex-glm52-b300-config-audit/artifacts/cutedsl-first-case-independent-review.json. TP8/C4 independent calibration verified: /Users/ziangli/playground/projects/inferencex-glm52-b300-config-audit/artifacts/cutedsl-tp8-independent-review.json.

| Case | Completed | Output tok/s | Output/GPU | Reported median TPOT ms | Derived tok/s/user | Issues |
|---|---:|---:|---:|---:|---:|---:|
| 1k1k/tp4_conc128 | 1280/1280 | 3669.454522 | 917.363631 | 33.997472 | 29.413951 | 0 |
| 1k1k/tp4_conc16 | 160/160 | 1235.505336 | 308.876334 | 11.836847 | 84.481959 | 0 |
| 1k1k/tp4_conc256 | 2560/2560 | 5298.435932 | 1324.608983 | 47.468109 | 21.066775 | 0 |
| 1k1k/tp4_conc32 | 320/320 | 1890.285956 | 472.571489 | 15.831964 | 63.163355 | 0 |
| 1k1k/tp4_conc4 | 40/40 | 479.977945 | 119.994486 | 7.465220 | 133.954517 | 0 |
| 1k1k/tp4_conc64 | 640/640 | 2575.072059 | 643.768015 | 23.700496 | 42.193209 | 0 |
| 1k1k/tp4_conc8 | 80/80 | 797.750230 | 199.437557 | 9.218645 | 108.475815 | 0 |
| 1k1k/tp8_conc4 | 40/40 | 488.123068 | 61.015383 | 7.525125 | 132.888160 | 0 |
| 8k1k/tp4_conc128 | 1280/1280 | 2039.455228 | 509.863807 | 60.771579 | 16.455060 | 0 |
| 8k1k/tp4_conc16 | 160/160 | 910.706285 | 227.676571 | 15.184101 | 65.858361 | 0 |
| 8k1k/tp4_conc256 | 2560/2560 | 2339.312597 | 584.828149 | 107.482066 | 9.303878 | 0 |
| 8k1k/tp4_conc32 | 320/320 | 1337.053618 | 334.263405 | 21.684087 | 46.116767 | 0 |
| 8k1k/tp4_conc4 | 40/40 | 431.952304 | 107.988076 | 8.034131 | 124.468965 | 0 |
| 8k1k/tp4_conc64 | 640/640 | 1674.238047 | 418.559512 | 36.579166 | 27.337966 | 0 |
| 8k1k/tp4_conc8 | 80/80 | 686.846284 | 171.711571 | 10.305170 | 97.038671 | 0 |
| 8k1k/tp8_conc4 | 40/40 | 425.899563 | 53.237445 | 8.597220 | 116.316665 | 0 |

## Runtime installation issues

None.

## Calibration issues

None.

## Discovery issues

None.

## Case issues

None.

## Review notes

- pip-check diagnostics changed during the allowed provider replacement; inspect retained before/after text
- pip-check reports dependency diagnostics; installation receipts alone do not certify a clean dependency resolver
- 1k1k/tp4_conc128: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 1k1k/tp4_conc128: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 1k1k/tp4_conc16: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 1k1k/tp4_conc16: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 1k1k/tp4_conc256: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 1k1k/tp4_conc256: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 1k1k/tp4_conc32: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 1k1k/tp4_conc32: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 1k1k/tp4_conc4: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 1k1k/tp4_conc4: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 1k1k/tp4_conc64: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 1k1k/tp4_conc64: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 1k1k/tp4_conc8: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 1k1k/tp4_conc8: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 1k1k/tp8_conc4: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 1k1k/tp8_conc4: Review phase-resolved error_label evidence; successful measurement does not make logs error-free
- 1k1k/tp8_conc4: Review phase-resolved traceback_header evidence; successful measurement does not make logs error-free
- 8k1k/tp4_conc128: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 8k1k/tp4_conc128: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 8k1k/tp4_conc16: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 8k1k/tp4_conc16: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 8k1k/tp4_conc256: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 8k1k/tp4_conc256: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 8k1k/tp4_conc32: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 8k1k/tp4_conc32: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 8k1k/tp4_conc4: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 8k1k/tp4_conc4: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 8k1k/tp4_conc64: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 8k1k/tp4_conc64: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 8k1k/tp4_conc8: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 8k1k/tp4_conc8: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 8k1k/tp8_conc4: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 8k1k/tp8_conc4: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures

## Limitations

- Throughput is recomputed from actual token arrays and duration. Median TPOT is a reported aggregate matched to its rounded log; raw latency/TTFT samples are unavailable, so only its reciprocal is independently calculated.
- AL is lifetime cumulative per returned DP state, including warmup; no measured-only or weighted aggregate is inferred. Warmup responses are discarded; measured success is not warmup-response or quality validation.
- Configured graph buckets differ from actual captures clamped to each DP pool. Log replay counts are batch observations, not a kernel execution trace.
- Phase resolution preserves whole-second boundaries and inherits timestamps for untimed stack lines. Diagnostic counts are not unique request failure counts; review teardown separately.
- Recorded commits/imports and clean-tree receipts do not independently rehash remote source or prove every kernel execution. See the explicit first-case and TP8 calibration status and bound independent reviews; no quality evaluation is provided.
- Full package-freeze delta and reported package versions are checked; direct-reference packages without a == version retain only receipt-level identity. Existing or changed pip-check diagnostics remain explicit review notes.
- The checker does not alter historical auditors or raw artifacts. Full-matrix completeness is required only with --require-full-matrix, and zero issues is not an error-free-log or causal-performance claim.
