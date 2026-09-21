"""R7 fixed-resource preparation primitives; no work occurs on import."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = Path("/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery7")
OLD = Path("/data/home/ziangli/inferencex-glm52-stock-20260921")
RUN = "c2-w4a16-megamoe-autotune-20260921-recovery7"
PYTHON = "/opt/sglang/bin/python3"
SG = "26c41009549f9ad407e107b33d5144f6e085418b"
BOOTSTRAP_SG = "6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2"
FI = "ad0a5e5e78e57070ec7c582efe733cb55cd8839f"
RECIPE_BASE = "fe115d78ec56c79f5ee3453993a316627ef8eec4"
GATES = {'stock_sg_c8', 'stock_payload_preservation', 'source_payload_preservation', 'bootstrap_acceptance', 'execution_review'}
COMMAND_LOG = None
COMMAND_NUMBER = 0


C8_PARSER_SUPPLEMENT = 'STOCK_SG_WORKAROUND_STARTUP_READY_WITH_LOG_PARSER_FAILURE_NO_MEASUREMENT'
C8_PARSER_ERROR = "ValueError('Proxy NONE INFO proof missing for a natural rank')"
C8_PARSER_ISSUES = ['Producer proxy summary differs', 'Controller/postguard errors', 'Four-rank stock/no-proxy startup evidence incomplete']


def accepted_c8_parser_supplement(report):
    """Exact offline false-negative receipt only; original exit1 is never normalized."""
    return (
        report.get('classification') == C8_PARSER_SUPPLEMENT
        and report.get('worker_exit') == report.get('controller_exit') == 1
        and report.get('recorded_worker_and_controller_exit') == [1, 1]
        and report.get('original_classification') == 'OTHER_FAILURE_OR_INCOMPLETE'
        and report.get('original_issues') == C8_PARSER_ISSUES
        and report.get('original_issue_count') == 3
        and report.get('original_observation_error') == C8_PARSER_ERROR
        and report.get('original_runtime_failure_preserved') is True
        and report.get('native_semantics_changed_by_review') is False
        and report.get('health') is True and report.get('cleanup_errors') == []
        and report.get('symptom_lines') == [] and report.get('performance_requests') == 0
        and report.get('observations', {}).get('all_four_complete') is True
        and report.get('observations', {}).get('errors') == []
        and report.get('proxy_evidence', {}).get('covered_ranks') == [0, 1, 2, 3]
        and report.get('natural_returncode_before_cleanup') is None
        and isinstance(report.get('supplement_bindings'), dict)
        and bool(report.get('supplement_bindings'))
    )


def need(ok, why):
    if not ok:
        raise ValueError(why)


def now():
    return datetime.now(timezone.utc).isoformat()


def safe(path):
    path = Path(path)
    need(
        path.is_absolute()
        and ".." not in path.parts
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Unsafe linked/nonabsolute path",
    )
    return path


def describe(path, limit=4 * 1024**3):
    path = safe(path)
    before = path.stat()
    need(path.is_file() and before.st_size <= limit, "Regular file bound")
    with path.open("rb") as f:
        h = hashlib.file_digest(f, "sha256").hexdigest()
        after = os.fstat(f.fileno())
    keys = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    need(
        all(
            getattr(before, k) == getattr(after, k) == getattr(path.stat(), k)
            for k in keys
        ),
        "File changed",
    )
    return {"bytes": after.st_size, "sha256": h}


def read(path, expected=None):
    desc = describe(path, 4 * 1024**2)
    if expected is not None:
        need(desc["sha256"] == expected, "Receipt SHA differs")
    data = Path(path).read_bytes()
    need(hashlib.sha256(data).hexdigest() == desc["sha256"], "Receipt changed on read")
    return json.loads(data)


def write(path, value):
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    need(len(data) <= 8 * 1024**2, "Output receipt bound")
    with Path(path).open("xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def module(filename, name):
    pins = read(HERE / "primitive-lock.json")
    record = pins[filename]
    path = HERE / "primitives" / filename
    need(
        describe(path) == {k: record[k] for k in ("bytes", "sha256")},
        "Primitive changed",
    )
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def bundle_guard():
    manifest = read(HERE / "bundle-manifest.json")
    for name, expected in manifest.items():
        p = Path(name)
        need(not p.is_absolute() and ".." not in p.parts, "Unsafe bundle name")
        need(describe(HERE / p) == expected, "Bundle bytes changed: " + name)
    return manifest


def load_lock(path, expected):
    need(
        isinstance(expected, str) and len(expected) == 64,
        "Explicit activation SHA required",
    )
    lock = read(path, expected)
    need(
        lock.get("status") == "BOUND_FOR_REVIEWED_R7_EXECUTION",
        "Activation remains unbound",
    )
    need(
        lock.get("root") == str(ROOT) and lock.get("run_id") == RUN, "Wrong R7 root/run"
    )
    node=lock.get('node',{})
    need(node.get('name')=='infx-glm52-stock-0921' and node.get('cluster')=='c2' and node.get('namespace')=='ziangli' and isinstance(node.get('hostname'),str) and node['hostname'].startswith('hu-pdx-'), 'Unbound replacement node')
    need(lock.get('runtime_guard') and lock['runtime_guard']['node']==node and len(set(lock['runtime_guard']['gpu_uuids']))==8, 'Actual bootstrap/GPU guard missing')
    need(lock['runtime_guard']['source_pins']=={'sglang':BOOTSTRAP_SG,'flashinfer':FI}, 'Bootstrap baseline pins differ')
    need(
        set(lock["gate_receipts"]) == GATES and all(lock["gate_receipts"].values()),
        "Required actual acceptance missing",
    )
    for name, item in lock["gate_receipts"].items():
        report = read(item["path"], item["sha256"])
        need(
            report.get(item.get("status_field", "status")) == item["accepted_status"]
            and report.get("issues") == []
            and report.get("issue_count", 0) == 0,
            "Gate not independently accepted: " + name,
        )
        need(
            not any(
                word in item["accepted_status"].upper()
                for word in ("PENDING", "NOT_", "FAIL")
            ) or (name == 'stock_sg_c8' and item.get('status_field') == 'classification'
                  and item['accepted_status'] == C8_PARSER_SUPPLEMENT
                  and accepted_c8_parser_supplement(report)),
            "Nonacceptance status",
        )
    pub = lock.get("publication")
    need(
        isinstance(pub, dict)
        and len(pub.get("commit", "")) == 40
        and all(c in "0123456789abcdef" for c in pub["commit"]),
        "Unbound published recipe",
    )
    need(
        pub["bundle_manifest_sha256"]
        == describe(HERE / "bundle-manifest.json")["sha256"],
        "Published bundle differs",
    )
    for key in ('recipe_seed', 'model_path', 'sglang_seed'):
        safe(pub[key] if key=='recipe_seed' else lock[key])
    need(lock['native_binding']['stock_manifest_sha256']==describe(HERE/'stock-native.json')['sha256'], 'Stock provider manifest differs')
    need(
        lock.get("selected")
        and lock.get("native_binding")
        and isinstance(lock.get("base_environment"), dict),
        "Native/runtime binding missing",
    )
    need(
        isinstance(lock.get("prior_owners"), list) and lock["prior_owners"],
        "Actual prior terminal owners required",
    )
    for owner in lock["prior_owners"]:
        need(
            type(owner["pid"]) is int
            and owner["pid"] > 1
            and type(owner["starttime"]) is int,
            "Invalid terminal owner",
        )
    need(
        lock["model_path"]
        == "/data/home/ziangli/inferencex-glm52-b300/checkpoints/GLM-5.2-NVFP4",
        "Model resource must match accepted bootstrap",
    )
    need(lock['native_binding']['hostname']==node['hostname'], 'Native/actual node identity differs')
    need(Path(lock['sglang_seed']).is_relative_to(OLD/'diagnostics'), 'SG runtime seed outside accepted new-node diagnostic scope')
    bundle_guard()
    return lock


def host_guard(lock):
    need(
        sys.prefix == "/opt/sglang"
        and sys.version_info[:2] == (3, 12)
        and socket.gethostname() == lock["node"]["hostname"],
        "Wrong runtime/host",
    )
    for owner in lock["prior_owners"]:
        need(not Path(f"/proc/{owner['pid']}").exists(), "Prior owner present/reused")
    for key in os.environ:
        need(
            not key.startswith("NVSHMEM_")
            and key not in ("LD_PRELOAD", "LD_AUDIT", "TORCH_USE_RTLD_GLOBAL"),
            "Injected parent environment",
        )
    guard = module("guard.py", "_r7_guard")
    guard.ROOT=OLD
    result = guard.guards(lock["runtime_guard"])
    checkpoint = module("checkpoint.py", "_r7_checkpoint").inspect_model()
    expected = read(
        OLD / "environment/bootstrap/helpers/recovery4_frozen/checkpoint.json"
    )
    need(
        checkpoint == expected and len(checkpoint["shard_bytes"]) == 47,
        "Checkpoint metadata/size changed",
    )
    result["checkpoint"] = checkpoint
    return result


def cmd(argv, *, env=None, output=None, timeout=900):
    global COMMAND_NUMBER
    environment = dict(
        os.environ,
        GIT_OPTIONAL_LOCKS="0",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONNOUSERSITE="1",
    )
    if env is not None:
        environment.update(env)
    record = {"argv": argv, "at": now(), "error": None, "returncode": None}
    prefix = None
    if COMMAND_LOG is not None:
        COMMAND_NUMBER += 1
        prefix = COMMAND_LOG / f"{COMMAND_NUMBER:03d}"
    try:
        if output is None:
            r = subprocess.run(
                argv, capture_output=True, env=environment, timeout=timeout
            )
            need(
                len(r.stdout) <= 16 * 1024**2 and len(r.stderr) <= 16 * 1024**2,
                "Command receipt bound",
            )
            if prefix:
                prefix.with_suffix(".stdout").write_bytes(r.stdout)
                prefix.with_suffix(".stderr").write_bytes(r.stderr)
            record["returncode"] = r.returncode
            r.check_returncode()
            return r.stdout.decode().strip()
        with Path(output).open("xb") as f:
            r = subprocess.run(
                argv, stdout=f, stderr=subprocess.PIPE, env=environment, timeout=timeout
            )
        need(len(r.stderr) <= 16 * 1024**2, "Command error receipt bound")
        if prefix:
            prefix.with_suffix(".stderr").write_bytes(r.stderr)
        record.update(
            returncode=r.returncode,
            output=str(output),
            output_descriptor=describe(output),
        )
        r.check_returncode()
        return str(output)
    except BaseException as error:
        record["error"] = repr(error)
        raise
    finally:
        if prefix:
            write(prefix.with_suffix(".json"), record)


def clean_head(root, pin):
    need(
        cmd(["git", "-C", str(root), "rev-parse", "HEAD"]) == pin, "Source HEAD differs"
    )
    need(
        not cmd(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"]
        ),
        "Tracked source dirty",
    )


def clone(old, new, pin):
    safe(old)
    safe(new)
    need(not new.exists(), "Clone destination exists")
    clean_head(old, pin)
    cmd(
        [
            "git",
            "clone",
            "--local",
            "--no-hardlinks",
            "--no-checkout",
            str(old),
            str(new),
        ]
    )
    cmd(["git", "-C", str(new), "checkout", "--detach", pin])
    clean_head(new, pin)
    need((new/'.git').is_dir() and not (new/'.git').is_symlink(), 'Clone is not independent')
    need(cmd(['git','-C',str(new),'rev-parse','--path-format=absolute','--git-common-dir'])==str(new/'.git'), 'Shared Git common dir')
    need(not (new/'.git/objects/info/alternates').exists(), 'Clone has alternates')


class LayoutBase:
    FI = FI
    command = staticmethod(cmd)
    clean_head = staticmethod(clean_head)
    sha = staticmethod(lambda path: describe(path)["sha256"])


def recipe_files(recipe):
    return recipe / "experimental/glm52_b300_fixed_seq"


def published_equality(recipe):
    campaign_inputs = read(HERE / "frozen_campaign/inputs.json")["files"]
    case_inputs = read(HERE / "frozen_campaign/frozen_case/inputs.json")["files"]
    for relative in (
        "experimental/glm52_b300_fixed_seq/config.env",
        "experimental/glm52_b300_fixed_seq/config-megamoe.env",
        "experimental/glm52_b300_fixed_seq/common.sh",
        "experimental/glm52_b300_fixed_seq/artifacts.py",
        "benchmarks/benchmark_lib.sh",
    ):
        item = (case_inputs if "artifacts.py" in relative else campaign_inputs)[
            "inferencex/" + relative
        ]
        need(
            describe(recipe / relative) == {k: item[k] for k in ("bytes", "sha256")},
            "Original recipe changed: " + relative,
        )
    installed = recipe_files(recipe) / "recovery7"
    for name, expected in bundle_guard().items():
        need(
            describe(installed / name) == expected, "Published helper differs: " + name
        )
    need(
        describe(installed / "bundle-manifest.json")
        == describe(HERE / "bundle-manifest.json"),
        "Published manifest differs",
    )
    for name in ("run_megamoe_recovery7.sh", "common-recovery7.sh"):
        need(
            describe(recipe_files(recipe) / name)
            == describe(HERE / "publication" / name),
            "Published recipe entry differs",
        )


def prepare(lock, lock_path):
    global COMMAND_LOG
    clean_parent(lock)
    native_guard(lock)
    before = host_guard(lock)
    need(not ROOT.exists() and not ROOT.is_symlink(), "R7 root must be exclusive")
    seed = Path(lock["publication"]["recipe_seed"])
    clean_head(seed, lock["publication"]["commit"])
    published_equality(seed)
    cmd(
        [
            "git",
            "-C",
            str(seed),
            "merge-base",
            "--is-ancestor",
            RECIPE_BASE,
            lock["publication"]["commit"],
        ]
    )
    os.environ["GIT_OPTIONAL_LOCKS"] = (
        "0"  # direct frozen layout git calls inherit read-only behavior
    )
    safe(ROOT)
    ROOT.mkdir(parents=False)
    envroot = ROOT / "environment"
    envroot.mkdir()
    (ROOT / "sources").mkdir()
    (ROOT / "results").mkdir()
    (ROOT / "archives").mkdir()
    COMMAND_LOG = envroot / "commands"
    COMMAND_LOG.mkdir()
    (ROOT / "caches/megamoe").mkdir(parents=True)
    terminal = {"status": "PREPARATION_FAILED", "error": None}
    try:
        shutil.copyfile(lock_path, envroot / "activation.json")
        (envroot / "acceptance").mkdir()
        for name, item in lock["gate_receipts"].items():
            read(item["path"], item["sha256"])
            shutil.copyfile(item["path"], envroot / "acceptance" / (name + ".json"))
        write(envroot / "before.json", before)
        write(
            envroot / "reused-successes.json", read(HERE / "frozen_campaign/reuse.json")
        )
        verify_reuse(lock)
        write(
            envroot / "reuse-verified.json",
            {
                "root": lock["reused_raw_root"],
                "raw_files": read(HERE / "frozen_campaign/reuse.json")["raw_files"],
            },
        )
        cmd(
            [PYTHON, "-I", "-B", "-m", "pip", "freeze"],
            output=envroot / "freeze-before.txt",
        )
        verify_sglang_seed(Path(lock["sglang_seed"]))
        clone(Path(lock["sglang_seed"]), ROOT / "sources/sglang", SG)
        verify_sglang_seed(ROOT / "sources/sglang")
        clone(OLD / "sources/flashinfer", ROOT / "sources/flashinfer", FI)
        layout = module("layout.py", "_r7_layout")
        fi = ROOT / "sources/flashinfer"
        cmd(["git", "-C", str(fi), "submodule", "init", "--", *layout.DEPENDENCIES])
        for relative, pin in layout.DEPENDENCIES.items():
            dest = fi / relative
            if dest.exists():
                need(
                    dest.is_dir() and not dest.is_symlink() and not any(dest.iterdir()),
                    "Dependency destination nonempty",
                )
                dest.rmdir()
            clone(OLD / "sources/flashinfer" / relative, dest, pin)
        cmd(
            [
                "git",
                "-C",
                str(fi),
                "submodule",
                "absorbgitdirs",
                "--",
                *layout.DEPENDENCIES,
            ]
        )
        write(envroot / "dependencies.json", layout.check_dependencies(LayoutBase, fi))
        write(
            envroot / "resource-layout.json",
            layout.resources(LayoutBase, fi, create=True),
        )
        shutil.copyfile(
            fi / "flashinfer/_build_meta.py", envroot / "flashinfer-build-meta.py"
        )
        clone(seed, ROOT / "sources/inferencex", lock["publication"]["commit"])
        published_equality(ROOT / "sources/inferencex")
        imports = {
            "PYTHONPATH": str(ROOT / "sources/sglang/python")
            + ":"
            + str(fi)
            + ":"
            + str(ROOT / "sources/inferencex")
        }
        code = 'import json,sglang,flashinfer,flashinfer._build_meta as m; print(json.dumps({"sglang":sglang.__file__,"flashinfer":flashinfer.__file__,"meta":m.__file__,"commit":m.__git_commit__,"version":m.__version__}))'
        probe = json.loads(cmd([PYTHON, "-B", "-c", code], env=imports))
        write(envroot / "source-imports.json", probe)
        need(
            probe
            == {
                "sglang": str(ROOT / "sources/sglang/python/sglang/__init__.py"),
                "flashinfer": str(fi / "flashinfer/__init__.py"),
                "meta": str(fi / "flashinfer/_build_meta.py"),
                "commit": FI,
                "version": "0.7.0",
            },
            "Fresh source import mix",
        )
        source_archives = envroot / "sources"
        source_archives.mkdir()
        repos = {
            "sglang": (ROOT / "sources/sglang", SG),
            "flashinfer": (fi, FI),
            "inferencex": (ROOT / "sources/inferencex", lock["publication"]["commit"]),
        }
        repos.update(
            {
                f"dependency-{i}": (fi / rel, pin)
                for i, (rel, pin) in enumerate(layout.DEPENDENCIES.items())
            }
        )
        source_origins = {}
        for name, (repo, pin) in repos.items():
            cmd(
                ["git", "-C", str(repo), "archive", "--format=tar.gz", pin],
                output=source_archives / (name + ".tar.gz"),
            )
            source_origins[name] = {
                "source": str(repo),
                "commit": pin,
                "archive": describe(source_archives / (name + ".tar.gz")),
            }
        write(envroot / "source-archive-origins.json", source_origins)
        # No global install and no copying of any old cache.
        cmd(
            [PYTHON, "-I", "-B", "-m", "pip", "freeze"],
            output=envroot / "freeze-after.txt",
        )
        need(
            (envroot / "freeze-before.txt").read_bytes()
            == (envroot / "freeze-after.txt").read_bytes(),
            "Package freeze changed",
        )
        write(envroot / "after.json", host_guard(lock))
        need(
            not any((ROOT / "caches/megamoe").iterdir()),
            "Fresh cache not empty before launch",
        )
        terminal.update(
            status="PREPARED_R7_NO_BENCHMARK",
            source_pins={
                "sglang": SG,
                "flashinfer": FI,
                "inferencex": lock["publication"]["commit"],
            },
            fresh_cache=True,
        )
    except BaseException as error:
        terminal["error"] = repr(error)
        raise
    finally:
        COMMAND_LOG = None
        terminal["at"] = now()
        terminal["files"] = {
            str(p.relative_to(envroot)): describe(p)
            for p in envroot.rglob("*")
            if p.is_file()
        }
        write(envroot / "setup-completed.json", terminal)
    return terminal


def clean_parent(lock):
    # Keep the image's ordered LD_LIBRARY_PATH; do not leak diagnostic overrides
    # or credentials into serialized receipts. Caller supplies only an exact
    # source-bound public runtime projection, not arbitrary replacement values.
    env = dict(os.environ)
    for key in list(env):
        if key.startswith(("NVSHMEM_", "MEGAMOE_R7_NATIVE_")) or key in (
            "LD_PRELOAD",
            "LD_AUDIT",
            "TORCH_USE_RTLD_GLOBAL",
        ):
            raise ValueError("Injected native parent environment")
    for key, value in lock["base_environment"].items():
        need(
            key
            in ("PATH", "LD_LIBRARY_PATH", "HOME", "USER", "TMPDIR", "OMP_NUM_THREADS"),
            "Unsupported base environment binding",
        )
        need(env.get(key) == value, "Base environment changed: " + key)
    need(
        "PATH" in lock["base_environment"]
        and "LD_LIBRARY_PATH" in lock["base_environment"],
        "Missing executable/loader path binding",
    )
    need(
        shutil.which("python3", path=env["PATH"]) == PYTHON,
        "Recipe python3 not pinned runtime",
    )
    env.update(
        PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0", PYTHONNOUSERSITE="1"
    )
    return env


def verify_reuse(lock):
    reuse = read(HERE / "frozen_campaign/reuse.json")
    root = safe(lock["reused_raw_root"])
    need(root.name == reuse["run_id"], "Old raw identity changed")
    for name, desc in reuse["raw_files"].items():
        need(describe(root / name) == desc, "Old accepted raw changed: " + name)
    return {
        "run_id": reuse["run_id"],
        "root": str(root),
        "raw_files": reuse["raw_files"],
        "calibration_parent_sha256": reuse["calibration_parent_sha256"],
        "two_case_parent_sha256": reuse["two_case_parent_sha256"],
        "native_variant": "original-wheel; not patched",
    }


def native_guard(lock):
    sys.path.insert(0, str(HERE/'frozen_campaign/frozen_case/frozen'))
    import stock
    stock.contract(lock['native_binding'])
    actual=read(HERE/'stock-native.json')
    prefix=actual['selected']['prefix']
    expected=dict(actual['selected'])
    expected['host_descriptor']=actual['members']['lib/libnvshmem_host.so.3']
    expected['plugin_descriptor']=actual['members']['lib/nvshmem_bootstrap_uid.so.3']
    need(lock['selected']==expected, 'Stock selected paths/descriptors differ')
    for name,desc in actual['members'].items():
        need(describe(Path(prefix)/name)==desc, 'Original wheel bytes changed: '+name)
    return {'native_variant':stock.VARIANT,'stock_manifest':describe(HERE/'stock-native.json')}


def verify_sglang_seed(root):
    clean_head(root,SG)
    need((root/'.git').is_dir() and not (root/'.git').is_symlink(), 'Independent SG clone required')
    need(not (root/'.git/objects/info/alternates').exists(), 'SG alternates forbidden')
    parents=[line.split()[1] for line in cmd(['git','-C',str(root),'cat-file','-p',SG]).splitlines() if line.startswith('parent ')]
    need(parents==[BOOTSTRAP_SG], 'SG successor parent differs')
    need(cmd(['git','-C',str(root),'diff','--numstat','--no-ext-diff',BOOTSTRAP_SG,SG])=='20\t0\tpython/sglang/srt/arg_groups/moe_hook.py', 'SG successor scope differs')
    need(describe(root/'python/sglang/srt/arg_groups/moe_hook.py')['sha256']=='d14be94722df85d545bceb955429a31211a94b91818619b5aae9352038a78277', 'Published workaround bytes differ')
