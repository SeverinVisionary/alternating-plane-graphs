# `apg101.tex` — the standalone Conjecture 10.1 note

**This is the submission.** Seven pages, AustMS `baustms` class, for the
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

Kept in full: Definition 2.1 and the `X,Y` class, Conventions (C1) and (C2),
the per-edge identity, both halves of the proof, the calibration with its
"not a certification" disclosure, and all of \S5 removing the (C2) dependence.

## Keeping it in step

`apg.tex` remains the archival version and the source of truth. **This file is
maintained by hand and will drift** — that has already happened twice between
`apg.tex` and `apg_bams.tex`, each time putting a statement known to be false
into the file a referee would read. Diff the shared sections before submitting.

## Build

    curl -O https://archive.austms.org.au/Publ/Bulletin/baustms.cls
    curl -O https://archive.austms.org.au/Publ/Bulletin/srtnumbered.bst
    TEXINPUTS=".:" tectonic apg101.tex

Abstract is 146 words, inside both the class template's 150 and the submissions
page's 200. MSC 2020: primary 05C10, secondary 05C30.
