# GLM-5.2 MegaMoE：标称 1k 输入 / 2k 输出

[English](README.md) | **中文**

这个单节点配方在八张 B300 上执行 **24 个全新测点**，不复用上一轮 GLM-5.2 的测量结果。
两种 target 精度共用固定 FlashInfer build 与 SGLang autotune adapter，但 native kernel 和 AUTO 计时器不同。脚本不安装软件、不申请资源、
不下载模型，也不自动重试。

| 设置 | 值 |
|---|---|
| Target 精度 | NVFP4 W4A4 / W4A16；BF16 combine、外部 FC2 reduction |
| 并行 | TP = EP = DP attention = 4 或 8，单节点 |
| 客户端并发 | 每种精度/拓扑分别测试 4、8、16、32、64、128 |
| 执行顺序 | W4A4 TP4、W4A4 TP8、W4A16 TP4、W4A16 TP8；每组 **128、4、8、16、32、64** |
| 请求 | 标称输入 1024 / 输出 2048；random ratio **0.8**、seed **0**、chat template |
| 数量 | 每点 2×C warmup、10×C 测量；总计 2,016 个 warmup、10,080 个测量请求 |
| 流量/采样 | 无限到达率；当前 InferenceX 的 `vllm` HTTP client，temperature 0、ignore EOS |
| MTP | EAGLE，3 steps / top-k 1 / 4 draft tokens；原生 BF16 draft，`flashinfer_trtllm` / `none` |
| 显存/KV | 静态比例 0.80、`fp8_e4m3` KV、关闭 radix cache |
| Prefill | 全局 chunk 32768、max prefill tokens 32768、关闭 prefill CUDA graphs |
| Decode | graph max batch = C；server max running requests = max(C, DP) |
| 本机通信 | `NVSHMEM_REMOTE_TRANSPORT=none`、`NVSHMEM_IB_ENABLE_IBGDA=0`、`NVSHMEM_DISABLE_LOCAL_ONLY_PROXY=1` |

长度是标称值，未修改的 client 会处理 chat template 并抽样。比较必须读取保存的
`input_lens` / `output_lens`。同一并发在四组中必须得到完全一致的有序长度数组，否则保留原始文件并停止。
原 client 会等待 warmup 请求结束，但不导出每个 warmup 的结果；日志中的 `Warmup completed`
不能独立证明数值正确。

源码基线为 SGLang `16c1b8638b462ca1b896e2b76d5c002caf06988b`、FlashInfer
`19e8aebb541684df09e12cc79610338aa429a2cf`，镜像见 [config.example.json](config.example.json)。
实际配置必须填写已验收的完整 SHA、路径、镜像 digest 和镜像环境。
FlashInfer 使用同一完整 commit 构建并安装的 main/cubin wheel；`PYTHONPATH` 只加入 SGLang `python/`
与 InferenceX，不加入尚未构建的 FlashInfer 源码树。源码树只做来源检查，`runtime.initial.json`
校验已安装 wheel 的位置和两份完整 build commit，拒绝旧 AOT provider。
示例路径及 `LD_LIBRARY_PATH` 只是占位，不能覆盖安装时已核实的值。
每个 case 前后检查源码 HEAD、tracked diff、配方 SHA 和完整 package freeze。
脚本记录模型元数据 SHA 与所有 shard 大小；完整权重字节、GPU/镜像/拓扑验收仍由 setup 证据负责。

## 运行

先按[一次性安装说明](INSTALL_zh.md)准备并验证镜像、源码、编译依赖与固定 revision 的本地模型，组间不重新安装或构建。
复制配置到源码目录外，填写实际路径和环境，只创建 `run_root` 的父目录；`run_root` 本身不能已存在。

```bash
RECIPE=experimental/glm52_megamoe_1k2k
cp "$RECIPE/config.example.json" /data/experiments/campaign.json
# 按已核实安装编辑 campaign.json。
python3 "$RECIPE/run.py" --config /data/experiments/campaign.json --plan \
  > /data/experiments/campaign-plan.json
setsid /opt/sglang/bin/python3 -u "$RECIPE/run.py" \
  --config /data/experiments/campaign.json --run \
  > /data/experiments/campaign-worker.log 2>&1 < /dev/null &
echo "$!" > /data/experiments/campaign-worker.pid
```

外层 launcher 仍须记录 worker birth identity 和 waited exit；`worker-exit.json` 是 worker 自述，
不能代替外层 wait 返回值。读取 `progress.json` 查看已完成点，遇到不确定的启动结果不得重复派发。
SIGINT/SIGTERM 会停止当前点、清理其真实 owned 进程并退出。清理前复核 PID birth、wait 直接子进程；
若仍有 owned 进程或 GPU application，拒绝进入下一点。任何失败保留部分日志并停止整个串行 campaign。
没有 overwrite/resume 开关。

## Cache 与证据

24 个点共用 `run_root/caches/compile/`。它从空目录开始，正常 JIT 编译可以增加内容，但不清空或替换。
显式指定 SGLang JIT、DeepGEMM、CuTe AOT、FlashInfer、CuTe DSL、CUDA、Torch extensions/Inductor、
Triton、TileLang、XDG 路径。`SGLANG_CACHE_DIR` 则指向
`caches/tactics/<precision>/tp<TP>/`，形成四个隔离的 tuning namespace。
每组先跑 C128 以准备最大 decode/prefill profile，小点仍各自启动 server、warmup、测量。
必须检查日志和 tactic，不能仅凭复用目录就声称没有重新调优。

两种精度都使用现有 SGLang shared profile/cache 集成。固定 FlashInfer 源码内部，原生 W4A4 AUTO
使用同步后的 host wall time，W4A16 AUTO 使用 private CUDA graph 的 GPU event；两者均不依赖 CUPTI。
本实验保持上游实现不变，shared profile 集成不代表内部调优计时器相同。

只在 GPU idle 的 case 前及清理后记录 compile 文件 stat，并复制/哈希 tactic 文件，不扫描运行中 server 的 cache。case 失败或 owned cleanup 未完成时，跳过 after-cache 快照并记录原因。
compile stat 清单不代表完整 cache payload 已做 SHA 归档；结束后需另行保存共享 cache 树。

每个独占的 `cases/<precision>-tp<TP>-ep<EP>-dp<DP>-c<C>/` 包含：

- `settings.json`、server/client 原始 argv/environment、源码和 freeze 回执；
- server/client 完整日志、server-watch identity、birth-bound owner/cleanup 回执；
- 前后 `server_info`，含最终设置与 MTP 计数；
- 原始 `result.json`，含有序长度数组及 client 原始 scalar/tail 指标；
- 带时间的 GPU 利用率、显存、功耗和进程列表；
- idle 时的 cache 清单及 tactic 副本；
- 终态 `exit.json`，以及逐文件 size/SHA 的不可变 `manifest.json`。

只有 `exit.status == completed`、cleanup errors/remaining 为空且 manifest 匹配才是成功点；失败点也会封存 manifest。
`metrics.json` 的吞吐是 **全部测量输出 token / 完整测量墙钟区间 / 实际 TP（4 或 8）**，不是 decode 活跃阶段日志吞吐。
默认 client 保存 median/p90/p99，不导出逐请求延迟数组。stream interval 30 的 ITL 是流式 chunk 间隔，
不能当单 token TPOT。启动、调优和 graph 时间不计入吞吐。
本实验不证明输出质量或多节点安全；local-only NVSHMEM 配置要求本机 P2P 拓扑足够。
健康启动和脚本成功也不能替代首次真实测点的 profile/kernel 路径审查。

## 读取已封存结果

只将带 manifest 的终态 case 原始字节复制到本地 run 目录，并保留根目录 config/worker 回执。
读取器核对逐文件 SHA、完成与清理状态、设置、源码/freeze，以及同并发的有序长度数组。
每次调用使用新的输出目录：

```bash
python3 experimental/glm52_megamoe_1k2k/results.py \
  --run-root /data/experiments/collected-run \
  --output /data/experiments/results-partial --partial
# 全部 24 个点和 worker 均结束后：
python3 experimental/glm52_megamoe_1k2k/results.py \
  --run-root /data/experiments/collected-run \
  --output /data/experiments/results-final
```

`--partial` 只为已封存点输出表格/JSON/CSV，不生成最终图。完整模式要求 24 点 worker 终态齐全，
输出包含四条精度/拓扑 frontier 的 `pareto.png`/`pareto.svg`。两种模式均在
`raw-metrics.json`/`.csv` 中保留已保存延迟指标与原始 SHA；吞吐按完整测量区间和实际 GPU 数归一化。
这些结构校验不代替上述首次测点 kernel/profile 审查及外层 waited terminal 验收。
绘图需要本地分析环境安装 Matplotlib，不应为此更改 serving 安装。

## 本地检查与来源

```bash
python3 -B experimental/glm52_megamoe_1k2k/check.py
bash -n experimental/glm52_megamoe_1k2k/benchmark_mtp.sh
```

CPU 检查执行真实 matrix/命令/environment/result 代码，并以外部 client stub 运行 Bash bridge；
不会启动 server 或证明 GPU 性能。Server 协议改编自
[上一轮 common.sh](https://github.com/zianglih/InferenceX/blob/c1354d2e479a02632bc59b0c37c4b3f1e7a8d031/experimental/glm52_b300_fixed_seq/common.sh)，
client、抽样和指标直接复用本仓库未修改的
[benchmark_lib.sh](../../benchmarks/benchmark_lib.sh) 和 [infx/bench_serving](../../infx/bench_serving/)。
没有复制旧结果或 recovery adapter 框架。
