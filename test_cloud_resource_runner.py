#!/usr/bin/env python3
"""Regression tests for the portable cloud resource wrapper."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "cloud_resource_runner.py"


class CloudResourceRunnerTests(unittest.TestCase):
    def _run(self, child: str) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        with tempfile.TemporaryDirectory(prefix="apg-resource-runner-") as directory:
            metadata = Path(directory) / "resources.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--metadata",
                    str(metadata),
                    "--",
                    sys.executable,
                    "-c",
                    child,
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            payload = json.loads(metadata.read_text(encoding="utf-8"))
        self.assertIsInstance(payload, dict)
        return completed, payload

    def test_success_preserves_child_output_and_resource_record(self) -> None:
        completed, payload = self._run("print('child-ok')")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "child-ok\n")
        self.assertEqual(payload["format"], "apg-cloud-resource-runner-v1")
        self.assertEqual(payload["returncode"], 0)
        self.assertEqual(payload["normalized_exit_status"], 0)
        self.assertGreaterEqual(payload["wall_seconds"], 0.0)
        self.assertIn("max_rss_platform_units", payload)
        self.assertNotIn("launch_error", payload)

    def test_child_failure_is_not_lost(self) -> None:
        completed, payload = self._run("import sys; sys.exit(7)")
        self.assertEqual(completed.returncode, 7)
        self.assertEqual(payload["returncode"], 7)
        self.assertEqual(payload["normalized_exit_status"], 7)

    def test_missing_executable_still_writes_block_metadata(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-resource-runner-") as directory:
            metadata = Path(directory) / "resources.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--metadata",
                    str(metadata),
                    "--",
                    "apg-intentionally-missing-executable",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            payload = json.loads(metadata.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 127)
        self.assertEqual(payload["returncode"], 127)
        self.assertEqual(payload["normalized_exit_status"], 127)
        self.assertIn("FileNotFoundError", str(payload["launch_error"]))


if __name__ == "__main__":
    unittest.main()
