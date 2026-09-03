#!/usr/bin/env python3
"""Finite-domain Z3 search over labelled orientable combinatorial maps.

This is deliberately a *positive-witness* engine.  ``unknown`` and any
resource-limit exit are recorded as INCOMPLETE, never as UNSAT/nonexistence.
The fixed vertex slots and fixed face labels are only a labelling convention:
within a profile, every rotation system has such a labelling.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from typing import Any

import z3


def profile_closed(n: int, r: int) -> tuple[list[int], list[int]]:
    n3 = r
    n4 = n - 2 * r + 4
    n5 = r - 4
    if n < 4 or r < 4 or min(n3, n4, n5) < 0:
        raise ValueError(f"invalid closed profile order={n}, r={r}")
    vd = [3] * n3 + [4] * n4 + [5] * n5
    if len(vd) != n or sum(vd) != 4 * n - 4:
        raise AssertionError("closed profile count identity failed")
    return vd, list(vd)


def profile_block(order: int = 27, r: int = 12) -> tuple[list[int], list[int]]:
    """Return the strict two-socket profile for block order ``order``.

    Here ``r`` is the parameter of a capped closure.  Capping changes the six
    degree-2 socket whites into four degree-3 and two degree-4 incidences, so
    the open block has ``r-4`` degree-3 and degree-5 vertices and
    ``order-2*r+2`` degree-4 vertices.
    """

    n3 = r - 4
    n4 = order - 2 * r + 2
    n5 = r - 4
    if order < 4 or min(n3, n4, n5) < 0:
        raise ValueError(f"invalid block profile order={order}, r={r}")
    degrees = [2] * 6 + [3] * n3 + [4] * n4 + [5] * n5
    faces = [3] * n3 + [4] * n4 + [5] * n5 + [6] * 2
    if len(degrees) != order or sum(degrees) != 4 * order - 12:
        raise AssertionError("block profile count identity failed")
    return degrees, faces


def cycles_from_degrees(degrees: list[int]) -> tuple[list[list[int]], list[int], list[int]]:
    cycles: list[list[int]] = []
    vertex_of: list[int] = []
    for v, degree in enumerate(degrees):
        cycle = list(range(len(vertex_of), len(vertex_of) + degree))
        cycles.append(cycle)
        vertex_of.extend([v] * degree)
    inverse = [0] * len(vertex_of)
    for cycle in cycles:
        for i, dart in enumerate(cycle):
            inverse[dart] = cycle[(i - 1) % len(cycle)]
    return cycles, vertex_of, inverse


def dump_rotation(degrees: list[int], alpha: list[int]) -> dict[str, object]:
    cycles, vertex_of, _ = cycles_from_degrees(degrees)
    rows = []
    for v, cycle in enumerate(cycles):
        ns = [vertex_of[alpha[d]] for d in cycle]
        # Normalization is a representation convention, not a re-embedding.
        m = min(ns)
        i = ns.index(m)
        rows.append({"id": v, "clockwise": ns[i:] + ns[:i]})
    return {"format": "apg-plane-rotation-v1", "vertices": rows}


def _solver_statistics(statistics: z3.Statistics) -> dict[str, object]:
    """Make Z3's run diagnostics JSON-safe without relying on key names."""

    result: dict[str, object] = {}
    for key in statistics.keys():
        value: Any = statistics.get_key_value(key)
        if isinstance(value, (int, float, str, bool)) or value is None:
            result[str(key)] = value
        else:
            result[str(key)] = str(value)
    return result


def build_solver(
    degrees: list[int],
    face_lengths: list[int],
    *,
    open_block: bool,
    explicit_connectivity: bool = False,
) -> tuple[z3.Solver, list[z3.IntNumRef | z3.ArithRef]]:
    cycles, vertex_of, sigma_inv = cycles_from_degrees(degrees)
    dcount, vcount, fcount = len(vertex_of), len(degrees), len(face_lengths)
    max_len = max(face_lengths)
    solver = z3.Solver()
    alpha = [z3.Int(f"a_{d}") for d in range(dcount)]
    face = [z3.Int(f"f_{d}") for d in range(dcount)]
    pos = [z3.Int(f"p_{d}") for d in range(dcount)]
    aa = z3.Array("alpha_array", z3.IntSort(), z3.IntSort())
    ff = z3.Array("face_array", z3.IntSort(), z3.IntSort())
    pp = z3.Array("pos_array", z3.IntSort(), z3.IntSort())
    vertex_array = z3.K(z3.IntSort(), -1)
    degree_array = z3.K(z3.IntSort(), -1)
    sigma_array = z3.K(z3.IntSort(), -1)
    length_array = z3.K(z3.IntSort(), -1)
    for d in range(dcount):
        solver.add(z3.Select(aa, d) == alpha[d], z3.Select(ff, d) == face[d], z3.Select(pp, d) == pos[d])
        vertex_array = z3.Store(vertex_array, d, vertex_of[d])
        degree_array = z3.Store(degree_array, d, degrees[vertex_of[d]])
        sigma_array = z3.Store(sigma_array, d, sigma_inv[d])
    for f, length in enumerate(face_lengths):
        length_array = z3.Store(length_array, f, length)

    # alpha is the fixed-point-free edge involution; phi=sigma^-1 alpha.
    for d in range(dcount):
        target_vertex = z3.Select(vertex_array, alpha[d])
        target_degree = z3.Select(degree_array, alpha[d])
        successor = z3.Select(sigma_array, alpha[d])
        solver.add(alpha[d] >= 0, alpha[d] < dcount, alpha[d] != d)
        solver.add(z3.Select(aa, alpha[d]) == d)
        solver.add(target_vertex != vertex_of[d], target_degree != degrees[vertex_of[d]])
        solver.add(face[d] >= 0, face[d] < fcount)
        solver.add(pos[d] >= 0, pos[d] < z3.Select(length_array, face[d]))
        solver.add(z3.Select(ff, successor) == face[d])
        solver.add(z3.Select(pp, successor) == (pos[d] + 1) % z3.Select(length_array, face[d]))
        solver.add(z3.Select(length_array, face[d]) != z3.Select(length_array, z3.Select(ff, alpha[d])))

    # Every labelled face-position slot occurs exactly once, hence each is one cycle.
    solver.add(z3.Distinct([face[d] * (max_len + 1) + pos[d] for d in range(dcount)]))
    # Simplicity: each vertex's incident darts lead to different neighbour vertices.
    for cycle in cycles:
        solver.add(z3.Distinct([z3.Select(vertex_array, alpha[d]) for d in cycle]))
        # A facial boundary cannot revisit a vertex.
        for i, d in enumerate(cycle):
            for e in cycle[i + 1:]:
                solver.add(face[d] != face[e])

    if open_block:
        socket_faces = (fcount - 2, fcount - 1)
        for d in range(dcount):
            is_socket = z3.Or(face[d] == socket_faces[0], face[d] == socket_faces[1])
            # Position parity fixes an orientation on each alternating socket C6.
            solver.add(z3.Implies(is_socket, z3.Or(z3.And(pos[d] % 2 == 0, degrees[vertex_of[d]] == 2), z3.And(pos[d] % 2 == 1, degrees[vertex_of[d]] == 5))))
            solver.add(z3.Implies(is_socket, z3.Select(length_array, z3.Select(ff, alpha[d])) == 5))

        # A strict Section-8 block has all six degree-2 whites on the two
        # marked sockets.  This is a positive-search restriction (the
        # postprocessor still validates it independently), not a claim about
        # arbitrary open maps.  Relabel the sockets and rotate their boundary
        # slots so dart 0 is the first white on socket 0; every strict block
        # admits this convention.
        for d, degree in enumerate(degrees):
            if degree == 2:
                solver.add(z3.Or(face[d] == socket_faces[0], face[d] == socket_faces[1]))
        solver.add(face[0] == socket_faces[0], pos[0] == 0)

    # Remove the largest harmless source of symmetry.  Face labels within a
    # fixed length class are arbitrary, as are the starting positions on a
    # face.  Dart 0 can therefore be placed at position 0 of the first face
    # of whichever length contains it.  This is a disjunction over the three
    # nonempty classes, so it does not assume an unproved incident face size.
    if not open_block:
        starts: dict[int, int] = {}
        for face_id, length in enumerate(face_lengths):
            starts.setdefault(length, face_id)
        solver.add(
            z3.Or(
                *[
                    z3.And(face[0] == face_id, pos[0] == 0)
                    for face_id in starts.values()
                ]
            )
        )

    # Vertex labels and cyclic dart slots are a convention.  Relabel a
    # degree-3 vertex first and rotate its first neighbour's dart to the
    # beginning of the corresponding degree class.  At least one of the
    # degree-4/degree-5 classes occurs at a degree-3 neighbour by alternation,
    # so the disjunction is always satisfiable for a genuine APG.  For a
    # strict block, dart 0 is a degree-2 white and the analogous canonical
    # choice is its first degree-5 neighbour.
    if open_block:
        first_degree5 = sum(d for d in degrees if d < 5)
        solver.add(alpha[0] == first_degree5)
    else:
        r = degrees.count(3)
        first_degree4 = 3 * r
        first_degree5 = first_degree4 + 4 * degrees.count(4)
        solver.add(z3.Or(alpha[0] == first_degree4, alpha[0] == first_degree5))

    if explicit_connectivity:
        # Optional diagnostic only.  With all dart slots occupied, the fixed
        # counts give V-E+F=2.  That Euler value does not by itself exclude a
        # disconnected map with positive-genus components, so the default is
        # an intentional over-approximation for positive search.  Every model
        # still goes through the independent connectivity/sphere verifier.
        # Keep the expansion behind a flag for diagnostic comparisons; it is
        # expensive in Z3 and is not needed to preserve any genuine witness.
        adjacent: list[list[z3.BoolRef]] = [[z3.BoolVal(False) for _ in range(vcount)] for _ in range(vcount)]
        for u, cycle in enumerate(cycles):
            for v in range(vcount):
                if u != v:
                    adjacent[u][v] = z3.Or([z3.Select(vertex_array, alpha[d]) == v for d in cycle])
        reach = [[z3.Bool(f"reach_{k}_{v}") for v in range(vcount)] for k in range(vcount)]
        for v in range(vcount):
            solver.add(reach[0][v] == (v == 0))
        for k in range(1, vcount):
            for v in range(vcount):
                solver.add(reach[k][v] == z3.Or(reach[k - 1][v], *[z3.And(reach[k - 1][u], adjacent[u][v]) for u in range(vcount)]))
        solver.add(*reach[-1])
    return solver, alpha


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--lane", choices=("closed", "block"), required=True)
    p.add_argument("--r", type=int)
    p.add_argument("--timeout-s", type=int, required=True)
    p.add_argument("--random-seed", type=int, default=0)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument(
        "--explicit-connectivity",
        action="store_true",
        help="retain the redundant bounded reachability encoding (diagnostic)",
    )
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.threads < 1:
        p.error("--threads must be positive")
    if args.lane == "closed":
        if args.r not in (16, 17, 18):
            p.error("closed lane requires r in {16,17,18}")
        degrees, faces = profile_closed(46, args.r)
    else:
        if args.r not in (None, 12):
            p.error("block lane has fixed r=12")
        degrees, faces = profile_block()
    started = time.time()
    solver, alpha = build_solver(
        degrees,
        faces,
        open_block=args.lane == "block",
        explicit_connectivity=args.explicit_connectivity,
    )
    constraint_count = len(solver.assertions())
    solver.set(
        timeout=args.timeout_s * 1000,
        random_seed=args.random_seed,
        threads=args.threads,
    )
    result = solver.check()
    record: dict[str, object] = {
        "format": "apg-exact-map-sat-v1", "lane": args.lane, "r": args.r or 12,
        "disposition": "INCOMPLETE", "z3_result": str(result), "timeout_seconds": args.timeout_s,
        "wall_seconds": time.time() - started, "z3_version": z3.get_version_string(),
        "python": sys.version, "platform": platform.platform(),
        "encoding": "labelled-dart-involution-plus-face-permutation",
        "encoding_constraint_count": constraint_count,
        "heuristic": False,
        "random_seed": args.random_seed,
        "threads": args.threads,
        "explicit_connectivity": args.explicit_connectivity,
        "solver_statistics": _solver_statistics(solver.statistics()),
    }
    if result == z3.sat:
        model = solver.model()
        av = [model.eval(alpha[d], model_completion=True).as_long() for d in range(len(alpha))]
        record["disposition"] = "CANDIDATE"
        record["certificate"] = dump_rotation(degrees, av)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "certificate"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
