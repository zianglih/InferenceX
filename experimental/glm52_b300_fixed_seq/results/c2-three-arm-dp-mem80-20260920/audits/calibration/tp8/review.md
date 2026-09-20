# CuTe TP8/C4: independent real-case review

**Passed: zero identified issues.** This review covers `c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp8_conc4`: **40/40 measured requests successful, zero failed, exit zero**. It calibrates the actual eight-DP capacity and graph behavior. It does not establish full-sweep completion, accuracy or repeated-run performance.

The [independent script](cutedsl-tp8-review-work/review.py) imports no auditor implementation. Its [verification output](cutedsl-tp8-review-work/verification-output.json) records the direct checks. The [review JSON](cutedsl-tp8-independent-review.json) binds all 13 raw files, eight runtime receipts, full pins, normalized settings and this report's SHA256. All raw bytes also match the collector manifest, transfer receipt and tar members; the tar SHA matches. `result.json` SHA256: `ce9110452b1f46d78d204f8914cf599f1a1dda82e964f5d585486de0515d043d`.

## Independent raw arithmetic

| Quantity | Value |
|---|---:|
| Input token sum, 40 positive integer samples | 294170 |
| Output token sum, 40 positive integer samples | 36805 |
| Duration | 86.41708802198991 s |
| Output tokens / duration | 425.8995627188283 tok/s |
| Output tokens / duration / 8 GPUs | 53.23744533985354 tok/s/GPU |
| Input + output tokens / duration | 3829.971682403592 tok/s |
| Requests / duration | 0.4628714171648725 req/s |
| Reported median TPOT | 8.597220336384785 ms |
| 1000 / reported median TPOT | 116.31666525607622 tok/s/user |

Measured UTC interval: **2026-09-20T15:31:54.450646+00:00 → 2026-09-20T15:33:20.867735+00:00**. Recomputed throughputs agree at relative tolerance 1e-12; wall-clock bounds and duration agree within 1 ms. Printed two-decimal duration, output/total throughput and median TTFT/TPOT/ITL/E2EL agree with saved aggregates. Individual latency samples are absent, so the median itself was not independently reconstructed.

## Capacity and graphs

Both before/after top-level responses and **all eight returned DP states** were checked individually: TP=DP=EP=8, DP attention enabled, global server capacity **8**, and **each DP pool exactly 1**. Client concurrency remains **4**, with 40 measured requests and eight requested warmups. This is the intended minimum server-capacity correction, not client C8.

All scopes resolve memory fraction .80; target `flashinfer_cutedsl`/A2A `none`; MTP `flashinfer_trtllm`/A2A `none`, EAGLE 3/1/4, inherited `modelopt_fp4`, explicitness false, no draft quantization override. The W4A16 flag is 1, fused finalize 0 and per-token activation 0. Dtype is BF16, model quantization ModelOpt FP4, attention DSA/TRTLLM and KV FP8 E4M3. CLI chunked prefill 32,768 normalizes to **4,096 per DP**; max prefill tokens remains 32,768.

Prefill graph backend is disabled. Configured decode graph is `full`, maximum 4, buckets `[1,2,3,4]`; **every actual target/draft capture uses `[1]`**, matching the DP pool. All eight target-verify capture entries are present. Exact capture lines and returned DP observations are retained in JSON.

Fully contained measured seconds show 80 prefill-false and 306 decode-true log lines, plus three boundary-second decode lines. Before measurement there are 25 prefill-false and 63 decode-true lines. No prefill-true or decode-false line appears. These are logged batches, not request or kernel counts; boundary seconds remain separate.

The recorded server command matches the independently reviewed first case except expected TP/DP/EP, capacity and graph-limit changes. The client retains sampled caps 8192/1024, range ratio .8 and chat-template use. `Warmup completed.` is present; discarded warmup responses cannot independently establish eight successful warmup responses.

## Diagnostics and runtime

The complete log has zero allocator OOM, OOM-exception, word-ERROR, traceback-header or `RuntimeError:` matches. It retains 33 startup warning observations and one untimed launch warning. Six CuTe W4A16 operation-name lines and 20 BF16 TRTLLM autotune lines occur before measurement; these corroborate dispatch, not an exhaustive per-layer precision profile or whole-model A16 claim.

At **15:33:22 UTC**, after measurement ended **15:33:20.867735 UTC** and after a successful server-info response, cleanup logs SIGTERM, child exit -15 and SIGQUIT. These are preserved post-measurement watchdog diagnostics, not measured request failures. Exact physical LF lines follow:

- Line 991: `[2026-09-20 15:33:22] SIGTERM received. signum=None frame=None. Draining requests and shutting down...`
- Line 992: `[2026-09-20 15:33:22] Subprocess scheduler_0 (pid=168915) crashed with exit code -15. Triggering SIGQUIT for cleanup...`
- Line 993: `[2026-09-20 15:33:22] SIGQUIT received. signum=None, frame=None. It usually means one child failed.`

After-run acceptance values per returned DP state: `[3.0026041666666665, 2.9885869565217393, 2.897448979591837, 3.1277173913043477, 3.0733333333333333, 3.002659574468085, 3.0988372093023258, 2.8255208333333335]`. These are lifetime cumulative values including warmup, not a measured-only or weighted aggregate.


The eight runtime receipts are byte-identical to the independently reviewed first-case environment, and the entire package inventory matches that case. Setup completion precedes case initialization; source-head/clean-tree receipt fields match. FlashInfer is source 0.7.0, all five CuTe packages are 4.7.1, nccl-extensions is 0.1.0 and old cubin/JIT distributions are absent. Source/compiler import identity and environment match, except GPU visibility expands to eight devices. The inherited `FLASHINFER_VERSION=0.6.18` label is distinct from the imported source version. The unchanged sealed pip-check diagnostics remain non-clean; see the [environment review](cutedsl-20260920-independent-environment-review.md). No fresh remote Git/package inspection is claimed.

- InferenceX: `3433a0c1169a6b162edf91c7ea193196c08a6386`
- SGLang: `50eeb742961908afa68f4f523a1a19c5de6eb0b3`
- FlashInfer: `f9dd3c10541e087b716772245a9d033499745048`
- Model revision: `53e0691e21895a3863a606dfd12910c69eba94ab`
- Image: `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85`

This completed review is suitable for explicit `--tp8-review` binding. It does not change the cumulative auditor's pending label itself. The 15:35:49 UTC status snapshot had eight completed 8k1k points / 5,120 successful requests and 1k1k C256 running; remaining points are not claimed complete.
