"""The constant collar, measured instead of asserted.

The bounded-collar capping lemma needs a `q` such that everything the caps touch
lies within the first or last `q` period collars -- a complement that does not
grow with the period count.  The repository asserted that from a four-row table
of interface measurements taken from the *strip*.  These gates measure it on the
finished certificates, by aligning the `(1,-1)` cover against each one and
pruning the alignment to a genuine map isomorphism.
"""
from __future__ import annotations

import pytest

import strip_alignment as sa

ORDERS = (
    tuple(range(46, 57)) + tuple(range(67, 75)) + tuple(range(88, 93)) + (109, 110)
)
STABLE = [o for o in ORDERS if o >= sa.STABLE_FROM[o % 3]]
SHORT = [o for o in ORDERS if o < sa.STABLE_FROM[o % 3]]


@pytest.mark.parametrize("order", STABLE)
def test_the_complement_is_constant_within_a_residue_class(order: int) -> None:
    assert sa.complement(order) == sa.COMPLEMENT_BY_RESIDUE[order % 3]


@pytest.mark.parametrize("order", STABLE)
def test_the_strip_image_absorbs_every_additional_period(order: int) -> None:
    """n = 3t + cap with cap fixed: the whole growth is strip."""

    assert len(sa.best_alignment(order)) == order - sa.COMPLEMENT_BY_RESIDUE[order % 3]


@pytest.mark.parametrize("order", SHORT)
def test_the_short_orders_are_below_the_threshold(order: int) -> None:
    """Pinned as a boundary effect rather than silently excluded."""

    assert sa.complement(order) != sa.COMPLEMENT_BY_RESIDUE[order % 3]


@pytest.mark.parametrize("order", (54, 74, 109))
def test_the_alignment_is_a_map_isomorphism_onto_its_image(order: int) -> None:
    """Control: otherwise 'strip image' could be any large vertex correspondence."""

    mapping = sa.best_alignment(order)
    source = sa.cover_rotation(*sa.CERTIFICATE_CLASS, 0, 60)
    target = sa.load(order)
    images = set(mapping.values())
    assert len(images) == len(mapping), "the alignment is not injective"
    interior = 0
    for vertex, image in mapping.items():
        kept = [mapping[u] for u in source[vertex] if u in mapping]
        assert set(kept) <= set(target[image]), f"{vertex}: a cover edge is missing"
        if len(kept) == len(source[vertex]):
            ring = target[image]
            start = ring.index(kept[0])
            forward = [ring[(start + i) % len(ring)] for i in range(len(ring))]
            backward = [ring[(start - i) % len(ring)] for i in range(len(ring))]
            assert kept in (forward, backward), f"{vertex}: rotation does not match"
            interior += 1
    assert interior >= 10, "too few full-ring vertices for the control to mean anything"


def test_the_wrong_cover_class_aligns_worse_but_not_hopelessly() -> None:
    """Alignment size is a weak discriminator between classes; say so.

    Pruning enforces that every cover edge between kept vertices is present,
    not that absent edges stay absent, so a sub-map of the wrong cover still
    embeds fairly far: 60 vertices of order 110 for `(-2,-1)` against 81 for
    `(1,-1)`.  The sharp discriminator is the cycle profile in
    `test_certificate_unrolling.py` -- 61 matching vertices against 0.  This
    gate exists to keep that distinction visible rather than to carry it.
    """

    source = sa.cover_rotation(-2, -1, 0, 60)
    target = sa.load(110)
    degrees = {v: len(r) for v, r in target.items()}
    wrong = 0
    for image_seed in [v for v in target if degrees[v] == 5]:
        for mirror in (False, True):
            for shift in range(5):
                mapping = sa.grow(source, target, ("z", 30), image_seed, shift, mirror)
                if mapping:
                    wrong = max(wrong, len(sa.prune(mapping, source, target)))
    right = len(sa.best_alignment(110))
    assert wrong < right, f"the wrong class aligned {wrong}, the right one {right}"
    assert right - wrong >= 15
