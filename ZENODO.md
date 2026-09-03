# Three conjectures on alternating plane graphs — deposit summary

**Settles three of the four open problems** in Section 10 of Althöfer, Haugland,
Scherer, Schneider & Van Cleemput, *Alternating plane graphs*,
*Ars Mathematica Contemporanea* **8** (2015) 337–363,
[doi:10.26493/1855-3974.584.09a](https://doi.org/10.26493/1855-3974.584.09a).

---

## Highlights

| | |
| --- | --- |
| ✅ **Conjecture 10.1** | **Proved, and not resting on an interpretation.** Definition 2.1 is silent about bridges; the paper rules bridges out a few lines later, asserting that an alternating plane graph "is always at least 2-edge-connected, since plane graph with edge connectivity 1 contains a face that is adjacent to itself" (p. 339). The proof here does not use that sentence — it closes under the permissive reading too, in which bridges are allowed. |
| ✅ **Conjecture 10.2** | **Settled.** Certificates for all **26** previously open orders, plus a *proved* periodic capping lemma generating order 48 and **every** order ≥ 50. |
| ✅ **Conjecture 10.3** | **Settled.** A verified 3-connected witness at **every** order ≥ 19. |
| ⬜ **Fourth problem** | **Open.** The asymptotic distribution of `v₄/v₃` on `[1, 1.5]`. Out of reach of these methods, and we say why. |

**Also here:** a `(3,4,5)`-alternating plane graph on **46 vertices with a
separating pair**, refuting the natural shortcut that every such graph is
3-connected.

---

## The open orders, closed

Conjecture 10.2 was open at exactly 26 orders. All now carry certificates:

| block | orders |
| --- | --- |
| 46–56 | 11 orders |
| 67–74 | 8 orders |
| 88–92 | 5 orders |
| 109, 110 | 2 orders |

And the capping lemma removes the need for a finite list: one certificate per
residue class mod 3 generates the family from floors **48**, **50** and **52**.

---

## Verification

```sh
make deps          # pytest, and nothing else
make verify-fast   # load-bearing gates, ~1 minute
make verify        # everything, ~13 minutes
```

| measure | value |
| --- | --- |
| gates | **1253 passed, 13 skipped** |
| runtime | 13 min (Python 3.9.6, macOS) |
| dependencies of the settled results | **standard library only** |
| independent verifiers per certificate | **3** |

The 13 skips are declared, not hidden: 11 need a third-party corpus that is not
redistributed here, 1 needs optional `python-sat`, 1 follows from the first.

**Certificates store rotation systems only.** No file records a claim that a
graph *is* an alternating plane graph — degrees, faces, face sizes, bridges,
connectivity and both alternation conditions are recomputed on every run. Each
gate is paired with a control that must fail, so a check cannot pass by being
vacuous.

---

## What is in the deposit

| path | count | contents |
| --- | --- | --- |
| `certificates/` | 80 JSON | witnesses, counterexample, published corpus re-expressed |
| `*.py` | 74 | constructions, three verifiers, search lanes, tooling |
| `test_*.py` | 77 | the gates |
| `figures/` | 12 | SVG + TikZ, computed from the certificates |
| `paper/` | 1 | manuscript, **draft — never compiled** |
| `results/` | 614 | run artifacts, provenance only |

---

## Read these first

| document | what it answers |
| --- | --- |
| [`ARTIFACT.md`](ARTIFACT.md) | what is settled, how to check it, what is not load-bearing |
| [`FORMATS.md`](FORMATS.md) | the data format, with a dependency-free reference reader |
| [`ATTRIBUTION.md`](ATTRIBUTION.md) | what is the source paper's, what is re-verified, what is new |
| [`REVIEW.md`](REVIEW.md) | what independent review changed — including three claims here that were **false and withdrawn** |
| [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md) | the extent of AI assistance, which is substantial |
| [`NOTICE.md`](NOTICE.md) | why no third-party bytes are redistributed |
| [`DENSITY.md`](DENSITY.md) | the fourth problem, quoted, and why it is out of reach |

---

## Honest limits

- **The manuscript has never been compiled.** There was no TeX installation on
  the machine it was drafted on. It is a draft and is labelled as one.
- **Three claims made here were false and were withdrawn**, plus a certificate
  misidentified as not 3-connected. All four are recorded at the files that made
  them rather than quietly deleted.
- **The published corpus is not redistributed** — no licence statement was found
  at its source. Each graph is re-expressed in this repository's own format,
  with the digest of every original preserved for verification.
- **AI assistance was substantial**, including the step that makes Conjecture
  10.1 unconditional. No AI system is an author.

---

## Citation

Cite this deposit *and* the paper whose conjectures it settles. Machine-readable
metadata is in [`CITATION.cff`](CITATION.cff).

| | |
| --- | --- |
| **this deposit** | DOI [10.5281/zenodo.22269200](https://doi.org/10.5281/zenodo.22269200) — the *concept* DOI, which always resolves to the latest version |
| **version 1.0.0** | DOI [10.5281/zenodo.22269201](https://doi.org/10.5281/zenodo.22269201) |
| **landing page** | <https://severinvisionary.github.io/alternating-plane-graphs/> |
| **the source paper** | Althöfer, Haugland, Scherer, Schneider & Van Cleemput, *Alternating plane graphs*, *Ars Math. Contemp.* **8** (2015) 337–363, [doi:10.26493/1855-3974.584.09a](https://doi.org/10.26493/1855-3974.584.09a) |

