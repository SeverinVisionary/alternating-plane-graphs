from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from unittest import mock

import block_tools as bt
import five_edge_rematch as k5
import map_search
import near_open_search
import near_opening
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
BASE = ROOT / "results/blocks/D24.json"
STATE = ROOT / "results/calibration/D24_five_edge_positive.json"
CERTIFICATE = ROOT / "results/calibration/D24_five_edge_recovered.json"
LOG = ROOT / "results/logs/D24_five_edge_calibration.json"
BASE_PAIRS = ((5, 11), (9, 30), (10, 26), (22, 27), (37, 44))
PERTURBED_PAIRS = ((5, 22), (9, 44), (10, 27), (11, 30), (26, 37))


class FiveEdgeRematchTests(unittest.TestCase):
    def test_inclusion_exclusion_and_exact_deranged_family(self) -> None:
        self.assertEqual(k5.inclusion_exclusion_count(), 945 - 5*105 + 10*15 - 10*3 + 5 - 1)
        matchings = k5.deranged_matchings(BASE_PAIRS)
        self.assertEqual(len(matchings), 544)
        self.assertEqual(len(set(matchings)), 544)
        old = {frozenset(pair) for pair in BASE_PAIRS}
        support = {dart for pair in BASE_PAIRS for dart in pair}
        for matching in matchings:
            self.assertEqual({dart for pair in matching for dart in pair}, support)
            self.assertFalse(any(frozenset(pair) in old for pair in matching))

    def test_apply_rejects_retained_noncurrent_wrong_support_and_malformed(self) -> None:
        _, alphas, _ = k3.load_state_file(STATE)
        alpha = alphas[0]
        retained = (PERTURBED_PAIRS[0], *k5.deranged_matchings(PERTURBED_PAIRS[1:] + ((45, 46),))[0][1:])
        with self.assertRaises(ValueError):
            k5.apply_rematching(alpha, PERTURBED_PAIRS, retained)
        changed = list(PERTURBED_PAIRS); changed[0] = (5, 23)
        with self.assertRaisesRegex(ValueError, "not a current edge"):
            k5.apply_rematching(alpha, changed, k5.deranged_matchings(changed)[0])
        wrong = list(BASE_PAIRS); wrong[-1] = (37, 45)
        with self.assertRaisesRegex(ValueError, "exactly the ten selected darts"):
            k5.apply_rematching(alpha, PERTURBED_PAIRS, wrong)
        with self.assertRaises(ValueError):
            k5.apply_rematching(alpha, PERTURBED_PAIRS, [BASE_PAIRS[0]] * 5)

    def test_calibration_state_and_scan_are_frozen(self) -> None:
        fixed, alphas, payload = k3.load_state_file(STATE)
        self.assertEqual(k5.file_sha256(STATE), "01d774d5d949f2bc3301eacca27a4e91ef0d2d09620fb1398a4213d0fa11b508")
        self.assertEqual(k5.file_sha256(CERTIFICATE), "9b3819cb2d7d0d4034dd122b54f3be380d8afd0fb1bca1db79f0700a4da56e6a")
        self.assertEqual(k5.file_sha256(LOG), "fcdea2df4495ddc5b79fcd837b6f19e8b82fbd5f6fcb71fbd9d2ebfec1938f83")
        self.assertEqual(k5.file_sha256(BASE), "9210f91150f77ec8e951a272816c3d4f736153fbbbfac0e707576e5aec1b6ab8")
        self.assertEqual(tuple(map(tuple, payload["construction"]["base_selected_pairs"])), BASE_PAIRS)
        self.assertEqual(tuple(map(tuple, payload["construction"]["applied_rematching"])), PERTURBED_PAIRS)
        self.assertEqual(payload["construction"]["retained_original_pairs"], 0)
        self.assertTrue(payload["construction"]["genuinely_five_edge"])
        self.assertEqual(payload["construction"]["scan_counts"], {
            "abstract_graph_prunes": 3397, "fifth_edges": 7,
            "graph_invalid": 3460, "nonspherical_prunes": 63,
            "plane_valid": 1, "rematchings": 3461,
        })
        state = payload["states"][0]
        self.assertEqual(state["state_sha256"], "9851e10ad166880470f85e9851ba39db3104defef819d90d3d584e260e1fef8a")
        self.assertEqual(state["breakdown"], {"abstract_graph": 0, "equal_face": 0, "face_distribution": 160, "hex": 0, "total": 490, "white": 330})
        self.assertEqual(k3.plane_valid_gate(fixed, alphas[0]), (True, None))

    def test_all_544_outcomes_and_unique_D24_recovery_are_frozen(self) -> None:
        payload = json.loads(LOG.read_text(encoding="utf-8"))
        result = payload["result"]
        self.assertEqual(result["matchings_per_quintuple"], 544)
        self.assertEqual(result["counts"], {
            "abstract_graph_prunes": 521, "attempts": 544,
            "distinct_plane_valid": 1, "duplicates": 0,
            "graph_invalid_prunes": 543, "nonspherical_prunes": 22,
            "raw_plane_valid": 1, "score_zero": 1,
            "zero_score_block_tools_rejections": 0,
            "zero_score_blocks_rejections": 0,
            "zero_score_cross_validated": 1,
            "zero_score_validation_rejections": 0,
        })
        outcomes = result["candidate_outcomes"]
        self.assertEqual(len(outcomes), 544)
        manifest = hashlib.sha256(json.dumps(outcomes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(manifest, "30bc9c37ba489bd6f9beb62cbf796ee3898a43506459c08c3d47769a033d4de9")
        valid = [item for item in outcomes if item["plane_valid"]]
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0]["state_sha256"], "56f06a93f592865ddcc82892c55118ec74630238cd3b403448176a3118579c28")
        self.assertTrue(valid[0]["cross_validated"])
        block = bt.load_json(CERTIFICATE)
        self.assertEqual(bt.canonical_map_hash(block), "fae4bc323d2f570b0dcc8aa47a17152abb466a1297d7ca1a2c75fb1743372cdc")
        checks = result["success_checks"][payload["recovered_D24_hash"]]
        self.assertTrue(checks["block_tools_verified"] and checks["blocks_verified"])
        self.assertEqual(checks["block_tools_closed_sha256"], checks["blocks_closed_sha256"])

    def test_plane_gate_precedes_scoring_and_zero_uses_all_checks(self) -> None:
        fixed, alphas, payload = k3.load_state_file(STATE)
        original_score = map_search.score_breakdown
        def gated_score(inner_fixed, alpha):
            self.assertEqual(k3.plane_valid_gate(inner_fixed, alpha), (True, None))
            return original_score(inner_fixed, alpha)
        selected = tuple(map(tuple, payload["calibration_selected_current_pairs"]))
        with mock.patch("five_edge_rematch.map_search.score_breakdown", side_effect=gated_score) as score:
            result, _ = k5.enumerate_fixed_quintuple(fixed, alphas[0], selected)
        self.assertEqual(score.call_count, 1)
        self.assertEqual(result["counts"]["graph_invalid_prunes"], 543)
        with (
            mock.patch("near_open_search.bt.validate_block", wraps=near_open_search.bt.validate_block) as one,
            mock.patch("near_open_search.blocks.validate_block", wraps=near_open_search.blocks.validate_block) as two,
            mock.patch("near_open_search.bt.close_block", wraps=near_open_search.bt.close_block) as close_one,
            mock.patch("near_open_search.blocks.close_block", wraps=near_open_search.blocks.close_block) as close_two,
            mock.patch("near_open_search.verify.verify_certificate", wraps=near_open_search.verify.verify_certificate) as verifier,
        ):
            result, _ = k5.enumerate_fixed_quintuple(fixed, alphas[0], selected)
        self.assertGreaterEqual(one.call_count, 2); self.assertGreaterEqual(two.call_count, 2)
        self.assertEqual(close_one.call_count, 1); self.assertEqual(close_two.call_count, 1)
        self.assertEqual(verifier.call_count, 2)
        self.assertEqual(result["counts"]["zero_score_cross_validated"], 1)


if __name__ == "__main__":
    unittest.main()
