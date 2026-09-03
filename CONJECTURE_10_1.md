# Conjecture 10.1 — a proof, from the paper's own inequality

> **Conjecture 10.1** (Althofer, Haugland, Scherer, Schneider, Van Cleemput,
> *Ars Math. Contemp.* **8** (2015) 337–363, p. 362.)
> There are no `2,Y`-alternating plane graphs and no `X,2`-alternating plane
> graphs.

An `X,Y`-alternating plane graph (Definition 3.4, p. 341) is an APG with
**exactly `X` distinct vertex degrees and exactly `Y` distinct face sizes**. So
the conjecture says: no APG has only two distinct degrees, and none has only two
distinct face sizes.

The argument, both halves, is in the module docstring of
[`conjecture_10_1.py`](conjecture_10_1.py) and gated by
[`test_conjecture_10_1.py`](test_conjecture_10_1.py). In one line each:

* **`X = 2`.** Two degrees plus vertex alternation makes `G` bipartite, so every
  face is even and hence at least 4; the paper's own `(9.5)` then gives
  `f <= 5e/12`, while `v = (1/d1 + 1/d2)e <= 7e/12`. So `v + f <= e`, against
  Euler's `v + f = e + 2`.
* **`X,2`.** Dually: two face sizes plus face alternation makes every vertex
  degree even, hence at least 4; degree-4 vertices are independent, so
  `v <= 5e/12`, while `f = (1/s1 + 1/s2)e <= 7e/12`. Same contradiction.

## This is the paper's own machinery

Lemma 9.2 (pp. 357–358) proves no *weak* APG has degrees `2` and `k` for
`k >= 12`, and its engine `(9.3)`–`(9.5)` is exactly the face bound above:
every edge lies between an `r`-face and an `s`-face with `4 <= r < s`, so
`f = sum over edges of (1/r + 1/s) <= (1/4 + 1/6)e`. **That derivation never
used the degree 2.** It needs only bipartiteness, faces of size at least 3, and
adjacent faces of unequal size — all of which a strong APG with two degrees has.
Half one is Lemma 9.2 with `1/2` replaced by `1/d1 <= 1/3`, where the inequality
is no longer tight.

Why the conjecture stood: Section 9.1 runs this chain on the *weak* class with
degrees `2` and `k`, while Section 3.2 attacks the *strong* `X,Y` class with
different machinery (`(3.9)`–`(3.13)`) that yields only the lower bounds
`V >= 25` and `V >= 56` and never bounds `f`. The two sections were never
connected.

## Calibration, and the weakest step

The chain is run against a result the paper *proves*: on the weak `2,k` class it
must exclude exactly `k >= 12`, reproducing Lemma 9.2, and must **not** exclude
`k <= 10`, where the paper exhibits weak `2,k`-APGs (Table 5, Figures 8–9). It
does both. Any over-counting step would have failed that test. `k = 11` is left
open by the chain, exactly as in the paper, which needs Lemma 9.4 for it.

Both halves *derive* through (C2) — that no edge has the same face on both
sides — and both **conclusions survive its failure**, so the theorem does not
depend on how Definition 2.1 is read at a bridge. Half one by a leaf-block
argument. Half two, since 2026-09-02, by a counting argument that costs a
hypothetical bridged `X,2`-APG exactly as much as it gains: see "Removing the
dependence on (C2)" in [`conjecture_10_1.py`](conjecture_10_1.py). The
parity lemma it turns on is in [`bridge_lemma.py`](bridge_lemma.py).

## Status

**Reviewed by five independent reviewers on 2026-09-02**, each given the same
brief and told to break it. All five returned sound, none raised a critical or
high finding, and none could construct a `2,Y`- or `X,2`-alternating plane
graph.

They did catch a real error in the write-up, and agreed on it: the claim that
half one did not depend on the no-bridge reading was **false**. They also
supplied the restructuring this file now uses — both halves as a single
symmetric per-edge inequality — and replaced an `n4` counting detour with the
genuine dual identity. What review changed, in full: [`REVIEW.md`](REVIEW.md).
Transcripts are not part of this package.

### The weakest point, since closed

Every reviewer named the same weakest point: **(C2)**, that no edge has
the same face on both sides, was the paper's reading of Definition 2.1 (p. 339)
rather than a hypothesis written into it, and half two had no argument that
survived its failure.

**It now does** (2026-09-02). Under the weak reading, a hypothetical `X,2`-APG
with `B >= 1` bridges is refuted by a count: the face carrying a bridge has size
at least 8, which drops every edge below the per-edge budget except those at a
degree-3 vertex; the parity lemma forces such a vertex onto exactly one bridge,
and since a bridge's two ends differ in degree only one of them can be that
vertex, tethering at most two positive edges per bridge. The total excess is
then at most `-B/12`, where Euler demands exactly 2. With `B = 0` the parity
lemma makes every degree even and the original bound applies. So **no `X,2`-APG exists under either
reading**, and in particular any would be bridgeless — which is (C2).

Found in independent review, which also retracted a step of ours: the earlier
claim that each side of a bridge has at least five
vertices was a non sequitur, since a side may contain further bridges and parity
permits odd degree at their endpoints. Nothing needed it. Gated in
[`test_conjecture_10_1.py`](test_conjecture_10_1.py), including controls that
the count fails if the tether is loosened to five positive edges per bridge, and
that it survives a bridge-face bound of 7 but fails at 6 -- so the bound matters
but not at full strength.
