#!/usr/bin/env python3
"""Keep the executable all-26 cloud promotion handoff documentation runnable."""

from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
JOB = ROOT / "CLOUD_TARGET_PROMOTION_JOB.md"
TEMPLATE = ROOT / "promotion_handoff_input.template.json"


class CloudTargetPromotionJobTests(unittest.TestCase):
    def test_handoff_template_freezes_the_exact_boolean_profiles_and_paths(self) -> None:
        value = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual(value["format"], "apg-boolean-block-handoff-input-v1")
        self.assertEqual(sorted(map(int, value["profiles"])), [28, 29, 31])
        for order in (28, 29, 31):
            self.assertEqual(
                value["profiles"][str(order)],
                {
                    "raw_record": f"inputs/{order}/raw.json",
                    "postprocess_record": f"inputs/{order}/postprocess.json",
                    "opened_block": f"inputs/{order}/opened_block.json",
                },
            )

    def test_documented_final_exact_26_assertion_is_valid_python(self) -> None:
        text = JOB.read_text(encoding="utf-8")
        start_marker = "python3 - \"$PROMOTION_DIR\" <<'PY'\n"
        start = text.index(start_marker) + len(start_marker)
        end = text.index("\nPY\n```", start)
        snippet = text[start:end]
        ast.parse(snippet)
        self.assertIn("CERTIFIED_26_TARGETS", snippet)
        self.assertIn("COMPLETE: 26/26 independently verified", snippet)
        self.assertIn("promotion_handoff_gate.py", text)
        self.assertIn("compose_target_witnesses.py", text)
        self.assertIn("finalize_target_promotion.py", text)
        self.assertIn("cmp -s", text)
        self.assertIn("dispatch_metadata.json", text)


if __name__ == "__main__":
    unittest.main()
