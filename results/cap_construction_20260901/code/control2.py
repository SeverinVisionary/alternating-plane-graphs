import json, collections, itertools
from maputil import rotation_to_faces, faces_to_rotation, emit_json, run_verifiers
from capsearch import Search

d = json.load(open('certificates/known/ghent17.json'))
rot = {row['id']: list(row['clockwise']) for row in d['vertices']}
faces = rotation_to_faces(rot)
deg = {v: len(ns) for v, ns in rot.items()}
adjG = {frozenset((u,w)) for u,ns in rot.items() for w in ns}
# dart -> face id
fid = {}
for i,f in enumerate(faces):
    for j in range(len(f)):
        fid[(f[j], f[(j+1)%len(f)])] = i

def edges_of_face(i):
    f = faces[i]
    return {frozenset((f[j], f[(j+1)%len(f)])) for j in range(len(f))}

# enumerate simple cycles up to length 6
cycles = set()
def canon(cyc):
    best=None; n=len(cyc)
    for rev in (cyc, cyc[::-1]):
        for i in range(n):
            r = rev[i:]+rev[:i]
            if best is None or r < best: best=r
    return best
adjl = {v: set(ns) for v,ns in rot.items()}
for s in rot:
    stack=[(s,[s],{s})]
    while stack:
        u,path,inp = stack.pop()
        for w in adjl[u]:
            if w==s and len(path)>=3:
                cycles.add(canon(tuple(path)))
            elif w not in inp and len(path)<6 and w>s:
                stack.append((w,path+[w],inp|{w}))
print("cycles up to len 6:", len(cycles))

tested = found_ok = repro = 0
fail_examples = []
for cyc in sorted(cycles, key=len):
    n = len(cyc)
    Cedges = {frozenset((cyc[i], cyc[(i+1)%n])) for i in range(n)}
    # faces strictly inside: dual BFS from left faces of directed cycle
    left_seeds = {fid[(cyc[i], cyc[(i+1)%n])] for i in range(n)}
    right_seeds = {fid[(cyc[(i+1)%n], cyc[i])] for i in range(n)}
    if left_seeds & right_seeds: continue
    inside = set(left_seeds)
    stack = list(left_seeds)
    while stack:
        i = stack.pop()
        for e in edges_of_face(i):
            if e in Cedges: continue
            a,b = tuple(e)
            for dd in ((a,b),(b,a)):
                j = fid[dd]
                if j not in inside:
                    inside.add(j); stack.append(j)
    if inside & right_seeds: continue  # cycle not separating properly (shouldn't happen)
    inside_vertices = {v for i in inside for v in faces[i]} - set(cyc)
    if not (1 <= len(inside_vertices) <= 9): continue
    # interface
    onC = set(cyc)
    ok = True
    region = []
    forb = []
    for i in range(n):
        u = cyc[i]
        rem = sum(1 for w in adjl[u] if w in inside_vertices)
        # plus edges to other C vertices that lie inside (chords inside)
        for w in adjl[u]:
            if w in onC and frozenset((u,w)) not in Cedges:
                # this chord is inside iff its two faces are inside
                a,b = u,w
                if fid[(a,b)] in inside and fid[(b,a)] in inside:
                    rem += 1
        region.append((u, rem))
        e_dart = (cyc[(i+1)%n], cyc[i])  # right face = outside face
        forb.append(len(faces[fid[e_dart]]))
    outside = [f for i,f in enumerate(faces) if i not in inside]
    adj_seed = {e for e in adjG if not (e & inside_vertices)}
    # remove chords that are inside (they were counted in rem and deleted)
    adj_seed = {e for e in adj_seed if not (e <= onC and frozenset(e) not in Cedges
                and fid[tuple(e)] in inside and fid[tuple(e)[::-1]] in inside)}
    degs = {v: deg[v] for v in rot if v not in inside_vertices}
    s = Search(region, forb, degs, adj_seed, max_new=len(inside_vertices)+2, max_solutions=300)
    sols = s.run()
    tested += 1
    ok_any = False; rep = False
    inside_face_sets = {frozenset(faces[i]) for i in inside}
    for fcs, dd, nnew in sols:
        allf = [list(f) for f in outside] + [list(f) for f in fcs]
        try:
            rot2 = faces_to_rotation(allf)
        except AssertionError:
            continue
        emit_json(rot2, 'c2.json')
        res = run_verifiers('c2.json', len(rot2))
        if all(rc==0 for rc,_,_ in res.values()):
            ok_any = True
            if nnew == len(inside_vertices):
                rep = True   # candidate reproduction (same size)
    found_ok += ok_any
    repro += rep
    if not rep:
        fail_examples.append((cyc, len(inside_vertices), len(sols)))
print(f"tested disk cuts: {tested}; with >=1 verified filling: {found_ok}; with same-size filling found: {repro}")
for ex in fail_examples[:10]:
    print("MISS:", ex)
