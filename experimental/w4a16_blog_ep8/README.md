# W4A16 blog: fresh EP8 serving comparison

This recipe measures three target MoE paths on eight B300 GPUs: MegaMoE W4A4,
MegaMoE W4A16, and TRTLLM NVFP4 W4A4. It runs DeepSeek-V4.1 Flash with DSpark
first, followed by GLM-5.2 with EAGLE/MTP. Each model has 21 points at concurrency
1, 2, 4, 8, 16, 32, and 64. These are fresh measurements; older InferenceX results
are not inputs to the plots.

[Fresh measured results and plots](results/20261010/README.md): V4.1 is complete;
GLM-5.2 is running. The measured recipe commit is `9d9e053d072568ecba7ad2543f3ded240d3d76f4`;
later result-only commits do not change the running recipe.

## Source and environment pins

| Component | Pin |
| --- | --- |
| Image | `lmsysorg/sglang:nightly-dev-cu13-20261010-961bcf48` |
| Image digest | `sha256:53efab7e8255a47b19edc81a0f1ad37cd6c8341bfe8f448d268700b182b2f03d` |
| SGLang integration base | `38114937747fff49d749c3ee6a7e2f240e34530a` from [#39210](https://github.com/sgl-project/sglang/pull/39210) |
| SGLang with DSpark compatibility | `22250e374abcff99e78e862da647a83b1c2ebe27` from [child draft #7](https://github.com/zianglih/sglang/pull/7) |
| FlashInfer source | `866c80d0c70a90624b4c2056d12d1543d709609e` from [#6277](https://github.com/flashinfer-ai/flashinfer/pull/6277) |
| DeepGEMM dependency | `sgl-deep-gemm==0.2.2`, required by the pinned SGLang source |
| V4.1 checkpoint | `nvidia/DeepSeek-V4.1-Flash-NVFP4@3431dde3247c13b5957f682b1e3c6fcae2566079` |
| GLM-5.2 checkpoint | NVFP4 revision `53e0691e21895a3863a606dfd12910c69eba94ab` |

The benchmark commit, exact installation manifest, and checkpoint paths are
recorded in each `campaign.json`. The AMD64 development image uses CUDA 13.0;
the originally considered CUDA 13.4 image was ARM64-only. The SGLang child commit
allows FlashInfer MegaMoE with the native DSpark MXFP4 draft and scopes its backend
contexts across draft construction, graph capture, and execution. It preserves
the integration's attention-DP and static ragged-verification machinery.

Build the FlashInfer Python and cubin packages from the pinned checkout. Do not
install released FlashInfer wheels or a released JIT-cache provider. The installer quarantines orphaned FlashInfer module directories left by the image's package uninstall before building the cubin package. SGLang is
also installed from a local source wheel, including its Rust extensions. The
runner imports installed packages and checks the small installed-source manifest
before running; it does not shadow those packages with source-tree imports.

The installation scripts expect clean, pinned clones at `ROOT/sources/flashinfer`
and `ROOT/sources/sglang`, the development image's existing CUDA/PyTorch stack,
and build dependencies `setuptools-rust==1.13.0` and `setuptools-scm==10.3.4`.
The image includes `sgl-deep-gemm==0.2.1.post1`; upgrade only that runtime
dependency to SGLang's required `0.2.2` with `--no-deps`. Its existing dependency
`apache-tvm-ffi==0.1.11` must remain installed. Preserve the image's PyTorch and
the source-built FlashInfer packages; do not resolve SGLang's full dependency
list, which pins released FlashInfer wheels.
The verified image environment uses `/opt/sglang/bin/python3`. On an idle allocated node:

```bash
/opt/sglang/bin/python3 -m pip install --no-cache-dir setuptools-rust==1.13.0 setuptools-scm==10.3.4
/opt/sglang/bin/python3 -m pip install --no-deps --no-cache-dir sgl-deep-gemm==0.2.2
/opt/sglang/bin/python3 experimental/w4a16_blog_ep8/install_sources.py \
  --root /data/home/ziangli/inferencex-w4a16-blog-rerun-20261009 \
  --cuda-version 13.0 --sg-sha 22250e374abcff99e78e862da647a83b1c2ebe27
```

## Workload and backend settings

| Setting | Both models |
| --- | --- |
| Topology | TP8, EP8, attention-DP8; one model replica |
| Input/output lengths | Nominal 1,024 / 8,192, uniformly sampled at ratio 0.8 |
| Random seed | 0 |
| Warmup/measured requests | 2C / 10C; all must succeed |
| Sampling | Temperature 0, `ignore_eos=true`, unlimited offered request rate |
| Stream interval | 30 |
| Memory fraction | 0.80 |
| Prefill limits | Global chunk 32,768; resolved per-attention-rank chunk 4,096; max prefill tokens 32,768 |
| Running-request capacity | `max(C, 8)` global, including C1/C2/C4 |
| Graphs | Decode graph max batch C; prefill graphs disabled |
| Radix cache | Disabled |
| Weight loading | Multithreaded |

MegaMoE arms use `flashinfer_megamoe` for both target runner and all-to-all.
TRTLLM uses `flashinfer_trtllm_routed` for V4.1 and `flashinfer_trtllm` for GLM-5.2,
with target all-to-all `none`. Only MegaMoE W4A16 sets
`SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1`; this selector also affects eligible dense
NVFP4 linears. All other kernel/tactic/precision settings use the pinned runtime's
defaults. No per-token scaling, fast-math, combine, IKR, or 4over6 override is set.

V4.1 uses the checkpoint's text-only chat formatter (`thinking_mode="chat"`,
`reasoning_effort=None`), `vision_n_layers=0`, DP LM head, DSpark block size 5,
static ragged verification, and explicit native draft runner `flashinfer_mxfp4`
with draft all-to-all `none`. The same checkpoint supplies target and draft.
Target attention/KV/dense precision follow V4.1 runtime defaults, including its
native mixed-precision layers; the three arm names describe the target MoE path.

GLM-5.2 uses its tokenizer chat template, `modelopt_fp4`, FP8 E4M3 KV,
DSA with TRTLLM prefill/decode, `glm47` tool parser, `glm45` reasoning parser, and
EAGLE with three steps, top-k 1, four verification tokens. Its bundled draft uses
`flashinfer_trtllm` with draft all-to-all `none`. It retains its inherited DP
LM-head default.

The runner first qualifies C1 on all three arms of a model, then runs C2–C64 for
each arm. V4.1 finishes before GLM-5.2 starts. The exact order is saved. Every case
starts a fresh server and closes its owned server/client descendants before the
next case. Compile caches are shared; runtime tactic caches are separate by model
and arm. Normal warmups can populate defaults; this is not a cold-start study.

## Measurement definitions

The client reuses InferenceX's deterministic random-workload sampler and completion
request payload. A compressed ordered prompt plan is generated once per model/C
before timing and reused by all three arms. V4.1's formatter is loaded from the
pinned checkpoint after checking its source hash.

The clean harness differs from the earlier campaign in three disclosed ways:
prompt preparation uses the existing serial sampler, warmup failures are fatal,
and requests share an aiohttp session/connection pool. These choices apply equally
to the three arms and are outside the model/config comparison; direct differences
against older campaign numbers should not be attributed solely to kernel changes.

- **Throughput per GPU:** all measured completion tokens divided by the entire
  measured interval, including scheduling and drain, divided by eight GPUs.
- **Interactivity:** `1000 / median TPOT (ms)`, where each request's TPOT is the
  first-to-last completion-chunk span divided by its completion count minus one.
- **Acceptance length:** sum of measured completion tokens / sum of native
  verification counts. It includes the bonus token. This is a weighted ratio,
  not an average of request or server-window averages.
- **Acceptance rate:** sum of native correct draft tokens / sum of native proposed
  draft tokens. The configured proposal budget is five per verification for
  DSpark and three for GLM's EAGLE setup. A larger draft budget alone does not
  establish a larger W4A16 acceptance difference.
- **ITL:** spacing of received chunks at stream interval 30, not single-token
  latency. TTFT/E2EL and mean/median/p90/p99 latency scalars are also saved.

Every measured response must contain final usage and native speculative details.
The client validates native ratios and request output lengths, and the exporter
requires complete counter coverage, zero warmup/measured failures, and identical
ordered prompt/length digests across arms at each concurrency. Acceptance length
is a diagnostic of speculative execution, not an independent quality evaluation.

## Run and render

Copy `config.example.json` outside the source checkout, replace the benchmark
commit with the committed recipe HEAD, confirm the image/checkpoint/installation
paths, and use fresh output/TMP directories. The runner refuses existing output
roots. It does not allocate nodes, install packages, resume, or retry failed cases.
An operator must inspect any failure before creating an explicitly named new run.

```bash
python experimental/w4a16_blog_ep8/run.py --config /data/path/campaign-config.json --plan
python experimental/w4a16_blog_ep8/run.py --config /data/path/campaign-config.json --run
python experimental/w4a16_blog_ep8/results.py \
  --run /data/path/run --model dsv41 --output /data/path/compact-dsv41
python experimental/w4a16_blog_ep8/render.py \
  --table /data/path/compact-dsv41/metrics.json --output /data/path/compact-dsv41/figures
python experimental/w4a16_blog_ep8/results.py \
  --run /data/path/run --model glm52 --output /data/path/compact-glm52
python experimental/w4a16_blog_ep8/render.py \
  --table /data/path/compact-glm52/metrics.json --output /data/path/compact-glm52/figures
```

Only compact JSON/CSV/Markdown tables, provenance, comparison tables, and inspected
PNG/SVG plots belong in the public result set. Full compressed server/client logs,
small per-request counter records, prompt plans, build wheels, and compile caches
stay on cluster persistent storage. Generated text and token-level timing arrays
are not retained. No whole-container snapshot or exhaustive tensor hashing is
needed for this recipe.

The renderer makes independent throughput/interactivity frontiers for the three
arms and a separate acceptance-length chart for each model. It retains all
concurrency points, marks dominated points, and emits scalar plot data for replay.
Green is MegaMoE W4A4, orange is MegaMoE W4A16, and blue is TRTLLM NVFP4 W4A4.

## Focused CPU checks

```bash
uv run --no-project --with numpy --with aiohttp --with matplotlib \
  python -m unittest discover -s experimental/w4a16_blog_ep8 -p 'test_*.py' -v
ruff check experimental/w4a16_blog_ep8
```

CPU checks exercise final-stream accounting, warmup exclusion and bounded
concurrency, ratio aggregation, command/environment isolation, result validation,
and Pareto rendering. GPU runtime validation and the actual complete 42-point
campaign are separate acceptance steps; generated fixture plots are not results.

This standalone manual recipe is recorded under changelog key
`experimental-w4a16-blog-b300-sglang-ep8`. It is deliberately not registered in the
shared CI matrix or substituted for an existing AgentX key. The ordinary matrix
validator therefore rejects that key; a successful manual campaign does not imply
a green CI sweep, eval qualification, dashboard ingestion, or merge eligibility.
