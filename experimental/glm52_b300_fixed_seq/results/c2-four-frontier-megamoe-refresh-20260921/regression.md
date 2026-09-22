[English](regression.md) | [简体中文](regression_zh.md)

# Original-Mega-first regression comparison

Status: **regression_comparison**. This separate regression view keeps original16 Mega out of main48; final charts additionally show their own separate frontier.

| Workload / TP / C | Arm | Output tok/s/GPU | Interactivity tok/s | Median TPOT ms | Median TTFT ms | Median E2EL ms | p95 TPOT ms |
|---|---|---:|---:|---:|---:|---:|---:|
| 1k1k / 4 / 128 | new_mega | 1047.430106 | 33.405298 | 29.935372 | 517.310060 | 28138.841880 | not saved |
| 1k1k / 4 / 128 | original_mega | 1072.480061 | 34.658960 | 28.852568 | 531.065708 | 27257.934953 | not saved |
| 1k1k / 4 / 128 | split | 917.363631 | 29.413951 | 33.997472 | 598.149209 | 31924.891559 | not saved |
| 1k1k / 4 / 128 | trtllm | 1036.160466 | 33.362347 | 29.973910 | 515.985024 | 28202.113637 | not saved |
| 1k1k / 4 / 16 | new_mega | 330.158865 | 89.393468 | 11.186500 | 301.501642 | 10836.418176 | not saved |
| 1k1k / 4 / 16 | original_mega | 315.063790 | 85.372710 | 11.713345 | 390.385216 | 11414.005206 | not saved |
| 1k1k / 4 / 16 | split | 308.876334 | 84.481959 | 11.836847 | 343.910744 | 11447.017115 | not saved |
| 1k1k / 4 / 16 | trtllm | 327.841154 | 88.189992 | 11.339155 | 302.262790 | 10736.125545 | not saved |
| 1k1k / 4 / 256 | new_mega | 1354.029495 | 21.419275 | 46.686922 | 627.776704 | 43820.170413 | not saved |
| 1k1k / 4 / 256 | original_mega | 1466.501235 | 23.331841 | 42.859884 | 571.186753 | 40233.113132 | not saved |
| 1k1k / 4 / 256 | split | 1324.608983 | 21.066775 | 47.468109 | 595.518674 | 44643.512408 | not saved |
| 1k1k / 4 / 256 | trtllm | 1235.308464 | 19.416322 | 51.503061 | 725.958635 | 48401.588832 | not saved |
| 1k1k / 4 / 32 | new_mega | 510.972458 | 68.875882 | 14.518870 | 331.348063 | 14062.017240 | not saved |
| 1k1k / 4 / 32 | original_mega | 526.362023 | 71.315441 | 14.022209 | 301.532212 | 13484.445830 | not saved |
| 1k1k / 4 / 32 | split | 472.571489 | 63.163355 | 15.831964 | 426.048949 | 15191.480624 | not saved |
| 1k1k / 4 / 32 | trtllm | 489.798147 | 66.162738 | 15.114248 | 394.583960 | 14610.117773 | not saved |
| 1k1k / 4 / 4 | new_mega | 132.624042 | 141.484371 | 7.067918 | 278.355537 | 6740.176271 | not saved |
| 1k1k / 4 / 4 | original_mega | 128.056265 | 137.327614 | 7.281857 | 266.616662 | 6948.737552 | not saved |
| 1k1k / 4 / 4 | split | 119.994486 | 133.954517 | 7.465220 | 296.718565 | 7407.417925 | not saved |
| 1k1k / 4 / 4 | trtllm | 132.285868 | 141.276142 | 7.078336 | 273.501431 | 6870.053865 | not saved |
| 1k1k / 4 / 64 | new_mega | 748.100647 | 49.138232 | 20.350752 | 461.741173 | 19427.673156 | not saved |
| 1k1k / 4 / 64 | original_mega | 749.322548 | 49.333511 | 20.270197 | 436.901905 | 19304.630309 | not saved |
| 1k1k / 4 / 64 | split | 643.768015 | 42.193209 | 23.700496 | 538.952806 | 22554.735970 | not saved |
| 1k1k / 4 / 64 | trtllm | 679.052549 | 44.276952 | 22.585114 | 555.363863 | 21360.301244 | not saved |
| 1k1k / 4 / 8 | new_mega | 213.891324 | 115.006958 | 8.695126 | 278.740513 | 8601.009244 | not saved |
| 1k1k / 4 / 8 | original_mega | 203.409913 | 109.816574 | 9.106094 | 273.803842 | 8940.476247 | not saved |
| 1k1k / 4 / 8 | split | 199.437557 | 108.475815 | 9.218645 | 305.359444 | 9154.440361 | not saved |
| 1k1k / 4 / 8 | trtllm | 208.041505 | 112.530877 | 8.886450 | 279.115836 | 8665.449972 | not saved |
| 1k1k / 8 / 4 | new_mega | 70.643929 | 150.044449 | 6.664692 | 273.960224 | 6487.543793 | not saved |
| 1k1k / 8 / 4 | original_mega | 65.905381 | 139.196603 | 7.184083 | 261.021328 | 6920.678254 | not saved |
| 1k1k / 8 / 4 | split | 61.015383 | 132.888160 | 7.525125 | 294.227992 | 7240.864714 | not saved |
| 1k1k / 8 / 4 | trtllm | 63.806441 | 140.017300 | 7.141975 | 279.960074 | 6946.582102 | not saved |
| 8k1k / 4 / 128 | new_mega | 518.027957 | 16.572426 | 60.341197 | 1205.573986 | 57230.491664 | not saved |
| 8k1k / 4 / 128 | original_mega | 470.624529 | 15.073434 | 66.341882 | 1416.563798 | 62737.675719 | not saved |
| 8k1k / 4 / 128 | split | 509.863807 | 16.455060 | 60.771579 | 1213.877333 | 57696.174201 | not saved |
| 8k1k / 4 / 128 | trtllm | 586.492224 | 18.872581 | 52.986924 | 1105.559302 | 50074.804972 | not saved |
| 8k1k / 4 / 16 | new_mega | 248.455324 | 70.537661 | 14.176824 | 658.278077 | 14032.860960 | not saved |
| 8k1k / 4 / 16 | original_mega | 222.771697 | 63.508029 | 15.746041 | 686.549250 | 15569.167908 | not saved |
| 8k1k / 4 / 16 | split | 227.676571 | 65.858361 | 15.184101 | 735.632963 | 15383.345565 | not saved |
| 8k1k / 4 / 16 | trtllm | 262.413468 | 74.674299 | 13.391488 | 751.048711 | 13361.231522 | not saved |
| 8k1k / 4 / 256 | new_mega | 591.458530 | 9.345877 | 106.999054 | 1759.810612 | 100991.660146 | not saved |
| 8k1k / 4 / 256 | original_mega | 550.248568 | 8.757005 | 114.194292 | 1791.145396 | 107983.570680 | not saved |
| 8k1k / 4 / 256 | split | 584.828149 | 9.303878 | 107.482066 | 1588.726515 | 101632.068347 | not saved |
| 8k1k / 4 / 256 | trtllm | 694.865552 | 11.045281 | 90.536399 | 1476.763242 | 85635.248041 | not saved |
| 8k1k / 4 / 32 | new_mega | 335.827591 | 45.527189 | 21.964897 | 955.483927 | 21514.080226 | not saved |
| 8k1k / 4 / 32 | original_mega | 304.208853 | 41.147211 | 24.302984 | 1093.219516 | 23909.116739 | not saved |
| 8k1k / 4 / 32 | split | 334.263405 | 46.116767 | 21.684087 | 909.233886 | 21222.861307 | not saved |
| 8k1k / 4 / 32 | trtllm | 362.701097 | 49.637475 | 20.146069 | 761.222552 | 20080.953778 | not saved |
| 8k1k / 4 / 4 | new_mega | 114.125565 | 131.230909 | 7.620156 | 565.425701 | 7684.169163 | not saved |
| 8k1k / 4 / 4 | original_mega | 107.459001 | 120.773982 | 8.279929 | 605.053452 | 8232.733449 | not saved |
| 8k1k / 4 / 4 | split | 107.988076 | 124.468965 | 8.034131 | 635.486976 | 8151.892970 | not saved |
| 8k1k / 4 / 4 | trtllm | 118.400751 | 138.478648 | 7.221330 | 462.951541 | 7491.098019 | not saved |
| 8k1k / 4 / 64 | new_mega | 435.387470 | 28.433077 | 35.170306 | 1047.815474 | 33932.730180 | not saved |
| 8k1k / 4 / 64 | original_mega | 391.166091 | 25.671804 | 38.953243 | 1193.971575 | 37683.997512 | not saved |
| 8k1k / 4 / 64 | split | 418.559512 | 27.337966 | 36.579166 | 997.449573 | 34934.650990 | not saved |
| 8k1k / 4 / 64 | trtllm | 474.733110 | 31.159667 | 32.092769 | 877.272045 | 30766.821100 | not saved |
| 8k1k / 4 / 8 | new_mega | 178.951885 | 100.653943 | 9.935031 | 680.432838 | 10148.767629 | not saved |
| 8k1k / 4 / 8 | original_mega | 162.419426 | 93.224222 | 10.726826 | 671.264200 | 11108.474569 | not saved |
| 8k1k / 4 / 8 | split | 171.711571 | 97.038671 | 10.305170 | 574.673367 | 10350.561440 | not saved |
| 8k1k / 4 / 8 | trtllm | 183.116052 | 102.415418 | 9.764155 | 735.450974 | 9861.833113 | not saved |
| 8k1k / 8 / 4 | new_mega | 61.808411 | 135.896259 | 7.358554 | 585.975992 | 7364.546708 | not saved |
| 8k1k / 8 / 4 | original_mega | 56.231134 | 121.960400 | 8.199383 | 580.809834 | 7910.525426 | not saved |
| 8k1k / 8 / 4 | split | 53.237445 | 116.316665 | 8.597220 | 620.841202 | 8415.241264 | not saved |
| 8k1k / 8 / 4 | trtllm | 57.518821 | 128.752912 | 7.766815 | 563.413697 | 7771.737311 | not saved |

Saved tail latencies (milliseconds; p95 is not saved):

| Workload / TP / C | Arm | p90 TTFT | p99 TTFT | p90 TPOT | p99 TPOT | p90 E2EL | p99 E2EL |
|---|---|---:|---:|---:|---:|---:|---:|
| 1k1k / 4 / 128 | new_mega | 2003.366413 | 2992.176736 | 34.056227 | 37.359565 | 32753.882564 | 37021.932245 |
| 1k1k / 4 / 128 | original_mega | 2110.553818 | 3063.158759 | 32.836879 | 36.157183 | 31685.044746 | 35794.073433 |
| 1k1k / 4 / 128 | split | 2524.690661 | 3571.930863 | 38.806380 | 43.436401 | 37595.120426 | 43678.084493 |
| 1k1k / 4 / 128 | trtllm | 2187.893725 | 3352.360958 | 34.908442 | 38.908032 | 33617.351402 | 38811.386531 |
| 1k1k / 4 / 16 | new_mega | 1488.171162 | 2507.464061 | 12.494093 | 13.451314 | 12855.628495 | 13964.043993 |
| 1k1k / 4 / 16 | original_mega | 1540.062082 | 2416.830520 | 13.198084 | 14.061680 | 13260.320742 | 14439.276870 |
| 1k1k / 4 / 16 | split | 1941.402747 | 3442.956629 | 13.406565 | 14.690133 | 13484.265313 | 15552.288118 |
| 1k1k / 4 / 16 | trtllm | 1494.650155 | 2466.545642 | 12.661011 | 14.680779 | 12699.472306 | 15274.764051 |
| 1k1k / 4 / 256 | new_mega | 3090.805444 | 5523.582480 | 53.882705 | 60.231456 | 51726.059978 | 59937.343321 |
| 1k1k / 4 / 256 | original_mega | 2685.706642 | 5596.684234 | 49.512096 | 55.063283 | 47965.046019 | 54246.700334 |
| 1k1k / 4 / 256 | split | 2945.964771 | 6220.187128 | 54.845131 | 60.202135 | 52347.543325 | 59461.971169 |
| 1k1k / 4 / 256 | trtllm | 3026.021952 | 4818.303588 | 59.803790 | 65.555811 | 57390.103405 | 64800.517955 |
| 1k1k / 4 / 32 | new_mega | 1568.645791 | 3022.625813 | 16.753514 | 18.377031 | 16611.461866 | 18203.671795 |
| 1k1k / 4 / 32 | original_mega | 1488.077855 | 2667.777714 | 15.729998 | 16.841645 | 15955.533353 | 17097.910774 |
| 1k1k / 4 / 32 | split | 1793.326566 | 3138.515203 | 17.807545 | 19.329700 | 17734.181110 | 19753.905202 |
| 1k1k / 4 / 32 | trtllm | 1812.275493 | 3162.575432 | 17.256721 | 19.511708 | 17318.156632 | 19206.618525 |
| 1k1k / 4 / 4 | new_mega | 942.355452 | 1570.479140 | 7.498161 | 8.127629 | 7823.276038 | 8415.639707 |
| 1k1k / 4 / 4 | original_mega | 1003.526003 | 1969.620988 | 7.947691 | 8.363181 | 8173.259129 | 9146.726174 |
| 1k1k / 4 / 4 | split | 1621.043245 | 2536.056264 | 8.383064 | 8.887659 | 9034.189184 | 9861.715524 |
| 1k1k / 4 / 4 | trtllm | 711.028222 | 1083.620446 | 7.833114 | 8.311896 | 7751.508887 | 8341.376039 |
| 1k1k / 4 / 64 | new_mega | 1738.195666 | 2449.849520 | 23.433689 | 25.817172 | 22926.684461 | 26635.390324 |
| 1k1k / 4 / 64 | original_mega | 1773.319940 | 2718.601419 | 23.097953 | 25.687159 | 22681.776017 | 25864.655145 |
| 1k1k / 4 / 64 | split | 2175.355378 | 3980.771243 | 26.993933 | 29.868036 | 26540.070135 | 30680.962140 |
| 1k1k / 4 / 64 | trtllm | 1858.350747 | 4383.324516 | 26.227636 | 29.053119 | 25252.736557 | 29941.042823 |
| 1k1k / 4 / 8 | new_mega | 1367.575472 | 2109.389382 | 9.750671 | 10.670347 | 9762.613632 | 10728.276511 |
| 1k1k / 4 / 8 | original_mega | 1399.480853 | 2665.054699 | 10.139564 | 10.989725 | 10202.230764 | 12086.988765 |
| 1k1k / 4 / 8 | split | 1295.621671 | 2446.276464 | 10.411093 | 10.942805 | 10255.304353 | 11604.969150 |
| 1k1k / 4 / 8 | trtllm | 1333.209370 | 2566.939902 | 9.708118 | 10.260469 | 10135.209625 | 11294.492866 |
| 1k1k / 8 / 4 | new_mega | 316.790902 | 511.275985 | 7.160383 | 7.507701 | 7309.242456 | 7603.103684 |
| 1k1k / 8 / 4 | original_mega | 298.535957 | 507.037220 | 7.756798 | 8.031561 | 7766.301859 | 8152.512209 |
| 1k1k / 8 / 4 | split | 303.720069 | 315.103907 | 8.335453 | 8.722731 | 8127.140129 | 8632.624551 |
| 1k1k / 8 / 4 | trtllm | 300.623436 | 304.371523 | 8.265035 | 9.034570 | 7763.568756 | 8925.532342 |
| 8k1k / 4 / 128 | new_mega | 5967.339426 | 21299.799937 | 69.222238 | 79.659779 | 68244.372675 | 80455.199368 |
| 8k1k / 4 / 128 | original_mega | 6696.617276 | 23371.065849 | 77.461635 | 90.458974 | 75526.229074 | 90631.952289 |
| 8k1k / 4 / 128 | split | 6286.900494 | 23841.717647 | 70.208243 | 80.035983 | 69453.678905 | 82577.201290 |
| 8k1k / 4 / 128 | trtllm | 5143.248211 | 18054.396658 | 61.365834 | 70.329655 | 60555.318164 | 71102.616421 |
| 8k1k / 4 / 16 | new_mega | 2584.676292 | 11625.930008 | 16.273736 | 17.680208 | 17000.082415 | 24848.629374 |
| 8k1k / 4 / 16 | original_mega | 2911.963955 | 12755.791190 | 18.141259 | 20.772748 | 18806.443793 | 25906.855590 |
| 8k1k / 4 / 16 | split | 3312.252899 | 12348.983430 | 17.204569 | 22.579613 | 18433.615508 | 26771.084323 |
| 8k1k / 4 / 16 | trtllm | 2373.627196 | 10587.986961 | 15.723686 | 18.086051 | 15993.021542 | 24401.710002 |
| 8k1k / 4 / 256 | new_mega | 7554.546325 | 42579.037090 | 122.659961 | 142.976161 | 120759.415043 | 145089.201673 |
| 8k1k / 4 / 256 | original_mega | 8687.942210 | 44075.178635 | 131.638591 | 150.947387 | 129007.037758 | 151503.880312 |
| 8k1k / 4 / 256 | split | 8130.946887 | 46296.686568 | 123.747003 | 144.215083 | 121972.794657 | 149341.605757 |
| 8k1k / 4 / 256 | trtllm | 6724.333847 | 34732.192013 | 104.092758 | 120.438023 | 102738.808191 | 122023.973070 |
| 8k1k / 4 / 32 | new_mega | 3451.915866 | 12856.890374 | 25.288344 | 29.165402 | 26065.922625 | 34142.752575 |
| 8k1k / 4 / 32 | original_mega | 3751.252602 | 12769.890491 | 28.061267 | 31.228945 | 28855.493455 | 36763.038671 |
| 8k1k / 4 / 32 | split | 3746.342875 | 12835.602224 | 25.367096 | 29.021437 | 26103.819739 | 34603.229425 |
| 8k1k / 4 / 32 | trtllm | 3333.688696 | 10768.744264 | 23.510817 | 26.295733 | 23809.508574 | 30487.990466 |
| 8k1k / 4 / 4 | new_mega | 1136.803300 | 3567.256023 | 8.373742 | 9.868720 | 9034.382472 | 10487.924571 |
| 8k1k / 4 / 4 | original_mega | 1324.782221 | 2267.726987 | 9.253841 | 9.935239 | 9567.639220 | 10478.849555 |
| 8k1k / 4 / 4 | split | 1366.392580 | 3270.125150 | 9.184634 | 10.684796 | 9206.269104 | 12438.262874 |
| 8k1k / 4 / 4 | trtllm | 1655.702891 | 2090.433084 | 8.308981 | 9.101547 | 8731.816484 | 9064.253202 |
| 8k1k / 4 / 64 | new_mega | 4718.859147 | 10909.993461 | 40.535841 | 46.512654 | 39787.371517 | 46588.385381 |
| 8k1k / 4 / 64 | original_mega | 5395.981013 | 11896.631859 | 44.843362 | 53.653016 | 44870.041016 | 56071.465319 |
| 8k1k / 4 / 64 | split | 4452.503556 | 11925.337869 | 41.846115 | 47.152783 | 41304.632645 | 48320.894878 |
| 8k1k / 4 / 64 | trtllm | 4106.022326 | 9192.624558 | 36.993112 | 41.091603 | 36846.660950 | 43101.648373 |
| 8k1k / 4 / 8 | new_mega | 2021.957453 | 3580.010997 | 11.254651 | 12.069213 | 11866.393027 | 13477.320782 |
| 8k1k / 4 / 8 | original_mega | 2014.759448 | 4134.160818 | 12.425106 | 14.721064 | 13128.318189 | 15616.110918 |
| 8k1k / 4 / 8 | split | 1922.010675 | 3091.342692 | 11.600723 | 12.874049 | 12266.783113 | 13607.828981 |
| 8k1k / 4 / 8 | trtllm | 1585.461653 | 3171.337176 | 10.849070 | 12.757427 | 11944.982403 | 13139.064010 |
| 8k1k / 8 / 4 | new_mega | 845.211685 | 902.328518 | 8.386048 | 8.997721 | 8345.334702 | 9274.596188 |
| 8k1k / 8 / 4 | original_mega | 627.885943 | 1207.776120 | 9.099280 | 9.804997 | 9183.844974 | 9813.245238 |
| 8k1k / 8 / 4 | split | 898.835962 | 970.314128 | 9.483014 | 10.105760 | 9179.933142 | 10271.418910 |
| 8k1k / 8 / 4 | trtllm | 743.310250 | 879.866600 | 9.001896 | 9.564095 | 8826.816659 | 9840.958111 |

New-Mega tail latency change versus each matched control (percent; positive is slower):

| Workload / TP / C | Control | p90 TTFT | p99 TTFT | p90 TPOT | p99 TPOT | p90 E2EL | p99 E2EL |
|---|---|---:|---:|---:|---:|---:|---:|
| 1k1k / 4 / 128 | original_mega | -5.079% | -2.317% | +3.713% | +3.325% | +3.373% | +3.430% |
| 1k1k / 4 / 128 | split | -20.649% | -16.231% | -12.241% | -13.990% | -12.877% | -15.239% |
| 1k1k / 4 / 128 | trtllm | -8.434% | -10.744% | -2.441% | -3.980% | -2.569% | -4.611% |
| 1k1k / 4 / 16 | original_mega | -3.369% | +3.750% | -5.334% | -4.341% | -3.052% | -3.291% |
| 1k1k / 4 / 16 | split | -23.346% | -27.171% | -6.806% | -8.433% | -4.662% | -10.212% |
| 1k1k / 4 / 16 | trtllm | -0.433% | +1.659% | -1.318% | -8.375% | +1.230% | -8.581% |
| 1k1k / 4 / 256 | original_mega | +15.084% | -1.306% | +8.827% | +9.386% | +7.841% | +10.490% |
| 1k1k / 4 / 256 | split | +4.917% | -11.199% | -1.755% | +0.049% | -1.187% | +0.799% |
| 1k1k / 4 / 256 | trtllm | +2.141% | +14.637% | -9.901% | -8.122% | -9.869% | -7.505% |
| 1k1k / 4 / 32 | original_mega | +5.414% | +13.301% | +6.507% | +9.117% | +4.111% | +6.467% |
| 1k1k / 4 / 32 | split | -12.529% | -3.692% | -5.919% | -4.929% | -6.331% | -7.848% |
| 1k1k / 4 / 32 | trtllm | -13.443% | -4.425% | -2.916% | -5.815% | -4.081% | -5.222% |
| 1k1k / 4 / 4 | original_mega | -6.096% | -20.265% | -5.656% | -2.817% | -4.282% | -7.993% |
| 1k1k / 4 / 4 | split | -41.867% | -38.074% | -10.556% | -8.552% | -13.404% | -14.664% |
| 1k1k / 4 / 4 | trtllm | +32.534% | +44.929% | -4.276% | -2.217% | +0.926% | +0.890% |
| 1k1k / 4 / 64 | original_mega | -1.981% | -9.886% | +1.454% | +0.506% | +1.080% | +2.980% |
| 1k1k / 4 / 64 | split | -20.096% | -38.458% | -13.189% | -13.563% | -13.615% | -13.186% |
| 1k1k / 4 / 64 | trtllm | -6.466% | -44.110% | -10.653% | -11.138% | -9.211% | -11.041% |
| 1k1k / 4 / 8 | original_mega | -2.280% | -20.850% | -3.835% | -2.906% | -4.309% | -11.241% |
| 1k1k / 4 / 8 | split | +5.554% | -13.771% | -6.343% | -2.490% | -4.804% | -7.554% |
| 1k1k / 4 / 8 | trtllm | +2.578% | -17.825% | +0.438% | +3.995% | -3.676% | -5.013% |
| 1k1k / 8 / 4 | original_mega | +6.115% | +0.836% | -7.689% | -6.523% | -5.885% | -6.739% |
| 1k1k / 8 / 4 | split | +4.304% | +62.256% | -14.097% | -13.929% | -10.064% | -11.926% |
| 1k1k / 8 / 4 | trtllm | +5.378% | +67.978% | -13.365% | -16.900% | -5.852% | -14.816% |
| 8k1k / 4 / 128 | original_mega | -10.890% | -8.863% | -10.637% | -11.938% | -9.641% | -11.229% |
| 8k1k / 4 / 128 | split | -5.083% | -10.662% | -1.404% | -0.470% | -1.741% | -2.570% |
| 8k1k / 4 / 128 | trtllm | +16.023% | +17.976% | +12.803% | +13.266% | +12.698% | +13.154% |
| 8k1k / 4 / 16 | original_mega | -11.239% | -8.858% | -10.294% | -14.887% | -9.605% | -4.085% |
| 8k1k / 4 / 16 | split | -21.966% | -5.855% | -5.410% | -21.698% | -7.777% | -7.181% |
| 8k1k / 4 / 16 | trtllm | +8.891% | +9.803% | +3.498% | -2.244% | +6.297% | +1.832% |
| 8k1k / 4 / 256 | original_mega | -13.046% | -3.395% | -6.821% | -5.281% | -6.393% | -4.234% |
| 8k1k / 4 / 256 | split | -7.089% | -8.030% | -0.878% | -0.859% | -0.995% | -2.847% |
| 8k1k / 4 / 256 | trtllm | +12.346% | +22.592% | +17.837% | +18.713% | +17.540% | +18.902% |
| 8k1k / 4 / 32 | original_mega | -7.980% | +0.681% | -9.882% | -6.608% | -9.667% | -7.128% |
| 8k1k / 4 / 32 | split | -7.859% | +0.166% | -0.310% | +0.496% | -0.145% | -1.331% |
| 8k1k / 4 / 32 | trtllm | +3.546% | +19.391% | +7.560% | +10.913% | +9.477% | +11.988% |
| 8k1k / 4 / 4 | original_mega | -14.189% | +57.305% | -9.511% | -0.670% | -5.574% | +0.087% |
| 8k1k / 4 / 4 | split | -16.803% | +9.086% | -8.829% | -7.638% | -1.867% | -15.680% |
| 8k1k / 4 / 4 | trtllm | -31.340% | +70.647% | +0.779% | +8.429% | +3.465% | +15.706% |
| 8k1k / 4 / 64 | original_mega | -12.549% | -8.293% | -9.606% | -13.308% | -11.328% | -16.912% |
| 8k1k / 4 / 64 | split | +5.982% | -8.514% | -3.131% | -1.358% | -3.673% | -3.585% |
| 8k1k / 4 / 64 | trtllm | +14.925% | +18.682% | +9.577% | +13.193% | +7.981% | +8.090% |
| 8k1k / 4 / 8 | original_mega | +0.357% | -13.404% | -9.420% | -18.014% | -9.612% | -13.696% |
| 8k1k / 4 / 8 | split | +5.200% | +15.808% | -2.983% | -6.252% | -3.264% | -0.959% |
| 8k1k / 4 / 8 | trtllm | +27.531% | +12.886% | +3.738% | -5.395% | -0.658% | +2.574% |
| 8k1k / 8 / 4 | original_mega | +34.612% | -25.290% | -7.838% | -8.233% | -9.130% | -5.489% |
| 8k1k / 8 / 4 | split | -5.966% | -7.007% | -11.568% | -10.964% | -9.092% | -9.705% |
| 8k1k / 8 / 4 | trtllm | +13.709% | +2.553% | -6.841% | -5.922% | -5.455% | -5.755% |

- 1k1k TP4 C128 vs original_mega: output/GPU -2.336%; interactivity -3.617%; median TPOT +3.753%.

- 1k1k TP4 C128 vs split: output/GPU +14.178%; interactivity +13.570%; median TPOT -11.948%.

- 1k1k TP4 C128 vs trtllm: output/GPU +1.088%; interactivity +0.129%; median TPOT -0.129%.

1k1k TP4 C128 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]; after-snapshot cumulative AL by response index [2.9877955695677425, 2.9685869087228163, 2.9940041143315885, 2.987097150377756] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 2}, "before": {"bf16_trtllm_kernel_text": 18, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 16, 32, 64, 128, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]; after-snapshot cumulative AL by response index [2.992638201044037, 2.9777733413189593, 2.9781620258205836, 2.9866812716273743] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 18, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]; after-snapshot cumulative AL by response index [2.9722319100526464, 2.9759700414338264, 2.9557628027895846, 2.9812429640421163] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 18, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]; after-snapshot cumulative AL by response index [2.974054726368159, 2.9616505573759695, 2.989084879642051, 3.0047270188660202] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 1k1k TP4 C16 vs original_mega: output/GPU +4.791%; interactivity +4.710%; median TPOT -4.498%.

- 1k1k TP4 C16 vs split: output/GPU +6.890%; interactivity +5.814%; median TPOT -5.494%.

- 1k1k TP4 C16 vs trtllm: output/GPU +0.707%; interactivity +1.365%; median TPOT -1.346%.

1k1k TP4 C16 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4]; after-snapshot cumulative AL by response index [2.939464416240282, 2.9293232081001865, 2.9938608458390177, 2.9128961530795294] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 15, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 16, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4]; after-snapshot cumulative AL by response index [2.899426234913935, 2.9806135637031494, 2.915542560967506, 2.9344969471728164] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 14, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4]; after-snapshot cumulative AL by response index [2.8955654683810024, 3.0126860042515258, 2.9302635969302635, 2.978480754870681] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 13, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4]; after-snapshot cumulative AL by response index [2.855791807983303, 2.894102054340623, 2.938840560462182, 2.9874106839060905] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 1k1k TP4 C256 vs original_mega: output/GPU -7.669%; interactivity -8.197%; median TPOT +8.929%.

- 1k1k TP4 C256 vs split: output/GPU +2.221%; interactivity +1.673%; median TPOT -1.646%.

- 1k1k TP4 C256 vs trtllm: output/GPU +9.611%; interactivity +10.316%; median TPOT -9.351%.

1k1k TP4 C256 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 40, 44, 48, 52, 56, 60, 64]; after-snapshot cumulative AL by response index [3.020217945160558, 2.983828866902004, 3.0113729628326884, 2.9739392936895213] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 19, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 16, 32, 64, 128, 256, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 40, 44, 48, 52, 56, 60, 64]; after-snapshot cumulative AL by response index [3.0040486337427925, 2.9802233780227523, 2.9825033814386934, 3.0222029648824646] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 19, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 40, 44, 48, 52, 56, 60, 64]; after-snapshot cumulative AL by response index [2.946437868173042, 3.000887762629778, 2.9606910468659913, 3.003015251416918] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 20, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 40, 44, 48, 52, 56, 60, 64]; after-snapshot cumulative AL by response index [3.0114485883290683, 3.041277913169821, 3.087463857023964, 3.0143457548788963] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 1k1k TP4 C32 vs original_mega: output/GPU -2.924%; interactivity -3.421%; median TPOT +3.542%.

- 1k1k TP4 C32 vs split: output/GPU +8.126%; interactivity +9.044%; median TPOT -8.294%.

- 1k1k TP4 C32 vs trtllm: output/GPU +4.323%; interactivity +4.101%; median TPOT -3.939%.

1k1k TP4 C32 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8]; after-snapshot cumulative AL by response index [2.9422821985791496, 2.972572906387178, 2.988548844750709, 2.9656665530173885] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 16, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 16, 32, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8]; after-snapshot cumulative AL by response index [2.9871273944070746, 2.95263698630137, 2.9599701218891115, 3.0027492108746565] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 16, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8]; after-snapshot cumulative AL by response index [2.972356252513068, 2.990155724771901, 2.9777601544721053, 2.988062978081158] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 15, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8]; after-snapshot cumulative AL by response index [3.0383476716241162, 2.9153815071722002, 2.9911639244363193, 3.0104245771487745] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 1k1k TP4 C4 vs original_mega: output/GPU +3.567%; interactivity +3.027%; median TPOT -2.938%.

- 1k1k TP4 C4 vs split: output/GPU +10.525%; interactivity +5.621%; median TPOT -5.322%.

- 1k1k TP4 C4 vs trtllm: output/GPU +0.256%; interactivity +0.147%; median TPOT -0.147%.

1k1k TP4 C4 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1]; after-snapshot cumulative AL by response index [3.066758241758242, 3.0474719101123595, 2.960112359550562, 3.0074175824175824] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 12, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1]; after-snapshot cumulative AL by response index [3.066758241758242, 3.0474719101123595, 3.015449438202247, 3.0137640449438203] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 12, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1]; after-snapshot cumulative AL by response index [2.905163043478261, 3.0604395604395602, 2.906989247311828, 2.9985955056179776] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 13, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1]; after-snapshot cumulative AL by response index [2.957894736842105, 2.9080645161290324, 2.929891304347826, 2.8908602150537632] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 1k1k TP4 C64 vs original_mega: output/GPU -0.163%; interactivity -0.396%; median TPOT +0.397%.

- 1k1k TP4 C64 vs split: output/GPU +16.207%; interactivity +16.460%; median TPOT -14.134%.

- 1k1k TP4 C64 vs trtllm: output/GPU +10.168%; interactivity +10.979%; median TPOT -9.893%.

1k1k TP4 C64 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]; after-snapshot cumulative AL by response index [2.9545190375770054, 2.9914544264056544, 2.980069062625721, 2.9704583472733357] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 17, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 16, 32, 64, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]; after-snapshot cumulative AL by response index [2.996159071468107, 2.9923233615595697, 2.9651554576994927, 2.9667665121571645] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 17, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]; after-snapshot cumulative AL by response index [3.005627023270792, 2.986926790024135, 2.956459647957489, 2.985323257766583] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 16, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]; after-snapshot cumulative AL by response index [3.0409935345195245, 3.0183076086217446, 3.0373642115315747, 2.9486945408070113] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 1k1k TP4 C8 vs original_mega: output/GPU +5.153%; interactivity +4.726%; median TPOT -4.513%.

- 1k1k TP4 C8 vs split: output/GPU +7.247%; interactivity +6.021%; median TPOT -5.679%.

- 1k1k TP4 C8 vs trtllm: output/GPU +2.812%; interactivity +2.200%; median TPOT -2.153%.

1k1k TP4 C8 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2]; after-snapshot cumulative AL by response index [3.1054639596675297, 3.114029025570145, 3.066963664207156, 2.9085901639344263] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 13, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2]; after-snapshot cumulative AL by response index [3.093141989788878, 2.8948394644481996, 3.069432918395574, 3.085057471264368] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 13, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2]; after-snapshot cumulative AL by response index [3.129632258980548, 2.937948717948718, 3.088129991737813, 2.92998678996037] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 14, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2]; after-snapshot cumulative AL by response index [2.895103058947092, 2.8658505483295076, 2.898797071129707, 2.90419997462251] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 1k1k TP8 C4 vs original_mega: output/GPU +7.190%; interactivity +7.793%; median TPOT -7.230%.

- 1k1k TP8 C4 vs split: output/GPU +15.781%; interactivity +12.910%; median TPOT -11.434%.

- 1k1k TP8 C4 vs trtllm: output/GPU +10.716%; interactivity +7.161%; median TPOT -6.683%.

1k1k TP8 C4 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1]; after-snapshot cumulative AL by response index [3.0482954545454546, 3.1151162790697673, 2.9233333333333333, 2.921022727272727, 2.878125, 2.9302083333333333, 3.0044444444444443, 2.9244791666666665] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 22, "graph_capture_text": 20, "severity_tagged_warning": 35}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 4096]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1]; after-snapshot cumulative AL by response index [2.878125, 2.9244791666666665, 3.0482954545454546, 2.921022727272727, 3.0044444444444443, 2.9302083333333333, 3.1151162790697673, 2.9233333333333333] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 21, "graph_capture_text": 20, "severity_tagged_warning": 34}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1]; after-snapshot cumulative AL by response index [2.8663265306122447, 3.133720930232558, 2.839673913043478, 3.0732142857142857, 2.9581521739130436, 3.070108695652174, 2.8643617021276597, 3.1343023255813955] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"cancelled_error": 2, "error_label": 2, "post_measurement_cleanup_error_label": 2, "sigterm": 1, "system_exit_zero": 2, "traceback_header": 4}, "before": {"bf16_trtllm_kernel_text": 22, "graph_capture_text": 20, "severity_tagged_warning": 33}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1]; after-snapshot cumulative AL by response index [2.8894444444444445, 2.7965, 3.015957446808511, 2.917391304347826, 2.966666666666667, 2.8559782608695654, 2.720408163265306, 3.077777777777778] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 20, "severity_tagged_warning": 9}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 8k1k TP4 C128 vs original_mega: output/GPU +10.072%; interactivity +9.945%; median TPOT -9.045%.

- 8k1k TP4 C128 vs split: output/GPU +1.601%; interactivity +0.713%; median TPOT -0.708%.

- 8k1k TP4 C128 vs trtllm: output/GPU -11.674%; interactivity -12.188%; median TPOT +13.879%.

8k1k TP4 C128 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]; after-snapshot cumulative AL by response index [2.917799293274412, 2.914735596158976, 2.9261480897330494, 2.9365284427219223] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 18, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 16, 32, 64, 128, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]; after-snapshot cumulative AL by response index [2.9296385986375175, 2.9235330523216914, 2.926237373737374, 2.91269204406774] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"cancelled_error": 4, "error_label": 4, "post_measurement_cleanup_error_label": 4, "sigterm": 1, "system_exit_zero": 4, "traceback_header": 8}, "before": {"bf16_trtllm_kernel_text": 18, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]; after-snapshot cumulative AL by response index [2.9199823239060834, 2.903244080843761, 2.9116063030141595, 2.913682477828541] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 18, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32]; after-snapshot cumulative AL by response index [2.946090032425148, 2.917206329071669, 2.9375499861091234, 2.9174793193893334] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"cancelled_error": 2, "error_label": 2, "post_measurement_cleanup_error_label": 2, "sigterm": 1, "system_exit_zero": 2, "traceback_header": 4}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 8k1k TP4 C16 vs original_mega: output/GPU +11.529%; interactivity +11.069%; median TPOT -9.966%.

- 8k1k TP4 C16 vs split: output/GPU +9.126%; interactivity +7.105%; median TPOT -6.634%.

- 8k1k TP4 C16 vs trtllm: output/GPU -5.319%; interactivity -5.540%; median TPOT +5.864%.

8k1k TP4 C16 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4]; after-snapshot cumulative AL by response index [2.9899470544869646, 2.9648401220644818, 3.0466598847066804, 2.965733941919693] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 15, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 16, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4]; after-snapshot cumulative AL by response index [2.9619475457488273, 2.960085435856361, 2.959884065608326, 2.994258628746912] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 15, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4]; after-snapshot cumulative AL by response index [2.9823882588392263, 2.931195373595321, 2.960425475687104, 2.9097496280002586] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 15, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4]; after-snapshot cumulative AL by response index [2.954118188391507, 2.993347525279404, 2.9326658814291324, 2.988629482607818] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"cancelled_error": 1, "error_label": 1, "post_measurement_cleanup_error_label": 1, "sigterm": 1, "system_exit_zero": 1, "traceback_header": 2}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 8k1k TP4 C256 vs original_mega: output/GPU +7.489%; interactivity +6.725%; median TPOT -6.301%.

- 8k1k TP4 C256 vs split: output/GPU +1.134%; interactivity +0.451%; median TPOT -0.449%.

- 8k1k TP4 C256 vs trtllm: output/GPU -14.882%; interactivity -15.386%; median TPOT +18.183%.

8k1k TP4 C256 runtime observations:

- new_mega: SG `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 40, 44, 48, 52, 56, 60, 64]; after-snapshot cumulative AL by response index [2.9724403080713193, 2.947779780435851, 2.9585527265230387, 2.9596535977290492] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 20, "graph_capture_text": 12, "severity_tagged_warning": 21}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 40, 44, 48, 52, 56, 60, 64]; after-snapshot cumulative AL by response index [2.9559822990634967, 2.9491395306829564, 2.9637121055887814, 2.963090015502853] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 19, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 40, 44, 48, 52, 56, 60, 64]; after-snapshot cumulative AL by response index [2.9596998160879817, 2.9648290150308294, 2.9481015363622167, 2.9460656282161146] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 19, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 40, 44, 48, 52, 56, 60, 64]; after-snapshot cumulative AL by response index [2.9667774908631914, 2.9627993393889347, 2.9659105005913147, 2.9825551267116333] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 20, "graph_capture_text": 12, "severity_tagged_warning": 11}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 8k1k TP4 C32 vs original_mega: output/GPU +10.394%; interactivity +10.645%; median TPOT -9.621%.

- 8k1k TP4 C32 vs split: output/GPU +0.468%; interactivity -1.278%; median TPOT +1.295%.

- 8k1k TP4 C32 vs trtllm: output/GPU -7.409%; interactivity -8.281%; median TPOT +9.028%.

8k1k TP4 C32 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8]; after-snapshot cumulative AL by response index [2.9598446029672796, 2.9808512749280682, 2.9341429238673515, 2.940213428779744] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 16, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 16, 32, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8]; after-snapshot cumulative AL by response index [2.9583723105706268, 2.941461955257122, 2.9102678423990223, 2.9690201253711646] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 15, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8]; after-snapshot cumulative AL by response index [2.9949426052237564, 2.957625424745153, 2.9507182023076663, 2.910160357518402] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 16, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8]; after-snapshot cumulative AL by response index [3.0117788783295407, 2.938465138043987, 2.960876525915549, 2.9644762000603806] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"cancelled_error": 2, "error_label": 2, "post_measurement_cleanup_error_label": 2, "sigterm": 1, "system_exit_zero": 2, "traceback_header": 4}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 8k1k TP4 C4 vs original_mega: output/GPU +6.204%; interactivity +8.658%; median TPOT -7.968%.

- 8k1k TP4 C4 vs split: output/GPU +5.683%; interactivity +5.433%; median TPOT -5.153%.

- 8k1k TP4 C4 vs trtllm: output/GPU -3.611%; interactivity -5.234%; median TPOT +5.523%.

8k1k TP4 C4 runtime observations:

- new_mega: SG `6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1]; after-snapshot cumulative AL by response index [3.116111111111111, 3.0080645161290325, 2.847, 3.0081521739130435] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 13, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1]; after-snapshot cumulative AL by response index [3.018421052631579, 3.1238888888888887, 3.023888888888889, 2.9710106382978725] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 13, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1]; after-snapshot cumulative AL by response index [3.0554347826086956, 3.034269662921348, 2.91015625, 3.196388888888889] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 13, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1]; after-snapshot cumulative AL by response index [3.002127659574468, 2.9907608695652175, 3.110483870967742, 3.0304945054945054] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 8k1k TP4 C64 vs original_mega: output/GPU +11.305%; interactivity +10.756%; median TPOT -9.711%.

- 8k1k TP4 C64 vs split: output/GPU +4.020%; interactivity +4.006%; median TPOT -3.852%.

- 8k1k TP4 C64 vs trtllm: output/GPU -8.288%; interactivity -8.750%; median TPOT +9.590%.

8k1k TP4 C64 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]; after-snapshot cumulative AL by response index [2.973769614239352, 2.967867413601077, 2.974921682609351, 2.968844354490859] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 2}, "before": {"bf16_trtllm_kernel_text": 16, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 16, 32, 64, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]; after-snapshot cumulative AL by response index [2.98100810833403, 2.989958524339664, 2.9759180415114423, 2.9643709825528006] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 17, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]; after-snapshot cumulative AL by response index [2.992688802412358, 2.9450320618761157, 2.9816128709903067, 2.9597447063125353] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 16, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16]; after-snapshot cumulative AL by response index [2.9366621429280726, 2.9581236192089833, 2.9526005255590264, 2.9538212617015307] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 8k1k TP4 C8 vs original_mega: output/GPU +10.179%; interactivity +7.970%; median TPOT -7.381%.

- 8k1k TP4 C8 vs split: output/GPU +4.217%; interactivity +3.726%; median TPOT -3.592%.

- 8k1k TP4 C8 vs trtllm: output/GPU -2.274%; interactivity -1.720%; median TPOT +1.750%.

8k1k TP4 C8 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2]; after-snapshot cumulative AL by response index [3.04019228201362, 3.039972432804962, 2.988866532528504, 2.938960357049094] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 2}, "before": {"bf16_trtllm_kernel_text": 13, "graph_capture_text": 12, "severity_tagged_warning": 19}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 8, 8192]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1, 2]; after-snapshot cumulative AL by response index [2.9781727878708666, 2.9913595247738627, 2.996109993293092, 2.870946906084485] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 14, "graph_capture_text": 12, "severity_tagged_warning": 18}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1, 2]; after-snapshot cumulative AL by response index [2.9538784067085953, 2.98280297901151, 3.055183498526654, 2.9340761374187556] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2}, "before": {"bf16_trtllm_kernel_text": 13, "graph_capture_text": 12, "severity_tagged_warning": 17}, "boundary": {"sigterm": 1}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1, 2]; after-snapshot cumulative AL by response index [2.9839074344992684, 2.9529192711796783, 3.0592970217332978, 2.9054071832653596] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"graph_capture_text": 12, "severity_tagged_warning": 5}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

- 8k1k TP8 C4 vs original_mega: output/GPU +9.918%; interactivity +11.427%; median TPOT -10.255%.

- 8k1k TP8 C4 vs split: output/GPU +16.100%; interactivity +16.833%; median TPOT -14.408%.

- 8k1k TP8 C4 vs trtllm: output/GPU +7.458%; interactivity +5.548%; median TPOT -5.256%.

8k1k TP8 C4 runtime observations:

- new_mega: SG `26c41009549f9ad407e107b33d5144f6e085418b`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1]; after-snapshot cumulative AL by response index [3.0180851063829786, 2.894387755102041, 2.945108695652174, 3.2627906976744185, 2.935, 3.046875, 3.136111111111111, 3.235227272727273] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 18, "graph_capture_text": 20, "severity_tagged_warning": 35}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
  Prepared new-Mega capacities: [1, 2, 4, 4096]; native cache and startup log evidence are bound in regression.json.
- original_mega: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `ad0a5e5e78e57070ec7c582efe733cb55cd8839f`; observed capture batches [1]; after-snapshot cumulative AL by response index [2.955, 2.9797872340425533, 2.990816326530612, 3.225, 2.895, 2.8625, 2.874468085106383, 3.091304347826087] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 20, "graph_capture_text": 20, "severity_tagged_warning": 34}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- split: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `f9dd3c10541e087b716772245a9d033499745048`; observed capture batches [1]; after-snapshot cumulative AL by response index [3.0026041666666665, 2.9885869565217393, 2.897448979591837, 3.1277173913043477, 3.0733333333333333, 3.002659574468085, 3.0988372093023258, 2.8255208333333335] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"sigquit_diagnostic": 2, "sigterm": 1}, "before": {"bf16_trtllm_kernel_text": 20, "graph_capture_text": 20, "severity_tagged_warning": 33}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.
- trtllm: SG `50eeb742961908afa68f4f523a1a19c5de6eb0b3`; FI `None`; observed capture batches [1]; after-snapshot cumulative AL by response index [2.933333333333333, 2.99468085106383, 2.9585106382978723, 3.006666666666667, 3.151666666666667, 3.032446808510638, 2.8297872340425534, 2.9973958333333335] (includes warmup; no DP average). Diagnostic counts by phase: `{"after": {"cancelled_error": 2, "error_label": 2, "post_measurement_cleanup_error_label": 2, "sigterm": 1, "system_exit_zero": 2, "traceback_header": 4}, "before": {"bf16_trtllm_kernel_text": 23, "graph_capture_text": 20, "severity_tagged_warning": 9}, "boundary": {}, "measured": {}, "untimed": {"severity_tagged_warning": 1}}`.

Runtime identities, before/after cumulative MTP observations, graph/tuning evidence, all recorded p90/p95/p99 latency summaries, and phase diagnostics are retained per arm in regression.json.

- Partial snapshot: only listed finalized, calibrated coordinates; no missing-point interpolation or final Pareto.
- Mixed SGLang/source/runtime comparison. A speed regression is an observation, not proof of an integration or autotuning cause.
- Throughput spans the measured request interval, including prefill/queueing; it is not isolated decode-kernel timing.
- Latency medians/percentiles are saved summaries, not reconstructed from missing per-request latency samples; absent p95 remains unavailable.
- MTP averages are server-lifetime cumulative. Any valid counter difference spans before/after server_info, including client warmup; never subtract averages or call it measurement-only.
- Equal input/output token lengths establish workload sampling comparability, not output-quality or numerical equivalence.

## Signed changes versus each reference

| Scenario / TP / C | Reference | Output/GPU % | Interactivity % | Median TTFT % | Median TPOT % | Median E2EL % |
|---|---|---:|---:|---:|---:|---:|
| 1k1k / 4 / 128 | original_mega | -2.335704 | -3.617139 | -2.590197 | +3.752886 | +3.231745 |
| 1k1k / 4 / 128 | split | +14.178290 | +13.569568 | -13.514880 | -11.948243 | -11.859241 |
| 1k1k / 4 / 128 | trtllm | +1.087635 | +0.128740 | +0.256797 | -0.128575 | -0.224351 |
| 1k1k / 4 / 16 | original_mega | +4.791117 | +4.709653 | -22.768171 | -4.497821 | -5.060336 |
| 1k1k / 4 / 16 | split | +6.890308 | +5.813677 | -12.331427 | -5.494259 | -5.334131 |
| 1k1k / 4 / 16 | trtllm | +0.706961 | +1.364640 | -0.251817 | -1.346268 | +0.934160 |
| 1k1k / 4 / 256 | original_mega | -7.669393 | -8.197236 | +9.907434 | +8.929182 | +8.915684 |
| 1k1k / 4 / 256 | split | +2.221071 | +1.673248 | +5.416796 | -1.645711 | -1.844259 |
| 1k1k / 4 / 256 | trtllm | +9.610639 | +10.315821 | -13.524452 | -9.351171 | -9.465430 |
| 1k1k / 4 / 32 | original_mega | -2.923761 | -3.420800 | +9.888115 | +3.541964 | +4.283242 |
| 1k1k / 4 / 32 | split | +8.125960 | +9.044052 | -22.227701 | -8.293944 | -7.434847 |
| 1k1k / 4 / 32 | trtllm | +4.323069 | +4.100714 | -16.025967 | -3.939179 | -3.751513 |
| 1k1k / 4 / 4 | original_mega | +3.567008 | +3.026890 | +4.402904 | -2.937962 | -3.001427 |
| 1k1k / 4 / 4 | split | +10.525114 | +5.621201 | -6.188702 | -5.322039 | -9.007750 |
| 1k1k / 4 / 4 | trtllm | +0.255639 | +0.147391 | +1.774801 | -0.147174 | -1.890489 |
| 1k1k / 4 / 64 | original_mega | -0.163067 | -0.395835 | +5.685319 | +0.397408 | +0.637375 |
| 1k1k / 4 / 64 | split | +16.206557 | +16.460050 | -14.326233 | -14.133645 | -13.864329 |
| 1k1k / 4 / 64 | trtllm | +10.168300 | +10.979255 | -16.857901 | -9.893070 | -9.047757 |
| 1k1k / 4 / 8 | original_mega | +5.152851 | +4.726412 | +1.802996 | -4.513104 | -3.796968 |
| 1k1k / 4 / 8 | split | +7.247264 | +6.020828 | -8.717245 | -5.678911 | -6.045494 |
| 1k1k / 4 / 8 | trtllm | +2.811852 | +2.200357 | -0.134469 | -2.152983 | -0.743651 |
| 1k1k / 8 / 4 | original_mega | +7.189926 | +7.793183 | +4.957026 | -7.229755 | -6.258555 |
| 1k1k / 8 / 4 | split | +15.780522 | +12.910322 | -6.888457 | -11.434138 | -10.403743 |
| 1k1k / 8 / 4 | trtllm | +10.715984 | +7.161364 | -2.143109 | -6.682786 | -6.608118 |
| 8k1k / 4 / 128 | original_mega | +10.072452 | +9.944591 | -14.894480 | -9.045094 | -8.778113 |
| 8k1k / 4 / 128 | split | +1.601241 | +0.713247 | -0.684035 | -0.708196 | -0.807129 |
| 8k1k / 4 / 128 | trtllm | -11.673517 | -12.187814 | +9.046524 | +13.879410 | +14.289994 |
| 8k1k / 4 / 16 | original_mega | +11.529125 | +11.068886 | -4.117865 | -9.965785 | -9.867624 |
| 8k1k / 4 / 16 | split | +9.126434 | +7.105097 | -10.515419 | -6.633761 | -8.778875 |
| 8k1k / 4 / 16 | trtllm | -5.319142 | -5.539574 | -12.352146 | +5.864439 | +5.026703 |
| 8k1k / 4 / 256 | original_mega | +7.489336 | +6.724580 | -1.749427 | -6.300873 | -6.474976 |
| 8k1k / 4 / 256 | split | +1.133731 | +0.451417 | +10.768631 | -0.449388 | -0.630124 |
| 8k1k / 4 / 256 | trtllm | -14.881587 | -15.385795 | +19.166740 | +18.183466 | +17.932350 |
| 8k1k / 4 / 32 | original_mega | +10.393760 | +10.644654 | -12.599079 | -9.620577 | -10.017252 |
| 8k1k / 4 / 32 | split | +0.467950 | -1.278447 | +5.086705 | +1.295003 | +1.372194 |
| 8k1k / 4 / 32 | trtllm | -7.409271 | -8.280612 | +25.519656 | +9.028202 | +7.136745 |
| 8k1k / 4 / 4 | original_mega | +6.203821 | +8.658261 | -6.549463 | -7.968341 | -6.663210 |
| 8k1k / 4 / 4 | split | +5.683488 | +5.432634 | -11.024817 | -5.152707 | -5.737610 |
| 8k1k / 4 / 4 | trtllm | -3.610776 | -5.233831 | +22.134965 | +5.522890 | +2.577341 |
| 8k1k / 4 / 64 | original_mega | +11.305014 | +10.756054 | -12.241171 | -9.711482 | -9.954537 |
| 8k1k / 4 / 64 | split | +4.020446 | +4.005823 | +5.049468 | -3.851537 | -2.867986 |
| 8k1k / 4 / 64 | trtllm | -8.287949 | -8.750384 | +19.440199 | +9.589502 | +10.290010 |
| 8k1k / 4 / 8 | original_mega | +10.178868 | +7.969732 | +1.365876 | -7.381450 | -8.639412 |
| 8k1k / 4 / 8 | split | +4.216556 | +3.725599 | +18.403406 | -3.591784 | -1.949593 |
| 8k1k / 4 / 8 | trtllm | -2.274059 | -1.719931 | -7.480871 | +1.750031 | +2.909545 |
| 8k1k / 8 / 4 | original_mega | +9.918486 | +11.426544 | +0.889475 | -10.254777 | -6.901927 |
| 8k1k / 8 / 4 | split | +16.099506 | +16.833008 | -5.615802 | -14.407750 | -12.485614 |
| 8k1k / 8 / 4 | trtllm | +7.457715 | +5.548105 | +4.004570 | -5.256470 | -5.239377 |
