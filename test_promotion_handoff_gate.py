#!/usr/bin/env python3
"""Controls for the raw/postprocess/opened-block promotion handoff."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import blocks
import exact_map_postprocess as post
import promotion_handoff_gate as handoff
from boolean_socket_canonical import canonical_closed_cap_fans, canonicalize_closed_cap_rotation


ROOT = Path(__file__).resolve().parent


def _known_closed_cap_record() -> dict[str, object]:
    data = json.loads((ROOT / "results" / "blocks" / "A21.json").read_text(encoding="utf-8"))
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
    fans = canonical_closed_cap_fans([len(canonical[vertex]) for vertex in range(len(canonical))])
    return {
        "format": "apg-exact-map-bool-sat-v1",
        "lane": "closed",
        "order": 21,
        "r": 10,
        "disposition": "CANDIDATE",
        "canonical": True,
        "require_cap_fans": True,
        "require_t0": True,
        "cap_fans": [
            {"center": center, "leaves": list(leaves)} for center, leaves in fans
        ],
        "certificate": blocks.rotation_to_certificate(canonical),
    }


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class PromotionHandoffGateTests(unittest.TestCase):
    def _control_artifacts(self, root: Path) -> tuple[Path, Path, Path]:
        raw_path = root / "raw.json"
        post_path = root / "postprocess.json"
        _write(raw_path, _known_closed_cap_record())
        result = post.postprocess_record(
            raw_path,
            post_path,
            expected_order=21,
            expected_block_t=0,
        )
        self.assertEqual(result["disposition"], "CERTIFIED")
        return raw_path, post_path, Path(result["opened_block"]["path"])  # type: ignore[index]

    def _input_manifest(self, root: Path, raw: Path, postprocess: Path, opened: Path) -> Path:
        input_path = root / "handoff-input.json"
        _write(
            input_path,
            {
                "format": handoff.INPUT_FORMAT,
                "profiles": {
                    "21": {
                        "raw_record": raw.relative_to(root).as_posix(),
                        "postprocess_record": postprocess.relative_to(root).as_posix(),
                        "opened_block": opened.relative_to(root).as_posix(),
                    }
                },
            },
        )
        return input_path

    def test_certified_cap_route_emits_portable_source_bound_ledger(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-handoff-positive-") as temporary:
            root = Path(temporary).resolve()
            raw, postprocess, opened = self._control_artifacts(root)
            source = self._input_manifest(root, raw, postprocess, opened)
            output = root / "handoff-ledger.json"
            result = handoff.audit_handoff_input(
                source, output, expected_profiles={21: 10}
            )
            self.assertEqual(result["disposition"], "ELIGIBLE")
            self.assertTrue(result["block_input_eligible"])
            self.assertFalse(result["target_certificate_exists"])
            self.assertFalse(result["nonexistence_claimed"])
            persisted = json.loads(output.read_text(encoding="utf-8"))
            entry = persisted["blocks"]["21"]
            self.assertEqual(entry["order"], 21)
            self.assertEqual(entry["r"], 10)
            self.assertEqual(
                entry["raw_record_sha256"], hashlib.sha256(raw.read_bytes()).hexdigest()
            )
            self.assertEqual(
                entry["postprocess_sha256"], hashlib.sha256(postprocess.read_bytes()).hexdigest()
            )
            self.assertEqual(
                entry["opened_block_sha256"], hashlib.sha256(opened.read_bytes()).hexdigest()
            )
            self.assertTrue(entry["closures_passed"])
            self.assertEqual(
                sorted(map(int, persisted["published_blocks"])), [21, 22, 23, 24]
            )
            for order, entry in persisted["published_blocks"].items():
                certificate = root / entry["opened_block_path"]
                self.assertTrue(certificate.is_file())
                self.assertEqual(
                    entry["opened_block_sha256"],
                    hashlib.sha256(certificate.read_bytes()).hexdigest(),
                )
                self.assertEqual(len(blocks.rotation_from_certificate(json.loads(certificate.read_text()))), int(order))

    def test_changed_raw_record_cannot_reuse_a_certified_postprocess(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-handoff-tamper-") as temporary:
            root = Path(temporary).resolve()
            raw, postprocess, opened = self._control_artifacts(root)
            source = self._input_manifest(root, raw, postprocess, opened)
            changed = json.loads(raw.read_text(encoding="utf-8"))
            changed["r"] = 999
            _write(raw, changed)
            output = root / "handoff-ledger.json"
            with self.assertRaisesRegex(handoff.HandoffError, "raw r mismatches"):
                handoff.audit_handoff_input(source, output, expected_profiles={21: 10})
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(persisted["disposition"], "INCOMPLETE")
            self.assertFalse(persisted["block_input_eligible"])
            self.assertFalse(output.with_name("MANIFEST_COMPLETE").exists())

    def test_opened_block_path_must_stay_inside_the_portable_artifact_package(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-handoff-path-") as temporary:
            root = Path(temporary).resolve()
            raw, postprocess, opened = self._control_artifacts(root)
            source = self._input_manifest(root, raw, postprocess, opened)
            data = json.loads(source.read_text(encoding="utf-8"))
            data["profiles"]["21"]["opened_block"] = "../outside.json"
            _write(source, data)
            output = root / "handoff-ledger.json"
            with self.assertRaisesRegex(handoff.HandoffError, "escapes the input artifact package"):
                handoff.audit_handoff_input(source, output, expected_profiles={21: 10})
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(persisted["disposition"], "INCOMPLETE")

    def test_spoofed_same_order_strict_block_cannot_replace_raw_cap_reopening(self) -> None:
        # A postprocessor JSON file alone is not authoritative.  Even if an
        # attacker updates its advertised opened-block digest, the handoff must
        # derive the exact opening from the raw marked fans and reject a
        # reflected (still strict, still same-order) substitute.
        with tempfile.TemporaryDirectory(prefix="apg-handoff-opening-link-") as temporary:
            root = Path(temporary).resolve()
            raw, postprocess, opened = self._control_artifacts(root)
            original = blocks.rotation_from_certificate(
                json.loads(opened.read_text(encoding="utf-8"))
            )
            replacement = root / "mirror-opened.json"
            _write(replacement, blocks.rotation_to_certificate(blocks.mirror_rotation(original)))
            self.assertNotEqual(replacement.read_bytes(), opened.read_bytes())
            spoofed_postprocess = json.loads(postprocess.read_text(encoding="utf-8"))
            spoofed_postprocess["opened_block"]["sha256"] = hashlib.sha256(
                replacement.read_bytes()
            ).hexdigest()
            _write(postprocess, spoofed_postprocess)
            source = self._input_manifest(root, raw, postprocess, replacement)
            output = root / "handoff-ledger.json"
            with self.assertRaisesRegex(
                handoff.HandoffError, "does not equal the raw cap reopening"
            ):
                handoff.audit_handoff_input(source, output, expected_profiles={21: 10})
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(persisted["disposition"], "INCOMPLETE")

    def test_malformed_but_reopenable_raw_candidate_fails_fresh_dual_check(self) -> None:
        # A cap reopening by itself is not enough: cyclic placement of a cap
        # edge can make the closed rotation non-spherical while deleting that
        # edge still recovers the same strict block.  Forge the otherwise
        # self-consistent postprocess hashes to exercise the source gate's own
        # fresh closed-APG verifier boundary.
        with tempfile.TemporaryDirectory(prefix="apg-handoff-raw-check-") as temporary:
            root = Path(temporary).resolve()
            raw_path, postprocess_path, opened = self._control_artifacts(root)
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            rotation = blocks.rotation_from_certificate(raw["certificate"])
            mutable = {vertex: list(neighbors) for vertex, neighbors in rotation.items()}
            mutable[0].remove(10)
            mutable[0].insert(1, 10)
            raw["certificate"] = blocks.rotation_to_certificate(
                blocks.normalize_rotation(mutable)
            )
            _write(raw_path, raw)
            postprocess = json.loads(postprocess_path.read_text(encoding="utf-8"))
            postprocess["source_record_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            postprocess["candidate"]["sha256"] = hashlib.sha256(
                json.dumps(raw["certificate"], indent=2, sort_keys=True).encode("utf-8")
                + b"\n"
            ).hexdigest()
            _write(postprocess_path, postprocess)
            source = self._input_manifest(root, raw_path, postprocess_path, opened)
            output = root / "handoff-ledger.json"
            with self.assertRaisesRegex(
                handoff.HandoffError, "raw closed candidate failed an independent checker"
            ):
                handoff.audit_handoff_input(source, output, expected_profiles={21: 10})
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(persisted["disposition"], "INCOMPLETE")

    def test_noncanonical_raw_rotation_cannot_normalize_its_way_through_source_gate(self) -> None:
        # Preserve the same abstract cap opening but rotate one raw clockwise
        # list away from the canonical smallest-neighbour convention.  The
        # postprocess candidate hash still binds the normalized rotation, so
        # this specifically proves the source gate checks the retained raw
        # certificate rather than silently checking a normalized substitute.
        with tempfile.TemporaryDirectory(prefix="apg-handoff-noncanonical-") as temporary:
            root = Path(temporary).resolve()
            raw_path, postprocess_path, opened = self._control_artifacts(root)
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            rows = raw["certificate"]["vertices"]
            row_zero = next(row for row in rows if row["id"] == 0)
            self.assertEqual(row_zero["clockwise"], [10, 15, 16])
            row_zero["clockwise"] = [15, 16, 10]
            _write(raw_path, raw)
            postprocess = json.loads(postprocess_path.read_text(encoding="utf-8"))
            postprocess["source_record_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
            _write(postprocess_path, postprocess)
            source = self._input_manifest(root, raw_path, postprocess_path, opened)
            output = root / "handoff-ledger.json"
            with self.assertRaisesRegex(
                handoff.HandoffError, "raw closed candidate failed an independent checker"
            ):
                handoff.audit_handoff_input(source, output, expected_profiles={21: 10})
            persisted = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(persisted["disposition"], "INCOMPLETE")

    def test_duplicate_raw_json_keys_cannot_enter_the_source_handoff(self) -> None:
        # A plain Python JSON decoder silently keeps the last duplicate member.
        # The raw evidence boundary must reject both a duplicate top-level
        # certificate and a nested duplicate rotation list before it can
        # normalize either spelling into an apparent checker-passing witness.
        with tempfile.TemporaryDirectory(prefix="apg-handoff-duplicate-json-") as temporary:
            root = Path(temporary).resolve()
            for label, needle, replacement in (
                (
                    "certificate",
                    '  "certificate": ',
                    '  "certificate": {"format": "ambiguous"},\n  "certificate": ',
                ),
                (
                    "clockwise",
                    '      "clockwise": [',
                    '      "clockwise": [],\n      "clockwise": [',
                ),
            ):
                with self.subTest(member=label):
                    raw_path, postprocess_path, opened = self._control_artifacts(root)
                    raw_text = raw_path.read_text(encoding="utf-8")
                    self.assertEqual(raw_text.count(needle), 1 if label == "certificate" else 21)
                    raw_path.write_text(
                        raw_text.replace(needle, replacement, 1), encoding="utf-8"
                    )
                    source = self._input_manifest(root, raw_path, postprocess_path, opened)
                    output = root / "handoff-ledger.json"
                    with self.assertRaisesRegex(
                        handoff.HandoffError, r"duplicate JSON object key",
                    ):
                        handoff.audit_handoff_input(
                            source, output, expected_profiles={21: 10}
                        )
                    persisted = json.loads(output.read_text(encoding="utf-8"))
                    self.assertEqual(persisted["disposition"], "INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
