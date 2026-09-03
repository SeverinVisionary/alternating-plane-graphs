# Public source bytes for the structural census

> **The `.plc` bytes referred to below are not in this repository.** No licence
> statement was found at their source, so they are not redistributed; each graph
> is re-expressed in this repository's own `apg-plane-rotation-v1` format, and
> the digest of every original is kept in
> [`../UPSTREAM_PROVENANCE.json`](../UPSTREAM_PROVENANCE.json). Byte-level checks
> described here skip unless the corpus is restored alongside this tree. See
> [`../../NOTICE.md`](../../NOTICE.md).

The nineteen `.plc` files in this directory were retrieved on 2026-08-29 from
the public URLs listed in
[`results/logs/milestone3_alternative_order_opening_scan.json`](../../results/logs/milestone3_alternative_order_opening_scan.json).
`source_census.py` checks every byte against that manifest before decoding it.

The files are a frozen input corpus, not newly discovered constructions. The
census verifies the closed rotation systems and exhausts the legal disjoint
closure-fan pairs for each source; a zero strict-opening count is only a
bounded result for this corpus and is not a nonexistence theorem.
