# Resume the MegaMoE sweep after recovery1 C8 startup failure

Recovery1 retains two accepted 8k1k/TP4 points: C256 (2,560 measured requests) and C4 (40). C8 failed before readiness, with no measured result. The user authorized retrying the failed coordinate and completing the sweep without changing the SG/FI pins, packages, tactics or workload. The failure cause remains unknown.

`continue_megamoe_recovery2.py` creates a separate recovery2 root, exact source clones and a byte-verified copy of the sealed recovery1 cache. Original sources, caches and all failed evidence stay unchanged. `recovery2_reused_successes.json` binds all 28 previously accepted raw files. The installed FlashInfer editable metadata stays unchanged; PYTHONPATH selects the new exact source clone. Preparation performs no package installation.

On the same idle `infx-glm52-auto-0921` node, stage this helper, its frozen `campaign_20260921.py` dependency and the reused-success lock in an exclusive directory. Then run:

```sh
python3 -B continue_megamoe_recovery2.py prepare --recipe-commit FULL_PUBLISHED_RECIPE_SHA
```

Preparation and measurement are separate. After verifying its sealed environment and source/cache-copy receipts, launch once:

```sh
python3 -B /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery2/sources/inferencex/experimental/glm52_b300_fixed_seq/continue_megamoe_recovery2.py launch
```

The wrapper runs exactly 14 remaining points / 7,640 requests: 8k1k TP4 C8/16/32/64/128 and TP8 C4, then 1k1k TP4 C256/4/8/16/32/64/128 and TP8 C4. Any failure stops the wrapper and is preserved. Combining these with the two original successful coordinates requires a separate audit of all 16 points / 10,240 requests, preserving both real run IDs and recipe commits. A 14-point continuation archive is not a standalone complete 16-point result. Existing full-matrix success collectors remain unchanged; use the dedicated continuation collector/auditor.

All original controls, settings and final publication gates remain applicable: exact ordered client token lengths; TP=DP=EP; DP attention; memory .80; disabled prefill graphs; MTP 3/1/4 with TRT-LLM/none; full raw files, source bytes, first real continuation-case calibration, independent audit and actual Pareto PNG inspection. Reuse historical TRT/Split controls and disclose the mixed software/node environments. No statistical-significance or isolated integration-causality claim follows from a retry.
