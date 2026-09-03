"""Map utilities: faces <-> rotation, JSON emit, verify convention.

verify.py convention: darts are ordered pairs (u,v); the face on the LEFT of
(u,v) advances by phi((u,v)) = (v, w) where w is the neighbour immediately
BEFORE u in v's clockwise list.
"""
import json, subprocess, tempfile, os

def rotation_to_faces(rot):
    darts = [(u, v) for u, ns in rot.items() for v in ns]
    idx = {v: {w: i for i, w in enumerate(ns)} for v, ns in rot.items()}
    def phi(d):
        u, v = d
        ns = rot[v]
        return (v, ns[(idx[v][u] - 1) % len(ns)])
    faces, seen = [], set()
    for d in darts:
        if d in seen: continue
        walk, c = [], d
        while c not in seen:
            seen.add(c); walk.append(c); c = phi(c)
        faces.append([a for a, b in walk])
    return faces  # vertex cycles; face on left of (walk[i], walk[i+1])

def faces_to_rotation(faces):
    phi = {}
    for f in faces:
        k = len(f)
        for i in range(k):
            d = (f[i], f[(i+1) % k])
            assert d not in phi, f"dart {d} in two faces"
            phi[d] = (f[(i+1) % k], f[(i+2) % k])
    # every dart's reverse must exist
    for (u, v) in list(phi):
        assert (v, u) in phi, f"dart {(v,u)} missing"
    sigma_inv = {d: phi[(d[1], d[0])] for d in phi}
    sigma = {v: k for k, v in sigma_inv.items()}
    rot = {}
    for (u, v) in phi:
        if u in rot: continue
        cyc, d = [], (u, v)
        while True:
            cyc.append(d[1])
            d = sigma[d]
            if d == (u, v): break
        rot[u] = cyc
    return rot

def emit_json(rot, path):
    labels = sorted(rot, key=str)
    ren = {v: i+1 for i, v in enumerate(labels)}
    rows = []
    for v in labels:
        ns = [ren[w] for w in rot[v]]
        # normalize: smallest neighbour first
        i = ns.index(min(ns))
        ns = ns[i:] + ns[:i]
        rows.append({"id": ren[v], "clockwise": ns})
    data = {"format": "apg-plane-rotation-v1", "vertices": rows}
    with open(path, "w") as fh:
        json.dump(data, fh)
    return ren

def run_verifiers(path, order, repo=""):
    out = {}
    for script in ("verify.py", "verify_darts.py"):
        p = subprocess.run(["python3", os.path.join(repo, script), path,
                            "--expect-order", str(order)],
                           capture_output=True, text=True)
        out[script] = (p.returncode, p.stdout.strip(), p.stderr.strip())
    return out
