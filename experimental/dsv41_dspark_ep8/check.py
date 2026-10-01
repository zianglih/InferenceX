"""Focused CPU behavior checks; no model, package installation, or serving request."""

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run as recipe
import preflight
from infx.bench_serving import encoding_dsv41 as encoder
from infx.bench_serving.speculative_metrics import summarize_speculative_metrics


class Checks(unittest.TestCase):
    def test_matrix_commands_and_isolation(self):
        cases = recipe.matrix()
        self.assertEqual(len(cases), 18)
        self.assertEqual(sum(c["measured_requests"] for c in cases), 3780)
        self.assertEqual(sum(c["warmup_requests"] for c in cases), 756)
        cfg = {
            "python": "/p/python",
            "model_path": "/model",
            "served_model": "fixture",
            "port": 30000,
            "run_root": "/new/run",
            "tmp_root": "/tmp/new",
            "sglang_root": "/source",
            "gpu_ids": list(map(str, range(8))),
            "base_environment": {"PATH": "/bin", "HOME": "/new/run/home"},
        }
        for case in cases:
            args = recipe.server_command(cfg, case)
            self.assertEqual(
                args[args.index("--speculative-dspark-block-size") + 1], "5"
            )
            self.assertEqual(
                args[args.index("--speculative-draft-model-path") + 1], "/model"
            )
            self.assertNotIn("--quantization", args)
            self.assertNotIn("--attention-backend", args)
            self.assertEqual(
                args[args.index("--speculative-moe-runner-backend") + 1],
                "flashinfer_mxfp4",
            )
            env = recipe.environment(cfg, case)
            self.assertEqual(env["SGLANG_RAGGED_VERIFY_MODE"], "static")
            self.assertEqual(
                env["SGLANG_CACHE_DIR"], f"/new/run/caches/tactics/{case['arm_id']}/tp8"
            )
            self.assertEqual(
                env.get("SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16"),
                "1" if case["precision"] == "w4a16" else None,
            )

    def test_preflight_uses_separate_bounded_tmp(self):
        cfg = {
            "run_root": "/run",
            "run_id": "run",
            "tmp_root": "/tmp/infx-dsv41-dspark-1001",
            "base_environment": {"HOME": "/run/home"},
        }
        actual = preflight.preflight_config(
            cfg, Path("/fresh/preflight"), Path("/tmp/infx-dsv41-pre-1001")
        )
        self.assertEqual(actual["tmp_root"], "/tmp/infx-dsv41-pre-1001")
        self.assertEqual(actual["base_environment"]["HOME"], "/fresh/preflight/home")
        self.assertEqual(cfg["base_environment"]["HOME"], "/run/home")
        with self.assertRaisesRegex(ValueError, "short"):
            preflight.preflight_config(
                cfg, Path("/fresh/preflight"), Path(cfg["tmp_root"] + "-pre")
            )
        with self.assertRaisesRegex(ValueError, "separate"):
            preflight.preflight_config(
                cfg, Path("/fresh/preflight"), Path(cfg["tmp_root"])
            )

    def test_pinned_encoder_chat_and_corrupt_source(self):
        body = b"""def encode_messages(messages, **kw):
    if kw != dict(thinking_mode="chat", reasoning_effort=None, return_multi_modal_data=True):
        raise ValueError("Wrong explicit prompt mode")
    return "<" + messages[0]["content"] + ">", {"images": []}
"""
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "encoding"
            path.mkdir()
            f = path / "encoding.py"
            f.write_bytes(body)
            with patch.object(
                encoder, "ENCODER_SHA256", hashlib.sha256(body).hexdigest()
            ):
                encoder._encoder.cache_clear()
                self.assertEqual(encoder.encode_text_chat(d, "hello"), "<hello>")
                f.write_bytes(body + b"# corruption")
                encoder._encoder.cache_clear()
                with self.assertRaisesRegex(ValueError, "reviewed source"):
                    encoder.encode_text_chat(d, "hello")
        encoder._encoder.cache_clear()

    def test_media_rejected(self):
        class ModelEncoder:
            def encode_messages(self, *args, **kwargs):
                return "prompt", {"images": ["unexpected"]}

        with patch.object(encoder, "_encoder", return_value=ModelEncoder()):
            with self.assertRaisesRegex(ValueError, "text-only"):
                encoder.encode_text_chat("/fixture", "hello")

    def test_dspark_counter_budget(self):
        details = {
            "spec_verify_ct": 2,
            "spec_num_correct_drafts": 8,
            "spec_num_proposed_drafts": 10,
            "spec_accept_length": 5.0,
            "spec_accept_rate": 0.8,
        }
        records = [
            {
                "request_index": 0,
                "success": True,
                "completion_tokens": 10,
                "spec_tokens_details": details,
            }
        ]
        raw = {
            "output_lens": [10],
            "speculative_metrics": summarize_speculative_metrics(records),
        }
        actual = recipe.validate_speculative_metrics(raw, 1)
        self.assertEqual(actual["acceptance_length"], 5.0)
        details["spec_num_proposed_drafts"] = 12
        details["spec_accept_rate"] = 8 / 12
        raw["speculative_metrics"] = summarize_speculative_metrics(records)
        with self.assertRaisesRegex(ValueError, "gamma5"):
            recipe.validate_speculative_metrics(raw, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
