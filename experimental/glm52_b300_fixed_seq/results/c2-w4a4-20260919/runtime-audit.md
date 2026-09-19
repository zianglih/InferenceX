# Discovered completed baseline case audit

Audited 16 completed cases; 10240 measured requests completed; 0 invariant mismatches. Skipped 0 incomplete/nonbaseline cases.

This checks discovered artifacts only; it does not certify that the full requested matrix exists.

| Case | UTC measured interval | Completed | Output tok/s | Allocator before / measured / after | Late-load total | Cleanup ERROR | Prefill measured T/F | Cumulative AL | Issues |
|---|---|---:|---:|---|---:|---:|---|---:|---:|
| 1k1k/tp4_conc4 | 2026-09-19T08:50:19.194763+00:00 → 2026-09-19T08:51:03.703653+00:00 | 40/40 | 824.756595 | 0 / 0 / 0 | 0 | 0 | 35/0 | 2.943976 | 0 |
| 1k1k/tp4_conc8 | 2026-09-19T08:55:39.800822+00:00 → 2026-09-19T08:56:38.501736+00:00 | 80/80 | 1266.181305 | 0 / 0 / 0 | 0 | 0 | 73/1 | 3.044365 | 0 |
| 1k1k/tp4_conc16 | 2026-09-19T09:01:26.688088+00:00 → 2026-09-19T09:02:43.903634+00:00 | 160/160 | 1899.475030 | 0 / 0 / 0 | 0 | 0 | 145/1 | 2.931075 | 0 |
| 1k1k/tp4_conc32 | 2026-09-19T09:07:32.812727+00:00 → 2026-09-19T09:09:15.375539+00:00 | 320/320 | 2883.637796 | 0 / 0 / 0 | 0 | 0 | 271/2 | 2.977393 | 0 |
| 1k1k/tp4_conc64 | 2026-09-19T09:14:26.011045+00:00 → 2026-09-19T09:16:49.278945+00:00 | 640/640 | 4117.105080 | 0 / 0 / 0 | 0 | 0 | 488/12 | 2.979266 | 0 |
| 1k1k/tp4_conc128 | 2026-09-19T09:22:25.534605+00:00 → 2026-09-19T09:26:05.975025+00:00 | 1280/1280 | 5342.922157 | 0 / 0 / 0 | 0 | 0 | 830/49 | 2.991937 | 0 |
| 1k1k/tp4_conc256 | 2026-09-19T09:32:51.196618+00:00 → 2026-09-19T09:41:57.859843+00:00 | 2560/2560 | 4317.191813 | 4 / 12 / 0 | 476 | 0 | 1166/226 | 3.001624 | 0 |
| 1k1k/tp8_conc4 | 2026-09-19T09:46:20.782690+00:00 → 2026-09-19T09:46:56.701186+00:00 | 40/40 | 1022.008296 | 0 / 0 / 0 | 0 | 0 | 37/1 | 2.993972 | 0 |
| 8k1k/tp4_conc4 | 2026-09-19T07:23:11.543831+00:00 → 2026-09-19T07:24:03.112256+00:00 | 40/40 | 713.711916 | 0 / 0 / 0 | 0 | 0 | 0/38 | 3.101852 | 0 |
| 8k1k/tp4_conc8 | 2026-09-19T07:28:58.991710+00:00 → 2026-09-19T07:30:15.612933+00:00 | 80/80 | 966.690386 | 0 / 0 / 0 | 0 | 0 | 0/76 | 2.961587 | 0 |
| 8k1k/tp4_conc16 | 2026-09-19T07:35:23.491268+00:00 → 2026-09-19T07:37:17.163783+00:00 | 160/160 | 1288.139000 | 0 / 0 / 0 | 0 | 0 | 0/147 | 2.964214 | 0 |
| 8k1k/tp4_conc32 | 2026-09-19T07:42:43.776832+00:00 → 2026-09-19T07:45:36.289946+00:00 | 320/320 | 1716.640510 | 0 / 0 / 0 | 0 | 0 | 0/284 | 2.975076 | 0 |
| 8k1k/tp4_conc64 | 2026-09-19T07:51:38.804680+00:00 → 2026-09-19T07:56:23.295254+00:00 | 640/640 | 2073.625821 | 0 / 0 / 0 | 0 | 3 | 0/533 | 2.976039 | 0 |
| 8k1k/tp4_conc128 | 2026-09-19T08:03:25.434191+00:00 → 2026-09-19T08:11:43.916286+00:00 | 1280/1280 | 2362.353664 | 3 / 1 / 0 | 24 | 0 | 0/888 | 2.930392 | 0 |
| 8k1k/tp4_conc256 | 2026-09-19T08:21:23.759844+00:00 → 2026-09-19T08:39:32.075416+00:00 | 2560/2560 | 2168.793740 | 9 / 12 / 0 | 666 | 0 | 2/1419 | 2.968263 | 0 |
| 8k1k/tp8_conc4 | 2026-09-19T08:45:06.096194+00:00 → 2026-09-19T08:45:49.902195+00:00 | 40/40 | 840.181697 | 0 / 0 / 0 | 0 | 0 | 0/37 | 3.004611 | 0 |

- AL is server-lifetime cumulative acceptance length, including warmup and completed reporting windows; it is not measured-only AL.
- Warmup request result objects are discarded; zero-failure claims apply to measured requests only. No accuracy evaluation was run.
- Graph counts are logged batches, not every kernel/graph invocation. Whole-second log lines overlapping a measured boundary are classified as boundary, not assigned to either phase.
- JSON retains warning/advisory/error counts by phase and physical line evidence. Untimestamped stack lines inherit the preceding log timestamp; severity counts are not unique exception counts.
- Allocator warnings can recover; successful requests do not quantify their performance impact. No causal explanation of throughput differences is established.
- Source/model/image fields are recorded artifact provenance, not fresh checksum verification. Installed package metadata may retain the base-image SGLang version.

## Invariant mismatches

None.

## Manual supplement: final TP8 shutdown

The final 1k1k TP8/C4 measurement ends at 09:46:56.701186 UTC with 40/40 successful requests. Its original `server.log` records the after-run server-info response and SIGTERM at 09:46:57 (lines 551–553), detokenizer exit -15 and SIGQUIT at 09:46:58 (lines 554–555), and no live schedulers at 09:47:03 (line 557). Final case status is completed/exit 0. The shared cleanup helper sends SIGTERM to its owned process group; the SGLang watchdog treats any nonzero child exit, including signal termination, as a child failure and triggers SIGQUIT. This sequence is a shutdown-triggered watchdog escalation after measurement.

The automated table counts literal `ERROR:` labels; it does not capture this unprefixed watchdog error message. This manual review supplements that count. Full server logs remain in the raw archive identified in [run notes](README.md); the complete logs are not error-free.

中文：最后的 1k1k TP8/C4 在 40/40 个正式请求成功后进入 SIGTERM 清理，随后子进程退出 -15 触发 watchdog 的 SIGQUIT 诊断；最终 case 退出码为 0。这是测量后的清理诊断。自动表格仅统计字面 `ERROR:` 标记，会漏掉这条无前缀消息，因此在这里补充人工核对，不能将完整日志描述为无错误。
