# Recovery3: restore the FlashInfer source-resource layout

**English** | [中文](RECOVERY3_zh.md)

Recovery2 stopped before measurement because the fresh FlashInfer checkout lacked
`flashinfer/data/csrc/.../fp4Quantize.cpp`. The canonical file was present at the
pinned commit; the ignored resource links normally created by an editable install
were absent. Recovery3 uses a new root and run ID, retaining both earlier failures
and the two accepted recovery1 results.

- **Unchanged:** SGLang `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2`, FlashInfer
  `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`, image, installed package inventory,
  model, `.80`, TP=DP=EP, native BF16 TRT-LLM MTP, and all client settings.
- **Preparation fix:** register the exact CCCL/CUTLASS/spdlog gitlinks and clone
  independent Git objects from recovery1. Create exactly five links under the new
  `flashinfer/data`: `cutlass`, `spdlog`, `cccl`, `csrc`, `include`; all targets
  belong to the new checkout. Generate pinned `_build_meta.py` explicitly, without
  importing `build_backend` or invoking pip. Validate eleven source/header
  sentinels against Git, including all seven FP4 quantization compilation units.
  Verify both imported metadata and JIT csrc paths belong to the new checkout.
- **Evidence:** the initial setup seal includes three main Git archives plus all
  three dependency Git archives, layout/sentinel hashes, generated metadata,
  source-import receipts, helpers, runtime/freeze before and after, and recovery2
  terminal receipts. Resource layout and source cleanliness are rechecked at
  launch and worker entry. No later dependency appendix is required.
- **Caches:** copy only the SHA-sealed recovery1 cache inventory into the new
  cache root, preserving old bytes and remapping its internal link. Recovery2
  supplies no successful results or caches to this continuation.
- **Remaining matrix:** 8k1k TP4 C8/16/32/64/128 and TP8 C4; 1k1k TP4
  C256/4/8/16/32/64/128 and TP8 C4. Fourteen new cases require 7,640 successes;
  immutable references to recovery1 C256/C4 add 2,600, giving 16 / 10,240 only
  after independent combined acceptance. No old result metadata is rewritten.

The new helper privately reuses the SHA-frozen recovery2 cache copy, reference
checks, matrix gate, and archiving implementation. Recovery2 and original
full-sweep success gates remain unchanged. Any nonzero benchmark exit is archived
as a failure with `complete_matrix: null`; it is never promoted to success.

After this recipe is reviewed, committed and pushed, the caller must provide its
full published commit. Use the already reviewed node `hu-pdx-126`; preparation
requires eight idle B300s, both previous workers terminal, unchanged installed
packages/runtime, and a nonexistent destination. Preparation never launches a
benchmark. Failed preparation is retained and cannot be overwritten.

```bash
# Run through the approved node dispatch, using the newly published helper bytes.
python3 -B continue_megamoe_recovery3.py prepare --recipe-commit FULL_PUBLISHED_SHA

# Review environment/setup-completed.json before the separate launch.
python3 -B /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery3/sources/inferencex/experimental/glm52_b300_fixed_seq/continue_megamoe_recovery3.py launch
python3 -B /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery3/sources/inferencex/experimental/glm52_b300_fixed_seq/continue_megamoe_recovery3.py status
```

The detached worker waits for the benchmark, writes a benchmark exit receipt,
seals raw/environment/source and cache archives, then writes the worker exit
receipt. Launch is exclusive; there is no automatic retry. The run ID is
`c2-w4a16-megamoe-autotune-20260921-recovery3`. Collection/calibration must use a
separately reviewed recovery3 consumer; recovery2 consumers do not establish
recovery3 acceptance. Local fixture checks are preparation validation, not GPU or
performance evidence.
