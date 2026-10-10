# DeepSeek-V4.1 Flash: DSpark, EP8, concurrency 1-64

21 measured points; 3,810 successful measured requests; zero measured failures. 762 successful warmup requests are excluded.

| Backend | C | Output tokens/s/GPU | Median TPOT (ms) | AL | Acceptance rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| MegaMoE W4A4 | 1 | 66.360 | 1.7156 | 5.2006 | 0.8404 |
| MegaMoE W4A4 | 2 | 117.168 | 1.8134 | 4.5858 | 0.7174 |
| MegaMoE W4A4 | 4 | 220.254 | 1.9346 | 4.8012 | 0.7604 |
| MegaMoE W4A4 | 8 | 387.143 | 2.0588 | 4.8497 | 0.7701 |
| MegaMoE W4A4 | 16 | 644.017 | 2.3854 | 4.7147 | 0.7431 |
| MegaMoE W4A4 | 32 | 990.025 | 2.9840 | 4.5179 | 0.7037 |
| MegaMoE W4A4 | 64 | 1560.653 | 3.7890 | 4.5246 | 0.7051 |
| MegaMoE W4A16 | 1 | 61.617 | 1.7501 | 4.6785 | 0.7359 |
| MegaMoE W4A16 | 2 | 118.550 | 1.8358 | 4.7009 | 0.7403 |
| MegaMoE W4A16 | 4 | 211.211 | 2.0987 | 4.4259 | 0.6853 |
| MegaMoE W4A16 | 8 | 415.095 | 2.1702 | 5.0351 | 0.8072 |
| MegaMoE W4A16 | 16 | 590.282 | 2.5774 | 4.6865 | 0.7375 |
| MegaMoE W4A16 | 32 | 1041.808 | 3.2210 | 4.6995 | 0.7401 |
| MegaMoE W4A16 | 64 | 1528.966 | 4.0019 | 4.6570 | 0.7316 |
| TRTLLM NVFP4 W4A4 | 1 | 51.985 | 2.1527 | 4.6362 | 0.7274 |
| TRTLLM NVFP4 W4A4 | 2 | 98.369 | 2.0860 | 4.5803 | 0.7162 |
| TRTLLM NVFP4 W4A4 | 4 | 196.621 | 2.1940 | 4.5809 | 0.7164 |
| TRTLLM NVFP4 W4A4 | 8 | 346.465 | 2.3382 | 4.5784 | 0.7158 |
| TRTLLM NVFP4 W4A4 | 16 | 617.334 | 2.6559 | 4.7093 | 0.7420 |
| TRTLLM NVFP4 W4A4 | 32 | 975.818 | 3.2979 | 4.6420 | 0.7286 |
| TRTLLM NVFP4 W4A4 | 64 | 1326.517 | 4.6143 | 4.5919 | 0.7185 |

AL is the measured completion-token sum divided by the verification-count sum, including native bonus tokens. Acceptance rate uses correct/proposed draft totals. The compact table retains those exact integer totals and coverage counts.

Throughput includes the whole measured interval. Interactivity is 1,000 / saved median TPOT. Saved ITL is chunk spacing at stream interval 30. All signed backend comparisons are retained in comparisons.csv; a single sweep does not establish statistical significance or output quality. W4A16 also affects eligible NVFP4 dense linears.

The plots use only this fresh campaign. Full logs and per-request records remain in cluster persistent storage; public replay validates compact arithmetic and plotting.
