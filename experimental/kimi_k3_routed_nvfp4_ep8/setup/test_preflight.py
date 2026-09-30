"""CPU-only guards for the explicit runtime probe; no ML imports or device calls."""

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "preflight", Path(__file__).with_name("preflight.py")
)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PreflightTests(unittest.TestCase):
    def test_import_is_gpu_free(self):
        self.assertNotIn("torch", sys.modules)
        self.assertNotIn("sglang", sys.modules)

    def test_json_and_optimization_fail_closed(self):
        for raw in ['{"x":1,"x":2}', '{"x":NaN}']:
            with self.assertRaises((RuntimeError, ValueError)):
                p.parse(raw)
        r = subprocess.run(
            [sys.executable, "-B", "-O", str(Path(p.__file__)), "--help"],
            capture_output=True,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(b"Optimized Python prohibited", r.stderr)

    def test_digest_rejects_changed_links_and_cap(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve()
            f = root / "data"
            f.write_bytes(b"abc")
            expected = {"bytes": 3, "sha256": hashlib.sha256(b"abc").hexdigest()}
            self.assertEqual(p.digest(f, expected), expected)
            (root / "link").symlink_to(f)
            for target, desc, cap in [
                (root / "link", expected, 9),
                (f, expected, 2),
                (f, {**expected, "bytes": 4}, 9),
            ]:
                with self.assertRaises(RuntimeError):
                    p.digest(target, desc, cap)

    def test_native_file_cap_is_separate(self):
        expected = {"bytes": 438000000, "sha256": "a" * 64}
        with patch.object(p, "digest", return_value=expected) as spy:
            self.assertEqual(
                p.protected_runtime({"protected_runtime_files": {"/native": expected}}),
                {"/native": expected},
            )
            spy.assert_called_once_with("/native", expected, limit=1 << 30)
        with tempfile.TemporaryDirectory() as d:
            f = Path(d).resolve() / "sparse"
            with f.open("wb") as out:
                out.truncate((1 << 30) + 1)
            with (
                patch.object(
                    p.os,
                    "open",
                    side_effect=AssertionError("must refuse before opening"),
                ),
                self.assertRaises(RuntimeError),
            ):
                p.protected_runtime({"protected_runtime_files": {str(f): expected}})

    def test_gpu_exact_idle_and_context(self):
        expected = [
            {"index": i, "uuid": f"GPU-{i}", "name": "NVIDIA B300 SXM6 AC"}
            for i in range(8)
        ]
        rows = "\n".join(f"{i}, GPU-{i}, NVIDIA B300 SXM6 AC, 0, 0" for i in range(8))
        with patch.object(p, "command", side_effect=[rows, ""]):
            self.assertEqual(len(p.gpu_query(expected)["gpus"]), 8)
        for bad in [
            rows.replace("GPU-0", "GPU-other"),
            rows.replace("AC, 0, 0", "AC, 1, 0", 1),
            rows.replace("AC, 0, 0", "AC, 0, 101", 1),
        ]:
            with (
                patch.object(p, "command", side_effect=[bad, ""]),
                self.assertRaises(RuntimeError),
            ):
                p.gpu_query(expected)
        with (
            patch.object(p, "command", side_effect=[rows, "999999, GPU-0"]),
            self.assertRaises(RuntimeError),
        ):
            p.gpu_query(expected)
        with patch.object(p, "command", side_effect=[rows, f"{os.getpid()}, GPU-0"]):
            p.gpu_query(expected, True)

    def fixture(self, d):
        root = Path(d).resolve() / "model"
        root.mkdir()
        sidecars = {}
        config = {
            "quantization_config": {
                "quant_method": "modelopt",
                "quant_algo": "NVFP4",
                "group_size": 16,
                "ignore": ["dense"],
            },
            "text_config": {},
        }
        for n in (
            *p.METADATA,
            *(f"meta-{i}.json" for i in range(10)),
            *(f".eval_results/e{i}.yaml" for i in range(5)),
            "assets/logo.png",
        ):
            f = root / n
            f.parent.mkdir(exist_ok=True)
            f.write_bytes(json.dumps(config).encode() if n == "config.json" else b"{}")
            sidecars[n] = p.digest(f)
        shards = {}
        for i in range(96):
            n = f"model-{i:05}-of-000096.safetensors"
            f = root / n
            f.write_bytes(b"not-a-real-tensor")
            shards[n] = {**p.digest(f), "stat": p.identity(f.stat())}
        accepted = {
            "status": "ACCEPTED_CUSTOM_ROUTED_NVFP4",
            "data_kind": "actual",
            "output_path": str(root),
            "scope": "main_language_routed_experts_only",
            "checks": dict.fromkeys(
                [
                    "original_published_file_hashes",
                    "bf16_non_routed_tensor_bytes",
                    "nvfp4_non_routed_tensor_bytes",
                    "routed_scope_shapes_dtypes_scales",
                    "numerical_conversion_checks",
                    "non_routed_linear_exclusions",
                    "metadata_tokenizer_preservation",
                ],
                True,
            ),
            "metadata": {n: sidecars[n] for n in p.METADATA},
        }
        a = root.parent / "accepted.json"
        a.write_text(json.dumps(accepted))
        ad = p.digest(a)
        r = {
            "checkpoint": {
                "path": str(root),
                "acceptance_path": str(a),
                "acceptance_sha256": ad["sha256"],
                "shards": shards,
                "sidecars": sidecars,
            },
            "bound_files": {str(a): ad},
        }
        return root, r, ad

    def test_checkpoint_scope_no_tensor_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root, r, ad = self.fixture(d)
            seen = []
            original = p.digest

            def spy(name, *args, **kwargs):
                seen.append(str(name))
                return original(name, *args, **kwargs)

            with (
                patch.object(p, "MODEL", str(root)),
                patch.object(p, "digest", side_effect=spy),
            ):
                answer = p.checkpoint(r)
            self.assertEqual(answer["acceptance"], ad)
            self.assertEqual(answer["files"], 120)
            self.assertFalse(answer["tensor_hashes_recomputed"])
            self.assertFalse(any(x.endswith(".safetensors") for x in seen))

    def test_checkpoint_mutations(self):
        for mode in ["unknown", "nested", "sidecar", "shard", "acceptance"]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as d:
                root, r, _ = self.fixture(d)
                if mode == "unknown":
                    (root / "unexpected").write_bytes(b"x")
                if mode == "nested":
                    (root / "assets/extra").write_bytes(b"x")
                if mode == "sidecar":
                    (root / "README").write_bytes(b"x")
                if mode == "shard":
                    (root / next(iter(r["checkpoint"]["shards"]))).write_bytes(b"x")
                if mode == "acceptance":
                    r["checkpoint"]["acceptance_sha256"] = "0" * 64
                with (
                    patch.object(p, "MODEL", str(root)),
                    self.assertRaises(RuntimeError),
                ):
                    p.checkpoint(r)

    def test_request_checks_selectors_and_baseline(self):
        # Request validation does not read checkpoints or import packages.
        r = {
            "schema_version": 1,
            "source_patch": p.source_contract.PATCH,
            "remote_project": p.PROJECT,
            "sglang_root": str(Path(p.PROJECT).parent / "sources/sglang-r3"),
            "flashinfer_source_root": "/data/synthetic-flashinfer",
            "run_root": str(
                Path(p.PROJECT).parent
                / "kimi-k3-ep8-three-curves-c32-20260929-all12-r4"
            ),
            "tmp_root": "/tmp/infx-k3-preflight-r4",
            "port": 30000,
            "node": dict.fromkeys(
                ("hostname", "pod_uid", "sts_uid", "image_id"), "synthetic"
            ),
            "gpus": [
                {"index": i, "uuid": f"GPU-synthetic-{i}", "name": "NVIDIA B300"}
                for i in range(8)
            ],
            "bound_files": {},
            "protected_runtime_files": {},
            "provider_versions": {},
            "checkpoint": {
                "path": p.MODEL,
                "acceptance_path": "/synthetic/accepted.json",
                "acceptance_sha256": "0" * 64,
                "shards": {
                    f"model-{i:05}-of-000096.safetensors": {} for i in range(96)
                },
                "sidecars": {
                    n: {} for n in (*p.METADATA, *(f"metadata-{i}" for i in range(16)))
                },
            },
            "server_args": {
                arm: [
                    "--model-path",
                    p.MODEL,
                    "--quantization",
                    "modelopt_fp4",
                    "--moe-runner-backend",
                    "flashinfer_trtllm"
                    if arm == "trtllm-w4a4"
                    else "flashinfer_megamoe",
                    "--moe-a2a-backend",
                    "none" if arm == "trtllm-w4a4" else "flashinfer_megamoe",
                ]
                for arm in p.ARMS
            },
        }
        r["provider_versions"] = {"torch": "test"}
        r["protected_runtime_files"] = {"/not/read": {"bytes": 1, "sha256": "0" * 64}}
        with patch.object(p, "path", side_effect=Path):
            p.validate_request(r)
        for key, val in [
            ("run_root", p.PROJECT + "/other"),
            ("tmp_root", "/tmp/infx-k3-3c-r4"),
            ("gpus", r["gpus"][:-1]),
            ("protected_runtime_files", {}),
        ]:
            x = copy.deepcopy(r)
            x[key] = val
            with self.assertRaises(RuntimeError):
                p.validate_request(x)
        for replacement in (
            [],
            ["--quantization", "fp8"],
            ["--quantization=modelopt_fp4"],
            ["--quantization", "modelopt_fp4", "--quantization", "modelopt_fp4"],
            ["--quantization", "modelopt_fp4", "--speculative-algorithm", "EAGLE"],
        ):
            x = copy.deepcopy(r)
            args = x["server_args"]["trtllm-w4a4"]
            index = args.index("--quantization")
            args[index : index + 2] = replacement
            with self.assertRaises(RuntimeError):
                p.validate_request(x)

    def test_exact_opencv_loader_environment_transform(self):
        loader = Path("/opt/sglang/lib/python3.12/site-packages/cv2")
        files = {
            str(loader / n): {"bytes": 1, "sha256": "a" * 64}
            for n in ("__init__.py", "config.py", "config-3.py", "load_config_py3.py")
        }
        before = {"LD_LIBRARY_PATH": "/original/lib", "PATH": "/original/bin"}
        prefix = str(loader) + "/../../lib64:"

        def run(after, bound=None, origin=None, override=False):
            with (
                patch.dict(os.environ, after, clear=True),
                patch.dict(
                    sys.modules,
                    {
                        "cv2": SimpleNamespace(
                            __file__=origin or str(loader / "__init__.py")
                        )
                    },
                ),
                patch.object(sys, "version_info", (3, 12, 0)),
                patch.object(p.os.path, "lexists", return_value=override),
                patch.object(p, "digest", side_effect=lambda path, expected: expected),
            ):
                return p.source_environment_changes(
                    before, {"bound_files": files if bound is None else bound}
                )

        self.assertEqual(run(before), {})
        valid = {**before, "LD_LIBRARY_PATH": prefix + before["LD_LIBRARY_PATH"]}
        actual = run(valid)
        self.assertEqual(actual["LD_LIBRARY_PATH"]["before"], before["LD_LIBRARY_PATH"])
        self.assertEqual(actual["LD_LIBRARY_PATH"]["after"], valid["LD_LIBRARY_PATH"])
        self.assertEqual(actual["LD_LIBRARY_PATH"]["source_files"], files)
        for wrong in (
            prefix + valid["LD_LIBRARY_PATH"],
            prefix + "/changed",
            "/wrong:" + before["LD_LIBRARY_PATH"],
            None,
        ):
            with self.subTest(wrong=wrong), self.assertRaises(RuntimeError):
                run(
                    {
                        k: v
                        for k, v in {**before, "LD_LIBRARY_PATH": wrong}.items()
                        if v is not None
                    }
                )
        for kwargs in ({"bound": {}}, {"origin": "/wrong/cv2.py"}, {"override": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(RuntimeError):
                run(valid, **kwargs)
        with self.assertRaises(RuntimeError):
            run({**valid, "PATH": "/changed/bin"})

    def test_environment_rejects_optional_controls_early(self):
        for arm, selector in [
            ("megamoe-w4a4", "1"),
            ("megamoe-w4a16", None),
            ("trtllm-w4a4", "1"),
        ]:
            env = {} if selector is None else {p.SELECTOR: selector}
            with (
                patch.dict(os.environ, env, clear=True),
                self.assertRaises(RuntimeError),
            ):
                p.environment(arm, {})
        for key in p.FORBIDDEN:
            with (
                patch.dict(os.environ, {key: "1"}, clear=True),
                self.assertRaises(RuntimeError),
            ):
                p.environment("megamoe-w4a4", {})


if __name__ == "__main__":
    unittest.main()
