#!/usr/bin/env python3
"""The increment-3 periodic (3,4,5)-alternating strip, and its checker.

A strip that composes with itself indefinitely is an infinite periodic
alternating map on the cylinder.  The translation acts freely, so the quotient
is a map on the *torus* with `c` vertices, `c` = the increment.  That reduction
turns "does a self-composable strip exist" into a finite question, and at
`c = 3` the answer is yes.

The quotient certificate, which this module re-checks rather than trusts:
vertices x (degree 3), y (degree 4), z (degree 5); edges e0,e1,e2 = (y,z),
e3,e4 = (x,z), e5 = (x,y); dart 2e at the first endpoint of e and dart 2e+1 at
the second; rotations x:(6,8,10), y:(0,2,4,11), z:(1,3,7,5,9); unroll class
omega = (-2,-1,0,-1,-2,-1) assigning edge e of the quotient to the lifted edge
from copy k of its first endpoint to copy k+omega[e] of its second.

Per period the strip adds one vertex and one face of each size, which is
exactly what a closed APG needs: `n` rises by 3 and `r` by 1, so
`v5 = r-4` and `v4 = n-2r+4` both rise by 1 and stay consistent.  The degree-5
orbit carries exactly two pentagonal incidences, so the strip is `t`-neutral
and pumping never consumes the `t <= 4` composition budget.

THE UNROLL CLASS IS NOT UNIQUE, AND THE DIFFERENCE MATTERS.  The *quotient*
above is unique up to renaming and mirror, but ``omega`` is only one choice of
primitive unrolling; others give different -- and inequivalent -- cylinder
strips.  The unrolling encoded here was recorded as ``(1,0)`` and is the one
the disk-filling search reported uncappable: no disk cap completed it at any of
its short meridian cuts, which is also why no closed APG contains one of those
seams, and why the seam-witness search that was once proposed for it could
never have succeeded.  A ``(2,3)`` unrolling of the *same* quotient is cappable
at both ends, and capping it is what produced the 26 target certificates in
``certificates/targets/``.

**THE LABELS ARE NOT DEFINED, AND ONE OF THEM LOOKS WRONG** (independent review,
2026-09-01).  A pair of integers names a class in ``H^1(T^2; Z)`` only once a
homology basis is fixed, and nothing here fixes one.  In the natural
coordinates -- gauge the tree edges to zero, leaving ``(p, p-q, 0, 0, q, 0)``
-- the ``omega`` below is ``(p, q) = (-2, -1)``, while ``(1, 0)`` is
``(1, 1, 0, 0, 0, 0)``, whose lift has ``e0`` parallel to ``e1``: not simple,
so not a strip at all.  See ``unrolling_class.py``, which computes this, and
``test_unrolling_class.py``, which pins it.  What is committed here *is* a
genuine cocycle with a connected, simple lift -- it is the class ``(-2, -1)``.

**AND IT IS NOT THE CLASS THE CERTIFICATES ARE BUILT FROM.**
``certificate_unrolling.py`` settles that by measurement rather than by label:
cover classes are invisible at radius 1 (``omega`` changes which *copy* an edge
reaches, never which vertex type), but they differ in which closed walks lift
to cycles.  Counting simple cycles of length 3..6 through each vertex separates
them, and every certificate of order >= 48 contains vertices with the profile
of a deep-interior vertex of the ``(1, -1)`` cover -- 61 of them at order 110 --
while **no certificate contains a single vertex matching the ``(-2, -1)`` cover
committed here**.

So the narrative is structurally right and its labels are wrong: the capped
strip is ``(p, q) = (1, -1)``, ``omega = (1, 2, 0, 0, -1, 0)``, and the
uncappability search concerns ``(-2, -1)``, the class below.

So this module verifies the strip and the reduction that finds it; it is not
itself the construction.  See ``SEARCH_STATUS.md`` and
an independent review of the cap construction, since removed from the tree.

Provenance: the quotient was proposed by an independent review
(recorded in an independent review, since removed from the tree) and is re-derived and
re-checked here from the certificate alone.
"""
import collections

EDGES = [('y','z'), ('y','z'), ('y','z'), ('x','z'), ('x','z'), ('x','y')]
ROT = {'x': (6, 8, 10), 'y': (0, 2, 4, 11), 'z': (1, 3, 7, 5, 9)}
OMEGA = (-2, -1, 0, -1, -2, -1)
DEG = {'x': 3, 'y': 4, 'z': 5}

def faces_of(sigma, alpha, darts):
    sinv = {v: k for k, v in sigma.items()}
    phi = {d: sinv[alpha[d]] for d in darts}
    seen, faces = {}, []
    for d in darts:
        if d in seen: continue
        walk, c = [], d
        while c not in seen:
            seen[c] = len(faces); walk.append(c); c = phi[c]
        faces.append(walk)
    return faces, seen

def check(verbose: bool = True) -> bool:
    """Re-derive and re-check the strip from the quotient certificate."""

    print("=== 1. quotient torus map ===")
    sigma = {}
    for v, cyc in ROT.items():
        for i, d in enumerate(cyc):
            sigma[d] = cyc[(i + 1) % len(cyc)]
    alpha = {}
    for e in range(6):
        alpha[2*e] = 2*e+1; alpha[2*e+1] = 2*e
    vertex_of = {}
    for v, cyc in ROT.items():
        for d in cyc: vertex_of[d] = v
    # dart placement must agree with the edge list
    for e, (u, w) in enumerate(EDGES):
        assert vertex_of[2*e] == u and vertex_of[2*e+1] == w, f"dart placement wrong at e{e}"
    print("dart placement agrees with the edge list: OK")
    for v, cyc in ROT.items():
        assert len(cyc) == DEG[v]
    print("degrees:", {v: len(c) for v, c in ROT.items()})
    faces, face_of = faces_of(sigma, alpha, range(12))
    sizes = sorted(len(f) for f in faces)
    print("face sizes:", sizes, "  V-E+F =", 3 - 6 + len(faces), "(0 = torus)")
    assert sizes == [3, 4, 5], f"face sizes are {sizes}, not 3/4/5"
    for e in range(6):
        u, w = EDGES[e]
        assert DEG[u] != DEG[w], f"e{e} joins equal degrees"
        l, r = face_of[2*e], face_of[2*e+1]
        assert l != r, f"e{e} has the same face on both sides"
        assert len(faces[l]) != len(faces[r]), f"e{e} separates two faces of size {len(faces[l])}"
    print("alternation (degrees and face sizes) holds in the quotient: OK")
    print("face edge-sets:", [sorted({d // 2 for d in f}) for f in faces])

    print()
    print("=== 2. lift to the cylinder ===")
    K = 12
    def lift_vertex(v, k): return (v, k)
    # edge e joins first-endpoint copy k to second-endpoint copy k+omega[e]
    adj = collections.defaultdict(list)
    lift_dart = {}
    darts = []
    for e, (u, w) in enumerate(EDGES):
        for k in range(-K, K + 1):
            a, b = (u, k), (w, k + OMEGA[e])
            d0, d1 = (e, k, 0), (e, k, 1)
            lift_dart[d0] = (a, b); lift_dart[d1] = (b, a)
            darts += [d0, d1]
    dart_at = collections.defaultdict(list)
    for d, (a, b) in lift_dart.items():
        dart_at[a].append(d)
    # rotation at a lifted vertex is inherited from the quotient
    lsigma = {}
    for v0 in list(dart_at):
        v, k = v0
        cyc = ROT[v]
        ordered = []
        for qd in cyc:
            e, side = qd // 2, qd % 2
            kk = k if side == 0 else k - OMEGA[e]
            ordered.append((e, kk, side))
        if any(d not in lift_dart for d in ordered):  # window edge
            continue
        for i, d in enumerate(ordered):
            lsigma[d] = ordered[(i + 1) % len(ordered)]
    lalpha = {(e, k, 0): (e, k, 1) for e in range(6) for k in range(-K, K+1)}
    lalpha.update({(e, k, 1): (e, k, 0) for e in range(6) for k in range(-K, K+1)})
    interior = [d for d in lsigma if lalpha[d] in lsigma]
    # simplicity of the lifted graph
    pairs = collections.Counter()
    for d in interior:
        a, b = lift_dart[d]
        pairs[tuple(sorted([a, b], key=str))] += 1
    assert all(v <= 2 for v in pairs.values()), "parallel edges in the lift"
    assert not any(a == b for a, b in (lift_dart[d] for d in interior)), "loop in the lift"
    print("lift is simple (no loops, no parallel edges): OK")
    # degrees in the lift
    degs = collections.Counter()
    for v0, ds in dart_at.items():
        if all(d in lsigma for d in ds): degs[DEG[v0[0]]] += 1
    print("interior vertex degrees:", dict(sorted(degs.items())))
    # faces of the lift, restricted to fully-interior walks
    lsinv = {v: k for k, v in lsigma.items()}
    ok = {d for d in interior if lalpha[d] in lsinv}
    lphi = {d: lsinv[lalpha[d]] for d in ok if lalpha[d] in lsinv}
    seen, lfaces = {}, []
    for d in lphi:
        if d in seen: continue
        walk, c, closed = [], d, True
        while c not in seen:
            if c not in lphi: closed = False; break
            seen[c] = len(lfaces); walk.append(c); c = lphi[c]
        if closed and c == d: lfaces.append(walk)
    good = [f for f in lfaces if len(f) >= 3]
    print(f"complete interior faces traced: {len(good)}")
    print("their sizes:", dict(sorted(collections.Counter(len(f) for f in good).items())))
    bad = [f for f in good if len(f) not in (3, 4, 5)]
    print("faces outside {3,4,5}:", len(bad))
    # repeated vertex on a face?
    rep = [f for f in good if len({lift_dart[d][0] for d in f}) != len(f)]
    print("interior faces repeating a vertex:", len(rep))
    # alternation across interior edges
    face_id = {}
    for i, f in enumerate(good):
        for d in f: face_id[d] = i
    same = 0
    for d in face_id:
        m = lalpha[d]
        if m in face_id and len(good[face_id[d]]) == len(good[face_id[m]]): same += 1
    print("interior edges separating equal-size faces:", same)
    degbad = sum(1 for d in interior if DEG[lift_dart[d][0][0]] == DEG[lift_dart[d][1][0]])
    print("interior edges joining equal degrees:", degbad)
    print()
    ok = not bad and not rep and same == 0 and degbad == 0 and len(good) > 20
    print("VERDICT:", "strip confirmed" if ok else "STRIP CLAIM FAILS")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if check() else 1)
