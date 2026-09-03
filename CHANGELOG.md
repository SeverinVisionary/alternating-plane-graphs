# Changelog

Versions are for the deposit, not for an API. A release is a state of the
evidence: what is settled, and what a reader can check.

## Unreleased

Everything below is on `main` and none of it is tagged yet. The upstream-corpus
licence question is resolved: no third-party bytes are redistributed, each graph
is re-expressed in this repository's own format, and the digests of the
originals are kept for verification. A tag should now wait only on the
manuscript compiling.

### Settled

* **Conjecture 10.1** — proved, and since 2026-09-02 **unconditional**. The
  proof previously assumed (C2), that no edge has the same face on both sides,
  which is the source paper's reading of Definition 2.1 at a bridge rather than
  a hypothesis written into it. Both halves are now shown to hold under the weak
  reading too, so a counterexample would have to be bridgeless whichever way the
  definition is read.
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
* `paper/apg.tex`, all nine sections drafted, **never compiled** — no TeX
  installation on the machine it was written on.

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
