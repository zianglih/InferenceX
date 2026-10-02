# DeepSeek-V4.1 DSpark EP8 measured benchmark

[中文](README_zh.md)

This manual recipe reuses the GLM campaign's serial runner, owned-process cleanup,
case sealing, random-request client, native counter reducer, saved-data reader,
and Pareto plotting. The recipe does not install packages, download models or submit jobs.

The completed [18-point DSpark report](REPORT.md) includes all 3,780 successful
measured requests, acceptance length, separate Pareto plots and compact replay data.
The [original GLM-5.2 results](../glm52_ep8_c64_measured_mtp/results/2026-10-01-measured-mtp-39points/README.md) remain separate.

- **Grid:** TP=EP=attention DP=8; target MegaMoE W4A4, MegaMoE W4A16, and traditional
  TRTLLM W4A4 (`flashinfer_trtllm_routed` / A2A `none`); C2/4/8/16/32/64. The three C2 points execute first as real measured
  qualification points. Then each arm completes C4–64. Total: 18 points, 3,780
  measured requests and 756 scheduled warmups. Any failed case stops the sweep.
- **Runtime:** SGLang stays at `29c2b32d7f7351082168e622a4747bcff6469271` and
  the previous September 30 CUDA13 image digest. The corrected FlashInfer Python
  source is `7a962707af69863d386be2a9bc01ee4607470bcc`, based on
  `a03f2205263d4e691d68e485bff287e37a19b6c3`; installed main/cubin build metadata
  and cubin/NCCL wheel payloads remain at that original build. No rebuild or
  source-tree `PYTHONPATH` shadowing is used. The optional `flashinfer_wheel_commit`
  and `flashinfer_python_patch` fields permit only the reviewed
  `flashinfer/gemm/kernels/dense_blockscaled_gemm_sm100.py` replacement, identically
  across all three arms. Source snapshots verify original-base and corrected Git
  blobs; provider proof verifies the installed module's path and corrected bytes.
  The original file SHA is `a07193ecc61c522a1dc26548662524d1cbf27a0b0257888fbb4ca241bd2c7593`,
  corrected SHA `a4c20af8ad49c1d050db3dd9b933fa771a4b9d5ca830c5de8a6c66376aa19114`.
  Installation/payload preservation is separately reviewed. This is one reviewed
  correction relative to the restored baseline; original RECORD files and build
  metadata remain unchanged, including previously recorded baseline exceptions.
  Normal configurations omitting both optional fields still require matching
  source/main/cubin commits. The new `mxfp8-fix-v3` run/HOME/TMP preserves both
  earlier failed attempts; source checks are not GPU/kernel or performance acceptance.
- **Checkpoint:** pinned `nvidia/DeepSeek-V4.1-Flash-NVFP4` revision
  `3431dde3247c13b5957f682b1e3c6fcae2566079`; target, bundled DSpark draft, and
  tokenizer share the exact unchanged checkpoint. Gamma=5 and verification width=6.
  The target checkpoint is hybrid (NVFP4 routed experts plus inherited dense
  precision), while the draft remains native MXFP4/MXFP8, using
  `flashinfer_mxfp4` and A2A `none` in every arm. No BF16 draft conversion.
- **Text-only model:** all three arms explicitly pass
  `--json-model-override-args '{"vision_n_layers":0}'`. This changes the in-memory
  V4.1 configuration only; every original checkpoint file, including vision
  weights, remains intact. The existing loader skips the vision tower, aligner,
  image parameters and VL routing bias when no vision tower is built. Text
  routing keeps its normal bias; the bundled DSpark stages already disable vision.
  Vision-specific Engram/image-token handling is also disabled; this is not a
  multimodal or generated-image-token equivalence claim. The sampler draws base
  vocabulary IDs; the image marker is an added token, and the pinned encoder
  rejects image placeholders/media in user text.
  Preflight records and checks zero vision layers and non-multimodal target/draft
  configurations. Neither `--language-only` (encoder disaggregation) nor
  `--language-model-only` (unsupported architecture allowlist) applies to this pin.
  The earlier multimodal startup failed before health and measurement; its source,
  config, run and failure receipts are retained separately. The example now uses a separate `mxfp8-fix-v3` root and short TMP for the successor.
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
python3 -B experimental/dsv41_dspark_ep8/preflight.py --config /absolute/campaign.json --output /absolute/preflight-mxfp8-fix-v3 --tmp-root /tmp/infx-dsv41-fpre-1001
# Import-only preflight does not load a model or qualify distributed kernels.
python3 -B experimental/dsv41_dspark_ep8/run.py --config /absolute/campaign.json --run
python3 -B experimental/dsv41_dspark_ep8/results.py --run-root /absolute/completed-run --output /absolute/new-review
python3 -B experimental/dsv41_dspark_ep8/render.py --table /absolute/new-review/raw-metrics.json --output /absolute/new-compact-replay
```

`results.py` requires sealed raw evidence. `render.py` needs only the compact table
and replays its arithmetic and plot, not the original raw/native acceptance.
The experimental recipe is not registered in the scheduled matrix or an eval suite.

The included [kernel patch](flashinfer-mxfp8-support.patch) makes the FP8 tactic
support check conservative: FP8 tactics with a narrow tile N below64 and logical
N larger than that tile N are not eligible. This is a supported-domain guard, not a claim that every rejected
shape was reproduced as faulty. FP4 eligibility is unchanged. A fresh source
checkout can reproduce the corrected bytes without rebuilding/reinstalling any wheel:

```bash
FI_SRC=/absolute/fresh-flashinfer
git clone https://github.com/flashinfer-ai/flashinfer.git "$FI_SRC"
git -C "$FI_SRC" checkout a03f2205263d4e691d68e485bff287e37a19b6c3
git -C "$FI_SRC" apply --check "$PWD/experimental/dsv41_dspark_ep8/flashinfer-mxfp8-support.patch"
git -C "$FI_SRC" apply "$PWD/experimental/dsv41_dspark_ep8/flashinfer-mxfp8-support.patch"
git -C "$FI_SRC" add flashinfer/gemm/kernels/dense_blockscaled_gemm_sm100.py
git -C "$FI_SRC" commit -m 'fix: constrain FP8 narrow-N GEMM support'
# Record this checkout's actual new commit/root in the config; commit metadata may differ.
# Only on a quiescent restored installation, before PREP or any server:
/opt/sglang/bin/python3 - "$FI_SRC" <<'PY'
import hashlib, importlib.util, os, pathlib, site, sys, tempfile
relative = pathlib.Path("flashinfer/gemm/kernels/dense_blockscaled_gemm_sm100.py")
source = pathlib.Path(sys.argv[1]) / relative
raw = source.read_bytes()
assert hashlib.sha256(raw).hexdigest() == "a4c20af8ad49c1d050db3dd9b933fa771a4b9d5ca830c5de8a6c66376aa19114"
spec = importlib.util.find_spec("flashinfer")
package = pathlib.Path(spec.origin).resolve().parent
assert any(package.is_relative_to(pathlib.Path(p).resolve()) for p in site.getsitepackages())
installed = package.joinpath(*relative.parts[1:])
assert installed.resolve(strict=True) == installed
assert hashlib.sha256(installed.read_bytes()).hexdigest() == "a07193ecc61c522a1dc26548662524d1cbf27a0b0257888fbb4ca241bd2c7593"
fd, name = tempfile.mkstemp(prefix=".reviewed-mxfp8-", dir=installed.parent)
try:
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
    os.chmod(name, installed.stat().st_mode & 0o777)
    os.replace(name, installed)
finally:
    pathlib.Path(name).unlink(missing_ok=True)
assert hashlib.sha256(installed.read_bytes()).hexdigest() == hashlib.sha256(raw).hexdigest()
print(installed, hashlib.sha256(raw).hexdigest())
PY
```

The recipe itself never applies this patch. Keep the original installed file and
installation proof in the local preservation archive. The example records the
reviewed source commit; a reproducer must record its own clean commit if it differs.
The source and installed hashes remain mandatory, and provider metadata retains
the original wheel identity. Do not run the application step during a campaign.
