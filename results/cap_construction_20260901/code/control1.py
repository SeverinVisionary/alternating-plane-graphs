import json, sys
from maputil import rotation_to_faces, faces_to_rotation, emit_json, run_verifiers
from capsearch import Search

d = json.load(open('certificates/known/ghent17.json'))
rot = {row['id']: list(row['clockwise']) for row in d['vertices']}
faces = rotation_to_faces(rot)
deg = {v: len(ns) for v, ns in rot.items()}
adjG = {frozenset((u, w)) for u, ns in rot.items() for w in ns}

def region_of_deleted(V):
    inc = [f for f in faces if V in f]
    other = [f for f in faces if V not in f]
    # face containing dart (V, w): starts path at w
    by_start = {}
    for f in inc:
        i = f.index(V)
        cyc = f[i:] + f[:i]      # [V, w1, ..., wk]
        by_start[cyc[1]] = cyc[1:]
    # chain: path of face f ends at wk; next face is the one whose path starts at wk
    start = next(iter(by_start))
    walk = []
    cur = start
    while True:
        p = by_start.pop(cur)
        walk.extend(p[:-1])
        cur = p[-1]
        if cur == start:
            break
    if by_start: return None  # disconnected star? skip
    if len(set(walk)) != len(walk): return None  # duplicate boundary vertex
    n = len(walk)
    forb = []
    for i in range(n):
        a, b = walk[i], walk[(i+1) % n]
        cand = [f for f in other if any((f[j], f[(j+1) % len(f)]) == (b, a) for j in range(len(f)))]
        if len(cand) != 1: return None
        forb.append(len(cand[0]))
    region = [(v, 1 if v in rot[V] else 0) for v in walk]
    return region, forb, inc, other

tot = 0
for V in sorted(rot):
    rr = region_of_deleted(V)
    if rr is None:
        print(f"V={V}: skipped (complex region)")
        continue
    region, forb, inc, other = rr
    adj = {e for e in adjG if V not in e}
    s = Search(region, forb, {v: dg for v, dg in deg.items() if v != V},
               adj, max_new=2, max_solutions=500)
    sols = s.run()
    good, reproduced = 0, False
    for fcs, degs, nnew in sols:
        allf = [list(f) for f in other] + [list(f) for f in fcs]
        try:
            rot2 = faces_to_rotation(allf)
        except AssertionError as e:
            print(f"  V={V}: assembly failed: {e}")
            continue
        path = 'ctl.json'
        emit_json(rot2, path)
        res = run_verifiers(path, len(rot2))
        if all(rc == 0 for rc, _, _ in res.values()):
            good += 1
            if {frozenset(f) for f in fcs} == {frozenset(f) for f in inc}:
                reproduced = True
        else:
            print(f"  V={V}: verifier reject:", {k: v[2][:90] or v[1][:90] for k, v in res.items()})
    print(f"V={V} deg={deg[V]}: boundary={len(region)} solutions={len(sols)} verified={good} original_reproduced={reproduced} nodes={s.nodes}")
    tot += 1
