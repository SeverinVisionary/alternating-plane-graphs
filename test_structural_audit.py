#!/usr/bin/env python3
"""Known-answer tests for the exact APG structural audit."""

from __future__ import annotations

import unittest
from pathlib import Path

import structural_audit as audit


ROOT = Path(__file__).resolve().parent
RESULT_BLOCKS = ROOT / "results" / "blocks"
KNOWN = ("A21", "B22", "C23", "D24")


class StructuralAuditTests(unittest.TestCase):
    def test_all_known_blocks_match_the_closed_invariants_for_every_hub_choice(self) -> None:
        expected_order_and_r = {
            "A21": (21, 10),
            "B22": (22, 10),
            "C23": (23, 10),
            "D24": (24, 10),
        }
        for name in KNOWN:
            with self.subTest(block=name):
                data = audit.load_block(RESULT_BLOCKS / f"{name}.json")
                result = audit.analyze_block(data)
                self.assertEqual(result["variant_count"], 9)
                self.assertTrue(result["all_invariants_equal"])
                expected_order, expected_r = expected_order_and_r[name]
                for variant in result["variants"]:
                    self.assertEqual(variant["order"], expected_order)
                    self.assertEqual(variant["r"], expected_r)
                    self.assertEqual(variant["t_vertex"], 0)
                    self.assertEqual(variant["t_face"], 0)
                    self.assertEqual(variant["euler"], 2)
                    self.assertEqual(variant["faces"], expected_order)
                    self.assertTrue(variant["all_faces_simple"])
                    self.assertTrue(variant["corner_formula_matches"])
                    self.assertTrue(variant["edge_formula_matches"])
                    self.assertTrue(variant["core_matrix_matches_Y"])
                    self.assertEqual(variant["h55_component_sizes"], [6, 6])
                    self.assertTrue(variant["h55_all_degree_two"])
                    self.assertTrue(variant["port_components_distinct"])
                    self.assertTrue(variant["port_components_are_isolated_cycles"])
                    self.assertEqual(variant["boundary_edge_count"], 12)
                    self.assertEqual(variant["cap_edge_count"], 4)
                    for motif in variant["cap_motifs"]:
                        self.assertEqual(motif["hub_degree"], 4)
                        self.assertEqual(motif["leaf_degrees"], [3, 3])
                        self.assertEqual(
                            motif["cap_edge_face_sizes"], [[3, 4], [3, 4]]
                        )

    def test_t0_branch_table_is_explicit_and_not_an_implicit_pruning_rule(self) -> None:
        expected = {
            21: [(10, 6, 0, 0)],
            22: [(10, 4, 2, 2)],
            23: [(10, 2, 4, 4)],
            24: [(10, 0, 6, 6), (11, 7, 0, 2)],
            25: [(11, 5, 2, 4)],
            26: [(11, 3, 4, 6)],
            27: [(11, 1, 6, 8), (12, 8, 0, 4)],
            28: [(12, 6, 2, 6)],
            29: [(12, 4, 4, 8)],
            30: [(12, 2, 6, 10), (13, 9, 0, 6)],
            31: [(12, 0, 8, 12), (13, 7, 2, 8)],
            32: [(13, 5, 4, 10)],
            33: [(13, 3, 6, 12), (14, 10, 0, 8)],
            34: [(13, 1, 8, 14), (14, 8, 2, 10)],
            35: [(14, 6, 4, 12)],
            36: [(14, 4, 6, 14), (15, 11, 0, 10)],
        }
        for order, rows in expected.items():
            with self.subTest(order=order):
                actual = audit.feasible_t0_branches(order)
                self.assertEqual(
                    [
                        (row["r"], row["beta"], row["gamma"], row["epsilon"])
                        for row in actual
                    ],
                    rows,
                )

    def test_ordered_known_block_gluings_preserve_additive_t_and_h55_cycles(self) -> None:
        loaded = {
            name: audit.load_block(RESULT_BLOCKS / f"{name}.json")
            for name in KNOWN
        }
        rows = audit.gluing_t_audit(loaded)
        self.assertEqual(len(rows), 16)
        self.assertTrue(all(row["t_additive"] for row in rows))
        self.assertTrue(all(row["t_composed"] == 0 for row in rows))
        self.assertTrue(
            all(row["h55_component_sizes"] == [6, 6, 6, 6] for row in rows)
        )
        block_orders = dict(zip(KNOWN, (21, 22, 23, 24)))
        for row in rows:
            expected_order = block_orders[row["inner"]] + block_orders[row["outer"]] - 3
            self.assertEqual(row["order"], expected_order)


if __name__ == "__main__":
    unittest.main()
