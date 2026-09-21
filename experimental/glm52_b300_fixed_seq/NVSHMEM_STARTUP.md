# NVSHMEM proxy initialization and the SGLang workaround

## Observed failure

Real GLM-5.2 startup failed with `nvshmem API called before nvshmem_init` while preparing MegaMoE. Natural host initialization returned on all four ranks, but the first symmetric allocation did not return. The native library can report this symptom after initialization; the message alone does not establish that SGLang omitted the init call.

In [NVSHMEM 3.4.5 proxy.cpp](https://github.com/NVIDIA/nvshmem/blob/131da55f643ac87c810ba0bc51d359258bf433a1/src/host/proxy/proxy.cpp), two pinned allocations for `global_exit_request_state` and `global_exit_code` have no initial stores. The proxy progress loop tests the former against `PROXY_GLOBAL_EXIT_REQUESTED` and passes the latter to global exit. On the installed wheel, read-only hardware-breakpoint observations saw request `2` / code `0` after allocation on all four ranks, followed by the proxy call into the global-exit PLT. The allocator/writer history, ultimate resolved callee and subsequent state-clearing instruction were not observed; debugger timing is a limitation.

## Matched native experiment

Both builds came from official `v3.4.5-0`, commit `131da55f643ac87c810ba0bc51d359258bf433a1`, source archive SHA256 `74047b0b572d677a6c072c9e5486514d19fe7dff1252a2548ee08ce8d68b6bc5`. The patched arm added only:

```cpp
*proxy_state->global_exit_request_state = PROXY_GLOBAL_EXIT_NOT_REQUESTED;
*proxy_state->global_exit_code = 0;
```

Each store follows its respective allocation, before proxy publication. Both used Release/sm103, GCC13.3, nvcc13.0.88 and UCX disabled because headers were absent. They are matched source builds, not proven wheel-equivalent. Each loaded its corresponding host/UID/transport plugins; installed device/header files remained unchanged. Full original receipts, source/binary bytes and failures are retained in the experiment workspace.

| 2026-09-21 UTC arm | Natural init returned | First malloc returned | HTTP health | Before-init fatal lines | Controller exit |
| --- | ---: | ---: | --- | ---: | ---: |
| Pristine, 18:27:53–18:38:38 | 4/4 ranks | 0/4 ranks | false | 4 | 1 |
| Two-store patch, 18:58:28–19:21:27 | 4/4 ranks | 4/4 ranks | true | 0 | 0 |

This used SG6d8/FIad0 and the image, real checkpoint and C8 protocol recorded in [RECOVERY7.md](./RECOVERY7.md). No benchmark client was run; internal SGLang startup warmup and health requests occurred. The pristine receipt retains an immediate postrun GPU-apps guard failure; a separate later postflight proved all recorded owners absent and eight GPUs idle. Patched cleanup passed; its server was intentionally terminated after readiness. These observations support the two-store intervention for this fixed stack, not throughput, numerical equivalence, general topology coverage or legitimate device-global-exit behavior.

## Integration workaround

[SGLang PR39210](https://github.com/sgl-project/sglang/pull/39210), head `26c41009549f9ad407e107b33d5144f6e085418b`, uses NVSHMEM's public configuration to skip proxy initialization on the selected single-node W4A16 MegaMoE path. Defaults are `NVSHMEM_REMOTE_TRANSPORT=none`, `NVSHMEM_IB_ENABLE_IBGDA=0`, and `NVSHMEM_DISABLE_LOCAL_ONLY_PROXY=1`, preserving explicit overrides. The source branch retains direct peer transport and returns before the faulty proxy allocations. Direct peer connectivity is required; NVSHMEM device wait timeouts and device global exit do not function in this mode.

Recovery7 uses the unmodified wheel. On hu-pdx-30, the SG26c real C8 diagnostic ran from 21:53:12 to 22:21:37 UTC. All four ranks returned from natural init and first malloc with the stock host/UID and the three effective defaults. Target and draft autotuning/graphs completed, health became true, and owned cleanup left eight idle GPUs. No benchmark client was run.

| Rank / device | Actual PID | Init returned | First malloc returned | Proxy-disabled stdout line |
| --- | ---: | --- | --- | ---: |
| 0 | 8114 | true | true | 254 |
| 1 | 8162 | true | true | 256 |
| 2 | 8210 | true | true | 254 |
| 3 | 8276 | true | true | 254 |

The loaded stock host SHA256 is `c43004bb93053aa70603a204fe0c9052bdd29f38822d3048599183f8d5930d8f`; UID SHA256 is `69b2b46a146adec27389c3bbdb46efd3d0853dc32eead1f6e08d6d906ad70c82`. The preserved terminal fields are:

```json
{"health":true,"error":null,"cleanup_errors":[],"performance_requests":0,"numerical_acceptance":false,"natural_returncode_before_cleanup":null,"exit_code":1,"observation_error":"ValueError('Proxy NONE INFO proof missing for a natural rank')"}
```

The diagnostic controller and waited worker both retain exit **1**: three complete, PID-attributed native `Proxy is disabled.` messages were concatenated on stdout line254, while rank1 appeared on line256. The original checker used one regex search per line and missed ranks0/2. Every rank's own segment includes the device wait/global-exit limitation warning. A separate offline review checks each native prefix and its bounded message segment; it does not rewrite the original exit or raw logs. The InferenceX producer and independent case reader use the same corrected framing before accepting a case. This is startup evidence only, not throughput or numerical validation.

## 中文说明

已观察到的错误发生在真实初始化返回之后：四个 rank 的 init 返回，但首个 malloc 未返回。NVSHMEM3.4.5 proxy 分配 request/code 两个整数后没有初始化；硬件断点捕获了 request=2/code=0 以及 proxy 调用 global-exit PLT。没有追溯分配器来源、全部写入者或最终清零指令。

相同官方源码、相同构建配置的对照中，原版出现四条 before-init 错误，两处初始化赋值的补丁完成四个 rank 的 init/malloc 和健康检查。上表保留各项实际结果；单次启动对照不是性能或数值验证，重编译产物也不等于原 wheel。原版清理检查的失败和随后单独通过的检查保留为不同证据。

SGLang workaround 使用公开配置在限定的单节点 W4A16 MegaMoE 路径跳过 proxy 初始化，保留直接 peer 通路和用户覆盖；相应 device timeout/global-exit 功能不可用。原 wheel + SG26c 在 hu-pdx-30 的真实 C8 启动完成了四个 rank 的 init/malloc、target/draft 调优与图捕获、健康检查及清理。控制器和 worker 的原始退出码仍为 **1**：三个 rank 的完整 native 日志拼在同一行，旧校验器每行只匹配一次，漏掉 ranks0/2。独立离线复核逐个 native 前缀及其消息片段核对；每个 rank 都有自己的完整功能限制警告，不改写原始日志或退出码。InferenceX 使用同样修正后的日志分帧校验；这仍不是性能或数值结果。
