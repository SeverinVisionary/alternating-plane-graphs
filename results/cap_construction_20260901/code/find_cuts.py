import collections, itertools, sys
from strip_lib import *

K0, K1 = -8, 14
verts, rot, edgeid = build_window(K0, K1)
adj = collections.defaultdict(set)
for (v,k), cyc in rot.items():
    for nb in cyc:
        if nb is not None:
            adj[(v,k)].add(nb)

# sanity: interior degrees
for v,k in sorted(verts, key=str):
    if 0 <= k <= 6:
        assert len(adj[(v,k)]) == DEG[v], ((v,k), adj[(v,k)])

def separates(cycle_vs):
    """Does deleting cycle_vs disconnect ('x',K0+2) from ('x',K1-2)?"""
    banned = set(cycle_vs)
    src, dst = ('x', K0+1), ('x', K1-1)
    if src in banned or dst in banned: return None
    seen = {src}; stack=[src]
    while stack:
        u = stack.pop()
        if u == dst: return False
        for w in adj[u]:
            if w not in banned and w not in seen:
                seen.add(w); stack.append(w)
    return True

# enumerate simple cycles up to length L through a vertex with k in {0,1}
L = 9
found = {}
def canon(cyc):
    # canonical form up to rotation, reflection, and k-translation
    best = None
    n = len(cyc)
    for rev in (cyc, cyc[::-1]):
        for i in range(n):
            r = rev[i:]+rev[:i]
            kmin = min(k for _,k in r)
            r = tuple((v,k-kmin) for v,k in r)
            if best is None or r < best: best = r
    return best

start_set = [(v,k) for v in 'xyz' for k in (0,)]
for s in start_set:
    # DFS for cycles starting/ending at s, s is minimal by convention not enforced (we canonicalize)
    stack = [(s, [s], {s})]
    while stack:
        u, path, inpath = stack.pop()
        for w in adj[u]:
            if w == s and len(path) >= 3:
                c = canon(tuple(path))
                if c not in found:
                    found[c] = list(path)
            elif w not in inpath and len(path) < L:
                stack.append((w, path+[w], inpath|{w}))

ess = []
for c, path in found.items():
    r = separates(path)
    if r:
        ess.append(path)
print(f"simple cycles up to length {L} through k=0 (up to translation/rotation/reflection): {len(found)}")
print(f"essential (end-separating): {len(ess)}")
bylen = collections.Counter(len(p) for p in ess)
print("essential by length:", dict(sorted(bylen.items())))
for p in sorted(ess, key=len)[:20]:
    print(len(p), p)
