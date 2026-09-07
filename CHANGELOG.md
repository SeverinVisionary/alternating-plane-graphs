# Changelog

Versions are for the deposit, not for an API. A release is a state of the
evidence: what is settled, and what a reader can check.

## 1.0.3 — 2026-09-06

A second adversarial pass, run against the working tree rather than the public
snapshot, found the withdrawal of 2026-09-05 incomplete and found the gate that
was supposed to measure Conjecture 10.3's coverage measuring nothing.

* **`witness_coverage.residue()` was asserting the withdrawn theorem.** Its
  `family_orders()` term is `range(floor, 400, 3)` over a hard-coded tuple and
  reads no file, so `residue() == []` held whether or not any witness existed
  from order 48 up -- and three gates asserted exactly that. Delete every stored
  witness above 47 and the old residue notices **one** missing order out of 328.
  `verified_orders()` and `verified_residue()` now measure the checked evidence
  (stored certificates plus Section-8 closures); the three gates assert those,
  and a new control pins the old function's blindness so it cannot be mistaken
  for evidence again. The published sentence "derives the covered set from files
  rather than asserting it" was false where it mattered most.
* **The withdrawal is finished.** `paper/apg.tex` still said "Three are settled
  here", still listed the spliced family in Theorem 7.1's source table, and
  still asserted the family is 3-connected at every order; the BAMS variant was
  untouched; `CONJECTURE_10_3.md` was titled "settled"; `ATTRIBUTION.md`,
  `THREE_CONNECTIVITY_CLAIM.md` and three `docs/index.html` metadata fields
  still claimed the conjecture. All corrected.
* **The deposit is retitled.** "Settling Conjectures 10.1, 10.2 and 10.3" is not
  what this establishes. It is now "Alternating plane graphs: settling
  Conjectures 10.1 and 10.2, with witnesses for 10.3". The manuscript's own
  title was already neutral and is unchanged.
* **The span correction of 2026-09-05 was itself wrong.** It claimed the gate
  found span 3, hence a four-copy window. Measured over every spliceable order
  at `d = 1, 2, 3, 5`, the maximum span is **2** -- three consecutive copies,
  the wording used all along. The gate's `<= 3` was a slack threshold, not a
  finding, and is now `<= 2`. What survives is that the bound is measured, not
  derived: the manuscript presented it as following from face size and edge
  offset, which does not follow, and now says so.
* **"Each gate is paired with a control that must fail" was not true.**
  `test_verifier_mutations.py` lists 17 verifier conditions with no negative
  control. Stated as "most", with the exceptions named, on every surface.
* **Three gates were reading an empty directory.** `certificates/census_sources`
  has held `.json` since 1.0.0, but two gates in `test_exact_map_cnf.py` and one
  in `test_closed_map_search.py` still globbed `*.plc`. The last had no count
  assertion and had been passing vacuously. All three now read the census.
* **Two optional-dependency gates failed instead of skipping**, against the
  promise in `requirements-optional.txt`: one needs `z3`, and one drove a CLI
  that refuses solver work on macOS. The second is not fixable by passing
  `--allow-darwin`: `--timeout` bounds the solve loop only, the encoding is
  built before the clock starts, and a run launched with `--timeout 3` was still
  alive after eight hours. That gate now asserts the refusal on Darwin.
* **Licence and provenance.** "No third-party graph data is redistributed" was
  false as written -- no third-party *files* are, but the graphs are the
  corpus's. Zenodo carries one licence field, so the record's `MIT` is now
  explicitly scoped to the code and the original work. The remedy remains
  contacting the corpus authors, which has not been done.
* Counts and timings corrected: **1308 gates, 1295 passed, 13 skipped**, 7m52s
  -- or about two hours where the optional `python-sat` is installed, because
  the two repaired census gates then do the work they had been skipping. Four
  independent verifiers, not three, on four remaining surfaces.

## 1.0.3 — 2026-09-05

**A theorem was withdrawn.** An adversarial review pass, briefed to attack the
deposit, found the induction carrying 3-connectivity through the spliced family
to be unestablished. Conjecture 10.3 was stated as a theorem on the strength of
it; that statement is withdrawn. The manuscript's theorem now claims only the 54
orders with explicit witnesses, and says the conjecture is not proved. Full
account in `REVIEW.md`; the gap itself is stated at the top of
`family_connectivity.py`.

Six further corrections from the same review, each verified locally before being
applied:

* **The calibration assurance was false.** "Any step that over-counted would
  have failed this test" -- an invalid *stronger* bound, `5/12 - 1/1000`,
  reproduces the same `k >= 12` threshold exactly, so the calibration cannot
  detect the dangerous direction. `conjecture_10_1.py` had said so all along
  under the heading "what it does not show"; the manuscript and
  `CONJECTURE_10_1.md` had not.
* **A withdrawn argument was still advertised.** `CONJECTURE_10_1.md` credited
  half one to a leaf-block argument that `bridge_lemma.py` records as unsound.
* **"Five independent reviewers" read as five mathematicians.** They were five
  AI review runs, and `FOR_REVIEWERS.md` says in terms that no human has checked
  this. The two files contradicted each other.
* **The face-span bound is measured, not derived.** *(Partly retracted the next
  day: this entry also claimed the span was 3 and the window four copies. It is
  2 and three copies, measured over every spliceable order; the gate's `<= 3`
  was a slack threshold, not a finding, and has been tightened to `<= 2`. The
  original "three consecutive copies" wording was correct.)* Face size at most five and
  edge offset at most two do not imply it: `0, 2, 4, 3, 1, 0` is a closed
  sequence of five steps of size at most two touching five levels. The prose
  also said "three consecutive copies" where the gate permits four.
* **"Standard library only" was wrong** for the suite, which needs `pytest`. The
  four verifiers are dependency-free; the harness is not.
* **A rejection control was over-broad**, using bare `pytest.raises(Exception)`
  where an unrelated bug would satisfy it. Now `verify.VerificationError`.

Also: `NOTICE.md` claimed the MIT licence covered *everything* in the
repository, and offered "different bytes" as a clearance argument for the
re-expressed corpus. Re-encoding does not grant a permission that was absent;
the file now says so and points at contacting the corpus authors as the actual
remedy. And the certificate count is stated honestly: **80 files, 62 distinct
graphs**, with the duplication explained in `ARTIFACT.md`.

## 1.0.2 — 2026-09-03

Two changes, both prompted by preparing the deposit for a human verifier.

**The Conjecture 10.2 claim is made precise.** Its closure is a union of four
ranges and three of them are the 2015 paper's -- the heuristic search over
`20..42`, the Section-8 construction, and Theorem 8.1 for `n >= 111`. Only the
26 certified orders were new, so "settled" meant "settled, given the source
paper", which is weaker than it sounded. The periodic capping lemma was already
proved here and already yields order 48 and every order from 50 up, but the
coverage gate did not use it. It does now, and two new gates state the position
exactly: this deposit closes **every order `n >= 46`** on its own, making the
paper's Theorem 8.1 redundant, while orders `20..45` are inherited and are not
re-established here. A control checks the lemma is load-bearing rather than
decorative -- without it the certificates and the paper's finite constructions
stop at 110. The claim is qualified where it needs to be: the family's floor
orders and 57, 58, 59, 61, 63 rest on machine-verified splices rather than the
lemma *as stated*, per the manuscript's own deletion remark.

The gate count moves from 1253 to **1257** with the four new coverage tests;
the quoted runtime is the measured 10m40s for this release rather than the
13m07s of 1.0.0.

**The simple-facial-walks restriction is documented where it is imposed.** All
four decision procedures reject a facial walk that repeats a vertex, which
Definition 2.1 does not require -- the paper says on p. 362 that some of its
Section-7 alternating plane graphs are not 2-connected. `general_apg.is_apg`
recorded this in its docstring; `verify.py`, `verify_darts.py` and
`fast_apg_check.py` imposed it silently. All three now carry the same note. The
restriction is safe in the direction the existence results need -- a stricter
test can only reject a good witness, never accept a bad one -- but a reader is
now told rather than left to find it.

## 1.0.1 — 2026-09-02

DOI [10.5281/zenodo.22269200](https://doi.org/10.5281/zenodo.22269200) (concept).

**A false claim about the source paper was published in 1.0.0 and is withdrawn
here.** The 1.0.0 abstract said Definition 2.1 is "ambiguous at a bridge" and
that "the paper does not say which" reading is meant. That is wrong. Four lines
below Definition 2.1 the paper states that an alternating plane graph "is always
at least 2-edge-connected, since plane graph with edge connectivity 1 contains a
face that is adjacent to itself" (p. 339) — the strict reading, explicitly.

The repository's own source code had this right the whole time:
`conjecture_10_1.py` quotes that sentence verbatim and attributes the reading to
the paper. Only the summary prose drifted off it, and it drifted in the
flattering direction, describing a robustness result as the closing of a gap the
authors had left open.

Nothing mathematical changes. The proof did not use that sentence in 1.0.0 and
does not use it now; it still closes under the permissive reading in which
bridges are allowed. What changes is the claim made about the paper:

* **was** — the definition is ambiguous at a bridge and the paper is silent
* **is** — Definition 2.1's four bullets say nothing about bridges, but the
  paper rules them out a few lines later as an asserted consequence, stated in
  passing rather than proved; this proof does not depend on that assertion

Corrected in `ARTIFACT.md`, `ZENODO.md`, `CITATION.cff`, `.zenodo.json`, the
GitHub release notes and the landing page. The 1.0.0 record stays published, so
what was first claimed remains readable.

The same false wording stood in `paper/apg.tex`, which is corrected here too:
Convention (C2) now quotes the p. 339 sentence and the surrounding text says
plainly that this is a robustness statement, not the repair of a gap.

**The manuscript now compiles.** `paper/apg.pdf` ships, 11 pages, built with
Tectonic. The "never compiled" limit that 1.0.0 carried in six places is
therefore retired; what remains true, and is now what those places say, is that
the manuscript is a draft that has had no peer review.

`docs/artifact.pdf` is regenerated from the corrected `ARTIFACT.md`. Its first
edition was produced by a script that was not committed, and `ARTIFACT.md` then
changed underneath it, so the shipped PDF asserted on its own front page a claim
the repository had already withdrawn. The generator is now committed as
`render_artifact_pdf.py` (`make artifact-pdf`), so the rendering can be checked
against its source.

Also in this release: a GitHub Pages landing page under `docs/`, and the minted
DOI recorded in `README.md`, `ZENODO.md` and `CITATION.cff`.

## 1.0.0 — 2026-09-02

DOI [10.5281/zenodo.22269201](https://doi.org/10.5281/zenodo.22269201).
First deposit. The upstream-corpus licence question is resolved: no third-party
bytes are redistributed, each graph is re-expressed in this repository's own
format, and the digests of the originals are kept for verification.

### Settled

* **Conjecture 10.1** — proved, and since 2026-09-02 no longer resting on
  (C2), the convention that no edge has the same face on both sides. (C2) is the
  source paper's reading of Definition 2.1 at a bridge, asserted on p. 339 as a
  consequence rather than written into the definition. Both halves are now shown
  to hold under the weak reading too, so a counterexample would have to be
  bridgeless whichever way the definition is read. This is robustness, not a gap
  in the paper — see 1.0.1 above.
* **Conjecture 10.2** — settled. Certificates at all 26 previously open orders,
  plus a proved periodic capping lemma generating order 48 and every order from
  50 up.
* **Conjecture 10.3** — settled. A verified 3-connected witness at every order
  from 19 up, with the covered set derived from files rather than asserted.

### Open

* The asymptotic degree distribution: the density of `v4/v3` on `[1, 1.5]`.
  See [`DENSITY.md`](DENSITY.md); the methods here are existence arguments and
  produce no measure over the class.

### Disclosure

* `AI_DISCLOSURE.md`. This work was produced with substantial AI assistance,
  including the step that makes Conjecture 10.1 unconditional, and AI review was
  used adversarially throughout. No AI system is an author. Surfaced in
  `README.md`, `ARTIFACT.md`, `ATTRIBUTION.md`, `CITATION.cff`, `.zenodo.json`
  and the manuscript, since a disclosure only in a file nobody opens is not one.

### Package

* `LICENSE`, `NOTICE.md`, `ARTIFACT.md`, `ATTRIBUTION.md`, `FORMATS.md`,
  `CITATION.cff`, `.zenodo.json`, `CHANGELOG.md`.
* `Makefile` with `verify`, `verify-fast`, `figures`, `manifest`. Requirements
  pinned; the settled results need only the standard library plus pytest.
* `certificates/MANIFEST.sha256` over every file under `certificates/`, gated in both
  directions with a tamper control.
* `export_planar_code.py`, so certificates can be checked by `plantri` or House
  of Graphs. It was round-tripped against all 33 third-party planar_code files
  while those were present; that gate now skips, since the bytes are not
  redistributed.
* `certificates/UPSTREAM_PROVENANCE.json`, pairing the digest of each original
  file with the digest of its re-expression.
* `REVIEW.md`, recording what independent review changed, including three
  claims made here that were false and were withdrawn.
* `draw.py` and `figures/`, computed from the certificates. Honest about its
  limit: barycentric collapse makes drawings above roughly order 50 artefacts of
  the arithmetic, and the tool refuses to write them.
* `paper/apg.tex`, all nine sections drafted. Not compiled at 1.0.0 — there was
  no TeX installation on the machine it was written on. It compiles as of 1.0.1.

### Corrections carried from the upstream repository

* `test_exact_map_cnf.py` imported `pysat` at module scope with no guard, so a
  bare `pytest` run errored at collection on any machine without it.
* `CONJECTURE_10_1.md` asserted "half one has no such dependence" on (C2) in one
  section and reported the review panel finding that exact claim false three
  paragraphs later.
* `bridge_lemma.py` claimed each side of a bridge has at least five vertices, on
  the grounds that every non-endpoint vertex of a side has even degree. A non
  sequitur — a side may contain further bridges, and parity permits odd degree
  at their endpoints. Retracted in place; nothing depended on it.
* `draw.py` attributed its crossings to graphs not being 3-connected. The real
  cause is numerical collapse of the barycentric solution. The correction as
  first written was itself wrong: it named `TARGET_46` as the non-3-connected
  certificate, conflating it with the separate order-46 counterexample.
  `TARGET_46` is 3-connected. The counterexample draws with no crossings and a
  wider vertex separation than any 3-connected certificate of similar order,
  which is what actually shows crossings do not track connectivity.
* `UNCAPPABILITY_SPEC.md` argues about the `(1,0)` unrolling while the
  certificates are `(1,-1)`. Kept, with a retraction header.
