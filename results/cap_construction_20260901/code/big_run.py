import collections, itertools, time, sys
from strip_lib import *
from cutlib import cut_interfaces, rotation_of
from capsearch import Search

# --- enumerate all meridians up to length L ---
K0, K1 = -8, 14
verts, rotw, _ = build_window(K0, K1)
adj = collections.defaultdict(set)
for (v,k), cyc in rotw.items():
    for nb in cyc:
        if nb is not None: adj[(v,k)].add(nb)
def canon(cyc):
    best=None; n=len(cyc)
    for rev in (cyc, cyc[::-1]):
        for i in range(n):
            r = rev[i:]+rev[:i]
            kmin = min(k for _,k in r)
            r = tuple((v,k-kmin) for v,k in r)
            if best is None or r < best: best = r
    return best
L = int(sys.argv[1]) if len(sys.argv)>1 else 10
MAXNEW = int(sys.argv[2]) if len(sys.argv)>2 else 40
found = {}
for s in [(v,0) for v in 'xyz']:
    stack=[(s,[s],{s})]
    while stack:
        u,path,inp = stack.pop()
        for w in adj[u]:
            if w==s and len(path)>=3:
                c = canon(tuple(path))
                if c not in found: found[c]=list(path)
            elif w not in inp and len(path)<L:
                stack.append((w,path+[w],inp|{w}))
merid = [p for p in found.values() if abs(cycle_winding(p))==1]
merid.sort(key=len)
print(f"meridians up to length {L}: {len(merid)}")

def degree_assignments(cycle, arcs_capside, arcs_keptside):
    """joint final-degree choices for cut vertices."""
    n = len(cycle)
    onC = set(cycle)
    choices = []
    for u in cycle:
        kept = arcs_keptside[u]
        constr = {DEG[w[0]] for w in kept if w not in onC}
        opts = []
        for d in (3,4,5):
            if d in constr: continue
            rem = d - 2 - len(kept)
            if rem < 0: continue
            opts.append((d, rem))
        choices.append(opts)
    out = []
    for combo in itertools.product(*choices):
        ok = True
        dmap = {cycle[i]: combo[i][0] for i in range(n)}
        for i in range(n):
            u, v = cycle[i], cycle[(i+1)%n]
            if dmap[u] == dmap[v]: ok=False; break
        if not ok: continue
        # kept neighbours that are themselves cut vertices (kept chords)
        for u in cycle:
            for w in arcs_keptside[u]:
                if w in onC and dmap[u] == dmap[w]: ok=False; break
            if not ok: break
        if ok:
            out.append(combo)
    return out

results = []
t00 = time.time()
for ci, cyc in enumerate(merid):
    iface = cut_interfaces(cyc)
    for side in ('capL','capR'):
        p = iface[side]
        cap_arcs  = iface['left_arcs'] if side=='capL' else iface['right_arcs']
        kept_arcs = iface['right_arcs'] if side=='capL' else iface['left_arcs']
        cycle_dir = [v for v,_ in p['region']]  # order matching region
        assigns = degree_assignments(cycle_dir, cap_arcs, kept_arcs)
        for ai, combo in enumerate(assigns):
            region = [(cycle_dir[i], combo[i][1]) for i in range(len(cycle_dir))]
            deg = {cycle_dir[i]: combo[i][0] for i in range(len(cycle_dir))}
            s = Search(region, p["forb"], deg, p["adj"], max_new=MAXNEW, max_nodes=3000000)
            sols = s.run()
            tag = f"cut#{ci}(len{len(cyc)}) {side} deg={[c[0] for c in combo]}"
            results.append((tag, len(sols), s.nodes, s.max_depth_new, s.hit_max_new)); print(f"{tag}: sols={len(sols)} nodes={s.nodes} deep={s.max_depth_new} hit={s.hit_max_new} aborted={s.aborted}", flush=True)
            if sols:
                print("!!! FILLINGS FOUND:", tag, len(sols))
                import pickle
                pickle.dump((cyc, side, combo, sols), open(f"HIT_{ci}_{side}_{ai}.pkl","wb"))
nz = [r for r in results if r[1]>0]
print(f"jobs: {len(results)}, with fillings: {len(nz)}, elapsed {time.time()-t00:.0f}s")
hist = collections.Counter()
for tag, ns, nodes, deep, hit in results:
    hist[(ns>0, deep>=MAXNEW or hit>0)] += 1
print("histogram (has_fillings, hit_depth_cap):", dict(hist))
mx = max(results, key=lambda r: r[2])
print("largest tree:", mx)
