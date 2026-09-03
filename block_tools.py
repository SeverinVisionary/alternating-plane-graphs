#!/usr/bin/env python3
"""Exact two-hexagon block recovery, validation, composition, and closure.

This module deliberately reimplements combinatorial-map traversal instead of
importing ``verify.py``.  Candidate APGs are still checked by that committed
verifier in a separate process after serialization.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import time
from collections import Counter
from pathlib import Path
from typing import Iterable


BLOCK_FORMAT = "apg-two-hex-block-v1"
APG_FORMAT = "apg-plane-rotation-v1"
ALLOWED = {3, 4, 5}


class BlockError(ValueError):
    pass


def _normalize(values: Iterable[int]) -> list[int]:
    row = list(values)
    if not row:
        return row
    start = row.index(min(row))
    return row[start:] + row[:start]


def _canonical_cycle(values: Iterable[int]) -> tuple[int, ...]:
    cycle = tuple(values)
    choices: list[tuple[int, ...]] = []
    for oriented in (cycle, tuple(reversed(cycle))):
        for start in range(len(oriented)):
            choices.append(oriented[start:] + oriented[:start])
    return min(choices)


def _rotation_from_rows(rows: object) -> dict[int, list[int]]:
    if not isinstance(rows, list) or not rows:
        raise BlockError("vertices must be a nonempty list")
    result: dict[int, list[int]] = {}
    previous: int | None = None
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "clockwise"}:
            raise BlockError("each vertex row must contain id and clockwise")
        vertex = row["id"]
        neighbors = row["clockwise"]
        if isinstance(vertex, bool) or not isinstance(vertex, int):
            raise BlockError("vertex ids must be integers")
        if previous is not None and vertex <= previous:
            raise BlockError("vertex rows are not strictly ordered")
        if not isinstance(neighbors, list) or any(
            isinstance(x, bool) or not isinstance(x, int) for x in neighbors
        ):
            raise BlockError("clockwise rows must be integer lists")
        if len(neighbors) != len(set(neighbors)) or vertex in neighbors:
            raise BlockError("loop or repeated neighbor")
        if neighbors != _normalize(neighbors):
            raise BlockError("rotation row is not normalized")
        result[vertex] = list(neighbors)
        previous = vertex
    return result


def _rows(rotation: dict[int, list[int]]) -> list[dict[str, object]]:
    return [
        {"clockwise": _normalize(rotation[v]), "id": v}
        for v in sorted(rotation)
    ]


def _trace_faces(
    rotation: dict[int, list[int]],
) -> tuple[list[tuple[int, ...]], dict[tuple[int, int], int]]:
    labels = set(rotation)
    for vertex, neighbors in rotation.items():
        for neighbor in neighbors:
            if neighbor not in labels or vertex not in rotation[neighbor]:
                raise BlockError(f"asymmetric or missing edge {vertex}-{neighbor}")
    darts = {(u, v) for u, ns in rotation.items() for v in ns}
    face_of: dict[tuple[int, int], int] = {}
    faces: list[tuple[int, ...]] = []
    for start in sorted(darts):
        if start in face_of:
            continue
        face_id = len(faces)
        dart = start
        local: set[tuple[int, int]] = set()
        walk: list[tuple[int, int]] = []
        while dart not in local:
            if dart in face_of or dart not in darts:
                raise BlockError("invalid facial walk")
            local.add(dart)
            walk.append(dart)
            u, v = dart
            around = rotation[v]
            position = around.index(u)
            dart = (v, around[(position - 1) % len(around)])
        if dart != start:
            raise BlockError("facial walk did not close at its start")
        for used in walk:
            face_of[used] = face_id
        faces.append(tuple(u for u, _ in walk))
    if set(face_of) != darts:
        raise BlockError("not every dart belongs to a face")
    return faces, face_of


def _connected(rotation: dict[int, list[int]]) -> bool:
    reached: set[int] = set()
    stack = [next(iter(rotation))]
    while stack:
        vertex = stack.pop()
        if vertex in reached:
            continue
        reached.add(vertex)
        stack.extend(rotation[vertex])
    return reached == set(rotation)


def _verify_apg_rotation(rotation: dict[int, list[int]]) -> dict[str, object]:
    if not _connected(rotation):
        raise BlockError("closed graph is disconnected")
    faces, face_of = _trace_faces(rotation)
    degrees = {v: len(ns) for v, ns in rotation.items()}
    if set(degrees.values()) - ALLOWED:
        raise BlockError("closed graph has a forbidden vertex degree")
    face_sizes = [len(face) for face in faces]
    if set(face_sizes) - ALLOWED:
        raise BlockError("closed graph has a forbidden face size")
    for u, neighbors in rotation.items():
        for v in neighbors:
            if u < v:
                if degrees[u] == degrees[v]:
                    raise BlockError("closed graph has equal adjacent degrees")
                if face_sizes[face_of[(u, v)]] == face_sizes[face_of[(v, u)]]:
                    raise BlockError("closed graph has equal adjacent face sizes")
    order = len(rotation)
    edges = sum(degrees.values()) // 2
    if order - edges + len(faces) != 2:
        raise BlockError("closed rotation is not spherical")
    vertex_counts = {size: list(degrees.values()).count(size) for size in sorted(ALLOWED)}
    face_counts = {size: face_sizes.count(size) for size in sorted(ALLOWED)}
    if vertex_counts != face_counts:
        raise BlockError("closed histogram duality failed")
    r = vertex_counts[3]
    if (
        vertex_counts[5] != r - 4
        or vertex_counts[4] != order - 2 * r + 4
        or edges != 2 * order - 2
        or len(faces) != order
    ):
        raise BlockError("closed APG count formula failed")
    return {
        "order": order,
        "edges": edges,
        "faces": len(faces),
        "vertex_counts": vertex_counts,
        "face_counts": face_counts,
    }


def load_json(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise BlockError("top-level JSON must be an object")
    return data


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _closure_rotation(block: dict[str, object]) -> dict[int, list[int]]:
    rotation = _rotation_from_rows(block["vertices"])
    for socket in block["sockets"]:  # type: ignore[index]
        closure = socket["closure"]
        for row in closure["rows"]:
            rotation[row["id"]] = list(row["clockwise"])
    return rotation


def close_block(block: dict[str, object]) -> dict[str, object]:
    validate_block(block, check_closure=True)
    return {"format": APG_FORMAT, "vertices": _rows(_closure_rotation(block))}


def validate_block(
    block: dict[str, object], *, check_closure: bool = True
) -> dict[str, object]:
    if set(block) != {"format", "provenance", "sockets", "vertices"}:
        raise BlockError("block top level has unexpected keys")
    if block["format"] != BLOCK_FORMAT:
        raise BlockError("wrong block format")
    rotation = _rotation_from_rows(block["vertices"])
    if not _connected(rotation):
        raise BlockError("block graph is disconnected")
    faces, face_of = _trace_faces(rotation)
    edges = sum(len(ns) for ns in rotation.values()) // 2
    if len(rotation) - edges + len(faces) != 2:
        raise BlockError("block rotation is not spherical")

    sockets = block["sockets"]
    if not isinstance(sockets, list) or len(sockets) != 2:
        raise BlockError("a block must have exactly two sockets")
    actual_faces = {_canonical_cycle(face): i for i, face in enumerate(faces)}
    marked_face_ids: list[int] = []
    all_whites: set[int] = set()
    previous_cycle: tuple[int, ...] | None = None
    for socket in sockets:
        if not isinstance(socket, dict) or set(socket) != {"closure", "cycle"}:
            raise BlockError("socket has unexpected keys")
        cycle = tuple(socket["cycle"])
        canonical = _canonical_cycle(cycle)
        if cycle != canonical or len(cycle) != 6 or canonical not in actual_faces:
            raise BlockError("socket is not a normalized reconstructed hexagonal face")
        if previous_cycle is not None and cycle <= previous_cycle:
            raise BlockError("sockets are not strictly ordered")
        previous_cycle = cycle
        marked_face_ids.append(actual_faces[canonical])
        degrees_on_cycle = [len(rotation[v]) for v in cycle]
        if not all(
            degrees_on_cycle[i] == 2 and degrees_on_cycle[(i + 1) % 6] == 5
            for i in (0, 2, 4)
        ) and not all(
            degrees_on_cycle[i] == 5 and degrees_on_cycle[(i + 1) % 6] == 2
            for i in (0, 2, 4)
        ):
            raise BlockError("socket does not alternate degree 2 and degree 5")
        whites = {v for v in cycle if len(rotation[v]) == 2}
        if all_whites & whites:
            raise BlockError("the two sockets share a white vertex")
        all_whites |= whites
        closure = socket["closure"]
        if not isinstance(closure, dict) or set(closure) != {"center", "endpoints", "rows"}:
            raise BlockError("malformed closure recipe")
        center = closure["center"]
        endpoints = closure["endpoints"]
        if (
            center not in whites
            or not isinstance(endpoints, list)
            or len(endpoints) != 2
            or set(endpoints) | {center} != whites
        ):
            raise BlockError("closure recipe does not name the socket whites")
        rows = closure["rows"]
        if not isinstance(rows, list) or {row.get("id") for row in rows} != whites:
            raise BlockError("closure rows do not cover socket whites")

    if len(set(marked_face_ids)) != 2:
        raise BlockError("both socket records name the same face")
    degrees = {v: len(ns) for v, ns in rotation.items()}
    if {v for v, degree in degrees.items() if degree == 2} != all_whites:
        raise BlockError("degree-2 vertices are not exactly the six socket whites")
    if any(degree not in {2, 3, 4, 5} for degree in degrees.values()):
        raise BlockError("block has a forbidden vertex degree")
    for u, neighbors in rotation.items():
        for v in neighbors:
            if u >= v:
                continue
            if u in all_whites or v in all_whites:
                white, black = (u, v) if u in all_whites else (v, u)
                if degrees[white] != 2 or degrees[black] != 5:
                    raise BlockError("socket white is not adjacent to degree 5")
            elif degrees[u] == degrees[v]:
                raise BlockError("equal adjacent black degrees")

    face_sizes = [len(face) for face in faces]
    marked = set(marked_face_ids)
    for face_id, size in enumerate(face_sizes):
        if face_id in marked:
            if size != 6:
                raise BlockError("marked face is not hexagonal")
        elif size not in ALLOWED:
            raise BlockError("unmarked face has a forbidden size")
    for u, neighbors in rotation.items():
        for v in neighbors:
            if u >= v:
                continue
            left, right = face_of[(u, v)], face_of[(v, u)]
            if left in marked or right in marked:
                other = right if left in marked else left
                if other in marked or face_sizes[other] != 5:
                    raise BlockError("socket boundary is not surrounded by pentagons")
            elif face_sizes[left] == face_sizes[right]:
                raise BlockError("equal adjacent unmarked face sizes")

    closed_summary = None
    if check_closure:
        closed_summary = _verify_apg_rotation(_closure_rotation(block))
    return {
        "order": len(rotation),
        "edges": edges,
        "faces": len(faces),
        "closed_summary": closed_summary,
    }


def _fan_candidates(rotation: dict[int, list[int]]) -> list[tuple[int, int, int]]:
    degrees = {v: len(ns) for v, ns in rotation.items()}
    fans: list[tuple[int, int, int]] = []
    for center, neighbors in rotation.items():
        if degrees[center] != 4:
            continue
        endpoints = [
            v
            for v in neighbors
            if degrees[v] == 3
            and all(degrees[x] == 5 for x in rotation[v] if x != center)
        ]
        for a, b in itertools.combinations(endpoints, 2):
            if all(degrees[x] == 5 for x in neighbors if x not in {a, b}):
                fans.append((center, min(a, b), max(a, b)))
    return sorted(set(fans))


def recover_blocks(
    certificate: dict[str, object], *, provenance: dict[str, object]
) -> list[dict[str, object]]:
    if certificate.get("format") != APG_FORMAT:
        raise BlockError("wrong APG certificate format")
    original = _rotation_from_rows(certificate["vertices"])
    _verify_apg_rotation(original)
    recovered: list[dict[str, object]] = []
    seen: set[str] = set()
    for first, second in itertools.combinations(_fan_candidates(original), 2):
        if set(first) & set(second):
            continue
        rotation = copy.deepcopy(original)
        for center, a, b in (first, second):
            for endpoint in (a, b):
                rotation[center].remove(endpoint)
                rotation[endpoint].remove(center)
            rotation[center] = _normalize(rotation[center])
            rotation[a] = _normalize(rotation[a])
            rotation[b] = _normalize(rotation[b])
        try:
            faces, _ = _trace_faces(rotation)
        except BlockError:
            continue
        sockets: list[dict[str, object]] = []
        okay = True
        for center, a, b in (first, second):
            matches = [
                face
                for face in faces
                if len(face) == 6 and {center, a, b} <= set(face)
            ]
            if len(matches) != 1:
                okay = False
                break
            cycle = _canonical_cycle(matches[0])
            sockets.append(
                {
                    "closure": {
                        "center": center,
                        "endpoints": sorted((a, b)),
                        "rows": [
                            {"clockwise": original[v], "id": v}
                            for v in sorted((center, a, b))
                        ],
                    },
                    "cycle": list(cycle),
                }
            )
        if not okay:
            continue
        sockets.sort(key=lambda item: tuple(item["cycle"]))
        block = {
            "format": BLOCK_FORMAT,
            "provenance": provenance,
            "sockets": sockets,
            "vertices": _rows(rotation),
        }
        try:
            validate_block(block)
        except BlockError:
            continue
        key = hashlib.sha256(
            json.dumps(
                {"sockets": sockets, "vertices": block["vertices"]},
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
        if key not in seen:
            seen.add(key)
            recovered.append(block)
    return recovered


def mirror_block(block: dict[str, object]) -> dict[str, object]:
    """Reflect a strict block and reconstruct its marked socket records."""

    validate_block(block, check_closure=False)
    rotation = _rotation_from_rows(block["vertices"])
    mirrored_rotation = {
        vertex: _normalize(reversed(neighbors))
        for vertex, neighbors in rotation.items()
    }
    mirrored_sockets: list[dict[str, object]] = []
    for socket in block["sockets"]:  # type: ignore[index]
        closure = socket["closure"]
        rows = [
            {
                "id": row["id"],
                "clockwise": _normalize(reversed(row["clockwise"])),
            }
            for row in closure["rows"]
        ]
        rows.sort(key=lambda row: row["id"])
        mirrored_sockets.append(
            {
                "cycle": list(_canonical_cycle(reversed(socket["cycle"]))),
                "closure": {
                    "center": closure["center"],
                    "endpoints": sorted(closure["endpoints"]),
                    "rows": rows,
                },
            }
        )
    mirrored_sockets.sort(key=lambda item: tuple(item["cycle"]))
    mirrored = {
        "format": BLOCK_FORMAT,
        "provenance": copy.deepcopy(block["provenance"]),
        "sockets": mirrored_sockets,
        "vertices": _rows(mirrored_rotation),
    }
    validate_block(mirrored)
    return mirrored


def recover_blocks_with_mirror(
    certificate: dict[str, object], *, provenance: dict[str, object]
) -> list[dict[str, object]]:
    """Recover strict openings from both orientations of a closed APG."""

    original = _rotation_from_rows(certificate["vertices"])
    mirrored = {
        "format": APG_FORMAT,
        "vertices": _rows(
            {
                vertex: _normalize(reversed(neighbors))
                for vertex, neighbors in original.items()
            }
        ),
    }
    candidates = recover_blocks(certificate, provenance=provenance)
    candidates.extend(recover_blocks(mirrored, provenance=provenance))
    deduplicated: dict[str, dict[str, object]] = {}
    for candidate in candidates:
        key = json.dumps(
            {"sockets": candidate["sockets"], "vertices": candidate["vertices"]},
            sort_keys=True,
            separators=(",", ":"),
        )
        deduplicated[key] = candidate
    return [deduplicated[key] for key in sorted(deduplicated)]


def block_from_rotation(
    rotation: dict[int, list[int]], *, provenance: dict[str, object]
) -> dict[str, object]:
    """Attach deterministic fan closures to an already-open valid block map."""

    rotation = {v: _normalize(ns) for v, ns in rotation.items()}
    faces, _ = _trace_faces(rotation)
    socket_cycles = sorted(
        _canonical_cycle(face) for face in faces if len(face) == 6
    )
    if len(socket_cycles) != 2:
        raise BlockError("open map does not have exactly two hexagonal faces")

    option_sets: list[list[dict[str, object]]] = []
    for cycle in socket_cycles:
        whites = sorted(v for v in cycle if len(rotation[v]) == 2)
        if len(whites) != 3:
            raise BlockError("hexagon does not contain three degree-2 whites")
        options: list[dict[str, object]] = []
        for center in whites:
            endpoints = sorted(set(whites) - {center})
            neighbor_sets = {
                center: [*rotation[center], *endpoints],
                endpoints[0]: [*rotation[endpoints[0]], center],
                endpoints[1]: [*rotation[endpoints[1]], center],
            }
            rows_by_vertex = [
                sorted(
                    {
                        tuple(_normalize(permutation))
                        for permutation in itertools.permutations(neighbor_sets[vertex])
                    }
                )
                for vertex in sorted(whites)
            ]
            for chosen in itertools.product(*rows_by_vertex):
                options.append(
                    {
                        "center": center,
                        "endpoints": endpoints,
                        "rows": [
                            {"clockwise": list(row), "id": vertex}
                            for vertex, row in zip(sorted(whites), chosen)
                        ],
                    }
                )
        option_sets.append(options)

    candidates: list[tuple[str, dict[str, object]]] = []
    for first, second in itertools.product(*option_sets):
        sockets = [
            {"closure": first, "cycle": list(socket_cycles[0])},
            {"closure": second, "cycle": list(socket_cycles[1])},
        ]
        block = {
            "format": BLOCK_FORMAT,
            "provenance": provenance,
            "sockets": sockets,
            "vertices": _rows(rotation),
        }
        try:
            validate_block(block)
        except BlockError:
            continue
        key = json.dumps(sockets, sort_keys=True, separators=(",", ":"))
        candidates.append((key, block))
    if not candidates:
        raise BlockError("no valid pair of socket fan closures exists")
    return min(candidates, key=lambda item: item[0])[1]


def _socket_whites(block: dict[str, object], index: int) -> list[int]:
    rotation = _rotation_from_rows(block["vertices"])
    cycle = block["sockets"][index]["cycle"]  # type: ignore[index]
    return [v for v in cycle if len(rotation[v]) == 2]


def _remap_socket(socket: dict[str, object], mapping: dict[int, int]) -> dict[str, object]:
    closure = socket["closure"]
    result = {
        "cycle": list(_canonical_cycle(mapping[v] for v in socket["cycle"])),
        "closure": {
            "center": mapping[closure["center"]],
            "endpoints": sorted(mapping[v] for v in closure["endpoints"]),
            "rows": [
                {
                    "id": mapping[row["id"]],
                    "clockwise": _normalize(mapping[v] for v in row["clockwise"]),
                }
                for row in closure["rows"]
            ],
        },
    }
    result["closure"]["rows"].sort(key=lambda row: row["id"])
    return result


def _compact_block(block: dict[str, object]) -> dict[str, object]:
    rotation = _rotation_from_rows(block["vertices"])
    mapping = {old: new for new, old in enumerate(sorted(rotation), start=1)}
    compact_rotation = {
        mapping[v]: _normalize(mapping[x] for x in neighbors)
        for v, neighbors in rotation.items()
    }
    sockets = [_remap_socket(socket, mapping) for socket in block["sockets"]]  # type: ignore[index]
    sockets.sort(key=lambda item: tuple(item["cycle"]))
    return {
        "format": BLOCK_FORMAT,
        "provenance": block["provenance"],
        "sockets": sockets,
        "vertices": _rows(compact_rotation),
    }


def _paired_orders(first: list[int], second: list[int]) -> list[list[int]]:
    result = []
    for permutation in itertools.permutations(first + second):
        positions = {v: i for i, v in enumerate(permutation)}
        def adjacent(pair: list[int]) -> bool:
            delta = (positions[pair[0]] - positions[pair[1]]) % 4
            return delta in {1, 3}
        if adjacent(first) and adjacent(second):
            normalized = _normalize(permutation)
            if normalized not in result:
                result.append(normalized)
    return sorted(result)


def compose_two(
    first: dict[str, object], second: dict[str, object]
) -> dict[str, object]:
    validate_block(first)
    validate_block(second)
    first_rotation = _rotation_from_rows(first["vertices"])
    second_rotation = _rotation_from_rows(second["vertices"])
    candidates: list[tuple[str, dict[str, object]]] = []
    for first_socket_index in range(2):
        for second_socket_index in range(2):
            first_whites = _socket_whites(first, first_socket_index)
            second_whites = _socket_whites(second, second_socket_index)
            for assigned in itertools.permutations(first_whites):
                second_map: dict[int, int] = dict(zip(second_whites, assigned))
                next_label = max(first_rotation) + 1
                for vertex in sorted(second_rotation):
                    if vertex not in second_map:
                        second_map[vertex] = next_label
                        next_label += 1
                base = copy.deepcopy(first_rotation)
                for vertex, neighbors in second_rotation.items():
                    mapped_vertex = second_map[vertex]
                    if vertex in second_whites:
                        continue
                    base[mapped_vertex] = _normalize(second_map[v] for v in neighbors)
                options: list[list[list[int]]] = []
                for second_white, first_white in zip(second_whites, assigned):
                    left = list(first_rotation[first_white])
                    right = [second_map[v] for v in second_rotation[second_white]]
                    if len(set(left + right)) != 4:
                        options = []
                        break
                    options.append(_paired_orders(left, right))
                if not options:
                    continue
                for rotations in itertools.product(*options):
                    rotation = copy.deepcopy(base)
                    for first_white, row in zip(assigned, rotations):
                        rotation[first_white] = row
                    sockets = [
                        copy.deepcopy(first["sockets"][1 - first_socket_index]),  # type: ignore[index]
                        _remap_socket(
                            second["sockets"][1 - second_socket_index], second_map  # type: ignore[index]
                        ),
                    ]
                    sockets.sort(key=lambda item: tuple(item["cycle"]))
                    candidate = _compact_block(
                        {
                            "format": BLOCK_FORMAT,
                            "provenance": {
                                "method": "compose",
                                "orders": [len(first_rotation), len(second_rotation)],
                            },
                            "sockets": sockets,
                            "vertices": _rows(rotation),
                        }
                    )
                    try:
                        validate_block(candidate, check_closure=False)
                    except BlockError:
                        continue
                    key = json.dumps(
                        {
                            "sockets": candidate["sockets"],
                            "vertices": candidate["vertices"],
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    candidates.append((key, candidate))
    if not candidates:
        raise BlockError("no compatible socket composition found")
    result = min(candidates, key=lambda item: item[0])[1]
    validate_block(result)
    expected = len(first_rotation) + len(second_rotation) - 3
    if len(result["vertices"]) != expected:
        raise BlockError("composition order formula failed")
    return result


def compose_two_variants(
    first: dict[str, object], second: dict[str, object]
) -> list[dict[str, object]]:
    """Compose all four input-reflection classes, retaining exact maps."""

    candidates: dict[str, dict[str, object]] = {}
    for first_variant in (first, mirror_block(first)):
        for second_variant in (second, mirror_block(second)):
            try:
                composed = compose_two(first_variant, second_variant)
            except BlockError:
                continue
            key = json.dumps(
                {"sockets": composed["sockets"], "vertices": composed["vertices"]},
                sort_keys=True,
                separators=(",", ":"),
            )
            candidates[key] = composed
    if not candidates:
        raise BlockError("no compatible composition in either reflection class")
    return [candidates[key] for key in sorted(candidates)]


def compose_chain(blocks: list[dict[str, object]]) -> dict[str, object]:
    if not blocks:
        raise BlockError("empty block chain")
    result = copy.deepcopy(blocks[0])
    for block in blocks[1:]:
        result = compose_two(result, block)
    result["provenance"] = {
        "method": "compose-chain",
        "source_orders": [len(block["vertices"]) for block in blocks],
    }
    return result


def expand_block_once(block: dict[str, object]) -> list[dict[str, object]]:
    """Enumerate the Figure-5-style one-vertex two-edge subdivision move.

    Two disjoint non-socket edges are replaced by four edges through one new
    degree-4 vertex.  Endpoint rotation positions are preserved; all six cyclic
    orders at the new vertex are tried and the independent block predicates do
    the exact pruning.
    """

    validate_block(block)
    original = _rotation_from_rows(block["vertices"])
    degrees = {v: len(ns) for v, ns in original.items()}
    boundary_edges: set[frozenset[int]] = set()
    for socket in block["sockets"]:  # type: ignore[index]
        cycle = socket["cycle"]
        boundary_edges.update(
            frozenset((cycle[i], cycle[(i + 1) % 6])) for i in range(6)
        )
    edges = [
        (u, v)
        for u, neighbors in original.items()
        for v in neighbors
        if u < v
        and frozenset((u, v)) not in boundary_edges
        and degrees[u] != 4
        and degrees[v] != 4
    ]
    new_vertex = max(original) + 1
    results: dict[str, dict[str, object]] = {}
    for first, second in itertools.combinations(edges, 2):
        endpoints = (*first, *second)
        if len(set(endpoints)) != 4:
            continue
        for new_row in {
            tuple(_normalize(permutation))
            for permutation in itertools.permutations(endpoints)
        }:
            rotation = copy.deepcopy(original)
            for u, v in (first, second):
                rotation[u][rotation[u].index(v)] = new_vertex
                rotation[v][rotation[v].index(u)] = new_vertex
                rotation[u] = _normalize(rotation[u])
                rotation[v] = _normalize(rotation[v])
            rotation[new_vertex] = list(new_row)
            candidate = _compact_block(
                {
                    "format": BLOCK_FORMAT,
                    "provenance": {
                        "method": "two-edge-one-vertex-expansion",
                        "parent_order": len(original),
                        "replaced_edges": [list(first), list(second)],
                    },
                    "sockets": copy.deepcopy(block["sockets"]),
                    "vertices": _rows(rotation),
                }
            )
            try:
                validate_block(candidate)
            except BlockError:
                continue
            key = json.dumps(
                {
                    "sockets": candidate["sockets"],
                    "vertices": candidate["vertices"],
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            results.setdefault(key, candidate)
    return [results[key] for key in sorted(results)]


def apg_edge_replacements(
    certificate: dict[str, object],
) -> list[dict[str, object]]:
    """Enumerate exact embedding-preserving delete-one/add-one edge surgeries."""

    if certificate.get("format") != APG_FORMAT:
        raise BlockError("wrong APG certificate format")
    original = _rotation_from_rows(certificate["vertices"])
    _verify_apg_rotation(original)
    edges = sorted(
        (u, v)
        for u, neighbors in original.items()
        for v in neighbors
        if u < v
    )
    results: dict[str, dict[str, object]] = {}
    for u, v in edges:
        reduced = copy.deepcopy(original)
        reduced[u].remove(v)
        reduced[v].remove(u)
        reduced[u] = _normalize(reduced[u])
        reduced[v] = _normalize(reduced[v])
        if min(len(reduced[u]), len(reduced[v])) < 2:
            continue
        try:
            faces, _ = _trace_faces(reduced)
        except BlockError:
            continue
        merged = [face for face in faces if u in face and v in face]
        if len(merged) != 1 or len(set(merged[0])) != len(merged[0]):
            continue
        face = merged[0]
        for i, x in enumerate(face):
            for j in range(i + 1, len(face)):
                y = face[j]
                if y in reduced[x] or x == y or {x, y} == {u, v}:
                    continue
                candidate_rotation = copy.deepcopy(reduced)
                for vertex, new_neighbor, position in (
                    (x, y, candidate_rotation[x].index(face[(i - 1) % len(face)])),
                    (y, x, candidate_rotation[y].index(face[(j - 1) % len(face)])),
                ):
                    candidate_rotation[vertex].insert(position, new_neighbor)
                    candidate_rotation[vertex] = _normalize(candidate_rotation[vertex])
                try:
                    _verify_apg_rotation(candidate_rotation)
                except BlockError:
                    continue
                candidate = {
                    "format": APG_FORMAT,
                    "vertices": _rows(candidate_rotation),
                }
                key = json.dumps(
                    candidate["vertices"], sort_keys=True, separators=(",", ":")
                )
                results.setdefault(key, candidate)
    return [results[key] for key in sorted(results)]


def block_edge_replacements(block: dict[str, object]) -> list[dict[str, object]]:
    """Enumerate one embedded black-edge replacement while retaining sockets."""

    validate_block(block)
    original = _rotation_from_rows(block["vertices"])
    socket_vertices = {
        vertex
        for socket in block["sockets"]  # type: ignore[index]
        for vertex in socket["cycle"]
    }
    boundary_edges = {
        frozenset((cycle[i], cycle[(i + 1) % 6]))
        for socket in block["sockets"]  # type: ignore[index]
        for cycle in [socket["cycle"]]
        for i in range(6)
    }
    edges = sorted(
        (u, v)
        for u, neighbors in original.items()
        for v in neighbors
        if u < v
        and u not in socket_vertices
        and v not in socket_vertices
        and frozenset((u, v)) not in boundary_edges
    )
    results: dict[str, dict[str, object]] = {}
    for u, v in edges:
        reduced = copy.deepcopy(original)
        reduced[u].remove(v)
        reduced[v].remove(u)
        reduced[u] = _normalize(reduced[u])
        reduced[v] = _normalize(reduced[v])
        try:
            faces, _ = _trace_faces(reduced)
        except BlockError:
            continue
        merged = [face for face in faces if u in face and v in face]
        if len(merged) != 1 or len(set(merged[0])) != len(merged[0]):
            continue
        face = merged[0]
        for i, x in enumerate(face):
            for j in range(i + 1, len(face)):
                y = face[j]
                if (
                    x in socket_vertices
                    or y in socket_vertices
                    or y in reduced[x]
                    or {x, y} == {u, v}
                ):
                    continue
                rotation = copy.deepcopy(reduced)
                for vertex, new_neighbor, position in (
                    (x, y, rotation[x].index(face[(i - 1) % len(face)])),
                    (y, x, rotation[y].index(face[(j - 1) % len(face)])),
                ):
                    rotation[vertex].insert(position, new_neighbor)
                    rotation[vertex] = _normalize(rotation[vertex])
                candidate = _compact_block(
                    {
                        "format": BLOCK_FORMAT,
                        "provenance": {
                            "method": "embedded-edge-replacement",
                            "parent_order": len(original),
                            "removed_edge": [u, v],
                            "added_edge": [x, y],
                        },
                        "sockets": copy.deepcopy(block["sockets"]),
                        "vertices": _rows(rotation),
                    }
                )
                try:
                    validate_block(candidate)
                except BlockError:
                    continue
                key = json.dumps(
                    {"sockets": candidate["sockets"], "vertices": candidate["vertices"]},
                    sort_keys=True,
                    separators=(",", ":"),
                )
                results.setdefault(key, candidate)
    return [results[key] for key in sorted(results)]


def block_two_edge_switches(
    block: dict[str, object],
    *,
    stats: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    """Enumerate degree-preserving switches of two internal block edges.

    Both socket boundaries, including their stored closure recipes, are
    retained.  Only edges whose four endpoints lie outside both socket
    boundaries may be rewired.  For each disjoint edge pair, both alternate
    endpoint pairings and every cyclic insertion splice are validated exactly.
    """

    started = time.monotonic()
    validate_block(block)
    original = _rotation_from_rows(block["vertices"])
    degrees = {vertex: len(neighbors) for vertex, neighbors in original.items()}
    socket_vertices = {
        vertex
        for socket in block["sockets"]  # type: ignore[index]
        for vertex in socket["cycle"]
    }
    edges = sorted(
        (u, v)
        for u, neighbors in original.items()
        for v in neighbors
        if u < v and u not in socket_vertices and v not in socket_vertices
    )
    counts: Counter[str] = Counter()
    validation_prunes: Counter[str] = Counter()
    results: dict[str, dict[str, object]] = {}
    raw_survivor_hashes: list[str] = []
    for first, second in itertools.combinations(edges, 2):
        counts["edge_pair_combinations"] += 1
        endpoints = (*first, *second)
        if len(set(endpoints)) != 4:
            counts["pruned_shared_endpoint"] += 1
            continue
        counts["disjoint_edge_pairs"] += 1
        a, b = first
        c, d = second
        for new_edges in (((a, c), (b, d)), ((a, d), (b, c))):
            counts["pairing_attempts"] += 1
            if any(y in original[x] for x, y in new_edges):
                counts["pruned_existing_edge"] += 1
                continue
            if any(degrees[x] == degrees[y] for x, y in new_edges):
                counts["pruned_equal_endpoint_degree"] += 1
                continue
            reduced = copy.deepcopy(original)
            for x, y in (first, second):
                reduced[x].remove(y)
                reduced[y].remove(x)
                reduced[x] = _normalize(reduced[x])
                reduced[y] = _normalize(reduced[y])
            row_options: list[tuple[int, list[list[int]]]] = []
            for x, y in new_edges:
                for vertex, neighbor in ((x, y), (y, x)):
                    options = {
                        tuple(
                            _normalize(
                                row[:position] + [neighbor] + row[position:]
                            )
                        )
                        for row in [reduced[vertex]]
                        for position in range(len(row))
                    }
                    row_options.append(
                        (vertex, [list(option) for option in sorted(options)])
                    )
            option_lists = [options for _, options in row_options]
            for chosen in itertools.product(*option_lists):
                counts["splice_attempts"] += 1
                rotation = copy.deepcopy(reduced)
                for (vertex, _), row in zip(row_options, chosen):
                    rotation[vertex] = row
                candidate = _compact_block(
                    {
                        "format": BLOCK_FORMAT,
                        "provenance": {
                            "method": "internal-two-edge-switch",
                            "parent_order": len(original),
                            "removed_edges": [list(first), list(second)],
                            "added_edges": [list(edge) for edge in new_edges],
                        },
                        "sockets": copy.deepcopy(block["sockets"]),
                        "vertices": _rows(rotation),
                    }
                )
                counts["candidate_validation_attempts"] += 1
                try:
                    validate_block(candidate)
                except BlockError as error:
                    counts["candidate_validation_failures"] += 1
                    validation_prunes[str(error)] += 1
                    continue
                counts["raw_survivors"] += 1
                raw_survivor_hashes.append(canonical_map_hash(candidate))
                key = json.dumps(
                    {
                        "sockets": candidate["sockets"],
                        "vertices": candidate["vertices"],
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                )
                results.setdefault(key, candidate)
    survivors = [results[key] for key in sorted(results)]
    if stats is not None:
        stats.clear()
        stats.update(
            {
                "eligible_edges": len(edges),
                "counts": dict(sorted(counts.items())),
                "validation_prune_reasons": dict(sorted(validation_prunes.items())),
                "raw_survivor_hashes": sorted(raw_survivor_hashes),
                "distinct_survivor_hashes": [
                    canonical_map_hash(candidate) for candidate in survivors
                ],
                "distinct_survivors": len(survivors),
                "wall_seconds": time.monotonic() - started,
            }
        )
    return survivors


def apg_two_edge_switches(
    certificate: dict[str, object],
    *,
    stats: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    """Enumerate degree-preserving two-edge switches with every rotation splice."""

    started = time.monotonic()
    if certificate.get("format") != APG_FORMAT:
        raise BlockError("wrong APG certificate format")
    original = _rotation_from_rows(certificate["vertices"])
    _verify_apg_rotation(original)
    degrees = {v: len(ns) for v, ns in original.items()}
    edges = sorted(
        (u, v)
        for u, neighbors in original.items()
        for v in neighbors
        if u < v
    )
    counts: Counter[str] = Counter()
    validation_prunes: Counter[str] = Counter()
    results: dict[str, dict[str, object]] = {}
    raw_survivor_hashes: list[str] = []
    for first, second in itertools.combinations(edges, 2):
        counts["edge_pair_combinations"] += 1
        endpoints = (*first, *second)
        if len(set(endpoints)) != 4:
            counts["pruned_shared_endpoint"] += 1
            continue
        counts["disjoint_edge_pairs"] += 1
        a, b = first
        c, d = second
        for new_edges in (((a, c), (b, d)), ((a, d), (b, c))):
            counts["pairing_attempts"] += 1
            if any(y in original[x] for x, y in new_edges):
                counts["pruned_existing_edge"] += 1
                continue
            if any(degrees[x] == degrees[y] for x, y in new_edges):
                counts["pruned_equal_endpoint_degree"] += 1
                continue
            reduced = copy.deepcopy(original)
            for x, y in (first, second):
                reduced[x].remove(y)
                reduced[y].remove(x)
                reduced[x] = _normalize(reduced[x])
                reduced[y] = _normalize(reduced[y])
            row_options: list[tuple[int, list[list[int]]]] = []
            for x, y in new_edges:
                for vertex, neighbor in ((x, y), (y, x)):
                    options = {
                        tuple(_normalize(row[:position] + [neighbor] + row[position:]))
                        for row in [reduced[vertex]]
                        for position in range(len(row))
                    }
                    row_options.append((vertex, [list(option) for option in sorted(options)]))
            option_lists = [options for _, options in row_options]
            for chosen in itertools.product(*option_lists):
                counts["splice_attempts"] += 1
                rotation = copy.deepcopy(reduced)
                for (vertex, _), row in zip(row_options, chosen):
                    rotation[vertex] = row
                counts["candidate_validation_attempts"] += 1
                try:
                    _verify_apg_rotation(rotation)
                except BlockError as error:
                    counts["candidate_validation_failures"] += 1
                    validation_prunes[str(error)] += 1
                    continue
                candidate = {"format": APG_FORMAT, "vertices": _rows(rotation)}
                counts["raw_survivors"] += 1
                candidate_hash = canonical_map_hash(candidate)
                raw_survivor_hashes.append(candidate_hash)
                key = candidate_hash
                results.setdefault(key, candidate)
    survivors = [results[key] for key in sorted(results)]
    if stats is not None:
        stats.clear()
        stats.update(
            {
                "eligible_edges": len(edges),
                "counts": dict(sorted(counts.items())),
                "validation_prune_reasons": dict(sorted(validation_prunes.items())),
                "raw_survivor_hashes": sorted(raw_survivor_hashes),
                "distinct_survivor_hashes": sorted(results),
                "distinct_survivors": len(survivors),
                "wall_seconds": time.monotonic() - started,
            }
        )
    return survivors


def canonical_map_hash(certificate: dict[str, object]) -> str:
    rotation = _rotation_from_rows(certificate["vertices"])
    payload = json.dumps(_rows(rotation), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _cli() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    recover = sub.add_parser("recover")
    recover.add_argument("certificate", type=Path)
    recover.add_argument("output", type=Path)
    recover.add_argument("--source-url", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("blocks", nargs="+", type=Path)
    close = sub.add_parser("close")
    close.add_argument("block", type=Path)
    close.add_argument("output", type=Path)
    compose = sub.add_parser("compose")
    compose.add_argument("output", type=Path)
    compose.add_argument("blocks", nargs="+", type=Path)
    expand = sub.add_parser("expand")
    expand.add_argument("block", type=Path)
    expand.add_argument("output_directory", type=Path)
    switch = sub.add_parser("block-switch")
    switch.add_argument("block", type=Path)
    switch.add_argument("output_directory", type=Path)
    switch.add_argument("--stats", required=True, type=Path)
    apg_switch = sub.add_parser("apg-switch")
    apg_switch.add_argument("certificate", type=Path)
    apg_switch.add_argument("output_directory", type=Path)
    apg_switch.add_argument("--stats", required=True, type=Path)
    args = parser.parse_args()

    if args.command == "recover":
        certificate = load_json(args.certificate)
        candidates = recover_blocks(
            certificate,
            provenance={
                "method": "closure-fan-opening",
                "source_url": args.source_url,
            },
        )
        if not candidates:
            raise BlockError("no strict two-socket opening found")
        write_json(args.output, candidates[0])
        print(f"PASS recovered {len(candidates)} block(s); wrote {args.output}")
    elif args.command == "validate":
        for path in args.blocks:
            summary = validate_block(load_json(path))
            print(f"PASS {path}: {summary}")
    elif args.command == "close":
        certificate = close_block(load_json(args.block))
        write_json(args.output, certificate)
        print(f"PASS closed {args.block} -> {args.output}")
    elif args.command == "compose":
        blocks = [load_json(path) for path in args.blocks]
        result = compose_chain(blocks)
        write_json(args.output, result)
        print(f"PASS composed {len(blocks)} block(s) -> {args.output}")
    elif args.command == "expand":
        results = expand_block_once(load_json(args.block))
        for index, result in enumerate(results):
            write_json(args.output_directory / f"candidate_{index:04d}.json", result)
        print(f"PASS found {len(results)} one-step expansion(s)")
    elif args.command == "block-switch":
        stats: dict[str, object] = {}
        results = block_two_edge_switches(load_json(args.block), stats=stats)
        for index, result in enumerate(results):
            write_json(args.output_directory / f"neighbor_{index:04d}.json", result)
        write_json(args.stats, stats)
        print(
            f"PASS found {len(results)} distinct internal two-edge switch(es); "
            f"wrote {args.stats}"
        )
    elif args.command == "apg-switch":
        stats = {}
        results = apg_two_edge_switches(load_json(args.certificate), stats=stats)
        for index, result in enumerate(results):
            write_json(args.output_directory / f"survivor_{index:04d}.json", result)
        write_json(args.stats, stats)
        print(
            f"PASS found {len(results)} distinct APG two-edge switch survivor(s); "
            f"wrote {args.stats}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
