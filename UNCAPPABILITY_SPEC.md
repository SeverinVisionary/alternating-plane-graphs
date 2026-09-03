# The uncappability claim: what it would take to prove it

> **Superseded in part, and kept for provenance. Read this first.**
>
> This file argues about the `(1,0)` unrolling.
> [`unrolling_class.py`](unrolling_class.py) and
> [`certificate_unrolling.py`](certificate_unrolling.py) later established that
> the certificates' class is **`(1,-1)`**, not `(1,0)`, so the object this file
> reasons about is not the object the certificates instantiate. The reasoning
> about what a terminated search would need in order to become a proof is
> unaffected and is still the useful part; the class label is wrong.
>
> **Nothing in this repository depends on this file.** The claim is a *negative*
> result about one cover class, and an independent review noted it is
> logically unnecessary for everything that is settled. It is not cited by any
> gate. It is kept because [`DENSITY.md`](DENSITY.md) points at it as the record
> of how hard the corresponding structure theorem is, and because deleting a
> superseded argument hides that it was made.

The repository records that the `(1,0)` unrolling is uncappable — no disk cap
completes it at any of its 16 short-meridian interfaces — and uses that to
retire the seam-insertion route and to explain why no published APG contains
such a seam. The 2026-09-01 independent review's verdict on that claim:

> A terminated search with no solutions can become a proof, but only after
> proving both finiteness and completeness.

Nothing about the 26 certificates depends on this. The claim is a *negative*
result about one cover class, and the reviewer notes it is "logically unnecessary
for Conjecture 10.2". It is written up here because the repository states it as
fact in three documents.

## First, the claim is about a different object than it says

`certificate_unrolling.py` shows that the class committed in
`periodic_strip.py` and labelled "the `(1,0)` unrolling" is, in the canonical
coordinates of `unrolling_class.py`, the class **`(p,q) = (-2,-1)`** — and that
the certificates are built from **`(1,-1)`**, a different class. So the claim to
prove is:

> The `(-2,-1)` cover of the `c = 3` alternating torus quotient admits no disk
> cap at any short-meridian interface.

Any rewrite has to start by re-running the search against that class, since the
label it was recorded under names neither.

## What a proof must contain

From the independent review, condensed:

1. **Scope and interface completeness.** Define a disk cap; say which vertices,
   edges and rotations may be added; define "short meridian"; fix the
   equivalence used between interfaces; and prove every allowed short-meridian
   interface is one of the enumerated cases. Sixteen searched cuts prove
   "none of these sixteen caps", not "the unrolling admits no cap".
2. **Finiteness.** A fixed boundary generally admits disk fillings with
   arbitrarily many interior vertices, so a depth-bounded enumeration proves
   nothing at all sizes. One of: an a priori bound on minimal cap size; a
   reducibility theorem; a boundary-state saturation argument; or an
   independently checkable UNSAT certificate for a finite encoding **plus** a
   proof the encoding covers every cap.
3. **Complete branching.** Every non-terminal partial cap must provably
   enumerate all possible next cells.
4. **Sound pruning.** Every rule extension-preserving: current versus forced
   final degree kept apart, partial facial lengths monotone, symmetry rejection
   keeping one representative per class, memoised states proven to have
   identical completions, curvature or Euler pruning including boundary terms,
   and no time limit or unproved size cap in the argument.

## The easiest finiteness route is closed, and here is the computation

If every vertex type admissible in a `(3,4,5)`-APG were positively curved,
Gauss-Bonnet would bound any disk's interior and requirement 2 would be free.
[`curvature.py`](curvature.py) enumerates all of them —
`k(v) = 1 - deg(v)/2 + Σ_{f ∋ v} 1/|f|`, degrees and face sizes in `{3,4,5}`,
cyclically adjacent faces of different size:

| | |
| --- | --- |
| admissible vertex types | **54** |
| negatively curved | **36** (including degree-4 types) |
| flat | **0** |
| range | `-4/15` at degree 5 meeting `(3,4,5,4,5)` … `+17/60` at degree 3 meeting `(3,4,5)` |

So a cap can absorb arbitrarily much negative curvature and **there is no size
bound from curvature**. Requirement 2 has to be met by boundary-state
saturation or by a checkable UNSAT certificate; the cheap route does not exist.
That is worth knowing before anyone re-runs the search hoping a bigger node cap
will settle it.

## What Gauss-Bonnet does give, and it is worth having

`Σ k(v) = 2` with every term at most `17/60` forces **at least
`⌈2 / (17/60)⌉ = 8` positively curved vertices** in any `(3,4,5)`-APG.

Both facts are checked on all 26 certificates in exact rational arithmetic,
computed from the rotation system alone and sharing no code with either
verifier ([`test_curvature.py`](test_curvature.py)): `Σ k = 2` exactly at every
order, between 28 and 51 positively curved vertices, no flat vertex, and every
curvature inside `[-4/15, 17/60]`. That is an independent structural
verification of the certificates as a side effect.

## The state signature a saturation argument needs

Also from the reviewer — the interface signature must record at least: the cyclic
order of boundary darts and corners; the current *and* target degree of each
boundary vertex; which open facial traces connect to which; the accumulated
lengths of those traces; the sizes of faces on the already-completed side of
each seam edge; the adjacency and identification information needed to prevent
loops and parallel edges; and the boundary connectivity partition.

"The same number of deficient vertices and missing edges" is not a state. That
is the same gap `PUMPING_LEMMA_STATUS.md` records on the positive side: a
degree deficit determines neither the pairing of open traces nor their lengths.

## Status

**Open.** The claim is not retracted — an exhaustive search over 16 interfaces
returning zero solutions is real evidence, and the repository's wording has been
weakened to "as far as the committed evidence goes". What does not exist is a
proof, a completeness identity asserted in the run (the project rule (6)), a
committed terminal run report, or a re-run against the class the claim is
actually about.
