from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import blocks
import map_search
import near_open_search
import near_opening
from conftest import requires_upstream_corpus


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "certificates/search_seeds/upstream/51_34-34.plc"
SEED = ROOT / "results/near_openings/order34_51_fans_8_32.json"
RANKING = ROOT / "results/logs/near_opening_rankings/51_34-34.json"
SOURCE_SHA256 = "1f2670651eb62019115375bacd8335aaedf3e711ec6e9f4173ca1fce5e605f76"
SOURCE_URL = "https://www.althofer.de/apg/apgs/51_34-34.plc"
STATE_SHA256 = "938ee94260c196b7f4fb9aef81ca3fab0aaeb67b92dc2bf520cb087a029aaa93"


class NearOpenOrder34SetupTests(unittest.TestCase):
    def test_exact_k4_result_replays(self) -> None:
        seed = json.loads(SEED.read_text(encoding="utf-8"))
        fixed, _ = near_opening.state_from_seed(seed)
        log = json.loads(
            (ROOT / "results/logs/order34_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(log["source"]["sha256"], SOURCE_SHA256)
        self.assertEqual(log["source"]["state_sha256"], STATE_SHA256)
        result = log["result"]
        counts = result["counts"]
        self.assertEqual(result["mandatory_edges"], [[5, 6], [5, 10]])
        self.assertEqual(result["donor_edges"], 12)
        self.assertEqual(counts["donor_pair_attempts"], 66)
        self.assertEqual(counts["perfect_rematching_attempts"], 6930)
        self.assertEqual(counts["pruned_original_matching"], 66)
        self.assertEqual(counts["pruned_overlapping_selected_edges"], 0)
        self.assertEqual(counts["pruned_abstract_graph"], 6728)
        self.assertEqual(counts["graph_valid_candidates"], 136)
        self.assertEqual(counts["duplicate_graph_valid_candidates"], 0)
        self.assertEqual(counts["distinct_graph_valid_candidates"], 136)
        self.assertEqual(counts["zero_score_candidates"], 0)
        self.assertEqual(counts["zero_score_cross_validated"], 0)
        self.assertEqual(result["success_hashes"], [])
        self.assertEqual(result["success_checks"], {})
        self.assertEqual(sum(result["score_histogram"].values()), 136)
        histogram_manifest = hashlib.sha256(
            json.dumps(
                result["score_histogram"], sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        self.assertEqual(
            histogram_manifest,
            "cf5a37e69e05e5fb83f990dc6f1fc467e519b6c3d3b16d61c9ad16e7614adcc5",
        )
        self.assertEqual(result["best_score"], 1500)
        self.assertEqual(result["best_state_count"], 2)
        frontier = result["frontier_states"]
        self.assertEqual(len(frontier), 64)
        keys = []
        for state in frontier:
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
            keys[:2],
            [
                (
                    1500,
                    "3ab7444c3e518771a34870c0267c0f4cbb70923f8252aba7fef82bccd615af41",
                ),
                (
                    1500,
                    "960dd274ebd1b4b123e444858956347349b37e368c1d575fa4e01dd86e8e7b29",
                ),
            ],
        )
        payload = [
            {
                "state_sha256": state["state_sha256"],
                "score_breakdown": state["breakdown"],
            }
            for state in frontier
        ]
        manifest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self.assertEqual(
            manifest,
            "1f5d7f9c56720ce8ef0797706dfdb143050707ee80948144c0801f6a5b536678",
        )

    @requires_upstream_corpus

    def test_source_seed_rotation_and_ranking_replay(self) -> None:
        self.assertEqual(near_opening.file_sha256(SOURCE), SOURCE_SHA256)
        expected = json.loads(SEED.read_text(encoding="utf-8"))
        replayed = near_opening.make_seed(
            SOURCE,
            expected_sha256=SOURCE_SHA256,
            source_url=SOURCE_URL,
            first=blocks.ClosureFan(8, (6, 10)),
            second=blocks.ClosureFan(32, (33, 34)),
        )
        self.assertEqual(replayed, expected)
        self.assertEqual(replayed["source"]["order"], 34)
        self.assertTrue(replayed["source"]["verified_apg"])
        self.assertEqual(replayed["state_sha256"], STATE_SHA256)
        self.assertEqual(
            replayed["fans"],
            [
                {"hub": 8, "leaves": [6, 10]},
                {"hub": 32, "leaves": [33, 34]},
            ],
        )
        self.assertEqual(
            replayed["hexagons"],
            [[5, 6, 7, 8, 11, 10], [20, 33, 27, 34, 31, 32]],
        )
        self.assertEqual(
            replayed["score_breakdown"],
            {
                "abstract_graph": 160,
                "equal_face": 0,
                "face_distribution": 0,
                "hex": 120,
                "total": 460,
                "white": 180,
            },
        )
        source_rotation = near_opening.import_rotation(SOURCE, SOURCE_SHA256)
        self.assertEqual(
            blocks.rotation_to_certificate(source_rotation)["vertices"],
            replayed["source_rotation"],
        )
        ranking = json.loads(RANKING.read_text(encoding="utf-8"))
        self.assertEqual(ranking["source_file"], "51_34-34.plc")
        self.assertEqual(ranking["source_sha256"], SOURCE_SHA256)
        self.assertEqual(ranking["source_url"], SOURCE_URL)
        self.assertEqual(ranking["order"], 34)
        self.assertEqual(ranking["fan_candidates"], 13)
        self.assertEqual(ranking["disjoint_fan_pairs"], 53)
        self.assertEqual(
            ranking["records"][0],
            {
                "fans": replayed["fans"],
                "score_breakdown": replayed["score_breakdown"],
                "state_sha256": STATE_SHA256,
                "zero_validation": None,
            },
        )

    def test_structural_defect_and_minimal_k4_recipe(self) -> None:
        seed = json.loads(SEED.read_text(encoding="utf-8"))
        fixed, alpha = near_opening.state_from_seed(seed)
        edge_representatives = near_open_search._edge_representatives(fixed, alpha)
        defect_edges = [
            edge
            for edge in sorted(edge_representatives)
            if sorted(fixed.vertex_degree[vertex - 1] for vertex in edge) == [2, 4]
        ]
        self.assertEqual(defect_edges, [(5, 6), (5, 10)])
        prediction = near_open_search.predicted_k4_structure(
            fixed,
            alpha,
            mandatory_edges=((5, 6), (5, 10)),
        )
        self.assertEqual(prediction["hexagons"][0], [5, 6, 7, 8, 11, 10])
        self.assertEqual(prediction["shared_vertex"], 5)
        self.assertEqual(prediction["shared_vertex_degree"], 4)
        self.assertEqual(prediction["offending_white_vertices"], [6, 10])
        self.assertEqual(prediction["offending_white_degrees"], [2, 2])
        self.assertEqual(
            prediction["edge_degree_pattern_counts"],
            {"2,4": 2, "2,5": 10, "3,4": 15, "3,5": 12, "4,5": 23},
        )
        self.assertEqual(
            prediction["maximum_degree5_endpoints_from_one_additional_edge"],
            1,
        )
        self.assertEqual(prediction["degree5_endpoints_required"], 2)
        self.assertTrue(prediction["k3_impossible"])
        donor_edges = [
            edge
            for edge in edge_representatives
            if sorted(fixed.vertex_degree[vertex - 1] for vertex in edge) == [3, 5]
        ]
        self.assertEqual(len(donor_edges), 12)


if __name__ == "__main__":
    unittest.main()
