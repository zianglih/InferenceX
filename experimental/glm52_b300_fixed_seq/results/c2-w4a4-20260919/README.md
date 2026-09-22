# GLM-5.2 B300 W4A4 + MTP results — 2026-09-19

**English** | [中文](README_zh.md)

All **16 planned cases completed, with 10,240/10,240 measured requests successful**.
The complete matrix passed the publication gate; the runtime audit found zero
configuration mismatches. W4A16 MegaMoE and accuracy evaluation were not run.

- [Complete metrics and charts](summary/summary.md)
- [Unabridged client summary output for every point](raw_client_summaries.md)
- [Runtime observations](runtime-audit.md) and [machine-readable audit](runtime-audit.json)
- [SHA256 manifest of all original files](manifest.json)
- [Experiment configuration and reproduction](../../README.md)

## Environment

| Field | Recorded value |
| --- | --- |
| Hardware | C2, one 8× NVIDIA B300 SXM6 AC node; 275040 MiB per GPU; each point uses TP4 or TP8 GPUs |
| Image | `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85` |
| Image index digest | `sha256:d46a59f4b98658f728a1e006c003ad5ee0628e999fd8b2bef71ac1bb61b814da` |
| AMD64 image digest | `sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596` |
| Measured InferenceX commit | `0c684dd7fe30ebb165453c20989b2fcb24633b6c` |
| Imported SGLang source | [PR #39210](https://github.com/sgl-project/sglang/pull/39210), `50eeb742961908afa68f4f523a1a19c5de6eb0b3`, selected through `PYTHONPATH` |
| Model | `nvidia/GLM-5.2-NVFP4`, revision `53e0691e21895a3863a606dfd12910c69eba94ab` |
| FlashInfer Python / cubin / JIT cache | `0.6.18 / 0.6.18 / 0.6.18+cu130`; image-provided, no upgrade |
| PyTorch / CUDA runtime / Triton | `2.13.0+cu130 / 13.0 / 3.7.1` |
| Transformers / SGLang kernel / CuTe DSL | `5.12.1 / 0.4.7 / 4.6.2` |
| Driver | `590.48.01`; `nvidia-smi` reports CUDA compatibility 13.1 separately from the PyTorch runtime |

The image-installed SGLang distribution reports `0.0.0.dev1+g20518d851`; this is
distinct from the imported PR source. The [environment records](environment/) and
per-case package/server-info files retain these separate provenance fields. The
post-run audit does not freshly checksum every model weight or installed binary.

## Method

- **Matrix:** separately run 8k1k (`8192/1024`) and 1k1k (`1024/1024`). Each uses
  TP4/DP1/EP1 at concurrency 4, 8, 16, 32, 64, 128, 256, plus TP8/DP1/EP1 at
  concurrency 4. Each point starts a fresh server, followed by owned-process cleanup.
- **Server:** `modelopt_fp4`, `flashinfer_trtllm`, A2A `none`, BF16 model interface,
  FP8 E4M3 KV, DSA with TRT-LLM prefill/decode, memory fraction 0.85, prefill budgets
  32768, radix cache disabled and stream interval 30. Maximum running requests and
  the decode graph batch limit equal concurrency. Checkpoint exclusions remain in
  effect; W4A4 does not mean every model module is quantized.
- **MTP:** real EAGLE verification with steps/top-k/draft tokens `3/1/4`, native
  draft inheritance and no simulated acceptance. Resolved draft settings report
  `flashinfer_trtllm` and `modelopt_fp4`; the checkpoint excludes `model.layers.78*`
  from quantization, so the inherited label does not establish FP4 MTP weights.
- **Client:** shared InferenceX random client, `vllm` protocol adapter targeting
  SGLang `/v1/completions`, seed 0, chat template, range ratio 0.8, infinite arrival
  rate, concurrency cap and ignore EOS. The nominal length settings are not exact
  per-request lengths; raw token counts are retained.
- **Timing:** one initial single-request check, `2C` warmup attempts, then `10C`
  measured requests. Initial check and warmup are outside measurement. Each point
  is one measured run, not a median across repetitions; no confidence interval or
  latency-SLO qualification. Warmup result objects are discarded, so the zero-failure
  claim applies to measured requests only.
- **Metrics:** output throughput counts generated tokens; total throughput counts
  input plus output tokens, divided by measured duration. Per-GPU values divide by
  the actual TP GPU count. Latencies are milliseconds. Request-level latency
  percentiles are distinct from statistics across repeated benchmark runs.

## Runtime observations

The default resolves to **full decode graphs and breakable prefill graphs with a
2048-token maximum batch**. Actual use depends on the batch: logged measured 8k1k
prefill batches are mostly `False`, with two `True` batches at C256 (1664 and 1961
new tokens). 1k1k prefill logs are mostly `True` with some `False`; audited measured
decode log samples report `True`. These are logged batches, not every graph or
kernel invocation.

| Case | Allocator warnings before / during measurement | Total late-load / low-free-memory advisories | Measured requests |
| --- | --- | --- | --- |
| 8k1k TP4 C128 | 3 / 1 | 24 | 1280/1280 |
| 8k1k TP4 C256 | 9 / 12 | 666 | 2560/2560 |
| 1k1k TP4 C256 | 4 / 12 | 476 | 2560/2560 |

Advisory totals cover the whole case, not just measurement. These warnings were
nonfatal. Continuation is consistent with allocator recovery,
but the logs do not identify its exact retry branch or quantify performance cost.
The single-run TP4 output throughput falls from C128 to C256 in both workloads:
8k1k `2362.353664 → 2168.793740` tokens/s; 1k1k
`5342.922157 → 4317.191813` tokens/s. This does not establish the cause; all points
and warning evidence are retained.

Shutdown logs also contain diagnostics: 8k1k TP4 C64 has three `ERROR:` severity
lines after measurement during SIGTERM cleanup. For 1k1k TP8 C4, measurement ends
at 09:46:56.701186 UTC; SIGTERM at 09:46:57 is followed by detokenizer exit `-15`
and watchdog-triggered SIGQUIT at 09:46:58. No schedulers remain at 09:47:03 and
the case records exit code 0. This is a post-measurement shutdown escalation:
the watchdog treats a nonzero child exit, including SIGTERM, as an error and
signals SIGQUIT. Measured counts and case exit statuses pass; this does not mean
the complete server logs are error-free. The automated `ERROR:` prefix count
misses this unprefixed watchdog diagnostic; direct log inspection supplements the
[runtime audit](runtime-audit.md). Severity-line counts are not counts of
independent exceptions.

Reported acceptance length is cumulative over the server lifetime, including
warmup/reporting windows, not measured-only acceptance. There is no MTP-off control
or accuracy evaluation, so these results establish neither an isolated MTP speedup
nor numerical/quality equivalence. The future MegaMoE setup changes precision,
backend, TP=DP=EP topology, draft configuration and prefill graph policy together.

## Evidence retention

This directory contains 160 unchanged raw client/provenance files. The
[manifest](manifest.json) records SHA256, size, relative path and inclusion status
for **all 208 original per-case files**. Full server logs and GPU telemetry remain
in the persistent/local raw archive. Whole-node telemetry is not per-arm energy.

Persistent archive root:
`/data/home/ziangli/inferencex-glm52-b300/archives/`.

| Archive | SHA256 |
| --- | --- |
| `c2-w4a4-20260919-raw.tar.gz` | `1fde3e3fb77e40433b7c9589d69a8334ccdd6b7027991a1f1d7bfb89812907c5` |
| `c2-w4a4-20260919-flashinfer-0.6.18-autotune.tar.gz` | `113fd410166df5f2610ffd1ef8fbb6879d539ed03f2000fccc5bebd99068faf6` |

The checkpoint, source checkouts and run artifacts remain under the persistent
experiment root for the later MegaMoE run. These results belong to this fork
experiment and do not publish to the official InferenceX dashboard.
