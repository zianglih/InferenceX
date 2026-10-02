# 历史 GLM 图表：精简公开复现

[English](README.md) | [简体中文](README_zh.md)

24 个历史点及总图/EP4/EP8 图像逐字节不变。原实验没有保存原生验证计数，因此仅测量阶段的 MTP acceptance length 仍标为 `AL=N/A`。

在父目录执行：

```sh
python3 -B by-topology/render_compact.py --published-root . --output /absolute/path/to/new-historical-plots
```

绘图器校验精简公开清单，读取 `results/raw-metrics.json`，不读取完整日志或重新验证测量。Acceptance sidecar 的原始文件摘要是本地证据的历史引用。原完整包仍在本地保留；完整证据重放边界见 [REPRODUCE.md](../REPRODUCE.md)。
