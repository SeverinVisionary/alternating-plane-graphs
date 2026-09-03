"""Gates for the Section-8 closures that shrink Conjecture 10.3's residue.

The paper asserts in Section 10 that its Section-8 graphs are 3-connected, and
Conjecture 10.3 turns entirely on that.  This file checks it instead: every
closure goes to `verify.py`, `verify_darts.py`, `fast_apg_check.py` and the
brute-force connectivity test.
"""
from __future__ import annotations

import json

import pytest

import connectivity as cn
import fast_apg_check
import section8_witnesses as s8
import verify
import verify_darts
import witness_coverage as wc


@pytest.mark.parametrize("order", sorted(s8.RECIPES))
def test_the_chain_closes_to_the_order_the_arithmetic_predicts(order: int) -> None:
    """`18a + 19b + 20c + 21d + 3`, checked against the built object."""

    assert len(s8.witness(order)["vertices"]) == order


@pytest.mark.parametrize("order", sorted(s8.RECIPES))
def test_every_closure_passes_all_three_checkers(order: int, tmp_path) -> None:
    certificate = s8.witness(order)
    path = tmp_path / f"section8_{order}.json"
    path.write_text(json.dumps(certificate))
    verify.verify_certificate(verify.load_certificate(path), expected_order=order)
    verify_darts.check(verify_darts.load(path), expected_order=order)
    assert fast_apg_check.accepts_certificate(path)


@pytest.mark.parametrize("order", sorted(s8.RECIPES))
def test_every_closure_is_three_connected(order: int) -> None:
    """The paper asserts this; Conjecture 10.3 needs it checked."""

    certificate = s8.witness(order)
    rotation = {row["id"]: row["clockwise"] for row in certificate["vertices"]}
    assert cn.is_three_connected(rotation)


def test_nothing_is_left_open_once_these_closures_are_counted() -> None:
    """The Section-8 closures are part of what makes the residue empty.

    They are built at run time from `results/blocks/` rather than stored, so a
    scan of certificate files cannot see them; `witness_coverage.residue` has to
    ask for them explicitly.
    """

    assert wc.residue() == []
    assert set(s8.RECIPES) <= wc.section8_orders()
    # Load-bearing: without them, seven orders reopen.
    covered = wc.stored_orders() | wc.family_orders()
    assert sorted(set(range(19, 400)) - covered) == [24, 39, 40, 41, 43, 44, 45]


def test_thirty_seven_and_thirty_eight_are_out_of_reach_of_the_arithmetic() -> None:
    """Not an oversight: 34 and 35 are not sums of 18, 19, 20, 21.

    This is why the paper's own Section-8 coverage list skips them too.
    """

    reachable = set()
    for count in (1, 2, 3):
        stack = [(0, count)]
        while stack:
            total, left = stack.pop()
            if left == 0:
                reachable.add(total)
                continue
            for step in (18, 19, 20, 21):
                stack.append((total + step, left - 1))
    assert 34 not in reachable and 35 not in reachable
    assert {36, 37, 38, 39, 40, 41, 42} <= reachable       # the two-block range
