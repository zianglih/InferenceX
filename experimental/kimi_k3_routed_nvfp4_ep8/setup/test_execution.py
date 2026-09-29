#!/usr/bin/env python3
"""CPU behavior tests only. Synthetic fixtures are not runtime or benchmark acceptance."""

import copy
import io
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import execution as e
import plan


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            prefix="execution-synthetic-", dir=plan.ROOT / "artifacts"
        )
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, name, value):
        p = self.root / name
        e.save(p, value)
        return {"path": str(p), **plan.descriptor(p)}

    def fixture(self):
        cfg = copy.deepcopy(plan.read_json(plan.ROOT / "campaign.json"))
        cfg.update(
            status="READY_FOR_EXECUTION",
            authorization="EXECUTE_AUTHORIZED",
            blockers=[],
        )
        cfg["runtime"].update(
            run_root=str(self.root / "run"),
            python=sys.executable,
            tmp_root="/tmp/infx-k3-synthetic-test",
        )
        for name, value in cfg["runtime"].items():
            if isinstance(value, str) and value.startswith("/REVIEW_REQUIRED/"):
                cfg["runtime"][name] = str(self.root / name)
        ck = self.put(
            "checkpoint.json",
            {
                "status": "ACCEPTED_CUSTOM_ROUTED_NVFP4",
                "data_kind": "actual",
                "output_path": cfg["runtime"]["model_path"],
            },
        )
        cfg["checkpoint"]["acceptance"] = ck
        cd = self.put("campaign.json", cfg)
        pp = plan.build_plan(cd["path"], runtime_project=str(plan.ROOT))
        pd = self.put("PLAN.json", pp)
        request = {
            "remote_project": str(plan.ROOT),
            "run_root": cfg["runtime"]["run_root"],
            "sglang_root": cfg["runtime"]["sglang_root"],
            "flashinfer_source_root": cfg["runtime"]["flashinfer_root"],
            "checkpoint": {
                "path": cfg["runtime"]["model_path"],
                "acceptance_sha256": ck["sha256"],
            },
            "server_args": {
                arm: next(c for c in pp["cases"] if c["arm_id"] == arm)["server_argv"][
                    4:
                ]
                for arm in plan.ARM_CONTRACT
            },
            "port": 30000,
            "node": {"hostname": "synthetic"},
            "bound_files": {},
            "protected_runtime_files": {},
        }
        rd = self.put("request.json", request)
        receipts = {
            arm: self.put(
                arm + ".json",
                {
                    "status": "KIMI_RUNTIME_PREFLIGHT_PASSED_PENDING_ROOT_REVIEW",
                    "arm": arm,
                    "request_sha256": rd["sha256"],
                    "error": None,
                    "node_expected_external_api_guard": request["node"],
                    "python_executable": sys.executable,
                },
            )
            for arm in plan.ARM_CONTRACT
        }
        bindings = {**pp["bindings"]}
        for desc in (cd, pd, rd, ck, *receipts.values()):
            bindings[desc["path"]] = {k: desc[k] for k in ("bytes", "sha256")}
        for name in ("execution.py", "results.py", "preflight.py"):
            p = plan.ROOT / "setup" / name
            bindings[str(p)] = plan.descriptor(p)
        marker = {
            "schema_version": 1,
            "status": "ACCEPTED_KIMI_RUNTIME_PREFLIGHT",
            "campaign": cd,
            "plan": pd,
            "runtime_project_root": str(plan.ROOT),
            "checkpoint_acceptance": ck,
            "preflight_request": rd,
            "preflight_receipts": receipts,
            "environment_passthrough": {},
            "bindings": bindings,
        }
        return cfg, pp, marker

    def source_fixture(self):
        cfg = copy.deepcopy(plan.read_json(plan.ROOT / "campaign.json"))
        submodules = " initialized-parent 3rdparty/cutlass\n-b20f4d0adb95f53c4a1272915ef8d86cec304584 3rdparty/nixl"
        snapshots = {
            cfg["runtime"]["sglang_root"]: {
                "commit": cfg["pins"]["sglang"],
                "submodules": "",
            },
            cfg["runtime"]["flashinfer_root"]: {
                "commit": cfg["pins"]["flashinfer"],
                "submodules": submodules.strip(),
            },
        }
        receipts = {}
        for arm in plan.ARM_CONTRACT:
            receipts[arm] = self.put(
                "source-" + arm + ".json",
                {
                    "status": "KIMI_RUNTIME_PREFLIGHT_PASSED_PENDING_ROOT_REVIEW",
                    "arm": arm,
                    "error": None,
                    "sources": snapshots,
                },
            )
        observed = copy.deepcopy(snapshots)

        def capture(argv, _env, **_kwargs):
            if argv[0] == "git":
                row = observed[argv[2]]
                value = (
                    row["commit"]
                    if argv[3] == "rev-parse"
                    else row.get("dirty", "")
                    if argv[3] == "diff"
                    else row["submodules"]
                )
            else:
                value = "pinned-package==1\n"
            return {"returncode": 0, "stdout": value, "stderr": ""}

        return cfg, {"preflight_receipts": receipts}, observed, capture

    def test_runtime_snapshot_accepts_only_exact_preflight_submodules(self):
        cfg, marker, observed, capture = self.source_fixture()
        root = cfg["runtime"]["flashinfer_root"]
        with mock.patch.object(e, "capture", side_effect=capture):
            result = e.runtime_snapshot(cfg, {}, marker)
            self.assertEqual(
                result["sources"][root]["submodules"], observed[root]["submodules"]
            )
            self.assertEqual(result["pip_freeze"], ["pinned-package==1"])
            original = observed[root]["submodules"]
            for changed in (
                original.replace("-b20f", " b20f"),
                original.replace("-b20f", "+b20f"),
                original.replace("b20f", "a20f"),
                original + "\n unexpected-module",
            ):
                with self.subTest(changed=changed):
                    observed[root]["submodules"] = changed
                    with self.assertRaisesRegex(ValueError, "Source submodule state"):
                        e.runtime_snapshot(cfg, {}, marker)
            observed[root]["submodules"] = original
            observed[root]["dirty"] = "changed.py"
            with self.assertRaisesRegex(ValueError, "Source HEAD/working tree"):
                e.runtime_snapshot(cfg, {}, marker)

    def test_runtime_snapshot_requires_three_matching_bound_source_proofs(self):
        cfg, marker, observed, capture = self.source_fixture()
        with mock.patch.object(e, "capture", side_effect=capture):
            missing = copy.deepcopy(marker)
            del missing["preflight_receipts"]["trtllm-w4a4"]
            with self.assertRaisesRegex(ValueError, "Three source proofs"):
                e.runtime_snapshot(cfg, {}, missing)
            item = marker["preflight_receipts"]["trtllm-w4a4"]
            receipt = e.read_json(item["path"])
            receipt["sources"][cfg["runtime"]["flashinfer_root"]]["submodules"] += (
                " changed"
            )
            marker["preflight_receipts"]["trtllm-w4a4"] = self.put(
                "source-conflict.json", receipt
            )
            with self.assertRaisesRegex(ValueError, "snapshots disagree"):
                e.runtime_snapshot(cfg, {}, marker)
            marker["preflight_receipts"]["trtllm-w4a4"] = item
            Path(item["path"]).write_bytes(b"{}\n")
            with self.assertRaisesRegex(ValueError, "Changed bound file"):
                e.runtime_snapshot(cfg, {}, marker)

    def gate(self, cfg, pp, marker):
        md = self.put(
            "marker-" + str(len(list(self.root.glob("marker-*")))) + ".json", marker
        )
        original_plain = e.plain_path

        def fixture_plain(path, **kwargs):
            # Simulate Linux's real /tmp only; macOS /tmp is a symlink. Every
            # other path goes through the production no-link validator.
            if str(path) == cfg["runtime"]["tmp_root"]:
                return Path(path)
            return original_plain(path, **kwargs)

        with (
            mock.patch.object(e.sys, "platform", "linux"),
            mock.patch.object(e.socket, "gethostname", return_value="synthetic"),
            mock.patch.object(e, "plain_path", side_effect=fixture_plain),
        ):
            return e.validate_marker(
                marker["campaign"]["path"], pp, md["path"], md["sha256"]
            )

    def test_exact_gate_and_mutated_plan(self):
        cfg, pp, marker = self.fixture()
        self.gate(cfg, pp, marker)
        altered = copy.deepcopy(pp)
        altered["cases"][0]["client_argv"].append("--unexpected")
        with self.assertRaisesRegex(ValueError, "plan differs"):
            self.gate(cfg, altered, marker)

    def test_missing_arm_and_source_mutation(self):
        cfg, pp, marker = self.fixture()
        bad = copy.deepcopy(marker)
        bad["preflight_receipts"].pop("trtllm-w4a4")
        with self.assertRaisesRegex(ValueError, "Three preflight"):
            self.gate(cfg, pp, bad)
        Path(marker["preflight_request"]["path"]).write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "Changed bound"):
            self.gate(cfg, pp, marker)

    def test_unapproved_overlay_rejected(self):
        cfg, pp, marker = self.fixture()
        marker["environment_passthrough"] = {
            "FLASHINFER_DISABLE_FP4_QUANT_FAST_MATH": "1"
        }
        with self.assertRaisesRegex(ValueError, "Unreviewed environment"):
            self.gate(cfg, pp, marker)

    def test_existing_output_and_symlink_rejected(self):
        cfg, pp, marker = self.fixture()
        Path(cfg["runtime"]["run_root"]).mkdir()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.gate(cfg, pp, marker)
        target = self.root / "target"
        target.mkdir()
        link = self.root / "link"
        link.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "Linked"):
            e.plain_path(link / "new", absent=True)

    def test_atomic_writer_and_manifest_rehash(self):
        root = self.root / "run"
        case = root / "cases" / "example"
        case.mkdir(parents=True)
        e.save(case / "result.json", {"SYNTHETIC_TEST_ONLY": True})
        with self.assertRaises(FileExistsError):
            e.save(case / "result.json", {})
        e.seal_case(case, root, "example")
        manifest = plan.read_json(case / "manifest.json")
        self.assertEqual(manifest["case_id"], "example")
        for d in manifest["files"]:
            self.assertEqual(
                plan.descriptor(root / d["path"]),
                {k: d[k] for k in ("bytes", "sha256")},
            )

    def owner(self):
        x = e.OwnedProcess.__new__(e.OwnedProcess)
        x.role = "synthetic"
        x.directory = self.root
        x.process = mock.Mock()
        x.process.pid = 100
        x.process.poll.return_value = 0
        x.process.wait.return_value = 0
        x.log = io.BytesIO()
        saved = {
            "pid": 100,
            "starttime": "1",
            "state": "S",
            "ppid": 1,
            "sid": 100,
            "pgid": 100,
        }
        x.known = {100: saved}
        x.history = {(100, "1"): saved}
        return x, saved

    def test_pid_reuse_is_never_signalled(self):
        x, saved = self.owner()
        recycled = {**saved, "starttime": "2"}
        with (
            mock.patch.object(x, "discover"),
            mock.patch.object(e, "process_row", return_value=recycled),
            mock.patch.object(e.os, "kill") as kill,
        ):
            result = x.cleanup(1, 1)
        kill.assert_not_called()
        self.assertEqual(result["remaining"], [])
        self.assertEqual(result["owners"], [saved])

    def test_discovery_failure_not_absence(self):
        x, _ = self.owner()
        with (
            mock.patch.object(
                x, "discover", side_effect=PermissionError("synthetic denied")
            ),
            mock.patch.object(e.os, "kill") as kill,
        ):
            result = x.cleanup(1, 1)
        kill.assert_not_called()
        self.assertTrue(result["errors"])
        self.assertEqual(result["remaining"], [{"unknown": True}])

    def test_server_death_and_timeout(self):
        child = mock.Mock()
        child.role = "benchmark"
        child.running.return_value = True
        server = mock.Mock()
        server.running.return_value = False
        with self.assertRaisesRegex(ValueError, "Server died"):
            e.wait_child(child, 10, lambda: None, server)
        with mock.patch.object(e.time, "monotonic", side_effect=[0, 2]):
            with self.assertRaises(TimeoutError):
                e.wait_child(child, 1, lambda: None)

    def test_late_descendant_discovered_before_reap(self):
        x, saved = self.owner()
        x.direct_birth = saved
        zombie = {**saved, "state": "Z"}
        late = {
            "pid": 101,
            "starttime": "2",
            "state": "S",
            "ppid": 1,
            "sid": 100,
            "pgid": 100,
        }
        rows = {100: zombie, 101: late}

        def fake_wait(*args, **kwargs):
            self.assertIn(101, x.known)
            rows.pop(100)
            return 0

        x.process.wait.side_effect = fake_wait
        x.process.poll.side_effect = AssertionError(
            "poll must not reap before discovery"
        )
        with (
            mock.patch.object(
                e.Path,
                "iterdir",
                return_value=iter([Path("/proc/100"), Path("/proc/101")]),
            ),
            mock.patch.object(e, "process_row", side_effect=lambda pid: rows.get(pid)),
        ):
            e.wait_child(x, 1, lambda: None)
        self.assertEqual(x.known[101], late)
        self.assertEqual(x.history[(101, "2")], late)

    def test_gpu_wrong_identity_or_active_rejected(self):
        expected = [
            {"index": i, "uuid": f"synthetic-{i}", "name": "NVIDIA B300"}
            for i in range(8)
        ]
        snap = {
            "gpus": expected,
            "applications": {"stdout": "1234, synthetic-0, 10"},
            "metrics": [
                {"index": i, "utilization_percent": 0, "memory_mib": 0}
                for i in range(8)
            ],
        }
        with self.assertRaisesRegex(ValueError, "applications"):
            e.require_gpu(snap, expected, idle=True)
        snap["applications"]["stdout"] = ""
        e.require_gpu(snap, expected, idle=True)
        snap["metrics"][0]["memory_mib"] = 101
        with self.assertRaisesRegex(ValueError, "memory"):
            e.require_gpu(snap, expected, idle=True)
        snap["metrics"][0]["memory_mib"] = 0
        with self.assertRaisesRegex(ValueError, "identity"):
            e.require_gpu(snap, list(reversed(expected)), idle=True)

    def test_cache_scope_tactic_bytes_and_symlink_metadata(self):
        cache = self.root / "caches"
        (cache / "tactics/a").mkdir(parents=True)
        (cache / "compile").mkdir()
        (cache / "tactics/a/data").write_bytes(b"synthetic-tactic")
        external = self.root / "outside"
        external.write_bytes(b"must-not-copy")
        (cache / "compile/provider").symlink_to(external)
        destination = self.root / "cache.before.json"
        e.cache_snapshot(cache, destination)
        doc = plan.read_json(destination)
        self.assertEqual(doc["files"]["compile/provider"]["kind"], "symlink")
        self.assertEqual(
            (self.root / "cache.before-tactics/a/data").read_bytes(),
            b"synthetic-tactic",
        )
        self.assertFalse((self.root / "cache.before-tactics/compile/provider").exists())

    def case_fixture(self):
        from results import LATENCIES

        cfg = copy.deepcopy(plan.read_json(plan.ROOT / "campaign.json"))
        root = self.root / "run"
        (root / "cases").mkdir(parents=True)
        (root / "caches").mkdir()
        cfg["runtime"]["run_root"] = str(root)
        case = copy.deepcopy(plan.build_plan()["cases"][1])
        case["case_dir"] = str(root / "cases" / case["case_id"])
        case["environment"] = {}
        arrays = {"input_lens": [900] * 40, "output_lens": [7000] * 40}
        result = {
            "num_prompts": 40,
            "completed": 40,
            "max_concurrency": 4,
            "total_input_tokens": 36000,
            "total_output_tokens": 280000,
            "benchmark_outcome": {
                "status": "passed",
                "requested": 40,
                "completed": 40,
                "failed": 0,
                "max_failure_rate": 0.05,
            },
            "request_rate": "inf",
            "burstiness": 1,
            "best_of": 1,
            "backend": "vllm",
            "model_id": "Kimi-K3-NVFP4",
            "tokenizer_id": cfg["runtime"]["model_path"],
            "duration": 100,
            "benchmark_start_time_unix": 1000,
            "benchmark_end_time_unix": 1100,
            "output_throughput": 2800,
            "request_throughput": 0.4,
            "total_token_throughput": 3160,
            **arrays,
            **dict.fromkeys(LATENCIES, 10.0),
        }
        children = []

        class Child:
            def __init__(child, argv, env, directory, role, cwd):
                child.role = role
                child.directory = directory
                child.cleaned = 0
                child.process = mock.Mock()
                child.process.pid = 123
                child.process.poll.return_value = None if role == "server" else 0
                child.process.wait.return_value = 0
                child.process.returncode = 0
                if role == "request-plan":
                    e.save(directory / "requested-lengths.json", arrays)
                if role == "benchmark":
                    e.save(directory / "result.json", result)
                log = (
                    "Namespace(seed=0)\nWarming up with 8 requests...\nWarmup completed.\n"
                    if role == "benchmark"
                    else "SYNTHETIC_TEST_ONLY\n"
                )
                (directory / (role + ".log")).write_text(log)
                children.append(child)

            def discover(child):
                pass

            def running(child):
                return child.role == "server"

            def cleanup(child, *args):
                child.cleaned += 1
                return {
                    "errors": [],
                    "remaining": [],
                    "waited_returncode": 0,
                    "owners": [],
                }

        gpu = {"gpus": [], "applications": {"stdout": ""}}
        return cfg, case, arrays, Child, children, gpu

    def run_synthetic_case(self, references):
        from contextlib import ExitStack

        cfg, case, arrays, child, children, gpu = self.case_fixture()
        with ExitStack() as stack:
            for name, value in (
                ("fresh_guard", {"gpu": gpu}),
                ("runtime_snapshot", {}),
                ("gpu_snapshot", gpu),
                ("require_gpu", None),
                ("server_info", ({}, [])),
                ("cache_snapshot", None),
            ):
                stack.enter_context(mock.patch.object(e, name, return_value=value))
            stack.enter_context(mock.patch.object(e, "OwnedProcess", child))
            stack.enter_context(mock.patch.object(e.socket, "socket"))
            response = mock.MagicMock()
            response.__enter__.return_value.status = 200
            stack.enter_context(
                mock.patch.object(e, "http_open", return_value=response)
            )
            error = None
            try:
                e.run_case(
                    case,
                    cfg,
                    {"environment_passthrough": {}},
                    {"gpus": []},
                    references,
                    {},
                )
            except ValueError as exc:
                error = exc
        return case, arrays, children, error

    def test_case_real_result_validator_and_clean_seal(self):
        case, arrays, children, error = self.run_synthetic_case({})
        self.assertIsNone(error)
        directory = Path(case["case_dir"])
        self.assertEqual(plan.read_json(directory / "exit.json")["status"], "completed")
        self.assertEqual([c.cleaned for c in children], [1, 1, 1])
        self.assertEqual(plan.read_json(directory / "requested-lengths.json"), arrays)
        self.assertIn(
            "metrics.json",
            [
                Path(d["path"]).name
                for d in plan.read_json(directory / "manifest.json")["files"]
            ],
        )

    def test_cross_arm_mismatch_preserves_failed_case_and_cleanup(self):
        case, _, children, error = self.run_synthetic_case(
            {4: {"input_lens": [1], "output_lens": [1]}}
        )
        self.assertIsNotNone(error)
        directory = Path(case["case_dir"])
        terminal = plan.read_json(directory / "exit.json")
        self.assertEqual(terminal["status"], "failed")
        self.assertIn("Cross-arm", terminal["error"])
        self.assertEqual([c.cleaned for c in children], [1, 1, 1])
        self.assertTrue((directory / "result.json").is_file())
        self.assertTrue((directory / "manifest.json").is_file())

    @unittest.skipUnless(
        sys.platform == "linux",
        "Real Linux /proc ownership integration; macOS is not a substitute",
    )
    def test_real_owned_child_cleanup(self):
        x = e.OwnedProcess(
            [sys.executable, "-c", "import time;time.sleep(60)"],
            dict(os.environ),
            self.root,
            "child",
            self.root,
        )
        result = x.cleanup(2, 2)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["remaining"], [])
        self.assertEqual(result["waited_returncode"], -signal.SIGTERM)

    def test_optimized_main_refuses(self):
        p = subprocess.run(
            [sys.executable, "-O", str(plan.ROOT / "setup/execution.py")],
            capture_output=True,
        )
        self.assertNotEqual(p.returncode, 0)
        self.assertIn(b"Optimized execution", p.stderr)


if __name__ == "__main__":
    unittest.main()
