#!/usr/bin/env python3
"""Pure arithmetic controls for the Section-8 block-profile filter."""

from __future__ import annotations

import unittest

import section8_profiles as profiles


class Section8ProfileTests(unittest.TestCase):
    def test_port_argument_forces_only_the_small_residual_cases(self) -> None:
        self.assertEqual(profiles.strict_port_forced_t(10), 0)
        self.assertEqual(profiles.strict_port_forced_t(11), 1)
        self.assertIsNone(profiles.strict_port_forced_t(12))

    def test_portable_r12_has_the_derived_residual_h55_c4(self) -> None:
        self.assertEqual(profiles.strict_portable_t0_residual_h55_cycle_size(12), 4)
        self.assertIsNone(profiles.strict_portable_t0_residual_h55_cycle_size(10))
        self.assertIsNone(profiles.strict_portable_t0_residual_h55_cycle_size(11))
        self.assertIsNone(profiles.strict_portable_t0_residual_h55_cycle_size(13))

    def test_portable_r12_and_above_have_a_2regular_residual_h55(self) -> None:
        self.assertFalse(profiles.strict_portable_t0_residual_h55_is_2regular(10))
        self.assertFalse(profiles.strict_portable_t0_residual_h55_is_2regular(11))
        self.assertTrue(profiles.strict_portable_t0_residual_h55_is_2regular(12))
        self.assertTrue(profiles.strict_portable_t0_residual_h55_is_2regular(13))
        self.assertTrue(profiles.strict_portable_t0_residual_h55_is_2regular(14))

    def test_order25_r10_fails_the_unconditional_port_then_core_gate(self) -> None:
        # At r=10 the two strict ports consume every degree-5 vertex and every
        # pentagon, so t=0 is forced.  The resulting core has beta=-2, which
        # rules out this particular strict profile without assuming that it is
        # reusable indefinitely.
        self.assertEqual(profiles.strict_port_forced_t(10), 0)
        self.assertEqual(profiles.t0_core_parameters(25, 10), (-2, 8, 8))
        self.assertFalse(profiles.t0_profile_is_feasible(25, 10))

    def test_portable_branch_table_matches_the_audited_profiles(self) -> None:
        expected = {
            27: [(12, 8, 0, 4)],
            28: [(12, 6, 2, 6)],
            29: [(12, 4, 4, 8)],
            31: [(12, 0, 8, 12), (13, 7, 2, 8)],
            34: [(13, 1, 8, 14), (14, 8, 2, 10)],
        }
        for order, rows in expected.items():
            with self.subTest(order=order):
                self.assertEqual(
                    [
                        (entry["r"], entry["beta"], entry["gamma"], entry["epsilon"])
                        for entry in profiles.strict_portable_t0_branches(order)
                    ],
                    rows,
                )

        self.assertEqual(profiles.strict_portable_t0_branches(25), ())
        self.assertEqual(profiles.strict_portable_t0_branches(26), ())
        self.assertTrue(profiles.t0_profile_is_feasible(27, 11))
        self.assertFalse(profiles.strict_portable_t0_profile_is_feasible(27, 11))


if __name__ == "__main__":
    unittest.main()
