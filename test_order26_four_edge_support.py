from __future__ import annotations

import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

import four_edge_rematch as k4
import order26_four_edge_support as target
import three_edge_rematch as k3
import near_opening


ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "jobs/order26_four_edge_support.json"
STATE = ROOT / "results/targets/order26_four_edge_support_parents.json"
STAGE = ROOT / "results/logs/order26_four_edge_support_stage.json"
RESULT = ROOT / "results/logs/order26_four_edge_support_result.json"
GENUS_ONE = ROOT / "results/targets/order26_three_edge_parents.json"
PARENT_MANIFEST = "10e474800e632b44767b6dfd2137594d14db2eb87f96e22de6f717251fb112b7"
SUPPORT_MANIFEST = "7dadec97c34866026d2394bfa3c81d3ef1e7d47bda57cdfd03f8a093555ed2f1"


class Order26FourEdgeSupportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = target.load_spec(SPEC)
        self.payload = json.loads(STATE.read_text(encoding="utf-8"))

    def test_spec_hash_provenance_and_exact_budget_are_frozen(self) -> None:
        self.assertEqual(k4.file_sha256(SPEC), "0b9e7152a329f811e6deae549d26f7d548bcbd705a7685087b220cfeaf8cd9f1")
        self.assertEqual(self.spec["input_commit"], "92fd7808b9dd4c2e44531be10066c8b9c633c3ff")
        self.assertEqual(self.spec["parent_result_sha256"], "06f145c6b4c465c46943bb1f278acac364d8000f969e60f19a0a391646663e8a")
        self.assertEqual(self.spec["fixed_state_sha256"], "cfe788abcf2b63585bdcbc1a860ce08dcf7988380437caf5cf41461d36e133c7")
        self.assertEqual(self.spec["fixed_rotation_hash"], "aa82e2d913a9cc4c98a405fba9293a1440ae77f3acc40bbb6c6ff76f6b604346")
        self.assertEqual(self.spec["base_alpha_sha256"], "9115b20cf204b1ff18b321142d6bf5c13eaf0501336382aa98283d69a36ac23b")
        self.assertEqual(self.spec["parent_manifest_sha256"], PARENT_MANIFEST)
        self.assertEqual(self.spec["support_manifest_sha256"], SUPPORT_MANIFEST)
        self.assertEqual(self.spec["parent_count"], 56)
        self.assertEqual(self.spec["quadruples_per_parent"], math.comb(12, 4))
        self.assertEqual(self.spec["total_quadruples"], 56 * math.comb(12, 4))
        self.assertEqual(self.spec["matchings_per_quadruple"], 60)
        self.assertEqual(self.spec["total_attempts"], 56 * math.comb(12, 4) * 60)
        self.assertEqual(self.spec["total_attempts"], 1_663_200)

    def test_target_file_hash_order_alphas_breakdowns_and_provenance_are_frozen(self) -> None:
        self.assertEqual(k4.file_sha256(STATE), "93f9ec18ff60744b691da9ea3743ef4efa505e570ace71f5e8b26aef4c68b5e2")
        fixed, alphas = target.validate_target_state(self.spec, self.payload)
        states = self.payload["states"]
        self.assertEqual(len(states), 56)
        self.assertEqual(len(alphas), 56)
        self.assertEqual([s["state_sha256"] for s in states], sorted(s["state_sha256"] for s in states))
        self.assertEqual(target.canonical_sha256(target.parent_manifest(states)), PARENT_MANIFEST)
        self.assertEqual(self.payload["parent_result_sha256"], self.spec["parent_result_sha256"])
        self.assertEqual(self.payload["fixed_rotation_hash"], self.spec["fixed_rotation_hash"])
        self.assertEqual(self.payload["base_alpha_sha256"], self.spec["base_alpha_sha256"])
        for state, alpha in zip(states, alphas):
            self.assertEqual(state["breakdown"], target.EXPECTED_BREAKDOWN)
            self.assertEqual(near_opening._state_sha256(alpha), state["state_sha256"])
            self.assertEqual(k3.plane_valid_gate(fixed, alpha), (True, None))

    def test_all_support_decompositions_and_global_manifest_are_frozen(self) -> None:
        fixed, _ = target.validate_target_state(self.spec, self.payload)
        states = self.payload["states"]
        for state in states:
            replay = target.support_diagnostics(fixed, state["alpha"])
            self.assertEqual(state["support_edges"], replay["support_edges"])
            self.assertEqual(len(state["support_edges"]), 12)
            self.assertEqual(len(state["equal_face_edges"]), 6)
            self.assertEqual(len(state["bad_white_vertices_zero_based"]), 4)
            self.assertEqual(len(state["bad_white_incident_edges"]), 8)
            union = {
                tuple(edge) for edge in state["equal_face_edges"]
            } | {
                tuple(edge) for edge in state["bad_white_incident_edges"]
            }
            self.assertEqual(tuple(map(tuple, state["support_edges"])), tuple(sorted(union)))
        self.assertEqual(target.canonical_sha256(target.support_manifest(states)), SUPPORT_MANIFEST)

    def test_builder_reproduces_committed_target_state_exactly(self) -> None:
        rebuilt = target.build_target_state(self.spec, ROOT)
        self.assertEqual(rebuilt, self.payload)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            import block_tools as bt
            bt.write_json(path, rebuilt)
            self.assertEqual(k4.file_sha256(path), self.spec["target_state_sha256"])

    def test_stage_log_freezes_manifests_environment_and_no_compute_scope(self) -> None:
        record = json.loads(STAGE.read_text(encoding="utf-8"))
        self.assertEqual(record["format"], "apg-four-edge-order26-support-stage-v1")
        self.assertIn("no localized k4 target enumeration", record["claim_scope"])
        self.assertEqual(record["spec_sha256"], k4.file_sha256(SPEC))
        self.assertEqual(record["target_state_sha256"], k4.file_sha256(STATE))
        self.assertEqual(record["parent_manifest_sha256"], PARENT_MANIFEST)
        self.assertEqual(record["support_manifest_sha256"], SUPPORT_MANIFEST)
        self.assertEqual(record["identities"]["parents"], 56)
        self.assertEqual(record["identities"]["total_quadruples"], 27_720)
        self.assertEqual(record["identities"]["matchings_per_quadruple"], 60)
        self.assertEqual(record["identities"]["total_attempts"], 1_663_200)
        self.assertEqual(record["environment"]["uname"]["system"], "Linux")

    def test_missing_extra_or_reordered_parent_is_rejected(self) -> None:
        for mutation in ("missing", "extra", "reordered"):
            payload = copy.deepcopy(self.payload)
            if mutation == "missing":
                payload["states"].pop()
            elif mutation == "extra":
                payload["states"].append(copy.deepcopy(payload["states"][-1]))
            else:
                payload["states"][0], payload["states"][1] = payload["states"][1], payload["states"][0]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                target.validate_target_state(self.spec, payload)

    def test_support_list_drift_is_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["states"][0]["support_edges"][0] = payload["states"][0]["support_edges"][1]
        with self.assertRaisesRegex(ValueError, "support field"):
            target.validate_target_state(self.spec, payload)

    def test_nonplane_parent_is_rejected_even_with_updated_parent_manifest(self) -> None:
        _, genus_alphas, genus_payload = k3.load_state_file(GENUS_ONE)
        payload = copy.deepcopy(self.payload)
        state = payload["states"][0]
        state["alpha"] = genus_alphas[0]
        state["state_sha256"] = near_opening._state_sha256(genus_alphas[0])
        state["breakdown"] = genus_payload["states"][0]["breakdown"]
        spec = dict(self.spec)
        spec["parent_manifest_sha256"] = target.canonical_sha256(target.parent_manifest(payload["states"]))
        with self.assertRaisesRegex(ValueError, "non-plane"):
            target.validate_target_state(spec, payload)

    def test_forbidden_nonzero_component_and_budget_drift_are_rejected(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["states"][0]["breakdown"]["face_distribution"] = 1
        spec = dict(self.spec)
        spec["parent_manifest_sha256"] = target.canonical_sha256(target.parent_manifest(payload["states"]))
        with self.assertRaisesRegex(ValueError, "forbidden"):
            target.validate_target_state(spec, payload)
        for key, value in (
            ("total_attempts", 1_663_199),
            ("total_quadruples", 27_719),
            ("matchings_per_quadruple", 59),
        ):
            changed = dict(self.spec)
            changed[key] = value
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "spec.json"
                path.write_text(json.dumps(changed), encoding="utf-8")
                with self.assertRaises(ValueError):
                    target.load_spec(path)

    def test_incomplete_result_and_retained_original_edge_are_rejected(self) -> None:
        incomplete = {
            "complete": False,
            "counts": {},
        }
        with self.assertRaisesRegex(ValueError, "incomplete"):
            target.validate_result(self.spec, incomplete)
        incomplete = {
            "complete": True,
            "counts": {"attempts": 1_663_200},
        }
        with self.assertRaisesRegex(ValueError, "omits"):
            target.validate_result(self.spec, incomplete)
        fixed, alphas = target.validate_target_state(self.spec, self.payload)
        support = k4.equal_white_defect_support_edges(fixed, alphas[0])
        selected = support[:4]
        retained = (selected[0], *k3.deranged_matchings(selected[1:])[0])
        with self.assertRaisesRegex(ValueError, "retained an original edge"):
            k4.apply_rematching(alphas[0], selected, retained)

    def test_complete_result_hash_accounting_histogram_and_frontier_are_frozen(self) -> None:
        self.assertEqual(
            k4.file_sha256(RESULT),
            "df9a2c68f3c5ac246c0722b9959f09ca2574b11497095de97e8e316d2fd6753c",
        )
        record = json.loads(RESULT.read_text(encoding="utf-8"))
        target.validate_result_record(self.spec, record, ROOT)
        result = record["result"]
        self.assertEqual(result["support_edge_counts"], [12] * 56)
        self.assertEqual(result["quadruples"], 27_720)
        self.assertEqual(result["matchings_per_quadruple"], 60)
        self.assertEqual(result["expected_attempts"], 1_663_200)
        self.assertEqual(result["counts"], {
            "abstract_graph_prunes": 1_528_576,
            "attempts": 1_663_200,
            "distinct_plane_valid": 1_484,
            "duplicates": 308,
            "graph_invalid_prunes": 1_661_408,
            "nonspherical_prunes": 132_832,
            "raw_plane_valid": 1_792,
            "score_zero": 0,
            "zero_score_block_tools_rejections": 0,
            "zero_score_blocks_rejections": 0,
            "zero_score_cross_validated": 0,
            "zero_score_validation_rejections": 0,
        })
        self.assertEqual(result["score_histogram_distinct"], {
            "510": 1_372,
            "950": 56,
            "1170": 56,
        })
        self.assertEqual(result["best_score"], 510)
        self.assertEqual(result["frontier_state_count"], 64)
        self.assertTrue(result["frontier_truncated"])
        self.assertEqual(
            target.canonical_sha256(result["frontier_states"]),
            "3eb61e48e784ba7737e0b2c40d54f5985e0d69cd7981a124494720ee7fe03289",
        )
        minimum_hashes = [
            state["state_sha256"] for state in result["frontier_states"]
            if state["breakdown"]["total"] == 510
        ]
        self.assertEqual(len(minimum_hashes), 64)
        self.assertEqual(
            target.canonical_sha256(minimum_hashes),
            "68bbbf164d70c582bb68bd07473169775c0255cfde639311d6200b999c8eceb3",
        )
        self.assertTrue(all(
            state["breakdown"] == target.EXPECTED_BREAKDOWN
            for state in result["frontier_states"]
        ))
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(record["certificates"], {})

    def test_result_rejects_incomplete_accounting_and_certificate_mismatch(self) -> None:
        record = json.loads(RESULT.read_text(encoding="utf-8"))
        for mutation in ("plane", "dedup", "histogram", "frontier", "certificate"):
            changed = copy.deepcopy(record)
            if mutation == "plane":
                changed["result"]["counts"]["nonspherical_prunes"] -= 1
            elif mutation == "dedup":
                changed["result"]["counts"]["duplicates"] -= 1
            elif mutation == "histogram":
                changed["result"]["score_histogram_distinct"]["510"] -= 1
            elif mutation == "frontier":
                changed["result"]["frontier_states"].reverse()
            else:
                changed["result"]["success_hashes"] = ["0" * 64]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                target.validate_result_record(self.spec, changed, ROOT)


if __name__ == "__main__":
    unittest.main()
