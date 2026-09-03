# Closed cap-motif normal form for the Boolean APG search

This is a second **positive-witness** route to strict Section 8 blocks. It
does not turn a bounded `unsat`, `unknown`, or a closed APG without a valid
reopening into a nonexistence statement.

## Strict block to marked closed caps

Choose one degree-2 white as the hub on each strict socket. Capping adds two
edges from that hub to the other two whites. The capped APG therefore contains
two disjoint `4--(3,3)` fans: each chosen hub has degree 4 and each of the four
chosen leaves has degree 3. Deleting precisely those four edges restores the
open rotation system.

Every strict block at `(b,r)` is consequently represented by a closed APG of
order `b` and degree-three count `r` with two marked cap fans. In particular,
portable strict blocks `(28,12)`, `(29,12)`, and `(31,12)` lie in this family.

## Representation normal form

For an APG with two *marked* cap fans, relabel within degree classes so the
leaves are degree-3 vertices `0,1,2,3` and the hubs are the first two degree-4
vertices. Rotate the rows at leaf `0` and hub `0` so their shared edge is the
first dart at both ends; this preserves the existing `alpha[0]` convention.
All other labels and local row starts remain arbitrary.

`canonical_closed_cap_fans` computes these labelled fan slots and
`canonicalize_closed_cap_rotation` exercises them on every published strict
block, every cap choice, and every mirror. In addition to the four hub--leaf
edges, the Boolean constraints assert the forced *graph* interface of each
marked cap: the hub and its two leaves each have exactly two degree-five
neighbours; every pair has exactly one common degree-five neighbour; and no
degree-five vertex is adjacent to all three. This is necessary for a cap made
by closing a strict socket. The Boolean constraints additionally assert the
forced *facial* interface: each marked chord borders exactly one triangle and
one quadrilateral, and the two quadrilateral sides lie on the same 4-face.
The independent pure-Python facial check additionally identifies the shared
quadrilateral's fourth vertex as the leaves' unique common degree-five
neighbour. These are necessary conditions, not a claim that every marked local
interface opens to a socket.

## Certificate boundary

For a `CANDIDATE`, `exact_map_postprocess.py` first requires both independent
closed-APG verifiers. It then removes the four recorded fan edges through
`blocks.open_cap_fans`. The candidate is certified as a block only when:

1. the opened rotation passes the strict Section 8 validator and its two
   degree-2 triples equal the marked fans;
2. the `H55/t` structural audit completes;
3. all nine cap-hub closures pass both independent verifiers; and
4. when `--require-t0` is requested, all closures satisfy the `t=0` and `r`
   gates.

An unmarked closed record that names `require_t0` is rejected at the
postprocessing boundary.  It cannot borrow the block-only `t=0` label while
bypassing reopening and the nine-closure audit.

Only after a marked-cap candidate has reopened **and** completed the strict
block, structural, `t`/`r`, and all-nine-closure gates does the postprocessor
write the exact reopened strict rotation as `opened_block.json`, with its
SHA-256 in the `CERTIFIED` audit record. An incomplete postprocess exports no
reusable open block. A later all-target composition job may consume it only
through the source-bound handoff ledger. It is not an APG target certificate:
an open block has degree-two socket vertices and must not be passed to the
closed-APG verifiers as a final witness.

Failure at any stage remains `INCOMPLETE`, even if the pre-opening closed APG
is valid. Thus the normal form is complete for marked strict blocks while the
solver-side cap condition remains a positive over-approximation of reopening.

## Portable `t=0`

Capping changes neither degree-5 vertices nor pentagonal faces, so it preserves
the degree-5/pentagon incidence graph `H55`. The existing degree-5 pentagonal
incidence constraint is therefore necessary for a marked closed cap intended to
reopen to a portable strict `t=0` block; it is not imposed on untyped closed
APG searches or finite-use positive-`t` blocks.
