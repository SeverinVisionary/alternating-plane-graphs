#!/usr/bin/env python3
"""Exact structural audit for the Section-8 two-hexagon block interface.

The search code ranks candidates by a scalar score.  This module records the
invariants that a reusable block must satisfy instead: the closed degree/face
counts, the corner and joint edge-type matrices, the degree-5/pentagon
incidence graph, and the two marked cap motifs.  It deliberately uses the
separate ``blocks.py`` map implementation; no result annotation is trusted.

This module audits concrete closures; it does not by itself prove the universal
strict-port theorem.  The proof-to-interface bridge and the resulting profile
restriction are documented separately in ``SECTION8_PORT_THEOREM.md``.  Raw
``t=0`` branch tables remain exposed here only as algebraic diagnostics, not as
search-wide nonexistence verdicts.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Iterable

import blocks
from section8_profiles import t0_branches, t0_core_matrix


ROOT = Path(__file__).resolve().parent
RESULT_BLOCKS = ROOT / "results" / "blocks"
EDGE_TYPES: tuple[tuple[int, int], ...] = ((3, 4), (3, 5), (4, 5))
FACE_TYPES: tuple[tuple[int, int], ...] = EDGE_TYPES


def load_block(path: Path) -> dict[str, object]:
    """Load and validate one serialized open block."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    rotation = rotation_from_block(data)
    blocks.validate_block(rotation)
    return data


def rotation_from_block(data: dict[str, object]) -> blocks.Rotation:
    rows = data.get("vertices")
    if not isinstance(rows, list) or not rows:
        raise ValueError("block vertices must be a nonempty list")
    rotation: dict[int, Iterable[int]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "clockwise"}:
            raise ValueError("block vertex rows must contain id and clockwise")
        vertex = row["id"]
        neighbors = row["clockwise"]
        if not isinstance(vertex, int) or isinstance(vertex, bool):
            raise ValueError("block vertex ids must be integers")
        if not isinstance(neighbors, list):
            raise ValueError("block clockwise rows must be lists")
        rotation[vertex] = tuple(neighbors)
    return blocks.normalize_rotation(rotation)


def audit_data_from_block(block: blocks.Block) -> dict[str, object]:
    """Adapt a validated in-memory block to the structural-audit schema.

    The audit predates the exact-map postprocessor and originally consumed the
    historical ``results/blocks/*.json`` files directly.  Positive exact-map
    candidates already have the stronger :class:`blocks.Block` representation,
    so keep the small schema adapter here rather than making the postprocessor
    depend on that historical file format.  The closure entry is descriptive;
    :func:`analyze_closed` derives the actual fan edges afresh for every hub
    choice.
    """

    return {
        "vertices": [
            {"id": vertex, "clockwise": list(neighbors)}
            for vertex, neighbors in sorted(block.rotation.items())
        ],
        "sockets": [
            {
                "cycle": list(socket.boundary),
                "closure": {
                    "center": min(socket.whites),
                    "endpoints": [
                        white for white in socket.whites if white != min(socket.whites)
                    ],
                },
            }
            for socket in block.sockets
        ],
    }


def _edge_key(u: int, v: int) -> frozenset[int]:
    return frozenset((u, v))


def _type_index(value: tuple[int, int], types: tuple[tuple[int, int], ...]) -> int:
    normalized = tuple(sorted(value))
    try:
        return types.index(normalized)
    except ValueError as exc:
        raise ValueError(f"forbidden joint type {normalized}") from exc


def _matrix(counter: Counter[tuple[tuple[int, int], tuple[int, int]]],
            row_types: tuple[tuple[int, int], ...] = EDGE_TYPES,
            column_types: tuple[tuple[int, int], ...] = FACE_TYPES) -> list[list[int]]:
    return [
        [counter[(row_type, column_type)] for column_type in column_types]
        for row_type in row_types
    ]


def _corner_formula(order: int, r: int, t: int) -> list[list[int]]:
    return [
        [r, r, r],
        [r, 4 * order - 11 * r + 28 - t, 2 * r - 12 + t],
        [r, 2 * r - 12 + t, 2 * r - 8 - t],
    ]


def _edge_formula(order: int, r: int, t: int) -> list[list[int]]:
    return [
        [2 * order - 6 * r - 2 * t + 22,
         -2 * order + 7 * r + 2 * t - 22,
         2 * order - 6 * r + 18],
        [-2 * order + 7 * r + 2 * t - 22,
         2 * order - 6 * r - 2 * t + 22,
         -2 * order + 7 * r - 18],
        [2 * order - 6 * r + 18,
         -2 * order + 7 * r - 18,
         2 * order - 4 * r - 2],
    ]


def _y_formula(order: int, r: int) -> list[list[int]]:
    return t0_core_matrix(order, r)


def feasible_t0_branches(order: int) -> tuple[dict[str, object], ...]:
    """Return algebraic t=0 branches with nonnegative beta,gamma,epsilon."""

    return t0_branches(order)


def closure_variants(block_data: dict[str, object]) -> tuple[tuple[tuple[int, int], blocks.Rotation], ...]:
    """Close both sockets for all 3x3 choices of degree-4 hubs.

    The two leaves are added in their boundary order.  ``blocks._add_chord``
    performs the exact face-splitting rotation update and rejects an
    orientation inconsistency.
    """

    open_rotation = rotation_from_block(block_data)
    sockets = blocks.validate_block(open_rotation)
    variants: list[tuple[tuple[int, int], blocks.Rotation]] = []
    for hub_indices in itertools.product(range(3), repeat=2):
        rotation = open_rotation
        for socket, hub_index in zip(sockets, hub_indices):
            whites = list(socket.whites)
            hub = whites[hub_index]
            leaves = [white for index, white in enumerate(whites) if index != hub_index]
            for leaf in leaves:
                face = blocks._face_containing(rotation, {hub, leaf})
                rotation = blocks._add_chord(rotation, face, hub, leaf)
        variants.append((tuple(hub_indices), blocks.normalize_rotation(rotation)))
    return tuple(variants)


def _h55_components(
    faces: tuple[tuple[int, ...], ...], degrees: dict[int, int]
) -> tuple[dict[str, object], ...]:
    """Build components of the degree-5/pentagon incidence graph."""

    pentagons = {index: face for index, face in enumerate(faces) if len(face) == 5}
    nodes: set[tuple[str, int]] = {
        ("v", vertex) for vertex, degree in degrees.items() if degree == 5
    }
    nodes.update(("f", index) for index in pentagons)
    adjacency = {node: set() for node in nodes}
    for face_index, face in pentagons.items():
        for vertex in set(face):
            if degrees[vertex] != 5:
                continue
            left = ("v", vertex)
            right = ("f", face_index)
            adjacency[left].add(right)
            adjacency[right].add(left)

    components: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    node_key = lambda node: (0 if node[0] == "v" else 1, node[1])
    for start in sorted(nodes, key=node_key):
        if start in seen:
            continue
        queue: deque[tuple[str, int]] = deque([start])
        seen.add(start)
        component: list[tuple[str, int]] = []
        while queue:
            node = queue.popleft()
            component.append(node)
            for neighbor in sorted(adjacency[node], key=node_key):
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        vertices = sorted(node[1] for node in component if node[0] == "v")
        faces_in_component = sorted(node[1] for node in component if node[0] == "f")
        component_degrees = [len(adjacency[node]) for node in component]
        components.append(
            {
                "vertices": vertices,
                "pentagons": faces_in_component,
                "node_count": len(component),
                "vertex_count": len(vertices),
                "pentagon_count": len(faces_in_component),
                "node_degrees": sorted(component_degrees),
                "is_cycle": bool(component) and all(degree == 2 for degree in component_degrees),
            }
        )
    return tuple(components)


def _component_index(components: tuple[dict[str, object], ...], vertex: int) -> int:
    for index, component in enumerate(components):
        if vertex in component["vertices"]:  # type: ignore[operator]
            return index
    raise ValueError(f"degree-5 vertex {vertex} is absent from H55")


def analyze_closed(
    block_data: dict[str, object],
    hub_indices: tuple[int, int],
    rotation: blocks.Rotation,
) -> dict[str, object]:
    """Compute all structural data for one closed hub choice."""

    trace = blocks.trace_faces(rotation)
    faces = trace.faces
    all_faces_simple = all(len(set(face)) == len(face) for face in faces)
    if not all_faces_simple:
        raise ValueError("closed APG has a repeated vertex on a facial walk")
    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    order = len(rotation)
    edges = sum(degrees.values()) // 2
    euler = order - edges + len(faces)
    vertex_counts = dict(sorted(Counter(degrees.values()).items()))
    face_counts = dict(sorted(Counter(map(len, faces)).items()))
    r = vertex_counts.get(3, 0)

    vertex_pentagons = {
        vertex: sum(vertex in face for face in faces if len(face) == 5)
        for vertex, degree in degrees.items()
        if degree == 5
    }
    face_degree5 = {
        index: sum(degrees[vertex] == 5 for vertex in face)
        for index, face in enumerate(faces)
        if len(face) == 5
    }
    t_vertex = sum(value == 1 for value in vertex_pentagons.values())
    t_face = sum(value == 1 for value in face_degree5.values())

    corner_counts: Counter[tuple[int, int]] = Counter()
    for face in faces:
        for vertex in face:
            corner_counts[(degrees[vertex], len(face))] += 1
    corner_matrix = [
        [corner_counts[(degree, size)] for size in (3, 4, 5)]
        for degree in (3, 4, 5)
    ]

    edge_counts: Counter[tuple[tuple[int, int], tuple[int, int]]] = Counter()
    all_edges: list[tuple[int, int]] = []
    for vertex, neighbors in rotation.items():
        for neighbor in neighbors:
            if vertex >= neighbor:
                continue
            left_face = trace.face_of[(vertex, neighbor)]
            right_face = trace.face_of[(neighbor, vertex)]
            endpoint_type = tuple(sorted((degrees[vertex], degrees[neighbor])))
            face_type = tuple(sorted((len(faces[left_face]), len(faces[right_face]))) )
            edge_counts[(endpoint_type, face_type)] += 1
            all_edges.append((vertex, neighbor))
    edge_matrix = _matrix(edge_counts)

    open_rotation = rotation_from_block(block_data)
    sockets = blocks.validate_block(open_rotation)
    boundary_edges = {
        _edge_key(cycle[index], cycle[(index + 1) % len(cycle)])
        for socket in block_data["sockets"]  # type: ignore[index]
        for cycle in [socket["cycle"]]  # type: ignore[index]
        for index in range(len(cycle))
    }
    # The serialized closure records one reference hub choice.  Structural
    # auditing checks all 3x3 hub choices, so derive the actual cap edges from
    # the selected hubs rather than reusing that one reference choice.
    cap_edges: set[frozenset[int]] = set()
    for socket, hub_index in zip(sockets, hub_indices):
        whites = list(socket.whites)
        hub = whites[hub_index]
        cap_edges.update(
            _edge_key(hub, leaf) for leaf in whites if leaf != hub
        )
    core_counts: Counter[tuple[tuple[int, int], tuple[int, int]]] = Counter()
    for vertex, neighbor in all_edges:
        if _edge_key(vertex, neighbor) in boundary_edges or _edge_key(vertex, neighbor) in cap_edges:
            continue
        left_face = trace.face_of[(vertex, neighbor)]
        right_face = trace.face_of[(neighbor, vertex)]
        endpoint_type = tuple(sorted((degrees[vertex], degrees[neighbor])))
        face_type = tuple(sorted((len(faces[left_face]), len(faces[right_face]))) )
        core_counts[(endpoint_type, face_type)] += 1
    core_matrix = _matrix(core_counts)

    components = _h55_components(faces, degrees)
    port_component_indices: list[int] = []
    port_components_are_isolated_cycles = True
    cap_motifs: list[dict[str, object]] = []
    for socket, hub_index in zip(sockets, hub_indices):
        open_whites = list(socket.whites)
        hub = open_whites[hub_index]
        leaves = [white for index, white in enumerate(open_whites) if index != hub_index]
        port_black = [vertex for vertex in socket.boundary if len(open_rotation[vertex]) == 5]
        port_indices = {_component_index(components, vertex) for vertex in port_black}
        if len(port_indices) != 1:
            raise ValueError("one socket does not determine one H55 component")
        port_index = next(iter(port_indices))
        port_component_indices.append(port_index)
        port_component = components[port_index]
        if not (
            port_component["node_count"] == 6
            and port_component["vertex_count"] == 3
            and port_component["pentagon_count"] == 3
            and port_component["is_cycle"]
            and port_component["node_degrees"] == [2, 2, 2, 2, 2, 2]
        ):
            port_components_are_isolated_cycles = False
        edge_face_sizes: list[list[int]] = []
        for leaf in leaves:
            cap = _edge_key(hub, leaf)
            directed = [(hub, leaf), (leaf, hub)]
            if not all(dart in trace.face_of for dart in directed):
                raise ValueError("closure edge is absent from closed rotation")
            edge_face_sizes.append(
                sorted(
                    {
                        len(faces[trace.face_of[(hub, leaf)]]),
                        len(faces[trace.face_of[(leaf, hub)]]),
                    }
                )
            )
            if cap not in cap_edges:
                raise ValueError("closure edge is not recorded in source block")
        cap_motifs.append(
            {
                "hub": hub,
                "leaves": leaves,
                "hub_degree": degrees[hub],
                "leaf_degrees": [degrees[leaf] for leaf in leaves],
                "cap_edge_face_sizes": edge_face_sizes,
                "port_component": port_component_indices[-1],
            }
        )

    expected_corner = _corner_formula(order, r, t_vertex)
    expected_edge = _edge_formula(order, r, t_vertex)
    expected_y = _y_formula(order, r) if t_vertex == 0 else None
    return {
        "hub_indices": list(hub_indices),
        "order": order,
        "edges": edges,
        "faces": len(faces),
        "euler": euler,
        "all_faces_simple": all_faces_simple,
        "vertex_counts": vertex_counts,
        "face_counts": face_counts,
        "r": r,
        "t_vertex": t_vertex,
        "t_face": t_face,
        "vertex_pentagon_incidence": dict(sorted(vertex_pentagons.items())),
        "pentagon_degree5_incidence": dict(sorted(face_degree5.items())),
        "corner_matrix": corner_matrix,
        "corner_formula": expected_corner,
        "corner_formula_matches": corner_matrix == expected_corner,
        "edge_matrix": edge_matrix,
        "edge_formula": expected_edge,
        "edge_formula_matches": edge_matrix == expected_edge,
        "boundary_edge_count": len(boundary_edges),
        "cap_edge_count": len(cap_edges),
        "core_edge_count": sum(map(sum, core_matrix)),
        "core_edge_matrix": core_matrix,
        "expected_Y": expected_y,
        "core_matrix_matches_Y": expected_y is not None and core_matrix == expected_y,
        "h55_components": list(components),
        "h55_component_sizes": [component["node_count"] for component in components],
        "h55_all_degree_two": all(
            component["is_cycle"] for component in components
        ),
        "port_component_indices": port_component_indices,
        "port_components_distinct": len(set(port_component_indices)) == 2,
        "port_components_are_isolated_cycles": port_components_are_isolated_cycles,
        "cap_motifs": cap_motifs,
    }


def analyze_block(block_data: dict[str, object]) -> dict[str, object]:
    variants = [
        analyze_closed(block_data, hub_indices, rotation)
        for hub_indices, rotation in closure_variants(block_data)
    ]
    invariant_keys = (
        "order",
        "edges",
        "faces",
        "euler",
        "all_faces_simple",
        "vertex_counts",
        "face_counts",
        "r",
        "t_vertex",
        "t_face",
        "corner_matrix",
        "edge_matrix",
        "core_edge_matrix",
        "h55_component_sizes",
        "h55_all_degree_two",
        "port_components_distinct",
        "port_components_are_isolated_cycles",
    )
    first = variants[0]
    all_invariants_equal = all(
        all(variant[key] == first[key] for key in invariant_keys)
        for variant in variants[1:]
    )
    return {
        "order": first["order"],
        "variant_count": len(variants),
        "all_invariants_equal": all_invariants_equal,
        "variants": variants,
        "t0_branches": list(feasible_t0_branches(int(first["order"]))),
    }


def gluing_t_audit(blocks_by_name: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    """Cross-check t under every ordered A--D block composition."""

    out: list[dict[str, object]] = []
    for inner_name, outer_name in itertools.product(sorted(blocks_by_name), repeat=2):
        inner = blocks_by_name[inner_name]
        outer = blocks_by_name[outer_name]
        composed = blocks.compose_blocks(
            blocks.Block(
                rotation_from_block(inner),
                blocks.validate_block(rotation_from_block(inner)),
            ),
            blocks.Block(
                rotation_from_block(outer),
                blocks.validate_block(rotation_from_block(outer)),
            ),
        )
        composed_sockets = blocks.validate_block(composed.rotation)
        closed = blocks.close_block(composed)
        # ``close_block`` uses sorted socket whites.  Convert that choice back
        # to the boundary-order indices expected by ``analyze_closed``.
        hub_indices = tuple(
            list(socket.whites).index(min(socket.whites))
            for socket in composed_sockets
        )
        stats = analyze_closed(
            audit_data_from_block(blocks.Block(composed.rotation, composed_sockets)),
            hub_indices,
            closed,
        )
        inner_stats = analyze_block(inner)["variants"][0]
        outer_stats = analyze_block(outer)["variants"][0]
        out.append(
            {
                "inner": inner_name,
                "outer": outer_name,
                "order": stats["order"],
                "t_inner": inner_stats["t_vertex"],
                "t_outer": outer_stats["t_vertex"],
                "t_composed": stats["t_vertex"],
                "t_additive": stats["t_vertex"] == inner_stats["t_vertex"] + outer_stats["t_vertex"],
                "h55_component_sizes": stats["h55_component_sizes"],
            }
        )
    return out


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--block",
        action="append",
        dest="blocks",
        metavar="NAME",
        help="known block basename (for example A21); may be repeated",
    )
    parser.add_argument("--output", type=Path, help="write the JSON audit to this path")
    parser.add_argument("--gluing", action="store_true", help="include ordered A-D gluing audit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    names = args.blocks or ["A21", "B22", "C23", "D24"]
    loaded = {name: load_block(RESULT_BLOCKS / f"{name}.json") for name in names}
    result: dict[str, object] = {
        "claim_scope": (
            "Structural control audit only; see SECTION8_PORT_THEOREM.md for the "
            "separate strict-port proof and do not treat this audit as a "
            "search-completeness result."
        ),
        "blocks": {name: analyze_block(data) for name, data in loaded.items()},
    }
    if args.gluing:
        result["gluing"] = gluing_t_audit(loaded)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
