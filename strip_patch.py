#!/usr/bin/env python3
"""Finite cylinder patches cut from the increment-3 periodic strip.

`periodic_strip.py` verifies the infinite object.  This module cuts a finite
piece out of it and reports, exactly, what a cap would have to supply: which
vertices are short of their degree, by how much, and what the boundary looks
like.  Every capping route needs that interface, so it is derived here once
rather than by hand.

The lift, written out from the quotient certificate (edge `e` joins copy `k`
of its first endpoint to copy `k + omega[e]` of its second):

```text
e0: y_k -- z_{k-2}      e3: x_k -- z_{k-1}
e1: y_k -- z_{k-1}      e4: x_k -- z_{k-2}
e2: y_k -- z_k          e5: x_k -- y_{k-1}
```

so `x_k` reaches down (to levels `k-1`, `k-2`) only, `y_k` reaches down two
levels and up one, and `z_j` is reached from above only.  A *straight* cut
keeps every vertex whose level lies in a window and drops the rest; the
resulting deficiency is what `straight_patch` reports.

Nothing here is a construction.  A patch is an open disk-with-two-boundaries,
not an APG, and both independent verifiers will reject it as such -- correctly.
It becomes a claim only when caps close it and the closed rotation system
passes them.

Note the unrolling: this module cuts the ``(1,0)`` strip, which is now known to
be **uncappable**.  The interface it derives is still the right shape -- and the
constant-in-``m`` property is what makes the whole approach work -- but the
certificates in ``certificates/targets/`` come from capping a ``(2,3)``
unrolling of the same quotient instead.
"""
from __future__ import annotations

import argparse
import collections
import json
from typing import Iterable

from periodic_strip import DEG, EDGES, OMEGA, ROT

#: Lifted edge ``e`` joins ``(u, k)`` to ``(v, k + OMEGA[e])``.
LIFT = tuple((EDGES[e][0], EDGES[e][1], OMEGA[e]) for e in range(len(EDGES)))


def lifted_edges(levels: Iterable[int]) -> list[tuple[tuple[str, int], tuple[str, int]]]:
    """Every lifted edge with *both* endpoints inside ``levels``."""

    keep = set(levels)
    edges = []
    for k in sorted(keep):
        for u, v, shift in LIFT:
            a, b = (u, k), (v, k + shift)
            if a[1] in keep and b[1] in keep:
                edges.append((a, b))
    return edges


def straight_patch(periods: int) -> dict[str, object]:
    """Cut a straight patch spanning ``periods`` levels and report its interface.

    Returns the surviving adjacency, each vertex's realised degree, and the
    deficiency -- the number of edges a cap must still supply at that vertex.
    A vertex of deficiency zero is already interior and no cap may touch it.
    """

    if periods < 1:
        raise ValueError("a patch needs at least one period")
    levels = range(periods)
    edges = lifted_edges(levels)
    adjacency: dict[tuple[str, int], list[tuple[str, int]]] = collections.defaultdict(list)
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    vertices = [(v, k) for k in levels for v in ("x", "y", "z")]
    realised = {w: len(adjacency.get(w, ())) for w in vertices}
    deficiency = {w: DEG[w[0]] - realised[w] for w in vertices}
    if any(value < 0 for value in deficiency.values()):
        raise AssertionError("a lifted vertex exceeded its quotient degree")
    boundary = sorted((w for w in vertices if deficiency[w] > 0), key=lambda w: (w[1], w[0]))
    interior = [w for w in vertices if deficiency[w] == 0]
    return {
        "periods": periods,
        "vertices": vertices,
        "edges": edges,
        "adjacency": {w: sorted(adjacency.get(w, ())) for w in vertices},
        "realised_degree": realised,
        "deficiency": deficiency,
        "boundary": boundary,
        "interior": interior,
        "owed_edges": sum(deficiency.values()),
    }


def cap_arithmetic(a3: int, a4: int, a5: int, periods: int) -> dict[str, int]:
    """Profile of the closed map a cap pair with these counts would produce.

    Each period contributes one vertex of each degree, so ``v_d = a_d + m``.
    A closed APG needs ``v3 - v5 = 4``; that pins ``a3 - a5 = 4`` and leaves
    ``m`` free, which is what makes the family infinite.  ``v4 = n - 2r + 4``
    is then automatic, and this function asserts it rather than assuming it.
    """

    v3, v4, v5 = a3 + periods, a4 + periods, a5 + periods
    order = v3 + v4 + v5
    r = v3
    if v3 - v5 != 4:
        raise ValueError(f"caps give v3 - v5 = {v3 - v5}, but a closed APG needs 4")
    if v4 != order - 2 * r + 4:
        raise AssertionError("the v4 identity failed; the derivation is wrong")
    return {"order": order, "r": r, "v3": v3, "v4": v4, "v5": v5,
            "edges": 2 * order - 2, "faces": order}


def residues_closed(a3: int, a4: int, a5: int, smallest_periods: int = 1) -> dict[str, object]:
    """Which target orders a cap pair would close, and at which multiplicities."""

    targets = set(range(46, 57)) | set(range(67, 75)) | set(range(88, 93)) | {109, 110}
    base = cap_arithmetic(a3, a4, a5, smallest_periods)["order"]
    reachable = {}
    for target in sorted(targets):
        if target >= base and (target - base) % 3 == 0:
            reachable[target] = smallest_periods + (target - base) // 3
    return {"base_order": base, "residue": base % 3, "closes": reachable}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--periods", type=int, default=6)
    parser.add_argument("--output", type=str)
    arguments = parser.parse_args()

    patch = straight_patch(arguments.periods)
    print(f"straight patch, {patch['periods']} periods: "
          f"{len(patch['vertices'])} vertices, {len(patch['edges'])} edges")
    print(f"  interior vertices (deficiency 0): {len(patch['interior'])}")
    print(f"  boundary vertices: {len(patch['boundary'])}, edges owed to caps: {patch['owed_edges']}")
    by_level = collections.defaultdict(list)
    for w in patch["boundary"]:
        by_level[w[1]].append((w[0], DEG[w[0]], patch["deficiency"][w]))
    for level in sorted(by_level):
        rows = ", ".join(f"{v}(deg {d}, owes {n})" for v, d, n in sorted(by_level[level]))
        print(f"    level {level}: {rows}")

    print()
    print("cap arithmetic: a cap pair closes an infinite family iff a3 - a5 = 4")
    for a3, a4, a5 in ((4, 0, 0), (5, 2, 1), (6, 3, 2), (7, 1, 3)):
        profile = cap_arithmetic(a3, a4, a5, 1)
        reach = residues_closed(a3, a4, a5)
        print(f"  caps ({a3},{a4},{a5}): m=1 gives order {profile['order']} r={profile['r']}, "
              f"residue {reach['residue']} mod 3, closes {len(reach['closes'])} targets")

    if arguments.output:
        record = {
            "tool": "strip_patch.py",
            "note": "a patch is not an APG; it is the interface a cap must satisfy",
            "periods": patch["periods"],
            "boundary": [[w[0], w[1], patch["deficiency"][w]] for w in patch["boundary"]],
            "owed_edges": patch["owed_edges"],
            "interior_vertices": len(patch["interior"]),
            "nonexistence_claimed": False,
        }
        with open(arguments.output, "w") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
