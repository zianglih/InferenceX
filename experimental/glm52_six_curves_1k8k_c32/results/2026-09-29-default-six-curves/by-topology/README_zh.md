# GLM-5.2 曲线与 MTP 接受长度标注

[English](README.md) | **中文**

这些视图复用[原始发布](../REPRODUCE.md)中已验收的 24 个测量点。每个点同时标注并发数（`Cn`）和 仅测量请求的 MTP 接受长度（`AL=N/A`）。此次没有新增测量，原始 2,520 个文件及原始 `FILES.json` 均保持不变。

| 视图 | PNG | SVG | 精确坐标 | 前沿成员 |
| --- | --- | --- | --- | --- |
| TP=EP=DP4 | [EP4](figures/ep4/pareto.png) | [EP4](figures/ep4/pareto.svg) | [JSON](figures/ep4/plot-points.json) | [JSON](figures/ep4/frontiers.json) |
| TP=EP=DP8 | [EP8](figures/ep8/pareto.png) | [EP8](figures/ep8/pareto.svg) | [JSON](figures/ep8/plot-points.json) | [JSON](figures/ep8/frontiers.json) |
| 合并六条曲线 | [合并图](figures/six-curves/pareto.png) | [合并图](figures/six-curves/pareto.svg) | [JSON](figures/six-curves/plot-points.json) | [JSON](figures/six-curves/frontiers.json) |

每张单独拓扑图包含三个后端各自的前沿，以及 C4、C8、C16、C32 的全部 12 个点：每种拓扑有 **1,800 个成功测量请求和 360 个预热请求**，测量请求失败数为零。合并图包含全部 24 个已验收点、3,600 个测量请求和 720 个预热请求。连线仅连接同一后端、同一拓扑内的非支配点，不表示跨后端的统一前沿。所有图中文字均为英文。

- MegaMoE W4A4：绿色 `#009E73`。
- MegaMoE W4A16：橙色 `#E69F00`。
- TRTLLM NVFP4 W4A4：蓝色 `#0072B2`。
- 单独拓扑图保留实线和圆点；合并图中 EP4 使用实线/圆点，EP8 使用虚线/三角形。各拓扑均启用 TP=EP=DP attention。

沿用的读取器计算 **x = 1,000 / 已保存的 median TPOT（毫秒）**，**y = 完成的输出 token 总数 / 完整测量区间 / GPU 数**。所有坐标和前沿成员均与原始发布完全一致。EP4/EP8 的坐标和前沿 JSON 文件保持逐字节一致。各图坐标轴独立缩放，跨图比较时请查看刻度。

## 接受长度的定义与范围

[指标附表](figures/acceptance-length.json)将全部 24 个 case 标为 `measured_acceptance_length: null` 和 `status: unavailable`，并记录缺失计数的原因，以及结果文件和前后 server metadata 的精确描述。每个数据点均显示 **AL=N/A**；它不表示零，也不使用近似值代替。

希望得到的原生汇总值排除预热请求：

```text
Measured-only AL = sum(completion_tokens) / sum(spec_verify_ct)
                   over measured requests only
```

原生 completion-token 口径包含 bonus token。本次 benchmark client 未请求或保存逐请求 `spec_verify_ct`，也未保存测量边界处的计数增量。before 快照早于预热，after 快照只提供各 rank 的累计比值，而不是缺失的计数。因此，现有文件无法确定精确的仅测量请求汇总 AL。不会用已舍入的日志窗口值或包含预热的 rank 均值代替。

吞吐和延迟坐标仍然有效且保持不变。将 AL 标为不可用不会改变前沿成员、请求总数或基准结果。要获得精确的仅测量请求 AL，需要在未来运行中保存原生逐请求 completion 和 verification 计数，或口径相同、边界明确的计数；本次图表更新不执行新测量。

标称长度为 1,024 输入 / 8,192 输出，ratio 0.8，seed 0。EAGLE 使用 steps 3 / top-k 1 / draft tokens 4。保留后端量化与 fast-math 默认值。W4A16 选择也会影响符合条件的 dense NVFP4 linear；BF16 描述 draft MoE 路径，不代表所有 draft tensor。已保存的 ITL 是 stream interval 30 下的分块间隔。完整区间吞吐不是单独计时的 decode 吞吐。顺序运行的观测不能证明因果关系、统计显著性或数值/内容等价性。[完整报告与原始表格](../results/RESULTS.md)保留原始方法和限制。

## 仅用公开发布内容复现

使用 Python 3.11+ 和 Matplotlib。在当前目录选择一个尚不存在的输出目录：

```sh
python3 -B render.py --published-root .. --output ../regenerated-annotated-views
```

辅助脚本在渲染前后，按固定的原始清单校验全部 2,520 个文件。它通过未修改的公开读取器验证完整、已封存的原始测量，核对已发布指标，并复用原有绘图和前沿函数。新增内容仅包括 AL 标注、带引导线的确定性位置选择、视图标题和范围说明。标签布局会拒绝与其他标签或数据点标记重叠的位置。输出包含 EP4、EP8、合并图的 PNG/SVG、精确坐标/前沿、AL 附表和相对路径输入来源。无需网络、私有证据路径或新基准测试。

渲染环境为 Python 3.14.6、Matplotlib 3.10.6、NumPy 2.5.3 和 DejaVu Sans。图像字节可能受 Python、Matplotlib 和字体版本影响；坐标、前沿及 AL 状态 JSON 是复现目标。`INPUTS.json` 绑定未修改的公开输入。附加目录的 `FILES.json` 仅覆盖当前目录且不包含自身，不替代原始发布清单。本次仅更新图表和标注，不修改 recipe 或运行时。
