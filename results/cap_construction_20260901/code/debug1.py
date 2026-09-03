import json
from maputil import rotation_to_faces
from capsearch import Search

d = json.load(open('certificates/known/order20.json'))
rot = {row['id']: list(row['clockwise']) for row in d['vertices']}
faces = rotation_to_faces(rot)
deg = {v: len(ns) for v,ns in rot.items()}
adjG = {frozenset((u,w)) for u,ns in rot.items() for w in ns}
fid = {}
for i,f in enumerate(faces):
    for j in range(len(f)): fid[(f[j], f[(j+1)%len(f)])] = i
def edges_of_face(i):
    f=faces[i]; return {frozenset((f[j],f[(j+1)%len(f)])) for j in range(len(f))}

cyc = (1, 2, 6, 7, 8, 20, 4, 19)
n = len(cyc)
Cedges = {frozenset((cyc[i],cyc[(i+1)%n])) for i in range(n)}
left = {fid[(cyc[i],cyc[(i+1)%n])] for i in range(n)}
inside=set(left); stack=list(left)
while stack:
    i=stack.pop()
    for e in edges_of_face(i):
        if e in Cedges: continue
        a,b=tuple(e)
        for dd in ((a,b),(b,a)):
            j=fid[dd]
            if j not in inside: inside.add(j); stack.append(j)
inside_vertices={v for i in inside for v in faces[i]}-set(cyc)
print("inside faces:", [faces[i] for i in inside])
print("inside vertices:", inside_vertices)
onC=set(cyc)
region=[];forb=[]
adjl={v:set(ns) for v,ns in rot.items()}
for i in range(n):
    u=cyc[i]
    rem=sum(1 for w in adjl[u] if w in inside_vertices)
    for w in adjl[u]:
        if w in onC and frozenset((u,w)) not in Cedges:
            if fid[(u,w)] in inside and fid[(w,u)] in inside: rem+=1
    region.append((u,rem))
    forb.append(len(faces[fid[(cyc[(i+1)%n],cyc[i])]]))
print("region:", region)
print("forb:", forb)
adj_seed={e for e in adjG if not (e & inside_vertices)}
adj_seed={e for e in adj_seed if not (e<=onC and frozenset(e) not in Cedges
          and fid[tuple(e)] in inside and fid[tuple(e)[::-1]] in inside)}
degs={v:deg[v] for v in rot if v not in inside_vertices}
s=Search(region,forb,degs,adj_seed,max_new=2)
sols=s.run()
print("solutions:", len(sols), "nodes:", s.nodes)
# what are the inside chords?
chords=[e for e in adjG if e<=onC and frozenset(e) not in Cedges and fid[tuple(e)] in inside and fid[tuple(e)[::-1]] in inside]
print("inside chords:", chords)
