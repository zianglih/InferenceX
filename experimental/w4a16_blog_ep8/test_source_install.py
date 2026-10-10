"""The image uninstall must remove importable orphan provider namespaces."""

import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import flashinfer_orphans as orphans


class TestFlashInferOrphanQuarantine(unittest.TestCase):
    def test_registered_distribution_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "quarantine"
            registered = SimpleNamespace(metadata={"Name": "flashinfer_jit_cache"})
            with patch.object(orphans.md, "distributions", return_value=[registered]):
                with self.assertRaisesRegex(RuntimeError, "remain registered"):
                    orphans.quarantine_orphaned_flashinfer(destination)
            self.assertFalse(destination.exists())

    def test_orphan_namespaces_move_and_become_unimportable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = root / "site-packages"
            site.mkdir()
            names = (
                "flashinfer",
                "flashinfer_cubin",
                "flashinfer_jit_cache",
                "flashinfer_jit_cache_sm103a",
            )
            for name in (*names, "unrelated"):
                nested = site / name / "providers" / "nested"
                nested.mkdir(parents=True)
                (nested / "generated.bin").write_bytes(b"preserved")
            with (
                patch.object(orphans.md, "distributions", return_value=[]),
                patch.object(orphans.site, "getsitepackages", return_value=[str(site)]),
                patch.object(orphans.sysconfig, "get_path", return_value=str(site)),
                patch.object(sys, "path", [str(site)]),
            ):
                before = importlib.util.find_spec("flashinfer_jit_cache")
                self.assertIsNotNone(before)
                self.assertIsNone(before.origin)
                moved = orphans.quarantine_orphaned_flashinfer(root / "quarantine")
                self.assertEqual(len(moved), len(names))
                for name in names:
                    self.assertIsNone(importlib.util.find_spec(name))
                self.assertIsNotNone(importlib.util.find_spec("unrelated"))
            for row in moved:
                self.assertEqual(
                    (Path(row["to"]) / "providers/nested/generated.bin").read_bytes(),
                    b"preserved",
                )
                self.assertFalse(Path(row["from"]).exists())
            self.assertEqual(
                (site / "unrelated/providers/nested/generated.bin").read_bytes(),
                b"preserved",
            )


if __name__ == "__main__":
    unittest.main()
