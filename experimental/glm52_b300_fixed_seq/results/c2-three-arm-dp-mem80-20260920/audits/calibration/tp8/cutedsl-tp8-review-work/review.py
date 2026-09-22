#!/usr/bin/env python3
"""Independent actual TP8 raw review; imports no benchmark auditor code."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import tarfile

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"
RUN = "c2-w4a16-cutedsl-mem80-20260920"
CASE = "8k1k/w4a16-cutedsl/tp8_conc4"
DIRECTORY = ARTIFACTS / "measured" / RUN / CASE
FIRST = ARTIFACTS / "measured" / RUN / "8k1k/w4a16-cutedsl/tp4_conc256"
RUNTIME = ARTIFACTS / "cutedsl-20260920"
TRANSFER = ARTIFACTS / "measured" / f"{RUN}-completed-20260920T153612Z.tar.gz"
RAW_NAMES = ("result.json", "benchmark.log", "metadata.json", "status.json", "server_command.sh",
             "benchmark_command.sh", "server_info.before.json", "server_info.after.json", "packages.json",
             "nvidia-smi.txt", "server.log", "gpu_metrics.csv", "gpu_metrics_identity.csv")
RECEIPT_NAMES = ("runtime-before.json", "runtime-after.json", "packages-before.txt", "packages-after.txt",
                 "pip-check-before.txt", "pip-check-after.txt", "source-imports.json", "setup-completed.json")


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root, names):
    assert all((root / name).is_file() and not (root / name).is_symlink() for name in names)
    return {name: sha(root / name) for name in names}


def command(path):
    tokens = shlex.split(path.read_text())
    flags = {token: tokens[i + 1] if i + 1 < len(tokens) and not tokens[i + 1].startswith("--") else True
             for i, token in enumerate(tokens) if token.startswith("--")}
    return tokens, flags


def main():
    raw_hashes, runtime_hashes = hashes(DIRECTORY, RAW_NAMES), hashes(RUNTIME, RECEIPT_NAMES)
    first_review = load(ARTIFACTS / "cutedsl-first-case-independent-review.json")
    assert first_review["review_status"] == "passed" and first_review["issue_count"] == 0
    assert first_review["runtime_receipt_sha256"] == runtime_hashes
    assert sha(ARTIFACTS / first_review["independent_review_report"]["path"]) == first_review["independent_review_report"]["sha256"]
    receipt = load(TRANSFER.with_name(TRANSFER.name + ".verification.json"))
    assert sha(TRANSFER) == receipt["transfer_sha256"] and CASE in receipt["cases"]
    with tarfile.open(TRANSFER) as archive:
        manifest = json.load(archive.extractfile("collector-manifest.json"))
        for name, checksum in raw_hashes.items():
            relative = f"{CASE}/{name}"
            assert manifest["files"][relative] == receipt["files"][relative]
            assert checksum == receipt["files"][relative]["sha256"]
            assert (DIRECTORY / name).stat().st_size == receipt["files"][relative]["bytes"]
            assert hashlib.sha256(archive.extractfile(f"{RUN}/{relative}").read()).hexdigest() == checksum
    meta, result, status = [load(DIRECTORY / name) for name in ("metadata.json", "result.json", "status.json")]
    first_meta = load(FIRST / "metadata.json")
    pins = first_review["pins"]
    assert all(meta[k] == value for k, value in pins.items())
    expected_meta = {"run_id": RUN, "scenario": "8k1k", "backend": "w4a16_cutedsl", "tp": 8, "dp": 8,
                     "ep": 8, "gpu_count": 8, "concurrency": 4, "server_max_running_requests": 8,
                     "isl": 8192, "osl": 1024, "num_prompts": 40, "num_warmups": 8,
                     "random_range_ratio": .8, "mem_fraction_static": .8, "status": "completed"}
    assert all(meta[k] == value for k, value in expected_meta.items())
    assert status["status"] == "completed" and status["exit_code"] == status["failed"] == 0
    assert status["expected"] == status["completed"] == result["completed"] == result["num_prompts"] == 40
    for doc in (result, status):
        assert all(doc["benchmark_outcome"][k] == v for k, v in {"status": "passed", "requested": 40, "completed": 40, "failed": 0}.items())
    assert result["max_concurrency"] == 4
    for key, total in (("input_lens", "total_input_tokens"), ("output_lens", "total_output_tokens")):
        assert len(result[key]) == 40 and all(type(x) is int and x > 0 for x in result[key])
        assert sum(result[key]) == result[total]
    for key, count in (("request_throughput", 40), ("output_throughput", result["total_output_tokens"]),
                       ("total_token_throughput", result["total_input_tokens"] + result["total_output_tokens"])):
        assert math.isclose(result[key], count / result["duration"], rel_tol=1e-12)
    start, end = result["benchmark_start_time_unix"], result["benchmark_end_time_unix"]
    assert abs(end - start - result["duration"]) < .001
    assert datetime.fromisoformat(meta["started_at"]).timestamp() < start < end < datetime.fromisoformat(meta["finished_at"]).timestamp()
    seal = load(RUNTIME / "setup-completed.json")
    assert datetime.fromisoformat(seal["completed_at"]) < datetime.fromisoformat(meta["started_at"])
    assert seal["source_heads"] == {"sglang": pins["sglang_commit"], "flashinfer": pins["flashinfer_commit"], "inferencex": pins["inferencex_commit"]}
    assert load(RUNTIME / "source-imports.json")["source_tree_clean"] == dict.fromkeys(seal["source_heads"], True)
    packages = {item["name"]: item["version"] for item in load(DIRECTORY / "packages.json")}
    assert packages == {item["name"]: item["version"] for item in load(FIRST / "packages.json")}
    assert packages["flashinfer-python"] == "0.7.0" and packages["nccl-extensions"] == "0.1.0"
    assert all(packages["nvidia-cutlass-dsl" + suffix] == "4.7.1" for suffix in ("", "-libs-base", "-libs-core", "-libs-cu12", "-libs-cu13"))
    assert "flashinfer-cubin" not in packages and "flashinfer-jit-cache" not in packages
    for field in ("flashinfer_import_path", "flashinfer_import_version", "cute_dsl_compiler", "versions"):
        assert meta[field] == first_meta[field]
    env = dict(meta["environment"])
    assert env.pop("CUDA_VISIBLE_DEVICES") == "0,1,2,3,4,5,6,7"
    first_env = dict(first_meta["environment"])
    first_env.pop("CUDA_VISIBLE_DEVICES")
    assert env == first_env
    tokens, flags = command(DIRECTORY / "server_command.sh")
    expected_flags = command(FIRST / "server_command.sh")[1]
    expected_flags.update({"--tensor-parallel-size": "8", "--data-parallel-size": "8", "--expert-parallel-size": "8",
                           "--max-running-requests": "8", "--cuda-graph-max-bs-decode": "4"})
    assert flags == expected_flags
    assert "--speculative-draft-model-quantization" not in flags
    assert "SGLANG_FLASHINFER_MOE_FUSED_FINALIZE=0" in tokens and "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1" in tokens
    client_tokens, client_flags = command(DIRECTORY / "benchmark_command.sh")
    for key, value in {"--input-len": "8192", "--output-len": "1024", "--num-prompts": "40", "--max-concurrency": "4", "--random-range-ratio": "0.8"}.items():
        assert client_flags[key] == value
    assert "--use-chat-template" in client_tokens
    expected_state = {"tp_size": 8, "dp_size": 8, "ep_size": 8, "enable_dp_attention": True,
                      "max_running_requests": 8, "chunked_prefill_size": 4096, "mem_fraction_static": .8,
                      "moe_runner_backend": "flashinfer_cutedsl", "moe_a2a_backend": "none",
                      "speculative_moe_runner_backend": "flashinfer_trtllm", "speculative_moe_a2a_backend": "none",
                      "speculative_draft_model_quantization": "modelopt_fp4", "_speculative_draft_quantization_explicitly_set": False,
                      "cuda_graph_backend_prefill": "disabled", "dtype": "bfloat16", "quantization": "modelopt_fp4",
                      "attention_backend": "dsa", "dsa_prefill_backend": "trtllm", "dsa_decode_backend": "trtllm",
                      "kv_cache_dtype": "fp8_e4m3", "max_prefill_tokens": 32768, "speculative_algorithm": "EAGLE",
                      "speculative_num_steps": 3, "speculative_eagle_topk": 1, "speculative_num_draft_tokens": 4}
    states = {}
    for when in ("before", "after"):
        info = load(DIRECTORY / f"server_info.{when}.json")
        assert len(info["internal_states"]) == 8
        for state in [info, *info["internal_states"]]:
            assert all(type(state[k]) is type(value) and state[k] == value for k, value in expected_state.items())
            assert state["cuda_graph_config"]["decode"]["backend"] == "full"
            assert state["cuda_graph_config"]["decode"]["max_bs"] == 4 and state["cuda_graph_config"]["decode"]["bs"] == [1, 2, 3, 4]
            assert state["cuda_graph_config"]["prefill"]["backend"] == "disabled"
        assert all(s["effective_max_running_requests_per_dp"] == 1 and s["world_size"] == 8 for s in info["internal_states"])
        states[when] = [{"response_index": i, "world_size": s["world_size"], "effective_max_running_requests_per_dp": s["effective_max_running_requests_per_dp"], "avg_spec_accept_length": s.get("avg_spec_accept_length")} for i, s in enumerate(info["internal_states"])]
    after = load(DIRECTORY / "server_info.after.json")
    normalized = {key: after[key] for key in first_review["normalized_settings"] if key not in ("configured_decode_max_bs", "actual_capture_max")}
    normalized.update(configured_decode_max_bs=4, actual_capture_max=1)
    graph_counts, diagnostic_counts, captures, diagnostics = Counter(), Counter(), [], []
    phase = "untimed"
    for number, line in enumerate((DIRECTORY / "server.log").read_bytes().decode().split("\n"), 1):
        match = re.search(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)
        if match:
            t = datetime.strptime(match[1], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
            phase = "before" if t + 1 <= start else "after" if t >= end else "measured" if t >= start and t + 1 <= end else "boundary"
        capture = re.search(r"Capture (.+?) CUDA graph begin.*?bs=(\[[\d, ]+\])", line)
        if capture:
            assert json.loads(capture[2]) == [1]
            captures.append({"line": number, "kind": capture[1], "buckets": [1], "text": line})
        graph = re.search(r"(Prefill|Decode) batch.*?cuda graph: (True|False)", line)
        if graph:
            assert (graph[1], graph[2]) in (("Prefill", "False"), ("Decode", "True"))
            graph_counts[f"{phase}:{graph[1]}:{graph[2]}"] += 1
        patterns = {"oom": r"(?i)out of memory|OutOfMemoryError", "error": r"\bERROR\b", "traceback": r"Traceback \(most recent call last\)",
                    "runtime_error": r"RuntimeError:", "sigterm": r"SIGTERM received", "sigquit": r"SIGQUIT received|Triggering SIGQUIT",
                    "warning": r"(?:User|Future)Warning:|\bWARNING\b", "cutedsl_w4a16": r"CuteDslMoEWrapper::run::W4A16",
                    "bf16_trtllm": r"Tuning flashinfer::trtllm_bf16_moe"}
        for tag, pattern in patterns.items():
            if re.search(pattern, line):
                diagnostic_counts[f"{phase}:{tag}"] += 1
                if tag in ("oom", "error", "traceback", "runtime_error", "sigterm", "sigquit"):
                    diagnostics.append({"line": number, "phase": phase, "tag": tag, "text": line})
    assert captures and len([x for x in captures if x["kind"] == "target verify"]) == 8
    assert not any(count for key, count in diagnostic_counts.items() if key.endswith((":oom", ":runtime_error")))
    assert all(x["phase"] == "after" for x in diagnostics)
    log = (DIRECTORY / "benchmark.log").read_text()
    for label, key in (("Benchmark duration (s)", "duration"), ("Output token throughput (tok/s)", "output_throughput"),
                       ("Total Token throughput (tok/s)", "total_token_throughput"), ("Median TTFT (ms)", "median_ttft_ms"),
                       ("Median TPOT (ms)", "median_tpot_ms"), ("Median ITL (ms)", "median_itl_ms"), ("Median E2EL (ms)", "median_e2el_ms")):
        assert re.findall(re.escape(label) + r":\s+([\d.]+)", log)[-1] == f"{result[key]:.2f}"
    assert "Warmup completed." in log and "NVIDIA B300" in (DIRECTORY / "nvidia-smi.txt").read_text()
    assert hashes(DIRECTORY, RAW_NAMES) == raw_hashes and hashes(RUNTIME, RECEIPT_NAMES) == runtime_hashes
    report = {"schema_version": 1, "review_status": "passed", "issue_count": 0, "issues": [],
              "created_at": datetime.now(timezone.utc).isoformat(), "case": CASE, "run_id": RUN,
              "raw_file_sha256": raw_hashes, "runtime_receipt_sha256": runtime_hashes, "pins": pins,
              "normalized_settings": normalized, "independent_state_checks": states,
              "measured_counts": {"requested": 40, "completed": 40, "failed": 0, "exit_code": 0},
              "measurement": {key: result[key] for key in ("duration", "total_input_tokens", "total_output_tokens", "output_throughput", "total_token_throughput", "request_throughput", "median_tpot_ms")},
              "measured_start_utc": datetime.fromtimestamp(start, timezone.utc).isoformat(), "measured_end_utc": datetime.fromtimestamp(end, timezone.utc).isoformat(),
              "output_tokens_per_second_per_gpu": result["output_throughput"] / 8, "interactivity": 1000 / result["median_tpot_ms"],
              "graph_log_counts_by_phase": dict(graph_counts), "diagnostic_counts_by_phase": dict(diagnostic_counts),
              "diagnostic_evidence": diagnostics, "actual_capture_evidence": captures,
              "transfer_identity": {"path": str(TRANSFER), "sha256": sha(TRANSFER), "receipt_sha256": sha(TRANSFER.with_name(TRANSFER.name + ".verification.json"))},
              "setup_review_identity": {"path": "cutedsl-first-case-independent-review.json", "sha256": sha(ARTIFACTS / "cutedsl-first-case-independent-review.json")},
              "review_scope": "Independent direct raw/command/state/log/package/receipt and collector hash review; imports no auditor code. TP8/C4 only; not a full-sweep or quality claim."}
    (Path(__file__).parent / "verification-output.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "completed": 40, "capture_buckets": [1], "DP_pools": [1] * 8, "measurement": report["measurement"], "graphs": dict(graph_counts), "diagnostics": dict(diagnostic_counts)}, indent=2))


if __name__ == "__main__":
    main()
