#!/usr/bin/env python3
"""Keep the residual-H55 r=13 cloud job source-bound and serial."""

from __future__ import annotations

import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
JOB = ROOT / "CLOUD_BOOL_R13_RESIDUAL_H55_JOB.md"


class CloudResidualH55R13JobTests(unittest.TestCase):
    def test_job_waits_for_r12_and_runs_only_two_r13_profiles(self) -> None:
        text = JOB.read_text(encoding="utf-8")
        self.assertIn("not a parallel", text)
        self.assertIn("run_target 31", text)
        self.assertIn("run_target 34", text)
        self.assertIn("--r 13", text)
        self.assertIn("require_residual_h55_2regular == true", text)
        self.assertIn("require_residual_h55_c4 == false", text)
        self.assertIn("target_certificate_exists=false", text)
        self.assertIn("nonexistence_claimed=false", text)
        self.assertIn("direct-open", text)
        self.assertIn("not authorization to start", text)
        self.assertIn("direct_block_handoff_gate.py", text)
        self.assertIn("direct_handoff_31_ledger.json", text)
        self.assertIn("MANIFEST_COMPLETE", text)
        start_marker = 'python3 - "$LOG_DIR/direct_handoff_31_input.json" <<\'PY\'\n'
        start = text.index(start_marker) + len(start_marker)
        end = text.index("\nPY\n  python3", start)
        ast.parse(text[start:end])


if __name__ == "__main__":
    unittest.main()
