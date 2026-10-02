"""Real streaming-parser and measured-only aggregation behavior; no serving model."""

import asyncio
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import AsyncMock, patch

from infx.bench_serving import backend_request_func as backend
from infx.bench_serving import benchmark_serving as client
from infx.bench_serving.speculative_metrics import summarize_speculative_metrics


def details(tokens=10, verify=5, correct=5):
    return {
        "spec_accept_length": tokens / verify if verify else 0,
        "spec_accept_rate": correct / (3 * verify) if verify else 0,
        "spec_verify_ct": verify,
        "spec_num_correct_drafts": correct,
        "spec_num_proposed_drafts": 3 * verify,
    }


def frames(tokens=10, verify=5, correct=5):
    return [
        {"choices": [{"text": "a"}]},
        {"choices": [{"text": "b"}]},
        {
            "choices": [],
            "sglext": {"spec_tokens_details": details(tokens, verify, correct)},
        },
        {"choices": [], "usage": {"completion_tokens": tokens}},
        "[DONE]",
    ]


class Response:
    status = 200

    def __init__(self, messages):
        self.messages = messages
        self.content = self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def __aiter__(self):
        for message in self.messages:
            text = message if isinstance(message, str) else json.dumps(message)
            yield ("data: " + text + "\n\n").encode()


class Session:
    def __init__(self, responses, payloads):
        self.responses, self.payloads = responses, payloads

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    def post(self, url, *, json, headers):
        self.payloads.append(json)
        return Response(self.responses.pop(0))


def record(index, tokens=10, verify=5, correct=5):
    return {
        "request_index": index,
        "success": True,
        "completion_tokens": tokens,
        "spec_tokens_details": details(tokens, verify, correct),
    }


class Tests(unittest.TestCase):
    def parse(self, messages, capture=True):
        payloads = []
        request = backend.RequestFuncInput(
            prompt="test",
            api_url="http://unused/v1/completions",
            prompt_len=2,
            output_len=10,
            model="fixture",
            capture_speculative_metrics=capture,
        )
        with patch.object(
            backend.aiohttp, "ClientSession", return_value=Session([messages], payloads)
        ):
            output = asyncio.run(backend.async_request_openai_completions(request))
        return output, payloads[0]

    def test_final_extension_separate_from_usage_and_latency(self):
        out, payload = self.parse(frames())
        self.assertTrue(out.success)
        self.assertTrue(payload["return_spec_tokens_details"])
        self.assertEqual(out.output_tokens, 10)
        self.assertEqual(out.spec_tokens_details["spec_verify_ct"], 5)
        self.assertEqual(out.generated_text, "ab")
        self.assertEqual(len(out.itl), 1)  # metadata chunks are not output-token events

    def test_usage_before_extension(self):
        chunks = frames()
        chunks[2], chunks[3] = chunks[3], chunks[2]
        out, _ = self.parse(chunks)
        self.assertTrue(out.success)
        self.assertEqual(out.spec_tokens_details, details())

    def test_default_request_and_result_unchanged(self):
        out, payload = self.parse(frames(), capture=False)
        self.assertTrue(out.success)
        self.assertNotIn("return_spec_tokens_details", payload)
        self.assertIsNone(out.spec_tokens_details)

    def test_duplicate_or_truncated_final_frames_rejected(self):
        for messages in (
            frames()[:-1],
            frames()[:-1] + [frames()[2], "[DONE]"],
            frames()[:-1] + [frames()[3], "[DONE]"],
        ):
            with self.subTest(messages=messages):
                out, _ = self.parse(messages)
                self.assertFalse(out.success)
                self.assertTrue(out.error)

    def test_weighted_counts_and_true_zero_acceptance_rate(self):
        result = summarize_speculative_metrics([record(0), record(1, 30, 10, 20)])
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["completion_tokens"], 40)
        self.assertEqual(result["spec_verify_ct"], 15)
        self.assertAlmostEqual(result["acceptance_length"], 8 / 3)
        self.assertNotEqual(result["acceptance_length"], 2.5)
        zero = summarize_speculative_metrics([record(0, 10, 10, 0)])
        self.assertEqual(zero["acceptance_rate"], 0)
        self.assertEqual(zero["acceptance_length"], 1)

    def test_unavailable_and_invalid_counts_never_become_zero_al(self):
        mutations = [
            lambda x: x.update(spec_tokens_details=None),
            lambda x: x.update(completion_tokens=0),
            lambda x: x.update(success=False),
            lambda x: x["spec_tokens_details"].update(spec_verify_ct=0),
            lambda x: x["spec_tokens_details"].update(spec_verify_ct=True),
            lambda x: x["spec_tokens_details"].update(spec_num_correct_drafts=99),
            lambda x: x["spec_tokens_details"].update(spec_accept_length=float("nan")),
            lambda x: x["spec_tokens_details"].update(spec_accept_length=3),
        ]
        for mutate in mutations:
            row = record(0)
            mutate(row)
            result = summarize_speculative_metrics([row])
            self.assertEqual(result["status"], "unavailable")
            self.assertIsNone(result["acceptance_length"])
            self.assertEqual(result["requests"], [row])
        self.assertIsNone(summarize_speculative_metrics([])["acceptance_length"])

    def measured_benchmark(self, capture):
        payloads = []
        responses = [frames(1000, 1000, 0), frames(), frames(30, 10, 20)]
        with patch.object(
            backend.aiohttp,
            "ClientSession",
            side_effect=lambda **_: Session(responses, payloads),
        ):
            result = asyncio.run(
                client.benchmark(
                    backend="vllm",
                    api_url="http://unused/v1/completions",
                    base_url="http://unused",
                    model_id="fixture",
                    model_name="fixture",
                    tokenizer=object(),
                    input_requests=[("one", 2, 10, None), ("two", 3, 30, None)],
                    logprobs=None,
                    best_of=1,
                    request_rate=float("inf"),
                    burstiness=1,
                    disable_tqdm=True,
                    num_warmups=1,
                    profile=False,
                    selected_percentile_metrics=["ttft"],
                    selected_percentiles=[99],
                    ignore_eos=True,
                    goodput_config_dict={},
                    max_concurrency=1,
                    lora_modules=None,
                    capture_speculative_metrics=capture,
                )
            )
        return result, payloads

    def test_actual_benchmark_excludes_warmup_and_keeps_order(self):
        result, payloads = self.measured_benchmark(True)
        metric = result["speculative_metrics"]
        self.assertEqual(len(payloads), 3)
        self.assertTrue(all(p["return_spec_tokens_details"] for p in payloads))
        self.assertEqual([r["completion_tokens"] for r in metric["requests"]], [10, 30])
        self.assertEqual(metric["requested"], 2)
        self.assertEqual(metric["covered"], 2)
        self.assertAlmostEqual(metric["acceptance_length"], 8 / 3)
        self.assertEqual(metric["completion_tokens"], result["total_output_tokens"])
        self.assertEqual(result["output_lens"], [10, 30])

    def test_actual_default_benchmark_omits_telemetry(self):
        result, payloads = self.measured_benchmark(False)
        self.assertNotIn("speculative_metrics", result)
        self.assertTrue(all("return_spec_tokens_details" not in p for p in payloads))
        self.assertEqual(result["total_output_tokens"], 40)
        self.assertEqual(result["output_lens"], [10, 30])

    def test_missing_final_details_preserves_usage_but_is_unavailable(self):
        out, _ = self.parse([*frames()[:2], *frames()[3:]])
        self.assertTrue(out.success)  # Serving succeeded, required telemetry did not.
        self.assertEqual(out.output_tokens, 10)
        result = summarize_speculative_metrics(
            [
                {
                    "request_index": 0,
                    "success": out.success,
                    "completion_tokens": out.output_tokens,
                    "spec_tokens_details": out.spec_tokens_details,
                },
                record(1),
            ]
        )
        self.assertEqual(result["covered"], 1)
        self.assertEqual(result["requested"], 2)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["acceptance_length"])

    def test_cli_saves_missing_coverage_before_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            args = Namespace(
                seed=0,
                backend="vllm",
                model="fixture",
                served_model_name=None,
                tokenizer=None,
                tokenizer_mode="auto",
                base_url="http://unused",
                endpoint="/v1/completions",
                trust_remote_code=False,
                dataset_name="random",
                random_prefix_len=0,
                random_input_len=1,
                random_output_len=1,
                num_prompts=1,
                random_range_ratio=1,
                use_chat_template=False,
                dsv4=False,
                random_num_workers=1,
                goodput=None,
                logprobs=None,
                best_of=1,
                request_rate=float("inf"),
                burstiness=1,
                disable_tqdm=True,
                num_warmups=0,
                profile=False,
                percentile_metrics="ttft",
                metric_percentiles="99",
                ignore_eos=False,
                max_concurrency=1,
                lora_modules=None,
                save_result=True,
                metadata=None,
                save_detailed=False,
                result_filename="result.json",
                result_dir=directory,
                capture_speculative_metrics=True,
            )
            row = record(0)
            row["spec_tokens_details"] = None
            stats = summarize_speculative_metrics([row])
            raw = {
                "completed": 1,
                "speculative_metrics": stats,
                **{
                    f"{kind}_{metric}_ms": 0
                    for kind in ("median", "mean", "std", "p99")
                    for metric in ("ttft", "tpot", "itl")
                },
            }
            with (
                patch.object(client, "_load_tokenizer", return_value=object()),
                patch.object(client, "sample_random_requests", return_value=[]),
                patch.object(client, "benchmark", AsyncMock(return_value=raw)),
                patch.object(client.gc, "freeze"),
            ):
                with self.assertRaisesRegex(
                    SystemExit, "incomplete measured speculative"
                ):
                    client.main(args)
            saved = json.loads((Path(directory) / "result.json").read_bytes())
            self.assertEqual(saved["speculative_metrics"], stats)
            self.assertIsNone(saved["speculative_metrics"]["acceptance_length"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
