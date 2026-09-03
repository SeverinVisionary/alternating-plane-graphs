#!/usr/bin/env python3
"""Alternating plane graphs without the `(3,4,5)` restriction, and a search.

Conjecture 10.3 asks for a 3-connected **alternating plane graph** on every
order from 19 up.  Everything else in this directory is about the `(3,4,5)`
subclass, where Definition 3.1 pins degrees and face sizes to `{3,4,5}`.  That
subclass is extremely rigid -- a sweep over every single two-edge switch of
every one of the 26 certificates found **zero** switches that leave a valid
`(3,4,5)`-APG -- which is why `closed_map_search.py` plateaus.

The general class is Definition 2.1 and is much looser: degrees and face sizes
need only be at least three, and only the two alternation conditions bind.  So
the orders Conjecture 10.3 still needs are worth attacking here rather than in
the `(3,4,5)` lane.

`is_apg` is an independent decision procedure for the general class, written
over darts and an involution.  It is *not* `fast_apg_check.is_apg` with the
size test removed: that one additionally requires the `(3,4,5)` profile
identity `sorted(sizes) == sorted(degrees)`, which is a theorem about the
subclass and false in general.  The two agree on the subclass, which
`test_general_apg.py` checks at all 26 certificate orders.

Euler bounds the profile: `F = E - n + 2`, every face size is at least three so
`2E >= 3F`, and every degree is at least three so `2E >= 3n`.  Together
`ceil(3n/2) <= E <= 3n - 6`.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

from certificate_tools import cycles_from_degrees


def edge_bounds(order: int) -> tuple[int, int]:
    return (-(-3 * order // 2), 3 * order - 6)


def _faces(alpha: list[int], sigma_inverse: list[int]) -> tuple[list[int], list[int]]:
    """Face index per dart, and the size of each face."""

    darts = len(alpha)
    phi = [sigma_inverse[alpha[dart]] for dart in range(darts)]
    face_of = [-1] * darts
    sizes: list[int] = []
    for dart in range(darts):
        if face_of[dart] >= 0:
            continue
        index, cursor, size = len(sizes), dart, 0
        while face_of[cursor] < 0:
            face_of[cursor] = index
            size += 1
            cursor = phi[cursor]
        sizes.append(size)
    return face_of, sizes


def is_apg(degrees: list[int], alpha: list[int]) -> bool:
    """Decide Definition 2.1 **plus simple facial walks**, over a rotation system.

    Simple, connected, spherical; every degree and every face size at least
    three; adjacent vertices of different degree; faces sharing an edge of
    different size -- and every facial walk a simple cycle.

    That last condition is **not** in Definition 2.1 and makes this test
    strictly narrower than the paper's class: it demands 2-connectivity, whereas
    the paper says on p. 362 that some of its Section 7 alternating plane graphs
    are not 3-connected and some are not 2-connected.  Everything this
    repository counts as a witness passes anyway, so the Conjecture 10.3
    bookkeeping is unaffected -- a stricter test can only reject, never wrongly
    accept.  But a non-2-connected candidate would be rejected here for the
    wrong reason, which matters for anyone using this to hunt counterexamples.
    Flagged by independent review.
    """

    if len(degrees) < 4 or any(degree < 3 for degree in degrees):
        return False
    cycles, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
    if any(alpha[alpha[dart]] != dart or alpha[dart] == dart for dart in range(len(alpha))):
        return False
    seen: set[tuple[int, int]] = set()
    for dart, mate in enumerate(alpha):
        u, v = vertex_of[dart], vertex_of[mate]
        if u == v or degrees[u] == degrees[v]:
            return False
        key = (min(u, v), max(u, v))
        if dart < mate:
            if key in seen:
                return False
            seen.add(key)
    face_of, sizes = _faces(alpha, sigma_inverse)
    if any(size < 3 for size in sizes):
        return False
    walks: dict[int, list[int]] = {}
    for dart in range(len(alpha)):
        walks.setdefault(face_of[dart], []).append(vertex_of[dart])
    if any(len(set(corners)) != len(corners) for corners in walks.values()):
        return False
    if any(sizes[face_of[dart]] == sizes[face_of[alpha[dart]]] for dart in range(len(alpha))):
        return False
    reached, stack = {0}, [0]
    while stack:
        vertex = stack.pop()
        for dart in cycles[vertex]:
            other = vertex_of[alpha[dart]]
            if other not in reached:
                reached.add(other)
                stack.append(other)
    if len(reached) != len(degrees):
        return False
    return len(degrees) - len(alpha) // 2 + len(sizes) == 2


def score(degrees: list[int], alpha: list[int], vertex_of: list[int],
          sigma_inverse: list[int]) -> int:
    """Zero exactly when `is_apg` holds; graded so annealing has a gradient."""

    penalty = 0
    seen: set[tuple[int, int]] = set()
    for dart, mate in enumerate(alpha):
        u, v = vertex_of[dart], vertex_of[mate]
        if u == v or degrees[u] == degrees[v]:
            penalty += 2
        elif dart < mate:
            key = (min(u, v), max(u, v))
            if key in seen:
                penalty += 2
            seen.add(key)
    face_of, sizes = _faces(alpha, sigma_inverse)
    walks: dict[int, list[int]] = {}
    for dart in range(len(alpha)):
        walks.setdefault(face_of[dart], []).append(vertex_of[dart])
    for index, size in enumerate(sizes):
        if size < 3:
            penalty += 3 - size
        corners = walks[index]
        penalty += len(corners) - len(set(corners))
    for dart, mate in enumerate(alpha):
        if dart < mate and sizes[face_of[dart]] == sizes[face_of[mate]]:
            penalty += 1
    expected = len(alpha) // 2 - len(degrees) + 2      # Euler's face count
    penalty += abs(len(sizes) - expected)
    return penalty


def random_profile(order: int, rng: random.Random) -> list[int] | None:
    """A degree sequence with a legal edge count, biased to few distinct values.

    Alternation makes equal degrees an independent set, so a profile with two
    or three distinct degrees is much easier to realise than a spread one.
    """

    low, high = edge_bounds(order)
    edges = rng.randint(low, high)
    total = 2 * edges
    values = rng.sample([3, 4, 5, 6, 7, 8], rng.choice((2, 2, 2, 3)))
    for _ in range(200):
        degrees = [rng.choice(values) for _ in range(order)]
        shortfall = total - sum(degrees)
        for _ in range(abs(shortfall)):
            index = rng.randrange(order)
            step = 1 if shortfall > 0 else -1
            if 3 <= degrees[index] + step <= max(values):
                degrees[index] += step
        if sum(degrees) == total and len(set(degrees)) > 1:
            return sorted(degrees)
    return None


def _seed(degrees: list[int], vertex_of: list[int], rng: random.Random) -> list[int] | None:
    """A pairing that already respects simplicity and degree alternation."""

    darts = len(vertex_of)
    for _ in range(200):
        free = list(range(darts))
        rng.shuffle(free)
        alpha = [-1] * darts
        adjacent: dict[int, set[int]] = {v: set() for v in range(len(degrees))}
        ok = True
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
                ok = False
                break
            other = rng.choice(options)
            alpha[dart], alpha[other] = other, dart
            adjacent[vertex_of[dart]].add(vertex_of[other])
            adjacent[vertex_of[other]].add(vertex_of[dart])
        if ok and all(mate >= 0 for mate in alpha):
            return alpha
    return None


def search(order: int, seed: int, attempts: int, steps: int):
    rng = random.Random(seed)
    for _ in range(attempts):
        degrees = random_profile(order, rng)
        if degrees is None:
            continue
        cycles, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
        alpha = _seed(degrees, vertex_of, rng)
        if alpha is None:
            continue
        darts = len(alpha)
        current = score(degrees, alpha, vertex_of, sigma_inverse)
        for step in range(steps):
            if current == 0 and is_apg(degrees, alpha):
                return degrees, alpha
            temperature = 1.0 * (0.02 / 1.0) ** (step / steps)
            a, c = rng.randrange(darts), rng.randrange(darts)
            b, d = alpha[a], alpha[c]
            if len({a, b, c, d}) != 4:
                continue
            alpha[a], alpha[c] = c, a
            alpha[b], alpha[d] = d, b
            candidate = score(degrees, alpha, vertex_of, sigma_inverse)
            if candidate <= current or rng.random() < math.exp(
                (current - candidate) / temperature
            ):
                current = candidate
            else:
                alpha[a], alpha[b] = b, a
                alpha[c], alpha[d] = d, c
        if current == 0 and is_apg(degrees, alpha):
            return degrees, alpha
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
    parser.add_argument("--attempts", type=int, default=200)
    parser.add_argument("--steps", type=int, default=40_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    import connectivity as cn
    for order in args.orders:
        hit = search(order, args.seed + order, args.attempts, args.steps)
        if hit is None:
            print(f"order {order}: no hit", flush=True)
            continue
        degrees, alpha = hit
        certificate = to_certificate(degrees, alpha)
        rotation = {row["id"]: row["clockwise"] for row in certificate["vertices"]}
        three = cn.is_three_connected(rotation)
        print(f"order {order}: FOUND, 3-connected={three}, degrees={sorted(set(degrees))}",
              flush=True)
        if args.out and three:
            args.out.mkdir(parents=True, exist_ok=True)
            (args.out / f"APG3_{order}.json").write_text(
                json.dumps(certificate, indent=1, sort_keys=True) + "\n"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
