#!/usr/bin/env python3
"""Verify terminal case bytes and render the three DSpark backend frontiers."""

import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import re

import run as recipe


def read(path, decimal=False):
    def unique(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError(f"Duplicate JSON key: {key}")
            value[key] = item
        return value

    def nonfinite(value):
        raise ValueError(f"Nonfinite JSON value: {value}")

    return json.loads(
        path.read_text(),
        object_pairs_hook=unique,
        parse_constant=nonfinite,
        parse_float=Decimal if decimal else float,
    )


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def finite(value, name, positive=False):
    if (
        isinstance(value, bool)
        or not isinstance(value, (float, int))
        or not math.isfinite(value)
    ):
        raise ValueError(f"Invalid {name}: {value}")
    if positive and value <= 0:
        raise ValueError(f"Nonpositive {name}")
    return value


def verify_environment(directory, config, case, env, source):
    """Replay the producer checkout path from sealed command evidence."""
    client = read(directory / "benchmark_command.json")
    argv = client.get("argv")
    if (
        not isinstance(argv, list)
        or len(argv) != 2
        or argv[0] != "bash"
        or not isinstance(argv[1], str)
    ):
        raise ValueError("Invalid recorded benchmark command")
    script = Path(argv[1])
    relative = Path("experimental/dsv41_dspark_ep8/benchmark_mtp.sh")
    if (
        not script.is_absolute()
        or ".." in script.parts
        or str(script) != argv[1]
        or ":" in argv[1]
        or tuple(script.parts[-3:]) != relative.parts
    ):
        raise ValueError("Invalid producer checkout path")
    producer = script.parents[2]
    if producer == Path("/"):
        raise ValueError("Invalid producer checkout root")
    expected = recipe.environment(config, case)
    expected["PYTHONPATH"] = config["sglang_root"] + "/python:" + str(producer)
    if env != expected:
        raise ValueError("Recorded environment differs from the backend-default recipe")
    server = read(directory / "server.launch.json")
    pid = server.get("pid")
    if (
        type(pid) is not int
        or pid <= 0
        or server.get("argv") != recipe.server_command(config, case)
        or server.get("environment") != env
    ):
        raise ValueError("Recorded server launch differs")
    client_env = dict(
        env,
        CASE_DIR=str(Path(config["run_root"]) / "cases" / case["case_id"]),
        MODEL_PATH=config["model_path"],
        SERVED_MODEL=config["served_model"],
        PORT=str(config["port"]),
        CONC=str(case["concurrency"]),
        SERVER_PID=str(pid),
        EVAL_ONLY="false",
        PROFILE="0",
    )
    launch = read(directory / "benchmark.launch.json")
    if (
        client.get("environment") != client_env
        or launch.get("argv") != argv
        or launch.get("environment") != client_env
    ):
        raise ValueError("Recorded benchmark launch differs from producer command")
    source_files = (
        "experimental/dsv41_dspark_ep8/run.py",
        str(relative),
        "benchmarks/benchmark_lib.sh",
        "infx/bench_serving/benchmark_serving.py",
        "infx/bench_serving/backend_request_func.py",
        "infx/bench_serving/speculative_metrics.py",
        "infx/bench_serving/encoding_dsv41.py",
    )
    digests = {
        name: {
            "bytes": (recipe.REPO / name).stat().st_size,
            "sha256": sha(recipe.REPO / name),
        }
        for name in source_files
    }
    if source.get("recipe") != digests:
        raise ValueError(
            "Recorded recipe/client source digests differ from this reader"
        )


def verify_case(directory):
    if directory.is_symlink():
        raise ValueError("Linked case directory")
    manifest = read(directory / "manifest.json")
    files = manifest["files"]
    actual = set()
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Linked evidence: {path}")
        if path.is_file() and path != directory / "manifest.json":
            actual.add(path.relative_to(directory).as_posix())
    if actual != set(files):
        raise ValueError(f"Manifest members differ in {directory}")
    for name, desc in files.items():
        path = directory / name
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Nonlocal manifest member")
        if path.stat().st_size != desc["bytes"] or sha(path) != desc["sha256"]:
            raise ValueError(f"Changed raw evidence: {path}")
    terminal = read(directory / "exit.json")
    if (
        terminal["status"] != "completed"
        or terminal.get("error")
        or terminal.get("postflight_error")
    ):
        raise ValueError(f"Unsuccessful case: {directory}")
    for role in ("server", "benchmark"):
        cleanup = terminal["cleanup"][role]
        if cleanup.get("remaining") or cleanup.get("errors") or cleanup.get("error"):
            raise ValueError(f"Incomplete {role} cleanup")
    if terminal["cleanup"]["benchmark"]["waited_returncode"] != 0:
        raise ValueError("Benchmark client did not exit successfully")
    after_gpu = read(directory / "gpu.after.json")
    if (
        after_gpu["applications"]["returncode"]
        or after_gpu["applications"]["stdout"].strip()
    ):
        raise ValueError("Post-case GPUs not idle")
    settings = read(directory / "settings.json")
    case, config, env = settings["case"], settings["config"], settings["environment"]
    p, tp, c = case["precision"], case["tp"], case["concurrency"]
    expected_case = next(
        (row for row in recipe.matrix() if row["case_id"] == directory.name), None
    )
    if expected_case is None or case != expected_case:
        raise ValueError("Unexpected backend/precision/topology/concurrency identity")
    if terminal.get("case") != case:
        raise ValueError("Terminal case identity differs from settings")
    before = read(directory / "source.before.json")
    verify_environment(directory, config, case, env, before)
    if read(directory / "server_command.json") != recipe.server_command(config, case):
        raise ValueError("Actual server command differs from the recipe")
    if (settings["nominal_input"], settings["nominal_output"], settings["ratio"]) != (
        1024,
        8192,
        0.8,
    ):
        raise ValueError("Wrong sampled workload")
    for when in ("before", "after"):
        recipe.validate_server_info(
            read(directory / f"server_info.{when}.json"), config, case
        )
    resolved_before = read(directory / "server_info.before.json")
    resolved_after = read(directory / "server_info.after.json")
    for key in (
        "quantization",
        "kv_cache_dtype",
        "attention_backend",
        "dsv4_attn_backend",
        "speculative_draft_model_quantization",
    ):
        if resolved_before.get(key) != resolved_after.get(key):
            raise ValueError(f"Resolved model/backend default changed: {key}")
    after = read(directory / "source.after.json")
    if before != after:
        raise ValueError("Sources/packages changed within a point")
    for name in ("sglang", "flashinfer"):
        source = before[name]
        if (
            source["head"]["returncode"]
            or source["diff"]["returncode"]
            or source["diff"]["stdout"].strip()
            or source["head"]["stdout"].strip() != config[name + "_commit"]
            or source["root"] != config[name + "_root"]
        ):
            raise ValueError(f"Recorded {name} source differs from declared pin")
    from infx.bench_serving.encoding_dsv41 import ENCODER_SHA256

    if before["prompt_encoder"]["sha256"] != ENCODER_SHA256:
        raise ValueError("Unpinned prompt encoder")
    if before["freeze"]["returncode"] or not before["freeze"]["stdout"].strip():
        raise ValueError("Package freeze failed or is empty")
    log = (directory / "benchmark.log").read_text()
    namespaces = [line for line in log.splitlines() if line.startswith("Namespace(")]
    if len(namespaces) != 1 or not re.search(r"(?:\(|, )seed=0(?:,|\))", namespaces[0]):
        raise ValueError("Actual client did not record seed 0")
    if (
        f"Warming up with {2 * c} requests..." not in log
        or "Warmup completed." not in log
    ):
        raise ValueError("Full warmup was not recorded")
    result = read(directory / "result.json")
    if result["completed"] != 10 * c or result["num_prompts"] != 10 * c:
        raise ValueError("Measured success count differs")
    if result["max_concurrency"] != c or result["request_rate"] != "inf":
        raise ValueError("Traffic differs")
    if (
        result.get("benchmark_outcome", {}).get("status") != "passed"
        or result["benchmark_outcome"].get("failed") != 0
    ):
        raise ValueError("Client outcome is not passed")
    mtp = recipe.validate_speculative_metrics(result, 10 * c)
    lengths = {}
    for field, total in (
        ("input_lens", "total_input_tokens"),
        ("output_lens", "total_output_tokens"),
    ):
        values = result[field]
        if len(values) != 10 * c or any(type(x) is not int or x <= 0 for x in values):
            raise ValueError(f"Invalid {field}")
        if sum(values) != result[total]:
            raise ValueError(f"Wrong {total}")
        lengths[field] = values
    planned = read(directory / "requested-lengths.json")
    client_source = before["recipe"]["infx/bench_serving/benchmark_serving.py"]
    plan_settings = {
        "scope": "deterministic request plan, not server output",
        "seed": 0,
        "nominal_input": 1024,
        "nominal_output": 8192,
        "ratio": 0.8,
        "num_prompts": 10 * c,
        "model_path": config["model_path"],
        "client_source": client_source,
        "prompt_format": "DeepSeek-V4.1 chat; reasoning_effort=None",
        "encoder_source": before["prompt_encoder"],
    }
    if any(planned.get(k) != v for k, v in plan_settings.items()):
        raise ValueError("Requested-length plan settings/source differ")
    for field in ("input_lens", "output_lens"):
        values = planned.get(field)
        if (
            not isinstance(values, list)
            or len(values) != 10 * c
            or any(type(x) is not int or x <= 0 for x in values)
            or values != lengths[field]
        ):
            raise ValueError(f"Requested versus completed ordered {field} differ")
    if any(not 6553 <= x <= 8192 for x in planned["output_lens"]):
        raise ValueError("Requested output length is outside the sampled range")
    rate = result["total_output_tokens"] / finite(result["duration"], "duration", True)
    if not math.isclose(
        finite(result["output_throughput"], "output_throughput", True),
        rate,
        rel_tol=1e-9,
    ):
        raise ValueError("Output throughput differs from tokens / full interval")
    tpot = finite(result["median_tpot_ms"], "median_tpot_ms", True)
    row = {
        "case_id": directory.name,
        "arm_id": case["arm_id"],
        "precision": p,
        "moe_runner_backend": case["moe_runner_backend"],
        "moe_a2a_backend": case["moe_a2a_backend"],
        "tp": tp,
        "ep": tp,
        "dp": tp,
        "concurrency": c,
        "completed": result["completed"],
        "measured_acceptance_length": mtp["acceptance_length"],
        "measured_acceptance_rate": mtp["acceptance_rate"],
        "measured_spec_verify_ct": mtp["spec_verify_ct"],
        "measured_spec_covered": mtp["covered"],
        "measured_spec_correct_drafts": mtp["spec_num_correct_drafts"],
        "measured_spec_proposed_drafts": mtp["spec_num_proposed_drafts"],
        "prompt_format": "DeepSeek-V4.1 chat; reasoning_effort=None",
        "duration_s": result["duration"],
        "input_tokens": result["total_input_tokens"],
        "output_tokens": result["total_output_tokens"],
        "output_tok_s": rate,
        "output_tok_s_gpu": rate / tp,
        "interactivity_tok_s_user": 1000 / tpot,
        "result_sha256": files["result.json"]["sha256"],
        "case_manifest_sha256": sha(directory / "manifest.json"),
        "sglang_commit": config["sglang_commit"],
        "flashinfer_commit": config["flashinfer_commit"],
        "flashinfer_wheel_commit": config.get(
            "flashinfer_wheel_commit", config["flashinfer_commit"]
        ),
        "flashinfer_python_patch": config.get("flashinfer_python_patch"),
        "image": config["image"],
    }
    for key, value in result.items():
        if key.endswith("_ms"):
            row[key] = finite(value, key)
    return row, lengths, before, config


def load(root, partial):
    expected = {(r["arm_id"], r["tp"], r["concurrency"]) for r in recipe.matrix()}
    rows, lengths, seen, baseline = [], {}, set(), None
    campaign_config = recipe.read_config(root / "config.json")
    verify_startup(root, campaign_config)
    if read(root / "matrix.json") != recipe.matrix():
        raise ValueError(
            "Saved campaign matrix differs from the DSpark three-arm contract"
        )
    for directory in sorted((root / "cases").iterdir()):
        if not directory.is_dir() or not (directory / "manifest.json").exists():
            if partial:
                continue
            raise ValueError(f"Unfinalized case: {directory}")
        row, arrays, source, config = verify_case(directory)
        if config != campaign_config:
            raise ValueError("Case config differs from campaign config")
        key = (row["arm_id"], row["tp"], row["concurrency"])
        if key not in expected or key in seen:
            raise ValueError("Unexpected/duplicate matrix point")
        seen.add(key)
        if baseline is not None and source != baseline:
            raise ValueError("Source/package/recipe differs across cases")
        baseline = source
        c = row["concurrency"]
        if c in lengths and arrays != lengths[c]:
            raise ValueError(f"Ordered request lengths differ at C{c}")
        lengths[c] = arrays
        rows.append(row)
    if not partial:
        terminal = read(root / "worker-exit.json")
        if (
            seen != expected
            or terminal["status"] != "completed"
            or terminal.get("error")
        ):
            raise ValueError("Full 18-point campaign incomplete")
        if terminal["completed"] != [x["case_id"] for x in recipe.matrix()]:
            raise ValueError("Worker completed IDs differ")
        if sum(x["completed"] for x in rows) != 3780:
            raise ValueError("Full measured count differs")
    return rows


def frontier(rows):
    return sorted(
        (
            r
            for r in rows
            if not any(
                q["interactivity_tok_s_user"] >= r["interactivity_tok_s_user"]
                and q["output_tok_s_gpu"] >= r["output_tok_s_gpu"]
                and (
                    q["interactivity_tok_s_user"] > r["interactivity_tok_s_user"]
                    or q["output_tok_s_gpu"] > r["output_tok_s_gpu"]
                )
                for q in rows
            )
        ),
        key=lambda r: r["interactivity_tok_s_user"],
    )


ARM_STYLE = {
    "megamoe-w4a4": ("MegaMoE W4A4", "#009E73"),
    "megamoe-w4a16": ("MegaMoE W4A16", "#E69F00"),
    "trtllm-w4a4": ("TRTLLM NVFP4 W4A4", "#0072B2"),
}


def frontiers(rows):
    return [
        {
            "arm_id": arm,
            "tp": tp,
            "ep": tp,
            "dp": tp,
            "case_ids": [
                r["case_id"]
                for r in frontier(
                    [r for r in rows if (r["arm_id"], r["tp"]) == (arm, tp)]
                )
            ],
        }
        for arm in ARM_STYLE
        for tp in recipe.TOPOLOGIES
    ]


def figure(rows, topology=None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "svg.fonttype": "none",
            "svg.hashsalt": "dsv41-dspark-ep8",
        }
    )
    if topology not in (None, 8):
        raise ValueError("Expected the EP8 view")
    if topology is not None:
        rows = [row for row in rows if row["tp"] == topology]
    fig, ax = plt.subplots(figsize=(18, 12))
    fig.subplots_adjust(left=0.11, right=0.97, bottom=0.20, top=0.86)
    points = []
    for arm, (label, color) in ARM_STYLE.items():
        for tp in (8,) if topology is None else (topology,):
            group = [r for r in rows if (r["arm_id"], r["tp"]) == (arm, tp)]
            selected = frontier(group)
            marker, line = (
                ("o", "-") if tp == 4 or topology is not None else ("^", "--")
            )
            ax.plot(
                [r["interactivity_tok_s_user"] for r in selected],
                [r["output_tok_s_gpu"] for r in selected],
                color=color,
                linewidth=1.9,
                linestyle=line,
                marker=marker,
                markersize=7,
                markeredgecolor="white",
                markeredgewidth=0.7,
                label=f"{label} | TP=EP=DP={tp}",
                zorder=2,
            )
            ax.scatter(
                [r["interactivity_tok_s_user"] for r in group],
                [r["output_tok_s_gpu"] for r in group],
                color=color,
                marker=marker,
                s=63,
                edgecolor="white",
                linewidth=0.7,
                zorder=4,
            )
            for r in group:
                # Display-point offsets keep the measured clusters readable.
                # Leaders still terminate at the unchanged measured coordinates.
                dx, dy = {
                    "megamoe-w4a4": {
                        2: (12, 12), 4: (32, 12), 8: (38, 28),
                        16: (28, -8), 32: (25, -20), 64: (25, -20),
                    },
                    "megamoe-w4a16": {
                        2: (0, -50), 4: (75, 50), 8: (-5, 70),
                        16: (-12, 45), 32: (-25, 30), 64: (-20, 25),
                    },
                    "trtllm-w4a4": {
                        2: (-25, -50), 4: (-60, -10), 8: (-60, 25),
                        16: (-25, -25), 32: (-30, -30), 64: (-25, 0),
                    },
                }[arm].get(r["concurrency"], (9, 12))
                ax.annotate(
                    f"C{r['concurrency']}\nAL={r['measured_acceptance_length']:.2f}",
                    (r["interactivity_tok_s_user"], r["output_tok_s_gpu"]),
                    xytext=(dx, dy),
                    textcoords="offset points",
                    color=color,
                    ha="right" if dx < 0 else "left",
                    fontsize=10,
                    bbox={
                        "facecolor": "white",
                        "edgecolor": "none",
                        "alpha": 0.82,
                        "pad": 0.5,
                    },
                    arrowprops={"arrowstyle": "-", "color": color, "lw": 0.6},
                )
                points.append(
                    {
                        "case_id": r["case_id"],
                        "arm_id": arm,
                        "tp": tp,
                        "ep": tp,
                        "dp": tp,
                        "concurrency": r["concurrency"],
                        "measured_acceptance_length": r["measured_acceptance_length"],
                        "measured_acceptance_rate": r["measured_acceptance_rate"],
                        "acceptance_scope": "measured_requests_only",
                        "x": r["interactivity_tok_s_user"],
                        "y": r["output_tok_s_gpu"],
                    }
                )
    ax.set(
        xlabel="Interactivity = 1,000 / saved median TPOT (tokens/s/user)",
        ylabel="Whole-interval output throughput (tokens/s/GPU)",
    )
    ax.grid(alpha=0.20)
    ax.margins(x=0.12, y=0.16)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="best", fontsize=10, framealpha=0.96)
    fig.suptitle(
        "DeepSeek-V4.1 Flash | DSpark | B300 EP8 | Concurrency 2-64"
        + (f" | EP{topology}" if topology is not None else ""),
        y=0.965,
        fontsize=20,
        weight="bold",
    )
    fig.text(
        0.5,
        0.915,
        f"Nominal 1,024 input / 8,192 output | ratio 0.8 | {len(rows)} fresh points | {sum(10 * r['concurrency'] for r in rows):,} measured requests",
        ha="center",
        fontsize=12,
    )
    fig.text(
        0.5,
        0.115,
        f"3 independent frontiers; all {len(rows)} points shown. Each line connects nondominated points within one backend/topology group.",
        ha="center",
        fontsize=10,
    )
    fig.text(
        0.5,
        0.082,
        "DSpark: gamma 5 / verify width 6 | Bundled draft: MXFP4 + MXFP8 / flashinfer_mxfp4 / none",
        ha="center",
        fontsize=10,
    )
    fig.text(
        0.5,
        0.05,
        f"SG {rows[0]['sglang_commit'][:12]} | FI Python {rows[0]['flashinfer_commit'][:12]} / wheels {rows[0].get('flashinfer_wheel_commit', rows[0]['flashinfer_commit'])[:12]} | shared compile; isolated tactics",
        ha="center",
        fontsize=10,
    )
    fig.text(
        0.5,
        0.015,
        "AL: measured DSpark sum(completion_tokens)/sum(spec_verify_ct), including bonus tokens; warmups excluded. Whole-interval throughput.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    return fig, points


def plot(rows, out, topology=None):
    import matplotlib.pyplot as plt

    fig, points = figure(rows, topology)
    fig.savefig(out / "pareto.png", dpi=180)
    fig.savefig(out / "pareto.svg", metadata={"Date": None})
    plt.close(fig)
    (out / "plot-points.json").write_text(
        json.dumps(points, indent=2, allow_nan=False) + "\n"
    )
    groups = [g for g in frontiers(rows) if topology is None or g["tp"] == topology]
    (out / "frontiers.json").write_text(json.dumps(groups, indent=2) + "\n")
    if topology is None:
        for tp in recipe.TOPOLOGIES:
            destination = out / "figures" / f"ep{tp}"
            destination.mkdir(parents=True, exist_ok=False)
            plot(rows, destination, tp)


def verify_startup(root, config):
    receipt = read(root / "tmp-preflight.json")
    if (
        receipt.get("status") != "AF_UNIX_PATH_PREFLIGHT_PASSED"
        or receipt.get("error")
        or receipt.get("run_id") != config["run_id"]
        or receipt.get("run_root") != config["run_root"]
        or receipt.get("tmp_root") != config["tmp_root"]
    ):
        raise ValueError("Short TMP startup receipt differs or failed")
    probes = receipt.get("probes", [])
    if len(probes) != 3 or any(
        p.get("bound") is not True or p.get("cleanup_errors") for p in probes
    ):
        raise ValueError("All three actual AF_UNIX preflight probes are required")
    seed = read(root / "compile-cache-seed.json")
    if config["compile_cache_seed"] is None:
        if seed != {"status": "NO_SEED_FRESH_COMPILE_CACHE"}:
            raise ValueError("Unexpected compile seed receipt")
    elif (
        seed.get("status") != "VERIFIED_COMPILE_ONLY_COPY"
        or seed.get("seed") != config["compile_cache_seed"]
        or seed.get("tactics_copied") is not False
    ):
        raise ValueError("Compile seed copy receipt differs")


def saved_and_paired(rows, root):
    """Keep exact saved scalar values and recompute only explicit paired rates."""
    scalars, metrics = [], {}
    for row in rows:
        path = root / "cases" / row["case_id"] / "result.json"
        if sha(path) != row["result_sha256"]:
            raise ValueError("Result changed after case verification")
        raw, exact = read(path), read(path, decimal=True)
        saved = {
            k: v
            for k, v in raw.items()
            if v is None or isinstance(v, (str, bool, int, float))
        }
        saved.update(
            {
                "benchmark_outcome." + k: v
                for k, v in raw["benchmark_outcome"].items()
                if v is None or isinstance(v, (str, bool, int, float))
            }
        )
        saved.update(
            {
                "speculative_metrics." + k: v
                for k, v in raw["speculative_metrics"].items()
                if v is None or isinstance(v, (str, bool, int, float))
            }
        )
        scalars.append({"case_id": row["case_id"], **saved})
        with localcontext() as ctx:
            ctx.prec = 50
            rate = Decimal(exact["total_output_tokens"]) / exact["duration"]
            values = {
                "duration_s": exact["duration"],
                "measured_acceptance_length": Decimal(
                    exact["speculative_metrics"]["completion_tokens"]
                )
                / exact["speculative_metrics"]["spec_verify_ct"],
                "measured_acceptance_rate": Decimal(
                    exact["speculative_metrics"]["spec_num_correct_drafts"]
                )
                / exact["speculative_metrics"]["spec_num_proposed_drafts"],
                "output_tok_s": rate,
                "output_tok_s_gpu": rate / row["tp"],
                "interactivity_tok_s_user": Decimal(1000) / exact["median_tpot_ms"],
            }
            values.update(
                {k: Decimal(v) for k, v in exact.items() if k.endswith("_ms")}
            )
            metrics[row["case_id"]] = values
    by_key = {(r["arm_id"], r["tp"], r["concurrency"]): r["case_id"] for r in rows}
    pairs = []
    for c in recipe.CONCURRENCIES:
        for tp in recipe.TOPOLOGIES:
            for base, comp in (
                ("megamoe-w4a4", "megamoe-w4a16"),
                ("trtllm-w4a4", "megamoe-w4a4"),
                ("trtllm-w4a4", "megamoe-w4a16"),
            ):
                pairs.append(("backend", (base, tp, c), (comp, tp, c)))
    comparisons = []
    with localcontext() as ctx:
        ctx.prec = 50
        for kind, base, comp in pairs:
            if base not in by_key or comp not in by_key:
                continue
            a, b = by_key[base], by_key[comp]
            if metrics[a].keys() != metrics[b].keys():
                raise ValueError("Saved paired metric fields differ")
            for metric, va in metrics[a].items():
                vb = metrics[b][metric]
                comparisons.append(
                    {
                        "pair_id": f"{b}__over__{a}",
                        "kind": kind,
                        "baseline_case": a,
                        "comparison_case": b,
                        "metric": metric,
                        "baseline_value": str(va),
                        "comparison_value": str(vb),
                        "absolute_change": str(vb - va),
                        "percent_change": str((vb / va - 1) * 100) if va else None,
                    }
                )
    return scalars, comparisons


def write_table(out, stem, rows):
    (out / f"{stem}.json").write_text(
        json.dumps(rows, indent=2, allow_nan=False) + "\n"
    )
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with (out / f"{stem}.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    rows = load(args.run_root, args.partial)
    if not rows:
        raise ValueError("No finalized measured points")
    args.output.mkdir(parents=True, exist_ok=False)
    write_table(args.output, "raw-metrics", rows)
    scalars, comparisons = saved_and_paired(rows, args.run_root)
    write_table(args.output, "raw-saved-scalars", scalars)
    write_table(args.output, "paired-comparisons", comparisons)
    lines = [
        "# DeepSeek-V4.1 DSpark EP8 1k/8k results",
        "",
        f"Verified finalized points: {len(rows)}/18.",
        "",
        "Nominal lengths 1,024/8,192 with ratio 0.8 sampling; 2C warmup / 10C measured. "
        "Same-C ordered length arrays match across available arms.",
        "",
        "Throughput covers the complete measured wall interval, not separately timed decode. "
        "Measured DSpark acceptance length is sum(completion_tokens) / sum(spec_verify_ct), including the native bonus token. "
        "Every measured request must retain valid native counters; warmups are excluded.",
        "",
        "| Arm | TP=DP=EP | C | Requests | Duration s | Output tok/s | Output tok/s/GPU | 1000/median TPOT | Measured DSpark AL |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['arm_id']} | {r['tp']} | {r['concurrency']} | {r['completed']} | "
            f"{r['duration_s']:.6f} | {r['output_tok_s']:.6f} | {r['output_tok_s_gpu']:.6f} | {r['interactivity_tok_s_user']:.6f} | {r['measured_acceptance_length']:.6f} |"
        )
    lines += [
        "",
        "Complete saved scalar latency metrics, source pins and raw SHA bindings are in "
        "[raw-metrics.csv](raw-metrics.csv) and [raw-metrics.json](raw-metrics.json). All saved scalar "
        "fields are retained in raw-saved-scalars.json/CSV; paired-comparisons.json/CSV uses Decimal50 "
        "arithmetic and explicit baseline/comparison case IDs. Zero baselines have no percent change.",
        "",
        "The traditional arm uses backend defaults for per-tensor activation and quantization fast math; "
        "the W4A16 opt-in affects eligible NVFP4 linears. This checkpoint is hybrid: routed target experts "
        "are NVFP4, inherited dense layers retain their own precision, and bundled draft MoE is MXFP4/MXFP8. "
        "This reader checks sealed settings and accounting; "
        "actual native kernel/tactics/calibration, full terminal and preservation acceptance remain separate reviews.",
        "",
        "FlashInfer Python-source and installed-wheel commits are reported separately. An optional reviewed "
        "single-file Python correction does not imply that cubin/NCCL providers were rebuilt; "
        "the original and corrected file hashes are retained in each compact row when present.",
        "",
        "Saved ITL is stream_interval30 chunk spacing, not per-token TPOT. Sequential backend/topology/cache "
        "history differences do not establish causality or numerical/content equivalence. No unsaved percentiles are reconstructed.",
        "",
    ]
    if not args.partial:
        plot(rows, args.output)
        lines += ["![Three DSpark backend frontiers](pareto.png)", ""]
    (args.output / "RESULTS.md").write_text("\n".join(lines))
    print(
        json.dumps(
            {"points": len(rows), "partial": args.partial, "output": str(args.output)}
        )
    )


if __name__ == "__main__":
    main()
