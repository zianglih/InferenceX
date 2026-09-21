"""Fresh recovery3 preparation and fourteen-point continuation; no pip operations.

Reuses the frozen recovery2 cache/reference/matrix/archive implementation privately.
Only the new root is written. Five generated FlashInfer data links and build metadata
are created and sealed before source import; all three dependencies are registered.
"""

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import signal
import subprocess
import sys
from pathlib import Path

ROOT = Path("/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery3")
RUN = "c2-w4a16-megamoe-autotune-20260921-recovery3"
FAILED_ROOT = Path(
    "/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery2"
)
FAILED_RUN = "c2-w4a16-megamoe-autotune-20260921-recovery2"
PREVIOUS_HELPER_SHA = "54e47c31200909a657f970da860421cae015f9a1b3f56942af6a7beefd1d875b"
DEPENDENCIES = {
    "3rdparty/cccl": "16bd510c9b712e82b0ab6cbb630d8e29ba1f7116",
    "3rdparty/cutlass": "b46b16d003484063bca4ed365e44095c4c6ed633",
    "3rdparty/spdlog": "c3aed4b68373955e1cc94307683d44dca1515d2b",
}
DATA_TARGETS = {
    "cutlass": "3rdparty/cutlass",
    "spdlog": "3rdparty/spdlog",
    "cccl": "3rdparty/cccl",
    "csrc": "csrc",
    "include": "include",
}
SENTINELS = {
    "cutlass": ("include/cutlass/cutlass.h",),
    "spdlog": ("include/spdlog/spdlog.h",),
    "cccl": ("cub/cub/cub.cuh",),
    "include": ("flashinfer/attention/decode.cuh",),
    "csrc": (
        "nv_internal/tensorrt_llm/thop/fp4Quantize.cpp",
        "nv_internal/tensorrt_llm/thop/fp4Op.cpp",
        "nv_internal/cpp/kernels/quantization.cu",
        "nv_internal/cpp/common/envUtils.cpp",
        "nv_internal/cpp/common/logger.cpp",
        "nv_internal/cpp/common/stringUtils.cpp",
        "nv_internal/cpp/common/tllmException.cpp",
    ),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def previous():
    path = Path(__file__).with_name("continue_megamoe_recovery2.py")
    require(
        hashlib.sha256(path.read_bytes()).hexdigest() == PREVIOUS_HELPER_SHA,
        "Frozen recovery2 helper changed",
    )
    spec = importlib.util.spec_from_file_location("_recovery3_previous", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.ROOT, mod.RUN = ROOT, RUN
    # The reused launcher invokes this entrypoint; its original file remains unchanged.
    mod.__file__ = __file__
    return mod


def clone_dependencies(b, r, oldfi, fi):
    """Register exact gitlinks, then clone independent objects without network access."""
    for rel, revision in DEPENDENCIES.items():
        record = b.command(["git", "-C", str(fi), "ls-tree", "HEAD", rel]).split()
        require(
            record[:3] == ["160000", "commit", revision], "Dependency gitlink changed"
        )
        b.clean_head(oldfi / rel, revision)
    subprocess.run(
        ["git", "-C", str(fi), "submodule", "init", "--", *DEPENDENCIES], check=True
    )
    for rel, revision in DEPENDENCIES.items():
        dest = fi / rel
        if dest.exists():
            require(
                dest.is_dir() and not dest.is_symlink(), "Unsafe dependency destination"
            )
            dest.rmdir()
        r.copy_source(b, oldfi / rel, dest, revision)
    subprocess.run(
        ["git", "-C", str(fi), "submodule", "absorbgitdirs", "--", *DEPENDENCIES],
        check=True,
    )
    return check_dependencies(b, fi)


def check_dependencies(b, fi):
    records = {}
    text = subprocess.check_output(
        ["git", "-C", str(fi), "submodule", "status", "--", *DEPENDENCIES], text=True
    )
    for line in text.splitlines():
        require(line.startswith(" "), "Dependency not initialized at its pinned commit")
        revision, rel = line.split()[:2]
        require(
            DEPENDENCIES.get(rel) == revision and rel not in records,
            "Unexpected dependency",
        )
        b.clean_head(fi / rel, revision)
        records[rel] = revision
    require(records == DEPENDENCIES, "Dependency set incomplete")
    return records


def resources(b, fi, *, create=False):
    """Reproduce only the ignored resource layout, without importing build_backend."""
    b.clean_head(fi, b.FI)
    check_dependencies(b, fi)
    data = fi / "flashinfer/data"
    meta = fi / "flashinfer/_build_meta.py"
    version = (fi / "version.txt").read_text().strip()
    require(version == "0.7.0", "Unexpected source version")
    meta_bytes = (
        '"""Build metadata for flashinfer package."""\n'
        f'__version__ = "{version}"\n'
        f'__git_commit__ = "{b.FI}"\n'
    ).encode()
    if create:
        require(
            not data.exists()
            and not data.is_symlink()
            and not meta.exists()
            and not meta.is_symlink(),
            "Generated resource destination already exists",
        )
        # Validate every target before creating any link.
        for rel in DATA_TARGETS.values():
            target = fi / rel
            require(
                target.is_dir() and target.resolve() == target,
                "Resource target is missing or linked",
            )
        data.mkdir()
        for name, rel in DATA_TARGETS.items():
            (data / name).symlink_to(fi / rel, target_is_directory=True)
        with meta.open("xb") as stream:
            stream.write(meta_bytes)
    require(
        data.is_dir()
        and not data.is_symlink()
        and {x.name for x in data.iterdir()} == set(DATA_TARGETS),
        "Invalid generated data directory",
    )
    require(
        meta.is_file() and not meta.is_symlink() and meta.read_bytes() == meta_bytes,
        "Build metadata differs",
    )
    links = {}
    for name, rel in DATA_TARGETS.items():
        link, target = data / name, fi / rel
        require(
            link.is_symlink()
            and link.readlink() == target
            and link.resolve(strict=True) == target
            and target.is_dir(),
            "Generated resource link differs",
        )
        payload = {}
        for sentinel in SENTINELS[name]:
            canonical = target / sentinel
            require(
                canonical.is_file()
                and not canonical.is_symlink()
                and canonical.resolve() == canonical,
                "Missing/linked resource sentinel",
            )
            repository, git_path = (
                (target, sentinel) if rel in DEPENDENCIES else (fi, f"{rel}/{sentinel}")
            )
            expected = subprocess.check_output(
                ["git", "-C", str(repository), "show", f"HEAD:{git_path}"]
            )
            require(
                canonical.read_bytes() == expected
                and (link / sentinel).read_bytes() == expected,
                "Resource sentinel differs from pinned source",
            )
            payload[sentinel] = {
                "bytes": len(expected),
                "sha256": hashlib.sha256(expected).hexdigest(),
            }
        links[name] = {"target": str(target), "sentinels": payload}
    return {
        "schema_version": 1,
        "flashinfer_commit": b.FI,
        "source_root": str(fi),
        "version": version,
        "links": links,
        "build_meta": {
            "path": str(meta),
            "sha256": b.sha(meta),
            "bytes": len(meta_bytes),
        },
    }


def base(r):
    b = r.base()
    original = b.verified_inputs

    def verified(root, run_id):
        inputs = original(root, run_id)
        if root == ROOT:
            require(
                resources(b, ROOT / "sources/flashinfer")
                == json.loads(
                    (ROOT / "environment/flashinfer-resource-layout.json").read_text()
                ),
                "Prepared resource layout changed",
            )
        return inputs

    b.verified_inputs = verified
    return b


def idle(b, r):
    r.idle(b)
    exit_path = FAILED_ROOT / "results" / f"{FAILED_RUN}-exit.json"
    failed = json.loads(exit_path.read_text())
    require(
        failed.get("exit_code") == failed.get("benchmark_exit_code") == 1
        and not failed.get("error")
        and not failed.get("child_cleanup_pending")
        and failed.get("archives", {}).get("complete_matrix") is None,
        "Recovery2 is not safely terminal",
    )
    benchmark = json.loads(
        (FAILED_ROOT / "results" / f"{FAILED_RUN}-benchmark-exit.json").read_text()
    )
    archive = json.loads(
        (FAILED_ROOT / "archives" / f"{FAILED_RUN}-archives.json").read_text()
    )
    require(
        benchmark.get("exit_code") == 1
        and failed.get("archives") == archive
        and archive.get("benchmark_exit_code") == 1
        and all(isinstance(archive.get(k), dict) for k in ("raw", "caches")),
        "Recovery2 archive/exit receipts disagree",
    )
    launch = json.loads(
        (FAILED_ROOT / "results" / f"{FAILED_RUN}-launch.json").read_text()
    )
    state = subprocess.run(
        ["ps", "-o", "stat=", "-p", str(launch["pid"])],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    require(not state or state.startswith("Z"), "Recovery2 worker still active")


def archive_sources(b, root, recipe, evidence):
    sources = evidence / "sources"
    sources.mkdir()
    for name, commit in (
        ("sglang", b.SG),
        ("flashinfer", b.FI),
        ("inferencex", recipe),
    ):
        repo = root / "sources" / name
        b.clean_head(repo, commit)
        with (sources / f"{name}.tar.gz").open("xb") as out:
            subprocess.run(
                ["git", "-C", str(repo), "archive", "--format=tar.gz", "HEAD"],
                stdout=out,
                check=True,
            )
        sub = b.command(["git", "-C", str(repo), "submodule", "status", "--recursive"])
        (sources / f"{name}-submodules.txt").write_text(sub + "\n")
        for line in sub.splitlines():
            if line.startswith("-"):
                continue
            rev, rel = line.split()[:2]
            b.clean_head(repo / rel, rev)
            with (
                sources
                / f"{name}-submodule-{hashlib.sha256(rel.encode()).hexdigest()[:16]}.tar.gz"
            ).open("xb") as out:
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(repo / rel),
                        "archive",
                        "--format=tar.gz",
                        "HEAD",
                    ],
                    stdout=out,
                    check=True,
                )
    expected = {"sglang.tar.gz", "flashinfer.tar.gz", "inferencex.tar.gz"} | {
        f"flashinfer-submodule-{hashlib.sha256(rel.encode()).hexdigest()[:16]}.tar.gz"
        for rel in DEPENDENCIES
    }
    require(
        {path.name for path in sources.glob("*.tar.gz")} == expected,
        "Expected three main and three dependency archives",
    )


def prepare(b, r, recipe):
    require(
        isinstance(recipe, str) and re.fullmatch("[0-9a-f]{40}", recipe) is not None,
        "Full recipe SHA required",
    )
    require(
        not ROOT.exists() and not ROOT.is_symlink(), "Recovery3 root already exists"
    )
    require(b.command(["hostname"]) == "hu-pdx-126", "Unexpected node")
    idle(b, r)
    previous, refs = r.old_inputs(b)
    before = b.probe()
    b.require_stack(before)
    require(
        before
        == json.loads((r.OLD_ROOT / "environment/runtime-after.json").read_text()),
        "Runtime drift",
    )
    freeze = (
        b.command([sys.executable, "-m", "pip", "freeze"], env=b.clean_env()) + "\n"
    )
    require(
        freeze == (r.OLD_ROOT / "environment/packages-after.txt").read_text(),
        "Package drift",
    )
    ROOT.mkdir()
    e = ROOT / "environment"
    e.mkdir()
    for n in ("results", "archives"):
        (ROOT / n).mkdir()
    inputs = previous | {"task_root": str(ROOT), "run_id": RUN, "recipe_commit": recipe}
    b.write_json(e / "inputs.json", inputs)
    previous_receipts = {}
    for relative in (
        f"results/{FAILED_RUN}-exit.json",
        f"results/{FAILED_RUN}-benchmark-exit.json",
        f"archives/{FAILED_RUN}-archives.json",
    ):
        path = FAILED_ROOT / relative
        previous_receipts[relative] = {
            "sha256": b.sha(path),
            "content": json.loads(path.read_text()),
        }
    b.write_json(
        e / "previous-failed-attempt.json",
        {"root": str(FAILED_ROOT), "run_id": FAILED_RUN, "receipts": previous_receipts},
    )
    b.write_json(e / "reused-successful-cases.json", refs)
    shutil.copyfile(
        r.OLD_ROOT / "environment/image-receipt.json", e / "image-receipt.json"
    )
    b.write_json(e / "runtime-before.json", before)
    (e / "packages-before.txt").write_text(freeze)
    for name, commit in (
        ("sglang", b.SG),
        ("flashinfer", b.FI),
        ("inferencex", recipe),
    ):
        r.copy_source(b, r.OLD_ROOT / "sources" / name, ROOT / "sources" / name, commit)
    oldfi = r.OLD_ROOT / "sources/flashinfer"
    fi = ROOT / "sources/flashinfer"
    b.write_json(
        e / "flashinfer-dependencies.json", clone_dependencies(b, r, oldfi, fi)
    )
    b.write_json(e / "flashinfer-resource-layout.json", resources(b, fi, create=True))
    shutil.copyfile(fi / "flashinfer/_build_meta.py", e / "flashinfer-build-meta.py")
    recipe_root = ROOT / "sources/inferencex"
    require(
        b.sha(recipe_root / b.RELATIVE / Path(__file__).name) == b.sha(__file__),
        "Published continuation differs",
    )
    b.clean_head(fi, b.FI)
    b.write_json(e / "cache-copy.json", r.copy_cache(b, ROOT, r.OLD_ROOT))
    env = b.clean_env() | {
        "PYTHONPATH": f"{ROOT / 'sources/sglang/python'}:{fi}:{recipe_root}",
        "SGLANG_SOURCE_ROOT": str(ROOT / "sources/sglang"),
        "SGLANG_COMMIT": b.SG,
        "FLASHINFER_SOURCE_ROOT": str(fi),
        "FLASHINFER_COMMIT": b.FI,
    }
    with (e / "source-imports.log").open("x") as log:
        subprocess.run(
            [
                sys.executable,
                str(recipe_root / b.RELATIVE / "artifacts.py"),
                "verify-source",
            ],
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            check=True,
        )
    code = "import flashinfer._build_meta as m; import flashinfer.jit.env as j; import json; print(json.dumps({'build_meta_path':m.__file__, 'version':m.__version__, 'commit':m.__git_commit__, 'csrc':str(j.FLASHINFER_CSRC_DIR)}))"
    imported = json.loads(b.command([sys.executable, "-c", code], env=env))
    require(
        imported
        == {
            "build_meta_path": str(fi / "flashinfer/_build_meta.py"),
            "version": "0.7.0",
            "commit": b.FI,
            "csrc": str(fi / "flashinfer/data/csrc"),
        },
        "Imported resource metadata resolved outside fresh source",
    )
    b.write_json(e / "flashinfer-resource-import.json", imported)
    b.write_json(e / "resolved-config.json", b.resolved_config(recipe_root))
    after = b.probe()
    after_freeze = (
        b.command([sys.executable, "-m", "pip", "freeze"], env=b.clean_env()) + "\n"
    )
    require(
        after == before and after_freeze == freeze,
        "Preparation changed runtime/packages",
    )
    b.write_json(e / "runtime-after.json", after)
    (e / "packages-after.txt").write_text(after_freeze)
    archive_sources(b, ROOT, recipe, e)
    helpers = e / "helpers"
    helpers.mkdir()
    for name in (
        "campaign_20260921.py",
        "run_megamoe_20260921.sh",
        "continue_megamoe_recovery2.py",
        "run_megamoe_recovery2.sh",
        "continue_megamoe_recovery3.py",
        "run_megamoe_recovery3.sh",
        "recovery2_reused_successes.json",
    ):
        shutil.copyfile(recipe_root / b.RELATIVE / name, helpers / name)
    shutil.copyfile(__file__, e / "preparation-helper.py")
    b.write_json(
        e / "remaining-matrix.json",
        {
            "cases": r.CASES,
            "case_count": 14,
            "successful_requests_required": 7640,
            "reused_cases": refs,
            "combined_case_count": 16,
            "combined_successful_requests_required": 10240,
        },
    )
    idle(b, r)
    b.write_json(
        e / "setup-completed.json",
        {
            "completed_at": b.now(),
            "inputs": inputs,
            "files": b.inventory(e),
            "runtime_preserved": True,
            "image_evidence_source": "unchanged same-node provisioning receipt",
            "source_binding_note": "PYTHONPATH selects new exact clones; installed editable FI metadata remains unchanged",
            "launch_performed": False,
        },
    )
    print(
        json.dumps(
            {
                "prepared": True,
                "root": str(ROOT),
                "run_id": RUN,
                "launch_performed": False,
            }
        )
    )


def worker(b, r):
    result = {"started_at": b.now(), "exit_code": 1}
    child = None

    def interrupted(signum, _frame):
        if child is not None and child.poll() is None:
            child.send_signal(signum)
        raise InterruptedError(f"Worker received signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        inputs = b.verified_inputs(ROOT, RUN)
        require(
            b.probe()
            == json.loads((ROOT / "environment/runtime-after.json").read_text()),
            "Runtime drift",
        )
        require(
            b.command([sys.executable, "-m", "pip", "freeze"], env=b.clean_env())
            == (ROOT / "environment/packages-after.txt").read_text().strip(),
            "Package drift",
        )
        b.idle()
        env = b.clean_env() | {
            "CAMPAIGN_TASK_ROOT": str(ROOT),
            "CAMPAIGN_MODEL_PATH": inputs["model_path"],
            "CAMPAIGN_RECIPE_ROOT": str(ROOT / "sources/inferencex"),
            "CAMPAIGN_RUN_ID": RUN,
        }
        child = subprocess.Popen(
            [
                "bash",
                str(
                    ROOT
                    / "sources/inferencex"
                    / b.RELATIVE
                    / "run_megamoe_recovery3.sh"
                ),
            ],
            env=env,
        )
        rc = child.wait()
        result["benchmark_exit_code"] = rc
        b.atomic_json(
            ROOT / "results" / f"{RUN}-benchmark-exit.json",
            {"exit_code": rc, "finished_at": b.now()},
        )
        # This private module's archive explicitly seals the 14-case continuation.
        # The existing production full16 helper and success-fetch gates are untouched.
        b.full_matrix = lambda run, recipe, run_id: r.remaining_matrix(
            b, run, recipe, run_id
        )
        result["archives"] = b.archive_run(ROOT, inputs, rc)
        result["exit_code"] = 0 if rc == 0 else 1
    except BaseException as error:  # noqa: BLE001 - seal exit receipt after interruption
        result["error"] = f"{type(error).__name__}: {error}"
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=60)
            except subprocess.TimeoutExpired:
                result["child_cleanup_pending"] = True
    finally:
        result["finished_at"] = b.now()
        b.atomic_json(ROOT / "results" / f"{RUN}-exit.json", result)
    return result["exit_code"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "launch", "worker", "status"))
    parser.add_argument("--recipe-commit")
    args = parser.parse_args()
    r = previous()
    b = base(r)
    require(
        ROOT.is_absolute()
        and not ROOT.is_symlink()
        and not r.OLD_ROOT.is_symlink()
        and not FAILED_ROOT.is_symlink(),
        "Linked root",
    )
    if args.action == "prepare":
        prepare(b, r, args.recipe_commit)
    elif args.action == "launch":
        idle(b, r)
        r.launch(b)
    elif args.action == "worker":
        return worker(b, r)
    else:
        b.status(ROOT, RUN)
    return 0


if __name__ == "__main__":
    sys.exit(main())
