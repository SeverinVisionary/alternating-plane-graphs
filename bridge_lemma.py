#!/usr/bin/env python3
"""Bridges in alternating plane graphs, and what they cost.

Conjecture 10.1 as proved in `conjecture_10_1.py` rests on convention **(C2)**:
no edge has the same face on both sides.  (C2) is the paper's *reading* of
Definition 2.1 -- a bridge makes a face adjacent to itself, and the paper takes
"adjacent faces differ in size" to forbid that -- but it is not a hypothesis
written into the definition, and it is the single place where the argument
depends on an interpretation rather than a stated axiom.  Every leg of the
2026-09-02 review panel named it.

This module removes the interpretation from half two, the `X,2` case.  It does
so with the *weak* reading, in which face alternation constrains only pairs of
**distinct** faces and bridges are therefore allowed, and derives a parity
obstruction that bridges cannot satisfy.

## The parity lemma

Let `G` be a plane graph with exactly two face sizes `s1 < s2`, in which
distinct faces sharing an edge have different sizes.  Colour each face by its
size.  This is a colouring of the faces by two colours, proper on every pair of
distinct adjacent faces -- and a bridge is precisely an edge whose two sides
carry the same face, hence the same colour.

Walk the darts around a vertex `v` in rotation order.  Consecutive corners are
separated by an edge at `v`, and the corner colour flips across every non-bridge
edge and holds across every bridge.  The walk closes up, so the number of flips
is even:

    deg(v) - bridges_at(v)  is even, at every vertex v.            (P)

`(P)` is the whole content of the classical "a plane graph is face-2-colourable
iff it is Eulerian", stated so that bridges are permitted rather than assumed
away.  With no bridges it says every degree is even.

## What (P) costs a bridge

Let `e = uv` be a bridge and let `B` be a leaf block of the block-cut tree.  `B`
is not a single edge -- that would give its non-cut vertex degree one, and
Definition 2.1 demands degree at least three -- so `B` is 2-connected and has no
bridge inside it.  Every `w` in `B` other than its cut vertex therefore has
`bridges_at(w) = 0`, so by `(P)` **`deg(w)` is even**.

That is the obstruction `conjecture_10_1.py` needs and could not previously
state: in the `X,2` class, the vertices of every leaf block are forced even
except at the single cut vertex, and Definition 2.1's own degree alternation
then has to be satisfied inside a block whose degrees are all even.

## Two consequences that are proved, and one that is not

Proved, and gated in `test_bridge_lemma.py`:

* `(P)` itself, in both directions -- `parity_holds` agrees with
  `two_colouring is not None` on all 26 certificates and on five hand-built
  controls, two of them bridged.  `K4` and the cube are the negative controls:
  odd degrees, no face 2-colouring, `(P)` false.
* every vertex on no bridge has even degree, hence degree at least four, since
  Definition 2.1 already forbids degree two.

And the consequence they were built for, now **closed** and written up in
`conjecture_10_1.py` under "Removing the dependence on (C2)": there is no
`X,2`-APG at all under the weak reading, bridged or not.  In particular such a
graph would be bridgeless, so (C2) is a consequence of Definition 2.1 rather
than a reading of it, and Conjecture 10.1 no longer depends on the
interpretation.

`(P)` is what makes the count work.  It forces the degree-3 endpoint of any
edge that could exceed the per-edge budget to lie on exactly one bridge; and
since Definition 2.1(c) makes a bridge's two ends differ in degree, only one end
can be such a vertex, so at most two positive edges are tethered to each bridge.
Two are worth `2/24 = 1/12` against that bridge's own deficit of `-1/6`, leaving
`-1/12` per bridge where Euler demands a total of `+2`.

### A retracted step

An earlier version of this docstring claimed that each side of a bridge has at
least five vertices, arguing that every vertex of a side other than the bridge
endpoint "has all its edges inside `A`, hence even degree at least four".  That
is a **non sequitur**, and an independent review caught it: a side of a
bridge may contain further bridges, and `(P)` permits odd degree at their
endpoints.  The claim is recoverable by applying the argument to a leaf of the
bridge tree instead, but nothing needs it: Step 0 of the closing argument gets
the bound it was there to supply -- the bridge's face has size at least 8 --
directly from `deg_A(u) >= 2`, which forces a side to have at least three
vertices and therefore a facial walk of length at least three.

`is_apg_weak` decides Definition 2.1 under the weak reading.  It differs from
`general_apg.is_apg` in exactly the two places that matter here: it permits a
facial walk to repeat a vertex, and it applies face alternation only to
distinct faces.  `general_apg.is_apg` implements the (C2) reading, so it rejects
every bridged graph -- which is correct for the paper's class and useless for
deciding whether (C2) is a consequence or an assumption.
"""
from __future__ import annotations

from certificate_tools import cycles_from_degrees


def faces(alpha: list[int], sigma_inverse: list[int]) -> tuple[list[int], list[int]]:
    """Face index per dart, and the size of each face, sizes in dart counts."""

    phi = [sigma_inverse[alpha[dart]] for dart in range(len(alpha))]
    face_of = [-1] * len(alpha)
    sizes: list[int] = []
    for dart in range(len(alpha)):
        if face_of[dart] >= 0:
            continue
        index, cursor, size = len(sizes), dart, 0
        while face_of[cursor] < 0:
            face_of[cursor] = index
            size += 1
            cursor = phi[cursor]
        sizes.append(size)
    return face_of, sizes


def bridge_darts(alpha: list[int], face_of: list[int]) -> set[int]:
    """Darts whose edge carries the same face on both sides.

    In a plane graph that is exactly the set of bridges: an edge is a bridge iff
    its two sides lie on one face.
    """

    return {dart for dart in range(len(alpha)) if face_of[dart] == face_of[alpha[dart]]}


def is_apg_weak(degrees: list[int], alpha: list[int]) -> bool:
    """Definition 2.1 under the weak reading: bridges and repeated corners allowed.

    Simple, connected, spherical; degrees and face sizes at least three;
    adjacent vertices of different degree; and **distinct** faces sharing an
    edge of different size.  Nothing here forbids a bridge.
    """

    if len(degrees) < 4 or any(degree < 3 for degree in degrees):
        return False
    cycles, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
    if len(alpha) != len(vertex_of):
        return False
    if any(alpha[alpha[dart]] != dart or alpha[dart] == dart for dart in range(len(alpha))):
        return False
    seen: set[tuple[int, int]] = set()
    for dart, mate in enumerate(alpha):
        u, v = vertex_of[dart], vertex_of[mate]
        if u == v or degrees[u] == degrees[v]:
            return False
        if dart < mate:
            key = (min(u, v), max(u, v))
            if key in seen:
                return False
            seen.add(key)
    face_of, sizes = faces(alpha, sigma_inverse)
    if any(size < 3 for size in sizes):
        return False
    for dart in range(len(alpha)):
        here, there = face_of[dart], face_of[alpha[dart]]
        if here != there and sizes[here] == sizes[there]:
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


def bridges_at(degrees: list[int], alpha: list[int]) -> list[int]:
    """Number of bridges incident to each vertex."""

    _, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
    face_of, _ = faces(alpha, sigma_inverse)
    counts = [0] * len(degrees)
    for dart in bridge_darts(alpha, face_of):
        counts[vertex_of[dart]] += 1
    return counts


def parity_holds(degrees: list[int], alpha: list[int]) -> bool:
    """The lemma `(P)`: `deg(v) - bridges_at(v)` is even at every vertex."""

    counts = bridges_at(degrees, alpha)
    return all((degree - count) % 2 == 0 for degree, count in zip(degrees, counts))


def face_size_set(degrees: list[int], alpha: list[int]) -> set[int]:
    _, _, _, sigma_inverse = cycles_from_degrees(degrees)
    _, sizes = faces(alpha, sigma_inverse)
    return set(sizes)


def alpha_from_rotation(rotation: dict[int, list[int]]) -> tuple[list[int], list[int]]:
    """`(degrees, alpha)` from an explicit clockwise rotation system.

    Same convention as `certificate_tools.alpha_from_certificate`, but taking a
    dict rather than a certificate file, so test graphs can be written inline.
    Only simple graphs are expressible: a neighbour may appear once per vertex.
    """

    degree_of = {vertex: len(ring) for vertex, ring in rotation.items()}
    slots = sorted(rotation, key=lambda vertex: (degree_of[vertex], vertex))
    relabel = {vertex: index for index, vertex in enumerate(slots)}
    degrees = [degree_of[vertex] for vertex in slots]
    cycles, _, _, _ = cycles_from_degrees(degrees)
    alpha = [-1] * sum(degrees)
    for index, vertex in enumerate(slots):
        for position, neighbour in enumerate(rotation[vertex]):
            alpha[cycles[index][position]] = cycles[relabel[neighbour]][
                rotation[neighbour].index(vertex)
            ]
    if any(mate < 0 for mate in alpha) or any(alpha[alpha[d]] != d for d in range(len(alpha))):
        raise ValueError("not a symmetric rotation system")
    return degrees, alpha


def two_colouring(degrees: list[int], alpha: list[int]) -> dict[int, int] | None:
    """A proper 2-colouring of the faces, or `None` if none exists.

    Proper on **distinct** adjacent faces only, so a bridge does not by itself
    obstruct a colouring.  Computed from the dual, with no reference to face
    sizes, so `parity_holds` can be tested against the colouring hypothesis
    rather than against the APG hypothesis that normally supplies it.
    """

    _, _, _, sigma_inverse = cycles_from_degrees(degrees)
    face_of, sizes = faces(alpha, sigma_inverse)
    incident: dict[int, set[int]] = {index: set() for index in range(len(sizes))}
    for dart in range(len(alpha)):
        here, there = face_of[dart], face_of[alpha[dart]]
        if here != there:
            incident[here].add(there)
    colour: dict[int, int] = {}
    for start in range(len(sizes)):
        if start in colour:
            continue
        colour[start], stack = 0, [start]
        while stack:
            face = stack.pop()
            for other in incident[face]:
                if other not in colour:
                    colour[other] = 1 - colour[face]
                    stack.append(other)
                elif colour[other] == colour[face]:
                    return None
    return colour
