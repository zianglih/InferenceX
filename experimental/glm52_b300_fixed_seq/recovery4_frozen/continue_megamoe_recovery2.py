"""Fixed recovery2 continuation. No package install or production kernel changes.

Prepare/launch are separate. Reuses two successful recovery1 coordinates by
immutable references, copies sealed caches into a new root, and runs fourteen
remaining coordinates. Failure evidence and successful-run gates stay intact.
"""

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import sys

OLD_ROOT = Path(
    "/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery1"
)
ROOT = Path("/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery2")
OLD_RUN = "c2-w4a16-megamoe-autotune-20260921-recovery1"
RUN = "c2-w4a16-megamoe-autotune-20260921-recovery2"
OLD_RECIPE = "1d8a0aec06f6ea97b4edace3cdb9cb66a6f40a2d"
OLD_SEAL = "c83465f6bf7ca77e549d402bcf81b82c3e24af5381b2756a33e32dd60b03294b"
CACHE_SEAL = "f96afef3889c0e19e7792d99b7493650dd04cd6e0bc7a96285d4f125f8e217d7"
REUSED_LOCK_SHA = "2f3ccb31296bf146e115dcc9af4a6a0a432f5235734eff8d5fcc1d64c06d012b"
BASE_SHA = "a3d0490a474897b25eece24fe6e89d8e3ca5a43b2ed5177ca5e43aab8ec9135a"
REUSED = {
    "8k1k/w4a16-megamoe/tp4_conc256": "3ed73ec5f27d8de42c4aa54bfca5b5b652ebf80d4aad00a4069b349b114885e1",
    "8k1k/w4a16-megamoe/tp4_conc4": "46d40c45aa4cb4da6a255bf253e9c08bd6b793bf9ba680727e30c4383a75e8dc",
}
CASES = (
    [("8k1k", 4, c) for c in (8, 16, 32, 64, 128)]
    + [("8k1k", 8, 4)]
    + [("1k1k", 4, c) for c in (256, 4, 8, 16, 32, 64, 128)]
    + [("1k1k", 8, 4)]
)
RAW = (
    "result.json",
    "benchmark.log",
    "metadata.json",
    "status.json",
    "server_command.sh",
    "benchmark_command.sh",
    "server_info.before.json",
    "server_info.after.json",
    "packages.json",
    "nvidia-smi.txt",
    "server.log",
    "gpu_metrics.csv",
    "gpu_metrics_identity.csv",
    "autotune_cache.before.json",
)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def base():
    p = Path(__file__).with_name("campaign_20260921.py")
    import hashlib

    require(
        hashlib.sha256(p.read_bytes()).hexdigest() == BASE_SHA,
        "Frozen campaign helper changed",
    )
    spec = importlib.util.spec_from_file_location("_recovery2_base", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def idle(b):
    b.idle()
    rows = b.command(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
    ).splitlines()
    require(
        len(rows) == 8
        and all(
            "B300" in r and all(float(x.strip()) == 0 for x in r.split(",")[-2:])
            for r in rows
        ),
        "Eight idle B300 required",
    )
    for rid, root in ((OLD_RUN, OLD_ROOT), (RUN, ROOT)):
        p = root / "results" / f"{rid}-launch.json"
        if p.exists():
            pid = json.loads(p.read_text())["pid"]
            state = subprocess.run(
                ["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True
            ).stdout.strip()
            require(
                not state or state.startswith("Z"), f"Existing worker active: {pid}"
            )


def old_inputs(b):
    require(
        b.sha(OLD_ROOT / "environment/setup-completed.json") == OLD_SEAL,
        "Old setup seal changed",
    )
    inputs = b.verified_inputs(OLD_ROOT, OLD_RUN)
    require(inputs["recipe_commit"] == OLD_RECIPE, "Old recipe changed")
    worker = json.loads((OLD_ROOT / "results" / f"{OLD_RUN}-exit.json").read_text())
    bench = json.loads(
        (OLD_ROOT / "results" / f"{OLD_RUN}-benchmark-exit.json").read_text()
    )
    archive = json.loads(
        (OLD_ROOT / "archives" / f"{OLD_RUN}-archives.json").read_text()
    )
    require(
        worker.get("exit_code")
        == worker.get("benchmark_exit_code")
        == bench.get("exit_code")
        == 1
        and not worker.get("error")
        and not worker.get("child_cleanup_pending"),
        "Old run not safely terminal",
    )
    require(
        worker["archives"] == archive
        and archive["complete_matrix"] is None
        and archive["cache_manifest_sha256"] == CACHE_SEAL,
        "Old failed archive receipt changed",
    )
    lock = Path(__file__).with_name("recovery2_reused_successes.json")
    require(b.sha(lock) == REUSED_LOCK_SHA, "Reused success lock changed")
    locked = json.loads(lock.read_text())["raw_files"]
    for rel, rec in locked.items():
        path = OLD_ROOT / "results" / OLD_RUN / rel
        require(
            path.is_file()
            and not path.is_symlink()
            and path.stat().st_size == rec["bytes"]
            and b.sha(path) == rec["sha256"],
            "Accepted successful raw changed",
        )
    refs = {}
    for rel, digest in REUSED.items():
        case = OLD_ROOT / "results" / OLD_RUN / rel
        require(b.sha(case / "result.json") == digest, "Reused result changed")
        status = json.loads((case / "status.json").read_text())
        expected = 10 * int(rel.rsplit("conc", 1)[1])
        require(
            status["status"] == "completed"
            and status["exit_code"] == 0
            and status["failed"] == 0
            and status["completed"] == status["expected"] == expected,
            "Reused case not successful",
        )
        refs[rel] = {
            "run_id": OLD_RUN,
            "path": str(case),
            "successful_requests": expected,
            "raw_file_sha256": {n: b.sha(case / n) for n in RAW},
        }
    require(
        json.loads(
            (
                OLD_ROOT
                / "results"
                / OLD_RUN
                / "8k1k/w4a16-megamoe/tp4_conc8/status.json"
            ).read_text()
        )["exit_code"]
        == 1,
        "Expected original C8 failure absent",
    )
    return inputs, refs


def copy_source(b, old, new, commit):
    require(not new.exists(), f"Source already exists: {new}")
    new.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--no-hardlinks", "--no-checkout", str(old), str(new)],
        check=True,
    )
    if old.name == "inferencex":
        subprocess.run(
            [
                "git",
                "-C",
                str(new),
                "fetch",
                "--depth=1",
                "https://github.com/zianglih/InferenceX.git",
                commit,
            ],
            check=True,
        )
    subprocess.run(["git", "-C", str(new), "checkout", "--detach", commit], check=True)
    b.clean_head(new, commit)


def copy_cache(b, root=ROOT, old_root=OLD_ROOT):
    manifest = old_root / "archives" / f"{OLD_RUN}-cache-manifest.json"
    require(b.sha(manifest) == CACHE_SEAL, "Cache manifest changed")
    data = json.loads(manifest.read_text())
    old = old_root / "caches/megamoe"
    new = root / "caches/megamoe"
    require(not new.exists(), "Cache destination already exists")
    new.mkdir(parents=True)
    for rel, rec in data.items():
        pp = PurePosixPath(rel)
        require(
            not pp.is_absolute() and ".." not in pp.parts and str(pp) == rel,
            "Unsafe cache path",
        )
        src = old / rel
        dst = new / rel
        require(
            not any(x.is_symlink() for x in src.parents if x.is_relative_to(old)),
            "Linked cache ancestor",
        )
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rec["type"] == "file":
            require(
                src.is_file()
                and not src.is_symlink()
                and src.stat().st_size == rec["bytes"]
                and b.sha(src) == rec["sha256"],
                f"Cache file changed: {rel}",
            )
            shutil.copy2(src, dst)
            require(
                b.sha(dst) == rec["sha256"] and src.stat().st_ino != dst.stat().st_ino,
                "Cache copy differs or is hardlinked",
            )
        else:
            require(
                rec["type"] == "symlink"
                and src.is_symlink()
                and os.readlink(src) == rec["target"],
                "Unknown cache entry/link",
            )
            target = src.resolve(strict=True)
            require(
                str(target) == rec["resolved_target"] and target.is_relative_to(old),
                "Only sealed internal cache links supported",
            )
            require(
                b.inventory(target) == rec["resolved_files"],
                "Cache linked payload changed",
            )
            dst.symlink_to(new / target.relative_to(old))
    # Re-inventory both roots, including every file, to reject added or changed entries.
    old_inv = b.inventory(old)
    new_inv = b.inventory(new)
    require(set(old_inv) == set(new_inv) == set(data), "Cache inventory changed")
    for rel, rec in data.items():
        expected = {
            k: v for k, v in rec.items() if k in ("type", "bytes", "sha256", "target")
        }
        require(old_inv[rel] == expected, "Old cache inventory changed")
        if rec["type"] == "file":
            require(new_inv[rel] == expected, "New cache inventory differs")
    return {
        "source_manifest_sha256": CACHE_SEAL,
        "files": sum(x["type"] == "file" for x in data.values()),
        "symlinks": sum(x["type"] == "symlink" for x in data.values()),
        "bytes": sum(x.get("bytes", 0) for x in data.values()),
        "destination_inventory": new_inv,
    }


def prepare(b, recipe):
    require(
        isinstance(recipe, str) and re.fullmatch("[0-9a-f]{40}", recipe) is not None,
        "Full recipe SHA required",
    )
    require(
        not ROOT.exists() and not ROOT.is_symlink(), "Recovery2 root already exists"
    )
    require(b.command(["hostname"]) == "hu-pdx-126", "Unexpected node")
    idle(b)
    previous, refs = old_inputs(b)
    before = b.probe()
    b.require_stack(before)
    require(
        before == json.loads((OLD_ROOT / "environment/runtime-after.json").read_text()),
        "Runtime drift",
    )
    freeze = (
        b.command([sys.executable, "-m", "pip", "freeze"], env=b.clean_env()) + "\n"
    )
    require(
        freeze == (OLD_ROOT / "environment/packages-after.txt").read_text(),
        "Package drift",
    )
    ROOT.mkdir()
    e = ROOT / "environment"
    e.mkdir()
    for n in ("results", "archives"):
        (ROOT / n).mkdir()
    inputs = previous | {"task_root": str(ROOT), "run_id": RUN, "recipe_commit": recipe}
    b.write_json(e / "inputs.json", inputs)
    b.write_json(e / "reused-successful-cases.json", refs)
    shutil.copyfile(
        OLD_ROOT / "environment/image-receipt.json", e / "image-receipt.json"
    )
    b.write_json(e / "runtime-before.json", before)
    (e / "packages-before.txt").write_text(freeze)
    for name, commit in (
        ("sglang", b.SG),
        ("flashinfer", b.FI),
        ("inferencex", recipe),
    ):
        copy_source(b, OLD_ROOT / "sources" / name, ROOT / "sources" / name, commit)
    oldfi = OLD_ROOT / "sources/flashinfer"
    fi = ROOT / "sources/flashinfer"
    for line in subprocess.check_output(
        ["git", "-C", str(oldfi), "submodule", "status", "--recursive"], text=True
    ).splitlines():
        if line.startswith("-"):
            continue
        require(line.startswith(" "), "Changed prior submodule")
        revision, rel = line.split()[:2]
        require(
            rel in ("3rdparty/cutlass", "3rdparty/cccl", "3rdparty/spdlog"),
            "Unexpected dependency",
        )
        dest = fi / rel
        if dest.exists():
            dest.rmdir()
        copy_source(b, oldfi / rel, dest, revision)
    recipe_root = ROOT / "sources/inferencex"
    require(
        b.sha(recipe_root / b.RELATIVE / Path(__file__).name) == b.sha(__file__),
        "Published continuation differs",
    )
    b.clean_head(fi, b.FI)
    b.write_json(e / "cache-copy.json", copy_cache(b))
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
    sources = e / "sources"
    sources.mkdir()
    for name, commit in (
        ("sglang", b.SG),
        ("flashinfer", b.FI),
        ("inferencex", recipe),
    ):
        repo = ROOT / "sources" / name
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
            import hashlib

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
    helpers = e / "helpers"
    helpers.mkdir()
    for name in (
        "campaign_20260921.py",
        "run_megamoe_20260921.sh",
        "continue_megamoe_recovery2.py",
        "run_megamoe_recovery2.sh",
        "recovery2_reused_successes.json",
    ):
        shutil.copyfile(recipe_root / b.RELATIVE / name, helpers / name)
    shutil.copyfile(__file__, e / "preparation-helper.py")
    b.write_json(
        e / "remaining-matrix.json",
        {
            "cases": CASES,
            "case_count": 14,
            "successful_requests_required": 7640,
            "reused_cases": refs,
            "combined_case_count": 16,
            "combined_successful_requests_required": 10240,
        },
    )
    idle(b)
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


def remaining_matrix(b, run, recipe, run_id):
    require(run_id == RUN, "Wrong continuation ID")
    expected = {f"{s}/w4a16-megamoe/tp{tp}_conc{c}": (s, tp, c) for s, tp, c in CASES}
    require(
        {str(p.parent.relative_to(run)) for p in run.glob("*/*/tp*/status.json")}
        == set(expected),
        "Incomplete/extra continuation coordinates",
    )
    for rel, (s, tp, c) in expected.items():
        case = run / rel
        require(
            all((case / n).is_file() and not (case / n).is_symlink() for n in RAW),
            "Missing raw files",
        )
        st = json.loads((case / "status.json").read_text())
        meta = json.loads((case / "metadata.json").read_text())
        r = json.loads((case / "result.json").read_text())
        require(
            st["status"] == "completed"
            and st["exit_code"] == 0
            and st["failed"] == 0
            and st["expected"] == st["completed"] == r["completed"] == 10 * c,
            "Unsuccessful continuation case",
        )
        fields = {
            "run_id": RUN,
            "scenario": s,
            "backend": "w4a16_megamoe",
            "tp": tp,
            "dp": tp,
            "ep": tp,
            "concurrency": c,
            "mem_fraction_static": 0.8,
            "sglang_commit": b.SG,
            "flashinfer_commit": b.FI,
            "inferencex_commit": recipe,
            "image": b.IMAGE,
            "model_revision": b.MODEL_REVISION,
            "status": "completed",
            "num_prompts": 10 * c,
            "server_max_running_requests": max(c, tp),
            "prefill_cuda_graph_policy": "disabled",
        }
        for key, value in fields.items():
            require(meta.get(key) == value, f"Continuation metadata drift: {key}")
        require(r.get("max_concurrency") == c, "Measured concurrency drift")
        require(
            all(
                isinstance(r.get(k), (int, float)) and math.isfinite(r[k]) and r[k] > 0
                for k in ("duration", "output_throughput")
            ),
            "Invalid throughput or duration",
        )
    refs = json.loads((ROOT / "environment/reused-successful-cases.json").read_text())
    lock = Path(__file__).with_name("recovery2_reused_successes.json")
    require(b.sha(lock) == REUSED_LOCK_SHA, "Reused success lock changed")
    locked = json.loads(lock.read_text())["raw_files"]
    require(set(refs) == set(REUSED), "Missing/extra reused coordinates")
    for rel, ref in refs.items():
        require(
            ref["run_id"] == OLD_RUN
            and ref["path"] == str(OLD_ROOT / "results" / OLD_RUN / rel)
            and ref["successful_requests"] == 10 * int(rel.rsplit("conc", 1)[1]),
            "Reused provenance changed",
        )
        require(
            set(ref["raw_file_sha256"]) == set(RAW)
            and all(
                ref["raw_file_sha256"][n] == locked[f"{rel}/{n}"]["sha256"] for n in RAW
            ),
            "Reused accepted raw binding changed",
        )
        for name, digest in ref["raw_file_sha256"].items():
            require(
                b.sha(Path(ref["path"]) / name) == digest,
                "Reused successful bytes changed",
            )
    return {
        "cases": 14,
        "successful_requests": 7640,
        "combined_cases": 16,
        "combined_successful_requests": 10240,
        "reused_successful_cases": refs,
        "final_independent_audit_pending": True,
    }


def worker(b):
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
                    / "run_megamoe_recovery2.sh"
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
        b.full_matrix = lambda run, recipe, run_id: remaining_matrix(
            b, run, recipe, run_id
        )
        result["archives"] = b.archive_run(ROOT, inputs, rc)
        result["exit_code"] = 0 if rc == 0 else 1
    except BaseException as error:
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


def launch(b):
    inputs = b.verified_inputs(ROOT, RUN)
    idle(b)
    results = ROOT / "results"
    require(
        not (results / RUN).exists() and not list(results.glob(f"{RUN}-*")),
        "Already launched or partial launch exists",
    )
    script = ROOT / "sources/inferencex" / b.RELATIVE / Path(__file__).name
    with (results / f"{RUN}-launch.log").open("xb") as log:
        p = subprocess.Popen(
            [sys.executable, "-B", str(script), "worker"],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=b.clean_env(),
        )
    receipt = {
        "started_at": b.now(),
        "pid": p.pid,
        "argv": p.args,
        "helper_sha256": b.sha(script),
        "inputs": inputs,
    }
    b.atomic_json(results / f"{RUN}-launch.json", receipt)
    print(json.dumps(receipt, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("action", choices=("prepare", "launch", "worker", "status"))
    ap.add_argument("--recipe-commit")
    args = ap.parse_args()
    b = base()
    require(
        ROOT.is_absolute() and not ROOT.is_symlink() and not OLD_ROOT.is_symlink(),
        "Linked root",
    )
    if args.action == "prepare":
        prepare(b, args.recipe_commit)
    elif args.action == "launch":
        launch(b)
    elif args.action == "worker":
        return worker(b)
    else:
        b.status(ROOT, RUN)
    return 0


if __name__ == "__main__":
    sys.exit(main())
