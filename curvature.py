#!/usr/bin/env python3
"""Combinatorial curvature of (3,4,5)-alternating plane graphs.

Written to answer one question about the uncappability claim: is there an
a priori bound on the size of a minimal disk cap? If every vertex of the class
were positively curved, Gauss-Bonnet would bound any disk's interior and a
depth-limited search would be a proof. The answer is no, and this module is the
computation that says so.

The combinatorial curvature of a vertex in a plane map is

    k(v) = 1 - deg(v)/2 + sum over faces f incident to v of 1/|f|

and Gauss-Bonnet for a sphere map reads `sum_v k(v) = 2`.

Enumerating every vertex type admissible in a (3,4,5)-APG -- degree in
{3,4,5}, incident face sizes in {3,4,5}, cyclically adjacent faces of different
size -- gives **54** types, of which **36 are negatively curved** and **none is
flat**. The extremes are `-4/15` at a degree-5 vertex meeting faces
`(3,4,5,4,5)` and `+17/60` at a degree-3 vertex meeting `(3,4,5)`.

So a disk cap can absorb arbitrarily much negative curvature, there is no size
bound from curvature, and "the search terminated at N nodes" cannot become a
proof by this route. That is the finiteness gap an independent review
named, made precise.

What survives is a global constraint, and it is sharp enough to be worth
checking: `sum k = 2` with every term at most `17/60` forces **at least 8
positively curved vertices** in any (3,4,5)-APG. All 26 certificates satisfy
both, computed in exact rational arithmetic from the rotation system alone --
an independent structural check that shares no code with either verifier.
"""
from __future__ import annotations

import json
from fractions import Fraction
from itertools import product
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGETS_DIR = HERE / "certificates" / "targets"

SIZES = (3, 4, 5)
MAX_CURVATURE = Fraction(17, 60)     # degree 3 meeting faces 3, 4, 5
MIN_CURVATURE = Fraction(-4, 15)     # degree 5 meeting faces 3, 4, 5, 4, 5


def vertex_curvature(degree: int, face_sizes) -> Fraction:
    return 1 - Fraction(degree, 2) + sum(Fraction(1, size) for size in face_sizes)


def admissible_types() -> list[tuple[Fraction, int, tuple]]:
    """Every (degree, cyclic face-size word) a (3,4,5)-APG vertex can have."""

    types = []
    for degree in SIZES:
        for word in product(SIZES, repeat=degree):
            if any(word[i] == word[(i + 1) % degree] for i in range(degree)):
                continue
            types.append((vertex_curvature(degree, word), degree, word))
    return sorted(types)


def face_sizes_at(rotation: dict) -> dict:
    """For each vertex, the sizes of its incident faces, in rotation order."""

    darts = {(v, u) for v, ring in rotation.items() for u in ring}
    face_of: dict = {}
    sizes: list[int] = []
    for start in sorted(darts):
        if start in face_of:
            continue
        walk = 0
        dart = start
        while dart not in face_of:
            face_of[dart] = len(sizes)
            walk += 1
            u, v = dart
            ring = rotation[v]
            dart = (v, ring[(ring.index(u) - 1) % len(ring)])
        sizes.append(walk)
    return {
        vertex: [sizes[face_of[(vertex, u)]] for u in ring]
        for vertex, ring in rotation.items()
    }


def curvatures(order: int) -> dict:
    data = json.loads((TARGETS_DIR / f"TARGET_{order}.json").read_text())
    rotation = {row["id"]: list(row["clockwise"]) for row in data["vertices"]}
    incident = face_sizes_at(rotation)
    return {
        vertex: vertex_curvature(len(rotation[vertex]), incident[vertex])
        for vertex in rotation
    }


def main() -> int:
    types = admissible_types()
    negative = [t for t in types if t[0] < 0]
    print(f"admissible vertex types: {len(types)}")
    print(f"  negatively curved: {len(negative)}")
    print(f"  flat: {sum(1 for t in types if t[0] == 0)}")
    print(f"  range: {types[0][0]} .. {types[-1][0]}")
    orders = (
        list(range(46, 57)) + list(range(67, 75)) + list(range(88, 93)) + [109, 110]
    )
    for order in orders:
        k = curvatures(order)
        positive = sum(1 for value in k.values() if value > 0)
        print(f"order {order:>3}: sum k = {sum(k.values())}, positively curved {positive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
