import collections, time, sys
from cutlib import cut_interfaces
from capsearch import Search

CUTS = {
 'C3':  [('x',0),('y',-1),('z',-2)],
 'C4a': [('x',0),('z',-1),('y',-1),('z',-2)],
 'C4b': [('y',0),('z',0),('y',1),('z',-1)],
 'C5a': [('x',0),('y',-1),('z',-2),('y',0),('z',-1)],
 'C5b': [('x',0),('y',-1),('z',-3),('x',-1),('z',-2)],
 'C6a': [('x',0),('y',-1),('z',-3),('x',-1),('y',-2),('z',-2)],
 'C6b': [('x',0),('z',-1),('x',1),('z',0),('y',0),('z',-2)],
 'C6c': [('x',0),('z',-1),('y',1),('z',0),('y',0),('z',-2)],
}
MAXNEW = int(sys.argv[1]) if len(sys.argv)>1 else 12
for name, cyc in CUTS.items():
    iface = cut_interfaces(cyc)
    for side in ('capL','capR'):
        p = iface[side]
        t0=time.time()
        s = Search(p['region'], p['forb'], p['deg'], p['adj'], max_new=MAXNEW)
        sols = s.run()
        cnt = collections.Counter(nnew for _,_,nnew in sols)
        print(f"{name} {side}: region={[(str(v),r) for v,r in p['region']]} forb={p['forb']}")
        print(f"   -> {len(sols)} fillings {dict(sorted(cnt.items()))} nodes={s.nodes} {time.time()-t0:.1f}s")
