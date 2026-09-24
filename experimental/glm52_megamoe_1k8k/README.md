# GLM-5.2 MegaMoE, nominal 1k input / 8k output

This standalone single-node recipe measures **24 new points** on eight B300 GPUs.
It does not reuse measurements from the earlier GLM-5.2 experiment. Both target
precisions share one pinned FlashInfer build and the SGLang autotune adapter,
with distinct native kernels and AUTO timers.
The recipe performs no package installation, remote dispatch, checkpoint download,
or automatic retry.

| Setting | Value |
|---|---|
| Target precision | NVFP4 W4A4 or W4A16; BF16 combine, external FC2 reduction |
| Parallelism | TP = EP = DP attention = 4 or 8, one node |
| Client concurrency | 4, 8, 16, 32, 64, 128 in each of four precision/topology groups |
| Execution order per group | **128, 4, 8, 16, 32, 64**; W4A4 TP4, W4A4 TP8, W4A16 TP4, W4A16 TP8 |
| Workload | Nominal input 1024 / output 8192, random ratio **0.8**, seed **0**, chat template |
| Requests | 2×C warmup, 10×C measured; 2,016 warmup and 10,080 measured attempts in total |
| Traffic / sampling | Unlimited arrival rate; current InferenceX `vllm` HTTP client, temperature 0, ignore EOS |
| MTP | EAGLE, 3 steps / top-k 1 / 4 draft tokens; native BF16 draft path, `flashinfer_trtllm` / `none` |
| Memory / KV | Static fraction 0.80; `fp8_e4m3` KV cache; radix cache disabled |
| Prefill | Global chunk budget 32768, max prefill tokens 32768, prefill CUDA graphs disabled |
| Decode | Graph max batch = C; server max running requests = max(C, DP) |
| Native communication | `NVSHMEM_REMOTE_TRANSPORT=none`, `NVSHMEM_IB_ENABLE_IBGDA=0`, `NVSHMEM_DISABLE_LOCAL_ONLY_PROXY=1` |

Both lengths are nominal: the unchanged client accounts for the chat template
and samples lengths. Inspect saved `input_lens` and `output_lens`, not the nominal
labels, when comparing points. Each same-concurrency point must reproduce both
ordered arrays from the first newly measured point. A mismatch stops the campaign.
The unchanged ratio-0.8 client samples requested output lengths from 6,553 through
8,192 tokens; use the saved output lengths for actual token accounting.
Before the HTTP client runs, `requested-lengths.json` saves the unchanged client's
seeded CPU request plan using the same tokenizer and sampler. Both ordered arrays
must exactly equal the completed arrays, so internally consistent but clipped
output lengths are rejected. The plan is not server-output or numerical proof.
Completed output lengths use the shared client's `usage.completion_tokens` when
available, otherwise its tokenizer fallback; this is not independent token-content
or numerical validation.
The shared client drains warmup requests but does not export individual warmup
outcomes; `Warmup completed` is not an independent numerical correctness claim.

The source baseline is SGLang `16c1b8638b462ca1b896e2b76d5c002caf06988b` and
FlashInfer `19e8aebb541684df09e12cc79610338aa429a2cf`, with the image in
[`config.example.json`](config.example.json). The runtime config must contain the
full accepted source SHAs, actual paths, image digest and actual image environment.
FlashInfer is installed as matched main and cubin wheels built at that full commit;
only SGLang's `python/` and InferenceX enter `PYTHONPATH`. The FlashInfer source root
is checked for provenance, not imported. `runtime.initial.json` checks installed
wheel origins and both full build commits; no stale AOT provider may be selected.
The example's paths and `LD_LIBRARY_PATH` are placeholders; do not copy them over
an installation's validated runtime paths. The script checks source HEAD, tracked
changes, recipe hashes and the complete package freeze before and after every case.
Model metadata SHA and all referenced shard sizes are recorded; full weight-byte
verification and GPU/image/topology qualification belong to setup evidence.

## Run

Follow the [one-time installation instructions](INSTALL.md), then validate the image,
two source checkouts, compiled dependencies and revision-pinned local checkpoint once. Do not rebuild or reinstall between arms.
Copy the config outside the source tree, fill its actual paths/environment, and
create only the parent of `run_root`. The run root itself must not exist.
The example sets a 14,400-second benchmark safety timeout; server readiness remains
3,600 seconds. These are failure bounds, not runtime or performance estimates.

```bash
RECIPE=experimental/glm52_megamoe_1k8k
cp "$RECIPE/config.example.json" /data/experiments/campaign.json
# Edit campaign.json to the validated installation paths and image environment.
python3 "$RECIPE/run.py" --config /data/experiments/campaign.json --plan \
  > /data/experiments/campaign-plan.json
setsid /opt/sglang/bin/python3 -u "$RECIPE/run.py" \
  --config /data/experiments/campaign.json --run \
  > /data/experiments/campaign-worker.log 2>&1 < /dev/null &
echo "$!" > /data/experiments/campaign-worker.pid
```

Root/launcher must save the worker's birth identity and waited exit as well. A
terminal `worker-exit.json` is a worker report, not a replacement for the external
waited return code. Read `progress.json` to locate the current completed points;
do not rerun an uncertain launch. SIGINT/SIGTERM stops the active case, cleans its
owned processes and exits. Cleanup rechecks PID birth identities before signals,
waits the direct children, and refuses to proceed if any owned process or GPU
application remains. Failure preserves partial logs and stops the whole serial
campaign. There is deliberately no overwrite/resume switch.

## Caches and evidence

`run_root/caches/compile/` is shared by all 24 points. It starts empty, grows through
normal JIT compilation, and is never cleared or replaced. SGLang JIT, DeepGEMM,
CuTe AOT, FlashInfer, CuTe DSL, CUDA, Torch extensions/Inductor, Triton, TileLang and
XDG cache locations are explicit. `SGLANG_CACHE_DIR` points instead to
`caches/tactics/<precision>/tp<TP>/`: four isolated FlashInfer tuning namespaces.
C128 runs first to prepare the maximum relevant decode/prefill profiles; smaller
points still run their own server startup, warmup and measured workload. Cache hits
and newly tuned profiles are evidence to inspect, not an assumption of zero tuning.

Both precisions use SGLang's existing shared profile/cache integration. Inside the
pinned FlashInfer implementation, native W4A4 AUTO uses synchronized host wall time,
whereas native W4A16 AUTO uses GPU events on a private CUDA graph. Neither timer
requires CUPTI. This experiment retains those upstream timing implementations;
shared profile integration does not imply identical internal tuning timers.

Only with GPUs idle, before startup and after cleanup, the runner saves compilation
cache stat inventories and copies/hashes tactic files. It never scans an active
server's caches. Failed cases or incomplete owned cleanup skip the after-cache
snapshot and record the reason. Compile inventories are **not** full cache-payload
SHA archives.
Retain the final shared cache tree separately when archiving the run.

Each exclusive `cases/<precision>-tp<TP>-ep<EP>-dp<DP>-c<C>/` contains:

- `settings.json`, exact server/client argv and environments, source/freeze receipts;
- raw server/client logs, server-watch identity, birth-bound ownership/cleanup receipts;
- `server_info.before.json` and `.after.json` with resolved settings and MTP counters;
- `requested-lengths.json`, binding the measured request plan to the client source and model path;
- `result.json`, including ordered length arrays and the client's original scalar/tail metrics;
- GPU samples with actual timestamps, utilization, memory, power and process listings;
- idle-only cache inventories and tactic copies;
- terminal `exit.json` and immutable `manifest.json` with size/SHA for every case file.

Only `exit.status == completed`, empty cleanup errors/remaining owners, and the
matching manifest identify a successful point. A failed point also has a manifest.
`metrics.json` derives throughput as **all measured output tokens / the complete
measured wall interval / actual TP** (4 or 8 GPUs), not active-decode log throughput.
The default client saves median/p90/p99 statistics; detailed per-request latency
arrays are not exported. Stream interval 30 means ITL is streamed-chunk timing,
not individual-token TPOT. Startup/tuning/graph time is outside throughput timing.
This throughput experiment does not establish output quality or multi-node safety;
the local-only NVSHMEM configuration is specific to an adequate single-node P2P topology.
Health and script completion do not replace the first actual point's offline
inspection of selected kernel paths and autotune profile coverage for both precisions.

## Read finalized results

Copy only manifest-sealed case evidence into a local run tree, retaining exact file
bytes and the root config/worker receipts. The reader verifies each case manifest,
completion/cleanup, settings, source/freeze, requested-versus-completed ordered
length equality and same-C ordered length arrays.
Use a fresh output directory for each invocation:

```bash
python3 experimental/glm52_megamoe_1k8k/results.py \
  --run-root /data/experiments/collected-run \
  --output /data/experiments/results-partial --partial
# After all 24 points and worker termination:
python3 experimental/glm52_megamoe_1k8k/results.py \
  --run-root /data/experiments/collected-run \
  --output /data/experiments/results-final
```

`--partial` writes tables/JSON/CSV for the available finalized points without a
final plot. Full mode requires the complete 24-point worker result and writes
`pareto.png`/`pareto.svg` with four precision/topology frontiers. Both modes retain
saved latency metrics and raw SHA bindings in `raw-metrics.json`/`.csv`; throughput
uses the complete measured interval and the actual GPU count. These structural
checks do not replace the separate first-point kernel/profile and external waited
terminal reviews described above. Plotting requires Matplotlib in the local
analysis environment; it does not belong in the serving install.

## Local check and attribution

```bash
python3 -B experimental/glm52_megamoe_1k8k/check.py
bash -n experimental/glm52_megamoe_1k8k/benchmark_mtp.sh
```

These CPU checks exercise the actual matrix/command/environment/result code and
the Bash bridge with a stub external client. They do not launch a server or prove
GPU performance. The server protocol is adapted from
[`zianglih/InferenceX@c1354d2`, `experimental/glm52_b300_fixed_seq/common.sh`](https://github.com/zianglih/InferenceX/blob/c1354d2e479a02632bc59b0c37c4b3f1e7a8d031/experimental/glm52_b300_fixed_seq/common.sh).
The client, sampling and metric implementation is the current repository's
[`benchmarks/benchmark_lib.sh`](../../benchmarks/benchmark_lib.sh) and
[`infx/bench_serving`](../../infx/bench_serving/), reused without modification.
Prior result data and recovery adapters are not included in this recipe.
