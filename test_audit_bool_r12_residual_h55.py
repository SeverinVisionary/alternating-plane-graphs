#!/usr/bin/env python3
"""Regression controls for the residual-H55 r=12 Cloud intake auditor."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import audit_bool_r12_residual_h55 as intake
import blocks
import exact_map_postprocess as post


ROOT = Path(__file__).resolve().parent
COMMIT = "a" * 40
TREE = "b" * 40


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _direct_a21() -> dict[str, object]:
    historical = json.loads((ROOT / "results" / "blocks" / "A21.json").read_text(encoding="utf-8"))
    rotation = blocks.rotation_from_certificate({"format": blocks.APG_FORMAT, "vertices": historical["vertices"]})
    return {"format": "apg-exact-map-bool-sat-v1", "lane": "block", "order": 21, "r": 10, "disposition": "CANDIDATE", "canonical": True, "require_t0": True, "require_residual_h55_2regular": False, "require_residual_h55_c4": False, "certificate": blocks.rotation_to_certificate(rotation)}


class ResidualH55IntakeTests(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        log = root / "log"
        log.mkdir(parents=True)
        certificate = json.loads((ROOT / "certificates" / "known" / "order20.json").read_text(encoding="utf-8"))
        _write(log / "bool_known_order20.json", {"disposition": "CANDIDATE", "require_residual_h55_2regular": False, "require_residual_h55_c4": False, "certificate": certificate})
        raw_a21 = log / "bool_known_A21.json"
        _write(raw_a21, _direct_a21())
        result = post.postprocess_record(raw_a21, log / "bool_known_A21_postprocess.json", expected_order=21, expected_block_t=0)
        self.assertEqual(result["disposition"], "CERTIFIED")
        for order in intake.TARGETS:
            _write(log / f"bool_r12_h55_b_{order}_r12_t0_seed0.json", {"format": "apg-exact-map-bool-sat-v1", "lane": "block", "order": order, "r": 12, "disposition": "INCOMPLETE", "z3_result": "unknown", "canonical": True, "require_t0": True, "require_residual_h55_2regular": True, "require_residual_h55_c4": True})
        (log / "environment_source_gate.log").write_text(f"Linux cloud\ngit fsck --full\nHEAD {COMMIT}\ntree {TREE}\n", encoding="utf-8")
        rows = []
        for path in sorted(item for item in log.rglob("*") if item.is_file()):
            if path.name == "SHA256SUMS":
                continue
            rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(log).as_posix()}")
        (log / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")
        return log

    def test_complete_unknown_bundle_is_validated_without_a_nonexistence_claim(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-r12-intake-") as name:
            log = self._fixture(Path(name))
            result = intake.audit(log, log / "intake.json", source_commit=COMMIT, source_tree=TREE)
            self.assertEqual(result["disposition"], "VALIDATED_INCOMPLETE")
            self.assertEqual(result["block_certificate_count"], 0)
            self.assertFalse(result["target_certificate_exists"])
            self.assertFalse(result["nonexistence_claimed"])
            self.assertTrue(result["controls"]["20"]["passed"])
            self.assertTrue(result["controls"]["21"]["passed"])
            self.assertNotIn(str(Path.home()), (log / "intake.json").read_text(encoding="utf-8"))
            self.assertNotIn("/tmp/", (log / "intake.json").read_text(encoding="utf-8"))

    def test_tampered_manifest_and_missing_positive_postprocess_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-r12-intake-tamper-") as name:
            log = self._fixture(Path(name))
            raw = log / "bool_r12_h55_b_28_r12_t0_seed0.json"
            raw.write_text(raw.read_text(encoding="utf-8") + " ", encoding="utf-8")
            with self.assertRaisesRegex(intake.AuditError, "SHA256SUMS mismatch"):
                intake.audit(log, log / "intake.json", source_commit=COMMIT, source_tree=TREE)
            persisted = json.loads((log / "intake.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted["disposition"], "INVALID")

            log = self._fixture(Path(name) / "second")
            target = json.loads((log / "bool_r12_h55_b_28_r12_t0_seed0.json").read_text(encoding="utf-8"))
            target["disposition"] = "CANDIDATE"
            target["certificate"] = _direct_a21()["certificate"]
            _write(log / "bool_r12_h55_b_28_r12_t0_seed0.json", target)
            rows = []
            for path in sorted(item for item in log.rglob("*") if item.is_file() and item.name not in {"SHA256SUMS", "intake.json"}):
                rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(log).as_posix()}")
            (log / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(intake.AuditError, "not listed in SHA256SUMS"):
                intake.audit(log, log / "intake.json", source_commit=COMMIT, source_tree=TREE)

    def test_source_gate_is_required(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-r12-intake-source-") as name:
            log = self._fixture(Path(name))
            (log / "environment_source_gate.log").write_text("Linux\ngit fsck --full\n", encoding="utf-8")
            rows = []
            for path in sorted(item for item in log.rglob("*") if item.is_file() and item.name != "SHA256SUMS"):
                rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(log).as_posix()}")
            (log / "SHA256SUMS").write_text("\n".join(rows) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(intake.AuditError, "environment/source gate"):
                intake.audit(log, log / "intake.json", source_commit=COMMIT, source_tree=TREE)

    def test_required_raw_record_cannot_be_added_outside_the_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-r12-intake-unlisted-") as name:
            log = self._fixture(Path(name))
            manifest = log / "SHA256SUMS"
            manifest.write_text(
                "\n".join(
                    row for row in manifest.read_text(encoding="utf-8").splitlines()
                    if "bool_r12_h55_b_31_r12_t0_seed0.json" not in row
                ) + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(intake.AuditError, "not listed in SHA256SUMS"):
                intake.audit(log, log / "intake.json", source_commit=COMMIT, source_tree=TREE)


if __name__ == "__main__":
    unittest.main()
