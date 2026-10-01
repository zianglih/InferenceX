#!/usr/bin/env python3
"""Resolve three arm configurations in fresh private scopes; no model/serving run."""

import argparse
import json
from pathlib import Path
import sys

import run as recipe


def child(config, case):
    import torch
    from sglang.srt.server_args import prepare_server_args
    from sglang.srt.environ import envs
    from infx.bench_serving.encoding_dsv41 import encode_text_chat

    args = prepare_server_args(recipe.server_command(config, case)[3:])
    args.resolve_once()
    resolved = args.resolved_dict()
    recipe.validate_server_info(resolved, config, case)
    if torch.cuda.device_count() != 8:
        raise ValueError("Expected eight visible GPUs")
    properties = [torch.cuda.get_device_properties(i) for i in range(8)]
    if any((p.major, p.minor) != (10, 3) or "B300" not in p.name for p in properties):
        raise ValueError("Expected eight B300 GPUs")
    # Peer capability checks are not collective execution or kernel qualification.
    peers = [
        [True if i == j else torch.cuda.can_device_access_peer(i, j) for j in range(8)]
        for i in range(8)
    ]
    if not all(all(row) for row in peers):
        raise ValueError("CUDA peer capability is incomplete")
    defaults = {
        "per_token_activation": envs.SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION.get(),
        "combine_dtype": envs.SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE.get(),
        "in_kernel_fc2_reduce": envs.SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE.get(),
        "w4a16": envs.SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16.get(),
    }
    if defaults != {
        "per_token_activation": False,
        "combine_dtype": "bf16",
        "in_kernel_fc2_reduce": False,
        "w4a16": case["precision"] == "w4a16",
    }:
        raise ValueError("Backend quantization defaults differ")
    encoded = encode_text_chat(config["model_path"], "Hello")
    return {
        "status": "CONFIG_IMPORT_CAPABILITY_ONLY",
        "case": case,
        "resolved": resolved,
        "backend_defaults": defaults,
        "gpu": [
            {"name": p.name, "uuid": str(p.uuid), "major": p.major, "minor": p.minor}
            for p in properties
        ],
        "peer_capability": peers,
        "prompt_example": encoded,
        "model_loaded": False,
        "kernels_qualified": False,
    }


def preflight_config(config, out, tmp_root):
    recipe.canonical_path(str(out))
    cfg = dict(config, run_root=str(out), run_id=out.name, tmp_root=str(tmp_root))
    cfg["base_environment"] = dict(config["base_environment"], HOME=str(out / "home"))
    recipe.validate_tmp_root(cfg)
    if cfg["tmp_root"] == config["tmp_root"]:
        raise ValueError("Preflight TMP must be separate from the measured campaign")
    return cfg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tmp-root", type=Path)
    parser.add_argument("--child-case")
    args = parser.parse_args()
    config = recipe.read_config(args.config)
    if args.child_case:
        case = next(c for c in recipe.matrix() if c["case_id"] == args.child_case)
        print(json.dumps(child(config, case), default=str, sort_keys=True))
        return
    if (
        args.output is None
        or args.tmp_root is None
        or not args.output.is_absolute()
        or sys.platform != "linux"
    ):
        raise ValueError(
            "Parent preflight needs Linux, an absolute exclusive output and explicit --tmp-root"
        )
    if config["sglang_commit"] == "0" * 40:
        raise ValueError("Actual reviewed PR commit is required")
    out = args.output
    cfg = preflight_config(config, out, args.tmp_root)
    out.mkdir(parents=True, exist_ok=False)
    recipe.save(out / "config.json", cfg)
    recipe.prepare_tmp_scope(cfg, out)
    commands = []
    recipe.save(
        out / "plan.json",
        [{**c, "argv": recipe.server_command(config, c)} for c in recipe.matrix()],
    )
    for case in (
        c for c in recipe.matrix() if c["concurrency"] == recipe.CONCURRENCIES[0]
    ):
        env = recipe.environment(cfg, case)
        for key, value in env.items():
            if key.endswith(("CACHE_DIR", "CACHE_PATH", "CACHE_HOME")) or key in (
                "HOME",
                "HF_HOME",
                "FLASHINFER_WORKSPACE_BASE",
                "TORCH_EXTENSIONS_DIR",
            ):
                Path(value).mkdir(parents=True, exist_ok=True)
        before = recipe.gpu_snapshot(env)
        recipe.require_idle(before)
        recipe.save(out / (case["arm_id"] + ".gpu.before.json"), before)
        source = recipe.source_snapshot(cfg, env)
        recipe.save(out / (case["arm_id"] + ".source.json"), source)
        recipe.save(
            out / (case["arm_id"] + ".runtime.json"), recipe.installed_runtime(cfg, env)
        )
        command = [
            config["python"],
            "-B",
            str(Path(__file__).resolve()),
            "--config",
            str(out / "config.json"),
            "--child-case",
            case["case_id"],
        ]
        observed = recipe.capture(command, env, 600)
        recipe.save(out / (case["arm_id"] + ".import.json"), observed)
        commands.append({"argv": command, "returncode": observed["returncode"]})
        if observed["returncode"]:
            raise RuntimeError("Preflight import/config failed; raw output preserved")
        if recipe.source_snapshot(cfg, env) != source:
            raise RuntimeError("Source/package state changed during preflight")
        after = recipe.gpu_snapshot(env)
        recipe.require_idle(after)
        recipe.save(out / (case["arm_id"] + ".gpu.after.json"), after)
    recipe.save(
        out / "PREPARED.json",
        {
            "status": "IMPORT_CONFIG_ONLY",
            "commands": commands,
            "campaign_config": recipe.digest(args.config),
            "case_count": len(recipe.matrix()),
            "requires_actual_three_arm_qualification": True,
        },
    )


if __name__ == "__main__":
    main()
