# Route calibration, 2026-09-01

Two of the routes frozen in [`../../ROUTES_2026-08-31.md`](../../ROUTES_2026-08-31.md)
carried calibration gates that had to fire before any engineering. Both fired.
Neither is a construction; target coverage remains **0/26 independently
verified**.

## Substitution notice

The external an independent reviewer could **not** be dispatched: this session
carries no credentials for it, so
[`../../REVIEW.md`](../../REVIEW.md)
remains **STAGED, not run**, and nothing below counts toward a milestone gate
under the project rules section 9. What follows is a local literature and computation
pass over the answerable parts of that brief. It is evidence, not a review.

## R3, symmetric quotient search: **KILLED by measurement**

`automorphism_census.py` enumerates the map automorphism group of every
published `(3,4,5)`-APG held here. For a connected oriented map an
orientation-preserving automorphism is fixed by the image of one dart, so the
group is enumerated exactly, in seconds.

| corpus | result |
| --- | --- |
| 23 published APGs, orders 17-42 | **21 rigid** (\|Aut\| = 1) |
| the two order-17 maps | \|Aut\| = 2, orientation-preserving |
| every map at orders 26-42 | rigid |

Record: [`automorphism_census.json`](automorphism_census.json).

The quotient route assumes symmetric witnesses exist at the target orders.
Every published witness above order 17 is asymmetric, and the two symmetric
ones are the smallest objects in the corpus. Imposing a `C2` would search a
class the record suggests is empty exactly where we need it. **Do not build
it.** Caveat: 23 maps are the corpus this repository holds, not the 88 House
of Graphs records and not a census; the finding is a strong prior, not a
theorem.

### It also explains the measured symmetry-break result

The vertex lex-leader break costs 24x on satisfiable instances (order 17:
99 s with, 4.2 s without) and that had been recorded as an unexplained
measurement. Rigidity explains it. With `|Aut| = 1` each isomorphism class
contributes a *full* `n3! n4! n5!` orbit of labelled solutions, so breaking
the labelling symmetry removes solutions in the same proportion as it removes
search space: solution density is unchanged and only the constraint overhead
is left. Symmetry breaking here can only pay on the refutation side, which is
where the program should now expect it to help.

## R4, canonical-construction search: **narrowed to SMS**

Brinkmann, *Generating maps on oriented surfaces using the homomorphism
principle* (arXiv:2408.16512, Discrete & Comput. Geom. 2025) is the closest
tool to what R4 proposed: it generates maps -- rotation systems, not abstract
graphs -- with a prescribed degree sequence or a prescribed number of faces,
at up to millions of non-isomorphic maps per second, and it needs no
isomorphism rejection at all when the underlying graph is rigid, which the
census above says ours are.

It is nonetheless **not a fit**, on the author's own terms and on arithmetic:

- The paper states the method "is not suitable" when only a tiny fraction of
  input graphs embeds in the chosen surface, and that the program "is not
  meant and in general not useful for genus 0" -- which is our surface.
- Its own count of embeddings of a graph, `(1/2) * prod (deg(i) - 1)!`, is
  `2^18 * 6^14 * 24^14 / 2` for the order-46 `r = 18` profile. Enumerating
  embeddings per abstract graph is hopeless before the plane condition is
  even applied.

So R4 should be **SAT-modulo-symmetries**, not homomorphism-principle
generation. The current references are Kirchweger and Szeider's SMS framework
as presented in Jooken's 2025 survey (arXiv:2508.20825, section 4.4), the
comparative study of symmetry breaks in quantified graph search
(arXiv:2502.15078), and *Breaking Symmetries with Involutions*
(arXiv:2506.02903). Note the tension with the rigidity finding: SMS is a
minimality *propagator*, which pays where partial-symmetry clauses do not, but
the density argument above still applies, so SMS should be prototyped against
the measured order-17/order-20 pair before it is built out.

## Corroborations of existing repository positions

- **Prior-art gate holds.** Jooken's 2025 survey lists "Alternating plane
  graphs" in its table of generators and censuses and cites the 2015 paper,
  with no closure of Conjecture 10.2 and no target-order witness. This is an
  independent look at the source `PRIOR_ART.md` already records, and it
  changes nothing.
- **The plantri pricing was right, and the survey shows when the trick does
  work.** Its own worked example settles the last open case of the
  Schmeichel-Hakimi conjecture by generating planar triangulations on 20
  vertices and deleting **one** edge. Our target needs `n - 4 = 42` deletions
  at order 46, which is exactly why the same trick prices out at `10^32`.
- **Refutation scale.** The Keller-conjecture resolution cited in the survey
  produced 224 GB of binary DRAT. If R6 is ever run at a target order, that is
  the order of magnitude to budget, and it is a reason to settle the
  encoding-faithfulness audit first rather than after.

## What still needs the independent review

Unchanged and unanswerable here: the strip-family question (R5), the
existence prior for a strict order-25 block, and the faithfulness question of
whether a `(3,4,5)`-APG under Definition 2.1 may have a facial walk repeating
a vertex. Those remain in the staged brief.
