# Independent review, and what it changed

Every substantive claim in this repository was put to independent reviewers
whose instruction was to break it. This file records what that produced. It
names findings rather than reviewers: the author is responsible for the
content either way, and the value here is the list of things that turned out to
be wrong.

Nothing below is decorative. Three claims made in this repository were **false**
and were withdrawn; each is retracted in place at the file that made it, rather
than quietly deleted.

## Conjecture 10.1, and the removal of (C2)

The proof originally held only under (C2) — that no edge has the same face on
both sides — which is the source paper's reading of Definition 2.1 at a bridge
rather than a hypothesis written into it. Review closed that gap, and closed it
more strongly than the question asked: under the weak reading there is no
`X,2`-APG at all, bridged or not, so a counterexample would be bridgeless
whichever way the definition is read. The argument is in
[`conjecture_10_1.py`](conjecture_10_1.py) under "Removing the dependence on
(C2)" and in §5 of the manuscript.

### Retracted: "half one has no such dependence"

An earlier version of [`CONJECTURE_10_1.md`](CONJECTURE_10_1.md) claimed half one
did not depend on (C2). **False**: half one derives through `(9.5)` too, where an
edge is weighted by `1/r + 1/s` for two *distinct* faces and a bridge would
contribute `2/r <= 1/2 > 5/12`. What distinguishes half one is that its
*conclusion* survives (C2) failing, by a leaf-block argument.

### Retracted: each side of a bridge has at least five vertices

[`bridge_lemma.py`](bridge_lemma.py) argued that every vertex of a bridge's side
other than the endpoint "has all its edges inside `A`, hence even degree at least
four". **A non sequitur**: a side may contain further bridges, and the parity
lemma permits odd degree at their endpoints. Nothing depended on it — Step 0 of
the closing argument supplies the bound it existed for, independently — and the
retraction is recorded in that module.

### Retracted: "the count is exactly tight"

The closing count was stated with the tether `P <= 4B`. Definition 2.1(c) makes
a bridge's two ends differ in degree, so at most one can be the degree-3 vertex
a positive edge needs: the true tether is `P <= 2B`. Both bounds close, so the
proof was never wrong — but the claim of exact tightness was, since it asserted
tightness of a bound no configuration attains.

### Sharpened: positive edges are `3-4` edges

A positive edge has face side at most `11/24`, so its vertex side must exceed
`13/24`, and among pairs of distinct degrees at least 3 only `1/3 + 1/4` clears
it. Now stated in Step 1.

### Corrected: degree-3 endpoints

"Each degree-3 bridge endpoint carries two non-bridge edges" is false
unqualified — one with three bridges carries none. The statement needed, and
proved, is that a degree-3 vertex **incident with a non-bridge edge** has
exactly one bridge and exactly two non-bridge edges.

## What was probed and held

An adversarial pass attacked six points and broke none: the Step 0 face
decomposition under cut vertices, nested bridges and mirrored embeddings
(reported as checked on 7736 bridges across 3000 randomly built maps, with the
decomposition exact every time and the bound of 8 attained; that sweep was the
reviewer's own and is **not** reproduced in this repository, so it is reported
here as testimony rather than as a gate); exhaustiveness and
disjointness of the Step 1 case split; whether two bridges can receive the same
positive edge; the direction of the Step 3 inequality and its behaviour under
disconnection; the parity lemma at a vertex all of whose edges are bridges; and
whether any step secretly re-assumes (C2). No reviewer could construct a bridged
`X,2`-APG.

With the sharp tether the count closes at `s2 >= 7` (`-1/84` per bridge), so
Step 0's bound of 8 is not needed at full strength; it fails at `s2 >= 6`
(`+1/12`), so some bound on the bridge face is indispensable. Both are gated.

## Elsewhere

* **`fast_apg_check.is_apg` never checked `{3,4,5}` membership.** It relied only
  on the profile identity `sorted(sizes) == sorted(degrees)` of Theorem 3.2, so
  it accepted graphs with a degree-6 vertex and a 6-face. Found by review, fixed,
  and regression-gated.
* **"Every `(3,4,5)`-APG is 3-connected" was false.** Review produced a
  counterexample on 46 vertices with a separating pair; it is verified here and
  stored in `certificates/counterexamples/`. See
  [`THREE_CONNECTIVITY_CLAIM.md`](THREE_CONNECTIVITY_CLAIM.md).

Review transcripts are not part of this package.
