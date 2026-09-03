from __future__ import annotations

import json
import unittest
from pathlib import Path

import near_open_beam


ROOT = Path(__file__).resolve().parent


class NearOpenRadius3Tests(unittest.TestCase):
    def test_radius2_frontier_one_parent_has_exact_two_edge_neighborhood(self) -> None:
        seed = json.loads(
            (ROOT / "results/near_openings/order26_27_fans_1_24.json").read_text(
                encoding="utf-8"
            )
        )
        k4_log = json.loads(
            (ROOT / "results/logs/order26_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        radius2_log = json.loads(
            (ROOT / "results/logs/order26_near_open_radius2.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, parents = near_open_beam.load_radius2_frontier(
            seed, k4_log, radius2_log
        )
        self.assertEqual(len(parents), 64)
        self.assertEqual(parents[0]["breakdown"]["total"], 670)
        _, stats = near_open_beam.expand_two_edge_beam(
            fixed, parents, max_parents=1
        )
        self.assertEqual(stats["counts"]["transition_attempts"], 2070)
        self.assertEqual(stats["parent_minimum_score"], 670)


if __name__ == "__main__":
    unittest.main()
