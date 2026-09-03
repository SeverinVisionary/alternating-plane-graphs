from __future__ import annotations

import json
import unittest
from pathlib import Path

import map_search
import near_open_dual_radius3
import near_opening


ROOT = Path(__file__).resolve().parent


class NearOpenDualRadius3Tests(unittest.TestCase):
    def test_all_parent_hashes_scores_manifest_and_exact_attempt_count(self) -> None:
        seed = json.loads(
            (ROOT / "results/near_openings/order26_28_fans_1_26.json").read_text(
                encoding="utf-8"
            )
        )
        k4_log = json.loads(
            (ROOT / "results/logs/order26_dual_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        radius2_log = json.loads(
            (ROOT / "results/logs/order26_dual_near_open_radius2.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, parents = near_open_dual_radius3.load_dual_radius2_frontier(
            seed, k4_log, radius2_log
        )
        self.assertEqual(len(parents), 64)
        self.assertEqual(
            near_open_dual_radius3.parent_manifest_sha256(parents),
            near_open_dual_radius3.EXPECTED_PARENT_MANIFEST_SHA256,
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
        radius3_log = json.loads(
            (ROOT / "results/logs/order26_dual_near_open_radius3.json").read_text(
                encoding="utf-8"
            )
        )
        result = radius3_log["result"]
        self.assertEqual(
            result["parent_state_hashes"],
            [parent["state_sha256"] for parent in parents],
        )
        self.assertEqual(result["edges_per_parent"], 46)
        self.assertEqual(result["edge_pairs_per_parent"], 1035)
        self.assertEqual(result["pairings_per_edge_pair"], 2)
        self.assertEqual(
            result["counts"]["transition_attempts"],
            near_open_dual_radius3.EXPECTED_ATTEMPTS,
        )
        self.assertEqual(result["parent_states_expanded"], 64)
        self.assertTrue(result["complete"])


if __name__ == "__main__":
    unittest.main()
