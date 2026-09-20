# InferenceX 图表指标来源核对

[English](SOURCE_METRICS.md) | [中文](SOURCE_METRICS_zh.md)

绘图源码位于独立的公开 [InferenceX-app 仓库](https://github.com/SemiAnalysisAI/InferenceX-app)，该仓库由 InferenceX 的 README.md:34 链接。只读本地副本固定在提交 `b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9`。

| 所需指标 | 原始客户端 JSON → 数据生成端 → 前端 | 来源 |
|---|---|---|
| E2EL 附图横轴 | `median_e2el_ms / 1000` → `median_e2el`，单位：秒 | [数据生成端](https://github.com/SemiAnalysisAI/InferenceX/blob/8979f7c4cdd2946a02b459d5e62018e41bc02405/infx/results/fixed_sequence.py#L203-L207)、[前端](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/components/inference/metric-registry.ts#L701-L708) |
| Per-request Interactivity 主图横轴（每请求交互速度） | `1000 / median_tpot_ms` → `median_intvty`，单位：tok/s/user | 同上面的数据生成端和前端源码 |
| 输出吞吐纵轴 | `output_throughput / gpu_count` → `output_tput_per_gpu` → `outputTputPerGpu.y`，单位：tok/s/chip | [数据生成端](https://github.com/SemiAnalysisAI/InferenceX/blob/8979f7c4cdd2946a02b459d5e62018e41bc02405/infx/results/fixed_sequence.py#L175-L198)、[指标](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/components/inference/metric-registry.ts#L76-L82)、[派生字段映射](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/lib/chart-utils.ts#L324-L338) |

`infx/bench_serving/benchmark_serving.py:465-473, 509-530` 将每个成功请求的 TPOT 定义为 `(latency - TTFT) / (output_len - 1)`，E2EL 来自请求延迟，各中位数通过 `np.median` 计算；输出吞吐为生成的输出 token 数除以基准测试的实际经过时间。对于 completions API，延迟从请求开始计至最后一个收到的 choices 数据块（`infx/bench_serving/backend_request_func.py:258-303`），其中包含 TTFT。我们的 ISL/OSL 上限按 ratio0.8 采样，并非固定的实际观测长度。

网站对固定序列工作负载将这些横轴指标固定为中位数：[resolveXAxisField.ts:37-67](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/components/inference/utils/resolveXAxisField.ts#L37-L67)。横轴提供 Interactivity、E2E Latency 和 TTFT，没有直接选择 TPOT 的选项：`XAxisModeSelector.tsx:15-24`。固定序列的默认横轴是 Interactivity；当前默认纵轴是成本指标 `y_tokensPerDollarH`（`lib/url-state.ts:126`），因此应将 output/GPU 描述为我们选用的网站指标，而非网站默认指标。

本实验 PP=PCP=1，元数据中 gpu_count=TP。`infx/results/topology.py:20-22` 按 TP×PP×PCP 计算物理 GPU 分配数；EP 共享这些 GPU。GPU 归一化时不要再乘入 DP/EP。

逐系列前沿点的选择已独立核对，与 [chart-utils.ts:624-687](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/lib/chart-utils.ts#L624-L687) 一致，包括历史 E2EL 模式下 y 值相等时的取舍规则。全局前沿已独立核对，与 [global-pareto.ts:25-62](https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/components/inference/utils/global-pareto.ts#L25-L62) 一致，该实现会移除被支配的点和坐标相同的重复点。E2EL 最小化 x、最大化 y；Interactivity 同时最大化 x 和 y。历史名称 `upper_left` 和 `upper_right` 与按 x 数值方向直观理解的含义相反，`ScatterGraph.tsx:1493-1524` 对此有明确说明。应以源码为准，而不是 `docs/d3-charts.md` 中已过时的方向表。

静态图保留所有成功观测点，按工作负载、运行软件和 run 区分系列，同时在每个实验组内合并不同拓扑配置，并用虚线和实测顶点圆环显示全局前沿。全局前沿的直线段与网站一致。每个系列的彩色连线采用直线作为视觉引导，而非网站的 D3 单调插值（`ScatterGraph.tsx:2331-2335`）；这一改动已明确说明。按用户要求，标签始终显示 C 和 TP/DP/EP，扩展了网站可选的并发数与高级拓扑标签（`ui/point-label.ts:4-12`）。不对未测量的中间点、相同运行软件下的内核加速比或延迟 SLO 作出结论。

中文摘要：图表代码在独立的官方 InferenceX-app 仓库。主图使用网站 Per-request Interactivity，即 `1000 / median_tpot_ms`，附图才使用 E2EL（秒）；纵轴选择网站输出 token 吞吐/芯片，绝非输入加输出吞吐。固定序列模式强制 median。已按实际源码核对 series/global Pareto 的不同 tie 规则；静态图保留所有成功点，显式标 C 与 TP/DP/EP，按运行软件与 run 分组，同一实验组跨 TP/DP/EP 构造前沿。每组曲线以直线作为视觉引导，并注明与网站平滑曲线的差异；不把插值当实测。

官方分组源码：`ScatterGraph.tsx:788-825` 按 `hwKey + precision` 对官方点分组，然后按日期分别计算。其 `1080-1110` 处的非官方叠加数据按 `hwKey + precision + runIndex` 分组。TP/DP/EP 和并发数不是系列分组键。`chart-utils.ts:264-289` 根据硬件、框架和推测解码构造 hwKey。静态实验遵循这一方式，在每个后端、运行软件和 run 内合并不同 TP/DP/EP 配置，同时保留每个点完整的拓扑信息和客户端并发数。
