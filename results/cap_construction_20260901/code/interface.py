"""Extract cap interfaces for meridian cuts of the c=3 strip."""
import collections
from strip_lib import *

# Build a big lift with full dart-level structure (like periodic_strip.py)
K = 20
lift_dart = {}
for e, (u, w) in enumerate(EDGES):
    for k in range(-K, K+1):
        a, b = (u, k), (w, k + OMEGA[e])
        lift_dart[(e,k,0)] = (a,b); lift_dart[(e,k,1)] = (b,a)
dart_at = collections.defaultdict(list)
for d,(a,b) in lift_dart.items(): dart_at[a].append(d)
lsigma = {}
for v0 in list(dart_at):
    v,k = v0
    ordered = []
    for qd in ROT[v]:
        e, side = qd//2, qd%2
        kk = k if side==0 else k - OMEGA[e]
        ordered.append((e,kk,side))
    if any(d not in lift_dart for d in ordered): continue
    for i,d in enumerate(ordered): lsigma[d] = ordered[(i+1)%len(ordered)]
lalpha = {}
for e in range(6):
    for k in range(-K,K+1):
        lalpha[(e,k,0)]=(e,k,1); lalpha[(e,k,1)]=(e,k,0)
lsinv = {v:k for k,v in lsigma.items()}
# verify.py convention: dart (u,v) advances along face on its LEFT via phi(d)=sigma^{-1}(alpha(d))
lphi = {d: lsinv[lalpha[d]] for d in lsigma if lalpha[d] in lsinv}
faceof = {}
faces = []
for d in list(lphi):
    if d in faceof: continue
    walk, c, ok = [], d, True
    while c not in faceof:
        if c not in lphi: ok=False; break
        faceof[c] = len(faces); walk.append(c); c = lphi[c]
    if ok and c==d:
        faces.append(walk)
    else:
        for dd in walk: faceof[dd] = None
facesize = {i: len(f) for i,f in enumerate(faces)}

def dart_between(a, b):
    """lift dart from vertex a to vertex b (unique)."""
    out = [d for d in dart_at[a] if lift_dart[d] == (a,b)]
    assert len(out)==1, (a,b,out)
    return out[0]

def rotation_of(v0):
    """clockwise neighbour list of lift vertex v0"""
    v,k = v0
    out = []
    for qd in ROT[v]:
        e, side = qd//2, qd%2
        kk = k if side==0 else k - OMEGA[e]
        d = (e,kk,side)
        out.append(lift_dart[d][1])
    return out

def interface(cycle, cap_side):
    """cycle: list of lift vertices, in order. cap_side: 'L' or 'R' relative
    to traversal direction. Returns list over boundary positions i of
    dict(vertex, deg, kept (strip edges), owed, face_across_next_Cedge_size)
    where face across C-edge (i -> i+1) is the STRIP face that survives
    (on the R side of dart i->i+1 if cap is L, else L side)."""
    n = len(cycle)
    out = []
    for i in range(n):
        u = cycle[i]; p = cycle[(i-1)%n]; nx = cycle[(i+1)%n]
        rotu = rotation_of(u)
        ip, inx = rotu.index(p), rotu.index(nx)
        # clockwise arc from nx to p exclusive:
        arc_nx_to_p = []
        j = (inx+1) % len(rotu)
        while j != ip:
            arc_nx_to_p.append(rotu[j]); j = (j+1)%len(rotu)
        arc_p_to_nx = [w for w in rotu if w not in (p,nx) and w not in arc_nx_to_p]
        # Determine which arc is on the Left of the directed cycle.
        # For dart u->nx, the face on its left is phi-face of dart(u,nx).
        # Vertices adjacent in clockwise rotation *after* nx (i.e., arc_nx_to_p
        # beginning) lie on the ... use a face test instead:
        # the corner between darts (u->nx) and next-clockwise dart at u belongs
        # to the face on the LEFT of u->nx?  In verify convention, face on left
        # of (u,v) contains corner at v between (v->u's predecessor)... safer:
        # compute face on left of dart u->p: contains corner at u between p and
        # the dart AFTER p clockwise?  Let's determine empirically below.
        out.append(dict(v=u, rot=rotu, p=p, nx=nx,
                        arc_nx_to_p=arc_nx_to_p, arc_p_to_nx=arc_p_to_nx))
    return out

# Empirical: figure out which side is left of a directed dart, using faces.
# Face on the left of dart a->b (verify convention) is the face of that dart in lphi.
# The corner of that face at b lies between the dart b->? ... simpler: the face
# on the left of a->b contains dart a->b itself. A vertex w in rotation of a is
# 'immediately counterclockwise' ... we can identify sides by checking which arc
# vertices appear in the two faces adjacent to edge (a,b).
def face_left_of(a,b):
    return faceof[dart_between(a,b)]

C3 = [('x',0),('y',-1),('z',-2)]
n = len(C3)
print("=== meridian C3:", C3)
for i in range(n):
    u, nx = C3[i], C3[(i+1)%n]
    fl = face_left_of(u,nx); fr = face_left_of(nx,u)
    print(f" edge {u}->{nx}: face left size {facesize.get(fl)}, right size {facesize.get(fr)}")
info = interface(C3, 'L')
for d in info:
    print(f" vertex {d['v']}: rot={d['rot']} p={d['p']} nx={d['nx']}")
    print(f"   arc(nx->p clockwise)={d['arc_nx_to_p']}")
    print(f"   arc(p->nx clockwise)={d['arc_p_to_nx']}")
