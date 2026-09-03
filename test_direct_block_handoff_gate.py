#!/usr/bin/env python3
"""Controls for the direct open Boolean source-handoff boundary."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import blocks
import direct_block_handoff_gate as handoff
import exact_map_postprocess as post


ROOT = Path(__file__).resolve().parent


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _source() -> dict[str, str]:
    return {
        "commit": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip(),
        "tree": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD^{tree}"], text=True).strip(),
    }


def _known_direct_record() -> dict[str, object]:
    historical = json.loads((ROOT / "results" / "blocks" / "A21.json").read_text(encoding="utf-8"))
    rotation = blocks.rotation_from_certificate({"format": blocks.APG_FORMAT, "vertices": historical["vertices"]})
    return {
        "format": "apg-exact-map-bool-sat-v1", "lane": "block", "order": 21, "r": 10,
        "disposition": "CANDIDATE", "canonical": True, "require_t0": True,
        "require_cap_fans": False, "require_residual_h55_2regular": False,
        "require_residual_h55_c4": False, "certificate": blocks.rotation_to_certificate(rotation),
    }


class DirectBlockHandoffGateTests(unittest.TestCase):
    def _artifacts(self, root: Path) -> tuple[Path, Path]:
        raw, postprocess = root / "raw.json", root / "postprocess.json"
        _write(raw, _known_direct_record())
        result = post.postprocess_record(raw, postprocess, expected_order=21, expected_block_t=0)
        self.assertEqual(result["disposition"], "CERTIFIED")
        return raw, postprocess

    def _manifest(self, root: Path, raw: Path, postprocess: Path) -> Path:
        path = root / "handoff-input.json"
        _write(path, {"format": handoff.INPUT_FORMAT, "source": _source(), "profiles": {"21": {"raw_record": raw.name, "postprocess_record": postprocess.name}}})
        return path

    def test_certified_direct_control_emits_portable_source_bound_ledger(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-direct-handoff-positive-") as temp:
            root = Path(temp).resolve()
            raw, postprocess = self._artifacts(root)
            result = handoff.audit_handoff_input(self._manifest(root, raw, postprocess), root / "ledger.json", expected_profiles={21: 10})
            self.assertEqual(result["disposition"], "ELIGIBLE")
            self.assertTrue(result["block_input_eligible"])
            self.assertFalse(result["target_certificate_exists"])
            entry = result["blocks"]["21"]
            strict = root / entry["strict_block_path"]
            self.assertTrue(strict.is_file())
            self.assertEqual(entry["strict_block_sha256"], hashlib.sha256(strict.read_bytes()).hexdigest())
            self.assertEqual(len(entry["fresh_closure_checker_runs"]), 9)
            self.assertTrue(all(item["passed"] for item in entry["fresh_closure_checker_runs"]))

    def test_raw_change_cannot_reuse_certified_postprocess(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-direct-handoff-tamper-") as temp:
            root = Path(temp).resolve()
            raw, postprocess = self._artifacts(root)
            source = self._manifest(root, raw, postprocess)
            record = json.loads(raw.read_text(encoding="utf-8"))
            record["r"] = 11
            _write(raw, record)
            output = root / "ledger.json"
            with self.assertRaisesRegex(handoff.HandoffError, "raw profile mismatches"):
                handoff.audit_handoff_input(source, output, expected_profiles={21: 10})
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["disposition"], "INCOMPLETE")

    def test_direct_route_rejects_cap_claim_and_mismatched_closure(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-direct-handoff-route-") as temp:
            root = Path(temp).resolve()
            raw, postprocess = self._artifacts(root)
            source = self._manifest(root, raw, postprocess)
            record = json.loads(raw.read_text(encoding="utf-8"))
            record["require_cap_fans"] = True
            _write(raw, record)
            with self.assertRaisesRegex(handoff.HandoffError, "must not claim cap-fan provenance"):
                handoff.audit_handoff_input(source, root / "ledger.json", expected_profiles={21: 10})

            raw, postprocess = self._artifacts(root)
            source = self._manifest(root, raw, postprocess)
            audit = json.loads(postprocess.read_text(encoding="utf-8"))
            audit["closures"][0]["sha256"] = "0" * 64
            _write(postprocess, audit)
            with self.assertRaisesRegex(handoff.HandoffError, "closure bytes do not match fresh reconstruction"):
                handoff.audit_handoff_input(source, root / "ledger.json", expected_profiles={21: 10})

    def test_manifest_source_and_paths_are_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-direct-handoff-source-") as temp:
            root = Path(temp).resolve()
            raw, postprocess = self._artifacts(root)
            source = self._manifest(root, raw, postprocess)
            data = json.loads(source.read_text(encoding="utf-8"))
            data["source"]["tree"] = "0" * 40
            _write(source, data)
            with self.assertRaisesRegex(handoff.HandoffError, "does not match the audited checkout"):
                handoff.audit_handoff_input(source, root / "ledger.json", expected_profiles={21: 10})
            data["source"] = _source()
            data["profiles"]["21"]["raw_record"] = "../raw.json"
            _write(source, data)
            with self.assertRaisesRegex(handoff.HandoffError, "escapes the input artifact package"):
                handoff.audit_handoff_input(source, root / "ledger.json", expected_profiles={21: 10})


if __name__ == "__main__":
    unittest.main()
