"""Behavioral checks for compact arithmetic, coverage, frontier selection and rendering."""

import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

import render
import results


def fixture(model_id="dsv41", gpu_count=8):
    campaign = {
        "schema_version": 1,
        "run_id": "synthetic-fixture-only",
        "sglang_commit": "1" * 40,
        "flashinfer_commit": "2" * 40,
        "benchmark_commit": "3" * 40,
        "image": "synthetic-image-for-tests",
        "models": {
            model_id: {
                "checkpoint_path": "/fixture/model",
                "checkpoint_revision": "fixture-revision",
                "prompt_format": "fixture",
            }
        },
        "matrix": {
            "tp": gpu_count,
            "ep": gpu_count,
            "dp": gpu_count,
            "concurrencies": [1, 2, 4, 8, 16, 32, 64],
            "arms": ["megamoe-w4a4", "megamoe-w4a16", "trtllm-w4a4"],
        },
        "workload": {
            "input_len": 1024,
            "output_len": 8192,
            "range_ratio": 0.8,
            "seed": 0,
            "warmup_multiplier": 2,
            "measured_multiplier": 10,
            "stream_interval": 30,
        },
    }
    rows = []
    for arm in ("megamoe-w4a4", "megamoe-w4a16", "trtllm-w4a4"):
        for c in (1, 2, 4, 8, 16, 32, 64):
            row = {
                "model_id": model_id,
                "arm_id": arm,
                "concurrency": c,
                "tp": gpu_count,
                "ep": gpu_count,
                "dp": gpu_count,
                "requested": 10 * c,
                "completed": 10 * c,
                "failed": 0,
                "warmup_requested": 2 * c,
                "warmup_completed": 2 * c,
                "warmup_failed": 0,
                "duration_s": 100,
                "input_tokens": 1000 * c,
                "server_input_tokens": 1010 * c,
                "output_tokens": 40000 * c,
                "spec_completion_tokens": 40000 * c,
                "spec_verify_ct": 10000 * c,
                "spec_correct_drafts": 30000 * c,
                "spec_proposed_drafts": (50000 if model_id == "dsv41" else 30000) * c,
                "spec_covered": 10 * c,
                "spec_requested": 10 * c,
                "acceptance_length": 4.0,
                "acceptance_rate": 0.6 if model_id == "dsv41" else 1.0,
                "prompt_format": "fixture",
                "request_plan_sha256": "a" * 64,
                "ordered_lengths_sha256": "b" * 64,
            }
            for metric in ("ttft", "tpot", "e2el", "itl"):
                for stat in ("mean", "median", "p90", "p99"):
                    row[f"{stat}_{metric}_ms"] = 2.0
            rows.append(row)
    return {
        "schema_version": 1,
        "model_id": model_id,
        "campaign": campaign,
        "rows": rows,
    }


class ResultsTest(unittest.TestCase):
    def test_derived_metrics_use_whole_interval_and_native_totals(self):
        for gpus, expected_per_gpu in ((4, 100.0), (8, 50.0)):
            with self.subTest(gpus=gpus):
                row = results.validate_case(fixture(gpu_count=gpus)["rows"][0], "dsv41")
                self.assertEqual(row["output_tok_s"], 400.0)
                self.assertEqual(row["output_tok_s_gpu"], expected_per_gpu)
                self.assertEqual(row["interactivity_tok_s_user"], 500.0)
                self.assertEqual(row["acceptance_length"], 4.0)
                self.assertEqual(row["acceptance_rate"], 0.6)

    def test_rejects_invalid_or_mismatched_topology(self):
        for changes in (
            {"tp": 4},
            {"dp": True},
            {"tp": 4.0, "ep": 4, "dp": 4},
            {"tp": 2, "ep": 2, "dp": 2},
        ):
            with self.subTest(changes=changes):
                table = fixture()
                table["campaign"]["matrix"].update(changes)
                with self.assertRaisesRegex(ValueError, "TP=EP=attention DP"):
                    results.validate_table(table)
                row = fixture()["rows"][0]
                row.update(changes)
                with self.assertRaisesRegex(ValueError, "TP=EP=attention DP"):
                    results.validate_case(row, "dsv41")
        table = fixture()
        table["rows"][0].update(tp=4, ep=4, dp=4)
        with self.assertRaisesRegex(ValueError, "topology differs from campaign"):
            results.validate_table(table)
        table = fixture(gpu_count=4)
        table["rows"][0]["output_tok_s_gpu"] = 50.0
        with self.assertRaisesRegex(ValueError, "Derived metric disagrees"):
            results.validate_table(table)

    def test_rejects_misleading_or_incomplete_measurements(self):
        corruptions = {
            "acceptance_length": 3.0,
            "output_tok_s_gpu": 400.0,
            "spec_covered": 9,
            "spec_completion_tokens": 39999,
            "spec_proposed_drafts": 40000,
            "spec_correct_drafts": 50001,
            "completed": 9,
            "warmup_failed": 1,
            "spec_verify_ct": True,
            "duration_s": 0,
            "median_tpot_ms": float("nan"),
            "server_input_tokens": -1,
            "ordered_lengths_sha256": "bad-digest",
        }
        for field, value in corruptions.items():
            with self.subTest(field=field):
                row = fixture()["rows"][0]
                row[field] = value
                with self.assertRaises(ValueError):
                    results.validate_case(row, "dsv41")

    def test_glm_uses_three_proposals_and_rejects_dspark_budget(self):
        row = results.validate_case(fixture("glm52")["rows"][0], "glm52")
        self.assertEqual(row["acceptance_rate"], 1.0)
        row["spec_proposed_drafts"] = 50000
        with self.assertRaisesRegex(ValueError, "proposal budget"):
            results.validate_case(row, "glm52")

    def test_rejects_duplicate_missing_or_unmatched_points(self):
        table = fixture()
        table["rows"][-1] = copy.deepcopy(table["rows"][0])
        with self.assertRaisesRegex(ValueError, "21 distinct"):
            results.validate_table(table)
        table = fixture()
        table["rows"].pop()
        with self.assertRaisesRegex(ValueError, "21 distinct"):
            results.validate_table(table)
        table = fixture()
        table["rows"][7]["request_plan_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "different ordered request plans"):
            results.validate_table(table)
        table = fixture()
        table["rows"][7]["ordered_lengths_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "different ordered token lengths"):
            results.validate_table(table)
        table = fixture()
        table["rows"][7]["server_input_tokens"] += 1
        with self.assertRaisesRegex(ValueError, "different server_input_tokens"):
            results.validate_table(table)

    def test_frontier_keeps_equal_points_and_tradeoffs(self):
        rows = [
            {"concurrency": 1, "interactivity_tok_s_user": 10, "output_tok_s_gpu": 100},
            {"concurrency": 2, "interactivity_tok_s_user": 11, "output_tok_s_gpu": 99},
            {"concurrency": 4, "interactivity_tok_s_user": 9, "output_tok_s_gpu": 90},
            {"concurrency": 8, "interactivity_tok_s_user": 10, "output_tok_s_gpu": 100},
        ]
        self.assertEqual(
            [row["concurrency"] for row in results.frontier(rows)], [1, 8, 2]
        )

    def test_comparisons_keep_regressions(self):
        rows = results.validate_table(fixture())
        for row in rows:
            if row["arm_id"] == "megamoe-w4a16":
                row.update(
                    output_tok_s_gpu=25.0 * row["concurrency"],
                    median_tpot_ms=4.0,
                    acceptance_length=3.0,
                )
        comparison = results.comparisons(rows)[0]
        self.assertEqual(comparison["throughput_change_pct"], -50.0)
        self.assertEqual(comparison["median_tpot_change_pct"], 100.0)
        self.assertEqual(comparison["acceptance_length_change"], -1.0)
        self.assertEqual(comparison["acceptance_length_change_pct"], -25.0)

    def test_collect_exports_exact_case_data_and_hashes(self):
        table = fixture(gpu_count=4)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results.write_json(root / "campaign.json", table["campaign"])
            for row in table["rows"]:
                case = (
                    root
                    / "dsv41"
                    / f"{row['arm_id']}-c{row['concurrency']}"
                    / "case.json"
                )
                case.parent.mkdir(parents=True)
                results.write_json(case, row)
            collected = results.collect(root, "dsv41")
            self.assertEqual(collected["rows"][0]["output_tok_s_gpu"], 100.0)
            self.assertEqual(len(collected["rows"][0]["case_sha256"]), 64)
            results.export(collected, root / "compact")
            reloaded = json.loads((root / "compact" / "metrics.json").read_text())
            self.assertEqual(reloaded["rows"][0]["spec_verify_ct"], 10000)
            self.assertEqual(reloaded["campaign"]["matrix"]["tp"], 4)
            self.assertEqual(reloaded["rows"][0]["output_tok_s_gpu"], 100.0)
            self.assertTrue(
                (root / "compact" / "RESULTS.md")
                .read_text()
                .startswith("# DeepSeek-V4.1 Flash: DSpark, EP4,")
            )
            with (root / "compact" / "comparisons.csv").open() as stream:
                comparisons = list(csv.DictReader(stream))
            self.assertEqual(len(comparisons), 21)
            self.assertEqual(comparisons[0]["throughput_change_pct"], "0.0")

    def test_render_preserves_all_points_and_avoids_label_overlap(self):
        for gpus, expected_per_gpu in ((4, 100.0), (8, 50.0)):
            with self.subTest(gpus=gpus), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "fixture-only"
                report = render.render(fixture(gpu_count=gpus), output)
                points = json.loads((output / "points.json").read_text())
                self.assertEqual(len(points), 21)
                self.assertEqual(points[0]["x"], 500.0)
                self.assertEqual(points[0]["y"], expected_per_gpu)
                self.assertEqual(points[0]["acceptance_length"], 4.0)
                self.assertEqual(report["text_overlap_count"], 0)
                self.assertEqual(len(report["labels"]), 21)
                self.assertTrue(
                    (output / "pareto.png").read_bytes().startswith(b"\x89PNG")
                )
                svg = (output / "pareto.svg").read_text()
                self.assertTrue(svg.startswith("<?xml"))
                self.assertIn(f"B300 EP{gpus} | Concurrency 1-64", svg)
                self.assertIn(f"TP = EP = attention DP = {gpus}", svg)
                self.assertIn(
                    f"B300 EP{gpus}", (output / "acceptance-length.svg").read_text()
                )
                self.assertTrue(
                    (output / "acceptance-length.png")
                    .read_bytes()
                    .startswith(b"\x89PNG")
                )


if __name__ == "__main__":
    unittest.main()
