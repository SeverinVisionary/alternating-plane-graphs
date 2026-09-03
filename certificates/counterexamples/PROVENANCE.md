# Counterexamples

Objects here are **valid `(3,4,5)`-APGs that fail a property something else in
this directory claimed or hoped for**. They are kept apart from
`certificates/targets/` and from the witness scan in
[`witness_coverage.py`](../../witness_coverage.py), which counts only 3-connected
witnesses, so that nothing here is ever mistaken for a Conjecture 10.3 witness.

## `APG46_two_cut.json`

A `(3,4,5)`-alternating plane graph on 46 vertices that is **not 3-connected**.
It refutes the claim in [`THREE_CONNECTIVITY_CLAIM.md`](../../THREE_CONNECTIVITY_CLAIM.md).

| field | value |
| --- | --- |
| order | 46 (edges 90, faces 46, `v3=f3=18`, `v4=f4=14`, `v5=f5=14`) |
| separating pair | `{1, 2}` — non-adjacent, both of degree 5 |
| components of `G - {1,2}` | two, of 22 vertices each |
| faces carrying both | the pentagons `1,3,2,7,6` and `1,8,2,5,4` |
| SHA-256 | `78fa8c2f3133f69810afca36fb69d9c0a20249914293e818e8a47d62e3b8e500` |

Found 2026-09-01 by an independent reviewer consulted on the claim, using a disk-filling
patch search over the two sides of a 2-cut interface. Verified here
independently of that search and of the reviewer that produced it: `verify.py` and
`verify_darts.py` both PASS at order 46, `fast_apg_check.accepts_certificate` is
true, and `connectivity.is_three_connected` is false by brute force over all
`46 choose 2` pairs, with `separating_pairs_on_faces` returning exactly
`[(1, 2)]`.

It is **not isomorphic to `TARGET_46`** — that one is 3-connected — so it is also
a second, independent `(3,4,5)`-APG at order 46.

The same leg reports, from an exhaustive version of that search, that 46 is the
*smallest* order admitting a non-3-connected `(3,4,5)`-APG. That minimality
claim is **not verified here** and is recorded as the reviewer's, not this
repository's: it depends on the completeness of a search whose enumeration was
validated empirically, on the order-17 graphs, rather than proved.
