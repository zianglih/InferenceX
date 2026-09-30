#!/usr/bin/env python3
"""CPU-only behavioral checks for review-plan semantics; no ML imports or launch."""

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

import plan
import run_campaign


class ReviewPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = plan.read_json(plan.ROOT / "campaign.json")
        cls.p = plan.build_plan()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(
            prefix="plan-test-", dir=plan.ROOT / "artifacts"
        )
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def cfg_path(self, cfg):
        p = self.base / "campaign.json"
        p.write_text(json.dumps(cfg))
        return p

    def test_matrix_counts_and_order(self):
        cases = self.p["cases"]
        self.assertEqual(len(cases), 12)
        self.assertEqual(len({x["case_id"] for x in cases}), 12)
        self.assertEqual(sum(x["warmup_requests"] for x in cases), 360)
        self.assertEqual(sum(x["measured_requests"] for x in cases), 1800)
        self.assertEqual(
            [(x["arm_id"], x["concurrency"]) for x in cases],
            [(a, c) for a in plan.ARM_CONTRACT for c in [32, 4, 8, 16]],
        )

    def test_c4_floor_and_graphmax(self):
        for c in self.p["cases"]:
            self.assertEqual(c["server_max_running_requests"], c["concurrency"])
            self.assertEqual(c["decode_graph_max_bs"], max(c["concurrency"], 8))
            self.assertEqual(c["effective_per_dp_request_capacity"], c["concurrency"])
            self.assertEqual(c["tp"], c["ep"])
            self.assertEqual(c["ep"], 8)
            self.assertEqual(c["dp"], 1)

    def test_exact_client_workload_flags(self):
        for c in self.p["cases"]:
            argv = c["client_argv"]
            for flag, val in {
                "--num-warmups": 2 * c["concurrency"],
                "--num-prompts": 10 * c["concurrency"],
                "--max-concurrency": c["concurrency"],
                "--seed": 0,
                "--random-input-len": 1024,
                "--random-output-len": 8192,
                "--random-range-ratio": 0.8,
                "--random-prefix-len": 0,
                "--request-rate": "inf",
                "--dataset-name": "random",
                "--result-filename": "result.json",
            }.items():
                self.assertEqual(argv[argv.index(flag) + 1], str(val))
            self.assertIn("--ignore-eos", argv)
            self.assertIn("--use-chat-template", argv)
            self.assertIn("--trust-remote-code", argv)
            self.assertEqual(
                argv[:4],
                [
                    self.cfg["runtime"]["python"],
                    "-B",
                    "-m",
                    "infx.bench_serving.benchmark_serving",
                ],
            )

    def test_arm_differences_only(self):
        for concurrency in [4, 8, 16, 32]:
            cases = [c for c in self.p["cases"] if c["concurrency"] == concurrency]

            def normalized(c):
                a = c["server_argv"][:]
                for key in ["--moe-runner-backend", "--moe-a2a-backend"]:
                    a[a.index(key) + 1] = "ARM_VALUE"
                e = {
                    k: v
                    for k, v in c["environment"].items()
                    if k
                    not in ["SGLANG_CACHE_DIR", "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16"]
                }
                b = c["client_argv"][:]
                b[b.index("--result-dir") + 1] = "CASE_PATH"
                return a, e, b

            self.assertEqual(normalized(cases[0]), normalized(cases[1]))
            self.assertEqual(normalized(cases[0]), normalized(cases[2]))
            self.assertEqual(cases[0]["server_argv"], cases[1]["server_argv"])
            self.assertNotIn(
                "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16", cases[0]["environment"]
            )
            self.assertEqual(
                cases[1]["environment"]["SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16"], "1"
            )
            self.assertNotIn(
                "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16", cases[2]["environment"]
            )

    def test_shared_compile_separate_tactics(self):
        self.assertEqual(len({c["compile_cache_root"] for c in self.p["cases"]}), 1)
        self.assertEqual(len({c["tactic_cache_root"] for c in self.p["cases"]}), 3)
        for arm in plan.ARM_CONTRACT:
            self.assertEqual(
                len(
                    {
                        c["tactic_cache_root"]
                        for c in self.p["cases"]
                        if c["arm_id"] == arm
                    }
                ),
                1,
            )

    def test_no_mtp_and_shared_checkpoint_format(self):
        for c in self.p["cases"]:
            self.assertFalse(
                any(x.startswith("--speculative") for x in c["server_argv"])
            )
            self.assertEqual(c["server_argv"].count("--quantization"), 1)
            self.assertEqual(
                c["server_argv"][c["server_argv"].index("--quantization") + 1],
                "modelopt_fp4",
            )
            self.assertIsNone(c["expected_server_info"]["speculative_algorithm"])
            self.assertEqual(c["expected_server_info"]["quantization"], "modelopt_fp4")

    def test_host_environment_never_inherited(self):
        with mock.patch.dict(
            os.environ,
            {
                "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16": "1",
                "FLASHINFER_FAKE_TUNING": "secret",
                "LD_PRELOAD": "bad.so",
                "CUDA_VISIBLE_DEVICES": "999",
                "PATH": "/bad",
            },
            clear=True,
        ):
            q = plan.build_plan()
        self.assertEqual(
            [c["environment"] for c in q["cases"]],
            [c["environment"] for c in self.p["cases"]],
        )

    def test_forbidden_environment_override_rejected(self):
        q = copy.deepcopy(self.cfg)
        q["arms"][0]["environment"]["FLASHINFER_MOE_TUNING_CONFIG"] = "bad"
        with self.assertRaisesRegex(ValueError, "Undocumented arm"):
            plan.validate_campaign(q)

    def test_forbidden_common_quant_or_mtp_rejected(self):
        for key, value in [
            ("--quantization", "fp8"),
            ("--speculative-algorithm", "EAGLE"),
            ("--disable-flashinfer-autotune", True),
            ("--log-level", "info"),
        ]:
            q = copy.deepcopy(self.cfg)
            q["common_server_args"][key] = value
            with self.assertRaisesRegex(ValueError, "Undocumented common"):
                plan.validate_campaign(q)

    def test_changed_workload_or_pin_rejected(self):
        q = copy.deepcopy(self.cfg)
        q["workload"]["speculation"] = "EAGLE"
        with self.assertRaisesRegex(ValueError, "Workload"):
            plan.validate_campaign(q)
        q = copy.deepcopy(self.cfg)
        q["pins"]["flashinfer"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "Unreviewed pin"):
            plan.validate_campaign(q)

    def test_custom_output_path_and_pending_binding(self):
        self.assertEqual(
            self.cfg["runtime"]["model_path"], plan.checkpoint_contract.MODEL_PATH
        )
        pending = copy.deepcopy(self.cfg)
        pending["checkpoint"]["local_tensor_verification"] = False
        pending["checkpoint"]["acceptance"].update(bytes=None, sha256=None)
        plan.validate_campaign(pending)
        self.assertFalse(self.p["executable"])
        q = copy.deepcopy(pending)
        q["checkpoint"]["source_revision"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "checkpoint contract"):
            plan.validate_campaign(q)
        q = copy.deepcopy(pending)
        q["checkpoint"]["local_tensor_verification"] = True
        with self.assertRaisesRegex(ValueError, "exact acceptance binding"):
            plan.validate_campaign(q)

    def test_interrupted_first_output_is_rejected(self):
        self.assertTrue(
            plan.checkpoint_contract.MODEL_PATH.endswith("/main-routed-nvfp4-attempt2")
        )
        q = copy.deepcopy(self.cfg)
        old_path = (
            plan.checkpoint_contract.REMOTE_ROOT + "/checkpoints/main-routed-nvfp4"
        )
        q["checkpoint"]["output_path"] = old_path
        q["runtime"]["model_path"] = old_path
        with self.assertRaisesRegex(ValueError, "checkpoint contract"):
            plan.validate_campaign(q)

    def test_tokenizer_metadata_bound_without_instantiation(self):
        t = self.p["tokenizer_source"]
        self.assertEqual(
            t["auto_map"]["AutoTokenizer"],
            ["tokenization_kimi.TikTokenTokenizer", None],
        )
        self.assertTrue(t["client_trust_remote_code_required"])
        self.assertFalse(t["code_executed"])
        self.assertFalse(t["tokenizer_instantiated"])
        for p, d in t["bindings"].items():
            self.assertEqual(plan.descriptor(p), d)

    def test_vendor_closure_bytes(self):
        v = self.p["client_source"]
        self.assertEqual(set(v["files"]), plan.VENDOR_FILES)
        for path, d in v["bindings"].items():
            self.assertEqual(plan.descriptor(path), d)
        self.assertIn("infx/bench_serving/server_watch.py", v["files"])

    def test_vendor_corruption_rejected(self):
        shutil.copytree(plan.ROOT / "vendor", self.base / "vendor")
        p = self.base / "vendor/inferencex/infx/bench_serving/backend_request_func.py"
        p.write_bytes(p.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Vendor source changed"):
            plan.verify_client(self.base, plan.PINS["client_inferencex"])

    def test_vendor_extra_module_rejected(self):
        shutil.copytree(plan.ROOT / "vendor", self.base / "vendor")
        (self.base / "vendor/inferencex/infx/bench_serving/extra.py").write_text("")
        with self.assertRaisesRegex(ValueError, "Unexpected or missing"):
            plan.verify_client(self.base, plan.PINS["client_inferencex"])

    def test_no_home_reassignment(self):
        for c in self.p["cases"]:
            self.assertNotIn("HOME", c["environment"])

    def test_local_patch_separate_binding_and_corruption(self):
        q = copy.deepcopy(self.cfg)
        shutil.copytree(plan.ROOT / "sglang", self.base / "sglang")
        (self.base / "artifacts").mkdir()
        shutil.copy2(
            plan.ROOT / "artifacts/sglang-dp1.patch",
            self.base / "artifacts/sglang-dp1.patch",
        )
        changes, bindings = plan.verify_local_changes(q, self.base)
        self.assertEqual(len(bindings), 4)
        relative = next(iter(changes["sglang"]["files"]))
        (self.base / relative).write_text("changed after acceptance")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            plan.verify_local_changes(q, self.base)

    def test_local_patch_pin_requires_descriptor(self):
        q = copy.deepcopy(self.cfg)
        q["pins"]["sglang_local_patch"] = "a" * 64
        q.pop("local_changes", None)
        with self.assertRaisesRegex(ValueError, "Exact reviewed source patch"):
            plan.verify_local_changes(q, self.base)

    def test_unknown_key_and_bool_capacity_rejected(self):
        q = copy.deepcopy(self.cfg)
        q["extra_environment"] = {"LD_PRELOAD": "bad"}
        with self.assertRaisesRegex(ValueError, "Unexpected campaign keys"):
            plan.validate_campaign(q)
        q = copy.deepcopy(self.cfg)
        q["common_server_args"]["--pp-size"] = True
        with self.assertRaisesRegex(ValueError, "Undocumented common"):
            plan.validate_campaign(q)

    def test_json_duplicate_and_nan_rejected(self):
        p = self.base / "bad.json"
        for text in ['{"a":1,"a":2}', '{"a":NaN}']:
            p.write_text(text)
            with self.assertRaises(ValueError):
                plan.read_json(p)

    def test_default_dry_run_no_subprocess_network_or_ml(self):
        with (
            mock.patch("subprocess.Popen", side_effect=AssertionError("spawn")),
            mock.patch("socket.socket", side_effect=AssertionError("network")),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            self.assertEqual(run_campaign.main([]), 0)
        value = json.loads(out.getvalue())
        self.assertFalse(value["executable"])
        self.assertEqual(value["status"], "REVIEW_ONLY_NOT_EXECUTABLE")
        for name in ["torch", "flashinfer", "transformers"]:
            self.assertNotIn(name, sys.modules)

    def test_execute_blocked_does_not_create_output(self):
        with (
            mock.patch("subprocess.Popen", side_effect=AssertionError("spawn")),
            contextlib.redirect_stderr(io.StringIO()) as err,
        ):
            self.assertEqual(run_campaign.main(["--execute"]), 2)
        value = json.loads(err.getvalue())
        self.assertTrue(value["execution_implemented"])
        self.assertTrue(any("approval marker" in x for x in value["reasons"]))
        self.assertTrue(any("REVIEW_REQUIRED" in x for x in value["reasons"]))

    def test_forged_marker_and_ready_status_still_blocked(self):
        q = copy.deepcopy(self.cfg)
        q["authorization"] = "EXECUTE_AUTHORIZED"
        q["status"] = "READY_FOR_EXECUTION"
        q["blockers"] = []
        for name, value in q["runtime"].items():
            if isinstance(value, str) and value.startswith("/REVIEW_REQUIRED/"):
                q["runtime"][name] = str(self.base / name)
        p = self.cfg_path(q)
        marker = self.base / "forged.json"
        marker.write_text('{"approved":true}')
        with (
            mock.patch("subprocess.Popen", side_effect=AssertionError("spawn")),
            contextlib.redirect_stderr(io.StringIO()) as err,
        ):
            rc = run_campaign.main(
                [
                    "--execute",
                    "--campaign",
                    str(p),
                    "--approval-marker",
                    str(marker),
                    "--approval-sha256",
                    plan.descriptor(marker)["sha256"],
                    "--runtime-project-root",
                    str(plan.ROOT),
                ]
            )
        self.assertEqual(rc, 1)
        self.assertEqual(
            json.loads(err.getvalue())["status"], "EXECUTION_REJECTED_OR_FAILED"
        )

    def test_exclusive_emission_and_nonexecutable_commands(self):
        out = self.base / "render"
        receipt = plan.emit_plan(self.p, out)
        self.assertEqual(receipt["status"], "LOCAL_DRY_RUN_EMITTED_NO_EXECUTION")
        self.assertEqual(len(list((out / "commands").glob("*.txt"))), 12)
        for p in out.rglob("*"):
            if p.is_file():
                self.assertEqual(p.stat().st_mode & 0o777, 0o600)
        for name, d in receipt["files"].items():
            self.assertEqual(plan.descriptor(out / name), d)
        with self.assertRaises(FileExistsError):
            plan.emit_plan(self.p, out)

    def test_symlink_output_rejected(self):
        actual = self.base / "real"
        actual.mkdir()
        link = self.base / "link"
        link.symlink_to(actual, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "Linked output"):
            plan.emit_plan(self.p, link / "child")
        self.assertFalse((actual / "child").exists())

    def test_runtime_paths_canonical_and_timeouts(self):
        for path in ["relative", "/a/../b", "/tmp/a\n", "/"]:
            with self.assertRaises(ValueError):
                plan.canonical_path(path)
        q = copy.deepcopy(self.cfg)
        q["runtime"]["term_seconds"] = False
        with self.assertRaisesRegex(ValueError, "Invalid guard timeout"):
            plan.validate_campaign(q)

    def test_plan_contains_no_measurements(self):
        self.assertNotIn("results", self.p)
        for c in self.p["cases"]:
            self.assertFalse(c["runtime_expectations_validated"])
            self.assertEqual(
                c["evidence_contract"]["status"], "DESIGN_ONLY_NO_EVIDENCE_PRODUCED"
            )
            self.assertNotIn("duration", c)
            self.assertNotIn("output_throughput", c)


if __name__ == "__main__":
    unittest.main()
