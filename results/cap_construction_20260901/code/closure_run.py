import time
from cutlib import cut_interfaces
from capsearch import Search
from run_all_cuts import CUTS
print("=== state-closure (loop-pruned, unbounded depth) runs ===")
allok = True
for name, cyc in CUTS.items():
    iface = cut_interfaces(cyc)
    for side in ('capL','capR'):
        p = iface[side]
        t0 = time.time()
        s = Search(p['region'], p['forb'], p['deg'], p['adj'],
                   max_new=10**9, max_nodes=5*10**6, loop_prune=True)
        sols = s.run()
        status = "ABORTED(node budget)" if s.aborted else "TERMINATED"
        if s.aborted or sols: allok = False
        print(f"{name} {side}: {status} sols={len(sols)} nodes={s.nodes} "
              f"deepest_interior={s.max_depth_new} loop_prunes={s.loop_prunes} "
              f"multi_region={s.multi_region_states} t={time.time()-t0:.1f}s", flush=True)
print("ALL TERMINATED WITH ZERO SOLUTIONS" if allok else "NOT CONCLUSIVE")
