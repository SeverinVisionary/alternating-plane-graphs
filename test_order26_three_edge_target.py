from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import order26_three_edge_target as target
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "jobs/order26_three_edge_all_triples.json"
STATE_PATH = ROOT / "results/targets/order26_three_edge_parents.json"
STAGE_LOG = ROOT / "results/logs/order26_three_edge_stage.json"
RESULT_LOG = ROOT / "results/logs/order26_three_edge_all_triples.json"
PARENT_HASHES = [
    "5ea1cc9a0cce8ff69386b3bd0fe623d3efaa8fcdc429319474c9ab67297f1bc4",
    "a5522bf00ed7e9730583405e6fa72d62ec1fceb9a67638feed413fc9e6fd15f1",
    "d337ec944b935bb8f473e35269907cbb2413b9fa4488754df52372b9d6ebab4a",
    "e91984c9ca36143cfb7c128d56bdf7116e6c2d735b69e702b76c6c1fa9e066a8",
    "ee24f1a2e77f4fadba9904102a91d1670669e1ccaa55693e4fffa69eab652ced",
    "f47b7c1a84035d3c674dd54575c914dc3f39574251a3439d697d8a71328bac0e",
]


class Order26ThreeEdgeTargetTests(unittest.TestCase):
    def test_spec_hash_provenance_and_exact_count_identities(self) -> None:
        self.assertEqual(
            hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest(),
            "8dba266aa5ed7610730acd919a721222bb6d375052198c0ae8615bb71668ea03",
        )
        spec = target.load_spec(SPEC_PATH)
        self.assertEqual(spec["input_commit"], "b9d0c5ec676843a1db2cd0ec38fd4de5089463e1")
        self.assertEqual(spec["source"]["url"], "https://www.althofer.de/apg/apgs/27_26-26.plc")
        self.assertEqual(spec["source"]["sha256"], "d78efd8db7aa415f36a15a9225cbf0b7c1bacfe096051514a7614edd683c4902")
        self.assertEqual(spec["seed_file_sha256"], "db44db0882c38e98ff94b40e42230c81f57e72d82cb5e0e221a499e57cd280c9")
        self.assertEqual(spec["frontier_log_sha256"], "e62332c8b3c4524994bf98a7faa25f6afce62ad227b5378dca1f0d3adbe954de")
        self.assertEqual(spec["parent_state_sha256"], PARENT_HASHES)
        self.assertEqual(spec["parent_count"], 6)
        self.assertEqual(spec["edges_per_parent"], 46)
        self.assertEqual(spec["triples_per_parent"], 15_180)
        self.assertEqual(spec["total_triples"], 91_080)
        self.assertEqual(spec["matchings_per_triple"], 8)
        self.assertEqual(spec["total_attempts"], 728_640)
        self.assertEqual(spec["frontier_limit"], 64)

    def test_target_state_replays_rotation_alphas_scores_and_validity(self) -> None:
        self.assertEqual(k3.file_sha256(STATE_PATH), "77b5c304505d43576813bda3feda59d745b36a296d901223f842729dc9d4c1bb")
        fixed, alphas, payload = k3.load_state_file(STATE_PATH)
        self.assertEqual(payload["source"]["url"], "https://www.althofer.de/apg/apgs/27_26-26.plc")
        self.assertEqual(payload["source"]["sha256"], "d78efd8db7aa415f36a15a9225cbf0b7c1bacfe096051514a7614edd683c4902")
        self.assertEqual(payload["seed_file_sha256"], "db44db0882c38e98ff94b40e42230c81f57e72d82cb5e0e221a499e57cd280c9")
        self.assertEqual(payload["frontier_log_sha256"], "e62332c8b3c4524994bf98a7faa25f6afce62ad227b5378dca1f0d3adbe954de")
        self.assertEqual(payload["fixed_rotation_hash"], "aa82e2d913a9cc4c98a405fba9293a1440ae77f3acc40bbb6c6ff76f6b604346")
        self.assertEqual(payload["base_alpha_sha256"], "9115b20cf204b1ff18b321142d6bf5c13eaf0501336382aa98283d69a36ac23b")
        self.assertEqual(payload["order"], 26)
        self.assertEqual(payload["edges"], 46)
        self.assertEqual(len(fixed.cycles), 26)
        self.assertEqual(len(alphas), 6)
        self.assertEqual([state["state_sha256"] for state in payload["states"]], PARENT_HASHES)
        for alpha, state in zip(alphas, payload["states"]):
            self.assertEqual(len(k3.edge_pairs(alpha)), 46)
            self.assertEqual(state["breakdown"], {
                "abstract_graph": 0,
                "equal_face": 40,
                "face_distribution": 160,
                "hex": 0,
                "total": 470,
                "white": 270,
            })
            self.assertTrue(state["graph_valid"])
            self.assertTrue(state["abstract_graph_valid"])
            self.assertFalse(state["spherical"])
            self.assertEqual(state["sphere_gate_reason"], "nonspherical")

    def test_builder_exactly_reproduces_committed_target_state(self) -> None:
        spec = target.load_spec(SPEC_PATH)
        rebuilt = target.build_target_state(spec, ROOT)
        committed = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(rebuilt, committed)

    def test_stage_log_replays_spec_state_and_environment(self) -> None:
        log = json.loads(STAGE_LOG.read_text(encoding="utf-8"))
        self.assertEqual(log["spec_sha256"], "8dba266aa5ed7610730acd919a721222bb6d375052198c0ae8615bb71668ea03")
        self.assertEqual(log["target_state_sha256"], "77b5c304505d43576813bda3feda59d745b36a296d901223f842729dc9d4c1bb")
        self.assertEqual(log["environment"]["uname"]["system"], "Linux")
        self.assertEqual(log["identities"], {
            "parents": 6,
            "edges_per_parent": 46,
            "triples_per_parent": 15_180,
            "total_triples": 91_080,
            "matchings_per_triple": 8,
            "total_attempts": 728_640,
        })

    def test_wrong_budget_or_unfrozen_state_hash_is_rejected(self) -> None:
        original = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        cases = []
        wrong_budget = copy.deepcopy(original)
        wrong_budget["total_attempts"] -= 8
        cases.append(wrong_budget)
        missing_hash = copy.deepcopy(original)
        missing_hash["target_state_sha256"] = "TO_BE_FILLED"
        cases.append(missing_hash)
        with tempfile.TemporaryDirectory() as directory:
            for index, payload in enumerate(cases):
                path = Path(directory) / f"bad-{index}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(ValueError):
                    target.load_spec(path)

    def test_result_accounting_gate_accepts_only_complete_exact_counts(self) -> None:
        spec = target.load_spec(SPEC_PATH)
        result = {
            "parent_count": 6,
            "edges": 46,
            "triples": 91_080,
            "matchings_per_triple": 8,
            "expected_attempts": 728_640,
            "counts": {
                "attempts": 728_640,
                "graph_invalid_prunes": 700_000,
                "raw_graph_valid": 28_640,
                "duplicates": 640,
                "distinct_graph_valid": 28_000,
            },
        }
        target.validate_result(spec, result)
        incomplete = copy.deepcopy(result)
        incomplete["counts"]["attempts"] -= 1
        with self.assertRaises(AssertionError):
            target.validate_result(spec, incomplete)

    def test_committed_complete_result_counters_histogram_and_frontier(self) -> None:
        payload = json.loads(RESULT_LOG.read_text(encoding="utf-8"))
        result = payload["result"]
        self.assertEqual(payload["spec_sha256"], "8dba266aa5ed7610730acd919a721222bb6d375052198c0ae8615bb71668ea03")
        self.assertEqual(payload["target_state_sha256"], "77b5c304505d43576813bda3feda59d745b36a296d901223f842729dc9d4c1bb")
        self.assertEqual(payload["environment"]["uname"]["system"], "Linux")
        self.assertEqual(payload["certificates"], {})
        self.assertTrue(result["complete"])
        self.assertEqual(result["mode"], "all-triples")
        self.assertEqual(result["parent_count"], 6)
        self.assertEqual(result["edges"], 46)
        self.assertEqual(result["triples"], 91_080)
        self.assertEqual(result["matchings_per_triple"], 8)
        self.assertEqual(result["expected_attempts"], 728_640)
        self.assertEqual(
            result["counts"],
            {
                "abstract_graph_prunes": 621294,
                "attempts": 728640,
                "distinct_graph_valid": 6,
                "duplicates": 0,
                "graph_invalid_prunes": 728634,
                "nonspherical_prunes": 107340,
                "raw_graph_valid": 6,
                "score_zero": 0,
                "zero_score_block_tools_rejections": 0,
                "zero_score_blocks_rejections": 0,
                "zero_score_cross_validated": 0,
                "zero_score_validation_rejections": 0,
            },
        )
        self.assertEqual(result["score_histogram_distinct"], {"800": 6})
        self.assertEqual(result["best_score"], 800)
        self.assertEqual(result["frontier_limit"], 64)
        self.assertEqual(result["frontier_state_count"], 6)
        self.assertFalse(result["frontier_truncated"])
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        expected_hashes = [
            "45bf7f1e438f78754fed51a14a9216c597ca3abb8ed6b2af49b222adbaaf504d",
            "6ad19ef9780de6b2ce485d63c2be6e2cd24106b439b35665d1dd82dd7e067897",
            "c3575c39d9356848d0f16b0d6b6b6b1cb97b1ba73e260a39b85fda6b18bf7917",
            "ce50c9b6128731cbf0c887143b64e5cd57922001823011065d7b3f3172510a8d",
            "d907d54800393986e357948244a28d8b6f371361beb83a078b43555ade335dbe",
            "e19cb3ccfcf8837437d9488e21900e72a9b0bfda1ae26e3ca73dc2be4368535e",
        ]
        self.assertEqual(
            [state["state_sha256"] for state in result["frontier_states"]],
            expected_hashes,
        )
        self.assertEqual(
            [state["parent_index"] for state in result["frontier_states"]],
            [5, 4, 3, 1, 0, 2],
        )
        fixed, _, _ = k3.load_state_file(STATE_PATH)
        for state in result["frontier_states"]:
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
            self.assertEqual(state["selected_pairs"], [[21, 79], [24, 82], [56, 78]])
            self.assertEqual(state["matching"], [[21, 24], [56, 79], [78, 82]])
            self.assertEqual(k3.plane_valid_gate(fixed, state["alpha"]), (True, None))
        target.validate_result(target.load_spec(SPEC_PATH), result)


if __name__ == "__main__":
    unittest.main()
