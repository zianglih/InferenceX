#!/usr/bin/env python3
"""Serial EP4/EP8 benchmark runner. Installation and allocation are external."""

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time
from urllib.request import urlopen

from client import PROMPT_FORMATS, write_json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CONCURRENCIES = (1, 2, 4, 8, 16, 32, 64)
ARMS = ("megamoe-w4a4", "megamoe-w4a16", "trtllm-w4a4")
MODELS = ("dsv41", "glm52")


def now():
    return datetime.now(timezone.utc).isoformat()


def selected_gpus(cfg):
    return cfg.get("gpu_ids", list(range(8)))


def matrix(models=MODELS):
    cases = []
    for model in models:
        # Qualify each backend at C1 before starting its longer sweep.
        cases.extend(
            {"model_id": model, "arm_id": arm, "concurrency": 1} for arm in ARMS
        )
        cases.extend(
            {"model_id": model, "arm_id": arm, "concurrency": c}
            for arm in ARMS
            for c in CONCURRENCIES[1:]
        )
    return cases


def target_backends(model_id, arm):
    if arm not in ARMS or model_id not in MODELS:
        raise ValueError("Unknown model/backend")
    if arm.startswith("megamoe"):
        return "flashinfer_megamoe", "flashinfer_megamoe"
    return (
        "flashinfer_trtllm_routed" if model_id == "dsv41" else "flashinfer_trtllm"
    ), "none"


def server_command(cfg, case):
    model, arm, c = case["model_id"], case["arm_id"], case["concurrency"]
    size = len(selected_gpus(cfg))
    checkpoint = cfg["models"][model]
    runner, a2a = target_backends(model, arm)
    args = [
        cfg["python"],
        "-m",
        "sglang.launch_server",
        "--model-path",
        checkpoint["checkpoint_path"],
        "--served-model-name",
        checkpoint["served_model"],
        "--host",
        "127.0.0.1",
        "--port",
        str(cfg["port"]),
        "--trust-remote-code",
        "--dtype",
        "bfloat16",
        "--tensor-parallel-size",
        str(size),
        "--expert-parallel-size",
        str(size),
        "--attn-dp-size",
        str(size),
        "--moe-runner-backend",
        runner,
        "--moe-a2a-backend",
        a2a,
        "--speculative-moe-a2a-backend",
        "none",
        "--mem-fraction-static",
        "0.80",
        "--chunked-prefill-size",
        "32768",
        "--max-prefill-tokens",
        "32768",
        "--max-running-requests",
        str(max(c, size)),
        "--cuda-graph-max-bs-decode",
        str(c),
        "--cuda-graph-backend-prefill",
        "disabled",
        "--flashinfer-allreduce-fusion-backend",
        "auto",
        "--disable-radix-cache",
        "--stream-interval",
        "30",
        "--model-loader-extra-config",
        '{"enable_multithread_load": true}',
    ]
    if model == "dsv41":
        args += [
            "--json-model-override-args",
            '{"vision_n_layers":0}',
            "--enable-dp-lm-head",
            "--speculative-algorithm",
            "DSPARK",
            "--speculative-dspark-block-size",
            "5",
            "--speculative-draft-model-path",
            checkpoint["checkpoint_path"],
            "--speculative-moe-runner-backend",
            "flashinfer_mxfp4",
        ]
    else:
        args += [
            "--quantization",
            "modelopt_fp4",
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
            "--speculative-algorithm",
            "EAGLE",
            "--speculative-num-steps",
            "3",
            "--speculative-eagle-topk",
            "1",
            "--speculative-num-draft-tokens",
            "4",
            "--speculative-moe-runner-backend",
            "flashinfer_trtllm",
        ]
    return args


def environment(cfg, case):
    root = Path(cfg["run_root"])
    compile_root = root / "cache" / "compile"
    env = {
        key: os.environ[key]
        for key in ("PATH", "LD_LIBRARY_PATH", "CUDA_HOME")
        if key in os.environ
    }
    env.update(
        PATH=str(Path(cfg["python"]).parent) + os.pathsep + env.get("PATH", os.defpath),
        HOME=str(root / "home"),
        LANG="C.UTF-8",
        PYTHONNOUSERSITE="1",
        PYTHONUNBUFFERED="1",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(REPO),
        CUDA_VISIBLE_DEVICES=",".join(map(str, selected_gpus(cfg))),
        TMPDIR=cfg["tmp_root"],
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        HF_HOME=str(root / "hf-home"),
        SGLANG_CACHE_DIR=str(
            root / "cache" / "tactics" / case["model_id"] / case["arm_id"]
        ),
    )
    for key, subdir in {
        "FLASHINFER_WORKSPACE_BASE": "flashinfer",
        "CUTE_DSL_CACHE_DIR": "cute",
        "CUDA_CACHE_PATH": "cuda",
        "TORCH_EXTENSIONS_DIR": "torch-extensions",
        "TORCHINDUCTOR_CACHE_DIR": "torchinductor",
        "TRITON_CACHE_DIR": "triton",
        "TILELANG_CACHE_DIR": "tilelang",
        "SGLANG_DG_CACHE_DIR": "deep-gemm",
        "SGLANG_CUTE_AOT_CACHE_DIR": "cute-aot",
        "SGLANG_JIT_CACHE_DIR": "sglang-jit",
        "XDG_CACHE_HOME": "xdg",
    }.items():
        env[key] = str(compile_root / subdir)
    if case["model_id"] == "dsv41":
        env["SGLANG_RAGGED_VERIFY_MODE"] = "static"
    if case["arm_id"] == "megamoe-w4a16":
        env["SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16"] = "1"
    return env


def validate_server_info(info, cfg, case):
    model, arm, c = case["model_id"], case["arm_id"], case["concurrency"]
    size = len(selected_gpus(cfg))
    runner, a2a = target_backends(model, arm)
    expected = {
        "model_path": cfg["models"][model]["checkpoint_path"],
        "tp_size": size,
        "ep_size": size,
        "attn_dp_size": size,
        "dp_size": 1,
        "dtype": "bfloat16",
        "mem_fraction_static": 0.8,
        "max_running_requests": max(c, size),
        "chunked_prefill_size": 32768 // size,
        "max_prefill_tokens": 32768,
        "disable_radix_cache": True,
        "stream_interval": 30,
        "moe_runner_backend": runner,
        "moe_a2a_backend": a2a,
        "speculative_moe_a2a_backend": "none",
        "speculative_num_draft_tokens": 6 if model == "dsv41" else 4,
        "speculative_algorithm": "DSPARK" if model == "dsv41" else "EAGLE",
        "speculative_moe_runner_backend": "flashinfer_mxfp4"
        if model == "dsv41"
        else "flashinfer_trtllm",
    }
    if model == "dsv41":
        expected.update(
            enable_dp_lm_head=True,
            speculative_dspark_block_size=5,
            json_model_override_args='{"vision_n_layers":0}',
        )
    else:
        expected.update(
            quantization="modelopt_fp4",
            kv_cache_dtype="fp8_e4m3",
            speculative_num_steps=3,
            speculative_eagle_topk=1,
        )
    errors = {
        key: {"expected": value, "actual": info.get(key)}
        for key, value in expected.items()
        if info.get(key) != value
    }
    prefill = info.get("cuda_graph_config", {}).get("prefill", {}).get("backend")
    if prefill != "disabled":
        errors["cuda_graph_config.prefill.backend"] = {
            "expected": "disabled",
            "actual": prefill,
        }
    if errors:
        raise ValueError("Effective server settings differ: " + json.dumps(errors))
    return expected


def process_row(pid):
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
        values = text[text.rfind(")") + 2 :].split()
        return {
            "pid": pid,
            "state": values[0],
            "ppid": int(values[1]),
            "sid": int(values[3]),
            "birth": values[19],
        }
    except (OSError, ValueError, IndexError):
        return None


class OwnedProcess:
    def __init__(self, args, env, log):
        self.log = log.open("wb")
        self.process = subprocess.Popen(
            args,
            cwd=REPO,
            env=env,
            stdout=self.log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        self.owners = {}
        self.observe()

    def observe(self):
        live = {}
        for path in Path("/proc").iterdir():
            if path.name.isdigit() and (row := process_row(int(path.name))):
                live[row["pid"]] = row
        for row in live.values():
            if row["sid"] == self.process.pid:
                self.owners[row["pid"]] = row["birth"]
        return [
            row
            for pid, birth in self.owners.items()
            if (row := live.get(pid))
            and row["birth"] == birth
            and row["state"] not in ("Z", "X")
        ]

    def wait(self, timeout, peer=None):
        deadline = time.monotonic() + timeout
        while self.process.poll() is None:
            self.observe()
            if peer is not None:
                peer.observe()
                if peer.process.poll() is not None:
                    raise RuntimeError("Server exited during the benchmark")
            if time.monotonic() >= deadline:
                raise TimeoutError("Owned process exceeded its timeout")
            time.sleep(1)
        return self.process.wait()

    def close(self):
        for sig, grace in ((signal.SIGTERM, 30), (signal.SIGKILL, 15)):
            for row in self.observe():
                fresh = process_row(row["pid"])
                if fresh and fresh["birth"] == row["birth"]:
                    try:
                        os.kill(row["pid"], sig)
                    except ProcessLookupError:
                        pass
            deadline = time.monotonic() + grace
            while self.observe() and time.monotonic() < deadline:
                time.sleep(0.2)
            if not self.observe():
                break
        rc = self.process.wait(timeout=15)
        remaining = self.observe()
        self.log.close()
        if remaining:
            raise RuntimeError("Owned descendants remain: " + repr(remaining))
        return {
            "returncode": rc,
            "remaining": remaining,
            "recorded_processes": len(self.owners),
        }


def gpu_state(cfg):
    def query(args):
        return subprocess.check_output(
            ["nvidia-smi", *args], text=True, timeout=20
        ).strip()

    inventory = query(
        [
            "--query-gpu=index,uuid,name,driver_version,memory.total",
            "--format=csv,noheader,nounits",
        ]
    )
    devices = {int(line.split(",", 1)[0]): line for line in inventory.splitlines()}
    if any(index not in devices for index in selected_gpus(cfg)):
        raise RuntimeError("Selected GPU index is unavailable: " + repr(devices))
    return {
        "at": now(),
        "gpus": "\n".join(devices[index] for index in selected_gpus(cfg)),
        # Keep the whole-node idle guard, including GPUs outside the selected set.
        "applications": query(
            [
                "--query-compute-apps=pid,gpu_uuid,used_memory",
                "--format=csv,noheader,nounits",
            ]
        ),
    }


def require_idle(cfg):
    state = gpu_state(cfg)
    if (
        len(state["gpus"].splitlines()) != len(selected_gpus(cfg))
        or state["applications"]
    ):
        raise RuntimeError(
            "Expected selected GPUs with no running GPU applications: " + repr(state)
        )
    return state


def http_json(cfg, path):
    with urlopen(f"http://127.0.0.1:{cfg['port']}/{path}", timeout=5) as response:
        return json.load(response)


def compress_log(path):
    with (
        path.open("rb") as source,
        gzip.open(path.with_suffix(path.suffix + ".gz"), "xb") as out,
    ):
        shutil.copyfileobj(source, out)
    path.unlink()


def run_case(cfg, case, plan):
    from results import validate_case

    directory = (
        Path(cfg["run_root"])
        / case["model_id"]
        / f"{case['arm_id']}-c{case['concurrency']}"
    )
    directory.mkdir(parents=True, exist_ok=False)
    env = environment(cfg, case)
    command = server_command(cfg, case)
    write_json(
        directory / "launch.json",
        {
            "at": now(),
            "command": command,
            "environment": env,
            "gpu_before": require_idle(cfg),
        },
    )
    server = client = None
    status = {"started_at": now(), "case": case, "status": "running"}
    row = None
    try:
        server = OwnedProcess(command, env, directory / "server.log")
        deadline = time.monotonic() + cfg["ready_timeout_seconds"]
        while True:
            server.observe()
            if server.process.poll() is not None:
                raise RuntimeError("Server exited before readiness")
            try:
                with urlopen(
                    f"http://127.0.0.1:{cfg['port']}/health", timeout=5
                ) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            if time.monotonic() >= deadline:
                raise TimeoutError("Server readiness timeout")
            time.sleep(2)
        info = http_json(cfg, "server_info")
        write_json(directory / "server_info.json", info)
        validate_server_info(info, cfg, case)
        args = [
            cfg["python"],
            "-B",
            str(HERE / "client.py"),
            "run",
            "--plan",
            str(plan),
            "--url",
            f"http://127.0.0.1:{cfg['port']}/v1/completions",
            "--served-model",
            cfg["models"][case["model_id"]]["served_model"],
            "--output",
            str(directory / "measurement.json"),
            "--timeout",
            str(cfg["benchmark_timeout_seconds"]),
            "--gpu-count",
            str(len(selected_gpus(cfg))),
        ]
        client = OwnedProcess(args, env, directory / "client.log")
        if client.wait(cfg["benchmark_timeout_seconds"], peer=server) != 0:
            raise RuntimeError("Benchmark client failed")
        row = json.loads((directory / "measurement.json").read_text())
        if any(row[key] != len(selected_gpus(cfg)) for key in ("tp", "ep", "dp")):
            raise ValueError("Measured topology differs from selected GPUs")
        row = validate_case({**row, **case}, case["model_id"])
        status["status"] = "passed"
    except BaseException as exc:
        status.update(status="failed", error=repr(exc))
        raise
    finally:
        cleanup_errors = []
        for role, process in (("client", client), ("server", server)):
            if process is not None:
                try:
                    status[role] = process.close()
                except BaseException as exc:
                    cleanup_errors.append(f"{role}: {exc!r}")
        status.update(finished_at=now(), cleanup_errors=cleanup_errors)
        if cleanup_errors:
            status["status"] = "failed"
        write_json(directory / "status.json", status)
        for name in ("client.log", "server.log"):
            if (directory / name).exists():
                compress_log(directory / name)
        if cleanup_errors:
            raise RuntimeError("; ".join(cleanup_errors))
    # Publish a case only after the measured client succeeded and server cleanup completed.
    write_json(directory / "gpu_after.json", require_idle(cfg))
    write_json(directory / "case.json", row)
    print(
        json.dumps(
            {
                "at": now(),
                **case,
                "status": "passed",
                "acceptance_length": row["acceptance_length"],
            }
        ),
        flush=True,
    )


def read_config(path):
    cfg = json.loads(path.read_text())
    cfg.setdefault("gpu_ids", list(range(8)))
    cfg.setdefault("model_ids", list(MODELS))
    ids = cfg["gpu_ids"]
    if (
        not isinstance(ids, list)
        or len(ids) not in (4, 8)
        or any(type(index) is not int or not 0 <= index < 8 for index in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValueError("Select four or eight distinct GPU indices from 0 through 7")
    models = cfg["model_ids"]
    if (
        not isinstance(models, list)
        or not models
        or any(model not in MODELS for model in models)
        or len(set(models)) != len(models)
    ):
        raise ValueError("Select a nonempty list of distinct supported model IDs")
    for field in ("sglang_commit", "flashinfer_commit", "benchmark_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", cfg[field]):
            raise ValueError("Missing exact source pin: " + field)
    if not re.search(r"@sha256:[0-9a-f]{64}$", cfg["image"]):
        raise ValueError("Pin an explicit image tag and digest")
    for field in (
        "run_root",
        "tmp_root",
        "python",
        "sglang_root",
        "flashinfer_root",
        "installation_manifest",
    ):
        value = Path(cfg[field])
        if (
            not value.is_absolute()
            or ".." in value.parts
            or value.is_relative_to("/workspace")
        ):
            raise ValueError("Expected explicit safe absolute path: " + field)
    if len(cfg["tmp_root"]) > 60:
        raise ValueError("Use a short TMP path for AF_UNIX sockets")
    if not cfg["run_id"] or not 1 <= cfg["port"] <= 65535:
        raise ValueError("Invalid run identity or port")
    for key in ("ready_timeout_seconds", "benchmark_timeout_seconds"):
        if type(cfg[key]) is not int or cfg[key] <= 0:
            raise ValueError("Expected a positive timeout: " + key)
    for model in models:
        checkpoint = cfg["models"][model]
        if not Path(checkpoint["checkpoint_path"]).is_absolute() or not re.fullmatch(
            r"[0-9a-f]{40}", checkpoint["checkpoint_revision"]
        ):
            raise ValueError("Expected an absolute checkpoint path and exact revision")
        if cfg["models"][model]["prompt_format"] != PROMPT_FORMATS[model]:
            raise ValueError("Unexpected prompt format")
    return cfg


def verify_installation(cfg):
    path = Path(cfg["installation_manifest"])
    raw = path.read_bytes()
    installation = json.loads(raw)
    if (
        installation["status"] != "VERIFIED_SOURCE_INSTALL_ONLY"
        or installation["sglang_sha"] != cfg["sglang_commit"]
        or installation["flashinfer_sha"] != cfg["flashinfer_commit"]
    ):
        raise ValueError("Installed source manifest does not match campaign pins")
    code = (
        "import importlib.util,json; "
        "print(json.dumps({name:importlib.util.find_spec(name).origin "
        "for name in ('sglang','flashinfer','flashinfer_cubin')}))"
    )
    origins = json.loads(
        subprocess.check_output(
            [cfg["python"], "-B", "-c", code],
            cwd=REPO,
            env=environment(cfg, matrix(cfg.get("model_ids", MODELS))[0]),
            text=True,
            timeout=30,
        )
    )
    for module, distribution in (
        ("sglang", "sglang"),
        ("flashinfer", "flashinfer-python"),
        ("flashinfer_cubin", "flashinfer-cubin"),
    ):
        expected = Path(installation["packages"][distribution]["root"]) / module
        if Path(origins[module]).resolve().parent != expected.resolve():
            raise ValueError(
                "Runtime package does not match installed manifest: " + module
            )
    for record in installation["source_files"].values():
        data = Path(record["installed"]).read_bytes()
        if (
            len(data) != record["bytes"]
            or hashlib.sha256(data).hexdigest() != record["sha256"]
        ):
            raise ValueError("Installed source changed: " + record["installed"])
    return {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "torch": installation["torch"],
        "package_versions": {
            k: v["version"] for k, v in installation["packages"].items()
        },
    }


def verify_sources(cfg):
    for root, expected in (
        (REPO, cfg["benchmark_commit"]),
        (Path(cfg["sglang_root"]), cfg["sglang_commit"]),
        (Path(cfg["flashinfer_root"]), cfg["flashinfer_commit"]),
    ):
        head = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
        if head != expected:
            raise ValueError(f"Source pin mismatch: {root}: {head}")
        dirty = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
            text=True,
        )
        if dirty:
            raise ValueError(f"Tracked source changes at {root}")


def interrupted(signum, frame):
    raise KeyboardInterrupt(f"Received signal {signum}")


def main():
    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    cfg = read_config(args.config)
    if args.plan == args.run:
        parser.error("Select exactly one of --plan or --run")
    cases = matrix(cfg["model_ids"])
    if args.plan:
        print(
            json.dumps(
                [{**case, "command": server_command(cfg, case)} for case in cases],
                indent=2,
            )
        )
        return
    verify_sources(cfg)
    installed = verify_installation(cfg)
    root = Path(cfg["run_root"])
    root.mkdir(parents=True, exist_ok=False)
    Path(cfg["tmp_root"]).mkdir(parents=True, exist_ok=False)
    (root / "home").mkdir()
    (root / "plans").mkdir()
    manifest = {
        **cfg,
        "schema_version": 1,
        "created_at": now(),
        "installation": installed,
        "order": cases,
        "matrix": {
            "tp": len(selected_gpus(cfg)),
            "ep": len(selected_gpus(cfg)),
            "dp": len(selected_gpus(cfg)),
            "concurrencies": list(CONCURRENCIES),
            "arms": list(ARMS),
        },
        "workload": {
            "input_len": 1024,
            "output_len": 8192,
            "range_ratio": 0.8,
            "seed": 0,
            "warmup_multiplier": 2,
            "measured_multiplier": 10,
            "stream_interval": 30,
        },
        "gpu_before": require_idle(cfg),
    }
    write_json(root / "campaign.json", manifest)
    try:
        for case in cases:
            plan = root / "plans" / f"{case['model_id']}-c{case['concurrency']}.json.gz"
            if not plan.exists():
                subprocess.run(
                    [
                        cfg["python"],
                        "-B",
                        str(HERE / "client.py"),
                        "prepare",
                        "--model-id",
                        case["model_id"],
                        "--checkpoint",
                        cfg["models"][case["model_id"]]["checkpoint_path"],
                        "--concurrency",
                        str(case["concurrency"]),
                        "--output",
                        str(plan),
                    ],
                    env=environment(cfg, case),
                    cwd=REPO,
                    check=True,
                    timeout=1800,
                )
            run_case(cfg, case, plan)
        write_json(
            root / "COMPLETE.json",
            {
                "at": now(),
                "points": len(cases),
                "status": "passed",
                "gpu_after": require_idle(cfg),
            },
        )
    except BaseException as exc:
        write_json(root / "FAILED.json", {"at": now(), "error": repr(exc)})
        raise


if __name__ == "__main__":
    main()
