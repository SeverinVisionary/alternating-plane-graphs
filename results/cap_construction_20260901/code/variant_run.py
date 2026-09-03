import collections, itertools, time, sys, pickle
from strip_lib import DEG
from genstrip import GenStrip
from capsearch import Search
from math import gcd

MAXLEN = int(sys.argv[1]) if len(sys.argv)>1 else 7
MAXNEW = int(sys.argv[2]) if len(sys.argv)>2 else 25

def degree_assignments(cycle, kept_arcs):
    n = len(cycle); onC = set(cycle)
    choices = []
    for u in cycle:
        kept = kept_arcs[u]
        constr = {DEG[w[0]] for w in kept if w not in onC}
        opts = []
        for d in (3,4,5):
            if d in constr: continue
            rem = d - 2 - len(kept)
            if rem < 0: continue
            opts.append((d, rem))
        choices.append(opts)
    for combo in itertools.product(*choices):
        dmap = {cycle[i]: combo[i][0] for i in range(n)}
        ok = all(dmap[cycle[i]] != dmap[cycle[(i+1)%n]] for i in range(n))
        if ok:
            for u in cycle:
                for w in kept_arcs[u]:
                    if w in onC and dmap[u]==dmap[w]: ok=False; break
                if not ok: break
        if ok: yield combo

cands = []
for a in range(1,4):
    for b in range(-4,5):
        if a==0 or b==a or b==2*a: continue
        if gcd(a,abs(b)) != 1: continue
        if (a,b)==(1,0): continue   # base strip done separately
        cands.append((a,b))
total_jobs = 0; hits = 0
for (a,b) in cands:
    gs = GenStrip(a,b,K=40)
    v = gs.check_valid()
    assert v=="OK", (a,b,v)
    merid = sorted(gs.meridians(MAXLEN), key=len)
    print(f"== unroll ({a},{b}): {len(merid)} meridians up to len {MAXLEN}", flush=True)
    for ci, cyc in enumerate(merid):
        iface = gs.cut_interfaces(cyc)
        if iface is None: continue
        for side in ('capL','capR'):
            p = iface[side]
            kept = iface['right_arcs'] if side=='capL' else iface['left_arcs']
            cdir = [vv for vv,_ in p['region']]
            for ai, combo in enumerate(degree_assignments(cdir, kept)):
                region = [(cdir[i], combo[i][1]) for i in range(len(cdir))]
                deg = {cdir[i]: combo[i][0] for i in range(len(cdir))}
                s = Search(region, p["forb"], deg, p["adj"], max_new=MAXNEW, max_nodes=3000000)
                sols = s.run()
                total_jobs += 1
                if s.aborted: print(f"   ABORT(node-budget) unroll({a},{b}) cut#{ci} {side} deg={[c[0] for c in combo]}", flush=True)
                if sols:
                    hits += 1
                    print(f"!!! HIT unroll({a},{b}) cut#{ci} {side} deg={[c[0] for c in combo]}: {len(sols)} fillings", flush=True)
                    pickle.dump(((a,b), cyc, side, combo, sols),
                                open(f"HITV_{a}_{b}_{ci}_{side}_{ai}.pkl","wb"))
    print(f"   jobs so far {total_jobs}, hits {hits}", flush=True)
print("DONE", total_jobs, "jobs,", hits, "hits")
