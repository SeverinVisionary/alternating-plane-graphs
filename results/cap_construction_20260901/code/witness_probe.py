import sys, time, collections
sys.setrecursionlimit(400000)
from capsearch import Search, Abort
from maputil import faces_to_rotation, emit_json, run_verifiers

MAXNEW = int(sys.argv[1]); MINNEW = int(sys.argv[2])
A, B, C = ('r',3), ('r',4), ('r',5)
deg = {A:3, B:4, C:5}
adj = {frozenset((A,B)), frozenset((B,C)), frozenset((C,A))}
t0=time.time()
s = Search([(A,1),(B,2),(C,3)], [3,3,3], deg, adj, max_new=MAXNEW, max_nodes=5*10**8)
hit = []
def onsol(sol):
    fcs, degs, nnew = sol
    if nnew >= MINNEW:
        hit.append(sol)
        raise Abort()
s.on_solution = onsol
s.run()
print(f"max_new={MAXNEW} min={MINNEW}: nodes={s.nodes} t={time.time()-t0:.1f}s hits={len(hit)} (sols below min: {len(s.solutions)-len(hit)})")
if hit:
    fcs, degs, nnew = hit[0]
    rot2 = faces_to_rotation([list(f) for f in fcs] + [[A,C,B]])
    emit_json(rot2, f"probe_order{nnew+3}.json")
    res = run_verifiers(f"probe_order{nnew+3}.json", nnew+3)
    print(f"order {nnew+3} witness:", {k: (rc, out.splitlines()[-1] if out else err[:60]) for k,(rc,out,err) in res.items()})
