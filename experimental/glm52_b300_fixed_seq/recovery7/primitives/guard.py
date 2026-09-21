"""D6 nvdiag guard: actual hu48 bootstrap receipts; inherited native/cleanup guards.
No function is executed at import. Final actual gates are owned by run_diagnostic.
"""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
ROOT=Path('/data/home/ziangli/inferencex-glm52-nvdiag-20260921')

def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def regular(path, expected=None, limit=32 * 1024 * 1024):
    path = Path(path)
    need(
        path.is_file() and not path.is_symlink() and path.stat().st_size <= limit,
        f"Not bounded regular file: {path}",
    )
    data = path.read_bytes()
    need(
        expected is None or hashlib.sha256(data).hexdigest() == expected,
        f"Bytes changed: {path}",
    )
    return data


def write(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def command(argv):
    result = subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=90,
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", PYTHONDONTWRITEBYTECODE="1"),
    )
    return result.stdout


def idle(lock):
    need(socket.gethostname() == lock["node"]["hostname"], "Wrong physical host")
    apps = command(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name,used_memory",
            "--format=csv,noheader,nounits",
        ]
    )
    need(not apps.strip(), "GPU applications present")
    gpu = command(
        [
            "nvidia-smi",
            "--query-gpu=index,uuid,name,driver_version,memory.used,utilization.gpu",
            "--format=csv,noheader,nounits",
        ]
    )
    rows = [[v.strip() for v in line.split(",")] for line in gpu.splitlines()]
    need(
        len(rows) == 8 and {r[0] for r in rows} == {str(i) for i in range(8)},
        "Expected eight GPUs",
    )
    need({r[1] for r in rows} == set(lock["gpu_uuids"]), "GPU identities changed")
    need(
        all(
            r[2] == "NVIDIA B300 SXM6 AC"
            and r[3] == "590.48.01"
            and int(r[4]) == int(r[5]) == 0
            for r in rows
        ),
        "Expected eight idle reviewed B300s",
    )
    active = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit() or int(p.name) == os.getpid():
            continue
        try:
            value = (
                (p / "cmdline")
                .read_bytes()
                .replace(b"\0", b" ")
                .decode(errors="replace")
            )
        except (FileNotFoundError, ProcessLookupError):
            continue
        if any(s in value for s in ("sglang.launch_server", "benchmark_serving")) or (
            str(ROOT) in value and any(s in value for s in (" worker", " archive"))
        ):
            active.append({"pid": int(p.name), "command": value})
    need(not active, "Serving/benchmark/archival process still active")
    return {
        "time": datetime.now(timezone.utc).isoformat(),
        "gpu": gpu,
        "apps": apps,
        "active": active,
    }


def bootstrap_receipt_gate(lock):
    # Exact collected 189 small files, including both nested seals and waited launch.
    for path, expected in lock["bootstrap_receipts"].items():
        data = regular(path, expected["sha256"], 2 * 1024**2)
        need(len(data) == expected["bytes"], "Bootstrap receipt size changed")
    env = ROOT / "environment/bootstrap"
    setup = json.loads(regular(ROOT / "environment/setup-completed.json"))
    need(setup["status"] == "prepared_no_diagnostic"
         and setup["sglang_commit"] == lock["source_pins"]["sglang"]
         and setup["flashinfer_commit"] == lock["source_pins"]["flashinfer"], "Wrong prepared setup")
    completed = json.loads(regular(env / "bootstrap-completed.json"))
    need(completed["status"] == "bootstrap_complete_no_diagnostic"
         and completed["task_root"] == str(ROOT)
         and completed["benchmark_or_diagnostic_launched"] is False,
         "Wrong bootstrap provenance")
    exitrec = json.loads(regular(lock["bootstrap_stage"] + "/worker-exit.json"))
    child = json.loads(regular(lock["bootstrap_stage"] + "/child.json"))
    need(exitrec["waited_exit_code"] == 0 and exitrec.get("error") is None
         and exitrec.get("cleanup_errors") == [] and exitrec["child_pid"] == child["pid"]
         and exitrec["child_starttime"] == child["starttime"], "Bootstrap not cleanly waited")
    for pid in (exitrec["worker_pid"], child["pid"]):
        need(type(pid) is int and pid > 1 and not Path(f"/proc/{pid}").exists(), "Bootstrap owner present/reused")
    return {"bootstrap_worker_exit": exitrec, "source_archives": lock["deferred_source_archives"]}


def guards(lock):
    need(
        sys.prefix == "/opt/sglang" and sys.version_info[:2] == (3, 12),
        "Wrong Python runtime",
    )
    evidence = {"idle": idle(lock)}
    evidence.update(bootstrap_receipt_gate(lock))
    env = ROOT / "environment/bootstrap"
    for name, pin in lock["source_pins"].items():
        source = ROOT / "sources" / name
        need(
            command(["git", "-C", str(source), "rev-parse", "HEAD"]).strip() == pin,
            f"{name} source HEAD changed",
        )
        need(
            not command(
                [
                    "git",
                    "-C",
                    str(source),
                    "status",
                    "--porcelain",
                    "--untracked-files=no",
                ]
            ).strip(),
            f"{name} tracked tree dirty",
        )
    # Version checks do not import a provider or initialize CUDA.
    for name, version in lock["provider_versions"].items():
        need(
            importlib.metadata.version(name) == version,
            f"Provider version changed: {name}",
        )
    for record in lock["provider_files"]:
        p = Path(record["path"])
        need(
            str(p.resolve(strict=True)) == record["resolved"]
            and p.resolve().is_relative_to("/opt/sglang/lib/python3.12/site-packages"),
            "Provider target moved",
        )
        need(
            p.stat().st_size == record["bytes"] and sha(p) == record["sha256"],
            f"Provider bytes changed: {p}",
        )
    freeze = command([sys.executable, "-I", "-B", "-m", "pip", "freeze"]).strip()
    need(
        hashlib.sha256(freeze.encode()).hexdigest() == lock["freeze_stripped_sha256"],
        "Full freeze changed",
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 30000))
    dependencies = json.loads((env / "flashinfer-dependencies.json").read_text())
    for relative, pin in dependencies.items():
        source = ROOT / "sources/flashinfer" / relative
        need(
            command(["git", "-C", str(source), "rev-parse", "HEAD"]).strip() == pin,
            "Dependency pin changed",
        )
        need(
            not command(
                [
                    "git",
                    "-C",
                    str(source),
                    "status",
                    "--porcelain",
                    "--untracked-files=no",
                ]
            ).strip(),
            "Dependency tree dirty",
        )
    layout = json.loads((env / "flashinfer-resource-layout.json").read_text())
    regular(layout["build_meta"]["path"], layout["build_meta"]["sha256"])
    for name, record in layout["links"].items():
        link = ROOT / "sources/flashinfer/flashinfer/data" / name
        need(
            link.is_symlink() and str(link.resolve(strict=True)) == record["target"],
            "FI resource link changed",
        )
        for relative, payload in record["sentinels"].items():
            regular(link / relative, payload["sha256"])
    evidence["freeze_stripped_sha256"] = lock["freeze_stripped_sha256"]
    return evidence


def cleanup(proc, birth, known):
    import psutil

    def live_owned():
        children = []
        for pid, created in known.items():
            try:
                child = psutil.Process(pid)
                if child.create_time() == created and child.status() != psutil.STATUS_ZOMBIE:
                    children.append(child)
            except psutil.NoSuchProcess:
                pass
        return children

    for sig in (signal.SIGTERM, signal.SIGKILL):
        group_owned = False
        try:
            leader = psutil.Process(proc.pid)
            if birth is not None and leader.create_time() == birth:
                group_owned = os.getpgid(proc.pid) == proc.pid
        except (psutil.NoSuchProcess, ProcessLookupError):
            pass
        children = live_owned()
        for child in children:
            try:
                # A known same-birth member still in this group proves group
                # ownership even after its original leader exited. A reused
                # group with no such member must never receive killpg.
                if os.getpgid(child.pid) == proc.pid:
                    group_owned = True
            except ProcessLookupError:
                pass
        if group_owned:
            try:
                os.killpg(proc.pid, sig)
            except ProcessLookupError:
                pass
        for pid, created in known.items():
            try:
                child = psutil.Process(pid)
                if (
                    child.create_time() == created
                    and child.status() != psutil.STATUS_ZOMBIE
                ):
                    child.send_signal(sig)
            except psutil.NoSuchProcess:
                pass
        try:
            proc.wait(timeout=8 if sig == signal.SIGTERM else 5)
        except subprocess.TimeoutExpired:
            pass
        time.sleep(0.2)
    remaining = []
    for pid, created in known.items():
        try:
            child = psutil.Process(pid)
            if (
                child.create_time() == created
                and child.status() != psutil.STATUS_ZOMBIE
            ):
                remaining.append(pid)
        except psutil.NoSuchProcess:
            pass
    need(not remaining, f"Owned children remain: {remaining}")
    return {
        "leader_returncode": proc.poll(),
        "owned_descendants": known,
        "remaining": remaining,
    }

