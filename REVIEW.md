# Independent review, and what it changed

Every substantive claim in this repository was put to independent reviewers
whose instruction was to break it. This file records what that produced. It
names findings rather than reviewers: the author is responsible for the
content either way, and the value here is the list of things that turned out to
be wrong.

Nothing below is decorative. Several claims made in this repository were
**false** and were withdrawn; each is retracted in place at the file that made it, rather
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

## Conjecture 10.3, and the withdrawal of the infinite tail

### Retracted (2026-09-05): "3-connected at every order from 19 up"

The strongest correction this repository has made, and the one that cost a
theorem. `family_connectivity.py` set out an induction carrying 3-connectivity
through the spliced family, and the manuscript stated Conjecture 10.3 itself as
a theorem on the strength of it.

**The induction is not established.** Its key step shows a freshly spliced copy
is adjacent to the copies on either side and concludes that connectivity is
preserved; what is required is that `S(n,d) - {u,v}` is connected, with the
separating pair already removed, and that does not follow -- a replacement path
could be forced through a removed vertex. A second step, that the splice point
can always be placed clear of a pair occupying up to four consecutive copies
inside a deep block of five, is an off-by-one asserted and never checked. A
third, that type agreement at two consecutive sizes implies the type multiset
never grows again, is evidence of stabilisation rather than proof of it.

**What replaced it.** The manuscript's Theorem now states only the 54 orders
carrying explicit witnesses -- 17, 19-56, 67-74, 88-92, 109-110 -- and says
plainly that Conjecture 10.3 is not proved. Orders 57-66, 75-87, 93-108 and
every `n >= 111` are open pending proof.

**The obvious alternative does not repair it.** The source paper states in its
concluding remarks that its Section-8 constructions are 3-connected, which would
cover exactly those gaps. That is an assertion in a summary bullet rather than a
theorem, and the same sentence hedges Section 6 with "most of". Routing the tail
through it substitutes an inherited unproved claim for a local one.

Found by an adversarial review pass whose brief was to attack the deposit. It
was listed in that brief as *not* a known weakness; the review found it anyway.

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

## Two professor legs on Conjecture 10.1, 2026-09-08

Two independent Extra High reviews of §2–§5, dispatched with the same source and
opposite stances: one told to assume the proof is wrong and find where, one told
to assume it sound and say what a referee would still refuse to sign off on.
Both verified against the live conversation (`chatgpt verify`, exit 0);
`tierAtSend = Extra High` recorded for each.

**Neither could break the proof.** Leg A: *"I would regard this as a correct
proof of Conjecture 10.1, subject to correcting the two statements above."* Leg
B: *"minor revision rather than rejection ... after those corrections I would
accept the paper as a correct proof."* Neither could exhibit a `2,Y`- or
`X,2`-alternating plane graph, and neither found a defect in the strict-reading
argument or in the `P <= 2B` tether.

They converged, independently, on the same weakest point, and on two further
false statements. All three are corrected in the manuscript.

1. **Step 0's justification was false as written.** It read: *"A simple
   connected plane graph on at least three vertices has every facial walk of
   length at least 3: a walk of length 2 requires parallel edges and one of
   length 1 a loop."* A facial walk of length 2 can also be **a single bridge
   traversed twice** -- `K2` is the example -- and that case was never disposed
   of. The conclusion survives: for those two darts alone to form a facial
   orbit, both endpoints have degree 1, forcing the component to be `K2`, which
   `deg_A(u) >= 2` excludes. But the stated reason did not cover it, and Step 0
   feeds every numerical estimate in the bridge argument. Now written out.
   Both legs named this as **the** weakest point.
2. **The Eulerian remark was false.** It claimed the parity lemma is *"the
   classical fact that a plane graph is face 2-colourable if and only if it is
   Eulerian, restated so that bridges are permitted"*. Leg B's counterexample: a
   triangle with a pendant edge has its two faces properly coloured once
   self-adjacency across the bridge is ignored, and is not Eulerian. The lemma is
   strictly weaker than the classical criterion, not a restatement of it. It was
   commentary, used nowhere, and is now stated correctly.
3. **Convention (C1) contained a false "if and only if".** It said a facial walk
   repeats a vertex *"if and only if the graph is not 2-connected"*. That is a
   statement about a single face and is wrong: two triangles sharing a cut vertex
   have two faces repeating nothing and an outer face that repeats. The true
   statement quantifies over all faces.

Also adopted from both legs: *"the outer walk of $A$"* is replaced by *"the
facial boundary walk of $A$ incident with the corner formerly occupied by $a$"*,
since in a fixed embedding that face need not be the unbounded one.

**What did not change.** Both legs confirmed (C1) is the only theorem-level
external vulnerability, and neither found new reason to doubt it. Leg A noted
independently that the paper's own Lemma 9.2 proof -- *"since the graph is
bipartite, all f_j for j odd are 0"* -- is false under a distinct-vertices
reading, which is further evidence for (C1) rather than against it.

### Exposition audit, 2026-09-08

A third pass, on readability rather than correctness, framed around Terence
Tao's observation that machine-assisted proofs tend to be *disproportioned*:
routine steps get lavish text because they are easy to write about, and the hard
step gets a sentence because the writer already believes it. The Step 0 error
above is exactly that shape -- a clause each for the loop and the parallel-edge
case, and **no words at all** for the bridge traversed twice.

Both follow-up reviews first confirmed the three corrections land, and that
apart from (C1) their acceptance is now unconditional. On (C1) they agreed,
independently, that **contacting the original authors is not a prerequisite to
submission**: the source paper's own mathematics operationally fixes the
meaning, and the documentation should be phrased as *"the convention required
by, and used in, (3.1), (9.2) and the proof of Lemma 9.2"* rather than as a
claim about intention. This corrects the position taken in this repository
earlier, that (C1) put author correspondence on the critical path.

Acted on, in the manuscript:

* **A symbol collision.** `B` was the number of bridges, and Step 0 then wrote
  `|F| = |dA| + |dB| + 2` using `B` for a component. Not a mathematical gap, but
  it stops a referee mid-read. The components are now `A` and `C`, with the
  boundary walks named `W_A`, `W_C`.
* **The charging map was hidden in a "Hence".** `P <= 2B` is the substantive
  step of the bridge argument and got less text than the calibration remark.
  Now written out: every positive edge has a unique degree-3 end, parity gives
  that end a unique bridge, the charge is therefore well defined, and a bridge
  has at most one degree-3 end with exactly two non-bridge edges at it.
* **A roadmap before the weak-reading proof.** By Step 3 the reader was holding
  seven facts at once. One paragraph now states the architecture first.
* **(C1) spent its space on the wrong thing** -- five lines on a 2-connectivity
  tangent, one clause on the documentary basis the proof actually rests on. The
  proportions are reversed, and the Lemma 9.2 evidence is now stated where a
  referee needs it.
* **Step 3 names its partition** instead of leaving the reader to infer it.

To pay for it: the calibration subsection and the disconnectedness remark are
compressed, and the sentence recording the withdrawn leaf-block draft is cut
from the paper -- it belongs here, not in a publication.

Not adopted: cutting Theorem 3.2 and the rotation-systems subsection, both
suggested as unused. They are unused *in the excerpt reviewed* and load-bearing
elsewhere in the paper.
