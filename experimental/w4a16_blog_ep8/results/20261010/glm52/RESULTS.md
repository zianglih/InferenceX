# GLM-5.2: EAGLE / MTP, EP8, concurrency 1-64

21 measured points; 3,810 successful measured requests; zero measured failures. 762 successful warmup requests are excluded.

| Backend | C | Output tokens/s/GPU | Median TPOT (ms) | AL | Acceptance rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| MegaMoE W4A4 | 1 | 26.520 | 4.7866 | 3.3891 | 0.7964 |
| MegaMoE W4A4 | 2 | 51.554 | 4.7478 | 3.5142 | 0.8382 |
| MegaMoE W4A4 | 4 | 92.590 | 5.1852 | 3.4455 | 0.8152 |
| MegaMoE W4A4 | 8 | 159.233 | 5.6939 | 3.4356 | 0.8119 |
| MegaMoE W4A4 | 16 | 287.056 | 6.3893 | 3.4953 | 0.8319 |
| MegaMoE W4A4 | 32 | 509.346 | 7.3284 | 3.4885 | 0.8296 |
| MegaMoE W4A4 | 64 | 889.284 | 8.2309 | 3.4667 | 0.8223 |
| MegaMoE W4A16 | 1 | 28.592 | 4.3849 | 3.5580 | 0.8527 |
| MegaMoE W4A16 | 2 | 53.609 | 4.4694 | 3.5241 | 0.8414 |
| MegaMoE W4A16 | 4 | 98.618 | 4.9126 | 3.5149 | 0.8384 |
| MegaMoE W4A16 | 8 | 175.960 | 5.3168 | 3.5451 | 0.8484 |
| MegaMoE W4A16 | 16 | 303.587 | 6.1173 | 3.5483 | 0.8495 |
| MegaMoE W4A16 | 32 | 526.836 | 7.0327 | 3.5369 | 0.8457 |
| MegaMoE W4A16 | 64 | 891.101 | 8.1697 | 3.5246 | 0.8416 |
| TRTLLM NVFP4 W4A4 | 1 | 24.050 | 5.1201 | 3.5804 | 0.8602 |
| TRTLLM NVFP4 W4A4 | 2 | 45.048 | 5.4384 | 3.4958 | 0.8320 |
| TRTLLM NVFP4 W4A4 | 4 | 85.810 | 5.6046 | 3.5169 | 0.8390 |
| TRTLLM NVFP4 W4A4 | 8 | 162.699 | 5.7440 | 3.4927 | 0.8310 |
| TRTLLM NVFP4 W4A4 | 16 | 290.586 | 6.4186 | 3.5394 | 0.8465 |
| TRTLLM NVFP4 W4A4 | 32 | 497.029 | 7.5419 | 3.5086 | 0.8363 |
| TRTLLM NVFP4 W4A4 | 64 | 743.673 | 9.9100 | 3.5298 | 0.8433 |

AL is the measured completion-token sum divided by the verification-count sum, including native bonus tokens. Acceptance rate uses correct/proposed draft totals. The compact table retains those exact integer totals and coverage counts.

Throughput includes the whole measured interval. Interactivity is 1,000 / saved median TPOT. Saved ITL is chunk spacing at stream interval 30. All signed backend comparisons are retained in comparisons.csv; a single sweep does not establish statistical significance or output quality. W4A16 also affects eligible NVFP4 dense linears.

The plots use only this fresh campaign. Full logs and per-request records remain in cluster persistent storage; public replay validates compact arithmetic and plotting.
