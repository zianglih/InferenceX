#!/usr/bin/env python3
"""One serial, fail-stop GLM-5.2 MegaMoE campaign; no installation or remote APIs."""

from __future__ import annotations

import argparse
import hashlib
import json
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
from urllib.error import URLError
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PRECISIONS = ("w4a4", "w4a16")
TOPOLOGIES = (4, 8)
CONCURRENCIES = (128, 4, 8, 16, 32, 64)
CONFIG_KEYS = {
    "run_id",
    "run_root",
    "tmp_root",
    "compile_cache_seed",
    "python",
    "sglang_root",
    "sglang_commit",
    "flashinfer_root",
    "flashinfer_commit",
    "model_path",
    "model_revision",
    "served_model",
    "image",
    "gpu_ids",
    "port",
    "ready_timeout_seconds",
    "benchmark_timeout_seconds",
    "term_seconds",
    "kill_seconds",
    "monitor_interval_seconds",
    "base_environment",
}


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def digest(path: Path) -> dict:
    h = hashlib.sha256()
    before = path.stat()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise RuntimeError(f"File changed while hashing: {path}")
    return {"bytes": after.st_size, "sha256": h.hexdigest()}


def save(path: Path, value: object) -> None:
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w") as f:
        json.dump(value, f, indent=2, sort_keys=True, allow_nan=False)
        f.write("\n")
    temp.replace(path)


def canonical_path(value: str) -> Path:
    p = Path(value)
    if not p.is_absolute() or ".." in p.parts or p == Path("/"):
        raise ValueError(f"Expected an absolute canonical path: {value}")
    return p


def read_config(path: Path) -> dict:
    cfg = json.loads(path.read_text())
    if set(cfg) != CONFIG_KEYS:
        raise ValueError(f"Config keys differ: {set(cfg) ^ CONFIG_KEYS}")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]+", cfg["run_id"]):
        raise ValueError("Invalid run_id")
    for key in ("sglang_commit", "flashinfer_commit", "model_revision"):
        if not re.fullmatch(r"[0-9a-f]{40}", cfg[key]):
            raise ValueError(f"{key} must be the full accepted SHA")
    for key in ("run_root", "python", "sglang_root", "flashinfer_root", "model_path"):
        canonical_path(cfg[key])
    root = Path(cfg["run_root"])
    if root.name != cfg["run_id"] or root.is_relative_to("/workspace"):
        raise ValueError("run_root must end in run_id and be outside /workspace")
    validate_tmp_root(cfg)
    validate_compile_seed(cfg)
    if not re.search(r"@sha256:[0-9a-f]{64}$", cfg["image"]):
        raise ValueError("Pin the image tag and digest")
    if len(cfg["gpu_ids"]) != 8 or len(set(cfg["gpu_ids"])) != 8:
        raise ValueError("Exactly eight distinct GPU IDs are required")
    if any(
        not re.fullmatch(r"(?:[0-9]+|GPU-[A-Za-z0-9-]+)", x) for x in cfg["gpu_ids"]
    ):
        raise ValueError("Invalid GPU ID")
    if type(cfg["port"]) is not int or not 1024 <= cfg["port"] <= 65535:
        raise ValueError("Invalid port")
    for key in (
        "ready_timeout_seconds",
        "benchmark_timeout_seconds",
        "term_seconds",
        "kill_seconds",
        "monitor_interval_seconds",
    ):
        if type(cfg[key]) is not int or cfg[key] <= 0:
            raise ValueError(f"{key} must be a positive integer")
    env = cfg["base_environment"]
    if not isinstance(env, dict) or not env.get("PATH"):
        raise ValueError("base_environment must explicitly contain PATH")
    for key, value in env.items():
        if not isinstance(value, str) or "\0" in value:
            raise ValueError(f"Invalid environment value: {key}")
        if key.startswith(("SGLANG_", "FLASHINFER_", "NVSHMEM_")) or key in (
            "PYTHONPATH",
            "LD_PRELOAD",
            "CUDA_VISIBLE_DEVICES",
        ):
            raise ValueError(
                f"Recipe owns {key}; do not inherit tuning or loader overrides"
            )
    return cfg


def matrix() -> list[dict]:
    return [
        {
            "precision": p,
            "tp": tp,
            "ep": tp,
            "dp": tp,
            "concurrency": c,
            "case_id": f"{p}-tp{tp}-ep{tp}-dp{tp}-c{c}",
            "warmup_requests": 2 * c,
            "measured_requests": 10 * c,
            "server_max_running_requests": max(c, tp),
        }
        for p in PRECISIONS
        for tp in TOPOLOGIES
        for c in CONCURRENCIES
    ]


def environment(cfg: dict, case: dict) -> dict[str, str]:
    root = Path(cfg["run_root"])
    compile_root = root / "caches" / "compile"
    tactics = root / "caches" / "tactics" / case["precision"] / f"tp{case['tp']}"
    env = dict(cfg["base_environment"])
    env.update(
        {
            "PATH": str(Path(cfg["python"]).parent) + os.pathsep + env["PATH"],
            "PYTHONPATH": os.pathsep.join((cfg["sglang_root"] + "/python", str(REPO))),
            "PYTHONNOUSERSITE": "1",
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "PYTHONPYCACHEPREFIX": str(root / "pycache"),
            "TMPDIR": cfg["tmp_root"],
            "HF_HOME": str(root / "hf-home"),
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "CUDA_VISIBLE_DEVICES": ",".join(cfg["gpu_ids"][: case["tp"]]),
            "SGLANG_ENABLE_JIT_DEEPGEMM": "1",
            "SGLANG_FLASHINFER_AUTOTUNE_CACHE": "1",
            "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16": str(
                int(case["precision"] == "w4a16")
            ),
            "SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION": "0",
            "SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE": "bf16",
            "SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE": "0",
            "NVSHMEM_REMOTE_TRANSPORT": "none",
            "NVSHMEM_IB_ENABLE_IBGDA": "0",
            "NVSHMEM_DISABLE_LOCAL_ONLY_PROXY": "1",
            "NVSHMEM_DEBUG": "INFO",
            "SGLANG_CACHE_DIR": str(tactics),
            "FLASHINFER_WORKSPACE_BASE": str(compile_root / "flashinfer"),
            "FLASHINFER_CUDA_ARCH_LIST": "10.3a",
            "MAX_JOBS": "16",
            "FLASHINFER_NVCC_THREADS": "2",
            "CUTE_DSL_CACHE_DIR": str(compile_root / "cute-dsl"),
            "CUTE_DSL_NO_CACHE": "0",
            "CUTE_DSL_DISABLE_FILE_CACHING": "0",
            "CUDA_CACHE_PATH": str(compile_root / "cuda"),
            "TORCH_EXTENSIONS_DIR": str(compile_root / "torch-extensions"),
            "TORCHINDUCTOR_CACHE_DIR": str(compile_root / "torchinductor"),
            "TRITON_CACHE_DIR": str(compile_root / "triton"),
            "TILELANG_CACHE_DIR": str(compile_root / "tilelang"),
            "SGLANG_DG_CACHE_DIR": str(compile_root / "deep-gemm"),
            "SGLANG_CUTE_AOT_CACHE_DIR": str(compile_root / "cute-aot"),
            "SGLANG_JIT_CACHE_DIR": str(compile_root / "sglang-jit"),
            "XDG_CACHE_HOME": str(compile_root / "xdg"),
        }
    )
    return env


def server_command(cfg: dict, case: dict) -> list[str]:
    return [
        cfg["python"],
        "-m",
        "sglang.launch_server",
        "--model-path",
        cfg["model_path"],
        "--served-model-name",
        cfg["served_model"],
        "--host",
        "127.0.0.1",
        "--port",
        str(cfg["port"]),
        "--trust-remote-code",
        "--dtype",
        "bfloat16",
        "--quantization",
        "modelopt_fp4",
        "--tensor-parallel-size",
        str(case["tp"]),
        "--data-parallel-size",
        str(case["dp"]),
        "--expert-parallel-size",
        str(case["ep"]),
        "--enable-dp-attention",
        "--tool-call-parser",
        "glm47",
        "--reasoning-parser",
        "glm45",
        "--kv-cache-dtype",
        "fp8_e4m3",
        "--attention-backend",
        "dsa",
        "--dsa-decode-backend",
        "trtllm",
        "--dsa-prefill-backend",
        "trtllm",
        "--moe-runner-backend",
        "flashinfer_megamoe",
        "--moe-a2a-backend",
        "flashinfer_megamoe",
        "--speculative-moe-runner-backend",
        "flashinfer_trtllm",
        "--speculative-moe-a2a-backend",
        "none",
        "--speculative-algorithm",
        "EAGLE",
        "--speculative-num-steps",
        "3",
        "--speculative-eagle-topk",
        "1",
        "--speculative-num-draft-tokens",
        "4",
        "--cuda-graph-max-bs-decode",
        str(case["concurrency"]),
        "--cuda-graph-backend-prefill",
        "disabled",
        "--mem-fraction-static",
        "0.80",
        "--chunked-prefill-size",
        "32768",
        "--max-prefill-tokens",
        "32768",
        "--max-running-requests",
        str(case["server_max_running_requests"]),
        "--flashinfer-allreduce-fusion-backend",
        "auto",
        "--disable-radix-cache",
        "--stream-interval",
        "30",
        "--model-loader-extra-config",
        '{"enable_multithread_load": true}',
    ]


def process_row(pid: int) -> dict | None:
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
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


class OwnedProcess:
    """Track birth identities; never signal a recycled PID or an unverified old PGID."""

    def __init__(self, command: list[str], env: dict, directory: Path, role: str):
        self.role, self.directory = role, directory
        self.log = (directory / f"{role}.log").open("wb")
        self.known: dict[int, dict] = {}
        self.process = subprocess.Popen(
            command,
            env=env,
            cwd=REPO,
            start_new_session=True,
            stdout=self.log,
            stderr=subprocess.STDOUT,
        )
        # Register the direct child immediately. Popen retains ownership even if a
        # subsequent /proc read fails; caller finally still waits/kills that child.
        try:
            self.discover()
            save(
                directory / f"{role}.launch.json",
                {
                    "at": now(),
                    "pid": self.process.pid,
                    "argv": command,
                    "birth": self.known.get(self.process.pid),
                    "environment": env,
                },
            )
        except BaseException as exc:
            # The un-waited direct child cannot have been recycled. If its
            # session is still ours, include children of a failed birth read.
            if self.process.poll() is None:
                try:
                    if os.getpgid(self.process.pid) == self.process.pid:
                        os.killpg(self.process.pid, signal.SIGTERM)
                    else:
                        self.process.terminate()
                except ProcessLookupError:
                    pass
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                if (
                    self.process.poll() is None
                    and os.getpgid(self.process.pid) == self.process.pid
                ):
                    os.killpg(self.process.pid, signal.SIGKILL)
                else:
                    self.process.kill()
                self.process.wait(timeout=10)
            save(
                directory / f"{role}.launch-error.json",
                {
                    "pid": self.process.pid,
                    "error": repr(exc),
                    "waited_returncode": self.process.returncode,
                    "descendant_absence_verified": False,
                },
            )
            self.log.close()
            raise

    def discover(self) -> None:
        rows = {}
        for p in Path("/proc").iterdir():
            if p.name.isdigit():
                row = process_row(int(p.name))
                if row:
                    rows[row["pid"]] = row
        live_known = {
            pid
            for pid, saved in self.known.items()
            if pid in rows and rows[pid]["starttime"] == saved["starttime"]
        }
        if self.process.poll() is None and self.process.pid in rows:
            live_known.add(self.process.pid)
        changed = True
        while changed:
            new = {
                pid
                for pid, row in rows.items()
                if row["ppid"] in live_known
                or (row["sid"] == self.process.pid and live_known)
            }
            changed = bool(new - live_known)
            live_known |= new
        additions = {
            pid: rows[pid]
            for pid in live_known
            if pid not in self.known
            or rows[pid]["starttime"] != self.known[pid]["starttime"]
        }
        if additions:
            with (self.directory / f"{self.role}.owners.jsonl").open("a") as f:
                f.write(
                    json.dumps({"at": now(), "owners": list(additions.values())}) + "\n"
                )
            self.known.update(additions)

    def alive(self) -> list[dict]:
        self.discover()
        return [
            row
            for pid, saved in self.known.items()
            if (row := process_row(pid))
            and row["starttime"] == saved["starttime"]
            and row["state"] not in ("Z", "X")
        ]

    def cleanup(self, term_seconds: int, kill_seconds: int) -> dict:
        errors = []
        for sig, grace in (
            (signal.SIGTERM, term_seconds),
            (signal.SIGKILL, kill_seconds),
        ):
            try:
                if self.process.poll() is None and self.process.pid not in self.known:
                    # Birth capture can lose a race or fail. The live, un-waited
                    # direct Popen child is still ours; never infer ownership
                    # from this PID after poll/wait reports its exit.
                    if os.getpgid(self.process.pid) == self.process.pid:
                        os.killpg(self.process.pid, sig)
                    else:
                        self.process.send_signal(sig)
                for row in self.alive():
                    check = process_row(row["pid"])
                    if check and check["starttime"] == row["starttime"]:
                        try:
                            os.kill(row["pid"], sig)
                        except ProcessLookupError:
                            pass
                deadline = time.monotonic() + grace
                while self.alive() and time.monotonic() < deadline:
                    time.sleep(0.2)
            except Exception as exc:
                errors.append(repr(exc))
        try:
            rc = self.process.wait(timeout=kill_seconds)
        except subprocess.TimeoutExpired:
            rc = None
            errors.append("direct child did not terminate")
        remaining = self.alive()
        self.log.close()
        result = {
            "at": now(),
            "waited_returncode": rc,
            "remaining": remaining,
            "errors": errors,
            "owners": list(self.known.values()),
        }
        save(self.directory / f"{self.role}.exit.json", result)
        return result


def capture(command: list[str], env: dict, timeout: int = 30) -> dict:
    result = subprocess.run(
        command, env=env, capture_output=True, text=True, timeout=timeout
    )
    return {
        "argv": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def gpu_snapshot(env: dict) -> dict:
    gpu = capture(
        [
            "nvidia-smi",
            "--query-gpu=index,uuid,name,driver_version,utilization.gpu,memory.used,memory.total,power.draw",
            "--format=csv,noheader,nounits",
        ],
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
    if gpu["returncode"] or apps["returncode"]:
        raise RuntimeError("nvidia-smi failed")
    return {"at": now(), "gpu": gpu, "applications": apps}


def require_idle(snapshot: dict) -> None:
    if len(snapshot["gpu"]["stdout"].strip().splitlines()) != 8:
        raise RuntimeError("Expected eight physical GPUs")
    if snapshot["applications"]["stdout"].strip():
        raise RuntimeError("GPU applications still present; stop before another case")


def cache_snapshot(root: Path, destination: Path) -> None:
    # Only this campaign's explicit caches, without following directory links.
    # Compilation payloads are stat inventories, not claims of full payload SHA.
    rows = {}
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            p = Path(directory) / name
            s = p.lstat()
            row = {"bytes": s.st_size, "mtime_ns": s.st_mtime_ns}
            if stat.S_ISLNK(s.st_mode):
                row.update(kind="symlink", link_text=os.readlink(p))
            elif stat.S_ISDIR(s.st_mode):
                row["kind"] = "directory"
            elif stat.S_ISREG(s.st_mode):
                row["kind"] = "file"
                if p.is_relative_to(root / "tactics"):
                    row.update(digest(p))
                    copy = (
                        destination.parent
                        / (destination.stem + "-tactics")
                        / p.relative_to(root / "tactics")
                    )
                    copy.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(p, copy)
                    if digest(copy) != {k: row[k] for k in ("bytes", "sha256")}:
                        raise RuntimeError(f"Tactic snapshot changed: {p}")
            else:
                raise RuntimeError(f"Unexpected cache file: {p}")
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


def source_snapshot(cfg: dict, env: dict) -> dict:
    result = {}
    for name in ("sglang", "flashinfer"):
        path = cfg[name + "_root"]
        head = capture(["git", "-C", path, "rev-parse", "HEAD"], env)
        clean = capture(["git", "-C", path, "diff", "--exit-code", "HEAD", "--"], env)
        if (
            head["returncode"]
            or head["stdout"].strip() != cfg[name + "_commit"]
            or clean["returncode"]
        ):
            raise RuntimeError(f"{name} source mismatch or tracked changes")
        result[name] = {"root": path, "head": head, "diff": clean}
    freeze = capture([cfg["python"], "-B", "-m", "pip", "freeze", "--all"], env, 120)
    if freeze["returncode"]:
        raise RuntimeError("pip freeze failed")
    result["freeze"] = freeze
    result["recipe"] = {
        str(p.relative_to(REPO)): digest(p)
        for p in (
            HERE / "run.py",
            HERE / "benchmark_mtp.sh",
            REPO / "benchmarks/benchmark_lib.sh",
            REPO / "infx/bench_serving/benchmark_serving.py",
            REPO / "infx/bench_serving/backend_request_func.py",
        )
    }
    return result


def http_json(cfg: dict, endpoint: str) -> dict:
    with urlopen(f"http://127.0.0.1:{cfg['port']}/{endpoint}", timeout=5) as response:
        return json.load(response)


def installed_runtime(cfg: dict, env: dict) -> dict:
    # Full source commits of the installed main/cubin wheels, not their shortened
    # package versions. Do not shadow a built wheel with an unbuilt source tree.
    script = """import json,pathlib,site,sys
import sglang,flashinfer,flashinfer_cubin
import flashinfer._build_meta as main,flashinfer_cubin._build_meta as cubin
from flashinfer.jit import env
assert main.__git_commit__ == cubin.__git_version__ == sys.argv[1]
assert flashinfer.__version__ == flashinfer_cubin.__version__
assert pathlib.Path(sglang.__file__).resolve().is_relative_to(pathlib.Path(sys.argv[2]).resolve())
assert any(pathlib.Path(flashinfer.__file__).resolve().is_relative_to(pathlib.Path(p).resolve()) for p in site.getsitepackages())
assert not env.FLASHINFER_AOT_PROVIDERS
print(json.dumps({'sglang':sglang.__file__,'flashinfer':flashinfer.__file__,'cubin':flashinfer_cubin.__file__,
 'version':flashinfer.__version__,'git_commit':main.__git_commit__,'cubin_git_commit':cubin.__git_version__,
 'aot_providers':len(env.FLASHINFER_AOT_PROVIDERS),'python':sys.executable,'prefix':sys.prefix}))
"""
    proof = capture(
        [
            cfg["python"],
            "-B",
            "-c",
            script,
            cfg["flashinfer_commit"],
            cfg["sglang_root"] + "/python",
        ],
        env,
        120,
    )
    if proof["returncode"]:
        raise RuntimeError(f"Installed provider proof failed: {proof}")
    return proof


def validate_server_info(info: dict, cfg: dict, case: dict) -> None:
    expected = {
        "model_path": cfg["model_path"],
        "tp_size": case["tp"],
        "dp_size": case["dp"],
        "ep_size": case["ep"],
        "enable_dp_attention": True,
        "mem_fraction_static": 0.8,
        "max_running_requests": case["server_max_running_requests"],
        # SGLang divides the global input chunk budget among DP workers.
        "chunked_prefill_size": 32768 // case["dp"],
        "max_prefill_tokens": 32768,
        "kv_cache_dtype": "fp8_e4m3",
        "disable_radix_cache": True,
        "moe_runner_backend": "flashinfer_megamoe",
        "moe_a2a_backend": "flashinfer_megamoe",
        "speculative_moe_runner_backend": "flashinfer_trtllm",
        "speculative_moe_a2a_backend": "none",
        "speculative_algorithm": "EAGLE",
        "speculative_num_steps": 3,
        "speculative_eagle_topk": 1,
        "speculative_num_draft_tokens": 4,
        "cuda_graph_backend_prefill": "disabled",
        "stream_interval": 30,
        "disable_flashinfer_autotune": False,
    }
    errors = {
        k: {"expected": v, "actual": info.get(k)}
        for k, v in expected.items()
        if info.get(k) != v
    }
    if errors:
        raise ValueError(f"Resolved server settings differ: {errors}")


def validate_result(result: dict, case: dict) -> dict:
    count = case["measured_requests"]
    if result.get("completed") != count or result.get("num_prompts") != count:
        raise ValueError("Incomplete measured request count")
    if (
        result.get("max_concurrency") != case["concurrency"]
        or result.get("request_rate") != "inf"
    ):
        raise ValueError("Benchmark traffic changed")
    for key in ("input_lens", "output_lens"):
        if len(result[key]) != count or any(
            type(x) is not int or x <= 0 for x in result[key]
        ):
            raise ValueError(f"Invalid ordered {key}")
    if (
        sum(result["input_lens"]) != result["total_input_tokens"]
        or sum(result["output_lens"]) != result["total_output_tokens"]
    ):
        raise ValueError("Token totals do not match the ordered arrays")
    if not 0 < result["duration"] < float("inf"):
        raise ValueError("Invalid measurement duration")
    throughput = result["total_output_tokens"] / result["duration"]
    if abs(result["output_throughput"] - throughput) > 1e-8 * max(1, throughput):
        raise ValueError("Throughput is not whole-interval output tokens / duration")
    return {k: result[k] for k in ("input_lens", "output_lens")}


def requested_lengths(model_path: str, count: int, destination: Path) -> None:
    """Reproduce the unchanged client's CPU request plan, without sending requests."""
    import random

    import numpy as np

    from infx.bench_serving import benchmark_serving as client

    if (
        Path(client.__file__).resolve()
        != REPO / "infx/bench_serving/benchmark_serving.py"
    ):
        raise ValueError("Request-plan client origin differs")
    if count <= 0:
        raise ValueError("Positive request count required")
    random.seed(0)
    np.random.seed(0)
    tokenizer = client._load_tokenizer(
        model_path, tokenizer_mode="auto", trust_remote_code=False
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
        tokenizer_id=model_path,
        tokenizer_mode="auto",
        trust_remote_code=False,
        num_workers=0,
    )
    value = {
        "scope": "deterministic request plan, not server output",
        "seed": 0,
        "nominal_input": 1024,
        "nominal_output": 8192,
        "ratio": 0.8,
        "num_prompts": count,
        "model_path": model_path,
        "client_source": digest(Path(client.__file__)),
        "input_lens": [row[1] for row in requests],
        "output_lens": [row[2] for row in requests],
    }
    with destination.open("x") as f:
        json.dump(value, f, indent=2, sort_keys=True)
        f.write("\n")


def validate_requested_lengths(
    planned: dict, result: dict, case: dict, cfg: dict
) -> None:
    expected = {
        "seed": 0,
        "nominal_input": 1024,
        "nominal_output": 8192,
        "ratio": 0.8,
        "num_prompts": case["measured_requests"],
        "model_path": cfg["model_path"],
        "client_source": digest(REPO / "infx/bench_serving/benchmark_serving.py"),
    }
    if any(planned.get(k) != v for k, v in expected.items()):
        raise ValueError("Requested-length plan settings/source differ")
    for key in ("input_lens", "output_lens"):
        if planned.get(key) != result[key]:
            raise ValueError(
                f"Requested versus completed ordered {key} differ; possible truncation"
            )


def validate_client_log(text: str, case: dict) -> None:
    # benchmark_lib intentionally exposes no seed override. Bind its unchanged
    # client default AND check the actual Namespace emitted by this invocation.
    namespaces = [line for line in text.splitlines() if line.startswith("Namespace(")]
    if len(namespaces) != 1 or not re.search(r"(?:\(|, )seed=0(?:,|\))", namespaces[0]):
        raise ValueError("Client did not record the required seed=0")
    if (
        f"Warming up with {case['warmup_requests']} requests..." not in text
        or "Warmup completed." not in text
    ):
        raise ValueError("Missing complete warmup phase evidence")


def seal_case(directory: Path) -> None:
    files = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"Unexpected link in case evidence: {path}")
        if path.is_file() and path.name != "manifest.json":
            files[str(path.relative_to(directory))] = digest(path)
    save(
        directory / "manifest.json",
        {
            "sealed_at": now(),
            "files": files,
            "scope": "terminal case evidence; cache payloads limited to tactics",
        },
    )


def run_case(cfg: dict, case: dict, references: dict, baseline: dict) -> None:
    root = Path(cfg["run_root"])
    directory = root / "cases" / case["case_id"]
    directory.mkdir()
    env = environment(cfg, case)
    server = client = None
    status = {"case": case, "started_at": now(), "status": "running", "error": None}
    save(
        directory / "settings.json",
        {
            "case": case,
            "config": cfg,
            "environment": env,
            "nominal_input": 1024,
            "nominal_output": 8192,
            "ratio": 0.8,
            "seed": 0,
            "seed_source": "unchanged shared client default; checked in actual Namespace",
        },
    )
    save(directory / "server_command.json", server_command(cfg, case))
    last_monitor = 0.0

    def tick() -> None:
        nonlocal last_monitor
        for proc in (server, client):
            if proc:
                proc.discover()
        if time.monotonic() - last_monitor >= cfg["monitor_interval_seconds"]:
            with (directory / "gpu.jsonl").open("a") as f:
                f.write(json.dumps(gpu_snapshot(env)) + "\n")
            last_monitor = time.monotonic()

    try:
        before = gpu_snapshot(env)
        save(directory / "gpu.before.json", before)
        require_idle(before)
        current = source_snapshot(cfg, env)
        save(directory / "source.before.json", current)
        if current != baseline:
            raise RuntimeError("Source, package freeze or recipe changed between cases")
        with socket.socket() as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", cfg["port"]))
        cache_snapshot(root / "caches", directory / "cache.before.json")
        server = OwnedProcess(server_command(cfg, case), env, directory, "server")
        deadline = time.monotonic() + cfg["ready_timeout_seconds"]
        while True:
            tick()
            if server.process.poll() is not None:
                raise RuntimeError(
                    f"Server exited before health: {server.process.returncode}"
                )
            try:
                with urlopen(
                    f"http://127.0.0.1:{cfg['port']}/health", timeout=2
                ) as response:
                    if response.status == 200:
                        break
            except (URLError, TimeoutError):
                pass
            if time.monotonic() > deadline:
                raise TimeoutError("Server readiness deadline exceeded")
            time.sleep(1)
        info = http_json(cfg, "get_server_info")
        save(directory / "server_info.before.json", info)
        validate_server_info(info, cfg, case)
        client_env = dict(
            env,
            CASE_DIR=str(directory),
            MODEL_PATH=cfg["model_path"],
            SERVED_MODEL=cfg["served_model"],
            PORT=str(cfg["port"]),
            CONC=str(case["concurrency"]),
            SERVER_PID=str(server.process.pid),
            EVAL_ONLY="false",
            PROFILE="0",
        )
        client_command = ["bash", str(HERE / "benchmark_mtp.sh")]
        save(
            directory / "benchmark_command.json",
            {"argv": client_command, "environment": client_env},
        )
        client = OwnedProcess(client_command, client_env, directory, "benchmark")
        deadline = time.monotonic() + cfg["benchmark_timeout_seconds"]
        while client.process.poll() is None:
            tick()
            if server.process.poll() is not None:
                raise RuntimeError("Server died during benchmark")
            if time.monotonic() > deadline:
                raise TimeoutError("Benchmark deadline exceeded")
            time.sleep(1)
        if client.process.returncode:
            raise RuntimeError(f"Benchmark failed: {client.process.returncode}")
        info = http_json(cfg, "get_server_info")
        save(directory / "server_info.after.json", info)
        validate_server_info(info, cfg, case)
        result = json.loads((directory / "result.json").read_text())
        lengths = validate_result(result, case)
        validate_requested_lengths(
            json.loads((directory / "requested-lengths.json").read_text()),
            result,
            case,
            cfg,
        )
        validate_client_log((directory / "benchmark.log").read_text(), case)
        save(
            directory / "metrics.json",
            {
                "output_tokens": result["total_output_tokens"],
                "duration_seconds": result["duration"],
                "gpu_count": info["tp_size"],
                "output_tokens_per_second": result["output_throughput"],
                "output_tokens_per_second_per_gpu": result["output_throughput"]
                / info["tp_size"],
                "definition": "all measured output tokens / complete measured wall interval / actual TP",
            },
        )
        ref = references.get(case["concurrency"])
        if ref is not None and lengths != ref:
            raise RuntimeError(
                "Ordered lengths differ from the earlier same-concurrency fresh case"
            )
        references[case["concurrency"]] = lengths
        status["status"] = "completed"
    except BaseException as exc:
        status.update(
            status="failed", error=repr(exc), traceback=traceback.format_exc()
        )
    finally:
        # A second INT/TERM cannot interrupt owned teardown halfway through.
        prior = {
            s: signal.signal(s, signal.SIG_IGN) for s in (signal.SIGINT, signal.SIGTERM)
        }
        try:
            status["cleanup"] = {}
            for proc in (client, server):
                if proc:
                    try:
                        row = proc.cleanup(cfg["term_seconds"], cfg["kill_seconds"])
                        status["cleanup"][proc.role] = row
                        if row["remaining"] or row["errors"]:
                            status["status"] = "failed"
                    except Exception as exc:
                        status["cleanup"][proc.role] = {"error": repr(exc)}
                        status["status"] = "failed"
            try:
                deadline = time.monotonic() + cfg["kill_seconds"]
                while True:
                    after = gpu_snapshot(env)
                    with (directory / "gpu.cleanup.jsonl").open("a") as f:
                        f.write(json.dumps(after) + "\n")
                    save(directory / "gpu.after.json", after)
                    if (
                        not after["applications"]["stdout"].strip()
                        or time.monotonic() >= deadline
                    ):
                        require_idle(after)
                        break
                    time.sleep(1)
                source_after = source_snapshot(cfg, env)
                save(directory / "source.after.json", source_after)
                if source_after != baseline:
                    raise RuntimeError("Source/package/recipe changed during the case")
                if status["status"] == "completed":
                    cache_snapshot(root / "caches", directory / "cache.after.json")
                else:
                    save(
                        directory / "cache.after-skipped.json",
                        {
                            "reason": "Case or owned cleanup incomplete; caches may still be active"
                        },
                    )
            except Exception as exc:
                status.update(status="failed", postflight_error=repr(exc))
            status["finished_at"] = now()
            save(directory / "exit.json", status)
            seal_case(directory)
        finally:
            for sig, handler in prior.items():
                signal.signal(sig, handler)
    if status["status"] != "completed":
        raise RuntimeError(f"Case failed; preserved at {directory}")


def validate_tmp_root(cfg: dict) -> Path:
    path = canonical_path(cfg["tmp_root"])
    if (
        path.parent != Path("/tmp")
        or not re.fullmatch(r"infx-[A-Za-z0-9._-]+", path.name)
        or len(os.fsencode(path)) >= 30
    ):
        raise ValueError(
            "tmp_root must be a short (<30 bytes), private /tmp/infx-* child"
        )
    return path


def socket_path_preflight(path: Path, receipt: dict) -> None:
    # Exact naming shapes from pinned FlashInfer fd_exchange.py/mixed_comm.py.
    # This tests OS pathname support only, without invoking CUDA or collectives.
    receipt["probes"] = []
    for prefix, leaf, kind in (
        (f"cuda_fd_xchg_{os.getpid()}_7_", "fd.sock", socket.SOCK_STREAM),
        (f"cuda_fd_bcast_{os.getpid()}_7_", "fd.sock", socket.SOCK_STREAM),
        ("flashinfer_mixed_comm_", "rank_7", socket.SOCK_DGRAM),
    ):
        directory = Path(tempfile.mkdtemp(prefix=prefix, dir=path))
        directory_identity = (directory.stat().st_dev, directory.stat().st_ino)
        target = directory / leaf
        row = {
            "path": str(target),
            "bytes_without_nul": len(os.fsencode(target)),
            "socket_type": kind,
            "bound": False,
            "cleanup_errors": [],
        }
        receipt["probes"].append(row)
        sock = None
        identity = None
        try:
            random_suffix = directory.name[len(prefix) :]
            worst_prefix = prefix.replace(str(os.getpid()), "2147483647", 1)
            worst = path / (worst_prefix + random_suffix) / leaf
            row["max_pid_rank_path_bytes_with_nul"] = len(os.fsencode(worst)) + 1
            if row["max_pid_rank_path_bytes_with_nul"] > 108:
                raise ValueError("AF_UNIX sun_path budget exceeded")
            sock = socket.socket(socket.AF_UNIX, kind)
            sock.bind(str(target))
            st = target.lstat()
            identity = (st.st_dev, st.st_ino)
            row.update(bound=True, socket_device=st.st_dev, socket_inode=st.st_ino)
        finally:
            if sock is not None:
                sock.close()
            if identity is not None:
                try:
                    st = target.lstat()
                    if (st.st_dev, st.st_ino) != identity or not stat.S_ISSOCK(
                        st.st_mode
                    ):
                        raise ValueError("Owned probe socket identity changed")
                    target.unlink()
                except Exception as exc:
                    row["cleanup_errors"].append(repr(exc))
            try:
                st = directory.lstat()
                if (st.st_dev, st.st_ino) != directory_identity or not stat.S_ISDIR(
                    st.st_mode
                ):
                    raise ValueError("Owned probe directory identity changed")
                directory.rmdir()  # No recursion; never remove an unexpected child.
            except Exception as exc:
                row["cleanup_errors"].append(repr(exc))
            if row["cleanup_errors"]:
                raise RuntimeError("Owned AF_UNIX probe cleanup failed: " + repr(row))


def prepare_tmp_scope(cfg: dict, root: Path) -> None:
    path = validate_tmp_root(cfg)
    receipt = {
        "run_id": cfg["run_id"],
        "run_root": str(root),
        "tmp_root": str(path),
        "at": now(),
        "worker": process_row(os.getpid()),
        "error": None,
        "scope_retained_for_postterminal_preservation": True,
    }
    try:
        # Existing TMPDIR is never adopted, emptied, or reused by another run.
        parent = os.open("/tmp", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.mkdir(path.name, mode=0o700, dir_fd=parent)
            child = os.open(
                path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
            )
            try:
                st = os.fstat(child)
                receipt["directory_identity"] = {
                    "device": st.st_dev,
                    "inode": st.st_ino,
                    "uid": st.st_uid,
                }
                marker = {
                    k: receipt[k]
                    for k in (
                        "run_id",
                        "run_root",
                        "tmp_root",
                        "worker",
                        "directory_identity",
                    )
                }
                fd = os.open(
                    ".inferencex-owner.json",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=child,
                )
                with os.fdopen(fd, "w") as stream:
                    json.dump(marker, stream, sort_keys=True)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
            finally:
                os.close(child)
        finally:
            os.close(parent)
        receipt["owner_marker"] = digest(path / ".inferencex-owner.json")
        socket_path_preflight(path, receipt)
        receipt["status"] = "AF_UNIX_PATH_PREFLIGHT_PASSED"
    except BaseException as exc:
        receipt.update(status="FAILED", error=repr(exc))
        raise
    finally:
        save(root / "tmp-preflight.json", receipt)


def validate_compile_seed(cfg: dict) -> None:
    seed = cfg["compile_cache_seed"]
    if seed is None:
        return
    if not isinstance(seed, dict) or set(seed) != {
        "root",
        "manifest",
        "manifest_sha256",
    }:
        raise ValueError("Invalid compile-only seed configuration")
    base, manifest = (canonical_path(seed[k]) for k in ("root", "manifest"))
    if base.is_relative_to(Path(cfg["run_root"])) or manifest.is_relative_to(base):
        raise ValueError(
            "Compile seed/manifest must precede and remain outside the fresh run"
        )
    if not re.fullmatch(r"[0-9a-f]{64}", seed["manifest_sha256"]):
        raise ValueError("Exact compile seed manifest SHA required")


def compile_seed_inventory(base: Path) -> dict:
    for p in (base, *base.parents):
        if p.is_symlink():
            raise ValueError("Linked compile seed path")
    if not base.is_dir():
        raise ValueError("Compile seed/cache root must be an existing directory")
    files, directories = {}, []
    total = 0
    for directory, dirs, names in os.walk(base, followlinks=False):
        for name in sorted(dirs + names):
            p = Path(directory) / name
            rel = p.relative_to(base).as_posix()
            mode = p.lstat().st_mode
            if stat.S_ISDIR(mode):
                directories.append(rel)
            elif stat.S_ISREG(mode):
                total += p.stat().st_size
                if total > 200 * 1024**3:
                    raise ValueError("Compile seed exceeds 200 GiB")
                files[rel] = digest(p)
            else:
                raise ValueError(
                    "Compile seed contains a link or special entry: " + str(p)
                )
            if len(files) + len(directories) > 250000:
                raise ValueError("Compile seed entry bound")
    return {"files": files, "directories": sorted(directories)}


def copy_compile_seed(cfg: dict, root: Path) -> None:
    seed = cfg["compile_cache_seed"]
    if seed is None:
        save(
            root / "compile-cache-seed.json", {"status": "NO_SEED_FRESH_COMPILE_CACHE"}
        )
        return
    source, manifest_path = Path(seed["root"]), Path(seed["manifest"])
    for p in (manifest_path, *manifest_path.parents):
        if p.is_symlink():
            raise ValueError("Linked compile seed manifest")
    if digest(manifest_path)["sha256"] != seed["manifest_sha256"]:
        raise ValueError("Compile seed manifest changed")
    manifest = json.loads(manifest_path.read_text())
    if (
        set(manifest) != {"schema", "root", "files", "directories", "source"}
        or manifest["schema"] != 1
        or manifest["root"] != str(source)
    ):
        raise ValueError("Compile seed manifest schema/root mismatch")
    before = compile_seed_inventory(source)
    if before != {k: manifest[k] for k in ("files", "directories")}:
        raise ValueError("Compile seed bytes differ from manifest")
    destination = root / "caches" / "compile"
    empty = compile_seed_inventory(destination)
    if empty["files"]:
        raise ValueError("New compile cache is already populated")
    for name in before["directories"]:
        (destination / name).mkdir(parents=True, exist_ok=True)
    for name in before["files"]:
        shutil.copyfile(
            source / name, destination / name
        )  # No hardlinks or source writes.
    copied = compile_seed_inventory(destination)
    if copied["files"] != before["files"] or copied["directories"] != sorted(
        set(empty["directories"]) | set(before["directories"])
    ):
        raise ValueError("Copied compile cache differs")
    if (
        compile_seed_inventory(source) != before
        or digest(manifest_path)["sha256"] != seed["manifest_sha256"]
    ):
        raise ValueError("Compile seed changed during copy")
    save(
        root / "compile-cache-seed.json",
        {
            "status": "VERIFIED_COMPILE_ONLY_COPY",
            "seed": seed,
            "source": manifest["source"],
            "copied": copied,
            "tactics_copied": False,
            "note": "Artifact reuse does not guarantee that every later kernel avoids compilation",
        },
    )


def run(cfg: dict) -> None:
    if sys.platform != "linux":
        raise RuntimeError("Execution requires Linux /proc; --plan is portable")
    root = Path(cfg["run_root"])
    for p in (root, *root.parents):
        if p.is_symlink():
            raise ValueError(f"Linked output ancestor: {p}")
    root.mkdir()  # Existing roots are never resumed or overwritten.
    for name in ("cases", "caches", "tmp", "hf-home", "pycache"):
        (root / name).mkdir()
    first_env = environment(cfg, matrix()[0])
    for case in matrix():
        for key, value in environment(cfg, case).items():
            if key.endswith(("CACHE_DIR", "CACHE_PATH", "CACHE_HOME")) or key in (
                "FLASHINFER_WORKSPACE_BASE",
                "TORCH_EXTENSIONS_DIR",
                "SGLANG_DG_CACHE_DIR",
            ):
                Path(value).mkdir(parents=True, exist_ok=True)
    save(root / "config.json", cfg)
    save(root / "matrix.json", matrix())
    status = {
        "started_at": now(),
        "worker": process_row(os.getpid()),
        "completed": [],
        "error": None,
    }
    save(root / "worker-start.json", status)

    def stop(sig: int, _frame: object) -> None:
        raise InterruptedError(f"Received signal {sig}")

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, stop)
    try:
        prepare_tmp_scope(cfg, root)
        copy_compile_seed(cfg, root)
        baseline = source_snapshot(cfg, first_env)
        save(root / "source.initial.json", baseline)
        save(root / "runtime.initial.json", installed_runtime(cfg, first_env))
        model = Path(cfg["model_path"])
        index = model / "model.safetensors.index.json"
        shards = sorted(set(json.loads(index.read_text())["weight_map"].values()))
        save(
            root / "checkpoint.json",
            {
                "declared_revision": cfg["model_revision"],
                "path": str(model),
                "metadata": {p.name: digest(p) for p in (model / "config.json", index)},
                "shards": {name: (model / name).stat().st_size for name in shards},
                "full_weight_sha256": "not computed by benchmark worker; retain setup evidence",
            },
        )
        references: dict = {}
        for case in matrix():
            run_case(cfg, case, references, baseline)
            status["completed"].append(case["case_id"])
            save(root / "progress.json", status)
    except BaseException as exc:
        status.update(error=repr(exc), traceback=traceback.format_exc())
        raise
    finally:
        status.update(
            finished_at=now(),
            status="completed"
            if len(status["completed"]) == 24 and not status["error"]
            else "failed",
        )
        save(root / "worker-exit.json", status)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--model-path")
    parser.add_argument("--num-prompts", type=int)
    parser.add_argument("--destination", type=Path)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--plan",
        action="store_true",
        help="Print actual matrix, commands and cache paths; no writes",
    )
    mode.add_argument(
        "--run", action="store_true", help="Execute once in a fresh exclusive run root"
    )
    mode.add_argument(
        "--request-lengths",
        action="store_true",
        help="Save a CPU-only deterministic request plan",
    )
    args = parser.parse_args()
    if args.request_lengths:
        if not args.model_path or not args.num_prompts or not args.destination:
            parser.error(
                "--request-lengths requires --model-path, --num-prompts and --destination"
            )
        requested_lengths(args.model_path, args.num_prompts, args.destination)
        return
    if args.config is None:
        parser.error("--config is required for --plan or --run")
    cfg = read_config(args.config)
    if args.plan:
        print(
            json.dumps(
                [
                    dict(
                        case,
                        argv=server_command(cfg, case),
                        environment=environment(cfg, case),
                    )
                    for case in matrix()
                ],
                indent=2,
            )
        )
    else:
        run(cfg)


if __name__ == "__main__":
    main()
