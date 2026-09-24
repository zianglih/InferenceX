# One-time shared FlashInfer installation

Use this setup once for both W4A4 and W4A16, before the [serial campaign](README.md).
These are the reviewed installation commands, not a claim that installation or GPU validation has completed.
Changing the workload to 1k/8k does not require a new environment or another installation.
Reuse the existing installation once its terminal receipts are accepted; the fresh-path
example below is only for a node that has not been set up.

- Image: `lmsysorg/sglang:nightly-dev-cu13-20260924-ffac53d7`; amd64 manifest `sha256:21d494298cea9592b92903f368f8b34c96e908b2eb64ca84fe195c6d1f0e1cd3`.
- SGLang: `16c1b8638b462ca1b896e2b76d5c002caf06988b`; FlashInfer: `19e8aebb541684df09e12cc79610338aa429a2cf`.
- Preserve the image's Torch `2.13.0+cu130`, actual toolkit `nvcc 13.0.88`, CuTe DSL `4.6.2`, and native CUPTI `13.0.85`. The image reports NCCL distribution `2.30.7` while `torch.cuda.nccl.version()` reports `2.29.7`; preserve and record both observations.
- The image already has the other base dependencies. Add only `nccl-extensions==0.1.0` with its exact wheel SHA and `--no-deps`. Do not run a SGLang dependency resolver, upgrade CUDA/NCCL, or install FlashInfer's optional CUDA-extra/AOT provider packages.

Run on a qualified idle B300 node in a fresh directory. Keep the full command/stdout/stderr/exit record, package freeze, source status, and model metadata before and after setup. A failed or partial installation must be inspected; do not silently rerun it.

```bash
set -eo pipefail
BOOT_PY=/opt/sglang/bin/python3
BOOT_ROOT=/data/experiments/glm52-1k8k-install
# Supply a fresh owned path; this example deliberately refuses an existing root.
test ! -e "$BOOT_ROOT"
mkdir "$BOOT_ROOT"
mkdir "$BOOT_ROOT/sources" "$BOOT_ROOT/wheels"
"$BOOT_PY" -m pip freeze --all > "$BOOT_ROOT/freeze.before.txt"

SG=16c1b8638b462ca1b896e2b76d5c002caf06988b
FI=19e8aebb541684df09e12cc79610338aa429a2cf
git clone --depth=1 --no-checkout --no-hardlinks https://github.com/sgl-project/sglang.git "$BOOT_ROOT/sources/sglang"
git -C "$BOOT_ROOT/sources/sglang" fetch --depth=1 origin "$SG"
git -C "$BOOT_ROOT/sources/sglang" checkout --detach "$SG"
git clone --depth=1 --no-checkout --no-hardlinks https://github.com/flashinfer-ai/flashinfer.git "$BOOT_ROOT/sources/flashinfer"
git -C "$BOOT_ROOT/sources/flashinfer" fetch --depth=1 origin "$FI"
git -C "$BOOT_ROOT/sources/flashinfer" checkout --detach "$FI"
git -C "$BOOT_ROOT/sources/flashinfer" submodule update --init --depth=1 -- 3rdparty/cccl 3rdparty/cutlass 3rdparty/spdlog
# Parent gitlinks: cccl16bd510c, cutlassb46b16d, spdlogc3aed4b; no NIXL native build.
git -C "$BOOT_ROOT/sources/flashinfer" submodule status

NCCL_EXT=nccl_extensions-0.1.0-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl
curl --fail --location 'https://files.pythonhosted.org/packages/f3/3c/b043c1f8ca2766d48e30e9cc5a0d65d51aef77e3a8d18dbbaa95fd5386e2/nccl_extensions-0.1.0-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl' -o "$BOOT_ROOT/wheels/$NCCL_EXT"
echo "54d46bee108f0bc18cdc35dbe17bba6452d6a38a270fa5e8ccde03267460fa87  $BOOT_ROOT/wheels/$NCCL_EXT" | sha256sum --check
"$BOOT_PY" -m pip install --no-index --no-deps "$BOOT_ROOT/wheels/$NCCL_EXT"

FI_BUILD=(env -u FLASHINFER_VERSION BUILD_NVEP=0 BUILD_NIXL_EP=0 BUILD_NCCL_EP=0 FLASHINFER_BUILD_NO_PIP=1 CUDA_MAJOR=13 FLASHINFER_CUDA_ARCH_LIST=10.3a FLASHINFER_LOCAL_VERSION=g19e8aebb5416 FLASHINFER_DEV_RELEASE_SUFFIX=)
"${FI_BUILD[@]}" "$BOOT_PY" -m pip wheel --no-deps --no-build-isolation --wheel-dir "$BOOT_ROOT/wheels" "$BOOT_ROOT/sources/flashinfer"
# Inspect the main wheel's METADATA and flashinfer/_build_meta.py before removing the image providers.
MAIN_WHEELS=("$BOOT_ROOT"/wheels/flashinfer_python-0.7.0+g19e8aebb5416-*.whl)
test "${#MAIN_WHEELS[@]}" -eq 1
unzip -p "${MAIN_WHEELS[0]}" flashinfer/_build_meta.py
"$BOOT_PY" -m pip uninstall -y flashinfer-python flashinfer-cubin flashinfer-jit-cache
# The cubin backend imports source FlashInfer: remove the old optional shim first.
"${FI_BUILD[@]}" "$BOOT_PY" -m pip wheel --no-deps --no-build-isolation --wheel-dir "$BOOT_ROOT/wheels" "$BOOT_ROOT/sources/flashinfer/flashinfer-cubin"
"$BOOT_PY" -m pip install --no-index --no-deps "$BOOT_ROOT"/wheels/flashinfer_python-0.7.0+g19e8aebb5416-*.whl "$BOOT_ROOT"/wheels/flashinfer_cubin-0.7.0+g19e8aebb5416-*.whl
sha256sum "$BOOT_ROOT"/wheels/*.whl > "$BOOT_ROOT/wheel-sha256.txt"
git -C "$BOOT_ROOT/sources/flashinfer" diff HEAD --exit-code
git -C "$BOOT_ROOT/sources/sglang" diff HEAD --exit-code
"$BOOT_PY" -m pip freeze --all > "$BOOT_ROOT/freeze.after.txt"
```

Require the two wheel versions to be `0.7.0+g19e8aebb5416`, the main `_build_meta.__git_commit__` and cubin `_build_meta.__git_version__` to equal the full FI commit, and unrelated freeze entries to remain unchanged. Capture imported paths: use the installed FI wheels, with only SGLang's `python/` and InferenceX on runtime `PYTHONPATH`. Require `flashinfer_jit_cache` absent and `flashinfer.jit.env.FLASHINFER_AOT_PROVIDERS` empty. The cubin package contains downloaded, source-checksummed artifacts; this is not an all-operator local AOT build. Generated untracked build metadata is expected; tracked changes are not.

Do not install `cupti-python` for these native Mega paths. W4A4 AUTO uses synchronized host wall time; W4A16 AUTO uses CUDA events. They retain their upstream timer implementations.

The campaign sets one shared compilation cache tree across all 24 points, including `FLASHINFER_WORKSPACE_BASE` and `CUTE_DSL_CACHE_DIR`, and four precision/TP-specific tactic directories. CuTe4.6.2 supports the latter directory variable and enables file caching by default; `CUTE_DSL_ENABLE_CACHE` is not its switch. Do not set `CUTE_DSL_NO_CACHE=1` or `CUTE_DSL_DISABLE_FILE_CACHING=1`. Shared paths enable reuse but do not prove every subsequent compile call is free of compilation work. Do not reinstall packages or clear caches between arms. See [README](README.md) for runtime configuration and evidence limits.
