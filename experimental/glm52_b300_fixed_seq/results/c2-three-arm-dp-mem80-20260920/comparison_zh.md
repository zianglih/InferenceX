# GLM-5.2 B300：TRT-LLM、MegaMoE与CuTe split MoE

[English](comparison.md) | [中文](comparison_zh.md)

共完成48点、16组同配置三方对照，30,720个正式测量请求成功，三组均通过完整审计。原对齐配置的TRT-LLM与MegaMoE测量原样复用，仅新增CuTe测量；排除历史DP1和中断的.85结果。

主轴采用InferenceX定义：**每请求交互速度 = 1000 / median_tpot_ms**（tok/s/user），以及**output_throughput / 实际GPU数**（tok/s/GPU），均越高越好。每组前沿合并TP4和TP8选择，保留并标注所有客户端C/TP/DP/EP点；绿色虚线前沿合并三组。纵轴是整个基准测试区间内的纯输出吞吐，不是单独计时的decode阶段吞吐。[固定提交的指标、分组及前沿定义](SOURCE_METRICS_zh.md)。

三组统一TP=DP=EP、DP attention、静态显存比例.80、禁用prefill graph、server上限=max(客户端C, TP)，以及TRT-LLM/none MTP。TP8/C4的客户端C仍为4。工作负载名称表示ISL/OSL采样上限，range ratio=.8、request-rate=inf，每点测量一次，实际请求长度不必相同。TPOT中位数取自客户端记录；缺少逐请求延迟数组，不能独立重建。请求成功不代表精度评估或延迟SLO达标。

运行环境、精度/backend与FlashInfer源码差异均在下表明确列出。TRT/Mega保留原实测配置提交，CuTe使用单独固定的配置提交。这是完整服务配置比较，不是单独kernel或精度变化的加速比；Mega/CuTe比值可以小于1，变化率可以为负。

## 运行来源

| 测试组 | Run | 镜像 | SGLang | 实测InferenceX | FlashInfer版本 / 提交 | CuTe | 静态显存比例 |
|---|---|---|---|---|---|---|---|
| W4A4 TRT-LLM | c2-w4a4-trtllm-dp-mem80-20260920 | lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | 86b464d794a8804a05e0c95f679d6bb02e120889 | 0.6.18 / image-provided | 4.6.2 | 0.8 |
| W4A16 MegaMoE | c2-w4a16-megamoe-mem80-20260920 | lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | 86b464d794a8804a05e0c95f679d6bb02e120889 | 0.7.0 / ad0a5e5e78e57070ec7c582efe733cb55cd8839f | 4.7.1 | 0.8 |
| W4A16 CuTe split MoE | c2-w4a16-cutedsl-mem80-20260920 | lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | 3433a0c1169a6b162edf91c7ea193196c08a6386 | 0.7.0 / f9dd3c10541e087b716772245a9d033499745048 | 4.7.1 | 0.8 |

## 1k1k

![1k1k](figures/1k1k_output_per_gpu_vs_interactivity_pareto.png)

[SVG](figures/1k1k_output_per_gpu_vs_interactivity_pareto.svg)

## 8k1k

![8k1k](figures/8k1k_output_per_gpu_vs_interactivity_pareto.png)

[SVG](figures/8k1k_output_per_gpu_vs_interactivity_pareto.svg)

## 同配置对照

比值为相同客户端并发和拓扑下的**MegaMoE / CuTe**，变化率(%) = (比值 - 1) × 100；不做插值或固定交互速度匹配。TRT-LLM保留为参考列。

| 场景 | TP/DP/EP | C | TRT输出/GPU | Mega输出/GPU | CuTe输出/GPU | Mega/CuTe输出 × / % | TRT交互速度 | Mega交互速度 | CuTe交互速度 | Mega/CuTe交互速度 × / % |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1k1k | 4/4/4 | 4 | 132.286 | 128.056 | 119.994 | 1.067 / +6.72% | 141.276 | 137.328 | 133.955 | 1.025 / +2.52% |
| 1k1k | 4/4/4 | 8 | 208.042 | 203.410 | 199.438 | 1.020 / +1.99% | 112.531 | 109.817 | 108.476 | 1.012 / +1.24% |
| 1k1k | 4/4/4 | 16 | 327.841 | 315.064 | 308.876 | 1.020 / +2.00% | 88.190 | 85.373 | 84.482 | 1.011 / +1.05% |
| 1k1k | 4/4/4 | 32 | 489.798 | 526.362 | 472.571 | 1.114 / +11.38% | 66.163 | 71.315 | 63.163 | 1.129 / +12.91% |
| 1k1k | 4/4/4 | 64 | 679.053 | 749.323 | 643.768 | 1.164 / +16.40% | 44.277 | 49.334 | 42.193 | 1.169 / +16.92% |
| 1k1k | 4/4/4 | 128 | 1036.160 | 1072.480 | 917.364 | 1.169 / +16.91% | 33.362 | 34.659 | 29.414 | 1.178 / +17.83% |
| 1k1k | 4/4/4 | 256 | 1235.308 | 1466.501 | 1324.609 | 1.107 / +10.71% | 19.416 | 23.332 | 21.067 | 1.108 / +10.75% |
| 1k1k | 8/8/8 | 4 | 63.806 | 65.905 | 61.015 | 1.080 / +8.01% | 140.017 | 139.197 | 132.888 | 1.047 / +4.75% |
| 8k1k | 4/4/4 | 4 | 118.401 | 107.459 | 107.988 | 0.995 / -0.49% | 138.479 | 120.774 | 124.469 | 0.970 / -2.97% |
| 8k1k | 4/4/4 | 8 | 183.116 | 162.419 | 171.712 | 0.946 / -5.41% | 102.415 | 93.224 | 97.039 | 0.961 / -3.93% |
| 8k1k | 4/4/4 | 16 | 262.413 | 222.772 | 227.677 | 0.978 / -2.15% | 74.674 | 63.508 | 65.858 | 0.964 / -3.57% |
| 8k1k | 4/4/4 | 32 | 362.701 | 304.209 | 334.263 | 0.910 / -8.99% | 49.637 | 41.147 | 46.117 | 0.892 / -10.78% |
| 8k1k | 4/4/4 | 64 | 474.733 | 391.166 | 418.560 | 0.935 / -6.54% | 31.160 | 25.672 | 27.338 | 0.939 / -6.09% |
| 8k1k | 4/4/4 | 128 | 586.492 | 470.625 | 509.864 | 0.923 / -7.70% | 18.873 | 15.073 | 16.455 | 0.916 / -8.40% |
| 8k1k | 4/4/4 | 256 | 694.866 | 550.249 | 584.828 | 0.941 / -5.91% | 11.045 | 8.757 | 9.304 | 0.941 / -5.88% |
| 8k1k | 8/8/8 | 4 | 57.519 | 56.231 | 53.237 | 1.056 / +5.62% | 128.753 | 121.960 | 116.317 | 1.049 / +4.85% |

输出单位为tok/s/GPU，交互速度单位为tok/s/user；完整精度保留在配对JSON和原始指标表中。

## 审计备注与完整证据

零不变量偏差不表示日志没有警告。下方审计备注保留原文。

[首点及TP8/C4独立校准、绑定的原始文件和运行环境回执](audits/calibration/index.md)。

- w4a4_trtllm：[审计](audits/w4a4_trtllm.md)、[JSON](audits/w4a4_trtllm.json)、[全部客户端打印结果](w4a4_trtllm_raw_client_summaries.md)。
  - `1k1k/tp4_conc128`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc128`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc16`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc256`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc32`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc4`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc64`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp4_conc8`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `1k1k/tp8_conc4`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `1k1k/tp8_conc4`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc128`: Review phase-resolved error_label; measured success is not an error-free log claim
  - `8k1k/tp4_conc128`: Review phase-resolved traceback_header; measured success is not an error-free log claim
  - `8k1k/tp4_conc128`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc16`: Review phase-resolved error_label; measured success is not an error-free log claim
  - `8k1k/tp4_conc16`: Review phase-resolved traceback_header; measured success is not an error-free log claim
  - `8k1k/tp4_conc16`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `8k1k/tp4_conc32`: Review phase-resolved error_label; measured success is not an error-free log claim
  - `8k1k/tp4_conc32`: Review phase-resolved traceback_header; measured success is not an error-free log claim
  - `8k1k/tp4_conc32`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `8k1k/tp4_conc4`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `8k1k/tp4_conc64`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; distinguish teardown from measurement
  - `8k1k/tp4_conc8`: No BF16 TRTLLM kernel text; inherited native-BF16 draft route is source-derived, not a per-kernel trace
  - `8k1k/tp8_conc4`: Review phase-resolved error_label; measured success is not an error-free log claim
  - `8k1k/tp8_conc4`: Review phase-resolved traceback_header; measured success is not an error-free log claim
- w4a16_megamoe：[审计](audits/w4a16_megamoe.md)、[JSON](audits/w4a16_megamoe.json)、[全部客户端打印结果](w4a16_megamoe_raw_client_summaries.md)。
  - `1k1k/tp4_conc128`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc128`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc16`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc256`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc32`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc64`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc8`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp8_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp8_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc128`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc128`: Review phase-resolved error_label evidence; successful measurement does not make logs error-free
  - `8k1k/tp4_conc16`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc256`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc32`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc64`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc8`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp8_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp8_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
- w4a16_cutedsl：[审计](audits/w4a16_cutedsl.md)、[JSON](audits/w4a16_cutedsl.json)、[全部客户端打印结果](w4a16_cutedsl_raw_client_summaries.md)。
  - `1k1k/tp4_conc128`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc128`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc16`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc256`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc32`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc64`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp4_conc8`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `1k1k/tp8_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `1k1k/tp8_conc4`: Review phase-resolved error_label evidence; successful measurement does not make logs error-free
  - `1k1k/tp8_conc4`: Review phase-resolved traceback_header evidence; successful measurement does not make logs error-free
  - `8k1k/tp4_conc128`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc128`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc16`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc16`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc256`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc256`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc32`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc32`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc64`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc64`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp4_conc8`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp4_conc8`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures
  - `8k1k/tp8_conc4`: FLASHINFER_VERSION environment label differs from imported source version; distinguish base-image label from runtime identity
  - `8k1k/tp8_conc4`: Review phase-resolved sigquit_diagnostic; teardown diagnostics are not automatically measured failures

## 附录

[完整48点原始指标表](raw_metrics_zh.md) · [配对数值与带符号变化率](paired_comparison.json) · [选定绘图指标与E2EL附图](figures/pareto.md)。原始逐点文件保留在`runs/<run_id>/`；各run清单记录原始文件哈希，包括在精简结果包外保留的大日志与遥测。
