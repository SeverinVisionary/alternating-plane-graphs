import collections
from strip_lib import *

K0, K1 = -8, 14
verts, rot, edgeid = build_window(K0, K1)
adj = collections.defaultdict(set)
for (v,k), cyc in rot.items():
    for nb in cyc:
        if nb is not None: adj[(v,k)].add(nb)

def canon(cyc):
    best = None; n = len(cyc)
    for rev in (cyc, cyc[::-1]):
        for i in range(n):
            r = rev[i:]+rev[:i]
            kmin = min(k for _,k in r)
            r = tuple((v,k-kmin) for v,k in r)
            if best is None or r < best: best = r
    return best

L = 10
found = {}
for s in [(v,0) for v in 'xyz']:
    stack = [(s, [s], {s})]
    while stack:
        u, path, inpath = stack.pop()
        for w in adj[u]:
            if w == s and len(path) >= 3:
                c = canon(tuple(path))
                if c not in found: found[c] = list(path)
            elif w not in inpath and len(path) < L:
                stack.append((w, path+[w], inpath|{w}))

merid = []
for c, p in found.items():
    t = cycle_winding(p)
    if abs(t) == 1: merid.append(p)
print(f"simple cycles len<={L} (canonical, through k=0): {len(found)}")
print(f"meridians (|winding|=1): {len(merid)}")
bylen = collections.Counter(len(p) for p in merid)
print("meridians by length:", dict(sorted(bylen.items())))
for p in sorted(merid, key=len):
    if len(p) <= 6:
        print(len(p), [f"{v}{k}" for v,k in p])
