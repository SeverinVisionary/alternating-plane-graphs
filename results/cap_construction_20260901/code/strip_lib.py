"""Shared model of the c=3 periodic strip (lift of the torus quotient)."""
import collections

EDGES = [('y','z'), ('y','z'), ('y','z'), ('x','z'), ('x','z'), ('x','y')]
ROT = {'x': (6, 8, 10), 'y': (0, 2, 4, 11), 'z': (1, 3, 7, 5, 9)}
OMEGA = (-2, -1, 0, -1, -2, -1)
DEG = {'x': 3, 'y': 4, 'z': 5}

def build_window(K0, K1):
    """Vertices (v,k) for k in [K0,K1]; edges of the lift with both ends inside.
    Returns adjacency-with-rotation: rot[(v,k)] = tuple of neighbour vertices in
    clockwise order (inherited from quotient), only for vertices whose full
    rotation lies inside the window ("interior"); for boundary-of-window
    vertices we still return the partial ordered list with None for missing.
    Also returns edge set."""
    verts = {(v,k) for v in 'xyz' for k in range(K0, K1+1)}
    # neighbour of (v,k) along quotient dart qd
    def nbr(v, k, qd):
        e, side = qd//2, qd%2
        u, w = EDGES[e]
        if side == 0:
            assert u == v
            return (w, k + OMEGA[e]), (e, k)
        else:
            assert w == v
            return (u, k - OMEGA[e]), (e, k - OMEGA[e])
    rot = {}
    edgeid = {}
    for (v,k) in verts:
        cyc = []
        for qd in ROT[v]:
            nb, eid = nbr(v,k,qd)
            cyc.append(nb if nb in verts else None)
            if nb in verts:
                edgeid[frozenset(((v,k),nb))] = eid
        rot[(v,k)] = tuple(cyc)
    return verts, rot, edgeid

def full_rot(v):
    """Quotient rotation of v as list of (edge, side)."""
    return [(qd//2, qd%2) for qd in ROT[v]]

TAU = (1, 0, 0, 0, 1, 0)   # circumferential winding functional; meridians have +-1

def cycle_winding(path, edgeid_lookup=None):
    """path = list of lift vertices forming a cycle; winding = sum of +-tau."""
    n = len(path)
    tot_t, tot_w = 0, 0
    for i in range(n):
        (v1,k1), (v2,k2) = path[i], path[(i+1)%n]
        # identify the edge: find e with endpoints v1,v2 and correct k relation
        cands = []
        for e,(u,w) in enumerate(EDGES):
            if (u,w) == (v1,v2) and k2 == k1 + OMEGA[e]:
                cands.append((e, +1))
            if (u,w) == (v2,v1) and k1 == k2 + OMEGA[e]:
                cands.append((e, -1))
        assert len(cands) >= 1, (path[i], path[(i+1)%n])
        assert len(cands) == 1, ("ambiguous edge", path[i], path[(i+1)%n], cands)
        e, s = cands[0]
        tot_t += s*TAU[e]; tot_w += s*OMEGA[e]
    assert tot_w == 0
    return tot_t
