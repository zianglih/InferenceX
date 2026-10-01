# GLM-5.2 EP8 C64 extension

**English** | [中文](README_zh.md)

This manual recipe adds concurrency 64 for MegaMoE W4A4, MegaMoE W4A16 and default per-tensor TRTLLM W4A4, each at TP=EP=DP-attention=8. Each case schedules 128 warmups followed by 640 measured requests. The three points extend the separately preserved [C1–32 campaign](../glm52_six_curves_1k8k_c32/); they do not rerun or replace those 36 points.

The [completed 39-point report](results/2026-10-01-measured-mtp-39points/README.md) combines the original 36 points with all three C64 cases: 5,700 successful measured requests, zero measured failures, and 1,140 scheduled warmups. It includes combined and per-topology plots, compact tables and public plotting commands. The original C2–32 view remains unchanged.

The runner preserves that campaign's workload and execution logic: nominal 1,024 input / 8,192 output tokens, length ratio 0.8, client seed 0, EAGLE with 3 steps / top-k 1 / 4 draft tokens, and backend defaults. The only runner changes are the matrix and campaign identity. W4A16 also selects eligible dense NVFP4 linears. The example config retains SGLang `9d38e0530a1e35d1756a7fabf044bc39b77209b8`, FlashInfer `a03f2205263d4e691d68e485bff287e37a19b6c3`, and the existing September 30 CUDA 13 image and checkpoint; it installs nothing.

Each run owns a new root, HOME, short TMP, compile and tactic namespaces. No cache seed is used; compilation is shared among the three new cases, while tactics are separated by backend. This cache history differs from later points in the completed campaign. Shared provider/system-default caches are not claimed cold or isolated.

```bash
python3 experimental/glm52_ep8_c64_measured_mtp/run.py --config /absolute/path/config.json --plan
python3 experimental/glm52_ep8_c64_measured_mtp/run.py --config /absolute/path/config.json --run
```

Supply all config fields explicitly. Inspect the plan, confirm source/provider pins and an idle dedicated eight-GPU node, and use exclusive run/TMP paths before executing. The runner fails closed on incomplete requests, token-length mismatches, missing native MTP counters or cleanup failures. The measured-only acceptance length is `sum(completion_tokens) / sum(spec_verify_ct)` including the native bonus-token convention; acceptance rate is `sum(correct_drafts) / sum(proposed_drafts)`. Warmups are scheduled and awaited, then discarded before measured counters are collected; individual warmup success records are not saved.

Full raw logs and validation evidence remain local. Public publication contains compact tables, plots and reproduction sources. The additional C2–32 view retains the original data. An extended combined plot must identify EP4 C1–32 and EP8 C1–64 explicitly; there are no EP4 C64 measurements. This manual key is not registered in the scheduled matrix. Preparing this recipe does not establish measured performance, evaluation, preservation or cleanup acceptance.
