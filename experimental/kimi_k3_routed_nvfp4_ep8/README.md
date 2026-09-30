# Kimi K3: three routed-NVFP4 MoE curves

**English** | [中文](README_zh.md)

This experimental recipe compares MegaMoE W4A4, MegaMoE W4A16 and TRTLLM per-tensor NVFP4 W4A4 on one eight-B300 node. It is separate from the GLM experiment and is not an official InferenceX leaderboard submission. This scripts-only successor follows the frozen R5 continuation package and contains no measured Kimi results. One prior R4 C32 point is accepted (1/12); R4 then failed at the C4 port bind. R5 has been launched for the remaining eleven cases, whose results remain pending. Startup evidence does not establish readiness, memory fit or performance for the continuation. Earlier failures remain preserved.

**Unpublished integration prerequisite:** SGLang base `561ad447` alone does not implement this recipe's reviewed DP1/SP MegaMoE path. The exact three-file integration is local, unstaged and unpublished. This package includes only `setup/source_contract.py` and the expected file/diff descriptors; it includes neither the patch nor SGLang source. Consequently, public-only dry planning intentionally fails until those separately reviewed bytes are supplied locally. This draft is not self-contained and must not be presented as a runnable upstream-only recipe.

| Shared setting | Value |
|---|---|
| Topology | TP=EP=8; DP=1; attention TP=8; DP attention disabled; PP=DCP=1 |
| Concurrency and order | C32 first, then C4/C8/C16 for each arm |
| Workload | Nominal 1,024 input / 8,192 output tokens; uniform length range ratio 0.8; seed 0; chat template; ignore EOS |
| Counts | 2C warmups and 10C measured requests; 360 warmups and 1,800 measurements across 12 cases |
| Speculation | None; no MTP, EAGLE, DSpark or external draft model |
| Dtypes | BF16 model execution, FP8 E4M3 KV, FP32 SSM state |
| Context / memory | 16,384 tokens / static memory fraction 0.85 |
| Prefill / caches | 32,768 global chunk and prefill limit; prefill graphs and radix cache disabled |
| Admission / decode graph maximum | C / max(C,8) |
| Streaming | interval 30; saved ITL is chunk spacing, not per-token TPOT |

All arms explicitly set `--quantization modelopt_fp4` to declare the accepted checkpoint format. At the pinned Kimi implementation, ModelConfig can infer this format while ServerArgs remains unset; the Mega backend gate requires the explicit shared declaration. This is a format integration setting, not a per-token or fast-math override.

The only arm selectors are MegaMoE versus TRTLLM MoE/A2A backends and `SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1` for the W4A16 arm. Default per-token, fast-math, combine, IKR and kernel-tuning settings remain unchanged. Compilation caches are shared across sequential cases; tactic caches are separated by arm. This is not an isolated GEMM causal experiment.

## Pinned inputs

- SGLang base `561ad447c74bb757a40677ee9ce038f9ca429d2c` plus the separately reviewed, unpublished three-file integration. The required binary diff is 6,993 bytes, SHA256 `d4bdb5246dbeaca7bf23472cbae617b434bcb3b77c248d0e40e46b8405786ef1`. `setup/source_contract.py` requires the exact HEAD, changed-file set, individual bytes and diff, with an empty index and untracked closure; it does not permit arbitrary dirty sources.
- FlashInfer `a03f2205263d4e691d68e485bff287e37a19b6c3`.
- InferenceX benchmark client `652ac186d88ebcd6ff995afbe7c3094751f0f4a2`; the complete eight-file client package is vendored unchanged with its byte manifest and license. The current repository checkout's client is not substituted.
- Image: `lmsysorg/sglang:nightly-dev-cu13-20260929-79cafec0@sha256:0f075735a6bf913a7cc1cd7ece4f526ae8af70fc5b88fdc02d9efe92a61cf3ae`.
- Original checkpoint: `moonshotai/Kimi-K3` revision `f831ab66814297da540d832a5235f8e904f29d06`; upstream Miles `9e4260de047a704208535c0e90c531929879ab40` converts routed experts MXFP4→BF16→NVFP4. Every other tensor retains its original dtype, shape and raw bytes in the accepted conversion contract. Original reference JSON files are reference metadata only.

The exact model path is intentionally fixed by `setup/checkpoint_contract.py` to this reviewed conversion's `main-routed-nvfp4-attempt2`. Its interrupted predecessor is not usable input. Moving or replacing the checkpoint requires a separately reviewed acceptance binding and corresponding contract update; changing a path does not establish tensor provenance. Model loading, GPU dispatch, quality and performance require actual serving evidence.

## Configure and plan

Use Python 3.12 or newer. Planning uses the standard library and does not import model packages or contact a server. See [DEPENDENCIES.md](DEPENDENCIES.md) for execution dependencies. The helpers do not install packages, fetch models or change source checkouts.

Planning also verifies the local integration bytes. The files identified by `campaign.json.local_changes.sglang` must first be supplied to a **private local copy**: `artifacts/sglang-dp1.patch` and the three listed `sglang/python/...` files. They are intentionally not shipped here. The serving checkout at `runtime.sglang_root` must independently satisfy the same exact guard. No command to obtain or publish this still-local integration is provided.

After that prerequisite, the interface is:

```sh
python3 -B setup/run_campaign.py --dry-run --campaign campaign.json \
  --output /absolute/new/kimi-plan
```

`campaign.json` retains status `PUBLIC_RECIPE_REQUIRES_LOCAL_PREFLIGHT`, authorization `PREPARE_ONLY`, and explicit `/REVIEW_REQUIRED/` locations. These public placeholders are separate from the immutable active R5 configuration. It does not embed a developer workstation receipt path. Copy it to a local runtime configuration and supply these values deliberately:

| Field | Local value required |
|---|---|
| `runtime.python` | Lexical Python executable in the validated serving environment |
| `runtime.sglang_root`, `runtime.flashinfer_root` | Exact source roots including the separately supplied reviewed SG integration; installed import origins must match preflight |
| `runtime.run_root` | Fresh exclusive output directory |
| `runtime.tmp_root` | Fresh owned `/tmp/infx-*` path shorter than 30 bytes |
| `runtime.model_path`, `checkpoint.output_path` | Fixed reviewed model location; both must match the checkpoint contract |
| `checkpoint.acceptance.path` | Local copy of the exact normalized checkpoint receipt; preserve its bytes/SHA binding |
| `--runtime-project-root` | Staged directory containing this recipe's exact scripts and vendored client |

The template retains the accepted checkpoint receipt's content digest but does not ship private conversion evidence. Execution must receive and validate that evidence separately. A dry plan is not evidence that the acceptance file, weights, runtime, GPU ownership or free memory has been validated.

## Continue from one accepted point

The canonical matrix remains twelve cases with 360 warmups and 1,800 measured requests. `continuation.execution_case_ids` selects exactly the remaining eleven: W4A4 C4/C8/C16, then W4A16 C32/C4/C8/C16, then TRTLLM C32/C4/C8/C16. This execution performs 296 warmups and 1,480 measurements. Preflight still checks the canonical C32 configuration for each arm; the worker and outer terminal must report only the eleven actually executed cases.

Two separately reviewed actual inputs are mandatory: `continuation.prior_acceptance` must bind `ACCEPTED_KIMI_PRIOR_C32_FOR_CONTINUATION`, and `continuation.cache_seed_acceptance` must bind `ACCEPTED_KIMI_QUIESCENT_CACHE_SEED`. The public descriptors are pending placeholders, not approvals. The prior receipt binds fourteen immutable JSON inputs, including the accepted native/settings/workload review, original C32 ordered arrays, source/cache lineage and failed R4 terminal. It accepts that point, not the original sweep. The runner seeds its C32 length reference from those exact arrays.

The reviewed seed copies compilation, HF and TMP payloads without hardlinks into new owned roots, preserving the source caches. A fresh TMP owner is retained; only explicitly reviewed historical marker/IPC exclusions are permitted. The full installed inventory is saved separately and bound by a compact receipt. There is no fresh-cache fallback, and preserved bytes do not guarantee path-dependent cache hits. `cache_seed.py` deliberately fixes the original R4, R5 and seed namespaces for this recipe; arbitrary path relocation needs a separately reviewed contract. Public path placeholders must be resolved consistently with these guards, not merely replaced with any available directory.

Plain port binding retries only `EADDRINUSE`, for at most 120 seconds, and logs wall-clock and monotonic elapsed time. No `SO_REUSEADDR` is used. Other errors and persistent occupation fail; source/runtime/checkpoint/GPU guards repeat after a successful wait. This does not establish the cause of R4's original port occupation.

Complete results require `ACCEPTED_COMPOSITE_CAMPAIGN`, one accepted R4 point plus eleven accepted R5 points, an actual successful eleven-case terminal and independent composite review. `prior_binding_map` relocates immutable parent evidence and the full installed inventory by identical bytes/SHA. The reader rejects a fabricated single twelve-case terminal or an ordinary complete-sweep receipt for a continuation campaign. Figures and reports identify both execution segments. No raw result or acceptance receipt is bundled here.

## Execute and review

The runner uses one `internal_states` entry for DP1, not eight entries merely because there are eight GPUs. The runner still checks every state's capacity/speculation and the owned endpoint before and after readback. Physical GPU identity and throughput normalization remain eight-GPU checks.

Use the finalized `setup/preflight.py` and `setup/run_campaign.py --execute` interfaces on the owned node. Supply their exact current preflight/approval receipt rather than reusing a stale source-only report. The local campaign must explicitly authorize execution and have no unresolved blockers. `--help` documents the final receipt arguments; the default remains dry planning. The serial driver owns its server/client processes, preserves source/argv/environment, raw logs, GPU/ownership receipts and sealed results, and tears down only the processes it launched.

The explicit interfaces are:

```sh
python3 -B setup/preflight.py --request /absolute/preflight-request.json \
  --sha256 REQUEST_SHA256 --arm megamoe-w4a4
# Repeat preflight for megamoe-w4a16 and trtllm-w4a4, then review all three
# receipts and assemble the source-bound ACCEPTED_KIMI_RUNTIME_PREFLIGHT marker.
/opt/sglang/bin/python3 -B setup/run_campaign.py --execute \
  --campaign /absolute/campaign.local.json \
  --runtime-project-root /absolute/staged-recipe \
  --approval-marker /absolute/accepted-runtime.json \
  --approval-sha256 APPROVAL_SHA256
```

The request and approval hashes name exact reviewed bytes. The runner also validates their campaign, plan, checkpoint, source and runtime bindings. These commands are opt-in interfaces, not evidence that a run succeeded.

Keep the immutable campaign, plan, installed-source and checkpoint proofs with the raw output. `setup/results.py` consumes a separately accepted complete collection, not a directory of arbitrary result JSONs. It requires a separately accepted composite of all 12 cases, 1,800 successful measured requests, zero failed measured requests, matched ordered lengths, actual native/backend reviews and waited terminal/cleanup evidence before producing English-only tables and three Pareto frontiers. The original failed sweep is retained as failed.

X is `1000 / saved median TPOT_ms`; Y is `total output tokens / complete measured duration / 8`. Whole-interval throughput is not timed decode. Preserve all saved percentiles and compare every same-C pair. No synthetic fixture or source-only validation counts as a measured result, and these data do not prove numerical equivalence or statistical significance.

## Local validation boundaries

The public-only preflight and continuation CPU tests use synthetic inputs and can run without the omitted integration:

```sh
python3 -B -m unittest discover -s setup -p test_preflight.py -v
python3 -B -m unittest discover -s setup -p test_continuation.py -v
```

Plan-dependent tests, the reader provenance fixtures and the full runner suite require the exact local integration files; run them only in a private working copy after supplying that prerequisite. The publication validation separately checks that an incomplete public dry run fails before producing a plan, and tests DP1/DP8 endpoint cardinality, wrong cardinalities, local capacity, speculation and owner failure paths against the exact R5 implementation. No synthetic fixture is a benchmark result.

The public preflight test file omits one inherited AST-extraction test to comply with repository test policy; the production preflight and all other runtime scripts remain exact R5 bytes. Its historical private validation is preserved. The continuation pending-parent test explicitly constructs a pending fixture. Composite reader fixtures are synthetic and cannot be published as measurements.
