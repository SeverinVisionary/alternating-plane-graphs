**A Pro-tier breadth review found a coverage gate computing the right kind of
answer from the wrong predicate, a "verified" set that counted availability
rather than verification, and three mathematical scope errors. The exposition
was also reproportioned after a separate readability pass.**

### The capping theorem's reach was measured against the wrong test

`test_conjecture_coverage.py` derived the theorem's insertion reach from the set
of spliceable orders. The theorem's hypothesis is a **deep block of at least
five copies**, which is a different and stronger condition. Measured, five of the
twenty spliceable orders — 48, 51, 53, 54, 56 — have deep blocks of only 1, 2,
2, 3 and 3 copies and are not eligible seeds at all.

With the hypothesis applied, eligible seeds begin at 67, 68 and 69, insertion
reaches nothing below 70, and **all ten orders 57–66 lie outside the theorem**.
None carries a stored certificate; they rest on the verified floor-upwards
splices instead.

This set has now been named wrongly twice. The previous correction, `58, 61,
64`, was defended on the grounds that it was *computed rather than asserted* —
and it was, from the wrong eligibility predicate. Deriving a number does not
make it right if the predicate is wrong.

### `verified_orders()` counted recipes, not verified outputs

`section8_orders()` returned the keys of `section8_witnesses.RECIPES`. Breaking
the builder would not have removed an order from a set named *verified*. It now
constructs each closure and runs it through the general APG check and the
3-connectivity check, returning only what survives. `witness_coverage.main()`
also still printed the withdrawn `residue()` as its headline.

### Three scope errors in the mathematics

* **The per-edge identity was false as stated.** Given for an unrestricted plane
  graph, it fails with isolated vertices: a triangle plus an isolated vertex has
  `sum c(a) = 5` against `v + f = 6`. Minimum degree 3 excludes this, so
  Conjecture 10.1 is untouched, but the hypothesis is now stated.
* **"(C2) is a consequence of Definition 2.1" is false read generally.** Three
  copies of a (3,4,5)-APG joined by two exterior bridges at a degree-5 vertex of
  each is a weak-reading alternating plane graph *with bridges*. It has neither
  exactly two degrees nor exactly two face sizes, so the theorem stands; the
  commentary claimed more than the theorem. The construction is now in the text.
* **Orders 37 and 38 were misattributed** to a gap in the source paper. Its
  heuristic search covers every order from 20 to 42; only its Section-8
  *construction* misses them.

### Exposition, after a separate readability pass

A symbol collision (`B` was both the bridge count and a component), the charging
map `P <= 2B` hidden inside a "Hence" when it is the substantive step, a
roadmap paragraph before the weak-reading proof, and (C1) spending five lines on
a 2-connectivity tangent while the documentary basis the proof rests on got one
clause. All reproportioned.

### Cross-document drift

The **main manuscript's abstract still said "We settle three"** — the BAMS
variant had been corrected two days earlier and the primary file had not. Also:
the bibliography named artifact version 1.0.2 while data availability named
1.0.4; `PUMPING_LEMMA_STATUS.md` still described the circular span argument the
manuscript had already replaced; "each certificate is accepted by every
verifier" is false for the order-19 general APGs; and the reviewer guide's claim
that the infinite assertions are "not machine-checkable in principle" is wrong —
nothing here checks them, which is a different statement.

### Recorded, not fixed

The insertion proof's window claim is still not fully discharged, and the
deletion statement disagrees with the implementation's cut rule. Both are in
`REVIEW.md` under "Not yet acted on".
