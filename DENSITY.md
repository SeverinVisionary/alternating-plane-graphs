# The fourth problem: the asymptotic degree distribution

Section 10 of the source paper poses four open items. Three are settled in this
repository. This one is not.

## The problem, verbatim

From (Althofer, Haugland, Scherer, Schneider, Van Cleemput, *Alternating plane
graphs*, Ars Math. Contemp. **8** (2015) 337-363), p. 362:

> "What the typical parameters are for large alternating plane graphs is still
> an open problem. E.g., if we let `r` be the number of vertices of degree 3 in
> a (3,4,5)-alternating plane graph, then we know from Theorem 3.2 that the
> number of vertices of degree 4 is in the interval `[r - 5, 3/2 r - 5]`. The
> question is, given this interval, how are the alternating plane graphs
> distributed. Is there a density function on the interval `[1, 1.5]` which
> gives the asymptotic fractions of (3,4,5)-alternating plane graphs for large
> vertex numbers `n`? If so, what does the density function look like?"

So the question is about **shape, not count**. Write `r = v3`. Theorem 3.2 pins
`v5 = v3 - 4` and confines `v4` to `[r - 5, 1.5r - 5]`, so the ratio `v4/v3`
lies asymptotically in `[1, 1.5]`. Where in that interval do actual
`(3,4,5)`-alternating plane graphs fall as `n` grows, and is there a limiting
density?

An earlier version of this file described the problem as the asymptotic *number*
of `(3,4,5)`-APGs. That was a misreading, corrected here after reading p. 362.

## The only thing this repository contributes: 26 data points

Every certificate satisfies `v5 = v3 - 4` and sits inside the paper's interval,
as it must. What is striking is **where**:

| `n` | `v3` | `v4` | `v5` | `v4/v3` |
| --- | --- | --- | --- | --- |
| 46 | 16 | 18 | 12 | 1.1250 |
| 50 | 18 | 18 | 14 | 1.0000 |
| 56 | 20 | 20 | 16 | 1.0000 |
| 74 | 26 | 26 | 22 | 1.0000 |
| 92 | 32 | 32 | 28 | 1.0000 |
| 109 | 37 | 39 | 33 | 1.0541 |
| 110 | 38 | 38 | 34 | 1.0000 |

Across all 26 the ratio runs from **1.0000 to 1.1250** — the bottom
one-quarter of an interval of width `0.5` — and it drifts *down* with `n`,
hitting exactly `1` at the largest orders.

**This is not evidence about the density function.** It is a selection effect,
and saying so is the point. The certificates were produced by one construction,
a capped unrolling of a periodic strip, and the spliced family adds copies of a
single period, so every member inherits that period's degree profile. A
construction that emits one graph per order tells you about the construction,
not about the distribution over all graphs at that order. If anything the
clustering at `v4/v3 = 1` is a warning: it is exactly what a periodic family
looks like, and exactly what a sample would not look like.

## Why the methods here do not reach it

Everything settled in this repository is **existence**: one graph per order, or
a class shown empty. The question here needs a *measure over all* graphs at
order `n`, and nothing here enumerates.

* The 26 certificates are 26 objects. No census of `(3,4,5)`-APGs at any order
  was attempted, and the search lanes ([`closed_map_search.py`](closed_map_search.py),
  [`plane_apg_search.py`](plane_apg_search.py), the `near_open_*` family) are
  hit-finders with no completeness argument, so they cannot produce a
  distribution even in principle.
* The periodic capping lemma makes this worse rather than better: it produces
  one graph per order from one certificate, all sharing a degree profile.
* The class is rigid in a way that frustrates sampling: a sweep over every
  two-edge switch of all 26 certificates found **zero** switches leaving a valid
  `(3,4,5)`-APG, so the one-switch neighbourhood of every certificate is empty.
  Local moves cannot walk the space, which rules out the obvious Markov-chain
  approach to sampling.

## What it would take

Not more compute on these lanes. A distribution needs either enumeration or a
sampler, and this repository has neither.

1. **An exhaustive census at small orders**, with `plantri` or an equivalent
   generator restricted to the degree and face-size profile. This is where
   anyone should start: it produces the first honest histogram of `v4/v3`, and
   would say immediately whether the mass concentrates, spreads, or is
   bimodal. It is a means to a conjecture, not to a theorem.
2. **A structure theorem** giving every `(3,4,5)`-APG a cap-strip-cap
   decomposition with a bounded interface alphabet — not merely the ones built
   here. The count then becomes a regular language and `v4/v3` a transfer-matrix
   computation, which would give the density function outright. The obstacle is
   the word *every*: this repository has a construction, not a classification.
3. **A bijection** with an already-counted family of plane maps. Theorem 3.2's
   identities (`v3 = f3`, `v4 = f4`, `v5 = f5`, `E = 2V - 2`, `F = V`) are
   unusually tight and are the natural hook.

Route 1 is a different project from this one, and the right next one.
