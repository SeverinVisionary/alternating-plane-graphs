import sys, time, random
sys.setrecursionlimit(400000)
from capsearch import Search, Abort
from maputil import faces_to_rotation, emit_json, run_verifiers

SEED = int(sys.argv[1]); MAXNEW = int(sys.argv[2]); MINNEW = int(sys.argv[3])
NODES = int(float(sys.argv[4]))
A, B, C = ('r',3), ('r',4), ('r',5)
deg = {A:3, B:4, C:5}
adj = {frozenset((A,B)), frozenset((B,C)), frozenset((C,A))}
t0=time.time()
s = Search([(A,1),(B,2),(C,3)], [3,3,3], deg, adj, max_new=MAXNEW,
           max_nodes=NODES, rng=random.Random(SEED))
hits=[]
def onsol(sol):
    fcs, degs, nnew = sol
    if nnew >= MINNEW:
        hits.append(sol)
        rot2 = faces_to_rotation([list(f) for f in fcs] + [[A,C,B]])
        emit_json(rot2, f"TARGET_order{nnew+3}_seed{SEED}.json")
        res = run_verifiers(f"TARGET_order{nnew+3}_seed{SEED}.json", nnew+3)
        print(f"[seed {SEED}] ORDER {nnew+3} WITNESS", {k:rc for k,(rc,o,e) in res.items()},
              f"t={time.time()-t0:.0f}s nodes={s.nodes}", flush=True)
        raise Abort()
s.on_solution = onsol
s.run()
print(f"[seed {SEED}] done: nodes={s.nodes} aborted={s.aborted} hits={len(hits)} small_sols={len(s.solutions)-len(hits)} t={time.time()-t0:.0f}s", flush=True)
