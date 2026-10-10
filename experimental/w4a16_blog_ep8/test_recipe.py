"""CPU tests for request accounting, resolved settings, and runner isolation."""

import asyncio
import copy
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, TestCase, mock

import client
import run


def fixture_config():
    return {
        "run_id": "fixture",
        "python": "/opt/venv/bin/python",
        "run_root": "/data/test-run",
        "tmp_root": "/tmp/infx-blog",
        "sglang_root": "/data/sources/sglang",
        "flashinfer_root": "/data/sources/flashinfer",
        "installation_manifest": "/data/install/verified.json",
        "sglang_commit": "a" * 40,
        "flashinfer_commit": "b" * 40,
        "benchmark_commit": "c" * 40,
        "image": "fixture:dev@sha256:" + "d" * 64,
        "port": 30000,
        "ready_timeout_seconds": 60,
        "benchmark_timeout_seconds": 60,
        "models": {
            model: {
                "checkpoint_path": "/data/models/" + model,
                "checkpoint_revision": "e" * 40,
                "served_model": model,
                "prompt_format": client.PROMPT_FORMATS[model],
            }
            for model in run.MODELS
        },
    }


def final_event(completion=5, verify=2, correct=4):
    return {
        "usage": {"completion_tokens": completion, "prompt_tokens": 17},
        "sglext": {
            "spec_tokens_details": {
                "spec_verify_ct": verify,
                "spec_num_correct_drafts": correct,
                "spec_num_proposed_drafts": verify * 3,
                "spec_accept_length": completion / verify,
                "spec_accept_rate": correct / (verify * 3),
            }
        },
    }


class Response:
    status = 200

    def __init__(self, events):
        self.events = events
        self.content = self.lines()

    async def lines(self):
        for event in self.events:
            yield (
                b"data: "
                + (event if isinstance(event, bytes) else json.dumps(event).encode())
                + b"\n\n"
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


class Session:
    def __init__(self, events):
        self.events = events
        self.sent = None

    def post(self, url, json):
        self.sent = (url, json)
        return Response(self.events)


class StreamTests(IsolatedAsyncioTestCase):
    async def test_final_native_counters_and_chunk_timing(self):
        session = Session(
            [
                {"choices": [{"text": "x"}]},
                {"choices": [{"text": ""}]},
                final_event(),
                b"[DONE]",
            ]
        )
        request = {"prompt": "p", "input_tokens": 16, "output_tokens": 5}
        with mock.patch.object(client.time, "perf_counter", side_effect=[0, 1, 3]):
            result = await client.request_one(
                session, "/completions", request, "served", 3
            )
        self.assertEqual(
            (result["ttft_s"], result["tpot_s"], result["e2el_s"], result["itl_s"]),
            (1, 0.5, 3, [2]),
        )
        self.assertEqual(result["spec_verify_ct"], 2)
        self.assertEqual(result["server_input_tokens"], 17)
        self.assertEqual(session.sent[1]["prompt"], "p")
        self.assertTrue(session.sent[1]["return_spec_tokens_details"])
        self.assertTrue(session.sent[1]["ignore_eos"])

    async def test_missing_duplicate_and_inconsistent_final_data_fail(self):
        request = {"prompt": "p", "input_tokens": 16, "output_tokens": 5}
        bad = copy.deepcopy(final_event())
        bad["sglext"]["spec_tokens_details"]["spec_accept_length"] = 99
        for tail in (
            [final_event()],
            [final_event(), final_event(), b"[DONE]"],
            [bad, b"[DONE]"],
            [final_event(), b"[DONE]", final_event()],
        ):
            with self.subTest(tail=tail), self.assertRaises(ValueError):
                await client.request_one(
                    Session([{"choices": [{"text": "x"}]}] + tail),
                    "/completions",
                    request,
                    "s",
                    3,
                )

    async def test_warmups_are_excluded_and_concurrency_is_bounded(self):
        plan = {
            "model_id": "glm52",
            "concurrency": 2,
            "requests": [{"id": i} for i in range(20)],
        }
        active = maximum = 0
        seen = []

        async def request(*args):
            nonlocal active, maximum
            active += 1
            maximum = max(maximum, active)
            seen.append(args[2]["id"])
            await asyncio.sleep(0)
            active -= 1
            return {"id": args[2]["id"]}

        with mock.patch.object(client, "request_one", side_effect=request):
            outputs, duration, warmups = await client.execute(
                plan, "/completions", "s", 10
            )
        self.assertEqual(warmups, 4)
        self.assertEqual(seen[:4], [0] * 4)
        self.assertEqual([row["id"] for row in outputs], list(range(20)))
        self.assertEqual(maximum, 2)
        self.assertGreater(duration, 0)


class AccountingTests(TestCase):
    def test_native_ratios_and_weighted_aggregation(self):
        rows = []
        for completion, verify, correct in [(5, 2, 4), (7, 4, 3)] * 5:
            event = final_event(completion, verify, correct)
            counters = client.native_counters(
                event["usage"], event["sglext"]["spec_tokens_details"], 3
            )
            rows.append(
                {
                    **counters,
                    "input_tokens": 16,
                    "server_input_tokens": 17,
                    "ttft_s": 1,
                    "tpot_s": 0.1,
                    "e2el_s": 2,
                    "itl_s": [0.3],
                }
            )
        plan = {
            "model_id": "glm52",
            "concurrency": 1,
            "requests": [{}] * 10,
            "prompt_format": client.PROMPT_FORMATS["glm52"],
        }
        row = client.summarize(plan, rows, 10, 2)
        self.assertEqual(row["acceptance_length"], 2)
        self.assertEqual(row["acceptance_rate"], 35 / 90)
        self.assertEqual(row["output_tok_s_gpu"], 0.75)
        self.assertEqual(row["spec_covered"], 10)
        self.assertNotEqual(row["acceptance_length"], (2.5 + 1.75) / 2)
        four = client.summarize(plan, rows, 10, 2, gpu_count=4)
        self.assertEqual((four["tp"], four["ep"], four["dp"]), (4, 4, 4))
        self.assertEqual(four["output_tok_s_gpu"], 1.5)
        self.assertEqual(four["request_plan_sha256"], row["request_plan_sha256"])
        self.assertEqual(four["acceptance_length"], 2)
        with self.assertRaisesRegex(ValueError, "four or eight"):
            client.summarize(plan, rows, 10, 2, gpu_count=0)


class RunnerTests(TestCase):
    def test_commands_keep_model_specific_draft_and_low_concurrency_capacity(self):
        cfg = fixture_config()
        cases = run.matrix()
        self.assertEqual(
            [(c["arm_id"], c["concurrency"]) for c in cases[:3]],
            [(arm, 1) for arm in run.ARMS],
        )
        self.assertEqual({c["model_id"] for c in cases[:21]}, {"dsv41"})
        for selected, size in ((None, "8"), ([1, 3, 5, 7], "4")):
            if selected is not None:
                cfg["gpu_ids"] = selected
            for model, expected in (
                ("dsv41", "flashinfer_mxfp4"),
                ("glm52", "flashinfer_trtllm"),
            ):
                for c, capacity in ((1, size), (64, "64")):
                    args = run.server_command(
                        cfg,
                        {
                            "model_id": model,
                            "arm_id": "megamoe-w4a16",
                            "concurrency": c,
                        },
                    )
                    self.assertEqual(
                        args[args.index("--max-running-requests") + 1], capacity
                    )
                    for flag in (
                        "--attn-dp-size",
                        "--tensor-parallel-size",
                        "--expert-parallel-size",
                    ):
                        self.assertEqual(args[args.index(flag) + 1], size)
                    self.assertEqual(
                        args[args.index("--chunked-prefill-size") + 1], "32768"
                    )
                    self.assertEqual(
                        args[args.index("--speculative-moe-runner-backend") + 1],
                        expected,
                    )
                    self.assertEqual("--enable-dp-lm-head" in args, model == "dsv41")

    def test_model_selection_and_invalid_topology(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            cfg = fixture_config()
            path.write_text(json.dumps(cfg))
            legacy = run.read_config(path)
            self.assertEqual(legacy["gpu_ids"], [0, 1, 2, 3, 4, 5, 6, 7])
            self.assertEqual(legacy["model_ids"], ["dsv41", "glm52"])
            cfg.update(gpu_ids=[0, 1, 2, 3], model_ids=["dsv41"])
            del cfg["models"]["glm52"]
            path.write_text(json.dumps(cfg))
            output = io.StringIO()
            with (
                mock.patch("sys.argv", ["run.py", "--config", str(path), "--plan"]),
                mock.patch("sys.stdout", output),
                mock.patch.object(run.signal, "signal"),
            ):
                run.main()
            cases = json.loads(output.getvalue())
            self.assertEqual(len(cases), 21)
            self.assertEqual({case["model_id"] for case in cases}, {"dsv41"})
            self.assertEqual([case["concurrency"] for case in cases[:3]], [1, 1, 1])
            self.assertEqual(
                [case["concurrency"] for case in cases[3:9]], [2, 4, 8, 16, 32, 64]
            )
            for bad in (
                {"gpu_ids": [0, 1, 2, 2]},
                {"gpu_ids": [0, 1, 2]},
                {"gpu_ids": [0, 1, 2, 8]},
                {"gpu_ids": [False, 1, 2, 3]},
                {"model_ids": []},
                {"model_ids": ["dsv41", "dsv41"]},
                {"model_ids": ["unknown"]},
            ):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    path.write_text(json.dumps({**cfg, **bad}))
                    run.read_config(path)

    def test_four_gpu_effective_server_settings(self):
        cfg = fixture_config()
        cfg["gpu_ids"] = [0, 1, 2, 3]
        case = {"model_id": "dsv41", "arm_id": "megamoe-w4a4", "concurrency": 1}
        info = {
            "model_path": "/data/models/dsv41",
            "tp_size": 4,
            "ep_size": 4,
            "attn_dp_size": 4,
            "dp_size": 1,
            "dtype": "bfloat16",
            "mem_fraction_static": 0.8,
            "max_running_requests": 4,
            "chunked_prefill_size": 8192,
            "max_prefill_tokens": 32768,
            "disable_radix_cache": True,
            "stream_interval": 30,
            "moe_runner_backend": "flashinfer_megamoe",
            "moe_a2a_backend": "flashinfer_megamoe",
            "speculative_moe_a2a_backend": "none",
            "speculative_num_draft_tokens": 6,
            "speculative_algorithm": "DSPARK",
            "speculative_moe_runner_backend": "flashinfer_mxfp4",
            "enable_dp_lm_head": True,
            "speculative_dspark_block_size": 5,
            "json_model_override_args": '{"vision_n_layers":0}',
            "cuda_graph_config": {"prefill": {"backend": "disabled"}},
        }
        checked = run.validate_server_info(info, cfg, case)
        self.assertEqual(checked["attn_dp_size"], 4)
        self.assertEqual(checked["chunked_prefill_size"], 8192)
        with self.assertRaisesRegex(ValueError, "chunked_prefill_size"):
            run.validate_server_info({**info, "chunked_prefill_size": 4096}, cfg, case)

    def test_selected_gpu_inventory_and_whole_node_idle_guard(self):
        cfg = fixture_config()
        cfg["gpu_ids"] = [1, 3, 5, 7]
        inventory = "\n".join(f"{i}, GPU-{i}, B300, driver, 275040" for i in range(8))
        with mock.patch.object(
            run.subprocess, "check_output", side_effect=[inventory, ""]
        ):
            state = run.require_idle(cfg)
        self.assertEqual(
            [line.split(",")[0] for line in state["gpus"].splitlines()],
            ["1", "3", "5", "7"],
        )
        with (
            mock.patch.object(
                run.subprocess,
                "check_output",
                side_effect=[inventory, "123, GPU-0, 10"],
            ),
            self.assertRaisesRegex(RuntimeError, "running GPU applications"),
        ):
            run.require_idle(cfg)
        with (
            mock.patch.object(
                run.subprocess,
                "check_output",
                return_value="0, GPU-0, B300, driver, 275040",
            ),
            self.assertRaisesRegex(RuntimeError, "unavailable"),
        ):
            run.require_idle(cfg)

    def test_environment_excludes_inherited_tuning_and_source_shadowing(self):
        cfg = fixture_config()
        cfg["gpu_ids"] = [1, 3, 5, 7]
        with mock.patch.dict(
            os.environ,
            {
                "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16": "1",
                "FLASHINFER_CUBIN_DIR": "/bad",
                "PYTHONPATH": "/bad",
            },
        ):
            for arm in run.ARMS:
                env = run.environment(cfg, {"model_id": "dsv41", "arm_id": arm})
                self.assertEqual(
                    "SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16" in env,
                    arm == "megamoe-w4a16",
                )
                self.assertNotIn("FLASHINFER_CUBIN_DIR", env)
                self.assertNotIn(cfg["sglang_root"], env["PYTHONPATH"])
                self.assertEqual(env["SGLANG_RAGGED_VERIFY_MODE"], "static")
                self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "1,3,5,7")


if __name__ == "__main__":
    import unittest

    unittest.main()
