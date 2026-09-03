import json, collections, sys
from maputil import rotation_to_faces, faces_to_rotation, emit_json, run_verifiers
from capsearch import Search

def test_cert(certpath, maxlen=8, maxinner=12, maxcuts=200):
    d = json.load(open(certpath))
    rot = {row['id']: list(row['clockwise']) for row in d['vertices']}
    faces = rotation_to_faces(rot)
    deg = {v: len(ns) for v, ns in rot.items()}
    adjG = {frozenset((u,w)) for u,ns in rot.items() for w in ns}
    fid = {}
    for i,f in enumerate(faces):
        for j in range(len(f)):
            fid[(f[j], f[(j+1)%len(f)])] = i
    def edges_of_face(i):
        f = faces[i]
        return {frozenset((f[j], f[(j+1)%len(f)])) for j in range(len(f))}
    cycles = set()
    def canon(cyc):
        best=None
        for rev in (cyc, cyc[::-1]):
            for i in range(len(cyc)):
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
                elif w not in inp and len(path)<maxlen and w>s:
                    stack.append((w,path+[w],inp|{w}))
    tested=found_ok=repro=0; fails=[]
    nsols_hist = collections.Counter()
    for cyc in sorted(cycles, key=len):
        if tested >= maxcuts: break
        n=len(cyc)
        Cedges = {frozenset((cyc[i], cyc[(i+1)%n])) for i in range(n)}
        left_seeds = {fid[(cyc[i], cyc[(i+1)%n])] for i in range(n)}
        right_seeds = {fid[(cyc[(i+1)%n], cyc[i])] for i in range(n)}
        if left_seeds & right_seeds: continue
        inside=set(left_seeds); stack=list(left_seeds)
        while stack:
            i=stack.pop()
            for e in edges_of_face(i):
                if e in Cedges: continue
                a,b=tuple(e)
                for dd in ((a,b),(b,a)):
                    j=fid[dd]
                    if j not in inside: inside.add(j); stack.append(j)
        if inside & right_seeds: continue
        inside_vertices={v for i in inside for v in faces[i]}-set(cyc)
        if not (1<=len(inside_vertices)<=maxinner): continue
        onC=set(cyc)
        region=[];forb=[]
        for i in range(n):
            u=cyc[i]
            rem=sum(1 for w in adjl[u] if w in inside_vertices)
            for w in adjl[u]:
                if w in onC and frozenset((u,w)) not in Cedges:
                    if fid[(u,w)] in inside and fid[(w,u)] in inside: rem+=1
            region.append((u,rem))
            forb.append(len(faces[fid[(cyc[(i+1)%n], cyc[i])]]))
        outside=[f for i,f in enumerate(faces) if i not in inside]
        adj_seed={e for e in adjG if not (e & inside_vertices)}
        adj_seed={e for e in adj_seed if not (e<=onC and frozenset(e) not in Cedges
                  and fid[tuple(e)] in inside and fid[tuple(e)[::-1]] in inside)}
        degs={v:deg[v] for v in rot if v not in inside_vertices}
        s=Search(region,forb,degs,adj_seed,max_new=len(inside_vertices),max_solutions=300)
        sols=s.run()
        tested+=1
        nsols_hist[len(sols)]+=1
        ok_any=rep=False
        for fcs,ddg,nnew in sols:
            allf=[list(f) for f in outside]+[list(f) for f in fcs]
            try: rot2=faces_to_rotation(allf)
            except AssertionError: continue
            emit_json(rot2,'c3.json')
            res=run_verifiers('c3.json',len(rot2))
            if all(rc==0 for rc,_,_ in res.values()):
                ok_any=True
                if nnew==len(inside_vertices): rep=True
        found_ok+=ok_any; repro+=rep
        if not rep: fails.append((cyc,len(inside_vertices),len(sols)))
    print(f"{certpath.split('/')[-1]}: tested={tested} verified_any={found_ok} original_size_reproduced={repro}")
    print("  #solutions histogram:", dict(sorted(nsols_hist.items())))
    for ex in fails[:8]: print("  MISS:", ex)

base='certificates/known/'
for f in ('ghent17.json','order20.json','order42.json'):
    test_cert(base+f)
