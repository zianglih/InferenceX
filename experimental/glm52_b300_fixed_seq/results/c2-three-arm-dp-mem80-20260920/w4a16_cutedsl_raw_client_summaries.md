# Raw client benchmark summaries

Exactly **16** client logs are included below. Each contains one complete `Serving Benchmark Result` block, reproduced verbatim including the client's printed precision. Full-precision values remain in the accompanying `result.json` files. The source logs are unchanged; this document does not independently validate runtime configuration, request success, or planned matrix coverage.

<details><summary>中文</summary>

以下逐项原样摘录客户端打印的完整 `Serving Benchmark Result` 区块，保留原有显示精度。完整精度保留在各项 `result.json` 中，原始日志未作修改。此文档本身不验证运行配置、请求成功率或计划矩阵覆盖情况。

</details>

## 1k1k/w4a16-cutedsl/tp4_conc4

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  76.48     
Total input tokens:                      37148     
Total generated tokens:                  36709     
Request throughput (req/s):              0.52      
Output token throughput (tok/s):         479.98    
Total Token throughput (tok/s):          965.70    
---------------Time to First Token----------------
Mean TTFT (ms):                          646.76    
Median TTFT (ms):                        296.72    
P90 TTFT (ms):                           1621.04   
P99 TTFT (ms):                           2536.06   
P99.9 TTFT (ms):                         2832.00   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          7.49      
Median TPOT (ms):                        7.47      
P90 TPOT (ms):                           8.38      
P99 TPOT (ms):                           8.89      
P99.9 TPOT (ms):                         8.97      
---------------Inter-token Latency----------------
Mean ITL (ms):                           585.59    
Median ITL (ms):                         446.96    
P90 ITL (ms):                            1173.23   
P99 ITL (ms):                            2561.06   
P99.9 ITL (ms):                          3639.14   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          7512.83   
Median E2EL (ms):                        7407.42   
P90 E2EL (ms):                           9034.19   
P99 E2EL (ms):                           9861.72   
P99.9 E2EL (ms):                         10040.13  
==================================================
```

## 1k1k/w4a16-cutedsl/tp4_conc8

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc8/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc8/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     80        
Benchmark duration (s):                  93.17     
Total input tokens:                      73937     
Total generated tokens:                  74326     
Request throughput (req/s):              0.86      
Output token throughput (tok/s):         797.75    
Total Token throughput (tok/s):          1591.33   
---------------Time to First Token----------------
Mean TTFT (ms):                          593.91    
Median TTFT (ms):                        305.36    
P90 TTFT (ms):                           1295.62   
P99 TTFT (ms):                           2446.28   
P99.9 TTFT (ms):                         2542.91   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          9.13      
Median TPOT (ms):                        9.22      
P90 TPOT (ms):                           10.41     
P99 TPOT (ms):                           10.94     
P99.9 TPOT (ms):                         10.96     
---------------Inter-token Latency----------------
Mean ITL (ms):                           728.94    
Median ITL (ms):                         517.03    
P90 ITL (ms):                            1547.92   
P99 ITL (ms):                            2992.79   
P99.9 ITL (ms):                          4610.38   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          9067.79   
Median E2EL (ms):                        9154.44   
P90 E2EL (ms):                           10255.30  
P99 E2EL (ms):                           11604.97  
P99.9 E2EL (ms):                         12567.38  
==================================================
```

## 1k1k/w4a16-cutedsl/tp4_conc16

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc16/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc16/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     160       
Benchmark duration (s):                  118.71    
Total input tokens:                      148067    
Total generated tokens:                  146669    
Request throughput (req/s):              1.35      
Output token throughput (tok/s):         1235.51   
Total Token throughput (tok/s):          2482.79   
---------------Time to First Token----------------
Mean TTFT (ms):                          758.50    
Median TTFT (ms):                        343.91    
P90 TTFT (ms):                           1941.40   
P99 TTFT (ms):                           3442.96   
P99.9 TTFT (ms):                         4154.87   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          11.71     
Median TPOT (ms):                        11.84     
P90 TPOT (ms):                           13.41     
P99 TPOT (ms):                           14.69     
P99.9 TPOT (ms):                         15.24     
---------------Inter-token Latency----------------
Mean ITL (ms):                           983.04    
Median ITL (ms):                         704.28    
P90 ITL (ms):                            2072.65   
P99 ITL (ms):                            3998.11   
P99.9 ITL (ms):                          5695.09   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          11485.96  
Median E2EL (ms):                        11447.02  
P90 E2EL (ms):                           13484.27  
P99 E2EL (ms):                           15552.29  
P99.9 E2EL (ms):                         16134.43  
==================================================
```

## 1k1k/w4a16-cutedsl/tp4_conc32

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc32/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc32/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     320       
Benchmark duration (s):                  156.46    
Total input tokens:                      294748    
Total generated tokens:                  295754    
Request throughput (req/s):              2.05      
Output token throughput (tok/s):         1890.29   
Total Token throughput (tok/s):          3774.14   
---------------Time to First Token----------------
Mean TTFT (ms):                          761.69    
Median TTFT (ms):                        426.05    
P90 TTFT (ms):                           1793.33   
P99 TTFT (ms):                           3138.52   
P99.9 TTFT (ms):                         4264.17   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          15.59     
Median TPOT (ms):                        15.83     
P90 TPOT (ms):                           17.81     
P99 TPOT (ms):                           19.33     
P99.9 TPOT (ms):                         21.92     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1251.42   
Median ITL (ms):                         898.26    
P90 ITL (ms):                            2646.79   
P99 ITL (ms):                            5311.78   
P99.9 ITL (ms):                          7305.01   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          15160.84  
Median E2EL (ms):                        15191.48  
P90 E2EL (ms):                           17734.18  
P99 E2EL (ms):                           19753.91  
P99.9 E2EL (ms):                         21448.09  
==================================================
```

## 1k1k/w4a16-cutedsl/tp4_conc64

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc64/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc64/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     640       
Benchmark duration (s):                  229.06    
Total input tokens:                      590968    
Total generated tokens:                  589849    
Request throughput (req/s):              2.79      
Output token throughput (tok/s):         2575.07   
Total Token throughput (tok/s):          5155.03   
---------------Time to First Token----------------
Mean TTFT (ms):                          1042.74   
Median TTFT (ms):                        538.95    
P90 TTFT (ms):                           2175.36   
P99 TTFT (ms):                           3980.77   
P99.9 TTFT (ms):                         14895.87  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          23.18     
Median TPOT (ms):                        23.70     
P90 TPOT (ms):                           26.99     
P99 TPOT (ms):                           29.87     
P99.9 TPOT (ms):                         31.41     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1884.88   
Median ITL (ms):                         1344.03   
P90 ITL (ms):                            3945.58   
P99 ITL (ms):                            8385.49   
P99.9 ITL (ms):                          13472.51  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          22388.98  
Median E2EL (ms):                        22554.74  
P90 E2EL (ms):                           26540.07  
P99 E2EL (ms):                           30680.96  
P99.9 E2EL (ms):                         41621.48  
==================================================
```

## 1k1k/w4a16-cutedsl/tp4_conc128

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc128/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc128/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     1280      
Benchmark duration (s):                  320.97    
Total input tokens:                      1181744   
Total generated tokens:                  1177796   
Request throughput (req/s):              3.99      
Output token throughput (tok/s):         3669.45   
Total Token throughput (tok/s):          7351.21   
---------------Time to First Token----------------
Mean TTFT (ms):                          1097.39   
Median TTFT (ms):                        598.15    
P90 TTFT (ms):                           2524.69   
P99 TTFT (ms):                           3571.93   
P99.9 TTFT (ms):                         15292.08  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          32.98     
Median TPOT (ms):                        34.00     
P90 TPOT (ms):                           38.81     
P99 TPOT (ms):                           43.44     
P99.9 TPOT (ms):                         45.52     
---------------Inter-token Latency----------------
Mean ITL (ms):                           2688.25   
Median ITL (ms):                         1869.85   
P90 ITL (ms):                            5751.54   
P99 ITL (ms):                            12052.02  
P99.9 ITL (ms):                          17897.45  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          31415.79  
Median E2EL (ms):                        31924.89  
P90 E2EL (ms):                           37595.12  
P99 E2EL (ms):                           43678.08  
P99.9 E2EL (ms):                         47749.94  
==================================================
```

## 1k1k/w4a16-cutedsl/tp4_conc256

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc256/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp4_conc256/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     2560      
Benchmark duration (s):                  445.42    
Total input tokens:                      2360891   
Total generated tokens:                  2360050   
Request throughput (req/s):              5.75      
Output token throughput (tok/s):         5298.44   
Total Token throughput (tok/s):          10598.76  
---------------Time to First Token----------------
Mean TTFT (ms):                          1282.16   
Median TTFT (ms):                        595.52    
P90 TTFT (ms):                           2945.96   
P99 TTFT (ms):                           6220.19   
P99.9 TTFT (ms):                         20675.21  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          45.95     
Median TPOT (ms):                        47.47     
P90 TPOT (ms):                           54.85     
P99 TPOT (ms):                           60.20     
P99.9 TPOT (ms):                         63.44     
---------------Inter-token Latency----------------
Mean ITL (ms):                           3804.65   
Median ITL (ms):                         2648.41   
P90 ITL (ms):                            8236.08   
P99 ITL (ms):                            16755.83  
P99.9 ITL (ms):                          24967.57  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          43628.25  
Median E2EL (ms):                        44643.51  
P90 E2EL (ms):                           52347.54  
P99 E2EL (ms):                           59461.97  
P99.9 E2EL (ms):                         64954.06  
==================================================
```

## 1k1k/w4a16-cutedsl/tp8_conc4

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp8_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/1k1k/w4a16-cutedsl/tp8_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  75.20     
Total input tokens:                      37148     
Total generated tokens:                  36709     
Request throughput (req/s):              0.53      
Output token throughput (tok/s):         488.12    
Total Token throughput (tok/s):          982.08    
---------------Time to First Token----------------
Mean TTFT (ms):                          278.55    
Median TTFT (ms):                        294.23    
P90 TTFT (ms):                           303.72    
P99 TTFT (ms):                           315.10    
P99.9 TTFT (ms):                         316.55    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          7.53      
Median TPOT (ms):                        7.53      
P90 TPOT (ms):                           8.34      
P99 TPOT (ms):                           8.72      
P99.9 TPOT (ms):                         8.89      
---------------Inter-token Latency----------------
Mean ITL (ms):                           630.71    
Median ITL (ms):                         487.35    
P90 ITL (ms):                            1223.49   
P99 ITL (ms):                            2169.11   
P99.9 ITL (ms):                          3054.59   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          7184.83   
Median E2EL (ms):                        7240.86   
P90 E2EL (ms):                           8127.14   
P99 E2EL (ms):                           8632.62   
P99.9 E2EL (ms):                         8783.34   
==================================================
```

## 8k1k/w4a16-cutedsl/tp4_conc4

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  85.21     
Total input tokens:                      294170    
Total generated tokens:                  36805     
Request throughput (req/s):              0.47      
Output token throughput (tok/s):         431.95    
Total Token throughput (tok/s):          3884.40   
---------------Time to First Token----------------
Mean TTFT (ms):                          895.03    
Median TTFT (ms):                        635.49    
P90 TTFT (ms):                           1366.39   
P99 TTFT (ms):                           3270.13   
P99.9 TTFT (ms):                         3357.86   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          8.12      
Median TPOT (ms):                        8.03      
P90 TPOT (ms):                           9.18      
P99 TPOT (ms):                           10.68     
P99.9 TPOT (ms):                         11.49     
---------------Inter-token Latency----------------
Mean ITL (ms):                           724.74    
Median ITL (ms):                         485.79    
P90 ITL (ms):                            1600.10   
P99 ITL (ms):                            3000.05   
P99.9 ITL (ms):                          4437.77   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          8341.75   
Median E2EL (ms):                        8151.89   
P90 E2EL (ms):                           9206.27   
P99 E2EL (ms):                           12438.26  
P99.9 E2EL (ms):                         12895.98  
==================================================
```

## 8k1k/w4a16-cutedsl/tp4_conc8

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc8/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc8/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     80        
Benchmark duration (s):                  107.84    
Total input tokens:                      585049    
Total generated tokens:                  74069     
Request throughput (req/s):              0.74      
Output token throughput (tok/s):         686.85    
Total Token throughput (tok/s):          6112.04   
---------------Time to First Token----------------
Mean TTFT (ms):                          963.03    
Median TTFT (ms):                        574.67    
P90 TTFT (ms):                           1922.01   
P99 TTFT (ms):                           3091.34   
P99.9 TTFT (ms):                         3283.29   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          10.26     
Median TPOT (ms):                        10.31     
P90 TPOT (ms):                           11.60     
P99 TPOT (ms):                           12.87     
P99.9 TPOT (ms):                         12.94     
---------------Inter-token Latency----------------
Mean ITL (ms):                           879.36    
Median ITL (ms):                         612.31    
P90 ITL (ms):                            1868.40   
P99 ITL (ms):                            3613.37   
P99.9 ITL (ms):                          5196.20   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          10449.18  
Median E2EL (ms):                        10350.56  
P90 E2EL (ms):                           12266.78  
P99 E2EL (ms):                           13607.83  
P99.9 E2EL (ms):                         13722.63  
==================================================
```

## 8k1k/w4a16-cutedsl/tp4_conc16

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc16/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc16/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     160       
Benchmark duration (s):                  160.78    
Total input tokens:                      1175512   
Total generated tokens:                  146426    
Request throughput (req/s):              1.00      
Output token throughput (tok/s):         910.71    
Total Token throughput (tok/s):          8221.88   
---------------Time to First Token----------------
Mean TTFT (ms):                          1682.37   
Median TTFT (ms):                        735.63    
P90 TTFT (ms):                           3312.25   
P99 TTFT (ms):                           12348.98  
P99.9 TTFT (ms):                         16199.62  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          15.11     
Median TPOT (ms):                        15.18     
P90 TPOT (ms):                           17.20     
P99 TPOT (ms):                           22.58     
P99.9 TPOT (ms):                         23.61     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1262.09   
Median ITL (ms):                         928.02    
P90 ITL (ms):                            2645.45   
P99 ITL (ms):                            5907.04   
P99.9 ITL (ms):                          7693.22   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          15525.93  
Median E2EL (ms):                        15383.35  
P90 E2EL (ms):                           18433.62  
P99 E2EL (ms):                           26771.08  
P99.9 E2EL (ms):                         30063.03  
==================================================
```

## 8k1k/w4a16-cutedsl/tp4_conc32

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc32/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc32/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     320       
Benchmark duration (s):                  221.49    
Total input tokens:                      2353025   
Total generated tokens:                  296143    
Request throughput (req/s):              1.44      
Output token throughput (tok/s):         1337.05   
Total Token throughput (tok/s):          11960.71  
---------------Time to First Token----------------
Mean TTFT (ms):                          1709.10   
Median TTFT (ms):                        909.23    
P90 TTFT (ms):                           3746.34   
P99 TTFT (ms):                           12835.60  
P99.9 TTFT (ms):                         17457.27  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          21.52     
Median TPOT (ms):                        21.68     
P90 TPOT (ms):                           25.37     
P99 TPOT (ms):                           29.02     
P99.9 TPOT (ms):                         29.17     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1781.68   
Median ITL (ms):                         1253.41   
P90 ITL (ms):                            3984.05   
P99 ITL (ms):                            8015.13   
P99.9 ITL (ms):                          12830.26  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          21602.72  
Median E2EL (ms):                        21222.86  
P90 E2EL (ms):                           26103.82  
P99 E2EL (ms):                           34603.23  
P99.9 E2EL (ms):                         38108.50  
==================================================
```

## 8k1k/w4a16-cutedsl/tp4_conc64

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc64/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc64/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     640       
Benchmark duration (s):                  352.36    
Total input tokens:                      4729464   
Total generated tokens:                  589927    
Request throughput (req/s):              1.82      
Output token throughput (tok/s):         1674.24   
Total Token throughput (tok/s):          15096.66  
---------------Time to First Token----------------
Mean TTFT (ms):                          2123.93   
Median TTFT (ms):                        997.45    
P90 TTFT (ms):                           4452.50   
P99 TTFT (ms):                           11925.34  
P99.9 TTFT (ms):                         24617.60  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          35.33     
Median TPOT (ms):                        36.58     
P90 TPOT (ms):                           41.85     
P99 TPOT (ms):                           47.15     
P99.9 TPOT (ms):                         51.27     
---------------Inter-token Latency----------------
Mean ITL (ms):                           2911.54   
Median ITL (ms):                         1948.72   
P90 ITL (ms):                            6555.67   
P99 ITL (ms):                            13916.09  
P99.9 ITL (ms):                          20899.00  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          34646.70  
Median E2EL (ms):                        34934.65  
P90 E2EL (ms):                           41304.63  
P99 E2EL (ms):                           48320.89  
P99.9 E2EL (ms):                         68838.29  
==================================================
```

## 8k1k/w4a16-cutedsl/tp4_conc128

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc128/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc128/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     1280      
Benchmark duration (s):                  577.40    
Total input tokens:                      9457437   
Total generated tokens:                  1177591   
Request throughput (req/s):              2.22      
Output token throughput (tok/s):         2039.46   
Total Token throughput (tok/s):          18418.67  
---------------Time to First Token----------------
Mean TTFT (ms):                          3106.19   
Median TTFT (ms):                        1213.88   
P90 TTFT (ms):                           6286.90   
P99 TTFT (ms):                           23841.72  
P99.9 TTFT (ms):                         38182.18  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          58.73     
Median TPOT (ms):                        60.77     
P90 TPOT (ms):                           70.21     
P99 TPOT (ms):                           80.04     
P99.9 TPOT (ms):                         101.21    
---------------Inter-token Latency----------------
Mean ITL (ms):                           4835.21   
Median ITL (ms):                         3180.92   
P90 ITL (ms):                            11022.49  
P99 ITL (ms):                            24604.49  
P99.9 ITL (ms):                          35008.22  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          57098.07  
Median E2EL (ms):                        57696.17  
P90 E2EL (ms):                           69453.68  
P99 E2EL (ms):                           82577.20  
P99.9 E2EL (ms):                         96390.61  
==================================================
```

## 8k1k/w4a16-cutedsl/tp4_conc256

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc256/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp4_conc256/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     2560      
Benchmark duration (s):                  1008.99   
Total input tokens:                      18878760  
Total generated tokens:                  2360332   
Request throughput (req/s):              2.54      
Output token throughput (tok/s):         2339.31   
Total Token throughput (tok/s):          21049.95  
---------------Time to First Token----------------
Mean TTFT (ms):                          4658.43   
Median TTFT (ms):                        1588.73   
P90 TTFT (ms):                           8130.95   
P99 TTFT (ms):                           46296.69  
P99.9 TTFT (ms):                         65845.17  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          103.45    
Median TPOT (ms):                        107.48    
P90 TPOT (ms):                           123.75    
P99 TPOT (ms):                           144.22    
P99.9 TPOT (ms):                         167.43    
---------------Inter-token Latency----------------
Mean ITL (ms):                           8574.55   
Median ITL (ms):                         5543.27   
P90 ITL (ms):                            19723.47  
P99 ITL (ms):                            43426.87  
P99.9 ITL (ms):                          62482.05  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          100020.17 
Median E2EL (ms):                        101632.07 
P90 E2EL (ms):                           121972.79 
P99 E2EL (ms):                           149341.61 
P99.9 E2EL (ms):                         174274.19 
==================================================
```

## 8k1k/w4a16-cutedsl/tp8_conc4

[Complete client log](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp8_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-cutedsl-mem80-20260920/8k1k/w4a16-cutedsl/tp8_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  86.42     
Total input tokens:                      294170    
Total generated tokens:                  36805     
Request throughput (req/s):              0.46      
Output token throughput (tok/s):         425.90    
Total Token throughput (tok/s):          3829.97   
---------------Time to First Token----------------
Mean TTFT (ms):                          655.37    
Median TTFT (ms):                        620.84    
P90 TTFT (ms):                           898.84    
P99 TTFT (ms):                           970.31    
P99.9 TTFT (ms):                         970.36    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          8.48      
Median TPOT (ms):                        8.60      
P90 TPOT (ms):                           9.48      
P99 TPOT (ms):                           10.11     
P99.9 TPOT (ms):                         10.16     
---------------Inter-token Latency----------------
Mean ITL (ms):                           732.11    
Median ITL (ms):                         483.70    
P90 ITL (ms):                            1465.03   
P99 ITL (ms):                            3363.75   
P99.9 ITL (ms):                          4354.44   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          8434.03   
Median E2EL (ms):                        8415.24   
P90 E2EL (ms):                           9179.93   
P99 E2EL (ms):                           10271.42  
P99.9 E2EL (ms):                         10547.40  
==================================================
```

