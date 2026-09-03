#!/usr/bin/env python3
"""Conjecture 10.1: no `2,Y`- and no `X,2`-alternating plane graph.

> **Conjecture 10.1** (Althofer, Haugland, Scherer, Schneider, Van Cleemput,
> *Ars Math. Contemp.* **8** (2015) 337-363, p. 362.)
> There are no `2,Y`-alternating plane graphs and no `X,2`-alternating plane
> graphs.

By Definition 3.4 (p. 341) an `X,Y`-alternating plane graph is an alternating
plane graph with **exactly `X` distinct vertex degrees and exactly `Y` distinct
face sizes**. So the conjecture says an APG can never have only two distinct
vertex degrees, nor only two distinct face sizes.

Both halves are one inequality, applied twice.

## Two conventions, used by both halves

**(C1) Face size counts edge-side incidences** — the length of the boundary
walk, with multiplicity, not the number of distinct vertices. The paper never
defines it but uses this reading in `(3.1)` and `(9.2)`, both asserting
`sum(s * f_s) = 2e`.

**(C2) No edge has the same face on both sides.** The paper takes this as a
consequence of Definition 2.1 (p. 339: an APG "is always at least
2-edge-connected, since a plane graph with edge connectivity 1 contains a face
that is adjacent to itself"). **Both halves use it** — an earlier version of
this file wrongly said half one did not, and three reviewers caught that: a
bridge would contribute `2/r` rather than `1/r + 1/s` and break the face bound.
It is no longer a hypothesis: see "Removing the dependence on (C2)" below, where
each half is shown to hold under the weak reading too, so a hypothetical
counterexample would be bridgeless whichever way Definition 2.1 is read.

## The per-edge identities

For an edge `a = uv` with incident face *occurrences* `F-(a)`, `F+(a)`:

    v = sum over edges of (1/deg(u) + 1/deg(w))
    f = sum over edges of (1/|F-(a)| + 1/|F+(a)|)

Each identity is double counting: a vertex of degree `d` collects `d` terms of
`1/d`, a face of size `s` collects `s` terms of `1/s`. **Neither needs facial
walks to be simple cycles**, so repeated vertices, cut vertices, repeated face
occurrences and parallel dual edges are all irrelevant. This is the paper's own
convention behind `(9.2)`.

So `v + f = sum over edges of (that edge's four reciprocals)`. Euler gives
`v + f = e + 2`, so **some edge must contribute more than 1**. Both halves rule
that out.

## Half one: no `2,Y`-alternating plane graph

Degrees take exactly two values `d1 < d2`.

* **Vertex side.** Adjacent vertices differ in degree and only two degrees
  occur, so every edge joins a `d1`-vertex to a `d2`-vertex — in particular `G`
  is **bipartite** — and contributes `1/d1 + 1/d2 <= 1/3 + 1/4 = 7/12`.
* **Face side.** Bipartite means every boundary walk is a closed walk of even
  length, so by (C1) every face has even size, hence at least 4. By (C2) the two
  sides of an edge are distinct faces, and adjacent faces differ in size, so
  their sizes are distinct even numbers: one is at least 4 and the other at
  least 6. The edge contributes `1/r + 1/s <= 1/4 + 1/6 = 5/12`.

Every edge contributes at most `7/12 + 5/12 = 1`, so `v + f <= e`. **This
contradicts Euler.** (This is the paper's `(9.5)` with `1/2` replaced by
`1/d1 <= 1/3`; the derivation of `(9.5)` never used the degree 2, and the two
lines above reproduce it rather than cite it.)

## Half two: no `X,2`-alternating plane graph

Face sizes take exactly two values `s1 < s2`. Exactly the same inequality with
the roles exchanged — no dual graph is constructed, so Lemma 2.2 and its
3-edge-connectivity hypothesis are never invoked.

* **Face side.** By (C2) and face alternation every edge separates an `s1`-face
  from an `s2`-face, contributing `1/s1 + 1/s2 <= 1/3 + 1/4 = 7/12`.
* **Vertex side.** *Every degree is even.* Fix `u` of degree `d`, let its edges
  in rotation order be `e_1, ..., e_d` and let `F_i` be the face occupying the
  **corner** between `e_i` and `e_{i+1}`, indices mod `d`. The two sides of
  `e_i` are the occurrences `F_{i-1}` and `F_i`, distinct faces by (C2), so
  `|F_{i-1}| != |F_i|`. With only two sizes the cyclic word
  `|F_1|, ..., |F_d|` alternates, and a cyclic alternating binary word has even
  length, so `d` is even. A cut vertex merely repeats a face at
  **non-consecutive** corners, which does not disturb alternation — this is why
  the argument is stated over corners rather than over "the incident faces".
  Degrees are at least 3, hence at least 4; adjacent vertices have distinct even
  degrees, so every edge contributes `1/4 + 1/6 = 5/12` at most.

Again every edge contributes at most 1, so `v + f <= e`, **contradicting
Euler**.

## Connectivity

Euler is used as `v - e + f = 2`. Disconnected only strengthens the
contradiction: with `c` components `v - e + f = 1 + c`, so `v + f = e + 1 + c`.
Both per-edge identities hold in any plane graph, and a face whose boundary has
several closed walks still has even size, being a sum of even lengths.

## Removing the dependence on (C2)

(C2) is now a *consequence* rather than a hypothesis, for both halves, so the
theorem no longer rests on a reading of Definition 2.1.

**Half one**, directly, with no block decomposition. Step 0 below uses only
minimum degree 3 and simplicity, so it applies here too: a bridge's face has
size at least 8. A `2,Y`-APG is bipartite -- two degrees and adjacent vertices
differing forces every edge to join a `d1`-vertex to a `d2`-vertex -- so every
closed walk, a facial walk at a bridge included, has even length, and every face
has even size at least 4. Then

    a bridge         c <= 1/3 + 1/4 + 2/8         = 5/6
    a non-bridge     c <= 1/3 + 1/4 + 1/4 + 1/6   = 1

so every edge has `x <= 0` and `sum of x = 2` is contradicted at once.

An earlier version of this file argued half one through a leaf block of the
bridge tree instead, claiming "the degree split still caps the vertex side"
there. It does not: the attachment vertex loses its bridge inside the block, so
a degree-3 attachment vertex has degree 2 in it and `1/d1 + 1/d2 <= 7/12` fails.
The argument above needs no block at all.

**Half two.** Work under the weak reading throughout, in which face alternation
constrains only *distinct* faces and bridges are allowed. Write `x(a) := c(a) - 1`
for an edge's excess, so the identity above says `sum of x = 2` exactly. Let `B`
be the number of bridges and suppose `B >= 1`.

*Step 0: the bridge face has size at least 8, hence `s2 >= 8`.* Let `a = uv` be
a bridge with sides `A` and `B`. Then `deg_A(u) = deg(u) - 1 >= 2`, so `A` has at
least three vertices; a simple connected plane graph on at least three vertices
has every facial walk of length at least 3, since length 2 needs parallel edges
and length 1 a loop. The bridge's face is traced as the outer walk of `A`, the
bridge, the outer walk of `B`, and the bridge again, so
`|F| = |bdy A| + |bdy B| + 2 >= 8`.

*Step 1: only edges at a degree-3 vertex can be positive.* With `s1 >= 3` and
`s2 >= 8`, and `bridge_excess`, `heavy_edge_excess`, `light_edge_excess` below:

    a bridge                       c <= 1/3 + 1/4 + 2/8       = 5/6      x <= -1/6
    non-bridge, both ends >= 4     c <= 1/4 + 1/5 + 1/3 + 1/8 = 109/120  x <= -11/120
    non-bridge, an end of degree 3 c <= 1/3 + 1/4 + 1/3 + 1/8 = 25/24    x <= 1/24

Note what the second line settles: a bridge endpoint of degree 5 still cannot
make an edge positive.

*Step 2: positive edges are tethered to bridges, two at most.* Sharper than
Step 1: a positive edge is a **3-4 edge**.  Its face side is at most `11/24`, so
its vertex side must exceed `13/24`, and among pairs of distinct degrees at
least 3 only `1/3 + 1/4 = 14/24` does; even `1/3 + 1/5 = 12.8/24` does not.

Let `a` be a positive edge and `u` its endpoint of degree 3, unique because
adjacent vertices differ in degree.  Lemma `(P)` of `bridge_lemma.py` says
`deg(u) - bridges_at(u)` is even, so `bridges_at(u)` is odd, hence 1 or 3; it is
not 3, because `a` itself is a non-bridge edge at `u`.  So `u` lies on exactly
one bridge, and therefore on exactly two non-bridge edges.  Send `a` to that
bridge.

Note the qualification: it is *not* true that every degree-3 bridge endpoint
carries two non-bridge edges, since one with `bridges_at = 3` carries none.  The
statement needed, and the one proved, is that a degree-3 vertex **incident with
a non-bridge edge** has exactly one bridge and exactly two non-bridge edges.

Finally, a bridge has two endpoints and by (c) they differ in degree, so at most
one of them has degree 3.  So at most **two** positive edges reach any one
bridge: `P <= 2B`.

*Step 3: the count closes.* Every non-positive edge has `x <= 0`, so

    2 = sum of x <= P*(1/24) + B*(-1/6) <= 2B/24 - B/6 = -B/12 < 0,

a contradiction. And if `B = 0` then `(P)` makes every degree even and at least
4, the vertex side is at most `5/12`, the face side at most `7/12`, every edge
has `x <= 0` and the sum cannot reach 2 either. **So no `X,2`-APG exists under
the weak reading**, bridged or not; in particular any such graph would be
bridgeless, which is (C2).

*How much room there is.* The tether is what carries the argument: treating the
positive edges as free bounds `B` from below and closes nothing.  With the loose
tether `P <= 4B` the total is exactly `0`, which still contradicts `2` but with
no margin; with the sharp `P <= 2B` it is `-B/12`.  The margin also means Step 0
is not needed at full strength: at `s2 >= 7` the per-bridge total is `-1/84`,
still negative.  It does fail at `s2 >= 6`, where the total is `+1/12`, so some
lower bound on the bridge face is indispensable.

## Why it stood

Section 9.1 runs this chain on the *weak* class with degrees `2` and `k`;
Section 3.2 attacks the *strong* `X,Y` class with different machinery
(`(3.9)`-`(3.13)`) that yields only the lower bounds `V >= 25` and `V >= 56` and
never bounds `f`. The two sections were never connected.

## Calibration, and what it does not show

`excluded_weak_two_k` runs the same chain on the class the paper settled: it
excludes exactly `k >= 12`, reproducing `(9.10)`, and does **not** exclude
`k <= 10`, for which the paper exhibits weak `2,k`-APGs (Table 5, Figures 8-9).
That shows the contradiction turns on `d1 >= 3` rather than on an over-count
that would also have killed the small-`k` weak graphs.

It is **not** a certification. A spuriously stronger bound such as
`5/12 - 1/1000` reproduces the same threshold, which
`test_conjecture_10_1.py` gates explicitly so this note cannot drift back into
an overclaim.
"""
from __future__ import annotations

from fractions import Fraction

# Reciprocal budget per edge.  Euler forces the total over all edges to be
# `e + 2`, so a proof needs every edge to contribute at most 1.
EDGE_BUDGET = Fraction(1)

# The two extremes an alternating class can reach: unrestricted (3 and 4), and
# constrained to distinct even values (4 and 6).
UNRESTRICTED = Fraction(1, 3) + Fraction(1, 4)          # = 7/12
EVEN_DISTINCT = Fraction(1, 4) + Fraction(1, 6)         # = 5/12

# Step 0 of the weak-reading argument: wherever a bridge exists, the face
# carrying it has size at least 8, so the larger of the two face sizes does too.
BRIDGE_FACE_MIN = 8

# The most positive edges that can be tethered to one bridge.  Condition (c) of
# Definition 2.1 makes the two ends of a bridge differ in degree, so at most one
# of them has degree 3, and that end carries exactly two non-bridge edges.
POSITIVE_EDGES_PER_BRIDGE = 2

# The bound before that observation: two ends, two non-bridge edges each.  Kept
# because the argument closes with it too, at exactly zero rather than with
# margin, and because a reader may reach for it first.
LOOSE_POSITIVE_EDGES_PER_BRIDGE = 4


def share(a: int, b: int) -> Fraction:
    """One edge's contribution from one side: `1/a + 1/b`."""

    return Fraction(1, a) + Fraction(1, b)


def edge_contribution(degrees: tuple[int, int], sizes: tuple[int, int]) -> Fraction:
    """What one edge contributes to `v + f`."""

    return share(*degrees) + share(*sizes)


def is_impossible(a: int, b: int) -> bool:
    """Does the class with the two values `a < b` force `v + f <= e`?

    Used for both halves: the constrained side is always `(4, 6)` -- distinct
    even values at least 4 -- so the pair `(a, b)` is the unconstrained side.
    """

    return share(a, b) + EVEN_DISTINCT <= EDGE_BUDGET


def surviving_pairs(bound: int = 200) -> list[tuple[int, int]]:
    """Every `3 <= a < b <= bound` the argument fails to exclude.

    Monotonicity of `1/x` makes the answer immediate from the pair `(3, 4)`;
    this enumerates it anyway as a regression on the arithmetic, not because
    there is anything to discover.
    """

    return [
        (a, b)
        for a in range(3, bound)
        for b in range(a + 1, bound + 1)
        if not is_impossible(a, b)
    ]


def tight_pair() -> tuple[int, int]:
    """The unconstrained-side pair at which the budget is met with equality."""

    return next(
        (a, b)
        for a in range(3, 60)
        for b in range(a + 1, 60)
        if share(a, b) + EVEN_DISTINCT == EDGE_BUDGET
    )


def bridge_excess() -> Fraction:
    """Most a bridge can contribute above 1, given `s2 >= BRIDGE_FACE_MIN`.

    Both sides of a bridge carry the same face, so the face term is `2/|F|`.
    """

    return (share(3, 4) + Fraction(2, BRIDGE_FACE_MIN)) - EDGE_BUDGET


def heavy_edge_excess() -> Fraction:
    """Most a non-bridge edge with both ends of degree at least 4 can contribute.

    Degrees are distinct, so `1/4 + 1/5`; face sizes are distinct with the
    larger at least `BRIDGE_FACE_MIN`, so `1/3 + 1/BRIDGE_FACE_MIN`.
    """

    return (share(4, 5) + share(3, BRIDGE_FACE_MIN)) - EDGE_BUDGET


def light_edge_excess() -> Fraction:
    """Most a non-bridge edge with an endpoint of degree 3 can contribute.

    The only class that can be positive, and the whole of the count in Step 2.
    """

    return (share(3, 4) + share(3, BRIDGE_FACE_MIN)) - EDGE_BUDGET


def closing_bound(bridges: int, per_bridge: int = POSITIVE_EDGES_PER_BRIDGE,
                  face_min: int = BRIDGE_FACE_MIN) -> Fraction:
    """Largest total excess available with `bridges` bridges, by Steps 1-3.

    Euler forces the true total to be exactly 2, so any value below 2 refutes
    the configuration.  `per_bridge` and `face_min` are parameters rather than
    constants so that the gates can show where the argument breaks: it survives
    `face_min = 7` and the loose tether `per_bridge = 4`, and fails at
    `face_min = 6` or `per_bridge = 5`.
    """

    if bridges < 1:
        raise ValueError("the bridged branch needs at least one bridge")
    bridge = (share(3, 4) + Fraction(2, face_min)) - EDGE_BUDGET
    light = (share(3, 4) + share(3, face_min)) - EDGE_BUDGET
    return bridges * (per_bridge * light + bridge)


def bridged_case_is_impossible(bridges: int) -> bool:
    """Does the count exclude an `X,2`-APG carrying exactly `bridges` bridges?"""

    return closing_bound(bridges) < Fraction(2)


def bridgeless_case_is_impossible() -> bool:
    """`B = 0`: `(P)` forces even degrees, and the original bound applies."""

    return UNRESTRICTED + EVEN_DISTINCT <= EDGE_BUDGET


def excluded_weak_two_k(k: int) -> bool:
    """The same chain on the paper's weak `2,k` class: must be exactly `k >= 12`."""

    return share(2, k) + EVEN_DISTINCT <= EDGE_BUDGET


def report() -> dict[str, object]:
    return {
        "edge_budget": EDGE_BUDGET,
        "unrestricted_side": UNRESTRICTED,
        "even_distinct_side": EVEN_DISTINCT,
        "surviving_pairs": surviving_pairs(),
        "tight_pair": tight_pair(),
        "weak_two_k_excluded_from": min(k for k in range(3, 200)
                                        if excluded_weak_two_k(k)),
        "bridge_excess": bridge_excess(),
        "heavy_edge_excess": heavy_edge_excess(),
        "light_edge_excess": light_edge_excess(),
        "closing_bound_per_bridge": closing_bound(1),
        "bridged_excluded": all(bridged_case_is_impossible(b) for b in range(1, 500)),
        "bridgeless_excluded": bridgeless_case_is_impossible(),
    }


def main() -> int:
    for key, value in report().items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
