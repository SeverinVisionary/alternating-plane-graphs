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
