# GLM-5.2 EP8 C64 扩展

[English](README.md) | **中文**

此手动配方为 MegaMoE W4A4、MegaMoE W4A16 和默认 per-tensor TRTLLM W4A4 增加并发 64 的测量点，均采用 TP=EP=DP-attention=8。每点先执行 128 条计划预热，再执行 640 条测量请求。这三点扩展已单独保留的 [C1–32 实验](../glm52_six_curves_1k8k_c32/)，不会重跑或替换原有 36 点。

runner 沿用原实验的工作负载和执行逻辑：标称输入 1,024 / 输出 8,192 token、长度比例 0.8、客户端 seed 0、EAGLE 的 3 steps / top-k 1 / 4 draft tokens，以及各后端默认配置。runner 仅修改矩阵与实验标识。W4A16 也会选择符合条件的 dense NVFP4 linear。示例配置保留 SGLang `9d38e0530a1e35d1756a7fabf044bc39b77209b8`、FlashInfer `a03f2205263d4e691d68e485bff287e37a19b6c3`，以及现有 9 月 30 日 CUDA 13 镜像和 checkpoint，不执行安装。

新实验使用独立的 root、HOME、短 TMP、编译缓存和 tactic 命名空间，不使用 cache seed。三个新增点共享编译结果，tactic 按后端分开。其缓存历史与原实验后续点不同；不声明共享 provider 或系统默认缓存完全冷启动或完全隔离。

```bash
python3 experimental/glm52_ep8_c64_measured_mtp/run.py --config /absolute/path/config.json --plan
python3 experimental/glm52_ep8_c64_measured_mtp/run.py --config /absolute/path/config.json --run
```

显式提供全部配置字段。执行前检查计划、source/provider pin、专用八卡节点空闲状态，以及尚不存在的 run/TMP 路径。请求不完整、token 长度不符、原生 MTP 计数缺失或清理失败时，runner 会停止。仅测量阶段的 AL 为 `sum(completion_tokens) / sum(spec_verify_ct)`，包含原生 bonus-token 约定；接受率为 `sum(correct_drafts) / sum(proposed_drafts)`。预热请求会被调度并等待完成，随后丢弃，再采集测量计数；不保存逐条预热成功记录。

完整原始日志和验证证据保留在本地，公开内容仅包含精简表格、图和复现源代码。新增 C2–32 视图保持原数据。扩展后的合并图必须明确标注 EP4 C1–32 与 EP8 C1–64；没有 EP4 C64 测量。此手动 key 未注册到 scheduled matrix；配方准备不代表实测性能、评估、归档或清理验收通过。
