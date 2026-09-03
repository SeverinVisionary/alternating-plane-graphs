"""Generalized assembly: minus-end cap + strip + plus-end cap, cuts may differ."""
import pickle, collections, glob
from genstrip import GenStrip
from maputil import faces_to_rotation, emit_json, run_verifiers

def face_vertex_walk(gs, fc):
    return [gs.lift_dart[d][0] for d in fc]

def capL_at_plus(gs, cyc):
    iface = gs.cut_interfaces(cyc)
    la, ra = iface['left_arcs'], iface['right_arcs']
    ml = sum(k for u in cyc for (v,k) in la[u]) / max(1, sum(len(la[u]) for u in cyc))
    mr = sum(k for u in cyc for (v,k) in ra[u]) / max(1, sum(len(ra[u]) for u in cyc))
    return ml > mr

def assemble_mixed(gs, cycM, sideM, solM, cycP, sideP, solP, tP, tag):
    """cycM at translation 0 must carry the cap covering -k (side sideM);
       cycP at translation tP carries the cap covering +k."""
    shift = lambda vv, dk: (vv[0], vv[1] + dk)
    cycPt = [shift(v, tP) for v in cycP]
    n1, n2 = len(cycM), len(cycPt)
    if set(cycM) & set(cycPt): return None  # overlapping cuts
    eM = {frozenset((cycM[i], cycM[(i+1)%n1])) for i in range(n1)}
    eP = {frozenset((cycPt[i], cycPt[(i+1)%n2])) for i in range(n2)}
    blocked = eM | eP
    # keep side of cycM = the +k side. If capL_at_plus(cycM), +k side is LEFT.
    Lp = capL_at_plus(gs, cycM)
    seeds = set()
    for i in range(n1):
        u, v = cycM[i], cycM[(i+1)%n1]
        d = gs.dart_between(u, v) if Lp else gs.dart_between(v, u)
        seeds.add(gs.faceof[d])
    keep = set(seeds); stack = list(seeds)
    while stack:
        fi = stack.pop()
        if fi is None: return None
        for d in gs.faces[fi]:
            a, b = gs.lift_dart[d]
            if frozenset((a, b)) in blocked: continue
            fj = gs.faceof.get(gs.lalpha[d])
            if fj is None: return None
            if fj not in keep:
                keep.add(fj); stack.append(fj)
        if len(keep) > 4000: return None  # runaway: cuts on same side
    def rename(sol, mapping, prefix):
        fcs, degs, nnew = sol
        out = []
        for f in fcs:
            out.append([ (prefix, v[1]) if (isinstance(v, tuple) and v[0]=='i')
                         else mapping[v] for v in f ])
        return out
    facesM = rename(solM, {v: v for v in cycM}, 'cM')
    facesP = rename(solP, {v: shift(v, tP) for v in cycP}, 'cP')
    strip_faces = [face_vertex_walk(gs, gs.faces[fi]) for fi in keep]
    try:
        rot = faces_to_rotation(strip_faces + facesM + facesP)
    except AssertionError:
        return None
    path = f"{tag}.json"
    emit_json(rot, path)
    return path, len(rot)

def load_inventory():
    inv = []
    for f in sorted(glob.glob('HITV_2_3_*.pkl')):
        ab, cyc, side, combo, sols = pickle.load(open(f, 'rb'))
        bysize = {}
        for s in sols:
            bysize.setdefault(s[2], s)
        inv.append(dict(file=f, cyc=cyc, side=side, degs=[c[0] for c in combo],
                        sols=bysize))
    return inv

if __name__ == '__main__':
    gs = GenStrip(2, 3, K=60)
    inv = load_inventory()
    # classify: which (cut, side) covers +k?
    plus_caps, minus_caps = [], []
    cyc_cache = {}
    for item in inv:
        key = tuple(item['cyc'])
        if key not in cyc_cache:
            cyc_cache[key] = capL_at_plus(gs, item['cyc'])
        Lp = cyc_cache[key]
        covers_plus = (item['side'] == 'capL') == Lp
        (plus_caps if covers_plus else minus_caps).append(item)
    print(f"plus-end caps: {len(plus_caps)} files; minus-end caps: {len(minus_caps)} files")
    # find a verified base order for one pair, then order arithmetic per sizes
    # brute force: iterate pairs x sizes, assemble at a base t, record order
    targets = set(list(range(46,57)) + list(range(67,75)) + list(range(88,93)) + [109,110])
    achieved = {}   # order -> (desc)
    import itertools, sys
    for M in minus_caps:
        for P in plus_caps:
            for szM, solM in sorted(M['sols'].items()):
                for szP, solP in sorted(P['sols'].items()):
                    # base translation: enough to separate
                    r = assemble_mixed(gs, M['cyc'], M['side'], solM,
                                       P['cyc'], P['side'], solP, 6,
                                       tag="tmp_asm")
                    if r is None: continue
                    path, order = r
                    base = order - 18   # order at t: base + 3t (t=6 here)
                    # which targets are hit at some t >= minimal?
                    for tgt in sorted(targets - set(achieved)):
                        if (tgt - order) % 3 == 0:
                            t = 6 + (tgt - order)//3
                            if t < 2: continue
                            rr = assemble_mixed(gs, M['cyc'], M['side'], solM,
                                                P['cyc'], P['side'], solP, t,
                                                tag=f"TARGET_{tgt}")
                            if rr is None: continue
                            p2, o2 = rr
                            assert o2 == tgt, (o2, tgt)
                            res = run_verifiers(p2, tgt)
                            if all(rc==0 for rc,_,_ in res.values()):
                                achieved[tgt] = (M['file'], szM, P['file'], szP, t)
                                print(f"TARGET {tgt}: PASS both verifiers  "
                                      f"[{M['file']}#{szM} + t={t} + {P['file']}#{szP}]", flush=True)
                    break
                else:
                    continue
                break
        # stop early if all done
        if targets <= set(achieved): break
    print()
    print(f"achieved {len(achieved)}/26 targets:", sorted(achieved))
    missing = sorted(targets - set(achieved))
    print("missing:", missing)
