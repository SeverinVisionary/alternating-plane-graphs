"""Closed-map enumeration: a closed (3,4,5)-APG = one rooted triangle face
(degrees 3,4,5) + a disk filling of its complement."""
import sys, time, collections
sys.setrecursionlimit(400000)
from capsearch import Search
from maputil import faces_to_rotation, emit_json, run_verifiers

MAXNEW = int(sys.argv[1]) if len(sys.argv) > 1 else 14
A, B, C = ('r',3), ('r',4), ('r',5)
deg = {A:3, B:4, C:5}
adj = {frozenset((A,B)), frozenset((B,C)), frozenset((C,A))}
region = [(A,1),(B,2),(C,3)]
forb = [3,3,3]
t0 = time.time()
sols = []
s = Search(region, forb, deg, adj, max_new=MAXNEW, max_nodes=2*10**8)
res = s.run()
print(f"max_new={MAXNEW}: raw fillings={len(res)} nodes={s.nodes} aborted={s.aborted} t={time.time()-t0:.1f}s")
bysize = collections.Counter(nnew+3 for _,_,nnew in res)
print("orders found (with multiplicity):", dict(sorted(bysize.items())))
# verify a sample of each order and dedupe by canonical certificate
import json, hashlib
seen = {}
for fcs, degs, nnew in res:
    allf = [list(f) for f in fcs] + [[A,C,B]]   # add root triangle, reversed orientation
    try:
        rot2 = faces_to_rotation(allf)
    except AssertionError as e:
        print("ASSEMBLY FAIL", e); continue
    path = f"closed_{nnew+3}.json"
    emit_json(rot2, path)
    # canonical string for dedupe: use verify output + sorted degree seq? cheap iso-invariant:
    key = (len(rot2), )
    out = run_verifiers(path, len(rot2))
    okv = all(rc==0 for rc,_,_ in out.values())
    seen.setdefault(nnew+3, []).append(okv)
for order, oks in sorted(seen.items()):
    print(f"order {order}: {len(oks)} fillings, verifier-pass {sum(oks)}/{len(oks)}")
