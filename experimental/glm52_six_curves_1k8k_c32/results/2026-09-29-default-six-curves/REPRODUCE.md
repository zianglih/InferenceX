# Reproduce the six GLM-5.2 frontiers

This selected raw-data bundle contains 24 points, 3,600 measured requests and 720 warmups. Publication, visual inspection and preservation status are tracked separately; PROVENANCE.json records this local preparation stage.

From this directory, use Python 3.11+ with Matplotlib and a new output directory:

```bash
python3 -B source/experimental/glm52_six_curves_1k8k_c32/results.py --run-root raw --output ../regenerated-six-curves
```

All necessary reader and five recorded recipe/client source files are included. The command rehashes every case member, checks the sealed producer environment and command joins across checkout relocation, and regenerates full JSON/CSV scalar tables, all 36 paired comparisons, point coordinates, six frontiers and PNG/SVG. Remote paths in raw receipts are preserved as evidence; no remote filesystem is needed. Plot byte identity can depend on Python/Matplotlib/fonts; saved numeric coordinates, scalar values, pair arithmetic and frontier membership are the reproducibility targets.

## Environment and methods

- Image: `lmsysorg/sglang:nightly-dev-cu13-20260929-79cafec0@sha256:0f075735a6bf913a7cc1cd7ece4f526ae8af70fc5b88fdc02d9efe92a61cf3ae`.
- SGLang: `9d38e0530a1e35d1756a7fabf044bc39b77209b8`; FlashInfer: `a03f2205263d4e691d68e485bff287e37a19b6c3`.
- Checkpoint revision: `53e0691e21895a3863a606dfd12910c69eba94ab`. The exact measured settings, package freeze, launch commands and logs are retained per case.
- One B300 node; each group uses TP=EP=DP attention 4 or 8. MegaMoE W4A4 is green #009E73; MegaMoE W4A16 is orange #E69F00; TRTLLM NVFP4 W4A4 is blue #0072B2. TP4 uses solid/circle; TP8 uses dashed/triangle.
- C32 calibrates first, followed by C4/C8/C16 for each group. Each case uses 2C warmups and 10C measured requests, nominal input/output 1,024/8,192, range ratio 0.8 and seed 0. Exact requested/completed arrays remain in the raw case files.
- EAGLE steps 3 / top-k 1 / draft tokens 4; draft TRTLLM/none BF16 MoE path; FP8 E4M3 KV, static memory 0.8, global prefill chunk 32,768, prefill graphs disabled, stream interval 30.
- x = 1,000 / saved median TPOT milliseconds; y = output tokens / the client's complete measured perf_counter interval / GPU count. This is not separately timed decode. Unix phase endpoints use a separate clock.
- Current backend defaults are retained. W4A16 selection can affect eligible dense NVFP4 linears as well as MegaMoE experts. Draft BF16 names its MoE path, not every tensor.
- Saved ITL is chunk spacing at stream interval 30. Saved percentiles are retained, not independently reconstructed from unsaved per-request latency samples. Sequential backend/topology/cache history does not establish causality, significance, numerical equivalence or response-content equivalence.
- This selected bundle is not the full source/cache/wheel archive, a whole-container snapshot or proof of installed RECORD byte equality. Preservation, checkpoint retention and owned-node cleanup have independent receipts.

[Complete result report](results/RESULTS.md) · [Saved scalar JSON](results/raw-saved-scalars.json) · [All paired metrics](results/paired-comparisons.csv) · [PNG](results/pareto.png) · [SVG](results/pareto.svg)
