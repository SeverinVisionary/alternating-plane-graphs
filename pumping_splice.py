#!/usr/bin/env python3
"""Splice periods into a certificate's periodic middle, and prove the family.

`strip_alignment.py` measures that the caps occupy a constant number of
vertices however long the strip is. That is hypothesis 3 of the periodic
capping lemma in `PUMPING_LEMMA_STATUS.md` and nothing else. This module does
the rest: it extracts the two caps as explicit patches, implements the
insertion, and builds `n + 3d` maps from an order-`n` certificate for every
integer `d` above an explicit floor.

The construction. `symbolic` re-runs the alignment and records, for every
aligned cover vertex, its certificate rotation as a list of tokens: a *strip*
token naming a cover vertex, or a *cap* token naming a certificate vertex the
alignment never reached. A copy all of whose three vertices carry only strip
tokens is *deep*. `splice(order, delta)` then rebuilds the rotation system with
the deep block lengthened (or shortened) by `delta` copies:

* cap vertices keep their rotations verbatim, with strip neighbours above the
  cut shifted by `delta`;
* strip vertices below the cut keep their rotations verbatim;
* strip vertices above the cut are the verbatim rotations of the old copy
  `c - delta`;
* the `delta` fresh copies are translates of the cut copy, which is deep and so
  carries no cap token.

Why this proves the lemma rather than producing more examples. Every face of a
`(3,4,5)`-APG has at most five darts, and a face trace only reads `alpha` and
the rotation predecessor at the vertices it visits, so a facial walk cannot
leave a window of a few consecutive copies (the cover's largest edge offset is
two). `deep_block_is_periodic` checks that the deep rotations really are
translates of one another, so every window of `splice(order, delta)` is a
translated window of the certificate, every face is a translated face, and both
alternation conditions are inherited. Three vertices, six edges and three faces
enter per copy, so `V - E + F` is unchanged and the lift stays spherical. The
floor on `delta` is where deletion would consume a copy that is not deep, that
is, where the two cap collars meet: the lemma's `t >= 2q + 1`.

Nothing here is trusted. `test_pumping_splice.py` puts every spliced map to
both independent verifiers and to the third dart-side checker.
"""
from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path

import strip_alignment as sa

HERE = Path(__file__).resolve().parent
KINDS = ("x", "y", "z")
WINDOW = 60


def _best_alignment(order: int, window: int = WINDOW):
    """`strip_alignment.best_alignment`, keeping the mirror flag it discards."""

    source = sa.cover_rotation(*sa.CERTIFICATE_CLASS, 0, window)
    target = sa.load(order)
    degrees = {vertex: len(ring) for vertex, ring in target.items()}
    seed = ("z", window // 2)
    best: dict = {}
    mirror_used = False
    for image_seed in [v for v in target if degrees[v] == 5]:
        for mirror in (False, True):
            for shift in range(5):
                mapping = sa.grow(source, target, seed, image_seed, shift, mirror)
                if not mapping:
                    continue
                mapping = sa.prune(mapping, source, target)
                if len(mapping) > len(best):
                    best, mirror_used = mapping, mirror
    return best, mirror_used


@lru_cache(maxsize=None)
def symbolic(order: int, window: int = WINDOW):
    """Aligned cover vertices, each with its certificate rotation as tokens.

    A token is ``("strip", cover_vertex)`` or ``("cap", certificate_label)``.
    Two kinds of aligned vertex are dropped first: one whose ring correspondence
    is undetermined because the alignment kept none of its cover neighbours, and
    one whose certificate ring contains a strip image that is *not* the cover
    neighbour at that position -- a chord, which means the alignment is not a
    map isomorphism there.  Both are ragged-boundary effects; dropping them
    moves the vertex into the cap.
    """

    source = sa.cover_rotation(*sa.CERTIFICATE_CLASS, 0, window)
    target = sa.load(order)
    phi, mirror = _best_alignment(order, window)

    def cover_ring(vertex):
        ring = list(source[vertex])
        return list(reversed(ring)) if mirror else ring

    while True:
        determined, bad = {}, []
        for vertex in phi:
            here, there = cover_ring(vertex), list(target[phi[vertex]])
            degree = len(here)
            offsets = [
                offset
                for offset in range(degree)
                if all(
                    phi[neighbour] == there[(index + offset) % degree]
                    for index, neighbour in enumerate(here)
                    if neighbour in phi
                )
            ]
            if len(offsets) == 1:
                determined[vertex] = (offsets[0], here, there)
            else:
                bad.append(vertex)
        if not bad:
            images = set(phi.values())
            for vertex, (offset, here, there) in determined.items():
                degree = len(here)
                if any(
                    neighbour not in phi and there[(index + offset) % degree] in images
                    for index, neighbour in enumerate(here)
                ):
                    bad.append(vertex)
        if not bad:
            break
        for vertex in set(bad):
            phi.pop(vertex, None)

    tokens = {}
    for vertex, (offset, here, there) in determined.items():
        degree = len(here)
        tokens[vertex] = tuple(
            ("strip", neighbour)
            if neighbour in phi
            else ("cap", there[(index + offset) % degree])
            for index, neighbour in enumerate(here)
        )
    return dict(phi), tokens, target


def deep_copies(tokens: dict) -> list[int]:
    """Copies carrying all three vertices with no cap attachment at all."""

    return sorted(
        copy
        for copy in {c for _, c in tokens}
        if all(
            (kind, copy) in tokens
            and all(token[0] == "strip" for token in tokens[(kind, copy)])
            for kind in KINDS
        )
    )


def deep_block_is_periodic(order: int) -> bool:
    """Hypothesis of the lemma: deep rotations are translates of one another.

    Without this the splice would only be a relabelling trick; with it, every
    bounded window of a spliced map is a translated window of the certificate.
    """

    _, tokens, _ = symbolic(order)
    deep = deep_copies(tokens)
    if len(deep) < 2:
        return False
    base = deep[0]
    for copy in deep[1:]:
        shift = copy - base
        for kind in KINDS:
            moved = tuple(
                ("strip", (k2, c2 + shift))
                for _, (k2, c2) in tokens[(kind, base)]
            )
            if moved != tokens[(kind, copy)]:
                return False
    return True


def splice(order: int, delta: int, cut: int | None = None) -> dict:
    """Rotation system of the order `order + 3 * delta` map, in split labels."""

    phi, tokens, target = symbolic(order)
    copies = sorted({c for _, c in tokens})
    low, high = min(copies), max(copies)
    deep = deep_copies(tokens)
    if not deep:
        raise ValueError(f"order {order}: the strip has no deep copy")
    if cut is None:
        # Deletions consume the copies just above the cut, so a negative delta
        # needs a cut low enough to keep them all inside the deep block.
        cut = deep[0] if delta < 0 else deep[len(deep) // 2]
    if cut not in deep:
        raise ValueError(f"cut {cut} is not deep")
    if delta < 0 and any(c not in deep for c in range(cut + 1, cut - delta + 1)):
        raise ValueError(f"delta {delta} would delete a copy that is not deep")

    def source_of(copy: int) -> tuple[int, int]:
        if copy <= cut:
            return copy, 0
        if copy > cut + delta:
            return copy - delta, delta
        return cut, copy - cut  # a fresh copy, templated on the cut copy

    def relabel(copy: int) -> int:
        if copy <= cut:
            return copy
        if delta < 0 and copy <= cut - delta:
            raise ValueError(f"copy {copy} is deleted by delta {delta}")
        return copy + delta

    strip = {
        (kind, copy)
        for copy in range(low, high + delta + 1)
        for kind in KINDS
        if (kind, source_of(copy)[0]) in tokens
    }
    cap = set(target) - set(phi.values())
    inverse = {image: vertex for vertex, image in phi.items()}

    rotation: dict = {}
    for kind, copy in strip:
        source_copy, shift = source_of(copy)
        ring = []
        for token, value in tokens[(kind, source_copy)]:
            if token == "strip":
                other_kind, other_copy = value
                moved = (other_kind, other_copy + shift)
                if moved not in strip:
                    raise ValueError(f"{(kind, copy)} points outside the strip")
                ring.append(("S",) + moved)
            else:
                if shift not in (0, delta):
                    raise ValueError(f"fresh copy {(kind, copy)} carries a cap token")
                ring.append(("C", value))
        rotation[("S", kind, copy)] = ring
    for vertex in cap:
        ring = []
        for neighbour in target[vertex]:
            if neighbour in cap:
                ring.append(("C", neighbour))
            else:
                other_kind, other_copy = inverse[neighbour]
                ring.append(("S", other_kind, relabel(other_copy)))
        rotation[("C", vertex)] = ring
    for vertex, ring in rotation.items():
        for neighbour in ring:
            if neighbour not in rotation:
                raise ValueError(f"{vertex} names a vertex that is not present")
    return rotation


def certificate(order: int, delta: int, cut: int | None = None) -> dict:
    """The spliced map as an `apg-plane-rotation-v1` certificate."""

    rotation = splice(order, delta, cut)
    labels = {
        vertex: index
        for index, vertex in enumerate(
            sorted(rotation, key=lambda key: (key[0], str(key[1:])))
        )
    }
    rows = []
    for vertex in sorted(rotation, key=lambda key: labels[key]):
        ring = [labels[neighbour] for neighbour in rotation[vertex]]
        start = ring.index(min(ring))
        rows.append({"id": labels[vertex], "clockwise": ring[start:] + ring[:start]})
    return {"format": "apg-plane-rotation-v1", "vertices": rows}


def floor_delta(order: int) -> int:
    """The most negative `delta` the two cap collars leave room for."""

    _, tokens, _ = symbolic(order)
    deep = deep_copies(tokens)
    return -(len(deep) - 1) if deep else 0


def reachable_orders(bound: int = 400) -> dict[int, int]:
    """Every order the splice family reaches, and a certificate that reaches it."""

    out: dict[int, int] = {}
    for order in TARGET_ORDERS:
        try:
            low = floor_delta(order)
        except ValueError:
            continue
        if not deep_copies(symbolic(order)[1]):
            continue
        for delta in range(low, (bound - order) // 3 + 1):
            out.setdefault(order + 3 * delta, order)
    return out


TARGET_ORDERS = (
    tuple(range(46, 57)) + tuple(range(67, 75)) + tuple(range(88, 93)) + (109, 110)
)


def main() -> int:
    print(f"{'order':>5} {'deep':>5} {'floor':>6} {'reach':>18}")
    for order in TARGET_ORDERS:
        _, tokens, _ = symbolic(order)
        deep = deep_copies(tokens)
        if not deep:
            print(f"{order:>5} {0:>5} {'-':>6} {'(no deep copy)':>18}")
            continue
        low = floor_delta(order)
        print(
            f"{order:>5} {len(deep):>5} {low:>6}"
            f"  {order + 3 * low} + 3k, k >= 0"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
