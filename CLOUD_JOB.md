# CLOUD JOB - `(3,4,5)`-APG Conjecture 10.2 construction search

Execute this job only in the user-launched isolated Linux cloud task pinned to
the dispatch commit on branch `apg-345-conjecture-10-2`.

Every major milestone must end in a durable commit pushed to that branch before
the next expensive lane starts.  At minimum, checkpoint the environment and
known-answer gates, block-calculus reproduction, each bounded search family,
each newly certified block order, and the final witness package separately.
Do not leave a milestone only in cloud-local files or an uncommitted worktree.

## Step 0 - hard environment gate

Run and retain this output before installing or compiling anything:

```sh
python3 --version
pwd
git status --short --branch
git rev-parse HEAD
```

STOP if `pwd` shows a macOS path such as `/Users/...`: this job must not run on
the development machine.  Stop as well if the checkout is dirty before
your work, or if the input commit differs from the dispatch prompt. Do not fall
back to the local host.

```sh
# Executable form of the same stop, so it does not depend on being read.
case "$(pwd)" in /Users/*) echo "macOS path: this job must not run here"; exit 99;; esac
```


Create `results/environment.txt` with the input commit, `pwd`, CPU count
(`python3 -c 'import os; print(os.cpu_count())'`), memory, compiler, Python,
installed solver/tool versions, and UTC start time.
Never add a `.github/` workflow.

## Frozen target and correctness rule

Read the project rules, this directory's `PRIOR_ART.md`, `README.md`, independent
verifier, and tests before acting.

The target orders are exactly:

```text
46 47 48 49 50 51 52 53 54 55 56
67 68 69 70 71 72 73 74
88 89 90 91 92
109 110
```

This is a positive-witness task. A miss, timeout, solver failure, incomplete
beam, or exhausted restricted family must be reported only as search evidence,
never as nonexistence. Do not create `results/MANIFEST_COMPLETE` unless all 26
orders pass the full independent gate below.

## Milestone 1 - known-answer and parser gates

Before target search:

1. Run every committed lightweight test through the normal production CLI.
2. Verify both published order-17 `(3,4,5)` APGs and selected published controls
   at orders 20, 21, 22, 23, 24, 29, 34, and 42.
3. Confirm that the published general-APG order-19 negative controls fail the
   `(3,4,5)` verifier for the documented reason; do not claim this reproduces
   the paper's exhaustive nonexistence result.
4. Record raw witness SHA-256 values and the exact source URLs.

Any known-answer failure blocks all target search until fixed.

## Milestone 2 - reproduce the Section 8 block calculus

Represent a block as a half-edge rotation system with two marked hexagonal
boundary faces. Each marked face alternates three degree-2 white vertices with
three degree-5 black vertices; every face across a boundary edge is a pentagon.
All other vertices/faces and both alternation conditions follow the paper.

Implement block validation independently from the final APG verifier. Then:

The dispatch branch now contains `blocks.py`, `test_blocks.py`, and published
JSON seeds for this milestone. Run those gates first and extend that code rather
than replacing its independently tested rotation operations.

1. Recover blocks A, B, and C mechanically by opening the two closure fans in
   published APGs of orders 21, 22, and 23.
2. Recover D at order 24 from Figure 5 or by a bounded patch-completion search.
   The published order-24 files need not expose the strict opening directly.
3. Close each single block and verify it as an APG.
4. Compose and close every ordered pair of A-D. Verify the resulting orders
   `39-45` and the exact order formula `n1+n2-3`.
5. Check the predicted histograms for a chain with block multiplicities
   `(a,b,c,d)` and `k=a+b+c+d`:

   ```text
   v3=f3=6k+4
   v5=f5=6k
   v4=f4=3a+4b+5c+6d+3k-1.
   ```

Archive deterministic block JSON, marked sockets, composer tests, and replay
commands. Search code must not bypass the committed final verifier.

## Milestone 3 - three-block extension search

The priority is to find compatible blocks of orders `25`, `29`, and `34`.
Their increments `22`, `26`, and `31`, combined with the published increments
`18-21`, arithmetically cover all 26 targets; confirm this with
`block_arithmetic.py`.

Use escalating positive-witness methods:

1. **Opening scan.** Test every legal pair of disjoint closure-fan openings in
   the published `(3,4,5)` APGs of the same order.
2. **Local surgery.** Enumerate embedding-preserving edge flips, vertex splits,
   and small face patches around those graphs, retaining the full combinatorial
   map and exact marked-boundary state.
3. **Boundary patch search.** Grow the annular map face-by-face with two fixed
   alternating hexagonal boundaries, pruning exact degree/face violations.
4. **Beam search.** If exhaustive patch enumeration is too large, run multiple
   deterministic beams partitioned by `(block order, admissible histogram,
   seed)`. Preserve full maps; a coarse boundary hash may rank or deduplicate a
   heuristic beam but may not support a completeness claim.

Prioritize one certified block at each of the three orders over collecting many
isomorphic examples. For every success retain the full search log, state count,
pruning counts, seed, wall time, and deterministic replay command.

## Milestone 4 - compose all target witnesses

**Boolean-primary promotion rule.** If the active covering triple is the
Boolean `(28,29,31)` `t=0` route, this generic milestone is not authorization
to compose files directly. First produce the retained raw/postprocess/opened
handoff directory from `CLOUD_BOOL_CAP_MOTIF_JOB.md`, then execute the exact
source-gated `CLOUD_TARGET_PROMOTION_JOB.md`. Its handoff ledger binds the
three new blocks and the committed A--D controls; its separate
`finalize_target_promotion.py` audit is the only process allowed to write
`MANIFEST_COMPLETE` for that route. A manual composition, a raw Boolean
candidate, or a `PROMOTED_PENDING_SEPARATE_FINAL_AUDIT` manifest remains
incomplete.

Once a covering set of proposed blocks verifies:

1. Supply the concrete audited `order -> t` map to
   `block_arithmetic.target_representations_with_t_budget()` to choose a
   deterministic block chain for each target.  Do not reuse the historical
   hard-coded `(25,29,34)` selector when the active search produced a
   different covering set; for the current Boolean primary triple, the
   conditional arithmetic control is
   `boolean_primary_t0_target_representations()`.
2. Compose and close the chain using the block implementation.
3. Serialize the resulting plane rotation system as deterministic JSON and,
   optionally, standard `planar_code`.
4. Run the committed independent verifier in a fresh process on every file.
5. Run the committed `verify_darts.py` checker in a fresh process on every
   file. It uses the opposite dart-permutation turn and imports none of the
   search, composer, or first-verifier code; retain its output beside the first
   verifier's output.

If any of the three block orders remains missing, proceed to Milestone 5 only
for the target orders not already constructible.

## Milestone 5 - direct fallback search

Implement the paper's face-by-face boundary-growth search or an equivalent
full-combinatorial-map beam search for unresolved targets. Enumerate every
admissible value of `r`, where

```text
v3=f3=r, v5=f5=r-4, v4=f4=n-2r+4,
ceil((2n+18)/7) <= r <= floor((n+9)/3).
```

Partition work by `(n, r, method, seed)`. Start by reproducing published
order-20 and order-42 witnesses through the same production path. Do not attempt
large exhaustive `plantri` enumeration: the 2015 paper already shows its growth
is prohibitive. A direct success is as valid as a block-composed success once
both independent verifiers accept it.

## Required result package

Commit all durable results to the same branch and push. Include:

```text
results/environment.txt
results/search_summary.json
results/logs/
results/blocks/                 # recovered/new marked block certificates
results/certificates/apg_<n>.json
results/independent_checks.json
results/manifest.json
```

Each manifest entry must contain the order, certificate path, raw SHA-256,
canonical plane-map hash, `(v3,v4,v5)`, `(f3,f4,f5)`, method, source block chain
or direct-search seed, verifier versions, and replay command.

Only after a separate final process has asserted exactly the frozen 26 orders,
no duplicates, no extras, and two independent successful checks for every
certificate may it write:

```text
results/MANIFEST_COMPLETE
```

The final cloud report must state literally one of:

- `COMPLETE: 26/26 independently verified`, or
- `INCOMPLETE: k/26 independently verified`, followed by the exact unresolved
  orders and honest disposition of every failed/blocked lane.

Record UTC end time and total wall time in `results/environment.txt`, commit,
push, and report the result commit hash.

## When you are done — archive yourself

A standing project rule.  Verbatim, and this is
the last thing you do:

> WHEN YOU ARE DONE, ARCHIVE YOURSELF. After your final report is written and
> everything is committed and pushed, call `archive_session` with
> `session_id: "self"`. That stops the session and releases its sandbox; the
> transcript stays readable in the Archived list. Do this as your LAST action,
> after the report — never before it, and never while work is still running.
> If the tool is unavailable or refuses (it normally asks for a confirmation
> that nobody is present to give), say so explicitly in your final report, so
> the session can be cleaned up by hand.
