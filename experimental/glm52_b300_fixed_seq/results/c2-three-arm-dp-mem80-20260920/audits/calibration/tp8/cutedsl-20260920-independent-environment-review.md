# Independent review of the real CuTe installation receipts

**Environment provenance checks passed with zero mismatches; GPU compatibility and first-case calibration remain pending.** This review used only the eight locally transferred real receipts. It made no remote calls, changed no packages/runtime, and reviewed no completed CuTe case. Machine-readable evidence: `cutedsl-20260920-runtime-only-audit.json`.

The setup seal is timestamped **2026-09-20 13:32:31.828178 UTC**. All eight canonical local files were independently rehashed and matched the decoded transfer payload, its remote-before/remote-after inventories and retained local inventory in `cutedsl-receipt-transfers/20260920T133339Z-izf3k8az/`. The transfer verification's own payload SHA also matches. This validates transferred receipt bytes, not ongoing remote state.

| Check | Result |
|---|---|
| Pre-install restored TRT identity | `packages-before.txt` and `pip-check-before.txt` are byte-identical to the restored TRT copies; `runtime-before.json` equals `runtime-restored.json` as a complete JSON object. |
| Full package freeze | 361 records before, 360 after. Exactly nine approved provider names changed; 353 other records are unchanged. No unapproved addition, removal or version change. |
| FlashInfer | Editable upstream source `f9dd3c10541e087b716772245a9d033499745048`, imported version 0.7.0. `flashinfer-cubin` and `flashinfer-jit-cache` intentionally removed; both runtime-version fields are null and both freeze entries are absent. |
| Compiler/transport | `nvidia-cutlass-dsl` plus libs-base/core/cu12/cu13 are all 4.7.1; `nccl-extensions` added at 0.1.0. |
| Preserved base runtime | Torch 2.13.0+cu130, CUDA 13.0, Triton 3.7.1, Transformers 5.12.1, SGLang kernel 0.4.7. Torch import path, loaded NCCL, NVCC text and all eight B300 GPU identity/driver/capacity lines match before/after. |
| Source identities | FlashInfer `f9dd3c10541e087b716772245a9d033499745048`; SGLang `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; InferenceX `3433a0c1169a6b162edf91c7ea193196c08a6386`. Both source and seal records agree. |
| Source imports/cleanliness | FlashInfer imports from `sources/flashinfer-f9dd3c10/flashinfer/__init__.py`; SGLang from `sources/sglang/python/sglang/__init__.py`; CuTe from installed `site-packages/nvidia_cutlass_dsl`. All three setup-time source-tree cleanliness values are true. These are recorded checks from the previously reviewed helper, not a fresh remote source rehash. |
| Existing runtime auditor | `audit_cutedsl_results.audit_runtime(...)` returns zero issues and explicit dependency-diagnostic review notes. Its case-calibration pending flag was not changed. |

## Dependency diagnostics are retained, not called clean

`pip-check-before.txt` has 13 diagnostics; `pip-check-after.txt` has 12: **nine unchanged, three added, four removed**. The three new lines are exactly:

```text
sglang 0.0.0.dev1+g20518d851 has requirement flashinfer_python[cu13]==0.6.18, but you have flashinfer-python 0.7.0.
sglang 0.0.0.dev1+g20518d851 has requirement nvidia-cutlass-dsl[cu13]==4.6.2, but you have nvidia-cutlass-dsl 4.7.1.
quack-kernels 0.6.4 has requirement nvidia-cutlass-dsl==4.6.2, but you have nvidia-cutlass-dsl 4.7.1.
```

These are `pip-check-after.txt` lines **4, 5 and 8**. The first two reflect unchanged image-installed SGLang distribution metadata; source import identity is separately pinned to 50eeb. They and the quack-kernels constraint are tolerated by the explicit source-provider setup, not evidence of a clean dependency resolver or demonstrated compatibility.

The four removed diagnostics are the old 4.6.2 libs-base/cu13/core/cu12 requirements for protobuf `<7,>=6.30.2` with installed protobuf 7.36.2. The nine retained lines cover absent nixl-cu12/opencv-python, typeguard/imageio/pillow/protobuf constraints and the preexisting Torch/NCCL distribution constraint. Loaded NCCL still reports **2.29.7**, while installed `nvidia-nccl-cu13` remains **2.30.7**; both are unchanged from the restored control and must not be conflated.

The intentionally absent cubin/JIT distributions are confirmed by the actual probe and freeze. **This pip-check output contains no new “missing cubin/JIT” diagnostic line.** Such package absence is distinct from the three new version-constraint diagnostics above; any separate startup warning must be attributed to its own log evidence.

## Scope remaining

No server-info normalization, kernel execution, graph capture, memory capacity, measured requests or performance is established by these receipts. First real C256 review and TP8/C4 calibration remain required. Do not clear `real_case_calibration_pending` or label the complete matrix validated from this installation-only pass.
