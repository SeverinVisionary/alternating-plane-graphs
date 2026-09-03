#!/usr/bin/env python3
"""Known-answer tests for exact Section 8 block operations."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import blocks


ROOT = Path(__file__).resolve().parent
SEEDS = ROOT / "certificates" / "search_seeds"
VERIFY = ROOT / "verify.py"
RESULT_BLOCKS = ROOT / "results" / "blocks"


def _load_rotation(name: str) -> blocks.Rotation:
    data = json.loads((SEEDS / name).read_text(encoding="utf-8"))
    return blocks.rotation_from_certificate(data)


def _load_cloud_block(name: str) -> blocks.Block:
    data = json.loads((RESULT_BLOCKS / name).read_text(encoding="utf-8"))
    rotation = blocks.normalize_rotation(
        {row["id"]: row["clockwise"] for row in data["vertices"]}
    )
    return blocks.Block(rotation, blocks.validate_block(rotation))


class BlockOperationsTests(unittest.TestCase):
    def _verify_closed(self, rotation: blocks.Rotation, expected_order: int) -> str:
        certificate = blocks.rotation_to_certificate(rotation)
        with tempfile.TemporaryDirectory(prefix="apg-block-test-") as temp_dir:
            path = Path(temp_dir) / "closed.json"
            path.write_text(
                json.dumps(certificate, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(VERIFY),
                    str(path),
                    "--expect-order",
                    str(expected_order),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"order={expected_order}", result.stdout)
        return result.stdout

    def test_all_published_seeds_are_positive_apg_controls(self) -> None:
        names = (
            "order21.json",
            "order22.json",
            "order23.json",
            "order25.json",
            "order29a.json",
            "order29b.json",
            "order34a.json",
            "order34b.json",
        )
        for name in names:
            with self.subTest(name=name):
                rotation = _load_rotation(name)
                expected = int(name.removeprefix("order").split(".")[0].rstrip("ab"))
                self._verify_closed(rotation, expected)

    def test_open_and_close_published_A_B_C_blocks(self) -> None:
        for name, expected_order in (
            ("order21.json", 21),
            ("order22.json", 22),
            ("order23.json", 23),
        ):
            with self.subTest(name=name):
                opened = blocks.opening_scan(_load_rotation(name))
                self.assertEqual(len(opened), 1)
                block = opened[0]
                self.assertEqual(block.order, expected_order)
                self.assertEqual(len(block.sockets), 2)
                self.assertEqual(
                    {len(block.rotation[white]) for socket in block.sockets for white in socket.whites},
                    {2},
                )
                self._verify_closed(blocks.close_block(block), expected_order)

    def test_composition_reproduces_all_ordered_A_B_C_pairs(self) -> None:
        known = {
            order: blocks.opening_scan(_load_rotation(f"order{order}.json"))[0]
            for order in (21, 22, 23)
        }
        for inner_order, inner in known.items():
            for outer_order, outer in known.items():
                with self.subTest(inner=inner_order, outer=outer_order):
                    composed = blocks.compose_blocks(inner, outer)
                    expected_order = inner_order + outer_order - 3
                    self.assertEqual(composed.order, expected_order)
                    output = self._verify_closed(
                        blocks.close_block(composed), expected_order
                    )
                    self.assertIn("vertex_counts={3: 16", output)
                    self.assertIn(f"4: {expected_order - 28}", output)
                    self.assertIn("5: 12", output)

    def test_cloud_A_D_blocks_cross_validate_and_compose_independently(self) -> None:
        # block_tools.py was produced in Linux cloud; blocks.py is a separately
        # written implementation.  Reconstructing all sixteen pairs here keeps
        # a shared bug in the cloud composer from passing its own gate.
        known = {
            letter: _load_cloud_block(f"{letter}{order}.json")
            for letter, order in zip("ABCD", (21, 22, 23, 24))
        }
        for letter, block in known.items():
            with self.subTest(single=letter):
                self._verify_closed(blocks.close_block(block), block.order)
        for inner_letter, inner in known.items():
            for outer_letter, outer in known.items():
                with self.subTest(pair=inner_letter + outer_letter):
                    composed = blocks.compose_blocks(inner, outer)
                    expected_order = inner.order + outer.order - 3
                    output = self._verify_closed(
                        blocks.close_block(composed), expected_order
                    )
                    self.assertIn("vertex_counts={3: 16", output)
                    self.assertIn(f"4: {expected_order - 28}", output)
                    self.assertIn("5: 12", output)

    def test_direct_opening_scan_does_not_overclaim_priority_seeds(self) -> None:
        # This checks only the listed published embeddings.  It is deliberately
        # not an existence/nonexistence test for blocks at these orders.
        for name in (
            "order25.json",
            "order29a.json",
            "order29b.json",
            "order34a.json",
            "order34b.json",
        ):
            with self.subTest(name=name):
                self.assertEqual(blocks.opening_scan(_load_rotation(name)), ())

    def test_block_validator_rejects_non_pentagonal_socket_neighbor(self) -> None:
        block = blocks.opening_scan(_load_rotation("order21.json"))[0]
        rotation = {vertex: list(neighbors) for vertex, neighbors in block.rotation.items()}
        # Reorder a degree-5 vertex to change the sphere embedding while keeping
        # the abstract graph and degrees unchanged.
        vertex = next(
            value
            for value, neighbors in rotation.items()
            if len(neighbors) == 5 and len(set(neighbors)) == 5
        )
        rotation[vertex][1], rotation[vertex][2] = rotation[vertex][2], rotation[vertex][1]
        with self.assertRaises(blocks.BlockError):
            blocks.validate_block(blocks.normalize_rotation(rotation))

    def test_block_certificate_records_reconstructed_sockets(self) -> None:
        block = blocks.opening_scan(_load_rotation("order21.json"))[0]
        data = blocks.block_to_certificate(block)
        self.assertEqual(data["format"], blocks.BLOCK_FORMAT)
        self.assertEqual(len(data["vertices"]), 21)
        self.assertEqual(len(data["sockets"]), 2)

    def test_reference_block_exposes_all_nine_explicit_closures(self) -> None:
        block = _load_cloud_block("A21.json")
        variants = blocks.close_block_variants(block)
        self.assertEqual(
            {indices for indices, _ in variants},
            {(first, second) for first in range(3) for second in range(3)},
        )
        reference_indices = (0, 0)
        self.assertEqual(blocks.close_block(block), dict(variants)[reference_indices])
        for indices, rotation in variants:
            with self.subTest(hubs=indices):
                self._verify_closed(rotation, 21)

    def test_cap_fan_opening_inverts_every_A21_closure(self) -> None:
        block = _load_cloud_block("A21.json")
        sockets = blocks.validate_block(block.rotation)
        for hub_indices, closed in blocks.close_block_variants(block):
            fans = tuple(
                blocks.ClosureFan(
                    hub=sorted(socket.whites)[hub_index],
                    leaves=tuple(
                        white
                        for index, white in enumerate(sorted(socket.whites))
                        if index != hub_index
                    ),
                )
                for socket, hub_index in zip(sockets, hub_indices)
            )
            with self.subTest(hubs=hub_indices):
                opened = blocks.open_cap_fans(closed, fans)
                self.assertEqual(opened.rotation, block.rotation)
                self.assertEqual(
                    {fan.whites for fan in opened.source_fans},
                    {fan.whites for fan in fans},
                )

    def test_mirror_scan_and_composition_cover_reflection_classes(self) -> None:
        source = _load_rotation("order21.json")
        mirrored_blocks = blocks.opening_scan_with_mirror(source)
        self.assertEqual(len(mirrored_blocks), 2)
        for block in mirrored_blocks:
            with self.subTest(rotation=tuple(block.rotation.items())[:1]):
                self._verify_closed(blocks.close_block(block), 21)

        inner = _load_cloud_block("A21.json")
        outer = _load_cloud_block("B22.json")
        compositions = blocks.compose_blocks_variants(inner, outer)
        self.assertEqual(len(compositions), 4)
        for composition in compositions:
            with self.subTest(rotation=tuple(composition.rotation.items())[:1]):
                self._verify_closed(blocks.close_block(composition), 40)

    def test_exhaustive_composition_records_socket_shift_and_reflection_trace(self) -> None:
        inner = _load_cloud_block("A21.json")
        outer = _load_cloud_block("B22.json")
        # The legacy first-success result remains exactly the first cyclic
        # alignment, while promotion needs all three possible white matches.
        alignments = blocks.compose_blocks_alignments(inner, outer)
        self.assertEqual(alignments[0][1], blocks.compose_blocks(inner, outer))
        self.assertEqual([shift for shift, _ in alignments], [0, 1, 2])

        variants = blocks.compose_blocks_all_variants(inner, outer)
        self.assertEqual(len(variants), 48)
        traces = {
            (
                variant.inner_reflected,
                variant.outer_reflected,
                variant.inner_socket,
                variant.outer_socket,
                variant.shift,
            )
            for variant in variants
        }
        self.assertEqual(
            traces,
            {
                (inner_reflected, outer_reflected, inner_socket, outer_socket, shift)
                for inner_reflected in (False, True)
                for outer_reflected in (False, True)
                for inner_socket in range(2)
                for outer_socket in range(2)
                for shift in range(3)
            },
        )
        legacy_key = tuple(blocks.compose_blocks(inner, outer).rotation.items())
        self.assertIn(legacy_key, {tuple(item.block.rotation.items()) for item in variants})
        for variant in variants:
            with self.subTest(trace=variant):
                self._verify_closed(blocks.close_block(variant.block), 40)

    def test_relaxed_scan_recovers_the_strict_reference_block(self) -> None:
        block = _load_cloud_block("A21.json")
        closed = blocks.close_block(block)
        candidates = blocks.relaxed_opening_scan(closed)
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertEqual(candidate.rotation, block.rotation)
        self.assertEqual(
            blocks.validate_relaxed_block(candidate.rotation), candidate.sockets
        )


if __name__ == "__main__":
    unittest.main()
