"""Temporary CPU-only composite fixtures; no actual acceptance or measurement."""

import copy
from pathlib import Path
import tempfile
import unittest

import continuation
import results
from test_results import descriptor, fixture, put


def composite_fixture(root):
    fixture(root)
    accepted = results.read_json(root / "ACCEPTANCE.json")
    campaign = results.read_json(root / "campaign.json")
    # Synthetic fixture supplies the fixed recipe path; public defaults are pending.
    campaign["runtime"]["run_root"] = (
        "/data/home/ziangli/inferencex-kimik3-three-curves-c32-20260929/"
        "kimi-k3-ep8-three-curves-c32-20260929-remaining11-r5"
    )
    planned = results.read_json(root / "PLAN.json")
    for case in planned["cases"]:
        case["case_dir"] = campaign["runtime"]["run_root"] + "/cases/" + case["case_id"]
        case["compile_cache_root"] = campaign["runtime"]["run_root"] + "/caches/compile"
        case["tactic_cache_root"] = campaign["runtime"]["run_root"] + "/caches/tactics"
        case["environment"] = {"PYTHONPATH": "/synthetic/r4/vendor/inferencex"}
        case["client_argv"] += ["--result-dir", case["case_dir"]]
    old_cfg = put(root, "prior/campaign.json", campaign)
    old_plan = put(root, "prior/PLAN.json", {**planned, "campaign": old_cfg})
    first = accepted["cases"][0]
    base = "cases/" + continuation.PRIOR_ID
    settings = put(
        root, base + "/settings.json", {"case": planned["cases"][0], "config": campaign}
    )
    # The entire envelope is synthetic_test_only and production CLI refuses it.
    # This one object omits its optional marker solely to exercise the strict parent gate.
    row = results.read_json(root / base / "result.json")
    row.pop("SYNTHETIC_TEST_ONLY")
    result = put(root, base + "/result.json", row)
    requested = descriptor(root, base + "/requested-lengths.json")
    manifest = results.read_json(root / first["manifest"]["path"])
    manifest["files"] = [
        result if d["path"] == result["path"] else d for d in manifest["files"]
    ] + [settings]
    first["manifest"] = put(root, first["manifest"]["path"], manifest)
    review = results.read_json(root / first["review"]["path"])
    review["manifest_sha256"] = first["manifest"]["sha256"]
    review["bindings"] = manifest["files"]
    first["review"] = put(root, first["review"]["path"], review)
    failed = put(
        root,
        "prior/failed.json",
        {
            "status": "failed",
            "exit_code": 1,
            "error": "SYNTHETIC EADDRINUSE fixture",
            "cleanup_errors": [],
            "remaining_owners": [],
            "completed_case_ids": [continuation.PRIOR_ID],
        },
    )
    failure_review = put(
        root,
        "prior/failure-review.json",
        {
            "status": "PASS_ACTUAL_FAILED_TERMINAL_REVIEW",
            "terminal_sha256": failed["sha256"],
            "SYNTHETIC_TEST_ONLY": True,
        },
    )
    proof = put(root, "prior/proof.json", {"SYNTHETIC_TEST_ONLY": True})
    prior = {
        "schema_version": 1,
        "status": "ACCEPTED_KIMI_PRIOR_C32_FOR_CONTINUATION",
        "data_kind": "actual",
        "case_id": continuation.PRIOR_ID,
        "accepted_case_only": True,
        "original_sweep_accepted": False,
        "case_review": first["review"],
        "independent_actual_review": proof,
        "root_case_review": proof,
        "original_source": proof,
        "cache_lineage": proof,
        "failed_terminal": failed,
        "failed_terminal_review": failure_review,
        "campaign": old_cfg,
        "plan": old_plan,
        "settings": settings,
        "manifest": first["manifest"],
        "result": result,
        "requested_lengths": requested,
        "SYNTHETIC_TEST_ONLY": True,
    }
    prior_desc = put(root, "prior/ACCEPTED.json", prior)
    remote_prior = {**prior_desc, "path": "/synthetic/prior/ACCEPTED.json"}
    seed = put(
        root,
        "prior/SEED.json",
        {
            "status": "ACCEPTED_KIMI_QUIESCENT_CACHE_SEED",
            "data_kind": "actual",
            "prior_case_acceptance": remote_prior,
            "SYNTHETIC_TEST_ONLY": True,
        },
    )
    remote_seed = {**seed, "path": "/synthetic/prior/SEED.json"}
    campaign["continuation"] = {
        "schema_version": 1,
        "prior_case_id": continuation.PRIOR_ID,
        "execution_case_ids": continuation.EXECUTION_IDS,
        "execution_totals": continuation.TOTALS,
        "prior_acceptance": remote_prior,
        "cache_seed_acceptance": remote_seed,
    }
    accepted["campaign"] = put(root, "campaign.json", campaign)
    planned.update(campaign=accepted["campaign"], continuation=campaign["continuation"])
    accepted["plan"] = put(root, "PLAN.json", planned)
    terminal = {
        "status": "completed",
        "exit_code": 0,
        "error": None,
        "cleanup_errors": [],
        "remaining_owners": [],
        "completed_case_ids": continuation.EXECUTION_IDS,
        "execution_case_ids": continuation.EXECUTION_IDS,
        "execution_totals": continuation.TOTALS,
        "prior_case_id": continuation.PRIOR_ID,
        "prior_acceptance": remote_prior,
        "cache_seed_acceptance": remote_seed,
    }
    accepted["terminal"] = put(root, "terminal-summary.json", terminal)
    accepted["terminal_review"] = put(
        root,
        "terminal-review.json",
        {
            "status": "PASS_ACTUAL_CONTINUATION_TERMINAL_REVIEW",
            "terminal_sha256": accepted["terminal"]["sha256"],
            "waited_returncode": 0,
            "completed_case_ids": continuation.EXECUTION_IDS,
            "bindings": [accepted["terminal"]],
        },
    )
    accepted["composite_review"] = put(
        root,
        "composite-review.json",
        {
            "status": "PASS_ACTUAL_COMPOSITE_CAMPAIGN_REVIEW",
            "terminal_sha256": accepted["terminal"]["sha256"],
            "bindings": [prior_desc, accepted["terminal"]],
        },
    )
    inventory = put(
        root,
        "cache-installation-inventory.json",
        {
            "roots": {
                "caches": campaign["runtime"]["run_root"] + "/caches",
                "hf-home": campaign["runtime"]["run_root"] + "/hf-home",
                "tmp": campaign["runtime"]["tmp_root"],
            },
            "files": {
                "tmp/.inferencex-owner.json": {"kind": "file", "bytes": 12},
                "caches/fixture.bin": {"kind": "file", "bytes": 8},
            },
            "SYNTHETIC_TEST_ONLY": True,
        },
    )
    remote_inventory = {
        **inventory,
        "path": campaign["runtime"]["run_root"] + "/cache-installation-inventory.json",
    }
    accepted["cache_seed_installation"] = put(
        root,
        "cache-installation.json",
        {
            "status": "ACCEPTED_SEED_INSTALLED_WITH_FRESH_TMP_OWNER",
            "acceptance_sha256": seed["sha256"],
            "seed_acceptance": remote_seed,
            "prior_case_acceptance": remote_prior,
            "installed_inventory": remote_inventory,
            "copied_files": 1,
            "copied_bytes": 8,
            "excluded": ["tmp/.inferencex-owner.json"],
            "compile_payloads_hashed": True,
            "tactic_payloads_hashed": True,
        },
    )
    accepted.update(
        status="ACCEPTED_COMPOSITE_CAMPAIGN",
        prior_acceptance=prior_desc,
        prior_binding_map={
            remote_prior["path"]: prior_desc,
            remote_seed["path"]: seed,
            remote_inventory["path"]: inventory,
        },
    )
    put(root, "ACCEPTANCE.json", accepted)
    return accepted


class CompositeTests(unittest.TestCase):
    def test_composite_twelve_rows_has_honest_eleven_segment(self):
        with tempfile.TemporaryDirectory(prefix="SYNTHETIC-composite-") as td:
            root = Path(td)
            composite_fixture(root)
            data = results.load(root, allow_synthetic=True)
            self.assertEqual(data["execution_segments"], 2)
            self.assertEqual(len(data["rows"]), 12)
            self.assertEqual(sum(x["measured_requests"] for x in data["rows"]), 1800)
            self.assertEqual(len(results.comparisons(data)), 12)
            with self.assertRaisesRegex(ValueError, "actual evidence only"):
                results.load(root)
            with self.assertRaisesRegex(ValueError, "Synthetic"):
                results.publish(data, root / "never-published")

    def test_prior_workload_arrays_and_alias_tampering_rejected(self):
        with tempfile.TemporaryDirectory(prefix="SYNTHETIC-parent-") as td:
            root = Path(td)
            accepted = composite_fixture(root)
            good = copy.deepcopy(accepted)
            accepted["prior_binding_map"]["/synthetic/prior/SEED.json"]["sha256"] = (
                "0" * 64
            )
            put(root, "ACCEPTANCE.json", accepted)
            with self.assertRaisesRegex(ValueError, "alias changes bytes"):
                results.load(root, allow_synthetic=True)
            put(root, "ACCEPTANCE.json", good)
            planned = results.read_json(root / "PLAN.json")
            campaign = results.read_json(root / "campaign.json")
            prior = results.read_json(root / "prior/ACCEPTED.json")
            documents = {
                d["path"]: results.read_json(root / d["path"])
                for d in prior.values()
                if isinstance(d, dict) and "path" in d
            }
            documents[campaign["continuation"]["prior_acceptance"]["path"]] = prior

            def reader(d):
                return documents[d["path"]]

            baseline = continuation.verify_prior(campaign, planned, reader)
            self.assertEqual(len(baseline["reference_arrays"]["input_lens"]), 320)
            changed = copy.deepcopy(campaign)
            changed["common_server_args"]["--stream-interval"] = 31
            with self.assertRaisesRegex(ValueError, "shared configuration"):
                continuation.verify_prior(changed, planned, reader)
            documents[prior["requested_lengths"]["path"]]["output_lens"][0] += 1
            with self.assertRaises(ValueError):
                continuation.verify_prior(campaign, planned, reader)

    def test_continuation_cannot_claim_single_successful_twelve(self):
        with tempfile.TemporaryDirectory(prefix="SYNTHETIC-terminal-") as td:
            root = Path(td)
            accepted = composite_fixture(root)
            accepted["status"] = "ACCEPTED_COMPLETE_CAMPAIGN"
            put(root, "ACCEPTANCE.json", accepted)
            with self.assertRaisesRegex(ValueError, "masquerade"):
                results.load(root, allow_synthetic=True)
            accepted["status"] = "ACCEPTED_COMPOSITE_CAMPAIGN"
            terminal = results.read_json(root / "terminal-summary.json")
            terminal["completed_case_ids"] = [
                continuation.PRIOR_ID,
                *continuation.EXECUTION_IDS,
            ]
            accepted["terminal"] = put(root, "terminal-summary.json", terminal)
            put(root, "ACCEPTANCE.json", accepted)
            with self.assertRaisesRegex(ValueError, "eleven-case"):
                results.load(root, allow_synthetic=True)


if __name__ == "__main__":
    unittest.main()
