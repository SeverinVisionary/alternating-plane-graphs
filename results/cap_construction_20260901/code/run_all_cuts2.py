import collections, time, sys
from cutlib import cut_interfaces
from capsearch import Search
from run_all_cuts import CUTS
MAXNEW = int(sys.argv[1]) if len(sys.argv)>1 else 30
for name, cyc in CUTS.items():
    iface = cut_interfaces(cyc)
    for side in ('capL','capR'):
        p = iface[side]
        t0=time.time()
        s = Search(p['region'], p['forb'], p['deg'], p['adj'], max_new=MAXNEW)
        sols = s.run()
        print(f"{name} {side}: fillings={len(sols)} nodes={s.nodes} deepest_interior={s.max_depth_new} hit_cap={s.hit_max_new} {time.time()-t0:.1f}s")
