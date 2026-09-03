"""Pin the unrolling that is actually committed, in coordinates that mean something.

The independent review's strongest objection was that `(1,0)` and `(2,3)` name
nothing without a homology basis, and that `(1,0)` in the natural basis has a
non-simple lift. `unrolling_class.py` answers the question these gates freeze:
the committed `OMEGA` is a genuine cocycle whose lift is connected and simple,
and whose canonical coordinates are `(-2, -1)`.
"""
from __future__ import annotations

import math

import pytest

import unrolling_class as uc


def test_the_quotient_is_an_alternating_torus_map() -> None:
    assert sorted(len(face) for face in uc.faces()) == [3, 4, 5]
    assert len(uc.ROT) - len(uc.EDGES) + len(uc.faces()) == 0  # Euler char 0


def test_omega_is_a_cocycle() -> None:
    """Without this the lift is a graph cover, not a cover of the *map*."""

    assert uc.facial_voltage_sums() == [0, 0, 0]


def test_the_lift_is_connected_and_simple() -> None:
    p, q = uc.canonical_pq()
    assert math.gcd(abs(p), abs(q)) == 1, "gcd(p,q)=1 is what makes the cover connected"
    assert p != 0 and q != 0 and p != q, "these three keep the lifted graph simple"
    assert uc.lift_is_simple()


def test_the_committed_unrolling_is_not_the_one_the_docs_name() -> None:
    """`periodic_strip.py` calls this the `(1,0)` unrolling. It is not.

    In the normal form `(p, p-q, 0, 0, q, 0)` the committed class is
    `(p, q) = (-2, -1)`. The class `(1, 0)` is `(1, 1, 0, 0, 0, 0)`, whose lift
    puts `e0` parallel to `e1` and `e3` parallel to `e4` -- not simple, so not
    a candidate for a strip at all.

    Either the labels use an unstated basis or they are wrong. Until the basis
    is written down, neither the uncappability claim (stated about "the (1,0)
    unrolling") nor the certificates' provenance (stated as "a (2,3)
    unrolling") is reproducible.
    """

    assert uc.canonical_pq() == (-2, -1)

    one_zero = (1, 1, 0, 0, 0, 0)
    assert uc.facial_voltage_sums(one_zero) == [0, 0, 0], "still a cocycle"
    assert not uc.lift_is_simple(one_zero), "but its lift has parallel edges"


def test_a_non_cocycle_is_rejected() -> None:
    """Negative control: an arbitrary offset assignment is not an unrolling."""

    bogus = (1, 0, 0, 0, 0, 0)
    assert uc.facial_voltage_sums(bogus) != [0, 0, 0]
    with pytest.raises(ValueError):
        uc.canonical_pq(bogus)
