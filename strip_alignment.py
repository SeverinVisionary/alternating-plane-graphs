#!/usr/bin/env python3
"""Align the `(1,-1)` cover against a certificate, and measure what is left over.

`certificate_unrolling.py` establishes *which* cover class the certificates are
built from. This module finds *where*: it grows a maximal orientation-consistent
partial map isomorphism from the cover into a certificate, so the certificate
splits into a strip image and a complement.

That complement is the thing the independent review's bounded-collar capping lemma
is about. The lemma needs an integer `q` such that every vertex and face whose
incidence changes under capping lies within the first or last `q` period
collars -- in other words, a complement that does **not** grow with the period
count. Here it is measured instead of assumed, on an image that really is a map
isomorphism (`grow` walks a spanning tree and skips mismatches, so its output
is pruned to a fixpoint where every cover edge between kept vertices is a
certificate edge):

    residue 0:  27 vertices at every one of its orders, 48 through 90
    residue 1:  42 vertices at orders 67 through 109
    residue 2:  29 vertices at orders 53 through 110

Constant, exactly as a bounded collar requires -- the certificate grows by three
vertices per period and the part the caps occupy does not move. Below each
threshold the complement is smaller and irregular (26, 28, 23, 29 for residue 1
at orders 46-55; 24, 28 for residue 2 at 47, 50), because the strip is too short
for the alignment to reach a deep interior: the same boundary effect
`pumping_family.py` records at `t = 2`.

What this does **not** do is build the caps or prove the lemma. It measures the
one hypothesis that was being asserted from a table of four numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGETS_DIR = HERE / "certificates" / "targets"

EDGES = (("y", "z"), ("y", "z"), ("y", "z"), ("x", "z"), ("x", "z"), ("x", "y"))
ROT = {"x": (6, 8, 10), "y": (0, 2, 4, 11), "z": (1, 3, 7, 5, 9)}

CERTIFICATE_CLASS = (1, -1)

# Measured; the tests pin them.
COMPLEMENT_BY_RESIDUE = {0: 27, 1: 42, 2: 29}
# Below these orders the strip is too short for the alignment to reach a deep
# interior, and the complement is smaller and irregular.
STABLE_FROM = {0: 48, 1: 67, 2: 53}


def cover_rotation(p: int, q: int, lo: int, hi: int) -> dict:
    """Rotation system of the cyclic cover in class `(p, q)`, copies `lo..hi-1`."""

    voltages = (p, p - q, 0, 0, q, 0)
    rotation = {}
    for kind, ring in ROT.items():
        for copy in range(lo, hi):
            lifted = []
            for dart in ring:
                edge = dart // 2
                if dart % 2 == 0:
                    lifted.append((EDGES[edge][1], copy + voltages[edge]))
                else:
                    lifted.append((EDGES[edge][0], copy - voltages[edge]))
            rotation[(kind, copy)] = lifted
    return rotation


def load(order: int) -> dict:
    data = json.loads((TARGETS_DIR / f"TARGET_{order}.json").read_text())
    return {row["id"]: list(row["clockwise"]) for row in data["vertices"]}


def _ring(rotation: dict, vertex, mirror: bool) -> list:
    ring = list(rotation[vertex])
    return list(reversed(ring)) if mirror else ring


def grow(source: dict, target: dict, seed, image_seed, shift: int, mirror: bool):
    """Maximal partial map isomorphism from one seeded flag; mismatches stop it."""

    mapping = {seed: image_seed}
    used = {image_seed}
    source_ring = _ring(source, seed, False)
    target_ring = _ring(target, image_seed, mirror)
    if len(source_ring) != len(target_ring):
        return None
    target_ring = target_ring[shift:] + target_ring[:shift]
    stack = [(seed, source_ring, target_ring)]
    while stack:
        vertex, here, there = stack.pop()
        for nxt, image in zip(here, there):
            if nxt not in source or nxt in mapping:
                continue
            ahead = _ring(source, nxt, False)
            behind = _ring(target, image, mirror)
            if image in used or len(ahead) != len(behind):
                continue
            if mapping[vertex] not in behind:
                continue
            i = ahead.index(vertex)
            j = behind.index(mapping[vertex])
            mapping[nxt] = image
            used.add(image)
            stack.append((nxt, ahead[i:] + ahead[:i], behind[j:] + behind[:j]))
    return mapping


def prune(mapping: dict, source: dict, target: dict) -> dict:
    """Keep only the part that really is a map isomorphism onto its image.

    `grow` walks a spanning tree and skips whatever does not match, so a vertex
    can be mapped while one of its non-tree edges is not present in the target.
    Dropping such vertices to a fixpoint leaves a set on which every cover edge
    is a certificate edge -- which is what "strip image" has to mean.
    """

    kept = dict(mapping)
    changed = True
    while changed:
        changed = False
        for vertex in list(kept):
            image = kept[vertex]
            for neighbour in source[vertex]:
                if neighbour in kept and kept[neighbour] not in target[image]:
                    del kept[vertex]
                    changed = True
                    break
    return kept


def best_alignment(order: int, window: int = 60) -> dict:
    """The largest edge-consistent strip image found over all seed flags."""

    source = cover_rotation(*CERTIFICATE_CLASS, 0, window)
    target = load(order)
    degrees = {vertex: len(ring) for vertex, ring in target.items()}
    seed = ("z", window // 2)
    best: dict = {}
    for image_seed in [v for v in target if degrees[v] == 5]:
        for mirror in (False, True):
            for shift in range(5):
                mapping = grow(source, target, seed, image_seed, shift, mirror)
                if not mapping:
                    continue
                mapping = prune(mapping, source, target)
                if len(mapping) > len(best):
                    best = mapping
    return best


def complement(order: int) -> int:
    """Certificate vertices the alignment does not reach: an upper bound on the cap."""

    return len(load(order)) - len(best_alignment(order))


def main() -> int:
    orders = (
        list(range(46, 57)) + list(range(67, 75)) + list(range(88, 93)) + [109, 110]
    )
    for order in orders:
        mapping = best_alignment(order)
        copies = sorted({copy for _, copy in mapping})
        print(
            f"order {order:>3}  strip image {len(mapping):>3}"
            f"  copies {min(copies)}..{max(copies)}"
            f"  complement {len(load(order)) - len(mapping):>3}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
