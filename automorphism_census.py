#!/usr/bin/env python3
"""Automorphism groups of every published (3,4,5)-APG this repository holds.

Calibration for the symmetric-quotient route: imposing an automorphism only
pays if symmetric witnesses plausibly exist at the target orders, and the
public record is the only evidence available about that.

For a connected oriented map an orientation-preserving automorphism is
determined by the image of a single dart, so the whole group is enumerated by
trying each dart as the image of dart 0 and propagating through sigma and
alpha; a reversing automorphism uses sigma^-1 in place of sigma.  Cost is
quadratic in the dart count, so the whole corpus runs in seconds.

This measures the corpus, which is not a census: House of Graphs holds 88
records at orders 17-44 and this repository holds 23 of them.
"""
import sys, subprocess, tempfile, pathlib, collections, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import exact_map_cnf as cnf

def automorphisms(degrees, alpha, reversing=False):
    cycles, vertex_of, sigma, sigma_inv = cnf.cycles_from_degrees(degrees)
    rot = sigma_inv if reversing else sigma
    n = len(alpha)
    found = []
    for image in range(n):
        phi = [-1]*n
        phi[0] = image
        stack = [0]
        ok = True
        while stack and ok:
            x = stack.pop()
            for src, dst in ((sigma[x], rot[phi[x]]), (alpha[x], alpha[phi[x]])):
                if phi[src] == -1:
                    phi[src] = dst
                    stack.append(src)
                elif phi[src] != dst:
                    ok = False
                    break
        if ok and -1 not in phi and len(set(phi)) == n:
            # degrees must be preserved
            if all(degrees[vertex_of[x]] == degrees[vertex_of[phi[x]]] for x in range(n)):
                found.append(tuple(phi))
    return found

tmp = pathlib.Path(tempfile.mkdtemp())
base = pathlib.Path(__file__).resolve().parent
fixtures = sorted((base/'certificates'/'known').glob('*.json'))
for src in sorted((base/'certificates'/'census_sources').glob('*.plc')):
    out = tmp/f"{src.stem}.json"
    subprocess.run([sys.executable, str(base/'import_planar_code.py'), str(src), str(out)],
                   check=True, capture_output=True)
    fixtures.append(out)

rows = []
for f in fixtures:
    d, a = cnf.alpha_from_certificate(f)
    plus = automorphisms(d, a, reversing=False)
    minus = automorphisms(d, a, reversing=True)
    total = len(plus) + len(minus)
    rows.append({"fixture": f.stem, "order": len(d), "r": d.count(3),
                 "orientation_preserving": len(plus), "with_reflections": total})
    print(f"{f.stem:>14} order={len(d):3d} r={d.count(3):3d} |Aut+|={len(plus):3d} |Aut|={total:3d}", flush=True)
dist = collections.Counter(row["with_reflections"] for row in rows)
print("\n|Aut| distribution:", dict(sorted(dist.items())))
print("trivial (|Aut|=1):", dist[1], "of", len(rows))
print("nontrivial:", len(rows)-dist[1], "of", len(rows))
out = base / 'results' / 'logs' / 'automorphism_census.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(
    {"tool": "automorphism_census.py",
     "note": "map automorphisms of the 23 published (3,4,5)-APGs held here; "
             "the corpus is not a census",
     "rows": rows,
     "trivial": dist[1], "total": len(rows)}, indent=2, sort_keys=True) + "\n")
print("wrote", out)
