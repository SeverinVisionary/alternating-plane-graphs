# Strict Section-8 ports, finite-use blocks, and the `t` budget

This note is a proof-and-implementation checkpoint for the two-hexagon
construction in Section 8 of the primary paper, [Althofer et al.
(2015)](https://doi.org/10.26493/1855-3974.584.09a).  It applies only to the
strict, untyped Section-8 interface accepted by [`blocks.validate_block`](blocks.py).
It is not a nonexistence result for arbitrary APGs, nor a claim that every
strict block may be used an unbounded number of times in an externally typed
construction.

## Exact interface bridge

The following hypotheses are checked directly by `validate_block` before a
solver candidate can enter the block postprocessor:

| Mathematical requirement | Enforced implementation condition |
| --- | --- |
| simple, connected spherical rotation | `_validate_graph`, exact Euler equation, and a reconstructed face partition |
| no bridge or self-adjacent face | every edge must have two distinct incident faces of unequal sizes |
| simple pentagons and sockets | every reconstructed facial walk has distinct vertices |
| two socket faces | exactly two faces of length six |
| socket whites | exactly six degree-two vertices, all adjacent only to degree-five vertices |
| strict port geometry | each socket alternates degree `2,5`, its white sets are disjoint, and every socket edge has a pentagon on its other side |
| remaining alternation | all nonwhite degrees and nonsocket face sizes are in `{3,4,5}`, with no equal adjacent degree or face size |

The cap operation is then checked for all nine choices by
`blocks.close_block_variants`; a positive exact-map record additionally runs
both independent APG verifiers on every cap.  The construction used below is
fresh-copy composition, implemented by `blocks.compose_blocks`: it never
identifies two vertices within a physical copy.

## The port-cycle theorem

For a capped closure, let `H55` be the simple bipartite incidence graph whose
left nodes are degree-five vertices, whose right nodes are pentagons, and whose
edges are incidences.  Let `t` be the number of degree-five nodes of degree one
in `H55`.  The Section 3 count in the paper gives `0 <= t <= 4` for any closed
`(3,4,5)`-APG.

Consider one strict socket.  Its simple six-cycle has the form

```text
b0 - w0 - b1 - w1 - b2 - w2 - b0,
```

where the `wi` are degree-two whites and the `bi` are degree-five.  The face
across the two edges at `wi` is one pentagon `Pi`, because `wi` has degree two
and every socket edge borders a pentagon.  The three `Pi` are distinct: if two
coincided, their simple five-cycle would contain five consecutive vertices
`bi, wi, b{i+1}, w{i+1}, b{i+2}`, forcing its last edge to join two
degree-five vertices.

Each `Pi` contains exactly its two adjacent `b` vertices: degree-five vertices
are an independent set on a pentagon, and a 5-cycle has independence number
two.  At each `bi`, face alternation excludes any third incident pentagon.  It
follows that the socket determines an isolated component

```text
b0 - P0 - b1 - P1 - b2 - P2 - b0
```

of `H55`.  The two sockets determine distinct components.  Otherwise a common
pentagon would give two distinct socket whites adjacent to the same two
nonadjacent degree-five vertices on a simple pentagon, whereas that length-two
pentagon path has a unique middle vertex.

Thus every strict two-socket block has two distinct isolated `C6` port
components in `H55`.  Capping adds only white--white edges, triangles, and a
quadrilateral, so it leaves `H55` unchanged.

## Consequences at the small profiles

If `r` denotes the degree-three count after capping, the closed APG identities
give `|V5| = |F5| = r - 4`.

* At `r=10`, the two port components consume all six degree-five vertices and
  all six pentagons, so they force `t=0` without any repeatability assumption.
* At `r=11`, they consume six of seven nodes on each side.  The one remaining
  degree-five vertex and pentagon must be incident, hence
  `H55 = C6 + C6 + K2` and `t=1`.  This does **not** rule out a finite-use
  block at `r=11`.
* At `r >= 12` on the portable `t=0` branch, the isolated ports leave
  `r-10` degree-five vertices and `r-10` pentagons.  A degree-five vertex
  cannot have zero pentagonal incidences: its five incident face sizes form a
  proper coloring of a 5-cycle, and omitting size five would require a proper
  2-coloring by sizes three and four.  It has at most two pentagonal
  incidences, because the pentagonal positions are independent on that
  5-cycle.  Thus `t=0` makes every residual degree-five vertex have `H55`
  degree two.  The same proper-coloring argument on each pentagon says it has
  at least one incident degree-five vertex, and independence gives at most
  two.  The residual incidence total is exactly `2(r-10)`, so every residual
  pentagon has degree two as well.  Therefore the residual `H55` is a simple
  2-regular bipartite graph (a disjoint union of even cycles).  At `r=12` it
  has two nodes on each side, hence is exactly `K2,2 = C4`; at `r=13` it is
  exactly a `C6`.

The residual 2-regular conclusion (and its `r=12`/`r=13` special cases) is a
sound propagation condition only after the strict socket interface, cap
invariance, simple facial walks, canonical port allocation, and the portable
`t=0` condition have all been established.  It is not a general condition on
a closed APG, a finite-use block, another `r` profile, or an absence claim.

For the `t=0` core, after removing the twelve socket-boundary and four cap
edges, exact joint edge double-counting gives

```text
beta    = 7r - 2b - 22
gamma   = 2b - 6r + 18
epsilon = 2b - 4r - 2,
```

and these are counts of actual core edge classes, hence are nonnegative.  At
`(b,r)=(25,10)`, the port theorem forces `t=0` but `beta=-2`.  Therefore a
strict order-25, `r=10` block is impossible.  This is a profile contradiction,
not a bounded-solver result.

The pure arithmetic implementation is
[`section8_profiles.py`](section8_profiles.py).  Its regression gate includes
the `beta=-2` calculation, distinguishes raw core rows from strict portable
rows, and freezes the audited profile tables.

## Fresh-copy composition and finite-use accounting

When two disjoint strict blocks are composed in cyclic-order-compatible
fashion, only three degree-two whites from each are identified.  The consumed
hexagons become three quadrilaterals.  No degree-five vertex or pentagon is
created, deleted, or identified, and every old degree-five/pentagon incidence
is preserved.  Hence

```text
H55(B1 o B2) = H55(B1) disjoint-union H55(B2),
t(B1 o B2)   = t(B1) + t(B2).
```

The same is true after capping the two remaining sockets.  A chain used in a
finite target certificate must consequently satisfy `sum(t(block)) <= 4`.
`block_arithmetic.py` now has `t_total`, `representation_with_t_budget`, and
`target_representations_with_t_budget` so coverage is not inferred merely from
block orders.

If a block can occur with unbounded multiplicity under this untyped fresh-copy
operation, then `m*t <= 4` for every `m`, so `t=0`.  This is the portable
branch used by `--require-t0`; it is intentionally an opt-in search restriction.
It must not be used to discard a one-off `r=11` block such as the still-open
`(25,11)` finite-use branch.

## Search disposition

The prior Boolean pilot incorrectly scheduled `(25,10)`.  The replacement
schedule is deliberately split:

1. `(25,11)` is a finite-use candidate; its postprocess audit must show the
   forced `t=1` structure before it is used in a target composition.
2. `(27,12)`, `(28,12)`, `(29,12)`, `(31,12)`, and `(34,13)` are portable
   `t=0` branches and are searched with `--require-t0`.

Conditional on three certified `t=0` blocks at orders `(28,29,31)`, the
published blocks plus that triple cover every target under the `t<=4` budget.
`block_arithmetic.boolean_primary_t0_target_representations()` and its
regression test freeze that statement independently of the cloud-job prose.

No timeout, `unknown`, bounded `unsat`, or missing candidate is a mathematical
absence claim.  A positive block still needs strict validation, all nine caps,
both fresh independent verifiers, an `H55/t` audit, and a finite `t`-budget
composition check before it contributes to any of the 26 target orders.
