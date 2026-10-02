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


def speculative(lengths):
    from infx.bench_serving.speculative_metrics import summarize_speculative_metrics

    return summarize_speculative_metrics(
        [
            {
                "request_index": i,
                "success": True,
                "completion_tokens": length,
                "spec_tokens_details": {
                    "spec_verify_ct": 2,
                    "spec_num_correct_drafts": 4,
                    "spec_num_proposed_drafts": 6,
                    "spec_accept_length": length / 2,
                    "spec_accept_rate": 4 / 6,
                },
            }
            for i, length in enumerate(lengths)
        ]
    )


def config() -> dict:
    return {
        "campaign_contract": "glm52-six-curves-measured-mtp-v1",
        "run_id": "trial",
        "run_root": "/tmp/trial",
        "tmp_root": "/tmp/infx-local-check",
        "compile_cache_seed": None,
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
        self.assertEqual(len({r["case_id"] for r in rows}), 36)
        self.assertEqual(sum(r["measured_requests"] for r in rows), 3780)
        self.assertEqual(sum(r["warmup_requests"] for r in rows), 756)
        for arm_id in ("megamoe-w4a4", "megamoe-w4a16", "trtllm-w4a4"):
            for tp in (4, 8):
                arm = [r for r in rows if r["arm_id"] == arm_id and r["tp"] == tp]
                self.assertEqual([r["concurrency"] for r in arm], [32, 1, 2, 4, 8, 16])
                self.assertTrue(all(r["tp"] == r["dp"] == r["ep"] for r in arm))

    def test_tactics_separate_compile_shared(self):
        envs = [run.environment(config(), row) for row in run.matrix()]
        self.assertEqual(len({e["SGLANG_CACHE_DIR"] for e in envs}), 6)
        self.assertEqual(len({e["FLASHINFER_WORKSPACE_BASE"] for e in envs}), 1)
        self.assertEqual(len({e["CUTE_DSL_CACHE_DIR"] for e in envs}), 1)
        self.assertNotIn("SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16", envs[0])
        self.assertEqual(envs[12]["SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16"], "1")
        self.assertNotIn("SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16", envs[-1])
        for row, env in zip(run.matrix(), envs):
            self.assertNotIn("SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION", env)
            self.assertNotIn("SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE", env)
            self.assertNotIn("SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE", env)
            argv = run.server_command(config(), row)
            self.assertNotIn("--disable-flashinfer-quant-fast-math", argv)
            self.assertEqual(
                argv[argv.index("--moe-runner-backend") + 1],
                "flashinfer_trtllm"
                if row["arm_id"] == "trtllm-w4a4"
                else "flashinfer_megamoe",
            )
        self.assertTrue(all("NVSHMEM_REMOTE_TRANSPORT" not in e for e in envs))
        self.assertTrue(all("NVSHMEM_IB_ENABLE_IBGDA" not in e for e in envs))
        self.assertTrue(all("NVSHMEM_DISABLE_LOCAL_ONLY_PROXY" not in e for e in envs))
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

    def test_measured_mtp_coverage_replay_and_order(self):
        raw = {"output_lens": [8, 9], "speculative_metrics": speculative([8, 9])}
        checked = run.validate_speculative_metrics(raw, 2)
        self.assertEqual(checked["acceptance_length"], 4.25)
        self.assertEqual(checked["spec_verify_ct"], 4)
        for mutate in (
            lambda d: d.pop("speculative_metrics"),
            lambda d: d["speculative_metrics"].update(acceptance_length=4.0),
            lambda d: d["speculative_metrics"].update(
                requests=d["speculative_metrics"]["requests"][:1]
            ),
            lambda d: d.update(output_lens=[9, 8]),
            lambda d: d["speculative_metrics"]["requests"][0][
                "spec_tokens_details"
            ].pop("spec_verify_ct"),
        ):
            bad = copy.deepcopy(raw)
            mutate(bad)
            with self.assertRaises(ValueError):
                run.validate_speculative_metrics(bad, 2)

    def test_low_concurrency_keeps_client_count_and_server_floor(self):
        for tp in (4, 8):
            for c in (1, 2):
                case = next(
                    x for x in run.matrix() if x["tp"] == tp and x["concurrency"] == c
                )
                argv = run.server_command(config(), case)
                self.assertEqual(case["measured_requests"], 10 * c)
                self.assertEqual(case["warmup_requests"], 2 * c)
                self.assertEqual(
                    argv[argv.index("--max-running-requests") + 1], str(tp)
                )
                self.assertEqual(
                    argv[argv.index("--cuda-graph-max-bs-decode") + 1], str(c)
                )

    def test_config_rejects_inherited_behavior(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config.json"
            cfg = config()
            p.write_text(json.dumps(cfg))
            self.assertEqual(run.read_config(p)["run_id"], "trial")
            for key in (
                "SGLANG_SIMULATE_ACC_LEN",
                "TRTLLM_DISABLE_FP4_QUANT_FAST_MATH",
                "NVSHMEM_REMOTE_TRANSPORT",
                "LD_PRELOAD",
            ):
                bad = copy.deepcopy(cfg)
                bad["base_environment"][key] = "1"
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError):
                    run.read_config(p)
            preserved = copy.deepcopy(cfg)
            preserved["base_environment"]["SGLANG_RUST_BUILD_MODE"] = "never"
            p.write_text(json.dumps(preserved))
            checked = run.read_config(p)
            for case in run.matrix():
                self.assertEqual(
                    run.environment(checked, case)["SGLANG_RUST_BUILD_MODE"], "never"
                )
            for key, value in (
                ("SGLANG_RUST_BUILD_MODE", "auto"),
                ("SGLANG_RUST_BUILD_MODE", "force"),
                ("SGLANG_BUILD_COMMIT", "unrelated-image-label"),
            ):
                invalid = copy.deepcopy(cfg)
                invalid["base_environment"][key] = value
                p.write_text(json.dumps(invalid))
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
        result["speculative_metrics"] = speculative(result["output_lens"])
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
            proc.process = SimpleNamespace(pid=10, poll=lambda: None, returncode=None)
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

    def test_late_same_session_descendant_is_cleaned_after_leader_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            child = run.OwnedProcess.__new__(run.OwnedProcess)
            child.directory, child.role = Path(temp), "child"
            leader = {
                "pid": 10,
                "starttime": "100",
                "state": "Z",
                "ppid": 1,
                "sid": 10,
                "pgid": 10,
            }
            late = {
                "pid": 11,
                "starttime": "101",
                "state": "S",
                "ppid": 1,
                "sid": 10,
                "pgid": 10,
            }
            rows = {10: leader, 11: late}
            child.known = {10: leader.copy()}
            child.log = (Path(temp) / "child.log").open("w")

            def reap():
                rows.pop(10, None)
                child.process.returncode = 0
                return 0

            child.process = SimpleNamespace(
                pid=10, returncode=None, poll=reap, wait=lambda **_: 0
            )
            signaled = []

            def kill(pid, sig):
                signaled.append(pid)
                rows[pid] = dict(rows[pid], state="Z")

            with (
                patch.object(
                    Path,
                    "iterdir",
                    side_effect=lambda: [Path(f"/proc/{pid}") for pid in rows],
                ),
                patch.object(run, "process_row", side_effect=lambda pid: rows.get(pid)),
                patch.object(run.os, "kill", side_effect=kill),
            ):
                self.assertFalse(child.running())
                self.assertIn(11, child.known)
                receipt = child.cleanup(1, 1)
            self.assertEqual(signaled, [11])
            self.assertEqual(receipt["waited_returncode"], 0)
            self.assertEqual(receipt["remaining"], [])
            self.assertEqual(receipt["errors"], [])

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
                    running=lambda: False,
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

    def test_short_tmp_config_and_environment(self):
        cfg = config()
        self.assertEqual(
            run.environment(cfg, run.matrix()[0])["TMPDIR"], cfg["tmp_root"]
        )
        for value in (
            "/tmp/" + "infx-" + "x" * 25,
            "/var/tmp/infx-case",
            "/tmp/shared",
            "/tmp/infx-a/../infx-b",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                run.validate_tmp_root(dict(cfg, tmp_root=value))

    def test_real_unix_socket_shapes_and_cleanup(self):
        # macOS /tmp is a symlink; use its real path for this OS-only primitive.
        with tempfile.TemporaryDirectory(prefix="ix-", dir=Path("/tmp").resolve()) as d:
            receipt = {}
            run.socket_path_preflight(Path(d), receipt)
            self.assertEqual(len(receipt["probes"]), 3)
            self.assertTrue(
                all(p["bound"] and not p["cleanup_errors"] for p in receipt["probes"])
            )
            self.assertTrue(
                all(
                    p["max_pid_rank_path_bytes_with_nul"] <= 108
                    for p in receipt["probes"]
                )
            )
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_long_socket_budget_rejected_without_leaking_probe(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d).resolve() / ("long-" + "x" * 100)
            path.mkdir()
            receipt = {}
            with self.assertRaisesRegex(ValueError, "sun_path budget"):
                run.socket_path_preflight(path, receipt)
            self.assertFalse(receipt["probes"][0]["bound"])
            self.assertEqual(list(path.iterdir()), [])

    def test_exclusive_tmp_owner_marker_and_existing_scope_rejection(self):
        with tempfile.TemporaryDirectory(prefix="ix-", dir=Path("/tmp").resolve()) as d:
            parent = Path(d)
            path = parent / "infx-case"
            first = parent / "first"
            first.mkdir()
            second = parent / "second"
            second.mkdir()
            actual_open = os.open

            def mapped_open(name, flags, *args, **kwargs):
                return actual_open(
                    parent if name == "/tmp" else name, flags, *args, **kwargs
                )

            with (
                patch.object(run, "validate_tmp_root", return_value=path),
                patch.object(run.os, "open", mapped_open),
            ):
                run.prepare_tmp_scope(config(), first)
                marker = (path / ".inferencex-owner.json").read_bytes()
                proof = json.loads((first / "tmp-preflight.json").read_text())
                self.assertEqual(proof["status"], "AF_UNIX_PATH_PREFLIGHT_PASSED")
                self.assertEqual(json.loads(marker)["run_id"], "trial")
                self.assertEqual(path.stat().st_mode & 0o777, 0o700)
                with self.assertRaises(FileExistsError):
                    run.prepare_tmp_scope(config(), second)
                self.assertEqual((path / ".inferencex-owner.json").read_bytes(), marker)
                self.assertEqual(
                    json.loads((second / "tmp-preflight.json").read_text())["status"],
                    "FAILED",
                )

    def test_probe_does_not_remove_unexpected_children(self):
        with tempfile.TemporaryDirectory(prefix="ix-", dir=Path("/tmp").resolve()) as d:
            actual_mkdtemp = tempfile.mkdtemp

            def extra_child(*args, **kwargs):
                name = actual_mkdtemp(*args, **kwargs)
                (Path(name) / "foreign").write_bytes(b"keep")
                return name

            with patch.object(run.tempfile, "mkdtemp", extra_child):
                receipt = {}
                with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
                    run.socket_path_preflight(Path(d), receipt)
            self.assertEqual(next(Path(d).glob("*/foreign")).read_bytes(), b"keep")
            self.assertEqual(list(Path(d).glob("*/fd.sock")), [])

    def test_compile_copy_independent_bytes_and_fresh_tactics(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d).resolve()
            source = base / "seed"
            source.mkdir()
            (source / "torch").mkdir()
            (source / "empty").mkdir()
            (source / "torch" / "kernel.so").write_bytes(b"compiled")
            manifest = base / "seed.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "root": str(source),
                        "files": {
                            "torch/kernel.so": run.digest(source / "torch/kernel.so")
                        },
                        "directories": ["empty", "torch"],
                        "source": {"terminal": "fixture-only"},
                    }
                )
            )
            root = base / "run"
            (root / "caches/compile/cute").mkdir(parents=True)
            (root / "caches/tactics/w4a4/tp4").mkdir(parents=True)
            cfg = dict(
                config(),
                run_root=str(root),
                compile_cache_seed={
                    "root": str(source),
                    "manifest": str(manifest),
                    "manifest_sha256": run.digest(manifest)["sha256"],
                },
            )
            run.validate_compile_seed(cfg)
            run.copy_compile_seed(cfg, root)
            copied = root / "caches/compile/torch/kernel.so"
            self.assertEqual(copied.read_bytes(), b"compiled")
            self.assertNotEqual(
                copied.stat().st_ino, (source / "torch/kernel.so").stat().st_ino
            )
            self.assertEqual(list((root / "caches/tactics/w4a4/tp4").iterdir()), [])
            self.assertFalse(
                json.loads((root / "compile-cache-seed.json").read_text())[
                    "tactics_copied"
                ]
            )
            with self.assertRaisesRegex(ValueError, "already populated"):
                run.copy_compile_seed(cfg, root)
            copied.write_bytes(b"new")
            self.assertEqual((source / "torch/kernel.so").read_bytes(), b"compiled")
            (source / "torch/kernel.so").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "differ from manifest"):
                run.copy_compile_seed(cfg, root)

    def test_compile_seed_rejects_links_missing_roots_and_invalid_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            base = Path(d).resolve()
            source = base / "seed"
            source.mkdir()
            with self.assertRaises(ValueError):
                run.compile_seed_inventory(base / "absent")
            (source / "provider").symlink_to(base, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "link or special"):
                run.compile_seed_inventory(source)
            (source / "provider").unlink()
            manifest = base / "seed.json"
            manifest.write_text("{}")
            cfg = dict(
                config(),
                compile_cache_seed={
                    "root": str(source),
                    "manifest": str(manifest),
                    "manifest_sha256": "0" * 64,
                },
            )
            with self.assertRaisesRegex(ValueError, "manifest changed"):
                run.copy_compile_seed(cfg, base)
            cfg["compile_cache_seed"]["manifest_sha256"] = run.digest(manifest)[
                "sha256"
            ]
            with self.assertRaisesRegex(ValueError, "schema/root mismatch"):
                run.copy_compile_seed(cfg, base)
            cfg["compile_cache_seed"]["root"] = cfg["run_root"]
            with self.assertRaises(ValueError):
                run.validate_compile_seed(cfg)

    def test_shared_bridge_capture_is_explicit_optin(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            stub = root / "python3"
            stub.write_text(
                f"#!{sys.executable}\nimport json,sys\nprint(json.dumps(sys.argv[1:]))\n"
            )
            stub.chmod(0o755)
            env = dict(
                os.environ,
                PATH=str(root) + os.pathsep + os.environ["PATH"],
                EVAL_ONLY="false",
                PROFILE="0",
                PORT="30000",
                PYTHONPYCACHEPREFIX=str(root / "pycache"),
            )
            env.pop("INFERENCEX_SERVER_STATE", None)
            script = 'source "$1"; shift; run_benchmark_serving --model glm --port 30000 --backend vllm --input-len 1024 --output-len 8192 --random-range-ratio 0.8 --num-prompts 10 --max-concurrency 1 --result-filename result --result-dir "$1" --bench-serving-dir "$1" "${@:2}"'
            for flags in ([], ["--capture-speculative-metrics"]):
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        script,
                        "test",
                        str(run.REPO / "benchmarks/benchmark_lib.sh"),
                        str(root),
                        *flags,
                    ],
                    env=env,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                argv = json.loads(result.stdout.strip().splitlines()[-1])
                self.assertEqual(
                    argv.count("--capture-speculative-metrics"), len(flags)
                )
                self.assertEqual(argv[argv.index("--num-warmups") + 1], "2")

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
            self.assertIn("--capture-speculative-metrics", cmd)
            self.assertIn("--use-chat-template", cmd)
            self.assertIn("--ignore-eos", cmd)
            self.assertTrue((p / "server_watch.json").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
