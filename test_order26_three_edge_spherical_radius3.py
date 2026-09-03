from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import map_search
import order26_three_edge_spherical_radius3 as radius3
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "jobs/order26_three_edge_spherical_radius3.json"
PARENT_RESULT = ROOT / "results/logs/order26_three_edge_spherical_radius2.json"
STATE_PATH = ROOT / "results/targets/order26_three_edge_spherical_radius3_parents.json"
LEGACY_STATE_PATH = ROOT / "results/targets/order26_three_edge_parents.json"
STAGE_LOG = ROOT / "results/logs/order26_three_edge_spherical_radius3_stage.json"
RESULT_LOG = ROOT / "results/logs/order26_three_edge_spherical_radius3.json"
MINIMUM_HASHES = [
    "6752b9f958ff846f3d4a0534871582d69388f225d53163f5a18c1d284d8dbb23",
    "9148bc29266b2f048c3fa40185dbd45415186516847b1d4366641cea9e96897e",
    "c0700d86b3ba5670d24b6fac520f1161c05272311583f8795314c0109c4059f8",
    "cb6de8cc359a3ecfa9b1f03e6170306f97dc0023e061a5beec34d8e5db54488f",
]


class Order26ThreeEdgeSphericalRadius3Tests(unittest.TestCase):
    def test_spec_provenance_manifest_and_exact_budget_are_frozen(self) -> None:
        self.assertEqual(
            hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest(),
            "a5edc0c8159e526feb064006e4daedab600bf2b40d67a42897dc1e663e74572e",
        )
        spec = radius3.load_spec(SPEC_PATH)
        self.assertEqual(spec["input_commit"], "333c343f3e38e3a2b0721fbd97f9d97d97a6d52f")
        self.assertEqual(spec["parent_result_sha256"], "3bae1402ddbe9563494609a16aacd4c5655fdee9ee8e16ab9a7b108aaaa503fa")
        self.assertEqual(spec["parent_frontier_manifest_sha256"], "7f5debfc24c524143ecccb4503cb3ecbabcc30ba7a1f2e4d7259529e9091a50f")
        self.assertEqual(spec["fixed_state_sha256"], "29f82fc0da2285a99346c938cc0af63e225289ee8400b8ee99fec44815ff0e99")
        self.assertEqual(spec["fixed_rotation_hash"], "aa82e2d913a9cc4c98a405fba9293a1440ae77f3acc40bbb6c6ff76f6b604346")
        self.assertEqual(spec["base_alpha_sha256"], "9115b20cf204b1ff18b321142d6bf5c13eaf0501336382aa98283d69a36ac23b")
        self.assertEqual(spec["parent_count"], 64)
        self.assertEqual(spec["parent_score_histogram"], {"780": 6, "800": 58})
        self.assertEqual(spec["edges_per_parent"], 46)
        self.assertEqual(spec["triples_per_parent"], 15_180)
        self.assertEqual(spec["total_triples"], 971_520)
        self.assertEqual(spec["matchings_per_triple"], 8)
        self.assertEqual(spec["total_attempts"], 7_772_160)
        self.assertEqual(spec["frontier_limit"], 64)

    def test_all_64_parent_hashes_alphas_breakdowns_and_order_are_frozen(self) -> None:
        self.assertEqual(k3.file_sha256(PARENT_RESULT), "3bae1402ddbe9563494609a16aacd4c5655fdee9ee8e16ab9a7b108aaaa503fa")
        parent = json.loads(PARENT_RESULT.read_text(encoding="utf-8"))["result"]
        frontier = parent["frontier_states"]
        self.assertEqual(len(frontier), 64)
        self.assertEqual(radius3.manifest_sha256(frontier), "7f5debfc24c524143ecccb4503cb3ecbabcc30ba7a1f2e4d7259529e9091a50f")
        self.assertEqual(
            [(state["breakdown"]["total"], state["state_sha256"]) for state in frontier],
            sorted((state["breakdown"]["total"], state["state_sha256"]) for state in frontier),
        )
        self.assertEqual(sum(state["breakdown"]["total"] == 780 for state in frontier), 6)
        self.assertEqual(sum(state["breakdown"]["total"] == 800 for state in frontier), 58)

        self.assertEqual(k3.file_sha256(STATE_PATH), "5d39d7804f48bc1e2344656f680f6fb5f0703af1de73443902db2af69d8774d2")
        fixed, parents, payload = radius3.load_radius3_parents(STATE_PATH)
        self.assertEqual(payload["parent_frontier_manifest_sha256"], "7f5debfc24c524143ecccb4503cb3ecbabcc30ba7a1f2e4d7259529e9091a50f")
        self.assertEqual(payload["fixed_rotation_hash"], "aa82e2d913a9cc4c98a405fba9293a1440ae77f3acc40bbb6c6ff76f6b604346")
        self.assertEqual(payload["base_alpha_sha256"], "9115b20cf204b1ff18b321142d6bf5c13eaf0501336382aa98283d69a36ac23b")
        self.assertEqual(len(parents), 64)
        for source, committed, alpha in zip(frontier, payload["states"], parents):
            self.assertEqual(committed["state_sha256"], source["state_sha256"])
            self.assertEqual(committed["alpha"], source["alpha"])
            self.assertEqual(committed["breakdown"], source["breakdown"])
            self.assertTrue(committed["abstract_graph_valid"])
            self.assertTrue(committed["spherical"])
            self.assertEqual(committed["euler_characteristic"], 2)
            self.assertTrue(map_search._abstract_graph_ok(fixed, alpha))
            self.assertEqual(k3.euler_characteristic(fixed, alpha), 2)
            self.assertEqual(k3.plane_valid_gate(fixed, alpha), (True, None))

    def test_builder_exactly_reproduces_committed_radius3_state(self) -> None:
        spec = radius3.load_spec(SPEC_PATH)
        self.assertEqual(
            radius3.build_radius3_state(spec, ROOT),
            json.loads(STATE_PATH.read_text(encoding="utf-8")),
        )

    def test_genus_one_state_cannot_enter_radius3_frontier(self) -> None:
        payload = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        legacy = json.loads(LEGACY_STATE_PATH.read_text(encoding="utf-8"))
        replacement = copy.deepcopy(legacy["states"][0])
        replacement.update(
            {
                "abstract_graph_valid": True,
                "spherical": False,
                "euler_characteristic": 0,
                "sphere_gate_reason": "nonspherical",
            }
        )
        payload["states"][0] = replacement
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "genus-one.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "nonspherical state"):
                radius3.load_radius3_parents(path)

    def test_no_sampling_cap_or_budget_drift_is_accepted(self) -> None:
        spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        for key, value in (
            ("parent_count", 63),
            ("total_triples", 971_519),
            ("matchings_per_triple", 7),
            ("total_attempts", 7_772_159),
            ("frontier_limit", 63),
        ):
            mutated = copy.deepcopy(spec)
            mutated[key] = value
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "bad-spec.json"
                path.write_text(json.dumps(mutated), encoding="utf-8")
                with self.assertRaises(ValueError):
                    radius3.load_spec(path)

    def test_stage_log_replays_manifest_state_and_count_identities(self) -> None:
        log = json.loads(STAGE_LOG.read_text(encoding="utf-8"))
        self.assertEqual(log["spec_sha256"], "a5edc0c8159e526feb064006e4daedab600bf2b40d67a42897dc1e663e74572e")
        self.assertEqual(log["target_state_sha256"], "5d39d7804f48bc1e2344656f680f6fb5f0703af1de73443902db2af69d8774d2")
        self.assertEqual(log["parent_frontier_manifest_sha256"], "7f5debfc24c524143ecccb4503cb3ecbabcc30ba7a1f2e4d7259529e9091a50f")
        self.assertEqual(log["environment"]["uname"]["system"], "Linux")
        self.assertEqual(
            log["identities"],
            {
                "parents": 64,
                "scores": {"780": 6, "800": 58},
                "edges_per_parent": 46,
                "triples_per_parent": 15_180,
                "total_triples": 971_520,
                "matchings_per_triple": 8,
                "total_attempts": 7_772_160,
            },
        )

    def test_complete_radius3_result_counters_histogram_and_frontier_are_frozen(self) -> None:
        self.assertEqual(
            k3.file_sha256(RESULT_LOG),
            "ef42150945dbe902d1eea1a383557ba9d87076cb799ddedd3f22f2cab698148c",
        )
        payload = json.loads(RESULT_LOG.read_text(encoding="utf-8"))
        result = payload["result"]
        radius3.validate_result(radius3.load_spec(SPEC_PATH), result)
        self.assertTrue(result["complete"])
        self.assertEqual(
            result["counts"],
            {
                "abstract_graph_prunes": 6_621_150,
                "attempts": 7_772_160,
                "distinct_graph_valid": 1_498,
                "duplicates": 362,
                "graph_invalid_prunes": 7_770_300,
                "nonspherical_prunes": 1_149_150,
                "raw_graph_valid": 1_860,
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
                "510": 4,
                "780": 90,
                "800": 572,
                "820": 8,
                "840": 66,
                "860": 64,
                "880": 4,
                "890": 54,
                "920": 54,
                "940": 6,
                "960": 6,
                "980": 54,
                "1020": 6,
                "1060": 4,
                "1090": 6,
                "1110": 64,
                "1130": 74,
                "1150": 54,
                "1160": 58,
                "1170": 4,
                "1260": 6,
                "1270": 54,
                "1280": 54,
                "1290": 58,
                "1300": 16,
                "1320": 54,
                "1400": 4,
            },
        )
        self.assertEqual(result["best_score"], 510)
        self.assertEqual(result["frontier_state_count"], 64)
        self.assertTrue(result["frontier_truncated"])
        frontier = result["frontier_states"]
        self.assertEqual(
            [(state["breakdown"]["total"], state["state_sha256"]) for state in frontier],
            sorted((state["breakdown"]["total"], state["state_sha256"]) for state in frontier),
        )
        minima = [state for state in frontier if state["breakdown"]["total"] == 510]
        self.assertEqual([state["state_sha256"] for state in minima], MINIMUM_HASHES)
        expected_breakdown = {
            "abstract_graph": 0,
            "equal_face": 120,
            "face_distribution": 0,
            "hex": 0,
            "total": 510,
            "white": 390,
        }
        self.assertTrue(all(state["breakdown"] == expected_breakdown for state in minima))
        fixed, _, _ = radius3.load_radius3_parents(STATE_PATH)
        for state in frontier:
            self.assertEqual(k3.plane_valid_gate(fixed, state["alpha"]), (True, None))
            self.assertEqual(k3.euler_characteristic(fixed, state["alpha"]), 2)
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(payload["certificates"], {})


if __name__ == "__main__":
    unittest.main()
