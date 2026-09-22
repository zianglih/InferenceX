# MegaMoE recovery7: SGLang workaround with stock NVSHMEM

**English** | [中文](./RECOVERY7_zh.md)

This fork-only continuation runs the 14 remaining MegaMoE points. It uses SGLang `26c41009549f9ad407e107b33d5144f6e085418b` and the unmodified NVSHMEM 3.4.5 wheel. The original accepted recovery1 8k1k TP4 C256/C4 points remain unchanged: 2,600 measured requests with SGLang `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2` and the original proxy defaults. The remaining 14 points contain 7,640 measured requests. This recipe does not itself establish startup success or new serving performance.

## Workaround and scope

The [SGLang integration](https://github.com/sgl-project/sglang/pull/39210) supplies these defaults before NVSHMEM initialization, preserving explicit user overrides:

```text
NVSHMEM_REMOTE_TRANSPORT=none
NVSHMEM_IB_ENABLE_IBGDA=0
NVSHMEM_DISABLE_LOCAL_ONLY_PROXY=1
```

They apply only to single-node NVFP4 W4A16 MegaMoE with no speculation or an explicitly separate draft A2A backend of `none`. NVSHMEM retains its direct peer path and skips proxy initialization. This requires direct peer connectivity; NVSHMEM device-side wait timeouts and device global-exit functionality are disabled. The launcher leaves all three settings absent and verifies that the published SGLang code establishes them on every serving rank. It supplies only `NVSHMEM_DEBUG=INFO` for the native log evidence.

The underlying uninitialized proxy exit-request/code investigation and matched native-build experiment are summarized in [NVSHMEM_STARTUP.md](./NVSHMEM_STARTUP.md). Recovery7 loads the stock wheel, without the experimental native patch, preload, custom UID plugin or host-search overlay. Matched-build diagnostic success is not validation of this different workaround; a real startup with the published SGLang head and stock wheel is required before campaign activation.

## Fixed protocol

- FlashInfer `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; image `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85@sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596`.
- Eight B300 GPUs; five CuTe 4.7.1 providers, nccl-extensions 0.1.0, cupti-python 13.2.0 and CUPTI library 13.2.86. Preserve image Torch/CUDA/loaded NCCL and unrelated packages. The bootstrap probe loaded NCCL 2.29.7; the installed package and SGLang startup log report 2.30.7. These are distinct recorded observations, not an assertion that every process loaded the same NCCL image.
- TP=DP=EP, DP attention, memory fraction .80, FP8 E4M3 KV, disabled prefill graphs, global prefill chunk 32768, and native BF16 TRT-LLM/none MTP 3/1/4. Mega prepares its own profiles; do not force `SGLANG_FLASHINFER_AUTOTUNE_EXTEND=1`.
- Real 47-shard `nvidia/GLM-5.2-NVFP4`, revision `53e0691e21895a3863a606dfd12910c69eba94ab`. Config/index/revision and shard sizes are verified; this is not a new 464 GB tensor-content hash.
- Unchanged random client ratio .8, chat template, unlimited arrival rate, initial short check, 2C warmup and 10C measured requests. Nominal 8192/1024 and 1024/1024 are length bounds; the saved ordered input/output arrays define the actual comparison.
- Remaining order: 8k1k TP4 C8/16/32/64/128, TP8 C4; then 1k1k TP4 C256/4/8/16/32/64/128, TP8 C4. There are 1,528 warmup and 7,640 measured requests. With the original two points, the matrix totals 16 points and 10,240 measured requests.

## Preparation and launch

The portable entry point is `recovery7/cli.py`; it performs no HAI operations. Its shipped activation template is unbound and rejects execution. The campaign root/run are `/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery7` / `c2-w4a16-megamoe-autotune-20260921-recovery7`. Bind actual node identity, GPU UUIDs, current bootstrap/source/provider receipts and predecessor process births from the new resource. Historical records do not establish current liveness.

Stage the exact published recipe and five accepted JSON gate reports outside the new root. Fill and hash-bind `activation.template.json` with the published commit/bundle, actual environment and stock native descriptors, original PATH/ordered LD_LIBRARY_PATH, model path, immutable original raw28 root, and the accepted C8's independent SG26c source checkout. Required evidence includes actual stock-wheel C8, full source/native payloads, bootstrap and execution review. Pending or synthetic records do not authorize launch.

```bash
/opt/sglang/bin/python3 -B "$STAGE/recovery7/cli.py" prepare \
  --lock "$STAGE/activation.json" --lock-sha "$ACTIVATION_SHA"
# Verify and accept actual preparation before this separate, single launch.
/opt/sglang/bin/python3 -B "$STAGE/recovery7/cli.py" launch \
  --lock /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery7/environment/activation.json \
  --lock-sha "$ACTIVATION_SHA"
```

Preparation creates an exclusive root and clones pinned SG/FI/dependencies/recipe with `--local --no-hardlinks`. It checks SG26c's parent and sole 20-line production delta, installs no packages, copies no old caches and changes no old roots. It seals fresh imports, full freeze, checkpoint metadata, six source archives, stock native files and eight idle GPUs. The wrapper exports SG26c after sourcing the unchanged historical config. Failed or interrupted launch identities are preserved rather than reused.

## Evidence and comparison

Before any warmup/client work, all TP4/TP8 ranks must have natural-init entry/return records showing the effective defaults, actual SG/FI origins and stock host/UID maps. PID/device/hostname-attributed `Proxy is disabled.` logs and their native limitation text are bound to a preclient log prefix. The observer adds no native init/getter calls. Maps and birth records are checked again after measurement, before owned cleanup.

Original raw14 files remain unchanged. `native-runtime/<run>/<case>` adds native contracts, commands, process ownership, startup/post-measurement records and `proxy-disabled.json`. A finalized `joins/<case>.json` binds raw14 and these records only after original artifact finalization. The join is producer evidence; an independent raw/settings/native audit and first-case calibration remain required.

Compare each accepted new point against original Mega first, then unchanged Split/TRT, using identical ordered token lengths. Report signed throughput/GPU, interactivity, TTFT/TPOT/E2EL and saved p90/p99. InferenceX did not save per-request latency arrays or p95; do not reconstruct them. Per-DP cumulative MTP acceptance-length averages include warmup and are not a measured global acceptance rate.

The final 48-point report combines 16 refreshed Mega points with 32 historical controls. Pareto axes remain `1000 / median_tpot_ms` tokens/s/user and whole-interval output tokens/s/GPU, which includes prefill. Retain each point's source/default/node/cache provenance, including the two reused SG6d8 points. These comparisons do not isolate kernel/autotune/NVSHMEM causality or statistical significance. Full raw/source/native/cache verification, independent figures and publication readback precede resource cleanup.
