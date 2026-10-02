# SPDX-License-Identifier: Apache-2.0
"""Measured-request speculative metrics; no server-window or warmup averages."""

import math


def summarize_speculative_metrics(requests: list[dict]) -> dict:
    """Retain every record and fail closed unless exact counters cover the full set."""
    totals = dict.fromkeys(
        (
            "completion_tokens",
            "spec_verify_ct",
            "spec_num_correct_drafts",
            "spec_num_proposed_drafts",
        ),
        0,
    )
    errors = []
    covered = 0
    for index, row in enumerate(requests):
        try:
            if (
                type(row.get("request_index")) is not int
                or row["request_index"] != index
                or row.get("success") is not True
            ):
                raise ValueError("failed request or noncanonical request index")
            completion = row.get("completion_tokens")
            details = row.get("spec_tokens_details")
            if type(completion) is not int or completion <= 0 or not isinstance(details, dict):
                raise ValueError("missing positive final usage or speculative details")
            counters = {key: details.get(key) for key in totals if key != "completion_tokens"}
            if any(type(value) is not int or value < 0 for value in counters.values()):
                raise ValueError("missing, negative, or noninteger speculative counter")
            verify = counters["spec_verify_ct"]
            proposed = counters["spec_num_proposed_drafts"]
            correct = counters["spec_num_correct_drafts"]
            if verify == 0 or proposed == 0 or correct > proposed:
                raise ValueError("zero verification/proposal denominator or invalid accepted count")
            length = details.get("spec_accept_length")
            if (
                type(length) not in (int, float)
                or not math.isfinite(length)
                or not math.isclose(length, completion / verify, rel_tol=1e-9, abs_tol=1e-12)
            ):
                raise ValueError(
                    "native acceptance length disagrees with final usage / verify count"
                )
            rate = details.get("spec_accept_rate")
            if (
                type(rate) not in (int, float)
                or not math.isfinite(rate)
                or not math.isclose(rate, correct / proposed, rel_tol=1e-9, abs_tol=1e-12)
            ):
                raise ValueError("native acceptance rate disagrees with accepted / proposed counts")
            totals["completion_tokens"] += completion
            for key, value in counters.items():
                totals[key] += value
            covered += 1
        except (AttributeError, TypeError, ValueError) as exc:
            errors.append({"request_index": index, "error": str(exc)})
    complete = bool(requests) and not errors and covered == len(requests)
    return {
        "schema_version": 1,
        "status": "passed" if complete else "unavailable",
        "scope": "measured_requests_only",
        "aggregation": "sum_completion_tokens_over_sum_spec_verify_ct",
        "requested": len(requests),
        "covered": covered,
        **{key: value if complete else None for key, value in totals.items()},
        "acceptance_length": totals["completion_tokens"] / totals["spec_verify_ct"]
        if complete
        else None,
        "acceptance_rate": totals["spec_num_correct_drafts"] / totals["spec_num_proposed_drafts"]
        if complete
        else None,
        "error": None if complete else "Incomplete measured speculative-metric coverage",
        "coverage_errors": errors,
        "requests": requests,
    }
