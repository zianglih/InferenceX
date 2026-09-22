# GLM-5.2 NVFP4 + MTP on B300: local 8k/1k and 1k/1k experiment

**English** | [中文](README_zh.md)

This fork-only experiment carries the archived GLM-5 B300 workload forward to
`nvidia/GLM-5.2-NVFP4`. It is separate from the current AgentX configurations and
does not reactivate deprecated benchmark definitions or publish dashboard results.

## Current continuation: recovery5 on a different physical node

[Recovery5](RECOVERY5.md) runs the remaining 14 points / 7,640 requests on a new
8-B300 node, `hu-pdx-142`. The prior node, `hu-pdx-126`, remains available for
separate real-weight NVSHMEM diagnostics. Their observed driver and pristine
package inventories match; all eight GPU UUIDs differ. Sources, image, package
pins, server settings and client workloads remain fixed. A successful new-node
run would support further node-specific investigation, not establish root cause.

Recovery1's accepted 8k1k/TP4 C256 and C4 points (2,600 requests) retain their
original bytes and pins. Recovery1, recovery3 and recovery4 C8 startup failures,
and recovery2's separate missing-resource failure, remain preserved. Recovery4
used a fresh container and empty cache on the same physical host and reproduced
`nvshmem API called before nvshmem_init`; it produced no measured point.

The new bootstrap and continuation use exclusive source/run/cache identities and
the reviewed frozen preparation primitives. Preparation never starts serving.
Actual environment validation and an independent first-C8 audit remain required.
Final 16-point acceptance and the refreshed 48-point Pareto comparison are pending.
Historical setup below must not overwrite an earlier attempt; use the recovery5
guide for the current continuation.

## Authorized MegaMoE follow-up (recovery preparation)

`config-megamoe.env` now overrides the base SGLang pin with rebased
[PR #39210](https://github.com/sgl-project/sglang/pull/39210) head
`6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2`. The integration owner completed final-head unit, native EP4 and model validation.
The user authorized publishing the new scripts, then running only MegaMoE.
Full GLM-5.2 MTP serving and performance validation are the purpose of this new run.

The [Docker Hub tags](https://hub.docker.com/r/lmsysorg/sglang/tags) checked on
2026-09-21 UTC still list `nightly-dev-cu13-20260918-20518d85` as the latest
CUDA 13 dev nightly supporting linux/amd64. The overlay pins that image's amd64
manifest `sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596`.
The newer `nightly-cu134-20260920-efa7be2` supports arm64 only. Thus the image
release is unchanged; the SGLang source changes. FlashInfer remains at `ad0a5e5e`.

The authorized follow-up will measure **only the new MegaMoE arm**, then compare
it with the completed TRT-LLM and CuTe split controls. The user accepts their
different SGLang/dependency environments; the size of that effect is not yet
measured. Preserve the original 48-point report separately, and label the new
comparison with each arm's own pins rather than as an environment-matched or
kernel-only comparison. DP attention, TP=DP=EP, memory `0.80`, disabled prefill
graphs, TRT-LLM/none MTP, both workloads and the 16-point matrix remain unchanged.

The first new attempt lost its devbox during startup; no completed measurement had
been verified. The cause is unknown. Preserve that attempt and use a fresh root
and explicit `--run-id` for recovery. Each finalized, audited point will also be
compared with the original MegaMoE, Split and TRT-LLM measurements to flag possible
regressions before the full sweep completes. Partial comparisons remain separate
from final plots and cannot isolate integration causality across different environments.

Use a fresh source checkout, run ID, output directory and `MEGAMOE_CACHE_ROOT`.
The runner sets `SGLANG_CACHE_DIR=$MEGAMOE_CACHE_ROOT/sglang` and
`FLASHINFER_WORKSPACE_BASE=$MEGAMOE_CACHE_ROOT`; the overlay explicitly enables
`SGLANG_FLASHINFER_AUTOTUNE_CACHE=1` for reuse within this new campaign. The new
adapter's authoritative tactic records live in SGLang's namespaced autotune JSON,
not the legacy per-TP `knobs.json`. CuTe DSL, CUDA, Torch extensions/Inductor,
Triton and XDG caches also use explicit subdirectories of this campaign root.
Mega's own decode/prefill profiles do not
require `SGLANG_FLASHINFER_AUTOTUNE_EXTEND=1`; that does not establish prefill
tuning coverage for every other operator or the MTP draft.

The old project setup/launch helpers describe the completed run and must not be
reused with its old paths or IDs. Actual source imports, dependencies, tuning
coverage and memory headroom still require new runtime validation. Sourcing this
overlay selects the new pins; it does not install that stack or start a server.

[`campaign_20260921.py`](campaign_20260921.py) prepares an unused campaign root,
verifies the existing FI/CuTe stack, and changes only the editable FlashInfer source
binding without installing dependencies. Run from the published recipe checkout
on the idle selected node after preparing the pinned dependencies; provide the explicit image/node provenance receipt.
Review `environment/setup-completed.json` before the separate launch command:

```bash
python3 experimental/glm52_b300_fixed_seq/campaign_20260921.py prepare \
  --task-root /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery1 \
  --run-id c2-w4a16-megamoe-autotune-20260921-recovery1 \
  --recipe-commit "$(git rev-parse HEAD)" \
  --model-path /data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4 \
  --image-receipt /path/to/image-receipt.json
python3 /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery1/sources/inferencex/experimental/glm52_b300_fixed_seq/campaign_20260921.py launch \
  --task-root /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery1 \
  --run-id c2-w4a16-megamoe-autotune-20260921-recovery1
```

The worker records benchmark and overall exit codes separately and archives
raw/environment/source evidence plus the dedicated cache after the benchmark exits.
The archive's request/provenance check does not replace the independent runtime
and tuning audit. `status` reads the launch/exit state; failed evidence is retained.

## Completed baseline

- **Historical W4A4 TRT-LLM reference:** C2 measurement completed on 2026-09-19: all 16 points and
  10,240/10,240 measured requests passed. See [results, charts and runtime limits](results/c2-w4a4-20260919/README.md).
  Retains the original TP4/DP1/EP1 concurrency sweep and TP8/DP1/EP1 concurrency-4 point;
  these results remain unchanged and separate from the new comparison.
- **New W4A4 TRT-LLM control:** [`config-trtllm-aligned.env`](config-trtllm-aligned.env)
  aligns DP attention, TP=DP=EP, prefill graphs, draft settings and memory reservation with MegaMoE.
  It retains FlashInfer 0.6.18 and CuTe DSL 4.6.2; its existing 0.80 run is reused unchanged.
- **Completed W4A16 MegaMoE:** used the pinned FlashInfer PR #5019 source
  and a native TRT-LLM BF16 MTP draft. The first memory-fraction-0.85 attempt completed six points, then failed during C256 warmup. The complete-matrix run uses memory fraction 0.80 and remains preserved. The current
  [`config-megamoe.env`](config-megamoe.env) prepares the follow-up above; it no longer reproduces that run's SGLang pin.
- **W4A16 CuTe DSL split MoE:** [`config-cutedsl.env`](config-cutedsl.env) and
  [`w4a16_cutedsl_mtp.sh`](w4a16_cutedsl_mtp.sh) prepare a separate third arm at
  FlashInfer PR #5319. It sets `SGLANG_FLASHINFER_MOE_FUSED_FINALIZE=0` and
  `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`; all 16 points completed.
- **Quality:** these scripts collect throughput and latency, not model accuracy.
  They use real MTP verification; inherited simulated acceptance settings are cleared.

## Configuration and provenance

[`config.env`](config.env) is the executable experiment configuration. Source it,
then explicitly supply local paths and a unique run ID. No script downloads weights,
installs packages, or upgrades FlashInfer. The base configuration selects
`PARALLEL_TOPOLOGY=tp` and `PREFILL_CUDA_GRAPH_POLICY=latest-default` for the historical
topology. The TRT-LLM, MegaMoE and CuTe DSL overlays all select `dp-ep` and `disabled`.
The historical reference and new TRT-LLM control use the image's installed
FlashInfer unchanged. MegaMoE and CuTe DSL each pin their own FlashInfer source
and require a separately prepared dependency stack. Source checkouts must match their pins; `PYTHONPATH` and runtime import
checks select them. Keep the measured baseline's source, packages and cache archive
separate from the optimized run.

| Field | Value |
| --- | --- |
| Image | `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85` |
| SGLang | Base / completed arms: `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; next MegaMoE only: `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2` ([PR #39210](https://github.com/sgl-project/sglang/pull/39210)) |
| MegaMoE FlashInfer | [PR #5019](https://github.com/flashinfer-ai/flashinfer/pull/5019), `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; B300 build target `10.3a` |
| CuTe DSL FlashInfer | [PR #5319](https://github.com/flashinfer-ai/flashinfer/pull/5319), `f9dd3c10541e087b716772245a9d033499745048`; B300 build target `10.3a` |
| Model | `nvidia/GLM-5.2-NVFP4` |
| Model revision | `53e0691e21895a3863a606dfd12910c69eba94ab` |
| Quantization / KV cache | `modelopt_fp4` / `fp8_e4m3` |
| Attention | `dsa`, with TRT-LLM prefill and decode |
| MTP | EAGLE: 3 steps, top-k 1, 4 draft tokens |
| Draft MoE | All aligned arms: explicit `flashinfer_trtllm`, A2A `none`; historical reference: native inherited settings; no explicit draft quantization override |
| Memory / prefill | Historical `0.85`; all aligned arms `0.80`; CLI chunked prefill and max prefill tokens both `32768`, with DP normalization below |
| Cache / streaming | Radix cache disabled; stream interval `30` |
| Workload | Random, input cap `8192` or `1024`, output cap `1024`, range ratio `0.8`, chat template |
| Requests / warmup | `10 × concurrency` measured; `2 × concurrency` warmup |
| Sweep | TP4 concurrency `4,8,16,32,64,128,256`; TP8 concurrency `4`, for each scenario |

The two workloads are named "8k/1k" and "1k/1k," but the range ratio means actual
lengths vary below those upper bounds. Keep the raw input/output token counts when
comparing results. The shared InferenceX client uses an infinite request rate,
limits maximum concurrency, and ignores EOS. These are throughput sweeps without
an interactive latency SLO. Each point is one measured run, not a multi-run median.

| Arm | Target runner / A2A | TP / DP / EP | Prefill CUDA graphs | FlashInfer / CuTe DSL |
| --- | --- | --- | --- | --- |
| Historical W4A4 reference | `flashinfer_trtllm` / `none` | TP / 1 / 1 | Pinned SGLang default | 0.6.18 / 4.6.2 |
| New aligned W4A4 control | `flashinfer_trtllm` / `none` | TP / TP / TP, DP attention enabled | Disabled | 0.6.18 / 4.6.2 |
| New W4A16 MegaMoE | `flashinfer_megamoe` / `flashinfer_megamoe` | TP / TP / TP, DP attention enabled | Disabled | 0.7.0 at `ad0a5e5e` / 4.7.1 |
| W4A16 CuTe DSL split MoE | `flashinfer_cutedsl` / `none` | TP / TP / TP, DP attention enabled | Disabled | 0.7.0 at `f9dd3c10` / 4.7.1 |

At the pinned SGLang commit, MegaMoE [requires DP attention and DP=TP](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/arg_groups/moe_hook.py#L275-L303)
and [forces EP=TP](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/arg_groups/overrides.py#L1630-L1672).
TRT-LLM's NVFP4 path [passes local expert offsets and counts](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/layers/quantization/modelopt_quant.py#L2996-L3031),
so the new control uses the same expert partitioning with standard communication.
Source compatibility still requires fresh runtime validation.

The first DP-aligned MegaMoE attempt at `mem_fraction_static=0.85` stopped during
8k1k TP4/C256 warmup: the native BF16 TRT-LLM MTP prefill path could not allocate
its 3.16 GiB workspace with 1.37 GiB free. No measured C256 result was produced.
[The failed case and recovery record](results/failures/c2-w4a16-megamoe-20260920/README.md)
are preserved separately. Both new overlays now use **0.80** to reserve additional
runtime workspace, and both complete 16-point sweeps use fresh run IDs. C256 runs
first in each scenario to check the failing peak early; the matrix and request
counts are unchanged. The six successful 0.85 points are diagnostic observations,
not reused in the 0.80 comparison. Metadata, resolved arguments and plot grouping
record the memory fraction. The later CuTe DSL arm uses the same 0.80 reservation
and C256-first order; it does not restart or replace either existing 0.80 run.

The historical server request cap equals client concurrency. All aligned arms use
`max(client concurrency, DP)` because the pinned SGLang divides that cap by
attention DP and requires at least one request per rank. Thus all aligned TP8/C4 cases have
a server cap of **8**, while client concurrency remains **4** and the measured
request count remains **40**. The TP4 points are unchanged. Metadata records
`server_max_running_requests` separately from client `concurrency`.
At TP8/C4 in each aligned arm, the configured decode graph maximum remains **4**, but the
per-DP request capacity limits capture buckets to `[1]`. The shared chunked-prefill
CLI value `32768` resolves to **8192 per DP rank at TP4** and **4096 at TP8** in
all aligned arms; their prefill graphs remain disabled independently. These are
[source-derived pool limits](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/mem_cache/kv_cache_configurator.py#L2267-L2320)
and [capture-bucket filtering](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/model_executor/runner/base_cuda_graph_runner.py#L66-L105),
to be checked against each run's resolved settings and logs.

All arms use BF16 activations at the model interface and disable per-token FP4
activation quantization. MegaMoE uses BF16 combine storage with in-kernel FC2
reduction disabled. Both W4A16 arms enable `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`;
CuTe DSL additionally disables fused finalize and uses the standard A2A `none`
path, rather than MegaMoE's internal communication path.
The main comparison aligns parallel topology, prefill graph policy and draft
backend. Target W4A4 versus W4A16 precision, MoE/communication backend, FlashInfer
source and CuTe DSL version still differ; it does not isolate a kernel-only speedup.

The archived script's explicit `--quantization fp8` is incompatible with this
serialized NVFP4 checkpoint and is corrected to `modelopt_fp4`. Removed CLI names
are migrated to `dsa`, `--dsa-*-backend`, and `--cuda-graph-max-bs-decode`; the decode
configured graph bound still equals concurrency; the server request-cap exception is described
above. The removed
`SGLANG_ENABLE_SPEC_V2` setting is omitted because V2 is always active at this HEAD.
The historical reference preserves native draft settings. All aligned arms explicitly
set `--speculative-moe-runner-backend flashinfer_trtllm` and
`--speculative-moe-a2a-backend none`, and omit
`--speculative-draft-model-quantization`. This replaces the earlier Triton/unquant
draft setup in the MegaMoE arm. As in the historical reference, the serialized draft quantization setting can
inherit `modelopt_fp4`, while the GLM NextN decoder constructs its native BF16 MoE
with [`quant_config=None`](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/models/deepseek_nextn.py#L64-L79);
the inherited label does not make its weights FP4. The new arms align draft
backend and topology, but their FlashInfer versions differ, so they are not
identical software execution paths.

## Run the historical topology

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
export RUN_ID=c2-w4a4-historical-repeat
bash experimental/glm52_b300_fixed_seq/w4a4_trtllm_mtp.sh
```

For one point or a resumed subset, set `SWEEP_CASES` **after** sourcing the config,
for example `export SWEEP_CASES='4:4'`. Both scenarios run by default; select one
with `export SCENARIOS='8k1k:8192:1024'` or `export SCENARIOS='1k1k:1024:1024'`. Select available physical GPU indices with
`GPU_IDS`; each case uses the first TP entries. Use a new `RUN_ID` for repeated
measurements; existing case directories are never overwritten. Each case launches
its own server, records results, stops its owned process group, and fails the sweep
on a server/client/cleanup error or any missing measured request.

## Run the aligned TRT-LLM control

Use the original image environment with FlashInfer 0.6.18 and CuTe DSL 4.6.2,
not the environment upgraded for MegaMoE. Set the same local model/source/output
paths as above, then select the control overlay and a separate run ID:

```bash
source experimental/glm52_b300_fixed_seq/config.env
source experimental/glm52_b300_fixed_seq/config-trtllm-aligned.env
export RUN_ID=c2-w4a4-dp-aligned-first
bash experimental/glm52_b300_fixed_seq/w4a4_trtllm_mtp.sh
```

The overlay changes topology, prefill policy and memory reservation, not installed packages. Record
the fresh 16-point result independently; the historical DP1/EP1 measurements do
not substitute for this control.

## Prepare the optimized MegaMoE arm

After preparing the pinned FlashInfer checkout and compatible dependencies, source
`config.env` followed by `config-megamoe.env`, then provide `FLASHINFER_SOURCE_ROOT`
and a separate `MEGAMOE_CACHE_ROOT` alongside the shared paths. The overlay enables
`RUN_MEGAMOE=true` and pins the FlashInfer commit and B300 CUDA architecture.
Use a new run ID with [`w4a16_megamoe_mtp.sh`](w4a16_megamoe_mtp.sh); the same
8k1k/1k1k and TP/concurrency matrix remains configured.

Keep the image's Torch and install the optimized FlashInfer/CuTe stack separately;
the baseline image's FlashInfer 0.6.18 cubin/JIT packages are not the optimized
source's dependencies. The prepared stack uses matching CuTe DSL 4.7.1 packages
and fresh source-specific caches. Record its actual resolved environment and
startup/measurement outcomes. The overlay does not install dependencies or certify
runtime compatibility, accuracy or performance.

## Prepare the CuTe DSL split-MoE arm

Reuse the existing aligned TRT-LLM and MegaMoE results. Prepare the PR #5319 source
and its dependencies separately: FlashInfer 0.7.0, all five CuTe DSL packages at
4.7.1 and `nccl-extensions==0.1.0`, with the image's Torch unchanged and no installed
FlashInfer cubin/JIT-cache providers. The source declares the NCCL extension
dependency; the standard CuTe DSL target path does not use MegaMoE's EP transport.
The preflight checks the clean source commit/import, FlashInfer package/import
version, CuTe DSL versions and absence of the old binary providers. It does not
prove GPU compatibility or accuracy.

```bash
source experimental/glm52_b300_fixed_seq/config.env
source experimental/glm52_b300_fixed_seq/config-cutedsl.env
export SGLANG_SOURCE_ROOT=/data/home/ziangli/inferencex-glm52-b300/sources/sglang
export FLASHINFER_SOURCE_ROOT=/data/home/ziangli/inferencex-glm52-b300/sources/flashinfer-f9dd3c10
export CUTEDSL_CACHE_ROOT=/data/home/ziangli/inferencex-glm52-b300/caches/cutedsl-f9dd3c10-cute4.7.1-cu13
export MODEL_PATH=/data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4
export OUTPUT_ROOT=/data/home/ziangli/inferencex-glm52-b300/results
export RUN_ID=c2-w4a16-cutedsl-mem80-first
bash experimental/glm52_b300_fixed_seq/w4a16_cutedsl_mtp.sh
```

The canonical backend is `w4a16_cutedsl`, with case directories under
`<scenario>/w4a16-cutedsl/`. The caller supplies an absolute `CUTEDSL_CACHE_ROOT`
outside `/workspace`; SGLang uses its `sglang/` subdirectory, while FlashInfer's
workspace uses the root and stores its own cache under `.cache/flashinfer/`.
Preserve this entire source-specific cache separately. An inherited MegaMoE knob
cache is cleared. Server commands and metadata retain W4A16/finalize settings and
the resolved source/cache paths. The third arm retains both workloads, all 16
points, C256 first, the shared server-cap correction and native BF16 TRT-LLM MTP.
Its newer InferenceX configuration commit is recorded separately from the reused
runs; backend/software differences prevent a kernel-only causal comparison.

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
it. Preserve failed artifacts and do not present pending points as measured
data. Normalize throughput using the recorded GPU count when comparing TP4 and TP8.

## Main Pareto comparison

Use [`plot_pareto.py`](plot_pareto.py) with the aligned TRT-LLM, MegaMoE and CuTe DSL
completed run roots. Keep 8k1k and 1k1k in separate plots and plot the
historical reference separately:

```bash
python3 experimental/glm52_b300_fixed_seq/plot_pareto.py \
    --results "$ALIGNED_TRT_ROOT" "$MEGAMOE_RESULT_ROOT" "$CUTEDSL_RESULT_ROOT" \
    --output "$OUTPUT_ROOT/pareto-aligned" --dp-attention-aligned
```

The main x axis is **per-request interactivity = `1000 / median_tpot_ms`**
(tok/s/user), and y is **`output_throughput / gpu_count`** (output tok/s/GPU).
Both increase toward the preferred frontier. Interactivity excludes the first
token; it is neither mean request rate nor proof of a latency SLO. DP/EP share the
same TP GPUs and do not multiply the denominator. The E2EL view is supplementary.
These formulas follow the [pinned fixed-sequence producer](https://github.com/SemiAnalysisAI/InferenceX/blob/8979f7c4cdd2946a02b459d5e62018e41bc02405/infx/results/fixed_sequence.py#L187-L207),
with the [pinned interactivity metric](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/components/inference/metric-registry.ts#L701-L708)
and [selected output-only y metric](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/components/inference/metric-registry.ts#L76-L82).
The plotting helper validates alignment, rejects mixed historical/aligned inputs,
keeps successful observed points visible and labels client concurrency plus TP/DP/EP.
The complete memory-fraction-0.80 comparison contains **48 points and 30,720 successful measured requests**. See the [full report and figures](results/c2-three-arm-dp-mem80-20260920/comparison.md) and [all raw metric tables](results/c2-three-arm-dp-mem80-20260920/raw_metrics.md). MegaMoE output throughput/GPU exceeds CuTe split at all eight 1k1k coordinates (+1.99% to +16.91%); at 8k1k it is lower at seven coordinates and higher at TP8/C4 (+5.62%). These are single-run end-to-end observations with different FlashInfer heads, not isolated kernel speedups. Partial 0.85 observations remain separate and are not plot inputs.
