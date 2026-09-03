#!/usr/bin/env python3
"""Lightweight structural gates for the cloud-only near-opening search."""

from __future__ import annotations

import unittest
import hashlib
import json
from collections import Counter
from pathlib import Path
from unittest import mock

import block_tools as bt
import map_search
import near_open_search
import near_opening


ROOT = Path(__file__).resolve().parent


class NearOpenSearchTests(unittest.TestCase):
    def test_order30_k4_result_replays_exactly(self) -> None:
        seed_path = ROOT / "results/near_openings/order30_34_fans_8_15.json"
        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(seed_path.read_bytes()).hexdigest(),
            "fb451e5a09ff138f496a460fefbec164cd8e6291a86b231ef59a2a92fd41dd91",
        )
        self.assertEqual(
            seed["source"]["sha256"],
            "30780d7a870fd5736afa6c9cb3b223b4e70012d4c01f8ed7080c2dd8adf8080a",
        )
        self.assertEqual(
            seed["state_sha256"],
            "4a0472b81b2a649ca6774205c6edc2bcac4dbafc6d0675665e210f489f8c82ab",
        )
        fixed, _ = near_opening.state_from_seed(seed)
        log = json.loads(
            (ROOT / "results/logs/order30_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        result = log["result"]
        counts = result["counts"]
        self.assertEqual(result["mandatory_edges"], [[16, 18], [17, 18]])
        self.assertEqual(result["donor_edges"], 12)
        self.assertEqual(counts["donor_pair_attempts"], 66)
        self.assertEqual(counts["perfect_rematching_attempts"], 6930)
        self.assertEqual(counts["pruned_original_matching"], 66)
        self.assertEqual(counts["pruned_overlapping_selected_edges"], 0)
        self.assertEqual(counts["pruned_abstract_graph"], 6656)
        self.assertEqual(counts["graph_valid_candidates"], 208)
        self.assertEqual(counts["duplicate_graph_valid_candidates"], 0)
        self.assertEqual(counts["distinct_graph_valid_candidates"], 208)
        self.assertEqual(counts["zero_score_candidates"], 0)
        self.assertEqual(counts["zero_score_cross_validated"], 0)
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(sum(result["score_histogram"].values()), 208)
        self.assertEqual(result["score_histogram"]["630"], 1)
        self.assertEqual(result["best_score"], 630)
        self.assertEqual(result["best_state_count"], 1)
        states = result["frontier_states"]
        self.assertEqual(len(states), 64)
        keys = []
        for state in states:
            alpha = state["alpha"]
            self.assertEqual(
                near_opening._state_sha256(alpha), state["state_sha256"]
            )
            self.assertEqual(
                map_search.score_breakdown(fixed, alpha), state["breakdown"]
            )
            self.assertTrue(map_search._abstract_graph_ok(fixed, alpha))
            keys.append((state["breakdown"]["total"], state["state_sha256"]))
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(
            keys[0],
            (
                630,
                "4c7f2ac4c8f48865f7f2ad025272205c6f83da63751c3467a0284ddac1eb1f0f",
            ),
        )
        payload = [
            {
                "state_sha256": state["state_sha256"],
                "score_breakdown": state["breakdown"],
            }
            for state in states
        ]
        manifest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.assertEqual(
            manifest,
            "c9e58ba3a72586c0592cf938ef54b1fa589a9cc9a69cf125d68e13a8594b0df0",
        )

    def test_order33_structural_defect_and_k3_impossibility(self) -> None:
        seed = json.loads(
            (ROOT / "results/near_openings/order33_44_fans_1_8.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, alpha = near_opening.state_from_seed(seed)
        prediction = near_open_search.predicted_k4_structure(
            fixed,
            alpha,
            mandatory_edges=((2, 5), (4, 5)),
        )
        self.assertEqual(prediction["hexagons"][0], [1, 3, 2, 5, 4, 10])
        self.assertEqual(prediction["mandatory_degree_pairs"], [[2, 4], [2, 4]])
        self.assertEqual(prediction["shared_vertex"], 5)
        self.assertEqual(prediction["shared_vertex_degree"], 4)
        self.assertEqual(prediction["offending_white_vertices"], [2, 4])
        self.assertEqual(prediction["offending_white_degrees"], [2, 2])
        self.assertEqual(
            prediction["edge_degree_pattern_counts"],
            {"2,4": 2, "2,5": 10, "3,4": 13, "3,5": 14, "4,5": 21},
        )
        self.assertEqual(
            prediction["maximum_degree5_endpoints_from_one_additional_edge"],
            1,
        )
        self.assertEqual(prediction["degree5_endpoints_required"], 2)
        self.assertTrue(prediction["k3_impossible"])

    def test_order33_k4_result_replays_exactly(self) -> None:
        seed = json.loads(
            (ROOT / "results/near_openings/order33_44_fans_1_8.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, _ = near_opening.state_from_seed(seed)
        log = json.loads(
            (ROOT / "results/logs/order33_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        result = log["result"]
        counts = result["counts"]
        self.assertEqual(result["donor_edges"], 14)
        self.assertEqual(counts["donor_pair_attempts"], 91)
        self.assertEqual(counts["perfect_rematching_attempts"], 9555)
        self.assertEqual(counts["pruned_original_matching"], 91)
        self.assertEqual(counts["pruned_abstract_graph"], 9168)
        self.assertEqual(counts["graph_valid_candidates"], 296)
        self.assertEqual(counts["duplicate_graph_valid_candidates"], 0)
        self.assertEqual(counts["distinct_graph_valid_candidates"], 296)
        self.assertEqual(counts["zero_score_candidates"], 0)
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(sum(result["score_histogram"].values()), 296)
        self.assertEqual(result["best_score"], 870)
        states = result["frontier_states"]
        self.assertEqual(len(states), 64)
        keys = []
        for state in states:
            alpha = state["alpha"]
            self.assertEqual(
                near_opening._state_sha256(alpha), state["state_sha256"]
            )
            self.assertEqual(
                map_search.score_breakdown(fixed, alpha), state["breakdown"]
            )
            self.assertTrue(map_search._abstract_graph_ok(fixed, alpha))
            keys.append((state["breakdown"]["total"], state["state_sha256"]))
        self.assertEqual(keys, sorted(keys))
        payload = [
            {
                "state_sha256": state["state_sha256"],
                "score_breakdown": state["breakdown"],
            }
            for state in states
        ]
        manifest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.assertEqual(
            manifest,
            "9451cf31099b8b460664732af0421c4aa00b89c7c1566fe41ca87616594718af",
        )

    def test_dual_order26_structural_defect_and_k3_impossibility(self) -> None:
        seed = json.loads(
            (ROOT / "results/near_openings/order26_28_fans_1_26.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, alpha = near_opening.state_from_seed(seed)
        prediction = near_open_search.predicted_k4_structure(
            fixed,
            alpha,
            mandatory_edges=((2, 3), (3, 4)),
        )
        self.assertEqual(prediction["hexagons"][0], [1, 8, 2, 3, 4, 5])
        self.assertEqual(prediction["mandatory_degree_pairs"], [[2, 4], [4, 2]])
        self.assertEqual(prediction["shared_vertex"], 3)
        self.assertEqual(prediction["shared_vertex_degree"], 4)
        self.assertEqual(prediction["offending_white_vertices"], [2, 4])
        self.assertEqual(prediction["offending_white_degrees"], [2, 2])
        self.assertEqual(
            prediction["edge_degree_pattern_counts"],
            {"2,4": 2, "2,5": 10, "3,4": 9, "3,5": 12, "4,5": 13},
        )
        self.assertEqual(
            prediction["maximum_degree5_endpoints_from_one_additional_edge"],
            1,
        )
        self.assertEqual(prediction["degree5_endpoints_required"], 2)
        self.assertTrue(prediction["k3_impossible"])

    def test_dual_order26_k4_result_replays_exactly(self) -> None:
        seed = json.loads(
            (ROOT / "results/near_openings/order26_28_fans_1_26.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, _ = near_opening.state_from_seed(seed)
        log = json.loads(
            (ROOT / "results/logs/order26_dual_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        result = log["result"]
        counts = result["counts"]
        self.assertEqual(result["donor_edges"], 12)
        self.assertEqual(counts["donor_pair_attempts"], 66)
        self.assertEqual(counts["perfect_rematching_attempts"], 6930)
        self.assertEqual(counts["pruned_original_matching"], 66)
        self.assertEqual(counts["pruned_abstract_graph"], 6660)
        self.assertEqual(counts["graph_valid_candidates"], 204)
        self.assertEqual(counts["duplicate_graph_valid_candidates"], 0)
        self.assertEqual(counts["distinct_graph_valid_candidates"], 204)
        self.assertEqual(counts["zero_score_candidates"], 0)
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(sum(result["score_histogram"].values()), 204)
        self.assertEqual(result["best_score"], 840)
        states = result["frontier_states"]
        self.assertEqual(len(states), 64)
        keys = []
        for state in states:
            alpha = state["alpha"]
            self.assertEqual(
                near_opening._state_sha256(alpha), state["state_sha256"]
            )
            self.assertEqual(
                map_search.score_breakdown(fixed, alpha), state["breakdown"]
            )
            self.assertTrue(map_search._abstract_graph_ok(fixed, alpha))
            keys.append((state["breakdown"]["total"], state["state_sha256"]))
        self.assertEqual(keys, sorted(keys))
        payload = [
            {
                "state_sha256": state["state_sha256"],
                "score_breakdown": state["breakdown"],
            }
            for state in states
        ]
        manifest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.assertEqual(
            manifest,
            "9554901a8d5a265f5a8f48c174d0f031f06255d24df66ecf05fa3dba694b1e7f",
        )

    def test_perfect_matching_counts_and_coverage(self) -> None:
        for size, expected in ((0, 1), (2, 1), (4, 3), (6, 15), (8, 105)):
            with self.subTest(size=size):
                matchings = list(near_open_search.perfect_matchings(range(size)))
                self.assertEqual(len(matchings), expected)
                self.assertEqual(len(set(matchings)), expected)
                for matching in matchings:
                    flattened = [item for pair in matching for item in pair]
                    self.assertEqual(sorted(flattened), list(range(size)))

    def test_edge_parser_normalizes_endpoints(self) -> None:
        self.assertEqual(near_open_search._parse_pair("9,3"), (3, 9))

    def test_odd_perfect_matching_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            list(near_open_search.perfect_matchings((1, 2, 3)))

    def test_zero_is_sent_to_both_independent_validators(self) -> None:
        counts: Counter[str] = Counter()
        with (
            mock.patch.object(
                bt, "block_from_rotation", side_effect=bt.BlockError("synthetic")
            ),
            mock.patch.object(
                near_open_search.blocks,
                "validate_block",
                side_effect=near_open_search.blocks.BlockError("synthetic"),
            ) as independent,
        ):
            result = near_open_search._independently_validate_zero(
                {}, provenance={}, counts=counts
            )
        self.assertIsNone(result)
        independent.assert_called_once()
        self.assertEqual(counts["zero_score_block_tools_rejections"], 1)
        self.assertEqual(counts["zero_score_blocks_rejections"], 1)

    def test_order26_k4_frontier_retains_lowest_64_distinct_states(self) -> None:
        seed = json.loads(
            (ROOT / "results/near_openings/order26_27_fans_1_24.json").read_text(
                encoding="utf-8"
            )
        )
        fixed, alpha = near_opening.state_from_seed(seed)
        _, stats = near_open_search.targeted_k4_repairs(
            fixed,
            alpha,
            mandatory_edges=((22, 23), (22, 25)),
        )
        self.assertEqual(stats["counts"]["distinct_graph_valid_candidates"], 204)
        self.assertEqual(stats["frontier_state_count"], 64)
        self.assertTrue(stats["frontier_truncated"])
        keys = [
            (state["breakdown"]["total"], state["state_sha256"])
            for state in stats["frontier_states"]
        ]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(keys[0][0], 780)
        self.assertEqual(
            keys[0][1],
            "45fc5b2e04bd179ae5f24154293fc95d3196fe3f6c8d07ca2a8369c5a72c6e86",
        )


if __name__ == "__main__":
    unittest.main()
