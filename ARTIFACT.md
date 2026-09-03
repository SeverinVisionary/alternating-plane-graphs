# The artifact: what is in it, and how to check it

This repository is the evidence for three settled conjectures. It is meant to
be deposited and read by someone with no prior contact with it, so this file
says what is here, what is load-bearing, and how to verify it without trusting
any claim made in prose.

For a one-page formatted overview see [`ZENODO.md`](ZENODO.md).

Source problem: Althofer, Haugland, Scherer, Schneider and Van Cleemput,
*Alternating plane graphs*, Ars Math. Contemp. **8** (2015) 337-363,
DOI [`10.26493/1855-3974.584.09a`](https://doi.org/10.26493/1855-3974.584.09a).

## Results

| Section 10 item | status | where |
| --- | --- | --- |
| Conjecture 10.1 (no `2,Y`-, no `X,2`-APG) | **proved**, unconditionally | [`CONJECTURE_10_1.md`](CONJECTURE_10_1.md) |
| asymptotic degree distribution | **open** | [`DENSITY.md`](DENSITY.md) |
| Conjecture 10.2 (`(3,4,5)`-APG for all `n >= 20`) | **settled** | [`PUMPING_LEMMA_STATUS.md`](PUMPING_LEMMA_STATUS.md) |
| Conjecture 10.3 (3-connected APG for all `n >= 19`) | **settled** | [`CONJECTURE_10_3.md`](CONJECTURE_10_3.md) |

Attribution -- what is the source paper's, what is re-verified here, and what is
new -- is collected in [`ATTRIBUTION.md`](ATTRIBUTION.md).

**This work was produced with substantial AI assistance**, including the step
that makes Conjecture 10.1 unconditional. The extent, and what was and was not
taken on trust, is stated in [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md).

The (C2) qualification on 10.1 was removed on 2026-09-02. It had been the
paper's reading of Definition 2.1 at a bridge rather than a hypothesis written
into it; [`bridge_lemma.py`](bridge_lemma.py) supplies the parity lemma and
`conjecture_10_1.py` the count that closes it, so the theorem now holds under
either reading.

## Verifying it

```
make deps      # pytest 8.4.2, and nothing else
make verify    # 1253 passed, 13 skipped, about 13 minutes
```

or, for the load-bearing gates only, about a minute:

```
make verify-fast
```

Recorded runtime for the figure above: Python 3.9.6 on macOS, 13m07s. Of the
13 skips, 11 need the published planar_code corpus, which is not redistributed
here (see [`NOTICE.md`](NOTICE.md) and [`conftest.py`](conftest.py)), one needs
the optional `python-sat`, and one is an empty parameter set that follows from
the corpus being absent. Nothing that is settled depends on any of them.

**The core needs only the standard library.** The proofs, the certificates and
all three verifiers import nothing outside it; `pytest` is the runner. `numpy`,
`sympy`, `z3` and `python-sat` appear only in optional search lanes and one
archived analysis script, none of which any settled result rests on.

## What is in the box

| path | count | what it is |
| --- | --- | --- |
| `certificates/targets/` | 26 | the Conjecture 10.2 witnesses, one per previously open order |
| `certificates/` (all) | 80 JSON | plus order-19, surgery, counterexample, seed and published witnesses, all as rotation systems |
| `*.py` modules | 74 | constructions, three independent verifiers, search lanes |
| `test_*.py` | 77 | the gates |
| `results/` | 614 | run artifacts, provenance only |
| `figures/` | 12 | SVG and TikZ for the five smallest certificates and the order-46 counterexample |
| `*.md` | 32 | the write-ups |

Certificates are **rotation systems only** -- no coordinates, no stored faces,
no stored claim that a graph is an alternating plane graph. Degrees, faces, face
sizes, bridges, connectivity and both alternation conditions are recomputed on
every run by `verify.py`, `verify_darts.py` and `fast_apg_check.py`, which were
written independently of each other. A corrupted certificate cannot pass by
asserting its own correctness. The format is specified, with a dependency-free
reference reader, in [`FORMATS.md`](FORMATS.md); `test_formats.py` executes that
reader out of the markdown against every certificate, so the specification
cannot drift from the data.

### Not load-bearing, and kept anyway

* **`CLOUD_*_JOB.md` (9 files)** are operator briefs for dispatching heavy
  searches to a Linux host. They are workflow instructions, not mathematics.
  They are kept because 27 cross-references in the write-ups point at them and
  because they record what was attempted.
* **`results/`** holds run artifacts: search logs, calibration records and
  console captures. They are evidence about the *process*, never about the
  mathematics — every mathematical claim here is carried by a gate. Review
  transcripts are not part of this package; what independent review changed is
  recorded in [`REVIEW.md`](REVIEW.md).
* **The search lanes** -- `closed_map_search.py`, `plane_apg_search.py`, the
  `near_open_*` family -- returned no hits. They are kept for their diagnoses,
  which are recorded in their own docstrings: the `(3,4,5)` one-switch
  neighbourhood of every certificate is empty, and in the general class every
  local condition reaches zero while the whole residual penalty is genus.

## Figures

[`draw.py`](draw.py) computes a Tutte barycentric embedding from the rotation
system, so a figure cannot depict a different graph from the one verified.
`make figures` re-renders the committed SVG and TikZ in `figures/`, and
`test_draw.py` requires the committed files to match a fresh render exactly.

The pipeline is honest about its own limit. These certificates are capped
unrollings of a long periodic strip, so the barycentric solution crushes the
interior exponentially in the order: minimum vertex separation runs `2.3e-03` at
order 46 down to `5.0e-12` at order 110, and spurious crossings appear precisely
where it falls through double precision. Above roughly order 50 the drawing is
an artefact of the arithmetic rather than a picture of the graph, and `draw.py`
refuses to write it.

Crossings say nothing about connectivity: the order-46 counterexample, which is
*not* 3-connected, draws with none at all and at a wider separation than any
3-connected certificate of similar order. Figures for the large orders need a
schematic of the cap-strip-cap decomposition instead, which is not built.

## What is taken on trust

Stated in full in [`CONJECTURE_10_3.md`](CONJECTURE_10_3.md), and short:

* that the five order-19 graphs are *all* the alternating plane graphs on 19
  vertices. Irrelevant to the positive answer -- one verified 3-connected
  witness settles the order, and all five are verified here. It would matter
  only for a refutation.
* that the published planar_code witnesses are the paper's graphs. They are
  decoded and re-verified here, not taken on faith, and every result is
  independently reconstructible without them.

## Before this is deposited

Nothing legal is outstanding. No third-party bytes are redistributed: the
published `planar_code` corpus is not included, each of its graphs is
re-expressed in this repository's own format, and the digests of the originals
are kept for verification. See [`NOTICE.md`](NOTICE.md).

What remains is editorial. The manuscript in [`paper/`](paper/) has never been
compiled -- there is no TeX installation on the machine it was drafted on -- and
its density section paraphrases the source problem rather than quoting it. See
[`paper/README.md`](paper/README.md).
