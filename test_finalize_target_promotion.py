#!/usr/bin/env python3
"""Controls for the separate promotion-package final audit."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import blocks
import compose_target_witnesses as promotion
import finalize_target_promotion as finalizer


ROOT = Path(__file__).resolve().parent


def _published_open_block(root: Path, name: str, order: int) -> Path:
    historical = json.loads(
        (ROOT / "results" / "blocks" / f"{name}.json").read_text(encoding="utf-8")
    )
    rotation = blocks.rotation_from_certificate(
        {"format": blocks.APG_FORMAT, "vertices": historical["vertices"]}
    )
    blocks.validate_block(rotation)
    path = root / f"strict_block_{order}.json"
    path.write_text(
        json.dumps(blocks.rotation_to_certificate(rotation), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


class FinalizeTargetPromotionTests(unittest.TestCase):
    def _control_package(self, root: Path) -> tuple[Path, dict[int, tuple[int, ...]]]:
        sources = {21: _published_open_block(root, "A21", 21)}
        representations = {39: (21, 21)}
        package = root / "promotion"
        promotion.promote_target_witnesses(sources, package, representations=representations)
        return package, representations

    def test_bounded_control_replays_everything_but_never_writes_completion_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-final-audit-control-") as temporary:
            root = Path(temporary).resolve()
            package, representations = self._control_package(root)
            result = finalizer.audit_promotion_package(
                package, representations=representations
            )
            self.assertEqual(result["disposition"], "CERTIFIED_CONTROL_ONLY")
            self.assertEqual(result["target_certificate_count"], 1)
            self.assertTrue(result["target_audits"][0]["passed"])  # type: ignore[index]
            self.assertTrue((package / finalizer.FINAL_AUDIT_NAME).is_file())
            self.assertFalse((package / finalizer.COMPLETE_MARKER).exists())

    def test_tampered_certificate_fails_before_any_completion_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-final-audit-tamper-") as temporary:
            root = Path(temporary).resolve()
            package, representations = self._control_package(root)
            certificate = package / "certificates" / "apg_39.json"
            certificate.write_bytes(certificate.read_bytes() + b"\n")
            with self.assertRaisesRegex(finalizer.FinalAuditError, "SHA-256 mismatch"):
                finalizer.audit_promotion_package(package, representations=representations)
            audit = json.loads((package / finalizer.FINAL_AUDIT_NAME).read_text(encoding="utf-8"))
            self.assertEqual(audit["disposition"], "INCOMPLETE")
            self.assertFalse((package / finalizer.COMPLETE_MARKER).exists())

    def test_existing_completion_marker_is_never_reblessed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-final-audit-stale-") as temporary:
            root = Path(temporary).resolve()
            package, representations = self._control_package(root)
            (package / finalizer.COMPLETE_MARKER).write_text("stale\n", encoding="utf-8")
            with self.assertRaisesRegex(finalizer.FinalAuditError, "already exists"):
                finalizer.audit_promotion_package(package, representations=representations)
            audit = json.loads((package / finalizer.FINAL_AUDIT_NAME).read_text(encoding="utf-8"))
            self.assertEqual(audit["disposition"], "INCOMPLETE")

    def test_final_audit_refuses_an_output_path_that_could_overwrite_package_evidence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-final-audit-path-") as temporary:
            root = Path(temporary).resolve()
            package, representations = self._control_package(root)
            manifest = package / promotion.MANIFEST_NAME
            original = manifest.read_bytes()
            with self.assertRaisesRegex(finalizer.FinalAuditError, "fixed to the new package-relative"):
                finalizer.audit_promotion_package(
                    package,
                    representations=representations,
                    output=manifest,
                )
            self.assertEqual(manifest.read_bytes(), original)
            self.assertFalse((package / finalizer.COMPLETE_MARKER).exists())

    def test_final_audit_binds_the_selected_trace_to_the_frozen_chain(self) -> None:
        # (21, 24) and (22, 23) both have Section-8 order 42 and the same
        # r/t profile.  A forged package could otherwise retain the former in
        # ``block_chain``/``arithmetic_chain`` while replacing its valid
        # certificate and selected trace with the latter.  This is not a false
        # APG, but it is false frozen-chain provenance and must not be promoted.
        with tempfile.TemporaryDirectory(prefix="apg-final-audit-trace-chain-") as temporary:
            root = Path(temporary).resolve()
            sources = {
                order: _published_open_block(root, name, order)
                for order, name in ((21, "A21"), (22, "B22"), (23, "C23"), (24, "D24"))
            }
            frozen = {40: (21, 22), 41: (21, 23), 42: (21, 24), 43: (22, 24)}
            package = root / "promotion"
            promotion.promote_target_witnesses(sources, package, representations=frozen)

            alternate = root / "alternate"
            promotion.promote_target_witnesses(
                sources, alternate, representations={42: (22, 23)}
            )
            primary_manifest_path = package / promotion.MANIFEST_NAME
            primary_manifest = json.loads(primary_manifest_path.read_text(encoding="utf-8"))
            alternate_manifest = json.loads(
                (alternate / promotion.MANIFEST_NAME).read_text(encoding="utf-8")
            )
            primary_target = next(
                entry for entry in primary_manifest["targets"] if entry["order"] == 42
            )
            alternate_target = next(
                entry for entry in alternate_manifest["targets"] if entry["order"] == 42
            )
            self.assertEqual(primary_target["expected_profile"], alternate_target["expected_profile"])
            self.assertEqual(primary_target["observed_profile"], alternate_target["observed_profile"])
            self.assertEqual(
                alternate_target["composition"]["selected_trace"]["block_order_sequence"],
                [22, 23],
            )

            # Copy every fresh-checker-backed alternate target artifact, then
            # forge only its chain labels.  Old finalization accepted this
            # equal-order/profile substitution; the trace binding must reject
            # it before replaying a certificate into the frozen package.
            for field in ("certificate_path", "checks_path"):
                relative = alternate_target[field]
                (package / relative).write_bytes((alternate / relative).read_bytes())
            forged = json.loads(json.dumps(alternate_target))
            forged["block_chain"] = [21, 24]
            forged["composition"]["arithmetic_chain"] = [21, 24]
            index = primary_manifest["targets"].index(primary_target)
            primary_manifest["targets"][index] = forged
            primary_manifest_path.write_text(
                json.dumps(primary_manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                finalizer.FinalAuditError,
                r"trace block-order sequence differs from frozen arithmetic",
            ):
                finalizer.audit_promotion_package(package, representations=frozen)
            audit = json.loads((package / finalizer.FINAL_AUDIT_NAME).read_text(encoding="utf-8"))
            self.assertEqual(audit["disposition"], "INCOMPLETE")
            self.assertFalse((package / finalizer.COMPLETE_MARKER).exists())
