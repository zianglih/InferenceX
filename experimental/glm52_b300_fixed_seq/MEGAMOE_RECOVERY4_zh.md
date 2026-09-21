# Recovery4：新节点上的真实权重续跑

[English](MEGAMOE_RECOVERY4.md) | **中文**

这是新节点上的一次全新尝试，尚不能证明修复了此前的 NVSHMEM 启动失败。所有旧尝试保持原样。本流程不包含 dummy 模型、独立 kernel 测试、容差调整、恢复旧缓存或访问已删除节点。

实际请求于 2026-09-21 06:26:59 UTC Ready。父任务采集到的主机仍是 **`hu-pdx-126`，与已退休尝试相同的物理主机**；容器是新的，镜像包为初始状态，八张 B300 空闲，新 task/bootstrap 根目录均不存在。因此本次更换的是容器、源码和缓存状态，不是物理硬件。镜像证据来自显式创建请求、Ready 回应及初始软件清单，并非 Kubernetes `imageID` 实测。实际回执位于 `artifacts/megamoe-clean-node-20260921/provisioning/image-receipt.json`。

固定节点为 C2 / `ziangli` / `earth-non-preempt` 的 `infx-glm52-clean-0921`；物理主机必须来自新节点实际回执，不能猜测。镜像仍为 `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85@sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596`。SGLang 固定 `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2`，FlashInfer 固定 `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`。任务根目录、bootstrap 根目录和 run ID 均以 `recovery4` 结尾，完整路径见英文表格及默认计划输出。

真实模型仍为 `/data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4`，revision `53e0691e21895a3863a606dfd12910c69eba94ab`，47 个分片；与另一个 bundled-MTP 项目的 282 分片模型不同。测量配置保持 W4A16 MegaMoE、TP=DP=EP、MTP TRT-LLM/none、显存比例 `.80`、关闭 prefill CUDA graph、长度随机比例 `.8`、每个并发数十倍请求。

保留原 8k1k/TP4 的 C256 和 C4，共 2,600 个成功请求及原始 run、物理节点、镜像、recipe、缓存历史。新尝试只运行剩余 14 点 / 7,640 个请求，从 **8k1k / TP4 / C8** 开始。沿用原 `run_megamoe_recovery3.sh` 的相同字节；其名称是历史名称，当前路径和 run ID 全由调用者显式传入，脚本 SHA 为 `ae96cbb490c9b57dd74016a19552ae0a8bcff6b08df630613313282b75ccaa38`。

## 最小实现变化

- 新 bootstrap 从公开源独立克隆 SG、FI 和调用者固定的 recipe，并直接把 FI editable 安装到最终 campaign 源码树。检查五个生成的资源链接、`_build_meta.py`、固定源码哨兵、已注册依赖 gitlink，以及三个主仓库和三个依赖的全部六份源码归档。包下载/记录等原函数按 SHA 复用，旧文件不改。任何包变更前，两个新 helper 和十二个冻结输入必须与已克隆的发布 recipe 逐字一致；启动时再次核对。
- 仅更换明确锁定的八个 wheel 和 FI editable：五个 CuTe DSL 包 4.7.1、FI 0.7.0、nccl-extensions 0.1.0、cupti-python 13.2.0、CUDA CUPTI 13.2.86。其余软件与原镜像基准核对；GPU UUID 和安装前后运行时则与新节点自身快照核对。调用者镜像回执必须包括固定 node/cluster/namespace/queue/image 以及实际 `hostname`，脚本不会自行推断镜像 digest。
- bootstrap 导入使用独立的新缓存。campaign 缓存从空目录创建，`cache-origin.json` 明确记 `copied:false`；不查看、链接或复制旧缓存 payload/目录。只读取旧归档描述、终态回执及已接受的 28 个原始文件来绑定复用证据。
- 新 continuation 只允许执行 campaign 内已封存的 helper，重新核对同节点运行时、模型、源码和 helper；拒绝重复 run ID。保留十四点矩阵及退出/归档门控，不把旧节点 PID 拿到新节点检查。
- 原 bootstrap/recovery1/2/3、所有历史证据及另一个正在运行的 bundled-MTP 项目均保持原样。helper 字节哈希与 recipe commit 分别记录。

## 发布和执行

独立审查后，由父任务把新 `bootstrap_megamoe_recovery4.py`、`continue_megamoe_recovery4.py`、完整 `recovery4_frozen/` 和两份语言指南复制到 recipe 的 `experimental/glm52_b300_fixed_seq/`，再提交并推送。冻结文件不重命名，旧 helper 和运行时 wrapper 不改。bootstrap 的 `--recipe-commit` 使用实际新发布的完整 SHA，不能填预测值。

默认 `plan` 只在本地输出计划，不启动任何子进程。新节点实际 inventory、身份回执、候选审查及 staging 字节校验完成后，父任务才按英文指南的命令，通过独立 detached launcher 执行 `apply`。本准备任务没有执行这些远程命令。

实际准备结束后，审查 `BOOTSTRAP/evidence/bootstrap-completed.json` 与 `TASK/environment/setup-completed.json` 的全部绑定文件、包版本、GPU UUID、47 分片模型元数据/大小、五个链接与导入路径、六份源码归档、旧成功点引用及空缓存来源。原有 `pip check` 冲突如实保留，不顺手修改无关包。模型锁检查元数据、文件名和大小，**不是完整权重 payload SHA 校验**。

通过实际审查及常规源码/CLI preflight 后，只启动一次已封存的 `TASK/environment/helpers/continue_megamoe_recovery4.py launch`。正常 serving 启动、自调优、graph capture 和客户端 warmup 均沿用既有协议；首个真实 C8 仍须新的独立运行时/调优校准。失败 C8 不能计为结果，失败 run ID 不能重用。

## 最终边界

生产者最终门控为新 14 点 / 7,640 请求，加原样复用的 2 点 / 2,600 请求，仍标记最终独立审计待完成。使用前必须审查 recovery4 专属状态、collector 和 auditor 身份适配；不能把旧固定节点工具指向新节点，也不能放宽原 full16 门控。最终报告明确每个 run 的容器、物理主机、缓存历史及各组 recipe/helper pin；全部合并 16 点、源码/原始数据/缓存归档及独立审查通过后才生成最终曲线。旧失败不能证明缓存因果关系，新节点重跑也不能解释旧失败原因。

本地验证在 `artifacts/megamoe-recovery4-validation/`：包括身份、seal、防覆盖、合成的包/源码准备流程，以及原 28 文件的真实逐字哈希核验。未执行节点、GPU、安装或网络操作。独立审查和新节点实际准备是后续单独门控。
