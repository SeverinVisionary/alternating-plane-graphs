# `(3,4,5)`-alternating plane graphs

> **Start with [`ARTIFACT.md`](ARTIFACT.md)** — what is settled, how to check it,
> and what is deliberately not load-bearing. [`REVIEW.md`](REVIEW.md) records
> what independent review changed, including three claims made here that were
> false and were withdrawn.
>
> **This work was produced with substantial AI assistance, including one of its
> proof steps.** See [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md).
>
> [`ZENODO.md`](ZENODO.md) is a one-page formatted summary of the whole deposit.
>
> **Archived:** DOI [10.5281/zenodo.22269200](https://doi.org/10.5281/zenodo.22269200) (concept — always the latest version) ·
> [landing page](https://severinvisionary.github.io/alternating-plane-graphs/)

## Re-verify before trusting any of it

```sh
make deps          # pytest, and nothing else
make verify-fast   # the load-bearing gates, about a minute
make verify        # everything
```

## Where the paper's open problems stand

Section 10 of the source paper poses four items. Three are now settled here.

| item | status |
| --- | --- |
| **Conjecture 10.1** — no `2,Y`- and no `X,2`-APG | **proved**, and no longer conditional on (C2) ([`CONJECTURE_10_1.md`](CONJECTURE_10_1.md)) |
| asymptotic degree distribution — the density of `v4/v3` on `[1, 1.5]` | **open**, and out of reach of these methods ([`DENSITY.md`](DENSITY.md)) |
| **Conjecture 10.2** — `(3,4,5)`-APGs for all `n >= 20` | **settled** — 26 certificates plus a proved infinite family, closing every `n >= 46` here; `20..45` is the source paper's |
| **Conjecture 10.3** — 3-connected APG for all `n >= 19` | **settled** ([`CONJECTURE_10_3.md`](CONJECTURE_10_3.md)) |

## Status

**All 26 target orders now carry certificates accepted by three checkers**
(2026-09-01). They are in [`certificates/targets/`](certificates/targets/) with
a SHA-256 manifest and are gated by
[`test_target_certificates.py`](test_target_certificates.py) (115 checks). The
construction caps an unrolling of the periodic `c = 3` alternating torus
quotient; [`certificate_unrolling.py`](certificate_unrolling.py) identifies the
class as `(1,-1)`, not the `(2,3)` the search notes claimed. See
[`SEARCH_STATUS.md`](SEARCH_STATUS.md).

**The pumping lemma is proved** (2026-09-01).
[`pumping_splice.py`](pumping_splice.py) extracts the two caps as explicit
patches and splices periods into the middle, so a single certificate generates
a `(3,4,5)`-APG at every order `n + 3d` from an explicit floor upwards — orders
48, 50, 52 by residue class, hence **every order `n >= 50`, plus 48**. Splicing
`TARGET_110` down twenty periods reproduces `TARGET_50` up to isomorphism, and
`TARGET_92` down fourteen gives the same graph, so the caps are canonical
rather than one alignment's artefact. That is an independent construction of
the paper's Theorem 8.1 and of 23 of the 26 target orders; 46, 47 and 49 rest
on their certificates alone. Proof and its two machine-checked hypotheses:
[`PUMPING_LEMMA_STATUS.md`](PUMPING_LEMMA_STATUS.md).

**Conjecture 10.3 is settled** (2026-09-01). *"For any `n >= 19` there exists a
3-connected alternating plane graph on `n` vertices"* — every order from 19 up
now has a verified 3-connected witness here, and `witness_coverage.residue()`,
which derives the covered set from files and constructions rather than asserting
it, returns empty. Order 19 needed a general APG (no `(3,4,5)`-APG exists there);
all five 19-vertex APGs turn out to be 3-connected. Orders 37 and 38, out of
reach of the Section-8 arithmetic, fell to disk surgery on graphs already held.
The tail is carried by a theorem, not a sweep:
[`family_connectivity.py`](family_connectivity.py) proves the spliced family is
3-connected at every order it produces. See
[`CONJECTURE_10_3.md`](CONJECTURE_10_3.md).

**The obvious shortcut is false.** Not every `(3,4,5)`-APG is 3-connected —
there is one on 46 vertices with a separating pair
([`THREE_CONNECTIVITY_CLAIM.md`](THREE_CONNECTIVITY_CLAIM.md)). Nothing above
depends on it; every witness was checked individually.

**What "three checkers" does and does not mean.** `verify.py` turns to the
predecessor dart and `verify_darts.py` to the successor; that was recorded here
as evidence of independence and it is the opposite. The two traversals produce
the *same face partition*, each face traced backwards relative to the other, so
they cannot disagree about face sizes, repetitions or adjacency on any input --
`test_the_two_verifiers_are_not_independent_evidence` asserts the identity at
all 26 orders. `fast_apg_check.py` is a third implementation over darts and an
involution rather than adjacency rows. Three implementations catch three ways
of coding the check wrong; none of them catches a shared misreading of
Definition 2.1. The genuinely external corroboration is the 2026-09-01 review
panel, whose legs re-derived all 26 with their own reconstructions -- one by
NetworkX, one by an exact-rational Tutte embedding that found zero edge
crossings. See [`REVIEW.md`](REVIEW.md).

**The prior-art search found nothing that settles these orders** (2026-09-01).
Every source was checked directly: the 2015 paper, Althöfer's maintained table
(88 entries, orders 4–44, **empty** intersection with the 26 target orders),
DataCite for `"alternating plane graph"` (**0 results**), Crossref, OpenAlex and
Semantic Scholar (two citing works, neither settling anything), and the authors'
generator repository (last pushed 2013-11-07). Evidence table in
[`PRIOR_ART.md`](PRIOR_ART.md).

**Not covered**, stated rather than glossed: Google Scholar (bot-gated), the
House of Graphs user-upload database (its search API needs credentials), and
author correspondence — the last being the difference between "not found in the
public record" and "confirmed new".

**Theorem 3.2 is settled at the source.** It is on p. 340 of the paper with a
complete proof: *"If `G` is a (3,4,5)-alternating plane graph, then `v3 = f3`,
`v4 = f4` and `v5 = f5`."* The derivation done here before the paper was read
reproduces the proof's own five-case table; the step it was missing is the
(5,5)-combination count. So the identities both verifiers impose are the
paper's, and every nonexistence-shaped result in this repository is about the
full class of Definition 3.1 rather than a proper subclass. See
[`THEOREM_3_2_STATUS.md`](THEOREM_3_2_STATUS.md).

**The Definition 2.1 face-size risk is retired unconditionally.** Both verifiers
reject any face repeating a vertex, so every certificate face is a simple cycle,
on which every candidate reading of "size" gives the same integer. Argument in
[`PRIOR_ART.md`](PRIOR_ART.md).

**Historical framing, kept for provenance.** What follows described the target
while it was an open search; it is superseded by the status above, and left in
place because the prior-art argument it records is still the evidence base. The
dated public-record audit in [`PRIOR_ART.md`](PRIOR_ART.md) located no published
or publicly deposited construction for the 26 orders

```text
46-56, 67-74, 88-92, 109, 110.
```

The 2015 paper constructs all other orders at least 20 and proves existence for
every order at least 111. One exact plane-map witness at each order above would
therefore close Conjecture 10.2. A failed or timed-out search is not evidence of
nonexistence.

## Certificate contract

A result certificate is a deterministic JSON plane rotation system. The cyclic
order of every neighbor list is part of the witness; an abstract graph encoding
such as graph6 is insufficient.

The independent verifier reconstructs faces from the rotation system and must
check, without trusting annotations supplied by the search:

- a connected simple graph embedded on the sphere (`V - E + F = 2`);
- every vertex degree and every face size is in `{3,4,5}`;
- the endpoints of every edge have different degrees;
- the two faces incident with every edge have different sizes; and
- the certificate's claimed order.

For order `n`, every valid witness also has `E = 2n - 2`, `F = n`, and

```text
v3 = f3 = r
v5 = f5 = r - 4
v4 = f4 = n - 2r + 4.
```

Those identities are predicted-object checks, not substitutes for reconstructing
the embedding.

## Construction program

The first lane extends the two-hexagon block construction in Section 8 of the
paper. Joining blocks of orders `b1,...,bk` identifies three vertices at each
join and produces a closed APG of order

```text
3 + sum(bi - 3).
```

The published blocks have orders `21,22,23,24`. If exact compatible blocks can
be found at orders `25,29,34`, their increments `22,26,31`, together with the
published increments `18,19,20,21`, represent every one of the 26 targets.
[`block_arithmetic.py`](block_arithmetic.py) freezes this reduction and prints a
deterministic representation for every target.

That triple is not unique. There are 11 three-order extensions within block
orders 25 through 36 that cover the same target set; for example, `(26,29,33)`
avoids order 25. The arithmetic module freezes the complete list so a difficult
priority order does not become an artificial bottleneck. A direct opening scan
of all 19 published `(3,4,5)` embeddings at the alternative orders 26 through
36 found no strict block, but that is only a scan of those public embeddings.

The active Boolean pilot instead uses the separately frozen conditional
`t=0` covering triple `(28,29,31)`. It is checked by
`boolean_primary_t0_target_representations()` rather than being inferred from
the historical `(25,29,34)` proposal. Neither triple is an existence claim:
an order enters a target construction only after its concrete strict block and
all certificate gates pass.

The cloud search therefore proceeds in this order:

1. recover, compose, close, and independently verify the published blocks;
2. search for compatible finite-use and portable blocks at the structurally
   admissible profiles;
3. compose any new blocks into all 26 target witnesses; and
4. use direct boundary-growth and local-surgery searches only for targets still
   unresolved.

[`blocks.py`](blocks.py) supplies an exact implementation of the first lane. It
recovers A-C from published rotation systems, validates strict socket blocks,
glues two blocks with the correct orientation reversal, and closes the remaining
hexagons. Its known-answer suite reproduces every ordered A-C pair. The published
order-25, order-29, and order-34 APGs do not expose compatible blocks by direct
fan opening; that bounded negative is only a seed-scan result, not nonexistence.

See [`CLOUD_JOB.md`](CLOUD_JOB.md) for the isolated-Linux execution contract.
Heavy enumeration and solver work was run on a separate Linux host, not on the
development machine.
The current Boolean exact-map dispatch is specified in
[`CLOUD_BOOL_MAP_JOB.md`](CLOUD_BOOL_MAP_JOB.md). It first proves the encoder
on both a closed published map and the A21 strict block, then searches the
finite-use `(25,11)` branch and portable `t=0` branches `(27,12)`, `(28,12)`,
`(29,12)`, `(31,12)`, and `(34,13)`. Both independent checkers are required
for every positive model. Its first isolated-cloud pilot certified both
controls but no target block; the audited dispositions and evidence boundary
are in [`SEARCH_STATUS.md`](SEARCH_STATUS.md) and
[`results/logs/boolean_cloud_pilot_4ab6dcb1_audit.json`](results/logs/boolean_cloud_pilot_4ab6dcb1_audit.json).
The strictly serial recovery is complete: the repaired source recorded bounded
`unknown` results for `(31,12)` and `(34,13)`, rather than a resource kill or a
mathematical negative. Its complete audit is
[`boolean_cloud_serial_recovery_d69d3863_audit.json`](results/logs/boolean_cloud_serial_recovery_d69d3863_audit.json).

The Boolean block encoder also has a representation-only complete socket
normal form: it labels both mandatory socket hexagons rather than searching
their interchangeable vertex and dart names. Its proof and published-block
positive control are in
[`BOOLEAN_SOCKET_CANONICALIZATION.md`](BOOLEAN_SOCKET_CANONICALIZATION.md).
It is now exercised by a separate source-pinned cloud control and target job:
[`CLOUD_BOOL_SOCKET_CANONICAL_JOB.md`](CLOUD_BOOL_SOCKET_CANONICAL_JOB.md).
That job runs the central portable primary triple `(28,12)`, `(29,12)`,
`(31,12)` strictly serially; it is still a positive-search protocol, not a
conclusion about target existence.

## Solver-core diagnosis and the pure-CNF lane

[`SOLVER_CORE_DIAGNOSIS.md`](SOLVER_CORE_DIAGNOSIS.md) explains why every
target profile in the recorded Cloud checkpoints returned Z3 `unknown` at its
bound, with a measurement rather than a reading: the exact-map lane states its
facial argument in Z3 *integer* arithmetic (784 integer variables and 344 442
AST nodes at block `(31,12)`), so three different structural strengthenings all
inherited the same solver-core bottleneck. It also prices the
exhaustive-generation route and closes it.

[`exact_map_cnf.py`](exact_map_cnf.py) is the pure-CNF alternative: `phi(d) = t`
is the matching literal `m[d, sigma(t)]` rather than an integer variable, faces
are Boolean labels, and the forced edge-class and corner counts are imposed. It
covers both the closed lane and, with a `Z/6` position constraint on hexagonal
faces, the open two-socket **block** lane -- so `(28,12)`, `(29,12)` and
`(31,12)` are expressible in CNF for the first time.

Gates: all 23 published `(3,4,5)`-APGs and all four published strict blocks
(A21-D24) are models; twelve verifier-accepted three-edge rematchings are still
models; and every published map relabels into a representative satisfying the
vertex normal form. The lane **certifies an order-17 witness in 4.2 s** and is
`INCOMPLETE` at order 20, so it does not yet reach the targets. Its
`ENCODING_UNSAT` disposition is a statement about the encoding at a profile and
never a nonexistence claim. The vertex symmetry break is gated but off by
default: it is a measured net loss on satisfiable instances.

```sh
python3 -m pytest -q test_exact_map_cnf.py          # ~10 minutes
python3 exact_map_cnf.py --order 20 --r 9 --timeout 600 \
  --output results/logs/cnf_order20.json
```

The CNF module needs `python-sat`. No other gate here does, and that is now
checked rather than asserted: the certificate-side helpers the gate shares with
it live in stdlib-only [`certificate_tools.py`](certificate_tools.py), and
`test_target_certificates.py` re-imports itself in a fresh interpreter with
`pysat` blocked. Before this split the advertised gate could not even be
collected without the solver installed.

## Lightweight checks

From this directory:

```sh
python3 -m pytest -q test_section8_profiles.py test_exact_map_bool_contract.py test_block_arithmetic.py test_structural_audit.py test_exact_map_postprocess.py test_cloud_resource_runner.py test_blocks.py test_verify.py
python3 -m pytest -q test_verify_darts.py test_block_tools.py
python3 block_arithmetic.py
```

The structural-control checkpoint can be replayed with:

```sh
python3 structural_audit.py --gluing \
  --output results/logs/structural_audit_known_blocks.json
python3 -m pytest -q test_structural_audit.py
```

This audit covers the known A21--D24 blocks and their ordered compositions.
[`SECTION8_PORT_THEOREM.md`](SECTION8_PORT_THEOREM.md) closes the strict
interface bridge for the two-port theorem: it proves `(25,10)` impossible from
the port cycles and core counts, while retaining `(25,11)` as a finite-use
branch with forced `t=1`. The portable `t=0` restriction remains opt-in and is
not a nonexistence claim about one-off blocks.

The public-source structural census is replayed with:

```sh
python3 source_census.py --output results/logs/source_structural_census.json
python3 -m pytest -q test_source_census.py
```

It verifies the 19 frozen planar-code inputs against their recorded hashes and
reports exact `(r,t,H55,fan,pair)` signatures before any opening result is
used.

For completeness checks around the strict lane, `blocks.py` also exposes
reflected opening/composition variants and the role-compatible over-approximate
`relaxed_opening_scan`. These helpers are intentionally diagnostic: a relaxed
candidate still needs an explicit gluing and nine-closure certificate.

The verifier and its known-answer/mutation tests are documented by their own
CLI help. No GitHub Actions workflow is used in this repository; all gates are
run explicitly and their output is archived with the result.

`verify_darts.py` is a second, standalone checker for the same certificate
contract. It uses the opposite dart-permutation turn and imports no search,
block, or `verify.py` code; run it on every eventual target certificate as an
independent cross-check.

`exact_map_postprocess.py` is the mandatory boundary between the exact-map
solver and a mathematical claim. It runs both checkers in fresh processes on
every positive model. For a two-socket model it also validates the strict block
interface and runs all nine cap-hub closures through both checkers. It
reconstructs the claimed `r` profile, and a requested block `t` profile is a
nine-closure gate rather than a log-only assertion. Solver `unknown`, timeout,
or a failed/partial closure set is recorded as
`INCOMPLETE`, never as nonexistence.

`BOOLEAN_CAP_MOTIF_NORMALIZATION.md` records a second Boolean route: search a
closed APG with two marked `4--(3,3)` cap fans, reopen their four marked edges,
and accept it only if the result is a strict block with all nine verified
closures. `CLOUD_BOOL_CAP_MOTIF_JOB.md` freezes the source-gated portable
`(28,12),(29,12),(31,12)` batch for that route. A closed hit that fails strict
reopening is retained as diagnostic evidence, not a block or target witness.

`promotion_handoff_gate.py`, `compose_target_witnesses.py`, and
`finalize_target_promotion.py` form the corresponding promotion boundary. A
future `(28,12),(29,12),(31,12)` triple must first be revalidated from its raw
Boolean records and hashes; the composer then exhaustively records compatible
reflection/socket/shift joins for the frozen 26 orders. A separate finalizer
replays the source handoff, every strict-block closure, every composition trace,
and both independent target checkers before it can write `MANIFEST_COMPLETE`.
The reproducible isolated-Linux procedure is
[`CLOUD_TARGET_PROMOTION_JOB.md`](CLOUD_TARGET_PROMOTION_JOB.md). This is an
executable promotion gate rather than a construction result: it reports `0/26`
until actual witnesses pass it, and it was written while the orders were open.
All 26 have since been settled; see the scoreboard at the top of this file.

## Definition of done

Completion requires exactly 26 target-order certificates, each accepted by two
independent rotation-system verifiers, plus a manifest with hashes and replay
commands. Any target assembled from blocks must also record each block's
audited `t` and pass the additive `t <= 4` composition budget. Search logs,
random seeds, timeouts, or partial witness sets are useful progress but do not
close the conjecture. For the Boolean-primary route, the source-bound finalizer
must additionally replay the immutable handoff ledger, source artifacts,
strict-block closures, and all 26 construction traces; only that finalizer may
write `MANIFEST_COMPLETE`.
