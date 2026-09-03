# Theorem 3.2 — read at the source, and it is exactly the missing step

**Closed 2026-09-01.** The 2026-09-01 review panel raised as a MEDIUM that both
verifiers and both search encodings impose

```text
v3 = f3,  v4 = f4,  v5 = f5,   v5 = v3 - 4,   E = 2n - 2,   F = n
```

on the authority of a "Theorem 3.2" this repository cited by name and never
quoted. The paper was then read directly from the UGent deposit
(<https://backoffice.biblio.ugent.be/download/6921573/6921591>, retrieved
2026-09-01, `sha256 e1c72804d769a81c336638f118714338488a42f472fc087d1b492841852884cf`),
and the theorem is there, on p. 340, with a complete proof.

> **Theorem 3.2.** If `G` is a (3, 4, 5)-alternating plane graph, then
> `v3 = f3`, `v4 = f4` and `v5 = f5`.

So the identities are the paper's, they are proved, and the verifiers are
right to impose them. What follows is kept because the independent derivation
done before the paper was read reproduces the proof's own structure, and
because the one step we could not find is precisely the one the authors supply.

## What we derived without the paper

**Lemma 1. `v3 = f3`.** Every 3-face has exactly one degree-3 vertex (its three
vertices are pairwise adjacent, so their degrees are pairwise distinct and
therefore exactly `{3,4,5}`); every degree-3 vertex lies in exactly one 3-face
(its three faces are pairwise adjacent, so their sizes are exactly `{3,4,5}`).
Counting that incidence both ways gives it. Write `r` for the common value.

*This is the paper's (3.3), by the same argument.*

**Lemma 2.** Counting dart-ends against face-corners gives
`4(v4 - f4) = 5(f5 - v5)`, so `5 | (v4 - f4)`: write `v4 - f4 = 5k`,
`f5 - v5 = 4k`.

*The paper states the same divisibility one line after (3.3): "(3.1) and (3.3)
together implies that `v5 - f5` must be divisible by 4."*

**Lemma 3.** Substituting into Euler collapses everything to `v5 = r - 4 - 2k`.

*The paper reaches the same place through its (3.2), `v3 + f3 = v5 + f5 + 8`,
and lists the five surviving cases:*

| paper's row | `k` here |
| --- | --- |
| `v5 = v3 - 8, f5 = v3` | `k = 2` |
| `v5 = v3 - 6, f5 = v3 - 2` | `k = 1` |
| `v5 = v3 - 4, f5 = v3 - 4` | **`k = 0`** |
| `v5 = v3 - 2, f5 = v3 - 6` | `k = -1` |
| `v5 = v3, f5 = v3 - 8` | `k = -2` |

The five rows are exactly `k ∈ {-2,-1,0,1,2}`, which is what our
parametrisation predicts, and the range is cut to five by the paper's
`f5 ≤ v3` and `v5 ≤ f3` (its (3.4) and (3.5), from counting (3,5)- and
(5,3)-combinations).

## The step we were missing

Let `a_i` be the number of degree-5 vertices incident with exactly one face of
size `i`, and `b_j` the number of pentagons incident with exactly one vertex of
degree `j`. The paper shows

```text
a3 = 2v5 - v3,   a4 + a5 = v3 - v5,   so  0 <= a5 <= v3 - v5      (3.6)
b3 = 2f5 - v3,   b4 + b5 = v3 - f5,   so  0 <= b5 <= v3 - f5      (3.7)
```

and then counts (5,5)-combinations two ways -- `2v5 - a5` and `2f5 - b5` --
to get

```text
a5 - b5 = 2(v5 - f5)                                              (3.8)
```

Against the five rows, `2(v5 - f5)` is `-16, -8, 0, 8, 16`, while (3.6) and
(3.7) cap `a5` and `b5` at `0`, `<= 2`, free, `<= 2`, `0` respectively. Both
are non-negative integers, so only the middle row survives:

> "Since `a5` and `b5` are both non-negative integers, it is clear that (3.8)
> is only possible if `v5 = f5 = v3 - 4`."

`v4 = f4` then follows from (3.1). **`k = 0` is forced.**

## Consequences for this repository

- The verifiers' profile block is sound. It cannot reject a genuine
  `(3,4,5)`-APG, so the six identity checks are redundant given the rest of the
  definition -- which is why `verifier_mutations.py` cannot give them a
  negative control, and that is now explained rather than merely observed.
- Every nonexistence-shaped result here -- the CNF and SAT lanes'
  `closed_profile()`, the "0 models found" dispositions -- is a statement about
  the full class of Definition 3.1, not a proper subclass. That was the open
  risk; it is closed.
- `E = 2n - 2` and `F = n` follow from Lemmas 1-3 with `k = 0`.

Everything above is checked against the objects we hold by
[`test_profile_identities.py`](test_profile_identities.py), which keeps the
derivation and the (now-proved) `k = 0` step as separate assertions.
