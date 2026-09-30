#!/usr/bin/env python3
"""Explicit Kimi runtime/metadata probe. No install, model construction or serving."""

from __future__ import annotations
import argparse
import datetime
import hashlib
import importlib
import importlib.metadata as metadata
import json
import os
from pathlib import Path
import site
import socket
import stat
import subprocess
import sys
from types import SimpleNamespace

if not __debug__:
    raise RuntimeError("Optimized Python prohibited")
import source_contract

SG = "561ad447c74bb757a40677ee9ce038f9ca429d2c"
FI = "a03f2205263d4e691d68e485bff287e37a19b6c3"
PROJECT = "/data/home/ziangli/inferencex-kimik3-three-curves-c32-20260929/r4"
MODEL = "/data/home/ziangli/kimik3-routed-nvfp4-conversion-20260929/checkpoints/main-routed-nvfp4-attempt2"
ARMS = ("megamoe-w4a4", "megamoe-w4a16", "trtllm-w4a4")
SELECTOR = "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16"
FORBIDDEN = (
    "SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION",
    "SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE",
    "SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE",
    "SGLANG_FLASHINFER_MEGAMOE_MAX_TOKENS_PER_RANK",
    "FLASHINFER_DISABLE_FP4_QUANT_FAST_MATH",
    "TRTLLM_DISABLE_FP4_QUANT_FAST_MATH",
    "FLASHINFER_AUTOTUNE_TIMER",
    "SGLANG_FLASHINFER_AUTOTUNE_EXTEND",
    "SGLANG_FLASHINFER_AUTOTUNE_CACHE",
    "FLASHINFER_MOE_EP_KNOB_CACHE",
    "LD_PRELOAD",
    "NVSHMEM_REMOTE_TRANSPORT",
    "NVSHMEM_IB_ENABLE_IBGDA",
    "NVSHMEM_DISABLE_LOCAL_ONLY_PROXY",
    "SGLANG_BUILD_COMMIT",
    "SGLANG_BUILD_URL",
    "SGLANG_IMAGE_TAG",
)
METADATA = (
    "config.json",
    "hf_quant_config.json",
    "model.safetensors.index.json",
    "tokenizer_config.json",
    "tokenization_kimi.py",
    "encoding_k3.py",
    "tiktoken.model",
    "generation_config.json",
)


def need(ok, msg):
    if not ok:
        raise RuntimeError(msg)


def parse(data):
    def pairs(rows):
        out = {}
        for k, v in rows:
            need(k not in out, "Duplicate JSON key")
            out[k] = v
        return out

    return json.loads(
        data,
        object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
    )


def path(value):
    p = Path(value)
    need(
        p.is_absolute()
        and str(p) == value
        and ".." not in p.parts
        and p.resolve() == p,
        "Noncanonical/linked path: " + value,
    )
    return p


def identity(s):
    return {
        "inode": s.st_ino,
        "size": s.st_size,
        "mtime_ns": s.st_mtime_ns,
        "ctime_ns": s.st_ctime_ns,
    }


def digest(filename, expected=None, limit=256 << 20):
    p = path(str(filename))
    before = p.lstat()
    need(
        stat.S_ISREG(before.st_mode) and before.st_size <= limit,
        "Nonregular/oversize control: " + str(p),
    )
    h = hashlib.sha256()
    count = 0
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        need(
            os.fstat(fd).st_ino == before.st_ino
            and os.fstat(fd).st_dev == before.st_dev,
            "Opened file differs",
        )
        while count < before.st_size:
            data = os.read(fd, min(1 << 20, before.st_size - count))
            need(data, "Short control read")
            h.update(data)
            count += len(data)
        need(not os.read(fd, 1), "Control grew")
        need(
            identity(os.fstat(fd)) == identity(before) == identity(p.lstat()),
            "Control changed",
        )
    finally:
        os.close(fd)
    d = {"bytes": count, "sha256": h.hexdigest()}
    if expected is not None:
        need(d == expected, "Control bytes differ: " + str(p))
    return d


def command(argv):
    # Fixed local query commands only. No shell, no model command or installer.
    r = subprocess.run(
        argv,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=30,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"},
    )
    need(len(r.stdout) + len(r.stderr) <= 1 << 20, "Query output overflow")
    need(
        r.returncode == 0,
        "Query failed: " + repr(argv) + " " + r.stderr.decode(errors="replace")[:2000],
    )
    return r.stdout.decode().strip()


def gpu_query(expected, allow_own=False):
    text = command(
        [
            "nvidia-smi",
            "--query-gpu=index,uuid,name,utilization.gpu,memory.used",
            "--format=csv,noheader,nounits",
        ]
    )
    rows = []
    for line in text.splitlines():
        x = [s.strip() for s in line.split(",")]
        need(len(x) == 5, "GPU query shape")
        rows.append(
            {
                "index": int(x[0]),
                "uuid": x[1],
                "name": x[2],
                "utilization": int(x[3]),
                "memory_mib": int(x[4]),
            }
        )
    need(
        len(rows) == 8
        and [{k: r[k] for k in ("index", "uuid", "name")} for r in rows] == expected,
        "GPU identity differs",
    )
    need(
        len({r["uuid"] for r in rows}) == 8
        and all("B300" in r["name"] and r["utilization"] == 0 for r in rows),
        "Unexpected/busy GPU",
    )
    apps = command(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,gpu_uuid",
            "--format=csv,noheader,nounits",
        ]
    )
    processes = []
    for line in apps.splitlines():
        x = [s.strip() for s in line.split(",")]
        need(len(x) == 2 and x[0].isdigit(), "GPU app query shape")
        processes.append({"pid": int(x[0]), "uuid": x[1]})
    need(
        all(
            allow_own
            and x["pid"] == os.getpid()
            and x["uuid"] in {r["uuid"] for r in rows}
            for x in processes
        ),
        "Other GPU applications active",
    )
    if not allow_own:
        need(all(r["memory_mib"] <= 100 for r in rows), "GPU memory not idle")
    return {
        "gpus": rows,
        "applications": processes,
        "only_probe_context_permitted": allow_own,
    }


def port_free(port):
    need(type(port) is int and port == 30000, "Unreviewed endpoint port")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))


def validate_request(r):
    required = {
        "schema_version",
        "remote_project",
        "sglang_root",
        "flashinfer_source_root",
        "run_root",
        "tmp_root",
        "port",
        "node",
        "gpus",
        "bound_files",
        "checkpoint",
        "protected_runtime_files",
        "provider_versions",
        "server_args",
        "source_patch",
    }
    need(set(r) == required and r["schema_version"] == 1, "Request schema differs")
    need(
        r["source_patch"] == source_contract.PATCH,
        "Exact source patch contract differs",
    )
    need(
        r["remote_project"] == PROJECT
        and r["sglang_root"] == str(Path(PROJECT).parent / "sources/sglang-r3"),
        "Separate Kimi source path required",
    )
    need(
        r["run_root"]
        == str(Path(PROJECT).parent / "kimi-k3-ep8-three-curves-c32-20260929-all12-r4")
        and r["tmp_root"] == "/tmp/infx-k3-preflight-r4",
        "Run/preflight scope differs",
    )
    need(
        set(r["node"]) == {"hostname", "pod_uid", "sts_uid", "image_id"},
        "Node schema differs",
    )
    need(
        len(r["gpus"]) == 8 and [x["index"] for x in r["gpus"]] == list(range(8)),
        "Eight ordered GPUs required",
    )
    ck = r["checkpoint"]
    need(
        set(ck)
        == {"path", "acceptance_path", "acceptance_sha256", "shards", "sidecars"}
        and ck["path"] == MODEL,
        "Checkpoint contract differs",
    )
    need(
        len(ck["shards"]) == 96
        and len(ck["sidecars"]) == 24
        and set(METADATA) <= set(ck["sidecars"]),
        "Checkpoint file closure differs",
    )
    need(set(r["server_args"]) == set(ARMS), "Three arm CLI lists required")
    for arm, args in r["server_args"].items():
        need(
            isinstance(args, list) and all(isinstance(x, str) for x in args),
            "CLI must be string vector",
        )
        need(
            "--model-path" in args and args[args.index("--model-path") + 1] == MODEL,
            "CLI checkpoint differs",
        )
        need(
            args.count("--quantization") == 1
            and args[args.index("--quantization") + 1 :][:1] == ["modelopt_fp4"]
            and not any(
                x.startswith("--quantization=") or x.startswith("--speculative")
                for x in args
            ),
            "Exact common checkpoint format modelopt_fp4 and no speculation required",
        )
        runner = "flashinfer_trtllm" if arm == "trtllm-w4a4" else "flashinfer_megamoe"
        a2a = "none" if arm == "trtllm-w4a4" else "flashinfer_megamoe"
        need(
            args[args.index("--moe-runner-backend") + 1] == runner
            and args[args.index("--moe-a2a-backend") + 1] == a2a,
            "Backend CLI differs",
        )
    need(
        r["protected_runtime_files"] and r["provider_versions"],
        "Actual restored runtime baseline required",
    )
    need(
        set(r["provider_versions"])
        <= {
            "torch",
            "transformers",
            "sgl-kernel",
            "flashinfer-python",
            "flashinfer-cubin",
            "nvidia-cutlass-dsl",
            "nccl-extensions",
            "nccl4py",
            "nvshmem4py-cu13",
        },
        "Unknown provider baseline",
    )
    for name in (
        "remote_project",
        "sglang_root",
        "flashinfer_source_root",
        "run_root",
        "tmp_root",
    ):
        path(r[name])


def environment(arm, r):
    need(
        arm in ARMS
        and os.environ.get(SELECTOR) == ("1" if arm == "megamoe-w4a16" else None),
        "Arm selector differs",
    )
    bad = [
        k
        for k in os.environ
        if k in FORBIDDEN or k.startswith("FLASHINFER_NVFP4_4OVER6")
    ]
    need(not bad, "Optional/runtime-misleading overrides: " + repr(bad))
    need(
        os.environ.get("CUDA_VISIBLE_DEVICES") == "0,1,2,3,4,5,6,7",
        "Visible devices differ",
    )
    need(
        os.environ.get("HF_HUB_OFFLINE") == "1"
        and os.environ.get("TRANSFORMERS_OFFLINE") == "1",
        "Offline model resolution required",
    )
    need(os.environ.get("TMPDIR") == r["tmp_root"], "TMP scope differs")
    need(
        os.environ.get("PYTHONPATH")
        == r["sglang_root"] + "/python:" + PROJECT + "/vendor/inferencex",
        "Import path differs",
    )
    # Preserve an observed image Rust policy; never initiate a Cargo build here.
    need(
        os.environ.get("SGLANG_RUST_BUILD_MODE") == "never",
        "Explicit observed Rust-never policy required",
    )
    for key in (
        "SGLANG_CACHE_DIR",
        "FLASHINFER_WORKSPACE_BASE",
        "CUTE_DSL_CACHE_DIR",
        "CUDA_CACHE_PATH",
        "TORCH_EXTENSIONS_DIR",
        "TORCHINDUCTOR_CACHE_DIR",
        "TRITON_CACHE_DIR",
        "TILELANG_CACHE_DIR",
        "SGLANG_DG_CACHE_DIR",
        "SGLANG_CUTE_AOT_CACHE_DIR",
        "SGLANG_JIT_CACHE_DIR",
        "XDG_CACHE_HOME",
        "HF_HOME",
    ):
        v = os.environ.get(key, "")
        need(
            v.startswith(PROJECT + "/preflight/")
            and path(v).is_relative_to(Path(PROJECT) / "preflight"),
            "Private prep cache required: " + key,
        )
    tmp = path(r["tmp_root"])
    s = tmp.lstat()
    need(
        stat.S_ISDIR(s.st_mode)
        and stat.S_IMODE(s.st_mode) == 0o700
        and s.st_uid == os.getuid(),
        "Private TMP required",
    )
    marker = tmp / ".kimi-preflight-owner.json"
    need(str(marker) in r["bound_files"], "Bound TMP marker required")
    digest(marker, r["bound_files"][str(marker)])
    owner = parse(marker.read_bytes())
    need(
        owner["tmp_root"] == str(tmp)
        and owner["directory_identity"]
        == {"device": s.st_dev, "inode": s.st_ino, "uid": s.st_uid},
        "TMP inode owner differs",
    )
    need(
        not os.path.lexists(r["run_root"])
        and not os.path.lexists("/tmp/infx-k3-3c-r4"),
        "Actual run/TMP must remain absent",
    )
    return {
        k: v
        for k, v in os.environ.items()
        if k.startswith(("SGLANG_", "FLASHINFER_"))
        or k
        in (
            "PATH",
            "LD_LIBRARY_PATH",
            "CUDA_HOME",
            "PYTHONPATH",
            "TMPDIR",
            "HF_HOME",
            "HF_HUB_OFFLINE",
            "TRANSFORMERS_OFFLINE",
            "CUDA_VISIBLE_DEVICES",
        )
    }


def checkpoint(r):
    ck = r["checkpoint"]
    root = path(ck["path"])
    before = root.lstat()
    need(stat.S_ISDIR(before.st_mode), "Checkpoint root absent")
    need(
        ck["acceptance_path"] in r["bound_files"],
        "Acceptance must be exact bound control",
    )
    acceptance_d = digest(
        ck["acceptance_path"], r["bound_files"][ck["acceptance_path"]]
    )
    need(acceptance_d["sha256"] == ck["acceptance_sha256"], "Acceptance SHA differs")
    accepted = parse(Path(ck["acceptance_path"]).read_bytes())
    need(
        accepted["status"] == "ACCEPTED_CUSTOM_ROUTED_NVFP4"
        and accepted["data_kind"] == "actual"
        and accepted["output_path"] == MODEL
        and accepted["scope"] == "main_language_routed_experts_only",
        "Actual normalized acceptance required",
    )
    need(
        set(accepted["checks"])
        == {
            "original_published_file_hashes",
            "bf16_non_routed_tensor_bytes",
            "nvfp4_non_routed_tensor_bytes",
            "routed_scope_shapes_dtypes_scales",
            "numerical_conversion_checks",
            "non_routed_linear_exclusions",
            "metadata_tokenizer_preservation",
        }
        and all(v is True for v in accepted["checks"].values()),
        "Accepted checks incomplete",
    )
    expected = set(ck["shards"]) | set(ck["sidecars"])
    seen = set()
    dirs = {".eval_results", "assets"}
    for base, children, files in os.walk(root, followlinks=False):
        b = Path(base)
        for n in children:
            q = b / n
            rel = q.relative_to(root).as_posix()
            need(rel in dirs and not q.is_symlink(), "Unexpected checkpoint directory")
        for n in files:
            q = b / n
            rel = q.relative_to(root).as_posix()
            need(not q.is_symlink() and rel in expected, "Unexpected checkpoint file")
            seen.add(rel)
    need(seen == expected, "Checkpoint file closure differs")
    observed = {}
    for n, row in ck["shards"].items():
        need("/" not in n and n.endswith(".safetensors"), "Invalid shard name")
        p = path(str(root / n))
        s = p.lstat()
        need(
            stat.S_ISREG(s.st_mode)
            and s.st_size == row["bytes"]
            and identity(s) == row["stat"],
            "Shard historical identity differs: " + n,
        )
        observed[n] = identity(s)
    for n, d in ck["sidecars"].items():
        digest(root / n, d)
    for n in METADATA:
        need(
            all(
                accepted["metadata"][n][k] == ck["sidecars"][n][k]
                for k in ("bytes", "sha256")
            ),
            "Acceptance metadata differs: " + n,
        )
    config = parse((root / "config.json").read_bytes())
    q = config["quantization_config"]
    need(
        q["quant_method"] == "modelopt"
        and q["quant_algo"] == "NVFP4"
        and q["group_size"] == 16
        and q["ignore"]
        and not config.get("text_config", {}).get("quantization_config"),
        "Standard routed NVFP4 metadata required",
    )
    need(identity(root.lstat()) == identity(before), "Checkpoint root changed")
    return {
        "acceptance": acceptance_d,
        "files": 120,
        "shards": observed,
        "sidecar_hashes": ck["sidecars"],
        "tensor_hashes_recomputed": False,
        "scope": "96 shard identity/size checks against accepted inventory;24 metadata fresh hashes. No tensor payload reads.",
    }


def rust_visibility():
    # Inspect only these fixed optional modules. Never invoke the Rust loader's
    # fingerprint/Cargo path or construct a cache/server; disabled radix + HTTP
    # does not select these optional runtime backends.
    modules = {
        "sglang.srt.mem_cache.rust_tree_core.mem_cache": (
            "DecLockRefParamsBinding",
            "InsertParamsBinding",
            "MatchParamsBinding",
            "RustBigramUnifiedTreeCoreBinding",
            "RustUnifiedTreeCoreBinding",
            "TreeCoreInitParamsBinding",
        ),
        "sglang.srt.rust_extensions._server": ("Server", "ServerArgs"),
        "sglang.srt.rust_extensions._grpc": ("start_server",),
    }
    rows = {}
    for name, apis in modules.items():
        spec = importlib.util.find_spec(name)
        if spec is None:
            rows[name] = {
                "visible": False,
                "loaded": False,
                "selected_by_campaign": False,
            }
            continue
        path = Path(spec.origin).resolve()
        need(
            any(str(path).endswith(s) for s in importlib.machinery.EXTENSION_SUFFIXES),
            "Rust module is not a native extension",
        )
        before = {"path": str(path), **digest(path)}
        module = importlib.import_module(name)
        need(
            Path(module.__file__).resolve() == path
            and {"path": str(path), **digest(path)} == before,
            "Rust extension origin changed",
        )
        need(
            all(callable(getattr(module, key, None)) for key in apis),
            "Rust extension API differs: " + name,
        )
        rows[name] = {
            "visible": True,
            "loaded": True,
            "selected_by_campaign": False,
            "file": before,
            "apis": list(apis),
        }
    return {
        "policy": "never",
        "cargo_invocations": 0,
        "modules": rows,
        "limit": "Visibility and import/API evidence only; disabled radix cache with chunked prefill selects ChunkCache and HTTP does not select Rust server/grpc. Actual loaded model behavior remains a first-case gate.",
    }


def protected_runtime(r):
    # Exact root-approved native binaries may exceed the metadata/control cap.
    # Keep streaming and all identity checks; no model/tensor path is added.
    return {
        p: digest(p, d, limit=1 << 30) for p, d in r["protected_runtime_files"].items()
    }


def providers(r, arm):
    import torch
    import sglang
    import flashinfer
    import flashinfer_cubin
    from flashinfer import _build_meta as main
    from flashinfer_cubin import _build_meta as cubin
    from flashinfer.jit import env as jit_env

    need(
        Path(sglang.__file__)
        .resolve()
        .is_relative_to(Path(r["sglang_root"]) / "python"),
        "Wrong SGLang import origin",
    )
    roots = [Path(x).resolve() for x in site.getsitepackages()]
    for m in (flashinfer, flashinfer_cubin):
        need(
            any(Path(m.__file__).resolve().is_relative_to(p) for p in roots),
            "Unbuilt FI source shadowed installed provider",
        )
    need(
        main.__git_commit__ == cubin.__git_version__ == FI
        and flashinfer.__version__ == flashinfer_cubin.__version__,
        "FlashInfer pair pin differs",
    )
    need(not jit_env.FLASHINFER_AOT_PROVIDERS, "Stale AOT provider")
    modules = (
        "sglang.srt.models.kimi_k3",
        "sglang.srt.layers.quantization.modelopt_quant",
        "sglang.srt.layers.moe.flashinfer_megamoe",
        "flashinfer.moe_ep",
        "flashinfer.fused_moe",
    )
    loaded = {n: importlib.import_module(n) for n in modules}
    need(
        callable(loaded[modules[0]].KimiK3ForConditionalGeneration),
        "Kimi model class missing",
    )
    moe = loaded["flashinfer.moe_ep"]
    model_config = parse((Path(MODEL) / "config.json").read_bytes())["text_config"]
    geometry = {
        "intermediate_size": model_config["moe_intermediate_size"],
        "top_k": model_config["num_experts_per_token"],
    }
    activation = loaded[
        "sglang.srt.layers.moe.flashinfer_megamoe"
    ]._nvfp4_megamoe_activation_kwargs(
        SimpleNamespace(
            is_gated=True,
            activation=model_config["hidden_act"],
            gemm1_alpha=model_config["activation_situ_beta"],
            gemm1_clamp_limit=model_config["activation_situ_linear_beta"],
        )
    )
    a = moe.Nvfp4CutedslMegaMoeConfig(**geometry, **activation)
    b = moe.Sm100_Bf16_Nvfp4_Bf16_Cutedsl_MegaMoeConfig(**geometry, **activation)
    need(
        (
            a.fast_math,
            a.combine_dtype,
            a.enable_in_kernel_fc2_reduce,
            a.apply_topk_in_fc1,
        )
        == (True, "bf16", False, True),
        "W4A4 native defaults differ",
    )
    need(
        (b.enable_in_kernel_fc2_reduce, b.apply_topk_in_fc1) == (False, False),
        "W4A16 native defaults differ",
    )
    for module, names in [
        (
            moe,
            [
                "MoEEpMegaLayer",
                "BootstrapConfig",
                "FleetParams",
                "MegaConfig",
                "MoEWeightPack",
                "preprocess_nvfp4_cutedsl_mega_weights",
                "preprocess_bf16_nvfp4_cutedsl_mega_weights",
            ],
        ),
        (
            loaded["flashinfer.fused_moe"],
            ["trtllm_fp4_block_scale_moe", "trtllm_fp4_block_scale_routed_moe"],
        ),
    ]:
        for name in names:
            need(
                callable(getattr(module, name, None)),
                "Required native API missing: " + name,
            )
    from sglang.srt.environ import envs

    defaults = {
        n: getattr(envs, n).get()
        for n in (
            "SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION",
            "SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE",
            "SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE",
            SELECTOR,
        )
    }
    need(
        list(defaults.values()) == [False, "bf16", False, arm == "megamoe-w4a16"],
        "Loaded SG defaults differ",
    )
    from sglang.srt.server_args import prepare_server_args

    args = prepare_server_args(r["server_args"][arm])
    args.resolve_once()
    from sglang.srt.arg_groups.overrides import resolved_view

    view = resolved_view(args)
    expected = {
        "quantization": "modelopt_fp4",
        "tp_size": 8,
        "ep_size": 8,
        "dp_size": 1,
        "pp_size": 1,
        "enable_dp_attention": False,
        "speculative_algorithm": None,
        "disable_radix_cache": True,
        "chunked_prefill_size": 32768,
        "max_running_requests": 32,
        "cuda_graph_max_bs_decode": 32,
    }
    resolved = {k: getattr(view, k) for k in expected}
    need(
        resolved == expected,
        "Resolved first-C32 server configuration differs: " + repr(resolved),
    )
    versions = {}
    for name in (
        "torch",
        "transformers",
        "sgl-kernel",
        "flashinfer-python",
        "flashinfer-cubin",
        "nvidia-cutlass-dsl",
        "nccl-extensions",
        "nccl4py",
        "nvshmem4py-cu13",
    ):
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    for n, v in r["provider_versions"].items():
        need(versions.get(n) == v, "Baseline package version differs: " + n)
    files = {}
    for m in (
        torch,
        sglang,
        flashinfer,
        flashinfer_cubin,
        main,
        cubin,
        *loaded.values(),
    ):
        p = Path(m.__file__).resolve()
        files[str(p)] = digest(p)
    protected = protected_runtime(r)
    need(torch.cuda.device_count() == 8, "Eight visible CUDA devices required")
    devices = []
    peers = []
    for i in range(8):
        p = torch.cuda.get_device_properties(i)
        uuid = str(p.uuid)
        need((p.major, p.minor) == (10, 3) and "B300" in p.name, "B300 required")
        need(
            uuid.removeprefix("GPU-") == r["gpus"][i]["uuid"].removeprefix("GPU-"),
            "Torch GPU UUID differs",
        )
        devices.append(
            {"index": i, "name": p.name, "uuid": uuid, "capability": [p.major, p.minor]}
        )
        row = [
            True if i == j else bool(torch.cuda.can_device_access_peer(i, j))
            for j in range(8)
        ]
        need(all(row), "Peer capability unavailable")
        peers.append(row)
    return {
        "rust": rust_visibility(),
        "versions": versions,
        "torch_cuda": torch.version.cuda,
        "module_files": files,
        "protected_runtime_files": protected,
        "defaults": defaults,
        "resolved_server_args": resolved,
        "peer_devices": devices,
        "peer_matrix": peers,
        "peer_queries": 56,
        "self_entries": 8,
        "cuda_initialized": torch.cuda.is_initialized(),
        "native_config_geometry": geometry,
        "native_activation": activation,
        "native_config_geometry_scope": "API dataclass construction from accepted model logical config, no layer/native workspace construction",
        "no_model_or_collective_launched": True,
    }


def source_environment_changes(before, r):
    """Allow only the pinned OpenCV loader's observed Linux path prepend."""
    changes = {
        k: {"before": v, "after": os.environ.get(k)}
        for k, v in before.items()
        if os.environ.get(k) != v
    }
    if not changes:
        return {}
    need(
        set(changes) == {"LD_LIBRARY_PATH"},
        "Unexpected changed supplied keys: " + repr(sorted(changes)),
    )
    loader = Path("/opt/sglang/lib/python3.12/site-packages/cv2")
    module = sys.modules.get("cv2")
    need(
        sys.version_info[:2] == (3, 12)
        and module is not None
        and Path(module.__file__).resolve() == loader / "__init__.py",
        "OpenCV loader origin differs",
    )
    need(
        not os.path.lexists(loader / "config-3.12.py"),
        "Unexpected OpenCV version-specific config",
    )
    sources = {}
    for name in ("__init__.py", "config.py", "config-3.py", "load_config_py3.py"):
        p = str(loader / name)
        need(p in r["bound_files"], "OpenCV loader source unbound: " + name)
        sources[p] = digest(p, r["bound_files"][p])
    # Keep the lexical ../.. spelling used by the exact observed OpenCV source.
    # The resolved directory was absent; this does not attest to bundled library bytes.
    prefix = os.path.join(os.path.join(str(loader), "../../"), "lib64")
    need(
        changes["LD_LIBRARY_PATH"]["after"] == prefix + ":" + before["LD_LIBRARY_PATH"],
        "Unexpected OpenCV loader path transform",
    )
    changes["LD_LIBRARY_PATH"]["source_files"] = sources
    changes["LD_LIBRARY_PATH"]["scope"] = (
        "Observed import side effect only; supplied launch environment unchanged; no library-directory or library-byte acceptance"
    )
    return changes


def source_snapshot(r):
    source = {}
    for root, pin in [(r["sglang_root"], SG), (r["flashinfer_source_root"], FI)]:
        if pin == SG:
            source[root] = source_contract.patched_source(root)
            continue
        need(
            command(["git", "-C", root, "diff", "--cached", "--name-only"]) == "",
            "Staged FI changes prohibited",
        )
        need(
            command(["git", "-C", root, "rev-parse", "HEAD"]) == pin,
            "Source HEAD differs",
        )
        need(
            command(["git", "-C", root, "diff", "--name-only", "HEAD"]) == "",
            "Tracked source changed",
        )
        untracked = command(
            ["git", "-C", root, "ls-files", "--others", "--exclude-standard"]
        ).splitlines()
        expected_untracked = (
            [
                "LICENSE.cutlass.txt",
                "LICENSE.flashattention3.txt",
                "LICENSE.fmt.txt",
                "LICENSE.spdlog.txt",
            ]
            if pin == FI
            else []
        )
        need(untracked == expected_untracked, "Untracked source closure differs")
        generated = {}
        for n in untracked:
            p = str(Path(root) / n)
            need(p in r["bound_files"], "Generated license missing binding")
            generated[p] = digest(p, r["bound_files"][p])
        source[root] = {
            "commit": pin,
            "submodules": command(["git", "-C", root, "submodule", "status"]),
            "untracked": untracked,
            "generated_files": generated,
        }
    return source


def run(r, arm):
    validate_request(r)
    need(
        sys.platform == "linux" and socket.gethostname() == r["node"]["hostname"],
        "Wrong runtime host",
    )
    need(
        sys.executable == "/opt/sglang/bin/python3" and sys.prefix == "/opt/sglang",
        "Wrong lexical interpreter",
    )
    env = environment(arm, r)
    controls = {p: digest(p, d) for p, d in r["bound_files"].items()}
    port_free(r["port"])
    before = gpu_query(r["gpus"])
    mount = command(["findmnt", "-T", "/data", "-n", "-o", "TARGET,SOURCE,FSTYPE"])
    need(mount.split() == ["/data", "c2-data", "wekafs"], "Weka mount differs")
    source = source_snapshot(r)
    ck = checkpoint(r)
    proof = providers(r, arm)
    need(source_snapshot(r) == source, "Source changed during provider probe")
    port_free(r["port"])
    after = gpu_query(r["gpus"], allow_own=True)
    environment_after = {
        k: v
        for k, v in os.environ.items()
        if k.startswith(("SGLANG_", "FLASHINFER_", "NVSHMEM_", "NCCL_")) or k in env
    }
    changes = source_environment_changes(env, r)
    expected_nv = (
        {
            "NVSHMEM_REMOTE_TRANSPORT": "none",
            "NVSHMEM_IB_ENABLE_IBGDA": "0",
            "NVSHMEM_DISABLE_LOCAL_ONLY_PROXY": "1",
        }
        if arm.startswith("megamoe")
        else {}
    )
    need(
        {
            k: os.environ[k]
            for k in (
                "NVSHMEM_REMOTE_TRANSPORT",
                "NVSHMEM_IB_ENABLE_IBGDA",
                "NVSHMEM_DISABLE_LOCAL_ONLY_PROXY",
            )
            if k in os.environ
        }
        == expected_nv,
        "Source NVSHMEM defaults differ",
    )
    need(
        not any(k in os.environ for k in FORBIDDEN if not k.startswith("NVSHMEM_")),
        "Unexpected optional quant override after imports",
    )
    for p, d in controls.items():
        digest(p, d)
    for n, s in ck["shards"].items():
        need(identity((Path(MODEL) / n).lstat()) == s, "Shard changed during probe")
    return {
        "schema_version": 1,
        "status": "KIMI_RUNTIME_PREFLIGHT_PASSED_PENDING_ROOT_REVIEW",
        "error": None,
        "arm": arm,
        "node_expected_external_api_guard": r["node"],
        "hostname": socket.gethostname(),
        "python_executable": sys.executable,
        "python_resolved": str(Path(sys.executable).resolve()),
        "python_prefix": sys.prefix,
        "python_base_prefix": sys.base_prefix,
        "environment": env,
        "source_environment_after": environment_after,
        "source_environment_changes": changes,
        "source_environment_additions": {
            k: v for k, v in environment_after.items() if k not in env
        },
        "bound_files": controls,
        "sources": source,
        "checkpoint": ck,
        "gpu_before": before,
        "gpu_after": after,
        "provider": proof,
        "mount": mount,
        "port": r["port"],
        "limits": [
            "Root must separately verify fresh Pod/STS/image identity before/after and all GPUs idle after this probe exits.",
            "Imports may initialize CUDA and create private prep caches. No no-CUDA-initialization assertion.",
            "No model load, explicit tensor allocation/native kernel, NVSHMEM/collective initialization or serving request is performed.",
            "Peer capability and native API imports are not model/native compilation/collective correctness acceptance.",
            "Accepted tensor hashes remain historical; only checkpoint file identities and sidecar bytes are checked here.",
        ],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--request", type=Path, required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--arm", choices=ARMS, required=True)
    a = ap.parse_args()
    need(digest(a.request, limit=1 << 20)["sha256"] == a.sha256, "Request SHA differs")
    r = parse(a.request.read_bytes())
    try:
        answer = run(r, a.arm)
    except BaseException as e:
        print(
            json.dumps({"status": "PREFLIGHT_FAILED", "arm": a.arm, "error": repr(e)}),
            flush=True,
        )
        raise
    process_stat = Path("/proc/self/stat").read_text().rsplit(") ", 1)[1].split()
    answer["process"] = {
        "pid": os.getpid(),
        "birth": int(process_stat[19]),
        "state": process_stat[0],
    }
    answer["finished_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    answer["request"] = {"path": str(a.request), **digest(a.request)}
    answer["request_sha256"] = a.sha256
    answer["source"] = {
        "path": str(Path(__file__).resolve()),
        **digest(Path(__file__).resolve()),
    }
    print(json.dumps(answer, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
