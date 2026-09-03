from __future__ import annotations

import hashlib
import json
import math
import unittest
from pathlib import Path

import map_search
import near_open_order30_radius2
import near_open_order30_radius3
import near_opening


ROOT = Path(__file__).resolve().parent


class NearOpenOrder30Radius3Tests(unittest.TestCase):
    def test_all_parents_result_and_exact_attempt_count(self) -> None:
        seed_path = ROOT / "results/near_openings/order30_34_fans_8_15.json"
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        k4_log = json.loads(
            (ROOT / "results/logs/order30_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        radius2_log = json.loads(
            (ROOT / "results/logs/order30_near_open_radius2.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, parents = near_open_order30_radius3.load_order30_radius2_frontier(
            seed_path, seed, k4_log, radius2_log
        )
        self.assertEqual(
            hashlib.sha256(seed_path.read_bytes()).hexdigest(),
            near_open_order30_radius2.EXPECTED_SEED_FILE_SHA256,
        )
        self.assertEqual(
            seed["source"]["sha256"],
            near_open_order30_radius2.EXPECTED_SOURCE_SHA256,
        )
        self.assertEqual(
            seed["state_sha256"],
            near_open_order30_radius2.EXPECTED_SEED_STATE_SHA256,
        )
        self.assertEqual(len(parents), 64)
        self.assertEqual(
            near_open_order30_radius3.parent_manifest_sha256(parents),
            near_open_order30_radius3.EXPECTED_PARENT_MANIFEST_SHA256,
        )
        parent_keys = []
        for parent in parents:
            alpha = parent["alpha"]
            self.assertEqual(
                near_opening._state_sha256(alpha), parent["state_sha256"]
            )
            self.assertEqual(
                map_search.score_breakdown(fixed, alpha), parent["breakdown"]
            )
            self.assertTrue(map_search._abstract_graph_ok(fixed, alpha))
            parent_keys.append(
                (parent["breakdown"]["total"], parent["state_sha256"])
            )
        self.assertEqual(parent_keys, sorted(parent_keys))
        radius3_log = json.loads(
            (ROOT / "results/logs/order30_near_open_radius3.json").read_text(
                encoding="utf-8"
            )
        )
        result = radius3_log["result"]
        self.assertEqual(
            result["parent_state_hashes"],
            [parent["state_sha256"] for parent in parents],
        )
        self.assertEqual(
            result["edges_per_parent"],
            near_open_order30_radius2.EXPECTED_EDGES_PER_PARENT,
        )
        self.assertEqual(
            result["edge_pairs_per_parent"],
            math.comb(near_open_order30_radius2.EXPECTED_EDGES_PER_PARENT, 2),
        )
        self.assertEqual(result["pairings_per_edge_pair"], 2)
        self.assertEqual(
            result["counts"]["transition_attempts"],
            near_open_order30_radius3.EXPECTED_ATTEMPTS,
        )
        self.assertEqual(result["parent_states_expanded"], 64)
        self.assertTrue(result["complete"])
        counts = result["counts"]
        self.assertEqual(counts["parents"], 64)
        self.assertEqual(counts["pruned_abstract_graph"], 119146)
        self.assertEqual(counts["raw_graph_valid_transitions"], 64022)
        self.assertEqual(counts["duplicate_graph_valid_states"], 1673)
        self.assertEqual(counts["distinct_graph_valid_states"], 62349)
        self.assertEqual(counts["zero_score_candidates"], 0)
        self.assertEqual(counts["zero_score_cross_validated"], 0)
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(result["parent_minimum_score"], 610)
        self.assertEqual(result["best_score"], 550)
        self.assertEqual(result["best_state_count"], 2)
        self.assertTrue(result["descent_below_parent_minimum"])
        self.assertEqual(sum(result["score_histogram_distinct"].values()), 62349)
        histogram_sha256 = hashlib.sha256(
            json.dumps(
                result["score_histogram_distinct"],
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        self.assertEqual(
            histogram_sha256,
            "9ed4246b435fbc9a37a18a9315a94e09c06fa0395cdfb40f075dfdb57f26d6a2",
        )
        self.assertEqual(
            [state["state_sha256"] for state in result["best_states"]],
            [
                "3b621631bf9a223e133094c25daaed2ac7d7bc9ed60f7f6175caac18bed44e95",
                "d33d8aa3c6899c4017bb12dd84c697fc9efb6b1f26d88906f09d7a714d6b5a54",
            ],
        )
        frontier = result["frontier_states"]
        self.assertEqual(len(frontier), 64)
        frontier_keys = []
        for state in frontier:
            alpha = state["alpha"]
            self.assertEqual(
                near_opening._state_sha256(alpha), state["state_sha256"]
            )
            self.assertEqual(
                map_search.score_breakdown(fixed, alpha), state["breakdown"]
            )
            self.assertTrue(map_search._abstract_graph_ok(fixed, alpha))
            frontier_keys.append(
                (state["breakdown"]["total"], state["state_sha256"])
            )
        self.assertEqual(frontier_keys, sorted(frontier_keys))
        frontier_payload = [
            {
                "state_sha256": state["state_sha256"],
                "score_breakdown": state["breakdown"],
            }
            for state in frontier
        ]
        frontier_manifest = hashlib.sha256(
            json.dumps(
                frontier_payload, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        self.assertEqual(
            frontier_manifest,
            "950f3912d8594efccd96af34751da80d48cdc95315f2da51c200ff0ecbd2592b",
        )
        decision = radius3_log["decision"]
        self.assertTrue(decision["order30_seed_family_closed"])
        self.assertTrue(decision["radius4_forbidden_by_operator"])
        self.assertFalse(decision["next_radius_started"])


if __name__ == "__main__":
    unittest.main()
