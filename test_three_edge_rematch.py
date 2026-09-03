from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import block_tools as bt
import map_search
import near_open_search
import near_opening
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
BASE = ROOT / "results/blocks/D24.json"
STATE = ROOT / "results/calibration/D24_three_edge_positive.json"
CERTIFICATE = ROOT / "results/calibration/D24_three_edge_recovered.json"
LOG = ROOT / "results/logs/D24_three_edge_calibration.json"
BASE_PAIRS = ((5, 11), (6, 17), (13, 20))
PERTURBED_PAIRS = ((5, 20), (6, 13), (11, 17))


class ThreeEdgeRematchTests(unittest.TestCase):
    def test_deranged_matching_count_is_exact_and_no_edge_is_retained(self) -> None:
        matchings = k3.deranged_matchings(BASE_PAIRS)
        self.assertEqual(len(matchings), 8)
        self.assertEqual(len(set(matchings)), 8)
        originals = {frozenset(pair) for pair in BASE_PAIRS}
        for matching in matchings:
            self.assertEqual(len(matching), 3)
            self.assertEqual({dart for pair in matching for dart in pair}, {5, 6, 11, 13, 17, 20})
            self.assertFalse(any(frozenset(pair) in originals for pair in matching))

    def test_apply_rejects_a_retained_original_edge(self) -> None:
        fixed, alphas, _ = k3.load_state_file(STATE)
        alpha = alphas[0]
        retained = ((5, 20), (6, 11), (13, 17))
        with self.assertRaisesRegex(ValueError, "retained an original edge"):
            k3.apply_rematching(alpha, PERTURBED_PAIRS, retained)
        self.assertEqual(len(fixed.cycles), 24)

    def test_calibration_state_replays_hash_score_and_graph_validity(self) -> None:
        fixed, alphas, payload = k3.load_state_file(STATE)
        self.assertEqual(payload["base_file_sha256"], "9210f91150f77ec8e951a272816c3d4f736153fbbbfac0e707576e5aec1b6ab8")
        self.assertEqual(payload["fixed_rotation_hash"], "fae4bc323d2f570b0dcc8aa47a17152abb466a1297d7ca1a2c75fb1743372cdc")
        self.assertEqual(payload["base_alpha_sha256"], "56f06a93f592865ddcc82892c55118ec74630238cd3b403448176a3118579c28")
        self.assertEqual(tuple(map(tuple, payload["construction"]["base_selected_pairs"])), BASE_PAIRS)
        self.assertEqual(tuple(map(tuple, payload["construction"]["applied_rematching"])), PERTURBED_PAIRS)
        self.assertEqual(payload["construction"]["retained_original_pairs"], 0)
        self.assertTrue(payload["construction"]["genuinely_three_edge"])
        self.assertEqual(
            payload["construction"]["scan_counts"],
            {
                "abstract_graph_prunes": 21174,
                "edge_triples": 3048,
                "graph_invalid": 24379,
                "graph_valid": 5,
                "nonspherical_prunes": 3205,
                "rematchings": 24384,
                "score_zero_skipped": 4,
            },
        )
        state = payload["states"][0]
        self.assertEqual(state["state_sha256"], "bbdc97256b43fce92a38897828810551addd9d81c3c0b8f4dc11fed93691cb76")
        self.assertEqual(
            state["breakdown"],
            {
                "abstract_graph": 0,
                "equal_face": 120,
                "face_distribution": 160,
                "hex": 180,
                "total": 640,
                "white": 180,
            },
        )
        self.assertTrue(state["graph_valid"])
        self.assertEqual(near_opening._state_sha256(alphas[0]), state["state_sha256"])
        self.assertEqual(k3.plane_valid_gate(fixed, alphas[0]), (True, None))

    def test_corrupt_state_hash_is_rejected(self) -> None:
        payload = json.loads(STATE.read_text(encoding="utf-8"))
        payload["states"][0]["state_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "state alpha hash"):
                k3.load_state_file(path)

    def test_invalid_candidates_are_pruned_before_scoring(self) -> None:
        fixed, alphas, _ = k3.load_state_file(STATE)
        original_score = map_search.score_breakdown

        def gated_score(inner_fixed: map_search.FixedMap, alpha: list[int]) -> dict[str, int]:
            self.assertEqual(k3.plane_valid_gate(inner_fixed, alpha), (True, None))
            return original_score(inner_fixed, alpha)

        with mock.patch("three_edge_rematch.map_search.score_breakdown", side_effect=gated_score) as score:
            result, _ = k3.enumerate_three_edge_rematchings(
                fixed,
                alphas,
                selected_triple=PERTURBED_PAIRS,
                frontier_limit=8,
                record_outcomes=True,
            )
        self.assertEqual(score.call_count, 1)
        self.assertEqual(result["counts"]["graph_invalid_prunes"], 7)
        self.assertEqual(result["counts"]["distinct_graph_valid"], 1)

    def test_zero_reaches_both_validators_both_closers_and_final_verifier(self) -> None:
        fixed, alphas, _ = k3.load_state_file(STATE)
        with (
            mock.patch(
                "near_open_search.bt.block_from_rotation",
                wraps=near_open_search.bt.block_from_rotation,
            ) as block_tools_builder,
            mock.patch(
                "near_open_search.bt.validate_block",
                wraps=near_open_search.bt.validate_block,
            ) as block_tools_validator,
            mock.patch(
                "near_open_search.blocks.validate_block",
                wraps=near_open_search.blocks.validate_block,
            ) as blocks_validator,
            mock.patch(
                "near_open_search.verify.verify_certificate",
                wraps=near_open_search.verify.verify_certificate,
            ) as final_verifier,
        ):
            result, successes = k3.enumerate_three_edge_rematchings(
                fixed,
                alphas,
                selected_triple=PERTURBED_PAIRS,
                frontier_limit=8,
            )
        self.assertGreaterEqual(block_tools_builder.call_count, 1)
        self.assertGreaterEqual(block_tools_validator.call_count, 2)
        self.assertGreaterEqual(blocks_validator.call_count, 2)
        self.assertEqual(final_verifier.call_count, 2)
        self.assertEqual(result["counts"]["zero_score_cross_validated"], 1)
        self.assertEqual(result["success_hashes"], ["fae4bc323d2f570b0dcc8aa47a17152abb466a1297d7ca1a2c75fb1743372cdc"])
        self.assertEqual(list(successes), result["success_hashes"])

    def test_all_triples_mode_derives_exact_attempt_count(self) -> None:
        triangle = {1: [2, 3], 2: [3, 1], 3: [1, 2]}
        fixed, alpha = map_search.rotation_to_map(triangle)
        result, successes = k3.enumerate_three_edge_rematchings(
            fixed,
            [alpha],
            selected_triple=None,
            frontier_limit=8,
        )
        self.assertEqual(result["mode"], "all-triples")
        self.assertEqual(result["parent_count"], 1)
        self.assertEqual(result["edges"], 3)
        self.assertEqual(result["triples"], 1)
        self.assertEqual(result["matchings_per_triple"], 8)
        self.assertEqual(result["expected_attempts"], 8)
        self.assertEqual(result["counts"]["attempts"], 8)
        self.assertFalse(successes)

    def test_committed_eight_outcomes_and_recovered_certificate_are_frozen(self) -> None:
        payload = json.loads(LOG.read_text(encoding="utf-8"))
        result = payload["result"]
        self.assertEqual(result["parent_count"], 1)
        self.assertEqual(result["edges"], 42)
        self.assertEqual(result["triples"], 1)
        self.assertEqual(result["matchings_per_triple"], 8)
        self.assertEqual(result["expected_attempts"], 8)
        self.assertEqual(
            result["counts"],
            {
                "abstract_graph_prunes": 4,
                "attempts": 8,
                "distinct_graph_valid": 1,
                "duplicates": 0,
                "graph_invalid_prunes": 7,
                "nonspherical_prunes": 3,
                "raw_graph_valid": 1,
                "score_zero": 1,
                "zero_score_block_tools_rejections": 0,
                "zero_score_blocks_rejections": 0,
                "zero_score_cross_validated": 1,
                "zero_score_validation_rejections": 0,
            },
        )
        outcomes = result["candidate_outcomes"]
        self.assertEqual(len(outcomes), 8)
        self.assertEqual(
            [outcome["state_sha256"] for outcome in outcomes],
            [
                "2aae6246296efaf3fe0b6e8ddc41134e3c2b8ddacf0a5286e1434e5a7828668c",
                "cd7e83e63f778e989c723f8a13539ae783742c63131d39284eeb96ad2c3ab1a2",
                "56f06a93f592865ddcc82892c55118ec74630238cd3b403448176a3118579c28",
                "5fba551e77e942f2cb82e20174c9792a095f0bd0fbed123949ad77c55503302d",
                "e3ff5cda8e233ae471d66b25e1997492aead4329e7f4b8b8ed2bb2b0cd9d17e1",
                "0bb1f54a6f73fee7410cce8530fbe51710ae002555df6ef6bca21b53d5dc43f7",
                "e87f296bfd74dbe7c059a69babc169956d7673006e28213081381bf514d70d3f",
                "1d1220d535819e5b66de420aa98d13b1581f244da4e895ed96cd6ff883ea78ea",
            ],
        )
        self.assertEqual([outcome["graph_valid"] for outcome in outcomes], [False, False, True, False, False, False, False, False])
        self.assertTrue(outcomes[2]["cross_validated"])
        self.assertEqual(outcomes[2]["breakdown"]["total"], 0)
        recovered = bt.load_json(CERTIFICATE)
        self.assertEqual(bt.canonical_map_hash(recovered), payload["recovered_D24_hash"])
        checks = result["success_checks"][payload["recovered_D24_hash"]]
        self.assertTrue(checks["block_tools_verified"])
        self.assertTrue(checks["blocks_verified"])
        self.assertEqual(checks["block_tools_closed_sha256"], checks["blocks_closed_sha256"])


if __name__ == "__main__":
    unittest.main()
