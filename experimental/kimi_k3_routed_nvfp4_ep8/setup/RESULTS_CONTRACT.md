# Accepted-results interface

The result reader consumes an exact local collection after independent case and terminal review. A runner completion receipt is not automatically an accepted campaign.

```sh
python3 -B setup/results.py --root /absolute/accepted-collection \
  --acceptance ACCEPTANCE.json --output /absolute/new-results
```

`ACCEPTANCE.json` requires schema 1, status `ACCEPTED_COMPLETE_CAMPAIGN`, `data_kind: actual`, exact descriptors for campaign, PLAN, normalized checkpoint acceptance, vendored client SOURCE, terminal summary and independent terminal review, plus the 12 ordered case manifest/review pairs. All collection descriptors have `path` relative to the collection root, exact `bytes`, and lowercase SHA256. Preserve original raw bytes; never rewrite a failed or incomplete receipt into an acceptance. See `results.py::load` for the authoritative validated fields.

Each case review must say `PASS_ACTUAL_CASE_REVIEW`, bind the manifest SHA and actual warmup count, and supply rehashable supporting evidence for request plan, actual client argv, workload settings, source/runtime, native backend and owned postbenchmark cleanup. Each manifest includes the unmodified client `result.json`, exact ordered `requested-lengths.json`, full `benchmark.log` and the remaining runner evidence. The reader checks all 12 identities, 360 warmups, 1,800 successful measured requests, zero failures, same-C ordered input/output arrays across arms, token sums, durations and saved scalar identities.

The terminal summary is exactly status `completed`, `waited_returncode:0`, `error:null`, empty cleanup errors and remaining owners, and all 12 ordered completed case IDs. `PASS_ACTUAL_TERMINAL_REVIEW` binds its SHA and the original waited-exit/ownership evidence. These JSON statements must be backed by actual reviews, not synthesized from plan files.

The normalized checkpoint acceptance must match campaign's exact byte binding, source revision, Miles commit, fixed output path and all seven checks in `checkpoint_contract.py`. All three conversion-stage receipts, actual output metadata and independent supporting review remain required. Public recipe files are not a substitute for that evidence.

Only a fully accepted collection may produce RAW_METRICS.csv, RESULTS.json, ORDERED_LENGTHS.json, COMPARISONS.json, FRONTIERS.json and PNG/SVG. Keep every saved mean/median/std/p90/p99/p99.9 statistic. Each of 12 same-C pair comparisons preserves 24 latency plus 4 throughput/interactivity metrics. Signs are candidate/baseline minus one; zero baselines yield null. The R4 TP8/EP8/DP1 reader uses solid lines and circle markers for all three curves; colors remain green/orange/blue. Exact topology and server/graph capacities must match the accepted plan, and the local integration descriptors and bytes remain part of the accepted results provenance. The unpublished integration is not supplied by this scripts-only package. Visually inspect final figures for label overlap. No synthetic fixture may be published as measured data.

## 中文

reader仅接收独立验收后的完整collection；runner运行完成不自动等于campaign验收。所有描述符必须保留准确相对路径、字节数和SHA256。必须有12个点、360次预热、1,800次成功测量、零失败、有序请求长度匹配、完整原始日志、实际后端和进程清理审查，以及真实waited terminal证据。失败或不完整回执不能改写成验收。

checkpoint验收须匹配固定转换来源和输出路径，包含三个阶段、实际metadata、七项检查及独立支持证据。公开配方不能替代这些文件。仅完整实际collection可以产生图表；保留所有统计量及12组相同C对比，逐项检查最终PNG/SVG，不得将合成fixture当作实测。

R4 reader 对应 TP8/EP8/DP1，三条曲线采用实线和圆点，颜色仍为绿/橙/蓝。拓扑、server/graph 容量以及本地集成的描述符和字节必须与已验收 plan 一致；本脚本包不提供尚未公开的集成源码。
