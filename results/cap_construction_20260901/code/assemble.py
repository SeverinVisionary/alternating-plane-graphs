"""Assemble closed APG = capR + m periods of (a,b)-strip + capL, and verify."""
import pickle, collections, sys
from genstrip import GenStrip
from maputil import faces_to_rotation, emit_json, run_verifiers

def face_vertex_walk(gs, fc):
    return [gs.lift_dart[d][0] for d in fc]

def assemble(gs, cyc, capL_sol, capR_sol, m, tag="asm"):
    """cyc: cut cycle at position 0 (list of lift vertices).
    capL covers the LEFT side of the directed cycle; determine geometric side.
    Returns path of certificate or raises."""
    iface = gs.cut_interfaces(cyc)
    la, ra = iface['left_arcs'], iface['right_arcs']
    mean_l = sum(k for u in cyc for (v,k) in la[u]) / max(1,sum(len(la[u]) for u in cyc))
    mean_r = sum(k for u in cyc for (v,k) in ra[u]) / max(1,sum(len(ra[u]) for u in cyc))
    capL_at_plus = mean_l > mean_r     # capL covers +k side?
    # place capL at C(m_hi) if it covers +k, capR at C(0); else swap roles
    shift = (lambda vv, dk: (vv[0], vv[1]+dk))
    if capL_at_plus:
        capP, capM = capL_sol, capR_sol      # +end cap, -end cap
        cycP = [shift(v, m) for v in cyc]     # capL boundary maps by +m
        mapP = {v: shift(v, m) for v in set(cyc)}
        mapM = {v: v for v in set(cyc)}
        cycM = cyc
    else:
        capP, capM = capR_sol, capL_sol
        mapP = {v: shift(v, m) for v in set(cyc)}
        mapM = {v: v for v in set(cyc)}
        cycP = [shift(v, m) for v in cyc]
        cycM = cyc
    # surviving strip faces: dual BFS from keep-side faces of the low cut,
    # not crossing edges of either cut cycle.
    n = len(cyc)
    cutedgesM = {frozenset((cycM[i], cycM[(i+1)%n])) for i in range(n)}
    cutedgesP = {frozenset((cycP[i], cycP[(i+1)%n])) for i in range(n)}
    blocked = cutedgesM | cutedgesP
    # keep-side faces across low cut: faces on the +k side of C(0):
    # if capL_at_plus, the keep side of C(0) is the LEFT side; else RIGHT.
    seeds = set()
    for i in range(n):
        u, v = cycM[i], cycM[(i+1)%n]
        d = gs.dart_between(u, v) if capL_at_plus else gs.dart_between(v, u)
        seeds.add(gs.faceof[d])
    keep = set(seeds); stack = list(seeds)
    while stack:
        fi = stack.pop()
        fc = gs.faces[fi]
        for d in fc:
            a, b = gs.lift_dart[d]
            if frozenset((a,b)) in blocked: continue
            fj = gs.faceof.get(gs.lalpha[d])
            if fj is not None and fj not in keep:
                keep.add(fj); stack.append(fj)
    strip_faces = [face_vertex_walk(gs, gs.faces[fi]) for fi in keep]
    # sanity: all strip face vertices within cut k-range
    # rename cap faces
    def rename(sol, mapping, prefix):
        fcs, degs, nnew = sol
        out = []
        for f in fcs:
            nf = []
            for v in f:
                if isinstance(v, tuple) and v[0]=='i':
                    nf.append((prefix, v[1]))
                else:
                    nf.append(mapping[v])
            out.append(nf)
        return out
    facesP = rename(capP, mapP, 'cP')
    facesM = rename(capM, mapM, 'cM')
    allf = strip_faces + facesP + facesM
    rot = faces_to_rotation(allf)
    path = f"{tag}_m{m}.json"
    emit_json(rot, path)
    res = run_verifiers(path, len(rot))
    return path, len(rot), res, len(strip_faces)

if __name__ == '__main__':
    gs = GenStrip(2,3,K=40)
    ab, cyc, side, comboL, solsL = pickle.load(open('HITV_2_3_0_capL_2.pkl','rb'))
    ab2, cyc2, side2, comboR, solsR = pickle.load(open('HITV_2_3_0_capR_1.pkl','rb'))
    assert cyc == cyc2
    print("cut:", [f"{v}{k}" for v,k in cyc], "capL degs", [c[0] for c in comboL], "capR degs", [c[0] for c in comboR])
    for m in (3,4,5,6):
        try:
            path, order, res, nsf = assemble(gs, cyc, solsL[0], solsR[0], m, tag="pump23")
            ok = all(rc==0 for rc,_,_ in res.values())
            print(f"m={m}: order={order} strip_faces={nsf} verify={'PASS' if ok else 'FAIL'}")
            if not ok:
                for k,(rc,o,e) in res.items():
                    if rc: print("   ", k, (e or o).splitlines()[-1][:150])
        except AssertionError as e:
            print(f"m={m}: assembly failed: {e}")
