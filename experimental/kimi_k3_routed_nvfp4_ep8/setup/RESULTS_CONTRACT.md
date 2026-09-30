# Accepted-results interface

The result reader consumes an exact local collection after independent case and terminal review. A runner completion receipt is not automatically an accepted campaign. The R5 recipe is a continuation: its canonical plan has twelve cases, but its execution and terminal cover only eleven new cases.

```sh
python3 -B setup/results.py --root /absolute/accepted-collection \
  --acceptance ACCEPTANCE.json --output /absolute/new-results
```

## Shared evidence

`ACCEPTANCE.json` requires schema 1, `data_kind: actual`, exact descriptors for campaign, PLAN, normalized checkpoint acceptance, vendored client SOURCE, terminal and independent terminal review, plus the twelve ordered case manifest/review pairs. Collection descriptors have a path relative to the collection root, exact `bytes` and lowercase SHA256. Never rewrite a failed or incomplete receipt into an acceptance. `results.py::load` and `continuation.py` are authoritative for the validated fields.

Each case review must say `PASS_ACTUAL_CASE_REVIEW`, bind the manifest SHA and actual warmup count, and supply rehashable supporting evidence for request plan, client argv, workload settings, source/runtime, native backend and owned postbenchmark cleanup. Each manifest includes the unmodified client result, ordered requested lengths, full benchmark log and remaining runner evidence. Across the composite, the reader checks twelve identities, 360 warmups, 1,800 successful measured requests, zero failed measured requests, same-C ordered input/output arrays across arms, token sums, durations and saved scalar identities.

The normalized checkpoint acceptance must match campaign's exact byte binding, source revision, Miles commit, fixed output path and all seven checks in `checkpoint_contract.py`. All three conversion-stage receipts, actual output metadata and independent supporting review remain required. Public recipe files do not replace this evidence.

## R5: accepted prior point plus eleven new cases

R5 requires status `ACCEPTED_COMPOSITE_CAMPAIGN`. The canonical first case is the previously accepted MegaMoE W4A4 C32 point; the remaining eleven must be independently accepted R5 cases. The new execution has 296 warmups and 1,480 measured requests. These are required counts, not claims of current completion.

- `prior_acceptance` binds `ACCEPTED_KIMI_PRIOR_C32_FOR_CONTINUATION`, with `accepted_case_only:true` and `original_sweep_accepted:false`. Its exact supporting inputs include the original case native/settings/workload reviews, manifest, result, ordered arrays, source/cache lineage and failed R4 terminal/review. The composite's first manifest must match the accepted prior manifest. The original failed sweep remains failed.
- The actual worker `terminal` must be `status: completed`, `exit_code:0`, `error:null`, with empty cleanup errors and remaining owners. `completed_case_ids` and `execution_case_ids` must be the exact ordered eleven IDs; `execution_totals` must be 11/296/1480 and `prior_case_id` the accepted C32. Its prior/cache acceptance descriptors must match the campaign.
- `terminal_review` must be `PASS_ACTUAL_CONTINUATION_TERMINAL_REVIEW`, bind the terminal SHA, record `waited_returncode:0` and the exact eleven completed IDs, and retain actual waited-exit/ownership evidence. `composite_review` must separately be `PASS_ACTUAL_COMPOSITE_CAMPAIGN_REVIEW` and bind that terminal SHA. No successful single twelve-case terminal may be fabricated.
- The seed must be `ACCEPTED_KIMI_QUIESCENT_CACHE_SEED`, `data_kind: actual`, joined to the same prior acceptance. `cache_seed_installation` must bind the actual `ACCEPTED_SEED_INSTALLED_WITH_FRESH_TMP_OWNER` receipt and its full `cache-installation-inventory.json`; the compact receipt alone is insufficient. The reader verifies cache/HF/TMP namespaces, a fresh TMP owner, exact copied file/byte coverage and the explicit historical marker exclusion. Preserved bytes do not guarantee path-dependent cache hits.
- `prior_binding_map` explicitly relocates the sealed parent's absolute descriptor paths and the installed-inventory descriptor into the collection. Every relocation preserves exact bytes/SHA; the original receipt itself is never rewritten. Supply the full referenced JSON evidence, not only the alias map.

An ordinary `ACCEPTED_COMPLETE_CAMPAIGN` is rejected when campaign contains `continuation`. For a separate campaign without continuation, the existing complete-run path still requires a single exact twelve-case terminal with `waited_returncode:0` and `PASS_ACTUAL_TERMINAL_REVIEW`. That legacy path is not the R5 acceptance contract.

## Output boundary

Only the fully accepted composite may produce RAW_METRICS.csv, RESULTS.json, ORDERED_LENGTHS.json, COMPARISONS.json, FRONTIERS.json and PNG/SVG for this continuation. Keep every saved mean/median/std/p90/p99/p99.9 statistic. Each of twelve same-C pair comparisons preserves 24 latency plus four throughput/interactivity metrics. Signs are candidate/baseline minus one; zero baselines yield null. Reports identify one accepted R4 point and eleven accepted R5 points rather than claiming one uninterrupted sweep.

The TP8/EP8/DP1 reader retains green/orange/blue solid lines and circle markers. Exact topology, server/graph capacities and local integration provenance must match the accepted plan. The unpublished integration is not supplied by this scripts-only package. Inspect final PNG/SVG for overlap; no synthetic fixture may be published as measured data. This interface document does not issue any case, terminal or composite acceptance.

## 中文

reader 只接收经过独立 case/terminal 审查的精确 collection；runner 完成不自动构成 campaign 验收。R5 的标准计划为十二点，实际续跑及 terminal 只覆盖新的十一点。

共同证据要求 schema 1、`data_kind: actual`、campaign/PLAN/checkpoint/client SOURCE/terminal/独立审查的精确描述符，以及十二组有序 manifest/review。collection 路径相对根目录，保留准确 bytes 和 SHA256。每个 `PASS_ACTUAL_CASE_REVIEW` 都绑定 manifest、实际 warmup 及 request/client/workload/source/runtime/native/cleanup 证据。总计须为十二点、360 次 warmup、1,800 次成功测量、测量请求零失败，同 C 有序数组匹配，并核验 token、duration 及所有保存统计量。转换验收仍须包含三个阶段、实际 metadata、七项检查及独立证据；公开脚本不能替代它们。

R5 必须使用 `ACCEPTED_COMPOSITE_CAMPAIGN`：一个已验收的 R4 MegaMoE W4A4 C32 点，加十一个独立验收的 R5 点。新的执行应有 296 次 warmup 和 1,480 次测量；这些是验收要求，不表示目前已经完成。

- `prior_acceptance` 必须为 `ACCEPTED_KIMI_PRIOR_C32_FOR_CONTINUATION`，明确 `accepted_case_only:true`、`original_sweep_accepted:false`，绑定原 native/settings/workload 审查、manifest/result/有序数组、source/cache 关系及失败 R4 terminal/review。composite 首个 manifest 必须等于 prior manifest，原扫描仍保留为失败。
- 实际 worker `terminal` 要求 `status: completed`、`exit_code:0`、`error:null`，cleanup/remaining owner 为空；完成及执行 ID 均为精确有序十一点，`execution_totals` 为 11/296/1480，prior ID 和 prior/cache 描述符与计划一致。
- `terminal_review` 必须为 `PASS_ACTUAL_CONTINUATION_TERMINAL_REVIEW`，绑定 terminal SHA、`waited_returncode:0`、精确十一点 ID 及实际 wait/ownership 证据。另需 `PASS_ACTUAL_COMPOSITE_CAMPAIGN_REVIEW` 绑定该 terminal SHA，不得虚构单次十二点成功 terminal。
- seed 必须为 actual `ACCEPTED_KIMI_QUIESCENT_CACHE_SEED`，连接同一 prior。`cache_seed_installation` 绑定实际 `ACCEPTED_SEED_INSTALLED_WITH_FRESH_TMP_OWNER` 和完整 `cache-installation-inventory.json`，不能只提供紧凑回执。reader 核验 cache/HF/TMP 路径、新 TMP owner、复制文件/字节覆盖及明确的历史 marker 排除；字节保留不保证依赖路径的缓存命中。
- `prior_binding_map` 将父回执的绝对描述符及安装清单描述符映射到 collection，必须保持同一 bytes/SHA，不改写原回执，并提供完整引用 JSON，而非仅映射表。

包含 `continuation` 的 campaign 不能使用普通 `ACCEPTED_COMPLETE_CAMPAIGN`。仅另一种没有 continuation 的 campaign 才保留原单次十二点 terminal（`waited_returncode:0`）及 `PASS_ACTUAL_TERMINAL_REVIEW` 路径；它不是 R5 合同。

本次续跑只有完整验收的 composite 才能输出表格和 PNG/SVG。保留全部统计量及十二组同 C 对比（每组 24 项 latency 加四项吞吐/交互指标），报告明确两个执行阶段。TP8/EP8/DP1 仍用绿/橙/蓝实线圆点；拓扑、server/graph 容量和本地集成来源须匹配已验收 plan。未公开集成不在脚本包内，合成 fixture 不得作为实测发布。本文件本身不授予任何实际验收。
