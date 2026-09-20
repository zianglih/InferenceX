# Raw client benchmark summaries

Exactly **16** client logs are included below. Each contains one complete `Serving Benchmark Result` block, reproduced verbatim including the client's printed precision. Full-precision values remain in the accompanying `result.json` files. The source logs are unchanged; this document does not independently validate runtime configuration, request success, or planned matrix coverage.

<details><summary>中文</summary>

以下逐项原样摘录客户端打印的完整 `Serving Benchmark Result` 区块，保留原有显示精度。完整精度保留在各项 `result.json` 中，原始日志未作修改。此文档本身不验证运行配置、请求成功率或计划矩阵覆盖情况。

</details>

## 1k1k/w4a4-trtllm/tp4_conc4

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  69.37     
Total input tokens:                      37148     
Total generated tokens:                  36709     
Request throughput (req/s):              0.58      
Output token throughput (tok/s):         529.14    
Total Token throughput (tok/s):          1064.61   
---------------Time to First Token----------------
Mean TTFT (ms):                          369.29    
Median TTFT (ms):                        273.50    
P90 TTFT (ms):                           711.03    
P99 TTFT (ms):                           1083.62   
P99.9 TTFT (ms):                         1103.85   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          7.10      
Median TPOT (ms):                        7.08      
P90 TPOT (ms):                           7.83      
P99 TPOT (ms):                           8.31      
P99.9 TPOT (ms):                         8.41      
---------------Inter-token Latency----------------
Mean ITL (ms):                           525.13    
Median ITL (ms):                         400.82    
P90 ITL (ms):                            1049.77   
P99 ITL (ms):                            2095.19   
P99.9 ITL (ms):                          3306.92   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          6880.87   
Median E2EL (ms):                        6870.05   
P90 E2EL (ms):                           7751.51   
P99 E2EL (ms):                           8341.38   
P99.9 E2EL (ms):                         8397.68   
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc8

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc8/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc8/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     80        
Benchmark duration (s):                  89.32     
Total input tokens:                      73937     
Total generated tokens:                  74326     
Request throughput (req/s):              0.90      
Output token throughput (tok/s):         832.17    
Total Token throughput (tok/s):          1659.98   
---------------Time to First Token----------------
Mean TTFT (ms):                          582.69    
Median TTFT (ms):                        279.12    
P90 TTFT (ms):                           1333.21   
P99 TTFT (ms):                           2566.94   
P99.9 TTFT (ms):                         2676.00   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          8.77      
Median TPOT (ms):                        8.89      
P90 TPOT (ms):                           9.71      
P99 TPOT (ms):                           10.26     
P99.9 TPOT (ms):                         10.45     
---------------Inter-token Latency----------------
Mean ITL (ms):                           719.00    
Median ITL (ms):                         520.63    
P90 ITL (ms):                            1544.52   
P99 ITL (ms):                            2839.01   
P99.9 ITL (ms):                          4032.76   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          8716.42   
Median E2EL (ms):                        8665.45   
P90 E2EL (ms):                           10135.21  
P99 E2EL (ms):                           11294.49  
P99.9 E2EL (ms):                         11516.18  
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc16

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc16/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc16/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     160       
Benchmark duration (s):                  111.84    
Total input tokens:                      148067    
Total generated tokens:                  146669    
Request throughput (req/s):              1.43      
Output token throughput (tok/s):         1311.36   
Total Token throughput (tok/s):          2635.23   
---------------Time to First Token----------------
Mean TTFT (ms):                          618.09    
Median TTFT (ms):                        302.26    
P90 TTFT (ms):                           1494.65   
P99 TTFT (ms):                           2466.55   
P99.9 TTFT (ms):                         2804.59   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          11.20     
Median TPOT (ms):                        11.34     
P90 TPOT (ms):                           12.66     
P99 TPOT (ms):                           14.68     
P99.9 TPOT (ms):                         16.68     
---------------Inter-token Latency----------------
Mean ITL (ms):                           933.68    
Median ITL (ms):                         678.34    
P90 ITL (ms):                            1938.23   
P99 ITL (ms):                            3894.69   
P99.9 ITL (ms):                          5623.31   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          10876.85  
Median E2EL (ms):                        10736.13  
P90 E2EL (ms):                           12699.47  
P99 E2EL (ms):                           15274.76  
P99.9 E2EL (ms):                         17082.04  
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc32

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc32/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc32/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     320       
Benchmark duration (s):                  150.96    
Total input tokens:                      294748    
Total generated tokens:                  295754    
Request throughput (req/s):              2.12      
Output token throughput (tok/s):         1959.19   
Total Token throughput (tok/s):          3911.72   
---------------Time to First Token----------------
Mean TTFT (ms):                          741.12    
Median TTFT (ms):                        394.58    
P90 TTFT (ms):                           1812.28   
P99 TTFT (ms):                           3162.58   
P99.9 TTFT (ms):                         4033.88   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          14.97     
Median TPOT (ms):                        15.11     
P90 TPOT (ms):                           17.26     
P99 TPOT (ms):                           19.51     
P99.9 TPOT (ms):                         19.90     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1224.44   
Median ITL (ms):                         866.60    
P90 ITL (ms):                            2631.13   
P99 ITL (ms):                            5280.23   
P99.9 ITL (ms):                          8112.92   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          14569.64  
Median E2EL (ms):                        14610.12  
P90 E2EL (ms):                           17318.16  
P99 E2EL (ms):                           19206.62  
P99.9 E2EL (ms):                         20367.96  
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc64

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc64/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc64/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     640       
Benchmark duration (s):                  217.16    
Total input tokens:                      590968    
Total generated tokens:                  589849    
Request throughput (req/s):              2.95      
Output token throughput (tok/s):         2716.21   
Total Token throughput (tok/s):          5437.57   
---------------Time to First Token----------------
Mean TTFT (ms):                          939.47    
Median TTFT (ms):                        555.36    
P90 TTFT (ms):                           1858.35   
P99 TTFT (ms):                           4383.32   
P99.9 TTFT (ms):                         9109.88   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          21.94     
Median TPOT (ms):                        22.59     
P90 TPOT (ms):                           26.23     
P99 TPOT (ms):                           29.05     
P99.9 TPOT (ms):                         33.05     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1797.84   
Median ITL (ms):                         1271.18   
P90 ITL (ms):                            3883.75   
P99 ITL (ms):                            8027.75   
P99.9 ITL (ms):                          11224.02  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          21142.75  
Median E2EL (ms):                        21360.30  
P90 E2EL (ms):                           25252.74  
P99 E2EL (ms):                           29941.04  
P99.9 E2EL (ms):                         35267.15  
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc128

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc128/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc128/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     1280      
Benchmark duration (s):                  284.17    
Total input tokens:                      1181744   
Total generated tokens:                  1177796   
Request throughput (req/s):              4.50      
Output token throughput (tok/s):         4144.64   
Total Token throughput (tok/s):          8303.18   
---------------Time to First Token----------------
Mean TTFT (ms):                          977.62    
Median TTFT (ms):                        515.99    
P90 TTFT (ms):                           2187.89   
P99 TTFT (ms):                           3352.36   
P99.9 TTFT (ms):                         13262.60  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          29.14     
Median TPOT (ms):                        29.97     
P90 TPOT (ms):                           34.91     
P99 TPOT (ms):                           38.91     
P99.9 TPOT (ms):                         43.72     
---------------Inter-token Latency----------------
Mean ITL (ms):                           2402.59   
Median ITL (ms):                         1677.27   
P90 ITL (ms):                            5132.78   
P99 ITL (ms):                            10679.76  
P99.9 ITL (ms):                          15798.02  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          27755.26  
Median E2EL (ms):                        28202.11  
P90 E2EL (ms):                           33617.35  
P99 E2EL (ms):                           38811.39  
P99.9 E2EL (ms):                         43998.13  
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc256

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc256/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp4_conc256/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     2560      
Benchmark duration (s):                  477.62    
Total input tokens:                      2360891   
Total generated tokens:                  2360050   
Request throughput (req/s):              5.36      
Output token throughput (tok/s):         4941.23   
Total Token throughput (tok/s):          9884.23   
---------------Time to First Token----------------
Mean TTFT (ms):                          1307.17   
Median TTFT (ms):                        725.96    
P90 TTFT (ms):                           3026.02   
P99 TTFT (ms):                           4818.30   
P99.9 TTFT (ms):                         17288.53  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          49.56     
Median TPOT (ms):                        51.50     
P90 TPOT (ms):                           59.80     
P99 TPOT (ms):                           65.56     
P99.9 TPOT (ms):                         69.28     
---------------Inter-token Latency----------------
Mean ITL (ms):                           4083.03   
Median ITL (ms):                         2836.41   
P90 ITL (ms):                            8964.51   
P99 ITL (ms):                            18290.79  
P99.9 ITL (ms):                          26950.15  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          46997.21  
Median E2EL (ms):                        48401.59  
P90 E2EL (ms):                           57390.10  
P99 E2EL (ms):                           64800.52  
P99.9 E2EL (ms):                         69767.04  
==================================================
```

## 1k1k/w4a4-trtllm/tp8_conc4

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp8_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/1k1k/w4a4-trtllm/tp8_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  71.91     
Total input tokens:                      37148     
Total generated tokens:                  36709     
Request throughput (req/s):              0.56      
Output token throughput (tok/s):         510.45    
Total Token throughput (tok/s):          1027.01   
---------------Time to First Token----------------
Mean TTFT (ms):                          275.25    
Median TTFT (ms):                        279.96    
P90 TTFT (ms):                           300.62    
P99 TTFT (ms):                           304.37    
P99.9 TTFT (ms):                         305.32    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          7.31      
Median TPOT (ms):                        7.14      
P90 TPOT (ms):                           8.27      
P99 TPOT (ms):                           9.03      
P99.9 TPOT (ms):                         9.34      
---------------Inter-token Latency----------------
Mean ITL (ms):                           571.31    
Median ITL (ms):                         443.74    
P90 ITL (ms):                            1071.13   
P99 ITL (ms):                            2393.06   
P99.9 ITL (ms):                          3465.02   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          6973.89   
Median E2EL (ms):                        6946.58   
P90 E2EL (ms):                           7763.57   
P99 E2EL (ms):                           8925.53   
P99.9 E2EL (ms):                         9129.41   
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc4

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  77.71     
Total input tokens:                      294170    
Total generated tokens:                  36805     
Request throughput (req/s):              0.51      
Output token throughput (tok/s):         473.60    
Total Token throughput (tok/s):          4258.95   
---------------Time to First Token----------------
Mean TTFT (ms):                          738.72    
Median TTFT (ms):                        462.95    
P90 TTFT (ms):                           1655.70   
P99 TTFT (ms):                           2090.43   
P99.9 TTFT (ms):                         2206.59   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          7.42      
Median TPOT (ms):                        7.22      
P90 TPOT (ms):                           8.31      
P99 TPOT (ms):                           9.10      
P99.9 TPOT (ms):                         9.11      
---------------Inter-token Latency----------------
Mean ITL (ms):                           641.79    
Median ITL (ms):                         437.04    
P90 ITL (ms):                            1279.22   
P99 ITL (ms):                            2845.79   
P99.9 ITL (ms):                          4556.90   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          7557.69   
Median E2EL (ms):                        7491.10   
P90 E2EL (ms):                           8731.82   
P99 E2EL (ms):                           9064.25   
P99.9 E2EL (ms):                         9110.01   
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc8

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc8/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc8/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     80        
Benchmark duration (s):                  101.12    
Total input tokens:                      585049    
Total generated tokens:                  74069     
Request throughput (req/s):              0.79      
Output token throughput (tok/s):         732.46    
Total Token throughput (tok/s):          6517.98   
---------------Time to First Token----------------
Mean TTFT (ms):                          901.26    
Median TTFT (ms):                        735.45    
P90 TTFT (ms):                           1585.46   
P99 TTFT (ms):                           3171.34   
P99.9 TTFT (ms):                         3306.93   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          9.67      
Median TPOT (ms):                        9.76      
P90 TPOT (ms):                           10.85     
P99 TPOT (ms):                           12.76     
P99.9 TPOT (ms):                         13.03     
---------------Inter-token Latency----------------
Mean ITL (ms):                           804.55    
Median ITL (ms):                         570.50    
P90 ITL (ms):                            1677.60   
P99 ITL (ms):                            3389.57   
P99.9 ITL (ms):                          4298.36   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          9861.94   
Median E2EL (ms):                        9861.83   
P90 E2EL (ms):                           11944.98  
P99 E2EL (ms):                           13139.06  
P99.9 E2EL (ms):                         13229.78  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc16

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc16/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc16/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     160       
Benchmark duration (s):                  139.50    
Total input tokens:                      1175512   
Total generated tokens:                  146426    
Request throughput (req/s):              1.15      
Output token throughput (tok/s):         1049.65   
Total Token throughput (tok/s):          9476.30   
---------------Time to First Token----------------
Mean TTFT (ms):                          1257.46   
Median TTFT (ms):                        751.05    
P90 TTFT (ms):                           2373.63   
P99 TTFT (ms):                           10587.99  
P99.9 TTFT (ms):                         12013.05  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          13.37     
Median TPOT (ms):                        13.39     
P90 TPOT (ms):                           15.72     
P99 TPOT (ms):                           18.09     
P99.9 TPOT (ms):                         19.82     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1102.58   
Median ITL (ms):                         823.16    
P90 ITL (ms):                            2396.90   
P99 ITL (ms):                            4236.89   
P99.9 ITL (ms):                          6953.69   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          13489.22  
Median E2EL (ms):                        13361.23  
P90 E2EL (ms):                           15993.02  
P99 E2EL (ms):                           24401.71  
P99.9 E2EL (ms):                         26304.82  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc32

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc32/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc32/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     320       
Benchmark duration (s):                  204.12    
Total input tokens:                      2353025   
Total generated tokens:                  296143    
Request throughput (req/s):              1.57      
Output token throughput (tok/s):         1450.80   
Total Token throughput (tok/s):          12978.27  
---------------Time to First Token----------------
Mean TTFT (ms):                          1454.22   
Median TTFT (ms):                        761.22    
P90 TTFT (ms):                           3333.69   
P99 TTFT (ms):                           10768.74  
P99.9 TTFT (ms):                         15621.96  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          19.89     
Median TPOT (ms):                        20.15     
P90 TPOT (ms):                           23.51     
P99 TPOT (ms):                           26.30     
P99.9 TPOT (ms):                         28.23     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1661.89   
Median ITL (ms):                         1163.86   
P90 ITL (ms):                            3730.06   
P99 ITL (ms):                            7299.04   
P99.9 ITL (ms):                          10772.72  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          19849.24  
Median E2EL (ms):                        20080.95  
P90 E2EL (ms):                           23809.51  
P99 E2EL (ms):                           30487.99  
P99.9 E2EL (ms):                         35840.13  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc64

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc64/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc64/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     640       
Benchmark duration (s):                  310.66    
Total input tokens:                      4729464   
Total generated tokens:                  589927    
Request throughput (req/s):              2.06      
Output token throughput (tok/s):         1898.93   
Total Token throughput (tok/s):          17122.74  
---------------Time to First Token----------------
Mean TTFT (ms):                          1800.85   
Median TTFT (ms):                        877.27    
P90 TTFT (ms):                           4106.02   
P99 TTFT (ms):                           9192.62   
P99.9 TTFT (ms):                         22001.28  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          31.15     
Median TPOT (ms):                        32.09     
P90 TPOT (ms):                           36.99     
P99 TPOT (ms):                           41.09     
P99.9 TPOT (ms):                         47.05     
---------------Inter-token Latency----------------
Mean ITL (ms):                           2557.15   
Median ITL (ms):                         1747.35   
P90 ITL (ms):                            5642.94   
P99 ITL (ms):                            11622.59  
P99.9 ITL (ms):                          17343.56  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          30480.84  
Median E2EL (ms):                        30766.82  
P90 E2EL (ms):                           36846.66  
P99 E2EL (ms):                           43101.65  
P99.9 E2EL (ms):                         54757.20  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc128

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc128/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc128/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     1280      
Benchmark duration (s):                  501.96    
Total input tokens:                      9457437   
Total generated tokens:                  1177591   
Request throughput (req/s):              2.55      
Output token throughput (tok/s):         2345.97   
Total Token throughput (tok/s):          21186.85  
---------------Time to First Token----------------
Mean TTFT (ms):                          2529.21   
Median TTFT (ms):                        1105.56   
P90 TTFT (ms):                           5143.25   
P99 TTFT (ms):                           18054.40  
P99.9 TTFT (ms):                         30449.31  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          50.96     
Median TPOT (ms):                        52.99     
P90 TPOT (ms):                           61.37     
P99 TPOT (ms):                           70.33     
P99.9 TPOT (ms):                         75.58     
---------------Inter-token Latency----------------
Mean ITL (ms):                           4216.40   
Median ITL (ms):                         2826.25   
P90 ITL (ms):                            9545.40   
P99 ITL (ms):                            20460.78  
P99.9 ITL (ms):                          31013.43  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          49383.94  
Median E2EL (ms):                        50074.80  
P90 E2EL (ms):                           60555.32  
P99 E2EL (ms):                           71102.62  
P99.9 E2EL (ms):                         79995.33  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc256

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc256/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp4_conc256/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     2560      
Benchmark duration (s):                  849.20    
Total input tokens:                      18878760  
Total generated tokens:                  2360332   
Request throughput (req/s):              3.01      
Output token throughput (tok/s):         2779.46   
Total Token throughput (tok/s):          25010.57  
---------------Time to First Token----------------
Mean TTFT (ms):                          3829.26   
Median TTFT (ms):                        1476.76   
P90 TTFT (ms):                           6724.33   
P99 TTFT (ms):                           34732.19  
P99.9 TTFT (ms):                         51200.46  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          87.10     
Median TPOT (ms):                        90.54     
P90 TPOT (ms):                           104.09    
P99 TPOT (ms):                           120.44    
P99.9 TPOT (ms):                         136.71    
---------------Inter-token Latency----------------
Mean ITL (ms):                           7188.99   
Median ITL (ms):                         4683.98   
P90 ITL (ms):                            16546.33  
P99 ITL (ms):                            35685.80  
P99.9 ITL (ms):                          53254.36  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          84098.81  
Median E2EL (ms):                        85635.25  
P90 E2EL (ms):                           102738.81 
P99 E2EL (ms):                           122023.97 
P99.9 E2EL (ms):                         135787.68 
==================================================
```

## 8k1k/w4a4-trtllm/tp8_conc4

[Complete client log](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp8_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a4-trtllm-dp-mem80-20260920/8k1k/w4a4-trtllm/tp8_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  79.98     
Total input tokens:                      294170    
Total generated tokens:                  36805     
Request throughput (req/s):              0.50      
Output token throughput (tok/s):         460.15    
Total Token throughput (tok/s):          4137.98   
---------------Time to First Token----------------
Mean TTFT (ms):                          592.64    
Median TTFT (ms):                        563.41    
P90 TTFT (ms):                           743.31    
P99 TTFT (ms):                           879.87    
P99.9 TTFT (ms):                         893.47    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          7.82      
Median TPOT (ms):                        7.77      
P90 TPOT (ms):                           9.00      
P99 TPOT (ms):                           9.56      
P99.9 TPOT (ms):                         9.61      
---------------Inter-token Latency----------------
Mean ITL (ms):                           641.59    
Median ITL (ms):                         435.10    
P90 ITL (ms):                            1328.41   
P99 ITL (ms):                            2686.88   
P99.9 ITL (ms):                          3211.43   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          7762.44   
Median E2EL (ms):                        7771.74   
P90 E2EL (ms):                           8826.82   
P99 E2EL (ms):                           9840.96   
P99.9 E2EL (ms):                         9959.88   
==================================================
```

