#!/usr/bin/env python3
"""CPU-only synthetic rejection/metric fixtures; these are not Kimi measurements."""

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import results


PROJECT = Path(__file__).resolve().parents[1]


def put(root, relative, value):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2) + "\n" if not isinstance(value, str) else value
    )
    return descriptor(root, relative)


def descriptor(root, relative):
    raw = (root / relative).read_bytes()
    return {
        "path": relative,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def synthetic_checkpoint(root, campaign):
    """Synthetic contract fixture only; never accepted by production CLI."""
    cc = results.checkpoint_contract
    stages = {
        stage: put(root, f"checkpoint/{stage}.json", {"SYNTHETIC_TEST_ONLY": True})
        for stage in ("original", "bf16", "nvfp4")
    }
    metadata = {}
    for name in cc.METADATA:
        value = {"SYNTHETIC_TEST_ONLY": True}
        if name == "config.json":
            value["quantization_config"] = {
                "quant_method": "modelopt",
                "quant_algo": "NVFP4",
                "group_size": 16,
                "ignore": ["synthetic_nonexpert"],
            }
        metadata[name] = put(root, "checkpoint/metadata/" + name, value)
    checks = dict.fromkeys(cc.CHECKS, True)
    review = put(
        root,
        "checkpoint/independent.json",
        {
            "SYNTHETIC_TEST_ONLY": True,
            "status": "PASS_CUSTOM_ROUTED_NVFP4_REVIEW",
            "output_path": cc.MODEL_PATH,
            "checks": checks,
            "bindings": [*stages.values(), *metadata.values()],
        },
    )
    desc = put(
        root,
        "checkpoint/ACCEPTED.json",
        {
            "schema_version": 1,
            "status": "ACCEPTED_CUSTOM_ROUTED_NVFP4",
            "data_kind": "synthetic_test_only",
            **{
                key: campaign["checkpoint"][key]
                for key in (
                    "source_repo",
                    "source_revision",
                    "miles_commit",
                    "output_path",
                    "scope",
                )
            },
            "checks": checks,
            "stage_reviews": stages,
            "metadata": metadata,
            "independent_review": review,
        },
    )
    campaign["checkpoint"]["acceptance"].update(
        {key: desc[key] for key in ("bytes", "sha256")}
    )
    campaign["checkpoint"]["local_tensor_verification"] = True
    return desc


def fixture(root):
    campaign = json.loads((PROJECT / "campaign.json").read_text())
    checkpoint = synthetic_checkpoint(root, campaign)
    campaign_desc = put(root, "campaign.json", campaign)
    shutil.copytree(PROJECT / "vendor", root / "vendor")
    cases, records, ids = [], [], []
    for arm in results.ARMS:
        for c in (32, 4, 8, 16):
            cid = f"{arm}-tp8-ep8-dp8-c{c}"
            ids.append(cid)
            flags = {
                "--backend": "sglang-oai",
                "--model": "/synthetic/model",
                "--dataset-name": "random",
                "--num-warmups": str(2 * c),
                "--num-prompts": str(10 * c),
                "--max-concurrency": str(c),
                "--random-input-len": "1024",
                "--random-output-len": "8192",
                "--random-range-ratio": "0.8",
                "--seed": "0",
                "--request-rate": "inf",
                "--ignore-eos": True,
                "--use-chat-template": True,
                "--save-result": True,
                "--percentile-metrics": "ttft,tpot,itl,e2el",
                "--metric-percentiles": "90,99,99.9",
            }
            argv = ["python", "-m", "infx.bench_serving.benchmark_serving"]
            for key, value in flags.items():
                argv.append(key)
                if value is not True:
                    argv.append(value)
            case = {
                "case_id": cid,
                "arm_id": arm,
                "tp": 8,
                "ep": 8,
                "dp": 8,
                "concurrency": c,
                "warmup_requests": 2 * c,
                "measured_requests": 10 * c,
                "server_max_running_requests": max(c, 8),
                "decode_graph_max_bs": c,
                "server_argv": ["python", "-m", "sglang.launch_server"],
                "client_argv": argv,
                "environment": {},
            }
            cases.append(case)
            requested = {
                "input_lens": [900 + i % 10 for i in range(10 * c)],
                "output_lens": [7000 + i % 11 for i in range(10 * c)],
            }
            inp, out = sum(requested["input_lens"]), sum(requested["output_lens"])
            duration = 100.0 + c
            row = {
                "SYNTHETIC_TEST_ONLY": True,
                "date": "SYNTHETIC",
                "backend": "sglang-oai",
                "model_id": "/synthetic/model",
                "tokenizer_id": "/synthetic/model",
                "best_of": 1,
                "num_prompts": 10 * c,
                "request_rate": "inf",
                "burstiness": 1.0,
                "max_concurrency": c,
                "duration": duration,
                "benchmark_start_time_unix": 1000.0,
                "benchmark_end_time_unix": 1000.0 + duration + 0.00001,
                "completed": 10 * c,
                "total_input_tokens": inp,
                "total_output_tokens": out,
                "request_throughput": 10 * c / duration,
                "request_goodput:": None,
                "output_throughput": out / duration,
                "total_token_throughput": (inp + out) / duration,
                **requested,
                "benchmark_outcome": {
                    "status": "passed",
                    "requested": 10 * c,
                    "completed": 10 * c,
                    "failed": 0,
                    "max_failure_rate": 0.05,
                },
            }
            for kind in ("ttft", "tpot", "itl", "e2el"):
                for stat, value in zip(
                    ("mean", "median", "std", "p90", "p99", "p99.9"),
                    (12.0, 10.0, 2.0, 15.0, 20.0, 25.0),
                    strict=True,
                ):
                    row[f"{stat}_{kind}_ms"] = value
            base = f"cases/{cid}"
            files = [
                put(root, f"{base}/result.json", row),
                put(root, f"{base}/requested-lengths.json", requested),
                put(
                    root,
                    f"{base}/benchmark.log",
                    f"SYNTHETIC TEST ONLY\nWarming up with {2 * c} requests...\nWarmup completed.\n",
                ),
                put(root, f"{base}/native/receipt.json", {"SYNTHETIC_TEST_ONLY": True}),
            ]
            manifest = put(
                root, f"{base}/manifest.json", {"case_id": cid, "files": files}
            )
            review = put(
                root,
                f"reviews/{cid}.json",
                {
                    "SYNTHETIC_TEST_ONLY": True,
                    "status": "PASS_ACTUAL_CASE_REVIEW",
                    "case_id": cid,
                    "manifest_sha256": manifest["sha256"],
                    "warmup_requests": 2 * c,
                    "checks": dict.fromkeys(results.CASE_CHECKS, True),
                    "bindings": files,
                },
            )
            records.append({"case_id": cid, "manifest": manifest, "review": review})
    changes = campaign.get("local_changes", {})
    if changes:
        relative = changes["sglang"]["patch"]["path"]
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT / relative, root / relative)
        for relative in changes["sglang"]["files"]:
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / relative, root / relative)
    plan = put(
        root,
        "PLAN.json",
        {
            "campaign": campaign_desc,
            "cases": cases,
            "pins": campaign["pins"],
            "local_changes": changes,
        },
    )
    terminal = put(
        root,
        "terminal-summary.json",
        {
            "status": "completed",
            "waited_returncode": 0,
            "error": None,
            "cleanup_errors": [],
            "remaining_owners": [],
            "completed_case_ids": ids,
        },
    )
    review = put(
        root,
        "terminal-review.json",
        {
            "status": "PASS_ACTUAL_TERMINAL_REVIEW",
            "terminal_sha256": terminal["sha256"],
            "bindings": [terminal],
            "SYNTHETIC_TEST_ONLY": True,
        },
    )
    return put(
        root,
        "ACCEPTANCE.json",
        {
            "schema_version": 1,
            "status": "ACCEPTED_COMPLETE_CAMPAIGN",
            "data_kind": "synthetic_test_only",
            "campaign": campaign_desc,
            "checkpoint_acceptance": checkpoint,
            "plan": plan,
            "client_source": descriptor(root, "vendor/inferencex/SOURCE.json"),
            "terminal": terminal,
            "terminal_review": review,
            "cases": records,
        },
    )


class ResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = Path(
            tempfile.mkdtemp(
                prefix="results-synthetic-test-only-", dir=PROJECT / "artifacts"
            )
        )
        cls.raw = cls.folder / "synthetic-input"
        cls.raw.mkdir()
        fixture(cls.raw)
        cls.data = results.load(cls.raw, allow_synthetic=True)
        print(f"SYNTHETIC TEST ONLY; preserved CPU fixtures: {cls.folder}")

    def test_custom_checkpoint_pending_and_incomplete_review_rejected(self):
        campaign = copy.deepcopy(self.data["campaign"])
        campaign["checkpoint"]["local_tensor_verification"] = False
        accepted = results.read_json(self.raw / "ACCEPTANCE.json")
        with self.assertRaisesRegex(ValueError, "pending"):
            results.checkpoint_contract.verify_acceptance(
                campaign["checkpoint"],
                accepted["checkpoint_acceptance"],
                results.Evidence(self.raw),
                allow_synthetic=True,
            )
        with self.assertRaisesRegex(ValueError, "actual evidence only"):
            results.checkpoint_contract.verify_acceptance(
                self.data["campaign"]["checkpoint"],
                accepted["checkpoint_acceptance"],
                results.Evidence(self.raw),
            )
        root = self.folder / "bad-conversion"
        root.mkdir()
        campaign = copy.deepcopy(self.data["campaign"])
        desc = synthetic_checkpoint(root, campaign)
        doc = results.read_json(root / desc["path"])
        doc["checks"]["nvfp4_non_routed_tensor_bytes"] = False
        desc = put(root, desc["path"], doc)
        campaign["checkpoint"]["acceptance"].update(
            {key: desc[key] for key in ("bytes", "sha256")}
        )
        with self.assertRaisesRegex(ValueError, "Incomplete conversion checks"):
            results.checkpoint_contract.verify_acceptance(
                campaign["checkpoint"],
                desc,
                results.Evidence(root),
                allow_synthetic=True,
            )

    def test_complete_grid_and_full_saved_scalars(self):
        self.assertEqual(len(self.data["rows"]), 12)
        self.assertEqual(sum(r["measured_requests"] for r in self.data["rows"]), 1800)
        self.assertEqual(sum(r["warmup_requests"] for r in self.data["rows"]), 360)
        self.assertTrue(
            all(
                set(results.LATENCIES) <= r.keys()
                for r in self.data["raw_results"].values()
            )
        )

    def test_cli_data_gate_and_publish_gate_reject_synthetic(self):
        with self.assertRaisesRegex(ValueError, "actual evidence only"):
            results.load(self.raw)
        with self.assertRaisesRegex(ValueError, "Synthetic"):
            results.publish(self.data, self.folder / "must-not-exist")
        self.assertFalse((self.folder / "must-not-exist").exists())

    def test_decimal_axes_and_12_complete_pairs(self):
        data = self.data
        pairs = results.comparisons(data)
        self.assertEqual(len(pairs), 12)
        self.assertTrue(all(len(p["metrics"]) == 28 for p in pairs))
        self.assertTrue(
            all(
                v["candidate_over_baseline_minus_one_pct"] == "0"
                for p in pairs
                for v in p["metrics"].values()
            )
        )
        self.assertEqual(
            Decimal(
                data["rows"][0]["derived"]["interactivity_tokens_per_second_per_user"]
            ),
            Decimal(100),
        )

    def test_ordered_permutation_rejected_even_with_same_totals(self):
        case = self.data["plan"]["cases"][0]
        raw = copy.deepcopy(self.data["raw_results"][case["case_id"]])
        requested = self.data["requested_lengths"][case["case_id"]]
        raw["output_lens"][0], raw["output_lens"][1] = (
            raw["output_lens"][1],
            raw["output_lens"][0],
        )
        with self.assertRaisesRegex(ValueError, "Ordered"):
            results.verify_result(raw, requested, case)

    def test_nonzero_failure_rejected_even_client_passed(self):
        case = self.data["plan"]["cases"][0]
        raw = copy.deepcopy(self.data["raw_results"][case["case_id"]])
        raw["benchmark_outcome"]["failed"] = 1
        with self.assertRaisesRegex(ValueError, "zero failures"):
            results.verify_result(
                raw, self.data["requested_lengths"][case["case_id"]], case
            )

    def test_duration_and_saved_throughput_mismatch(self):
        case = self.data["plan"]["cases"][0]
        for key, value in (
            ("duration", 0),
            ("output_throughput", 1),
            ("median_tpot_ms", float("nan")),
        ):
            with self.subTest(key=key):
                raw = copy.deepcopy(self.data["raw_results"][case["case_id"]])
                raw[key] = value
                with self.assertRaises(ValueError):
                    results.verify_result(
                        raw, self.data["requested_lengths"][case["case_id"]], case
                    )

    def test_missing_point_and_wrong_client_flag(self):
        for mutation in (
            lambda p: p["cases"].pop(),
            lambda p: p["cases"][0]["client_argv"].append("--seed"),
        ):
            plan = copy.deepcopy(self.data["plan"])
            mutation(plan)
            with self.assertRaises(ValueError):
                results.validate_plan(self.data["campaign"], plan)

    def test_bound_byte_changes_traversal_and_symlink_rejected(self):
        e = results.Evidence(self.raw)
        desc = descriptor(self.raw, "terminal-summary.json")
        desc["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Changed bytes"):
            e.bound(desc)
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            results.safe_path(self.raw, "../outside")
        link = self.raw / "synthetic-link"
        link.symlink_to(self.raw / "terminal-summary.json")
        with self.assertRaisesRegex(ValueError, "Symlink"):
            results.safe_path(self.raw, "synthetic-link")

    def test_frontier_maximizes_both_axes_and_preserves_ties(self):
        def p(x, y):
            return {
                "derived": {
                    "interactivity_tokens_per_second_per_user": str(x),
                    "output_tokens_per_second_per_gpu": str(y),
                }
            }

        a, b, dominated, duplicate = p(1, 3), p(3, 1), p(1, 1), p(1, 3)
        found = results.frontier([a, b, dominated, duplicate])
        self.assertEqual(len(found), 3)
        self.assertNotIn(dominated, found)
        self.assertEqual(
            {x[1] for x in results.ARMS.values()}, {"#009E73", "#E69F00", "#0072B2"}
        )

    def test_duplicate_json_key_rejected(self):
        path = self.folder / "duplicate.json"
        path.write_text('{"x":1,"x":2}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            results.read_json(path)

    def test_local_patch_bytes_and_plan_coupling(self):
        root = self.folder / "synthetic-patch"
        root.mkdir()
        patch = put(root, "artifacts/test.patch", "SYNTHETIC TEST PATCH ONLY\n")
        source = put(root, "sglang/test.py", "# SYNTHETIC TEST SOURCE ONLY\n")
        campaign = copy.deepcopy(self.data["campaign"])
        campaign["pins"]["sglang_local_patch"] = patch["sha256"]
        campaign["local_changes"] = {
            "sglang": {
                "base_commit": campaign["pins"]["sglang"],
                "patch": patch,
                "files": {source["path"]: {k: source[k] for k in ("bytes", "sha256")}},
            }
        }
        results.verify_local_changes(results.Evidence(root), campaign)
        (root / source["path"]).write_text("changed\n")
        with self.assertRaisesRegex(ValueError, "Changed bytes"):
            results.verify_local_changes(results.Evidence(root), campaign)
        plan = copy.deepcopy(self.data["plan"])
        with self.assertRaisesRegex(ValueError, "source pins differ"):
            results.validate_plan(campaign, plan)

    def test_resealed_cross_arm_length_difference_rejected(self):
        root = self.folder / "cross-arm-mutation"
        root.mkdir()
        fixture(root)
        acceptance = results.read_json(root / "ACCEPTANCE.json")
        record = acceptance["cases"][4]
        manifest = results.read_json(root / record["manifest"]["path"])
        for desc in manifest["files"]:
            if Path(desc["path"]).name in ("result.json", "requested-lengths.json"):
                value = results.read_json(root / desc["path"])
                value["output_lens"][0], value["output_lens"][1] = (
                    value["output_lens"][1],
                    value["output_lens"][0],
                )
                put(root, desc["path"], value)
        manifest["files"] = [descriptor(root, d["path"]) for d in manifest["files"]]
        record["manifest"] = put(root, record["manifest"]["path"], manifest)
        review = results.read_json(root / record["review"]["path"])
        review["manifest_sha256"] = record["manifest"]["sha256"]
        review["bindings"] = manifest["files"]
        record["review"] = put(root, record["review"]["path"], review)
        put(root, "ACCEPTANCE.json", acceptance)
        with self.assertRaisesRegex(ValueError, "Cross-arm requested arrays differ"):
            results.load(root, allow_synthetic=True)

    def test_resealed_unclean_terminal_rejected(self):
        root = self.folder / "unclean-terminal"
        root.mkdir()
        fixture(root)
        acceptance = results.read_json(root / "ACCEPTANCE.json")
        terminal = results.read_json(root / acceptance["terminal"]["path"])
        terminal["remaining_owners"] = [{"pid": 42, "start_ticks": 123}]
        acceptance["terminal"] = put(root, acceptance["terminal"]["path"], terminal)
        review = results.read_json(root / acceptance["terminal_review"]["path"])
        review["terminal_sha256"] = acceptance["terminal"]["sha256"]
        review["bindings"] = [acceptance["terminal"]]
        acceptance["terminal_review"] = put(
            root, acceptance["terminal_review"]["path"], review
        )
        put(root, "ACCEPTANCE.json", acceptance)
        with self.assertRaisesRegex(ValueError, "actual clean waited exit"):
            results.load(root, allow_synthetic=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
