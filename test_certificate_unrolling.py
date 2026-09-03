"""Which cover class the certificates come from, checked rather than labelled.

The uncappability result is stated about "the `(1,0)` unrolling" and the
certificates about "a `(2,3)` unrolling", in a basis nobody wrote down. These
gates replace both labels with a measurement in the canonical coordinates of
`unrolling_class.py`.
"""
from __future__ import annotations

import pytest

import certificate_unrolling as cu
import unrolling_class as uc

SMALL = (46, 47, 49)   # t = 2, 5, 3: a radius-3 ball still reaches a cap
ORDERS = (
    tuple(range(46, 57)) + tuple(range(67, 75)) + tuple(range(88, 93)) + (109, 110)
)


def test_the_two_classes_are_distinguishable() -> None:
    """Control: without this every match below could be vacuous.

    Radius-1 cannot separate cover classes -- `omega` never changes a
    neighbour's type -- so the invariant has to see cycles. Check that it does.
    """

    a = cu.interior_profiles(*cu.CERTIFICATE_CLASS)
    b = cu.interior_profiles(*cu.COMMITTED_CLASS)
    assert a != b
    for degree in (3, 4, 5):
        assert a[degree] != b[degree], f"degree {degree} cannot tell the classes apart"


def test_the_committed_omega_is_the_class_it_is_compared_against() -> None:
    """`periodic_strip.py`'s omega really is `(-2, -1)` in these coordinates."""

    assert uc.canonical_pq() == cu.COMMITTED_CLASS


@pytest.mark.parametrize("order", [order for order in ORDERS if order not in SMALL])
def test_every_larger_certificate_contains_the_1_minus_1_strip(order: int) -> None:
    assert cu.count_matching(order, *cu.CERTIFICATE_CLASS) >= 1


@pytest.mark.parametrize("order", ORDERS)
def test_no_certificate_contains_the_committed_strip(order: int) -> None:
    """The class `periodic_strip.py` commits appears in none of the witnesses.

    That is the point: the uncappable class and the capped class are different
    objects, which is what the narrative says -- but the labels it uses name
    neither of them.
    """

    assert cu.count_matching(order, *cu.COMMITTED_CLASS) == 0


@pytest.mark.parametrize("order", SMALL)
def test_the_smallest_orders_have_no_deep_interior(order: int) -> None:
    """Pinned so it reads as a boundary effect rather than a contradiction."""

    assert cu.count_matching(order, *cu.CERTIFICATE_CLASS) == 0


def test_the_interior_count_grows_with_the_period_count() -> None:
    counts = [cu.count_matching(order, *cu.CERTIFICATE_CLASS) for order in (74, 92, 110)]
    assert counts == sorted(counts) and counts[0] < counts[-1]
