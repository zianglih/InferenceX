#!/usr/bin/env python3
"""CPU-only behavior checks. No source-text assertions, server, CUDA or network."""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import run


def config() -> dict:
    return {
        "run_id": "trial",
        "run_root": "/tmp/trial",
        "python": "/opt/bin/python3",
        "sglang_root": "/src/sg",
        "sglang_commit": "1" * 40,
        "flashinfer_root": "/src/fi",
        "flashinfer_commit": "2" * 40,
        "model_path": "/models/glm",
        "model_revision": "3" * 40,
        "served_model": "glm",
        "image": "test:tag@sha256:" + "4" * 64,
        "gpu_ids": [str(i) for i in range(8)],
        "port": 30000,
        "ready_timeout_seconds": 3600,
        "benchmark_timeout_seconds": 14400,
        "term_seconds": 30,
        "kill_seconds": 15,
        "monitor_interval_seconds": 5,
        "base_environment": {"PATH": "/usr/bin:/bin", "LD_LIBRARY_PATH": "/image/lib"},
    }


class Checks(unittest.TestCase):
    def test_matrix_requests_and_order(self):
        rows = run.matrix()
        self.assertEqual(len({r["case_id"] for r in rows}), 24)
        self.assertEqual(sum(r["measured_requests"] for r in rows), 10080)
        self.assertEqual(sum(r["warmup_requests"] for r in rows), 2016)
        for precision in ("w4a4", "w4a16"):
            for tp in (4, 8):
                arm = [r for r in rows if r["precision"] == precision and r["tp"] == tp]
                self.assertEqual(
                    [r["concurrency"] for r in arm], [128, 4, 8, 16, 32, 64]
                )
                self.assertTrue(all(r["tp"] == r["dp"] == r["ep"] for r in arm))

    def test_tactics_separate_compile_shared(self):
        envs = [run.environment(config(), row) for row in run.matrix()]
        self.assertEqual(len({e["SGLANG_CACHE_DIR"] for e in envs}), 4)
        self.assertEqual(len({e["FLASHINFER_WORKSPACE_BASE"] for e in envs}), 1)
        self.assertEqual(len({e["CUTE_DSL_CACHE_DIR"] for e in envs}), 1)
        self.assertTrue(
            all(
                e["CUTE_DSL_NO_CACHE"] == "0"
                and e["CUTE_DSL_DISABLE_FILE_CACHING"] == "0"
                for e in envs
            )
        )
        self.assertEqual(envs[0]["SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16"], "0")
        self.assertEqual(envs[-1]["SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16"], "1")
        self.assertTrue(all(e["NVSHMEM_REMOTE_TRANSPORT"] == "none" for e in envs))
        self.assertTrue(all(e["NVSHMEM_IB_ENABLE_IBGDA"] == "0" for e in envs))
        self.assertTrue(all(e["NVSHMEM_DISABLE_LOCAL_ONLY_PROXY"] == "1" for e in envs))
        self.assertTrue(all(e["LD_LIBRARY_PATH"] == "/image/lib" for e in envs))
        self.assertTrue(
            all(
                e["PYTHONPATH"].split(os.pathsep) == ["/src/sg/python", str(run.REPO)]
                for e in envs
            )
        )

    def test_tp8_c4_keeps_client_concurrency(self):
        row = next(r for r in run.matrix() if r["tp"] == 8 and r["concurrency"] == 4)
        argv = run.server_command(config(), row)
        self.assertEqual(argv[argv.index("--max-running-requests") + 1], "8")
        self.assertEqual(argv[argv.index("--cuda-graph-max-bs-decode") + 1], "4")
        self.assertEqual(row["measured_requests"], 40)
        self.assertEqual(
            argv[argv.index("--speculative-moe-runner-backend") + 1],
            "flashinfer_trtllm",
        )

    def test_config_rejects_inherited_behavior(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config.json"
            cfg = config()
            p.write_text(json.dumps(cfg))
            self.assertEqual(run.read_config(p)["run_id"], "trial")
            for key in ("SGLANG_SIMULATE_ACC_LEN", "LD_PRELOAD"):
                bad = copy.deepcopy(cfg)
                bad["base_environment"][key] = "1"
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):
                    run.read_config(p)
            cfg["run_root"] = "/tmp/trial/../elsewhere"
            p.write_text(json.dumps(cfg))
            with self.assertRaises(ValueError):
                run.read_config(p)

    def test_result_counts_totals_and_interval(self):
        case = {"measured_requests": 2, "concurrency": 2}
        result = {
            "completed": 2,
            "num_prompts": 2,
            "max_concurrency": 2,
            "request_rate": "inf",
            "input_lens": [3, 4],
            "output_lens": [8, 9],
            "total_input_tokens": 7,
            "total_output_tokens": 17,
            "duration": 2.0,
            "output_throughput": 8.5,
        }
        self.assertEqual(run.validate_result(result, case)["output_lens"], [8, 9])
        for key, value in (
            ("completed", 1),
            ("input_lens", [7]),
            ("total_output_tokens", 16),
            ("output_throughput", 17),
            ("duration", 0),
        ):
            bad = dict(result, **{key: value})
            with self.assertRaises(ValueError):
                run.validate_result(bad, case)

    def test_seed_and_warmup_evidence(self):
        case = {"warmup_requests": 8}
        raw = "Namespace(model='glm', seed=0, x=1)\nWarming up with 8 requests...\nWarmup completed.\n"
        run.validate_client_log(raw, case)
        for bad in (
            raw.replace("seed=0", "seed=1"),
            raw.replace("Warmup completed.", "failed"),
        ):
            with self.assertRaises(ValueError):
                run.validate_client_log(bad, case)

    def test_request_plan_calls_original_sampler_after_seeding(self):
        events = []
        tokenizer = object()

        def load(*args, **kwargs):
            events.append(("tokenizer", args, kwargs))
            return tokenizer

        def sample(**kwargs):
            events.append(("sample", kwargs))
            return [("first", 901, 8192), ("second", 1007, 6553)]

        client = SimpleNamespace(
            __file__=str(run.REPO / "infx/bench_serving/benchmark_serving.py"),
            _load_tokenizer=load,
            sample_random_requests=sample,
        )
        modules = {
            "numpy": SimpleNamespace(
                random=SimpleNamespace(seed=lambda n: events.append(("numpy", n)))
            ),
            "infx.bench_serving": SimpleNamespace(benchmark_serving=client),
        }
        with (
            tempfile.TemporaryDirectory() as d,
            patch.dict(sys.modules, modules),
            patch("random.seed", side_effect=lambda n: events.append(("random", n))),
        ):
            destination = Path(d) / "requested-lengths.json"
            run.requested_lengths("/model", 2, destination)
            saved = json.loads(destination.read_text())
            self.assertEqual(events[:2], [("random", 0), ("numpy", 0)])
            self.assertEqual(
                events[2],
                (
                    "tokenizer",
                    ("/model",),
                    {"tokenizer_mode": "auto", "trust_remote_code": False},
                ),
            )
            self.assertEqual(
                events[3],
                (
                    "sample",
                    {
                        "prefix_len": 0,
                        "input_len": 1024,
                        "output_len": 8192,
                        "num_prompts": 2,
                        "range_ratio": 0.8,
                        "tokenizer": tokenizer,
                        "use_chat_template": True,
                        "dsv4": False,
                        "tokenizer_id": "/model",
                        "tokenizer_mode": "auto",
                        "trust_remote_code": False,
                        "num_workers": 0,
                    },
                ),
            )
            self.assertEqual(saved["input_lens"], [901, 1007])
            self.assertEqual(saved["output_lens"], [8192, 6553])
            self.assertEqual(saved["client_source"], run.digest(Path(client.__file__)))
            with self.assertRaises(FileExistsError):
                run.requested_lengths("/model", 2, destination)

    def test_requested_completed_lengths_reject_truncation_and_reordering(self):
        case = {"measured_requests": 2}
        planned = {
            "seed": 0,
            "nominal_input": 1024,
            "nominal_output": 8192,
            "ratio": 0.8,
            "num_prompts": 2,
            "model_path": config()["model_path"],
            "client_source": run.digest(
                run.REPO / "infx/bench_serving/benchmark_serving.py"
            ),
            "input_lens": [901, 1007],
            "output_lens": [8192, 6553],
        }
        result = {k: planned[k] for k in ("input_lens", "output_lens")}
        run.validate_requested_lengths(planned, result, case, config())
        for key, value in (
            ("output_lens", [8191, 6553]),
            ("output_lens", [6553, 8192]),
            ("input_lens", [1007, 901]),
        ):
            with self.assertRaises(ValueError):
                run.validate_requested_lengths(
                    planned, dict(result, **{key: value}), case, config()
                )
        for key, value in (("seed", 1), ("nominal_output", 2048), ("num_prompts", 1)):
            with self.assertRaises(ValueError):
                run.validate_requested_lengths(
                    dict(planned, **{key: value}), result, case, config()
                )

    def test_cache_copy_and_case_seal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            caches = root / "caches"
            (caches / "tactics/w4a4/tp4").mkdir(parents=True)
            (caches / "compile").mkdir()
            (caches / "tactics/w4a4/tp4/tactics.json").write_text('{"profile":1}\n')
            (caches / "compile/kernel.bin").write_bytes(b"compiled")
            (caches / "compile/link").symlink_to("kernel.bin")
            case = root / "case"
            case.mkdir()
            run.cache_snapshot(caches, case / "cache.after.json")
            snapshot = json.loads((case / "cache.after.json").read_text())
            self.assertNotIn("sha256", snapshot["files"]["compile/kernel.bin"])
            self.assertEqual(
                snapshot["files"]["compile/link"]["link_text"], "kernel.bin"
            )
            self.assertEqual(
                (case / "cache.after-tactics/w4a4/tp4/tactics.json").read_text(),
                '{"profile":1}\n',
            )
            run.save(case / "exit.json", {"status": "failed", "error": "preserved"})
            run.seal_case(case)
            manifest = json.loads((case / "manifest.json").read_text())
            self.assertIn("exit.json", manifest["files"])
            self.assertNotIn("manifest.json", manifest["files"])
            self.assertEqual(
                manifest["files"]["cache.after-tactics/w4a4/tp4/tactics.json"]["bytes"],
                14,
            )

    def test_discovery_retains_reused_owned_pid_births(self):
        with tempfile.TemporaryDirectory() as d:
            proc = run.OwnedProcess.__new__(run.OwnedProcess)
            proc.role, proc.directory, proc.known = "server", Path(d), {}
            proc.process = SimpleNamespace(pid=10, poll=lambda: None)
            birth = {10: "100", 11: "101"}

            def proc_text(path, *args, **kwargs):
                pid = int(path.parent.name)
                fields = (
                    ["S", "1" if pid == 10 else "10", "10", "10"]
                    + ["0"] * 15
                    + [birth[pid]]
                )
                return f"{pid} (worker) " + " ".join(fields)

            with (
                patch.object(
                    Path,
                    "iterdir",
                    return_value=iter([Path("/proc/10"), Path("/proc/11")]),
                ),
                patch.object(Path, "read_text", proc_text),
            ):
                proc.discover()
            birth[11] = "202"
            with (
                patch.object(
                    Path,
                    "iterdir",
                    return_value=iter([Path("/proc/10"), Path("/proc/11")]),
                ),
                patch.object(Path, "read_text", proc_text),
            ):
                proc.discover()
            ledger = [
                json.loads(line)
                for line in (Path(d) / "server.owners.jsonl").read_text().splitlines()
            ]
            self.assertEqual(
                [
                    r["starttime"]
                    for row in ledger
                    for r in row["owners"]
                    if r["pid"] == 11
                ],
                ["101", "202"],
            )
            self.assertEqual(proc.known[11]["starttime"], "202")

    def test_failed_or_partial_spawn_skips_after_cache_scan(self):
        for partial_spawn in (False, True):
            with (
                self.subTest(partial_spawn=partial_spawn),
                tempfile.TemporaryDirectory() as d,
            ):
                cfg = config()
                cfg["run_root"] = d
                (Path(d) / "cases").mkdir()
                case = run.matrix()[0]
                server = SimpleNamespace(
                    role="server",
                    process=SimpleNamespace(poll=lambda: 1, returncode=1),
                    discover=lambda: None,
                    cleanup=lambda *_: {"remaining": [123], "errors": []},
                )
                with (
                    patch.object(
                        run,
                        "gpu_snapshot",
                        return_value={"applications": {"stdout": ""}},
                    ),
                    patch.object(run, "require_idle"),
                    patch.object(run, "source_snapshot", return_value={}),
                    patch.object(run.socket, "socket"),
                    patch.object(run, "cache_snapshot") as snapshot,
                    patch.object(
                        run,
                        "OwnedProcess",
                        side_effect=RuntimeError("partial spawn")
                        if partial_spawn
                        else None,
                        return_value=server,
                    ),
                ):
                    with self.assertRaises(RuntimeError):
                        run.run_case(cfg, case, {}, {})
                self.assertEqual(snapshot.call_count, 1)
                self.assertEqual(snapshot.call_args.args[1].name, "cache.before.json")
                directory = Path(d) / "cases" / case["case_id"]
                self.assertTrue((directory / "cache.after-skipped.json").is_file())
                self.assertEqual(
                    json.loads((directory / "exit.json").read_text())["status"],
                    "failed",
                )
                self.assertTrue((directory / "manifest.json").is_file())

    def test_actual_bash_bridge_arguments_and_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            stub = p / "python3"
            stub.write_text(
                f"#!{sys.executable}\n"
                + """import json,os,sys
from pathlib import Path
with open(os.environ['STUB_ARGS'], 'a') as f: f.write(json.dumps(sys.argv[1:])+'\\n')
if 'capture' in sys.argv: print('{}')
elif '--request-lengths' in sys.argv: pass
else: sys.exit(int(os.environ['STUB_EXIT']))
"""
            )
            stub.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(p) + os.pathsep + os.environ["PATH"],
                CASE_DIR=str(p),
                MODEL_PATH="/model",
                SERVED_MODEL="glm",
                PORT="30000",
                CONC="4",
                SERVER_PID="123",
                EVAL_ONLY="false",
                PROFILE="0",
                PYTHONPATH="/source",
                PYTHONPYCACHEPREFIX=str(p / "pycache"),
                STUB_ARGS=str(p / "args.jsonl"),
                STUB_EXIT="7",
            )
            result = subprocess.run(
                ["bash", str(run.HERE / "benchmark_mtp.sh")],
                env=env,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 7)
            calls = [
                json.loads(line) for line in (p / "args.jsonl").read_text().splitlines()
            ]
            self.assertEqual(
                calls[-2],
                [
                    str(run.HERE / "run.py"),
                    "--request-lengths",
                    "--model-path",
                    "/model",
                    "--num-prompts",
                    "40",
                    "--destination",
                    str(p / "requested-lengths.json"),
                ],
            )
            cmd = calls[-1]
            self.assertEqual(cmd[cmd.index("--num-prompts") + 1], "40")
            self.assertEqual(cmd[cmd.index("--num-warmups") + 1], "8")
            self.assertEqual(cmd[cmd.index("--random-output-len") + 1], "8192")
            self.assertEqual(cmd[cmd.index("--random-range-ratio") + 1], "0.8")
            self.assertIn("--use-chat-template", cmd)
            self.assertIn("--ignore-eos", cmd)
            self.assertTrue((p / "server_watch.json").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
