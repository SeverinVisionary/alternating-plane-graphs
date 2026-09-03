#!/usr/bin/env python3
"""Keep the portable cap-motif cloud job bound to the full cap interface."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
JOB = ROOT / "CLOUD_BOOL_CAP_MOTIF_JOB.md"


class CloudBooleanCapMotifJobTests(unittest.TestCase):
    def test_controls_and_targets_require_the_full_marked_cap_interface(self) -> None:
        text = JOB.read_text(encoding="utf-8")
        self.assertIn("run_target 28 12", text)
        self.assertIn("run_target 29 12", text)
        self.assertIn("run_target 31 12", text)
        self.assertGreaterEqual(text.count(".require_cap_interface == true"), 2)
        self.assertGreaterEqual(text.count(".require_cap_facets == true"), 2)
        self.assertIn("target_certificate_exists=false", text)
        self.assertIn("nonexistence_claimed=false", text)


if __name__ == "__main__":
    unittest.main()
