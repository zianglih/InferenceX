# Kimi K3：三条 routed-NVFP4 MoE 曲线

[English](README.md) | **中文**

本实验在单节点八张 B300 上比较 MegaMoE W4A4、MegaMoE W4A16 和 TRTLLM per-tensor NVFP4 W4A4。它与 GLM 实验分开，不属于官方 InferenceX 排行榜提交。本次仅发布与冻结 R5 continuation 对齐的脚本，不包含 Kimi 实测结果。此前 R4 的一个 C32 测试点已验收（1/12），随后 R4 在 C4 端口绑定时失败。R5 已启动剩余十一个测试点，其结果仍待完成。启动证据不表示 continuation 已就绪、显存可容纳或性能已验收；所有历史失败均保留。

**尚未公开的集成是必要前置条件：**仅有 SGLang 基线 `561ad447` 不支持本配方已审查的 DP1/SP MegaMoE 路径。所需三个文件的修改仍仅保存在本地，未暂存、提交或发布。公开包只提供 `setup/source_contract.py` 与精确文件/diff 描述符，不包含补丁或 SGLang 源码。因此，只有单独在本地提供这些已审查字节后，dry plan 才能通过。本 draft 尚非独立可复现包，不能描述为仅靠未修改上游源码即可运行。

所有分支使用 TP=EP=8、DP=1、attention TP=8、禁用 DP attention、PP=DCP=1。每个分支先运行C32，再运行C4/C8/C16；名义输入1,024、输出8,192 tokens，长度范围比例0.8、seed0，使用chat template并忽略EOS。每个点预热2C、测量10C，共12个点、360次预热、1,800次测量。全部禁用MTP及外部draft model，不使用EAGLE、DSpark或接受率模拟。

共同配置为BF16执行、FP8 E4M3 KV、FP32 SSM状态、16,384 context、0.85静态显存比例和32,768全局prefill/chunk上限。关闭prefill graphs和radix cache；请求容量为 C，decode graph 最大值为 max(C,8)。stream interval 30下的ITL表示流式chunk间隔，不是逐token TPOT。

分支只改变MoE/A2A后端，以及W4A16分支的 `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`。不额外覆盖per-token、fast-math、combine、IKR或kernel调优参数。编译缓存按顺序共享，tactic缓存按分支分开；因此这不是孤立GEMM因果实验。

## 固定来源

SGLang 基线固定为 `561ad447c74bb757a40677ee9ce038f9ca429d2c`，还需要单独审查且尚未公开的三个文件集成。对应 binary diff 为 6,993 字节，SHA256 `d4bdb5246dbeaca7bf23472cbae617b434bcb3b77c248d0e40e46b8405786ef1`。`setup/source_contract.py` 要求精确 HEAD、修改文件集合、文件及 diff 字节，并要求 index 和 untracked 集合为空，不接受任意 dirty checkout。FlashInfer为 `a03f2205263d4e691d68e485bff287e37a19b6c3`。完整八文件基准客户端固定为 InferenceX `652ac186d88ebcd6ff995afbe7c3094751f0f4a2`，原样附带字节清单和许可证，不替换成当前仓库版本。

镜像为 `lmsysorg/sglang:nightly-dev-cu13-20260929-79cafec0@sha256:0f075735a6bf913a7cc1cd7ece4f526ae8af70fc5b88fdc02d9efe92a61cf3ae`。原始模型为 `moonshotai/Kimi-K3` 的 `f831ab66814297da540d832a5235f8e904f29d06`，由上游 Miles `9e4260de047a704208535c0e90c531929879ab40` 将主模型routed experts按MXFP4→BF16→NVFP4转换。已验收的转换合同要求其他tensor的dtype、shape和原始字节不变。附带原始JSON仅用于来源参考。

`setup/checkpoint_contract.py` 有意固定本次已审查转换的 `main-routed-nvfp4-attempt2` 路径；中断的前一次输出不可用于服务。迁移路径或更换模型需要单独审查验收绑定及合同。仅改路径不能证明权重来源；模型加载、GPU分派、质量和性能仍需实际服务证据。

## 配置和规划

使用Python 3.12或更新版本。规划仅依赖标准库，不导入模型软件包、不联系服务端。执行依赖见 [DEPENDENCIES.md](DEPENDENCIES.md)。这些脚本不安装软件包、不下载模型、不改动源码checkout。

规划也会核验本地集成字节。请仅在**私有本地副本**中单独提供 `campaign.json.local_changes.sglang` 指定的 `artifacts/sglang-dp1.patch` 和三个 `sglang/python/...` 文件；它们不随公开包发布。`runtime.sglang_root` 指向的实际服务 checkout 也须满足同一精确守卫。此处不提供获取或发布该本地集成的命令。满足此前置条件后，接口为：

```sh
python3 -B setup/run_campaign.py --dry-run --campaign campaign.json \
  --output /absolute/new/kimi-plan
```

公开 `campaign.json` 保持状态 `PUBLIC_RECIPE_REQUIRES_LOCAL_PREFLIGHT` 和授权字段 `PREPARE_ONLY`；这些公开占位值与不可变的实际 R5 配置分开，使用明确的 `/REVIEW_REQUIRED/` 占位路径，不内嵌开发者工作站验收文件路径。复制为本地配置后，显式提供已验证环境的 `runtime.python`、固定源码根目录 `runtime.sglang_root` / `runtime.flashinfer_root`、全新独占 `runtime.run_root`、短于30字节且属于本次任务的 `/tmp/infx-*`。`runtime.model_path` 和 `checkpoint.output_path` 必须与固定合同一致。`checkpoint.acceptance.path` 指向准确验收文件的本地副本，保留其bytes/SHA。`--runtime-project-root` 指向远端实际暂存的脚本和vendor目录。

模板保留验收文件内容摘要，但不发布私有转换证据。执行前必须另行提供并验证这些证据。dry plan不能证明文件、权重、运行时、GPU所有权或显存容量可用。

## 从一个已验收测试点继续

标准矩阵仍包含十二个测试点、360 次 warmup 和 1,800 次测量。`continuation.execution_case_ids` 精确选择剩余十一点：W4A4 C4/C8/C16，随后 W4A16 C32/C4/C8/C16，再运行 TRTLLM C32/C4/C8/C16。本次执行 296 次 warmup 和 1,480 次测量。preflight 仍检查每个分支的标准 C32 配置；worker 和 outer terminal 只能记录实际执行的十一点。

必须另行提供两个经过审查的实际输入：`continuation.prior_acceptance` 绑定 `ACCEPTED_KIMI_PRIOR_C32_FOR_CONTINUATION`，`continuation.cache_seed_acceptance` 绑定 `ACCEPTED_KIMI_QUIESCENT_CACHE_SEED`。公开描述符只是待提供的占位值，不构成批准。prior receipt 绑定十四个不可变 JSON，包括已验收的 native/settings/workload 审查、原 C32 有序数组、来源和缓存关系、R4 失败 terminal。它只验收该测试点，不验收原扫描；runner 以这些精确数组初始化 C32 长度参考。

经过审查的 seed 在全新自有目录中恢复 compilation、HF 和 TMP 文件，不使用硬链接，保留原缓存。新的 TMP owner 保持不变；只允许明确审查过的历史 marker/IPC 排除。完整安装清单另存，并由紧凑回执绑定。没有空缓存回退；字节保留也不保证依赖路径的缓存命中。`cache_seed.py` 有意固定此配方的 R4、R5 和 seed 路径；任意迁移需单独审查合同。公开路径占位值必须与这些守卫一致，不能随意改成可用目录。

普通端口绑定仅对 `EADDRINUSE` 最多重试 120 秒，记录墙钟和单调时钟耗时，不使用 `SO_REUSEADDR`。其他错误或持续占用均失败；等待成功后再次核验 source/runtime/checkpoint/GPU。该处理不证明 R4 原端口占用的原因。

完整结果必须使用 `ACCEPTED_COMPOSITE_CAMPAIGN`：一个已验收 R4 点、十一个已验收 R5 点、实际成功的十一点 terminal，以及独立 composite 审查。`prior_binding_map` 只按相同 bytes/SHA 迁移不可变父证据和完整安装清单。reader 拒绝虚构的单次十二点成功 terminal，也拒绝将普通完整扫描回执用于 continuation。图表和报告标明两个执行阶段。本包不发布原始结果或验收回执。

## 执行和结果

runner 按 DP1 校验一个 `internal_states` 条目，不再因为有八张 GPU 就要求八个条目；每个条目的容量和 speculation，以及 HTTP readback 前后的自有 endpoint 检查均保留。物理 GPU 身份和吞吐量归一化仍使用八卡。

在所属节点上使用最终 `setup/preflight.py` 和 `setup/run_campaign.py --execute` 接口，提供本次准确的preflight/approval回执。最终参数以 `--help` 为准；默认仍是dry planning。本地配置必须显式授权且没有未解决blocker。串行driver只管理自己启动的服务端和客户端，并保留来源、argv、环境、原始日志、GPU/进程所有权和封存结果。

保存不可变campaign、plan、安装来源及checkpoint证据。`setup/results.py` 只接收单独验收的 composite collection：12 个点、1,800 次成功测量、测量请求零失败、匹配的有序长度、实际后端审查及 waited terminal/cleanup 证据。原失败扫描仍保留为失败。它不会把任意JSON目录当作实测结果。

图的X轴为 `1000 / saved median TPOT_ms`，Y轴为 `total output tokens / complete measured duration / 8`，覆盖完整测量时间而不是仅decode时间。保留全部已保存percentile，比较所有相同C的分支组合。合成fixture或源码验证不是实测结果，也不证明数值等价或统计显著性。图表及表格采用英文。

所有分支共同显式设置 `--quantization modelopt_fp4`，声明已验收 checkpoint 的格式。固定 Kimi 版本的 ModelConfig 自动识别不会传播到 Mega gate 读取的 ServerArgs，因此需要该共同声明；它不是 per-token 或 fast-math 调优覆盖。

## 本地验证范围

公开包的 preflight 和 continuation CPU 测试使用合成输入，不需要未公开集成：

```sh
python3 -B -m unittest discover -s setup -p test_preflight.py -v
python3 -B -m unittest discover -s setup -p test_continuation.py -v
```

依赖 plan 的测试、reader 来源 fixture 及完整 runner suite 仍需精确本地集成文件，应在满足前置条件后的私有副本运行。发布验证另行确认不完整公开包的 dry run 会在输出 plan 前拒绝，并对准确的 R5 实现检查 DP1/DP8 endpoint 数量、错误数量、容量、speculation 和 owner 失败路径。合成 fixture 不属于 benchmark 结果。

公开 preflight 测试删除一个旧 AST 抽取测试以符合仓库规范；production preflight 和其他运行脚本仍保持 R5 精确字节，私有历史验证保留。

continuation 的 pending-parent 测试显式构造待验收 fixture；composite reader fixture 均为合成输入，不可当作测量发布。
