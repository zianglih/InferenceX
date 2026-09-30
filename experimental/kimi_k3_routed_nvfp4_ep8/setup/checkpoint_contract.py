"""Offline contract for the custom routed-only NVFP4 checkpoint.

These normalized acceptance fields must be authored from actual conversion
receipts and an independent review. This module never converts or launches.
"""

from pathlib import PurePosixPath
import re

SOURCE_REPO = "moonshotai/Kimi-K3"
SOURCE_REVISION = "f831ab66814297da540d832a5235f8e904f29d06"
MILES_COMMIT = "9e4260de047a704208535c0e90c531929879ab40"
REMOTE_ROOT = "/data/home/ziangli/kimik3-routed-nvfp4-conversion-20260929"
MODEL_PATH = REMOTE_ROOT + "/checkpoints/main-routed-nvfp4-attempt2"
CHECKS = (
    "original_published_file_hashes",
    "bf16_non_routed_tensor_bytes",
    "nvfp4_non_routed_tensor_bytes",
    "routed_scope_shapes_dtypes_scales",
    "numerical_conversion_checks",
    "non_routed_linear_exclusions",
    "metadata_tokenizer_preservation",
)
METADATA = (
    "config.json",
    "hf_quant_config.json",
    "model.safetensors.index.json",
    "tokenizer_config.json",
    "tokenization_kimi.py",
    "encoding_k3.py",
    "tiktoken.model",
    "generation_config.json",
)


def require(value, message):
    if not value:
        raise ValueError(message)


def validate_checkpoint(ck, model_path):
    expected = {
        "kind": "custom_main_routed_nvfp4",
        "source_repo": SOURCE_REPO,
        "source_revision": SOURCE_REVISION,
        "miles_commit": MILES_COMMIT,
        "source_quantization": "mxfp4",
        "conversion_stages": ["mxfp4_to_bf16", "main_routed_experts_to_nvfp4"],
        "output_quantization": "modelopt_fp4",
        "output_quant_algo": "NVFP4",
        "group_size": 16,
        "scope": "main_language_routed_experts_only",
        "non_routed_preservation": "original_tensor_dtype_shape_bytes_at_both_stages",
        "output_path": MODEL_PATH,
        "num_nextn_predict_layers": 0,
    }
    require(
        set(ck) == set(expected) | {"acceptance", "local_tensor_verification"},
        "Custom checkpoint schema differs",
    )
    require(
        all(ck.get(k) == v for k, v in expected.items()),
        "Custom checkpoint contract differs",
    )
    require(model_path == MODEL_PATH, "Custom checkpoint model path differs")
    require(
        type(ck["local_tensor_verification"]) is bool, "Invalid verification marker"
    )
    gate = ck["acceptance"]
    require(
        set(gate) == {"path", "bytes", "sha256"}, "Checkpoint acceptance binding schema"
    )
    path = PurePosixPath(gate["path"])
    require(
        path.is_absolute() and ".." not in path.parts and str(path) == gate["path"],
        "Unsafe conversion acceptance path",
    )
    pending = gate["bytes"] is None and gate["sha256"] is None
    require(
        pending
        or (
            type(gate["bytes"]) is int
            and gate["bytes"] > 0
            and isinstance(gate["sha256"], str)
            and re.fullmatch("[0-9a-f]{64}", gate["sha256"])
        ),
        "Incomplete conversion acceptance binding",
    )
    require(
        not ck["local_tensor_verification"] or not pending,
        "Verified checkpoint requires an exact acceptance binding",
    )


def verify_acceptance(ck, desc, evidence, *, allow_synthetic=False):
    """Rehash normalized root acceptance and all linked local evidence."""
    validate_checkpoint(ck, ck["output_path"])
    gate = ck["acceptance"]
    require(
        ck["local_tensor_verification"] and gate["sha256"] is not None,
        "Custom conversion acceptance is pending",
    )
    require(
        all(desc[k] == gate[k] for k in ("bytes", "sha256")),
        "Conversion acceptance binding differs",
    )
    doc = evidence.document(desc)
    require(
        doc.get("schema_version") == 1
        and doc.get("status") == "ACCEPTED_CUSTOM_ROUTED_NVFP4",
        "Custom conversion is not accepted",
    )
    kind = doc.get("data_kind")
    require(
        kind == "actual" or (allow_synthetic and kind == "synthetic_test_only"),
        "Conversion requires actual evidence only",
    )
    for key in (
        "source_repo",
        "source_revision",
        "miles_commit",
        "output_path",
        "scope",
    ):
        require(doc.get(key) == ck[key], "Conversion identity differs: " + key)
    require(
        doc.get("checks") == dict.fromkeys(CHECKS, True), "Incomplete conversion checks"
    )
    stages = doc.get("stage_reviews", {})
    require(
        set(stages) == {"original", "bf16", "nvfp4"},
        "Three actual conversion stage receipts required",
    )
    for stage, bound in stages.items():
        evidence.bound(bound)
    metadata = doc.get("metadata", {})
    require(
        set(METADATA) <= set(metadata), "Exact custom output metadata/code required"
    )
    for name, bound in metadata.items():
        require(PurePosixPath(bound["path"]).name == name, "Metadata filename differs")
        evidence.bound(bound)
    config = evidence.document(metadata["config.json"])
    quant = config.get("quantization_config", {})
    require(
        quant.get("quant_method") == "modelopt"
        and quant.get("quant_algo") == "NVFP4"
        and quant.get("group_size") == 16,
        "Custom output must autodetect standard serialized NVFP4",
    )
    require(
        not config.get("text_config", {}).get("quantization_config"),
        "Stale nested source quantization metadata",
    )
    require(
        isinstance(quant.get("ignore"), list) and bool(quant["ignore"]),
        "Actual non-routed exclusion list required",
    )
    review = evidence.document(doc["independent_review"])
    require(
        review.get("status") == "PASS_CUSTOM_ROUTED_NVFP4_REVIEW"
        and review.get("output_path") == MODEL_PATH,
        "Independent custom conversion review required",
    )
    require(
        review.get("checks") == doc["checks"], "Independent conversion checks differ"
    )
    bounds = review.get("bindings")
    require(
        isinstance(bounds, list) and bool(bounds),
        "Independent conversion supporting bytes required",
    )
    for bound in bounds:
        evidence.bound(bound)
    required = [*stages.values(), *metadata.values()]
    require(
        all(bound in bounds for bound in required),
        "Independent review must bind all stage and output metadata bytes",
    )
    return doc
