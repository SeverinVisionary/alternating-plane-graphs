"""Gates for the periodic strip and the cap interface it presents.

The load-bearing fact here is that the boundary a cap must fill does **not**
grow with the number of periods.  If it did, the cap route would be no better
than searching for a large map; because it does not, one cap pair yields an
infinite family.
"""
from __future__ import annotations

import collections

import pytest

import periodic_strip
import strip_patch

TARGETS = set(range(46, 57)) | set(range(67, 75)) | set(range(88, 93)) | {109, 110}


def test_the_strip_re_derives_and_re_checks() -> None:
    """The whole verification, run as a gate rather than as a script."""

    assert periodic_strip.check() is True


def test_the_quotient_is_a_torus_map_of_the_right_shape() -> None:
    assert len(periodic_strip.ROT) == 3
    assert sorted(len(c) for c in periodic_strip.ROT.values()) == [3, 4, 5]
    assert len(periodic_strip.EDGES) == 6
    # V - E + F = 3 - 6 + 3 = 0.
    assert 3 - 6 + 3 == 0
    assert len(periodic_strip.OMEGA) == len(periodic_strip.EDGES)


def test_a_lifted_vertex_never_exceeds_its_quotient_degree() -> None:
    for periods in range(1, 12):
        patch = strip_patch.straight_patch(periods)
        for vertex, realised in patch["realised_degree"].items():
            assert realised <= periodic_strip.DEG[vertex[0]]


@pytest.mark.parametrize("periods", [4, 5, 6, 8, 10, 14, 20])
def test_the_cap_interface_does_not_grow_with_the_number_of_periods(periods: int) -> None:
    """The reason the cap route is smaller than any witness search.

    A straight cut leaves the same seven deficient vertices owing the same
    fourteen edges however long the cylinder is, so a cap pair solved once
    closes the family for every ``m``.
    """

    patch = strip_patch.straight_patch(periods)
    assert len(patch["boundary"]) == 7
    assert patch["owed_edges"] == 14
    # Everything else is genuinely interior and grows linearly.
    assert len(patch["interior"]) == 3 * periods - 7


def test_the_two_ends_owe_the_same_amount() -> None:
    patch = strip_patch.straight_patch(8)
    owed = collections.Counter()
    for vertex in patch["boundary"]:
        end = "low" if vertex[1] < 4 else "high"
        owed[end] += patch["deficiency"][vertex]
    assert owed["low"] == owed["high"] == 7


def test_the_cap_condition_is_exactly_a3_minus_a5_equals_four() -> None:
    for periods in (1, 2, 7, 40):
        profile = strip_patch.cap_arithmetic(6, 3, 2, periods)
        assert profile["v3"] - profile["v5"] == 4
        assert profile["v4"] == profile["order"] - 2 * profile["r"] + 4
        assert profile["edges"] == 2 * profile["order"] - 2
        assert profile["faces"] == profile["order"]
    with pytest.raises(ValueError, match="needs 4"):
        strip_patch.cap_arithmetic(5, 3, 2, 6)


def test_three_residues_would_close_every_target() -> None:
    """Three cap pairs, one per residue mod 3, cover all 26 open orders."""

    covered: set[int] = set()
    # a3 - a5 = 4 in each; the a4 values shift the base order across residues.
    for a3, a4, a5 in ((6, 2, 2), (6, 3, 2), (6, 4, 2)):
        covered |= set(strip_patch.residues_closed(a3, a4, a5)["closes"])
    assert covered == TARGETS
    assert collections.Counter(t % 3 for t in TARGETS) == {1: 10, 2: 10, 0: 6}


def test_a_patch_is_not_yet_an_apg() -> None:
    """Guards against anyone mistaking a patch for a construction."""

    patch = strip_patch.straight_patch(6)
    assert patch["owed_edges"] > 0
    assert any(value > 0 for value in patch["deficiency"].values())
