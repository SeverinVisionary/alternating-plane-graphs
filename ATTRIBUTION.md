# What is theirs, what is re-verified, what is new

A paper settling someone else's conjectures owes the reader one place where the
boundary is drawn. This is that place. The distinction is spread across
[`PRIOR_ART.md`](PRIOR_ART.md), [`THEOREM_3_2_STATUS.md`](THEOREM_3_2_STATUS.md),
[`CONJECTURE_10_3.md`](CONJECTURE_10_3.md) and six `PROVENANCE.md` files, each
scrupulous on its own; collected here it can be checked in one reading.

Source: Ingo Althofer, Jan Kristian Haugland, Karl Scherer, Frank Schneider and
Nico Van Cleemput, *Alternating plane graphs*, Ars Mathematica Contemporanea
**8** (2015) 337-363, DOI [`10.26493/1855-3974.584.09a`](https://doi.org/10.26493/1855-3974.584.09a).

## Theirs

Every one of these is used here as given, cited and restated, and none is
re-proved. A few statements -- the conjectures themselves -- are quoted
verbatim, in quotation marks and attributed:

* **The problems.** All four open items in Section 10, including the three
  settled here. The conjecture numbering is theirs.
* **The definitions.** Definition 2.1 (alternating plane graph), Definition 3.1
  (the `(3,4,5)` subclass), Definition 3.4 (`X,Y`-APG).
* **Theorem 3.2** -- `v3 = f3`, `v4 = f4`, `v5 = f5`, whence `v5 = v3 - 4`,
  `E = 2V - 2` and `F = V`. This repository derived the consequences without it
  and was missing the theorem itself;
  [`THEOREM_3_2_STATUS.md`](THEOREM_3_2_STATUS.md) records that.
* **Lemma 2.2**, that the dual of a 3-edge-connected APG is an APG.
* **Theorem 8.1** and the Section-8 arithmetic `18a + 19b + 20c + 21d + 3`.
* **Lemma 9.2, Lemma 9.4 and equations (9.3)-(9.5).** The proof of Conjecture
  10.1 here is (9.5) applied to a class the paper never connected it to; the
  inequality is theirs.
* **The published witnesses**, as planar_code, at orders 17, 20, 21, 22, 23, 25,
  26-36 and 42, together with the search seeds. Decoded and re-verified here,
  never treated as correct on authority.
* **The exhaustive counts**: that there are exactly five alternating plane
  graphs on 19 vertices, and that there is no `(3,4,5)`-APG on 18 or 19
  vertices. Both are used as context, and neither is load-bearing -- see
  "taken on trust" in [`CONJECTURE_10_3.md`](CONJECTURE_10_3.md).
* **Table 5 and Figures 8-9**, the weak `2,k`-APGs for `k <= 10`, which are the
  calibration target for the Conjecture 10.1 chain.

## Re-verified here, not new

* Every published witness above is decoded from the original bytes by
  [`import_planar_code.py`](import_planar_code.py) and re-checked by three
  independently written verifiers. Digests of the upstream bytes are in the
  neighbouring `PROVENANCE.md` and in
  [`certificates/MANIFEST.sha256`](certificates/MANIFEST.sha256).
* The Section-8 closures at orders 21-24 and 39-45 are rebuilt here from
  `results/blocks/` by [`section8_witnesses.py`](section8_witnesses.py). At 21,
  22 and 23 a published witness also exists, so those three orders have two
  independent sources; the closure construction is ours, the orders are not new.
* The consequences of Theorem 3.2 were derived here before the theorem was read
  at source. They are not an independent proof of it and are not presented as
  one.

## New here

* **The periodic capping lemma, proved.**
  [`pumping_splice.py`](pumping_splice.py) extracts the two caps as explicit
  patches and splices periods, so one certificate per residue class generates a
  `(3,4,5)`-APG at order 48 and every order from 50 up. This is an independent
  construction of Theorem 8.1 and of 23 of the 26 target orders; 46, 47 and 49
  rest on their certificates alone.
* **The 26 certificates** at orders 46-56, 67-74, 88-92, 109 and 110 -- the
  previously open orders of Conjecture 10.2.
* **Conjecture 10.3 settled**: a verified 3-connected witness at every order
  from 19 up, with [`witness_coverage.py`](witness_coverage.py) deriving the
  covered set from files rather than asserting it, and each source gated as
  load-bearing.
* **Orders 37 and 38 by disk surgery**, which the Section-8 arithmetic cannot
  reach and the paper's own coverage list skips.
* **The order-46 counterexample.** A `(3,4,5)`-APG with a separating pair,
  refuting "every `(3,4,5)`-APG is 3-connected" -- a claim this repository
  asserted and had to withdraw. See
  [`THREE_CONNECTIVITY_CLAIM.md`](THREE_CONNECTIVITY_CLAIM.md).
* **The spliced family is 3-connected at every order**, proved in
  [`family_connectivity.py`](family_connectivity.py), not sampled.
* **Conjecture 10.1**, both halves reduced to one symmetric per-edge
  inequality, and then freed of the (C2) reading by a counting argument that
  tethers the only edges able to exceed the budget to bridges, at most two per
  bridge, against a deficit of `1/6` each. The inequality is the paper's; the
  reduction, the application to the strong class, and the count are new.
* **The parity lemma** of [`bridge_lemma.py`](bridge_lemma.py): in a class with
  exactly two face sizes, `deg(v)` minus the number of bridges at `v` is even at
  every vertex. Classical in substance -- it is "face-2-colourable iff
  Eulerian" -- but stated so bridges are permitted rather than assumed away,
  which is what the (C2) question needs.
* **The verification apparatus**: three independent decision procedures,
  [`export_planar_code.py`](export_planar_code.py), the format specification
  with an executable reference reader, and 1253 gates.

## How it was produced

Everything in the "New here" list was produced with substantial AI assistance,
and the (C2) removal was supplied by an AI reviewer rather than by the author.
No AI system is an author or a contributor. The extent is stated in
[`AI_DISCLOSURE.md`](AI_DISCLOSURE.md); what review changed, including the
claims that were withdrawn, is in [`REVIEW.md`](REVIEW.md).

## Not claimed

The asymptotic density problem of Section 10 is untouched. Nothing here bears on
it; [`DENSITY.md`](DENSITY.md) quotes the problem from p. 362 and says why the
methods used here do not reach it.
