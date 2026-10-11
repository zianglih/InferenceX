# DeepSeek-V4.1 Flash: DSpark, EP4, concurrency 1-64

21 measured points; 3,810 successful measured requests; zero measured failures. 762 successful warmup requests are excluded.

| Backend | C | Output tokens/s/GPU | Median TPOT (ms) | AL | Acceptance rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| MegaMoE W4A4 | 1 | 126.024 | 1.7776 | 5.0314 | 0.8065 |
| MegaMoE W4A4 | 2 | 228.917 | 1.9038 | 4.7957 | 0.7594 |
| MegaMoE W4A4 | 4 | 353.717 | 2.0893 | 4.4963 | 0.6994 |
| MegaMoE W4A4 | 8 | 617.228 | 2.5031 | 4.5184 | 0.7038 |
| MegaMoE W4A4 | 16 | 1023.140 | 2.9957 | 4.5336 | 0.7069 |
| MegaMoE W4A4 | 32 | 1522.363 | 3.7763 | 4.4028 | 0.6807 |
| MegaMoE W4A4 | 64 | 2759.638 | 4.2673 | 4.4766 | 0.6955 |
| MegaMoE W4A16 | 1 | 127.877 | 1.8018 | 4.9264 | 0.7855 |
| MegaMoE W4A16 | 2 | 217.784 | 2.0222 | 4.5766 | 0.7155 |
| MegaMoE W4A16 | 4 | 397.228 | 2.1700 | 4.7592 | 0.7521 |
| MegaMoE W4A16 | 8 | 640.123 | 2.6461 | 4.8031 | 0.7608 |
| MegaMoE W4A16 | 16 | 1009.060 | 3.2755 | 4.6558 | 0.7313 |
| MegaMoE W4A16 | 32 | 1535.186 | 4.0698 | 4.6206 | 0.7243 |
| MegaMoE W4A16 | 64 | 2678.316 | 4.7597 | 4.6894 | 0.7381 |
| TRTLLM NVFP4 W4A4 | 1 | 99.916 | 2.0220 | 4.3004 | 0.6602 |
| TRTLLM NVFP4 W4A4 | 2 | 220.742 | 2.1002 | 4.8385 | 0.7678 |
| TRTLLM NVFP4 W4A4 | 4 | 361.681 | 2.1562 | 4.4477 | 0.6897 |
| TRTLLM NVFP4 W4A4 | 8 | 663.483 | 2.4569 | 4.8257 | 0.7653 |
| TRTLLM NVFP4 W4A4 | 16 | 1098.623 | 3.0477 | 4.7671 | 0.7536 |
| TRTLLM NVFP4 W4A4 | 32 | 1551.622 | 3.9508 | 4.6736 | 0.7349 |
| TRTLLM NVFP4 W4A4 | 64 | 2640.574 | 4.7781 | 4.6894 | 0.7381 |

AL is the measured completion-token sum divided by the verification-count sum, including native bonus tokens. Acceptance rate uses correct/proposed draft totals. The compact table retains those exact integer totals and coverage counts.

Throughput includes the whole measured interval. Interactivity is 1,000 / saved median TPOT. Saved ITL is chunk spacing at stream interval 30. All signed backend comparisons are retained in comparisons.csv; a single sweep does not establish statistical significance or output quality. W4A16 also affects eligible NVFP4 dense linears.

The plots use only this fresh campaign. Full logs and per-request records remain in cluster persistent storage; public replay validates compact arithmetic and plotting.
