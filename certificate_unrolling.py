#!/usr/bin/env python3
"""Which cover class the certificates are actually built from.

The independent review's objection stands: `(1,0)` and `(2,3)` name nothing without
a homology basis, so neither the uncappability claim -- stated about "the
`(1,0)` unrolling" -- nor the certificates' stated provenance was reproducible.
`unrolling_class.py` fixes the coordinates; this module answers the question in
them, by looking at the certificates rather than at the narrative.

**Radius-1 cannot do it.** Every cyclic cover of the same quotient has the same
local picture: `omega` changes which *copy* an edge lands in, never which
vertex type, so degrees and neighbour degrees are identical in every class.
What distinguishes classes is which closed walks in the quotient lift to
cycles, i.e. which have zero total voltage. So the invariant used here is the
**number of simple cycles of each length 3..6 through a vertex**, which reads
that difference directly.

The answer, over all 26 certificates:

* every certificate of order >= 48 contains vertices whose cycle profile is
  exactly that of a deep-interior vertex of the **`(p, q) = (1, -1)`** cover --
  57 of them at order 109, 61 at order 110, growing linearly with the period
  count;
* **no** certificate contains a single vertex matching the `(p, q) = (-2, -1)`
  cover, which is the class actually committed in `periodic_strip.py` and
  labelled there "the `(1,0)` unrolling";
* orders 46, 47 and 49 contain none of either: at `t = 2, 5, 3` periods a ball
  of radius 3 still reaches a cap, which is the same boundary effect
  `pumping_family.py` sees at `t = 2`.

So the repository's story is structurally right -- one class caps and another
does not -- and its labels are wrong in the only coordinates anyone can check.
In the normal form of `unrolling_class.py`:

    the strip inside the certificates   (p, q) = (1, -1),  omega = (1, 2, 0, 0, -1, 0)
    the strip in periodic_strip.py      (p, q) = (-2, -1), omega = (-2, -1, 0, -1, -2, -1)

and the uncappability search therefore concerns the second, not the first.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGETS_DIR = HERE / "certificates" / "targets"

EDGES = (("y", "z"), ("y", "z"), ("y", "z"), ("x", "z"), ("x", "z"), ("x", "y"))
TYPE_OF_DEGREE = {3: "x", 4: "y", 5: "z"}

CERTIFICATE_CLASS = (1, -1)     # measured here
COMMITTED_CLASS = (-2, -1)      # periodic_strip.py's omega, in the same normal form
MAX_CYCLE = 6


def cover(p: int, q: int, periods: int = 40) -> dict:
    """The cyclic cover of the quotient in class `(p, q)`, truncated."""

    voltages = (p, p - q, 0, 0, q, 0)
    adjacency: dict = collections.defaultdict(set)
    for edge, (first, second) in enumerate(EDGES):
        for copy in range(periods):
            other = copy + voltages[edge]
            if 0 <= other < periods:
                adjacency[(first, copy)].add((second, other))
                adjacency[(second, other)].add((first, copy))
    return {vertex: sorted(neighbours) for vertex, neighbours in adjacency.items()}


def cycle_profile(adjacency: dict, start, max_length: int = MAX_CYCLE) -> tuple:
    """Simple cycles of each length through `start`, as a sorted tuple of pairs."""

    counts: collections.Counter = collections.Counter()

    def walk(path: list, seen: set) -> None:
        vertex = path[-1]
        for neighbour in adjacency[vertex]:
            if neighbour == start and len(path) >= 3:
                counts[len(path)] += 1
            elif neighbour not in seen and len(path) < max_length:
                walk(path + [neighbour], seen | {neighbour})

    walk([start], {start})
    return tuple(sorted((length, counts[length] // 2) for length in range(3, max_length + 1)))


def interior_profiles(p: int, q: int) -> dict:
    """The profile of a deep-interior vertex of each degree in class `(p, q)`."""

    adjacency = cover(p, q)
    return {
        degree: cycle_profile(adjacency, (TYPE_OF_DEGREE[degree], 20))
        for degree in (3, 4, 5)
    }


def certificate_adjacency(order: int) -> tuple[dict, dict]:
    data = json.loads((TARGETS_DIR / f"TARGET_{order}.json").read_text())
    rotation = {row["id"]: list(row["clockwise"]) for row in data["vertices"]}
    adjacency = {vertex: sorted(ring) for vertex, ring in rotation.items()}
    degrees = {vertex: len(ring) for vertex, ring in rotation.items()}
    return adjacency, degrees


def count_matching(order: int, p: int, q: int) -> int:
    """How many vertices of this certificate look like the interior of `(p, q)`."""

    reference = interior_profiles(p, q)
    adjacency, degrees = certificate_adjacency(order)
    return sum(
        1
        for vertex in adjacency
        if cycle_profile(adjacency, vertex) == reference.get(degrees[vertex])
    )


def main() -> int:
    orders = (
        list(range(46, 57)) + list(range(67, 75)) + list(range(88, 93)) + [109, 110]
    )
    print(f"{'order':>6} {'(1,-1)':>8} {'(-2,-1)':>9}")
    for order in orders:
        print(
            f"{order:>6} {count_matching(order, *CERTIFICATE_CLASS):>8}"
            f" {count_matching(order, *COMMITTED_CLASS):>9}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
