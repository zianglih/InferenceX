#!/usr/bin/env python3
"""Explicit, serial Kimi execution. No installation, remote control or acceptance issuance.

The root-approved preflight marker is an input, never generated here. Importing
this module performs no subprocess, network, GPU, filesystem write or ML import.
"""

from __future__ import annotations

import json
import errno
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import time
import traceback
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import ProxyHandler, build_opener

import source_contract
import continuation
import cache_seed

from plan import (
    ARM_CONTRACT,
    ROOT,
    canonical_path,
    descriptor,
    read_json,
    require,
)

PASSTHROUGH = {
    "HOME",
    "USER",
    "LOGNAME",
    "LD_LIBRARY_PATH",
    "LIBRARY_PATH",
    "CUDA_HOME",
    "CUDA_PATH",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "SGLANG_RUST_BUILD_MODE",
}
DEAD = {"Z", "X"}


def now():
    return datetime.now(timezone.utc).isoformat()


def encoded(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def save(path, value, *, replace=False):
    path = Path(path)
    raw = encoded(value)
    if replace:
        tmp = path.with_name(path.name + ".pending")
        save_bytes(tmp, raw)
        os.replace(tmp, path)
    else:
        save_bytes(path, raw)


def save_bytes(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def append(path, value):
    with Path(path).open("a") as stream:
        stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()


def plain_path(path, *, absent=False):
    path = canonical_path(str(path))
    for ancestor in (path, *path.parents):
        require(not ancestor.is_symlink(), f"Linked path: {ancestor}")
    if absent:
        require(not path.exists(), f"Exclusive path already exists: {path}")
    return path


def bound(item):
    require(set(item) == {"path", "bytes", "sha256"}, "Descriptor schema")
    path = plain_path(item["path"])
    require(
        descriptor(path) == {k: item[k] for k in ("bytes", "sha256")},
        f"Changed bound file: {path}",
    )
    return path


def process_row(pid):
    try:
        with open(f"/proc/{pid}/stat") as stream:
            text = stream.read(16385)
        require(len(text) <= 16384, "Oversized proc stat")
        fields = text[text.rfind(")") + 2 :].split()
        return {
            "pid": pid,
            "state": fields[0],
            "ppid": int(fields[1]),
            "pgid": int(fields[2]),
            "sid": int(fields[3]),
            "starttime": fields[19],
        }
    except (FileNotFoundError, ProcessLookupError):
        return None


def same_birth(row, saved):
    return (
        row is not None
        and row["pid"] == saved["pid"]
        and row["starttime"] == saved["starttime"]
    )


class OwnedProcess:
    """An owned new session, with descendant discovery and PID/birth-qualified signals.

    Unobserved children that escape ancestry/session before discovery cannot be
    reconstructed. No process-name or historical numeric PGID cleanup is used.
    """

    def __init__(self, argv, env, directory, role, cwd):
        self.role, self.directory = role, Path(directory)
        self.known = {}
        self.history = {}
        self.log = (self.directory / f"{role}.log").open("xb")
        self.process = None
        try:
            self.process = subprocess.Popen(
                argv,
                env=env,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=self.log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            row = process_row(self.process.pid)
            require(
                row is not None and row["sid"] == self.process.pid,
                "New child birth/session unavailable",
            )
            self.direct_birth = row
            self._remember([row])
            self.discover()
            save(
                self.directory / f"{role}.launch.json",
                {
                    "at": now(),
                    "pid": self.process.pid,
                    "birth": row,
                    "argv": argv,
                    "environment": env,
                    "cwd": str(cwd),
                    "stdin": "DEVNULL",
                    "new_session": True,
                },
            )
        except BaseException as exc:
            # A still-unwaited direct Popen child is ours even if /proc capture failed.
            rc = None
            if self.process is not None:
                if self.process.poll() is None:
                    self.process.terminate()
                try:
                    rc = self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    rc = self.process.wait(timeout=5)
            save(
                self.directory / f"{role}.launch-error.json",
                {
                    "error": repr(exc),
                    "waited_returncode": rc,
                    "descendant_absence_verified": False,
                },
            )
            self.log.close()
            raise

    def _remember(self, rows):
        additions = []
        for row in rows:
            key = (row["pid"], row["starttime"])
            if key not in self.history:
                additions.append(row)
                self.history[key] = row
            self.known[row["pid"]] = row
        if additions:
            append(
                self.directory / f"{self.role}.owners.jsonl",
                {"at": now(), "owners": additions},
            )

    def discover(self):
        rows = {}
        for p in Path("/proc").iterdir():
            if p.name.isdecimal():
                row = process_row(int(p.name))
                if row:
                    rows[row["pid"]] = row
        live = {
            pid for pid, saved in self.known.items() if same_birth(rows.get(pid), saved)
        }
        # Direct PID may only enter from its saved birth, never from a recycled PID.
        changed = True
        while changed:
            children = {
                pid
                for pid, row in rows.items()
                if row["ppid"] in live or (live and row["sid"] == self.process.pid)
            }
            changed = bool(children - live)
            live |= children
        self._remember([rows[pid] for pid in sorted(live)])

    def running(self):
        # Do not call poll() here: an exited-but-unwaited leader keeps its birth
        # available while we discover any late descendants in the owned session.
        row = process_row(self.process.pid)
        require(
            same_birth(row, self.direct_birth),
            "Owned direct birth unavailable before wait",
        )
        return row["state"] not in DEAD

    def alive(self):
        self.discover()
        return [
            row
            for pid, saved in self.known.items()
            if same_birth(row := process_row(pid), saved) and row["state"] not in DEAD
        ]

    def cleanup(self, term_seconds, kill_seconds):
        if hasattr(self, "cleanup_result"):
            return self.cleanup_result
        errors, signals = [], []
        for sig, grace in (
            (signal.SIGTERM, term_seconds),
            (signal.SIGKILL, kill_seconds),
        ):
            try:
                for row in self.alive():
                    current = process_row(row["pid"])
                    if same_birth(current, row) and current["state"] not in DEAD:
                        try:
                            os.kill(row["pid"], sig)
                            signals.append(
                                {"at": now(), "signal": int(sig), "owner": current}
                            )
                        except ProcessLookupError:
                            pass
                deadline = time.monotonic() + grace
                while self.alive() and time.monotonic() < deadline:
                    time.sleep(0.2)
            except Exception as exc:
                errors.append(repr(exc))
                # Discovery failure never turns into success. Direct-child cleanup
                # remains possible, without claiming unknown descendants absent.
                if self.process.poll() is None:
                    self.process.send_signal(sig)
        try:
            rc = self.process.wait(timeout=kill_seconds)
        except subprocess.TimeoutExpired:
            rc = None
            errors.append("Direct child wait timed out")
        try:
            remaining = self.alive()
        except Exception as exc:
            remaining = [{"unknown": True}]
            errors.append(repr(exc))
        self.log.close()
        result = {
            "at": now(),
            "waited_returncode": rc,
            "remaining": remaining,
            "errors": errors,
            "signals": signals,
            "owners": list(self.history.values()),
        }
        save(self.directory / f"{self.role}.exit.json", result)
        self.cleanup_result = result
        return result


def capture(argv, env, timeout=30):
    p = subprocess.run(
        argv,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return {
        "argv": argv,
        "returncode": p.returncode,
        "stdout": p.stdout,
        "stderr": p.stderr,
    }


def gpu_snapshot(env):
    identity = capture(
        ["nvidia-smi", "--query-gpu=index,uuid,name", "--format=csv,noheader,nounits"],
        env,
    )
    apps = capture(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,gpu_uuid,used_memory",
            "--format=csv,noheader,nounits",
        ],
        env,
    )
    usage = capture(
        [
            "nvidia-smi",
            "--query-gpu=index,utilization.gpu,memory.used",
            "--format=csv,noheader,nounits",
        ],
        env,
    )
    require(
        identity["returncode"] == apps["returncode"] == usage["returncode"] == 0,
        "GPU observation failed",
    )
    metrics = []
    for line in usage["stdout"].splitlines():
        index, util, memory = [int(part.strip()) for part in line.split(",")]
        metrics.append(
            {"index": index, "utilization_percent": util, "memory_mib": memory}
        )
    require(
        [row["index"] for row in metrics] == list(range(8)),
        "GPU utilization identity/order changed",
    )
    rows = []
    for line in identity["stdout"].splitlines():
        index, uuid, name = [part.strip() for part in line.split(",", 2)]
        rows.append({"index": int(index), "uuid": uuid, "name": name})
    return {
        "at": now(),
        "gpus": rows,
        "identity": identity,
        "applications": apps,
        "usage": usage,
        "metrics": metrics,
    }


def require_gpu(snapshot, expected, *, idle):
    require(
        snapshot["gpus"] == expected and len(expected) == 8,
        "GPU identity/order changed",
    )
    if idle:
        require(
            not snapshot["applications"]["stdout"].strip(), "GPU applications remain"
        )
        require(
            [row["index"] for row in snapshot["metrics"]] == list(range(8))
            and all(
                row["utilization_percent"] == 0 and 0 <= row["memory_mib"] <= 100
                for row in snapshot["metrics"]
            ),
            "GPU utilization/memory is not idle",
        )


def checkpoint_snapshot(request):
    # Reuse the exact pure preflight closure check. This function performs only
    # checkpoint directory/stat and sidecar reads; it imports no ML providers.
    from preflight import checkpoint

    return checkpoint(request)


def runtime_snapshot(cfg, env, marker):
    # Match the source state actually accepted by all three preflight probes.
    # Preserve optional uninitialized submodules only in that exact accepted state.
    expected = None
    roots = {cfg["runtime"][key] for key in ("sglang_root", "flashinfer_root")}
    require(
        set(marker["preflight_receipts"]) == set(ARM_CONTRACT),
        "Three source proofs required",
    )
    for arm, item in marker["preflight_receipts"].items():
        receipt = read_json(bound(item))
        require(
            receipt["status"] == "KIMI_RUNTIME_PREFLIGHT_PASSED_PENDING_ROOT_REVIEW"
            and receipt["arm"] == arm
            and receipt.get("error") is None,
            "Source preflight proof failed",
        )
        observed = receipt["sources"]
        require(set(observed) == roots, "Preflight source roots differ")
        require(
            expected is None or observed == expected,
            "Preflight source snapshots disagree",
        )
        expected = observed
    sources = {}
    for key, pin in (("sglang_root", "sglang"), ("flashinfer_root", "flashinfer")):
        root = cfg["runtime"][key]
        if pin == "sglang":
            source_contract.check_campaign(cfg)
            observed = source_contract.patched_source(root, env)
            require(
                observed == expected[root],
                "Patched source differs from accepted preflight",
            )
            sources[root] = observed
            continue
        rows = {}
        for label, command in (
            ("head", ["rev-parse", "HEAD"]),
            ("dirty", ["diff", "--name-only", "HEAD"]),
            ("submodules", ["submodule", "status"]),
            ("index", ["diff", "--cached", "--name-only"]),
            ("untracked", ["ls-files", "--others", "--exclude-standard"]),
        ):
            observed = capture(["git", "-C", root, *command], env)
            require(observed["returncode"] == 0, "Source query failed: " + root)
            rows[label] = observed["stdout"].strip()
        require(
            rows["head"] == cfg["pins"][pin]
            and not rows["dirty"]
            and not rows["index"],
            "Source HEAD/working tree changed",
        )
        require(
            expected[root]["commit"] == cfg["pins"][pin]
            and rows["submodules"] == expected[root]["submodules"],
            "Source submodule state differs from accepted preflight",
        )
        require(
            rows["untracked"].splitlines() == expected[root]["untracked"],
            "FI untracked closure changed",
        )
        for path, desc in expected[root]["generated_files"].items():
            require(descriptor(path) == desc, "FI generated license changed")
        sources[root] = rows
    packages = capture(
        [cfg["runtime"]["python"], "-B", "-m", "pip", "freeze", "--all"],
        env,
        timeout=120,
    )
    require(packages["returncode"] == 0, "Installed distribution snapshot failed")
    return {"sources": sources, "pip_freeze": packages["stdout"].splitlines()}


def rehash_bindings(bindings):
    require(isinstance(bindings, dict) and bindings, "Empty binding map")
    for path, expected in bindings.items():
        bound({"path": path, **expected})
    return bindings


def validate_marker(campaign_path, planned, marker_path, marker_sha256):
    require(
        marker_path is not None and marker_sha256 is not None,
        "Explicit approval marker and SHA256 required",
    )
    marker_path = plain_path(marker_path)
    require(
        descriptor(marker_path)["sha256"] == marker_sha256,
        "Approval marker SHA mismatch",
    )
    marker = read_json(marker_path)
    require(
        marker["schema_version"] == 1
        and marker["status"] == "ACCEPTED_KIMI_RUNTIME_PREFLIGHT",
        "Approval marker status",
    )
    require(
        bound(marker["campaign"]) == Path(campaign_path).resolve(),
        "Approval campaign path",
    )
    require(marker["campaign"] == planned["campaign"], "Approval campaign bytes")
    accepted_plan = read_json(bound(marker["plan"]))
    require(accepted_plan == planned, "Exact approved plan differs")
    require(not planned["execution_blockers"], "Campaign execution blockers remain")
    require(
        marker["runtime_project_root"] == planned["runtime_project_root"] == str(ROOT),
        "Runtime project differs",
    )
    cfg = read_json(campaign_path)
    ck = read_json(bound(marker["checkpoint_acceptance"]))
    require(
        {k: marker["checkpoint_acceptance"][k] for k in ("bytes", "sha256")}
        == {k: cfg["checkpoint"]["acceptance"][k] for k in ("bytes", "sha256")},
        "Checkpoint acceptance pin differs",
    )
    require(
        ck["status"] == "ACCEPTED_CUSTOM_ROUTED_NVFP4"
        and ck.get("data_kind") == "actual"
        and ck["output_path"] == cfg["runtime"]["model_path"],
        "Checkpoint acceptance identity",
    )
    request = read_json(bound(marker["preflight_request"]))
    source_contract.check_campaign(cfg)
    require(request["source_patch"] == source_contract.PATCH, "Preflight patch differs")
    require(
        request["remote_project"] == str(ROOT)
        and request["run_root"] == cfg["runtime"]["run_root"],
        "Preflight project/run mismatch",
    )
    require(
        request["sglang_root"] == cfg["runtime"]["sglang_root"]
        and request["flashinfer_source_root"] == cfg["runtime"]["flashinfer_root"],
        "Preflight source roots differ",
    )
    require(
        request["checkpoint"]["path"] == cfg["runtime"]["model_path"]
        and request["checkpoint"]["acceptance_sha256"]
        == marker["checkpoint_acceptance"]["sha256"],
        "Preflight checkpoint differs",
    )
    require(request["port"] == 30000, "Preflight endpoint mismatch")
    require(
        set(marker["preflight_receipts"]) == set(ARM_CONTRACT),
        "Three preflight arm receipts required",
    )
    for arm, desc in marker["preflight_receipts"].items():
        receipt = read_json(bound(desc))
        require(
            receipt["status"] == "KIMI_RUNTIME_PREFLIGHT_PASSED_PENDING_ROOT_REVIEW"
            and receipt["arm"] == arm,
            "Preflight receipt failed/wrong arm",
        )
        require(
            receipt.get("error") is None
            and receipt["node_expected_external_api_guard"] == request["node"],
            "Preflight node/failure join",
        )
        require(
            receipt["python_executable"] == cfg["runtime"]["python"],
            "Preflight Python differs",
        )
        require(
            receipt["request_sha256"] == marker["preflight_request"]["sha256"],
            "Preflight request join",
        )
    for arm in ARM_CONTRACT:
        first = next(case for case in planned["cases"] if case["arm_id"] == arm)
        require(
            request["server_args"][arm] == first["server_argv"][4:],
            "Preflight C32 server argv differs",
        )
    extra = marker["environment_passthrough"]
    require(
        type(extra) is dict
        and set(extra) <= PASSTHROUGH
        and all(isinstance(v, str) and "\0" not in v for v in extra.values()),
        "Unreviewed environment passthrough",
    )
    require(
        "SGLANG_RUST_BUILD_MODE" not in extra
        or extra["SGLANG_RUST_BUILD_MODE"] == "never",
        "Rust policy",
    )
    for key, value in extra.items():
        require(os.environ.get(key) == value, "Image environment changed: " + key)
    require(
        marker["continuation"] == cfg["continuation"], "Approval continuation differs"
    )
    for desc in (
        cfg["continuation"]["prior_acceptance"],
        cfg["continuation"]["cache_seed_acceptance"],
    ):
        bound(desc)
        require(
            marker["bindings"].get(desc["path"])
            == {k: desc[k] for k in ("bytes", "sha256")},
            "Approval parent/seed binding missing",
        )
    bindings = marker["bindings"]
    rehash_bindings(bindings)
    required = {
        str(p)
        for p in (
            Path(campaign_path).resolve(),
            Path(marker["plan"]["path"]),
            Path(marker["preflight_request"]["path"]),
            Path(marker["checkpoint_acceptance"]["path"]),
        )
    }
    required |= set(planned["bindings"])
    required |= {
        str(ROOT / "setup" / n)
        for n in (
            "execution.py",
            "results.py",
            "preflight.py",
            "source_contract.py",
            "continuation.py",
            "cache_seed.py",
        )
    }
    required |= {d["path"] for d in marker["preflight_receipts"].values()}
    require(required <= bindings.keys(), "Approval binding closure incomplete")
    for desc in (
        marker["campaign"],
        marker["plan"],
        marker["preflight_request"],
        marker["checkpoint_acceptance"],
        *marker["preflight_receipts"].values(),
    ):
        require(
            bindings[desc["path"]] == {k: desc[k] for k in ("bytes", "sha256")},
            "Descriptor/binding disagreement",
        )
    for group in (
        planned["bindings"],
        request["bound_files"],
        request["protected_runtime_files"],
    ):
        require(
            all(bindings.get(k) == v for k, v in group.items()),
            "Preflight source/native binding closure",
        )
    require(
        sys.platform == "linux" and socket.gethostname() == request["node"]["hostname"],
        "Execution host differs",
    )
    require(
        sys.executable == cfg["runtime"]["python"],
        "Lexical Python differs; do not resolve venv executable",
    )
    for path in (cfg["runtime"]["run_root"], cfg["runtime"]["tmp_root"]):
        plain_path(path, absent=True)
    require(
        not Path(cfg["runtime"]["run_root"]).is_relative_to(
            Path(cfg["runtime"]["model_path"])
        ),
        "Run may not be inside checkpoint",
    )
    return marker, request, cfg


def child_environment(case, marker):
    require(
        not (set(case["environment"]) & set(marker["environment_passthrough"])),
        "Overlay replaces planned environment",
    )
    return {**case["environment"], **marker["environment_passthrough"]}


def fresh_guard(marker, request, env, *, idle=True):
    require(socket.gethostname() == request["node"]["hostname"], "Host changed")
    rehash_bindings(marker["bindings"])
    checkpoint = checkpoint_snapshot(request)
    gpu = gpu_snapshot(env)
    require_gpu(gpu, request["gpus"], idle=idle)
    return {
        "at": now(),
        "gpu": gpu,
        "checkpoint": checkpoint,
        "bound_files": marker["bindings"],
        "node": request["node"],
    }


def tmp_scope(path, root):
    path = plain_path(path, absent=True)
    require(
        path.parent == Path("/tmp")
        and path.name.startswith("infx-")
        and len(os.fsencode(path)) < 30,
        "Short exclusive TMP required",
    )
    path.mkdir(mode=0o700)
    receipt = {
        "at": now(),
        "run_root": str(root),
        "tmp_root": str(path),
        "worker": process_row(os.getpid()),
        "probes": [],
        "error": None,
    }
    save(path / ".inferencex-owner.json", receipt)
    try:
        for prefix, leaf, kind in (
            (f"cuda_fd_xchg_{os.getpid()}_7_", "fd.sock", socket.SOCK_STREAM),
            (f"cuda_fd_bcast_{os.getpid()}_7_", "fd.sock", socket.SOCK_STREAM),
            ("flashinfer_mixed_comm_", "rank_7", socket.SOCK_DGRAM),
        ):
            directory = Path(tempfile.mkdtemp(prefix=prefix, dir=path))
            ident = directory.stat()
            target = directory / leaf
            maxpath = (
                path
                / (
                    prefix.replace(str(os.getpid()), "2147483647", 1)
                    + directory.name[len(prefix) :]
                )
                / leaf
            )
            require(len(os.fsencode(maxpath)) + 1 <= 108, "AF_UNIX pathname budget")
            with socket.socket(socket.AF_UNIX, kind) as sock:
                sock.bind(str(target))
                st = target.lstat()
            require(
                stat.S_ISSOCK(target.lstat().st_mode)
                and target.lstat().st_ino == st.st_ino,
                "Probe socket changed",
            )
            target.unlink()
            require(directory.stat().st_ino == ident.st_ino, "Probe directory changed")
            directory.rmdir()
            receipt["probes"].append(
                {
                    "path": str(target),
                    "type": int(kind),
                    "bound": True,
                    "max_pid_path_bytes_with_nul": len(os.fsencode(maxpath)) + 1,
                }
            )
    except BaseException as exc:
        receipt["error"] = repr(exc)
        raise
    finally:
        save(root / "tmp-preflight.json", receipt)


def cache_snapshot(root, destination):
    rows = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            p = Path(directory) / name
            st = p.lstat()
            row = {"bytes": st.st_size, "mtime_ns": st.st_mtime_ns}
            if stat.S_ISLNK(st.st_mode):
                row.update(kind="symlink", link_text=os.readlink(p))
            elif stat.S_ISDIR(st.st_mode):
                row["kind"] = "directory"
            elif stat.S_ISREG(st.st_mode):
                row["kind"] = "file"
                if p.is_relative_to(root / "tactics"):
                    desc = descriptor(p)
                    row.update(desc)
                    copy = (
                        destination.parent
                        / (destination.stem + "-tactics")
                        / p.relative_to(root / "tactics")
                    )
                    copy.parent.mkdir(parents=True, exist_ok=True)
                    with p.open("rb") as source, copy.open("xb") as target:
                        shutil.copyfileobj(source, target, 1024 * 1024)
                    require(
                        descriptor(copy) == desc == descriptor(p), "Tactic copy changed"
                    )
            else:
                raise RuntimeError("Unsupported cache entry: " + str(p))
            rows[str(p.relative_to(root))] = row
    save(
        destination,
        {
            "at": now(),
            "root": str(root),
            "files": rows,
            "compile_payloads_hashed": False,
            "tactic_payloads_hashed": True,
        },
    )


def request_lengths(model, count, destination):
    """Execution-only child: same pinned sampler/tokenizer, no requests sent."""
    import random
    import numpy as np
    from infx.bench_serving import benchmark_serving as client

    require(
        Path(client.__file__).resolve()
        == ROOT / "vendor/inferencex/infx/bench_serving/benchmark_serving.py",
        "Sampler source origin",
    )
    random.seed(0)
    np.random.seed(0)
    tokenizer = client._load_tokenizer(
        model, tokenizer_mode="auto", trust_remote_code=True
    )
    requests = client.sample_random_requests(
        prefix_len=0,
        input_len=1024,
        output_len=8192,
        num_prompts=count,
        range_ratio=0.8,
        tokenizer=tokenizer,
        use_chat_template=True,
        dsv4=False,
        tokenizer_id=model,
        tokenizer_mode="auto",
        trust_remote_code=True,
        num_workers=0,
    )
    save(
        destination,
        {
            "seed": 0,
            "nominal_input": 1024,
            "nominal_output": 8192,
            "ratio": 0.8,
            "num_prompts": count,
            "model_path": model,
            "trust_remote_code": True,
            "client_source": descriptor(Path(client.__file__)),
            "input_lens": [r[1] for r in requests],
            "output_lens": [r[2] for r in requests],
            "scope": "deterministic sampler, not server output",
        },
    )


def endpoint_owned(owner, port=30000):
    owner.discover()
    inodes = set()
    for table in ("/proc/net/tcp", "/proc/net/tcp6"):
        for line in Path(table).read_text().splitlines()[1:]:
            fields = line.split()
            if int(fields[1].split(":")[1], 16) == port and fields[3] == "0A":
                inodes.add(fields[9])
    require(bool(inodes), "No listening endpoint")
    joined = []
    for row in owner.alive():
        for fd in Path(f"/proc/{row['pid']}/fd").iterdir():
            try:
                link = os.readlink(fd)
            except (FileNotFoundError, ProcessLookupError):
                continue
            if link.startswith("socket:[") and link[8:-1] in inodes:
                require(
                    same_birth(process_row(row["pid"]), row),
                    "Endpoint owner birth changed",
                )
                joined.append({"owner": row, "inode": link[8:-1]})
    require(
        inodes <= {j["inode"] for j in joined},
        "Listening endpoint is not exclusively owned",
    )
    return joined


def http_open(path, timeout):
    # Never route the fixed local control endpoint through inherited proxies.
    return build_opener(ProxyHandler({})).open(
        "http://127.0.0.1:30000/" + path, timeout=timeout
    )


def server_info(case, owner):
    joins = endpoint_owned(owner)
    with http_open("get_server_info", timeout=10) as response:
        info = json.load(response)
    require(owner.running(), "Owned server exited during readback")
    endpoint_owned(owner)
    for key, expected in case["expected_server_info"].items():
        require(
            info.get(key) == expected,
            f"Resolved server setting differs: {key}: {info.get(key)!r} != {expected!r}",
        )
    states = info.get("internal_states")
    require(
        isinstance(states, list)
        and len(states) == case["expected_server_info"]["dp_size"],
        "One internal state per expected DP rank required",
    )
    for item in states:
        require(
            item["effective_max_running_requests_per_dp"]
            == case["effective_per_dp_request_capacity"],
            "Local DP capacity mismatch",
        )
        require(item["speculative_algorithm"] is None, "Unexpected speculation")
    return info, joins


def wait_child(child, timeout, tick, server=None):
    deadline = time.monotonic() + timeout
    while True:
        tick()
        child.discover()
        if not child.running():
            # The direct child is still unreaped: capture late same-session
            # descendants before wait() removes its /proc birth identity.
            child.discover()
            require(
                child.process.wait() == 0,
                f"{child.role} exited {child.process.returncode}",
            )
            return
        if server is not None:
            require(server.running(), "Server died during client phase")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"{child.role} deadline exceeded")
        time.sleep(0.5)


def seal_case(directory, root, case_id):
    files = []
    for path in sorted(directory.rglob("*")):
        require(not path.is_symlink(), "Linked case evidence")
        if path.is_file():
            require(path.name != "manifest.json", "Case already sealed")
            files.append({"path": str(path.relative_to(root)), **descriptor(path)})
    save(
        directory / "manifest.json",
        {"case_id": case_id, "sealed_at": now(), "files": files},
    )


def wait_plain_bind(log_path, *, port=30000, timeout=120.0, interval=1.0):
    """Bounded plain bind checks only; never sets SO_REUSEADDR or ignores other errors."""
    require(0 < timeout <= 120 and 0 < interval <= 1, "Port wait bounds")
    started = time.monotonic()
    deadline = started + timeout
    attempts = 0
    while True:
        attempts += 1
        try:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", port))
        except OSError as exc:
            append(
                log_path,
                {
                    "at": now(),
                    "attempt": attempts,
                    "status": "bind-error",
                    "elapsed_seconds": time.monotonic() - started,
                    "errno": exc.errno,
                    "error": repr(exc),
                },
            )
            if exc.errno != errno.EADDRINUSE:
                raise
            remaining = deadline - time.monotonic()
            if remaining <= 0 or attempts >= 121:
                raise TimeoutError(
                    "Plain bind remained occupied after bounded EADDRINUSE wait"
                ) from exc
            time.sleep(min(interval, remaining))
        else:
            append(
                log_path,
                {
                    "at": now(),
                    "attempt": attempts,
                    "status": "bind-available",
                    "elapsed_seconds": time.monotonic() - started,
                    "errno": None,
                },
            )
            return


def run_case(case, cfg, marker, request, references, baseline):
    from results import verify_result

    root = Path(cfg["runtime"]["run_root"])
    directory = Path(case["case_dir"])
    require(directory == root / "cases" / case["case_id"], "Case directory mismatch")
    directory.mkdir(mode=0o700)
    env = child_environment(case, marker)
    processes, server, last_gpu = [], None, 0.0
    status = {
        "case_id": case["case_id"],
        "started_at": now(),
        "status": "running",
        "error": None,
        "cleanup_errors": [],
        "remaining_owners": [],
    }
    save(directory / "settings.json", {"case": case, "environment": env, "config": cfg})
    for role, argv in (
        ("server", case["server_argv"]),
        ("benchmark", case["client_argv"]),
    ):
        save(
            directory / f"{role}_command.json",
            {"argv": argv, "environment": env, "cwd": str(ROOT)},
        )

    def tick():
        nonlocal last_gpu
        for child in processes:
            child.discover()
        if time.monotonic() - last_gpu >= 5:
            gpu = gpu_snapshot(env)
            require_gpu(gpu, request["gpus"], idle=False)
            append(directory / "gpu.jsonl", gpu)
            last_gpu = time.monotonic()

    try:
        before = fresh_guard(marker, request, env)
        require(
            runtime_snapshot(cfg, env, marker) == baseline,
            "Installed/source state changed before case",
        )
        save(directory / "source.before.json", before)
        save(directory / "gpu.before.json", before["gpu"])
        wait_plain_bind(directory / "port-preflight.jsonl")
        after_port = fresh_guard(marker, request, env)
        require(
            runtime_snapshot(cfg, env, marker) == baseline,
            "Installed/source state changed during port wait",
        )
        save(directory / "source.after-port.json", after_port)
        cache_snapshot(root / "caches", directory / "cache.before.json")
        command = [
            cfg["runtime"]["python"],
            "-B",
            str(ROOT / "setup/execution.py"),
            "--request-lengths",
            cfg["runtime"]["model_path"],
            str(case["measured_requests"]),
            str(directory / "requested-lengths.json"),
        ]
        sampler = OwnedProcess(command, env, directory, "request-plan", ROOT)
        processes.append(sampler)
        wait_child(sampler, cfg["runtime"]["ready_timeout_seconds"], tick)
        sampled = sampler.cleanup(
            cfg["runtime"]["term_seconds"], cfg["runtime"]["kill_seconds"]
        )
        require(
            not sampled["errors"] and not sampled["remaining"], "Sampler cleanup failed"
        )
        processes.remove(sampler)
        server = OwnedProcess(case["server_argv"], env, directory, "server", ROOT)
        processes.append(server)
        deadline = time.monotonic() + cfg["runtime"]["ready_timeout_seconds"]
        while True:
            tick()
            require(server.running(), "Server exited before readiness")
            try:
                with http_open("health", timeout=2) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError):
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError("Server readiness deadline exceeded")
            time.sleep(1)
        info, joins = server_info(case, server)
        save(directory / "server_info.before.json", info)
        save(directory / "endpoint-owner.before.json", joins)
        client = OwnedProcess(case["client_argv"], env, directory, "benchmark", ROOT)
        processes.append(client)
        wait_child(client, cfg["runtime"]["benchmark_timeout_seconds"], tick, server)
        info, joins = server_info(case, server)
        save(directory / "server_info.after.json", info)
        save(directory / "endpoint-owner.after.json", joins)
        result, requested = (
            read_json(directory / "result.json"),
            read_json(directory / "requested-lengths.json"),
        )
        metrics = verify_result(result, requested, case)
        log = (directory / "benchmark.log").read_text()
        namespaces = [
            line for line in log.splitlines() if line.startswith("Namespace(")
        ]
        require(
            len(namespaces) == 1
            and re.search(r"(?:\(|, )seed=0(?:,|\))", namespaces[0]),
            "Client seed Namespace",
        )
        warmup = f"Warming up with {case['warmup_requests']} requests..."
        require(
            log.count(warmup) == log.count("Warmup completed.") == 1
            and log.index(warmup) < log.index("Warmup completed."),
            "Client warmup not completed exactly once",
        )
        arrays = {k: requested[k] for k in ("input_lens", "output_lens")}
        require(
            case["concurrency"] not in references
            or references[case["concurrency"]] == arrays,
            "Cross-arm ordered request lengths changed",
        )
        references[case["concurrency"]] = arrays
        save(
            directory / "metrics.json",
            {
                "derived": metrics,
                "definition": "complete measured interval output/GPU; TPOT-derived interactivity; ITL is chunk spacing",
            },
        )
        status["status"] = "completed"
    except BaseException as exc:
        status.update(
            status="failed", error=repr(exc), traceback=traceback.format_exc()
        )
    finally:
        handlers = {
            sig: signal.signal(sig, signal.SIG_IGN)
            for sig in (signal.SIGINT, signal.SIGTERM)
        }
        try:
            status["cleanup"] = {}
            for child in reversed(processes):
                try:
                    cleanup = child.cleanup(
                        cfg["runtime"]["term_seconds"], cfg["runtime"]["kill_seconds"]
                    )
                    status["cleanup"][child.role] = cleanup
                    status["cleanup_errors"].extend(cleanup["errors"])
                    status["remaining_owners"].extend(cleanup["remaining"])
                except BaseException as exc:
                    status["cleanup_errors"].append(repr(exc))
            if status["cleanup_errors"] or status["remaining_owners"]:
                status["status"] = "failed"
            try:
                deadline = time.monotonic() + cfg["runtime"]["kill_seconds"]
                while True:
                    gpu = gpu_snapshot(env)
                    append(directory / "gpu.cleanup.jsonl", gpu)
                    require_gpu(gpu, request["gpus"], idle=False)
                    try:
                        require_gpu(gpu, request["gpus"], idle=True)
                    except ValueError:
                        if time.monotonic() >= deadline:
                            raise
                    else:
                        save(directory / "gpu.after.json", gpu)
                        break
                    time.sleep(1)
                after = fresh_guard(marker, request, env)
                require(
                    runtime_snapshot(cfg, env, marker) == baseline,
                    "Installed/source state changed after case",
                )
                save(directory / "source.after.json", after)
                if status["status"] == "completed":
                    cache_snapshot(root / "caches", directory / "cache.after.json")
                else:
                    save(
                        directory / "cache.after-skipped.json",
                        {
                            "reason": "Failed case; no cache scan after uncertain teardown"
                        },
                    )
            except BaseException as exc:
                status.update(status="failed", postflight_error=repr(exc))
            status["finished_at"] = now()
            save(directory / "exit.json", status)
            seal_case(directory, root, case["case_id"])
        finally:
            for sig, handler in handlers.items():
                signal.signal(sig, handler)
    require(status["status"] == "completed", f"Case failed; retained {directory}")
    return status


def execute(campaign_path, planned, marker_path, marker_sha256):
    require(__debug__, "Optimized execution is not supported")
    marker, request, cfg = validate_marker(
        campaign_path, planned, marker_path, marker_sha256
    )
    execution_cases = continuation.selected_cases(planned)
    require(
        marker["continuation"] == cfg["continuation"], "Approved continuation differs"
    )
    prior_data = continuation.verify_prior(
        cfg, planned, lambda item: read_json(bound(item))
    )
    seed = cache_seed.validate_seed(
        cfg,
        cfg["continuation"]["prior_acceptance"],
        cfg["continuation"]["cache_seed_acceptance"],
    )
    env = child_environment(execution_cases[0], marker)
    marker["bindings"] = {
        **marker["bindings"],
        str(Path(marker_path)): descriptor(marker_path),
    }
    initial = fresh_guard(marker, request, env)
    root = plain_path(cfg["runtime"]["run_root"], absent=True)
    plain_path(cfg["runtime"]["tmp_root"], absent=True)
    os.umask(0o077)
    root.mkdir(mode=0o700)
    status = {
        "started_at": now(),
        "worker": process_row(os.getpid()),
        "completed_case_ids": [],
        "execution_case_ids": cfg["continuation"]["execution_case_ids"],
        "execution_totals": cfg["continuation"]["execution_totals"],
        "prior_case_id": cfg["continuation"]["prior_case_id"],
        "prior_acceptance": cfg["continuation"]["prior_acceptance"],
        "cache_seed_acceptance": cfg["continuation"]["cache_seed_acceptance"],
        "error": None,
        "cleanup_errors": [],
        "remaining_owners": [],
    }
    save(root / "worker-start.json", status)
    for name, path in (
        ("config.json", campaign_path),
        ("PLAN.json", marker["plan"]["path"]),
        ("approval.json", marker_path),
        ("checkpoint-acceptance.json", marker["checkpoint_acceptance"]["path"]),
    ):
        save_bytes(root / name, Path(path).read_bytes())
    save(root / "source.initial.json", initial)
    save(root / "matrix.json", planned["cases"])
    save(root / "execution-matrix.json", execution_cases)
    save(root / "prior-c32.json", prior_data)
    prior = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}

    def stop(sig, _frame):
        raise InterruptedError(f"Received signal {sig}")

    for sig in prior:
        signal.signal(sig, stop)
    try:
        wait_plain_bind(root / "port-preflight.jsonl")
        save(root / "port-ready.guard.json", fresh_guard(marker, request, env))
        port_ready_runtime = runtime_snapshot(cfg, env, marker)
        for name in ("cases", "caches", "hf-home"):
            (root / name).mkdir(mode=0o700)
        tmp_scope(cfg["runtime"]["tmp_root"], root)
        cache_receipt = cache_seed.install_seed(
            seed, root, Path(cfg["runtime"]["tmp_root"])
        )
        save(root / "compile-cache-seed.json", cache_receipt)
        for case in planned["cases"]:
            for value in case["environment"].values():
                if value.startswith(str(root / "caches") + "/"):
                    require(
                        plain_path(value).is_dir(),
                        "Seed omitted planned cache namespace",
                    )
        baseline = runtime_snapshot(cfg, env, marker)
        require(
            baseline == port_ready_runtime,
            "Installed/source state changed during seed restoration",
        )
        save(root / "runtime.initial.json", baseline)
        references = {32: prior_data["reference_arrays"]}
        for case in execution_cases:
            run_case(case, cfg, marker, request, references, baseline)
            status["completed_case_ids"].append(case["case_id"])
            save(root / "progress.json", status, replace=True)
        save(root / "source.final.json", fresh_guard(marker, request, env))
        final_runtime = runtime_snapshot(cfg, env, marker)
        require(final_runtime == baseline, "Final runtime/source state changed")
        save(root / "runtime.final.json", final_runtime)
    except BaseException as exc:
        status.update(error=repr(exc), traceback=traceback.format_exc())
        if "case" in locals() and (Path(case["case_dir"]) / "exit.json").is_file():
            failed = read_json(Path(case["case_dir"]) / "exit.json")
            status["cleanup_errors"] = failed["cleanup_errors"]
            status["remaining_owners"] = failed["remaining_owners"]
    finally:
        status.update(
            finished_at=now(),
            status="completed"
            if status["error"] is None
            and status["completed_case_ids"]
            == cfg["continuation"]["execution_case_ids"]
            else "failed",
        )
        status["exit_code"] = 0 if status["status"] == "completed" else 1
        status["outer_waited_exit_required"] = True
        save(root / "worker-exit.json", status)
        for sig, handler in prior.items():
            signal.signal(sig, handler)
    return status["exit_code"]


if __name__ == "__main__":
    require(__debug__, "Optimized execution is not supported")
    if len(sys.argv) == 5 and sys.argv[1] == "--request-lengths":
        request_lengths(sys.argv[2], int(sys.argv[3]), Path(sys.argv[4]))
    else:
        raise SystemExit("Use run_campaign.py --execute with a pinned accepted marker")
