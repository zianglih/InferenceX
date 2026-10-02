# DeepSeek-V4.1 + DSpark：三个 EP8 后端的独立 Pareto 曲线

[English report](REPORT.md)

本实验在单台8张B300节点上比较 target MegaMoE W4A4、MegaMoE W4A16、传统TRTLLM W4A4，TP=EP=attention DP=8，C2/4/8/16/32/64。复用GLM的runner与指标定义，但新模型、prompt、draft及图表独立，不与GLM结果拼成同一条曲线。benchmark使用个人non-preempt队列的独立节点，与SGLang开发隔离。

**实际完成情况：** 18 个已验收点，3,780/3,780 条测量请求成功，测量错误为零。完成18点，756条计划且已等待的预热不进入测量统计。worker于2026-10-02 01:03:27 UTC完成全部18点；supervisor于01:03:28记录它对runner的实际wait返回0及自身终态0。01:12:08两次观测均确认全部3,911条已记录process birth和56个session不存在。此结论仅限有界的已记录owner集合，不表示连续/未知进程不存在，也不是父进程对外层supervisor的独立OS wait。18行紧凑结果、540行有符号指标、独立EP8重放与main/EP8 PNG/SVG图像审核均已通过；完整 raw 证据保留本地；归档／持久保留和节点清理需单独验收。[18-point metrics](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/raw-metrics.json) · [all saved scalars/tails](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/raw-saved-scalars.json) · [18 matched groups / 540 signed metric rows](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/paired-comparisons.csv) · [EP8 PNG](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/figures/ep8/pareto.png) · [EP8 SVG](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/figures/ep8/pareto.svg) · [replay source](results/dsv41-dspark-ep8-20261001-mxfp8-fix-v3-all18/source/experimental/dsv41_dspark_ep8/render.py)

六个并发点中，Mega W4A16 的实测每 GPU 吞吐均高于 Mega W4A4，但并非所有延迟指标均改善。C64 的三后端吞吐见完整表；有符号比较保留退化，单轮串行实验不能隔离精度或后端的因果效应。

下表仅显示舍入值；完整 JSON/CSV 保留原数值。

| Backend / 后端 | C | Measured / 测量 | Output tok/s/GPU | 1000 / median TPOT | TTFT median ms | TPOT median ms | E2EL median ms | AL | Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Mega W4A4 | 2 | 20 | 110.553 | 553.845 | 285.249 | 1.806 | 13826.148 | 4.593126 | 0.718782 |
| Mega W4A4 | 4 | 40 | 199.739 | 489.302 | 281.785 | 2.044 | 14950.746 | 4.253591 | 0.650868 |
| Mega W4A4 | 8 | 80 | 334.451 | 460.644 | 512.953 | 2.171 | 18086.335 | 4.374164 | 0.674992 |
| Mega W4A4 | 16 | 160 | 606.895 | 405.407 | 400.957 | 2.467 | 20002.697 | 4.485681 | 0.697318 |
| Mega W4A4 | 32 | 320 | 1047.878 | 334.066 | 496.242 | 2.993 | 24283.912 | 4.545689 | 0.709296 |
| Mega W4A4 | 64 | 640 | 1557.788 | 264.719 | 2420.513 | 3.778 | 31938.428 | 4.388790 | 0.677910 |
| Mega W4A16 | 2 | 20 | 122.728 | 516.892 | 298.772 | 1.935 | 14886.135 | 4.830385 | 0.766275 |
| Mega W4A16 | 4 | 40 | 208.879 | 491.916 | 289.886 | 2.033 | 15481.747 | 4.496625 | 0.699471 |
| Mega W4A16 | 8 | 80 | 352.346 | 453.145 | 470.653 | 2.207 | 17268.184 | 4.771841 | 0.754553 |
| Mega W4A16 | 16 | 160 | 635.021 | 399.236 | 303.246 | 2.505 | 20446.741 | 4.612369 | 0.722650 |
| Mega W4A16 | 32 | 320 | 1064.911 | 315.449 | 565.099 | 3.170 | 25218.250 | 4.714787 | 0.743117 |
| Mega W4A16 | 64 | 640 | 1627.940 | 253.472 | 2221.999 | 3.945 | 32776.007 | 4.665568 | 0.733273 |
| TRT W4A4 | 2 | 20 | 94.942 | 467.710 | 313.444 | 2.138 | 16240.234 | 4.248575 | 0.649884 |
| TRT W4A4 | 4 | 40 | 198.718 | 464.568 | 304.303 | 2.153 | 16638.532 | 4.733598 | 0.746905 |
| TRT W4A4 | 8 | 80 | 352.820 | 437.299 | 299.521 | 2.287 | 17854.400 | 4.689910 | 0.738122 |
| TRT W4A4 | 16 | 160 | 577.451 | 380.220 | 545.828 | 2.630 | 21519.406 | 4.615761 | 0.723319 |
| TRT W4A4 | 32 | 320 | 977.192 | 298.422 | 389.568 | 3.351 | 26711.382 | 4.695072 | 0.739175 |
| TRT W4A4 | 64 | 640 | 1388.839 | 221.203 | 2191.424 | 4.521 | 37560.065 | 4.688657 | 0.737896 |

有符号变化为 `(comparison / baseline − 1) × 100`；延迟负值表示更低延迟，所有保存尾部均保留在完整比较表中。

| Comparison / baseline | C | Output/GPU Δ | Interactivity Δ | AL Δ | Median TPOT Δ | Median TTFT Δ | p99 TTFT Δ | Median E2EL Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Mega W4A16 / Mega W4A4 | 2 | +11.01% | -6.67% | +5.17% | +7.15% | +4.74% | -73.77% | +7.67% |
| Mega W4A4 / TRT W4A4 | 2 | +16.44% | +18.42% | +8.11% | -15.55% | -9.00% | +269.43% | -14.86% |
| Mega W4A16 / TRT W4A4 | 2 | +29.27% | +10.52% | +13.69% | -9.51% | -4.68% | -3.09% | -8.34% |
| Mega W4A16 / Mega W4A4 | 4 | +4.58% | +0.53% | +5.71% | -0.53% | +2.87% | +360.68% | +3.55% |
| Mega W4A4 / TRT W4A4 | 4 | +0.51% | +5.32% | -10.14% | -5.05% | -7.40% | +21.27% | -10.14% |
| Mega W4A16 / TRT W4A4 | 4 | +5.11% | +5.89% | -5.01% | -5.56% | -4.74% | +458.67% | -6.95% |
| Mega W4A16 / Mega W4A4 | 8 | +5.35% | -1.63% | +9.09% | +1.65% | -8.25% | +43.70% | -4.52% |
| Mega W4A4 / TRT W4A4 | 8 | -5.21% | +5.34% | -6.73% | -5.07% | +71.26% | -44.62% | +1.30% |
| Mega W4A16 / TRT W4A4 | 8 | -0.13% | +3.62% | +1.75% | -3.50% | +57.14% | -20.42% | -3.28% |
| Mega W4A16 / Mega W4A4 | 16 | +4.63% | -1.52% | +2.82% | +1.55% | -24.37% | +14.58% | +2.22% |
| Mega W4A4 / TRT W4A4 | 16 | +5.10% | +6.62% | -2.82% | -6.21% | -26.54% | -21.68% | -7.05% |
| Mega W4A16 / TRT W4A4 | 16 | +9.97% | +5.00% | -0.07% | -4.76% | -44.44% | -10.26% | -4.98% |
| Mega W4A16 / Mega W4A4 | 32 | +1.63% | -5.57% | +3.72% | +5.90% | +13.88% | -23.33% | +3.85% |
| Mega W4A4 / TRT W4A4 | 32 | +7.23% | +11.94% | -3.18% | -10.67% | +27.38% | -6.72% | -9.09% |
| Mega W4A16 / TRT W4A4 | 32 | +8.98% | +5.71% | +0.42% | -5.40% | +45.06% | -28.48% | -5.59% |
| Mega W4A16 / Mega W4A4 | 64 | +4.50% | -4.25% | +6.31% | +4.44% | -8.20% | +20.02% | +2.62% |
| Mega W4A4 / TRT W4A4 | 64 | +12.16% | +19.67% | -6.40% | -16.44% | +10.45% | -34.55% | -14.97% |
| Mega W4A16 / TRT W4A4 | 64 | +17.22% | +14.59% | -0.49% | -12.73% | +1.40% | -21.44% | -12.74% |

以下 AL 汇总仅累加测量 completion/verify 分母，不平均各点 AL，也不代表汇总吞吐。

| Backend | AL range across six points | Summed completion tokens | Summed verify count | Denominator-weighted AL |
|---|---:|---:|---:|---:|
| Mega W4A4 | 4.253591–4.593126 | 9,305,531 | 2,096,892 | 4.437773 |
| Mega W4A16 | 4.496625–4.830385 | 9,305,531 | 1,990,579 | 4.674786 |
| TRT W4A4 | 4.248575–4.733598 | 9,305,531 | 1,990,578 | 4.674788 |

- **负载与顺序：** 名义输入1,024/输出8,192、ratio 0.8、seed 0、greedy、ignore EOS、无限到达率、stream interval 30；每点`2C`预热后`10C`测量，每点重启server。先按Mega W4A4、Mega W4A16、TRT W4A4执行三个C2，再按同一后端顺序分别执行C4/8/16/32/64。相同C的请求/完成长度数组必须跨后端一致。预热会等待完成，但沿用客户端不逐条强制预热响应成功。


| 三后端共同声明/解析设置 | 全18点实际值 |
|---|---|
| TP / EP / attention DP；attention TP | 8 / 8 / 8；1 |
| 声明dtype / 解析KV dtype | bfloat16 / fp8_e4m3 |
| attention选择 | dsv4；dsv4_attn_backend=auto |
| target / draft quantization参数字段 | null / null（checkpoint/config原生选择，不表示模型未量化） |
| memory fraction / radix / prefill graphs | 0.80 / disabled / disabled |
| 声明global chunk / 解析每DP chunk | 32768 / 4096 |
| max_prefill_tokens / stream interval | 32768 / 30 |
| 每DP请求池 | max(C,8)/8；graph batch取实际保存配置 |
| DSpark block / target verify / draft width | 5 / 6 / 5 |
| DP LM head | enabled |

- **精度与范围：** target routed experts为NVFP4，dense等路径保留原生混合精度，包含MXFP8；W4A16 selector也影响符合条件的NVFP4 linear。内置DSpark draft在三个后端中均为原生MXFP4/MXFP8，使用`flashinfer_mxfp4`/A2A `none`，并非全BF16。传统target为`flashinfer_trtllm_routed`/`none`，Mega target的runner/A2A均为`flashinfer_megamoe`；不加入额外per-token、quantization-fast-math、combine或IKR覆盖。
- **文本与推测解码：** 三个后端均显式设置`vision_n_layers:0`，不改原始checkpoint，使用V4.1 chat mode与`reasoning_effort=None`；不声明多模态或生成image token时等价。DSpark block size 5、verify width 6，显式DP LM head及static ragged verify。
- **统计：** AL为全部成功测量请求的`sum(completion_tokens)/sum(spec_verify_ct)`，包含bonus token。rate为`sum(correct_drafts)/(5*sum(spec_verify_ct))`，分母是配置proposal budget，并非实际ragged验证槽位数。每条测量请求要求原生计数；预热和server lifetime/window平均值不进入统计。x=`1000/median_tpot_ms`，y=`测量输出token/完整测量区间/8`；ITL表示interval 30的chunk间隔。保留已存标量延迟尾部和有符号差值，不重建缺失的逐请求延迟或未保存百分位。
- **JIT与缓存：** 首个已验收Mega W4A4 C2点的测量区间内，10月1日19:46:05 UTC报告一次5.93s非cache-hit Triton编译；不扣除时间。日志时间仅为秒级报告时间，不是精确编译起止跟踪。因此不声明完全预编译的稳态比较。新HOME/TMP/compiler/tactic目录无seed，同一串行实验共享编译缓存、后端分开tactics；不声称provider/default缓存冷启动或隔离。单轮顺序/缓存差异不能证明因果或统计显著性。
- **原生cache字段：** 首个Mega W4A4 C2的实际runtime和外层geometry均为`apply_topk_in_fc1=True`；native writer/lookup遗漏可选参数，entry因默认值写成`False`。读取只返回knobs，已保存knobs不覆盖实际flag；不能用该native字段单独判断routing weight位置。其余各点均已结合各自保存的profile独立审核。
- **C16 cache历史：** 已验收的Mega W4A4 C16实际target Mega profiles为capacity `1/2/4/8/12/4096`，其中`8/12`为新调优，`6`仅作为此前点的历史记录留在target保存的并集中。八个draft snapshot在加载各自cache后，均逐字节保留此前target Mega namespace `1/2/4/6/4096`。这些继承记录不必覆盖当前target profiles，也不代表draft使用MegaMoE。当前target profiles与独立原生MXFP4 draft profiles（`1/2/4/8/16/32/64/128`）已按角色结合保存记录、runtime配置和graph日志审核；snapshot不能证明每次serving kernel dispatch，也不能据此声称所有tactics均复用。
- **C64清理限定：** 已验收Mega W4A4 C64的client和server均有waited exit0，但10月1日21:59:32 UTC原始`gpu.after`仍非idle；冻结的owner/GPU helper因此检查失败，该失败保留。另行审核的21:59:35下一点启动前snapshot显示同一组八张GPU UUID均为零显存、零利用率、无compute application，早于21:59:37下一server启动。它仅证明稍后的idle状态，不改写原snapshot，也不推断两次读数差异的原因。该稍后idle证据已逐字节匹配下一已封存Mega W4A16 C4启动前回执；整个campaign终态已另行审核，见上述完成说明。
- **最后TRT C64 owner范围：** case-only helper因终态collection含3,558条已记录birth联合集、而非仅33条本case birth而拒绝，原失败保留。独立addendum验证33条均包含、保存联合集检查及GPU时序；不把原helper改称通过。supervisor回执记录它对runner的实际wait，不等于父进程对supervisor的独立OS wait。
- **环境与修正：** 精确pin见英文表。FI仅替换一个已审Python文件以保守收紧FP8 narrow-N tactic支持域；原wheel/build metadata、cubin/NCCL payload不变，不声称重建wheel或安装目录等于RECORD。启动前38项已安装回归测试通过（34项策略、4项GPU）；原14行依赖冲突/缺失依赖记录保留，不声明依赖环境完全干净。
- **checkpoint与历史：** 上游index声明payload为510,286,023,000B，tensor header描述527,273,322,840B，相差16,987,299,840B。原index/权重未改；严格metadata检查原失败保留，后续验收保留84文件SHA及48个tensor文件/header验证。此前vision/A2A及MXFP8启动失败没有进入测量结果，完整证据留本地。client exit0后server因清理exit−9不等于优雅退出；最终归档、持久保留和节点清理单独验收。

紧凑文件只提供表格算术和绘图重放，不能替代私有raw/native/terminal验收。使用英文命令可重绘EP8视图；main view由独立presentation projection重绘，并保持指标、AL、坐标及frontier成员不变。已验收的presentation后继仅调整标注位置，保持18行指标、540行有符号比较、AL、坐标和frontier成员不变；每个后端均有六个非支配点。独立EP8重放的point/frontier逐字节一致。root检查了main/EP8 PNG和完整浏览器SVG视图，18个C/AL标注均可读；无DejaVu Sans时SVG查看器可使用已有字体替代。完整 raw 证据保留本地；归档／持久保留和节点清理需单独验收。吞吐和AL不证明输出质量，也不证明与GLM/MTP等价。完整日志、请求数组、native明细和checkpoint不上传GitHub。
