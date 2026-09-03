"""Exhaustive search for alternating cap patches filling a disk region.

Region: cyclic list of (vertex, rem) with region interior on the LEFT of the
walk R[i] -> R[i+1]; forb[i] = size of the face on the outer side of edge i
(the face placed on edge i's inner side must differ in size).

Rules enforced: all faces are simple cycles of size 3/4/5; adjacent faces
(sharing any edge) differ in size; every edge joins vertices of different
degree; no parallel edges; every vertex ends with exactly deg(v) edges.

Each solution is a filling of the region: faces are emitted as vertex tuples
directed with the face on the LEFT of each dart.  Each distinct filling is
generated exactly once (the face adjacent to the pivot edge is unique in any
completed filling).
"""
import sys
sys.setrecursionlimit(100000)

class Abort(Exception):
    pass

class Search:
    def __init__(self, region, forb, deg, adj, max_new,
                 max_solutions=None, on_solution=None, max_nodes=None,
                 loop_prune=False, rng=None):
        self.rng = rng
        self.max_nodes = max_nodes
        self.aborted = False
        self.loop_prune = loop_prune
        self.path_states = set()
        self.loop_prunes = 0
        self.multi_region_states = 0
        self.deg = dict(deg)
        self.adj = set(adj)
        self.max_new = max_new
        self.new_count = 0
        self.next_id = 0
        self.faces = []
        self.solutions = []
        self.max_solutions = max_solutions
        self.on_solution = on_solution
        self.nsol = 0
        self.region0 = (tuple(region), tuple(forb))
        self.nodes = 0
        self.max_depth_new = 0
        self.hit_max_new = 0

    def new_vertex(self, d):
        v = ('i', self.next_id)
        self.next_id += 1
        self.deg[v] = d
        return v

    def run(self):
        try:
            self.fill((self.region0,))
        except Abort:
            self.aborted = True
        return self.solutions

    # ------------------------------------------------------------------
    def fill(self, regions):
        if self.max_solutions is not None and self.nsol >= self.max_solutions:
            return
        self.nodes += 1
        if self.max_nodes is not None and self.nodes > self.max_nodes:
            raise Abort()
        if not regions:
            self.nsol += 1
            sol = ([list(f) for f in self.faces], dict(self.deg),
                   self.new_count)
            self.solutions.append(sol)
            if self.on_solution: self.on_solution(sol)
            return
        (reg, forb), rest = regions[0], regions[1:]
        r = len(reg)
        if r < 3:
            return  # length-2 region would need a parallel edge: dead
        state = None
        if self.loop_prune:
            if not rest:
                state = self._canon_state(reg, forb)
                if state in self.path_states:
                    self.loop_prunes += 1
                    return
                self.path_states.add(state)
            else:
                self.multi_region_states += 1
        try:
            self._fill_body(reg, forb, rest)
        finally:
            if state is not None:
                self.path_states.discard(state)

    def _canon_state(self, reg, forb):
        r = len(reg)
        verts = [v for v, _ in reg]
        best = None
        for s in range(r):
            seq = tuple((self.deg[reg[(s+i) % r][0]], reg[(s+i) % r][1],
                         forb[(s+i) % r]) for i in range(r))
            adjm = tuple(sorted(
                (i, j) for i in range(r) for j in range(i+1, r)
                if frozenset((verts[(s+i) % r], verts[(s+j) % r])) in self.adj))
            cand = (seq, adjm)
            if best is None or cand < best:
                best = cand
        return best

    def _fill_body(self, reg, forb, rest):
        r = len(reg)
        v0, rem0 = reg[0]
        v1, rem1 = reg[1]

        # walk DFS.  cur on boundary: curpos set; interior: curpos None.
        # segments: list of (apos, [interior vertices], bpos) for new paths.
        # seg_start: boundary pos where the current (open) new path started.
        # consumed: vertex -> rem used by this face.
        def place_face(walk, used, segments, consumed, closed_by_boundary):
            size = len(walk)
            if size not in (3, 4, 5): return
            for ei in used:
                if forb[ei] is not None and forb[ei] == size: return
            if closed_by_boundary and rem0 - consumed.get(v0, 0) != 0:
                return  # v0 becomes interior but still owes edges
            # subregions
            subregions = []
            for (apos, path, bpos) in segments:
                idxs = [apos]
                j = apos
                while j != bpos:
                    j = (j + 1) % r
                    idxs.append(j)
                items, forbs = [], []
                for t, j in enumerate(idxs):
                    v, rem = reg[j]
                    if t == 0 or t == len(idxs) - 1:
                        items.append([v, rem - consumed.get(v, 0)])
                    else:
                        items.append([v, rem])
                    if t < len(idxs) - 1:
                        forbs.append(forb[j])
                arc_len = len(idxs)
                for w in reversed(path):
                    items.append([w, self.deg[w] - 2])
                while len(forbs) < len(items):
                    forbs.append(size)
                subregions.append((items, forbs, arc_len))
            # double-touch: vertex that is an endpoint of two segments must
            # split its remaining rem between the two corners.  The segment's
            # boundary-arc endpoints sit at positions 0 and arc_len-1.
            ends = {}
            for si, (items, forbs, arc_len) in enumerate(subregions):
                for pi in {0, arc_len - 1}:
                    v = items[pi][0]
                    ends.setdefault(v, []).append((si, pi))
            doubles = [(v, occ) for v, occ in ends.items() if len(occ) == 2]
            assert all(len(occ) <= 2 for occ in ends.values())
            # occurrences of the same boundary vertex twice as an endpoint
            def recurse(subs):
                if any(len(items) < 3 for items, _, _ in subs):
                    # a 2-vertex subregion means a parallel edge: dead branch
                    return
                newregions = tuple(
                    (tuple((v, rem) for v, rem in items), tuple(forbs))
                    for items, forbs, _ in subs) + tuple(rest)
                self.faces.append(tuple(walk))
                self.fill(newregions)
                self.faces.pop()
            def split_enum(subs, dbls):
                if not dbls:
                    recurse(subs)
                    return
                (v, occ), tail = dbls[0], dbls[1:]
                (s1, p1), (s2, p2) = occ
                total = subs[s1][0][p1][1]
                assert subs[s2][0][p2][1] == total
                for r1 in range(total + 1):
                    subs2 = [([list(it) for it in items], list(forbs), al)
                             for items, forbs, al in subs]
                    subs2[s1][0][p1][1] = r1
                    subs2[s2][0][p2][1] = total - r1
                    split_enum(subs2, tail)
            split_enum([([list(it) for it in items], list(forbs), al)
                        for items, forbs, al in subregions], doubles)

        def step(cur, curpos, arrived_new, walk, used, segments,
                 seg_start, path, consumed):
            if self.max_solutions is not None and self.nsol >= self.max_solutions:
                return
            n = len(walk)
            # --- boundary step / boundary closing (only from boundary) ---
            if curpos is not None:
                v, rem = reg[curpos]
                remaining = rem - consumed.get(v, 0)
                if arrived_new or remaining == 0:
                    nxt = (curpos + 1) % r
                    if nxt == 0:
                        place_face(walk, used + [curpos], segments, consumed,
                                   closed_by_boundary=True)
                    elif n < 5:
                        vn, remn = reg[nxt]
                        if vn not in walk:
                            step(vn, nxt, False, walk + [vn],
                                 used + [curpos], segments, None, [], consumed)
            # --- new-edge options ---
            if curpos is not None:
                v, rem = reg[curpos]
                remaining = rem - consumed.get(v, 0)
            else:
                v, remaining = cur, 1   # interior path vertex departs once
            if remaining < 1:
                return
            dv = self.deg[v]
            ss = seg_start if curpos is None else curpos
            # (a) fresh interior vertex
            if self.new_count >= self.max_new:
                self.hit_max_new += 1
            if self.new_count < self.max_new and n < 5:
                _degs = [3, 4, 5]
                if self.rng: self.rng.shuffle(_degs)
                for d in _degs:
                    if d == dv: continue
                    w = self.new_vertex(d)
                    self.new_count += 1
                    if self.new_count > self.max_depth_new:
                        self.max_depth_new = self.new_count
                    self.adj.add(frozenset((v, w)))
                    c2 = dict(consumed)
                    if curpos is not None:
                        c2[v] = c2.get(v, 0) + 1
                    step(w, None, False, walk + [w], used, segments,
                         ss, path + [w], c2)
                    self.adj.discard(frozenset((v, w)))
                    self.new_count -= 1
                    del self.deg[w]
                    self.next_id -= 1
            # (b) chord to a later boundary position q (not 0)
            if n < 5:
                q = ( (curpos if curpos is not None else seg_start) + 1) % r
                while q != 0:
                    vq, remq = reg[q]
                    if (vq not in walk
                            and frozenset((v, vq)) not in self.adj
                            and self.deg[vq] != dv
                            and remq - consumed.get(vq, 0) >= 1):
                        c2 = dict(consumed)
                        if curpos is not None:
                            c2[v] = c2.get(v, 0) + 1
                        c2[vq] = c2.get(vq, 0) + 1
                        self.adj.add(frozenset((v, vq)))
                        step(vq, q, True, walk + [vq], used,
                             segments + [(ss, list(path), q)], None, [], c2)
                        self.adj.discard(frozenset((v, vq)))
                    q = (q + 1) % r
            # (c) closing new edge back to v0
            if n >= 3:
                if (frozenset((v, v0)) not in self.adj
                        and self.deg[v0] != dv
                        and rem0 - consumed.get(v0, 0) >= 1):
                    c2 = dict(consumed)
                    if curpos is not None:
                        c2[v] = c2.get(v, 0) + 1
                    c2[v0] = c2.get(v0, 0) + 1
                    self.adj.add(frozenset((v, v0)))
                    place_face(walk, used, segments + [(ss, list(path), 0)],
                               c2, closed_by_boundary=False)
                    self.adj.discard(frozenset((v, v0)))

        step(v1, 1, False, [v0, v1], [0], [], None, [], {})
