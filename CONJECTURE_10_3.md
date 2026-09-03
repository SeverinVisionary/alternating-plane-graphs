# Conjecture 10.3 — settled

> Companion notes: [`CONJECTURE_10_1.md`](CONJECTURE_10_1.md) for the paper's
> other numbered conjecture, and
> [`THREE_CONNECTIVITY_CLAIM.md`](THREE_CONNECTIVITY_CLAIM.md) for the shortcut
> that turned out to be false.

> **Conjecture 10.3** (Althofer, Haugland, Scherer, Schneider, Van Cleemput,
> *Alternating plane graphs*, *Ars Math. Contemp.* **8** (2015) 337–363, p. 362.)
> For any `n >= 19` there exists a 3-connected alternating plane graph on `n`
> vertices.

**Every order from 19 up now has a 3-connected witness verified in this
repository**, and `witness_coverage.residue()` — which derives the covered set
from files and constructions rather than asserting it — returns the empty list.
Gated by [`test_conjecture_10_3.py`](test_conjecture_10_3.py), which also checks
that each source is load-bearing: removing any one of them reopens orders.

| orders | source | what it is |
| --- | --- | --- |
| **19** | [`certificates/order19/`](certificates/order19/PROVENANCE.md) | all five 19-vertex APGs; general APGs, not `(3,4,5)` |
| 17, 20, 26–36, 42 | [`certificates/census_sources/`](certificates/census_sources/PROVENANCE.md), [`known/`](certificates/known/PROVENANCE.md) | published planar-code witnesses |
| 21, 22, 23, 25 | [`certificates/search_seeds/`](certificates/search_seeds/PROVENANCE.md) | published search seeds |
| 21–24, 39–45 | [`section8_witnesses.py`](section8_witnesses.py) | Section-8 closures built from `results/blocks/` |
| **37, 38** | [`certificates/surgery/`](certificates/surgery/PROVENANCE.md) | disk surgery on graphs already held |
| 46–56, 67–74, 88–92, 109, 110 | [`certificates/targets/`](certificates/targets/) | the Conjecture 10.2 certificates |
| 48, and every `n >= 50` | [`pumping_splice.py`](pumping_splice.py) + [`family_connectivity.py`](family_connectivity.py) | the spliced family, **proved** 3-connected at every order |

The infinite tail is not a horizon artefact. `family_connectivity.py` proves the
spliced family is 3-connected at *every* order it produces, by the same
locality that carries the periodic capping lemma; the finite sweeps only check
that theorem's hypotheses.

## The three orders that were hard, and why

**19** is the one order the settled Conjecture 10.2 cannot reach: the paper's
exhaustive search reports no `(3,4,5)`-APG on 18 or 19 vertices at all, so a
witness has to be a general APG in the sense of Definition 2.1. There are
exactly five APGs on 19 vertices; **all five are 3-connected**. `verify.py`,
`verify_darts.py` and `fast_apg_check` all reject them, correctly — each has a
degree-6 vertex or a 6-face.

**37 and 38** are out of reach of the Section-8 arithmetic `18a+19b+20c+21d+3`,
because 34 and 35 are not sums of `18, 19, 20, 21` — which is exactly why the
paper's own Section-8 coverage list skips them. They close by **disk surgery**:
cut the star of a vertex, an edge or a face out of a stored `(3,4,5)`-APG, let
the boundary degrees float, and refill the disk under Definition 3.1.

## The shortcut that does not exist

If every `(3,4,5)`-APG were 3-connected, the settled 10.2 would have given 10.3
for all `n >= 20` in one step. **It is false**: there is a `(3,4,5)`-APG on 46
vertices with a separating pair. See
[`THREE_CONNECTIVITY_CLAIM.md`](THREE_CONNECTIVITY_CLAIM.md). Nothing above
depends on it — every witness here was checked individually, never inferred
from a class-wide claim — but it is why `family_connectivity.py` is necessary
rather than tidy.

## What is taken on trust, stated plainly

* That the five order-19 files are *all* the APGs on 19 vertices — the paper's
  exhaustive search and the House of Graphs census. **Irrelevant to the positive
  answer**: one 3-connected witness settles the order, and there are five. It
  would matter only for a refutation.
* The published planar-code witnesses at 17, 20, 21–23, 25–36 and 42 are the
  paper's graphs, decoded here and re-verified, not new constructions.

Everything else — the Section-8 closures, the surgery witnesses, the 26 target
certificates and the spliced family — is built and checked in this repository.

## Search lanes that did not work, and why

Three annealing lanes were built and none returns a hit; the diagnoses are the
useful part and are recorded in [`closed_map_search.py`](closed_map_search.py),
[`general_apg.py`](general_apg.py) and
[`plane_apg_search.py`](plane_apg_search.py). In short: the `(3,4,5)` class is
rigid enough that the one-switch neighbourhood of every certificate is **empty**,
and in the general class every local condition reaches zero while the whole
residual penalty is genus. Neither lane was needed in the end — every order
fell to construction.
