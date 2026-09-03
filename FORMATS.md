# Data formats

Everything in `certificates/` is in one of two formats. This file specifies both
well enough to read them without any code from this repository, which is what a
deposit needs: the certificates are the evidence, and they should outlive the
Python that produced them.

## `apg-plane-rotation-v1` -- the certificate format

A UTF-8 JSON object with exactly two keys.

```json
{
  "format": "apg-plane-rotation-v1",
  "vertices": [
    {"id": 1, "clockwise": [2, 43, 38]},
    {"id": 2, "clockwise": [1, 40, 17, 13]}
  ]
}
```

* `format` is the literal string above.
* `vertices` is a list of objects, one per vertex, in no particular order.
* `id` is a positive integer, unique across the list. Ids are `1..n` in every
  file here, but a reader should not rely on that.
* `clockwise` is the **rotation** at that vertex: its neighbours in clockwise
  order in the plane embedding. Length equals the vertex's degree.

That is the whole format. It carries no coordinates, no faces and no edge list,
because a rotation system determines the plane map up to homeomorphism, and
faces are derived rather than asserted -- a stored face list would be a second
source of truth that could disagree with the rotations.

### Well-formedness

A file is a valid plane map iff all of the following hold. Every certificate in
this repository satisfies them, and `verify.py` and `verify_darts.py` check them
independently of each other.

1. **Symmetry.** For every `u` and every `v` in `u`'s ring, `u` appears in `v`'s
   ring. Edges are undirected.
2. **Simplicity.** No ring contains a repeat, and no ring contains its own
   vertex. No loops, no parallel edges.
3. **Connectivity.** The graph is connected.
4. **Sphericity.** Trace faces and check Euler. See below; `n - m + f` must be
   `2`.

### Deriving the faces

Build darts as the pairs `(u, i)` for `i` indexing `u`'s ring, so `u` has
`deg(u)` darts. Define

* `alpha(u, i) = (v, j)` where `v = clockwise[u][i]` and `j` is the position of
  `u` in `v`'s ring -- the other end of the same edge;
* `sigma(u, i) = (u, i+1 mod deg(u))` -- the next dart clockwise at `u`.

Then faces are the orbits of

    phi = sigma^-1 . alpha

and the **size** of a face is the length of its orbit, i.e. the number of
edge-side incidences on its facial walk. Note the consequences, both of which
matter for the mathematics here:

* a bridge contributes **2** to the size of the single face carrying it, since
  the facial walk traverses it twice;
* a face's size is not the number of distinct vertices on it. They differ
  exactly when the facial walk repeats a vertex, which happens iff the graph is
  not 2-connected.

An edge is a **bridge** iff its two darts lie in the same face orbit.

### Reference reader

Twenty lines of dependency-free Python, sufficient to check any certificate:

```python
import json

def faces(path):
    rings = {r["id"]: r["clockwise"] for r in json.load(open(path))["vertices"]}
    darts = [(u, i) for u in rings for i in range(len(rings[u]))]
    alpha = {(u, i): (v, rings[v].index(u))
             for u in rings for i, v in enumerate(rings[u])}
    sigma_inv = {(u, i): (u, (i - 1) % len(rings[u])) for u, i in darts}
    seen, sizes = set(), []
    for dart in darts:
        if dart in seen:
            continue
        size, cursor = 0, dart
        while cursor not in seen:
            seen.add(cursor)
            size += 1
            cursor = sigma_inv[alpha[cursor]]
        sizes.append(size)
    n, m = len(rings), len(darts) // 2
    assert n - m + len(sizes) == 2, "not spherical"
    return sizes
```

## `planar_code` -- the published corpus

**planar_code** is the binary format used by `plantri`, House of Graphs and the
source paper's authors. No `.plc` file ships here.
`import_planar_code.py` decodes the first graph of a file into
`apg-plane-rotation-v1`. It is a provenance aid only: no certificate's validity
depends on it, and the verifiers never call it.

Layout, as this repository reads it:

* optional 15-byte header `>>planar_code<<`;
* then, per graph: one byte `n`, then for each vertex in turn its neighbours in
  clockwise order as one byte each, terminated by a `0` byte.

Neighbours are 1-based. A leading `0` byte in place of `n` signals a wider
integer width; the files here do not use it. See `import_planar_code.py` for the
exact reader.

### Writing planar_code

[`export_planar_code.py`](export_planar_code.py) writes a certificate back out
as planar_code, so it can be checked by `plantri`, House of Graphs or anything
else that reads the format:

```
python3 export_planar_code.py certificates/targets/TARGET_46.json TARGET_46.plc
```

One subtlety, because it will otherwise look like a bug. planar_code does **not**
require a vertex's ring to begin at its smallest neighbour, and seven of the 33
upstream files did not. Both this repository's reader and its writer
canonicalise to the min-first rotation, which is the same embedding read from a
different starting point. So decoding and re-encoding is byte-identical for a
file already in that order and merely map-identical otherwise, and
`test_export_planar_code.py` asserts each of those where it applies -- with a
control requiring that neither case is vacuous.

**These bytes are not in this repository.** No licence was found at their
source, so they are not redistributed; each graph is re-expressed in
`apg-plane-rotation-v1` instead. The SHA-256 of every original, paired with the
digest of its re-expression, is in
[`certificates/UPSTREAM_PROVENANCE.json`](certificates/UPSTREAM_PROVENANCE.json).
See [`NOTICE.md`](NOTICE.md).

## What is derived and what is stored

Nothing in `certificates/` stores a claim that a graph *is* an alternating plane
graph. Only rotations are stored; degrees, faces, face sizes, bridges,
connectivity and the alternation conditions are all recomputed on every run by
`verify.py`, `verify_darts.py` and `fast_apg_check.py`, which were written
independently of one another. A corrupted certificate cannot pass by asserting
its own correctness.
