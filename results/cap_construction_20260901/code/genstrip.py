"""The c=3 quotient unrolled along a general primitive class U = a*omega + b*tau.
Validity: a != 0, b not in {a, 2a}, gcd(|a|,|b|)=1 (parallel-edge freedom).
Provides: lift validity check, meridian enumeration, interface extraction."""
import collections, math
from strip_lib import EDGES, ROT, OMEGA, DEG, TAU

def unroll_vec(a, b):
    return tuple(a*OMEGA[e] + b*TAU[e] for e in range(6))

def winding_vec(a, b):
    # V = c*omega + d*tau with a*d - b*c = 1
    g, c0, d0 = ext_gcd(a, b)
    assert g == 1
    # a*d0 + b*c0 = 1?? ext_gcd gives a*c0 + b*d0 = 1; want ad - bc = 1:
    # choose d = c0, c = -d0: a*c0 - b*(-d0)?? -> a*c0 + b*d0 = 1  OK
    c, d = -d0, c0
    assert a*d - b*c == 1
    return tuple(c*OMEGA[e] + d*TAU[e] for e in range(6))

def ext_gcd(a, b):
    if b == 0: return (abs(a), 1 if a > 0 else -1, 0)
    g, x, y = ext_gcd(b, a % b)
    return (g, y, x - (a//b)*y)

class GenStrip:
    def __init__(self, a, b, K=40):
        self.a, self.b = a, b
        self.U = unroll_vec(a, b)
        self.V = winding_vec(a, b)
        self.K = K
        U = self.U
        self.lift_dart = {}
        for e,(u,w) in enumerate(EDGES):
            for k in range(-K, K+1):
                A, B = (u,k), (w,k+U[e])
                self.lift_dart[(e,k,0)] = (A,B); self.lift_dart[(e,k,1)] = (B,A)
        self.dart_at = collections.defaultdict(list)
        for d,(A,B) in self.lift_dart.items(): self.dart_at[A].append(d)
        self.lsigma = {}
        for v0 in list(self.dart_at):
            v,k = v0
            ordered = []
            ok = True
            for qd in ROT[v]:
                e, side = qd//2, qd%2
                kk = k if side==0 else k-U[e]
                if (e,kk,side) not in self.lift_dart: ok=False; break
                ordered.append((e,kk,side))
            if not ok: continue
            for i,d in enumerate(ordered):
                self.lsigma[d] = ordered[(i+1)%len(ordered)]
        self.lalpha = {}
        for e in range(6):
            for k in range(-K,K+1):
                self.lalpha[(e,k,0)]=(e,k,1); self.lalpha[(e,k,1)]=(e,k,0)
        lsinv = {v:k for k,v in self.lsigma.items()}
        self.lphi = {d: lsinv[self.lalpha[d]] for d in self.lsigma
                     if self.lalpha[d] in lsinv}
        self.faceof, self.faces = {}, []
        for d in list(self.lphi):
            if d in self.faceof: continue
            walk, c, ok = [], d, True
            while c not in self.faceof and c not in walk:
                if c not in self.lphi: ok=False; break
                walk.append(c); c = self.lphi[c]
            if ok and walk and c == walk[0]:
                fid = len(self.faces)
                for dd in walk: self.faceof[dd] = fid
                self.faces.append(walk)
            else:
                for dd in walk: self.faceof[dd] = None

    def check_valid(self):
        """simplicity + alternation + embedded faces in a central window"""
        # parallel/loop
        pairs = collections.Counter()
        for d,(A,B) in self.lift_dart.items():
            if d[2] == 0:
                if A == B: return "loop"
                pairs[frozenset((A,B))] += 1
        if any(c > 1 for c in pairs.values()): return "parallel"
        # faces in a central window: sizes and no repeated vertices
        good = 0
        for f in self.faces:
            ks = [self.lift_dart[d][0][1] for d in f]
            if all(-self.K//2 <= k <= self.K//2 for k in ks):
                if len(f) not in (3,4,5): return f"face size {len(f)}"
                vs = [self.lift_dart[d][0] for d in f]
                if len(set(vs)) != len(f): return "face repeats vertex"
                good += 1
        if good < 10: return "too few interior faces"
        # alternation across central edges
        for d in self.lphi:
            e,k,side = d
            if not (-self.K//2 <= k <= self.K//2): continue
            m = self.lalpha[d]
            fa, fb = self.faceof.get(d), self.faceof.get(m)
            if fa is None or fb is None: continue
            if len(self.faces[fa]) == len(self.faces[fb]): return "face alternation fails"
            A, B = self.lift_dart[d]
            if DEG[A[0]] == DEG[B[0]]: return "degree alternation fails"
        return "OK"

    def adjacency(self):
        adj = collections.defaultdict(set)
        for d,(A,B) in self.lift_dart.items():
            if d[2]==0:
                adj[A].add(B); adj[B].add(A)
        return adj

    def dart_between(self, A, B):
        out = [d for d in self.dart_at[A] if self.lift_dart[d] == (A,B)]
        assert len(out)==1
        return out[0]

    def rotation_of(self, v0):
        v,k = v0
        out = []
        for qd in ROT[v]:
            e, side = qd//2, qd%2
            kk = k if side==0 else k-self.U[e]
            out.append(self.lift_dart[(e,kk,side)][1])
        return out

    def cycle_winding(self, path):
        n = len(path); tw = tu = 0
        for i in range(n):
            (v1,k1),(v2,k2) = path[i], path[(i+1)%n]
            cands = []
            for e,(u,w) in enumerate(EDGES):
                if (u,w)==(v1,v2) and k2==k1+self.U[e]: cands.append((e,+1))
                if (u,w)==(v2,v1) and k1==k2+self.U[e]: cands.append((e,-1))
            assert len(cands)==1, (path, i, cands)
            e,s = cands[0]
            tw += s*self.V[e]; tu += s*self.U[e]
        assert tu == 0
        return tw

    def meridians(self, maxlen, kwin=6):
        adj = self.adjacency()
        def canon(cyc):
            best=None; n=len(cyc)
            for rev in (cyc, cyc[::-1]):
                for i in range(n):
                    r = rev[i:]+rev[:i]
                    kmin = min(k for _,k in r)
                    r = tuple((v,k-kmin) for v,k in r)
                    if best is None or r < best: best = r
            return best
        found = {}
        for s in [(v,0) for v in 'xyz']:
            stack=[(s,[s],{s})]
            while stack:
                u,path,inp = stack.pop()
                for w in adj[u]:
                    if abs(w[1]) > self.K - kwin: continue
                    if w==s and len(path)>=3:
                        c = canon(tuple(path))
                        if c not in found: found[c]=list(path)
                    elif w not in inp and len(path)<maxlen:
                        stack.append((w,path+[w],inp|{w}))
        return [p for p in found.values() if abs(self.cycle_winding(p))==1]

    def cut_interfaces(self, cycle):
        n = len(cycle); onC = set(cycle)
        left_arcs, right_arcs = {}, {}
        for i in range(n):
            u = cycle[i]; p = cycle[(i-1)%n]; nx = cycle[(i+1)%n]
            rotu = self.rotation_of(u)
            ip, inx = rotu.index(p), rotu.index(nx)
            arcL = []
            j = (inx+1)%len(rotu)
            while j != ip:
                arcL.append(rotu[j]); j = (j+1)%len(rotu)
            arcR = [t for t in rotu if t not in (p,nx) and t not in arcL]
            left_arcs[u], right_arcs[u] = arcL, arcR
        leftface, rightface = {}, {}
        for i in range(n):
            u,v = cycle[i], cycle[(i+1)%n]
            leftface[(u,v)] = self.faceof[self.dart_between(u,v)]
            rightface[(u,v)] = self.faceof[self.dart_between(v,u)]
            if leftface[(u,v)] is None or rightface[(u,v)] is None:
                return None   # too close to window edge
        out = {}
        fl = [len(self.faces[rightface[(cycle[i],cycle[(i+1)%n])]]) for i in range(n)]
        regionL = [(cycle[i], len(left_arcs[cycle[i]])) for i in range(n)]
        adjL = {frozenset((cycle[i],cycle[(i+1)%n])) for i in range(n)}
        for u in cycle:
            for t in right_arcs[u]:
                if t in onC: adjL.add(frozenset((u,t)))
        rev = cycle[::-1]
        fr = []
        for i in range(n):
            A,B = rev[i], rev[(i+1)%n]
            fr.append(len(self.faces[leftface[(B,A)]]))
        regionR = [(rev[i], len(right_arcs[rev[i]])) for i in range(n)]
        adjR = {frozenset((cycle[i],cycle[(i+1)%n])) for i in range(n)}
        for u in cycle:
            for t in left_arcs[u]:
                if t in onC: adjR.add(frozenset((u,t)))
        out['capL'] = dict(region=regionL, forb=fl, adj=adjL)
        out['capR'] = dict(region=regionR, forb=fr, adj=adjR)
        out['left_arcs']=left_arcs; out['right_arcs']=right_arcs
        return out
