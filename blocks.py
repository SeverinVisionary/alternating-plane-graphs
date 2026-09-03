#!/usr/bin/env python3
"""Exact two-hexagon block operations from Section 8 of the APG paper.

This module manipulates labelled combinatorial maps.  It intentionally does not
import the final APG verifier: block validation, face traversal, opening,
closing, and composition have their own implementation.  Tests pass every
closed result to ``verify.py`` in a separate process.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations, product
from typing import Iterable


APG_FORMAT = "apg-plane-rotation-v1"
BLOCK_FORMAT = "apg-two-hexagon-block-v1"
Rotation = dict[int, tuple[int, ...]]
Dart = tuple[int, int]


class BlockError(ValueError):
    """The supplied rotation system does not satisfy the block contract."""


@dataclass(frozen=True)
class Socket:
    """One marked hexagonal block face in its facial orientation."""

    boundary: tuple[int, ...]
    whites: tuple[int, ...]


@dataclass(frozen=True)
class ClosureFan:
    """Two chords from a degree-4 hub to two degree-3 leaves."""

    hub: int
    leaves: tuple[int, int]

    @property
    def whites(self) -> frozenset[int]:
        return frozenset((self.hub, *self.leaves))

    @property
    def edges(self) -> tuple[tuple[int, int], tuple[int, int]]:
        return ((self.hub, self.leaves[0]), (self.hub, self.leaves[1]))


@dataclass(frozen=True)
class Block:
    """A validated block and, when known, the closure fans that exposed it."""

    rotation: Rotation
    sockets: tuple[Socket, Socket]
    source_fans: tuple[ClosureFan, ...] = ()

    @property
    def order(self) -> int:
        return len(self.rotation)


@dataclass(frozen=True)
class CompositionVariant:
    """One replayable successful two-block Section-8 gluing.

    ``compose_blocks`` intentionally preserves its historical first-success
    convention for old replay hashes.  New promotion code needs the broader
    positive search space, so this record retains every choice that can matter:
    reflection of each input, which socket of each input was joined, and the
    cyclic correspondence shift of the three white vertices.
    """

    block: Block
    inner_reflected: bool
    outer_reflected: bool
    inner_socket: int
    outer_socket: int
    shift: int


@dataclass(frozen=True)
class RelaxedBlock:
    """A role-compatible two-hex opening, without the strict Section-8 gate.

    This is an over-approximation for search triage.  Its socket whites may be
    adjacent to degree 3 or degree 5 vertices and the hexagons may border
    triangles or pentagons.  It is not accepted as a reusable block until a
    concrete gluing and all closure faces are independently checked.
    """

    rotation: Rotation
    sockets: tuple[Socket, Socket]
    source_fans: tuple[ClosureFan, ...] = ()


@dataclass(frozen=True)
class FaceTrace:
    faces: tuple[tuple[int, ...], ...]
    face_of: dict[Dart, int]


def _rotate_to_smallest(values: Iterable[int]) -> tuple[int, ...]:
    items = tuple(values)
    if not items:
        return ()
    start = items.index(min(items))
    return items[start:] + items[:start]


def normalize_rotation(rotation: dict[int, Iterable[int]]) -> Rotation:
    return {
        vertex: _rotate_to_smallest(neighbors)
        for vertex, neighbors in sorted(rotation.items())
    }


def rotation_from_certificate(data: object) -> Rotation:
    """Read the small deterministic JSON certificate schema used by verify.py."""

    if not isinstance(data, dict) or data.get("format") != APG_FORMAT:
        raise BlockError(f"certificate format must be {APG_FORMAT!r}")
    rows = data.get("vertices")
    if not isinstance(rows, list) or not rows:
        raise BlockError("certificate vertices must be a nonempty list")
    rotation: dict[int, tuple[int, ...]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "clockwise"}:
            raise BlockError("each vertex row must contain id and clockwise")
        vertex = row["id"]
        neighbors = row["clockwise"]
        if not isinstance(vertex, int) or isinstance(vertex, bool):
            raise BlockError("vertex labels must be integers")
        if not isinstance(neighbors, list) or any(
            not isinstance(value, int) or isinstance(value, bool) for value in neighbors
        ):
            raise BlockError("clockwise lists must contain integer labels")
        if vertex in rotation:
            raise BlockError(f"duplicate vertex {vertex}")
        rotation[vertex] = tuple(neighbors)
    return normalize_rotation(rotation)


def rotation_to_certificate(rotation: Rotation) -> dict[str, object]:
    normalized = normalize_rotation(rotation)
    return {
        "format": APG_FORMAT,
        "vertices": [
            {"clockwise": list(normalized[vertex]), "id": vertex}
            for vertex in sorted(normalized)
        ],
    }


def mirror_rotation(rotation: Rotation) -> Rotation:
    """Return the orientation-reversed rotation system.

    Reversing every cyclic neighbour order reflects the spherical embedding;
    normalisation only chooses deterministic starting neighbours and does not
    change the reflected cyclic order.
    """

    return normalize_rotation(
        {vertex: tuple(reversed(neighbors)) for vertex, neighbors in rotation.items()}
    )


def mirror_block(block: Block) -> Block:
    """Reflect a block and reconstruct its marked sockets."""

    rotation = mirror_rotation(block.rotation)
    return Block(rotation, validate_block(rotation))


def block_to_certificate(block: Block) -> dict[str, object]:
    normalized = normalize_rotation(block.rotation)
    return {
        "format": BLOCK_FORMAT,
        "sockets": [
            {
                "boundary": list(socket.boundary),
                "whites": list(socket.whites),
            }
            for socket in block.sockets
        ],
        "vertices": [
            {"clockwise": list(normalized[vertex]), "id": vertex}
            for vertex in sorted(normalized)
        ],
    }


def trace_faces(rotation: Rotation) -> FaceTrace:
    """Trace every face using the clockwise predecessor dart convention."""

    darts = {
        (vertex, neighbor)
        for vertex, neighbors in rotation.items()
        for neighbor in neighbors
    }
    unused = set(darts)
    face_of: dict[Dart, int] = {}
    faces: list[tuple[int, ...]] = []
    while unused:
        start = min(unused)
        dart = start
        local: set[Dart] = set()
        boundary: list[int] = []
        while dart not in local:
            if dart not in unused:
                raise BlockError("facial walk entered a previous face")
            unused.remove(dart)
            local.add(dart)
            u, v = dart
            boundary.append(u)
            around_v = rotation[v]
            try:
                position = around_v.index(u)
            except ValueError as exc:
                raise BlockError(f"asymmetric dart {u}-{v}") from exc
            dart = (v, around_v[(position - 1) % len(around_v)])
        if dart != start:
            raise BlockError("facial walk repeated before returning to its start")
        face_id = len(faces)
        for used in local:
            face_of[used] = face_id
        faces.append(tuple(boundary))
    if set(face_of) != darts:
        raise BlockError("not every dart was assigned to a face")
    return FaceTrace(tuple(faces), face_of)


def _validate_graph(rotation: Rotation) -> None:
    if not rotation:
        raise BlockError("empty rotation system")
    labels = set(rotation)
    for vertex, neighbors in rotation.items():
        if not neighbors:
            raise BlockError(f"isolated vertex {vertex}")
        if len(neighbors) != len(set(neighbors)):
            raise BlockError(f"vertex {vertex} repeats a neighbor")
        if vertex in neighbors:
            raise BlockError(f"loop at vertex {vertex}")
        for neighbor in neighbors:
            if neighbor not in labels or vertex not in rotation[neighbor]:
                raise BlockError(f"asymmetric edge {vertex}-{neighbor}")

    reached: set[int] = set()
    stack = [min(labels)]
    while stack:
        vertex = stack.pop()
        if vertex in reached:
            continue
        reached.add(vertex)
        stack.extend(rotation[vertex])
    if reached != labels:
        raise BlockError("block graph is disconnected")


def validate_block(rotation: Rotation) -> tuple[Socket, Socket]:
    """Validate and recover the two strict Section 8 socket faces."""

    rotation = normalize_rotation(rotation)
    _validate_graph(rotation)
    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    if any(degree not in {2, 3, 4, 5} for degree in degrees.values()):
        raise BlockError("block vertex degree outside {2,3,4,5}")
    white_vertices = {vertex for vertex, degree in degrees.items() if degree == 2}
    if len(white_vertices) != 6:
        raise BlockError(f"expected six degree-2 whites, found {len(white_vertices)}")
    for white in white_vertices:
        if any(degrees[neighbor] != 5 for neighbor in rotation[white]):
            raise BlockError(f"white vertex {white} is not surrounded by degree-5 vertices")

    traced = trace_faces(rotation)
    edge_count = sum(degrees.values()) // 2
    if len(rotation) - edge_count + len(traced.faces) != 2:
        raise BlockError("block rotation is not a sphere embedding")
    if any(len(face) not in {3, 4, 5, 6} for face in traced.faces):
        raise BlockError("block contains a face outside {3,4,5,6}")
    if any(len(set(face)) != len(face) for face in traced.faces):
        raise BlockError("block has a repeated vertex on a facial walk")

    six_faces = [face for face in traced.faces if len(face) == 6]
    if len(six_faces) != 2:
        raise BlockError(f"expected two hexagonal sockets, found {len(six_faces)}")
    sockets: list[Socket] = []
    socket_whites: set[int] = set()
    for raw_face in six_faces:
        if len(set(raw_face)) != 6:
            raise BlockError("socket boundary repeats a vertex")
        boundary = _rotate_to_smallest(raw_face)
        kinds = tuple(degrees[vertex] for vertex in boundary)
        if any(
            {kinds[index], kinds[(index + 1) % 6]} != {2, 5}
            for index in range(6)
        ):
            raise BlockError("socket boundary does not alternate degrees 2 and 5")
        whites = tuple(vertex for vertex in boundary if degrees[vertex] == 2)
        if socket_whites.intersection(whites):
            raise BlockError("the two sockets share a white vertex")
        socket_whites.update(whites)
        sockets.append(Socket(boundary, whites))
    if socket_whites != white_vertices:
        raise BlockError("degree-2 whites are not exactly the socket whites")

    for u, neighbors in rotation.items():
        for v in neighbors:
            if u < v and degrees[u] == degrees[v]:
                raise BlockError(f"edge {u}-{v} joins equal vertex degrees")
            if u >= v:
                continue
            left = traced.face_of[(u, v)]
            right = traced.face_of[(v, u)]
            if left == right:
                raise BlockError(f"edge {u}-{v} borders one face twice")
            left_size = len(traced.faces[left])
            right_size = len(traced.faces[right])
            if left_size == right_size:
                raise BlockError(f"edge {u}-{v} joins equal face sizes")
            if 6 in {left_size, right_size} and {left_size, right_size} != {5, 6}:
                raise BlockError("a socket is adjacent to a non-pentagonal face")

    sockets.sort(key=lambda socket: socket.boundary)
    return (sockets[0], sockets[1])


def validate_relaxed_block(rotation: Rotation) -> tuple[Socket, Socket]:
    """Validate necessary role-specific conditions for a two-hex opening.

    Compared with :func:`validate_block`, this deliberately permits socket
    whites to meet degree 3 as well as degree 5 and permits a hexagon's
    neighbouring face to be a triangle as well as a pentagon.  The resulting
    object is only a candidate: it still needs an explicit composition and
    closure check before it can be called compatible.
    """

    rotation = normalize_rotation(rotation)
    _validate_graph(rotation)
    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    if any(degree not in {2, 3, 4, 5} for degree in degrees.values()):
        raise BlockError("relaxed block vertex degree outside {2,3,4,5}")

    traced = trace_faces(rotation)
    edge_count = sum(degrees.values()) // 2
    if len(rotation) - edge_count + len(traced.faces) != 2:
        raise BlockError("relaxed block rotation is not a sphere embedding")
    faces = traced.faces
    if any(len(face) not in {3, 4, 5, 6} for face in faces):
        raise BlockError("relaxed block contains a face outside {3,4,5,6}")
    if any(len(set(face)) != len(face) for face in faces):
        raise BlockError("relaxed block has a repeated vertex on a face")

    six_faces = [face for face in faces if len(face) == 6]
    if len(six_faces) != 2:
        raise BlockError("expected two hexagonal relaxed sockets")
    socket_whites: set[int] = set()
    sockets: list[Socket] = []
    marked_ids = {index for index, face in enumerate(faces) if len(face) == 6}
    for raw_face in six_faces:
        boundary = _rotate_to_smallest(raw_face)
        if len(set(boundary)) != 6:
            raise BlockError("relaxed socket boundary repeats a vertex")
        kinds = tuple(degrees[vertex] for vertex in boundary)
        whites = tuple(vertex for vertex in boundary if degrees[vertex] == 2)
        if len(whites) != 3 or any(kinds[index] == 2 and kinds[(index + 1) % 6] == 2 for index in range(6)):
            raise BlockError("relaxed socket must alternate degree-2 and non-white vertices")
        if any(degrees[neighbor] not in {3, 5} for white in whites for neighbor in rotation[white]):
            raise BlockError("relaxed socket white is not gluable at degree 4")
        if socket_whites.intersection(whites):
            raise BlockError("the two relaxed sockets share a white vertex")
        socket_whites.update(whites)
        sockets.append(Socket(boundary, whites))
        for index, vertex in enumerate(raw_face):
            neighbor = raw_face[(index + 1) % 6]
            other_id = traced.face_of[(neighbor, vertex)]
            if other_id in marked_ids or len(faces[other_id]) not in {3, 5}:
                raise BlockError("relaxed socket hexagon is not bordered by 3/5 faces")

    if len(socket_whites) != 6 or {vertex for vertex, degree in degrees.items() if degree == 2} != socket_whites:
        raise BlockError("relaxed degree-2 vertices are not exactly the socket whites")
    for u, neighbors in rotation.items():
        for v in neighbors:
            if u >= v:
                continue
            if degrees[u] == degrees[v]:
                raise BlockError(f"relaxed block has equal adjacent degrees at {u}-{v}")
            left = traced.face_of[(u, v)]
            right = traced.face_of[(v, u)]
            if left in marked_ids or right in marked_ids:
                other = right if left in marked_ids else left
                if len(faces[other]) not in {3, 5}:
                    raise BlockError("relaxed socket edge has a forbidden adjacent face")
            elif len(faces[left]) == len(faces[right]):
                raise BlockError("relaxed block has equal adjacent face sizes")

    sockets.sort(key=lambda socket: socket.boundary)
    return sockets[0], sockets[1]


def candidate_closure_fans(rotation: Rotation) -> tuple[ClosureFan, ...]:
    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    candidates: list[ClosureFan] = []
    for hub in sorted(rotation):
        if degrees[hub] != 4:
            continue
        leaves = sorted(
            neighbor for neighbor in rotation[hub] if degrees.get(neighbor) == 3
        )
        candidates.extend(
            ClosureFan(hub, pair) for pair in combinations(leaves, 2)
        )
    return tuple(candidates)


def _delete_edges(rotation: Rotation, edges: Iterable[tuple[int, int]]) -> Rotation:
    mutable = {vertex: list(neighbors) for vertex, neighbors in rotation.items()}
    for u, v in edges:
        if v not in mutable.get(u, ()) or u not in mutable.get(v, ()):
            raise BlockError(f"cannot delete missing edge {u}-{v}")
        mutable[u].remove(v)
        mutable[v].remove(u)
    return normalize_rotation(mutable)


def opening_scan(rotation: Rotation) -> tuple[Block, ...]:
    """Open every pair of disjoint closure fans that yields a strict block."""

    rotation = normalize_rotation(rotation)
    found: dict[tuple[tuple[int, tuple[int, ...]], ...], Block] = {}
    for first, second in combinations(candidate_closure_fans(rotation), 2):
        if first.whites.intersection(second.whites):
            continue
        try:
            opened = _delete_edges(rotation, (*first.edges, *second.edges))
            sockets = validate_block(opened)
        except BlockError:
            continue
        if {first.whites, second.whites} != {
            frozenset(socket.whites) for socket in sockets
        }:
            continue
        fingerprint = tuple(opened.items())
        found[fingerprint] = Block(opened, sockets, (first, second))
    return tuple(found[key] for key in sorted(found))


def opening_scan_with_mirror(rotation: Rotation) -> tuple[Block, ...]:
    """Scan both an embedding and its reflected orientation."""

    found: dict[tuple[tuple[int, tuple[int, ...]], ...], Block] = {}
    for candidate in (normalize_rotation(rotation), mirror_rotation(rotation)):
        for block in opening_scan(candidate):
            key = tuple(block.rotation.items())
            found[key] = block
    return tuple(found[key] for key in sorted(found))


def relaxed_opening_scan(rotation: Rotation) -> tuple[RelaxedBlock, ...]:
    """Enumerate role-compatible openings from one closed rotation.

    The scan uses the same degree-4/degree-3 fan candidates as the strict
    opening scan, but applies :func:`validate_relaxed_block` after deleting
    the four fan edges.  It is intentionally an over-approximation and does
    not assert that any returned opening composes with another block.
    """

    rotation = normalize_rotation(rotation)
    fans = candidate_closure_fans(rotation)
    found: dict[tuple[tuple[int, tuple[int, ...]], ...], RelaxedBlock] = {}
    for first, second in combinations(fans, 2):
        if first.whites.intersection(second.whites):
            continue
        try:
            opened = _delete_edges(rotation, (*first.edges, *second.edges))
            sockets = validate_relaxed_block(opened)
        except BlockError:
            continue
        if {first.whites, second.whites} != {
            frozenset(socket.whites) for socket in sockets
        }:
            continue
        block = RelaxedBlock(opened, sockets, (first, second))
        found[tuple(opened.items())] = block
    return tuple(found[key] for key in sorted(found))


def _add_chord(rotation: Rotation, face: tuple[int, ...], a: int, b: int) -> Rotation:
    if a == b or a not in face or b not in face:
        raise BlockError("chord endpoints must be distinct vertices of one face")
    if b in rotation[a] or a in rotation[b]:
        raise BlockError(f"chord {a}-{b} already exists")
    if len(set(face)) != len(face):
        raise BlockError("cannot add a chord to a face with repeated vertices")

    mutable = {vertex: list(neighbors) for vertex, neighbors in rotation.items()}
    size = len(face)
    for endpoint, other in ((a, b), (b, a)):
        position = face.index(endpoint)
        previous = face[(position - 1) % size]
        following = face[(position + 1) % size]
        around = mutable[endpoint]
        previous_position = around.index(previous)
        if around[(previous_position - 1) % len(around)] != following:
            raise BlockError("face orientation disagrees with endpoint rotation")
        around.insert(previous_position, other)
    return normalize_rotation(mutable)


def _face_containing(rotation: Rotation, vertices: set[int]) -> tuple[int, ...]:
    candidates = [
        face
        for face in trace_faces(rotation).faces
        if vertices.issubset(face) and len(face) > 3
    ]
    if not candidates:
        raise BlockError(f"no nontriangular face contains {sorted(vertices)}")
    return max(candidates, key=lambda face: (len(face), tuple(face)))


def close_block_with_hubs(block: Block, hub_indices: tuple[int, int]) -> Rotation:
    """Close both sockets using explicit boundary-order hub indices.

    Each index selects one of the three degree-2 socket whites in ascending
    label order.  A caller that needs all possible closures should use
    :func:`close_block_variants`.
    """

    if len(hub_indices) != 2 or any(index not in range(3) for index in hub_indices):
        raise BlockError("hub_indices must contain two values from {0,1,2}")
    sockets = validate_block(block.rotation)
    rotation = block.rotation
    for socket, hub_index in zip(sockets, hub_indices):
        # Keep the historical deterministic convention (and its public
        # replay hash): explicit hub indices are in ascending label order.
        whites = tuple(sorted(socket.whites))
        hub = whites[hub_index]
        leaves = tuple(white for index, white in enumerate(whites) if index != hub_index)
        face = _face_containing(rotation, set(whites))
        rotation = _add_chord(rotation, face, hub, leaves[0])
        face = _face_containing(rotation, {hub, leaves[1]})
        rotation = _add_chord(rotation, face, hub, leaves[1])
    return normalize_rotation(rotation)


def close_block(block: Block) -> Rotation:
    """Close both sockets with the deterministic reference fan operation."""

    return close_block_with_hubs(block, (0, 0))


def close_block_variants(
    block: Block,
) -> tuple[tuple[tuple[int, int], Rotation], ...]:
    """Enumerate every successful 3x3 socket-hub closure."""

    variants: list[tuple[tuple[int, int], Rotation]] = []
    for hub_indices in product(range(3), repeat=2):
        try:
            rotation = close_block_with_hubs(block, hub_indices)
        except BlockError:
            continue
        variants.append((hub_indices, rotation))
    return tuple(variants)


def open_cap_fans(rotation: Rotation, fans: Iterable[ClosureFan]) -> Block:
    """Delete two marked closed-APG cap fans and recover a strict block.

    A Section 8 cap has one degree-4 hub joined to two degree-3 leaves.
    Removing its two fan edges lowers precisely those three vertices to
    degree 2.  This is the inverse of :func:`close_block_with_hubs`, but it
    deliberately starts from a closed rotation so a Boolean closed-map search
    can mark only the four fan edges.  The strict block validator remains the
    acceptance boundary: arbitrary 4--3--3 fan edges are not assumed to open
    to sockets.
    """

    rotation = normalize_rotation(rotation)
    selected = tuple(fans)
    if len(selected) != 2:
        raise BlockError("exactly two cap fans are required")
    if len({vertex for fan in selected for vertex in fan.whites}) != 6:
        raise BlockError("the two cap fans must have six distinct vertices")

    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    edges: list[tuple[int, int]] = []
    for fan in selected:
        if fan.hub not in rotation or any(leaf not in rotation for leaf in fan.leaves):
            raise BlockError("cap fan names a missing vertex")
        if degrees[fan.hub] != 4 or any(degrees[leaf] != 3 for leaf in fan.leaves):
            raise BlockError("cap fan must have a degree-4 hub and degree-3 leaves")
        edges.extend(fan.edges)

    opened = _delete_edges(rotation, edges)
    sockets = validate_block(opened)
    expected_whites = {fan.whites for fan in selected}
    observed_whites = {frozenset(socket.whites) for socket in sockets}
    if observed_whites != expected_whites:
        raise BlockError("cap fans did not become the two strict socket triples")
    return Block(opened, sockets, selected)


def _neighbors_on_face(face: tuple[int, ...], vertex: int) -> tuple[int, int]:
    position = face.index(vertex)
    return (face[(position - 1) % len(face)], face[(position + 1) % len(face)])


def compose_blocks_alignments(
    inner: Block,
    outer: Block,
    *,
    inner_socket: int = 1,
    outer_socket: int = 0,
) -> tuple[tuple[int, Block], ...]:
    """Return every successful cyclic white-vertex correspondence.

    The returned pairs are ``(shift, block)`` in cyclic shift order.  This is
    deliberately broader than :func:`compose_blocks`, whose legacy contract is
    to return the first successful alignment only.  It preserves enough data
    for a downstream final certificate to replay an asymmetric gluing rather
    than assuming the first successful shift represents every possibility.
    """

    inner_sockets = validate_block(inner.rotation)
    outer_sockets = validate_block(outer.rotation)
    if inner_socket not in range(2) or outer_socket not in range(2):
        raise BlockError("socket indices must each be 0 or 1")
    socket_a = inner_sockets[inner_socket]
    socket_b = outer_sockets[outer_socket]
    whites_a = list(socket_a.whites)
    raw_whites_b = list(socket_b.whites)

    # Gluing two oriented boundary components reverses their cyclic order.  Try
    # the three rotations deterministically because the smallest-labelled
    # boundary anchor is unrelated to the intended white correspondence.
    reversed_b = [raw_whites_b[0], raw_whites_b[2], raw_whites_b[1]]
    failures: list[str] = []
    successful: list[tuple[int, Block]] = []
    for shift in range(3):
        whites_b = reversed_b[shift:] + reversed_b[:shift]
        shared = dict(zip(whites_b, whites_a))
        next_label = max(inner.rotation) + 1
        relabel = dict(shared)
        for vertex in sorted(outer.rotation):
            if vertex not in relabel:
                relabel[vertex] = next_label
                next_label += 1

        combined: dict[int, Iterable[int]] = {
            vertex: neighbors
            for vertex, neighbors in inner.rotation.items()
            if vertex not in whites_a
        }
        for vertex, neighbors in outer.rotation.items():
            if vertex not in whites_b:
                combined[relabel[vertex]] = tuple(relabel[value] for value in neighbors)

        for vertex_b, vertex_a in zip(whites_b, whites_a):
            previous_a, following_a = _neighbors_on_face(socket_a.boundary, vertex_a)
            previous_b, following_b = _neighbors_on_face(socket_b.boundary, vertex_b)
            combined[vertex_a] = (
                previous_a,
                following_a,
                relabel[previous_b],
                relabel[following_b],
            )

        candidate_rotation = normalize_rotation(combined)
        try:
            sockets = validate_block(candidate_rotation)
        except BlockError as exc:
            failures.append(str(exc))
            continue
        expected_order = inner.order + outer.order - 3
        if len(candidate_rotation) != expected_order:
            raise BlockError(
                f"composition order {len(candidate_rotation)} != {expected_order}"
            )
        successful.append((shift, Block(candidate_rotation, sockets)))
    if successful:
        return tuple(successful)
    raise BlockError("no orientation-preserving socket gluing succeeded: " + "; ".join(failures))


def compose_blocks(
    inner: Block,
    outer: Block,
    *,
    inner_socket: int = 1,
    outer_socket: int = 0,
) -> Block:
    """Glue one socket from each block using the historical first alignment.

    New code that needs a complete positive construction search should call
    :func:`compose_blocks_alignments` or :func:`compose_blocks_all_variants`.
    Keeping this method's first-success selection maintains existing replay
    hashes and public controls.
    """

    return compose_blocks_alignments(
        inner,
        outer,
        inner_socket=inner_socket,
        outer_socket=outer_socket,
    )[0][1]


def compose_blocks_variants(
    inner: Block,
    outer: Block,
    *,
    inner_socket: int = 1,
    outer_socket: int = 0,
) -> tuple[Block, ...]:
    """Compose all global-reflection classes of two marked blocks.

    ``compose_blocks`` retains the historical orientation-preserving result.
    This wrapper also reflects either input block, which covers a chiral outer
    block and the equivalent global reflection of the inner block.  Exact
    labelled duplicates are removed, but reflected maps are retained because
    their cyclic rotations are distinct certificates.
    """

    candidates: dict[tuple[tuple[int, tuple[int, ...]], ...], Block] = {}
    for first in (inner, mirror_block(inner)):
        for second in (outer, mirror_block(outer)):
            try:
                composed = compose_blocks(
                    first,
                    second,
                    inner_socket=inner_socket,
                    outer_socket=outer_socket,
                )
            except BlockError:
                continue
            candidates[tuple(composed.rotation.items())] = composed
    if not candidates:
        raise BlockError("no compatible composition in either reflection class")
    return tuple(candidates[key] for key in sorted(candidates))


def compose_blocks_all_variants(
    inner: Block,
    outer: Block,
) -> tuple[CompositionVariant, ...]:
    """Enumerate all successful reflection, socket, and shift choices.

    This is the exhaustive two-block positive-construction primitive used by
    target promotion.  It tries both orientations of both inputs, all four
    socket pairs, and all three cyclic white correspondences.  Exact labelled
    duplicate rotations are removed, retaining the lexicographically first
    replay trace.  No failed alignment is interpreted as nonexistence.
    """

    candidates: dict[
        tuple[tuple[int, tuple[int, ...]], ...], CompositionVariant
    ] = {}
    for inner_reflected in (False, True):
        first = mirror_block(inner) if inner_reflected else inner
        for outer_reflected in (False, True):
            second = mirror_block(outer) if outer_reflected else outer
            for inner_socket, outer_socket in product(range(2), repeat=2):
                try:
                    alignments = compose_blocks_alignments(
                        first,
                        second,
                        inner_socket=inner_socket,
                        outer_socket=outer_socket,
                    )
                except BlockError:
                    continue
                for shift, composed in alignments:
                    candidate = CompositionVariant(
                        block=composed,
                        inner_reflected=inner_reflected,
                        outer_reflected=outer_reflected,
                        inner_socket=inner_socket,
                        outer_socket=outer_socket,
                        shift=shift,
                    )
                    key = tuple(composed.rotation.items())
                    incumbent = candidates.get(key)
                    trace = (
                        int(inner_reflected),
                        int(outer_reflected),
                        inner_socket,
                        outer_socket,
                        shift,
                    )
                    if incumbent is None or trace < (
                        int(incumbent.inner_reflected),
                        int(incumbent.outer_reflected),
                        incumbent.inner_socket,
                        incumbent.outer_socket,
                        incumbent.shift,
                    ):
                        candidates[key] = candidate
    if not candidates:
        raise BlockError("no compatible composition across reflection/socket/shift variants")
    return tuple(candidates[key] for key in sorted(candidates))
