# Aligned TRTLLM raw audit

16 cases; 10240 measured requests; 0 issues; 0 missing coordinates.

| Case | Completed | Output tok/s | Output/GPU | Reported median TPOT ms | Derived tok/s/user | Issues |
|---|---:|---:|---:|---:|---:|---:|
| 1k1k/tp4_conc128 | 1280/1280 | 4144.641866 | 1036.160466 | 29.973910 | 33.362347 | 0 |
| 1k1k/tp4_conc16 | 160/160 | 1311.364618 | 327.841154 | 11.339155 | 88.189992 | 0 |
| 1k1k/tp4_conc256 | 2560/2560 | 4941.233855 | 1235.308464 | 51.503061 | 19.416322 | 0 |
| 1k1k/tp4_conc32 | 320/320 | 1959.192588 | 489.798147 | 15.114248 | 66.162738 | 0 |
| 1k1k/tp4_conc4 | 40/40 | 529.143472 | 132.285868 | 7.078336 | 141.276142 | 0 |
| 1k1k/tp4_conc64 | 640/640 | 2716.210196 | 679.052549 | 22.585114 | 44.276952 | 0 |
| 1k1k/tp4_conc8 | 80/80 | 832.166020 | 208.041505 | 8.886450 | 112.530877 | 0 |
| 1k1k/tp8_conc4 | 40/40 | 510.451532 | 63.806441 | 7.141975 | 140.017300 | 0 |
| 8k1k/tp4_conc128 | 1280/1280 | 2345.968898 | 586.492224 | 52.986924 | 18.872581 | 0 |
| 8k1k/tp4_conc16 | 160/160 | 1049.653872 | 262.413468 | 13.391488 | 74.674299 | 0 |
| 8k1k/tp4_conc256 | 2560/2560 | 2779.462206 | 694.865552 | 90.536399 | 11.045281 | 0 |
| 8k1k/tp4_conc32 | 320/320 | 1450.804387 | 362.701097 | 20.146069 | 49.637475 | 0 |
| 8k1k/tp4_conc4 | 40/40 | 473.603004 | 118.400751 | 7.221330 | 138.478648 | 0 |
| 8k1k/tp4_conc64 | 640/640 | 1898.932439 | 474.733110 | 32.092769 | 31.159667 | 0 |
| 8k1k/tp4_conc8 | 80/80 | 732.464210 | 183.116052 | 9.764155 | 102.415418 | 0 |
| 8k1k/tp8_conc4 | 40/40 | 460.150572 | 57.518821 | 7.766815 | 128.752912 | 0 |

## Restoration issues

None.

## Discovery issues

None.

## Case issues

None.

## Review notes

- 1k1k/tp4_conc128: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 1k1k/tp4_conc128: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 1k1k/tp4_conc16: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 1k1k/tp4_conc16: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 1k1k/tp4_conc256: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 1k1k/tp4_conc256: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 1k1k/tp4_conc32: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 1k1k/tp4_conc32: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 1k1k/tp4_conc4: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 1k1k/tp4_conc4: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 1k1k/tp4_conc64: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 1k1k/tp4_conc64: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 1k1k/tp4_conc8: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 1k1k/tp4_conc8: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 1k1k/tp8_conc4: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 1k1k/tp8_conc4: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 8k1k/tp4_conc128: Review phase-resolved error_label; measured success is not an error-free log claim
- 8k1k/tp4_conc128: Review phase-resolved traceback_header; measured success is not an error-free log claim
- 8k1k/tp4_conc128: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 8k1k/tp4_conc16: Review phase-resolved error_label; measured success is not an error-free log claim
- 8k1k/tp4_conc16: Review phase-resolved traceback_header; measured success is not an error-free log claim
- 8k1k/tp4_conc16: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 8k1k/tp4_conc256: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 8k1k/tp4_conc32: Review phase-resolved error_label; measured success is not an error-free log claim
- 8k1k/tp4_conc32: Review phase-resolved traceback_header; measured success is not an error-free log claim
- 8k1k/tp4_conc32: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 8k1k/tp4_conc4: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 8k1k/tp4_conc4: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 8k1k/tp4_conc64: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 8k1k/tp4_conc64: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 8k1k/tp4_conc8: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
- 8k1k/tp4_conc8: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
- 8k1k/tp8_conc4: Review phase-resolved error_label; measured success is not an error-free log claim
- 8k1k/tp8_conc4: Review phase-resolved traceback_header; measured success is not an error-free log claim

## Limitations

- Token sums and request/output/total throughput are independently recomputed; output/GPU divides by active TP GPUs.
- Median TPOT is a reported aggregate cross-checked against the rounded benchmark log. Raw per-request latency/TTFT samples were not retained; the median itself cannot be independently recomputed. Interactivity is recomputed as 1000 / reported median_tpot_ms.
- At the pinned source, TPOT samples include successful requests with output_len > 1: (latency - TTFT) / (output_len - 1), followed by median and conversion to milliseconds.
- AL remains lifetime cumulative per DP state, including warmup; no measured-only or DP-weighted mean is claimed.
- Configured graph buckets differ from actual capture; phase-resolved replay counts describe logged batches, not every kernel.
- Restoration receipts bind original inventory, restored packages/imports and wheel manifest. Case metadata does not independently rehash remote source or record per-case installed FlashInfer imports.
- Native BF16 draft is established by pinned NextN source semantics plus inherited quantization and TRTLLM backend; inspect runtime kernel/autotune evidence separately.
- Zero measured request failures do not imply warning-free startup/teardown or numerical accuracy; review all retained notes before publication.
