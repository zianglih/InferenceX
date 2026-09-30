#!/usr/bin/env python3
"""Create a local publication candidate from accepted real sealed results."""

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[2]
RECIPE = Path("experimental/glm52_six_curves_1k8k_c32")
ROOT_FILES = (
    "config.json",
    "matrix.json",
    "worker-exit.json",
    "tmp-preflight.json",
    "compile-cache-seed.json",
)
SOURCE_FILES = (
    RECIPE / "run.py",
    RECIPE / "results.py",
    RECIPE / "benchmark_mtp.sh",
    Path("benchmarks/benchmark_lib.sh"),
    Path("infx/bench_serving/benchmark_serving.py"),
    Path("infx/bench_serving/backend_request_func.py"),
    Path("infx/bench_serving/speculative_metrics.py"),
    Path("infx/__init__.py"),
    Path("infx/bench_serving/__init__.py"),
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(path):
    path = Path(path).absolute()
    need(
        ".." not in path.parts
        and path.resolve() == path
        and all(not q.is_symlink() for q in (path, *path.parents)),
        "Linked or noncanonical local path",
    )
    return path


def descriptor(path):
    path = canonical(path)
    a = path.stat()
    need(stat.S_ISREG(a.st_mode), "Regular file required")

    def stamp(value):
        return (
            value.st_dev,
            value.st_ino,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    with path.open("rb") as stream:
        need(stamp(os.fstat(stream.fileno())) == stamp(a), "Input changed at open")
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        need(stamp(os.fstat(stream.fileno())) == stamp(a), "Input changed during hash")
    need(stamp(path.stat()) == stamp(a), "Input changed after hash")
    return {"bytes": a.st_size, "sha256": digest}


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def copy_exact(source, destination, expected=None):
    before = descriptor(source)
    if expected is not None:
        need(before == expected, "Source differs from sealed descriptor")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("xb") as dst:
        while block := src.read(1024**2):
            dst.write(block)
        dst.flush()
        os.fsync(dst.fileno())
    need(
        descriptor(source) == before == descriptor(destination), "Copied bytes changed"
    )
    need(destination.stat().st_nlink == 1, "Public copy must be private")


def load_reader(repo):
    lock = json.loads((Path(__file__).parent / "SOURCE_LOCK.json").read_bytes())
    need(
        set(lock["files"]) == {str(p) for p in SOURCE_FILES},
        "Reader source closure differs",
    )
    for relative, expected in lock["files"].items():
        need(
            descriptor(repo / relative) == expected,
            "Pinned reader source changed: " + relative,
        )
    sys.path.insert(0, str(repo / RECIPE))
    return importlib.import_module("results")


def verify_release(path, reader):
    release = reader.read(path)
    expected = [c["case_id"] for c in reader.recipe.matrix()]
    need(
        release.get("status") == "MEASURED_RESULTS_ACCEPTED",
        "Actual measured release required",
    )
    need(
        release.get("case_ids") == expected
        and release.get("measured_requests") == 3780
        and release.get("warmup_requests") == 756
        and release.get("campaign_contract") == "glm52-six-curves-measured-mtp-v1"
        and release.get("failed_requests") == 0,
        "Incomplete release accounting",
    )
    for key in (
        "native_cases_accepted",
        "measured_speculative_metrics_accepted",
        "paired_comparisons_accepted",
        "runner_terminal_accepted",
        "outer_terminal_accepted",
    ):
        need(release.get(key) is True, "Missing actual acceptance: " + key)
    bindings = release.get("bindings")
    need(isinstance(bindings, list) and bindings, "Actual receipt bindings required")
    seen = set()
    for row in bindings:
        need(set(row) == {"path", "bytes", "sha256"}, "Invalid release binding")
        source = canonical(row["path"])
        need(
            source.is_relative_to(PROJECT) and str(source) not in seen,
            "Release binding outside project or duplicate",
        )
        seen.add(str(source))
        need(
            descriptor(source) == {k: row[k] for k in ("bytes", "sha256")},
            "Changed release receipt",
        )
    return release


def verify_view(reader, rows, directory, topology=None):
    selected_rows = [r for r in rows if topology is None or r["tp"] == topology]
    points = reader.read(directory / "plot-points.json")
    need(
        len(points) == (36 if topology is None else 18)
        and {q["case_id"] for q in points} == {q["case_id"] for q in selected_rows},
        "Wrong plot point coverage",
    )
    by_id = {q["case_id"]: q for q in selected_rows}
    for point in points:
        row = by_id[point["case_id"]]
        need(
            point["x"] == 1000 / row["median_tpot_ms"]
            and point["y"] == row["output_tokens"] / row["duration_s"] / row["tp"],
            "Plot coordinates differ",
        )
        need(
            all(
                point[k] == row[k] for k in ("arm_id", "tp", "ep", "dp", "concurrency")
            ),
            "Plot labels differ",
        )
        need(
            point["measured_acceptance_length"] == row["measured_acceptance_length"]
            and point["measured_acceptance_rate"] == row["measured_acceptance_rate"]
            and point["acceptance_scope"] == "measured_requests_only",
            "Measured AL/rate plot values differ",
        )
    groups = reader.read(directory / "frontiers.json")
    need(len(groups) == (6 if topology is None else 3), "Wrong frontier count")
    need(
        groups
        == [
            g for g in reader.frontiers(rows) if topology is None or g["tp"] == topology
        ],
        "Frontier identities differ",
    )
    for group in groups:
        selected = [
            q
            for q in points
            if (q["arm_id"], q["tp"]) == (group["arm_id"], group["tp"])
        ]
        expected = [
            q
            for q in selected
            if not any(
                (v["x"] >= q["x"] and v["y"] >= q["y"])
                and (v["x"] > q["x"] or v["y"] > q["y"])
                for v in selected
            )
        ]
        need(
            group["case_ids"]
            == [q["case_id"] for q in sorted(expected, key=lambda v: v["x"])],
            "Frontier dominance differs",
        )


def package(args):
    repo, raw, evidence, out = map(
        canonical, (args.repo_root, args.run_root, args.release_evidence, args.output)
    )
    need(
        repo.is_relative_to(PROJECT)
        and raw.is_relative_to(PROJECT)
        and evidence.is_relative_to(PROJECT),
        "Inputs must be owned project-local data",
    )
    need(
        out.is_relative_to(PROJECT / "artifacts"),
        "Output must be an exclusive project artifact",
    )
    reader = load_reader(repo)
    release = verify_release(evidence, reader)
    rows = reader.load(raw, False)
    need(
        len(rows) == 36 and sum(r["completed"] for r in rows) == 3780,
        "Complete real grid required",
    )
    out.mkdir(parents=True, exist_ok=False)
    try:
        payload = out / "payload"
        payload.mkdir()
        copy_exact(evidence, out / "release-evidence.exact.json")
        for name in ROOT_FILES:
            copy_exact(raw / name, payload / "raw" / name)
        for row in rows:
            source = raw / "cases" / row["case_id"]
            target = payload / "raw/cases" / row["case_id"]
            manifest = reader.read(source / "manifest.json")
            copy_exact(source / "manifest.json", target / "manifest.json")
            for name, info in manifest["files"].items():
                part = Path(name)
                need(
                    not part.is_absolute()
                    and ".." not in part.parts
                    and str(part) == name,
                    "Unsafe case member",
                )
                copy_exact(
                    source / part,
                    target / part,
                    {"bytes": info["bytes"], "sha256": info["sha256"]},
                )
        for part in SOURCE_FILES:
            copy_exact(repo / part, payload / "source" / part)
        command = [
            sys.executable,
            "-B",
            str(payload / "source" / RECIPE / "results.py"),
            "--run-root",
            str(payload / "raw"),
            "--output",
            str(payload / "results"),
        ]
        result = subprocess.run(command, capture_output=True, timeout=300)
        (out / "reader.stdout").write_bytes(result.stdout)
        (out / "reader.stderr").write_bytes(result.stderr)
        write(
            out / "reader.exit.json", {"argv": command, "returncode": result.returncode}
        )
        need(
            result.returncode == 0, "Copied public reader failed; exact output retained"
        )
        rendered = reader.read(payload / "results/raw-metrics.json")
        need(rendered == rows, "Relocated raw metrics differ")
        saved, pairs = reader.saved_and_paired(rows, raw)
        need(
            reader.read(payload / "results/raw-saved-scalars.json") == saved,
            "Saved scalar values differ",
        )
        need(
            reader.read(payload / "results/paired-comparisons.json") == pairs,
            "Paired arithmetic differs",
        )
        ids = {q["pair_id"] for q in pairs}
        need(len(ids) == 54, "Expected exactly 54 pairs")
        need(
            len({q["pair_id"] for q in pairs if q["kind"] == "backend"}) == 36
            and len({q["pair_id"] for q in pairs if q["kind"] == "topology"}) == 18,
            "Wrong pair grouping",
        )
        for relative, topology in (("", None), ("figures/ep4", 4), ("figures/ep8", 8)):
            verify_view(reader, rows, payload / "results" / relative, topology)
        import matplotlib

        config = reader.read(payload / "raw/config.json")
        provenance = {
            "status": "LOCAL_DRAFT_PENDING_VISUAL_AND_PUBLICATION_REVIEW",
            "points": 36,
            "measured_requests": 3780,
            "warmup_requests": 756,
            "backend_pairs": 36,
            "topology_pairs": 18,
            "pair_metric_rows": len(pairs),
            "frontiers": 6,
            "release_evidence": descriptor(evidence),
            "review_receipts": [
                {k: b[k] for k in ("bytes", "sha256")} for b in release["bindings"]
            ],
            "source_files": {
                str(part): descriptor(payload / "source" / part)
                for part in SOURCE_FILES
            },
            "render_environment": {
                "python": sys.version,
                "matplotlib": matplotlib.__version__,
            },
            "scope": "Selected raw sealed evidence and reader reproduction; no full archive, installed-byte, preservation or deletion claim",
        }
        write(payload / "PROVENANCE.json", provenance)
        (payload / "REPRODUCE.md").write_text(f"""# Reproduce the six GLM-5.2 frontiers

This selected raw-data bundle contains 36 points, 3,780 measured requests and 756 warmups. Publication, visual inspection and preservation status are tracked separately; PROVENANCE.json records this local preparation stage.

From this directory, use Python 3.11+ with Matplotlib and a new output directory:

```bash
python3 -B source/{RECIPE}/results.py --run-root raw --output ../regenerated-six-curves
```

All seven measured reader/recipe/client files and two unchanged Python package initializers are included. The initializers keep the bundled infx package authoritative when another infx distribution is installed; the seven measured files and import-origin checks are unchanged. The command rehashes every case member, checks the sealed producer environment and command joins across checkout relocation, and regenerates full JSON/CSV scalar tables, all 54 paired comparisons, point coordinates, six frontiers and PNG/SVG. Remote paths in raw receipts are preserved as evidence; no remote filesystem is needed. Plot byte identity can depend on Python/Matplotlib/fonts; saved numeric coordinates, scalar values, pair arithmetic and frontier membership are the reproducibility targets.

## Environment and methods

- Image: `{config["image"]}`.
- SGLang: `{config["sglang_commit"]}`; FlashInfer: `{config["flashinfer_commit"]}`.
- Checkpoint revision: `{config["model_revision"]}`. The exact measured settings, package freeze, launch commands and logs are retained per case.
- One B300 node; each group uses TP=EP=DP attention 4 or 8. MegaMoE W4A4 is green #009E73; MegaMoE W4A16 is orange #E69F00; TRTLLM NVFP4 W4A4 is blue #0072B2. The combined view uses TP4 solid/circle and TP8 dashed/triangle. Both standalone EP4/EP8 views use solid/circle.
- C32 calibrates first, followed by C1/C2/C4/C8/C16 for each group. Each case uses 2C warmups and 10C measured requests, nominal input/output 1,024/8,192, range ratio 0.8 and seed 0. Exact requested/completed arrays remain in the raw case files.
- EAGLE steps 3 / top-k 1 / draft tokens 4; draft TRTLLM/none BF16 MoE path; FP8 E4M3 KV, static memory 0.8, global prefill chunk 32,768, prefill graphs disabled, stream interval 30.
- Measured MTP AL = sum(final completion_tokens) / sum(spec_verify_ct), including native bonus scope; acceptance rate = sum(correct drafts) / sum(proposed drafts). Every measured request must have valid counters and exact ordered output-length joins; warmups are excluded. No lifetime or log-window estimate is used.
- Runtime is the September 30 cae69be5 image with Torch 2.13, distinct from the September 29 baseline. Successful pip commands, the failed namespace postcheck, and separate validation-only continuation remain preserved in prerequisite evidence; pip check reported 14 dependency conflicts. This is not environment equality with the old run.
- x = 1,000 / saved median TPOT milliseconds; y = output tokens / the client's complete measured perf_counter interval / GPU count. This is not separately timed decode. Unix phase endpoints use a separate clock.
- Current backend defaults are retained. W4A16 selection can affect eligible dense NVFP4 linears as well as MegaMoE experts. Draft BF16 names its MoE path, not every tensor.
- Saved ITL is chunk spacing at stream interval 30. Saved percentiles are retained, not independently reconstructed from unsaved per-request latency samples. Sequential backend/topology/cache history does not establish causality, significance, numerical equivalence or response-content equivalence.
- This selected bundle is not the full source/cache/wheel archive, a whole-container snapshot or proof of installed RECORD byte equality. Preservation, checkpoint retention and owned-node cleanup have independent receipts.

[Complete result report](results/RESULTS.md) · [Saved scalar JSON](results/raw-saved-scalars.json) · [All paired metrics](results/paired-comparisons.csv) · [PNG](results/pareto.png) · [SVG](results/pareto.svg) · [EP4 PNG](results/figures/ep4/pareto.png) · [EP4 SVG](results/figures/ep4/pareto.svg) · [EP8 PNG](results/figures/ep8/pareto.png) · [EP8 SVG](results/figures/ep8/pareto.svg)
""")
        files = {
            str(f.relative_to(payload)): descriptor(f)
            for f in sorted(payload.rglob("*"))
            if f.is_file()
        }
        write(
            payload / "FILES.json",
            {
                "files": files,
                "file_count": len(files),
                "total_bytes": sum(v["bytes"] for v in files.values()),
                "self_excluded": "FILES.json",
            },
        )
        write(
            out / "PREPARED.json",
            {
                "status": provenance["status"],
                "payload_manifest": descriptor(payload / "FILES.json"),
                "visual_inspection_required": [
                    "results/pareto.png",
                    "results/pareto.svg",
                    "results/figures/ep4/pareto.png",
                    "results/figures/ep4/pareto.svg",
                    "results/figures/ep8/pareto.png",
                    "results/figures/ep8/pareto.svg",
                ],
                "no_remote_or_publication_action": True,
            },
        )
        print(
            json.dumps(
                {
                    "status": provenance["status"],
                    "output": str(out),
                    "files": len(files),
                }
            )
        )
    except BaseException as error:
        write(
            out / "FAILED.json", {"error": repr(error), "partial_bytes_preserved": True}
        )
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for field in ("repo-root", "run-root", "release-evidence", "output"):
        parser.add_argument("--" + field, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(
            json.dumps(
                {
                    "status": "PLAN_ONLY",
                    "requires": "36 independently accepted actual cases with complete measured-MTP coverage and runner/outer terminals; root release file; exclusive project output",
                    "outputs": "exact selected raw bytes, copied source, three-view full-reader tables/plots, provenance and FILES manifest",
                    "remote_actions": False,
                }
            )
        )
        return
    need(
        all(
            getattr(args, name) is not None
            for name in ("repo_root", "run_root", "release_evidence", "output")
        ),
        "Explicit inputs, release evidence and exclusive output required",
    )
    package(args)


if __name__ == "__main__":
    main()
