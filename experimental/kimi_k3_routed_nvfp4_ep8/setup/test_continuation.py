"""CPU behavior for explicit eleven-case scope and bounded plain-port retries."""

import copy
import errno
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest.mock import patch

import continuation
import plan

import execution


class ContinuationTests(unittest.TestCase):
    def fixture(self):
        cfg = plan.read_json(Path(__file__).resolve().parents[1] / "campaign.json")
        cases = [
            {
                "case_id": cid,
                "warmup_requests": 2 * int(cid.rsplit("-c", 1)[1]),
                "measured_requests": 10 * int(cid.rsplit("-c", 1)[1]),
            }
            for cid in [continuation.PRIOR_ID, *continuation.EXECUTION_IDS]
        ]
        return cfg, {"cases": cases, "continuation": copy.deepcopy(cfg["continuation"])}

    def test_exact_eleven_selection_and_totals(self):
        cfg, planned = self.fixture()
        plan.validate_campaign(cfg)
        chosen = continuation.selected_cases(planned)
        self.assertEqual(chosen[0]["case_id"], "megamoe-w4a4-tp8-ep8-dp1-c4")
        self.assertEqual(chosen[-1]["case_id"], "trtllm-w4a4-tp8-ep8-dp1-c16")
        self.assertEqual(len(chosen), 11)
        self.assertEqual(sum(x["warmup_requests"] for x in chosen), 296)
        self.assertEqual(sum(x["measured_requests"] for x in chosen), 1480)
        for ids in [
            continuation.EXECUTION_IDS[1:],
            continuation.EXECUTION_IDS[::-1],
            [continuation.PRIOR_ID, *continuation.EXECUTION_IDS],
            continuation.EXECUTION_IDS[:-1] + [continuation.EXECUTION_IDS[0]],
        ]:
            bad = copy.deepcopy(planned)
            bad["continuation"]["execution_case_ids"] = ids
            with self.assertRaises(ValueError):
                continuation.selected_cases(bad)

    def test_missing_pending_parent_cannot_execute(self):
        cfg, planned = self.fixture()
        # Explicit pending input: independent of the checked-in campaign's status.
        cfg["continuation"]["prior_acceptance"] = {
            "path": "/REVIEW_REQUIRED/PRIOR_ACCEPTANCE.json",
            "bytes": 0,
            "sha256": "0" * 64,
        }
        planned["continuation"] = copy.deepcopy(cfg["continuation"])
        with self.assertRaisesRegex(ValueError, "Actual prior acceptance absent"):
            continuation.verify_prior(
                cfg, planned, lambda d: self.fail("No pending receipt can be read")
            )
        bad = copy.deepcopy(cfg)
        del bad["continuation"]
        with self.assertRaises((ValueError, KeyError)):
            plan.validate_campaign(bad)

    def test_terminal_is_eleven_not_fabricated_twelve(self):
        _, planned = self.fixture()
        terminal = {
            "status": "completed",
            "exit_code": 0,
            "error": None,
            "cleanup_errors": [],
            "remaining_owners": [],
            "completed_case_ids": list(continuation.EXECUTION_IDS),
            "execution_case_ids": list(continuation.EXECUTION_IDS),
            "execution_totals": dict(continuation.TOTALS),
            "prior_case_id": continuation.PRIOR_ID,
        }
        continuation.verify_execution_terminal(terminal, planned)
        for key, value in [
            (
                "completed_case_ids",
                [continuation.PRIOR_ID, *continuation.EXECUTION_IDS],
            ),
            ("exit_code", 1),
            ("remaining_owners", [{"pid": 123}]),
            (
                "execution_totals",
                {"cases": 12, "warmup_requests": 360, "measured_requests": 1800},
            ),
        ]:
            bad = copy.deepcopy(terminal)
            bad[key] = value
            with self.assertRaises(ValueError):
                continuation.verify_execution_terminal(bad, planned)

    def test_plain_bind_waits_for_release_and_logs(self):
        with tempfile.TemporaryDirectory() as td:
            held = socket.socket()
            held.bind(("127.0.0.1", 0))
            held.listen()
            port = held.getsockname()[1]
            release = threading.Timer(0.06, held.close)
            release.start()
            try:
                execution.wait_plain_bind(
                    Path(td) / "port.jsonl", port=port, timeout=1, interval=0.02
                )
            finally:
                release.join()
                held.close()
            rows = [
                json.loads(x)
                for x in (Path(td) / "port.jsonl").read_text().splitlines()
            ]
            self.assertEqual(rows[0]["errno"], errno.EADDRINUSE)
            self.assertEqual(rows[-1]["status"], "bind-available")
            self.assertGreater(len(rows), 1)

    def test_persistent_occupation_fails_and_other_errno_never_retries(self):
        with tempfile.TemporaryDirectory() as td, socket.socket() as held:
            held.bind(("127.0.0.1", 0))
            held.listen()
            with self.assertRaises(TimeoutError):
                execution.wait_plain_bind(
                    Path(td) / "persistent.jsonl",
                    port=held.getsockname()[1],
                    timeout=0.02,
                    interval=0.01,
                )

            class Denied:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    return None

                def bind(self, _):
                    raise OSError(errno.EACCES, "fixture denial")

            with (
                patch.object(execution.socket, "socket", return_value=Denied()),
                patch.object(
                    execution.time,
                    "sleep",
                    side_effect=AssertionError("must not retry"),
                ),
            ):
                with self.assertRaises(PermissionError):
                    execution.wait_plain_bind(Path(td) / "denied.jsonl", timeout=1)
            rows = (Path(td) / "denied.jsonl").read_text().splitlines()
            self.assertEqual(len(rows), 1)
            self.assertEqual(json.loads(rows[0])["errno"], errno.EACCES)


if __name__ == "__main__":
    unittest.main(verbosity=2)
