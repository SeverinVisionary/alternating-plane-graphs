"""Gates for the general-APG lane and the planarity-preserving search.

Conjecture 10.3 is about Definition 2.1 -- alternating plane graphs with no
restriction on degrees or face sizes -- so it needs its own decision procedure,
not `fast_apg_check.is_apg` with a test removed (that one also imposes
`sorted(sizes) == sorted(degrees)`, a theorem about the `(3,4,5)` subclass).
What is gated here is that the general procedure agrees with the subclass one
where they overlap, that it still rejects the things it must, and that the
planar search's states really are spheres.
"""
from __future__ import annotations

import random
from pathlib import Path

import pytest

import connectivity as cn
import fast_apg_check as fac
import general_apg as g
import plane_apg_search as ps_search
import pumping_splice as ps
from certificate_tools import alpha_from_certificate, cycles_from_degrees

HERE = Path(__file__).resolve().parent
TARGETS = HERE / "certificates" / "targets"


@pytest.mark.parametrize("order", ps.TARGET_ORDERS)
def test_the_general_procedure_accepts_every_certificate(order: int) -> None:
    degrees, alpha = alpha_from_certificate(TARGETS / f"TARGET_{order}.json")
    assert g.is_apg(degrees, alpha)
    assert fac.is_apg(degrees, alpha)


@pytest.mark.parametrize("order", (46, 74, 110))
def test_the_general_procedure_still_rejects_a_broken_map(order: int) -> None:
    """Negative control: looser conditions must not mean no conditions."""

    degrees, alpha = alpha_from_certificate(TARGETS / f"TARGET_{order}.json")
    a = 0
    c = next(d for d in range(len(alpha)) if len({a, alpha[a], d, alpha[d]}) == 4)
    b, d = alpha[a], alpha[c]
    alpha[a], alpha[c] = c, a
    alpha[b], alpha[d] = d, b
    assert not g.is_apg(degrees, alpha)


def test_a_degree_tie_is_rejected() -> None:
    degrees, alpha = alpha_from_certificate(TARGETS / "TARGET_46.json")
    degrees = list(degrees)
    cycles, vertex_of, _, _ = cycles_from_degrees(degrees)
    # Not a real map any more; the point is that the tie alone is fatal.
    victim = vertex_of[alpha[cycles[0][0]]]
    degrees[victim] = degrees[0]
    assert not g.is_apg(degrees, alpha)


def test_euler_bounds_the_edge_count() -> None:
    for order in (19, 24, 45, 110):
        low, high = g.edge_bounds(order)
        assert low == -(-3 * order // 2) and high == 3 * order - 6
        assert low <= high


# --------------------------------------------------------------------------
# The planar search's states


@pytest.mark.parametrize("order", (4, 5, 10, 20, 45))
def test_generated_triangulations_are_spheres_with_triangular_faces(order: int) -> None:
    rotation = ps_search.random_triangulation(order, random.Random(order))
    edges = len(ps_search._edges(rotation))
    walks = ps_search.facial_walks(rotation)
    assert order - edges + len(walks) == 2
    assert {len(walk) for walk in walks} == {3}
    assert all(len(set(ring)) == len(ring) for ring in rotation.values())


def test_deleting_an_edge_keeps_the_state_on_the_sphere() -> None:
    """The property the whole lane exists for."""

    rotation = ps_search.random_triangulation(20, random.Random(2))
    edges = ps_search._edges(rotation)
    removed = set(edges[:7])
    reduced = ps_search.delete(rotation, removed)
    remaining = len(ps_search._edges(reduced))
    walks = ps_search.facial_walks(reduced)
    assert 20 - remaining + len(walks) == 2


@pytest.mark.parametrize("order", (46, 74, 110))
def test_the_search_objective_is_zero_exactly_on_a_real_apg(order: int) -> None:
    assert ps_search.penalty(cn.load_rotation(TARGETS / f"TARGET_{order}.json")) == 0


def test_the_search_objective_is_positive_on_a_triangulation() -> None:
    """Every face size 3, so face alternation fails everywhere."""

    assert ps_search.penalty(ps_search.random_triangulation(12, random.Random(4))) > 0
