# DeepSeek-V4.1 with DSpark: three EP8 backend frontiers

[中文报告](REPORT_zh.md)

This separate study compares target MegaMoE W4A4, MegaMoE W4A16 and traditional TRTLLM W4A4 at TP=EP=attention DP=8 and C2/4/8/16/32/64 on one eight-B300 node. It reuses the GLM runner and metric definitions while keeping the new model, prompt formatting, draft and plots separate. The benchmark uses a dedicated node in the personal non-preempt queue, separate from SGLang development.

**Actual completion:** 18 accepted points; 3,780/3,780 measured requests completed successfully with zero measured errors. The completed matrix contains 18 points and 756 scheduled, awaited warmups excluded from measured statistics. The worker completed all 18 cases at 2026-10-02 01:03:27 UTC. At 01:03:28 the supervisor recorded its actual wait on the runner returning 0 and its own terminal status 0. Both fresh observations at 01:12:08 found all 3,911 recorded process births and 56 recorded sessions absent. This is bounded saved-owner closure, not continuous/unknown-process absence or an independent parent OS wait on the outer supervisor. All 18 compact output, 540 signed metric rows, portable EP8 replay and main/EP8 PNG/SVG visual review passed. Full raw evidence remains local. Archival/retention and node cleanup require separate acceptance. [18-point metrics](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/raw-metrics.json) · [all saved scalars/tails](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/raw-saved-scalars.json) · [18 matched groups / 540 signed metric rows](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/paired-comparisons.csv) · [EP8 PNG](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/figures/ep8/pareto.png) · [EP8 SVG](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/figures/ep8/pareto.svg) · [replay source](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/source/experimental/dsv41_dspark_ep8/render.py)

Mega W4A16 has higher measured output/GPU than Mega W4A4 at every tested concurrency, but it does not improve every latency metric. At C64, output/GPU is Mega W4A4 1557.788, Mega W4A16 1627.940, TRT W4A4 1388.839 tok/s/GPU. The signed table preserves regressions; this single sequential sweep does not isolate a causal precision or backend effect.

Display values are rounded; the linked JSON/CSV retains the saved numerical fields.

| Backend / 后端 | C | Measured / 测量 | Output tok/s/GPU | 1000 / median TPOT | TTFT median ms | TPOT median ms | E2EL median ms | AL | Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Mega W4A4 | 2 | 20 | 110.553 | 553.845 | 285.249 | 1.806 | 13826.148 | 4.593126 | 0.718782 |
| Mega W4A4 | 4 | 40 | 199.739 | 489.302 | 281.785 | 2.044 | 14950.746 | 4.253591 | 0.650868 |
| Mega W4A4 | 8 | 80 | 334.451 | 460.644 | 512.953 | 2.171 | 18086.335 | 4.374164 | 0.674992 |
| Mega W4A4 | 16 | 160 | 606.895 | 405.407 | 400.957 | 2.467 | 20002.697 | 4.485681 | 0.697318 |
| Mega W4A4 | 32 | 320 | 1047.878 | 334.066 | 496.242 | 2.993 | 24283.912 | 4.545689 | 0.709296 |
| Mega W4A4 | 64 | 640 | 1557.788 | 264.719 | 2420.513 | 3.778 | 31938.428 | 4.388790 | 0.677910 |
| Mega W4A16 | 2 | 20 | 122.728 | 516.892 | 298.772 | 1.935 | 14886.135 | 4.830385 | 0.766275 |
| Mega W4A16 | 4 | 40 | 208.879 | 491.916 | 289.886 | 2.033 | 15481.747 | 4.496625 | 0.699471 |
| Mega W4A16 | 8 | 80 | 352.346 | 453.145 | 470.653 | 2.207 | 17268.184 | 4.771841 | 0.754553 |
| Mega W4A16 | 16 | 160 | 635.021 | 399.236 | 303.246 | 2.505 | 20446.741 | 4.612369 | 0.722650 |
| Mega W4A16 | 32 | 320 | 1064.911 | 315.449 | 565.099 | 3.170 | 25218.250 | 4.714787 | 0.743117 |
| Mega W4A16 | 64 | 640 | 1627.940 | 253.472 | 2221.999 | 3.945 | 32776.007 | 4.665568 | 0.733273 |
| TRT W4A4 | 2 | 20 | 94.942 | 467.710 | 313.444 | 2.138 | 16240.234 | 4.248575 | 0.649884 |
| TRT W4A4 | 4 | 40 | 198.718 | 464.568 | 304.303 | 2.153 | 16638.532 | 4.733598 | 0.746905 |
| TRT W4A4 | 8 | 80 | 352.820 | 437.299 | 299.521 | 2.287 | 17854.400 | 4.689910 | 0.738122 |
| TRT W4A4 | 16 | 160 | 577.451 | 380.220 | 545.828 | 2.630 | 21519.406 | 4.615761 | 0.723319 |
| TRT W4A4 | 32 | 320 | 977.192 | 298.422 | 389.568 | 3.351 | 26711.382 | 4.695072 | 0.739175 |
| TRT W4A4 | 64 | 640 | 1388.839 | 221.203 | 2191.424 | 4.521 | 37560.065 | 4.688657 | 0.737896 |

Signed changes are `(comparison / baseline − 1) × 100`; negative latency changes mean lower latency. Every saved tail remains in the linked full table.

| Comparison / baseline | C | Output/GPU Δ | Interactivity Δ | AL Δ | Median TPOT Δ | Median TTFT Δ | p99 TTFT Δ | Median E2EL Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Mega W4A16 / Mega W4A4 | 2 | +11.01% | -6.67% | +5.17% | +7.15% | +4.74% | -73.77% | +7.67% |
| Mega W4A4 / TRT W4A4 | 2 | +16.44% | +18.42% | +8.11% | -15.55% | -9.00% | +269.43% | -14.86% |
| Mega W4A16 / TRT W4A4 | 2 | +29.27% | +10.52% | +13.69% | -9.51% | -4.68% | -3.09% | -8.34% |
| Mega W4A16 / Mega W4A4 | 4 | +4.58% | +0.53% | +5.71% | -0.53% | +2.87% | +360.68% | +3.55% |
| Mega W4A4 / TRT W4A4 | 4 | +0.51% | +5.32% | -10.14% | -5.05% | -7.40% | +21.27% | -10.14% |
| Mega W4A16 / TRT W4A4 | 4 | +5.11% | +5.89% | -5.01% | -5.56% | -4.74% | +458.67% | -6.95% |
| Mega W4A16 / Mega W4A4 | 8 | +5.35% | -1.63% | +9.09% | +1.65% | -8.25% | +43.70% | -4.52% |
| Mega W4A4 / TRT W4A4 | 8 | -5.21% | +5.34% | -6.73% | -5.07% | +71.26% | -44.62% | +1.30% |
| Mega W4A16 / TRT W4A4 | 8 | -0.13% | +3.62% | +1.75% | -3.50% | +57.14% | -20.42% | -3.28% |
| Mega W4A16 / Mega W4A4 | 16 | +4.63% | -1.52% | +2.82% | +1.55% | -24.37% | +14.58% | +2.22% |
| Mega W4A4 / TRT W4A4 | 16 | +5.10% | +6.62% | -2.82% | -6.21% | -26.54% | -21.68% | -7.05% |
| Mega W4A16 / TRT W4A4 | 16 | +9.97% | +5.00% | -0.07% | -4.76% | -44.44% | -10.26% | -4.98% |
| Mega W4A16 / Mega W4A4 | 32 | +1.63% | -5.57% | +3.72% | +5.90% | +13.88% | -23.33% | +3.85% |
| Mega W4A4 / TRT W4A4 | 32 | +7.23% | +11.94% | -3.18% | -10.67% | +27.38% | -6.72% | -9.09% |
| Mega W4A16 / TRT W4A4 | 32 | +8.98% | +5.71% | +0.42% | -5.40% | +45.06% | -28.48% | -5.59% |
| Mega W4A16 / Mega W4A4 | 64 | +4.50% | -4.25% | +6.31% | +4.44% | -8.20% | +20.02% | +2.62% |
| Mega W4A4 / TRT W4A4 | 64 | +12.16% | +19.67% | -6.40% | -16.44% | +10.45% | -34.55% | -14.97% |
| Mega W4A16 / TRT W4A4 | 64 | +17.22% | +14.59% | -0.49% | -12.73% | +1.40% | -21.44% | -12.74% |

AL summary below pools only native measured token/verify denominators, not point averages; it is not a throughput aggregate.

| Backend | AL range across six points | Summed completion tokens | Summed verify count | Denominator-weighted AL |
|---|---:|---:|---:|---:|
| Mega W4A4 | 4.253591–4.593126 | 9,305,531 | 2,096,892 | 4.437773 |
| Mega W4A16 | 4.496625–4.830385 | 9,305,531 | 1,990,579 | 4.674786 |
| TRT W4A4 | 4.248575–4.733598 | 9,305,531 | 1,990,578 | 4.674788 |

- **Workload and order:** nominal 1,024 input / 8,192 output, ratio 0.8, seed 0, greedy sampling, ignore EOS, infinite request rate and stream interval 30; each point schedules `2C` warmups then `10C` measured requests. A new server starts for each point. C2 runs Mega W4A4, Mega W4A16, then TRT W4A4; the remaining C4/8/16/32/64 run within each arm in the same arm order. Same-C requested/completed length arrays must match across arms. Warmups are awaited, but the inherited client does not independently assert every warmup response succeeds.


| Common declared/resolved setting | Actual value across all18 cases |
|---|---|
| TP / EP / attention DP; attention TP | 8 / 8 / 8; 1 |
| Declared dtype / resolved KV dtype | bfloat16 / fp8_e4m3 |
| Attention selection | dsv4; dsv4_attn_backend=auto |
| Target / draft quantization argument fields | null / null (native checkpoint/config selection, not an unquantized-model claim) |
| Memory fraction; radix cache; prefill graphs | 0.80; disabled; disabled |
| Declared global chunk / resolved per-DP chunk | 32768 / 4096 |
| max_prefill_tokens / stream interval | 32768 / 30 |
| Local request pool | max(C,8)/8; actual graph batches follow the saved configuration |
| DSpark block / target verify / draft widths | 5 / 6 / 5 |
| DP LM head | enabled |

- **Target/draft boundary:** target routed experts use NVFP4; dense and other target paths retain the checkpoint/runtime's native mixed precision, including MXFP8. Mega W4A16's existing selector also affects eligible NVFP4 linears. The bundled DSpark draft remains native MXFP4/MXFP8 with `flashinfer_mxfp4` and A2A `none` in all arms. It is not a wholly BF16 draft. Traditional target uses `flashinfer_trtllm_routed`/A2A `none`; Mega target uses `flashinfer_megamoe` for runner/A2A. No extra per-token, quantization-fast-math, combine or IKR override is introduced.
- **Text and speculation:** all arms use `--json-model-override-args '{"vision_n_layers":0}'`, preserving original checkpoint bytes while skipping the vision path. Prompt encoding explicitly uses DeepSeek-V4.1 chat mode with `reasoning_effort=None`. This does not establish multimodal/generated-image-token equivalence. DSpark block size 5 gives verification width 6; DP LM head and static ragged verification are explicit.
- **AL and metrics:** AL is `sum(measured completion_tokens)/sum(measured spec_verify_ct)`, including native bonus tokens. Rate is `sum(correct_drafts)/(5*sum(spec_verify_ct))`; this denominator is the configured proposal budget, not actual ragged verification slots. Every measured request requires valid native counters; warmups and server lifetime/window averages are excluded. Plot x is `1000/median_tpot_ms`; y is all measured output tokens/full measured wall interval/8. ITL is streamed chunk spacing at interval 30. Preserve all saved scalar latency tails and signed comparisons; missing per-request latency arrays or unsaved percentiles cannot be reconstructed.
- **Compilation and cache qualification:** the first accepted Mega W4A4 C2 point contains a 5.93s non-cache-hit Triton compilation warning reported at 19:46:05 UTC on October 1, inside its measured interval. No time is subtracted. Log times are report timestamps at one-second resolution, not compiler start/end tracing. This is not a fully precompiled steady-state comparison. Fresh campaign HOME/TMP/compiler/tactic roots use no seed; compilation is shared within this sequential sweep and tactics are separated by arm. Provider/default caches are not claimed cold or isolated; order/cache differences preclude causal or statistical-significance claims from a single sweep.
- **Native cache qualification:** the reviewed first Mega W4A4 C2 profiles retain runtime/enclosing-geometry `apply_topk_in_fc1=True`. Their native cache entry records `False` because both native writer and lookup omit that optional argument; lookup returns knobs only, and those knobs do not override the runtime flag. The native metadata field alone does not establish routing-weight placement. All subsequent points were independently reviewed against their own saved profiles.
- **C16 cache history:** in the accepted Mega W4A4 C16 case, current target Mega profiles are capacities `1/2/4/8/12/4096`; `8/12` were newly tuned, while `6` remains only in the stored target union from earlier points. All eight draft snapshots retain the prior target Mega namespace `1/2/4/6/4096` byte-for-byte after loading their own cache. These inherited records need not cover the current target profiles and do not imply that the draft runs MegaMoE. Target profiles and the separate native MXFP4 draft profiles (`1/2/4/8/16/32/64/128`) were reviewed by role against saved records, runtime configuration and graph logs. The snapshots do not prove every serving kernel dispatch or that all tactics were reused.
- **C64 cleanup qualification:** the accepted Mega W4A4 C64 client and server both have waited exit 0, but the original 21:59:32 UTC `gpu.after` snapshot on October 1 is non-idle; the frozen owner/GPU helper failed that stronger check and remains failed. A separately reviewed prelaunch snapshot at 21:59:35 shows the same eight GPU UUIDs at zero memory, zero utilization and no compute applications, before the next server launch at 21:59:37. This supports later idle only; it neither changes the original sample nor establishes why its values differed. The later-idle proof is now joined byte-for-byte to the next sealed Mega W4A16 C4 prelaunch receipts; whole-campaign termination was reviewed separately as summarized above.
- **Final TRT C64 owner scope:** the case-only owner helper rejected the terminal corpus because it contained the full 3,558-recorded-birth union instead of only the 33 case births. That failure is preserved. A separate accepted addendum verified inclusion of all 33 case births, the saved union checks and GPU timeline; it does not relabel the original helper as passing. The supervisor receipt records its actual wait on the runner, not an independent parent OS wait on the supervisor.
- **Environment and correction:** the exact pins are below. A single installed FI Python file was replaced with the reviewed conservative FP8 narrow-N support guard; original wheel/build metadata, cubin and NCCL provider payloads remain unchanged. This was not a wheel rebuild or a claim that installed files equal RECORD. All 38 installed regression tests passed before launch (34 policy/four GPU). The 14 previously recorded dependency-conflict/missing-dependency lines remain; no clean dependency environment is claimed.
- **Checkpoint and history:** the pinned upstream index declares 510,286,023,000 payload bytes; inspected tensor headers describe 527,273,322,840, a 16,987,299,840-byte metadata mismatch. Original index/weights are unchanged. The accepted recovery retained SHA checks for 84 files and 48 tensor-file/header validation after the original strict metadata check failed. Earlier vision/A2A and MXFP8 startup failures produced no accepted measurements and remain local. A measured client exit 0 followed by owned server cleanup with exit −9 does not mean graceful server exit. Final archival/retention and node cleanup require separate actual acceptance.

| Reproduction item | Exact pin |
|---|---|
| InferenceX measured recipe | `933b8821ecb45935b869fb10a4bfe06fff3ec99c` |
| SGLang child draft | `29c2b32d7f7351082168e622a4747bcff6469271`; [zianglih/sglang#4](https://github.com/zianglih/sglang/pull/4) |
| Integration branch base, unchanged by this study | `561ad447c74bb757a40677ee9ce038f9ca429d2c` |
| FlashInfer corrected Python source | `7a962707af69863d386be2a9bc01ee4607470bcc` |
| FlashInfer original wheel/source build | `a03f2205263d4e691d68e485bff287e37a19b6c3` |
| Corrected file | `flashinfer/gemm/kernels/dense_blockscaled_gemm_sm100.py` |
| Original / corrected file SHA256 | `a07193ecc61c522a1dc26548662524d1cbf27a0b0257888fbb4ca241bd2c7593` / `a4c20af8ad49c1d050db3dd9b933fa771a4b9d5ca830c5de8a6c66376aa19114` |
| Checkpoint | `nvidia/DeepSeek-V4.1-Flash-NVFP4@3431dde3247c13b5957f682b1e3c6fcae2566079` |
| Prompt encoder SHA256 | `502bdaec8a3fd88ebc24c4721a7038fbe42f2063c664638127056107920035c1` |
| Torch | `2.13.0+cu130` |
| Image | `lmsysorg/sglang:nightly-dev-cu13-20260930-cae69be5@sha256:0412c5b792cb35706de0359de4a1af52c160d4bdef6ff7530baf9df4e2a7b0b4` |

The compact bundle replays table arithmetic and plots with Python 3.11+ and Matplotlib; the local plotting environment is Python 3.14.6 / Matplotlib 3.10.6. From the reviewed public bundle:

```sh
python3 -B source/experimental/dsv41_dspark_ep8/render.py \
  --table raw-metrics.json --output /absolute/new-dspark-ep8-replay
```

This replays the EP8 view, not private raw/native/terminal validation. The presentation projection separately replays the main view and keeps numerical tables, point coordinates, AL and frontier membership unchanged. The accepted annotation-only presentation successor preserves all 18 metric rows, all 540 signed metric rows, AL, measured coordinates and frontier memberships. Each backend contributes six nondominated points. Portable EP8 replay reproduced exact point/frontier files; root inspected both main/EP8 PNGs and complete browser-rendered SVGs with all 18 C/AL labels readable. SVG viewers may substitute an available font when DejaVu Sans is unavailable. Full raw evidence remains local. Archival/retention and node cleanup require separate acceptance. Throughput and AL do not establish output quality or equivalence with GLM/MTP.
