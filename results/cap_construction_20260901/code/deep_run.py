import time
from cutlib import cut_interfaces
from capsearch import Search
from run_all_cuts import CUTS
for MAXNEW in (60, 100):
    for name, cyc in CUTS.items():
        iface = cut_interfaces(cyc)
        for side in ('capL','capR'):
            p = iface[side]
            t0 = time.time()
            s = Search(p['region'], p['forb'], p['deg'], p['adj'], max_new=MAXNEW)
            sols = s.run()
            print(f"max_new={MAXNEW} {name} {side}: sols={len(sols)} nodes={s.nodes} deepest={s.max_depth_new} t={time.time()-t0:.1f}s", flush=True)
