import pickle, glob, itertools
from genstrip import GenStrip
from assemble2 import assemble_mixed, capL_at_plus, load_inventory
from maputil import run_verifiers

gs = GenStrip(2, 3, K=80)
inv = load_inventory()
cyc_cache = {}
plus_caps, minus_caps = [], []
for item in inv:
    key = tuple(item['cyc'])
    if key not in cyc_cache:
        cyc_cache[key] = capL_at_plus(gs, item['cyc'])
    covers_plus = (item['side'] == 'capL') == cyc_cache[key]
    (plus_caps if covers_plus else minus_caps).append(item)

targets = [47, 50, 53, 56, 68, 71, 74, 89, 92, 110]
achieved = {}
for tgt in targets:
    done = False
    for M, P in itertools.product(minus_caps, plus_caps):
        if done: break
        for szM, solM in sorted(M['sols'].items()):
            if done: break
            for szP, solP in sorted(P['sols'].items()):
                # determine base order at t=6
                r = assemble_mixed(gs, M['cyc'], M['side'], solM,
                                   P['cyc'], P['side'], solP, 6, tag="tmp2")
                if r is None: continue
                _, order6 = r
                if (tgt - order6) % 3 != 0: continue
                t = 6 + (tgt - order6)//3
                if t < 0: continue
                rr = assemble_mixed(gs, M['cyc'], M['side'], solM,
                                    P['cyc'], P['side'], solP, t,
                                    tag=f"TARGET_{tgt}")
                if rr is None: continue
                p2, o2 = rr
                if o2 != tgt: continue
                res = run_verifiers(p2, tgt)
                if all(rc == 0 for rc, _, _ in res.values()):
                    achieved[tgt] = (M['file'], szM, P['file'], szP, t)
                    print(f"TARGET {tgt}: PASS both verifiers  "
                          f"[{M['file']}#{szM} + t={t} + {P['file']}#{szP}]", flush=True)
                    done = True
                    break
    if not done:
        print(f"TARGET {tgt}: NOT yet closed with current caps", flush=True)
print("closed now:", sorted(achieved))
