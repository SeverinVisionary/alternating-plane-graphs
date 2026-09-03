# Witnesses built by disk surgery on graphs already in this repository

> **The `.plc` bytes referred to below are not in this repository.** No licence
> statement was found at their source, so they are not redistributed; each graph
> is re-expressed in this repository's own `apg-plane-rotation-v1` format, and
> the digest of every original is kept in
> [`../UPSTREAM_PROVENANCE.json`](../UPSTREAM_PROVENANCE.json). Byte-level checks
> described here skip unless the corpus is restored alongside this tree. See
> [`../../NOTICE.md`](../../NOTICE.md).

These close orders 37 and 38, the last two `(3,4,5)` orders Conjecture 10.3 was
missing. They are **first-party constructions**: nothing was downloaded for
them. The method is to cut a disk out of a stored `(3,4,5)`-APG — the star of a
vertex, an edge, or a face — let the boundary degrees float subject to their
outside neighbours, and refill the disk with a fixed number of new vertices
under the Definition 3.1 constraints.

| file | order | built from | refilled with |
| --- | --- | --- | --- |
| `APG37_3conn.json` | 37 | `census_sources/60_36-36.plc` minus vertex 16 | 2 vertices |
| `APG38_3conn.json` | 38 | `census_sources/51_34-34.plc` minus the star of an edge | 4 vertices |
| `APG38_3conn_b.json` | 38 | `census_sources/29_27-27.plc` minus a face star | — |

Found 2026-09-01 by an independent reviewer. Verified here independently of that leg:
`verify.py` and `verify_darts.py` both PASS at the stated order, `fast_apg_check`
and `general_apg.is_apg` both accept, and `connectivity.is_three_connected` is
true by brute force with `separating_pairs_on_faces` empty. Gated by
[`test_surgery_witnesses.py`](../../test_surgery_witnesses.py).

The two order-38 graphs are not isomorphic to each other.
