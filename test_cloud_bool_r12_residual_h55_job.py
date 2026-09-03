#!/usr/bin/env python3
"""Keep the residual-H55 cloud job scoped to its proved portable branch."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
JOB = ROOT / "CLOUD_BOOL_R12_RESIDUAL_H55_JOB.md"


class CloudResidualH55JobTests(unittest.TestCase):
    def test_job_runs_only_the_three_canonical_r12_profiles(self) -> None:
        text = JOB.read_text(encoding="utf-8")
        self.assertIn("run_target 28", text)
        self.assertIn("run_target 29", text)
        self.assertIn("run_target 31", text)
        self.assertGreaterEqual(text.count("require_residual_h55_c4"), 3)
        self.assertIn("require_residual_h55_c4 == false", text)
        self.assertIn("require_residual_h55_c4 == true", text)
        self.assertIn("target_certificate_exists=false", text)
        self.assertIn("nonexistence_claimed=false", text)


if __name__ == "__main__":
    unittest.main()
