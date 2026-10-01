# DeepSeek-V4.1 DSpark EP8 measured benchmark

[中文](README_zh.md)

This manual recipe reuses the GLM campaign's serial runner, owned-process cleanup,
case sealing, random-request client, native counter reducer, saved-data reader,
and Pareto plotting. It does not install packages, download models, submit jobs,
or claim successful GPU qualification.

- **Grid:** TP=EP=attention DP=8; target MegaMoE W4A4, MegaMoE W4A16, and traditional
  TRTLLM W4A4 (`flashinfer_trtllm_routed` / A2A `none`); C2/4/8/16/32/64. The three C2 points execute first as real measured
  qualification points. Then each arm completes C4–64. Total: 18 points, 3,780
  measured requests and 756 scheduled warmups. Any failed case stops the sweep.
- **Runtime:** `config.example.json` pins SGLang PR head
  `29c2b32d7f7351082168e622a4747bcff6469271`, FlashInfer
  `a03f2205263d4e691d68e485bff287e37a19b6c3`, and the previous September 30 CUDA13
  image digest. Both source trees must be clean at their declared commits.
  Installed FlashInfer main/cubin build metadata must match; its source tree
  must not shadow the installed wheels. Environment restoration is a separate step.
- **Checkpoint:** pinned `nvidia/DeepSeek-V4.1-Flash-NVFP4` revision
  `3431dde3247c13b5957f682b1e3c6fcae2566079`; target, bundled DSpark draft, and
  tokenizer share the exact unchanged checkpoint. Gamma=5 and verification width=6.
  The target checkpoint is hybrid (NVFP4 routed experts plus inherited dense
  precision), while the draft remains native MXFP4/MXFP8, using
  `flashinfer_mxfp4` and A2A `none` in every arm. No BF16 draft conversion.
- **Routing:** the explicit routed TRT target preserves DeepSeek's materialized
  routing and matches its NVFP4 source default. The shared TRT primitive name
  alone does not identify a logits-versus-routed call; native evidence is required.
- **Defaults:** no GLM parser, DSA, KV dtype, or modelopt quantization override.
  Actual resolved model/attention/KV/quantization defaults are saved by preflight
  and each server endpoint. DP LM head and static ragged verification are explicit.
  W4A16 alone sets its existing selector; optional per-token/fast-math knobs remain
  absent. Actual primitive/precision/topology evidence remains a native review gate.
- **Workload:** nominal 1,024 input / 8,192 output, ratio0.8, seed0, 2C warmups
  followed by 10C measured requests, greedy sampling, ignore EOS, unbounded request
  rate and stream interval30. Warmups are scheduled and awaited; the inherited
  client does not independently require every warmup response to succeed. All
  measured responses must succeed. Same-C ordered requested/completed token lengths
  must match across arms. The existing sampler retains its parallel preprocessing.
- **Prompt formatting:** explicit DeepSeek-V4.1 `thinking_mode="chat"`,
  `reasoning_effort=None`, text-only. The opt-in `--dsv41` path verifies and loads
  checkpoint `encoding/encoding.py` SHA256
  `502bdaec8a3fd88ebc24c4721a7038fbe42f2063c664638127056107920035c1`.
  Unlike the old `--dsv4` path, this does not silently select thinking mode.
  Previous GLM runs used their tokenizer's chat template with a generation prompt;
  the nominal sampling method is reused, not GLM prompt bytes or its tokenizer.
- **Accounting:** AL is `sum(completion_tokens)/sum(spec_verify_ct)` over all
  successful measured requests, including native bonus tokens. Rate is
  `sum(correct_drafts)/sum(proposed_drafts)`, where DSpark exports
  `proposed_drafts=5*verify_count`; this is the configured proposal budget, not
  the number of ragged slots actually verified. Every final request must contain
  valid counters; warmups and server lifetime/window averages are excluded.
- **Performance:** x=`1000/saved median TPOT`; y=`output_tokens/full measured
  duration/8`. Saved scalar latencies are retained; no absent latency arrays or
  percentiles are reconstructed. ITL reflects streamed chunk spacing. These
  measurements do not establish numerical/content quality or causal backend effects.
- **Storage:** fresh exclusive HOME/TMP/compiler/tactic scopes, no cache seed.
  Compiler caches are shared within this new campaign; tactic namespaces are
  separate by arm. Cleanup addresses recorded owned births and waits for children;
  a successful benchmark does not imply a graceful server exit. Full logs, raw
  requests/counters, and archives remain local. Publish only compact tables,
  plots, source/provenance descriptors, and replay code; old GLM bundles are unchanged.

From the InferenceX checkout, review/update the actual paths in a copied config:

```bash
python3 -B experimental/dsv41_dspark_ep8/check.py
python3 -B experimental/dsv41_dspark_ep8/run.py --config /absolute/campaign.json --plan
# On the explicitly restored node, with the config's source PYTHONPATH and loader environment:
python3 -B experimental/dsv41_dspark_ep8/preflight.py --config /absolute/campaign.json --output /absolute/exclusive-preflight --tmp-root /tmp/infx-dsv41-pre-1001
# Import-only preflight does not load a model or qualify distributed kernels.
python3 -B experimental/dsv41_dspark_ep8/run.py --config /absolute/campaign.json --run
python3 -B experimental/dsv41_dspark_ep8/results.py --run-root /absolute/completed-run --output /absolute/new-review
python3 -B experimental/dsv41_dspark_ep8/render.py --table /absolute/new-review/raw-metrics.json --output /absolute/new-compact-replay
```

`results.py` requires sealed raw evidence. `render.py` needs only the compact table
and replays its arithmetic and plot, not the original raw/native acceptance.
The experimental recipe is not registered in the scheduled matrix or an eval suite.
