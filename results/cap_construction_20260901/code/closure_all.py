import sys as _s; _s.setrecursionlimit(400000)
"""Loop-pruned unbounded-depth cap search:
  - base strip (1,0): all meridians up to length 10, all admissible boundary
    degree assignments, both sides;
  - variant unrolls (a,b), |a|<=3,|b|<=4: meridians up to length 8, all degree
    assignments, both sides."""
import collections, itertools, time, sys, pickle
from strip_lib import DEG
from genstrip import GenStrip
from capsearch import Search
from math import gcd

def degree_assignments(cycle, kept_arcs):
    n = len(cycle); onC = set(cycle)
    choices = []
    for u in cycle:
        kept = kept_arcs[u]
        constr = {DEG[w[0]] for w in kept if w not in onC}
        opts = [(d, d-2-len(kept)) for d in (3,4,5)
                if d not in constr and d-2-len(kept) >= 0]
        choices.append(opts)
    for combo in itertools.product(*choices):
        dmap = {cycle[i]: combo[i][0] for i in range(n)}
        if any(dmap[cycle[i]] == dmap[cycle[(i+1)%n]] for i in range(n)): continue
        bad = False
        for u in cycle:
            for w in kept_arcs[u]:
                if w in onC and dmap[u] == dmap[w]: bad = True; break
            if bad: break
        if not bad: yield combo

def run_family(a, b, maxlen):
    gs = GenStrip(a, b, K=40)
    assert gs.check_valid() == "OK"
    merid = sorted(gs.meridians(maxlen), key=len)
    jobs = terminated = aborted = hits = 0
    deepmax = 0
    capped = []
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
                s = Search(region, p['forb'], deg, p['adj'],
                           max_new=200, max_nodes=3*10**6, loop_prune=True)
                sols = s.run()
                jobs += 1
                deepmax = max(deepmax, s.max_depth_new)
                if s.hit_max_new and not s.aborted:
                    capped.append((ci, len(cyc), side, [c[0] for c in combo]))
                if s.aborted:
                    aborted += 1
                    print(f"  ABORT ({a},{b}) cut#{ci}(len{len(cyc)}) {side} deg={[c[0] for c in combo]} nodes={s.nodes}", flush=True)
                else:
                    terminated += 1
                if sols:
                    hits += 1
                    print(f"  !!! HIT ({a},{b}) cut#{ci} {side}: {len(sols)}", flush=True)
                    pickle.dump(((a,b),cyc,side,combo,sols), open(f"HITC_{a}_{b}_{ci}_{side}_{ai}.pkl","wb"))
    print(f"unroll ({a},{b}) maxlen {maxlen}: meridians={len(merid)} jobs={jobs} "
          f"terminated_zero={terminated-hits} hits={hits} aborted={aborted} "
          f"depth_capped={len(capped)} deepest={deepmax}", flush=True)
    for c in capped[:6]: print("    capped:", c, flush=True)
    return jobs, hits, aborted

T0 = time.time()
tot = collections.Counter()
j,h,ab = run_family(1, 0, 10)
tot.update(dict(jobs=j,hits=h,ab=ab))
for a in range(1,4):
    for b in range(-4,5):
        if a==0 or b==a or b==2*a or (a,b)==(1,0): continue
        if gcd(a,abs(b)) != 1: continue
        j,h,ab = run_family(a, b, 8)
        tot.update(dict(jobs=j,hits=h,ab=ab))
print("TOTAL", dict(tot), f"{time.time()-T0:.0f}s")
