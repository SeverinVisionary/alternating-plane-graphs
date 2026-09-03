# Why every target profile returns `unknown`, and what the alternatives cost

Dated 2026-08-31. Isolated Linux worker, 4 cores, 15 GB RAM (the project rules §11).
Nothing here is a construction, a block certificate, or a nonexistence claim.
Target coverage remains **0/26 independently verified**.

## The observation this starts from

Three successive strengthenings of the exact-map lane — the cap-facial
interface, the complete socket normal form, and the residual-`H55` `r=12`
encoding — each ran the same three portable profiles `(28,12)`, `(29,12)` and
`(31,12)` on an isolated Linux worker, strictly serially, one Z3 thread, seed
zero. All nine runs returned Z3 `unknown` with disposition `INCOMPLETE`, at
600–649 solver seconds. In all three checkpoints the order-20 and A21 controls
passed.

Identical dispositions at identical bounds across three *different* structural
encodings are not evidence that the structure is wrong. They are the signature
of a bottleneck the three encodings share.

## Measurement: the shared bottleneck is the solver core

`exact_map_bool_sat.py` is named for its Boolean matching layer, and that layer
is genuinely Boolean. The facial argument on top of it is not. `phi`,
`face_length`, every row of the `phi_powers` chain, and the `vertex_at` rows
are `z3.Int` values defined by `Sum(If(...))` expressions ranging over every
dart — quadratic in the dart count per power level, and the power chain runs to
the maximum face size.

Built locally with the repository's own profile constructors:

| profile | darts | build | assertions | distinct AST nodes | Boolean matching vars | **integer vars** |
| --- | --- | --- | --- | --- | --- | --- |
| closed `(20,9)` | 76 | 9.5 s | 14 529 | 127 631 | 1 923 | 456 |
| block `(28,12)`, `t=0` | 100 | 21.5 s | 41 336 | 275 718 | 2 976 | 700 |
| block `(29,12)`, `t=0` | 104 | 22.7 s | 44 492 | 298 046 | 3 232 | 728 |
| block `(31,12)`, `t=0` | 112 | 25.9 s | 51 056 | 344 442 | 3 744 | 784 |

Replay with

```sh
python3 measure_encoding_cost.py \
  --output results/logs/solver_core_diagnosis_20260831.json
```

The counts are distinct AST nodes reachable from `solver.assertions()` and
uninterpreted constants of integer sort; build seconds are wall clock on a
shared four-core worker and vary by a second or two between runs. The archived
record is
[`results/logs/solver_core_diagnosis_20260831.json`](results/logs/solver_core_diagnosis_20260831.json).

Two things follow.

1. **The formula is mostly arithmetic, and the arithmetic is the part that
   states the mathematics.** Seven hundred integer variables tied together by a
   quarter-million-node `Sum(If(...))` network put the entire facial argument
   inside linear-integer-arithmetic reasoning. A `phi^k` chain defined this way
   propagates nothing until the underlying matching literals are nearly
   decided; the theory solver re-derives by simplex what a Boolean encoding
   settles by unit propagation.
2. **Roughly 4% of each 600 s budget is spent before the search starts.**
   Building `(31,12)` costs 25.9 s. That is not the cause of the timeout, but
   it is a direct measure of formula size, and it scales the wrong way.

This diagnosis is about *why the bound is not reached*. It says nothing about
whether a target block exists, and it does not weaken any recorded control:
the order-20 and A21 controls passed on their own merits and remain valid.

## Alternative 1: a pure-CNF encoding — built, gated, not yet competitive

`exact_map_cnf.py` states the same closed-map mathematics with no arithmetic at
all:

- `alpha` is the same Boolean perfect matching on darts;
- `phi = sigma^-1 alpha` is **not a variable**: `phi(d) = t` *is* the matching
  literal `m[d, sigma(t)]`, so the face permutation costs nothing;
- faces are Boolean labels of prescribed size, propagated along `phi`.

The property the integer encoding bought with an explicit `phi^k` power chain —
that each face class is a single `phi`-orbit — is here a theorem of the rest of
the constraint set. Loops and parallel edges are excluded outright, so every
`phi`-orbit has length at least three; every label class has size at most five;
a class holding two orbits would need at least six darts.
`prove_label_class_is_one_orbit` records that argument as an executable check,
and the encoder refuses any profile with a face of size six rather than
silently encoding something weaker — which is exactly why this module covers
the **closed** lane only and not the two-socket block lane.

It also states a constraint the profile forces but the Z3 lane leaves to
search. Alternation puts every edge between two different degrees, so

```text
3 n3 = e34 + e35,    4 n4 = e34 + e45,    5 n5 = e35 + e45
```

is a nonsingular system: the three edge-class counts are *determined* by the
profile. At `(20,9)` they are `e34 = 13`, `e35 = 14`, `e45 = 11`.

### Gates that pass

- **Predicted-object gate across parameters.** All 23 published
  `(3,4,5)`-APGs available here — the four known fixtures at orders 17, 20 and
  42, plus the 19 frozen planar-code census sources at orders 26–36 — are
  models of the encoding after re-embedding, spanning `r = 8` through `r = 14`.
  A constraint calibrated on one profile passes a one-map gate; it does not
  pass this one (the project rules §§3–4).
- The face-label normal form keeps the published maps: the order-20 map is a
  model both with and without the label ordering.
- Re-embedding round-trips: the four known fixtures pass both independent
  verifiers after a trip through the dart model.
- **Mutation control, now biting.** Two-swap rewirings were the wrong move:
  all 205 of them are invalid, so the control only ever agreed on the negative
  side and its load-bearing branch never fired. Three-edge deranged
  rematchings — the move `three_edge_rematch.py` enumerates, 8 of the 15
  perfect matchings on six darts — do reach other genuine APGs. Twelve of them
  pass both independent verifiers, and every one is still a model, and still a
  model under the vertex normal form after relabelling. That is the direction
  that catches an over-strong constraint.

### The constraints that made it work

Three additions moved this lane from "no witness at any order" to a certified
witness, and all three are consequences of the profile that the solver
otherwise had to find by search:

1. **The three faces at a degree-3 vertex have sizes exactly 3, 4 and 5.**
   They are distinct faces and pairwise adjacent along the three edges at the
   vertex, so their sizes are pairwise different — and three different values
   from `{3,4,5}` are all of them.
2. **A triangular face has vertex degrees exactly 3, 4 and 5**, because its
   three vertices are pairwise adjacent and alternation makes their degrees
   pairwise different.
3. **Forced corner counts.** Writing `c[L][k]` for the darts on size-`L` faces
   at degree-`k` vertices, (2) gives `c[3][k] = f3 = r` for every degree and
   (1) gives `c[L][3] = n3 = r` for every size. The rest of the 3x3 table is
   not determined by the profile.

Each is implied by the per-edge constraints, and each is nonetheless decisive:
before them, order 17 timed out at 240 s; after them it is **CERTIFIED in
4.2 s**, and the emitted rotation system passes both independent verifiers.

### The honest status

The lane now produces witnesses, and the frontier is far short of the targets.
Measured ladder, 240 s per profile, up to four `r` per order taken outward from
the published trend, vertex symmetry break off; record in
[`results/logs/cnf_scaling_ladder_20260831.json`](results/logs/cnf_scaling_ladder_20260831.json):

| order | witness | `ENCODING_UNSAT` at | `INCOMPLETE` at |
| --- | --- | --- | --- |
| 17 | **CERTIFIED, 4.2 s**, both verifiers | — | — |
| 20 | none | `r = 7` (4.2 s), `r = 10` (4.0 s) | `r = 8, 9` |
| 22 | none | `r = 7` (4.2 s), `r = 8` (9.2 s) | `r = 9, 10` |
| 24 | none | — | `r = 8, 9, 10, 11` |
| 26 | none | `r = 9` (45.4 s) | `r = 10, 11, 12` |
| 28 | none | — | `r = 9, 10, 11, 12` |
| 30 | none | `r = 10` (105.4 s) | `r = 11, 12, 13` |
| 33 | none | — | `r = 11, 12, 13, 14` |
| 36 | none | — | `r = 11, 12, 13, 14` |

The run was stopped by its outer wall during order 40, so orders 43 and 46 were
never reached; two order-40 profiles were `INCOMPLETE`.

Three things this says.

- **The wall is sharp, not gradual.** A witness at 17 in four seconds, and
  nothing from 20 upward. There is no band of "slow but reachable" orders to
  push through with a bigger budget.
- **It is not that witnesses are scarce.** Order 26 at `r = 11` is a profile
  where the frozen census holds a published witness, and 240 s does not find
  one. The search is failing on profiles known to be satisfiable.
- **Refutation and search scale differently — with a caveat.** `ENCODING_UNSAT`
  is decided at order 30 in 105 s while satisfiable profiles at order 20 are
  undecided at 240 s. But the refuted profiles are the cheap boundary cases on
  *either* side of the undecided interior — at order 20 both `r = 7` and
  `r = 10` refute in about 4 s while `r = 8, 9` do not. (An earlier revision of
  this file said the refutations were all at extreme *low* `r`; that was wrong,
  and `(20,10)` is the counterexample.) No interior profile has been refuted,
  so this is not evidence that they will be, and the refutation lane still needs
  the faithfulness audit before any `unsat` means more than "this encoding,
  this profile".

Formula size is not the obstacle. Closed `(46,18)`, the smallest target
profile, is 775 102 variables and 3 664 506 clauses built in 6.3 s — an
ordinary size for a CDCL solver.

The obstacle is symmetry. The encoding fixes vertex slots by degree, so a
solution survives `n3! n4! n5!` relabellings: `1.2 x 10^8` at order 17 and
`3.1 x 10^10` at order 20. That 267-fold jump tracks the observed slowdown,
and the profiles in between are what the ladder is measuring.

**The vertex lex-leader break is now gated, and measured to be a net loss.**
Relabelling by adjacent same-degree transpositions strictly increases the
flattened adjacency matrix, so the bubble sort terminates, and it terminates at
a labelling the encoder accepts. All 23 published APGs reach such a
representative, still pass both verifiers there, and are still models under the
break — the executable control that was missing. But on these *satisfiable*
instances the break costs more than it saves: order 17 takes **99 s with it
against 4.2 s without**. That is the familiar asymmetry — symmetry breaking
pays for refutation, not for finding one witness — so it stays off by default,
now for a measured reason rather than for want of a gate.

`unsat` from this encoding is recorded as `ENCODING_UNSAT` and is a statement
about this encoding at this profile. It is never a nonexistence claim: the
encoding adds representation conventions, and it does not state connectivity,
so both verifiers still gate every emitted certificate.

### The block lane is now encodable

The module no longer refuses hexagons. A size-six label class could be two
triangular orbits rather than one hexagonal face — the one case where the
"orbits are at least three, classes are at most five" argument fails — so each
hexagonal dart carries a position in `Z/6` with `pos(phi(d)) = pos(d) + 1`.
Walking an orbit of length `L` back to its start forces `L = 0 mod 6`, hence
`L >= 6`; the class has six darts and contains the orbit, so the class *is*
that orbit. No further clause is needed.

The edge-class counts generalise with the lane. With degree-2 socket whites
adjacent only to pentagon corners, the four unknowns `e25, e34, e35, e45`
satisfy four independent equations and are again determined: at block
`(21,10)` they are `12, 6, 12, 6`. The module solves that system exactly and
imposes it only when it has a unique non-negative integer solution.

Gate: the published strict blocks **A21, B22, C23 and D24 are all models** of
the open-block encoding, at 245k–372k clauses. This makes the profiles that
have been timing out — `(28,12)`, `(29,12)`, `(31,12)` — encodable in CNF for
the first time. It is not a search result: no block search has been run on it.

## Alternative 2: exhaustive generation — priced, and it does not reach

The 2015 authors' generator is public and was in the prior-art audit as a
repository with no target-order deposit. It had not been built or run here. It
builds and runs on this session: `github.com/nvcleemp/alternating`, a plugin for
plantri 4.5, last commit 2013-11-07, `make` with no changes needed.

Its generation strategy decides what pruning is possible. plantri's `-p` mode
starts from triangulations and *removes* edges, so along a generation path
**vertex degrees only decrease and face sizes only increase**. The face bound
is therefore prunable by plantri's own `-f` option; the degree bound is not,
because a high-degree vertex may still come down. But not for free: removing
one edge lowers exactly two degrees by one, so with

```text
excess = sum over v of max(0, degree[v] - 5)
budget = number of edge removals still allowed
```

any node with `excess > 2 * budget` has no `(3,4,5)` descendant and the whole
subtree can be cut. That bound is exact, not heuristic, and it is the natural
`{3,4,5}` specialisation of the published plugin's filters.

Measured with that bound in place, `-p -c1m3 -e(2n-2) -f5 -u`:

| order | graphs | cpu |
| --- | --- | --- |
| 12 | 0 | 1.58 s |
| 13 | 0 | 21.44 s |
| 14 | — | exceeded 600 s |

Zero at orders 12 and 13 is consistent with the published record, whose
smallest `(3,4,5)`-APGs are at order 17 — a weak control only. The positive
control at order 17 did not finish inside the budget available, so this lane
carries **no passing positive control** and its counts must not be quoted as
census results.

The pricing, however, does not depend on that control. The measured step is
`13.6x` per vertex, and it has a structural explanation rather than resting on
two points: plantri's cost here is dominated by enumerating triangulations on
`n` vertices, and rooted planar triangulations grow like `(256/27)^n` — about
`9.5^n`. Reaching order 46 from order 13 is therefore some `9.5^33 ≈ 10^32`
times the 21 s measured at order 13, and the plugin's pruning acts on the
edge-deletion phase *below* that enumeration, so it cannot change the base.

**Conclusion: exhaustive generation cannot reach the target orders, and the
reason is structural, not a compute budget.** Any generation-based route has to
avoid enumerating triangulations at the target order — for instance by
generating blocks at orders 25–34 and composing, which is what the block lane
already does, at a size where this cost is survivable.

The plugin source is deliberately **not vendored** into this repository:
`alternating.c` carries no licence and plantri has its own redistribution
terms. The bound above and the command lines are sufficient to reproduce the
measurement from upstream sources.

## What this changes for the program

- The `(28,12)`, `(29,12)`, `(31,12)` timeouts should not be read as evidence
  about those profiles. They are evidence about the encoding that ran them.
  Re-running the same lane with a larger budget buys little; the recorded
  `unknown` results already say the search never got started.
- Before more Cloud compute on the Boolean lane, the facial argument needs to
  leave integer arithmetic. `exact_map_cnf.py` shows that is possible for the
  closed lane and states precisely what is still missing.
- The exhaustive-generation route is now priced and closed. That is a result:
  it removes a route that looks attractive from the outside.
- Nothing here touches the prior-art gate, and nothing here is a candidate, a
  certificate, or a nonexistence assertion.
