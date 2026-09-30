"""Explicit R4 C32 lineage for an eleven-case continuation; no automatic acceptance."""

from pathlib import Path, PurePosixPath
import re

PRIOR_ID = "megamoe-w4a4-tp8-ep8-dp1-c32"
EXECUTION_IDS = [
    f"{arm}-tp8-ep8-dp1-c{c}"
    for arm in ("megamoe-w4a4", "megamoe-w4a16", "trtllm-w4a4")
    for c in (32, 4, 8, 16)
][1:]
TOTALS = {"cases": 11, "warmup_requests": 296, "measured_requests": 1480}


def need(value, message):
    if not value:
        raise ValueError(message)


def validate_spec(spec):
    need(
        isinstance(spec, dict)
        and set(spec)
        == {
            "schema_version",
            "prior_case_id",
            "execution_case_ids",
            "execution_totals",
            "prior_acceptance",
            "cache_seed_acceptance",
        }
        and spec["schema_version"] == 1,
        "Explicit continuation schema required",
    )
    need(
        spec["prior_case_id"] == PRIOR_ID,
        "Only the accepted first C32 may be inherited",
    )
    need(
        spec["execution_case_ids"] == EXECUTION_IDS,
        "Exact ordered remaining eleven required",
    )
    need(spec["execution_totals"] == TOTALS, "Continuation counts differ")
    for key in ("prior_acceptance", "cache_seed_acceptance"):
        row = spec[key]
        need(set(row) == {"path", "bytes", "sha256"}, "Continuation descriptor fields")
        p = Path(row["path"])
        need(
            p.is_absolute() and ".." not in p.parts and str(p) == row["path"],
            "Continuation canonical path",
        )
        need(
            type(row["bytes"]) is int
            and row["bytes"] >= 0
            and re.fullmatch("[0-9a-f]{64}", row["sha256"]),
            "Continuation descriptor",
        )


def selected_cases(planned):
    spec = planned["continuation"]
    validate_spec(spec)
    cases = planned["cases"]
    need(
        [c["case_id"] for c in cases] == [PRIOR_ID, *EXECUTION_IDS],
        "Canonical twelve plan required",
    )
    chosen = cases[1:]
    need(
        sum(c["warmup_requests"] for c in chosen) == 296
        and sum(c["measured_requests"] for c in chosen) == 1480,
        "Execution request totals differ",
    )
    return chosen


def _same_workload(old_cfg, cfg, old_case, case):
    for key in (
        "name",
        "pins",
        "hardware",
        "workload",
        "common_server_args",
        "arms",
        "local_changes",
    ):
        need(old_cfg[key] == cfg[key], "Prior shared configuration differs: " + key)
    for key in (
        "python",
        "model_path",
        "sglang_root",
        "flashinfer_root",
        "ready_timeout_seconds",
        "benchmark_timeout_seconds",
        "term_seconds",
        "kill_seconds",
    ):
        need(
            old_cfg["runtime"][key] == cfg["runtime"][key],
            "Prior runtime changes beyond namespace: " + key,
        )
    old_ck = dict(old_cfg["checkpoint"])
    new_ck = dict(cfg["checkpoint"])
    old_ck["acceptance"] = {
        k: v for k, v in old_ck["acceptance"].items() if k != "path"
    }
    new_ck["acceptance"] = {
        k: v for k, v in new_ck["acceptance"].items() if k != "path"
    }
    need(old_ck == new_ck, "Prior checkpoint format/acceptance differs")
    changes = {
        "case_dir",
        "client_argv",
        "environment",
        "compile_cache_root",
        "tactic_cache_root",
    }
    need(set(old_case) == set(case), "Prior case fields differ")
    for key in set(case) - changes:
        need(old_case[key] == case[key], "Prior case semantics differ: " + key)
    from results import options

    old_args = options(old_case["client_argv"])
    new_args = options(case["client_argv"])
    need(
        old_case["client_argv"][:4] == case["client_argv"][:4],
        "Prior client module differs",
    )
    need(
        old_args.pop("--result-dir") == old_case["case_dir"]
        and new_args.pop("--result-dir") == case["case_dir"],
        "Prior result directory",
    )
    need(old_args == new_args, "Prior client options differ")
    # The environment changes only the explicitly rendered run/TMP/runtime project namespace.
    old_run = old_cfg["runtime"]["run_root"]
    new_run = cfg["runtime"]["run_root"]
    old_project = (
        old_case["environment"]["PYTHONPATH"]
        .split(":")[-1]
        .removesuffix("/vendor/inferencex")
    )
    new_project = (
        case["environment"]["PYTHONPATH"]
        .split(":")[-1]
        .removesuffix("/vendor/inferencex")
    )
    replacements = [
        (old_run, new_run),
        (old_cfg["runtime"]["tmp_root"], cfg["runtime"]["tmp_root"]),
        (old_project, new_project),
    ]

    def relocated(value):
        for before, after in replacements:
            value = value.replace(before, after)
        return value

    need(
        {k: relocated(v) for k, v in old_case["environment"].items()}
        == case["environment"],
        "Prior launch environment changes beyond namespace",
    )
    for key in ("case_dir", "compile_cache_root", "tactic_cache_root"):
        need(relocated(old_case[key]) == case[key], "Prior case namespace differs")


def verify_prior(cfg, planned, read_bound, *, prior_descriptor=None):
    """read_bound(descriptor) returns parsed JSON after exact-byte verification."""
    from results import CASE_CHECKS, verify_result

    spec = cfg["continuation"]
    validate_spec(spec)
    selected_cases(planned)
    need(spec == planned["continuation"], "Plan continuation differs")
    need(
        spec["prior_acceptance"]["bytes"] > 0
        and not spec["prior_acceptance"]["path"].startswith("/REVIEW_REQUIRED/"),
        "Actual prior acceptance absent",
    )
    parent_desc = prior_descriptor or spec["prior_acceptance"]
    need(
        all(parent_desc[k] == spec["prior_acceptance"][k] for k in ("bytes", "sha256")),
        "Prior acceptance relocation changed bytes",
    )
    prior = read_bound(parent_desc)
    need(
        prior["schema_version"] == 1
        and prior["status"] == "ACCEPTED_KIMI_PRIOR_C32_FOR_CONTINUATION"
        and prior["data_kind"] == "actual"
        and prior["case_id"] == PRIOR_ID,
        "Accepted actual C32 parent required",
    )
    need(
        prior["accepted_case_only"] is True
        and prior["original_sweep_accepted"] is False,
        "Prior point is not a successful sweep",
    )
    review = read_bound(prior["case_review"])
    need(
        review["status"] == "PASS_ACTUAL_CASE_REVIEW"
        and review["case_id"] == PRIOR_ID
        and review["manifest_sha256"] == prior["manifest"]["sha256"]
        and review["warmup_requests"] == 64
        and all(review["checks"].get(k) is True for k in CASE_CHECKS),
        "Full actual prior case review required",
    )
    for name in (
        "independent_actual_review",
        "root_case_review",
        "original_source",
        "cache_lineage",
    ):
        need(prior[name]["bytes"] > 0, "Prior source/review/cache evidence absent")
        read_bound(prior[name])
    failure = read_bound(prior["failed_terminal"])
    need(
        failure["status"] == "failed"
        and failure["exit_code"] != 0
        and failure["completed_case_ids"] == [PRIOR_ID]
        and failure["error"]
        and not failure["cleanup_errors"]
        and not failure["remaining_owners"],
        "Preserved R4 failed terminal differs",
    )
    failure_review = read_bound(prior["failed_terminal_review"])
    need(
        failure_review["status"] == "PASS_ACTUAL_FAILED_TERMINAL_REVIEW"
        and failure_review["terminal_sha256"] == prior["failed_terminal"]["sha256"],
        "R4 failure review required",
    )
    cfg_old = read_bound(prior["campaign"])
    plan_old = read_bound(prior["plan"])
    need(
        plan_old["campaign"]["sha256"] == prior["campaign"]["sha256"],
        "Prior plan/config join",
    )
    settings = read_bound(prior["settings"])
    need(
        settings["config"] == cfg_old and settings["case"] == plan_old["cases"][0],
        "Prior settings/config/plan join",
    )
    _same_workload(cfg_old, cfg, settings["case"], planned["cases"][0])
    manifest = read_bound(prior["manifest"])
    need(manifest["case_id"] == PRIOR_ID, "Prior manifest identity")
    by_name = {}
    for row in manifest["files"]:
        path = PurePosixPath(row["path"])
        need(
            str(path) == row["path"]
            and not path.is_absolute()
            and ".." not in path.parts
            and path.parts[:2] == ("cases", PRIOR_ID),
            "Prior manifest path",
        )
        need(str(path) not in by_name, "Duplicate prior manifest member")
        by_name[str(path)] = row
    for name, field in [
        ("settings.json", "settings"),
        ("result.json", "result"),
        ("requested-lengths.json", "requested_lengths"),
    ]:
        row = by_name["cases/" + PRIOR_ID + "/" + name]
        need(
            all(row[k] == prior[field][k] for k in ("bytes", "sha256")),
            "Prior data not joined to manifest",
        )
    result = read_bound(prior["result"])
    requested = read_bound(prior["requested_lengths"])
    need(
        not result.get("SYNTHETIC_TEST_ONLY")
        and not requested.get("SYNTHETIC_TEST_ONLY"),
        "Actual prior arrays required",
    )
    derived = verify_result(result, requested, planned["cases"][0])
    return {
        "prior": prior,
        "reference_arrays": {k: requested[k] for k in ("input_lens", "output_lens")},
        "derived": derived,
    }


def verify_execution_terminal(terminal, planned):
    selected_cases(planned)
    need(
        terminal["status"] == "completed"
        and terminal["exit_code"] == 0
        and terminal["error"] is None
        and terminal["cleanup_errors"] == []
        and terminal["remaining_owners"] == []
        and terminal["completed_case_ids"] == EXECUTION_IDS,
        "Clean waited eleven-case worker terminal required",
    )
    need(
        terminal["execution_case_ids"] == EXECUTION_IDS
        and terminal["execution_totals"] == TOTALS
        and terminal["prior_case_id"] == PRIOR_ID,
        "Honest continuation terminal scope required",
    )
