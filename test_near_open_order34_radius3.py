from __future__ import annotations

import hashlib
import json
import math
import unittest
from pathlib import Path

import map_search
import near_open_order34_radius2
import near_open_order34_radius3
import near_opening


ROOT = Path(__file__).resolve().parent


class NearOpenOrder34Radius3Tests(unittest.TestCase):
    def test_all_parents_result_and_exact_attempt_count(self) -> None:
        seed_path = ROOT / "results/near_openings/order34_51_fans_8_32.json"
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        k4_log = json.loads(
            (ROOT / "results/logs/order34_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        radius2_log = json.loads(
            (ROOT / "results/logs/order34_near_open_radius2.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, parents = near_open_order34_radius3.load_order34_radius2_frontier(
            seed_path, seed, k4_log, radius2_log
        )
        self.assertEqual(
            hashlib.sha256(seed_path.read_bytes()).hexdigest(),
            near_open_order34_radius2.EXPECTED_SEED_FILE_SHA256,
        )
        self.assertEqual(
            seed["source"]["sha256"],
            near_open_order34_radius2.EXPECTED_SOURCE_SHA256,
        )
        self.assertEqual(
            seed["state_sha256"],
            near_open_order34_radius2.EXPECTED_SEED_STATE_SHA256,
        )
        self.assertEqual(len(parents), 64)
        self.assertEqual(
            near_open_order34_radius3.parent_manifest_sha256(parents),
            near_open_order34_radius3.EXPECTED_PARENT_MANIFEST_SHA256,
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
            (ROOT / "results/logs/order34_near_open_radius3.json").read_text(
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
            near_open_order34_radius2.EXPECTED_EDGES_PER_PARENT,
        )
        self.assertEqual(
            result["edge_pairs_per_parent"],
            math.comb(near_open_order34_radius2.EXPECTED_EDGES_PER_PARENT, 2),
        )
        self.assertEqual(result["pairings_per_edge_pair"], 2)
        self.assertEqual(
            result["counts"]["transition_attempts"],
            near_open_order34_radius3.EXPECTED_ATTEMPTS,
        )
        self.assertEqual(result["parent_states_expanded"], 64)
        self.assertTrue(result["complete"])
        counts = result["counts"]
        self.assertEqual(counts["parents"], 64)
        self.assertEqual(counts["pruned_abstract_graph"], 155614)
        self.assertEqual(counts["raw_graph_valid_transitions"], 86434)
        self.assertEqual(counts["duplicate_graph_valid_states"], 253)
        self.assertEqual(counts["distinct_graph_valid_states"], 86181)
        self.assertEqual(counts["zero_score_candidates"], 0)
        self.assertEqual(counts["zero_score_cross_validated"], 0)
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(result["parent_minimum_score"], 990)
        self.assertEqual(result["best_score"], 750)
        self.assertEqual(result["best_state_count"], 3)
        self.assertTrue(result["descent_below_parent_minimum"])
        self.assertEqual(sum(result["score_histogram_distinct"].values()), 86181)
        histogram_sha256 = hashlib.sha256(
            json.dumps(
                result["score_histogram_distinct"],
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        self.assertEqual(
            histogram_sha256,
            "b655f39102c1e893eeebcd9f4da4e617ce1994d633e62754fa0bb259bccbdd86",
        )
        self.assertEqual(
            [state["state_sha256"] for state in result["best_states"]],
            [
                "52525556412673bb467f5e916f910e790a005dedee76db3017c653149c562338",
                "629a11802ec57974d5111dd379e79f961930fd331dbe4802b9ca65e91a5b5ca5",
                "7ce375b3d88159eb61eb12709504b11399ecf34985e36828539359c9708bbc9a",
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
            "4c0f715fd3765c8aa861e3756025d01a9d8fcf37125d85d14b0ccad7feb4e943",
        )
        decision = radius3_log["decision"]
        self.assertTrue(decision["order34_seed_family_closed"])
        self.assertTrue(decision["radius4_forbidden_by_operator"])
        self.assertFalse(decision["next_radius_started"])


if __name__ == "__main__":
    unittest.main()
