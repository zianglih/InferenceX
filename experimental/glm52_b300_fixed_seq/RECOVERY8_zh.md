# MegaMoE recovery8：SGLang workaround 与原版 NVSHMEM

[English](./RECOVERY8.md) | **中文**

本 fork 延续实验只跑剩余14个 MegaMoE 测点，使用 SGLang `26c41009549f9ad407e107b33d5144f6e085418b` 和未修改的 NVSHMEM 3.4.5 wheel。原 recovery1 的 8k1k TP4 C256/C4 两点保持原始文件不变：2,600 个测量请求、SGLang `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2` 和原 proxy 默认值。新14点共7,640个测量请求。脚本本身不是启动成功或新增性能的证据。

## Workaround

[SGLang integration](https://github.com/sgl-project/sglang/pull/39210) 在首次初始化之前设置三个默认值，并保留用户显式覆盖：

```text
NVSHMEM_REMOTE_TRANSPORT=none
NVSHMEM_IB_ENABLE_IBGDA=0
NVSHMEM_DISABLE_LOCAL_ONLY_PROXY=1
```

作用范围限定为单节点 NVFP4 W4A16 MegaMoE，且不使用 speculation，或 draft A2A backend 明确为 `none`。直接 peer 通路保留，proxy 初始化被跳过；要求直接 peer 连通。该配置下 NVSHMEM device-side wait timeout 和 device global-exit 功能不可用。启动器不注入这三个值，只提供 `NVSHMEM_DEBUG=INFO`，并检查所有 serving rank 确实由新 SGLang 建立默认值。

[NVSHMEM_STARTUP.md](./NVSHMEM_STARTUP.md) 总结未初始化 proxy exit-request/code 的诊断和匹配 native 构建对照。本轮使用原版 wheel，没有实验性 native 补丁、preload、自定义 UID plugin 或 host-search overlay。原 native 补丁的启动验证不能替代这个 workaround 的实际验证；campaign 激活前必须先验收新 PR head 加原版 wheel 的真实模型启动。

## 固定配置

- FlashInfer `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`；镜像 `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85@sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596`。
- 8张 B300，五个 CuTe 4.7.1 provider，nccl-extensions 0.1.0，cupti-python 13.2.0 / CUPTI 13.2.86。保留镜像 Torch/CUDA/实际 loaded NCCL 和无关软件包；bootstrap probe 的 loaded NCCL 为2.29.7，安装包及 SGLang 启动日志为2.30.7；这些是分别记录的实际观察，不宣称所有进程加载同一 NCCL image。
- TP=DP=EP、DP attention、memory .80、FP8 E4M3 KV、关闭 prefill graph、全局 chunk32768、原生 BF16 TRT-LLM/none MTP3/1/4。Mega 自行准备 profiles，不强制 EXTEND=1。
- 真实47分片 `nvidia/GLM-5.2-NVFP4`，revision `53e0691e21895a3863a606dfd12910c69eba94ab`；核验 config/index/revision/分片尺寸，不宣称重新计算464GB权重内容哈希。
- 原随机长度 ratio .8、chat template、无限到达率、短检查、2C warmup、10C测量保持不变。8192/1024、1024/1024为名义长度边界，逐请求有序 input/output 长度数组决定实际配对。
- 剩余顺序：8k1k TP4 C8/16/32/64/128、TP8 C4；之后1k1k TP4 C256/4/8/16/32/64/128、TP8 C4。新 warmup1,528请求、测量7,640请求；加入原两点后16点/10,240测量请求。

## 分开准备与启动

`recovery8/cli.py` 不执行 HAI 操作；随附 activation template 未绑定，拒绝直接运行。用实际新节点/GPU身份、bootstrap/provider/runtime记录和当前进程 birth 绑定独立 activation；历史记录不能证明当前进程状态。绑定精确 published recipe commit/bundle、模型路径、原28文件目录、实际 C8 的独立 SG26c checkout、source/native完整内容验收和执行审查。

```bash
/opt/sglang/bin/python3 -B "$STAGE/recovery8/cli.py" prepare \
  --lock "$STAGE/activation.json" --lock-sha "$ACTIVATION_SHA"
# 实际准备结果独立验收之后，单独且只启动一次。
/opt/sglang/bin/python3 -B "$STAGE/recovery8/cli.py" launch \
  --lock /data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery8/environment/activation.json \
  --lock-sha "$ACTIVATION_SHA"
```

准备使用独占新目录，通过 `--local --no-hardlinks` 克隆 SG/FI/依赖/recipe；核验 SG26c 的 parent 和唯一20行生产代码增量。不会安装包、复制旧 cache 或修改旧目录。实际 import、完整 freeze、模型元数据、六份源码 archive、stock native 和8卡空闲检查均留存。失败或中断的启动身份保留，不覆盖重试。

## 证据与比较

warmup/client 之前，所有 TP4/TP8 rank 必须有 natural-init 进入/返回时的实际默认值、SG/FI来源、stock host/UID映射；`Proxy is disabled.` 和 native 功能限制文本必须对应真实 PID/device/hostname，并绑定启动日志前缀。observer 不增加 native init/getter 调用。测量后、清理前再次记录映射和进程 birth。

原 raw14 不变；`native-runtime/<run>/<case>` 保存额外 native/default/进程证据；原 artifact finalization 后才生成 `joins/<case>.json`。join 不替代独立审计；首个真实测点仍需 raw/settings/native 校准。

每个已验收新点先比较原 Mega，再比较历史 Split/TRT，要求有序 token 长度完全一致。报告带符号的吞吐/GPU、interactivity、TTFT/TPOT/E2EL 和已保存 p90/p99；不重建未保存的 p95 或逐请求 latency。各 DP 累积 MTP 平均 acceptance length 包含 warmup，不是测量区间的全局接受率。

最终48点包含16个更新 Mega 点和32个原 controls。Pareto 横轴 `1000/median_tpot_ms` tokens/s/user，纵轴整个区间 output tokens/s/GPU，包含 prefill。保留每点来源，明确原两点 SG6d8 与新14点 SG26c/defaults 的区别；不据此宣称独立 kernel/autotune/NVSHMEM 因果或统计显著性。完整 raw/source/native/cache 校验、独立图表检查、发布读回和数据保留检查完成后才清理资源。

## 源码准备的继续执行

Recovery7 在 benchmark 开始前停止：新的浅克隆缺少精确源码差异校验所需的父对象。Recovery8 保留原失败目录，从已验证的本地 seed 显式获取确切父对象，再执行原有的 parent、diff 和 blob 检查。仅使用新的 run/root 身份；模型、源码 pin、native 配置、客户端与剩余十四个坐标不变，不重跑已完成测点。
