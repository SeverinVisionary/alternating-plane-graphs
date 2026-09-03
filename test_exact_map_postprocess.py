#!/usr/bin/env python3
"""Regression gates for the exact-map candidate boundary."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import blocks
import exact_map_postprocess as post
from boolean_socket_canonical import (
    canonical_closed_cap_fans,
    canonicalize_closed_cap_rotation,
)


ROOT = Path(__file__).resolve().parent


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _known_closed_cap_record() -> dict[str, object]:
    """Build the dynamic A21 marked-cap positive control record."""

    data = _read(ROOT / "results" / "blocks" / "A21.json")
    rotation = blocks.rotation_from_certificate(
        {"format": blocks.APG_FORMAT, "vertices": data["vertices"]}
    )
    sockets = blocks.validate_block(rotation)
    source_fans = tuple(
        blocks.ClosureFan(
            hub=sorted(socket.whites)[0],
            leaves=tuple(sorted(socket.whites)[1:]),
        )
        for socket in sockets
    )
    closed = blocks.close_block_with_hubs(blocks.Block(rotation, sockets), (0, 0))
    canonical = canonicalize_closed_cap_rotation(closed, source_fans)
    degrees = [len(canonical[vertex]) for vertex in range(len(canonical))]
    fans = canonical_closed_cap_fans(degrees)
    return {
        "format": "apg-exact-map-bool-sat-v1",
        "lane": "closed",
        "r": 10,
        "disposition": "CANDIDATE",
        "require_cap_fans": True,
        "require_t0": True,
        "cap_fans": [
            {"center": hub, "leaves": list(leaves)} for hub, leaves in fans
        ],
        "certificate": blocks.rotation_to_certificate(canonical),
    }


class ExactMapPostprocessTests(unittest.TestCase):
    def _run(
        self,
        record: dict[str, object],
        *,
        expected_order: int | None = None,
        expected_block_t: int | None = None,
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory(prefix="apg-exact-postprocess-") as directory:
            root = Path(directory)
            record_path = root / "solver.json"
            output_path = root / "postprocess.json"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            return post.postprocess_record(
                record_path,
                output_path,
                expected_order=expected_order,
                expected_block_t=expected_block_t,
            )

    def test_non_candidate_is_never_promoted(self) -> None:
        result = self._run(
            {
                "format": "apg-exact-map-sat-v1",
                "lane": "closed",
                "r": 16,
                "disposition": "INCOMPLETE",
                "z3_result": "unknown",
            }
        )
        self.assertEqual(result["disposition"], "INCOMPLETE")
        self.assertNotIn("checker_runs", result)

    def test_known_closed_control_passes_both_checkers(self) -> None:
        certificate = _read(ROOT / "certificates" / "known" / "order20.json")
        result = self._run(
            {
                "format": "apg-exact-map-sat-v1",
                "lane": "closed",
                "r": 9,
                "disposition": "CANDIDATE",
                "certificate": certificate,
            },
            expected_order=20,
        )
        self.assertEqual(result["disposition"], "CERTIFIED")
        self.assertEqual(
            [item["passed"] for item in result["checker_runs"]],  # type: ignore[index]
            [True, True],
        )

    def test_rejects_unmarked_closed_t0_record(self) -> None:
        # ``--require-t0`` is meaningful for a closed map only when two marked
        # cap fans make it a candidate strict block.  A malformed solver record
        # must not bypass reopening and the nine-closure t gate merely because
        # its closed APG certificate is valid.
        certificate = _read(ROOT / "certificates" / "known" / "order20.json")
        with self.assertRaisesRegex(
            ValueError, "require_t0 closed record must mark cap fans"
        ):
            self._run(
                {
                    "format": "apg-exact-map-bool-sat-v1",
                    "lane": "closed",
                    "r": 9,
                    "disposition": "CANDIDATE",
                    "require_t0": True,
                    "certificate": certificate,
                },
                expected_order=20,
            )

    def test_known_block_control_runs_all_nine_closures(self) -> None:
        block = _read(ROOT / "results" / "blocks" / "A21.json")
        certificate = {
            "format": "apg-plane-rotation-v1",
            "vertices": copy.deepcopy(block["vertices"]),
        }
        result = self._run(
            {
                "format": "apg-exact-map-sat-v1",
                "lane": "block",
                "r": 10,
                "disposition": "CANDIDATE",
                "require_t0": True,
                "certificate": certificate,
            },
            expected_order=21,
        )
        self.assertEqual(result["disposition"], "CERTIFIED")
        self.assertEqual(result["closure_count"], 9)
        closures = result["closures"]
        self.assertTrue(all(item["passed"] for item in closures))  # type: ignore[union-attr]
        audit = result["structural_audit"]
        self.assertEqual(audit["status"], "COMPLETED")  # type: ignore[index]
        values = audit["value"]["variants"]  # type: ignore[index]
        self.assertEqual(len(values), 9)
        self.assertTrue(all(item["t_vertex"] == 0 for item in values))
        self.assertEqual(result["expected_block_t"], 0)
        self.assertTrue(result["block_t_gate"]["passed"])  # type: ignore[index]
        self.assertTrue(result["r_gate"]["passed"])  # type: ignore[index]

    def test_known_closed_cap_control_reopens_to_all_nine_strict_closures(self) -> None:
        result = self._run(
            _known_closed_cap_record(),
            expected_order=21,
            expected_block_t=0,
        )
        self.assertEqual(result["disposition"], "CERTIFIED")
        self.assertTrue(result["closed_r_gate"]["passed"])  # type: ignore[index]
        self.assertTrue(result["cap_opening"]["passed"])  # type: ignore[index]
        opened_block = result["opened_block"]
        self.assertEqual(opened_block["order"], 21)  # type: ignore[index]
        self.assertEqual(opened_block["format"], blocks.APG_FORMAT)  # type: ignore[index]
        self.assertEqual(len(opened_block["sha256"]), 64)  # type: ignore[index]
        self.assertEqual(result["closure_count"], 9)
        self.assertTrue(all(item["passed"] for item in result["closures"]))  # type: ignore[union-attr]
        self.assertTrue(result["block_t_gate"]["passed"])  # type: ignore[index]

    def test_cap_postprocessor_exports_a_hashable_strict_open_block(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-cap-export-") as directory:
            root = Path(directory)
            record_path = root / "solver.json"
            output_path = root / "postprocess.json"
            record_path.write_text(
                json.dumps(_known_closed_cap_record()), encoding="utf-8"
            )
            result = post.postprocess_record(
                record_path,
                output_path,
                expected_order=21,
                expected_block_t=0,
            )
            opened = result["opened_block"]
            opened_path = Path(opened["path"])  # type: ignore[index]
            self.assertTrue(opened_path.is_file())
            self.assertEqual(
                opened_path.parent,
                output_path.parent.resolve() / "postprocess_certificates",
            )
            certificate = _read(opened_path)
            rotation = blocks.rotation_from_certificate(certificate)
            sockets = blocks.validate_block(rotation)
            self.assertEqual(len(rotation), 21)
            self.assertEqual(len(sockets), 2)
            self.assertEqual(post._sha256(opened_path), opened["sha256"])  # type: ignore[index]

    def test_incomplete_cap_postprocess_cannot_export_a_reusable_open_block(self) -> None:
        # Regression for the provenance boundary: a closed candidate can
        # reopen successfully yet fail a later t gate.  Such an INCOMPLETE
        # record must not leave an ``opened_block.json`` artifact that a
        # downstream composer could mistake for a certified Boolean result.
        record = _known_closed_cap_record()
        record["require_t0"] = False
        with tempfile.TemporaryDirectory(prefix="apg-cap-incomplete-export-") as directory:
            root = Path(directory).resolve()
            record_path = root / "solver.json"
            output_path = root / "postprocess.json"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            result = post.postprocess_record(
                record_path,
                output_path,
                expected_order=21,
                expected_block_t=1,
            )
            self.assertEqual(result["disposition"], "INCOMPLETE")
            self.assertFalse(result["block_t_gate"]["passed"])  # type: ignore[index]
            self.assertNotIn("opened_block", result)
            self.assertFalse(
                (
                    output_path.parent
                    / "postprocess_certificates"
                    / "opened_block.json"
                ).exists()
            )

    def test_duplicate_raw_solver_record_key_is_rejected_before_normalization(self) -> None:
        # The postprocessor is the first raw-record boundary, so it must not
        # silently choose the last of two ambiguous JSON certificate members.
        with tempfile.TemporaryDirectory(prefix="apg-cap-duplicate-json-") as directory:
            root = Path(directory)
            record_path = root / "solver.json"
            output_path = root / "postprocess.json"
            encoded = json.dumps(_known_closed_cap_record(), indent=2, sort_keys=True)
            needle = '  "certificate": '
            self.assertEqual(encoded.count(needle), 1)
            record_path.write_text(
                encoded.replace(
                    needle,
                    '  "certificate": {"format": "ambiguous"},\n  "certificate": ',
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, r"duplicate JSON object key"):
                post.postprocess_record(
                    record_path,
                    output_path,
                    expected_order=21,
                    expected_block_t=0,
                )
            self.assertFalse(output_path.exists())

    def test_cli_repo_root_relative_paths_preserve_all_checker_certificates(self) -> None:
        # The postprocessor deliberately runs checkers from ROOT.  A cloud job
        # normally invokes it from the repository root with relative result
        # paths, so derived candidate/closure paths must be resolved before the
        # subprocess boundary rather than accidentally interpreted below ROOT.
        block = _read(ROOT / "results" / "blocks" / "A21.json")
        record = {
            "format": "apg-exact-map-sat-v1",
            "lane": "block",
            "r": 10,
            "disposition": "CANDIDATE",
            "require_t0": True,
            "certificate": {
                "format": "apg-plane-rotation-v1",
                "vertices": copy.deepcopy(block["vertices"]),
            },
        }
        repo_root = ROOT.parent.parent
        with tempfile.TemporaryDirectory(prefix="apg-relative-postprocess-", dir=ROOT) as directory:
            root = Path(directory)
            record_path = root / "solver.json"
            output_path = root / "postprocess.json"
            record_path.write_text(json.dumps(record), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "exact_map_postprocess.py"),
                    str(record_path.relative_to(repo_root)),
                    "--expected-order",
                    "21",
                    "--expected-block-t",
                    "0",
                    "--output",
                    str(output_path.relative_to(repo_root)),
                ],
                cwd=repo_root,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            result = _read(output_path)
        self.assertEqual(result["disposition"], "CERTIFIED")
        self.assertEqual(result["closure_count"], 9)
        self.assertTrue(all(item["passed"] for item in result["closures"]))  # type: ignore[index]

    def test_block_t_gate_rejects_a_mismatched_requested_profile(self) -> None:
        block = _read(ROOT / "results" / "blocks" / "A21.json")
        certificate = {
            "format": "apg-plane-rotation-v1",
            "vertices": copy.deepcopy(block["vertices"]),
        }
        result = self._run(
            {
                "format": "apg-exact-map-sat-v1",
                "lane": "block",
                "r": 10,
                "disposition": "CANDIDATE",
                "certificate": certificate,
            },
            expected_order=21,
            expected_block_t=1,
        )
        self.assertEqual(result["disposition"], "INCOMPLETE")
        self.assertFalse(result["block_t_gate"]["passed"])  # type: ignore[index]

    def test_block_r_gate_rejects_a_mislabeled_solver_profile(self) -> None:
        block = _read(ROOT / "results" / "blocks" / "A21.json")
        certificate = {
            "format": "apg-plane-rotation-v1",
            "vertices": copy.deepcopy(block["vertices"]),
        }
        result = self._run(
            {
                "format": "apg-exact-map-sat-v1",
                "lane": "block",
                "r": 12,
                "disposition": "CANDIDATE",
                "certificate": certificate,
            },
            expected_order=21,
        )
        self.assertEqual(result["disposition"], "INCOMPLETE")
        self.assertFalse(result["r_gate"]["passed"])  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
