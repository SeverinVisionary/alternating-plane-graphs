#!/usr/bin/env python3
"""Tests for the standalone dart-permutation APG checker."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import verify_darts


ROOT = Path(__file__).resolve().parent
KNOWN = ROOT / "certificates" / "known"
CONTROLS = ROOT / "results" / "controls"
DARTS = ROOT / "verify_darts.py"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class DartPermutationTests(unittest.TestCase):
    def test_known_and_composed_controls_pass_without_repo_verifier(self) -> None:
        paths = {
            KNOWN / "schneider17.json": 17,
            KNOWN / "ghent17.json": 17,
            KNOWN / "order20.json": 20,
            KNOWN / "order42.json": 42,
            CONTROLS / "order21.json": 21,
            CONTROLS / "order24.json": 24,
            CONTROLS / "pairs" / "AD_42.json": 42,
            CONTROLS / "pairs" / "DD_45.json": 45,
        }
        for path, expected_order in paths.items():
            with self.subTest(path=path.name):
                summary = verify_darts.check(_load(path))
                self.assertEqual(summary.order, expected_order)
                self.assertEqual(summary.edges, 2 * summary.order - 2)
                self.assertEqual(summary.faces, summary.order)

    def test_reversed_turn_convention_agrees_on_face_invariants(self) -> None:
        source = _load(KNOWN / "order20.json")
        summary = verify_darts.check(source, expected_order=20)
        self.assertEqual(summary.vertex_counts, summary.face_counts)
        self.assertEqual(summary.vertex_counts[5], summary.vertex_counts[3] - 4)

    def test_mutated_rotation_is_rejected(self) -> None:
        source = _load(KNOWN / "order20.json")
        mutated = copy.deepcopy(source)
        neighbors = mutated["vertices"][0]["clockwise"]  # type: ignore[index]
        neighbors[1], neighbors[2] = neighbors[2], neighbors[1]
        with self.assertRaises(verify_darts.DartCheckError):
            verify_darts.check(mutated)

    def test_cli_is_standalone_and_accepts_multiple_files(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(DARTS),
                str(KNOWN / "order20.json"),
                str(KNOWN / "order42.json"),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("order=20", result.stdout)
        self.assertIn("order=42", result.stdout)
        self.assertEqual(result.stderr, "")

    def test_cli_rejects_wrong_expected_order(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-dart-test-") as temp_dir:
            path = Path(temp_dir) / "order20.json"
            path.write_text(
                json.dumps(_load(KNOWN / "order20.json")), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, str(DARTS), str(path), "--expect-order", "21"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("does not equal expected order 21", result.stderr)

    def test_cli_rejects_duplicate_json_members(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-dart-duplicate-json-") as temp_dir:
            path = Path(temp_dir) / "order20.json"
            encoded = (KNOWN / "order20.json").read_text(encoding="utf-8")
            needle = '  "format": "apg-plane-rotation-v1",'
            self.assertEqual(encoded.count(needle), 1)
            path.write_text(
                encoded.replace(
                    needle,
                    '  "format": "ambiguous",\n  "format": "apg-plane-rotation-v1",',
                    1,
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(DARTS), str(path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("duplicate JSON object key", result.stderr)


if __name__ == "__main__":
    unittest.main()
