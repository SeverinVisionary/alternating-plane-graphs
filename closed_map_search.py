#!/usr/bin/env python3
"""Direct annealing search for *closed* `(3,4,5)`-APGs at a given order.

Every other search lane in this directory looks for Section-8 blocks, needs
`z3` or `python-sat`, or is pinned to a committed frontier state.  Conjecture
10.3 needs something smaller and different: an explicit `(3,4,5)`-APG at each
order in `21..25, 37..41, 43..45`, where the primary paper reports a heuristic
hit but publishes no graph we hold.  This module is stdlib only and searches
the closed maps directly.

The state is a fixed-point-free involution `alpha` on `2E` darts over a fixed
vertex permutation, exactly as in `map_search.py`; the move is the same
two-edge switch.  What differs is the objective, which scores the closed
`(3,4,5)`-APG conditions rather than the two-socket block interface.  The
profile is forced: `V - E + F = 2` with `F = V` gives `E = 2V - 2`, and
Theorem 3.2 gives `v5 = v3 - 4`, so a degree profile is one integer.

**This lane does not currently work, and the honest record of that is here
rather than in a commit message.**  The objective is right -- `score` is a
fourth independent implementation of the closed `(3,4,5)`-APG check, and it
returns zero on all 26 target certificates and on all four published witnesses,
which `test_closed_map_search.py` gates.  What fails is the search: at order 20,
where a published witness exists, annealing plateaus around penalty 9 and finds
no hit in three minutes over four degree profiles, with or without moves biased
towards darts in violated faces.  So the fourteen orders Conjecture 10.3 still
needs are open, and this file is the calibrated starting point for closing
them, not a closure.

Nothing here is trusted.  A hit is written out and re-read by `verify.py`,
`verify_darts.py` and `fast_apg_check.py` before it counts.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from certificate_tools import cycles_from_degrees

ALLOWED = frozenset({3, 4, 5})


def profiles(order: int) -> list[list[int]]:
    """Degree multisets allowed by Euler plus Theorem 3.2.

    Ordered by distance from `v3 = n // 3 + 2`, which is where every published
    witness in `certificates/` sits (order 17 has `v3 = 8`, order 42 has
    `v3 = 15`).  The ordering is a search heuristic only; the full list is still
    reachable, and a hit at any profile is verified the same way.
    """

    out = []
    for v3 in range(4, order + 1):
        v5 = v3 - 4
        v4 = order - v3 - v5
        if v4 < 0:
            continue
        out.append([3] * v3 + [4] * v4 + [5] * v5)
    centre = order // 3 + 2
    return sorted(out, key=lambda d: abs(d.count(3) - centre))


def _faces(alpha: list[int], sigma_inverse: list[int]) -> list[list[int]]:
    phi = [sigma_inverse[alpha[dart]] for dart in range(len(alpha))]
    seen, walks = set(), []
    for dart in range(len(alpha)):
        if dart in seen:
            continue
        walk, cursor = [], dart
        while cursor not in seen:
            seen.add(cursor)
            walk.append(cursor)
            cursor = phi[cursor]
        walks.append(walk)
    return walks


def score(alpha: list[int], degrees: list[int], vertex_of: list[int],
          sigma_inverse: list[int]) -> int:
    """Zero exactly when the map is a closed `(3,4,5)`-APG.

    The vertex conditions -- no loop, no parallel edge, no two adjacent equal
    degrees -- are maintained structurally by the moves, so this only has to
    score the faces.  `_valid_switch` is what keeps that true; the suite checks
    the two against each other on random states.
    """

    darts = len(alpha)
    phi = [sigma_inverse[alpha[dart]] for dart in range(darts)]
    face_of = [-1] * darts
    sizes: list[int] = []
    penalty = 0
    for dart in range(darts):
        if face_of[dart] >= 0:
            continue
        index = len(sizes)
        size, cursor = 0, dart
        corners = []
        while face_of[cursor] < 0:
            face_of[cursor] = index
            corners.append(vertex_of[cursor])
            size += 1
            cursor = phi[cursor]
        sizes.append(size)
        penalty += 0 if size in ALLOWED else min(abs(size - s) for s in ALLOWED)
        penalty += size - len(set(corners))
    for dart in range(darts):
        mate = alpha[dart]
        if dart < mate and sizes[face_of[dart]] == sizes[face_of[mate]]:
            penalty += 1
    penalty += abs(len(sizes) - len(degrees))
    return penalty


def _valid_switch(alpha: list[int], degrees: list[int], vertex_of: list[int],
                  a: int, c: int) -> bool:
    """May the edges at `a` and `c` be re-paired as `(a, c)` and `(b, d)`?"""

    b, d = alpha[a], alpha[c]
    if len({a, b, c, d}) != 4:
        return False
    for x, y in ((a, c), (b, d)):
        u, v = vertex_of[x], vertex_of[y]
        if u == v or degrees[u] == degrees[v]:
            return False
    neighbours_a = {vertex_of[alpha[dart]] for dart in _ring(vertex_of, a)}
    if vertex_of[c] in neighbours_a - {vertex_of[b]}:
        return False
    neighbours_b = {vertex_of[alpha[dart]] for dart in _ring(vertex_of, b)}
    if vertex_of[d] in neighbours_b - {vertex_of[a]}:
        return False
    return True


_RINGS: dict[int, list[list[int]]] = {}


def _ring(vertex_of: list[int], dart: int) -> list[int]:
    return _RINGS[id(vertex_of)][vertex_of[dart]]


def _seed_involution(degrees: list[int], vertex_of: list[int],
                     rng: random.Random) -> list[int] | None:
    """A pairing that already respects simplicity and degree alternation."""

    darts = len(vertex_of)
    for _ in range(400):
        free = list(range(darts))
        rng.shuffle(free)
        alpha = [-1] * darts
        adjacent: dict[int, set[int]] = {v: set() for v in range(len(degrees))}
        stuck = False
        while free:
            dart = free.pop()
            if alpha[dart] >= 0:
                continue
            options = [
                other for other in free
                if alpha[other] < 0
                and vertex_of[other] != vertex_of[dart]
                and degrees[vertex_of[other]] != degrees[vertex_of[dart]]
                and vertex_of[other] not in adjacent[vertex_of[dart]]
            ]
            if not options:
                stuck = True
                break
            other = rng.choice(options)
            alpha[dart], alpha[other] = other, dart
            adjacent[vertex_of[dart]].add(vertex_of[other])
            adjacent[vertex_of[other]].add(vertex_of[dart])
        if not stuck and all(mate >= 0 for mate in alpha):
            return alpha
    return None


def search(order: int, seed: int, restarts: int, steps: int,
           width: int = 5) -> dict | None:
    rng = random.Random(seed)
    for profile in profiles(order)[:width]:
        degrees = profile
        cycles, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
        _RINGS[id(vertex_of)] = [list(ring) for ring in cycles]
        darts = sum(degrees)
        for _ in range(restarts):
            alpha = _seed_involution(degrees, vertex_of, rng)
            if alpha is None:
                break
            current = score(alpha, degrees, vertex_of, sigma_inverse)
            for step in range(steps):
                if current == 0:
                    return {"degrees": degrees, "alpha": alpha}
                temperature = max(0.05, 1.5 * (1.0 - step / steps))
                a, c = rng.randrange(darts), rng.randrange(darts)
                if not _valid_switch(alpha, degrees, vertex_of, a, c):
                    continue
                b, d = alpha[a], alpha[c]
                alpha[a], alpha[c] = c, a
                alpha[b], alpha[d] = d, b
                candidate = score(alpha, degrees, vertex_of, sigma_inverse)
                if candidate <= current or rng.random() < math.exp(
                    (current - candidate) / temperature
                ):
                    current = candidate
                else:
                    alpha[a], alpha[b] = b, a
                    alpha[c], alpha[d] = d, c
            if current == 0:
                return {"degrees": degrees, "alpha": alpha}
    return None


def to_certificate(degrees: list[int], alpha: list[int]) -> dict:
    cycles, vertex_of, _, _ = cycles_from_degrees(degrees)
    rows = []
    for vertex, ring in enumerate(cycles):
        neighbours = [vertex_of[alpha[dart]] for dart in ring]
        start = neighbours.index(min(neighbours))
        rows.append({"id": vertex, "clockwise": neighbours[start:] + neighbours[:start]})
    return {"format": "apg-plane-rotation-v1", "vertices": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("orders", type=int, nargs="+")
    parser.add_argument("--seed", type=int, default=20260901)
    parser.add_argument("--restarts", type=int, default=40)
    parser.add_argument("--steps", type=int, default=200_000)
    parser.add_argument("--width", type=int, default=5,
                        help="how many degree profiles to try")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    for order in args.orders:
        hit = search(order, args.seed + order, args.restarts, args.steps, args.width)
        if hit is None:
            print(f"order {order}: no hit", flush=True)
            continue
        certificate = to_certificate(hit["degrees"], hit["alpha"])
        print(f"order {order}: FOUND", flush=True)
        if args.out:
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / f"APG_{order}.json").write_text(
                json.dumps(certificate, indent=1, sort_keys=True) + "\n"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
