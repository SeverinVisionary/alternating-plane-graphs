"""Gates for the closed-map search lane.

The search itself does not yet find anything -- see the module docstring of
`closed_map_search.py`, which records the calibration failure at order 20.  Its
*objective* is worth gating anyway: `score` is a fourth implementation of the
closed `(3,4,5)`-APG check, written over an involution and a face trace rather
than over adjacency rows, and it has to return zero exactly on the graphs the
other three accept.
"""
from __future__ import annotations

import collections
from pathlib import Path

import pytest

import closed_map_search as cms
import import_planar_code as ipc
import pumping_splice as ps
from certificate_tools import alpha_from_certificate, cycles_from_degrees

HERE = Path(__file__).resolve().parent
TARGETS = HERE / "certificates" / "targets"
KNOWN = HERE / "certificates" / "known"


def _score_of(path: Path) -> int:
    degrees, alpha = alpha_from_certificate(path)
    _, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
    return cms.score(alpha, degrees, vertex_of, sigma_inverse)


@pytest.mark.parametrize("order", ps.TARGET_ORDERS)
def test_the_objective_is_zero_on_every_target_certificate(order: int) -> None:
    assert _score_of(TARGETS / f"TARGET_{order}.json") == 0


@pytest.mark.parametrize(
    "name", ["schneider17.json", "ghent17.json", "order20.json", "order42.json"]
)
def test_the_objective_is_zero_on_every_published_witness(name: str) -> None:
    assert _score_of(KNOWN / name) == 0


@pytest.mark.parametrize("order", (46, 74, 110))
def test_a_transposed_pair_of_darts_costs_something(order: int) -> None:
    """Negative control: a zero objective must not be the only reachable value."""

    degrees, alpha = alpha_from_certificate(TARGETS / f"TARGET_{order}.json")
    _, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
    a = 0
    c = next(d for d in range(len(alpha)) if len({a, alpha[a], d, alpha[d]}) == 4)
    b, d = alpha[a], alpha[c]
    alpha[a], alpha[c] = c, a
    alpha[b], alpha[d] = d, b
    assert cms.score(alpha, degrees, vertex_of, sigma_inverse) > 0


def test_the_profile_arithmetic_admits_every_published_witness() -> None:
    """`v5 = v3 - 4` and `E = 2V - 2` are forced; the enumeration must agree."""

    sources = [KNOWN / n for n in
               ("schneider17.json", "ghent17.json", "order20.json", "order42.json")]
    for path in sources:
        degrees, _ = alpha_from_certificate(path)
        counts = collections.Counter(degrees)
        assert counts[5] == counts[3] - 4
        assert sorted(degrees) in [sorted(p) for p in cms.profiles(len(degrees))]


def test_the_census_sources_are_admitted_too() -> None:
    for path in sorted((HERE / "certificates" / "census_sources").glob("*.plc")):
        rotation = ipc.decode_first(path)
        counts = collections.Counter(len(ring) for ring in rotation)
        assert counts[5] == counts[3] - 4
