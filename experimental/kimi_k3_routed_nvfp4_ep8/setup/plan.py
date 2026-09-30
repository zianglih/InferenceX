#!/usr/bin/env python3
"""Pure, offline Kimi K3 command planner. Never launches a subprocess or imports ML packages."""

from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import shlex

import checkpoint_contract
import source_contract
import continuation

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    "sglang": "561ad447c74bb757a40677ee9ce038f9ca429d2c",
    "flashinfer": "a03f2205263d4e691d68e485bff287e37a19b6c3",
    "client_inferencex": "652ac186d88ebcd6ff995afbe7c3094751f0f4a2",
}
ARM_CONTRACT = {
    "megamoe-w4a4": (
        {
            "--moe-runner-backend": "flashinfer_megamoe",
            "--moe-a2a-backend": "flashinfer_megamoe",
        },
        {},
    ),
    "megamoe-w4a16": (
        {
            "--moe-runner-backend": "flashinfer_megamoe",
            "--moe-a2a-backend": "flashinfer_megamoe",
        },
        {"SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16": "1"},
    ),
    "trtllm-w4a4": (
        {"--moe-runner-backend": "flashinfer_trtllm", "--moe-a2a-backend": "none"},
        {},
    ),
}
COMMON = {
    "--served-model-name": "Kimi-K3-NVFP4",
    "--trust-remote-code": True,
    "--dtype": "bfloat16",
    "--quantization": "modelopt_fp4",
    "--tensor-parallel-size": 8,
    "--expert-parallel-size": 8,
    "--data-parallel-size": 1,
    "--context-length": 16384,
    "--mem-fraction-static": 0.85,
    "--kv-cache-dtype": "fp8_e4m3",
    "--mamba-ssm-dtype": "float32",
    "--chunked-prefill-size": 32768,
    "--max-prefill-tokens": 32768,
    "--disable-radix-cache": True,
    "--cuda-graph-backend-prefill": "disabled",
    "--stream-interval": 30,
    "--reasoning-parser": "kimi_k3",
    "--tool-call-parser": "kimi_k3",
    "--host": "127.0.0.1",
    "--port": 30000,
    "--pp-size": 1,
    "--dcp-size": 1,
}
WORKLOAD = {
    "concurrencies": [4, 8, 16, 32],
    "order": [32, 4, 8, 16],
    "input_length": 1024,
    "output_length": 8192,
    "range_ratio": 0.8,
    "prefix_length": 0,
    "seed": 0,
    "warmup_multiplier": 2,
    "measure_multiplier": 10,
    "ignore_eos": True,
    "use_chat_template": True,
    "stream_interval": 30,
    "speculation": "none",
    "intended_cases": 12,
    "warmup_requests": 360,
    "measured_requests": 1800,
}
HARDWARE = {
    "nodes": 1,
    "gpus": 8,
    "gpu_model": "B300",
    "tp": 8,
    "ep": 8,
    "dp_attention": 1,
    "pp": 1,
    "dcp": 1,
}
VENDOR_FILES = {
    "infx/__init__.py",
    "infx/bench_serving/__init__.py",
    "infx/bench_serving/benchmark_serving.py",
    "infx/bench_serving/backend_request_func.py",
    "infx/bench_serving/benchmark_outcome.py",
    "infx/bench_serving/benchmark_utils.py",
    "infx/bench_serving/encoding_dsv4.py",
    "infx/bench_serving/server_watch.py",
}
RUNTIME_KEYS = {
    "python",
    "model_path",
    "sglang_root",
    "flashinfer_root",
    "run_root",
    "tmp_root",
    "ready_timeout_seconds",
    "benchmark_timeout_seconds",
    "term_seconds",
    "kill_seconds",
}
FUTURE_FILES = [
    "settings.json",
    "server_command.json",
    "benchmark_command.json",
    "server.log",
    "benchmark.log",
    "server.launch.json",
    "benchmark.launch.json",
    "server.owners.jsonl",
    "benchmark.owners.jsonl",
    "gpu.jsonl",
    "gpu.before.json",
    "gpu.after.json",
    "gpu.cleanup.jsonl",
    "server_info.before.json",
    "server_info.after.json",
    "requested-lengths.json",
    "result.json",
    "server.exit.json",
    "benchmark.exit.json",
    "exit.json",
    "manifest.json",
]


def require(value, message):
    if not value:
        raise ValueError(message)


def descriptor(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), f"Expected regular source: {p}")
    h = hashlib.sha256()
    with p.open("rb") as stream:
        before = os.fstat(stream.fileno())
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
        after = os.fstat(stream.fileno())
    require(
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
        == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
        f"Changed source: {p}",
    )
    return {"bytes": after.st_size, "sha256": h.hexdigest()}


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path):
    def invalid(value):
        raise ValueError(f"Non-finite JSON constant: {value}")

    return json.loads(
        Path(path).read_bytes(), object_pairs_hook=pairs_unique, parse_constant=invalid
    )


def canonical_path(value):
    require(
        isinstance(value, str) and value and "\0" not in value and "\n" not in value,
        "Invalid path string",
    )
    p = Path(value)
    require(
        p.is_absolute() and ".." not in p.parts and str(p) == value and p != Path("/"),
        f"Noncanonical absolute path: {value}",
    )
    return p


def validate_campaign(cfg):
    require(
        type(cfg) is dict
        and type(cfg.get("schema_version")) is int
        and cfg["schema_version"] == 1,
        "Unsupported campaign schema",
    )
    require(
        set(cfg)
        <= {
            "schema_version",
            "name",
            "status",
            "authorization",
            "blockers",
            "pins",
            "checkpoint",
            "hardware",
            "workload",
            "common_server_args",
            "arms",
            "runtime",
            "plot",
            "user_decisions",
            "local_changes",
            "continuation",
        },
        "Unexpected campaign keys",
    )
    require(
        cfg.get("name") == "kimi-k3-ep8-three-curves-c32",
        "Unexpected campaign identity",
    )
    for key in ["status", "authorization"]:
        require(isinstance(cfg.get(key), str), "Missing campaign " + key)
    require(
        type(cfg.get("blockers")) is list
        and all(
            type(x) is dict
            and set(x) == {"id", "detail"}
            and all(isinstance(v, str) for v in x.values())
            for x in cfg["blockers"]
        ),
        "Malformed blockers",
    )
    require(
        len({x["id"] for x in cfg["blockers"]}) == len(cfg["blockers"]),
        "Duplicate blocker IDs",
    )
    for key, value in PINS.items():
        require(cfg["pins"].get(key) == value, "Unreviewed pin " + key)
    require(
        re.fullmatch(r".+@sha256:[0-9a-f]{64}", cfg["pins"]["image"]) is not None,
        "Image must be digest pinned",
    )
    require(
        json.dumps(cfg["hardware"], sort_keys=True)
        == json.dumps(HARDWARE, sort_keys=True),
        "Hardware/topology differs from reviewed TP8/EP8/DP1 contract",
    )
    require(
        json.dumps(cfg["workload"], sort_keys=True)
        == json.dumps(WORKLOAD, sort_keys=True),
        "Workload differs from no-MTP review contract",
    )
    require(
        json.dumps(cfg["common_server_args"], sort_keys=True)
        == json.dumps(COMMON, sort_keys=True),
        "Undocumented common argument/override or changed setting",
    )
    require(
        [x["id"] for x in cfg["arms"]] == list(ARM_CONTRACT),
        "Three ordered arms required",
    )
    for arm in cfg["arms"]:
        require(
            set(arm) == {"id", "label", "color", "server_args", "environment"},
            "Unexpected arm fields",
        )
        require(
            (arm["server_args"], arm["environment"]) == ARM_CONTRACT[arm["id"]],
            "Undocumented arm flag/environment override",
        )
        require(
            all(isinstance(arm[k], str) for k in ["label", "color"]),
            "Invalid arm presentation",
        )
    rt = cfg["runtime"]
    require(set(rt) == RUNTIME_KEYS, "Unexpected runtime keys")
    for key in [
        "python",
        "model_path",
        "sglang_root",
        "flashinfer_root",
        "run_root",
        "tmp_root",
    ]:
        canonical_path(rt[key])
    for key in [
        "ready_timeout_seconds",
        "benchmark_timeout_seconds",
        "term_seconds",
        "kill_seconds",
    ]:
        require(type(rt[key]) is int and rt[key] > 0, "Invalid guard timeout " + key)
    require(
        Path(rt["tmp_root"]).parent == Path("/tmp")
        and len(os.fsencode(rt["tmp_root"])) < 30
        and Path(rt["tmp_root"]).name.startswith("infx-"),
        "TMP must be a private short /tmp/infx-* path",
    )
    checkpoint_contract.validate_checkpoint(cfg["checkpoint"], rt["model_path"])
    continuation.validate_spec(cfg["continuation"])


def verify_client(project, pin):
    vendor = Path(project) / "vendor/inferencex"
    source = vendor / "SOURCE.json"
    doc = read_json(source)
    require(
        doc["commit"] == pin and set(doc["files"]) == VENDOR_FILES,
        "Vendor commit or complete package closure differs",
    )
    bindings = {str(source): descriptor(source)}
    for rel, expected in doc["files"].items():
        p = vendor / rel
        actual = descriptor(p)
        require(actual == expected, "Vendor source changed: " + rel)
        bindings[str(p)] = actual
        # Verify every local relative import statically; importing this package would load ML libraries.
        tree = ast.parse(p.read_bytes())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                base = p.parent
                for _ in range(node.level - 1):
                    base = base.parent
                if node.module:
                    q = base.joinpath(*node.module.split("."))
                    targets = [q.with_suffix(".py"), q / "__init__.py"]
                    require(
                        any(
                            t.is_file() and str(t.relative_to(vendor)) in VENDOR_FILES
                            for t in targets
                        ),
                        "Unvendored relative import " + str(q),
                    )
    require(
        {str(p.relative_to(vendor)) for p in (vendor / "infx").rglob("*.py")}
        == VENDOR_FILES,
        "Unexpected or missing vendored Python module",
    )
    require(not any(p.is_symlink() for p in vendor.rglob("*")), "Linked vendor source")
    return {
        "commit": pin,
        "local_root": str(vendor),
        "module": "infx.bench_serving.benchmark_serving",
        "source": str(source),
        "files": doc["files"],
        "bindings": bindings,
    }


def verify_tokenizer(project, cfg):
    # Original source metadata remains reference evidence only. The custom output's
    # copied tokenizer/code is governed by the separately bound conversion acceptance.
    directory = Path(project) / "artifacts/custom-checkpoint-reference"
    files = [
        directory / name
        for name in ("config.json", "tokenizer_config.json", "RECEIPT.json")
    ]
    bindings = {str(p): descriptor(p) for p in files}
    receipt = read_json(directory / "RECEIPT.json")
    require(
        receipt["revision"] == checkpoint_contract.SOURCE_REVISION,
        "Original metadata revision differs",
    )
    expected = {
        "config.json": (
            7006,
            "9710e121a58d03ac92c8d6da287a19541994319afbbe6d6202af001ffd379213",
        ),
        "tokenizer_config.json": (
            3478,
            "5d0803c94db9cd78763499e0956c95fd5a225c14a727e5a6cf5db3f96f010a6e",
        ),
    }
    for name, (size, sha) in expected.items():
        require(
            descriptor(directory / name) == {"bytes": size, "sha256": sha},
            "Original metadata bytes differ",
        )
        row = next(x for x in receipt["files"] if x["name"] == name)
        require(
            row["sha256"] == sha
            and row["bytes"] == size
            and row["url"]
            == f"https://huggingface.co/{checkpoint_contract.SOURCE_REPO}/resolve/{checkpoint_contract.SOURCE_REVISION}/{name}",
            "Original metadata source differs",
        )
    token = read_json(directory / "tokenizer_config.json")
    require(
        token.get("auto_map", {}).get("AutoTokenizer")
        == ["tokenization_kimi.TikTokenTokenizer", None],
        "Original tokenizer remote-code contract differs",
    )
    return {
        "status": "ORIGINAL_METADATA_REFERENCE_ONLY",
        "revision": cfg["checkpoint"]["source_revision"],
        "auto_map": token["auto_map"],
        "tokenizer_class": token["tokenizer_class"],
        "client_trust_remote_code_required": True,
        "code_executed": False,
        "tokenizer_instantiated": False,
        "custom_output_verified": False,
        "acceptance_binding": cfg["checkpoint"]["acceptance"],
        "bindings": bindings,
    }, bindings


def verify_local_changes(cfg, project):
    source_contract.check_campaign(cfg)
    changes = cfg.get("local_changes", {})
    require(
        type(changes) is dict and set(changes) <= {"sglang"},
        "Unsupported local_changes scope",
    )
    if not changes:
        require(
            "sglang_local_patch" not in cfg["pins"],
            "Patch pin requires exact local_changes bytes",
        )
        return {}, {}
    item = changes["sglang"]
    require(
        set(item) == {"base_commit", "patch", "files"}
        and item["base_commit"] == cfg["pins"]["sglang"],
        "Local patch base or schema mismatch",
    )
    patch = item["patch"]
    require(set(patch) == {"path", "bytes", "sha256"}, "Patch descriptor schema")
    require(
        cfg["pins"].get("sglang_local_patch") == patch["sha256"],
        "Local patch SHA pin differs",
    )
    bindings = {}

    def checked(rel, desc, scope):
        require(
            isinstance(rel, str)
            and not Path(rel).is_absolute()
            and ".." not in Path(rel).parts
            and str(Path(rel)) == rel,
            "Invalid local change relative path",
        )
        p = Path(project) / rel
        require(p.is_relative_to(Path(project) / scope), "Local change scope differs")
        for x in [p, *list(p.parents)[: len(Path(rel).parts)]]:
            require(not x.is_symlink(), "Linked local change")
        require(descriptor(p) == desc, "Local source/patch bytes changed: " + rel)
        bindings[str(p)] = desc

    checked(patch["path"], {k: patch[k] for k in ["bytes", "sha256"]}, "artifacts")
    require(
        type(item["files"]) is dict and item["files"],
        "Changed source file descriptors required",
    )
    for rel, desc in item["files"].items():
        checked(rel, desc, "sglang")
    return changes, bindings


def cli_flags(arguments):
    out = []
    for key, value in arguments.items():
        require(key.startswith("--"), "Invalid flag")
        if value is True:
            out.append(key)
        elif value is not False and value is not None:
            out.extend([key, str(value)])
    return out


def environment(cfg, arm, runtime_project):
    rt = cfg["runtime"]
    run = Path(rt["run_root"])
    comp = run / "caches/compile"
    tactics = run / "caches/tactics" / arm["id"] / "tp8"
    python = rt["python"]
    # Planned child environment only, no host inheritance. Actual image loader/HOME/library
    # context must be reviewed before any future execution implementation is authorized.
    env = {
        "PATH": str(Path(python).parent)
        + ":/usr/local/cuda/bin:/usr/local/nvidia/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONPATH": rt["sglang_root"]
        + "/python:"
        + str(Path(runtime_project) / "vendor/inferencex"),
        "PYTHONNOUSERSITE": "1",
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "TMPDIR": rt["tmp_root"],
        "HF_HOME": str(run / "hf-home"),
        "HF_HUB_OFFLINE": "1",
        "TRANSFORMERS_OFFLINE": "1",
        "CUDA_VISIBLE_DEVICES": "0,1,2,3,4,5,6,7",
        "SGLANG_CACHE_DIR": str(tactics),
    }
    cache_keys = {
        "FLASHINFER_WORKSPACE_BASE": "flashinfer",
        "CUTE_DSL_CACHE_DIR": "cute-dsl",
        "CUDA_CACHE_PATH": "cuda",
        "TORCH_EXTENSIONS_DIR": "torch-extensions",
        "TORCHINDUCTOR_CACHE_DIR": "torchinductor",
        "TRITON_CACHE_DIR": "triton",
        "TILELANG_CACHE_DIR": "tilelang",
        "SGLANG_DG_CACHE_DIR": "deep-gemm",
        "SGLANG_CUTE_AOT_CACHE_DIR": "cute-aot",
        "SGLANG_JIT_CACHE_DIR": "sglang-jit",
        "XDG_CACHE_HOME": "xdg",
    }
    env.update({key: str(comp / leaf) for key, leaf in cache_keys.items()})
    env.update(arm["environment"])
    return env


def execution_blockers(cfg, runtime_project):
    issues = [f"{x['id']}: {x['detail']}" for x in cfg["blockers"]]
    if cfg["authorization"] != "EXECUTE_AUTHORIZED":
        issues.append("authorization is " + cfg["authorization"])
    if cfg["status"] != "READY_FOR_EXECUTION":
        issues.append("campaign status is " + cfg["status"])
    if not cfg["checkpoint"]["local_tensor_verification"]:
        issues.append("Local checkpoint tensor verification is absent")
    for key, value in {
        **cfg["runtime"],
        "runtime_project_root": runtime_project,
    }.items():
        if isinstance(value, str) and "REVIEW_REQUIRED" in value:
            issues.append("Unresolved " + key + ": " + value)
    for key in ("prior_acceptance", "cache_seed_acceptance"):
        row = cfg["continuation"][key]
        if row["bytes"] <= 0 or "REVIEW_REQUIRED" in row["path"]:
            issues.append("Actual continuation input absent: " + key)
    return issues


def build_plan(
    campaign_path=ROOT / "campaign.json",
    project=ROOT,
    runtime_project="/REVIEW_REQUIRED/kimi-k3-project",
):
    campaign_path = Path(campaign_path).resolve()
    project = Path(project).resolve()
    canonical_path(runtime_project)
    cfg = read_json(campaign_path)
    validate_campaign(cfg)
    client = verify_client(project, cfg["pins"]["client_inferencex"])
    local_changes, local_bindings = verify_local_changes(cfg, project)
    tokenizer, tokenizer_bindings = verify_tokenizer(project, cfg)
    bindings = {
        str(campaign_path): descriptor(campaign_path),
        **client["bindings"],
        **local_bindings,
        **tokenizer_bindings,
    }
    for name in [
        "plan.py",
        "run_campaign.py",
        "execution.py",
        "results.py",
        "checkpoint_contract.py",
        "source_contract.py",
        "continuation.py",
        "cache_seed.py",
    ]:
        p = project / "setup" / name
        require(p.is_file(), "Missing required execution source: " + name)
        bindings[str(p)] = descriptor(p)
    cases = []
    rt = cfg["runtime"]
    w = cfg["workload"]
    for arm in cfg["arms"]:
        for c in w["order"]:
            case_id = f"{arm['id']}-tp8-ep8-dp1-c{c}"
            case_dir = str(Path(rt["run_root"]) / "cases" / case_id)
            args = {
                "--model-path": rt["model_path"],
                **cfg["common_server_args"],
                **arm["server_args"],
                "--max-running-requests": c,
                "--cuda-graph-max-bs-decode": max(c, 8),
            }
            server = [
                rt["python"],
                "-B",
                "-m",
                "sglang.launch_server",
                *cli_flags(args),
            ]
            bargs = {
                "--backend": "vllm",
                "--host": "127.0.0.1",
                "--port": 30000,
                "--endpoint": "/v1/completions",
                "--dataset-name": "random",
                "--model": COMMON["--served-model-name"],
                "--tokenizer": rt["model_path"],
                "--tokenizer-mode": "auto",
                "--trust-remote-code": True,
                "--random-input-len": 1024,
                "--random-output-len": 8192,
                "--random-range-ratio": 0.8,
                "--random-prefix-len": 0,
                "--seed": 0,
                "--request-rate": "inf",
                "--burstiness": 1.0,
                "--max-concurrency": c,
                "--num-warmups": 2 * c,
                "--num-prompts": 10 * c,
                "--ignore-eos": True,
                "--use-chat-template": True,
                "--save-result": True,
                "--result-dir": case_dir,
                "--result-filename": "result.json",
                "--percentile-metrics": "ttft,tpot,itl,e2el",
                "--metric-percentiles": "90,99,99.9",
            }
            bench = [rt["python"], "-B", "-m", client["module"], *cli_flags(bargs)]
            # Assert each rendered client option exists in the actual pinned parser source without importing it.
            tree = ast.parse(
                (
                    project
                    / "vendor/inferencex/infx/bench_serving/benchmark_serving.py"
                ).read_bytes()
            )
            supported = {
                a.value
                for n in ast.walk(tree)
                if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "add_argument"
                for a in n.args
                if isinstance(a, ast.Constant)
                and isinstance(a.value, str)
                and a.value.startswith("--")
            }
            require(set(bargs) <= supported, "Client plan includes unsupported flag")
            env = environment(cfg, arm, runtime_project)
            expected = {
                "model_path": rt["model_path"],
                "tp_size": 8,
                "ep_size": 8,
                "dp_size": 1,
                "enable_dp_attention": False,
                "pp_size": 1,
                "dcp_size": 1,
                "max_running_requests": c,
                "cuda_graph_max_bs_decode": max(c, 8),
                "chunked_prefill_size": 32768,
                "max_prefill_tokens": 32768,
                "speculative_algorithm": None,
                "quantization": "modelopt_fp4",
                "dtype": "bfloat16",
                "mem_fraction_static": 0.85,
                "kv_cache_dtype": "fp8_e4m3",
                "mamba_ssm_dtype": "float32",
                "disable_radix_cache": True,
                "stream_interval": 30,
                "moe_runner_backend": arm["server_args"]["--moe-runner-backend"],
                "moe_a2a_backend": arm["server_args"]["--moe-a2a-backend"],
            }
            cases.append(
                {
                    "case_id": case_id,
                    "arm_id": arm["id"],
                    "label": arm["label"],
                    "precision": "w4a16" if arm["id"] == "megamoe-w4a16" else "w4a4",
                    "backend": arm["server_args"]["--moe-runner-backend"],
                    "tp": 8,
                    "ep": 8,
                    "dp": 1,
                    "attention_tp": 8,
                    "moe_tp": 1,
                    "mega_local_decode_bound": (c + 7) // 8
                    if arm["id"].startswith("megamoe")
                    else None,
                    "mega_local_prefill_bound": 4096
                    if arm["id"].startswith("megamoe")
                    else None,
                    "concurrency": c,
                    "warmup_requests": 2 * c,
                    "measured_requests": 10 * c,
                    "server_max_running_requests": c,
                    "decode_graph_max_bs": max(c, 8),
                    "effective_per_dp_request_capacity": c,
                    "case_dir": case_dir,
                    "server_argv": server,
                    "client_argv": bench,
                    "environment": env,
                    "compile_cache_root": str(Path(rt["run_root"]) / "caches/compile"),
                    "tactic_cache_root": env["SGLANG_CACHE_DIR"],
                    "expected_server_info": expected,
                    "runtime_expectations_validated": False,
                    "evidence_contract": {
                        "status": "DESIGN_ONLY_NO_EVIDENCE_PRODUCED",
                        "files": FUTURE_FILES,
                    },
                }
            )
    require(
        len(cases) == 12
        and sum(x["warmup_requests"] for x in cases) == 360
        and sum(x["measured_requests"] for x in cases) == 1800,
        "Matrix totals differ",
    )
    return {
        "schema_version": 1,
        "status": "REVIEW_ONLY_NOT_EXECUTABLE",
        "executable": False,
        "campaign": {"path": str(campaign_path), **descriptor(campaign_path)},
        "name": cfg["name"],
        "pins": cfg["pins"],
        "local_changes": local_changes,
        "checkpoint": cfg["checkpoint"],
        "hardware": cfg["hardware"],
        "workload": w,
        "runtime_project_root": runtime_project,
        "client_source": client,
        "tokenizer_source": tokenizer,
        "cases": cases,
        "continuation": cfg["continuation"],
        "execution_totals": cfg["continuation"]["execution_totals"],
        "totals": {"cases": 12, "warmup_requests": 360, "measured_requests": 1800},
        "environment_policy": "Planned explicit child environment; no host inheritance or HOME reassignment. No tuning/per-token/fast-math/INFO overrides. Only MegaMoE W4A16 has its required precision selector. Future preflight must capture actual image PATH/loader/library/HOME and any verified Rust policy before execution.",
        "execution_blockers": execution_blockers(cfg, runtime_project),
        "bindings": bindings,
        "limitations": [
            "Commands are reviewed intentions, not runtime evidence. All arms explicitly declare the accepted modelopt_fp4 checkpoint format because this pinned Kimi resolution path does not propagate ModelConfig autodetection into ServerArgs before the Mega gate. Exactly the reviewed three-file SG561ad Kimi SP-MoE admission/local-capacity patch is required; no quantization tuning override is used. Custom output, exclusions, non-routed tensor preservation and numerical checks are governed by the exact normalized conversion acceptance; this planner does not independently validate that receipt.",
            "No speculation/MTP on any arm; no target/draft tensor or installed-kernel claims.",
            "Runtime paths, tensor presence, installed origins, native defaults, image loader/library/HOME/Rust policy and GPU UUID ownership require later accepted preflight. This is not a hermetic execution environment acceptance.",
            "Execution requires the separate root-accepted runtime marker and exact SHA256. The plan alone never starts work; execution.py records owned PID/birth cleanup, endpoint ownership, ordered lengths and terminal seals.",
            "This planner performs no node, conversion, package, benchmark or publication operation. Conversion evidence belongs to its separate project; no Kimi serving measurement is claimed.",
        ],
    }


def commands_markdown(plan):
    lines = [
        "# Kimi K3 commands for review",
        "",
        "**PLAN ONLY:** these command renderings do not execute. Use run_campaign.py --execute with the exact accepted runtime marker and SHA256 after campaign blockers are resolved. Checkpoint acceptance alone is insufficient.",
        "",
        "Canonical 12 cases/360 warmups/1,800 measured; this continuation executes only 11 cases/296 warmups/1,480 measured and inherits one independently accepted C32. No MTP. Commands use a clean explicit environment; do not run them before the source/preflight/execution gates are accepted.",
        "",
        "The files below are plain text, mode0600, with no shebang. Each example is an argument-vector rendering for review, not a launcher.",
        "",
    ]
    for c in plan["cases"]:
        env = ["env", "-i"] + [k + "=" + v for k, v in sorted(c["environment"].items())]
        lines.extend(
            [
                "## " + c["case_id"],
                "",
                f"Client C{c['concurrency']}; server limit{c['server_max_running_requests']}; graph maximum{c['decode_graph_max_bs']}; warmup{c['warmup_requests']}; measured{c['measured_requests']}.",
                "",
                "```sh",
                shlex.join(env + c["server_argv"]),
                shlex.join(env + c["client_argv"]),
                "```",
                "",
            ]
        )
    lines.extend(
        ["## Gates", ""] + ["- " + x for x in plan["execution_blockers"]] + [""]
    )
    return "\n".join(lines)


def emit_plan(plan, output):
    output = canonical_path(str(output))
    for p in [output, *output.parents]:
        require(not p.is_symlink(), "Linked output ancestor: " + str(p))
    require(output.parent.is_dir(), "Output parent must already exist")
    for path, expected in plan["bindings"].items():
        require(descriptor(path) == expected, "Input changed before emission: " + path)
    output.mkdir(mode=0o700)  # Existing output is never resumed or overwritten.

    def write(name, data):
        with (output / name).open("xb") as f:
            f.write(data)
        (output / name).chmod(0o600)

    write(
        "PLAN.json",
        (json.dumps(plan, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(),
    )
    write("COMMANDS.md", commands_markdown(plan).encode())
    command_dir = output / "commands"
    command_dir.mkdir(mode=0o700)
    for c in plan["cases"]:
        env = ["env", "-i"] + [k + "=" + v for k, v in sorted(c["environment"].items())]
        text = (
            (
                "# INHERITED ACCEPTED C32: do not execute again.\n"
                if c["case_id"] == continuation.PRIOR_ID
                else "# REVIEW ONLY: selected continuation case.\n"
            )
            + shlex.join(env + c["server_argv"])
            + "\n"
            + shlex.join(env + c["client_argv"])
            + "\n"
        )
        write("commands/" + c["case_id"] + ".txt", text.encode())
    manifest = {
        "status": "LOCAL_DRY_RUN_EMITTED_NO_EXECUTION",
        "files": {
            str(p.relative_to(output)): descriptor(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    }
    write(
        "MANIFEST.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(),
    )
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--campaign", type=Path, default=ROOT / "campaign.json")
    ap.add_argument("--dry-run", action="store_true", help="Default and only mode")
    ap.add_argument("--output", type=Path)
    ap.add_argument(
        "--runtime-project-root", default="/REVIEW_REQUIRED/kimi-k3-project"
    )
    args = ap.parse_args(argv)
    plan = build_plan(args.campaign, runtime_project=args.runtime_project_root)
    if args.output:
        manifest = emit_plan(plan, args.output)
        print(
            json.dumps(
                {
                    "status": manifest["status"],
                    "output": str(args.output),
                    "totals": plan["totals"],
                    "execution_blockers": plan["execution_blockers"],
                }
            )
        )
    else:
        print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
