# Recovery4: fresh-node, real-weight continuation

**English** | [中文](MEGAMOE_RECOVERY4_zh.md)

This is a new clean-node attempt, not a demonstrated fix for the earlier NVSHMEM startup failure. Preserve all earlier attempts. No dummy model, standalone kernel test, tolerance change, old-cache restore, or old-node access is part of this procedure.

Actual provisioning reached Ready at 06:26:59 UTC on 2026-09-21. The parent-collected inventory identifies **`hu-pdx-126`, the same physical host as the retired attempt**, with a fresh container, pristine image packages, eight idle B300 GPUs and absent new task/bootstrap roots. This changes container/source/cache state, not physical hardware. Image evidence is the explicit provisioning request, Ready response and pristine package inventory; it is not a Kubernetes `imageID` measurement. Use the actual receipt under `artifacts/megamoe-clean-node-20260921/provisioning/image-receipt.json`.

| Contract | Value |
|---|---|
| Intended node | `infx-glm52-clean-0921`, C2 / `ziangli` / `earth-non-preempt` |
| Physical host | Must come from the actual new provisioning receipt; never guessed |
| Image | `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85@sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596` |
| SGLang / FlashInfer | `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2` / `ad0a5e5e78e57070ec7c582efe733cb55cd8839f` |
| Task root | `/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery4` |
| Bootstrap root | `/data/home/ziangli/inferencex-glm52-megamoe-bootstrap-20260921-recovery4` |
| Run | `c2-w4a16-megamoe-autotune-20260921-recovery4` |
| Real checkpoint | `/data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4`, revision `53e0691e21895a3863a606dfd12910c69eba94ab`, 47 shards |
| Target providers | FI 0.7.0, five CuTe DSL packages 4.7.1, nccl-extensions 0.1.0, cupti-python 13.2.0, CUDA CUPTI 13.2.86; exact eight-wheel lock retained |
| Measurement contract | W4A16 MegaMoE, TP=DP=EP, MTP TRT-LLM/none, `.80`, prefill graphs disabled, ratio `.8`, ten prompts per concurrency; existing recipe unchanged |

The original C256 and C4 (8k1k, TP4) remain the original 2,600 successful requests, with their original run, physical host, image, recipe and cache history. Recovery4 supplies fourteen new coordinates / 7,640 requests, starting **8k1k / TP4 / C8**. The fixed continuation shell is byte-identical to the existing `run_megamoe_recovery3.sh` (SHA `ae96cbb490c9b57dd74016a19552ae0a8bcff6b08df630613313282b75ccaa38`). Its name is historical; all current paths and run IDs are explicit caller inputs.

## Minimal implementation delta

- [`bootstrap_megamoe_recovery4.py`](bootstrap_megamoe_recovery4.py) clones SG, FI and the caller-pinned recipe independently from their public origins. It installs editable FI **directly into the final campaign tree**. It verifies all five generated FI resource links, `_build_meta.py`, pinned source sentinels, registered dependency gitlinks and all six source archives. It uses the unchanged, byte-pinned package/download/recording primitives in `recovery4_frozen/`. Before any package mutation, both new helpers and all twelve frozen inputs must match the exact files in the cloned published recipe; launch checks that binding again.
- Package checks retain the exact original software baseline outside the explicit provider replacement list. GPU UUID and before/after runtime checks use this new node's own snapshot. The actual image receipt must contain the fixed `node`, `cluster`, `namespace`, `queue`, `image` fields plus the observed `hostname`. Bootstrap never infers an image digest from inside the container.
- Bootstrap imports use a separate fresh bootstrap cache. The campaign cache is newly created and empty, sealed as `cache-origin.json` with `copied:false`. No old cache payload or directory is inspected, linked, or copied. Old archive descriptor/terminal receipts and the accepted 28 raw files are read only to bind immutable reuse.
- [`continue_megamoe_recovery4.py`](continue_megamoe_recovery4.py) launches only its sealed campaign-local copy, checks same-node runtime/source/model/helper seals again, and refuses duplicate run IDs. It retains the accepted worker exit/archive lifecycle and fourteen-case matrix checks. It never checks an old node's PID on the new host.
- Old bootstrap, recovery1/2/3 helpers, all old evidence and the active unrelated bundled-MTP project remain unchanged. New helper byte hashes are separate from `recipe_commit`; both must be included in reports.

## Publication and deployment

Copy these exact new files into the recipe's `experimental/glm52_b300_fixed_seq/` if publishing them: `bootstrap_megamoe_recovery4.py`, `continue_megamoe_recovery4.py`, the complete `recovery4_frozen/` directory, and both guide language files. Do not rename a frozen input, modify an old helper, or change the existing runtime wrapper. Commit/push is performed by the parent only after independent review. Pass that new full recipe commit to bootstrap; the code does not embed a guessed future SHA.

The two default commands below are local plans only, with no subprocesses:

```bash
python3 -B setup/bootstrap_megamoe_recovery4.py plan
python3 -B setup/continue_megamoe_recovery4.py plan
```

After new-node inventory, identity confirmation, candidate review, and byte-verified staging, the parent can run the bootstrap in its own detached launcher. These are node-side commands, not commands executed by this preparation task:

```bash
python3 -B STAGED/bootstrap_megamoe_recovery4.py apply \
  --image-receipt ACTUAL_NEW_NODE_RECEIPT.json \
  --recipe-commit FULL_PUBLISHED_RECIPE_SHA
```

Review both `BOOTSTRAP/evidence/bootstrap-completed.json` and `TASK/environment/setup-completed.json`, all referenced bytes, provider versions, actual GPU UUIDs, 47-shard model metadata/sizes, five link/sentinel/import bindings, six source archives, original success references, and empty cache origin. Keep inherited `pip check` conflicts in the receipts; do not silently repair unrelated packages. The model lock verifies metadata, filenames and sizes, **not full tensor payload SHA**.

After that actual review and the normal source/CLI preflight, launch the real-weight continuation once:

```bash
python3 -B /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery4/environment/helpers/continue_megamoe_recovery4.py launch
```

The normal engine startup/autotuning/graph capture and benchmark-client warmup remain part of the existing serving protocol. The first actual C8 must receive a fresh independent runtime/tuning calibration. Failed C8 attempts never become measurements; preserve failures and do not reuse their run IDs.

## Final evidence boundary

The producer's final gate is fourteen new successful coordinates / 7,640 requests plus the immutable two old coordinates / 2,600 requests. It still marks final independent audit pending. Recovery4-specific status/collector/auditor identity adapters must be reviewed before use: **do not point an old fixed-node adapter at the new node or relax an old full16 gate**. Final reports must disclose the per-run container, physical-host and cache history and per-arm recipe/helper pins. No final curves until all sixteen combined points, source/raw/cache archives and independent checks pass. Earlier failures do not establish cache causality, and a fresh node does not prove their cause.

Local validation lives in `artifacts/megamoe-recovery4-validation/`: focused identity/seal/no-overwrite checks, a synthetic package/source preparation simulation, and a real rehash of the original 28 accepted files. It performs no node, GPU, package-install, or network action. Independent review and actual new-node preparation remain separate gates.
