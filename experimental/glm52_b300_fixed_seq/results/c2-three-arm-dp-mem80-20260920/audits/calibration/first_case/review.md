# CuTe first completed case: independent review

**Passed: 0 identified issues.** This review covers only `c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc256`, finalized with **2,560/2,560 measured requests successful, 0 failed, exit 0**. It does not establish TP8 compatibility or a complete performance comparison. The independent review script imports no benchmark auditor implementation.

The accompanying JSON binds all **13 raw file SHA-256 identities**, the **8 sealed setup receipts**, this report, source pins, and checked normalized settings. I independently hashed the local raw files and archived members against both the embedded collector manifest and transfer receipt; the packed archive SHA also matches. `result.json` SHA-256 is `3fa14f313b419312d89893946add81ba4bc52d46539f845fddbc56a15ce5eb45`.

| Independent arithmetic from raw result | Value |
|---|---:|
| Input token sum, 2,560 integer samples | 18,878,760 |
| Output token sum, 2,560 integer samples | 2,360,332 |
| Measured duration | 1,008.9852901990525 s |
| Output tokens / duration | 2,339.312597445652 tok/s |
| Output tokens / duration / 4 GPUs | 584.828149361413 tok/s/GPU |
| Total input + output tokens / duration | 21,049.952071957316 tok/s |
| Reported median TPOT | 107.48206580830121 ms |
| 1,000 / reported median TPOT | 9.30387774443731 tok/s/user |

The throughput recomputations agree with `result.json`. The finite, positive reported median TPOT agrees with the rounded `107.48` in `benchmark.log` physical LF line 38. Individual latency/TTFT samples are unavailable: **the median was not independently reconstructed**. The measurement interval is **2026-09-20 14:09:40.945895–14:26:29.931196 UTC**. Wall-clock timestamp subtraction differs from the recorded duration by approximately 10.1 microseconds, within the independent 1 ms consistency tolerance for separate clock samples.

## Resolved contract

Metadata, complete recorded commands, and both before/after responses agree. I checked each response's top-level settings and **all four returned DP states** individually.

| Contract | Actual evidence |
|---|---|
| Precision/topology | `modelopt_fp4`, BF16 dtype; TP=DP=EP=4; DP attention enabled; 4 active NVIDIA B300 GPUs |
| Memory and request pool | `mem_fraction_static=0.8` in metadata, command, and every before/after scope; global cap 256; each returned DP pool 64 |
| Prefill | Command chunk 32,768 normalizes to 8,192 per DP; max prefill tokens 32,768; effective graph backend `disabled` |
| Target | `flashinfer_cutedsl` / A2A `none`; recorded `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`, `SGLANG_FLASHINFER_MOE_FUSED_FINALIZE=0`, per-token activation flag `0` |
| MTP | EAGLE, 3 steps, top-k 1, 4 draft tokens; `flashinfer_trtllm` / A2A `none`; inherited `modelopt_fp4` label, explicit draft-quantization marker false, no command override |
| Attention/KV | DSA with TRT-LLM prefill/decode, `sgl-kernel` top-k, FP8 E4M3 KV, page size 64 |
| Decode graphs | Configured maximum 256; **actual captured maximum 64**, matching the per-DP pool; 27 observed capture sizes from 1 through 64 |

The legacy `disable_prefill_cuda_graph=false` field and inactive prefill buckets do not override the resolved `cuda_graph_backend_prefill=disabled`. Logs corroborate routed-MoE W4A16 dispatch with four physical lines containing `CuteDslMoEWrapper::run::W4A16::Swiglu`, and native-BF16 TRT-LLM draft dispatch with 19 lines containing `Tuning flashinfer::trtllm_bf16_moe`; all precede measurement. These are operation/autotune evidence, not an exhaustive per-layer kernel profile or a whole-model A16 claim.

## Graph and diagnostic phases

Counts below use physical LF lines, preserving progress carriage returns. Timestamps with whole-second precision that overlap a measurement boundary remain in a separate boundary category. Counts are log observations, not request counts.

| Log observation | Before measurement | Boundary | Measured | After measurement / untimed |
|---|---:|---:|---:|---:|
| Prefill `cuda graph: False` | 493 | 0 | 2,537 | 0 |
| Decode `cuda graph: True` | 91 | 5 | 336 | 0 |
| Severity-tagged/User/Future warning lines | 17 | 0 | 0 | 1 untimed launch warning |
| Autotune cache disagreement and retune | 1 | 0 | 0 | 0 |
| Allocator OOM, OOM exception, ERROR label, traceback, fatal-runtime pattern | 0 | 0 | 0 | 0 |

No prefill-graph `True` or decode-graph `False` observations were found. Capture progress appears at physical lines 167, 177, 206, 209, and 230. At **14:05:32**, line 209 reports per-rank autotune caches disagreeing and retuning from scratch; this is before measurement and is retained as an initialization observation.

At **14:26:31**, after the measurement end, physical lines **6803–6805** record SIGTERM, a child exit `-15` triggering SIGQUIT for cleanup, and the generic “one child failed” SIGQUIT message. These are **post-measurement teardown diagnostics**; they are preserved and separated from the 2,560 successful measured requests. There is one SIGTERM line, two lines containing SIGQUIT, and one child-exit `-15` line.

The log records 512 requested warmups and `Warmup completed.` (benchmark physical line 16); individual warmup responses are not retained, so this does **not** independently prove 512 successful warmup responses. After-run acceptance lengths are `[2.9596998160879817, 2.9648290150308294, 2.9481015363622167, 2.9460656282161146]`: cumulative lifetime values per returned DP state, including warmup, not measured-only acceptance or a weighted aggregate.

## Source and environment binding

- InferenceX `3433a0c1169a6b162edf91c7ea193196c08a6386`; SGLang `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FlashInfer `f9dd3c10541e087b716772245a9d033499745048`.
- Checkpoint revision `53e0691e21895a3863a606dfd12910c69eba94ab`; image `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85`.
- The eight receipts remain byte-identical to the independently reviewed environment. Their seal at **13:32:31.828178 UTC** precedes case initialization at **13:33:01.884581 UTC**. Source-head and clean-tree assertions are recorded receipt evidence, not a new remote inspection.
- The case package snapshot agrees with the sealed freeze: source FlashInfer **0.7.0**, five CuTe packages **4.7.1**, `nccl-extensions` **0.1.0**, and unchanged remaining providers. FlashInfer cubin/JIT distributions are absent. The environment variable `FLASHINFER_VERSION=0.6.18` is an inherited image label, not the imported FlashInfer identity.
- `pip check` remains **non-clean**: the sealed after receipt has 12 diagnostics, including the three known newly introduced version-requirement conflicts; see the independently hashed environment review for the complete delta. This review does not claim clean dependency resolution.

No quality evaluation, repeated-run confidence interval, or latency-SLO qualification was performed. This completed first-case review is suitable for explicit auditor calibration binding; pending labels have not been changed by this review. **TP8/C4 still requires its own real-case review.**

Evidence: [machine-readable review](cutedsl-first-case-independent-review.json), [independent review script](cutedsl-first-case-review-work/review.py), [sealed environment review](cutedsl-20260920-independent-environment-review.md).
