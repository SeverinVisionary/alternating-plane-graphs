"""Canonical form of a rotation system (map isomorphism, orientation-preserving
+ mirror), by BFS relabeling from every dart."""
def canon_map(rot):
    best = None
    verts = list(rot)
    for mirror in (False, True):
        R = {v: (list(ns)[::-1] if mirror else list(ns)) for v, ns in rot.items()}
        for v0 in verts:
            for w0 in R[v0]:
                lab = {v0: 0}
                order = [v0]
                # BFS: at each vertex, neighbors in rotation order starting from its parent dart
                start_dart = {v0: w0}
                i = 0
                while i < len(order):
                    v = order[i]; i += 1
                    ns = R[v]
                    s = ns.index(start_dart[v])
                    seq = ns[s:] + ns[:s]
                    for w in seq:
                        if w not in lab:
                            lab[w] = len(order)
                            order.append(w)
                            start_dart[w] = v
                sig = tuple(tuple(lab[w] for w in (R[v][R[v].index(start_dart[v]):] + R[v][:R[v].index(start_dart[v])])) for v in order)
                if best is None or sig < best:
                    best = sig
    return best
if __name__ == '__main__':
    import json, sys, collections
    from capsearch import Search
    from maputil import faces_to_rotation
    A, B, C = ('r',3), ('r',4), ('r',5)
    deg = {A:3, B:4, C:5}
    adj = {frozenset((A,B)), frozenset((B,C)), frozenset((C,A))}
    s = Search([(A,1),(B,2),(C,3)], [3,3,3], deg, adj, max_new=14)
    res = s.run()
    forms = collections.Counter()
    for fcs, degs, nnew in res:
        rot2 = faces_to_rotation([list(f) for f in fcs] + [[A,C,B]])
        forms[canon_map(rot2)] += 1
    print("isomorphism classes among the 8 order-17 fillings:", len(forms), "multiplicities:", sorted(forms.values()))
    # compare with published
    pub = []
    for f in ('ghent17.json','schneider17.json'):
        d = json.load(open('certificates/known/'+f))
        rot = {row['id']: list(row['clockwise']) for row in d['vertices']}
        pub.append(canon_map(rot))
    print("published order-17 classes matched:", sum(1 for p in pub if p in forms))
