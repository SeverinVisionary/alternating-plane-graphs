"""Enumerate all c=3 torus quotients: vertices x(3),y(4),z(5); forced edge
multiset 1*(x,y), 2*(x,z), 3*(y,z).  Count alternating torus maps."""
import itertools, collections
E = [('x','y'), ('x','z'), ('x','z'), ('y','z'), ('y','z'), ('y','z')]
# darts: 2e (first endpoint), 2e+1 (second)
DEG = {'x':3, 'y':4, 'z':5}
at = {'x': [0, 2, 4], 'y': [1, 6, 8, 10], 'z': [3, 5, 7, 9, 11]}
alpha = {}
for e in range(6): alpha[2*e]=2*e+1; alpha[2*e+1]=2*e
vert_of = {}
for v, ds in at.items():
    for d in ds: vert_of[d]=v
good = []
for px in itertools.permutations(at['x'][1:]):
    rx = (at['x'][0],)+px
    for py in itertools.permutations(at['y'][1:]):
        ry = (at['y'][0],)+py
        for pz in itertools.permutations(at['z'][1:]):
            rz = (at['z'][0],)+pz
            sigma = {}
            for cyc in (rx,ry,rz):
                for i,d in enumerate(cyc): sigma[d]=cyc[(i+1)%len(cyc)]
            sinv = {v:k for k,v in sigma.items()}
            phi = {d: sinv[alpha[d]] for d in range(12)}
            seen=set(); faces=[]
            for d in range(12):
                if d in seen: continue
                w=[]; c=d
                while c not in seen:
                    seen.add(c); w.append(c); c=phi[c]
                faces.append(w)
            if len(faces) != 3: continue          # torus
            sizes = sorted(len(f) for f in faces)
            if sizes != [3,4,5]: continue
            fid = {}
            for i,f in enumerate(faces):
                for d in f: fid[d]=i
            ok=True
            for e in range(6):
                if fid[2*e]==fid[2*e+1]: ok=False; break
                if len(faces[fid[2*e]])==len(faces[fid[2*e+1]]): ok=False; break
            if not ok: continue
            # faces must not repeat a vertex? on torus quotient they can (lift matters); skip
            good.append((rx,ry,rz))
print("alternating torus maps with V=3 (raw rotation systems):", len(good))
# classify up to mirror (reverse all rotations) -- relabelling is trivial here
# (vertices distinguished by degree, darts fixed by edge naming); the dart
# naming freedom = permuting parallel edges: quotient by that.
import itertools as it
def canon(rs):
    rx,ry,rz = rs
    forms = set()
    # dart renaming: permute e1<->e2 (x,z) darts {2,3}<->{4,5}; permute e3,e4,e5 (y,z): {6,7},{8,9},{10,11}
    for pxz in it.permutations([(2,3),(4,5)]):
        for pyz in it.permutations([(6,7),(8,9),(10,11)]):
            m = {0:0,1:1}
            for (a,b),(c,d) in zip([(2,3),(4,5)], pxz): m[a]=c; m[b]=d
            for (a,b),(c,d) in zip([(6,7),(8,9),(10,11)], pyz): m[a]=c; m[b]=d
            for flip in (False,True):
                def f(cyc):
                    cc = tuple(m[d] for d in cyc)
                    if flip: cc = cc[::-1]
                    i = cc.index(min(cc))
                    return cc[i:]+cc[:i]
                forms.add((f(rx),f(ry),f(rz)))
    return min(forms)
classes = {canon(rs) for rs in good}
print("up to parallel-edge renaming and mirror:", len(classes))
for c in classes: print(c)
