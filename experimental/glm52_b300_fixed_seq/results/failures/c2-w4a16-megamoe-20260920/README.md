# MegaMoE memory-fraction-0.85 attempt: preserved warmup failure

**English** | [中文](README_zh.md)

This is failure evidence, not a throughput observation. In run `c2-w4a16-megamoe-20260920`,
8k1k TP4/DP4/EP4 at client concurrency256 failed during the512-request warmup.
The main2560-request measurement never began and `result.json` does not exist;
null completed/failed counts must not be interpreted as measured request failures.
The preceding six points (C4–128) completed2520 measured requests and remain in
the full archived attempt, separate from the fresh memory-fraction-0.80 comparison.

At07:37:44UTC, the native MTP BF16 TRT-LLM `Bf16MoeLauncher::prepare_moe` failed to
allocate3.16GiB with1.37GiB free on GPU3. The stack runs through
`_draft_extend_for_prefill`, NextN and `trtllm_bf16_moe`. This was a fatal warmup
OOM followed by scheduler exit−3 and SIGQUIT, not an ordinary post-measurement cleanup.
The sweep and serial follow-up exited1; no provider restoration or TRT-LLM control began.

[Original status](8k1k/w4a16-megamoe/tp4_conc256/status.json),
[server log](8k1k/w4a16-megamoe/tp4_conc256/server.log),
[client log](8k1k/w4a16-megamoe/tp4_conc256/benchmark.log),
[command](8k1k/w4a16-megamoe/tp4_conc256/server_command.sh), and
[byte-preservation manifest](manifest.json) are retained. The case files are unchanged.
The full seven-case incomplete attempt and original environment/knobs remain on
persistent storage and in a verified local archive:
`c2-w4a16-megamoe-20260920-incomplete-oom.tar.gz`,
SHA256 `fd18815af835bdc62d659bd8f0ea7bacb7136d465e2d7ecc9647eaf59880d145`.

Recovery: use `mem_fraction_static=0.80` for both fresh full16-point arms, preserving
TP=DP=EP, MTP TRT-LLM/none, disabled prefill graphs, workloads, request counts,
source pins and each arm's providers. Run C256 first. No old0.85 point is reused
in the new main comparison; the reduced-memory profile still requires runtime validation.
