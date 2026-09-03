#!/usr/bin/env python3
"""Regression tests for the manifest-indexed public-source census."""

from __future__ import annotations

import unittest

import source_census
from conftest import requires_upstream_corpus


class SourceCensusTests(unittest.TestCase):
    @requires_upstream_corpus
    def test_all_manifest_sources_verify_and_have_reproducible_signatures(self) -> None:
        expected = {
            "27_26-26.plc": (26, 11, 1, 7, 18),
            "28_26-26.plc": (26, 11, 1, 7, 18),
            "29_27-27.plc": (27, 11, 2, 10, 32),
            "30_28-28.plc": (28, 11, 3, 13, 52),
            "31_29-29.plc": (29, 12, 2, 7, 17),
            "32_29-29.plc": (29, 12, 2, 7, 18),
            "34_30-30.plc": (30, 12, 2, 9, 29),
            "36_30-30.plc": (30, 12, 2, 9, 29),
            "38_31-31.plc": (31, 12, 4, 12, 51),
            "39_32-32.plc": (32, 12, 3, 14, 62),
            "40_32-32.plc": (32, 13, 2, 8, 21),
            "41_32-32.plc": (32, 13, 2, 8, 21),
            "44_33-33.plc": (33, 13, 2, 10, 36),
            "45_33-33.plc": (33, 13, 2, 10, 35),
            "51_34-34.plc": (34, 13, 2, 13, 53),
            "52_34-34.plc": (34, 13, 2, 11, 44),
            "56_35-35.plc": (35, 13, 2, 12, 52),
            "60_36-36.plc": (36, 14, 2, 10, 34),
            "61_36-36.plc": (36, 14, 2, 10, 32),
        }
        result = source_census.build_census()
        self.assertEqual(result["summary"]["published_embeddings"], 19)
        self.assertEqual(result["summary"]["verified_embeddings"], 19)
        self.assertEqual(result["summary"]["verification_failures"], 0)
        self.assertEqual(result["summary"]["strict_blocks_total"], 0)
        self.assertEqual(len(result["records"]), len(expected))

        for record in result["records"]:
            with self.subTest(file=record["file"]):
                self.assertTrue(record["verified"])
                stats = record["stats"]
                signature = stats["signature"]
                self.assertTrue(stats["edge_formula_matches"])
                self.assertEqual(stats["relaxed_openings"], 0)
                self.assertEqual(signature["relaxed_openings"], 0)
                self.assertEqual(signature["mirrored_strict_blocks"], 0)
                self.assertEqual(signature["mirrored_relaxed_openings"], 0)
                self.assertEqual(stats["t_vertex"], stats["t_face"])
                self.assertEqual(
                    (
                        stats["order"],
                        stats["r"],
                        stats["t_vertex"],
                        signature["fan_candidates"],
                        signature["disjoint_fan_pairs"],
                    ),
                    expected[record["file"]],
                )


if __name__ == "__main__":
    unittest.main()
