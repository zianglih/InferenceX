#!/usr/bin/env python3
"""Local union of closed base36 and separately validated EP8 C64 raw evidence."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
OLD = "experimental/glm52_six_curves_1k8k_c32"
NEW = "experimental/glm52_ep8_c64_measured_mtp"
ARMS = ("megamoe-w4a4", "megamoe-w4a16", "trtllm-w4a4")
BASE_IDS = {f"{a}-tp{t}-ep{t}-dp{t}-c{c}" for a in ARMS
            for t in (4, 8) for c in (1, 2, 4, 8, 16, 32)}
NEW_IDS = {f"{a}-tp8-ep8-dp8-c64" for a in ARMS}


def need(value, message):
    if not value:
        raise ValueError(message)


def safe(path):
    path = Path(path).absolute()
    need(".." not in path.parts and path.resolve() == path, "Noncanonical/linked path")
    return path


def desc(path):
    path = safe(path)
    need(path.is_file(), "Missing regular file")
    before = path.stat()
    with path.open("rb") as stream:
        value = {"bytes": before.st_size, "sha256": hashlib.file_digest(stream, "sha256").hexdigest()}
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
         (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns), "File changed while hashing")
    return value


def read(path):
    def pairs(items):
        value = {}
        for k, v in items:
            need(k not in value, "Duplicate JSON key")
            value[k] = v
        return value
    def invalid(value):
        raise ValueError("Nonfinite JSON: " + value)
    return json.loads(safe(path).read_bytes(), object_pairs_hook=pairs, parse_constant=invalid)


def write(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def load_reader(source, relative, tag):
    directory = source / relative
    def module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        obj = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(obj)
        return obj
    old = sys.modules.get("run")
    try:
        sys.modules["run"] = module(tag + "_run", directory / "run.py")
        return module(tag + "_results", directory / "results.py")
    finally:
        if old is None:
            sys.modules.pop("run", None)
        else:
            sys.modules["run"] = old


def check_source_lock():
    value = read(HERE / "source-lock.json")
    for rel, expected in value["files"].items():
        need(not Path(rel).is_absolute() and ".." not in Path(rel).parts, "Unsafe source member")
        need(desc(HERE / rel) == expected, "Candidate source changed: " + rel)


def base_bundle(bundle, expected):
    """Bind the immutable public base before consuming its already accepted numbers."""
    bundle = safe(bundle)
    need(desc(bundle / "FILES.json") == expected, "Closed base manifest changed")
    manifest = read(bundle / "FILES.json")
    files = manifest["files"]
    need(manifest["file_count"] == len(files), "Base count differs")
    actual = set()
    for path in bundle.rglob("*"):
        need(not path.is_symlink(), "Linked base member")
        if path.is_file():
            actual.add(path.relative_to(bundle).as_posix())
    need(actual == set(files) | {"FILES.json"}, "Base members differ")
    for name, value in files.items():
        need(not Path(name).is_absolute() and ".." not in Path(name).parts, "Unsafe base member")
        need(desc(bundle / name) == value, "Closed base bytes changed: " + name)
    need(sum(v["bytes"] for v in files.values()) == manifest["total_bytes"], "Base bytes count differs")
    rows = read(bundle / "results/raw-metrics.json")
    validate_rows(rows, BASE_IDS, 3780)
    return rows


def validate_rows(rows, expected, measured):
    need(len(rows) == len(expected) and {r["case_id"] for r in rows} == expected,
         "Missing, duplicate or unexpected matrix point")
    for r in rows:
        tp, c, arm = r["tp"], r["concurrency"], r["arm_id"]
        need(type(tp) is int and type(c) is int and r["ep"] == r["dp"] == tp,
             "Topology differs")
        need(r["case_id"] == f"{arm}-tp{tp}-ep{tp}-dp{tp}-c{c}" and
             type(r["completed"]) is int and r["completed"] == 10*c, "Row identity/count differs")
    need(sum(r["completed"] for r in rows) == measured, "Measured count differs")


def union_rows(base, extension):
    validate_rows(base, BASE_IDS, 3780)
    validate_rows(extension, NEW_IDS, 1920)
    for name in ("sglang_commit", "flashinfer_commit", "image"):
        need(len({r[name] for r in base + extension}) == 1, "Cross-run runtime source differs: " + name)
    # Preserve the original36 rows/order/identities; never construct an EP4 C64 row.
    return base + extension


def same_runtime_config(base, extension):
    allowed = {"campaign_contract", "run_id", "run_root", "tmp_root", "base_environment"}
    need(set(base) == set(extension), "Cross-run config keys differ")
    for key in set(base) - allowed:
        need(base[key] == extension[key], "Cross-run setting differs: " + key)
    a, b = dict(base["base_environment"]), dict(extension["base_environment"])
    a.pop("HOME", None)
    b.pop("HOME", None)
    need(a == b, "Cross-run explicit base environment differs")


def same_runtime_source(base, extension):
    # Only recipe paths/identities change; source checkout and full freeze stay exact.
    need({k: v for k, v in base.items() if k != "recipe"} ==
         {k: v for k, v in extension.items() if k != "recipe"}, "Cross-run source/package freeze differs")


def join_pairs(base_pairs, extension_pairs):
    expected = {(f"{b}-tp8-ep8-dp8-c64", f"{c}-tp8-ep8-dp8-c64") for b, c in (
        ("megamoe-w4a4", "megamoe-w4a16"), ("trtllm-w4a4", "megamoe-w4a4"),
        ("trtllm-w4a4", "megamoe-w4a16"))}
    metrics = {r["metric"] for r in base_pairs}
    need(len({r["pair_id"] for r in base_pairs}) == 54 and len(base_pairs) == 54*len(metrics),
         "Base paired table differs")
    need(len(extension_pairs) == 3*len(metrics), "Extension metric count differs")
    seen = set()
    for row in extension_pairs:
        key = (row["baseline_case"], row["comparison_case"])
        need(key in expected and row["kind"] == "backend" and row["metric"] in metrics,
             "Unexpected C64 pair; no EP4 counterpart exists")
        need(row["pair_id"] == key[1] + "__over__" + key[0], "Pair identity differs")
        need((key, row["metric"]) not in seen, "Duplicate paired metric")
        seen.add((key, row["metric"]))
    return base_pairs + extension_pairs


def assemble(extension_root, output):
    check_source_lock()
    lock = read(HERE / "base-lock.json")
    bindings = {}
    for name, expected in lock["bindings"].items():
        path = PROJECT / name
        need(desc(path) == expected, "Accepted base binding changed: " + name)
        bindings[str(path)] = expected
    bundle = PROJECT / lock["bundle"]
    base = base_bundle(bundle, lock["bindings"][lock["bundle"] + "/FILES.json"])
    table = read(PROJECT / lock["summary"])
    need({r["case_id"]: r for r in table} == {r["case_id"]: r for r in base}, "Accepted base table differs")
    release = read(PROJECT / lock["release"])
    need(release["status"] == "MEASURED_RESULTS_ACCEPTED" and release["measured_requests"] == 3780,
         "Base release not accepted")
    extension_root = safe(extension_root)
    new = load_reader(HERE / "source", NEW, "extension")
    added = new.load(extension_root, False)
    same_runtime_config(read(PROJECT / lock["base_config"]), read(extension_root / "config.json"))
    for row in added:
        same_runtime_source(read(PROJECT / lock["base_source"]),
                            read(extension_root / "cases" / row["case_id"] / "source.before.json"))
    rows = union_rows(base, added)
    scalars, pairs = new.saved_and_paired(added, extension_root)
    pairs = join_pairs(read(bundle / "results/paired-comparisons.json"), pairs)
    scalars = read(bundle / "results/raw-saved-scalars.json") + scalars
    for path in extension_root.rglob("*"):
        need(not path.is_symlink(), "Linked collected evidence")
        if path.is_file():
            bindings[str(path)] = desc(path)
    output = safe(output)
    output.mkdir(parents=True, exist_ok=False)
    new.write_table(output, "raw-metrics", rows)
    new.write_table(output, "raw-saved-scalars", scalars)
    new.write_table(output, "paired-comparisons", pairs)
    # Keep the old subset and its original full36 input/plotting source untouched.
    shutil.copytree(bundle / "results/c2-32", output / "c2-32")
    shutil.copyfile(bundle / "results/raw-metrics.json", output / "base36-raw-metrics.json")
    shutil.copytree(HERE / "source", output / "source")
    shutil.copyfile(HERE / "layout_original.py", output / "layout_original.py")
    shutil.copyfile(HERE / "join39.py", output / "join39.py")
    shutil.copyfile(HERE / "render39.py", output / "render39.py")
    shutil.copyfile(bundle / "publication-layout/render_concurrency_subset.py", output / "render_concurrency_subset.py")
    export = {p.relative_to(output).as_posix(): desc(p) for p in output.rglob("*")
              if p.is_file() and (p.relative_to(output).parts[0] == "source" or p.name in
                                  ("layout_original.py", "join39.py", "render39.py", "raw-metrics.json",
                                   "render_concurrency_subset.py", "base36-raw-metrics.json"))}
    write(output / "plot-source-manifest.json", {"files": export})
    subset = {p.relative_to(output / "c2-32").as_posix(): desc(p)
              for p in (output / "c2-32").rglob("*") if p.is_file()}
    need(all(v == desc(bundle / "results/c2-32" / k) for k, v in subset.items()), "Subset copy changed")
    report = {"status": "STRUCTURAL_39_POINT_JOIN_REQUIRES_INDEPENDENT_ACTUAL_ACCEPTANCE",
              "points": 39, "measured_requests": 5700, "scheduled_warmups": 1140,
              "backend_pairs": 39, "topology_pairs": 18, "pair_metric_rows": len(pairs),
              "new_case_ids": sorted(NEW_IDS), "base_case_ids": sorted(BASE_IDS),
              "extension_root": str(extension_root), "base_manifest": desc(bundle / "FILES.json"),
              "unchanged_c2_32": subset, "bindings": bindings,
              "pending_separate_gates": ["new3 independent actual native/runtime/tactic acceptance",
                  "new3 outer/controller terminal review", "extension preservation", "root publication approval"],
              "limits": ["Base36 and extension3 are separate runs, with separate cache and sequential history.",
                  "No EP4 C64 measurement or topology comparison is present.",
                  "Measured MTP ratios exclude warmups and preserve the native bonus convention.",
                  "Saved ITL is streamed chunk spacing; no timed decode, causality, quality or significance claim.",
                  "Public plot replay uses tables; full raw/native/owner evidence stays local."]}
    write(output / "JOIN.json", report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--extension-root", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    report = assemble(a.extension_root, a.output)
    print(json.dumps({k: report[k] for k in ("status", "points", "measured_requests", "pair_metric_rows")}))


if __name__ == "__main__":
    main()
