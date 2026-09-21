# Recovery5：在不同物理节点继续剩余点

[English](RECOVERY5.md) | **中文**

这次新运行使用 C2 的 `infx-glm52-peer-0921`，namespace 为 `infra`，queue 为 `earth`，物理主机为 `hu-pdx-142`。脚本要求调用方提供实际镜像回执，并核对八张 GPU 的 UUID。父任务的实际清单确认这些 UUID 与保留的故障主机 `hu-pdx-126` 完全不同；驱动同为 `590.48.01`，原始镜像包清单与检查点元数据一致。这证明物理主机不同，不能据此断言之前 NVSHMEM 失败的根因。故障节点另行保留用于诊断。

仅增加两个入口，继续使用按字节锁定的 [`recovery4_frozen/`](recovery4_frozen/) 工具、wheel 锁、原成功结果引用，以及不变的十四点 wrapper `run_megamoe_recovery3.sh`。Recovery1–4 的源码、日志、失败和归档均保留。

| 契约 | Recovery5 |
| --- | --- |
| 镜像 | `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85@sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596` |
| SGLang / FlashInfer | `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2` / `ad0a5e5e78e57070ec7c582efe733cb55cd8839f` |
| 依赖 | 同一份八个 SHA 锁定的 wheel：五个 CuTe DSL `4.7.1` 包、`nccl-extensions==0.1.0`、`cupti-python==13.2.0`、`nvidia-cuda-cupti==13.2.86`；FlashInfer 为 editable `0.7.0`，不装 cubin/JIT distribution |
| 运行时 | 保留镜像的 Torch/CUDA/NCCL 和其余无关包，并核对安装前后状态 |
| Serving | 真实 `nvidia/GLM-5.2-NVFP4`，TP=DP=EP、`.80`、TRT-LLM BF16 MTP/none、EAGLE 3/1/4、关闭 prefill graph；工作负载和客户端设置不变 |
| 新运行 | `c2-w4a16-megamoe-autotune-20260921-recovery5`：14 点，要求 7,640 个请求全部成功 |
| 复用 | Recovery1 的 8k1k TP4/C256 和 TP4/C4：2 点、2,600 个成功请求；不复制或改写 case 元数据 |
| 合并目标 | 只有逐点验收及新 C8 校准通过后，才能合并为 16 点、10,240 个成功请求 |

新的 campaign 和 bootstrap 根分别为 `/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery5` 与 `/data/home/ziangli/inferencex-glm52-megamoe-bootstrap-20260921-recovery5`，均必须尚不存在。所有源码按确切 commit 新克隆。FlashInfer 直接安装到最终源码目录，检查五个 data 资源链接、build metadata、十一个 sentinel 文件及三个已注册的依赖 commit，并在准备阶段封存完整六份源码归档。Bootstrap 导入使用独立缓存；第一次服务器启动前，campaign 缓存必须保持为空。不扫描、复制或导入旧缓存。

先发布已经审查的脚本。在脚本所在目录，下列默认命令仅输出计划，不调用任何进程或网络：

```bash
python3 -B bootstrap_megamoe_recovery5.py
python3 -B continue_megamoe_recovery5.py
```

操作者将两份新脚本与不变的 `recovery4_frozen` 目录一起暂存。在确切 peer 节点上显式提供实际镜像回执，以及新发布 recipe 的完整 commit：

```bash
/opt/sglang/bin/python3 -B bootstrap_megamoe_recovery5.py apply \
  --image-receipt /absolute/path/to/peer-image-receipt.json \
  --recipe-commit FULL_PUBLISHED_RECIPE_COMMIT
```

镜像回执必须绑定实际 inventory SHA `132064aa6e3f29eeed84a678fe5b6bf9da21cc9ae2a260a16468f442341c4161`。镜像证据来自显式申请、Ready 回执及原始运行时，不声称已取得 Kubernetes imageID。准备阶段不会启动服务器。新环境封存证据及 CLI 兼容性验收后，才从 campaign 内已封存的 helper 单次启动：

```bash
/opt/sglang/bin/python3 -B \
  /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery5/environment/helpers/continue_megamoe_recovery5.py launch
```

Worker 记录 benchmark 退出状态，再为成功或失败运行封存原始结果/源码及 campaign 缓存。完整矩阵成功必须包含确切剩余十四点。失败 case 保留，不能冒充成功结果；启动与校准必须等待实际证据。Bootstrap、CLI 与默认缓存仍需在退节点时另行保全。本 campaign 不使用 dummy 模型或诊断 kernel。
