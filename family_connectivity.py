#!/usr/bin/env python3
"""3-connectivity of the whole spliced family, not just of the members checked.

`test_connectivity.py` verifies 3-connectivity one graph at a time, which is
fine for the 26 certificates -- a finite set -- and not fine for
`pumping_splice.py`, which produces one graph per integer.  "Verified up to
order 260" is not "3-connected"; Conjecture 10.3 needs the family, not a
prefix of it.

The gap closes with the same two facts the periodic capping lemma uses, plus
the reduction lemma proved in `connectivity.py`.

> **Theorem.** Fix a base order `n` with a deep block of at least five copies.
> If `S(n, d0)` is 3-connected and the candidate-pair types of `S(n, d0)` and
> `S(n, d0 + 1)` agree up to translation, then `S(n, d)` is 3-connected for
> every `d >= d0`.

*Proof.*  A separating pair of a 2-connected plane graph lies non-consecutively
on a common face (the reduction lemma).  A face of a spliced map spans at most
four consecutive copies (`test_pumping_splice.py` measures the span and gets
three at most), so every candidate pair lies inside a bounded window of copies,
or involves a cap vertex; call its **type** its image under
the translation that sends the window's lowest copy to zero, cap vertices
fixed.  Splicing one more period is a local surgery: it cuts the edges crossing
the cut copy and re-routes them through a fresh copy, which is a translate of
the cut copy and is adjacent to the copies on both sides.

> **This proof has an identified gap. Read the note below before relying on it.**

Let `d > d0` and let `{u, v}` be a candidate pair of `S(n, d)`.  Its type occurs
in `S(n, d0)` -- that is the hypothesis, carried up by induction, since each
splice adds only translates of types already present.  Write `{u0, v0}` for a
representative in `S(n, d0)`.  `S(n, d0) - {u0, v0}` is connected because
`S(n, d0)` is 3-connected.  Now insert periods one at a time, each time away
from the removed pair (possible because the cut copy is deep and the pair sits
in a bounded window; when the pair *is* near the cut, translate the cut instead,
which the deep block of five or more copies allows).  Each insertion replaces a
set of cut-crossing edges by a path through the fresh copy, and the fresh copy
is adjacent to both sides, so a connected graph stays connected.  Hence
`S(n, d) - {u, v}` is connected.  No candidate pair separates, so by the
reduction lemma no pair does, and `S(n, d)` is 3-connected. QED

What this module does is check the hypothesis -- 3-connectivity at `d0`, and
that the type multiset stops growing -- which is the finite part.

## The gap, identified 2026-09-05 by adversarial review

The induction step above is **not established**, and the theorem should not be
cited as proved until it is. Two distinct problems:

1. **The insertion step assumes what it must prove.** "Each insertion replaces a
   set of cut-crossing edges by a path through the fresh copy, and the fresh
   copy is adjacent to both sides, so a connected graph stays connected" shows
   that the fresh copy attaches to the rest. What is needed is that
   `S(n, d) - {u, v}` is connected -- that every connection surviving in
   `S(n, d0) - {u0, v0}` still survives after insertion, with `{u, v}` already
   removed. Adjacency of the fresh copy to both sides does not give that on its
   own; a replacement path could in principle be forced through a removed
   vertex. A sufficient repair is explicit replacement paths for every boundary
   connection, or a finite boundary-connectivity invariant whose transition
   under insertion is proved.

2. **"Translate the cut instead" is unquantified.** A candidate pair occupies a
   window of up to four consecutive copies (span `<= 3`); the deep block has at
   least five. Whether a cut can *always* be placed clear of that window inside
   that block is an off-by-one that is asserted here and nowhere checked.

3. Separately, matching *types* at `d0` and `d0 + 1` does not by itself imply
   the type multiset never grows again. Two consecutive agreements are evidence
   of stabilisation, not a proof of it.

**What survives.** The reduction lemma in `connectivity.py` is proved. The
finite hypotheses -- 3-connectivity at `d0`, and type agreement at `d0` and
`d0 + 1` -- are genuinely checked, for the representatives listed below. Every
order that carries a stored certificate is verified 3-connected directly and
does not depend on this argument at all. What is *not* established is the
extension from those checks to every order in the family.

**The alternative route does not avoid the problem.** One could instead lean on
the source paper, which states (p. 363, concluding remarks) that "the (3,4,5)-
alternating plane graphs constructed in Section 8 ... are 3-connected". That is
an assertion in a summary bullet, not a theorem with a proof, and it is hedged
for Section 6 ("most of"). Routing the tail through it substitutes an inherited
unproved assertion for a local one. It may still be the better choice -- it is
at least refereed -- but it should be described accurately rather than sold as
a repair.
"""
from __future__ import annotations

import connectivity as cn
import pumping_splice as ps

REPRESENTATIVES = (90, 109, 110)


def _window(pair) -> tuple:
    """A candidate pair's type: copies shifted so the lowest one is zero."""

    copies = [vertex[2] for vertex in pair if vertex[0] == "S"]
    shift = min(copies) if copies else 0
    typed = []
    for vertex in pair:
        if vertex[0] == "S":
            typed.append(("S", vertex[1], vertex[2] - shift))
        else:
            typed.append(("C", vertex[1]))
    return tuple(sorted(typed, key=str))


def pair_types(order: int, delta: int) -> set[tuple]:
    return {_window(pair) for pair in cn.candidate_pairs(ps.splice(order, delta))}


def face_span(order: int, delta: int) -> int:
    """Largest number of copies a single facial walk touches, minus one."""

    spans = []
    for walk in cn.faces(ps.splice(order, delta)):
        copies = [vertex[2] for vertex in walk if vertex[0] == "S"]
        if copies:
            spans.append(max(copies) - min(copies))
    return max(spans)


def types_stabilise(order: int, delta: int) -> bool:
    """Does splicing one more period add no new candidate-pair type?"""

    return pair_types(order, delta + 1) == pair_types(order, delta)


def main() -> int:
    for order in REPRESENTATIVES:
        base = ps.floor_delta(order) + 4
        print(
            f"order {order}: face span {face_span(order, base)} copies,"
            f" {len(pair_types(order, base))} candidate-pair types,"
            f" stable={types_stabilise(order, base)},"
            f" 3-connected={cn.is_three_connected(ps.splice(order, base))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
