"""Gauss-Bonnet as an independent check, and the finiteness gap made precise."""
from __future__ import annotations

from fractions import Fraction

import pytest

import curvature as cv

ORDERS = (
    tuple(range(46, 57)) + tuple(range(67, 75)) + tuple(range(88, 93)) + (109, 110)
)


def test_the_admissible_vertex_types() -> None:
    types = cv.admissible_types()
    assert len(types) == 54
    assert sum(1 for k, _, _ in types if k < 0) == 36
    assert sum(1 for k, _, _ in types if k == 0) == 0
    assert types[0][0] == cv.MIN_CURVATURE == Fraction(-4, 15)
    assert types[-1][0] == cv.MAX_CURVATURE == Fraction(17, 60)


def test_negative_curvature_kills_the_easy_finiteness_argument() -> None:
    """A disk cap can absorb unbounded negative curvature, so no size bound.

    This is the point of the module: if every admissible type were positively
    curved, Gauss-Bonnet would bound a cap's interior and the terminated search
    would be a proof.
    """

    negative = [(d, w) for k, d, w in cv.admissible_types() if k < 0]
    assert negative, "if this were empty the uncappability search would be finite"
    assert any(d == 4 for d, _ in negative), "even degree-4 vertices can be negative"


@pytest.mark.parametrize("order", ORDERS)
def test_gauss_bonnet_holds_exactly(order: int) -> None:
    """Exact rational arithmetic, from the rotation system, no verifier involved."""

    assert sum(cv.curvatures(order).values()) == 2


@pytest.mark.parametrize("order", ORDERS)
def test_at_least_eight_positively_curved_vertices(order: int) -> None:
    """`sum k = 2` with every term <= 17/60 forces ceil(2 / (17/60)) = 8."""

    k = cv.curvatures(order)
    assert sum(1 for value in k.values() if value > 0) >= 8
    assert all(cv.MIN_CURVATURE <= value <= cv.MAX_CURVATURE for value in k.values())


@pytest.mark.parametrize("order", (46, 74, 110))
def test_no_certificate_vertex_is_flat(order: int) -> None:
    assert all(value != 0 for value in cv.curvatures(order).values())
