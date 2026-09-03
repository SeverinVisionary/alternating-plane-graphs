from __future__ import annotations

import unittest
from pathlib import Path

import blocks
import map_search
import near_opening
from conftest import requires_upstream_corpus


ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT / "certificates" / "search_seeds" / "upstream"


class NearOpeningTests(unittest.TestCase):
    @requires_upstream_corpus
    def test_order26_target_seed_reproduces_exact_score_and_rotation(self) -> None:
        path = UPSTREAM / "27_26-26.plc"
        seed = near_opening.make_seed(
            path,
            expected_sha256="d78efd8db7aa415f36a15a9225cbf0b7c1bacfe096051514a7614edd683c4902",
            source_url="https://www.althofer.de/apg/apgs/27_26-26.plc",
            first=blocks.ClosureFan(1, (2, 4)),
            second=blocks.ClosureFan(24, (23, 25)),
        )
        self.assertEqual(
            seed["score_breakdown"],
            {
                "abstract_graph": 160,
                "equal_face": 0,
                "face_distribution": 0,
                "hex": 120,
                "total": 370,
                "white": 90,
            },
        )
        self.assertIn([10, 25, 22, 23, 21, 24], seed["hexagons"])
        fixed, alpha = near_opening.state_from_seed(seed)
        self.assertEqual(map_search.score_breakdown(fixed, alpha), seed["score_breakdown"])

    @requires_upstream_corpus

    def test_order33_target_seed_reproduces_exact_score(self) -> None:
        path = UPSTREAM / "44_33-33.plc"
        seed = near_opening.make_seed(
            path,
            expected_sha256="b779feb98cac0025bf165abd3b3d8e7968bff96bac5e428d17c7e1d07017a414",
            source_url="https://www.althofer.de/apg/apgs/44_33-33.plc",
            first=blocks.ClosureFan(1, (2, 4)),
            second=blocks.ClosureFan(8, (7, 9)),
        )
        self.assertEqual(seed["score_breakdown"]["face_distribution"], 0)
        self.assertEqual(seed["score_breakdown"]["total"], 460)
        fixed, alpha = near_opening.state_from_seed(seed)
        self.assertEqual(map_search.score_breakdown(fixed, alpha), seed["score_breakdown"])

    @requires_upstream_corpus

    def test_target_files_rank_every_disjoint_pair(self) -> None:
        cases = (
            (
                "27_26-26.plc",
                "d78efd8db7aa415f36a15a9225cbf0b7c1bacfe096051514a7614edd683c4902",
                7,
                18,
                370,
            ),
            (
                "44_33-33.plc",
                "b779feb98cac0025bf165abd3b3d8e7968bff96bac5e428d17c7e1d07017a414",
                10,
                36,
                460,
            ),
        )
        for filename, digest, fan_count, pair_count, best_score in cases:
            with self.subTest(filename=filename):
                ranking = near_opening.rank_openings(UPSTREAM / filename, digest)
                self.assertEqual(ranking["fan_candidates"], fan_count)
                self.assertEqual(ranking["disjoint_fan_pairs"], pair_count)
                self.assertEqual(ranking["records"][0]["score_breakdown"]["total"], best_score)


if __name__ == "__main__":
    unittest.main()
