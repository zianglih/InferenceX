# Raw client benchmark summaries

Exactly **16** client logs are included below. Each contains one complete `Serving Benchmark Result` block, reproduced verbatim including the client's printed precision. Full-precision values remain in the accompanying `result.json` files. The source logs are unchanged; this document does not independently validate runtime configuration, request success, or planned matrix coverage.

<details><summary>中文</summary>

以下逐项原样摘录客户端打印的完整 `Serving Benchmark Result` 区块，保留原有显示精度。完整精度保留在各项 `result.json` 中，原始日志未作修改。此文档本身不验证运行配置、请求成功率或计划矩阵覆盖情况。

</details>

## 1k1k/w4a16-megamoe/tp4_conc4

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  71.67     
Total input tokens:                      37148     
Total generated tokens:                  36709     
Request throughput (req/s):              0.56      
Output token throughput (tok/s):         512.23    
Total Token throughput (tok/s):          1030.58   
---------------Time to First Token----------------
Mean TTFT (ms):                          468.42    
Median TTFT (ms):                        266.62    
P90 TTFT (ms):                           1003.53   
P99 TTFT (ms):                           1969.62   
P99.9 TTFT (ms):                         2385.24   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          7.17      
Median TPOT (ms):                        7.28      
P90 TPOT (ms):                           7.95      
P99 TPOT (ms):                           8.36      
P99.9 TPOT (ms):                         8.38      
---------------Inter-token Latency----------------
Mean ITL (ms):                           622.66    
Median ITL (ms):                         460.62    
P90 ITL (ms):                            1244.09   
P99 ITL (ms):                            2284.88   
P99.9 ITL (ms):                          2716.85   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          7037.45   
Median E2EL (ms):                        6948.74   
P90 E2EL (ms):                           8173.26   
P99 E2EL (ms):                           9146.73   
P99.9 E2EL (ms):                         9470.06   
==================================================
```

## 1k1k/w4a16-megamoe/tp4_conc8

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc8/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc8/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     80        
Benchmark duration (s):                  91.35     
Total input tokens:                      73937     
Total generated tokens:                  74326     
Request throughput (req/s):              0.88      
Output token throughput (tok/s):         813.64    
Total Token throughput (tok/s):          1623.02   
---------------Time to First Token----------------
Mean TTFT (ms):                          575.46    
Median TTFT (ms):                        273.80    
P90 TTFT (ms):                           1399.48   
P99 TTFT (ms):                           2665.05   
P99.9 TTFT (ms):                         3035.45   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          9.10      
Median TPOT (ms):                        9.11      
P90 TPOT (ms):                           10.14     
P99 TPOT (ms):                           10.99     
P99.9 TPOT (ms):                         11.23     
---------------Inter-token Latency----------------
Mean ITL (ms):                           760.78    
Median ITL (ms):                         538.02    
P90 ITL (ms):                            1608.77   
P99 ITL (ms):                            3240.01   
P99.9 ITL (ms):                          5499.51   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          9020.10   
Median E2EL (ms):                        8940.48   
P90 E2EL (ms):                           10202.23  
P99 E2EL (ms):                           12086.99  
P99.9 E2EL (ms):                         12238.46  
==================================================
```

## 1k1k/w4a16-megamoe/tp4_conc16

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc16/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc16/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     160       
Benchmark duration (s):                  116.38    
Total input tokens:                      148067    
Total generated tokens:                  146669    
Request throughput (req/s):              1.37      
Output token throughput (tok/s):         1260.26   
Total Token throughput (tok/s):          2532.52   
---------------Time to First Token----------------
Mean TTFT (ms):                          638.04    
Median TTFT (ms):                        390.39    
P90 TTFT (ms):                           1540.06   
P99 TTFT (ms):                           2416.83   
P99.9 TTFT (ms):                         2470.50   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          11.65     
Median TPOT (ms):                        11.71     
P90 TPOT (ms):                           13.20     
P99 TPOT (ms):                           14.06     
P99.9 TPOT (ms):                         14.30     
---------------Inter-token Latency----------------
Mean ITL (ms):                           942.55    
Median ITL (ms):                         678.25    
P90 ITL (ms):                            1969.23   
P99 ITL (ms):                            3899.35   
P99.9 ITL (ms):                          6163.37   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          11300.67  
Median E2EL (ms):                        11414.01  
P90 E2EL (ms):                           13260.32  
P99 E2EL (ms):                           14439.28  
P99.9 E2EL (ms):                         14881.73  
==================================================
```

## 1k1k/w4a16-megamoe/tp4_conc32

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc32/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc32/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     320       
Benchmark duration (s):                  140.47    
Total input tokens:                      294748    
Total generated tokens:                  295754    
Request throughput (req/s):              2.28      
Output token throughput (tok/s):         2105.45   
Total Token throughput (tok/s):          4203.73   
---------------Time to First Token----------------
Mean TTFT (ms):                          635.11    
Median TTFT (ms):                        301.53    
P90 TTFT (ms):                           1488.08   
P99 TTFT (ms):                           2667.78   
P99.9 TTFT (ms):                         3423.62   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          13.94     
Median TPOT (ms):                        14.02     
P90 TPOT (ms):                           15.73     
P99 TPOT (ms):                           16.84     
P99.9 TPOT (ms):                         17.81     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1152.02   
Median ITL (ms):                         844.36    
P90 ITL (ms):                            2441.58   
P99 ITL (ms):                            4542.00   
P99.9 ITL (ms):                          6557.04   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          13501.78  
Median E2EL (ms):                        13484.45  
P90 E2EL (ms):                           15955.53  
P99 E2EL (ms):                           17097.91  
P99.9 E2EL (ms):                         17371.98  
==================================================
```

## 1k1k/w4a16-megamoe/tp4_conc64

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc64/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc64/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     640       
Benchmark duration (s):                  196.79    
Total input tokens:                      590968    
Total generated tokens:                  589849    
Request throughput (req/s):              3.25      
Output token throughput (tok/s):         2997.29   
Total Token throughput (tok/s):          6000.27   
---------------Time to First Token----------------
Mean TTFT (ms):                          826.00    
Median TTFT (ms):                        436.90    
P90 TTFT (ms):                           1773.32   
P99 TTFT (ms):                           2718.60   
P99.9 TTFT (ms):                         11348.79  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          19.88     
Median TPOT (ms):                        20.27     
P90 TPOT (ms):                           23.10     
P99 TPOT (ms):                           25.69     
P99.9 TPOT (ms):                         26.92     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1624.15   
Median ITL (ms):                         1167.04   
P90 ITL (ms):                            3427.48   
P99 ITL (ms):                            6919.94   
P99.9 ITL (ms):                          9830.44   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          19130.70  
Median E2EL (ms):                        19304.63  
P90 E2EL (ms):                           22681.78  
P99 E2EL (ms):                           25864.66  
P99.9 E2EL (ms):                         32897.03  
==================================================
```

## 1k1k/w4a16-megamoe/tp4_conc128

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc128/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc128/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     1280      
Benchmark duration (s):                  274.55    
Total input tokens:                      1181744   
Total generated tokens:                  1177796   
Request throughput (req/s):              4.66      
Output token throughput (tok/s):         4289.92   
Total Token throughput (tok/s):          8594.22   
---------------Time to First Token----------------
Mean TTFT (ms):                          959.91    
Median TTFT (ms):                        531.07    
P90 TTFT (ms):                           2110.55   
P99 TTFT (ms):                           3063.16   
P99.9 TTFT (ms):                         14027.86  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          28.05     
Median TPOT (ms):                        28.85     
P90 TPOT (ms):                           32.84     
P99 TPOT (ms):                           36.16     
P99.9 TPOT (ms):                         37.62     
---------------Inter-token Latency----------------
Mean ITL (ms):                           2289.09   
Median ITL (ms):                         1614.49   
P90 ITL (ms):                            4891.68   
P99 ITL (ms):                            10069.05  
P99.9 ITL (ms):                          14710.37  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          26735.44  
Median E2EL (ms):                        27257.93  
P90 E2EL (ms):                           31685.04  
P99 E2EL (ms):                           35794.07  
P99.9 E2EL (ms):                         40513.09  
==================================================
```

## 1k1k/w4a16-megamoe/tp4_conc256

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc256/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp4_conc256/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     2560      
Benchmark duration (s):                  402.33    
Total input tokens:                      2360891   
Total generated tokens:                  2360050   
Request throughput (req/s):              6.36      
Output token throughput (tok/s):         5866.00   
Total Token throughput (tok/s):          11734.10  
---------------Time to First Token----------------
Mean TTFT (ms):                          1163.89   
Median TTFT (ms):                        571.19    
P90 TTFT (ms):                           2685.71   
P99 TTFT (ms):                           5596.68   
P99.9 TTFT (ms):                         18621.66  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          41.58     
Median TPOT (ms):                        42.86     
P90 TPOT (ms):                           49.51     
P99 TPOT (ms):                           55.06     
P99.9 TPOT (ms):                         60.69     
---------------Inter-token Latency----------------
Mean ITL (ms):                           3397.77   
Median ITL (ms):                         2339.72   
P90 ITL (ms):                            7355.90   
P99 ITL (ms):                            15182.28  
P99.9 ITL (ms):                          23292.17  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          39484.33  
Median E2EL (ms):                        40233.11  
P90 E2EL (ms):                           47965.05  
P99 E2EL (ms):                           54246.70  
P99.9 E2EL (ms):                         59342.96  
==================================================
```

## 1k1k/w4a16-megamoe/tp8_conc4

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp8_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/1k1k/w4a16-megamoe/tp8_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  69.62     
Total input tokens:                      37148     
Total generated tokens:                  36709     
Request throughput (req/s):              0.57      
Output token throughput (tok/s):         527.24    
Total Token throughput (tok/s):          1060.79   
---------------Time to First Token----------------
Mean TTFT (ms):                          275.54    
Median TTFT (ms):                        261.02    
P90 TTFT (ms):                           298.54    
P99 TTFT (ms):                           507.04    
P99.9 TTFT (ms):                         507.52    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          7.08      
Median TPOT (ms):                        7.18      
P90 TPOT (ms):                           7.76      
P99 TPOT (ms):                           8.03      
P99.9 TPOT (ms):                         8.10      
---------------Inter-token Latency----------------
Mean ITL (ms):                           563.37    
Median ITL (ms):                         399.30    
P90 ITL (ms):                            1082.24   
P99 ITL (ms):                            2483.69   
P99.9 ITL (ms):                          3077.55   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          6768.38   
Median E2EL (ms):                        6920.68   
P90 E2EL (ms):                           7766.30   
P99 E2EL (ms):                           8152.51   
P99.9 E2EL (ms):                         8216.20   
==================================================
```

## 8k1k/w4a16-megamoe/tp4_conc4

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  85.63     
Total input tokens:                      294170    
Total generated tokens:                  36805     
Request throughput (req/s):              0.47      
Output token throughput (tok/s):         429.84    
Total Token throughput (tok/s):          3865.37   
---------------Time to First Token----------------
Mean TTFT (ms):                          849.95    
Median TTFT (ms):                        605.05    
P90 TTFT (ms):                           1324.78   
P99 TTFT (ms):                           2267.73   
P99.9 TTFT (ms):                         2282.55   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          8.23      
Median TPOT (ms):                        8.28      
P90 TPOT (ms):                           9.25      
P99 TPOT (ms):                           9.94      
P99.9 TPOT (ms):                         9.96      
---------------Inter-token Latency----------------
Mean ITL (ms):                           620.79    
Median ITL (ms):                         449.52    
P90 ITL (ms):                            1266.72   
P99 ITL (ms):                            2702.04   
P99.9 ITL (ms):                          3743.89   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          8408.01   
Median E2EL (ms):                        8232.73   
P90 E2EL (ms):                           9567.64   
P99 E2EL (ms):                           10478.85  
P99.9 E2EL (ms):                         10669.40  
==================================================
```

## 8k1k/w4a16-megamoe/tp4_conc8

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc8/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc8/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     80        
Benchmark duration (s):                  114.01    
Total input tokens:                      585049    
Total generated tokens:                  74069     
Request throughput (req/s):              0.70      
Output token throughput (tok/s):         649.68    
Total Token throughput (tok/s):          5781.29   
---------------Time to First Token----------------
Mean TTFT (ms):                          1156.50   
Median TTFT (ms):                        671.26    
P90 TTFT (ms):                           2014.76   
P99 TTFT (ms):                           4134.16   
P99.9 TTFT (ms):                         4672.64   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          10.83     
Median TPOT (ms):                        10.73     
P90 TPOT (ms):                           12.43     
P99 TPOT (ms):                           14.72     
P99.9 TPOT (ms):                         15.02     
---------------Inter-token Latency----------------
Mean ITL (ms):                           886.81    
Median ITL (ms):                         650.19    
P90 ITL (ms):                            1933.63   
P99 ITL (ms):                            3778.51   
P99.9 ITL (ms):                          4847.22   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          11177.49  
Median E2EL (ms):                        11108.47  
P90 E2EL (ms):                           13128.32  
P99 E2EL (ms):                           15616.11  
P99.9 E2EL (ms):                         16267.59  
==================================================
```

## 8k1k/w4a16-megamoe/tp4_conc16

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc16/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc16/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     160       
Benchmark duration (s):                  164.32    
Total input tokens:                      1175512   
Total generated tokens:                  146426    
Request throughput (req/s):              0.97      
Output token throughput (tok/s):         891.09    
Total Token throughput (tok/s):          8044.76   
---------------Time to First Token----------------
Mean TTFT (ms):                          1638.10   
Median TTFT (ms):                        686.55    
P90 TTFT (ms):                           2911.96   
P99 TTFT (ms):                           12755.79  
P99.9 TTFT (ms):                         16617.69  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          15.51     
Median TPOT (ms):                        15.75     
P90 TPOT (ms):                           18.14     
P99 TPOT (ms):                           20.77     
P99.9 TPOT (ms):                         21.18     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1238.09   
Median ITL (ms):                         895.89    
P90 ITL (ms):                            2679.80   
P99 ITL (ms):                            5530.43   
P99.9 ITL (ms):                          7361.59   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          15829.66  
Median E2EL (ms):                        15569.17  
P90 E2EL (ms):                           18806.44  
P99 E2EL (ms):                           25906.86  
P99.9 E2EL (ms):                         31762.40  
==================================================
```

## 8k1k/w4a16-megamoe/tp4_conc32

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc32/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc32/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     320       
Benchmark duration (s):                  243.37    
Total input tokens:                      2353025   
Total generated tokens:                  296143    
Request throughput (req/s):              1.31      
Output token throughput (tok/s):         1216.84   
Total Token throughput (tok/s):          10885.29  
---------------Time to First Token----------------
Mean TTFT (ms):                          1784.95   
Median TTFT (ms):                        1093.22   
P90 TTFT (ms):                           3751.25   
P99 TTFT (ms):                           12769.89  
P99.9 TTFT (ms):                         19226.59  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          23.88     
Median TPOT (ms):                        24.30     
P90 TPOT (ms):                           28.06     
P99 TPOT (ms):                           31.23     
P99.9 TPOT (ms):                         35.56     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1942.62   
Median ITL (ms):                         1375.10   
P90 ITL (ms):                            4328.80   
P99 ITL (ms):                            8666.07   
P99.9 ITL (ms):                          13335.80  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          23851.89  
Median E2EL (ms):                        23909.12  
P90 E2EL (ms):                           28855.49  
P99 E2EL (ms):                           36763.04  
P99.9 E2EL (ms):                         44840.22  
==================================================
```

## 8k1k/w4a16-megamoe/tp4_conc64

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc64/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc64/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     640       
Benchmark duration (s):                  377.03    
Total input tokens:                      4729464   
Total generated tokens:                  589927    
Request throughput (req/s):              1.70      
Output token throughput (tok/s):         1564.66   
Total Token throughput (tok/s):          14108.63  
---------------Time to First Token----------------
Mean TTFT (ms):                          2393.91   
Median TTFT (ms):                        1193.97   
P90 TTFT (ms):                           5395.98   
P99 TTFT (ms):                           11896.63  
P99.9 TTFT (ms):                         25853.28  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          37.73     
Median TPOT (ms):                        38.95     
P90 TPOT (ms):                           44.84     
P99 TPOT (ms):                           53.65     
P99.9 TPOT (ms):                         57.87     
---------------Inter-token Latency----------------
Mean ITL (ms):                           3088.35   
Median ITL (ms):                         2025.75   
P90 ITL (ms):                            7184.10   
P99 ITL (ms):                            14663.65  
P99.9 ITL (ms):                          21005.98  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          37133.06  
Median E2EL (ms):                        37684.00  
P90 E2EL (ms):                           44870.04  
P99 E2EL (ms):                           56071.47  
P99.9 E2EL (ms):                         64591.56  
==================================================
```

## 8k1k/w4a16-megamoe/tp4_conc128

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc128/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc128/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     1280      
Benchmark duration (s):                  625.55    
Total input tokens:                      9457437   
Total generated tokens:                  1177591   
Request throughput (req/s):              2.05      
Output token throughput (tok/s):         1882.50   
Total Token throughput (tok/s):          17001.17  
---------------Time to First Token----------------
Mean TTFT (ms):                          3199.58   
Median TTFT (ms):                        1416.56   
P90 TTFT (ms):                           6696.62   
P99 TTFT (ms):                           23371.07  
P99.9 TTFT (ms):                         35710.35  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          63.88     
Median TPOT (ms):                        66.34     
P90 TPOT (ms):                           77.46     
P99 TPOT (ms):                           90.46     
P99.9 TPOT (ms):                         100.64    
---------------Inter-token Latency----------------
Mean ITL (ms):                           5248.50   
Median ITL (ms):                         3429.77   
P90 ITL (ms):                            12286.54  
P99 ITL (ms):                            26633.56  
P99.9 ITL (ms):                          39981.06  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          61913.11  
Median E2EL (ms):                        62737.68  
P90 E2EL (ms):                           75526.23  
P99 E2EL (ms):                           90631.95  
P99.9 E2EL (ms):                         104122.48 
==================================================
```

## 8k1k/w4a16-megamoe/tp4_conc256

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc256/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp4_conc256/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     2560      
Benchmark duration (s):                  1072.39   
Total input tokens:                      18878760  
Total generated tokens:                  2360332   
Request throughput (req/s):              2.39      
Output token throughput (tok/s):         2200.99   
Total Token throughput (tok/s):          19805.32  
---------------Time to First Token----------------
Mean TTFT (ms):                          4830.44   
Median TTFT (ms):                        1791.15   
P90 TTFT (ms):                           8687.94   
P99 TTFT (ms):                           44075.18  
P99.9 TTFT (ms):                         61945.24  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          109.30    
Median TPOT (ms):                        114.19    
P90 TPOT (ms):                           131.64    
P99 TPOT (ms):                           150.95    
P99.9 TPOT (ms):                         172.33    
---------------Inter-token Latency----------------
Mean ITL (ms):                           8968.67   
Median ITL (ms):                         5862.61   
P90 ITL (ms):                            20778.99  
P99 ITL (ms):                            45271.54  
P99.9 ITL (ms):                          68448.00  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          105573.81 
Median E2EL (ms):                        107983.57 
P90 E2EL (ms):                           129007.04 
P99 E2EL (ms):                           151503.88 
P99.9 E2EL (ms):                         177619.96 
==================================================
```

## 8k1k/w4a16-megamoe/tp8_conc4

[Complete client log](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp8_conc4/benchmark.log>) · [Full-precision result](<runs/c2-w4a16-megamoe-mem80-20260920/8k1k/w4a16-megamoe/tp8_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  81.82     
Total input tokens:                      294170    
Total generated tokens:                  36805     
Request throughput (req/s):              0.49      
Output token throughput (tok/s):         449.85    
Total Token throughput (tok/s):          4045.34   
---------------Time to First Token----------------
Mean TTFT (ms):                          629.13    
Median TTFT (ms):                        580.81    
P90 TTFT (ms):                           627.89    
P99 TTFT (ms):                           1207.78   
P99.9 TTFT (ms):                         1210.09   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          8.04      
Median TPOT (ms):                        8.20      
P90 TPOT (ms):                           9.10      
P99 TPOT (ms):                           9.80      
P99.9 TPOT (ms):                         9.88      
---------------Inter-token Latency----------------
Mean ITL (ms):                           646.01    
Median ITL (ms):                         422.57    
P90 ITL (ms):                            1502.95   
P99 ITL (ms):                            2604.18   
P99.9 ITL (ms):                          3136.73   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          8009.84   
Median E2EL (ms):                        7910.53   
P90 E2EL (ms):                           9183.84   
P99 E2EL (ms):                           9813.25   
P99.9 E2EL (ms):                         9878.11   
==================================================
```

