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

## Pro-tier breadth review, 2026-09-08

One pass at ChatGPT Pro (`tierAtSend = Pro`, verified), given the full
manuscript, this file, the reviewer guide and both files carrying the infinite
claims, and asked to cover every angle at once so that later rounds are not
needed. It consulted the source paper and the published v1.0.4 code externally.
Its verdict: **do not submit the whole manuscript in its present form**;
Conjecture 10.1 is sound and separable, and should go alone.

Everything below was reproduced here before being acted on.

### The finding that matters: a gate computed from the wrong predicate

`test_conjecture_coverage.py` derived the capping theorem's insertion reach from
`test_pumping_splice.SPLICEABLE`. The theorem's hypothesis is a **deep block of
at least five copies**, which is not what `SPLICEABLE` means. Measured:

| order | 48 | 51 | 53 | 54 | 56 |
| --- | --- | --- | --- | --- | --- |
| deep copies | 1 | 2 | 2 | 3 | 3 |

Five of the twenty spliceable orders are not eligible seeds at all. With the
hypothesis applied, the eligible seeds start at 67, 68, 69 and insertion reaches
nothing below 70, so **all ten orders 57-66 lie outside the theorem** and none
carries a stored certificate. They rest on the verified floor-upwards splices.

This is the second time this set has been named wrongly. The first version said
`57, 58, 59, 61, 63`; the correction said `58, 61, 64` and was justified on the
grounds that it was *computed rather than asserted*. It was -- from the wrong
eligibility test. **Deriving a number does not make it right if the predicate is
wrong**, and that is now the gate's own docstring.

### Availability counted as verification, again

`witness_coverage.section8_orders()` returned `set(section8_witnesses.RECIPES)`
-- the recipe *keys*. Breaking the builder would not have removed an order from
a set named `verified_orders()`. It now constructs each closure, runs it through
the general APG check and the 3-connectivity check, and returns only what
survives (cached, since it is called throughout the suite). Separately,
`witness_coverage.main()` still printed the withdrawn `residue()` as its
headline; it now prints `verified_residue()` and labels the other.

### Three mathematical scope errors

* **The per-edge identity was stated for an unrestricted plane graph and is
  false with isolated vertices** -- a triangle plus an isolated vertex gives
  `sum c(a) = 5` against `v + f = 6`, and `K1` gives `0` against `2`. Minimum
  degree 3 excludes both, so Conjecture 10.1 is untouched, but the lemma's
  stated generality was wrong. Hypothesis added.
* **"(C2) is a consequence of Definition 2.1" is false read generally.** The
  review supplied a construction: join three copies of a (3,4,5)-APG by two
  exterior bridges at a degree-5 vertex of each; degrees become 7, 6, 6, the
  merged exterior face has size at least 13 and differs from every interior
  face. That is a weak-reading APG *with bridges*. It has neither exactly two
  degrees nor exactly two face sizes, so the theorem stands -- but the
  commentary claimed more than the theorem. Scope now stated.
* **Orders 37 and 38 were misattributed.** They are out of reach of the
  Section-8 *arithmetic*, but `\cite{AHSSV2015}`'s heuristic search covers every
  order from 20 to 42, including these. The paper slid from the narrow fact to
  "skipped by the coverage list". Corrected in both places it appeared.

### Cross-document drift, again

* The **main manuscript's abstract still said "We settle three"** -- the BAMS
  variant had been fixed on 2026-09-06 and the primary file had not. The exact
  inverse of the drift caught two days earlier, in the other direction.
* The bibliography named artifact version 1.0.2 while the data-availability
  paragraph named 1.0.4.
* `PUMPING_LEMMA_STATUS.md` still grounded locality in spans measured on the
  splices -- the circular argument the manuscript had already replaced -- and
  still said two finite facts where the manuscript says three. Now headed with a
  superseding note.
* "Each certificate is accepted by every verifier" cannot be literal: the three
  (3,4,5) procedures correctly reject the order-19 general APGs. Narrowed.
* `FOR_REVIEWERS.md` said nothing had been checked by a human while the
  manuscript said the author verified the mathematics. Now: no independent human
  specialist has checked it.
* `FOR_REVIEWERS.md` called the infinite claims "not machine-checkable in
  principle". False -- a formal proof or a finite-state invariant could do it.
  What is true is that nothing here does.

### Not yet acted on

* **The insertion proof's window claim is still not fully discharged.** With
  `d = 1` the guaranteed periodic band is `[cut-2, cut+3]`, but the five-copy
  window `[cut+1, cut+5]` meets the fresh block and leaves it. Span four is also
  not radius two about an arbitrary starting dart. A rigorous proof must pick
  the counterpart dart and a region containing its whole trace.
* **The deletion statement and the implementation disagree.** The theorem takes
  an interior cut at distance >= 2 from both ends of `D`; the implementation
  deletes copies immediately above the cut and defaults to the first deep copy
  for negative `d`. Those are different operations. Insertion and deletion need
  separate statements.
* Three further obligations compressed into the word "local": faces routed
  through caps have no copy index; transferring individual faces does not
  transfer the *pair* incident to an edge, which is what face alternation needs;
  and "every face is a translated face" does not count the face orbits.
* The root `LICENSE` is a plain MIT notice with no carve-out, while the
  manuscript says MIT is not asserted over the re-expressed graphs. A path-level
  rights statement is wanted.

### The blind spot, stated by the reviewer

> *"The central blind spot is an internally consistent package built against the
> wrong external specification or an incomplete account of prior work... No
> further analysis restricted to these files can distinguish those situations.
> Agreement among prose, tests and generated metadata may simply mean that all
> three inherited the same assumption."*

Three distinct assurance tasks, not substitutable: a literature-aware
mathematician checks whether the statement is the intended problem and whether
the proof is new; an independent implementation checks whether the deposited
objects satisfy the statement; a release check binds both to the archived bytes.
Only the second is being done here, and only from one architecture.

## 2026-09-09 — Pro readability review of `paper/apg101.tex`

Model: ChatGPT Pro (`tierAtSend=Pro`, `modeAtSend=chat`), SID
`5ee89859-6931-4464-aa34-b362acce4b02`, verified against the live conversation.
Prompt: the three-layer exposition standard from `SeverinVisionary/imo-gold`
`RESEARCH_GUIDELINES.md` (§7 layered exposition, §8 teach-back, §6 evidence
boundaries), asking for (a) a checkable readability rubric with pass thresholds
and (b) every improvement in one pass. Full text archived at
[`submission/REVIEW_2026-09-09_readability_pro.md`](submission/REVIEW_2026-09-09_readability_pro.md).

**Verdict on correctness: no gap found.** The bridge-face estimate, the parity
argument, the assignment of positive edges to bridges, and the final inequality
all survived. The two essential qualifications — "incident with a non-bridge
edge", and "at most one degree-3 endpoint of a bridge" — were confirmed as
essential and correctly handled.

**Verdict on the disproportion worry: not the problem here.** Measured prose
counts put Step 2, the genuine bottleneck, at 250 of the 526 words of the
bridge proof (48%). The disproportion was elsewhere: the preliminaries were
longer than the entire main theorem section, and much of that space was
interpretative defence rather than orientation.

All 37 items were executed except the release test, which is a human
teach-back and cannot be closed by a model. The substantive changes are listed
in [`paper/README_note.md`](paper/README_note.md).

Two of the items were errors of source attribution, and both were checked
directly against the article PDF rather than taken on the reviewer's word:
(9.5) is the face bound `f <= 5e/12` (the `1/2` is in (9.8)); (9.2) is
`r*f_r = sum_s e_{r,s}`. The prior-art paragraph now also names the two
surviving degree pairs, {3,4} with order >= 25 and {3,5} with order >= 56,
which the source establishes in its §3.2 for the 2,Y case only.

## 2026-09-09 — Pro confirmation pass on the submission package

Model: ChatGPT Pro (`tierAtSend=Pro`), SID `8e8c5530-e15f-411c-b038-f0c4d353ff30`,
verified. Inputs: the revised `apg101.tex`, `COVER_LETTER.md`, `CHECKLIST.md`.
Full text at
[`submission/REVIEW_2026-09-09_package_pro.md`](submission/REVIEW_2026-09-09_package_pro.md).

**Verdict: NO-GO as it stood, GO after a correction pass.** No proof-level
reason to postpone. It re-derived and confirmed the four newly restructured
pieces independently: the nine-vertex example's counts and its `f = 5e/12`
sharpness, the promoted bridge-face lemma (noting the components in fact have
minimum degree 2, stronger than the 1 the proof needs), the claim that a
bridgeless bridge-relaxed graph satisfies Definition 2.1 outright, and the
three-copy construction.

Three explanatory errors it caught, all now fixed:

* The pendant-triangle example said "although no vertex has even degree" — the
  degrees are 3,2,2,1, so two of them are even. Now "not every vertex".
* The sentence introducing the parity lemma claimed corners of one face at a
  vertex are non-consecutive. Across a bridge they are consecutive; that is
  precisely the case the lemma exists to handle. Rewritten.
* The roadmap called both conventions ones "the source paper leaves implicit",
  contradicting the paper's own correct statement that the source explicitly
  excludes bridges.

Cover letter: "never uses the hypothesis it is stated under" was too sweeping —
the source's estimate does use bipartiteness and face alternation, just not the
degree 2. Narrowed. The categorical "I confirm this satisfies the Bulletin's
requirement" was removed; the disclosure now names the systems and the period of
use, per Cambridge's guidance, rather than asserting compliance. The defensive
"not a weakness" passage and the invitation to rule on prior art were cut.

Checklist: submission-system metadata (ORCID, keywords, MSC) and the form's
attestations were missing, since the checklist had only covered manuscript
format. Added.

Still open and not closable by any model: the human teach-back, and the author's
own confirmation of the printed sentence "The author re-derived every argument
independently."

**Version note.** This pass reviewed the 8-page text. The figures, tables and
expanded bibliography were added afterwards and have not been reviewed.
