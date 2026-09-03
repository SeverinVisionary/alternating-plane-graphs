#!/usr/bin/env python3
"""Lightweight correctness gates for the cloud-only combinatorial-map search."""

from __future__ import annotations

import json
import random
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

import block_tools as bt
import map_search


ROOT = Path(__file__).resolve().parent
BLOCKS = ROOT / "results" / "blocks"


def _load(name: str) -> dict[str, object]:
    return json.loads((BLOCKS / name).read_text(encoding="utf-8"))


class MapSearchTests(unittest.TestCase):
    def test_valid_block_round_trips_through_dart_representation(self) -> None:
        block = _load("D24.json")
        rotation = bt._rotation_from_rows(block["vertices"])
        fixed, alpha = map_search.rotation_to_map(rotation)
        self.assertEqual(map_search.rotation_from_state(fixed, alpha), rotation)
        self.assertEqual(map_search.score(fixed, alpha), 0)
        self.assertEqual(
            map_search.score_breakdown(fixed, alpha),
            {
                "abstract_graph": 0,
                "equal_face": 0,
                "face_distribution": 0,
                "hex": 0,
                "total": 0,
                "white": 0,
            },
        )

    def test_positive_score_breakdown_sums_exactly(self) -> None:
        block = _load("D24.json")
        fixed, alpha = map_search.rotation_to_map(
            bt._rotation_from_rows(block["vertices"])
        )
        perturbed = map_search.switch_move(fixed, alpha, random.Random(0))
        self.assertIsNotNone(perturbed)
        components = map_search.score_breakdown(fixed, perturbed)
        self.assertGreater(components["total"], 0)
        self.assertEqual(
            components["total"],
            sum(
                components[name]
                for name in (
                    "face_distribution",
                    "abstract_graph",
                    "equal_face",
                    "white",
                    "hex",
                )
            ),
        )
        self.assertEqual(map_search.score(fixed, perturbed), components["total"])

    def test_production_positive_perturbation_is_nonvacuous(self) -> None:
        block = _load("D24.json")
        success, stats, _ = map_search.run_search(
            block,
            order=24,
            r_value=None,
            seed=0,
            steps=0,
            initial_switches=1,
        )
        self.assertIsNone(success)
        self.assertEqual(stats.initial_score, 820)
        self.assertEqual(stats.initial_components["total"], 820)
        self.assertEqual(stats.initial_switches, 1)

    def test_graph_valid_mode_rejects_invalid_moves(self) -> None:
        block = _load("D24.json")
        _, stats, _ = map_search.run_search(
            block,
            order=24,
            r_value=None,
            seed=0,
            steps=10,
            initial_switches=1,
            graph_valid=True,
        )
        self.assertTrue(stats.graph_valid_mode)
        self.assertGreater(stats.graph_rejections, 0)

    def test_graph_valid_mode_recovers_fixed_positive_D24(self) -> None:
        block = _load("D24.json")
        success, stats, _ = map_search.run_search(
            block,
            order=24,
            r_value=None,
            seed=0,
            steps=1000,
            initial_switches=1,
            graph_valid=True,
        )
        self.assertIsNotNone(success)
        self.assertEqual(stats.initial_score, 820)
        self.assertEqual(stats.best_score, 0)
        self.assertEqual(stats.steps, 217)
        self.assertEqual(stats.zero_score_validation_rejections, 0)

    def test_retarget_profiles_cover_both_order25_r_values(self) -> None:
        block = _load("D24.json")
        for r_value, expected in (
            (10, Counter({2: 6, 3: 6, 4: 7, 5: 6})),
            (11, Counter({2: 6, 3: 7, 4: 5, 5: 7})),
        ):
            with self.subTest(r=r_value):
                fixed, alpha = map_search.retarget_from_block(
                    block, 25, r_value, random.Random(1000 + r_value)
                )
                self.assertEqual(Counter(fixed.vertex_degree), expected)
                self.assertEqual(len(alpha), sum(expected[d] * d for d in expected))
                self.assertTrue(all(alpha[alpha[dart]] == dart for dart in range(len(alpha))))

    def test_initial_zero_state_is_validated_before_any_moves(self) -> None:
        block = _load("D24.json")
        success, stats, _ = map_search.run_search(
            block, order=24, r_value=None, seed=7, steps=0
        )
        self.assertIsNotNone(success)
        self.assertEqual(stats.zero_score_states, 1)
        self.assertEqual(stats.zero_score_validation_rejections, 0)

    def test_later_zero_state_is_checked_after_invalid_zero(self) -> None:
        block = _load("D24.json")
        fixed, alpha = map_search.rotation_to_map(bt._rotation_from_rows(block["vertices"]))
        calls = 0

        def fake_block_from_rotation(*args: object, **kwargs: object) -> dict[str, object]:
            nonlocal calls
            calls += 1
            if calls == 1:
                raise bt.BlockError("synthetic invalid zero")
            return block

        with (
            mock.patch.object(map_search, "grow_from_block", return_value=(fixed, alpha)),
            mock.patch.object(map_search, "switch_move", return_value=list(alpha)),
            mock.patch.object(bt, "block_from_rotation", side_effect=fake_block_from_rotation),
        ):
            success, stats, _ = map_search.run_search(
                block, order=24, r_value=None, seed=8, steps=1
            )
        self.assertIs(success, block)
        self.assertEqual(stats.zero_score_states, 2)
        self.assertEqual(stats.zero_score_validation_rejections, 1)


if __name__ == "__main__":
    unittest.main()
