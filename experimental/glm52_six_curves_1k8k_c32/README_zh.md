# GLM-5.2：并发 1–32 的六条曲线与测量阶段 MTP 计数

[English](README.md) | [简体中文](README_zh.md)

本手动配方准备一次**新的 36 点实验**：在单台八卡 B300 节点上，比较三种后端，并分别使用 TP=EP=DP attention 4 和 8。每个成功点必须保存每条测量请求的原生推测解码计数。本次脚本变更**不包含新的实测结果**。实验不在 InferenceX 定时矩阵中；脚本不会安装依赖、申请节点、发布结果或删除存储。

不可变的 [2026-09-29 结果包](results/2026-09-29-default-six-curves/REPRODUCE.md)仍包含 **24 个已接受点、3,600 条成功测量请求、720 条预热请求和六条 Pareto 前沿**。当时的客户端没有保存测量阶段的推测解码计数，因此该历史实验的 measured-only MTP acceptance length **不可用**。现有 N/A 图和原始数据不会被本次重跑改写。

## 矩阵与固定负载

| Arm ID | Target MoE runner | Target MoE A2A | 精度选择 |
|---|---|---|---|
| `megamoe-w4a4` | `flashinfer_megamoe` | `flashinfer_megamoe` | 后端默认值；不设置 W4A16 selector |
| `megamoe-w4a16` | `flashinfer_megamoe` | `flashinfer_megamoe` | `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1` |
| `trtllm-w4a4` | `flashinfer_trtllm` | `none` | 后端默认 per-tensor NVFP4 W4A4 |

每个后端先运行 TP=EP=DP attention 4，再运行 8；各拓扑按 **32、1、2、4、8、16** 的客户端并发顺序运行，先完成最大点的校准。共 36 点、3,780 条测量请求和 756 条预热请求。每点启动新服务，运行 `2C` 预热和 `10C` 测量请求，然后仅清理其记录的进程，再进入下一点。

| 设置 | 值 |
|---|---|
| Target 模型 | GLM-5.2 NVFP4，checkpoint revision `53e0691e21895a3863a606dfd12910c69eba94ab` |
| 标称输入/输出 | 1,024 / 8,192 tokens，random-range ratio 0.8，seed 0 |
| 输出采样 | 6,553–8,192 tokens；保存请求和完成的有序长度数组 |
| 流量 | 无限请求速率，客户端并发 1/2/4/8/16/32 |
| Target dtype/quantization | `bfloat16` / `modelopt_fp4` |
| KV cache | `fp8_e4m3` |
| 推测解码 | `EAGLE`：steps 3、top-k 1、draft tokens 4；真实验证，不模拟 acceptance |
| Draft MoE | `flashinfer_trtllm` / `none`，BF16 MoE 路径 |
| Static memory fraction | 0.8 |
| 全局 chunked prefill | 32,768；DP4 本地预算 8,192，DP8 本地预算 4,096 |
| Graphs | 禁用 prefill graphs；decode 最大值跟随客户端 C |
| 服务容量 | `max(C, TP)`；低并发仍只有 C 条在途请求，每个 DP worker 至少保留一个服务槽位 |
| Streaming | `stream_interval=30` |

在固定 SGLang 默认实现下，W4A16 selector 也影响符合条件的 dense NVFP4 linear，因此**不是仅改变 MoE 精度的隔离实验**。不强制 dense 后端。Draft BF16 仅描述其 MoE 路径，不代表所有 draft tensors。接受实测前，须审核实际解析参数、完整启动日志、量化和原生 kernel 证据。

不注入 per-token activation、禁用 quantization fast math、combine dtype、in-kernel reduction 或 4over6 tuning。MegaMoE 的单节点 NVSHMEM 默认值由 SGLang 设置。子进程从显式 `base_environment` 开始，拒绝继承 `SGLANG_*`、`FLASHINFER_*`、`NVSHMEM_*`、`TRTLLM_*`、loader preload 和设备覆盖，再添加必要的 selector、源码、离线和缓存路径。唯一允许的 SGLang 环境例外是镜像既有策略 `SGLANG_RUST_BUILD_MODE=never`；不接受其他值或镜像 build 标签。准备检查另行记录可见 Rust 扩展的来源/API，以及未安装且未选用的模块；本实验不强制 Cargo 构建或无关 Rust gate。

## 固定示例环境

- SGLang：`9d38e0530a1e35d1756a7fabf044bc39b77209b8`。
- FlashInfer：`a03f2205263d4e691d68e485bff287e37a19b6c3`。
- 镜像：`lmsysorg/sglang:nightly-dev-cu13-20260930-cae69be5@sha256:0412c5b792cb35706de0359de4a1af52c160d4bdef6ff7530baf9df4e2a7b0b4`。
- Run ID：`glm52-six-curves-measured-mtp-20260930-all36`。
- 独占短 TMP：`/tmp/infx-g52-mtp-0930`。

`campaign_contract` 必须严格为 `glm52-six-curves-measured-mtp-v1`。新 runner/reader 会拒绝历史配置。

`config.example.json` 是声明的 pin 和绝对路径示例，不证明节点已安装这些内容。启动前须根据实际节点核对 Python、源码、checkpoint 和基础环境；六组共用同一套安装。导入、版本、依赖冲突、native peer/topology 和准备回执须另行保留。超时仅是失败保护，不是性能估计。

每点边界都会重新检查 tracked source clean、完整提交、package freeze 和本地配方/客户端摘要。仅有源码 checkout 并不能证明实际导入的全部包字节相同，仍须准备和 native review。

## 运行与收集

在 InferenceX checkout 中先审核纯本地计划：

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/run.py \
  --config /absolute/path/to/actual-config.json --plan
```

完成准备和进程所有权审核后，由唯一负责者在目标节点启动一次：

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/run.py \
  --config /absolute/path/to/actual-config.json --run
```

Run root 与短 TMP 必须是新建独占路径。Runner 记录 owner marker，并在实际 TMP 中进行三种 AF_UNIX bind/cleanup 探针；以 PID 和进程出生标识清理子进程。轮询或回收已跟踪 leader 前先发现同 session 的后代，包括已退出但尚未回收 leader 的新子进程；这不证明观察集合之外任意 detached 后代均不存在。每点之前和清理之后要求八张物理 GPU 空闲。短 socket 成功不代表所有 collective 都走了最快路径。

六个 tactic namespace 按后端、精度、拓扑隔离；新实验内部共享编译缓存。示例不使用 seed；显式配置的 seed 必须通过既有 manifest 和 compile-only-copy 校验，绝不复制 tactics。静止边界保留精确 tactic payload 和编译文件 stat inventory，不能据此声称完全不 JIT、不 retune 或已 hash 所有编译 payload。

测量时不改输入、不扫描活动缓存。仅收集已经封存且相关进程退出的 case。保留失败、stdout/stderr、所有权和终止回执。完整内外层退出、独立 raw/native review、发布、归档和存储保留分别验收。

## 读取新结果与绘图

需要 Python 3.11+；绘图还需要 Matplotlib。收集完整 case 文件后，使用新输出目录：

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/results.py \
  --run-root /absolute/path/to/collected-run \
  --output /absolute/path/to/new-results
```

运行期间可加 `--partial`，只验证已封存点并生成部分表，不生成最终图。完整 reader 拒绝不完整矩阵、失败客户端、未清理进程、缺少启动探针、改变的证据、不符的后端设置或同 C 的有序请求数组差异。

支持移动 checkout：reader 从封存 command 重建 producer `PYTHONPATH`，校验两种 launch environment 和 argv，其余环境严格相等。六个 recipe/client 源码摘要（包括纯 speculative-metrics reducer）必须与当前 reader 相符。复现包需携带这些源码，不改写原始远端路径，不猜测未记录的工作目录。

输出包括：

- `raw-metrics.json` / `.csv`：保存的延迟、推导速率、测量 AL/rate/coverage、源码与 result/manifest SHA。
- `raw-saved-scalars.json` / `.csv`：全部已保存 scalar，包括 outcome 和 speculative_metrics scalar；原始文件仍是权威。
- `paired-comparisons.json` / `.csv`：Decimal50 算术、显式 baseline/comparison；36 个同拓扑后端对比与 18 个同后端拓扑对比，零 baseline 不计算百分比。
- `pareto.png` / `.svg`、`plot-points.json`、`frontiers.json`：36 点和六条分别计算的非支配前沿。
- `figures/ep4/` 和 `figures/ep8/`：各18点、三条前沿，坐标与 AL 一致；两个单独视图均用实线/圆点，组合图 EP8 仍为虚线/三角。
- `RESULTS.md`：链接完整表格的英文报告。

横坐标为 `1000 / saved median_tpot_ms`，纵坐标为 `total_output_tokens / duration / GPU_count`。Duration 来自测量阶段完整 `perf_counter()` 区间，不是单独计时的 decode；Unix 阶段端点使用另一时钟。绿色 `#009E73` 表示 MegaMoE W4A4，橙色 `#E69F00` 表示 W4A16，蓝色 `#0072B2` 表示 TRTLLM W4A4。TP4 为实线/圆点，TP8 为虚线/三角；点标注 C 和 measured AL。

ITL 是 interval 30 的 streamed chunk 间隔，并非 per-token TPOT。保留原始均值、中位数、标准差、百分位，不重建未保存的 per-request latency。单次串行实验不能证明显著性、隔离因果、数值或内容等价；accounting reader 不能替代完整 terminal/native/持久保留审核。

## 测量阶段 MTP 合约

Wrapper 显式传递 `--capture-speculative-metrics`。共享 Bash bridge 对其他配方默认关闭此选项。原生 OpenAI-compatible 响应必须返回最终 `usage.completion_tokens` 与 `spec_tokens_details` 中的 `spec_verify_ct`、`spec_num_correct_drafts`、`spec_num_proposed_drafts`、原生 length/rate。按测量请求原始顺序保留记录。预热请求采用同一响应格式，但不进入聚合。

- **Acceptance length**：测量请求的 `sum(completion_tokens) / sum(spec_verify_ct)`，包含原生 bonus token 约定。
- **Acceptance rate**：同批请求的 `sum(spec_num_correct_drafts) / sum(spec_num_proposed_drafts)`。
- 覆盖不足时客户端仍保存原始计数和 coverage，但返回非零。Runner/reader 必须验证完整覆盖、正分母、纯 reducer 的精确重放，以及每条 completion token 与有序输出长度一致。缺失、非法、自相矛盾或部分计数不能成为接受点；不以 rank 均值、日志窗口、输出 token 加权估计或合成 AL 替代。
- CSV/JSON 显示 measured AL/rate 和 coverage；AL/rate 的匹配对比从整数计数用 Decimal50 重算。每条详情保留在封存 `result.json`。

## 复现历史 24 点结果

使用结果包冻结的 reader，不使用新的 36 点 reader：

```bash
cd experimental/glm52_six_curves_1k8k_c32/results/2026-09-29-default-six-curves
python3 -B source/experimental/glm52_six_curves_1k8k_c32/results.py \
  --run-root raw --output /absolute/path/to/new-historical-reproduction
```

该命令保持原 24 点合约，不伪造 measured MTP。新的 36 点结果必须在实际审核后保存到独立目录，不覆盖历史发布包。

## 本地行为验证

```bash
python3 -B experimental/glm52_six_curves_1k8k_c32/check.py
python3 -B experimental/glm52_six_curves_1k8k_c32/check_results.py
python3 -B experimental/glm52_six_curves_1k8k_c32/check_plot.py \
  --output /absolute/path/to/new-synthetic-layout-check
bash -n experimental/glm52_six_curves_1k8k_c32/benchmark_mtp.sh
```

绘图检查依赖 Matplotlib，并显著标记为合成样例。这些检查覆盖本地进程/缓存所有权、配方构造、封存 reader 拒绝路径、算术和绘图，不启动服务、不声明 GPU 性能。本实验没有 scheduled matrix key 或 runner-pool 注册，不能用常规 matrix planner 调度。
