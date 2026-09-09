# `apg101.tex` — the standalone Conjecture 10.1 note

**This is the submission.** Ten pages, AustMS `baustms` class, for the
Bulletin of the Australian Mathematical Society.

## Why it exists

The combined manuscript (`apg.tex`) settles two conjectures and advances a
third across fourteen pages. Two adversarial reviews and a Pro-tier breadth
review all landed on the same recommendation: **send Conjecture 10.1 alone.**

The reasons are worth keeping, because they will still be true next time:

* It is the one result here that is a **theorem** rather than a finite
  verification, and it is completely separable — no certificate, no
  construction, no artifact is used in its proof.
* The combined paper carries an unfinished construction. Theorem
  `thm:pumping`'s deletion direction disagrees with the implementation's cut
  rule, and its insertion window claim is not fully discharged (`REVIEW.md`,
  "Not yet acted on"). A referee meeting that first may never give the sound
  argument the attention it deserves.
* The Bulletin wants papers *"relatively short"* and *"in publishable form,
  without revision"*. Seven pages of one argument fits that; fourteen pages of
  three results with an open remark does not.

## What was removed, and what that cost

Removed: the periodic capping lemma, both Conjecture 10.2 and 10.3, the
withdrawn-induction narrative, the density discussion, the artifact section,
Theorem 3.2, and the rotation-systems subsection. **Nothing the proof uses was
removed** — checked by building with no undefined references or citations.

Kept in full: Definition 2.1 and the `X,Y` class, both conventions, the per-edge
identity, both halves of the proof, and all of \S5, now stated as the
bridge-relaxed extension rather than as the removal of a dependence.

## The 2026-09-09 exposition revision

A Pro-tier professor leg (`chatgpt`, `tierAtSend=Pro`, SID
`5ee89859-6931-4464-aa34-b362acce4b02`, verified) reviewed the note against the
three-layer exposition standard of `imo-gold`'s `RESEARCH_GUIDELINES.md` and
returned a rubric plus 37 itemised changes. It found **no gap in either proof**.
What it did find, and what was fixed:

* Two source correspondences were wrong. (9.5) of the source is the face bound
  `f <= 5e/12` and contains no `1/2` to replace; the degree-2 contribution is in
  (9.8)–(9.9). (9.2) is `r*f_r = sum_s e_{r,s}`, not the global `sum_s s f_s =
  2e` the note attributed to it. Both verified directly against the article PDF.
* The abstract's "unconditional / holds either way" read as independence from
  the *definition of face size*, which is not what is proved: boundary-walk
  length is fixed throughout, and what varies is whether face alternation
  includes self-adjacency across a bridge. Rewritten.
* "Alternation caps every edge at one" is false without the two-valued
  hypothesis and the parity it supplies. Rewritten.
* The old remark claimed that treating positive edges as unconstrained "gives
  only a lower bound on B". The inequality runs the other way; it gives no
  bound at all without a relation between P and B. Removed.
* The identity lemma was stated for graphs it did not need and did not survive
  (the empty graph gives 0 = v+f = 1; disconnected graphs need a different
  boundary convention). Restricted to connected, simple, at least one edge.
* The calibration paragraph's "So the contradiction turns on d1 >= 3 and not on
  an over-count" was disclaimed by its own next paragraph. Replaced by a worked
  9-vertex example that **attains** `f = 5e/12`, which does rule out a stronger
  coefficient.
* Two relaxations were both called "weak": the source's (degree 2 allowed) and
  ours (bridges allowed). Ours is now "bridge-relaxed" throughout.
* The unused exact 3–4 classification in Step 2, the parameter-sensitivity
  remark, the duplicated rotation argument, the duplicated historical remark,
  the disconnectedness aside, and the re-proved bridgeless case were deleted.
  The parity lemma was promoted into \S3 and the bridge-face bound into a
  lemma of \S5 stating the conclusion actually used (every bridge's face has
  length at least 8, not merely `s2 >= 8`).
* The AI disclosure moved from \S1 to endmatter and a separate computational
  support statement was added, saying plainly that the proofs depend on no
  computation and that the repository's checks are advisory.

## Figures, tables and references (2026-09-09)

The note previously carried one reference and no picture, which is not what a
paper in this area looks like. The source paper itself cites nine items, and the
counting tradition this argument sits in is well documented, so the sparse
bibliography was an artifact of drafting, not of the subject.

Added, each with a sentence in the text that actually uses it: Lebesgue (1940)
and Kotzig (1955) as the classical Euler-formula charge arguments; Cranston and
West (2017) for discharging, whose vocabulary the note now borrows explicitly
("initial charge with total 2 and no discharging rule"); Jendrol' and Voss (2013)
for the light-configuration literature; Mohar and Thomassen (2001) for the facial
walk convention behind Convention 2.3; Brinkmann and McKay (2007) for the
`plantri` generation behind the source's exhaustive search. All six were verified
against primary records, not cited from memory. Note that the source paper's own
citation of Brinkmann-McKay gives volume 42(4), 909-924; the article is in volume
58, 323-357.

Added five TikZ figures and two tables: the cut-vertex illustration of the
face-size convention; the nine-vertex worked example; the corners-in-rotation
diagram that makes the parity lemma readable; the bridge splice
`|F| = |W_A| + |W_C| + 2`; the three-copy bridged construction; a table of the
two cases of Theorem 4.1 side by side; and a table of the three-case local
estimate in Step 1. Ten pages, still inside the Bulletin's stated preference.

Not done: the leg's release test — one graph theorist unfamiliar with
alternating plane graphs reading the revised note in at most 90 minutes and
explaining both estimates unaided. That is a human teach-back review and no
model can close it.

## Keeping it in step

`apg.tex` remains the archival version and the source of truth. **This file is
maintained by hand and will drift** — that has already happened twice between
`apg.tex` and `apg_bams.tex`, each time putting a statement known to be false
into the file a referee would read. Diff the shared sections before submitting.

## Build

    curl -O https://archive.austms.org.au/Publ/Bulletin/baustms.cls
    curl -O https://archive.austms.org.au/Publ/Bulletin/srtnumbered.bst
    TEXINPUTS=".:" tectonic apg101.tex

Abstract is 149 words, inside both the class template's 150 and the submissions
page's 200. MSC 2020: primary 05C10, secondary 05C30.
