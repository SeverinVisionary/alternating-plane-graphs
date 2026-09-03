import unittest

import block_arithmetic as ba


class BlockArithmeticTests(unittest.TestCase):
    def test_target_set_is_exact(self):
        self.assertEqual(len(ba.TARGET_ORDERS), 26)
        self.assertEqual(
            ba.TARGET_ORDERS,
            (
                *range(46, 57),
                *range(67, 75),
                *range(88, 93),
                109,
                110,
            ),
        )

    def test_join_order_formula(self):
        self.assertEqual(ba.apg_order((21,)), 21)
        self.assertEqual(ba.apg_order((21, 22)), 40)
        self.assertEqual(ba.apg_order((21, 22, 23)), 60)
        with self.assertRaises(ValueError):
            ba.apg_order(())

    def test_three_proposed_blocks_cover_every_target(self):
        reps = ba.target_representations()
        self.assertEqual(tuple(reps), ba.TARGET_ORDERS)
        self.assertEqual(set(reps), set(ba.TARGET_ORDERS))
        for target, blocks in reps.items():
            self.assertEqual(ba.apg_order(blocks), target)

    def test_all_three_block_fallback_order_sets_are_frozen(self):
        self.assertEqual(
            ba.covering_new_block_triples(),
            (
                (25, 29, 34),
                (25, 30, 34),
                (25, 30, 35),
                (26, 29, 33),
                (27, 31, 35),
                (28, 29, 31),
                (28, 31, 34),
                (28, 31, 35),
                (28, 31, 36),
                (28, 32, 35),
                (28, 32, 36),
            ),
        )

    def test_published_blocks_alone_leave_exact_frontier(self):
        missing = tuple(
            target
            for target in ba.TARGET_ORDERS
            if ba.representation(target, ba.PUBLISHED_BLOCK_ORDERS) is None
        )
        self.assertEqual(missing, ba.TARGET_ORDERS)

    def test_finite_one_off_block_is_checked_against_the_t_budget(self):
        # The strict port theorem leaves a possible order-25 r=11 block with
        # t=1.  It is not portable, but it can still be useful once in a
        # finite target chain alongside portable t=0 blocks.  Order coverage
        # therefore must be checked with the additive t budget rather than by
        # treating every discovered block as freely repeatable.
        block_t = {21: 0, 22: 0, 23: 0, 24: 0, 25: 1, 29: 0, 34: 0}
        reps = ba.target_representations_with_t_budget(block_t)
        self.assertEqual(tuple(reps), ba.TARGET_ORDERS)
        for target, blocks in reps.items():
            with self.subTest(target=target):
                self.assertEqual(ba.apg_order(blocks), target)
                self.assertLessEqual(ba.t_total(blocks, block_t), 4)
        self.assertEqual(reps[46], (24, 25))
        self.assertEqual(ba.t_total(reps[46], block_t), 1)

    def test_active_boolean_primary_t0_triple_has_conditional_all_target_coverage(self):
        # These are deliberately not existence assertions: this merely freezes
        # the exact finite-chain arithmetic that becomes available if all three
        # cloud candidate blocks are independently certified.
        reps = ba.boolean_primary_t0_target_representations()
        self.assertEqual(tuple(reps), ba.TARGET_ORDERS)
        available = {
            *ba.PUBLISHED_BLOCK_ORDERS,
            *ba.BOOLEAN_PRIMARY_T0_BLOCK_ORDERS,
        }
        for target, blocks in reps.items():
            with self.subTest(target=target):
                self.assertEqual(ba.apg_order(blocks), target)
                self.assertTrue(set(blocks).issubset(available))
                self.assertEqual(ba.t_total(blocks, {order: 0 for order in available}), 0)

    def test_t_budget_rejects_an_uncovered_or_over_budget_target(self):
        self.assertIsNone(
            ba.representation_with_t_budget(46, {21: 0, 25: 5}, max_t=4)
        )
        with self.assertRaises(ValueError):
            ba.t_total((21, 25), {21: 0})


if __name__ == "__main__":
    unittest.main()
