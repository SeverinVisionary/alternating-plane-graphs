#!/usr/bin/env python3
"""Focused controls for deterministic all-target witness promotion."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import block_arithmetic
import blocks
import compose_target_witnesses as promotion
import exact_map_postprocess as postprocess
import promotion_handoff_gate as handoff
import verify
import verify_darts
from boolean_socket_canonical import canonical_closed_cap_fans, canonicalize_closed_cap_rotation


ROOT = Path(__file__).resolve().parent
PUBLISHED_BLOCKS = ROOT / "results" / "blocks"
COMPOSER = ROOT / "compose_target_witnesses.py"


def _write_published_open_block(temp_dir: Path, name: str, order: int) -> Path:
    """Convert the historical block schema to the exact-map reopened schema."""

    historical = json.loads((PUBLISHED_BLOCKS / f"{name}.json").read_text(encoding="utf-8"))
    rows = historical["vertices"]
    rotation = blocks.normalize_rotation(
        {row["id"]: row["clockwise"] for row in rows}
    )
    # This mirrors the exact-map postprocessor's ``opened_block.json`` output:
    # an APG-format rotation certificate that is a strict open block, not a
    # historical block_tools document and not a closed APG target certificate.
    blocks.validate_block(rotation)
    path = temp_dir / f"opened_block_{order}.json"
    path.write_text(
        json.dumps(blocks.rotation_to_certificate(rotation), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _known_closed_cap_record() -> dict[str, object]:
    """A compact source-gate control using the published A21 strict block."""

    data = json.loads((PUBLISHED_BLOCKS / "A21.json").read_text(encoding="utf-8"))
    rotation = blocks.rotation_from_certificate(
        {"format": blocks.APG_FORMAT, "vertices": data["vertices"]}
    )
    sockets = blocks.validate_block(rotation)
    fans = tuple(
        blocks.ClosureFan(
            hub=sorted(socket.whites)[0], leaves=tuple(sorted(socket.whites)[1:])
        )
        for socket in sockets
    )
    closed = blocks.close_block_with_hubs(blocks.Block(rotation, sockets), (0, 0))
    canonical = canonicalize_closed_cap_rotation(closed, fans)
    degrees = [len(canonical[vertex]) for vertex in range(len(canonical))]
    canonical_fans = canonical_closed_cap_fans(degrees)
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
            {"center": center, "leaves": list(leaves)}
            for center, leaves in canonical_fans
        ],
        "certificate": blocks.rotation_to_certificate(canonical),
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class ComposeTargetWitnessesTests(unittest.TestCase):
    def _published_sources(self, temp_dir: Path) -> dict[int, Path]:
        return {
            21: _write_published_open_block(temp_dir, "A21", 21),
            22: _write_published_open_block(temp_dir, "B22", 22),
            23: _write_published_open_block(temp_dir, "C23", 23),
            24: _write_published_open_block(temp_dir, "D24", 24),
        }

    def test_custom_published_block_control_writes_checked_witnesses(self) -> None:
        # A compact custom map exercises A--D without pretending that the
        # published four blocks cover the open 26-order frontier by themselves.
        representations = {
            39: (21, 21),
            40: (21, 22),
            41: (21, 23),
            42: (21, 24),
            # The production Boolean selector reaches four-block chains; keep
            # one bounded published control at that depth as a composition and
            # reflection-expansion regression gate.
            75: (21, 21, 21, 21),
        }
        with tempfile.TemporaryDirectory(prefix="apg-promotion-test-") as temp_name:
            temp_dir = Path(temp_name)
            sources = self._published_sources(temp_dir)
            output = temp_dir / "promotion"
            manifest = promotion.promote_target_witnesses(
                sources, output, representations=representations
            )

            self.assertEqual(
                manifest["disposition"], "PROMOTED_PENDING_SEPARATE_FINAL_AUDIT"
            )
            self.assertFalse((output / promotion.COMPLETE_MARKER).exists())
            persisted = json.loads((output / promotion.MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual(persisted["targets"], manifest["targets"])
            self.assertEqual(
                [entry["order"] for entry in persisted["targets"]], [39, 40, 41, 42, 75]
            )
            self.assertEqual(persisted["block_t"], {"21": 0, "22": 0, "23": 0, "24": 0})
            self.assertTrue(
                all(
                    entry["portable_t0_audit"]["passed"]
                    and len(entry["closure_checks"]) == 9
                    and all(item["passed"] for item in entry["closure_checks"])
                    for entry in persisted["blocks"].values()
                )
            )

            for entry in persisted["targets"]:
                with self.subTest(order=entry["order"]):
                    certificate_path = output / entry["certificate_path"]
                    checks_path = output / entry["checks_path"]
                    self.assertTrue(certificate_path.is_file())
                    self.assertTrue(checks_path.is_file())
                    certificate = verify.load_certificate(certificate_path)
                    verify.verify_certificate(certificate, expected_order=entry["order"])
                    verify_darts.check(verify_darts.load(certificate_path), expected_order=entry["order"])
                    checks = json.loads(checks_path.read_text(encoding="utf-8"))
                    self.assertTrue(checks["passed"])
                    self.assertEqual(entry["expected_profile"]["t_total"], 0)
                    self.assertEqual(
                        entry["expected_profile"]["vertex_counts"],
                        entry["observed_profile"]["vertex_counts"],
                    )
                    self.assertEqual(
                        entry["expected_profile"]["face_counts"],
                        entry["observed_profile"]["face_counts"],
                    )
                    self.assertEqual(len(entry["canonical_plane_map_sha256"]), 64)
                    self.assertEqual(
                        [run["checker"] for run in checks["checker_runs"]],
                        ["verify.py", "verify_darts.py"],
                    )
                    self.assertTrue(all(run["passed"] for run in checks["checker_runs"]))
                    self.assertTrue(all("PASS " in run["stdout"] for run in checks["checker_runs"]))

            depth_four = next(entry for entry in persisted["targets"] if entry["order"] == 75)
            self.assertEqual(depth_four["composition"]["search"]["order_permutation_count"], 1)
            self.assertEqual(len(depth_four["composition"]["selected_trace"]["steps"]), 3)
            self.assertTrue(depth_four["composition"]["replay_verified"])
            self.assertEqual(
                len(depth_four["composition"]["selected_open_block_canonical_sha256"]), 64
            )
            loaded_sources = {
                order: promotion._load_block(order, path).block
                for order, path in sources.items()
            }
            replayed = promotion.replay_composition_trace(
                loaded_sources, depth_four["composition"]["selected_trace"]
            )
            self.assertEqual(
                blocks.rotation_to_certificate(blocks.close_block(replayed)),
                json.loads(
                    (output / depth_four["certificate_path"]).read_text(encoding="utf-8")
                ),
            )

            # The reflection expansion plus selected closure has a stable
            # result for the exact same sources and custom chain map.
            repeat = temp_dir / "promotion-repeat"
            promotion.promote_target_witnesses(sources, repeat, representations=representations)
            for target in representations:
                self.assertEqual(
                    (output / "certificates" / f"apg_{target}.json").read_bytes(),
                    (repeat / "certificates" / f"apg_{target}.json").read_bytes(),
                )

    def test_default_boolean_selector_rejects_missing_cloud_block_orders(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-promotion-missing-") as temp_name:
            temp_dir = Path(temp_name)
            sources = self._published_sources(temp_dir)
            output = temp_dir / "promotion"
            with self.assertRaisesRegex(
                promotion.PromotionError,
                r"missing required strict-block certificate order\(s\): 28, 29, 31",
            ):
                promotion.promote_target_witnesses(sources, output)
            self.assertFalse(output.exists())

    def test_opened_block_with_duplicate_json_member_is_rejected_before_normalization(self) -> None:
        # `_load_block` is used both by the production composer and by the
        # finalizer's source-handoff replay.  A duplicate nested rotation key
        # must therefore fail before the parser can silently retain its final
        # value and make an ambiguous source artifact look canonical.
        with tempfile.TemporaryDirectory(prefix="apg-promotion-duplicate-opened-") as temp_name:
            temp_dir = Path(temp_name)
            opened = self._published_sources(temp_dir)[21]
            encoded = opened.read_text(encoding="utf-8")
            needle = '      "clockwise": ['
            self.assertEqual(encoded.count(needle), 21)
            opened.write_text(
                encoded.replace(
                    needle,
                    '      "clockwise": [],\n      "clockwise": [',
                    1,
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                promotion.PromotionError, r"duplicate JSON object key",
            ):
                promotion._load_block(21, opened)

    def test_custom_full_frozen_selector_cannot_bypass_production_handoff(self) -> None:
        # Passing the public frozen mapping explicitly must not turn the
        # all-target promotion route into a bare-path custom control.
        with tempfile.TemporaryDirectory(prefix="apg-promotion-full-custom-") as temp_name:
            output = Path(temp_name) / "promotion"
            with self.assertRaisesRegex(
                promotion.PromotionError,
                r"covering all 26 frozen targets must use default production mode",
            ):
                promotion.promote_target_witnesses(
                    {},
                    output,
                    representations=block_arithmetic.boolean_primary_t0_target_representations(),
                )
            self.assertFalse(output.exists())

    def test_handoff_entry_rechecks_raw_postprocess_opening_binding(self) -> None:
        # The production default uses orders 28/29/31 at r=12.  A21/r=10 is a
        # fast known-answer control proving that the composer consumes the
        # portable ledger's exact schema rather than trusting its booleans.
        with tempfile.TemporaryDirectory(prefix="apg-promotion-handoff-") as temp_name:
            temp_dir = Path(temp_name).resolve()
            raw_path = temp_dir / "raw.json"
            post_path = temp_dir / "postprocess.json"
            _write_json(raw_path, _known_closed_cap_record())
            post_result = postprocess.postprocess_record(
                raw_path, post_path, expected_order=21, expected_block_t=0
            )
            self.assertEqual(post_result["disposition"], "CERTIFIED")
            opened_path = Path(post_result["opened_block"]["path"])  # type: ignore[index]
            input_path = temp_dir / "input.json"
            _write_json(
                input_path,
                {
                    "format": handoff.INPUT_FORMAT,
                    "profiles": {
                        "21": {
                            "raw_record": raw_path.name,
                            "postprocess_record": post_path.name,
                            "opened_block": opened_path.relative_to(temp_dir).as_posix(),
                        }
                    },
                },
            )
            ledger_path = temp_dir / "ledger.json"
            ledger = handoff.audit_handoff_input(
                input_path, ledger_path, expected_profiles={21: 10}
            )
            source = promotion._load_block(21, opened_path)
            verified = promotion._verify_handoff_entry(
                21,
                source,
                ledger["blocks"]["21"],  # type: ignore[index]
                ledger_parent=temp_dir,
                expected_r=10,
            )
            self.assertTrue(verified["passed"])
            self.assertEqual(verified["opened_block_sha256"], source.source_sha256)
            raw_checks = verified["raw_closed_candidate_checks"]
            self.assertTrue(raw_checks["passed"])
            self.assertEqual(
                [run["checker"] for run in raw_checks["checker_runs"]],
                ["verify.py", "verify_darts.py"],
            )
            self.assertTrue(all(run["passed"] for run in raw_checks["checker_runs"]))

            # Finalizers must be able to replay source provenance after the
            # cloud checkout disappears.  The package copy preserves every
            # ledger-relative artifact and itself becomes a valid handoff root.
            package = temp_dir / "package"
            package.mkdir()
            materialized = promotion._materialize_source_handoff(
                package,
                {
                    "required": True,
                    "path": str(ledger_path),
                    "sha256": promotion._sha256(ledger_path),
                    "blocks": {"21": verified},
                    "published_blocks": {},
                    "passed": True,
                },
            )
            self.assertEqual(materialized["path"], "source_handoff/handoff-ledger.json")
            self.assertTrue(materialized["materialized"])
            copied_ledger_path = package / materialized["path"]
            self.assertEqual(materialized["sha256"], promotion._sha256(copied_ledger_path))
            copied_ledger = json.loads(copied_ledger_path.read_text(encoding="utf-8"))
            copied_entry = copied_ledger["blocks"]["21"]
            copied_opened = copied_ledger_path.parent / copied_entry["opened_block_path"]
            self.assertTrue(copied_opened.is_file())
            copied_source = promotion._load_block(21, copied_opened)
            self.assertTrue(
                promotion._verify_handoff_entry(
                    21,
                    copied_source,
                    copied_entry,
                    ledger_parent=copied_ledger_path.parent,
                    expected_r=10,
                )["passed"]
            )

            # A cap reopening alone is insufficient: relocating closed cap
            # edge 10--0 in its cyclic order makes the closed map non-spherical
            # while deleting that marked edge still recovers the same strict
            # source block.  Forge every retained digest/claim that precedes
            # the fresh verifier boundary, then require the composer itself to
            # reject the malformed raw APG.
            malformed_raw = json.loads(raw_path.read_text(encoding="utf-8"))
            raw_rotation = blocks.rotation_from_certificate(
                malformed_raw["certificate"]
            )
            mutable = {
                vertex: list(neighbors) for vertex, neighbors in raw_rotation.items()
            }
            mutable[0].remove(10)
            mutable[0].insert(1, 10)
            malformed_raw["certificate"] = blocks.rotation_to_certificate(
                blocks.normalize_rotation(mutable)
            )
            malformed_rotation = blocks.rotation_from_certificate(
                malformed_raw["certificate"]
            )
            malformed_reopened = blocks.open_cap_fans(
                malformed_rotation,
                promotion._raw_cap_fans(malformed_raw["cap_fans"]),
            )
            self.assertEqual(
                blocks.rotation_to_certificate(malformed_reopened.rotation),
                source.certificate,
            )
            _write_json(raw_path, malformed_raw)
            malformed_post = json.loads(post_path.read_text(encoding="utf-8"))
            malformed_post["source_record_sha256"] = promotion._sha256(raw_path)
            malformed_post["candidate"]["sha256"] = promotion._canonical_file_sha256(
                malformed_raw["certificate"]
            )
            _write_json(post_path, malformed_post)
            malformed_entry = dict(ledger["blocks"]["21"])
            malformed_entry["raw_record_sha256"] = promotion._sha256(raw_path)
            malformed_entry["postprocess_sha256"] = promotion._sha256(post_path)
            with self.assertRaisesRegex(
                promotion.PromotionError,
                r"raw closed candidate failed fresh independent checkers",
            ):
                promotion._verify_handoff_entry(
                    21,
                    source,
                    malformed_entry,
                    ledger_parent=temp_dir,
                    expected_r=10,
                )

    def test_cli_custom_control_succeeds_but_default_refuses_incomplete_sources(self) -> None:
        with tempfile.TemporaryDirectory(prefix="apg-promotion-cli-") as temp_name:
            temp_dir = Path(temp_name)
            sources = self._published_sources(temp_dir)
            representations_path = temp_dir / "representations.json"
            _write_json(representations_path, {"39": [21, 21]})
            custom_output = temp_dir / "custom-output"
            custom = subprocess.run(
                [
                    sys.executable,
                    str(COMPOSER),
                    "--block",
                    f"21={sources[21]}",
                    "--output-dir",
                    str(custom_output),
                    "--representations",
                    str(representations_path),
                ],
                cwd=str(ROOT),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(custom.returncode, 0, custom.stdout + custom.stderr)
            self.assertTrue((custom_output / promotion.MANIFEST_NAME).is_file())

            default_output = temp_dir / "default-output"
            default_command = [
                sys.executable,
                str(COMPOSER),
                "--output-dir",
                str(default_output),
            ]
            for order in sorted(sources):
                default_command.extend(("--block", f"{order}={sources[order]}"))
            default = subprocess.run(
                default_command,
                cwd=str(ROOT),
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(default.returncode, 2)
            self.assertIn("missing required strict-block certificate order(s): 28, 29, 31", default.stderr)
            self.assertFalse(default_output.exists())

    def test_checker_failure_records_incomplete_manifest_without_complete_marker(self) -> None:
        representations = {39: (21, 21)}
        with tempfile.TemporaryDirectory(prefix="apg-promotion-fail-") as temp_name:
            temp_dir = Path(temp_name)
            sources = {21: self._published_sources(temp_dir)[21]}
            output = temp_dir / "promotion"
            original = promotion._run_checker
            calls = 0

            def fail_first(
                checker: Path, certificate: Path, *, expected_order: int
            ) -> dict[str, object]:
                nonlocal calls
                calls += 1
                result = original(checker, certificate, expected_order=expected_order)
                if calls == 1:
                    result["returncode"] = 1
                    result["passed"] = False
                    result["stderr"] = "injected checker failure\n"
                return result

            promotion._run_checker = fail_first
            try:
                with self.assertRaisesRegex(promotion.PromotionError, r"failed an independent checker"):
                    promotion.promote_target_witnesses(
                        sources, output, representations=representations
                    )
            finally:
                promotion._run_checker = original
            manifest = json.loads((output / promotion.MANIFEST_NAME).read_text(encoding="utf-8"))
            self.assertEqual(manifest["disposition"], "INCOMPLETE")
            self.assertIn("failed an independent checker", manifest["reason"])
            failed_closure = manifest["blocks"]["21"]["closure_checks"][0]
            self.assertFalse(failed_closure["passed"])
            failed_checks = json.loads(
                (output / failed_closure["checks_path"]).read_text(encoding="utf-8")
            )
            self.assertFalse(failed_checks["passed"])
            self.assertFalse((output / promotion.COMPLETE_MARKER).exists())


if __name__ == "__main__":
    unittest.main()
