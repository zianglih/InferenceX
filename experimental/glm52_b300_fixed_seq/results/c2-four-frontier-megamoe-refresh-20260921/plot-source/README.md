Reproduce from preserved raw metadata/result files with Python3.11+ and matplotlib.

From this report root, with an absent output outside this report:

```sh
python3 -B plot-source/replot.py --input figures/pareto.json --output ../four-frontier-replot
```

The CLI verifies all four exported source hashes and128 raw file hashes, recomputes64 metrics/identities, and checks the four frontier memberships. It preserves historical display IDs and distinct source/run keys. No new measurements or pixel-byte identity is claimed.

Metric producer: https://github.com/SemiAnalysisAI/InferenceX/blob/8979f7c4cdd2946a02b459d5e62018e41bc02405/infx/results/fixed_sequence.py#L187-L207
Frontier source: https://github.com/SemiAnalysisAI/InferenceX-app/blob/b4b72f4f39ad6148f3477dcf67eb6a77257e7bb9/packages/app/src/
Local implementations: plot_pareto.py point_from_case/series_frontier; summarize.py read_case; plot_group.py four_series/draw.
