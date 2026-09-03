from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import map_search
import order26_three_edge_spherical_radius4 as radius4
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "jobs/order26_three_edge_spherical_radius4.json"
PARENT_RESULT = ROOT / "results/logs/order26_three_edge_spherical_radius3.json"
STATE_PATH = ROOT / "results/targets/order26_three_edge_spherical_radius4_parents.json"
LEGACY_STATE_PATH = ROOT / "results/targets/order26_three_edge_parents.json"
STAGE_LOG = ROOT / "results/logs/order26_three_edge_spherical_radius4_stage.json"
RESULT_LOG = ROOT / "results/logs/order26_three_edge_spherical_radius4.json"


class Order26ThreeEdgeSphericalRadius4Tests(unittest.TestCase):
    def test_spec_provenance_manifest_and_exact_budget_are_frozen(self) -> None:
        self.assertEqual(
            hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest(),
            "3659190e001e3af296215c7c02922c6258427e4ec2ea1b9861c79f7c06c5822e",
        )
        spec = radius4.load_spec(SPEC_PATH)
        self.assertEqual(spec["input_commit"], "19f0881baf64d6cf9dd5c577a18b91da84c21ae9")
        self.assertEqual(spec["parent_result_sha256"], "ef42150945dbe902d1eea1a383557ba9d87076cb799ddedd3f22f2cab698148c")
        self.assertEqual(spec["parent_frontier_manifest_sha256"], "b47f3257feac229b3a44e35a209894d6600d50dd3c162e4c6e3800a0137ad62a")
        self.assertEqual(spec["fixed_state_sha256"], "5d39d7804f48bc1e2344656f680f6fb5f0703af1de73443902db2af69d8774d2")
        self.assertEqual(spec["fixed_rotation_hash"], "aa82e2d913a9cc4c98a405fba9293a1440ae77f3acc40bbb6c6ff76f6b604346")
        self.assertEqual(spec["base_alpha_sha256"], "9115b20cf204b1ff18b321142d6bf5c13eaf0501336382aa98283d69a36ac23b")
        self.assertEqual(spec["parent_count"], 64)
        self.assertEqual(spec["parent_score_histogram"], {"510": 4, "780": 60})
        self.assertEqual(spec["edges_per_parent"], 46)
        self.assertEqual(spec["triples_per_parent"], 15_180)
        self.assertEqual(spec["total_triples"], 971_520)
        self.assertEqual(spec["matchings_per_triple"], 8)
        self.assertEqual(spec["total_attempts"], 7_772_160)
        self.assertEqual(spec["frontier_limit"], 64)

    def test_all_64_parent_hashes_alphas_breakdowns_and_order_are_frozen(self) -> None:
        self.assertEqual(k3.file_sha256(PARENT_RESULT), "ef42150945dbe902d1eea1a383557ba9d87076cb799ddedd3f22f2cab698148c")
        parent = json.loads(PARENT_RESULT.read_text(encoding="utf-8"))["result"]
        frontier = parent["frontier_states"]
        self.assertEqual(len(frontier), 64)
        self.assertEqual(radius4.manifest_sha256(frontier), "b47f3257feac229b3a44e35a209894d6600d50dd3c162e4c6e3800a0137ad62a")
        self.assertEqual(
            [(state["breakdown"]["total"], state["state_sha256"]) for state in frontier],
            sorted((state["breakdown"]["total"], state["state_sha256"]) for state in frontier),
        )
        self.assertEqual(sum(state["breakdown"]["total"] == 510 for state in frontier), 4)
        self.assertEqual(sum(state["breakdown"]["total"] == 780 for state in frontier), 60)

        self.assertEqual(k3.file_sha256(STATE_PATH), "cfe788abcf2b63585bdcbc1a860ce08dcf7988380437caf5cf41461d36e133c7")
        fixed, parents, payload = radius4.load_radius4_parents(STATE_PATH)
        self.assertEqual(payload["parent_frontier_manifest_sha256"], "b47f3257feac229b3a44e35a209894d6600d50dd3c162e4c6e3800a0137ad62a")
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

    def test_builder_exactly_reproduces_committed_radius4_state(self) -> None:
        spec = radius4.load_spec(SPEC_PATH)
        self.assertEqual(
            radius4.build_radius4_state(spec, ROOT),
            json.loads(STATE_PATH.read_text(encoding="utf-8")),
        )

    def test_genus_one_state_cannot_enter_radius4_frontier(self) -> None:
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
                radius4.load_radius4_parents(path)

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
                    radius4.load_spec(path)

    def test_stage_log_replays_manifest_state_and_count_identities(self) -> None:
        log = json.loads(STAGE_LOG.read_text(encoding="utf-8"))
        self.assertEqual(log["spec_sha256"], "3659190e001e3af296215c7c02922c6258427e4ec2ea1b9861c79f7c06c5822e")
        self.assertEqual(log["target_state_sha256"], "cfe788abcf2b63585bdcbc1a860ce08dcf7988380437caf5cf41461d36e133c7")
        self.assertEqual(log["parent_frontier_manifest_sha256"], "b47f3257feac229b3a44e35a209894d6600d50dd3c162e4c6e3800a0137ad62a")
        self.assertEqual(log["environment"]["uname"]["system"], "Linux")
        self.assertEqual(
            log["identities"],
            {
                "parents": 64,
                "scores": {"510": 4, "780": 60},
                "edges_per_parent": 46,
                "triples_per_parent": 15_180,
                "total_triples": 971_520,
                "matchings_per_triple": 8,
                "total_attempts": 7_772_160,
            },
        )

    def test_complete_radius4_result_and_closed_family_are_frozen(self) -> None:
        self.assertEqual(
            k3.file_sha256(RESULT_LOG),
            "06f145c6b4c465c46943bb1f278acac364d8000f969e60f19a0a391646663e8a",
        )
        payload = json.loads(RESULT_LOG.read_text(encoding="utf-8"))
        result = payload["result"]
        radius4.validate_result(radius4.load_spec(SPEC_PATH), result)
        self.assertTrue(result["complete"])
        self.assertEqual(
            result["counts"],
            {
                "abstract_graph_prunes": 6_621_804,
                "attempts": 7_772_160,
                "distinct_graph_valid": 1_559,
                "duplicates": 317,
                "graph_invalid_prunes": 7_770_284,
                "nonspherical_prunes": 1_148_480,
                "raw_graph_valid": 1_876,
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
                "510": 56,
                "670": 4,
                "690": 4,
                "760": 4,
                "780": 583,
                "800": 60,
                "820": 4,
                "840": 112,
                "860": 60,
                "870": 4,
                "880": 8,
                "900": 4,
                "920": 4,
                "940": 56,
                "950": 4,
                "960": 56,
                "970": 4,
                "990": 4,
                "1020": 56,
                "1040": 4,
                "1080": 4,
                "1090": 56,
                "1100": 12,
                "1110": 60,
                "1120": 8,
                "1130": 112,
                "1160": 4,
                "1180": 8,
                "1250": 4,
                "1260": 56,
                "1270": 4,
                "1290": 8,
                "1300": 116,
                "1480": 4,
                "1520": 8,
                "1530": 4,
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
        self.assertEqual(len(minima), 56)
        minimum_hash_payload = (
            json.dumps([state["state_sha256"] for state in minima], separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(minimum_hash_payload).hexdigest(),
            "968d1eaee4a49549214a19c7cfe8262424604072884b43ec1a33ffb9ae6eb9ca",
        )
        expected_breakdown = {
            "abstract_graph": 0,
            "equal_face": 120,
            "face_distribution": 0,
            "hex": 0,
            "total": 510,
            "white": 390,
        }
        self.assertTrue(all(state["breakdown"] == expected_breakdown for state in minima))
        fixed, _, _ = radius4.load_radius4_parents(STATE_PATH)
        for state in frontier:
            self.assertEqual(k3.plane_valid_gate(fixed, state["alpha"]), (True, None))
            self.assertEqual(k3.euler_characteristic(fixed, state["alpha"]), 2)
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(payload["certificates"], {})
        status = (ROOT / "SEARCH_STATUS.md").read_text(encoding="utf-8")
        self.assertIn("plane-valid order-26 k3 family is closed after radius 4", status)


if __name__ == "__main__":
    unittest.main()
