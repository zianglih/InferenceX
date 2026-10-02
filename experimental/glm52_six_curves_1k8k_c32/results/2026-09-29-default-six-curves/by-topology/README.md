# Historical GLM plots: compact public reproduction

[English](README.md) | [简体中文](README_zh.md)

The 24 historical points and all existing combined/EP4/EP8 image bytes are unchanged. Measured-only MTP acceptance length remains `AL=N/A` because native verification counts were not saved.

From the parent bundle directory:

```sh
python3 -B by-topology/render_compact.py --published-root . --output /absolute/path/to/new-historical-plots
```

The renderer verifies the compact public manifest and loads `results/raw-metrics.json`; it does not read raw logs or revalidate measurements. The saved acceptance sidecar's raw-file descriptors are historical references to locally retained evidence. All original full bundles remain local. See [REPRODUCE.md](../REPRODUCE.md) for the full-evidence boundary.
