#!/usr/bin/env python3
"""Vertex connectivity of a plane APG, and the reduction Conjecture 10.3 needs.

Conjecture 10.3 of the primary paper asks for a **3-connected** alternating
plane graph on every order from 19 up.  A `(3,4,5)`-APG is an APG, so any of
them that is 3-connected is a witness -- which turns the settled Conjecture
10.2 into progress on 10.3, but only after 3-connectivity is checked rather
than assumed.

Two routines, and the reason there are two.  `is_three_connected` is the honest
brute force: remove every pair and test connectivity.  `separating_pairs_on_faces`
uses a reduction that makes the same test local, and the suite runs both against
each other so the reduction is never trusted on its own.

> **Lemma.** Let `G` be a 2-connected plane graph and `{u, v}` a separating
> pair.  Then some face of `G` has `u` and `v` on its boundary, not consecutively.
>
> *Proof.* Let `H_1, ..., H_k`, `k >= 2`, be the components of `G - {u, v}`.
> Each `H_i` occupies a contiguous block of the rotation at `u`, since a
> neighbour of `u` in `H_i` cannot be separated in the plane from the rest of
> `H_i` without passing through `u` or `v`.  So the rotation at `u` has at least
> two blocks, and between two consecutive blocks -- say after `a` in `H_1` and
> before `b` in `H_2` -- sits a face `f` with the corner `a, u, b`.  Its facial
> walk leaves `u` into `H_2` and must return to `H_1`; it can only cross via `u`
> or `v`, and using `u` twice would make `u` a cut vertex, which a 2-connected
> plane graph does not have.  So it crosses at `v`, and `f` carries both.  Both
> neighbours of `u` along `f` are `a` and `b`, neither of which is `v`, so `u`
> and `v` are not consecutive on `f`. QED

Because a `(3,4,5)`-APG has faces of at most five vertices, the lemma leaves at
most `5 * |F|` candidate pairs instead of `|V| choose 2` -- and every candidate
pair lies inside one face, which is what makes the property transfer along the
spliced family in `pumping_splice.py`.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def adjacency(rotation: dict[int, list[int]]) -> dict[int, set[int]]:
    return {vertex: set(ring) for vertex, ring in rotation.items()}


def load_rotation(path: Path) -> dict[int, list[int]]:
    data = json.loads(Path(path).read_text())
    return {row["id"]: list(row["clockwise"]) for row in data["vertices"]}


def is_connected(graph: dict[int, set[int]], removed: frozenset = frozenset()) -> bool:
    alive = [vertex for vertex in graph if vertex not in removed]
    if not alive:
        return True
    seen, stack = {alive[0]}, [alive[0]]
    while stack:
        vertex = stack.pop()
        for neighbour in graph[vertex]:
            if neighbour not in removed and neighbour not in seen:
                seen.add(neighbour)
                stack.append(neighbour)
    return len(seen) == len(alive)


def is_three_connected(rotation: dict[int, list[int]]) -> bool:
    """Brute force: no cut vertex and no separating pair."""

    graph = adjacency(rotation)
    if len(graph) < 4 or not is_connected(graph):
        return False
    if any(not is_connected(graph, frozenset({v})) for v in graph):
        return False
    return all(
        is_connected(graph, frozenset(pair))
        for pair in itertools.combinations(sorted(graph), 2)
    )


def faces(rotation: dict[int, list[int]]) -> list[list[int]]:
    """Facial walks as vertex lists, from the rotation alone."""

    predecessor = {}
    for vertex, ring in rotation.items():
        for index, neighbour in enumerate(ring):
            predecessor[(vertex, neighbour)] = ring[index - 1]
    walks, seen = [], set()
    for dart in predecessor:
        if dart in seen:
            continue
        walk, cursor = [], dart
        while cursor not in seen:
            seen.add(cursor)
            walk.append(cursor[0])
            tail, head = cursor
            cursor = (head, predecessor[(head, tail)])
        walks.append(walk)
    return walks


def candidate_pairs(rotation: dict) -> set[tuple]:
    """Pairs the lemma allows to be separating: non-consecutive on some face.

    Kept separate from the search so the spliced family can reason about *which*
    pairs are candidates without deciding connectivity for each one.
    """

    candidates = set()
    for walk in faces(rotation):
        size = len(walk)
        for i in range(size):
            for j in range(i + 1, size):
                if (j - i) % size in (1, size - 1):
                    continue
                candidates.add(tuple(sorted((walk[i], walk[j]), key=str)))
    return candidates


def separating_pairs_on_faces(rotation: dict) -> list[tuple]:
    """Separating pairs, searched only where the lemma allows them to be."""

    graph = adjacency(rotation)
    return sorted(
        (pair for pair in candidate_pairs(rotation)
         if not is_connected(graph, frozenset(pair))),
        key=str,
    )


def main() -> int:
    targets = sorted((HERE / "certificates" / "targets").glob("TARGET_*.json"))
    for path in targets:
        rotation = load_rotation(path)
        print(f"{path.name:>18}  n={len(rotation):>3}  "
              f"3-connected={is_three_connected(rotation)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
