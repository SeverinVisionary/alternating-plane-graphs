#!/usr/bin/env python3
"""Which unrolling is actually encoded here, in coordinates that mean something.

The independent review's strongest objection (2026-09-01) was that the labels
`(1,0)` and `(2,3)` do not define an unrolling: an unrolling is a class in
`H^1(T^2; Z)`, and a pair of integers names one only once a homology basis is
fixed. Nothing in this repository fixes one.

It also supplied the coordinates that do. For this quotient, writing `w_i` for
the voltage of edge `e_i` oriented from its first listed endpoint to its
second, the three facial cocycle equations leave a two-parameter family, and a
gauge change on the tree edges `e_3`, `e_5` puts every class in the form

    (w0, w1, w2, w3, w4, w5) = (p, p - q, 0, 0, q, 0)

with

    connected lift  <=>  gcd(p, q) = 1
    simple lift     <=>  p != 0, q != 0, p != q.

This module puts the committed `OMEGA` into that form. The answer is
`(p, q) = (-2, -1)`, i.e. the class `+-(2, 1)` -- **not** `(1, 0)`, which is
what `periodic_strip.py` calls it. In these coordinates `(1, 0)` is
`(1, 1, 0, 0, 0, 0)`, whose lift has `e_0` parallel to `e_1` and `e_3` parallel
to `e_4`, so it is not simple at all.

So one of two things is true, and the repository does not say which: the labels
use some other basis, or they are wrong. That matters because the
uncappability claim is stated *about* "the `(1,0)` unrolling", and the
certificates are stated to come from "a `(2,3)` unrolling of the same
quotient". Neither statement is reproducible until the basis is written down.

What is verified here, independent of the labels: the committed `OMEGA` is a
genuine cocycle, its lift is connected and simple, and its canonical
coordinates are `(-2, -1)`.
"""
from __future__ import annotations

import math
from typing import Iterable, Sequence

# The c = 3 alternating torus quotient, copied from periodic_strip.py so this
# module can be read on its own.
EDGES = (("y", "z"), ("y", "z"), ("y", "z"), ("x", "z"), ("x", "z"), ("x", "y"))
ROT = {"x": (6, 8, 10), "y": (0, 2, 4, 11), "z": (1, 3, 7, 5, 9)}
OMEGA = (-2, -1, 0, -1, -2, -1)

TREE_EDGES = (2, 3, 5)  # the edges gauged to zero


def _permutations():
    alpha = {}
    dart_edge = {}
    for edge in range(len(EDGES)):
        alpha[2 * edge] = 2 * edge + 1
        alpha[2 * edge + 1] = 2 * edge
        dart_edge[2 * edge] = edge
        dart_edge[2 * edge + 1] = edge
    sigma = {}
    for ring in ROT.values():
        for index, dart in enumerate(ring):
            sigma[dart] = ring[(index + 1) % len(ring)]
    sigma_inverse = {value: key for key, value in sigma.items()}
    phi = {dart: sigma_inverse[alpha[dart]] for dart in alpha}
    return alpha, phi, dart_edge


def faces() -> list[list[int]]:
    _, phi, _ = _permutations()
    seen: set[int] = set()
    out = []
    for start in sorted(phi):
        if start in seen:
            continue
        walk = []
        cursor = start
        while cursor not in seen:
            seen.add(cursor)
            walk.append(cursor)
            cursor = phi[cursor]
        out.append(walk)
    return out


def facial_voltage_sums(omega: Sequence[int] = OMEGA) -> list[int]:
    """Signed voltage sum around each facial walk. All zero iff `omega` is a cocycle."""

    _, _, dart_edge = _permutations()
    sums = []
    for face in faces():
        total = 0
        for dart in face:
            sign = 1 if dart % 2 == 0 else -1
            total += sign * omega[dart_edge[dart]]
        sums.append(total)
    return sums


def lift_is_simple(omega: Sequence[int] = OMEGA) -> bool:
    """Parallel quotient edges must lift with distinct relative offsets."""

    by_kind: dict[tuple[str, str], list[int]] = {}
    for edge, ends in enumerate(EDGES):
        by_kind.setdefault(ends, []).append(omega[edge])
    return all(len(set(offsets)) == len(offsets) for offsets in by_kind.values())


def gauge(omega: Sequence[int], potentials: dict[str, int]) -> tuple[int, ...]:
    """Voltages after shifting each vertex's potential -- the same class."""

    return tuple(
        omega[edge] + potentials[second] - potentials[first]
        for edge, (first, second) in enumerate(EDGES)
    )


def canonical_pq(omega: Sequence[int] = OMEGA, span: int = 6) -> tuple[int, int]:
    """The `(p, q)` of the independent review's normal form `(p, p-q, 0, 0, q, 0)`."""

    for px in range(-span, span + 1):
        for py in range(-span, span + 1):
            for pz in range(-span, span + 1):
                shifted = gauge(omega, {"x": px, "y": py, "z": pz})
                if all(shifted[edge] == 0 for edge in TREE_EDGES):
                    p, q = shifted[0], shifted[4]
                    if shifted[1] != p - q:
                        raise ValueError(f"{shifted} is not of the claimed shape")
                    return p, q
    raise ValueError("no gauge reaches the normal form; omega is not a cocycle")


def report() -> dict[str, object]:
    p, q = canonical_pq()
    return {
        "facial_voltage_sums": facial_voltage_sums(),
        "is_cocycle": all(total == 0 for total in facial_voltage_sums()),
        "lift_is_simple": lift_is_simple(),
        "canonical_pq": (p, q),
        "connected_lift": math.gcd(abs(p), abs(q)) == 1,
        "face_lengths": sorted(len(face) for face in faces()),
    }


def main() -> int:
    for key, value in report().items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
