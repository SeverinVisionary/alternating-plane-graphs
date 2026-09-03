# "Every `(3,4,5)`-APG is 3-connected" — **false**, refuted at order 46

> **Claim (refuted 2026-09-01).** Every `(3,4,5)`-APG is 3-connected.

Had it been true, Conjecture 10.2 — settled — would have given Conjecture 10.3
for every `n >= 20` at a stroke, leaving only `n = 19`. It is not true. The
counterexample is
[`certificates/counterexamples/APG46_two_cut.json`](certificates/counterexamples/APG46_two_cut.json):
a `(3,4,5)`-alternating plane graph on 46 vertices whose vertex set has a
separating pair.

| | |
| --- | --- |
| order | 46; edges 90, faces 46, `v3=f3=18`, `v4=f4=14`, `v5=f5=14` |
| separating pair | `{1, 2}` — **non-adjacent**, both of degree 5 |
| components of `G - {1,2}` | two, of 22 vertices each |
| neighbour split | vertex 1: 3 and 2; vertex 2: 2 and 3 |
| faces carrying both | the pentagons `1,3,2,7,6` and `1,8,2,5,4` |

Verified in this repository independently of the search that produced it and of
the reviewer that ran it: `verify.py` and `verify_darts.py` both PASS at order 46,
`fast_apg_check` accepts, `connectivity.is_three_connected` is false by brute
force over all pairs, and `separating_pairs_on_faces` returns exactly
`[(1, 2)]`. Gated in [`test_connectivity.py`](test_connectivity.py).

It is **not isomorphic to `TARGET_46`**, which is 3-connected, so it is also a
second independent `(3,4,5)`-APG at that order.

## The partial proof was not wrong — the counterexample lands in its gap

Everything proved before the refutation still holds, and the counterexample
lands precisely where the argument stopped.

**Step 0.** A `(3,4,5)`-APG is 2-connected: every facial walk is a simple cycle,
and a cut vertex appears twice on some facial walk.

**Step 1 (reduction lemma, still true; implemented in
[`connectivity.py`](connectivity.py)).** In a 2-connected plane graph, a
separating pair lies non-consecutively on a common face. The counterexample
obeys it exactly: two pentagons carry `1` and `2`, each non-consecutively.

**Case A (still true).** If `u` and `v` each have exactly **one** neighbour in
the component, the two face-arcs coincide and force a degree-2 vertex.

**Case B (still true).** If both arcs have length two and `u`, `v` each have
exactly **two** neighbours in the component, either a face gives a degree-2
vertex or a strictly smaller separating pair contradicts minimality.

**The gap, and what fills it.** The open case was "`u` or `v` has three or more
neighbours inside the disk", where minimality stops producing a smaller cut.
The counterexample has splits `3+2` and `2+3` — so it is in that case and in
neither A nor B. The gap was real, not an artefact of how the argument was
written.

## Why the search evidence was misleading

Forty-nine `(3,4,5)`-APGs had been checked by brute force with no exception, and
a sweep over **every single two-edge switch of all 26 certificates** found zero
switches leaving a valid `(3,4,5)`-APG. That second fact is what made the first
one worthless: the one-switch neighbourhood of the class is empty, so a
perturbation search cannot reach a counterexample no matter how long it runs,
and its silence is a statement about rigidity, not about connectivity. The
counterexample was found instead by a **disk-filling patch search**, which
builds the two sides of a 2-cut interface directly rather than perturbing a
known graph.

## What this costs, and what it does not

It closes the route "one lemma, then 10.3 for every `n >= 20`". It costs
Conjecture 10.3 **nothing else**: every witness this repository counts was
checked individually, so the residue — `19, 37, 38` — was unchanged **at the time this was written**. All three have since closed and the residue is now empty; see [`CONJECTURE_10_3.md`](CONJECTURE_10_3.md) and
[`CONJECTURE_10_3.md`](CONJECTURE_10_3.md).

It also promotes [`family_connectivity.py`](family_connectivity.py) from a
tidiness argument to a necessary one. That module proves the spliced family is
3-connected at *every* order it produces. With the general claim false, that
theorem is the only thing standing between "48 and every `n >= 50`" and a
per-order spot check — and it is unaffected, because it argues from the family's
own periodic structure rather than from the class.

## An unverified claim, recorded as the reviewer's

An independent reviewer that produced the counterexample reports that **46 is the
smallest order** admitting a non-3-connected `(3,4,5)`-APG, from an exhaustive
version of its patch search: 684 labelled interfaces for `k = 2` with `uv` not
an edge, of which 616 are refuted with no size cap binding, and no feasible side
at all for `uv` an edge with up to 20 interior vertices. That is **not verified
here**. It depends on the completeness of an enumeration validated empirically —
by refilling faces of the order-17 graphs and recovering them — rather than
proved. Treat it as a lead, not a result.
