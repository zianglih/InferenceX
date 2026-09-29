# Kimi K3：三条 routed-NVFP4 MoE 曲线

[English](README.md) | **中文**

本实验在单节点八张B300上比较 MegaMoE W4A4、MegaMoE W4A16 和 TRTLLM per-tensor NVFP4 W4A4。它与GLM实验分开，不属于官方 InferenceX 排行榜提交。本次脚本包不包含Kimi实测结果。

所有分支使用 TP=EP=DP-attention=8、PP=DCP=1。每个分支先运行C32，再运行C4/C8/C16；名义输入1,024、输出8,192 tokens，长度范围比例0.8、seed0，使用chat template并忽略EOS。每个点预热2C、测量10C，共12个点、360次预热、1,800次测量。全部禁用MTP及外部draft model，不使用EAGLE、DSpark或接受率模拟。

共同配置为BF16执行、FP8 E4M3 KV、FP32 SSM状态、16,384 context、0.85静态显存比例和32,768全局prefill/chunk上限。关闭prefill graphs和radix cache；请求容量为max(C,8)，decode graph最大值为C。stream interval 30下的ITL表示流式chunk间隔，不是逐token TPOT。

分支只改变MoE/A2A后端，以及W4A16分支的 `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`。不额外覆盖per-token、fast-math、combine、IKR或kernel调优参数。编译缓存按顺序共享，tactic缓存按分支分开；因此这不是孤立GEMM因果实验。

## 固定来源

SGLang固定为 `561ad447c74bb757a40677ee9ce038f9ca429d2c`，FlashInfer为 `a03f2205263d4e691d68e485bff287e37a19b6c3`。完整八文件基准客户端固定为 InferenceX `652ac186d88ebcd6ff995afbe7c3094751f0f4a2`，原样附带字节清单和许可证，不替换成当前仓库版本。

镜像为 `lmsysorg/sglang:nightly-dev-cu13-20260929-79cafec0@sha256:0f075735a6bf913a7cc1cd7ece4f526ae8af70fc5b88fdc02d9efe92a61cf3ae`。原始模型为 `moonshotai/Kimi-K3` 的 `f831ab66814297da540d832a5235f8e904f29d06`，由上游 Miles `9e4260de047a704208535c0e90c531929879ab40` 将主模型routed experts按MXFP4→BF16→NVFP4转换。已验收的转换合同要求其他tensor的dtype、shape和原始字节不变。附带原始JSON仅用于来源参考。

`setup/checkpoint_contract.py` 有意固定本次已审查转换的 `main-routed-nvfp4-attempt2` 路径；中断的前一次输出不可用于服务。迁移路径或更换模型需要单独审查验收绑定及合同。仅改路径不能证明权重来源；模型加载、GPU分派、质量和性能仍需实际服务证据。

## 配置和规划

使用Python 3.12或更新版本。规划仅依赖标准库，不导入模型软件包、不联系服务端。执行依赖见 [DEPENDENCIES.md](DEPENDENCIES.md)。这些脚本不安装软件包、不下载模型、不改动源码checkout。

```sh
python3 -B setup/run_campaign.py --dry-run --campaign campaign.json \
  --output /absolute/new/kimi-plan
```

公开 `campaign.json` 保持 `PREPARE_ONLY`，使用明确的 `/REVIEW_REQUIRED/` 占位路径，不内嵌开发者工作站验收文件路径。复制为本地配置后，显式提供已验证环境的 `runtime.python`、固定源码根目录 `runtime.sglang_root` / `runtime.flashinfer_root`、全新独占 `runtime.run_root`、短于30字节且属于本次任务的 `/tmp/infx-*`。`runtime.model_path` 和 `checkpoint.output_path` 必须与固定合同一致。`checkpoint.acceptance.path` 指向准确验收文件的本地副本，保留其bytes/SHA。`--runtime-project-root` 指向远端实际暂存的脚本和vendor目录。

模板保留验收文件内容摘要，但不发布私有转换证据。执行前必须另行提供并验证这些证据。dry plan不能证明文件、权重、运行时、GPU所有权或显存容量可用。

## 执行和结果

在所属节点上使用最终 `setup/preflight.py` 和 `setup/run_campaign.py --execute` 接口，提供本次准确的preflight/approval回执。最终参数以 `--help` 为准；默认仍是dry planning。本地配置必须显式授权且没有未解决blocker。串行driver只管理自己启动的服务端和客户端，并保留来源、argv、环境、原始日志、GPU/进程所有权和封存结果。

保存不可变campaign、plan、安装来源及checkpoint证据。`setup/results.py` 只接收单独验收的完整collection：12个点、1,800次成功测量、零失败、匹配的有序长度、实际后端审查及waited terminal/cleanup证据。它不会把任意JSON目录当作实测结果。

图的X轴为 `1000 / saved median TPOT_ms`，Y轴为 `total output tokens / complete measured duration / 8`，覆盖完整测量时间而不是仅decode时间。保留全部已保存percentile，比较所有相同C的分支组合。合成fixture或源码验证不是实测结果，也不证明数值等价或统计显著性。图表及表格采用英文。

所有分支共同显式设置 `--quantization modelopt_fp4`，声明已验收 checkpoint 的格式。固定 Kimi 版本的 ModelConfig 自动识别不会传播到 Mega gate 读取的 ServerArgs，因此需要该共同声明；它不是 per-token 或 fast-math 调优覆盖。
