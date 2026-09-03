"""Gates for the family 3-connectivity theorem.

The theorem in `family_connectivity.py` reduces "every member of the spliced
family is 3-connected" to two finite checks plus the reduction lemma.  Those
two checks are what this file runs; without them the module is an argument
about a hypothesis nobody verified.
"""
from __future__ import annotations

import pytest

import connectivity as cn
import family_connectivity as fc
import pumping_splice as ps

REPRESENTATIVES = fc.REPRESENTATIVES


def _base(order: int) -> int:
    return ps.floor_delta(order) + 4


@pytest.mark.parametrize("order", REPRESENTATIVES)
def test_a_face_never_leaves_a_bounded_window_of_copies(order: int) -> None:
    """The locality fact the type argument needs, measured on the object."""

    assert fc.face_span(order, _base(order)) <= 3


@pytest.mark.parametrize("order", REPRESENTATIVES)
def test_the_candidate_pair_types_stop_growing(order: int) -> None:
    """Splicing another period adds only translates of types already present."""

    base = _base(order)
    assert fc.types_stabilise(order, base)
    assert fc.types_stabilise(order, base + 1)


@pytest.mark.parametrize("order", REPRESENTATIVES)
def test_the_base_of_the_induction_is_three_connected(order: int) -> None:
    assert cn.is_three_connected(ps.splice(order, _base(order)))


@pytest.mark.parametrize("order", REPRESENTATIVES)
def test_no_candidate_pair_separates_at_the_base_or_one_above(order: int) -> None:
    """The same fact by the face-local route, so the two never drift apart."""

    base = _base(order)
    for delta in (base, base + 1):
        assert cn.separating_pairs_on_faces(ps.splice(order, delta)) == []


@pytest.mark.parametrize("order", REPRESENTATIVES)
def test_the_type_set_is_not_trivially_empty(order: int) -> None:
    """Control: a stabilising type set proves nothing if there are no types."""

    assert len(fc.pair_types(order, _base(order))) > 50
