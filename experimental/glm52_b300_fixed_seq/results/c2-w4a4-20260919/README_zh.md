# GLM-5.2 B300 W4A4 + MTP 测量结果 — 2026-09-19

[English](README.md) | **中文**

**全部 16 个计划点已完成，10,240/10,240 个正式测量请求成功。** 完整矩阵通过发布
检查，运行时审计未发现配置不一致。W4A16 MegaMoE 和精度评测均未运行。

- [完整指标与图表](summary/summary.md)
- [每个点未经删节的客户端汇总输出](raw_client_summaries.md)
- [运行时观察](runtime-audit.md)和[机器可读审计](runtime-audit.json)
- [全部原始文件的 SHA256 manifest](manifest.json)
- [实验配置与复现步骤](../../README_zh.md)

## 环境

| 字段 | 记录值 |
| --- | --- |
| 硬件 | C2 单节点 8× NVIDIA B300 SXM6 AC，每 GPU 275040 MiB；每个点实际使用 TP4 或 TP8 张 GPU |
| 镜像 | `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85` |
| 镜像 index digest | `sha256:d46a59f4b98658f728a1e006c003ad5ee0628e999fd8b2bef71ac1bb61b814da` |
| AMD64 镜像 digest | `sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596` |
| 实际测量的 InferenceX commit | `0c684dd7fe30ebb165453c20989b2fcb24633b6c` |
| 实际 import 的 SGLang | [PR #39210](https://github.com/sgl-project/sglang/pull/39210)，`50eeb742961908afa68f4f523a1a19c5de6eb0b3`，通过 `PYTHONPATH` 选择 |
| 模型 | `nvidia/GLM-5.2-NVFP4`，revision `53e0691e21895a3863a606dfd12910c69eba94ab` |
| FlashInfer Python / cubin / JIT cache | `0.6.18 / 0.6.18 / 0.6.18+cu130`，使用镜像自带版本，没有升级 |
| PyTorch / CUDA runtime / Triton | `2.13.0+cu130 / 13.0 / 3.7.1` |
| Transformers / SGLang kernel / CuTe DSL | `5.12.1 / 0.4.7 / 4.6.2` |
| Driver | `590.48.01`；`nvidia-smi` 的 CUDA compatibility 13.1 与 PyTorch runtime 版本分开记录 |

镜像内 SGLang distribution version 为 `0.0.0.dev1+g20518d851`，不同于实际 import
的 PR 源码。[环境记录](environment/)和各点 package/server-info 文件保留了这两类
信息。运行后审计不代表重新校验过每个模型权重或已安装二进制的 checksum。

## 方法

- **矩阵：**分别运行 8k1k（`8192/1024`）和 1k1k（`1024/1024`）。每组包含
  TP4/DP1/EP1 的并发 4、8、16、32、64、128、256，以及 TP8/DP1/EP1 的并发 4。
  每个点启动独立 server，结束后清理所属进程。
- **Server：**`modelopt_fp4`、`flashinfer_trtllm`、A2A `none`、BF16 模型接口、
  FP8 E4M3 KV、TRT-LLM DSA prefill/decode、显存比例 0.85、prefill budget 32768、
  禁用 radix cache、stream interval 30。最大运行请求数和 decode graph batch 上限
  均等于并发。Checkpoint 排除规则仍生效；W4A4 不代表每个模块都被量化。
- **MTP：**真实 EAGLE 验证，steps/top-k/draft tokens 为 `3/1/4`，保留原生 draft
  继承设置，不模拟 acceptance。解析后的 draft runner 与量化标签分别为
  `flashinfer_trtllm`、`modelopt_fp4`，但 checkpoint 排除了 `model.layers.78*`，
  因此不能由继承标签推断 MTP 权重是 FP4。
- **Client：**原 InferenceX random client，以 `vllm` 协议适配器访问 SGLang 的
  `/v1/completions`；seed 0、chat template、range ratio 0.8、无限到达率、并发上限
  和 ignore EOS。标称长度不是每个请求的精确长度，原始 token 数已保留。
- **计时：**一次初始单请求检查，随后 2C 次 warmup，再正式测量 10C 个请求。检查
  和 warmup 不计入测量。每个点只跑一轮，不是多轮中位数，也没有置信区间或 latency
  SLO 验证。客户端丢弃 warmup 返回结果，所以零失败仅适用于正式测量请求。
- **指标：**output throughput 只计生成 token，total throughput 包含输入和输出，
  均除以测量时长。每 GPU 指标除以实际 TP GPU 数。延迟单位为毫秒；请求延迟分位数
  与多轮 benchmark 统计不是一回事。

## 运行时观察

默认配置解析为 **full decode graph，以及最大 token batch 2048 的 breakable
prefill graph**。是否使用取决于具体 batch：8k1k 的正式 prefill 日志大多为
`False`，C256 有两个 `True`（1664、1961 个 new tokens）。1k1k 大多为 `True`，
也存在 `False`；正式 decode 日志样本为 `True`。这些是日志中的 batch，不是完整
graph 或 kernel 调用计数。

| 点 | Allocator warning：测量前 / 测量中 | Late-load / low-free-memory advisory 总数 | 正式请求 |
| --- | --- | --- | --- |
| 8k1k TP4 C128 | 3 / 1 | 24 | 1280/1280 |
| 8k1k TP4 C256 | 9 / 12 | 666 | 2560/2560 |
| 1k1k TP4 C256 | 4 / 12 | 476 | 2560/2560 |

Advisory 总数覆盖整个点，不限于正式测量。这些 warning 没有终止运行。后续继续执行与 allocator 恢复一致，但无法由日志确定
具体重试分支或性能影响。两种 workload 的 TP4 单轮 output throughput 均在 C128
到 C256 时下降：8k1k 为 `2362.353664 → 2168.793740` tokens/s，1k1k 为
`5342.922157 → 4317.191813` tokens/s。结果不能证明下降原因；所有点和 warning
证据均保留。

退出阶段同样有诊断日志：8k1k TP4 C64 在测量结束后的 SIGTERM 清理阶段出现三条
`ERROR:` severity 行。1k1k TP8 C4 在 09:46:56.701186 UTC 结束测量，09:46:57 收到
SIGTERM，09:46:58 detokenizer 以 `-15` 退出，随后 watchdog 触发 SIGQUIT；09:47:03
已无 scheduler，case 最终记录退出码 0。这是测量后退出阶段的 watchdog escalation：
watchdog 将包括 SIGTERM 在内的子进程非零退出视为错误，并发送 SIGQUIT。正式请求
计数和 case 退出状态通过，不代表完整 server 日志无错误。自动 `ERROR:` 前缀计数
漏掉了这条没有此前缀的 watchdog 诊断，因此另以直接日志检查补充[运行时审计](runtime-audit.md)。
Severity 行数不等于独立异常数量。

记录的 acceptance length 是包括 warmup 和报告窗口的 server 全生命周期累计值，
不是仅正式测量期间的值。没有 MTP-off 对照或精度评测，不能声称独立 MTP 加速比或
数值/质量等价。未来 MegaMoE 配置会同时改变精度、backend、TP=DP=EP 拓扑、draft
和 prefill graph 策略。

## 证据保存

此目录包含 160 个保持原样的客户端与 provenance 文件。[Manifest](manifest.json)
为**全部 208 个原始逐点文件**记录 SHA256、大小、相对路径与是否包含在发布目录中。
完整 server 日志和 GPU 遥测保留在持久目录及本地原始归档。整机遥测不能直接当作
某方案的能耗。

持久归档目录：`/data/home/ziangli/inferencex-glm52-b300/archives/`。

| 归档 | SHA256 |
| --- | --- |
| `c2-w4a4-20260919-raw.tar.gz` | `1fde3e3fb77e40433b7c9589d69a8334ccdd6b7027991a1f1d7bfb89812907c5` |
| `c2-w4a4-20260919-flashinfer-0.6.18-autotune.tar.gz` | `113fd410166df5f2610ffd1ef8fbb6879d539ed03f2000fccc5bebd99068faf6` |

Checkpoint、源码 checkout 和运行结果继续保存在持久实验目录中，供后续 MegaMoE
使用。这些结果属于个人 fork 实验，不发布到官方 InferenceX dashboard。
