# Reproduce the published tables and four-frontier figure

This reconstruction needs only this result directory and the repository helper `experimental/glm52_megamoe_1k8k/reproduce_publication.py`. It does not access the historical `/Users/...` or `/data/...` paths recorded in provenance files. It does not launch a benchmark or require a GPU.

From the repository root, use a local analysis environment with Matplotlib 3.10.6:

```bash
python3 -m venv /tmp/glm52-r2-report-venv
/tmp/glm52-r2-report-venv/bin/python -m pip install 'matplotlib==3.10.6'
/tmp/glm52-r2-report-venv/bin/python -B \
  experimental/glm52_megamoe_1k8k/reproduce_publication.py \
  --published-dir experimental/glm52_megamoe_1k8k/results/r2-b300-20260924 \
  --output /tmp/glm52-r2-reproduced
```

The figure uses exactly two precision colors: green `#009E73` for W4A4 and orange `#E69F00` for W4A16. EP4 uses solid lines with circles; EP8 uses dashed lines with triangles, with matching legend symbols. All numerical inputs and coordinates remain unchanged.

The output directory must not exist. The helper:

1. Verifies the committed FILES.json SHA256 and every listed payload's exact byte length and SHA256.
2. Verifies the selected exact case files against each original manifest, successful measured outcomes and saved cleanup, settings, requested-versus-completed arrays and same-C ordered lengths across all four arms.
3. Recomputes all 24 rate coordinates from each original result.json and all 24 paired comparisons with 28 metrics each using Decimal precision 50.
4. Re-emits the original metric JSON/CSV, paired-comparison JSON/CSV, plotted coordinates and four-frontier PNG/SVG. It requires the numerical JSON/CSV outputs to match the published bytes exactly and separately reports whether figure bytes match.

Matplotlib 3.10.6 in the preparation environment reproduced both PNG and SVG byte-for-byte. Font, Matplotlib or platform differences can change rendering bytes; numerical reconstruction is still checked exactly. `REPRODUCED.json` records the outcome and hashes.

The selected publication raw subset intentionally does not contain every original manifest member, such as full server logs, native process samples, source-before/after and cache inventories/payloads. Thus this public reconstruction does not replace the full case, calibration, collective/tactic, outer/inner waited terminal or preservation acceptance audit. Those reviews require the separately retained complete evidence. The immutable provenance files retain historical paths and hashes, but this helper never dereferences them.

The older `results.py --run-root ...` command in RESULTS.md describes checking a complete separately collected run; it cannot validate that full evidence from this selected subset alone. The command above is the supported repository-only reproduction path for the published tables and figures.
