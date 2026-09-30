#!/usr/bin/env python3
"""Qualify report prose in a separate, verified GLM36 publication copy."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import stat

if not __debug__:
    raise RuntimeError("Optimized Python is prohibited")

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
DOCS = {"results/RESULTS.md", "REPRODUCE.md"}
STATUS = "LOCAL_DRAFT_PENDING_VISUAL_AND_PUBLICATION_REVIEW"
NEW_STATUS = "QUALIFIED_PUBLICATION_COPY_PENDING_INDEPENDENT_REVIEW"
BUNDLE = (
    "postprocess.py",
    "parent_package.py",
    "SOURCE_LOCK.json",
    "PROPOSED_REPORT_CORRECTIONS.json",
    "CONTRACT.json",
    "README.md",
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    def unique(pairs):
        out = {}
        for k, v in pairs:
            need(k not in out, "Duplicate JSON key")
            out[k] = v
        return out

    return json.loads(
        path.read_bytes(),
        object_pairs_hook=unique,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
    )


def load_parent():
    contract = read(HERE / "CONTRACT.json")
    for name, expected in contract["dependencies"].items():
        need(name in BUNDLE and Path(name).name == name, "Unexpected dependency")
        data = (HERE / name).read_bytes()
        need(
            {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            == expected,
            "Frozen dependency changed: " + name,
        )
    need(
        set(contract["dependencies"])
        == {
            "parent_package.py",
            "SOURCE_LOCK.json",
            "PROPOSED_REPORT_CORRECTIONS.json",
        },
        "Dependency closure differs",
    )
    spec = importlib.util.spec_from_file_location(
        "qualified_parent_package", HERE / "parent_package.py"
    )
    parent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parent)
    return parent


def member(name):
    need(type(name) is str and name, "Empty member")
    p = PurePosixPath(name)
    need(
        not p.is_absolute()
        and str(p) == name
        and ".." not in p.parts
        and "." not in p.parts
        and "\\" not in name,
        "Unsafe member",
    )
    return p


def inventory(root, parent):
    files = {}
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            p = Path(directory) / name
            mode = p.lstat().st_mode
            need(not stat.S_ISLNK(mode), "Linked payload member")
            if name in dirs:
                need(stat.S_ISDIR(mode), "Special payload directory")
            else:
                need(
                    stat.S_ISREG(mode) and p.stat().st_nlink == 1,
                    "Nonprivate or special payload file",
                )
                relative = p.relative_to(root).as_posix()
                member(relative)
                files[relative] = parent.descriptor(p)
    return files


def verify_input(prepared, parent):
    payload = parent.canonical(prepared / "payload")
    need(not (prepared / "FAILED.json").exists(), "Failed parent preparation")
    controls = {
        name: parent.descriptor(prepared / name)
        for name in ("PREPARED.json", "release-evidence.exact.json")
    }
    receipt = read(prepared / "PREPARED.json")
    manifest = read(payload / "FILES.json")
    actual = inventory(payload, parent)
    need(manifest.get("self_excluded") == "FILES.json", "Manifest self scope")
    expected = manifest["files"]
    for name in expected:
        member(name)
    need("FILES.json" not in expected, "Self included")
    need(
        {k: v for k, v in actual.items() if k != "FILES.json"} == expected,
        "Original full FILES closure or bytes changed",
    )
    need(
        manifest.get("file_count") == len(expected)
        and manifest.get("total_bytes") == sum(x["bytes"] for x in expected.values()),
        "Manifest totals differ",
    )
    need(
        receipt.get("status") == STATUS
        and receipt.get("payload_manifest") == actual["FILES.json"],
        "Original PREPARED descriptor/status differs",
    )
    required_views = [
        "results/pareto.png",
        "results/pareto.svg",
        "results/figures/ep4/pareto.png",
        "results/figures/ep4/pareto.svg",
        "results/figures/ep8/pareto.png",
        "results/figures/ep8/pareto.svg",
    ]
    need(
        receipt.get("visual_inspection_required") == required_views
        and receipt.get("no_remote_or_publication_action") is True,
        "Original preparation scope differs",
    )
    provenance = read(payload / "PROVENANCE.json")
    for key, value in {
        "status": STATUS,
        "points": 36,
        "measured_requests": 3780,
        "warmup_requests": 756,
        "backend_pairs": 36,
        "topology_pairs": 18,
        "frontiers": 6,
    }.items():
        need(provenance.get(key) == value, "Original provenance differs: " + key)
    lock = read(HERE / "SOURCE_LOCK.json")["files"]
    need(provenance.get("source_files") == lock, "Provenance source closure differs")
    need(
        {
            k.removeprefix("source/"): v
            for k, v in expected.items()
            if k.startswith("source/")
        }
        == lock,
        "Measured sources and package initializers differ",
    )
    reader = parent.load_reader(payload / "source")
    release_path = prepared / "release-evidence.exact.json"
    release = parent.verify_release(release_path, reader)
    need(
        provenance.get("release_evidence") == parent.descriptor(release_path),
        "Release descriptor differs",
    )
    need(
        provenance.get("review_receipts")
        == [{k: b[k] for k in ("bytes", "sha256")} for b in release["bindings"]],
        "Release review bindings differ",
    )
    rows = read(payload / "results/raw-metrics.json")
    canonical_cases = reader.recipe.matrix()
    need(
        [r["case_id"] for r in rows] == sorted(c["case_id"] for c in canonical_cases),
        "Canonical 36 reader rows differ",
    )
    by_id = {c["case_id"]: c for c in canonical_cases}
    need(
        all(r["completed"] == 10 * by_id[r["case_id"]]["concurrency"] for r in rows)
        and sum(r["completed"] for r in rows) == 3780,
        "Measured accounting differs",
    )
    need(read(payload / "raw/matrix.json") == canonical_cases, "Raw matrix differs")
    terminal = read(payload / "raw/worker-exit.json")
    need(
        terminal.get("status") == "completed"
        and not terminal.get("error")
        and terminal.get("completed") == [c["case_id"] for c in canonical_cases],
        "Original inner terminal incomplete",
    )
    need(
        all("raw/" + name in expected for name in parent.ROOT_FILES),
        "Original raw root closure missing",
    )
    for case in canonical_cases:
        prefix = "raw/cases/" + case["case_id"] + "/"
        manifest_name = prefix + "manifest.json"
        need(manifest_name in expected, "Missing canonical case manifest")
        case_manifest = read(payload / manifest_name)
        members = case_manifest["files"]
        need(
            {
                k.removeprefix(prefix): v
                for k, v in expected.items()
                if k.startswith(prefix) and k != manifest_name
            }
            == {k: {f: v[f] for f in ("bytes", "sha256")} for k, v in members.items()},
            "Original case and payload manifests disagree",
        )
    pairs = read(payload / "results/paired-comparisons.json")
    need(
        len({q["pair_id"] for q in pairs}) == 54
        and len({q["pair_id"] for q in pairs if q["kind"] == "backend"}) == 36
        and len({q["pair_id"] for q in pairs if q["kind"] == "topology"}) == 18
        and set(q["kind"] for q in pairs) == {"backend", "topology"},
        "54 pair grouping differs",
    )
    need(provenance.get("pair_metric_rows") == len(pairs), "Pair row count differs")
    for relative, topology in (("", None), ("figures/ep4", 4), ("figures/ep8", 8)):
        parent.verify_view(reader, rows, payload / "results" / relative, topology)
    need(
        all(name in expected for name in DOCS | set(required_views)),
        "Missing report or view",
    )
    need(
        not any(name.startswith("publication-qualification/") for name in expected),
        "Already qualified input",
    )
    need(
        all(
            parent.descriptor(prepared / name) == info
            for name, info in controls.items()
        ),
        "Original control changed during verification",
    )
    return expected, provenance, actual["FILES.json"], controls


def transformed(text, name, proposal):
    need(name in DOCS, "Only report prose may change")
    for change in proposal["changes"]:
        need(change["target"] in DOCS, "Proposal target outside reports")
        if change["target"] != name:
            continue
        operation = change["operation"]
        if operation == "replace_exact_once":
            need(text.count(change["old"]) == 1, "Report text anchor differs")
            text = text.replace(change["old"], change["new"], 1)
        elif operation in (
            "append_paragraph_once",
            "append_qualified_methods_paragraphs_once",
        ):
            need(change["text"] not in text, "Qualification already applied")
            text = text.rstrip("\n") + "\n\n" + change["text"] + "\n"
        else:
            raise ValueError("Unknown report operation")
    return text


def process(prepared, output):
    parent = load_parent()
    prepared, output = parent.canonical(prepared), parent.canonical(output)
    need(
        prepared.is_relative_to(PROJECT / "artifacts")
        and output.is_relative_to(PROJECT / "artifacts"),
        "Owned artifact paths required",
    )
    need(
        not output.is_relative_to(prepared) and not prepared.is_relative_to(output),
        "Input/output overlap",
    )
    original, provenance, manifest_desc, controls = verify_input(prepared, parent)
    proposal = read(HERE / "PROPOSED_REPORT_CORRECTIONS.json")
    need(proposal.get("status") == "PROPOSED_TEXT_ONLY_NOT_APPLIED", "Wrong proposal")
    payload = prepared / "payload"
    texts = {
        name: transformed((payload / name).read_bytes().decode("utf-8"), name, proposal)
        for name in DOCS
    }
    output.mkdir(parents=True, exist_ok=False)
    try:
        dest = output / "payload"
        for name, expected in original.items():
            if name not in DOCS | {"PROVENANCE.json"}:
                parent.copy_exact(payload / name, dest / name, expected)
        for name in ("PREPARED.json", "release-evidence.exact.json"):
            parent.copy_exact(
                prepared / name, output / "original" / name, controls[name]
            )
        for name in ("FILES.json", "PROVENANCE.json", *sorted(DOCS)):
            parent.copy_exact(
                payload / name,
                output / "original/payload" / name,
                manifest_desc if name == "FILES.json" else original[name],
            )
        changes = {}
        for name, text in texts.items():
            p = dest / name
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("xb") as stream:
                stream.write(text.encode("utf-8"))
            changes[name] = {"before": original[name], "after": parent.descriptor(p)}
        for name in BUNDLE:
            parent.copy_exact(HERE / name, dest / "publication-qualification" / name)
        new_provenance = dict(provenance)
        new_provenance.update(
            {
                "status": NEW_STATUS,
                "original_provenance": original["PROVENANCE.json"],
                "original_payload_manifest": manifest_desc,
                "original_prepared": controls["PREPARED.json"],
                "report_qualification": {
                    "changed_documents": changes,
                    "proposal": parent.descriptor(
                        HERE / "PROPOSED_REPORT_CORRECTIONS.json"
                    ),
                    "postprocessor": parent.descriptor(HERE / "postprocess.py"),
                    "note": "Only generated report prose is clarified. The seven exact measured sources plus two unchanged package initializers reproduce original prose; numeric/figure outputs are unchanged. Original prepared package and receipts remain separate, immutable evidence. No new measurement, acceptance, preservation or publication action.",
                },
            }
        )
        parent.write(dest / "PROVENANCE.json", new_provenance)
        current = inventory(dest, parent)
        untouched = set(original) - DOCS - {"PROVENANCE.json"}
        need(
            all(current.get(name) == original[name] for name in untouched),
            "Nondocument payload changed",
        )
        allowed = set(original) | {
            "publication-qualification/" + name for name in BUNDLE
        }
        need(set(current) == allowed, "Unexpected publication payload addition")
        need(
            inventory(payload, parent) == {**original, "FILES.json": manifest_desc},
            "Original payload drifted during copy",
        )
        need(
            all(
                parent.descriptor(prepared / name) == info
                for name, info in controls.items()
            ),
            "Original control changed during copy",
        )
        parent.write(
            dest / "FILES.json",
            {
                "files": current,
                "file_count": len(current),
                "total_bytes": sum(x["bytes"] for x in current.values()),
                "self_excluded": "FILES.json",
            },
        )
        parent.write(
            output / "PREPARED.json",
            {
                "status": NEW_STATUS,
                "original_payload_manifest": manifest_desc,
                "payload_manifest": parent.descriptor(dest / "FILES.json"),
                "changed_documents": changes,
                "unchanged_payload_files": len(untouched),
                "original_prepared_path": str(prepared),
                "independent_review_required": True,
                "remote_or_publication_actions": False,
            },
        )
        return {
            "status": NEW_STATUS,
            "output": str(output),
            "payload_manifest": parent.descriptor(dest / "FILES.json"),
        }
    except BaseException as error:
        parent.write(
            output / "FAILED.json",
            {"error": repr(error), "partial_bytes_preserved": True},
        )
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prepared", type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args()
    if not args.execute:
        print(
            json.dumps(
                {
                    "status": "PLAN_ONLY",
                    "actual_package_processed": False,
                    "requires": "Original full36 accepted PREPARED package and release evidence; exclusive output; later independent publication-copy review",
                }
            )
        )
        return
    need(
        args.prepared is not None and args.output is not None,
        "Explicit input/output required",
    )
    print(json.dumps(process(args.prepared, args.output)))


if __name__ == "__main__":
    main()
