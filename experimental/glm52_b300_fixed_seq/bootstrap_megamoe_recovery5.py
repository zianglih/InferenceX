#!/usr/bin/env python3
"""Independent peer-node, real-weight recovery5 preparation. Default plan is local-only.

The bootstrap and campaign roots are exclusive. No old cache is read or copied.
Only the original two successful raw cases and their seals are referenced.
No serving process, dummy model, kernel probe, or benchmark is launched here.
"""

import argparse
import hashlib
import importlib.util
import json
import platform
import re
import shutil
import socket
import sys
from pathlib import Path

ROOT = Path("/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery5")
BOOTSTRAP = Path(
    "/data/home/ziangli/inferencex-glm52-megamoe-bootstrap-20260921-recovery5"
)
RUN = "c2-w4a16-megamoe-autotune-20260921-recovery5"
WRAPPER_SHA = "ae96cbb490c9b57dd74016a19552ae0a8bcff6b08df630613313282b75ccaa38"
FROZEN = Path(__file__).with_name("recovery4_frozen")
PINS = {
    "bootstrap_megamoe_recovery1.py": "ebeb67415bee4613c104b2ea9b933ee4f0a6da0fe52d07790ad2d27aef083822",
    "megamoe_bootstrap_recovery1_wheels.json": "321f151aefd7fe9e6a82b7482f112264a3a3dcc6178d27a9869abc728b3b69ac",
    "campaign_20260921.py": "a3d0490a474897b25eece24fe6e89d8e3ca5a43b2ed5177ca5e43aab8ec9135a",
    "continue_megamoe_recovery2.py": "54e47c31200909a657f970da860421cae015f9a1b3f56942af6a7beefd1d875b",
    "continue_megamoe_recovery3.py": "5a90a63f157a81ce9ebda5aed0806cc692b57efb030a992f07e47c9fe93c2011",
    "recovery2_reused_successes.json": "2f3ccb31296bf146e115dcc9af4a6a0a432f5235734eff8d5fcc1d64c06d012b",
    "checkpoint.json": "1a93b7ff66f80560e3c60ef8e0a67217a71ac682587945da107ddd89fd663d6a",
    "first-case-independent-review.json": "4bef4a96b7a13771740b8487d0d912159a0dad8c119355b6b0878023f505a2df",
    "first-case-parent-acceptance.json": "faefc26ca26c58419f5628dea0a67b391332a64056b0c987dfb8ddcc57d090e0",
    "second-case-independent-review.json": "fd071d7d33155a72f1c359ce3a149b74344402c5c020f83563f6c70844373d9f",
    "reference-runtime.json": "acfec88f87392a2bac6dd4286a9df580f931241567f9587cd07fcb79b1fc299a",
    "reference-freeze.txt": "ee786fdd588c17fbcbb5081eb8041172b3f9fa9cb04b6a241ea890f6ce061040",
}
IDENTITY = {
    "node": "infx-glm52-peer-0921",
    "cluster": "c2",
    "hostname": "hu-pdx-142",
    "inventory_sha256": "132064aa6e3f29eeed84a678fe5b6bf9da21cc9ae2a260a16468f442341c4161",
    "namespace": "infra",
    "queue": "earth",
    "image": "lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85@sha256:b518f4f8cd15664cf0f733e9bf4fd2105c9c994882a369b247364394db99f596",
}

GPU_UUIDS = [
    "GPU-8aa047b0-1a50-0c08-3641-86cb87b5334a",
    "GPU-21f58b95-8639-1f76-d7ea-a2f90eb27a6a",
    "GPU-c7b5ca71-599a-7872-3945-ce90bc3e6eed",
    "GPU-90fd2382-6595-6a88-6fcb-27f7564235c5",
    "GPU-311eddde-16ce-10ab-e1be-fb3bb9f57a3f",
    "GPU-631a0cb9-8901-3b0e-1160-ae0e60e3cd8c",
    "GPU-670039d7-2083-cae9-5b29-96da5b9b6986",
    "GPU-d07c6b22-effa-5fd6-02f4-7215b87b20a6",
]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(name):
    path = FROZEN / name
    require(
        path.is_file() and not path.is_symlink() and sha(path) == PINS[name],
        f"Frozen primitive changed: {name}",
    )
    spec = importlib.util.spec_from_file_location("_recovery5_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    # Avoid writing import caches into the frozen, byte-bound helper directory.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def modules():
    require({p.name for p in FROZEN.iterdir()} == set(PINS), "Unexpected frozen inputs")
    for name, digest in PINS.items():
        path = FROZEN / name
        require(
            path.is_file() and not path.is_symlink() and sha(path) == digest,
            f"Frozen input changed: {name}",
        )
    pkg = load("bootstrap_megamoe_recovery1.py")
    pkg.ROOT, pkg.CAMPAIGN = BOOTSTRAP, ROOT
    b = load("campaign_20260921.py")
    r = load("continue_megamoe_recovery2.py")
    r.ROOT, r.RUN = ROOT, RUN
    layout = load("continue_megamoe_recovery3.py")
    return pkg, b, r, layout


def checked_identity(receipt, hostname):
    require(
        all(receipt.get(k) == v for k, v in IDENTITY.items()),
        "Wrong recovery5 node/image/queue identity",
    )
    require(
        isinstance(receipt.get("hostname"), str)
        and receipt["hostname"] == hostname
        and hostname.startswith("hu-"),
        "Actual physical host receipt required",
    )
    return receipt


def idle(b):
    # Do not inspect PIDs from a different physical node.
    b.idle()
    rows = b.command(
        [
            "nvidia-smi",
            "--query-gpu=uuid,name,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
    ).splitlines()
    require(
        len(rows) == 8
        and [row.split(",")[0].strip() for row in rows] == GPU_UUIDS
        and all(
            "B300" in row and all(float(x.strip()) == 0 for x in row.split(",")[-2:])
            for row in rows
        ),
        "Eight idle B300 with the observed peer GPU identities required",
    )


def source_clone(recorder, b, name, origin, pin):
    dest = ROOT / "sources" / name
    require(not dest.exists() and not dest.is_symlink(), "Source destination exists")
    recorder.run(["git", "init", str(dest)], f"{name}-init")
    recorder.run(
        ["git", "-C", str(dest), "remote", "add", "origin", origin], f"{name}-origin"
    )
    recorder.run(
        ["git", "-C", str(dest), "fetch", "--depth=1", "--no-tags", "origin", pin],
        f"{name}-fetch",
    )
    recorder.run(
        ["git", "-C", str(dest), "checkout", "--detach", pin], f"{name}-checkout"
    )
    b.clean_head(dest, pin)
    return dest


def checkpoint(pkg):
    actual = pkg.inspect_model()
    expected = json.loads((FROZEN / "checkpoint.json").read_text())
    require(
        actual == expected and len(actual["shard_bytes"]) == 47,
        "Real checkpoint metadata/shard inventory changed",
    )
    return actual


def published_helpers(recipe, relative):
    """Bind the reviewed dispatch to exactly the scripts published in the recipe."""
    published = recipe / relative
    expected = {
        name: sha(Path(__file__).with_name(name))
        for name in ("bootstrap_megamoe_recovery5.py", "continue_megamoe_recovery5.py")
    } | {f"recovery4_frozen/{name}": digest for name, digest in PINS.items()}
    require(
        {p.name for p in (published / "recovery4_frozen").iterdir()} == set(PINS),
        "Published frozen input set differs",
    )
    for rel, digest in expected.items():
        path = published / rel
        require(
            path.is_file()
            and not path.is_symlink()
            and path.resolve() == path.absolute()
            and sha(path) == digest,
            f"Published helper differs from reviewed dispatch: {rel}",
        )
    return {"recipe_root": str(recipe), "files": expected}


def empty_campaign_cache():
    cache = ROOT / "caches/megamoe"
    require(not cache.exists() and not cache.is_symlink(), "Fresh cache required")
    cache.mkdir(parents=True)
    require(not any(cache.iterdir()), "Fresh cache is not empty")
    return {
        "schema_version": 1,
        "path": str(cache),
        "copied": False,
        "source_cache": None,
        "initial_entries": [],
        "policy": "fresh empty cache; no old cache read, copied or linked",
    }


def validate_seal(evidence, filename):
    receipt = json.loads((evidence / filename).read_text())
    for rel, record in receipt["files"].items():
        path = evidence / rel
        require(
            not Path(rel).is_absolute() and ".." not in Path(rel).parts,
            "Unsafe sealed member",
        )
        require(
            record.get("type") == "file"
            and path.is_file()
            and not path.is_symlink()
            and path.resolve() == path.absolute()
            and path.stat().st_size == record["bytes"]
            and sha(path) == record["sha256"],
            f"Sealed evidence changed: {rel}",
        )
    return receipt


def apply(args):
    pkg, b, r, layout = modules()
    require(
        platform.system() == "Linux"
        and platform.machine() == "x86_64"
        and sys.version_info[:2] == (3, 12),
        "Linux x86_64 Python3.12 required",
    )
    require(
        re.fullmatch("[0-9a-f]{40}", args.recipe_commit or "") is not None,
        "Full recipe SHA required",
    )
    for path in (ROOT, BOOTSTRAP):
        pkg.safe_ancestors(path)
        require(not path.exists(), f"Exclusive new root required: {path}")
    identity = checked_identity(pkg.read_json(args.image_receipt), socket.gethostname())
    idle(b)
    model = checkpoint(pkg)
    # This reads only sealed old provenance and the accepted 28 raw files. No old
    # process checks, source imports, cache inventory or cache payload reads.
    _, refs = r.old_inputs(b)
    BOOTSTRAP.mkdir(parents=True)
    ROOT.mkdir(parents=True)
    evidence = BOOTSTRAP / "evidence"
    evidence.mkdir()
    (evidence / "commands").mkdir()
    (BOOTSTRAP / "wheels").mkdir()
    recorder = pkg.Recorder(evidence / "commands", pkg.clean_env())
    e = ROOT / "environment"
    e.mkdir()
    for name in ("results", "archives", "sources"):
        (ROOT / name).mkdir()
    helpers = e / "helpers"
    helpers.mkdir()
    for name in ("bootstrap_megamoe_recovery5.py", "continue_megamoe_recovery5.py"):
        shutil.copyfile(Path(__file__).with_name(name), helpers / name)
    shutil.copytree(FROZEN, helpers / "recovery4_frozen")
    try:
        shutil.copyfile(args.image_receipt, evidence / "image-receipt.json")
        pkg.write(evidence / "checkpoint.json", model)
        pkg.write(
            evidence / "bootstrap-cache-paths.json",
            {k: v for k, v in recorder.env.items() if str(BOOTSTRAP) in v},
        )
        reference = json.loads((FROZEN / "reference-runtime.json").read_text())
        reference_freeze = (FROZEN / "reference-freeze.txt").read_text()
        names = sorted(set(reference["versions"]) | set(b.PACKAGES) | set(pkg.TARGET))
        before = json.loads(
            recorder.run(
                [sys.executable, "-I", "-c", pkg.PROBE, json.dumps(names)],
                "probe-before",
            )
        )
        freeze_before = recorder.run(
            [sys.executable, "-I", "-m", "pip", "--isolated", "freeze"], "freeze-before"
        )
        pkg.verify_stack(before, freeze_before, reference, reference_freeze, pkg.FRESH)
        pkg.write(evidence / "runtime-before.json", before)
        (evidence / "packages-before.txt").write_text(freeze_before + "\n")
        recorder.run(
            [sys.executable, "-I", "-m", "pip", "--isolated", "check"],
            "pip-check-before",
            (0, 1),
        )
        lock = json.loads(
            (FROZEN / "megamoe_bootstrap_recovery1_wheels.json").read_text()
        )
        for record in lock["packages"].values():
            pkg.download_wheel(record, BOOTSTRAP / "wheels")
        sg = source_clone(
            recorder, b, "sglang", "https://github.com/sgl-project/sglang.git", b.SG
        )
        fi = source_clone(
            recorder,
            b,
            "flashinfer",
            "https://github.com/flashinfer-ai/flashinfer.git",
            b.FI,
        )
        recipe = source_clone(
            recorder,
            b,
            "inferencex",
            "https://github.com/zianglih/InferenceX.git",
            args.recipe_commit,
        )
        recorder.run(
            [
                "git",
                "-C",
                str(fi),
                "submodule",
                "update",
                "--init",
                "--recursive",
                "--depth=1",
                *layout.DEPENDENCIES,
            ],
            "fi-submodules",
        )
        layout.check_dependencies(b, fi)
        b.resolved_config(recipe)
        # This must precede uninstall/install: a reviewed dispatch cannot silently
        # differ from the source recipe that the run records as its tested commit.
        b.write_json(
            e / "published-helper-binding.json", published_helpers(recipe, b.RELATIVE)
        )
        require(
            sha(recipe / b.RELATIVE / "run_megamoe_recovery3.sh") == WRAPPER_SHA,
            "Fourteen-point real-weight wrapper changed",
        )
        idle(b)
        recorder.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pip",
                "--isolated",
                "uninstall",
                "-y",
                "flashinfer-python",
                "flashinfer-cubin",
                "flashinfer-jit-cache",
            ],
            "remove-fi",
        )
        recorder.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-deps",
                "--no-index",
                *[
                    str(BOOTSTRAP / "wheels" / x["filename"])
                    for x in lock["packages"].values()
                ],
            ],
            "install-locked-wheels",
        )
        # Install into the final source tree: never clone away ignored build outputs.
        recorder.run(
            [
                sys.executable,
                "-I",
                "-m",
                "pip",
                "--isolated",
                "install",
                "--no-deps",
                "--no-build-isolation",
                "--no-index",
                "-e",
                str(fi),
            ],
            "install-fi-editable",
        )
        resource = layout.resources(b, fi)
        after = json.loads(
            recorder.run(
                [sys.executable, "-I", "-c", pkg.PROBE, json.dumps(names)],
                "probe-after",
            )
        )
        freeze_after = recorder.run(
            [sys.executable, "-I", "-m", "pip", "--isolated", "freeze"], "freeze-after"
        )
        pkg.verify_stack(after, freeze_after, before, freeze_before, pkg.TARGET)
        pkg.verify_stack(after, freeze_after, reference, reference_freeze, pkg.TARGET)
        require(
            all(
                before[k] == after[k]
                for k in ("torch_import", "torch_cuda", "nccl", "nvcc", "gpu")
            ),
            "Image runtime/GPU identity changed during bootstrap",
        )
        b.require_stack(after)
        pkg.write(evidence / "runtime-after.json", after)
        (evidence / "packages-after.txt").write_text(freeze_after + "\n")
        recorder.run(
            [sys.executable, "-I", "-m", "pip", "--isolated", "check"],
            "pip-check-after",
            (0, 1),
        )
        imports_code = "import json,flashinfer,flashinfer._build_meta as m,flashinfer.jit.env as j,cutlass;from cupti import cupti;from flashinfer.moe_ep import Sm100_Bf16_Nvfp4_Bf16_Cutedsl_MegaMoeConfig;print(json.dumps({'flashinfer':flashinfer.__file__,'build_meta_path':m.__file__,'version':m.__version__,'commit':m.__git_commit__,'csrc':str(j.FLASHINFER_CSRC_DIR),'cutlass':cutlass.__file__,'cupti_timestamp_ok':isinstance(cupti.get_timestamp(),int)}))"
        imports = json.loads(
            recorder.run([sys.executable, "-I", "-c", imports_code], "source-imports")
        )
        require(
            all(
                imports.get(k) == v
                for k, v in {
                    "flashinfer": str(fi / "flashinfer/__init__.py"),
                    "build_meta_path": str(fi / "flashinfer/_build_meta.py"),
                    "version": "0.7.0",
                    "commit": b.FI,
                    "csrc": str(fi / "flashinfer/data/csrc"),
                    "cupti_timestamp_ok": True,
                }.items()
            ),
            "Editable import/build metadata binding differs",
        )
        pkg.write(evidence / "source-imports.json", imports)
        pkg.write(evidence / "prepared-resource-layout.json", resource)
        idle(b)
        pkg.write(
            evidence / "bootstrap-completed.json",
            {
                "completed_at": b.now(),
                "identity_receipt": identity,
                "bootstrap_root": str(BOOTSTRAP),
                "task_root": str(ROOT),
                "files": b.inventory(evidence),
                "wheels": lock["packages"],
                "image_runtime_and_unrelated_packages_preserved": True,
                "benchmark_launched": False,
                "dummy_or_kernel_probe_performed": False,
            },
        )
        # Campaign runtime-before/after describe post-bootstrap preparation, while
        # its included bootstrap seal retains the actual package changes.
        inputs = {
            "task_root": str(ROOT),
            "run_id": RUN,
            "model_path": str(pkg.MODEL),
            "recipe_commit": args.recipe_commit,
            "sglang_commit": b.SG,
            "flashinfer_commit": b.FI,
            "image": b.IMAGE,
        }
        b.write_json(e / "inputs.json", inputs)
        shutil.copyfile(args.image_receipt, e / "image-receipt.json")
        shutil.copytree(evidence, e / "bootstrap")
        b.write_json(e / "reused-successful-cases.json", refs)
        b.write_json(
            e / "flashinfer-dependencies.json", layout.check_dependencies(b, fi)
        )
        b.write_json(e / "flashinfer-resource-layout.json", resource)
        shutil.copyfile(
            fi / "flashinfer/_build_meta.py", e / "flashinfer-build-meta.py"
        )
        b.write_json(e / "flashinfer-resource-import.json", imports)
        b.write_json(e / "checkpoint.json", model)
        b.write_json(e / "cache-origin.json", empty_campaign_cache())
        for name in ("runtime-before.json", "runtime-after.json"):
            b.write_json(e / name, after)
        for name in ("packages-before.txt", "packages-after.txt"):
            (e / name).write_text(freeze_after + "\n")
        env = recorder.env | {
            "PYTHONPATH": f"{sg / 'python'}:{fi}:{recipe}",
            "SGLANG_SOURCE_ROOT": str(sg),
            "SGLANG_COMMIT": b.SG,
            "FLASHINFER_SOURCE_ROOT": str(fi),
            "FLASHINFER_COMMIT": b.FI,
        }
        recorder_source = pkg.Recorder(e / "source-checks", env)
        recorder_source.directory.mkdir()
        recorder_source.run(
            [
                sys.executable,
                "-B",
                str(recipe / b.RELATIVE / "artifacts.py"),
                "verify-source",
            ],
            "verify-source",
        )
        b.write_json(e / "resolved-config.json", b.resolved_config(recipe))
        layout.archive_sources(b, ROOT, args.recipe_commit, e)
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
        require(
            checkpoint(pkg) == model and layout.resources(b, fi) == resource,
            "Model or prepared source changed during setup",
        )
        require(
            not any((ROOT / "caches/megamoe").iterdir()),
            "Campaign cache changed before launch",
        )
        idle(b)
        b.write_json(
            e / "setup-completed.json",
            {
                "completed_at": b.now(),
                "inputs": inputs,
                "files": b.inventory(e),
                "runtime_preserved": True,
                "cache_copied": False,
                "bootstrap_seal_sha256": sha(e / "bootstrap/bootstrap-completed.json"),
                "image_evidence_source": "new-node caller receipt and same-node bootstrap before/after",
                "source_binding_note": "editable FI installed directly into final campaign source tree",
                "launch_performed": False,
            },
        )
    except BaseException as error:
        pkg.write(
            evidence / "preparation-failed.json",
            {
                "failed_at": b.now(),
                "error": f"{type(error).__name__}: {error}",
                "partial_evidence_preserved": True,
            },
        )
        raise
    return {
        "prepared": True,
        "root": str(ROOT),
        "run_id": RUN,
        "setup_seal_sha256": sha(e / "setup-completed.json"),
        "benchmark_launched": False,
    }


def plan():
    pkg, b, r, _ = modules()
    return {
        "identity": IDENTITY,
        "physical_host": IDENTITY["hostname"],
        "gpu_uuids": GPU_UUIDS,
        "task_root": str(ROOT),
        "bootstrap_root": str(BOOTSTRAP),
        "run_id": RUN,
        "sglang_commit": b.SG,
        "flashinfer_commit": b.FI,
        "image": b.IMAGE,
        "model": str(pkg.MODEL),
        "checkpoint_revision": pkg.REVISION,
        "cases": r.CASES,
        "remaining_requests": sum(c * 10 for _, _, c in r.CASES),
        "reused_cases": list(r.REUSED),
        "reused_requests": 2600,
        "packages": pkg.TARGET,
        "cache_copied": False,
        "dummy_or_kernel_probe": False,
        "default_remote_or_package_mutations": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=("plan", "apply"), default="plan")
    parser.add_argument("--image-receipt", type=Path)
    parser.add_argument("--recipe-commit")
    args = parser.parse_args()
    if args.action == "apply":
        require(
            args.image_receipt is not None, "Caller image/hostname receipt required"
        )
        value = apply(args)
    else:
        value = plan()
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
