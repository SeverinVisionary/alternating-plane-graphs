# v1.0.6 — the submission note, and a correction to the archival text

## Why this release exists

The Conjecture 10.1 material went through four review passes between 2026-09-07
and 2026-09-09, ending in the 10-page note `paper/apg101.tex` prepared for the
Bulletin of the Australian Mathematical Society. Those passes corrected
statements that the archival manuscript and this deposit's own description were
still making. **v1.0.5 is behind on all of it.**

## Corrections to claims that were public and wrong

* **"Unconditional" is withdrawn as a description of Conjecture 10.1.** Read
  naturally it claims independence from the *definition of face size*. That is
  not what is proved: boundary-walk length is fixed throughout, and what varies
  is only whether face alternation is required across a bridge. The source
  paper's definition excludes bridges and says so on p. 339; what this work adds
  is a second proof under a **bridge-relaxed** definition that admits them.
  Corrected in `paper/apg.tex`, `paper/apg_bams.tex`, `ARTIFACT.md`,
  `ZENODO.md`, `docs/index.html` and this deposit's description.
* **A false sentence about corners at a cut vertex.** The archival manuscript
  said that where one face occupies several corners at a vertex, "those corners
  are non-consecutive, so alternation is undisturbed". Across a bridge they are
  consecutive — precisely the case the parity lemma exists to handle. The proof
  was never wrong; the explanation of it was.
* **Two misattributed equations of the source paper**, now checked against the
  article itself: (9.5) is the face bound `f <= 5e/12` and contains no `1/2` to
  replace (the degree-2 contribution is in (9.8)–(9.9)); (9.2) is
  `r*f_r = sum_s e_{r,s}`, not the global `sum_s s f_s = 2e`.

## New

`paper/apg101.tex` and `paper/apg101.pdf` — Conjecture 10.1 alone, 10 pages,
five figures, two tables, seven references, in the AustMS `baustms` class. Its
proofs are self-contained and depend on no computation; the checks in this
repository are advisory for it.

`submission/` records the four reviews behind it, the cover letter and the
submission checklist.

## Unchanged

The certificates, the verifiers, and the status of Conjectures 10.2 and 10.3.
Conjecture 10.3 remains **not settled**: witnesses at 54 orders, infinite tail
unproved.

## Verification

`1296 passed, 13 skipped`. Python standard library only for the settled results.

## Still open

No mathematician other than the author has read the Conjecture 10.1 proof. The
teach-back review is satisfied only in its responsible-author form.
