# 一次安装，两种精度共用 FlashInfer

[English](INSTALL.md) | **中文**

在[串行实验](README_zh.md)前只执行一次安装，W4A4 与 W4A16 共用同一安装。这些是已审查的安装命令，不代表实际安装或 GPU 验证已经完成。

- 镜像：`lmsysorg/sglang:nightly-dev-cu13-20260924-ffac53d7`；amd64 manifest 为 `sha256:21d494298cea9592b92903f368f8b34c96e908b2eb64ca84fe195c6d1f0e1cd3`。
- SGLang：`16c1b8638b462ca1b896e2b76d5c002caf06988b`；FlashInfer：`19e8aebb541684df09e12cc79610338aa429a2cf`。
- 保留镜像 Torch `2.13.0+cu130`、实际工具链 `nvcc 13.0.88`、CuTe DSL `4.6.2`、原生 CUPTI `13.0.85`。镜像 NCCL distribution 为 `2.30.7`，而 `torch.cuda.nccl.version()` 返回 `2.29.7`；两项观测均保留、记录。
- 镜像已有其它基础依赖。仅按精确 wheel SHA 用 `--no-deps` 增加 `nccl-extensions==0.1.0`。不运行 SGLang 依赖解析安装，不升级 CUDA/NCCL，不安装 FlashInfer 可选 CUDA-extra/AOT provider 包。

在已确认空闲的 B300 节点使用全新目录。保留每条命令的 stdout/stderr/退出记录，以及安装前后完整 freeze、源码状态、模型元数据。失败或部分安装必须先检查，不能静默重跑。

```bash
set -eo pipefail
BOOT_PY=/opt/sglang/bin/python3
BOOT_ROOT=/data/experiments/glm52-1k2k-install
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

必须确认两个 wheel 版本均为 `0.7.0+g19e8aebb5416`，main 的 `_build_meta.__git_commit__` 与 cubin 的 `_build_meta.__git_version__` 均等于完整 FI commit，且无关 freeze 条目未变。记录实际导入路径：运行时使用已安装 FI wheel，`PYTHONPATH` 仅包含 SGLang 的 `python/` 和 InferenceX。要求 `flashinfer_jit_cache` 不存在、`flashinfer.jit.env.FLASHINFER_AOT_PROVIDERS` 为空。cubin 包下载源码校验和锁定的产物；这不是全算子的本地 AOT 编译。允许并记录生成的 untracked build metadata；不允许 tracked 源码变化。

这些原生 Mega 路径不需要安装 `cupti-python`。W4A4 AUTO 使用同步后的主机时间，W4A16 AUTO 使用 CUDA events；均保留上游计时实现。

实验全部24点共用一个编译缓存树，包括 `FLASHINFER_WORKSPACE_BASE` 和 `CUTE_DSL_CACHE_DIR`，并使用四个精度/TP 独立 tactic 目录。CuTe4.6.2 支持该缓存目录变量，默认启用文件缓存；`CUTE_DSL_ENABLE_CACHE` 不是它的开关。不得设置 `CUTE_DSL_NO_CACHE=1` 或 `CUTE_DSL_DISABLE_FILE_CACHING=1`。共享目录支持复用，但不证明每次后续 compile 调用都完全没有编译工作。各组之间不重新安装包、不清缓存。运行配置与证据边界见 [README](README_zh.md)。
