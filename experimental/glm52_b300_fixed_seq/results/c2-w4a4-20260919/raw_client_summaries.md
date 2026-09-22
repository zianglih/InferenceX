# Raw client benchmark summaries

Exactly **16** client logs are included below. Each contains one complete `Serving Benchmark Result` block, reproduced verbatim including the client's printed precision. Full-precision values remain in the accompanying `result.json` files. The source logs are unchanged; this document does not independently validate runtime configuration, request success, or planned matrix coverage.

<details><summary>中文</summary>

以下逐项原样摘录客户端打印的完整 `Serving Benchmark Result` 区块，保留原有显示精度。完整精度保留在各项 `result.json` 中，原始日志未作修改。此文档本身不验证运行配置、请求成功率或计划矩阵覆盖情况。

</details>

## 1k1k/w4a4-trtllm/tp4_conc4

[Complete client log](<1k1k/w4a4-trtllm/tp4_conc4/benchmark.log>) · [Full-precision result](<1k1k/w4a4-trtllm/tp4_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  44.51     
Total input tokens:                      37148     
Total generated tokens:                  36709     
Request throughput (req/s):              0.90      
Output token throughput (tok/s):         824.76    
Total Token throughput (tok/s):          1659.38   
---------------Time to First Token----------------
Mean TTFT (ms):                          105.52    
Median TTFT (ms):                        82.61     
P90 TTFT (ms):                           138.24    
P99 TTFT (ms):                           298.84    
P99.9 TTFT (ms):                         298.92    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          4.62      
Median TPOT (ms):                        4.60      
P90 TPOT (ms):                           5.05      
P99 TPOT (ms):                           6.30      
P99.9 TPOT (ms):                         6.76      
---------------Inter-token Latency----------------
Mean ITL (ms):                           361.17    
Median ITL (ms):                         261.87    
P90 ITL (ms):                            714.23    
P99 ITL (ms):                            1638.11   
P99.9 ITL (ms):                          2240.34   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          4331.26   
Median E2EL (ms):                        4248.70   
P90 E2EL (ms):                           4974.53   
P99 E2EL (ms):                           5707.83   
P99.9 E2EL (ms):                         6007.28   
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc8

[Complete client log](<1k1k/w4a4-trtllm/tp4_conc8/benchmark.log>) · [Full-precision result](<1k1k/w4a4-trtllm/tp4_conc8/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     80        
Benchmark duration (s):                  58.70     
Total input tokens:                      73937     
Total generated tokens:                  74326     
Request throughput (req/s):              1.36      
Output token throughput (tok/s):         1266.18   
Total Token throughput (tok/s):          2525.74   
---------------Time to First Token----------------
Mean TTFT (ms):                          109.78    
Median TTFT (ms):                        87.43     
P90 TTFT (ms):                           161.48    
P99 TTFT (ms):                           305.24    
P99.9 TTFT (ms):                         305.66    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          6.08      
Median TPOT (ms):                        6.10      
P90 TPOT (ms):                           6.88      
P99 TPOT (ms):                           7.40      
P99.9 TPOT (ms):                         7.83      
---------------Inter-token Latency----------------
Mean ITL (ms):                           479.68    
Median ITL (ms):                         342.79    
P90 ITL (ms):                            975.52    
P99 ITL (ms):                            1864.07   
P99.9 ITL (ms):                          2810.71   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          5746.04   
Median E2EL (ms):                        5735.39   
P90 E2EL (ms):                           6545.86   
P99 E2EL (ms):                           7511.11   
P99.9 E2EL (ms):                         7675.67   
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc16

[Complete client log](<1k1k/w4a4-trtllm/tp4_conc16/benchmark.log>) · [Full-precision result](<1k1k/w4a4-trtllm/tp4_conc16/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     160       
Benchmark duration (s):                  77.22     
Total input tokens:                      148067    
Total generated tokens:                  146669    
Request throughput (req/s):              2.07      
Output token throughput (tok/s):         1899.48   
Total Token throughput (tok/s):          3817.06   
---------------Time to First Token----------------
Mean TTFT (ms):                          137.43    
Median TTFT (ms):                        99.60     
P90 TTFT (ms):                           247.72    
P99 TTFT (ms):                           461.47    
P99.9 TTFT (ms):                         461.90    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          8.03      
Median TPOT (ms):                        8.03      
P90 TPOT (ms):                           9.08      
P99 TPOT (ms):                           10.02     
P99.9 TPOT (ms):                         11.62     
---------------Inter-token Latency----------------
Mean ITL (ms):                           673.31    
Median ITL (ms):                         493.88    
P90 ITL (ms):                            1394.44   
P99 ITL (ms):                            2651.39   
P99.9 ITL (ms):                          3787.95   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          7484.87   
Median E2EL (ms):                        7524.97   
P90 E2EL (ms):                           8599.34   
P99 E2EL (ms):                           9470.65   
P99.9 E2EL (ms):                         10052.56  
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc32

[Complete client log](<1k1k/w4a4-trtllm/tp4_conc32/benchmark.log>) · [Full-precision result](<1k1k/w4a4-trtllm/tp4_conc32/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     320       
Benchmark duration (s):                  102.56    
Total input tokens:                      294748    
Total generated tokens:                  295754    
Request throughput (req/s):              3.12      
Output token throughput (tok/s):         2883.64   
Total Token throughput (tok/s):          5757.47   
---------------Time to First Token----------------
Mean TTFT (ms):                          185.14    
Median TTFT (ms):                        108.76    
P90 TTFT (ms):                           272.98    
P99 TTFT (ms):                           811.86    
P99.9 TTFT (ms):                         813.41    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          10.51     
Median TPOT (ms):                        10.68     
P90 TPOT (ms):                           11.95     
P99 TPOT (ms):                           12.76     
P99.9 TPOT (ms):                         13.64     
---------------Inter-token Latency----------------
Mean ITL (ms):                           869.71    
Median ITL (ms):                         641.15    
P90 ITL (ms):                            1736.99   
P99 ITL (ms):                            3690.69   
P99.9 ITL (ms):                          5397.95   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          9890.56   
Median E2EL (ms):                        9900.38   
P90 E2EL (ms):                           11411.47  
P99 E2EL (ms):                           12735.51  
P99.9 E2EL (ms):                         13098.22  
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc64

[Complete client log](<1k1k/w4a4-trtllm/tp4_conc64/benchmark.log>) · [Full-precision result](<1k1k/w4a4-trtllm/tp4_conc64/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     640       
Benchmark duration (s):                  143.27    
Total input tokens:                      590968    
Total generated tokens:                  589849    
Request throughput (req/s):              4.47      
Output token throughput (tok/s):         4117.11   
Total Token throughput (tok/s):          8242.02   
---------------Time to First Token----------------
Mean TTFT (ms):                          317.02    
Median TTFT (ms):                        129.70    
P90 TTFT (ms):                           393.10    
P99 TTFT (ms):                           1802.13   
P99.9 TTFT (ms):                         4852.50   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          14.81     
Median TPOT (ms):                        15.01     
P90 TPOT (ms):                           17.00     
P99 TPOT (ms):                           18.73     
P99.9 TPOT (ms):                         20.05     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1223.12   
Median ITL (ms):                         872.95    
P90 ITL (ms):                            2524.27   
P99 ITL (ms):                            5078.48   
P99.9 ITL (ms):                          8261.50   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          13950.97  
Median E2EL (ms):                        13974.13  
P90 E2EL (ms):                           16248.17  
P99 E2EL (ms):                           18418.86  
P99.9 E2EL (ms):                         22245.93  
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc128

[Complete client log](<1k1k/w4a4-trtllm/tp4_conc128/benchmark.log>) · [Full-precision result](<1k1k/w4a4-trtllm/tp4_conc128/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     1280      
Benchmark duration (s):                  220.44    
Total input tokens:                      1181744   
Total generated tokens:                  1177796   
Request throughput (req/s):              5.81      
Output token throughput (tok/s):         5342.92   
Total Token throughput (tok/s):          10703.75  
---------------Time to First Token----------------
Mean TTFT (ms):                          414.74    
Median TTFT (ms):                        178.68    
P90 TTFT (ms):                           474.55    
P99 TTFT (ms):                           2731.17   
P99.9 TTFT (ms):                         2741.03   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          22.96     
Median TPOT (ms):                        23.27     
P90 TPOT (ms):                           26.73     
P99 TPOT (ms):                           29.45     
P99.9 TPOT (ms):                         35.33     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1889.64   
Median ITL (ms):                         1377.56   
P90 ITL (ms):                            3930.36   
P99 ITL (ms):                            7932.77   
P99.9 ITL (ms):                          11995.15  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          21506.37  
Median E2EL (ms):                        21590.46  
P90 E2EL (ms):                           25192.50  
P99 E2EL (ms):                           28572.89  
P99.9 E2EL (ms):                         35702.30  
==================================================
```

## 1k1k/w4a4-trtllm/tp4_conc256

[Complete client log](<1k1k/w4a4-trtllm/tp4_conc256/benchmark.log>) · [Full-precision result](<1k1k/w4a4-trtllm/tp4_conc256/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     2560      
Benchmark duration (s):                  546.66    
Total input tokens:                      2360891   
Total generated tokens:                  2360050   
Request throughput (req/s):              4.68      
Output token throughput (tok/s):         4317.19   
Total Token throughput (tok/s):          8635.92   
---------------Time to First Token----------------
Mean TTFT (ms):                          749.09    
Median TTFT (ms):                        404.36    
P90 TTFT (ms):                           902.72    
P99 TTFT (ms):                           5469.78   
P99.9 TTFT (ms):                         5474.61   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          57.59     
Median TPOT (ms):                        58.42     
P90 TPOT (ms):                           66.07     
P99 TPOT (ms):                           71.80     
P99.9 TPOT (ms):                         82.36     
---------------Inter-token Latency----------------
Mean ITL (ms):                           4781.80   
Median ITL (ms):                         3493.55   
P90 ITL (ms):                            9988.91   
P99 ITL (ms):                            19613.49  
P99.9 ITL (ms):                          29125.10  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          53784.15  
Median E2EL (ms):                        54165.25  
P90 E2EL (ms):                           63080.03  
P99 E2EL (ms):                           70347.69  
P99.9 E2EL (ms):                         79051.72  
==================================================
```

## 1k1k/w4a4-trtllm/tp8_conc4

[Complete client log](<1k1k/w4a4-trtllm/tp8_conc4/benchmark.log>) · [Full-precision result](<1k1k/w4a4-trtllm/tp8_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  35.92     
Total input tokens:                      37148     
Total generated tokens:                  36709     
Request throughput (req/s):              1.11      
Output token throughput (tok/s):         1022.01   
Total Token throughput (tok/s):          2056.24   
---------------Time to First Token----------------
Mean TTFT (ms):                          100.72    
Median TTFT (ms):                        76.75     
P90 TTFT (ms):                           117.83    
P99 TTFT (ms):                           304.60    
P99.9 TTFT (ms):                         304.61    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          3.71      
Median TPOT (ms):                        3.75      
P90 TPOT (ms):                           4.12      
P99 TPOT (ms):                           4.29      
P99.9 TPOT (ms):                         4.32      
---------------Inter-token Latency----------------
Mean ITL (ms):                           320.58    
Median ITL (ms):                         231.58    
P90 ITL (ms):                            677.53    
P99 ITL (ms):                            1140.32   
P99.9 ITL (ms):                          1966.04   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          3498.91   
Median E2EL (ms):                        3465.26   
P90 E2EL (ms):                           4038.99   
P99 E2EL (ms):                           4186.83   
P99.9 E2EL (ms):                         4212.52   
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc4

[Complete client log](<8k1k/w4a4-trtllm/tp4_conc4/benchmark.log>) · [Full-precision result](<8k1k/w4a4-trtllm/tp4_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  51.57     
Total input tokens:                      294170    
Total generated tokens:                  36805     
Request throughput (req/s):              0.78      
Output token throughput (tok/s):         713.71    
Total Token throughput (tok/s):          6418.17   
---------------Time to First Token----------------
Mean TTFT (ms):                          382.71    
Median TTFT (ms):                        314.53    
P90 TTFT (ms):                           583.67    
P99 TTFT (ms):                           1040.11   
P99.9 TTFT (ms):                         1040.23   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          5.05      
Median TPOT (ms):                        5.16      
P90 TPOT (ms):                           5.55      
P99 TPOT (ms):                           5.80      
P99.9 TPOT (ms):                         5.86      
---------------Inter-token Latency----------------
Mean ITL (ms):                           426.01    
Median ITL (ms):                         294.33    
P90 ITL (ms):                            880.91    
P99 ITL (ms):                            2101.11   
P99.9 ITL (ms):                          2957.73   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          5026.20   
Median E2EL (ms):                        5088.67   
P90 E2EL (ms):                           5653.17   
P99 E2EL (ms):                           6130.82   
P99.9 E2EL (ms):                         6329.42   
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc8

[Complete client log](<8k1k/w4a4-trtllm/tp4_conc8/benchmark.log>) · [Full-precision result](<8k1k/w4a4-trtllm/tp4_conc8/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     80        
Benchmark duration (s):                  76.62     
Total input tokens:                      585049    
Total generated tokens:                  74069     
Request throughput (req/s):              1.04      
Output token throughput (tok/s):         966.69    
Total Token throughput (tok/s):          8602.29   
---------------Time to First Token----------------
Mean TTFT (ms):                          512.78    
Median TTFT (ms):                        312.77    
P90 TTFT (ms):                           612.45    
P99 TTFT (ms):                           2907.28   
P99.9 TTFT (ms):                         6720.10   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          7.58      
Median TPOT (ms):                        7.54      
P90 TPOT (ms):                           8.84      
P99 TPOT (ms):                           9.81      
P99.9 TPOT (ms):                         9.84      
---------------Inter-token Latency----------------
Mean ITL (ms):                           630.56    
Median ITL (ms):                         462.15    
P90 ITL (ms):                            1317.17   
P99 ITL (ms):                            2911.16   
P99.9 ITL (ms):                          3902.15   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          7527.74   
Median E2EL (ms):                        7485.25   
P90 E2EL (ms):                           8686.29   
P99 E2EL (ms):                           10926.68  
P99.9 E2EL (ms):                         13586.07  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc16

[Complete client log](<8k1k/w4a4-trtllm/tp4_conc16/benchmark.log>) · [Full-precision result](<8k1k/w4a4-trtllm/tp4_conc16/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     160       
Benchmark duration (s):                  113.67    
Total input tokens:                      1175512   
Total generated tokens:                  146426    
Request throughput (req/s):              1.41      
Output token throughput (tok/s):         1288.14   
Total Token throughput (tok/s):          11629.35  
---------------Time to First Token----------------
Mean TTFT (ms):                          650.57    
Median TTFT (ms):                        332.12    
P90 TTFT (ms):                           849.81    
P99 TTFT (ms):                           3711.87   
P99.9 TTFT (ms):                         8191.77   
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          11.43     
Median TPOT (ms):                        11.48     
P90 TPOT (ms):                           13.34     
P99 TPOT (ms):                           15.45     
P99.9 TPOT (ms):                         16.86     
---------------Inter-token Latency----------------
Mean ITL (ms):                           932.99    
Median ITL (ms):                         665.24    
P90 ITL (ms):                            1992.54   
P99 ITL (ms):                            3864.72   
P99.9 ITL (ms):                          5947.50   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          11111.71  
Median E2EL (ms):                        11125.49  
P90 E2EL (ms):                           13347.67  
P99 E2EL (ms):                           15900.57  
P99.9 E2EL (ms):                         18876.82  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc32

[Complete client log](<8k1k/w4a4-trtllm/tp4_conc32/benchmark.log>) · [Full-precision result](<8k1k/w4a4-trtllm/tp4_conc32/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     320       
Benchmark duration (s):                  172.51    
Total input tokens:                      2353025   
Total generated tokens:                  296143    
Request throughput (req/s):              1.85      
Output token throughput (tok/s):         1716.64   
Total Token throughput (tok/s):          15356.33  
---------------Time to First Token----------------
Mean TTFT (ms):                          889.37    
Median TTFT (ms):                        350.85    
P90 TTFT (ms):                           1025.63   
P99 TTFT (ms):                           7496.37   
P99.9 TTFT (ms):                         12513.72  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          17.36     
Median TPOT (ms):                        17.74     
P90 TPOT (ms):                           20.43     
P99 TPOT (ms):                           24.28     
P99.9 TPOT (ms):                         25.97     
---------------Inter-token Latency----------------
Mean ITL (ms):                           1438.73   
Median ITL (ms):                         979.98    
P90 ITL (ms):                            3225.68   
P99 ITL (ms):                            6659.94   
P99.9 ITL (ms):                          8823.66   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          16944.66  
Median E2EL (ms):                        16896.09  
P90 E2EL (ms):                           20297.15  
P99 E2EL (ms):                           25339.01  
P99.9 E2EL (ms):                         29912.19  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc64

[Complete client log](<8k1k/w4a4-trtllm/tp4_conc64/benchmark.log>) · [Full-precision result](<8k1k/w4a4-trtllm/tp4_conc64/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     640       
Benchmark duration (s):                  284.49    
Total input tokens:                      4729464   
Total generated tokens:                  589927    
Request throughput (req/s):              2.25      
Output token throughput (tok/s):         2073.63   
Total Token throughput (tok/s):          18697.95  
---------------Time to First Token----------------
Mean TTFT (ms):                          1343.10   
Median TTFT (ms):                        434.08    
P90 TTFT (ms):                           1109.97   
P99 TTFT (ms):                           14729.33  
P99.9 TTFT (ms):                         18587.19  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          29.01     
Median TPOT (ms):                        29.74     
P90 TPOT (ms):                           34.33     
P99 TPOT (ms):                           40.49     
P99.9 TPOT (ms):                         44.16     
---------------Inter-token Latency----------------
Mean ITL (ms):                           2404.82   
Median ITL (ms):                         1631.09   
P90 ITL (ms):                            5337.51   
P99 ITL (ms):                            11190.63  
P99.9 ITL (ms):                          16071.56  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          28051.63  
Median E2EL (ms):                        28031.66  
P90 E2EL (ms):                           34431.39  
P99 E2EL (ms):                           43261.87  
P99.9 E2EL (ms):                         49264.43  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc128

[Complete client log](<8k1k/w4a4-trtllm/tp4_conc128/benchmark.log>) · [Full-precision result](<8k1k/w4a4-trtllm/tp4_conc128/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     1280      
Benchmark duration (s):                  498.48    
Total input tokens:                      9457437   
Total generated tokens:                  1177591   
Request throughput (req/s):              2.57      
Output token throughput (tok/s):         2362.35   
Total Token throughput (tok/s):          21334.82  
---------------Time to First Token----------------
Mean TTFT (ms):                          2300.45   
Median TTFT (ms):                        624.82    
P90 TTFT (ms):                           2843.06   
P99 TTFT (ms):                           28911.71  
P99.9 TTFT (ms):                         30830.62  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          51.16     
Median TPOT (ms):                        52.54     
P90 TPOT (ms):                           60.75     
P99 TPOT (ms):                           73.05     
P99.9 TPOT (ms):                         81.44     
---------------Inter-token Latency----------------
Mean ITL (ms):                           4223.23   
Median ITL (ms):                         2808.10   
P90 ITL (ms):                            9414.90   
P99 ITL (ms):                            21878.74  
P99.9 ITL (ms):                          31079.24  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          49326.78  
Median E2EL (ms):                        49234.54  
P90 E2EL (ms):                           60804.86  
P99 E2EL (ms):                           78761.52  
P99.9 E2EL (ms):                         84488.37  
==================================================
```

## 8k1k/w4a4-trtllm/tp4_conc256

[Complete client log](<8k1k/w4a4-trtllm/tp4_conc256/benchmark.log>) · [Full-precision result](<8k1k/w4a4-trtllm/tp4_conc256/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     2560      
Benchmark duration (s):                  1088.32   
Total input tokens:                      18878760  
Total generated tokens:                  2360332   
Request throughput (req/s):              2.35      
Output token throughput (tok/s):         2168.79   
Total Token throughput (tok/s):          19515.56  
---------------Time to First Token----------------
Mean TTFT (ms):                          4244.15   
Median TTFT (ms):                        972.41    
P90 TTFT (ms):                           3590.96   
P99 TTFT (ms):                           57855.89  
P99.9 TTFT (ms):                         62979.44  
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          112.56    
Median TPOT (ms):                        115.01    
P90 TPOT (ms):                           133.34    
P99 TPOT (ms):                           159.57    
P99.9 TPOT (ms):                         177.82    
---------------Inter-token Latency----------------
Mean ITL (ms):                           9307.36   
Median ITL (ms):                         6324.24   
P90 ITL (ms):                            20227.89  
P99 ITL (ms):                            44789.94  
P99.9 ITL (ms):                          64323.83  
----------------End-to-end Latency----------------
Mean E2EL (ms):                          107933.94 
Median E2EL (ms):                        107607.62 
P90 E2EL (ms):                           131838.83 
P99 E2EL (ms):                           172044.14 
P99.9 E2EL (ms):                         183627.10 
==================================================
```

## 8k1k/w4a4-trtllm/tp8_conc4

[Complete client log](<8k1k/w4a4-trtllm/tp8_conc4/benchmark.log>) · [Full-precision result](<8k1k/w4a4-trtllm/tp8_conc4/result.json>)

```text
============ Serving Benchmark Result ============
Successful requests:                     40        
Benchmark duration (s):                  43.81     
Total input tokens:                      294170    
Total generated tokens:                  36805     
Request throughput (req/s):              0.91      
Output token throughput (tok/s):         840.18    
Total Token throughput (tok/s):          7555.47   
---------------Time to First Token----------------
Mean TTFT (ms):                          335.97    
Median TTFT (ms):                        277.78    
P90 TTFT (ms):                           481.78    
P99 TTFT (ms):                           907.36    
P99.9 TTFT (ms):                         907.49    
-----Time per Output Token (excl. 1st token)------
Mean TPOT (ms):                          4.27      
Median TPOT (ms):                        4.36      
P90 TPOT (ms):                           4.95      
P99 TPOT (ms):                           5.45      
P99.9 TPOT (ms):                         5.60      
---------------Inter-token Latency----------------
Mean ITL (ms):                           342.16    
Median ITL (ms):                         242.42    
P90 ITL (ms):                            731.30    
P99 ITL (ms):                            1249.63   
P99.9 ITL (ms):                          1706.45   
----------------End-to-end Latency----------------
Mean E2EL (ms):                          4253.67   
Median E2EL (ms):                        4141.18   
P90 E2EL (ms):                           5167.86   
P99 E2EL (ms):                           5440.31   
P99.9 E2EL (ms):                         5484.10   
==================================================
```

