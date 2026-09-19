# B300 上的 GLM-5.2 NVFP4 + MTP：本地 8k/1k 与 1k/1k 实验

[English](README.md) | **中文**

本实验仅用于个人 fork，将已归档的 GLM-5 B300 workload 迁移至
`nvidia/GLM-5.2-NVFP4`。它独立于当前 AgentX 配置，不恢复已弃用的官方 benchmark
定义，也不直接发布 dashboard 结果。

- **W4A4 TRT-LLM：**配置已就绪，C2 测量待完成。保留原来的 TP4/DP1/EP1 并发
  sweep，以及 TP8/DP1/EP1、并发 4 的点。
- **W4A16 MegaMoE：**脚本已准备，等待优化栈完成后再运行。目前没有运行或测量。
  调用者必须显式设置 `RUN_MEGAMOE=true` 才能启动。
- **质量：**脚本测吞吐与延迟，不评估模型精度。MTP 使用真实验证，并清除继承的
  simulated acceptance 设置。

## 配置与来源

[`config.env`](config.env) 是可执行的实验配置。先 source，再显式提供本地路径和
唯一的 run ID。脚本不下载权重、不安装依赖，也不升级 FlashInfer。W4A4 使用镜像
已有的 FlashInfer。SGLang checkout 必须位于固定 commit 且没有已追踪的 Python
文件改动；脚本通过 `PYTHONPATH` 和实际 import 路径检查选中该 checkout。

| 字段 | 值 |
| --- | --- |
| 镜像 | `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85` |
| SGLang | [PR #39210](https://github.com/sgl-project/sglang/pull/39210)，`50eeb742961908afa68f4f523a1a19c5de6eb0b3` |
| 模型 | `nvidia/GLM-5.2-NVFP4` |
| 模型 revision | `53e0691e21895a3863a606dfd12910c69eba94ab` |
| 量化 / KV cache | `modelopt_fp4` / `fp8_e4m3` |
| Attention | `dsa`，prefill 和 decode 均使用 TRT-LLM |
| MTP | EAGLE：3 steps、top-k 1、4 draft tokens |
| Draft MoE | W4A4：原生继承设置；MegaMoE：`triton`、A2A `none`、量化 `unquant` |
| 显存 / prefill | `0.85`，chunked prefill 与 max prefill tokens 均为 `32768` |
| Cache / streaming | 禁用 radix cache；stream interval 为 `30` |
| Workload | Random，input 上限 `8192` 或 `1024`、output 上限 `1024`、range ratio `0.8`、chat template |
| 请求数 / warmup | 正式测量 `10 × concurrency`；warmup `2 × concurrency` |
| Sweep | TP4 并发 `4,8,16,32,64,128,256`；TP8 并发 `4`，每个 scenario 都跑一轮 |

两个 workload 称为“8k/1k”和“1k/1k”，但 range ratio 意味着真实长度会在这些上限以下变化。
比较结果时保留原始输入、输出 token 数。共享 InferenceX client 使用无限 request
rate、限制最大并发并忽略 EOS。这是没有 interactive latency SLO 的吞吐 sweep。
每个点仅测量一次，不是多轮运行的中位数。

| 方案 | Target runner / A2A | TP / DP / EP | Prefill CUDA graphs |
| --- | --- | --- | --- |
| W4A4 | `flashinfer_trtllm` / `none` | TP / 1 / 1 | 固定 SGLang HEAD 的默认策略 |
| W4A16 | `flashinfer_megamoe` / `flashinfer_megamoe` | TP / TP / TP，启用 DP attention | 关闭：当前 MegaMoE 的限制 |

两者都在模型接口使用 BF16 activation，设置 BF16 MegaMoE combine storage，关闭
per-token FP4 activation quantization 和 in-kernel FC2 reduction。仅 MegaMoE
开启 `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`。将来的比较同时改变量化精度、
MoE backend、并行拓扑和 prefill graph 策略，不能归因于单独的 MegaMoE kernel。

归档脚本显式写的 `--quantization fp8` 不适用于已序列化的 NVFP4 checkpoint，现改为
`modelopt_fp4`。旧 CLI 名称迁移为 `dsa`、`--dsa-*-backend` 和
`--cuda-graph-max-bs-decode`；decode graph 上限和最大运行请求数仍等于并发。
固定 HEAD 已始终启用 V2，所以不再设置已移除的 `SGLANG_ENABLE_SPEC_V2`。
W4A4 保留原生 draft 设置；MegaMoE 显式选择 Triton draft runner、无 draft A2A
和不量化的 draft，避免继承 target MegaMoE backend，这也是两个配置的区别。

## 运行 W4A4

在单个 B300 节点上使用配置中的镜像。提前准备固定 revision 的完整模型快照、固定
commit 的干净 SGLang checkout，以及 InferenceX client 依赖。源码和输出放在
`/workspace` 以外；脚本会拒绝在 `/workspace` 下创建结果目录。

```bash
# 在配置镜像内的 InferenceX checkout 中运行。
source experimental/glm52_b300_fixed_seq/config.env
export SGLANG_SOURCE_ROOT=/data/home/ziangli/inferencex-glm52-b300/sources/sglang
export MODEL_PATH=/data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4
export OUTPUT_ROOT=/data/home/ziangli/inferencex-glm52-b300/results
export RUN_ID=c2-w4a4-first
bash experimental/glm52_b300_fixed_seq/w4a4_trtllm_mtp.sh
```

若只运行一个点或补跑部分点，在 source 配置**之后**设置 `SWEEP_CASES`，例如
`export SWEEP_CASES='4:4'`。默认运行两个 scenario；若只跑一个，设置
`export SCENARIOS='8k1k:8192:1024'` 或 `export SCENARIOS='1k1k:1024:1024'`。通过 `GPU_IDS` 指定可用物理 GPU，每个点使用前 TP 个。
重复测量必须使用新的 `RUN_ID`；脚本不会覆盖已有结果目录。每个点启动独立 server，
收集结果后清理自己创建的 process group。server、client、清理错误或正式测量请求
缺失都会使 sweep 失败。

待运行的 MegaMoE 入口是 [`w4a16_megamoe_mtp.sh`](w4a16_megamoe_mtp.sh)。启用前
先验证最终优化版 SGLang/FlashInfer revision 和 API 兼容性，更新并记录 pin，再使用
独立 run ID。当前配置是可复现的起点，不代表 W4A4 镜像已包含最终优化 MegaMoE 栈。

## 结果与汇总

每个点在 `OUTPUT_ROOT/RUN_ID/<scenario>/<arm>/tp<TP>_conc<CONC>/` 中写入：

- 原始 `result.json`、client/server 日志，以及 `status.json` 中的请求计数。
- 包含模型、镜像、源码、版本、拓扑和最终状态的 `metadata.json`。
- 可通过 shell 重放的 server/benchmark 命令，以及运行前后的 `/get_server_info`。
- `packages.json`、`nvidia-smi.txt` 和 `gpu_metrics.csv`。共享 GPU monitor 采集
  整个节点；metadata 中的 `CUDA_VISIBLE_DEVICES` 标识实际使用的 GPU。整机遥测
  不能直接当作某个方案的能耗。

汇总仅使用脚本及请求计数均完整成功的点：

```bash
python3 experimental/glm52_b300_fixed_seq/summarize.py \
    --results "$OUTPUT_ROOT/$RUN_ID" --output "$OUTPUT_ROOT/$RUN_ID/summary"
```

图表需要 `matplotlib`；添加 `--no-plots` 可仅输出 JSON 和 Markdown。保留失败点的
原始资料，不把待运行的 MegaMoE 点展示成实测数据。比较 TP4 与 TP8 时，按结果记录
的实际 GPU 数归一化吞吐。
