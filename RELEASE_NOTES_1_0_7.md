# v1.0.7 — what the capping lemma proves, and a rewritten manuscript

Two changes. The manuscripts were rewritten for a reader, and the coverage claim
for Conjecture 10.2 was corrected to what the capping lemma actually proves. No
certificate, verifier or result changed.

## The capping lemma reaches every order from 67 up

Theorem 6.1 is proved for **inserting** periods, `d >= 0`. Its hypothesis is a
deep block of at least five copies, and the smallest certificates that have one
are at orders **67, 68 and 69**, one per residue class mod 3. So the lemma gives
every order `n >= 67`.

Earlier versions said it gave order 48 and every order from 50 up. That reach
came from **deleting** periods, and the locality argument in the proof is written
for insertion. The deletion splices are still checked by computation in
`test_pumping_splice.py`, including the ones at orders 57–66, but they are not
proved.

**Conjecture 10.2 is still settled**, with a different division of labour:

| orders | source |
| --- | --- |
| 20–45, 57–66, 75–87, 93–108 | the 2015 paper's heuristic search and Section 8 |
| every `n >= 111` | the 2015 paper's Theorem 8.1 |
| 46–56, 67–74, 88–92, 109, 110 | the 26 certificates here |
| every `n >= 67`, again | the capping lemma here |

What is gone is the claim that this deposit closes every order `n >= 46` on its
own. It closes 46–56 and every order from 67 up; orders 57–66 are the source
paper's.

`test_conjecture_coverage.py` now measures the deposit's own coverage from the
proved insertion reach, so it pins 57–66 as inherited instead of counting
deletion splices. The capping lemma is described with **three** finite
machine-checked hypotheses everywhere, not two.

## The manuscripts

`paper/apg.tex` and `paper/apg101.tex` were rewritten. The mathematics is
unchanged: every theorem, lemma and table entry says what it said before. What
changed is the prose. A journal desk-rejected the Conjecture 10.1 note over
prose that read as AI-generated, so the disclaimers, scoped caveats,
verification-log vocabulary and page-pinned source exegesis are gone, along with
about a third of the words.

`paper/apg101.tex` now uses the standard `amsart` class. It had been built with
the Bulletin of the Australian Mathematical Society's class, which printed
"Submitted to the Bulletin" on page 1 and, through a missing `\maketitle`, left
the title and abstract out of the PDF altogether.

Two source citations were wrong and are corrected: in the 2015 paper, (9.5) is
the face bound `f <= 5e/12`, the `1/2` is in (9.8), and (9.9) combines them;
(9.2) is not the face-size sum. `paper/apg_bams.tex` is untouched, as the record
of what was submitted.

The manuscripts carry no peer review.
