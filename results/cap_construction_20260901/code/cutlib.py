"""Interface extraction for an arbitrary meridian cut cycle of the strip."""
import collections
from strip_lib import EDGES, ROT, OMEGA, DEG, TAU, cycle_winding

K = 30
lift_dart = {}
for e,(u,w) in enumerate(EDGES):
    for k in range(-K, K+1):
        a, b = (u,k), (w,k+OMEGA[e])
        lift_dart[(e,k,0)] = (a,b); lift_dart[(e,k,1)] = (b,a)
dart_at = collections.defaultdict(list)
for d,(a,b) in lift_dart.items(): dart_at[a].append(d)
lsigma = {}
for v0 in list(dart_at):
    v,k = v0
    ordered = []
    ok = True
    for qd in ROT[v]:
        e, side = qd//2, qd%2
        kk = k if side==0 else k-OMEGA[e]
        if (e,kk,side) not in lift_dart: ok=False; break
        ordered.append((e,kk,side))
    if not ok: continue
    for i,d in enumerate(ordered): lsigma[d] = ordered[(i+1)%len(ordered)]
lsinv = {v:k for k,v in lsigma.items()}
lalpha = {}
for e in range(6):
    for k in range(-K,K+1):
        lalpha[(e,k,0)]=(e,k,1); lalpha[(e,k,1)]=(e,k,0)
lphi = {d: lsinv[lalpha[d]] for d in lsigma if lalpha[d] in lsinv}
faceof, faces = {}, []
for d in list(lphi):
    if d in faceof: continue
    walk, c, ok = [], d, True
    while c not in faceof and c not in [w for w in walk]:
        if c not in lphi: ok=False; break
        walk.append(c); c = lphi[c]
    if ok and walk and c == walk[0]:
        fid = len(faces)
        for dd in walk: faceof[dd] = fid
        faces.append(walk)
    else:
        for dd in walk: faceof[dd] = None

def face_vertices(fid):
    return [lift_dart[d][0] for d in faces[fid]]

def dart_between(a, b):
    out = [d for d in dart_at[a] if lift_dart[d] == (a,b)]
    assert len(out) == 1
    return out[0]

def rotation_of(v0):
    v,k = v0
    out = []
    for qd in ROT[v]:
        e, side = qd//2, qd%2
        kk = k if side==0 else k-OMEGA[e]
        out.append(lift_dart[(e,kk,side)][1])
    return out

def cut_interfaces(cycle):
    """cycle: list of lift vertices, |winding| must be 1.
    Returns dict with both cap problems, using the ORIGINAL lift vertices as
    boundary labels. capL = cap on the left of the directed cycle; capR = on
    the right (region boundary reversed).  forb = size of surviving strip face
    across each C-edge; rem = number of cap-side strip edges at each vertex.
    Also returns seed adjacency (C-edges + surviving-side edges between cycle
    vertices) per cap, and which geometric end (+k / -k) each cap covers."""
    w = cycle_winding(cycle)
    assert abs(w) == 1
    n = len(cycle)
    onC = set(cycle)
    left_arcs, right_arcs = {}, {}
    for i in range(n):
        u = cycle[i]; p = cycle[(i-1)%n]; nx = cycle[(i+1)%n]
        rotu = rotation_of(u)
        ip, inx = rotu.index(p), rotu.index(nx)
        arcL = []   # clockwise from nx to p = LEFT side
        j = (inx+1) % len(rotu)
        while j != ip:
            arcL.append(rotu[j]); j = (j+1) % len(rotu)
        arcR = [t for t in rotu if t not in (p,nx) and t not in arcL]
        left_arcs[u], right_arcs[u] = arcL, arcR
    # faces across C-edges
    leftface, rightface = {}, {}
    for i in range(n):
        u, v = cycle[i], cycle[(i+1)%n]
        leftface[(u,v)] = faceof[dart_between(u,v)]
        rightface[(u,v)] = faceof[dart_between(v,u)]
    # geometric side: mean k of left arcs vs right arcs
    lk = [k for u in cycle for (vv,k) in left_arcs[u]]
    rk = [k for u in cycle for (vv,k) in right_arcs[u]]
    out = {}
    # capL: region = cycle as-is (interior on left), forb = size of RIGHT face
    forbL = [len(faces[rightface[(cycle[i], cycle[(i+1)%n])]]) for i in range(n)]
    regionL = [(cycle[i], len(left_arcs[cycle[i]])) for i in range(n)]
    # seed adjacency: C-edges + surviving (right-side) edges between cycle verts
    adjL = {frozenset((cycle[i], cycle[(i+1)%n])) for i in range(n)}
    for u in cycle:
        for t in right_arcs[u]:
            if t in onC: adjL.add(frozenset((u,t)))
    # capR: region = reversed cycle, forb = size of LEFT face
    rev = cycle[::-1]
    forbR = []
    for i in range(n):
        a, b = rev[i], rev[(i+1)%n]   # this is C-edge (b,a) in original direction
        forbR.append(len(faces[leftface[(b,a)]]))
    regionR = [(rev[i], len(right_arcs[rev[i]])) for i in range(n)]
    adjR = {frozenset((cycle[i], cycle[(i+1)%n])) for i in range(n)}
    for u in cycle:
        for t in left_arcs[u]:
            if t in onC: adjR.add(frozenset((u,t)))
    deg = {u: DEG[u[0]] for u in cycle}
    out['capL'] = dict(region=regionL, forb=forbL, adj=adjL, deg=deg)
    out['capR'] = dict(region=regionR, forb=forbR, adj=adjR, deg=deg)
    out['left_arcs'] = left_arcs; out['right_arcs'] = right_arcs
    out['left_mean_k'] = sum(lk)/len(lk) if lk else None
    out['right_mean_k'] = sum(rk)/len(rk) if rk else None
    return out
