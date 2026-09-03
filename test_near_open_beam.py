from __future__ import annotations

import json
import unittest
from pathlib import Path

import near_open_beam


ROOT = Path(__file__).resolve().parent


class NearOpenBeamTests(unittest.TestCase):
    def test_frontier_and_one_parent_transition_count(self) -> None:
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
        fixed, parents = near_open_beam.load_frontier(seed, k4_log)
        self.assertEqual(len(parents), 64)
        self.assertEqual(parents[0]["breakdown"]["total"], 780)
        _, stats = near_open_beam.expand_two_edge_beam(
            fixed, parents, max_parents=1
        )
        self.assertFalse(stats["complete"])
        self.assertEqual(stats["edges_per_parent"], 46)
        self.assertEqual(stats["edge_pairs_per_parent"], 1035)
        self.assertEqual(stats["pairings_per_edge_pair"], 2)
        self.assertEqual(stats["counts"]["transition_attempts"], 2070)

    def test_complete_radius2_frontier_replays_hash_score_and_graph(self) -> None:
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
        _, states = near_open_beam.load_radius2_frontier(
            seed, k4_log, radius2_log
        )
        self.assertEqual(len(states), 64)
        self.assertEqual(states[0]["breakdown"]["total"], 670)
        self.assertEqual(
            states[0]["state_sha256"],
            "6ca67fc6ccbb65171b1d3058a538782144cb830351b2a617c26425a55c19a6eb",
        )


if __name__ == "__main__":
    unittest.main()
