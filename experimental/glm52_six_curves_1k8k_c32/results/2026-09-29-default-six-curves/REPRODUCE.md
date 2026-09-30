# Reproduce the 24-point plots from compact public tables

This directory contains aggregate result tables, settings, figures and original plotting/reader sources. Full logs, raw request traces, case receipts and native/runtime evidence have been retained locally and removed from the current public tree at the user's request. The original full bundles and their manifests remain unchanged in local project artifacts.

## Public plotting

With Python 3.11+ and Matplotlib, run from this directory using new output paths:

```sh
python3 -B by-topology/render_compact.py --published-root . --output /absolute/path/to/new-historical-plots
```

The inputs are the saved `results/raw-metrics.json` table and bundled sources. Plotting regenerates points and frontiers from those rows; it does **not** replay or validate the omitted raw evidence. Image bytes can depend on the plotting environment. Numeric points and frontier membership must match the saved JSON. All existing published PNG/SVG and numeric table bytes are preserved.

- [Result report](results/RESULTS.md), [compact settings](SETTINGS_SUMMARY.json), [scalar tables](results/raw-metrics.csv), [paired comparisons](results/paired-comparisons.csv).
- Throughput covers the client's full measured interval; x = 1000 / median TPOT, y = output tokens / duration / GPU count. Saved ITL is chunk spacing at stream interval 30.
- Measured-only MTP AL is unavailable because verification counters/boundary deltas were not saved. Labels remain `AL=N/A`; no lifetime/log estimate is substituted. The N/A annotations use the retained compact acceptance sidecar; its historical raw descriptors refer to the local evidence bundle.

## Full evidence replay (local bundle required)

From the **unchanged locally retained full bundle**, the original command remains:

```sh
python3 -B source/experimental/glm52_six_curves_1k8k_c32/results.py --run-root raw --output /absolute/path/to/new-full-evidence-replay
```

This command cannot run from this compact public tree because `raw/` is intentionally absent. The full bundle contains the original manifest, exact raw files and sources. `PROVENANCE.json` retains its manifest descriptor without publishing a large receipt chain. Runtime/native review, complete terminal acceptance, preservation and deletion remain separate evidence gates. See the result report for the CUDA quantizer, W4A16 dense-selector, cache history, runtime dependency and other qualifications.

<details><summary>中文</summary>

公开目录仅保留汇总表、设置摘要、图表及绘图/reader 源码。完整日志、逐请求记录和运行时证据已保存在本地项目 artifacts；原完整包和清单未改变。

以上命令从公开 `results/raw-metrics.json` 重绘图表、点坐标和前沿，不会重新验证已移到本地的原始证据。完整 reader 重放必须在含 `raw/` 的本地原完整包中执行；不能把公开绘图成功当作原始测量或运行时验收。现有图像和数值文件逐字节保留；历史实验 AL 仍为 N/A，不使用近似值。

</details>
