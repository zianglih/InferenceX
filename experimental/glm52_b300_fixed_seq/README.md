# GLM-5.2 NVFP4 + MTP on B300: local 8k/1k and 1k/1k experiment

**English** | [中文](README_zh.md)

This fork-only experiment carries the archived GLM-5 B300 workload forward to
`nvidia/GLM-5.2-NVFP4`. It is separate from the current AgentX configurations and
does not reactivate deprecated benchmark definitions or publish dashboard results.

- **W4A4 TRT-LLM:** C2 measurement completed on 2026-09-19: all 16 points and
  10,240/10,240 measured requests passed. See [results, charts and runtime limits](results/c2-w4a4-20260919/README.md).
  Retains the original TP4/DP1/EP1 concurrency sweep and TP8/DP1/EP1 concurrency-4 point.
- **W4A16 MegaMoE:** prepared and deferred until the optimization stack is ready.
  It has not been run or measured. Its entry point refuses to run unless the
  caller explicitly sets `RUN_MEGAMOE=true`.
- **Quality:** these scripts collect throughput and latency, not model accuracy.
  They use real MTP verification; inherited simulated acceptance settings are cleared.

## Configuration and provenance

[`config.env`](config.env) is the executable experiment configuration. Source it,
then explicitly supply local paths and a unique run ID. No script downloads weights,
installs packages, or upgrades FlashInfer. The baseline uses the image's installed
FlashInfer unchanged. The configured source checkout must be at the pinned commit
with no tracked Python changes; `PYTHONPATH` and a runtime import check select it.

| Field | Value |
| --- | --- |
| Image | `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85` |
| SGLang | [PR #39210](https://github.com/sgl-project/sglang/pull/39210), `50eeb742961908afa68f4f523a1a19c5de6eb0b3` |
| Model | `nvidia/GLM-5.2-NVFP4` |
| Model revision | `53e0691e21895a3863a606dfd12910c69eba94ab` |
| Quantization / KV cache | `modelopt_fp4` / `fp8_e4m3` |
| Attention | `dsa`, with TRT-LLM prefill and decode |
| MTP | EAGLE: 3 steps, top-k 1, 4 draft tokens |
| Draft MoE | W4A4: native inherited settings; MegaMoE: `triton`, A2A `none`, quantization `unquant` |
| Memory / prefill | `0.85`, chunked prefill and max prefill tokens both `32768` |
| Cache / streaming | Radix cache disabled; stream interval `30` |
| Workload | Random, input cap `8192` or `1024`, output cap `1024`, range ratio `0.8`, chat template |
| Requests / warmup | `10 × concurrency` measured; `2 × concurrency` warmup |
| Sweep | TP4 concurrency `4,8,16,32,64,128,256`; TP8 concurrency `4`, for each scenario |

The two workloads are named "8k/1k" and "1k/1k," but the range ratio means actual
lengths vary below those upper bounds. Keep the raw input/output token counts when
comparing results. The shared InferenceX client uses an infinite request rate,
limits maximum concurrency, and ignores EOS. These are throughput sweeps without
an interactive latency SLO. Each point is one measured run, not a multi-run median.

| Arm | Target runner / A2A | TP / DP / EP | Prefill CUDA graphs |
| --- | --- | --- | --- |
| W4A4 | `flashinfer_trtllm` / `none` | TP / 1 / 1 | Pinned SGLang default |
| W4A16 | `flashinfer_megamoe` / `flashinfer_megamoe` | TP / TP / TP, DP attention enabled | Disabled: current MegaMoE limitation |

Both use BF16 activations at the model interface, BF16 MegaMoE combine storage,
per-token FP4 activation quantization disabled, and in-kernel FC2 reduction disabled.
Only the MegaMoE arm enables `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`.
The future comparison changes precision, MoE backend, parallel topology and prefill
graph policy together; it does not isolate the effect of a MegaMoE kernel.

The archived script's explicit `--quantization fp8` is incompatible with this
serialized NVFP4 checkpoint and is corrected to `modelopt_fp4`. Removed CLI names
are migrated to `dsa`, `--dsa-*-backend`, and `--cuda-graph-max-bs-decode`; the decode
graph bound and max running requests still equal concurrency. The removed
`SGLANG_ENABLE_SPEC_V2` setting is omitted because V2 is always active at this HEAD.
The baseline preserves native draft settings. The MegaMoE arm explicitly selects
the Triton draft runner, no draft A2A, and an unquantized draft to avoid inheriting
the target MegaMoE backend; this is another difference between the two setups.

## Run the baseline

Use the configured image on one B300 node. Prepare a complete local snapshot of the
pinned model revision, a clean SGLang checkout at the configured commit, and the
InferenceX client dependencies in advance. Keep source and results outside
`/workspace`; the scripts reject result directories beneath it.

```bash
# Run from the InferenceX checkout inside the configured container.
source experimental/glm52_b300_fixed_seq/config.env
export SGLANG_SOURCE_ROOT=/data/home/ziangli/inferencex-glm52-b300/sources/sglang
export MODEL_PATH=/data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4
export OUTPUT_ROOT=/data/home/ziangli/inferencex-glm52-b300/results
export RUN_ID=c2-w4a4-first
bash experimental/glm52_b300_fixed_seq/w4a4_trtllm_mtp.sh
```

For one point or a resumed subset, set `SWEEP_CASES` **after** sourcing the config,
for example `export SWEEP_CASES='4:4'`. Both scenarios run by default; select one
with `export SCENARIOS='8k1k:8192:1024'` or `export SCENARIOS='1k1k:1024:1024'`. Select available physical GPU indices with
`GPU_IDS`; each case uses the first TP entries. Use a new `RUN_ID` for repeated
measurements; existing case directories are never overwritten. Each case launches
its own server, records results, stops its owned process group, and fails the sweep
on a server/client/cleanup error or any missing measured request.

The deferred MegaMoE entry point is
[`w4a16_megamoe_mtp.sh`](w4a16_megamoe_mtp.sh). Before enabling it, verify the final
optimized SGLang/FlashInfer revisions and API compatibility, update and record the
pins, and use a separate run ID. Its current config is a reproducible starting
point, not a claim that the baseline image includes the optimized MegaMoE stack.

## Artifacts and summary

Each case writes `OUTPUT_ROOT/RUN_ID/<scenario>/<arm>/tp<TP>_conc<CONC>/` containing:

- Original `result.json`, client/server logs, and request counts in `status.json`.
- `metadata.json` with model/image/source/version/topology provenance and final status.
- Shell-replayable server and benchmark invocations, plus before/after `/get_server_info`.
- `packages.json`, `nvidia-smi.txt`, and `gpu_metrics.csv`. The shared GPU monitor
  samples the whole node; `CUDA_VISIBLE_DEVICES` in metadata identifies the GPUs
  used by the case. Whole-node telemetry is not per-arm energy consumption.

The summary includes only cases whose scripts and request counts completed cleanly:

```bash
python3 experimental/glm52_b300_fixed_seq/summarize.py \
    --results "$OUTPUT_ROOT/$RUN_ID" --output "$OUTPUT_ROOT/$RUN_ID/summary"
```

Plot output requires `matplotlib`; `--no-plots` produces JSON and Markdown without
it. Preserve failed artifacts and do not present pending MegaMoE points as measured
data. Normalize throughput using the recorded GPU count when comparing TP4 and TP8.
