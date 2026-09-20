# B300 上的 GLM-5.2 NVFP4 + MTP：本地 8k/1k 与 1k/1k 实验

[English](README.md) | **中文**

本实验仅用于个人 fork，将已归档的 GLM-5 B300 workload 迁移至
`nvidia/GLM-5.2-NVFP4`。它独立于当前 AgentX 配置，不恢复已弃用的官方 benchmark
定义，也不直接发布 dashboard 结果。

- **历史 W4A4 TRT-LLM 参考：**C2 测量已于 2026-09-19 完成，全部 16 个点和 10,240/10,240 个
  正式请求通过。参见[结果、图表与运行时限制](results/c2-w4a4-20260919/README_zh.md)。
  保留原来的 TP4/DP1/EP1 并发 sweep，以及 TP8/DP1/EP1、并发 4 的点；原始结果不变，
  与新一轮对照分开保存。
- **新增 W4A4 TRT-LLM 对照：**通过 [`config-trtllm-aligned.env`](config-trtllm-aligned.env)
  将 DP attention、TP=DP=EP、prefill graph、draft 设置与显存预留与 MegaMoE 对齐。
  保留 FlashInfer 0.6.18 与 CuTe DSL 4.6.2；复用现有 0.80 运行，不重跑。
- **优化版 W4A16 MegaMoE：**已准备固定 FlashInfer PR #5019 源码与原生 TRT-LLM
  BF16 MTP draft。首次显存比例 0.85 的运行完成六个点后，在 C256 warmup 阶段失败；现有完整矩阵运行使用 0.80，新增第三组时复用该运行，不重跑已有点。先 source 基础
  配置，再 source [`config-megamoe.env`](config-megamoe.env) 启用此方案。
- **W4A16 CuTe DSL split MoE：**通过 [`config-cutedsl.env`](config-cutedsl.env) 和
  [`w4a16_cutedsl_mtp.sh`](w4a16_cutedsl_mtp.sh) 准备独立第三组，固定 FlashInfer
  PR #5319，设置 `SGLANG_FLASHINFER_MOE_FUSED_FINALIZE=0` 与
  `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`；全部 16 个点已完成。
- **质量：**脚本测吞吐与延迟，不评估模型精度。MTP 使用真实验证，并清除继承的
  simulated acceptance 设置。

## 配置与来源

[`config.env`](config.env) 是可执行的实验配置。先 source，再显式提供本地路径和
唯一的 run ID。脚本不下载权重、不安装依赖，也不升级 FlashInfer。基础配置选择
`PARALLEL_TOPOLOGY=tp`、`PREFILL_CUDA_GRAPH_POLICY=latest-default`，保留历史拓扑。
TRT-LLM、MegaMoE 与 CuTe DSL 的 overlay 均选择 `dp-ep`、`disabled`。
历史参考和新增 TRT-LLM 对照使用镜像已有的 FlashInfer；MegaMoE 与 CuTe DSL 分别固定
各自的 FlashInfer 源码，并要求提前准备对应依赖。源码 checkout 必须匹配 pin；通过
`PYTHONPATH` 和实际 import 路径检查选中它们。已测 baseline 的源码、包和 cache
归档与优化版运行分开保存。

| 字段 | 值 |
| --- | --- |
| 镜像 | `lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85` |
| SGLang | [PR #39210](https://github.com/sgl-project/sglang/pull/39210)，`50eeb742961908afa68f4f523a1a19c5de6eb0b3` |
| MegaMoE FlashInfer | [PR #5019](https://github.com/flashinfer-ai/flashinfer/pull/5019)，`ad0a5e5e78e57070ec7c582efe733cb55cd8839f`；B300 编译目标 `10.3a` |
| CuTe DSL FlashInfer | [PR #5319](https://github.com/flashinfer-ai/flashinfer/pull/5319)，`f9dd3c10541e087b716772245a9d033499745048`；B300 编译目标 `10.3a` |
| 模型 | `nvidia/GLM-5.2-NVFP4` |
| 模型 revision | `53e0691e21895a3863a606dfd12910c69eba94ab` |
| 量化 / KV cache | `modelopt_fp4` / `fp8_e4m3` |
| Attention | `dsa`，prefill 和 decode 均使用 TRT-LLM |
| MTP | EAGLE：3 steps、top-k 1、4 draft tokens |
| Draft MoE | 所有对齐方案：显式 `flashinfer_trtllm`、A2A `none`；历史参考：原生继承设置；均不显式覆盖 draft 量化 |
| 显存 / prefill | 历史方案 `0.85`；所有对齐方案均为 `0.80`；CLI chunked prefill 与 max prefill tokens 均为 `32768`，DP 归一化见下文 |
| Cache / streaming | 禁用 radix cache；stream interval 为 `30` |
| Workload | Random，input 上限 `8192` 或 `1024`、output 上限 `1024`、range ratio `0.8`、chat template |
| 请求数 / warmup | 正式测量 `10 × concurrency`；warmup `2 × concurrency` |
| Sweep | TP4 并发 `4,8,16,32,64,128,256`；TP8 并发 `4`，每个 scenario 都跑一轮 |

两个 workload 称为“8k/1k”和“1k/1k”，但 range ratio 意味着真实长度会在这些上限以下变化。
比较结果时保留原始输入、输出 token 数。共享 InferenceX client 使用无限 request
rate、限制最大并发并忽略 EOS。这是没有 interactive latency SLO 的吞吐 sweep。
每个点仅测量一次，不是多轮运行的中位数。

| 方案 | Target runner / A2A | TP / DP / EP | Prefill CUDA graphs | FlashInfer / CuTe DSL |
| --- | --- | --- | --- | --- |
| 历史 W4A4 参考 | `flashinfer_trtllm` / `none` | TP / 1 / 1 | 固定 SGLang HEAD 的默认策略 | 0.6.18 / 4.6.2 |
| 新增对齐版 W4A4 对照 | `flashinfer_trtllm` / `none` | TP / TP / TP，启用 DP attention | 关闭 | 0.6.18 / 4.6.2 |
| 新 W4A16 MegaMoE | `flashinfer_megamoe` / `flashinfer_megamoe` | TP / TP / TP，启用 DP attention | 关闭 | 0.7.0，`ad0a5e5e` / 4.7.1 |
| W4A16 CuTe DSL split MoE | `flashinfer_cutedsl` / `none` | TP / TP / TP，启用 DP attention | 关闭 | 0.7.0，`f9dd3c10` / 4.7.1 |

固定 SGLang 源码中，MegaMoE [强制要求 DP attention 且 DP=TP](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/arg_groups/moe_hook.py#L275-L303)，
并[强制 EP=TP](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/arg_groups/overrides.py#L1630-L1672)。
TRT-LLM 的 NVFP4 路径会[传入本地 expert 的 offset 和数量](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/layers/quantization/modelopt_quant.py#L2996-L3031)，
所以新对照可采用相同的 expert 分片，通信仍走标准路径。源码支持仍需新的实际运行验证。

首次 DP 对齐的 MegaMoE 在 `mem_fraction_static=0.85` 下于 8k1k TP4/C256
warmup 阶段停止：原生 BF16 TRT-LLM MTP prefill 路径要申请 3.16 GiB workspace，
但仅剩 1.37 GiB 显存，未产生该点的正式测量结果。
[失败原始文件与恢复说明](results/failures/c2-w4a16-megamoe-20260920/README_zh.md)
独立保留。新两组 overlay 均改为 **0.80**，预留更多运行时 workspace，并使用新 run ID
完整重跑各 16 点。每个 scenario 先跑 C256，提前验证此前失败的峰值；矩阵与请求数不变。
此前成功的六个 0.85 点仅作为诊断记录，不复用于 0.80 的对比。Metadata、实际解析参数
和绘图分组均记录显存比例。后续 CuTe DSL 第三组沿用 0.80 显存预留与 C256 优先顺序，
不会重启或替换两组现有 0.80 运行。

历史方案的 server 请求上限等于 client 并发。所有对齐方案均使用
`max(client concurrency, DP)`，因为固定 SGLang 会将此上限除以 attention DP，
且要求每个 rank 至少有一个请求。因此所有对齐方案 TP8/C4 的 server 上限均为 **8**，
client 并发仍是 **4**，正式测量请求数仍为 **40**。其余 TP4 点不变。Metadata 用
`server_max_running_requests` 单独记录 server 上限，与 client `concurrency` 区分。
所有对齐方案 TP8/C4 的 decode graph 配置上限仍为 **4**，但每个 DP rank 的请求容量
会将实际 capture buckets 限制为 `[1]`。共同的 chunked-prefill CLI 值 `32768`
在所有对齐方案中解析为 **TP4 每个 DP rank 8192**、**TP8 每个 DP rank 4096**；
prefill graphs 关闭是独立的设置。这些是由源码得到的[请求池容量规则](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/mem_cache/kv_cache_configurator.py#L2267-L2320)
和 [capture bucket 筛选规则](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/model_executor/runner/base_cuda_graph_runner.py#L66-L105)，
还要与每次运行的解析配置、日志核对。

所有方案都在模型接口使用 BF16 activation，并关闭 per-token FP4 activation quantization。
MegaMoE 使用 BF16 combine storage，并关闭 in-kernel FC2 reduction。两套 W4A16
方案都开启 `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`；CuTe DSL 另外关闭 fused finalize，
走标准 A2A `none` 路径，与 MegaMoE 内部通信路径不同。主比较对齐并行拓扑、prefill graph
策略与 draft backend；target 的 W4A4/W4A16 精度、MoE/通信 backend、FlashInfer
源码与 CuTe DSL 版本仍不同，不能归因于单独的 kernel 加速。

归档脚本显式写的 `--quantization fp8` 不适用于已序列化的 NVFP4 checkpoint，现改为
`modelopt_fp4`。旧 CLI 名称迁移为 `dsa`、`--dsa-*-backend` 和
`--cuda-graph-max-bs-decode`；decode graph 配置上限仍等于并发，server 请求上限的例外见上文。
固定 HEAD 已始终启用 V2，所以不再设置已移除的 `SGLANG_ENABLE_SPEC_V2`。
历史参考保留原生 draft 设置。所有对齐方案均显式设置
`--speculative-moe-runner-backend flashinfer_trtllm` 和
`--speculative-moe-a2a-backend none`，省略 `--speculative-draft-model-quantization`，
其中 MegaMoE 替代此前的 Triton/unquant draft 配置。与历史参考一样，序列化的 draft
量化设置可以继承 `modelopt_fp4`，但 GLM NextN decoder 以
[`quant_config=None`](https://github.com/sgl-project/sglang/blob/50eeb742961908afa68f4f523a1a19c5de6eb0b3/python/sglang/srt/models/deepseek_nextn.py#L64-L79)
构造原生 BF16 MoE，继承标签不会把其权重变成 FP4。对齐方案的 draft backend
与拓扑已经对齐，但 FlashInfer 版本不同，仍不是完全相同的软件执行路径。

## 运行历史拓扑

在单个 B300 节点上使用配置中的镜像。提前准备固定 revision 的完整模型快照、固定
commit 的干净 SGLang checkout，以及 InferenceX client 依赖。源码和输出放在
`/workspace` 以外；脚本会拒绝在 `/workspace` 下创建结果目录。

```bash
# 在配置镜像内的 InferenceX checkout 中运行。
source experimental/glm52_b300_fixed_seq/config.env
export SGLANG_SOURCE_ROOT=/data/home/ziangli/inferencex-glm52-b300/sources/sglang
export MODEL_PATH=/data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4
export OUTPUT_ROOT=/data/home/ziangli/inferencex-glm52-b300/results
export RUN_ID=c2-w4a4-historical-repeat
bash experimental/glm52_b300_fixed_seq/w4a4_trtllm_mtp.sh
```

若只运行一个点或补跑部分点，在 source 配置**之后**设置 `SWEEP_CASES`，例如
`export SWEEP_CASES='4:4'`。默认运行两个 scenario；若只跑一个，设置
`export SCENARIOS='8k1k:8192:1024'` 或 `export SCENARIOS='1k1k:1024:1024'`。通过 `GPU_IDS` 指定可用物理 GPU，每个点使用前 TP 个。
重复测量必须使用新的 `RUN_ID`；脚本不会覆盖已有结果目录。每个点启动独立 server，
收集结果后清理自己创建的 process group。server、client、清理错误或正式测量请求
缺失都会使 sweep 失败。

## 运行对齐版 TRT-LLM 对照

使用保留 FlashInfer 0.6.18 与 CuTe DSL 4.6.2 的原镜像环境，不复用已升级为
MegaMoE 软件栈的环境。按上文提供模型、源码、结果路径，再选择对照 overlay 和
独立的 run ID：

```bash
source experimental/glm52_b300_fixed_seq/config.env
source experimental/glm52_b300_fixed_seq/config-trtllm-aligned.env
export RUN_ID=c2-w4a4-dp-aligned-first
bash experimental/glm52_b300_fixed_seq/w4a4_trtllm_mtp.sh
```

Overlay 改变拓扑、prefill 策略与显存预留，不修改已安装的包。新 16 点结果独立记录；历史
DP1/EP1 的测量不能替代此对照。

## 准备优化版 MegaMoE

准备好固定 FlashInfer checkout 和对应依赖后，依次 source `config.env` 与
`config-megamoe.env`。除共享路径外，还须提供 `FLASHINFER_SOURCE_ROOT` 和独立的
`MEGAMOE_CACHE_ROOT`。Overlay 设置 `RUN_MEGAMOE=true`，并固定 FlashInfer commit
及 B300 CUDA 架构。用新的 run ID 运行 [`w4a16_megamoe_mtp.sh`](w4a16_megamoe_mtp.sh)；
仍配置相同的 8k1k/1k1k 与 TP/并发矩阵。

保留镜像 Torch，单独准备优化版 FlashInfer/CuTe 依赖；baseline 镜像中的 FlashInfer
0.6.18 cubin/JIT 包不属于优化源码的配套依赖。准备的栈使用匹配的 CuTe DSL 4.7.1
包和独立源码 cache。记录实际解析后的环境，以及启动和测量结果。Overlay 不安装
依赖，也不能证明运行时兼容性、精度或性能。

## 准备 CuTe DSL split-MoE 方案

复用已有的对齐版 TRT-LLM 和 MegaMoE 结果。单独准备 PR #5319 源码及依赖：
FlashInfer 0.7.0、全部五个 CuTe DSL 包 4.7.1、`nccl-extensions==0.1.0`，保留镜像
Torch，且不安装 FlashInfer cubin/JIT-cache provider。NCCL extension 是源码声明的
依赖；CuTe DSL 标准 target 路径不使用 MegaMoE EP transport。预检查源码 commit、
工作树干净状态、import 路径、FlashInfer 包/import 版本、CuTe DSL 版本与旧二进制
provider 缺席；这些检查不能证明 GPU 兼容性或精度。

```bash
source experimental/glm52_b300_fixed_seq/config.env
source experimental/glm52_b300_fixed_seq/config-cutedsl.env
export SGLANG_SOURCE_ROOT=/data/home/ziangli/inferencex-glm52-b300/sources/sglang
export FLASHINFER_SOURCE_ROOT=/data/home/ziangli/inferencex-glm52-b300/sources/flashinfer-f9dd3c10
export CUTEDSL_CACHE_ROOT=/data/home/ziangli/inferencex-glm52-b300/caches/cutedsl-f9dd3c10-cute4.7.1-cu13
export MODEL_PATH=/data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4
export OUTPUT_ROOT=/data/home/ziangli/inferencex-glm52-b300/results
export RUN_ID=c2-w4a16-cutedsl-mem80-first
bash experimental/glm52_b300_fixed_seq/w4a16_cutedsl_mtp.sh
```

Canonical backend 为 `w4a16_cutedsl`，每个点的目录为 `<scenario>/w4a16-cutedsl/`。
调用者须提供 `/workspace` 以外的绝对 `CUTEDSL_CACHE_ROOT`：SGLang 使用其中的
`sglang/` 子目录，FlashInfer workspace 使用该根目录，实际缓存位于
`.cache/flashinfer/`。完整保留此独立源码缓存；继承的 MegaMoE knob cache 会被清除。
Server 命令与 metadata 记录 W4A16/finalize 设置及源码/cache 路径。第三组保留两个
workload、全部 16 点、C256 优先顺序、共同 server 上限修正和原生 BF16 TRT-LLM MTP。
新增运行配置的 InferenceX commit 与复用的两组分别记录；backend/软件差异仍不能归因
为单独 kernel 的因果加速。

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
原始资料，不把待运行的点展示成实测数据。比较 TP4 与 TP8 时，按结果记录
的实际 GPU 数归一化吞吐。

## 主 Pareto 对比图

用 [`plot_pareto.py`](plot_pareto.py) 读取对齐版 TRT-LLM、MegaMoE
和 CuTe DSL 三个 run root。8k1k、1k1k 分别作图，历史参考另行作图：

```bash
python3 experimental/glm52_b300_fixed_seq/plot_pareto.py \
    --results "$ALIGNED_TRT_ROOT" "$MEGAMOE_RESULT_ROOT" "$CUTEDSL_RESULT_ROOT" \
    --output "$OUTPUT_ROOT/pareto-aligned" --dp-attention-aligned
```

主图 X 轴为**每请求交互性 `1000 / median_tpot_ms`**，单位 tok/s/user；Y 轴为
**`output_throughput / gpu_count`**，单位 output tok/s/GPU。两者越大越好。
交互性不包含首个 token，不是平均请求速率，也不代表满足某项延迟 SLO。
DP/EP 使用同一组 TP GPU，不再乘入分母。E2EL 图作为补充视图。
公式来自[固定 commit 的 fixed-sequence producer](https://github.com/SemiAnalysisAI/InferenceX/blob/8979f7c4cdd2946a02b459d5e62018e41bc02405/infx/results/fixed_sequence.py#L187-L207)，
并对应[固定版本的交互性指标](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/components/inference/metric-registry.ts#L701-L708)
和[仅输出吞吐的 Y 指标](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/components/inference/metric-registry.ts#L76-L82)。
绘图脚本检查对齐配置，拒绝混用历史与对齐版结果，保留成功实测点，并标注 client
并发和 TP/DP/EP。三组 **48 个点、30,720 个成功测量请求**全部完成，见[完整报告与图表](results/c2-three-arm-dp-mem80-20260920/comparison_zh.md)及[原始指标全表](results/c2-three-arm-dp-mem80-20260920/raw_metrics_zh.md)。MegaMoE 的输出吞吐/GPU 在 1k1k 全部八个点高于 CuTe split（+1.99% 至 +16.91%）；8k1k 七个点较低，仅 TP8/C4 较高（+5.62%）。这是不同 FlashInfer head 的单次端到端观测，不能视作独立 kernel 加速。旧 0.85 局部观测仍单独保留，不作为该图输入。
