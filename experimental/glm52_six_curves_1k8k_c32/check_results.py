#!/usr/bin/env python3
"""Behavior checks with synthetic local receipts; no GPU or benchmark claims."""

import json
from pathlib import Path
import tempfile
import unittest

import check
import results
import run


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def campaign(root, cases):
    cfg = check.config()
    cfg.update(run_id=root.name, run_root=str(root))
    root.mkdir()
    (root / "cases").mkdir()
    save(root / "config.json", cfg)
    save(root / "matrix.json", run.matrix())
    save(
        root / "tmp-preflight.json",
        {
            "status": "AF_UNIX_PATH_PREFLIGHT_PASSED",
            "error": None,
            "run_id": cfg["run_id"],
            "run_root": str(root),
            "tmp_root": cfg["tmp_root"],
            "probes": [{"bound": True, "cleanup_errors": []} for _ in range(3)],
        },
    )
    save(root / "compile-cache-seed.json", {"status": "NO_SEED_FRESH_COMPILE_CACHE"})
    source = {
        name: {
            "root": cfg[name + "_root"],
            "head": {"returncode": 0, "stdout": cfg[name + "_commit"]},
            "diff": {"returncode": 0, "stdout": ""},
        }
        for name in ("sglang", "flashinfer")
    }
    source.update(
        freeze={"returncode": 0, "stdout": "synthetic-fixture==1\n"},
        recipe={
            "infx/bench_serving/benchmark_serving.py": {"bytes": 17, "sha256": "a" * 64}
        },
    )
    for case in cases:
        directory = root / "cases" / case["case_id"]
        directory.mkdir()
        c, tp, count = case["concurrency"], case["tp"], case["measured_requests"]
        save(
            directory / "settings.json",
            {
                "case": case,
                "config": cfg,
                "environment": run.environment(cfg, case),
                "nominal_input": 1024,
                "nominal_output": 8192,
                "ratio": 0.8,
            },
        )
        save(directory / "server_command.json", run.server_command(cfg, case))
        save(
            directory / "exit.json",
            {
                "case": case,
                "status": "completed",
                "error": None,
                "cleanup": {
                    "server": {"errors": [], "remaining": []},
                    "benchmark": {
                        "errors": [],
                        "remaining": [],
                        "waited_returncode": 0,
                    },
                },
            },
        )
        save(
            directory / "gpu.after.json",
            {"applications": {"returncode": 0, "stdout": ""}},
        )
        info = {
            "tp_size": tp,
            "ep_size": tp,
            "dp_size": tp,
            "enable_dp_attention": True,
            "moe_runner_backend": case["moe_runner_backend"],
            "moe_a2a_backend": case["moe_a2a_backend"],
            "speculative_moe_runner_backend": "flashinfer_trtllm",
            "speculative_moe_a2a_backend": "none",
            "speculative_algorithm": "EAGLE",
            "speculative_num_steps": 3,
            "speculative_eagle_topk": 1,
            "speculative_num_draft_tokens": 4,
            "kv_cache_dtype": "fp8_e4m3",
            "mem_fraction_static": 0.8,
            "dtype": "bfloat16",
            "quantization": "modelopt_fp4",
            "stream_interval": 30,
            "disable_flashinfer_autotune": False,
            "cuda_graph_backend_prefill": "disabled",
            "chunked_prefill_size": 8192 if tp == 4 else 4096,
            "max_running_requests": 8 if tp == 8 and c == 4 else c,
            "model_path": cfg["model_path"],
        }
        for when in ("before", "after"):
            save(directory / f"server_info.{when}.json", info)
            save(directory / f"source.{when}.json", source)
        (directory / "benchmark.log").write_text(
            f"Namespace(seed=0, fixture=True)\nWarming up with {2 * c} requests...\nWarmup completed.\n"
        )
        raw = {
            "completed": count,
            "num_prompts": count,
            "max_concurrency": c,
            "request_rate": "inf",
            "benchmark_outcome": {"status": "passed", "failed": 0},
            "input_lens": [1024] * count,
            "output_lens": [8192] * count,
            "total_input_tokens": 1024 * count,
            "total_output_tokens": 8192 * count,
            "duration": 10.0,
            "output_throughput": 819.2 * count,
            "median_tpot_ms": 5.0,
            "median_ttft_ms": 20.0,
            "mean_tpot_ms": 6.0,
            "timestamp": "SYNTHETIC-NOT-MEASURED",
        }
        save(directory / "result.json", raw)
        save(
            directory / "requested-lengths.json",
            {
                "scope": "deterministic request plan, not server output",
                "seed": 0,
                "nominal_input": 1024,
                "nominal_output": 8192,
                "ratio": 0.8,
                "num_prompts": count,
                "model_path": cfg["model_path"],
                "client_source": source["recipe"][
                    "infx/bench_serving/benchmark_serving.py"
                ],
                "input_lens": raw["input_lens"],
                "output_lens": raw["output_lens"],
            },
        )
        run.seal_case(directory)
    save(
        root / "worker-exit.json",
        {
            "status": "completed",
            "error": None,
            "completed": [c["case_id"] for c in cases],
        },
    )
    return cfg


def change(directory, name, edit, reseal=True):
    value = results.read(directory / name)
    edit(value)
    save(directory / name, value)
    if reseal:
        run.seal_case(directory)


class ReaderChecks(unittest.TestCase):
    def test_complete_six_arms_rates_saved_values_and_pairing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "trial"
            campaign(root, run.matrix())
            rows = results.load(root, False)
            self.assertEqual((len(rows), sum(r["completed"] for r in rows)), (24, 3600))
            r = next(r for r in rows if r["case_id"] == "trtllm-w4a4-tp8-ep8-dp8-c4")
            self.assertEqual(
                (r["output_tok_s_gpu"], r["interactivity_tok_s_user"]), (4096, 200)
            )
            saved, paired = results.saved_and_paired(rows, root)
            self.assertEqual(len(saved), 24)
            self.assertEqual(saved[0]["timestamp"], "SYNTHETIC-NOT-MEASURED")
            self.assertEqual(len({r["pair_id"] for r in paired}), 36)
            per_gpu = next(
                r
                for r in paired
                if r["kind"] == "topology" and r["metric"] == "output_tok_s_gpu"
            )
            self.assertEqual(per_gpu["percent_change"], "-50.0")
            groups = results.frontiers(rows)
            self.assertEqual(len(groups), 6)
            self.assertTrue(
                all(
                    len(g["case_ids"]) == 1 and g["case_ids"][0].endswith("c32")
                    for g in groups
                )
            )

    def test_partial_never_passes_as_complete_and_startup_failure_rejects(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "trial"
            campaign(root, run.matrix()[:1])
            self.assertEqual(len(results.load(root, True)), 1)
            with self.assertRaisesRegex(ValueError, "campaign incomplete"):
                results.load(root, False)
            change(
                root,
                "tmp-preflight.json",
                lambda d: d["probes"][0].update(bound=False),
                False,
            )
            with self.assertRaisesRegex(ValueError, "three actual AF_UNIX"):
                results.load(root, True)

    def test_changed_bytes_and_backend_precision_relabel_reject(self):
        mutations = [
            (
                "result.json",
                lambda d: d.update(duration=11),
                False,
                "Changed raw evidence",
            ),
            (
                "settings.json",
                lambda d: d["case"].update(precision="w4a16"),
                True,
                "identity",
            ),
            (
                "settings.json",
                lambda d: d["environment"].update(
                    TRTLLM_DISABLE_FP4_QUANT_FAST_MATH="0"
                ),
                True,
                "environment",
            ),
            (
                "server_command.json",
                lambda d: d.append("--disable-flashinfer-quant-fast-math"),
                True,
                "command",
            ),
            (
                "server_info.after.json",
                lambda d: d.update(moe_runner_backend="flashinfer_megamoe"),
                True,
                "Resolved settings",
            ),
            (
                "result.json",
                lambda d: d["benchmark_outcome"].update(failed=1),
                True,
                "outcome",
            ),
            (
                "exit.json",
                lambda d: d["cleanup"]["server"].update(remaining=[123]),
                True,
                "cleanup",
            ),
        ]
        for name, edit, seal, error in mutations:
            with (
                self.subTest(name=name, error=error),
                tempfile.TemporaryDirectory() as temp,
            ):
                root = Path(temp) / "trial"
                campaign(root, [run.matrix()[-1]])
                directory = next((root / "cases").iterdir())
                change(directory, name, edit, seal)
                with self.assertRaisesRegex(ValueError, error):
                    results.load(root, True)

    def test_same_concurrency_ordered_arrays_must_match(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "trial"
            cases = [c for c in run.matrix() if c["concurrency"] == 4][:2]
            campaign(root, cases)
            directory = root / "cases" / cases[-1]["case_id"]

            def raw_edit(raw):
                raw["input_lens"][:2] = [1023, 1025]

            change(directory, "result.json", raw_edit)
            change(directory, "requested-lengths.json", raw_edit)
            with self.assertRaisesRegex(ValueError, "Ordered request lengths differ"):
                results.load(root, True)

    def test_frontier_retains_tradeoffs_and_excludes_dominated_points(self):
        rows = [
            {"case_id": name, "interactivity_tok_s_user": x, "output_tok_s_gpu": y}
            for name, x, y in (("a", 4, 2), ("b", 2, 4), ("c", 1, 1), ("d", 3, 1))
        ]
        self.assertEqual([r["case_id"] for r in results.frontier(rows)], ["b", "a"])

    def test_malformed_json_and_symlink_evidence_reject(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "bad.json"
            for text in ('{"x":1,"x":2}', '{"x":NaN}'):
                p.write_text(text)
                with self.assertRaises(ValueError):
                    results.read(p)
            root = Path(temp) / "trial"
            campaign(root, run.matrix()[:1])
            directory = next((root / "cases").iterdir())
            linked = Path(temp) / "linked"
            linked.symlink_to(directory)
            with self.assertRaisesRegex(ValueError, "Linked case"):
                results.verify_case(linked)


if __name__ == "__main__":
    unittest.main(verbosity=2)
