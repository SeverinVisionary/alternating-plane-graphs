from __future__ import annotations

import json
import unittest
from pathlib import Path

import blocks
import near_open_search
import near_opening
from conftest import requires_upstream_corpus


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "certificates/search_seeds/upstream/34_30-30.plc"
SEED = ROOT / "results/near_openings/order30_34_fans_8_15.json"
RANKING = ROOT / "results/logs/near_opening_rankings/34_30-30.json"
SOURCE_SHA256 = "30780d7a870fd5736afa6c9cb3b223b4e70012d4c01f8ed7080c2dd8adf8080a"
SOURCE_URL = "https://www.althofer.de/apg/apgs/34_30-30.plc"
STATE_SHA256 = "4a0472b81b2a649ca6774205c6edc2bcac4dbafc6d0675665e210f489f8c82ab"


class NearOpenOrder30SetupTests(unittest.TestCase):
    @requires_upstream_corpus
    def test_source_seed_rotation_and_ranking_replay(self) -> None:
        self.assertEqual(near_opening.file_sha256(SOURCE), SOURCE_SHA256)
        expected = json.loads(SEED.read_text(encoding="utf-8"))
        replayed = near_opening.make_seed(
            SOURCE,
            expected_sha256=SOURCE_SHA256,
            source_url=SOURCE_URL,
            first=blocks.ClosureFan(8, (7, 9)),
            second=blocks.ClosureFan(15, (16, 17)),
        )
        self.assertEqual(replayed, expected)
        self.assertEqual(replayed["source"]["order"], 30)
        self.assertTrue(replayed["source"]["verified_apg"])
        self.assertEqual(replayed["state_sha256"], STATE_SHA256)
        self.assertEqual(
            replayed["fans"],
            [
                {"hub": 8, "leaves": [7, 9]},
                {"hub": 15, "leaves": [16, 17]},
            ],
        )
        self.assertEqual(
            replayed["hexagons"],
            [[3, 9, 11, 8, 6, 7], [4, 16, 18, 17, 14, 15]],
        )
        self.assertEqual(
            replayed["score_breakdown"],
            {
                "abstract_graph": 160,
                "equal_face": 0,
                "face_distribution": 0,
                "hex": 120,
                "total": 370,
                "white": 90,
            },
        )
        source_rotation = near_opening.import_rotation(SOURCE, SOURCE_SHA256)
        self.assertEqual(
            blocks.rotation_to_certificate(source_rotation)["vertices"],
            replayed["source_rotation"],
        )
        ranking = json.loads(RANKING.read_text(encoding="utf-8"))
        self.assertEqual(ranking["source_file"], "34_30-30.plc")
        self.assertEqual(ranking["source_sha256"], SOURCE_SHA256)
        self.assertEqual(ranking["source_url"], SOURCE_URL)
        self.assertEqual(ranking["order"], 30)
        self.assertEqual(ranking["fan_candidates"], 9)
        self.assertEqual(ranking["disjoint_fan_pairs"], 29)
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
        self.assertEqual(defect_edges, [(16, 18), (17, 18)])
        prediction = near_open_search.predicted_k4_structure(
            fixed,
            alpha,
            mandatory_edges=((16, 18), (17, 18)),
        )
        self.assertEqual(prediction["shared_vertex"], 18)
        self.assertEqual(prediction["shared_vertex_degree"], 4)
        self.assertEqual(prediction["offending_white_vertices"], [16, 17])
        self.assertEqual(prediction["offending_white_degrees"], [2, 2])
        self.assertEqual(
            prediction["edge_degree_pattern_counts"],
            {"2,4": 2, "2,5": 10, "3,4": 12, "3,5": 12, "4,5": 18},
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
