# The periodic capping lemma: proved, with the finite hypothesis machine-checked

The construction's load-bearing step is "cap + `t` periods + cap is a
`(3,4,5)`-APG". Until 2026-09-01 this repository had twenty-six verified
instances of it and no lemma: four hypotheses were unverified, no splice was
implemented, and `q` was undetermined. All three gaps are now closed by
[`pumping_splice.py`](pumping_splice.py), which extracts the caps as explicit
patches, implements the insertion, and builds `n + 3d` maps that both
independent verifiers accept.

## The statement

> **Periodic capping lemma.** Fix a target order `n` whose alignment against the
> `(1,-1)` cover has a deep block `D` of at least five copies, and let
> `cut` be a copy at distance at least two from each end of `D`. For every
> integer `d >= -(|D| - 1)`, the rotation system `splice(n, d)` is a
> `(3,4,5)`-APG on `n + 3d` vertices.

`d` is unbounded above. The floor is where deletion would consume a copy that is
not deep, that is, where the two cap collars meet — the `t >= 2q + 1` of the
2026-09-01 independent review, with `q = 2`: each collar is two copies wide.

## The proof

Write `S` for `splice(n, d)`. Every vertex of `S` gets its rotation in one of
four ways, and each is either verbatim from `TARGET_n` or a translate of a deep
rotation:

| vertices | rotation |
| --- | --- |
| cap | verbatim, with strip neighbours above the cut shifted by `d` |
| strip copies `<= cut` | verbatim |
| strip copies `> cut + d` | verbatim from copy `c - d` |
| the `d` fresh copies | the cut copy's rotation, translated |

**Locality.** A facial walk is traced by `phi = sigma^-1 . alpha`, which reads
only the edge partner and the rotation predecessor at the vertices it visits. A
`(3,4,5)`-APG face has at most five darts and the cover's largest edge offset is
two, so a facial walk cannot span more than three consecutive copies
(`test_every_face_stays_inside_a_short_window_of_copies` measures the span and
gets exactly three).

**Every window is a translated window.** `deep_block_is_periodic` checks that
the deep rotations really are translates of one another. The fresh copies lie in
`(cut, cut + d]`, and `cut` is at distance at least two from each end of `D`, so
every five-copy window around a fresh copy is a translate of the window
`[cut - 2, cut + 2]` of `TARGET_n`. Away from the fresh block, `S` agrees with
`TARGET_n` verbatim. Hence **every face of `S` is a translated face of
`TARGET_n`**.

From that, each condition in Definition 3.1 is inherited, because each is local:
face sizes and vertex degrees lie in `{3,4,5}`; adjacent vertices have unequal
degrees and adjacent faces unequal sizes; facial walks are simple; and a loop or
a parallel edge would have to sit inside a two-copy window, where `S` and
`TARGET_n` agree.

**Connectivity** is inherited because each copy meets the next and every cap
vertex reaches the strip exactly as it did in `TARGET_n`.

**The lift is spherical.** A copy contributes three vertices, six edges and — as
every face is a translated face — three faces, and `3 - 6 + 3 = 0`. So
`V - E + F` is unchanged from `TARGET_n`, where it is `2`. QED

Only two facts in that argument are not pure bookkeeping — the face span and the
periodicity of the deep block — and both are finite checks on a single
certificate, gated in [`test_pumping_splice.py`](test_pumping_splice.py).

## What the family reaches

| residue of `n` mod 3 | floor order | family |
| --- | --- | --- |
| 0 | **48** | 48, 51, 54, 57, ... |
| 1 | **52** | 52, 55, 58, 61, ... |
| 2 | **50** | 50, 53, 56, 59, ... |

Every one of the twenty spliceable certificates in a residue class has the same
floor order — 90 shortened by fourteen periods and 72 shortened by eight both
land on 48. So the family is

> every order `n >= 50`, together with `n = 48`.

That is an independent construction of the paper's Theorem 8.1 (`n >= 111`) and
of twenty-three of the twenty-six target orders, from a single certificate per
residue class. Orders **46, 47 and 49** are outside it and rest on their
certificates alone.

## Why this is a proof and not twenty-six more examples

The splice reproduces certificates it did not start from. `TARGET_110`
shortened by twenty periods is `TARGET_50` up to isomorphism of rotation
systems, and so is `TARGET_92` shortened by fourteen; `TARGET_90` shortened by
fourteen and `TARGET_72` shortened by eight both give `TARGET_48`. Two
independently searched certificates decompose into the same pair of caps and the
same period, which is the check that the cap extraction is canonical rather than
an artefact of one alignment.

Every spliced map in this note was put to `verify.py`, `verify_darts.py` and
`fast_apg_check.py`, at orders from the floor to 410.

## What is still not proved

The **uncappability** claim in [`UNCAPPABILITY_SPEC.md`](UNCAPPABILITY_SPEC.md)
is untouched by this. It is a statement about which classes admit *no* cap, and
this lemma only builds caps for one class that does. It also still refers to the
`(1,0)` labelling that [`unrolling_class.py`](unrolling_class.py) shows is not
the certificates' class.
