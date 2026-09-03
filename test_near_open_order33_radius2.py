from __future__ import annotations

import json
import unittest
from pathlib import Path

import map_search
import near_open_order33_radius2
import near_opening


ROOT = Path(__file__).resolve().parent


class NearOpenOrder33Radius2Tests(unittest.TestCase):
    def test_seed_k4_parent_hashes_scores_manifest_and_attempt_count(self) -> None:
        seed = json.loads(
            (ROOT / "results/near_openings/order33_44_fans_1_8.json").read_text(
                encoding="utf-8"
            )
        )
        k4_log = json.loads(
            (ROOT / "results/logs/order33_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, parents = near_open_order33_radius2.load_order33_k4_frontier(
            seed, k4_log
        )
        self.assertEqual(
            seed["source"]["sha256"],
            near_open_order33_radius2.EXPECTED_SOURCE_SHA256,
        )
        self.assertEqual(
            seed["state_sha256"],
            near_open_order33_radius2.EXPECTED_SEED_STATE_SHA256,
        )
        self.assertEqual(len(parents), 64)
        self.assertEqual(
            near_open_order33_radius2.parent_manifest_sha256(parents),
            near_open_order33_radius2.EXPECTED_PARENT_MANIFEST_SHA256,
        )
        for parent in parents:
            alpha = parent["alpha"]
            self.assertEqual(
                near_opening._state_sha256(alpha), parent["state_sha256"]
            )
            self.assertEqual(
                map_search.score_breakdown(fixed, alpha), parent["breakdown"]
            )
            self.assertTrue(map_search._abstract_graph_ok(fixed, alpha))
        radius2_log = json.loads(
            (ROOT / "results/logs/order33_near_open_radius2.json").read_text(
                encoding="utf-8"
            )
        )
        result = radius2_log["result"]
        self.assertEqual(
            result["parent_state_hashes"],
            [parent["state_sha256"] for parent in parents],
        )
        self.assertEqual(result["edges_per_parent"], 60)
        self.assertEqual(result["edge_pairs_per_parent"], 1770)
        self.assertEqual(result["pairings_per_edge_pair"], 2)
        self.assertEqual(
            result["counts"]["transition_attempts"],
            near_open_order33_radius2.EXPECTED_ATTEMPTS,
        )
        self.assertEqual(result["parent_states_expanded"], 64)
        self.assertTrue(result["complete"])


if __name__ == "__main__":
    unittest.main()
