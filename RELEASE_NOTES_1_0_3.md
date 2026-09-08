**A theorem was withdrawn, and the gate that should have caught it was found to
be measuring nothing.**

### Conjecture 10.3 is no longer claimed as settled

Adversarial review found the induction in `family_connectivity.py` — carrying
3-connectivity through the spliced family — unestablished, with three distinct
defects. The manuscript now claims only the **54 orders with explicit
witnesses**: 17, 19–56, 67–74, 88–92, 109 and 110. Orders 57–66, 75–87, 93–108
and every n ≥ 111 are open here.

### The coverage gate was asserting the withdrawn theorem

`witness_coverage.residue()` unions in `family_orders()`, which is
`range(floor, 400, 3)` over a hard-coded tuple and reads no file. So
`residue() == []` held whether or not any witness existed from order 48 up, and
three gates asserted exactly that. Delete every stored witness above 47 and the
old function notices **one** missing order out of 328.

`verified_orders()` and `verified_residue()` now measure only checked evidence;
the three gates assert those, and a control pins the old function's blindness.

Three further gates were reading an empty directory — they globbed `*.plc` in a
corpus re-expressed as `.json` back in 1.0.0, and one had no count assertion and
was passing vacuously.

### The deposit is retitled

*"Settling Conjectures 10.1, 10.2 and 10.3"* is not what this establishes. It is
now **"Alternating plane graphs: settling Conjectures 10.1 and 10.2, with
witnesses for 10.3"**.

### Smaller corrections

- The 2026-09-05 face-span correction was itself wrong. The measured span is
  **2** — three consecutive copies, the original wording — not 3 and four. The
  gate's `<= 3` was a slack threshold, now `<= 2`. The manuscript no longer
  presents the bound as derived from face size and edge offset, which does not
  follow.
- *"Each gate is paired with a control that must fail"* is now *"most"*, with
  the exceptions named: of the 17 uncontrolled sites, six are the Theorem 3.2
  identities, two are a restriction the definition does not impose, and the two
  alternation clauses are each controlled in the *other* verifier.
- *"No third-party graph data is redistributed"* was false as written. No
  third-party **files** are, but the graphs are the corpus's; MIT is now
  explicitly scoped to the code and the original work.
- Counts and timings: **1308 gates, 1295 passed, 13 skipped**, 7m52s — or about
  two hours where the optional `python-sat` is installed.
- Prior art re-checked 2026-09-06 across OpenAlex, Semantic Scholar, the arXiv
  and the authors' own page: no published or deposited settlement of any of the
  three conjectures. Recorded as a dated refresh in `PRIOR_ART.md`.
