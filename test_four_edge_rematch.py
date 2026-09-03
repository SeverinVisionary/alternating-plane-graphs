from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from unittest import mock

import block_tools as bt
import four_edge_rematch as k4
import map_search
import near_open_search
import near_opening
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
BASE = ROOT / "results/blocks/D24.json"
STATE = ROOT / "results/calibration/D24_four_edge_positive.json"
CERTIFICATE = ROOT / "results/calibration/D24_four_edge_recovered.json"
LOG = ROOT / "results/logs/D24_four_edge_calibration.json"
RADIUS4 = ROOT / "results/logs/order26_three_edge_spherical_radius4.json"
RADIUS4_PARENTS = ROOT / "results/targets/order26_three_edge_spherical_radius4_parents.json"
GENUS_ONE_PARENTS = ROOT / "results/targets/order26_three_edge_parents.json"
BASE_PAIRS = ((5, 11), (9, 30), (22, 27), (37, 44))
PERTURBED_PAIRS = ((5, 22), (9, 44), (11, 30), (27, 37))


class FourEdgeRematchTests(unittest.TestCase):
    def test_inclusion_exclusion_and_deranged_count_are_exact(self) -> None:
        self.assertEqual(k4.inclusion_exclusion_count(), 105 - 4 * 15 + 6 * 3 - 4 + 1)
        matchings = k4.deranged_matchings(BASE_PAIRS)
        self.assertEqual(len(matchings), 60)
        self.assertEqual(len(set(matchings)), 60)
        originals = {frozenset(pair) for pair in BASE_PAIRS}
        selected = {dart for pair in BASE_PAIRS for dart in pair}
        for matching in matchings:
            self.assertEqual(len(matching), 4)
            self.assertEqual({dart for pair in matching for dart in pair}, selected)
            self.assertFalse(any(frozenset(pair) in originals for pair in matching))

    def test_apply_rejects_retained_edge_and_wrong_selection(self) -> None:
        _, alphas, _ = k3.load_state_file(STATE)
        retained = ((5, 22), (9, 11), (30, 44), (27, 37))
        with self.assertRaisesRegex(ValueError, "retained an original edge"):
            k4.apply_rematching(alphas[0], PERTURBED_PAIRS, retained)
        with self.assertRaisesRegex(ValueError, "exactly the eight selected darts"):
            k4.apply_rematching(alphas[0], PERTURBED_PAIRS, ((5, 11), (9, 30), (22, 27), (37, 45)))

    def test_calibration_state_hashes_score_plane_validity_and_scan_are_frozen(self) -> None:
        fixed, alphas, payload = k3.load_state_file(STATE)
        self.assertEqual(k4.file_sha256(BASE), "9210f91150f77ec8e951a272816c3d4f736153fbbbfac0e707576e5aec1b6ab8")
        self.assertEqual(payload["fixed_rotation_hash"], "fae4bc323d2f570b0dcc8aa47a17152abb466a1297d7ca1a2c75fb1743372cdc")
        self.assertEqual(payload["base_alpha_sha256"], "56f06a93f592865ddcc82892c55118ec74630238cd3b403448176a3118579c28")
        self.assertEqual(tuple(map(tuple, payload["construction"]["base_selected_pairs"])), BASE_PAIRS)
        self.assertEqual(tuple(map(tuple, payload["construction"]["applied_rematching"])), PERTURBED_PAIRS)
        self.assertEqual(payload["construction"]["retained_original_pairs"], 0)
        self.assertTrue(payload["construction"]["genuinely_four_edge"])
        self.assertEqual(payload["construction"]["scan_counts"], {
            "abstract_graph_prunes": 2_206_325,
            "edge_quadruples": 39_557,
            "graph_invalid": 2_373_371,
            "nonspherical_prunes": 167_046,
            "plane_valid": 8,
            "rematchings": 2_373_379,
            "score_zero_skipped": 3,
            "unique_recovery_rejections": 4,
        })
        state = payload["states"][0]
        self.assertEqual(state["state_sha256"], "0028cf263b487dba40b9b0258ba312041d5d364e77a7890cc63434d15512c0e6")
        self.assertEqual(state["breakdown"], {
            "abstract_graph": 0, "equal_face": 0, "face_distribution": 160,
            "hex": 0, "total": 490, "white": 330,
        })
        self.assertEqual(k3.plane_valid_gate(fixed, alphas[0]), (True, None))
        self.assertEqual(near_opening._state_sha256(alphas[0]), state["state_sha256"])

    def test_all_sixty_outcomes_and_exact_d24_inverse_are_frozen(self) -> None:
        payload = json.loads(LOG.read_text(encoding="utf-8"))
        result = payload["result"]
        self.assertEqual((result["parent_count"], result["edges"], result["quadruples"]), (1, 42, 1))
        self.assertEqual(result["matchings_per_quadruple"], 60)
        self.assertEqual(result["expected_attempts"], 60)
        self.assertEqual(result["counts"], {
            "abstract_graph_prunes": 58,
            "attempts": 60,
            "distinct_plane_valid": 1,
            "duplicates": 0,
            "graph_invalid_prunes": 59,
            "nonspherical_prunes": 1,
            "raw_plane_valid": 1,
            "score_zero": 1,
            "zero_score_block_tools_rejections": 0,
            "zero_score_blocks_rejections": 0,
            "zero_score_cross_validated": 1,
            "zero_score_validation_rejections": 0,
        })
        outcomes = result["candidate_outcomes"]
        self.assertEqual(len(outcomes), 60)
        manifest = hashlib.sha256(json.dumps(outcomes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(manifest, "90d4304a2daf9698f05d76070a69774b964431a2b99d5ee2496d3d6ccf80cd2d")
        valid = [outcome for outcome in outcomes if outcome["plane_valid"]]
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0]["matching_index"], 15)
        self.assertEqual(valid[0]["state_sha256"], "56f06a93f592865ddcc82892c55118ec74630238cd3b403448176a3118579c28")
        self.assertTrue(valid[0]["cross_validated"])
        recovered = bt.load_json(CERTIFICATE)
        self.assertEqual(bt.canonical_map_hash(recovered), payload["recovered_D24_hash"])
        checks = result["success_checks"][payload["recovered_D24_hash"]]
        self.assertTrue(checks["block_tools_verified"])
        self.assertTrue(checks["blocks_verified"])
        self.assertEqual(checks["block_tools_closed_sha256"], checks["blocks_closed_sha256"])

    def test_invalid_candidates_are_never_scored(self) -> None:
        fixed, alphas, _ = k3.load_state_file(STATE)
        original_score = map_search.score_breakdown

        def gated_score(inner_fixed: map_search.FixedMap, alpha: list[int]) -> dict[str, int]:
            self.assertEqual(k3.plane_valid_gate(inner_fixed, alpha), (True, None))
            return original_score(inner_fixed, alpha)

        with mock.patch("four_edge_rematch.map_search.score_breakdown", side_effect=gated_score) as score:
            result, _ = k4.enumerate_four_edge_rematchings(
                fixed, alphas, selected_quadruple=PERTURBED_PAIRS, support_mode=False,
                frontier_limit=60, record_outcomes=True,
            )
        self.assertEqual(score.call_count, 1)
        self.assertEqual(result["counts"]["graph_invalid_prunes"], 59)
        self.assertEqual(result["counts"]["distinct_plane_valid"], 1)

    def test_zero_reaches_both_validators_both_closers_and_final_verifier(self) -> None:
        fixed, alphas, _ = k3.load_state_file(STATE)
        with (
            mock.patch("near_open_search.bt.block_from_rotation", wraps=near_open_search.bt.block_from_rotation) as builder,
            mock.patch("near_open_search.bt.validate_block", wraps=near_open_search.bt.validate_block) as validator_one,
            mock.patch("near_open_search.blocks.validate_block", wraps=near_open_search.blocks.validate_block) as validator_two,
            mock.patch("near_open_search.bt.close_block", wraps=near_open_search.bt.close_block) as closer_one,
            mock.patch("near_open_search.blocks.close_block", wraps=near_open_search.blocks.close_block) as closer_two,
            mock.patch("near_open_search.verify.verify_certificate", wraps=near_open_search.verify.verify_certificate) as verifier,
        ):
            result, successes = k4.enumerate_four_edge_rematchings(
                fixed, alphas, selected_quadruple=PERTURBED_PAIRS, support_mode=False,
                frontier_limit=60,
            )
        self.assertGreaterEqual(builder.call_count, 1)
        self.assertGreaterEqual(validator_one.call_count, 2)
        self.assertGreaterEqual(validator_two.call_count, 2)
        self.assertEqual(closer_one.call_count, 1)
        self.assertEqual(closer_two.call_count, 1)
        self.assertEqual(verifier.call_count, 2)
        self.assertEqual(result["counts"]["zero_score_cross_validated"], 1)
        self.assertEqual(sorted(successes), result["success_hashes"])

    def test_selector_is_exactly_the_twelve_edge_support_on_all_score510_states(self) -> None:
        fixed, _, _ = k3.load_state_file(RADIUS4_PARENTS)
        payload = json.loads(RADIUS4.read_text(encoding="utf-8"))
        states = [state for state in payload["result"]["frontier_states"] if state["breakdown"]["total"] == 510]
        self.assertEqual(len(states), 56)
        for state in states:
            alpha = state["alpha"]
            faces, face_of = map_search._faces(fixed, alpha)
            lengths = [len(face) for face in faces]
            expected: set[tuple[int, int]] = set()
            for edge in k3.edge_pairs(alpha):
                left, right = edge
                if face_of[left] == face_of[right] or lengths[face_of[left]] == lengths[face_of[right]]:
                    expected.add(edge)
            bad_whites = {
                vertex for vertex, cycle in enumerate(fixed.cycles)
                if fixed.vertex_degree[vertex] == 2
                and sorted(lengths[face_of[dart]] for dart in cycle) != [5, 6]
            }
            for edge in k3.edge_pairs(alpha):
                if any(fixed.dart_vertex[dart] in bad_whites for dart in edge):
                    expected.add(edge)
            actual = k4.equal_white_defect_support_edges(fixed, alpha)
            self.assertEqual(actual, tuple(sorted(expected)))
            self.assertEqual(len(actual), 12)

    def test_selector_refuses_nonspherical_and_nonzero_preconditions(self) -> None:
        genus_fixed, genus_alphas, _ = k3.load_state_file(GENUS_ONE_PARENTS)
        with self.assertRaisesRegex(ValueError, "plane-valid"):
            k4.equal_white_defect_support_edges(genus_fixed, genus_alphas[0])

        fixed, _, _ = k3.load_state_file(RADIUS4_PARENTS)
        state = next(
            state for state in json.loads(RADIUS4.read_text(encoding="utf-8"))["result"]["frontier_states"]
            if state["breakdown"]["total"] == 510
        )
        original = map_search.score_breakdown(fixed, state["alpha"])
        for component in ("face_distribution", "abstract_graph", "hex"):
            changed = dict(original)
            changed[component] = 1
            with self.subTest(component=component), mock.patch("four_edge_rematch.map_search.score_breakdown", return_value=changed):
                with self.assertRaisesRegex(ValueError, "nonzero components"):
                    k4.equal_white_defect_support_edges(fixed, state["alpha"])

    def test_support_mode_attempt_identity_is_derived(self) -> None:
        fixed, _, _ = k3.load_state_file(RADIUS4_PARENTS)
        state = next(
            state for state in json.loads(RADIUS4.read_text(encoding="utf-8"))["result"]["frontier_states"]
            if state["breakdown"]["total"] == 510
        )
        support = k4.equal_white_defect_support_edges(fixed, state["alpha"])
        self.assertEqual(len(support), 12)
        # Do not enumerate the target; freeze only the exact budget identity.
        self.assertEqual(__import__("math").comb(len(support), 4) * 60, 29_700)


if __name__ == "__main__":
    unittest.main()
