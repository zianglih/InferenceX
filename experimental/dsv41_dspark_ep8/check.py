"""Focused CPU behavior checks; no model, package installation, or serving request."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import run as recipe
import preflight
from infx.bench_serving import encoding_dsv41 as encoder
from infx.bench_serving.speculative_metrics import summarize_speculative_metrics


class Checks(unittest.TestCase):
    def test_provider_patch_contract(self):
        self.assertIsNone(recipe.flashinfer_patch_spec({}))
        valid = {
            "flashinfer_wheel_commit": recipe.FLASHINFER_WHEEL_BASE,
            "flashinfer_python_patch": {
                "source_file": recipe.FLASHINFER_PATCH_SOURCE,
                "original_sha256": "a" * 64,
                "sha256": "b" * 64,
            },
        }
        self.assertEqual(recipe.flashinfer_patch_spec(valid)["sha256"], "b" * 64)
        for bad in (
            {"flashinfer_wheel_commit": recipe.FLASHINFER_WHEEL_BASE},
            dict(valid, flashinfer_wheel_commit="c" * 40),
            dict(
                valid,
                flashinfer_python_patch=dict(
                    valid["flashinfer_python_patch"], source_file="other.py"
                ),
            ),
            dict(
                valid,
                flashinfer_python_patch=dict(
                    valid["flashinfer_python_patch"], sha256="bad"
                ),
            ),
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                recipe.flashinfer_patch_spec(bad)

    def test_compact_provider_provenance(self):
        import render

        rows = []
        for case in recipe.matrix():
            count = case["measured_requests"]
            rows.append(
                dict(
                    case,
                    completed=count,
                    measured_spec_covered=count,
                    output_tokens=10 * count,
                    measured_spec_verify_ct=2 * count,
                    measured_spec_proposed_drafts=10 * count,
                    measured_spec_correct_drafts=8 * count,
                    duration_s=count,
                    median_tpot_ms=10,
                    output_tok_s=10,
                    output_tok_s_gpu=1.25,
                    interactivity_tok_s_user=100,
                    measured_acceptance_length=5,
                    measured_acceptance_rate=0.8,
                    sglang_commit="a" * 40,
                    flashinfer_commit="b" * 40,
                    prompt_format="DeepSeek-V4.1 chat; reasoning_effort=None",
                )
            )
        self.assertEqual(len(render.validate_table(rows)), 18)
        for row in rows:
            row.update(
                flashinfer_wheel_commit=recipe.FLASHINFER_WHEEL_BASE,
                flashinfer_python_patch={
                    "source_file": recipe.FLASHINFER_PATCH_SOURCE,
                    "original_sha256": "a" * 64,
                    "sha256": "b" * 64,
                },
            )
        self.assertEqual(render.validate_table(rows)[0]["output_tok_s_gpu"], 1.25)
        rows[0]["flashinfer_python_patch"] = None
        with self.assertRaisesRegex(ValueError, "Different FI commits"):
            render.validate_table(rows)

    def test_source_and_installed_provider_split(self):
        # Fake only external providers; execute the real Git/blob checks and the
        # actual child proof, including its source/module-origin/file-byte checks.
        with tempfile.TemporaryDirectory(dir=recipe.REPO.parent) as d:
            root = Path(d).resolve()
            source = root / "source"
            source.mkdir()
            kernel = source / recipe.FLASHINFER_PATCH_SOURCE
            kernel.parent.mkdir(parents=True)
            original = b"VALUE = 'original'\n"
            corrected = b"VALUE = 'corrected'\n"

            def git(*args):
                return (
                    subprocess.check_output(
                        ["git", "-C", str(source), *args], stderr=subprocess.DEVNULL
                    )
                    .decode()
                    .strip()
                )

            git("init", "-q")
            git("config", "user.name", "Local fixture")
            git("config", "user.email", "fixture@example.invalid")
            kernel.write_bytes(original)
            git("add", ".")
            git("commit", "-qm", "Original fixture")
            base = git("rev-parse", "HEAD")
            kernel.write_bytes(corrected)
            git("commit", "-qam", "Corrected fixture")
            head = git("rev-parse", "HEAD")
            package_root = root / "site-packages"
            sg_root = root / "sglang"
            files = {
                package_root / "flashinfer/__init__.py": "__version__='fixture'\n",
                package_root
                / "flashinfer/_build_meta.py": f"__git_commit__={base!r}\n",
                package_root
                / "flashinfer_cubin/__init__.py": "__version__='fixture'\n",
                package_root
                / "flashinfer_cubin/_build_meta.py": f"__git_version__={base!r}\n",
                package_root / "flashinfer/jit/__init__.py": "",
                package_root / "flashinfer/jit/env.py": "FLASHINFER_AOT_PROVIDERS=[]\n",
                package_root / "flashinfer/gemm/__init__.py": "",
                package_root / "flashinfer/gemm/kernels/__init__.py": "",
                sg_root / "python/sglang/__init__.py": "",
                root
                / "sitecustomize.py": f"import site\nsite.getsitepackages=lambda:[{str(package_root)!r}]\n",
            }
            for path, body in files.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body)
            installed = package_root / recipe.FLASHINFER_PATCH_SOURCE
            installed.write_bytes(corrected)
            cfg = {
                "python": sys.executable,
                "sglang_root": str(sg_root),
                "flashinfer_root": str(source),
                "flashinfer_commit": head,
                "flashinfer_wheel_commit": base,
                "flashinfer_python_patch": {
                    "source_file": recipe.FLASHINFER_PATCH_SOURCE,
                    "original_sha256": hashlib.sha256(original).hexdigest(),
                    "sha256": hashlib.sha256(corrected).hexdigest(),
                },
            }
            env = dict(
                os.environ,
                PYTHONPATH=os.pathsep.join(
                    map(str, (root, package_root, sg_root / "python"))
                ),
            )
            with patch.object(recipe, "FLASHINFER_WHEEL_BASE", base):
                proof = json.loads(recipe.installed_runtime(cfg, env)["stdout"])
                self.assertEqual(proof["git_commit"], base)
                self.assertEqual(proof["python_source_commit"], head)
                self.assertEqual(
                    proof["python_patch"]["installed_file"], str(installed)
                )
                self.assertEqual(proof["python_patch"]["installed_bytes"], 20)
                installed.write_bytes(original)
                with self.assertRaisesRegex(RuntimeError, "provider proof failed"):
                    recipe.installed_runtime(cfg, env)
                installed.write_bytes(corrected)
                with self.assertRaisesRegex(ValueError, "commit blob differs"):
                    recipe.verify_flashinfer_patch(
                        dict(cfg, flashinfer_commit=base), env
                    )
                wrong = dict(cfg["flashinfer_python_patch"], original_sha256="0" * 64)
                with self.assertRaisesRegex(ValueError, "base-commit blob differs"):
                    recipe.verify_flashinfer_patch(
                        dict(cfg, flashinfer_python_patch=wrong), env
                    )
                kernel.write_bytes(original)
                with self.assertRaisesRegex(ValueError, "source file differs"):
                    recipe.verify_flashinfer_patch(cfg, env)
                kernel.write_bytes(corrected)
                legacy = {
                    k: v
                    for k, v in cfg.items()
                    if k not in recipe.FLASHINFER_PATCH_KEYS
                }
                legacy["flashinfer_commit"] = base
                proof = json.loads(recipe.installed_runtime(legacy, env)["stdout"])
                self.assertEqual(proof["git_commit"], base)
                self.assertIsNone(proof["python_patch"])

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
            self.assertEqual(
                json.loads(args[args.index("--json-model-override-args") + 1]),
                {"vision_n_layers": 0},
            )
            self.assertNotIn("--language-only", args)
            self.assertNotIn("--language-model-only", args)
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
