# For reviewers

**Nothing in this repository has been checked by a human.** Four programs agree
that every certificate obeys the definition, three independent review passes
went over the arguments, and the whole thing is archived with a DOI — and not
one mathematician has read it. That is the gap this file exists to close.

If you are willing to spend time on it, this is what to spend it on. The list is
ordered by *how much of the result collapses if the item is wrong*, not by what
is convenient. **Items 1 to 3 need no computer at all**, and item 2 alone is
worth more than everything else here. Roughly one focused day for all of it; two
hours for the part that matters most.

Findings, including "this is wrong", are welcome at the repository's issues, or
to the author directly. A finding that costs this work a claim is the most
useful thing you could send.

---

## Before anything: what running the suite does and does not establish

```sh
make deps          # pytest, nothing else
make verify-fast   # 2m19s measured
make verify        # 7m52s measured -> 1295 passed, 13 skipped
                   #   ...but ~2h if `python-sat` is installed: two gates in
                   #   test_exact_map_cnf.py then run 27 fixtures through the
                   #   SAT encoding and every verifier instead of skipping.
```

Green means **the code accepts the files**. It does not touch:

- the Conjecture 10.1 proof (item 2) — a proof, not a computation;
- the periodic capping lemma (item 3) — a statement about *all* `d`;
- `family_connectivity`'s 3-connectivity claim for the whole spliced family;
- whether the verifiers encode Definition 2.1 correctly (item 1).

Those four carry every infinite claim in the deposit. All are pencil-and-paper.

---

## 1. Does the code encode Definition 2.1? (~30 min, no computer)

**This gates everything.** Four decision procedures were written for this
deposit, but by one person against one reading of the source definition.
Independence of *implementation* is not independence of *interpretation*: a
misreading would be confirmed unanimously by all four.

Read Definition 2.1 (Althöfer et al., *Ars Math. Contemp.* **8** (2015), **p. 339**
— not p. 338) against `verify.py::verify_certificate`, lines 122–265.

| Definition 2.1 | in `verify.py` |
| --- | --- |
| no adjacent vertices of equal degree | `degrees[u] == degrees[v]` over every edge → fail |
| no adjacent faces of equal size | `face_sizes[left] == face_sizes[right]` → fail |
| every degree ≥ 3 | degree must lie in `{3,4,5}` (Definition 3.1, stricter — correct here) |
| every face size ≥ 3 | size must lie in `{3,4,5}` |
| the exterior face counts too | faces are orbits on the sphere; `V − E + F = 2` asserted |

**Two known divergences to confirm rather than discover:**

- **Bridges.** At a bridge the same face lies on both sides, so `left == right`
  and the size test fails trivially — the *strict* reading. That matches the
  paper, which states on p. 339 that an APG is "always at least
  2-edge-connected, since plane graph with edge connectivity 1 contains a face
  that is adjacent to itself." Note this branch is unreachable inside the
  (3,4,5) class: a bridge forces a face of size ≥ 8, which the size gate rejects
  first.
- **Simple facial walks.** All four verifiers additionally reject any facial
  walk that repeats a vertex. **Definition 2.1 does not require this**, so they
  test a strictly narrower class than the paper defines — effectively demanding
  2-connectivity where the paper claims only 2-edge-connectivity, and the paper
  says (p. 362) some of its Section-7 APGs are not 2-connected.
  As of v1.0.2 all four files document this at the check site; before that only
  `general_apg.is_apg` did.
  *Is it harmful?* Argued no, because it is conservative in the direction each
  result needs — 10.2 and 10.3 are existence claims, so a stricter test can only
  reject a good witness, never accept a bad one; and 10.1 is a proof that does
  not use the verifiers. **Confirm that argument; it is the reconciliation the
  whole artifact rests on.**

---

## 2. The Conjecture 10.1 proof (~1–2 h, no computer)

[`CONJECTURE_10_1.md`](CONJECTURE_10_1.md), and §4–§5 of `paper/apg.pdf`. Roughly two pages.

A per-edge identity plus Euler forces some edge to contribute more than 1;
both halves rule that out. Check in particular:

- **(C1)**, that face size counts edge-side incidences with multiplicity, so a
  bridge counts twice. The paper never defines "size"; this reading is inferred
  from its (3.1) and (9.2), both asserting `Σ s·f_s = 2e`. *If (C1) is wrong the
  proof does not survive.*
- The bridge case in `bridge_lemma.py`: the parity lemma
  `deg(v) − bridges_at(v)` even, the tether `P ≤ 2B`, and the final
  `2 = Σx ≤ 2B/24 − B/6 = −B/12 < 0`.
- The slack is claimed measured, not asserted: closes at bridge-face bound 7,
  fails at 6.

**This is the deposit's one genuine theorem and the cheapest thing to check.
If you only have two hours, spend them here.**

---

## 3. The two infinite claims (~2–3 h, no computer)

Neither is machine-checkable in principle; both are proofs about all orders.

- **Periodic capping lemma** ([`PUMPING_LEMMA_STATUS.md`](PUMPING_LEMMA_STATUS.md)). "cap + `t` periods +
  cap is a (3,4,5)-APG", for every `d ≥ −(|D|−1)`. The argument is *locality*: a
  facial walk spans at most three consecutive copies, so every window around a
  fresh copy is a translate of a window of `TARGET_n`, hence every face of the
  splice is a translated face of the original. Check the span bound and that
  each Definition 3.1 condition really is local.
- **`family_connectivity.py`**, that the spliced family is 3-connected at
  *every* order it produces — this is what makes Conjecture 10.3's tail a
  theorem rather than a finite sweep.

---

## 4. The coverage arithmetic — and what is inherited (~45 min)

`test_conjecture_coverage.py` is readable set arithmetic. As of **v1.0.2** it
measures the union twice, and the second measurement is the honest headline.

**Union as the conjecture is classically closed** — note whose results these are:

| range | established by |
| --- | --- |
| n in [20, 42] | the **2015 paper's** heuristic search |
| Section-8 intervals | the **2015 paper's** construction |
| n >= 111 | the **2015 paper's** Theorem 8.1 |
| 46-56, 67-74, 88-92, 109, 110 | **this deposit's** 26 certificates |

**Union using only what this deposit establishes** — certificates plus the
periodic capping lemma, no Theorem 8.1:

- closes **every order n >= 46**;
- leaves orders **20 to 45** inherited from the paper, not re-established here.

Gated by `test_the_deposit_alone_covers_every_order_from_46_up` and
`test_orders_20_to_45_are_exactly_what_is_inherited`, with a control showing the
lemma is load-bearing: without it, the certificates and the paper's finite
constructions stop exactly at 110.

**The qualification to check.** Per the manuscript's deletion remark
(`rem:deletion`), the family's floor orders and **58, 61, 64** rest on
machine-verified splices rather than on the capping lemma *as stated* — its
locality argument is written for insertion, and the hypothesis `|D| >= 5` does
not reach those orders that way. Still this deposit's own evidence rather than
the paper's, so the `n >= 46` claim stands, but it is theorem **plus** verified
computation, not the theorem alone. **Satisfy yourself that those five orders
are genuinely covered**; it is the softest joint in the coverage argument.

For **Conjecture 10.3**, [`CONJECTURE_10_3.md`](CONJECTURE_10_3.md) has the per-order source table and
`witness_coverage.verified_orders()` derives the checked set from files and
run-time constructions rather than asserting it, and `verified_residue()` —
what is still open here — begins at **57**. The older `residue()` returns `[]`
but must not be read as evidence: its family term is arithmetic over
`FAMILY_FLOORS`, reads no file, and claims every order from 48 up on the
strength of an induction withdrawn on 2026-09-05. Order 19 is the interesting case — no (3,4,5)-APG
exists on 19 vertices, so its five witnesses are *general* APGs that all three
(3,4,5)-verifiers correctly reject; they are checked by the fourth,
`general_apg.is_apg` (`test_conjecture_10_3.py:38-45`).

---

## 5. Spot-check one certificate by hand (~1 h, optional but convincing)

`certificates/order19/ORDER19_05_19-19.json` — 19 vertices, 72 dart incidences,
1.4 KB of plain JSON, each row a clockwise neighbour rotation. Trace the faces
with `phi = sigma^-1 ∘ alpha`, then check degrees, face sizes and both
alternation conditions. Tedious, but it means the claim is falsifiable with
pencil and paper and does not require trusting any code.

---

## What is already known to be wrong, and was withdrawn

[`REVIEW.md`](REVIEW.md) records three claims made during this work that were false and
retracted, plus one certificate misidentified as not 3-connected. They are kept
at the files that made them rather than deleted. You are not expected to
rediscover these; if you find a *fourth*, that is the finding.

---

## Known gaps, stated so you need not hunt for them

- No human has previously checked any of this. There has been no peer review.
- The manuscript (`paper/apg.pdf`, 13 pp.) is a draft.
- Conjecture 10.2 inherits orders 20-45 from the source paper (item 4).
- 13 of 1308 gates are skipped: 11 need a third-party corpus that is not
  redistributed (no licence found at source), 1 needs optional `python-sat`,
  1 follows from the first.
- AI assistance was substantial, including the step that removed the (C2)
  dependence from Conjecture 10.1. See [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md). No AI system is an
  author.
