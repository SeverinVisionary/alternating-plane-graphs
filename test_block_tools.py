#!/usr/bin/env python3
"""Focused gates for cloud-produced block_tools local surgery."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import block_tools


ROOT = Path(__file__).resolve().parent


class BlockToolsSwitchTests(unittest.TestCase):
    def test_block_two_edge_switches_is_exact_and_instrumented(self) -> None:
        block = json.loads(
            (ROOT / "results" / "blocks" / "D24.json").read_text(encoding="utf-8")
        )
        stats: dict[str, object] = {}
        survivors = block_tools.block_two_edge_switches(block, stats=stats)
        counts = stats["counts"]
        self.assertEqual(
            counts.get("candidate_validation_attempts", 0),
            counts.get("splice_attempts", 0),
        )
        self.assertEqual(stats["distinct_survivors"], len(survivors))
        self.assertEqual(
            len(stats["distinct_survivor_hashes"]),
            len(set(stats["distinct_survivor_hashes"])),
        )
        for survivor in survivors:
            with self.subTest(hash=block_tools.canonical_map_hash(survivor)):
                summary = block_tools.validate_block(survivor)
                self.assertEqual(summary["order"], 24)

    def _load_block(self, name: str) -> dict[str, object]:
        return json.loads(
            (ROOT / "results" / "blocks" / name).read_text(encoding="utf-8")
        )

    def test_mirror_block_is_a_valid_strict_block(self) -> None:
        block = self._load_block("A21.json")
        mirrored = block_tools.mirror_block(block)
        self.assertEqual(block_tools.validate_block(mirrored)["order"], 21)
        self.assertNotEqual(
            block_tools.canonical_map_hash(block),
            block_tools.canonical_map_hash(mirrored),
        )

    def test_compose_two_variants_include_both_reflection_classes(self) -> None:
        first = self._load_block("A21.json")
        second = self._load_block("B22.json")
        variants = block_tools.compose_two_variants(first, second)
        self.assertEqual(len(variants), 4)
        for variant in variants:
            with self.subTest(hash=block_tools.canonical_map_hash(variant)):
                self.assertEqual(block_tools.validate_block(variant)["order"], 40)

    def test_recover_blocks_with_mirror_scans_both_orientations(self) -> None:
        certificate = json.loads(
            (ROOT / "certificates" / "search_seeds" / "order21.json").read_text(
                encoding="utf-8"
            )
        )
        blocks = block_tools.recover_blocks_with_mirror(
            certificate, provenance={"method": "test"}
        )
        self.assertEqual(len(blocks), 2)
        for block in blocks:
            self.assertEqual(block_tools.validate_block(block)["order"], 21)


if __name__ == "__main__":
    unittest.main()
