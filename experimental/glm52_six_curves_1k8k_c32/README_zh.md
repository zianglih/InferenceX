# GLM-5.2：并发数 4–32 的六条后端/拓扑曲线

[English](README.md) | [简体中文](README_zh.md)

本手动实验在一台配备八张 B300 GPU 的节点上，对比三种当前后端选择，每种分别使用 TP=EP=DP attention 4 和 8。它不属于 InferenceX 定时调度矩阵。实验脚本不会安装软件、申请节点、发布结果或删除存储；当前配方不附带实测结果。

## 实验矩阵与固定工作负载

| Arm ID | 目标 MoE runner | 目标 MoE A2A | 精度选择 |
|---|---|---|---|
| `megamoe-w4a4` | `flashinfer_megamoe` | `flashinfer_megamoe` | 后端默认值，不设置 W4A16 selector |
| `megamoe-w4a16` | `flashinfer_megamoe` | `flashinfer_megamoe` | `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1` |
| `trtllm-w4a4` | `flashinfer_trtllm` | `none` | 默认 per-tensor NVFP4 W4A4 |

每个 arm 先运行 TP=EP=DP attention 4，再运行 8；每种拓扑按 **32、4、8、16** 的顺序运行客户端并发数，首先完成最大并发点的校准。共 24 个点、3,600 个正式测量请求和 720 个预热请求。每个点启动新服务，执行 `2C` 次预热和 `10C` 次测量，随后只清理该点记录的所属进程，再进入下一点。

| 设置 | 值 |
|---|---|
| 目标模型 | GLM-5.2 NVFP4，checkpoint revision `53e0691e21895a3863a606dfd12910c69eba94ab` |
| 标称输入/输出 | 1,024 / 8,192 tokens，random-range ratio 0.8，客户端 seed 0 |
| 输出采样 | 请求长度 6,553–8,192 tokens，保留请求与完成长度的精确有序数组 |
| 流量 | 无限 request rate，客户端并发数 4/8/16/32 |
| 目标 dtype/quantization | `bfloat16` / `modelopt_fp4` |
| KV cache | `fp8_e4m3` |
| 推测解码 | `EAGLE`：steps 3、top-k 1、draft tokens 4，使用真实验证，不模拟 acceptance |
| Draft MoE | `flashinfer_trtllm` / `none`，BF16 MoE 路径 |
| Static memory fraction | 0.8 |
| 全局 chunked prefill | 32,768；DP4/DP8 的本地 attention 预算分别为 8,192/4,096 |
| Graphs | 禁用 prefill graphs；decode 最大 batch 配置跟随客户端并发数 |
| 服务容量 | `max(C, TP)`；TP8/C4 的服务容量为 8，本地容量为 1 |
| Streaming | `stream_interval=30` |

在固定版本 SGLang 的默认配置下，W4A16 selector 也会作用于符合条件的 dense NVFP4 linear。因此，这**不是仅改变 MoE 精度的隔离实验**，配方也不会强制指定 dense backend。Draft BF16 仅描述 draft MoE 路径，不能据此声称所有 draft tensor 都是 BF16。接受实测结果前，需要核对实际解析参数、完整启动日志、加载量化配置以及 native kernel 证据。

配方不注入 per-token activation flag/环境变量、禁用 quantization fast math 的开关、combine dtype、in-kernel reduction 或 4over6 调优覆盖。SGLang 自行提供单节点 MegaMoE 的 NVSHMEM 默认值。子进程从显式 `base_environment` 构造环境，拒绝继承 `SGLANG_*`、`FLASHINFER_*`、`NVSHMEM_*`、`TRTLLM_*`、loader preload 和设备覆盖，然后加入必要的 W4A16 selector、源码路径、离线设置及所属 cache 路径。唯一的 SGLang 环境例外是保留镜像已有的精确策略 `SGLANG_RUST_BUILD_MODE=never`；拒绝其他取值和镜像 build label。预检会记录可见可选 Rust extension 的来源/API，并明确记录缺失且未选用的模块。本工作负载禁用 radix cache、使用 ChunkCache 和默认 HTTP server，不强制运行 Cargo build 或增加无关 Rust 检查门槛。不要把调优开关放入 `base_environment`。

## 示例固定环境

- SGLang：`9d38e0530a1e35d1756a7fabf044bc39b77209b8`。
- FlashInfer：`a03f2205263d4e691d68e485bff287e37a19b6c3`。
- Image：`lmsysorg/sglang:nightly-dev-cu13-20260929-79cafec0@sha256:0f075735a6bf913a7cc1cd7ece4f526ae8af70fc5b88fdc02d9efe92a61cf3ae`。
- Runtime run ID：`glm52-six-curves-1k8k-c32-20260929-all24`。
- 所属短 TMP：`/tmp/infx-g52-6c-0929`。

`config.example.json` 记录预期版本和示例绝对路径，并不是软件已安装的证据。启动前，应根据实际准备好的节点确认 Python、源码、checkpoint 和基础环境字段。六个分组使用同一套安装，另外保留 import、版本、依赖冲突、native peer/拓扑检查和准备回执。Readiness 与 benchmark timeout 是失败保护，不是耗时估计。

Runner 在每个 case 边界复核 tracked source clean 状态、完整 commit、package freeze 以及配方/客户端摘要。存在源码 checkout 不代表所有导入的包字节都与它一致，仍需实际安装和 native 审核。

## 执行与采集

在 InferenceX checkout 内，先查看本地计划：

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/run.py \
  --config /absolute/path/to/actual-config.json --plan
```

完成准备与所有权审核后，由唯一 campaign owner 在准备好的节点上启动一次：

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/run.py \
  --config /absolute/path/to/actual-config.json --run
```

Run root 与短 TMP 必须是新建的独占路径。Runner 保存 owner marker，并在实际 TMP 内执行三次 AF_UNIX bind/cleanup 探测；进程清理同时核对 PID 和进程出生标识。每个点开始前及清理后，全部八张 GPU 都必须空闲。短 socket 探测通过不代表每次 collective 都走 fast path。

六个 tactic namespace 按后端、精度和拓扑隔离；本次新实验内部共享 compilation cache。示例默认不使用 compile seed；显式 seed 必须通过 manifest 与 compile-only-copy 检查，绝不复制 tactic。每个 case 仅在静止边界保存 cache 快照，包括精确 tactic payload 和 compilation 文件 stat 清单。这些快照不支持“无 JIT”“无 retuning”或 compile payload 全量哈希等声明。

测量时不得修改输入或扫描 live cache。只采集已封存且静止的 case 目录，保留失败 case、命令 stdout/stderr、所有权记录与所有终态回执。Runner 和外层进程完整退出、独立 raw/native 审核、发布、归档验证与存储保留是独立的发布条件。

## 读取结果并绘制六条前沿

需要 Python 3.11+；完整绘图还需要 Matplotlib。复制最终 campaign root 和所有精确 case 文件后，使用新的输出目录：

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/results.py \
  --run-root /absolute/path/to/collected-run \
  --output /absolute/path/to/new-results
```

运行期间可加 `--partial`，仅验证已完成 case 并输出部分表格，不生成最终图。完整 reader 会拒绝不完整或错误标识的矩阵、失败客户端、不完整所属进程清理、缺失启动探测、封存证据变化、解析后 backend 不符，以及同并发请求有序数组不一致。

输出包括：

- `raw-metrics.json` / `.csv`：已保存 latency 字段、派生速率、源码版本及 result/manifest SHA 绑定。
- `raw-saved-scalars.json` / `.csv`：每个 `result.json` 的全部 scalar，包括 outcome scalar；原始文件仍为依据。
- `paired-comparisons.json` / `.csv`：采用 50 位 Decimal 精度，明确 baseline/comparison ID；共 24 对同拓扑后端比较和 12 对同后端拓扑比较，零基线不计算百分比变化。
- `pareto.png` / `.svg`、`plot-points.json`、`frontiers.json`：全部 24 个点及六条独立计算的非支配前沿。
- `RESULTS.md`：链接完整表格的简洁英文报告。

x 坐标为 `1000 / saved median_tpot_ms`；y 坐标为 `total_output_tokens / duration / GPU_count`。Duration 来自客户端 `time.perf_counter()` 的完整测量区间，并非单独 decode 计时；Unix phase endpoint 使用另一时钟。MegaMoE W4A4 使用绿色 `#009E73`，MegaMoE W4A16 使用橙色 `#E69F00`，TRTLLM W4A4 使用蓝色 `#0072B2`。TP=EP=DP4 为实线/圆点，TP=EP=DP8 为虚线/三角。每个点标注 C，每个图例与机器可读坐标记录均标明拓扑。

已保存 ITL 是 interval 30 的流式 chunk 间隔，不是逐 token TPOT；MTP 服务状态均值可能包含预热。已保存均值、中位数、标准差与百分位被原样保留，不会根据未保存的逐请求 latency 重构。本单次串行实验不证明统计显著性、孤立因果关系、数值等价或回复内容等价。公开 accounting reader 不能代替完整终态、native 校准和持久保存审核。

## 本地行为验证

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/check.py
python3 -B experimental/glm52_six_curves_1k8k_c32/check_results.py
python3 -B experimental/glm52_six_curves_1k8k_c32/check_plot.py \
  --output /absolute/path/to/new-synthetic-layout-check
bash -n experimental/glm52_six_curves_1k8k_c32/benchmark_mtp.sh
```

绘图检查需要 Matplotlib，生成醒目标注为 synthetic 的布局 fixture。这些检查覆盖本地进程/cache 所有权、命令构造、reader 拒绝路径、计算和绘图，不启动服务，也不声明 GPU 性能。该手动实验没有定时矩阵 key 或 runner pool 注册，不支持通过常规 matrix planner 调度。
