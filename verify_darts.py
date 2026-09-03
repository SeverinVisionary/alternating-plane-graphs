#!/usr/bin/env python3
"""Standalone dart-permutation checker for (3,4,5)-APG certificates.

This checker intentionally shares no implementation with ``verify.py`` or the
block/search modules.  It reconstructs faces from the successor permutation
on directed edges (using the opposite local turn convention) and derives all
counts from the supplied rotation system.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn


FORMAT = "apg-plane-rotation-v1"
ALLOWED = frozenset({3, 4, 5})


class DartCheckError(ValueError):
    """A certificate fails an exact dart-permutation gate."""


@dataclass(frozen=True)
class DartSummary:
    order: int
    edges: int
    faces: int
    vertex_counts: dict[int, int]
    face_counts: dict[int, int]


def _fail(message: str) -> NoReturn:
    raise DartCheckError(message)


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _reject_constant(token: str) -> NoReturn:
    raise ValueError(f"non-JSON numeric constant {token!r}")


def _reject_duplicate_object_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Independently reject parser-dependent duplicate JSON members."""

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def load(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(
            handle,
            parse_constant=_reject_constant,
            object_pairs_hook=_reject_duplicate_object_keys,
        )


def _read_rotation(data: object) -> dict[int, tuple[int, ...]]:
    if not isinstance(data, dict) or set(data) != {"format", "vertices"}:
        _fail("top level must contain exactly format and vertices")
    if data["format"] != FORMAT:
        _fail(f"format must be {FORMAT!r}")
    rows = data["vertices"]
    if not isinstance(rows, list) or not rows:
        _fail("vertices must be a nonempty array")

    rotation: dict[int, tuple[int, ...]] = {}
    last: int | None = None
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) != {"id", "clockwise"}:
            _fail(f"vertices[{index}] must contain id and clockwise")
        label = row["id"]
        if not _is_integer(label):
            _fail(f"vertices[{index}].id is not an integer")
        if label in rotation:
            _fail(f"duplicate vertex {label}")
        if last is not None and label <= last:
            _fail("vertex rows are not strictly increasing")
        neighbors = row["clockwise"]
        if not isinstance(neighbors, list) or not neighbors:
            _fail(f"vertex {label} has an empty clockwise list")
        if any(not _is_integer(value) for value in neighbors):
            _fail(f"vertex {label} names a non-integer neighbor")
        if len(set(neighbors)) != len(neighbors):
            _fail(f"vertex {label} repeats a neighbor")
        if label in neighbors:
            _fail(f"vertex {label} has a loop")
        if neighbors[0] != min(neighbors):
            _fail(f"vertex {label} rotation is not normalized")
        rotation[label] = tuple(neighbors)
        last = label
    return rotation


def _face_cycles(
    rotation: dict[int, tuple[int, ...]],
) -> tuple[tuple[tuple[int, ...], ...], dict[tuple[int, int], int]]:
    darts = {
        (vertex, neighbor)
        for vertex, neighbors in rotation.items()
        for neighbor in neighbors
    }
    unvisited = set(darts)
    face_of: dict[tuple[int, int], int] = {}
    faces: list[tuple[int, ...]] = []

    # This is the successor permutation with a clockwise *successor* turn;
    # verify.py uses the predecessor turn.  The two permutations enumerate the
    # same faces with opposite orientations, but are independent code paths.
    successor: dict[tuple[int, int], tuple[int, int]] = {}
    for source, target in darts:
        around_target = rotation[target]
        try:
            position = around_target.index(source)
        except ValueError as exc:  # pragma: no cover - symmetry gate normally wins
            raise DartCheckError(f"missing reverse dart {target}-{source}") from exc
        successor[(source, target)] = (
            target,
            around_target[(position + 1) % len(around_target)],
        )

    while unvisited:
        start = min(unvisited)
        dart = start
        local: set[tuple[int, int]] = set()
        boundary: list[int] = []
        while dart not in local:
            if dart not in unvisited:
                _fail("dart permutation entered a previously traced face")
            local.add(dart)
            unvisited.remove(dart)
            boundary.append(dart[0])
            dart = successor[dart]
        if dart != start:
            _fail("dart permutation cycle merged before returning to its start")
        face_id = len(faces)
        for item in local:
            face_of[item] = face_id
        faces.append(tuple(boundary))

    if len(face_of) != len(darts):
        _fail("not every dart received a face")
    return tuple(faces), face_of


def check(data: object, *, expected_order: int | None = None) -> DartSummary:
    rotation = _read_rotation(data)
    labels = set(rotation)
    for source, neighbors in rotation.items():
        for target in neighbors:
            if target not in labels:
                _fail(f"vertex {source} names missing vertex {target}")
            if source not in rotation[target]:
                _fail(f"edge {source}-{target} is asymmetric")

    reached: set[int] = set()
    pending = [min(labels)]
    while pending:
        vertex = pending.pop()
        if vertex in reached:
            continue
        reached.add(vertex)
        pending.extend(rotation[vertex])
    if reached != labels:
        _fail("graph is disconnected")

    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    if any(degree not in ALLOWED for degree in degrees.values()):
        _fail("a vertex degree is outside {3,4,5}")
    order = len(rotation)
    if expected_order is not None and order != expected_order:
        _fail(f"order {order} does not equal expected order {expected_order}")

    edges = sum(degrees.values()) // 2
    faces, face_of = _face_cycles(rotation)
    if order - edges + len(faces) != 2:
        _fail(f"sphere Euler equation failed: {order}-{edges}+{len(faces)}")
    face_sizes = [len(face) for face in faces]
    for index, face in enumerate(faces):
        if face_sizes[index] not in ALLOWED:
            _fail(f"face {index} has forbidden size {face_sizes[index]}")
        if len(set(face)) != len(face):
            _fail(f"face {index} repeats a vertex")

    for source, neighbors in rotation.items():
        for target in neighbors:
            if source >= target:
                continue
            if degrees[source] == degrees[target]:
                _fail(f"edge {source}-{target} joins equal degrees")
            left = face_of[(source, target)]
            right = face_of[(target, source)]
            if left == right:
                _fail(f"edge {source}-{target} has one incident face")
            if face_sizes[left] == face_sizes[right]:
                _fail(f"edge {source}-{target} joins equal face sizes")

    vertex_counts = {size: sum(degree == size for degree in degrees.values()) for size in sorted(ALLOWED)}
    face_counts = {size: sum(size == face_size for face_size in face_sizes) for size in sorted(ALLOWED)}
    if vertex_counts != face_counts:
        _fail(f"vertex/face histograms differ: {vertex_counts} != {face_counts}")
    r = vertex_counts[3]
    if vertex_counts[5] != r - 4 or vertex_counts[4] != order - 2 * r + 4:
        _fail("APG histogram formula failed")
    if edges != 2 * order - 2 or len(faces) != order:
        _fail("APG edge/face count formula failed")
    return DartSummary(order, edges, len(faces), vertex_counts, face_counts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificates", nargs="+", type=Path)
    parser.add_argument("--expect-order", type=int)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.expect_order is not None and len(args.certificates) != 1:
        parser.error("--expect-order requires exactly one certificate")
    ok = True
    for path in args.certificates:
        try:
            summary = check(load(path), expected_order=args.expect_order)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            print(f"FAIL {path}: {exc}", file=sys.stderr)
            ok = False
            continue
        print(
            f"PASS {path}: order={summary.order} edges={summary.edges} "
            f"faces={summary.faces} vertex_counts={summary.vertex_counts}"
        )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
