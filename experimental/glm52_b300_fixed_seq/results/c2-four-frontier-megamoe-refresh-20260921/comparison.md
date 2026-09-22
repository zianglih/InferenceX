# R8 comparison

[English](comparison.md) | [简体中文](comparison_zh.md)

Status: FINAL; local assembly; no publication.

| Scenario / TP / C | Arm | Output tok/s/GPU | Interactivity tok/s/user | Median E2EL s | Run | SG | FI | Native configuration |
|---|---|---:|---:|---:|---|---|---|---|
| 1k1k / 4 / 4 | W4A4 TRT-LLM | 132.285868 | 141.276142 | 6.870054 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 1k1k / 4 / 4 | W4A16 MegaMoE | 132.624042 | 141.484371 | 6.740176 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 1k1k / 4 / 4 | W4A16 CuTe split MoE | 119.994486 | 133.954517 | 7.407418 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 1k1k / 4 / 8 | W4A4 TRT-LLM | 208.041505 | 112.530877 | 8.665450 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 1k1k / 4 / 8 | W4A16 MegaMoE | 213.891324 | 115.006958 | 8.601009 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 1k1k / 4 / 8 | W4A16 CuTe split MoE | 199.437557 | 108.475815 | 9.154440 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 1k1k / 4 / 16 | W4A4 TRT-LLM | 327.841154 | 88.189992 | 10.736126 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 1k1k / 4 / 16 | W4A16 MegaMoE | 330.158865 | 89.393468 | 10.836418 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 1k1k / 4 / 16 | W4A16 CuTe split MoE | 308.876334 | 84.481959 | 11.447017 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 1k1k / 4 / 32 | W4A4 TRT-LLM | 489.798147 | 66.162738 | 14.610118 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 1k1k / 4 / 32 | W4A16 MegaMoE | 510.972458 | 68.875882 | 14.062017 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 1k1k / 4 / 32 | W4A16 CuTe split MoE | 472.571489 | 63.163355 | 15.191481 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 1k1k / 4 / 64 | W4A4 TRT-LLM | 679.052549 | 44.276952 | 21.360301 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 1k1k / 4 / 64 | W4A16 MegaMoE | 748.100647 | 49.138232 | 19.427673 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 1k1k / 4 / 64 | W4A16 CuTe split MoE | 643.768015 | 42.193209 | 22.554736 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 1k1k / 4 / 128 | W4A4 TRT-LLM | 1036.160466 | 33.362347 | 28.202114 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 1k1k / 4 / 128 | W4A16 MegaMoE | 1047.430106 | 33.405298 | 28.138842 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 1k1k / 4 / 128 | W4A16 CuTe split MoE | 917.363631 | 29.413951 | 31.924892 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 1k1k / 4 / 256 | W4A4 TRT-LLM | 1235.308464 | 19.416322 | 48.401589 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 1k1k / 4 / 256 | W4A16 MegaMoE | 1354.029495 | 21.419275 | 43.820170 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 1k1k / 4 / 256 | W4A16 CuTe split MoE | 1324.608983 | 21.066775 | 44.643512 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 1k1k / 8 / 4 | W4A4 TRT-LLM | 63.806441 | 140.017300 | 6.946582 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 1k1k / 8 / 4 | W4A16 MegaMoE | 70.643929 | 150.044449 | 6.487544 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 1k1k / 8 / 4 | W4A16 CuTe split MoE | 61.015383 | 132.888160 | 7.240865 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 8k1k / 4 / 4 | W4A4 TRT-LLM | 118.400751 | 138.478648 | 7.491098 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 8k1k / 4 / 4 | W4A16 MegaMoE | 114.125565 | 131.230909 | 7.684169 | c2-w4a16-megamoe-autotune-20260921-recovery1 | 6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2 | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-original-proxy; immutable recovery1 |
| 8k1k / 4 / 4 | W4A16 CuTe split MoE | 107.988076 | 124.468965 | 8.151893 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 8k1k / 4 / 8 | W4A4 TRT-LLM | 183.116052 | 102.415418 | 9.861833 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 8k1k / 4 / 8 | W4A16 MegaMoE | 178.951885 | 100.653943 | 10.148768 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 8k1k / 4 / 8 | W4A16 CuTe split MoE | 171.711571 | 97.038671 | 10.350561 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 8k1k / 4 / 16 | W4A4 TRT-LLM | 262.413468 | 74.674299 | 13.361232 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 8k1k / 4 / 16 | W4A16 MegaMoE | 248.455324 | 70.537661 | 14.032861 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 8k1k / 4 / 16 | W4A16 CuTe split MoE | 227.676571 | 65.858361 | 15.383346 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 8k1k / 4 / 32 | W4A4 TRT-LLM | 362.701097 | 49.637475 | 20.080954 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 8k1k / 4 / 32 | W4A16 MegaMoE | 335.827591 | 45.527189 | 21.514080 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 8k1k / 4 / 32 | W4A16 CuTe split MoE | 334.263405 | 46.116767 | 21.222861 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 8k1k / 4 / 64 | W4A4 TRT-LLM | 474.733110 | 31.159667 | 30.766821 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 8k1k / 4 / 64 | W4A16 MegaMoE | 435.387470 | 28.433077 | 33.932730 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 8k1k / 4 / 64 | W4A16 CuTe split MoE | 418.559512 | 27.337966 | 34.934651 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 8k1k / 4 / 128 | W4A4 TRT-LLM | 586.492224 | 18.872581 | 50.074805 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 8k1k / 4 / 128 | W4A16 MegaMoE | 518.027957 | 16.572426 | 57.230492 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 8k1k / 4 / 128 | W4A16 CuTe split MoE | 509.863807 | 16.455060 | 57.696174 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 8k1k / 4 / 256 | W4A4 TRT-LLM | 694.865552 | 11.045281 | 85.635248 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 8k1k / 4 / 256 | W4A16 MegaMoE | 591.458530 | 9.345877 | 100.991660 | c2-w4a16-megamoe-autotune-20260921-recovery1 | 6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2 | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-original-proxy; immutable recovery1 |
| 8k1k / 4 / 256 | W4A16 CuTe split MoE | 584.828149 | 9.303878 | 101.632068 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |
| 8k1k / 8 / 4 | W4A4 TRT-LLM | 57.518821 | 128.752912 | 7.771737 | c2-w4a4-trtllm-dp-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | image-provided | historical control |
| 8k1k / 8 / 4 | W4A16 MegaMoE | 61.808411 | 135.896259 | 7.364547 | c2-w4a16-megamoe-autotune-20260921-recovery8 | 26c41009549f9ad407e107b33d5144f6e085418b | ad0a5e5e78e57070ec7c582efe733cb55cd8839f | original-wheel-sglang-no-proxy-defaults |
| 8k1k / 8 / 4 | W4A16 CuTe split MoE | 53.237445 | 116.316665 | 8.415241 | c2-w4a16-cutedsl-mem80-20260920 | 50eeb742961908afa68f4f523a1a19c5de6eb0b3 | f9dd3c10541e087b716772245a9d033499745048 | historical control |

| Scenario / TP / C | Mega / Split output ratio | Output change % | Interactivity ratio | Interactivity change % |
|---|---:|---:|---:|---:|
| 1k1k / 4 / 4 | 1.105251138 | +10.525114 | 1.056212014 | +5.621201 |
| 1k1k / 4 / 8 | 1.072472639 | +7.247264 | 1.060208284 | +6.020828 |
| 1k1k / 4 / 16 | 1.068903080 | +6.890308 | 1.058136771 | +5.813677 |
| 1k1k / 4 / 32 | 1.081259597 | +8.125960 | 1.090440522 | +9.044052 |
| 1k1k / 4 / 64 | 1.162065573 | +16.206557 | 1.164600495 | +16.460050 |
| 1k1k / 4 / 128 | 1.141782899 | +14.178290 | 1.135695682 | +13.569568 |
| 1k1k / 4 / 256 | 1.022210714 | +2.221071 | 1.016732477 | +1.673248 |
| 1k1k / 8 / 4 | 1.157805216 | +15.780522 | 1.129103217 | +12.910322 |
| 8k1k / 4 / 4 | 1.056834878 | +5.683488 | 1.054326344 | +5.432634 |
| 8k1k / 4 / 8 | 1.042165556 | +4.216556 | 1.037255993 | +3.725599 |
| 8k1k / 4 / 16 | 1.091264343 | +9.126434 | 1.071050966 | +7.105097 |
| 8k1k / 4 / 32 | 1.004679502 | +0.467950 | 0.987215527 | -1.278447 |
| 8k1k / 4 / 64 | 1.040204458 | +4.020446 | 1.040058226 | +4.005823 |
| 8k1k / 4 / 128 | 1.016012413 | +1.601241 | 1.007132471 | +0.713247 |
| 8k1k / 4 / 256 | 1.011337315 | +1.133731 | 1.004514167 | +0.451417 |
| 8k1k / 8 / 4 | 1.160995061 | +16.099506 | 1.168330078 | +16.833008 |

- Final charts show four separate observed frontiers: New Mega16, Original Mega16, Split16 and TRT16, with no pooled global frontier. The main comparison remains48; original16 references are additional plot observations only.
- Two preserved Mega points use SG6d8/original proxy; fourteen new points use SG26c/stock-wheel proxy disabled. The combined Mega frontier uses their union without averaging measurements or relabeling provenance.
- Historical TRT and Split controls retain their own sources, image and runtime. Ratios are observations, not isolated kernel, autotuning or workaround effects.
- Exact ordered input/output lengths establish matched sampled workloads, not numerical or output-quality equivalence.
- Interactivity is 1000/median TPOT; throughput is actual output tokens/duration/GPU. All successful observations remain visible.
- Device wait_until timeouts and device global_exit are disabled in the R8 configuration; valid global_exit semantics remain untested.
