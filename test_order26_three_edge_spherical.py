from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import map_search
import order26_three_edge_spherical as spherical
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "jobs/order26_three_edge_spherical_radius2.json"
STATE_PATH = ROOT / "results/targets/order26_three_edge_spherical_radius2_parents.json"
LEGACY_STATE_PATH = ROOT / "results/targets/order26_three_edge_parents.json"
STAGE_LOG = ROOT / "results/logs/order26_three_edge_spherical_radius2_stage.json"
RESULT_LOG = ROOT / "results/logs/order26_three_edge_spherical_radius2.json"
STATUS_NOTE = ROOT / "SEARCH_STATUS.md"
PARENT_HASHES = [
    "45bf7f1e438f78754fed51a14a9216c597ca3abb8ed6b2af49b222adbaaf504d",
    "6ad19ef9780de6b2ce485d63c2be6e2cd24106b439b35665d1dd82dd7e067897",
    "c3575c39d9356848d0f16b0d6b6b6b1cb97b1ba73e260a39b85fda6b18bf7917",
    "ce50c9b6128731cbf0c887143b64e5cd57922001823011065d7b3f3172510a8d",
    "d907d54800393986e357948244a28d8b6f371361beb83a078b43555ade335dbe",
    "e19cb3ccfcf8837437d9488e21900e72a9b0bfda1ae26e3ca73dc2be4368535e",
]
MINIMUM_HASHES = [
    "318a7705a37c95f8846a66b27723d955ac9abfacf2306b138fd31ced531efc21",
    "37631fcb6a168f5d2f2def28c86aa4c31e5fc2fb7085788eecaadaa0765ec2f6",
    "587fa1d1daa53031e5a513f4b2150ce6f34988c5fb938bcb9b02143ab259cf98",
    "940a089c952a6da1ea99b41e1454c71c6f2a34b87a0e5e17e539fad571a24a44",
    "9d880e115c6027d64bd161d0d16d95c19be07eee43d79222a6fc1628a8083ec6",
    "ac80774d7708df875754ca1919c869d98e3edef0c7a0778d9a0169aad1575c03",
]


class Order26ThreeEdgeSphericalTests(unittest.TestCase):
    def test_status_note_freezes_semantic_correction(self) -> None:
        text = STATUS_NOTE.read_text(encoding="utf-8")
        self.assertIn("simple and connected", text)
        self.assertIn("did **not** test the Euler characteristic", text)
        self.assertIn("`V - E + F = 0`", text)
        self.assertIn("orientable genus-one maps", text)
        self.assertIn("`V - E + F = 2`", text)
        self.assertIn("first plane-valid", text)
        self.assertIn("frontier obtained", text)

    def test_legacy_score470_parents_are_abstract_valid_genus_one_not_plane(self) -> None:
        fixed, parents, payload = k3.load_state_file(LEGACY_STATE_PATH)
        self.assertEqual(len(parents), 6)
        for state, alpha in zip(payload["states"], parents):
            self.assertEqual(state["breakdown"]["total"], 470)
            self.assertTrue(map_search._abstract_graph_ok(fixed, alpha))
            self.assertEqual(k3.euler_characteristic(fixed, alpha), 0)
            self.assertEqual(k3.plane_valid_gate(fixed, alpha), (False, "nonspherical"))

    def test_spec_hash_parent_provenance_and_budget_are_frozen(self) -> None:
        self.assertEqual(
            hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest(),
            "b11e30724450ff403e168401b8fb60c348398f434316c41f37cf62fb48ff16ea",
        )
        spec = spherical.load_spec(SPEC_PATH)
        self.assertEqual(spec["input_commit"], "a58ad734107ac6c9d453a20880b22754a489addd")
        self.assertEqual(spec["parent_result_sha256"], "96780eb9a1d947afd508025b150309eddcd4f4efd9fe85223efcd985cf3e8d8e")
        self.assertEqual(spec["fixed_state_sha256"], "77b5c304505d43576813bda3feda59d745b36a296d901223f842729dc9d4c1bb")
        self.assertEqual(spec["fixed_rotation_hash"], "aa82e2d913a9cc4c98a405fba9293a1440ae77f3acc40bbb6c6ff76f6b604346")
        self.assertEqual(spec["base_alpha_sha256"], "9115b20cf204b1ff18b321142d6bf5c13eaf0501336382aa98283d69a36ac23b")
        self.assertEqual(spec["parent_state_sha256"], PARENT_HASHES)
        self.assertEqual(spec["parent_count"], 6)
        self.assertEqual(spec["edges_per_parent"], 46)
        self.assertEqual(spec["triples_per_parent"], 15_180)
        self.assertEqual(spec["total_triples"], 91_080)
        self.assertEqual(spec["matchings_per_triple"], 8)
        self.assertEqual(spec["total_attempts"], 728_640)
        self.assertEqual(spec["frontier_limit"], 64)

    def test_spherical_parent_state_replays_all_alphas_scores_and_euler(self) -> None:
        self.assertEqual(k3.file_sha256(STATE_PATH), "29f82fc0da2285a99346c938cc0af63e225289ee8400b8ee99fec44815ff0e99")
        fixed, parents, payload = spherical.load_spherical_parents(STATE_PATH)
        self.assertEqual(payload["parent_result_sha256"], "96780eb9a1d947afd508025b150309eddcd4f4efd9fe85223efcd985cf3e8d8e")
        self.assertEqual(payload["fixed_rotation_hash"], "aa82e2d913a9cc4c98a405fba9293a1440ae77f3acc40bbb6c6ff76f6b604346")
        self.assertEqual(payload["base_alpha_sha256"], "9115b20cf204b1ff18b321142d6bf5c13eaf0501336382aa98283d69a36ac23b")
        self.assertEqual([state["state_sha256"] for state in payload["states"]], PARENT_HASHES)
        self.assertEqual(len(parents), 6)
        for state, alpha in zip(payload["states"], parents):
            self.assertEqual(len(k3.edge_pairs(alpha)), 46)
            self.assertEqual(
                state["breakdown"],
                {
                    "abstract_graph": 0,
                    "equal_face": 100,
                    "face_distribution": 160,
                    "hex": 180,
                    "total": 800,
                    "white": 360,
                },
            )
            self.assertTrue(state["abstract_graph_valid"])
            self.assertTrue(state["spherical"])
            self.assertEqual(state["euler_characteristic"], 2)
            self.assertTrue(map_search._abstract_graph_ok(fixed, alpha))
            self.assertEqual(k3.euler_characteristic(fixed, alpha), 2)
            self.assertEqual(k3.plane_valid_gate(fixed, alpha), (True, None))

    def test_builder_exactly_reproduces_committed_spherical_state(self) -> None:
        spec = spherical.load_spec(SPEC_PATH)
        rebuilt = spherical.build_spherical_state(spec, ROOT)
        committed = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(rebuilt, committed)

    def test_genus_one_parent_is_rejected_from_spherical_frontier(self) -> None:
        spherical_payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        legacy_payload = json.loads(LEGACY_STATE_PATH.read_text(encoding="utf-8"))
        replacement = copy.deepcopy(legacy_payload["states"][0])
        replacement.update(
            {
                "abstract_graph_valid": True,
                "spherical": False,
                "euler_characteristic": 0,
                "sphere_gate_reason": "nonspherical",
            }
        )
        spherical_payload["states"][0] = replacement
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "genus-one.json"
            path.write_text(json.dumps(spherical_payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nonspherical state"):
                spherical.load_spherical_parents(path)

    def test_stage_log_replays_spherical_state_and_exact_budget(self) -> None:
        log = json.loads(STAGE_LOG.read_text(encoding="utf-8"))
        self.assertEqual(log["spec_sha256"], "b11e30724450ff403e168401b8fb60c348398f434316c41f37cf62fb48ff16ea")
        self.assertEqual(log["target_state_sha256"], "29f82fc0da2285a99346c938cc0af63e225289ee8400b8ee99fec44815ff0e99")
        self.assertEqual(log["environment"]["uname"]["system"], "Linux")
        self.assertEqual(
            log["identities"],
            {
                "parents": 6,
                "edges_per_parent": 46,
                "triples_per_parent": 15_180,
                "total_triples": 91_080,
                "matchings_per_triple": 8,
                "total_attempts": 728_640,
            },
        )

    def test_complete_spherical_radius2_result_is_frozen(self) -> None:
        self.assertEqual(
            k3.file_sha256(RESULT_LOG),
            "3bae1402ddbe9563494609a16aacd4c5655fdee9ee8e16ab9a7b108aaaa503fa",
        )
        payload = json.loads(RESULT_LOG.read_text(encoding="utf-8"))
        result = payload["result"]
        spherical.validate_result(spherical.load_spec(SPEC_PATH), result)
        self.assertTrue(result["complete"])
        self.assertEqual(
            result["counts"],
            {
                "abstract_graph_prunes": 620_712,
                "attempts": 728_640,
                "distinct_graph_valid": 174,
                "duplicates": 0,
                "graph_invalid_prunes": 728_466,
                "nonspherical_prunes": 107_754,
                "raw_graph_valid": 174,
                "score_zero": 0,
                "zero_score_block_tools_rejections": 0,
                "zero_score_blocks_rejections": 0,
                "zero_score_cross_validated": 0,
                "zero_score_validation_rejections": 0,
            },
        )
        self.assertEqual(
            result["score_histogram_distinct"],
            {
                "780": 6,
                "800": 90,
                "840": 6,
                "860": 6,
                "890": 6,
                "920": 6,
                "980": 6,
                "1110": 6,
                "1130": 6,
                "1150": 6,
                "1160": 6,
                "1270": 6,
                "1280": 6,
                "1290": 6,
                "1320": 6,
            },
        )
        self.assertEqual(result["best_score"], 780)
        self.assertEqual(result["frontier_state_count"], 64)
        self.assertTrue(result["frontier_truncated"])
        frontier = result["frontier_states"]
        self.assertEqual(
            [(state["breakdown"]["total"], state["state_sha256"]) for state in frontier],
            sorted((state["breakdown"]["total"], state["state_sha256"]) for state in frontier),
        )
        minima = [state for state in frontier if state["breakdown"]["total"] == 780]
        self.assertEqual([state["state_sha256"] for state in minima], MINIMUM_HASHES)
        fixed, _, _ = spherical.load_spherical_parents(STATE_PATH)
        for state in frontier:
            self.assertEqual(k3.plane_valid_gate(fixed, state["alpha"]), (True, None))
            self.assertEqual(k3.euler_characteristic(fixed, state["alpha"]), 2)
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(payload["certificates"], {})


if __name__ == "__main__":
    unittest.main()
