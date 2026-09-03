# Changelog

Versions are for the deposit, not for an API. A release is a state of the
evidence: what is settled, and what a reader can check.

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
