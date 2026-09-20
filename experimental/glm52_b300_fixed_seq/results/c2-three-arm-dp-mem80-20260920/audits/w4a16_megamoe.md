# Discovered completed MegaMoE case audit

16 completed artifacts audited; 10240 measured requests; 0 invariant mismatches; 0 matrix coordinates missing.

Checker calibrated on the first real TP4/C4 case; other coordinates still require runtime evidence. Raw files are untouched.

| Case | Client C / server cap / effective per DP | Completed | Output tok/s | Measured allocator warnings | Returned cumulative AL | Review notes | Issues |
|---|---|---:|---:|---:|---|---:|---:|
| 1k1k/tp4_conc128 | 128 / 128 / [32, 32, 32, 32] | 1280/1280 | 4289.920242 | 0 | [2.992638201044037, 2.9777733413189593, 2.9781620258205836, 2.9866812716273743] | 2 | 0 |
| 1k1k/tp4_conc16 | 16 / 16 / [4, 4, 4, 4] | 160/160 | 1260.255160 | 0 | [2.899426234913935, 2.9806135637031494, 2.915542560967506, 2.9344969471728164] | 2 | 0 |
| 1k1k/tp4_conc256 | 256 / 256 / [64, 64, 64, 64] | 2560/2560 | 5866.004940 | 0 | [3.0040486337427925, 2.9802233780227523, 2.9825033814386934, 3.0222029648824646] | 2 | 0 |
| 1k1k/tp4_conc32 | 32 / 32 / [8, 8, 8, 8] | 320/320 | 2105.448093 | 0 | [2.9871273944070746, 2.95263698630137, 2.9599701218891115, 3.0027492108746565] | 2 | 0 |
| 1k1k/tp4_conc4 | 4 / 4 / [1, 1, 1, 1] | 40/40 | 512.225059 | 0 | [3.066758241758242, 3.0474719101123595, 3.015449438202247, 3.0137640449438203] | 2 | 0 |
| 1k1k/tp4_conc64 | 64 / 64 / [16, 16, 16, 16] | 640/640 | 2997.290190 | 0 | [2.996159071468107, 2.9923233615595697, 2.9651554576994927, 2.9667665121571645] | 2 | 0 |
| 1k1k/tp4_conc8 | 8 / 8 / [2, 2, 2, 2] | 80/80 | 813.639652 | 0 | [3.093141989788878, 2.8948394644481996, 3.069432918395574, 3.085057471264368] | 2 | 0 |
| 1k1k/tp8_conc4 | 4 / 8 / [1, 1, 1, 1, 1, 1, 1, 1] | 40/40 | 527.243050 | 0 | [2.878125, 2.9244791666666665, 3.0482954545454546, 2.921022727272727, 3.0044444444444443, 2.9302083333333333, 3.1151162790697673, 2.9233333333333333] | 2 | 0 |
| 8k1k/tp4_conc128 | 128 / 128 / [32, 32, 32, 32] | 1280/1280 | 1882.498117 | 0 | [2.9296385986375175, 2.9235330523216914, 2.926237373737374, 2.91269204406774] | 2 | 0 |
| 8k1k/tp4_conc16 | 16 / 16 / [4, 4, 4, 4] | 160/160 | 891.086788 | 0 | [2.9619475457488273, 2.960085435856361, 2.959884065608326, 2.994258628746912] | 2 | 0 |
| 8k1k/tp4_conc256 | 256 / 256 / [64, 64, 64, 64] | 2560/2560 | 2200.994271 | 0 | [2.9559822990634967, 2.9491395306829564, 2.9637121055887814, 2.963090015502853] | 2 | 0 |
| 8k1k/tp4_conc32 | 32 / 32 / [8, 8, 8, 8] | 320/320 | 1216.835411 | 0 | [2.9583723105706268, 2.941461955257122, 2.9102678423990223, 2.9690201253711646] | 2 | 0 |
| 8k1k/tp4_conc4 | 4 / 4 / [1, 1, 1, 1] | 40/40 | 429.836004 | 0 | [3.018421052631579, 3.1238888888888887, 3.023888888888889, 2.9710106382978725] | 2 | 0 |
| 8k1k/tp4_conc64 | 64 / 64 / [16, 16, 16, 16] | 640/640 | 1564.664363 | 0 | [2.98100810833403, 2.989958524339664, 2.9759180415114423, 2.9643709825528006] | 2 | 0 |
| 8k1k/tp4_conc8 | 8 / 8 / [2, 2, 2, 2] | 80/80 | 649.677705 | 0 | [2.9781727878708666, 2.9913595247738627, 2.996109993293092, 2.870946906084485] | 2 | 0 |
| 8k1k/tp8_conc4 | 4 / 8 / [1, 1, 1, 1, 1, 1, 1, 1] | 40/40 | 449.849070 | 0 | [2.955, 2.9797872340425533, 2.990816326530612, 3.225, 2.895, 2.8625, 2.874468085106383, 3.091304347826087] | 2 | 0 |

## Discovery and matrix issues

None.

## Invariant mismatches

None.

## Runtime review notes

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
- 1k1k/tp8_conc4: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- 8k1k/tp4_conc128: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
- 8k1k/tp4_conc128: Review phase-resolved error_label evidence; successful measurement does not make logs error-free
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

- AL is lifetime cumulative for each returned control-group state, including warmup; no measured-only or DP-weighted aggregate is available.
- Configured graph bucket lists are not the actual captured lists. Decode capture is clamped to each DP request pool; logged replay counts are batch observations, not every kernel invocation.
- Whole-second boundary lines remain boundary; untimed stack lines inherit the preceding timestamp. Warning counts are not unique failure counts.
- Request success covers measured requests; warmup responses are discarded, and no accuracy evaluation was run.
- Source/import/package fields are recorded provenance, not an independent rehash of remote files. Verify setup receipts, clean source/submodules, B300 identity and first real kernel execution separately.
- Throughput is independently recomputed from actual token arrays and measured duration. Workload labels denote sampled length bounds, not identical lengths for every request.
- Review notes must be interpreted before publication; invariant pass alone does not certify error-free execution, full matrix unless requested, or a causal performance explanation.
