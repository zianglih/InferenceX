# MegaMoE 显存比例0.85：保留 warmup 失败现场

[English](README.md) | **中文**

这是失败证据，不是吞吐测点。`c2-w4a16-megamoe-20260920` 的8k1k、
TP4/DP4/EP4、client concurrency256在512请求的warmup阶段失败，
正式2560请求测量尚未开始，没有`result.json`；不能把null计数解释为实测请求失败数。
此前C4–128六点共完成2520个正式请求，完整原始记录单独归档，不混入新的0.80比较。

07:37:44UTC，原生MTP BF16 TRT-LLM `Bf16MoeLauncher::prepare_moe`尝试申请
3.16GiB，GPU3仅剩1.37GiB。堆栈经过`_draft_extend_for_prefill`、NextN和
`trtllm_bf16_moe`，随后scheduler exit−3与SIGQUIT。这是warmup中的fatal OOM，
不是测量完成后的清理信息。Sweep和串行后续任务均exit1；尚未恢复包或启动TRT-LLM对照。

[原始状态](8k1k/w4a16-megamoe/tp4_conc256/status.json)、
[server日志](8k1k/w4a16-megamoe/tp4_conc256/server.log)、
[client日志](8k1k/w4a16-megamoe/tp4_conc256/benchmark.log)、
[启动命令](8k1k/w4a16-megamoe/tp4_conc256/server_command.sh)及
[原始文件哈希](manifest.json)均保留，case文件未改动。
完整七点未完成run、原环境和knobs已在持久目录及本地归档核对SHA256：
`c2-w4a16-megamoe-20260920-incomplete-oom.tar.gz`，
`fd18815af835bdc62d659bd8f0ea7bacb7136d465e2d7ecc9647eaf59880d145`。

恢复方案：新两组均使用`mem_fraction_static=0.80`与新run ID，完整重跑各16点，
优先C256；保持TP=DP=EP、MTP TRT-LLM/none、关闭prefill graph、workload、
请求数、源码pin及各自依赖。新主图不复用旧0.85测点，降低显存比例后的运行验证仍待完成。
