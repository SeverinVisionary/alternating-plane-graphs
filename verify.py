#!/usr/bin/env python3
"""Independent exact verifier for (3,4,5)-alternating plane graphs.

The certificate is a labelled combinatorial embedding (rotation system), not a
drawing.  Faces and every statistic used below are reconstructed from that
rotation system; certificates contain no trusted degree or face cache.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn


FORMAT = "apg-plane-rotation-v1"
ALLOWED_SIZES = frozenset({3, 4, 5})


class VerificationError(ValueError):
    """A certificate is well-formed JSON but fails an exact verification gate."""


@dataclass(frozen=True)
class VerificationSummary:
    order: int
    edges: int
    faces: int
    vertex_counts: dict[int, int]
    face_counts: dict[int, int]


def _fail(message: str) -> NoReturn:
    raise VerificationError(message)


def _is_int(value: object) -> bool:
    # bool is a subclass of int and must not be accepted as a vertex label.
    return isinstance(value, int) and not isinstance(value, bool)


def _reject_constant(token: str) -> NoReturn:
    raise ValueError(f"non-JSON numeric constant {token!r}")


def _reject_duplicate_object_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject duplicate members at every JSON object depth.

    JSON duplicate-key behaviour is parser-dependent.  A certificate needs one
    unambiguous byte-level meaning before its exact rotation system can be
    verified, rather than silently taking whichever duplicate this parser keeps.
    """

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def load_certificate(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(
            handle,
            parse_constant=_reject_constant,
            object_pairs_hook=_reject_duplicate_object_keys,
        )


def _parse_rotation(data: object) -> dict[int, tuple[int, ...]]:
    if not isinstance(data, dict):
        _fail("top level must be a JSON object")
    if data.get("format") != FORMAT:
        _fail(f"format must be exactly {FORMAT!r}")
    if set(data) != {"format", "vertices"}:
        _fail("top level must contain exactly 'format' and 'vertices'")

    rows = data["vertices"]
    if not isinstance(rows, list) or not rows:
        _fail("'vertices' must be a nonempty JSON array")

    rotation: dict[int, tuple[int, ...]] = {}
    previous_label: int | None = None
    for index, row in enumerate(rows):
        where = f"vertices[{index}]"
        if not isinstance(row, dict) or set(row) != {"id", "clockwise"}:
            _fail(f"{where} must contain exactly 'id' and 'clockwise'")
        label = row["id"]
        if not _is_int(label):
            _fail(f"{where}.id must be an integer (not boolean)")
        if label in rotation:
            _fail(f"duplicate vertex label {label}")
        if previous_label is not None and label <= previous_label:
            _fail("vertex rows must be in strictly increasing label order")

        neighbors = row["clockwise"]
        if not isinstance(neighbors, list):
            _fail(f"{where}.clockwise must be a JSON array")
        for neighbor in neighbors:
            if not _is_int(neighbor):
                _fail(f"{where}.clockwise entries must be integer labels")
        if len(set(neighbors)) != len(neighbors):
            _fail(f"vertex {label} has a repeated neighbor (parallel edge)")
        if label in neighbors:
            _fail(f"vertex {label} has a loop")
        if neighbors and neighbors[0] != min(neighbors):
            _fail(
                f"vertex {label} rotation is not normalized: its smallest "
                "neighbor must come first"
            )

        rotation[label] = tuple(neighbors)
        previous_label = label

    return rotation


def verify_certificate(
    data: object, *, expected_order: int | None = None
) -> VerificationSummary:
    rotation = _parse_rotation(data)
    labels = set(rotation)
    order = len(rotation)
    if expected_order is not None and order != expected_order:
        _fail(f"order {order} does not equal expected order {expected_order}")

    # The graph is reconstructed solely from the neighbour rotations.
    for vertex, neighbors in rotation.items():
        for neighbor in neighbors:
            if neighbor not in labels:
                _fail(f"vertex {vertex} names missing vertex {neighbor}")
            if vertex not in rotation[neighbor]:
                _fail(f"edge {vertex}-{neighbor} is not symmetric")

    degree_sum = sum(len(neighbors) for neighbors in rotation.values())
    if degree_sum % 2:
        _fail("sum of degrees is odd")
    edge_count = degree_sum // 2

    # Connectivity is checked independently of the claimed embedding.
    reached: set[int] = set()
    stack = [next(iter(rotation))]
    while stack:
        vertex = stack.pop()
        if vertex in reached:
            continue
        reached.add(vertex)
        stack.extend(neighbor for neighbor in rotation[vertex] if neighbor not in reached)
    if reached != labels:
        missing = sorted(labels - reached)
        _fail(f"graph is disconnected; unreachable labels begin {missing[:5]}")

    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    bad_degrees = {vertex: degree for vertex, degree in degrees.items() if degree not in ALLOWED_SIZES}
    if bad_degrees:
        vertex = min(bad_degrees)
        _fail(f"vertex {vertex} has forbidden degree {bad_degrees[vertex]}")
    # A dart (u,v) advances along the face on its left to the dart leaving v
    # immediately before u in v's clockwise rotation.  The inverse convention
    # would merely reverse every facial walk and yields the same checks.
    darts = {(vertex, neighbor) for vertex, neighbors in rotation.items() for neighbor in neighbors}
    face_of: dict[tuple[int, int], int] = {}
    faces: list[tuple[tuple[int, int], ...]] = []
    for start in sorted(darts):
        if start in face_of:
            continue
        face_id = len(faces)
        walk: list[tuple[int, int]] = []
        dart = start
        local: set[tuple[int, int]] = set()
        while dart not in local:
            if dart in face_of:
                _fail("facial walk entered a previously traced face before closing")
            if dart not in darts:
                _fail(f"facial walk reached nonexistent dart {dart}")
            local.add(dart)
            walk.append(dart)
            u, v = dart
            around_v = rotation[v]
            position = around_v.index(u)
            dart = (v, around_v[(position - 1) % len(around_v)])
        if dart != start:
            _fail(f"facial walk from {start} repeated dart {dart} before closing")
        for used in walk:
            face_of[used] = face_id
        faces.append(tuple(walk))

    if set(face_of) != darts or len(face_of) != 2 * edge_count:
        _fail("not every directed edge belongs to exactly one reconstructed face")

    face_count = len(faces)
    euler = order - edge_count + face_count
    if euler != 2:
        _fail(
            "rotation system is not a sphere embedding: "
            f"V-E+F = {order}-{edge_count}+{face_count} = {euler}"
        )

    face_sizes = [len(face) for face in faces]
    for face_id, size in enumerate(face_sizes):
        if size not in ALLOWED_SIZES:
            _fail(f"face {face_id} has forbidden size {size}")
        face_vertices = [vertex for vertex, _ in faces[face_id]]
        if len(set(face_vertices)) != len(face_vertices):
            _fail(f"face {face_id} repeats a vertex in its facial walk")
    for u, v in sorted(darts):
        if u >= v:
            continue
        left = face_of[(u, v)]
        right = face_of[(v, u)]
        if face_sizes[left] == face_sizes[right]:
            _fail(
                f"edge {u}-{v} separates two faces of size "
                f"{face_sizes[left]} (faces {left} and {right})"
            )

    for vertex, neighbors in rotation.items():
        for neighbor in neighbors:
            if vertex < neighbor and degrees[vertex] == degrees[neighbor]:
                _fail(
                    f"adjacent vertices {vertex} and {neighbor} both have "
                    f"degree {degrees[vertex]}"
                )

    # Theorem 3.2 and its Euler consequences are predicted-object gates.  They
    # follow from a correct (3,4,5)-APG, but checking them explicitly makes a
    # face-traversal or alternation bug much harder to hide behind a plausible
    # certificate.  Missing allowed sizes are counted as zero: Definition 3.1
    # says all sizes lie in the set, not that every listed size must occur.
    vertex_degrees = list(degrees.values())
    vertex_counts = {
        size: vertex_degrees.count(size) for size in sorted(ALLOWED_SIZES)
    }
    face_counts = {size: face_sizes.count(size) for size in sorted(ALLOWED_SIZES)}
    if vertex_counts != face_counts:
        _fail(
            "Theorem 3.2 histogram mismatch: "
            f"vertices={vertex_counts}, faces={face_counts}"
        )
    r = vertex_counts[3]
    if vertex_counts[5] != r - 4 or vertex_counts[4] != order - 2 * r + 4:
        _fail(
            "(3,4,5)-APG histogram formula failed: "
            f"order={order}, counts={vertex_counts}"
        )
    if edge_count != 2 * order - 2 or face_count != order:
        _fail(
            "(3,4,5)-APG count identities failed: "
            f"V={order}, E={edge_count}, F={face_count}"
        )

    return VerificationSummary(
        order=order,
        edges=edge_count,
        faces=face_count,
        vertex_counts=vertex_counts,
        face_counts=face_counts,
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify exact JSON rotation-system certificates for (3,4,5)-APGs."
    )
    parser.add_argument("certificates", nargs="+", type=Path)
    parser.add_argument(
        "--expect-order",
        type=int,
        help="require this order (only valid with one certificate)",
    )
    args = parser.parse_args(argv)
    if args.expect_order is not None and len(args.certificates) != 1:
        parser.error("--expect-order requires exactly one certificate")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    all_valid = True
    for path in args.certificates:
        try:
            data = load_certificate(path)
            summary = verify_certificate(data, expected_order=args.expect_order)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            all_valid = False
            continue
        print(
            f"PASS {path}: order={summary.order} edges={summary.edges} "
            f"faces={summary.faces} vertex_counts={summary.vertex_counts} "
            f"face_counts={summary.face_counts}"
        )
    return 0 if all_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
