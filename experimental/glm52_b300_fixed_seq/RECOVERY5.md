# Recovery5: remaining points on a separate physical node

**English** | [中文](RECOVERY5_zh.md)

This new campaign uses `infx-glm52-peer-0921` in C2, namespace `infra`, queue `earth`, physical host `hu-pdx-142`. The caller's observed image receipt and all eight GPU UUIDs are required. The parent inventory recorded disjoint UUIDs from the retained faulty host `hu-pdx-126`, matching driver `590.48.01`, matching pristine package inventories and the same checkpoint metadata. This establishes a different physical host; it does not establish the cause of earlier NVSHMEM failures. The faulty node is retained separately for diagnostics.

Only two new entrypoints are added. They reuse the byte-pinned [`recovery4_frozen/`](recovery4_frozen/) primitives, wheel lock, original success references and the unchanged `run_megamoe_recovery3.sh` fourteen-point wrapper. Recovery1–4 sources, logs, failures and archives remain intact.

| Contract | Recovery5 |
| --- | --- |
| Image | `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85@sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596` |
| SGLang / FlashInfer | `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2` / `ad0a5e5e78e57070ec7c582efe733cb55cd8839f` |
| Dependencies | Same eight SHA-locked wheels: five CuTe DSL `4.7.1` packages, `nccl-extensions==0.1.0`, `cupti-python==13.2.0`, `nvidia-cuda-cupti==13.2.86`; FlashInfer editable `0.7.0`, no cubin/JIT distribution |
| Runtime | Original image Torch/CUDA/NCCL and unrelated packages preserved and checked before/after |
| Serving | Real `nvidia/GLM-5.2-NVFP4`, TP=DP=EP, `.80`, TRT-LLM BF16 MTP/none, EAGLE 3/1/4, prefill graph disabled; unchanged workloads and client settings |
| New run | `c2-w4a16-megamoe-autotune-20260921-recovery5`: 14 points / 7,640 required successful requests |
| Reuse | Immutable recovery1 8k1k TP4/C256 and TP4/C4: 2 points / 2,600 successes; no copied or rewritten case metadata |
| Combined target | 16 points / 10,240 successes only after all per-case gates and new C8 calibration |

The new campaign and bootstrap roots are respectively `/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery5` and `/data/home/ziangli/inferencex-glm52-megamoe-bootstrap-20260921-recovery5`. Both must be absent. All sources are freshly cloned at exact commits. FlashInfer's editable install occurs directly in its final source directory; five data-resource links, build metadata, eleven sentinel files and three registered dependency commits are checked, and all six source archives are sealed at preparation time. Bootstrap imports use a separate cache; the campaign cache must remain empty until its first server starts. No old cache is scanned, copied or imported.

Publish the reviewed scripts first. From their containing directory, the default commands below print plans without invoking processes or network calls:

```bash
python3 -B bootstrap_megamoe_recovery5.py
python3 -B continue_megamoe_recovery5.py
```

The operator stages both new scripts and the unchanged `recovery4_frozen` directory together. On the exact peer node, supply the actual receipt and the full newly published recipe commit explicitly:

```bash
/opt/sglang/bin/python3 -B bootstrap_megamoe_recovery5.py apply \
  --image-receipt /absolute/path/to/peer-image-receipt.json \
  --recipe-commit FULL_PUBLISHED_RECIPE_COMMIT
```

The image receipt must match the observed inventory SHA `132064aa6e3f29eeed84a678fe5b6bf9da21cc9ae2a260a16468f442341c4161`. Its image evidence is explicit provisioning/Ready/pristine-runtime evidence, not a Kubernetes imageID claim. Preparation never starts a server. Review the new sealed environment and CLI compatibility before issuing the single launch from the campaign-local sealed helper:

```bash
/opt/sglang/bin/python3 -B \
  /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery5/environment/helpers/continue_megamoe_recovery5.py launch
```

The worker records the benchmark exit, then seals raw/source and campaign-cache archives for success or failure. Full-matrix success requires exactly the remaining fourteen cases. A failed case is retained and cannot be reused as a successful result; startup or calibration remains unverified until actual evidence arrives. Bootstrap/CLI/default caches need separate retirement preservation. No dummy model or diagnostic kernel is part of this campaign.
