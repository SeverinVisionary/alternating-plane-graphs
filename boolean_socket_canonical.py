#!/usr/bin/env python3
"""Representation-only socket normal form for the Boolean block encoder.

The strict Section-8 interface has exactly two alternating hexagonal sockets.
Their six degree-two whites and six boundary degree-five vertices can be
renamed, and every local cyclic dart list can be rotated, without changing the
underlying rotation system.  This module freezes the twelve matching pairs in
that normal form.  It has no Z3 dependency so its index arithmetic is directly
testable on the shared development host.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import blocks


def _dart_starts(degrees: Sequence[int]) -> tuple[int, ...]:
    starts: list[int] = []
    next_dart = 0
    for degree in degrees:
        if not isinstance(degree, int) or isinstance(degree, bool) or degree < 1:
            raise ValueError("degrees must be positive integers")
        starts.append(next_dart)
        next_dart += degree
    return tuple(starts)


def canonical_two_socket_pairs(degrees: Sequence[int]) -> tuple[tuple[int, int], ...]:
    """Return the twelve forced dart matches for the socket normal form.

    The input is the degree-sorted strict-block profile used by
    :func:`exact_map_sat.profile_block`: its six degree-two vertices are first,
    and degree-five vertices are later in the list.  The first three whites and
    first three degree-five vertices are the first socket; the next triples are
    the second.  For each socket, the returned pairs force the face walk

    ``w0, b0, w1, b1, w2, b2``.

    A caller must assert each returned unordered match.  The induced
    ``phi = sigma^-1 alpha`` cycles are then the two socket hexagons; no face
    label or mathematical restriction is introduced.
    """

    starts = _dart_starts(degrees)
    whites = [vertex for vertex, degree in enumerate(degrees) if degree == 2]
    blacks = [vertex for vertex, degree in enumerate(degrees) if degree == 5]
    if len(whites) != 6:
        raise ValueError(
            "strict two-socket normal form requires exactly six degree-two vertices"
        )
    if len(blacks) < 6:
        raise ValueError(
            "strict two-socket normal form requires at least six degree-five vertices"
        )

    pairs: list[tuple[int, int]] = []
    for socket_index in range(2):
        w0, w1, w2 = whites[3 * socket_index : 3 * socket_index + 3]
        b0, b1, b2 = blacks[3 * socket_index : 3 * socket_index + 3]
        w0_dart, w1_dart, w2_dart = starts[w0], starts[w1], starts[w2]
        b0_dart, b1_dart, b2_dart = starts[b0], starts[b1], starts[b2]
        pairs.extend(
            (
                (w0_dart, b0_dart),
                (b0_dart + 4, w1_dart),
                (w1_dart + 1, b1_dart),
                (b1_dart + 4, w2_dart),
                (w2_dart + 1, b2_dart),
                (b2_dart + 4, w0_dart + 1),
            )
        )
    return tuple(pairs)


def canonical_two_socket_face_darts(
    degrees: Sequence[int],
) -> tuple[tuple[tuple[int, ...], ...], tuple[int, ...]]:
    """Return the two forced hexagon dart cycles and their pentagon opposites.

    The twelve pairs from :func:`canonical_two_socket_pairs` determine the
    two ``phi = sigma^-1 alpha`` cycles without any solver decision.  The
    remaining endpoint of each of the twelve pair variables is the opposite
    dart of a socket edge and therefore lies on a pentagon in every strict
    block.  Returning those facts separately lets the Boolean encoder state
    the implied face labels immediately rather than rediscovering them through
    its generic period constraints.
    """

    starts = _dart_starts(degrees)
    dart_count = sum(degrees)
    sigma_inverse = [0] * dart_count
    for vertex, degree in enumerate(degrees):
        for offset in range(degree):
            sigma_inverse[starts[vertex] + offset] = starts[vertex] + (
                offset - 1
            ) % degree
    mates: dict[int, int] = {}
    for dart, mate in canonical_two_socket_pairs(degrees):
        if dart in mates or mate in mates:
            raise ValueError("canonical socket pairs must be disjoint")
        mates[dart] = mate
        mates[mate] = dart

    # On a socket dart, successor lands on another canonical endpoint.  On
    # the opposite pentagon dart it immediately leaves this partial matching.
    successor = {
        dart: sigma_inverse[mate]
        for dart, mate in mates.items()
    }
    cycles: list[tuple[int, ...]] = []
    covered: set[int] = set()
    for start in sorted(mates):
        if start in covered:
            continue
        orbit: list[int] = []
        positions: dict[int, int] = {}
        dart = start
        while dart in successor and dart not in positions:
            positions[dart] = len(orbit)
            orbit.append(dart)
            dart = successor[dart]
        if dart in positions:
            cycle = tuple(orbit[positions[dart] :])
            if len(cycle) == 6:
                cycles.append(cycle)
                covered.update(cycle)
    cycles.sort(key=lambda cycle: min(cycle))
    if len(cycles) != 2 or any(len(cycle) != 6 for cycle in cycles):
        raise ValueError("canonical pairs did not determine two socket hexagons")
    socket_darts = {dart for cycle in cycles for dart in cycle}
    pentagon_darts = {mates[dart] for dart in socket_darts}
    if len(socket_darts) != 12 or len(pentagon_darts) != 12:
        raise ValueError("canonical socket darts are not twelve distinct edge sides")
    if socket_darts.intersection(pentagon_darts):
        raise ValueError("a socket dart cannot be opposite another socket dart")
    return tuple(cycles), tuple(sorted(pentagon_darts))


def canonical_closed_cap_fans(
    degrees: Sequence[int],
) -> tuple[tuple[int, tuple[int, int]], tuple[int, tuple[int, int]]]:
    """Return two labelled 4--(3,3) cap fans in a closed-map normal form.

    A closed cap that can open to a Section 8 socket has a degree-4 hub and
    two degree-3 leaves.  Given an APG with two disjoint such caps, relabel
    within degree classes so their four leaves are the first four degree-3
    vertices and their hubs are the first two degree-4 vertices.  The returned
    pairs are therefore a representation convention for *marked* caps, not a
    claim that every closed APG contains them.
    """

    if any(
        not isinstance(degree, int)
        or isinstance(degree, bool)
        or degree not in {3, 4, 5}
        for degree in degrees
    ):
        raise ValueError("closed cap normal form requires degrees in {3,4,5}")
    if tuple(degrees) != tuple(sorted(degrees)):
        raise ValueError("closed cap normal form requires degree-sorted vertices")
    degree3 = [vertex for vertex, degree in enumerate(degrees) if degree == 3]
    degree4 = [vertex for vertex, degree in enumerate(degrees) if degree == 4]
    if len(degree3) < 4 or len(degree4) < 2:
        raise ValueError("two cap fans require four degree-3 leaves and two degree-4 hubs")
    return (
        (degree4[0], (degree3[0], degree3[1])),
        (degree4[1], (degree3[2], degree3[3])),
    )


def marked_cap_interface(
    rotation: blocks.Rotation,
    fans: Iterable[blocks.ClosureFan],
) -> tuple[dict[str, int], ...]:
    """Check the forced degree-five neighbourhood of marked Section-8 caps.

    Capping a strict socket at a chosen white ``h`` makes a degree-four hub
    joined to two degree-three leaves ``x,y``.  The two triangles created by
    the chords and the remaining quadrilateral force precisely this local
    incidence pattern: each of ``h,x,y`` has two degree-five neighbours; each
    pair has exactly one common degree-five neighbour; and no degree-five
    vertex is adjacent to all three.  This is a necessary condition, stated
    only in terms of the closed graph, for a marked fan to reopen to a strict
    socket.  It deliberately does *not* assert facial adjacency: that remains
    the independent reopening/postprocessing boundary.

    The returned names are useful evidence for pure-Python regression tests;
    callers should use only the fact that this function succeeds.
    """

    normalized = blocks.normalize_rotation(rotation)
    selected = tuple(fans)
    if len(selected) != 2:
        raise ValueError("marked cap interface requires exactly two fans")
    degrees = {vertex: len(neighbors) for vertex, neighbors in normalized.items()}
    if len({vertex for fan in selected for vertex in (fan.hub, *fan.leaves)}) != 6:
        raise ValueError("marked cap interface requires six distinct fan vertices")
    degree5 = {vertex for vertex, degree in degrees.items() if degree == 5}
    evidence: list[dict[str, int]] = []
    for fan in selected:
        hub, (left, right) = fan.hub, fan.leaves
        if any(vertex not in normalized for vertex in (hub, left, right)):
            raise ValueError("marked cap interface names a missing vertex")
        if degrees[hub] != 4 or degrees[left] != 3 or degrees[right] != 3:
            raise ValueError("marked cap interface has the wrong hub/leaf degrees")
        if left not in normalized[hub] or right not in normalized[hub]:
            raise ValueError("marked cap interface is missing a hub--leaf edge")
        neighbours = {
            vertex: set(normalized[vertex]).intersection(degree5)
            for vertex in (hub, left, right)
        }
        if any(len(value) != 2 for value in neighbours.values()):
            raise ValueError("marked cap vertex does not have exactly two degree-five neighbours")
        outer_left = neighbours[hub].intersection(neighbours[left])
        centre = neighbours[left].intersection(neighbours[right])
        outer_right = neighbours[hub].intersection(neighbours[right])
        if any(len(value) != 1 for value in (outer_left, centre, outer_right)):
            raise ValueError("marked cap pairs do not have one common degree-five neighbour")
        if neighbours[hub].intersection(neighbours[left], neighbours[right]):
            raise ValueError("marked cap has a degree-five vertex adjacent to hub and both leaves")
        evidence.append(
            {
                "hub": hub,
                "left_leaf": left,
                "right_leaf": right,
                "outer_left": next(iter(outer_left)),
                "centre": next(iter(centre)),
                "outer_right": next(iter(outer_right)),
            }
        )
    return tuple(evidence)


def marked_cap_facial_interface(
    rotation: blocks.Rotation,
    fans: Iterable[blocks.ClosureFan],
) -> tuple[dict[str, tuple[int, ...]], ...]:
    """Check the triangular/quadrilateral face interface of marked caps.

    The two chords inserted when a strict socket is capped each have one
    triangular side and one quadrilateral side. The quadrilateral is shared by
    the two chords. This exact local consequence is kept in pure Python so
    every published block closure regression-tests the solver reduction.
    """

    normalized = blocks.normalize_rotation(rotation)
    selected = tuple(fans)
    graph_evidence = marked_cap_interface(normalized, selected)
    trace = blocks.trace_faces(normalized)
    edge_faces: dict[frozenset[int], list[tuple[int, ...]]] = {}
    for face in trace.faces:
        for index, vertex in enumerate(face):
            edge_faces.setdefault(
                frozenset((vertex, face[(index + 1) % len(face)])), []
            ).append(face)

    evidence: list[dict[str, tuple[int, ...]]] = []
    for fan, graph in zip(selected, graph_evidence):
        cap_faces: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
        for edge in fan.edges:
            adjacent = edge_faces.get(frozenset(edge), [])
            if len(adjacent) != 2:
                raise ValueError("marked cap edge does not have two incident faces")
            triangles = [face for face in adjacent if len(face) == 3]
            quadrilaterals = [face for face in adjacent if len(face) == 4]
            if len(triangles) != 1 or len(quadrilaterals) != 1:
                raise ValueError("marked cap edge must border one triangle and one quadrilateral")
            cap_faces.append((triangles[0], quadrilaterals[0]))
        first_triangle, first_quad = cap_faces[0]
        second_triangle, second_quad = cap_faces[1]
        if set(first_quad) != set(second_quad):
            raise ValueError("the two marked cap edges must share one quadrilateral")
        hub, left, right = fan.hub, fan.leaves[0], fan.leaves[1]
        centre = graph["centre"]
        if set(first_quad) != {hub, left, centre, right}:
            raise ValueError("marked cap quadrilateral has the wrong four vertices")
        expected_triangles = {
            frozenset((hub, left, graph["outer_left"])),
            frozenset((hub, right, graph["outer_right"])),
        }
        if {frozenset(first_triangle), frozenset(second_triangle)} != expected_triangles:
            raise ValueError("marked cap triangles have the wrong degree-five corners")
        evidence.append(
            {
                "left_triangle": first_triangle,
                "quadrilateral": first_quad,
                "right_triangle": second_triangle,
            }
        )
    return tuple(evidence)


def _rotate_to(values: tuple[int, ...], first: int) -> tuple[int, ...]:
    index = values.index(first)
    return values[index:] + values[:index]


def canonicalize_two_socket_rotation(rotation: blocks.Rotation) -> blocks.Rotation:
    """Return a strict block with the complete socket normal form applied.

    This is used only for a fixed-known-block encoder control.  It changes
    vertex names within degree classes and the arbitrary start of each cyclic
    neighbour order; both preserve the same combinatorial map.  The returned
    lists intentionally retain their selected starts, because dart indices are
    the normal form's subject.
    """

    rotation = blocks.normalize_rotation(rotation)
    sockets = blocks.validate_block(rotation)
    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    socket_cycles: list[tuple[int, ...]] = []
    for socket in sockets:
        boundary = socket.boundary
        white_index = next(
            index for index, vertex in enumerate(boundary) if degrees[vertex] == 2
        )
        cycle = boundary[white_index:] + boundary[:white_index]
        if [degrees[vertex] for vertex in cycle] != [2, 5, 2, 5, 2, 5]:
            raise ValueError("strict socket did not retain its alternating face order")
        socket_cycles.append(cycle)

    port_whites = [cycle[index] for cycle in socket_cycles for index in (0, 2, 4)]
    port_blacks = [cycle[index] for cycle in socket_cycles for index in (1, 3, 5)]
    if len(set(port_whites)) != 6 or len(set(port_blacks)) != 6:
        raise ValueError("two strict sockets must have six distinct port vertices per side")
    port_black_set = set(port_blacks)
    old_order = [
        *port_whites,
        *sorted(vertex for vertex, degree in degrees.items() if degree == 3),
        *sorted(vertex for vertex, degree in degrees.items() if degree == 4),
        *port_blacks,
        *sorted(
            vertex
            for vertex, degree in degrees.items()
            if degree == 5 and vertex not in port_black_set
        ),
    ]
    if len(old_order) != len(rotation) or len(set(old_order)) != len(rotation):
        raise ValueError("relabel order did not partition the block vertices")
    old_to_new = {vertex: label for label, vertex in enumerate(old_order)}

    desired_first: dict[int, int] = {}
    for w0, b0, w1, b1, w2, b2 in socket_cycles:
        desired_first.update(
            {
                w0: b0,
                w1: b0,
                w2: b1,
                b0: w0,
                b1: w1,
                b2: w2,
            }
        )

    relabelled: blocks.Rotation = {}
    for old_vertex in old_order:
        neighbors = rotation[old_vertex]
        first = desired_first.get(old_vertex, min(neighbors))
        relabelled[old_to_new[old_vertex]] = tuple(
            old_to_new[neighbor] for neighbor in _rotate_to(neighbors, first)
        )
    blocks.validate_block(relabelled)
    return relabelled


def canonicalize_closed_cap_rotation(
    rotation: blocks.Rotation,
    fans: Iterable[blocks.ClosureFan],
) -> blocks.Rotation:
    """Relabel a closed APG with two marked cap fans into the cap normal form.

    The two fans are input data, not inferred from the closed APG.  Their
    order and each leaf order select the four canonical degree-3 slots.  The
    first leaf--hub edge also starts both local dart rows, making the existing
    closed-map ``alpha[0]`` symmetry convention compatible with the marked
    cap normal form.  Other local starts are arbitrary and are chosen
    deterministically.  No reflection or re-embedding occurs.
    """

    rotation = blocks.normalize_rotation(rotation)
    selected = tuple(fans)
    if len(selected) != 2:
        raise ValueError("closed cap normal form requires exactly two fans")
    leaves = [leaf for fan in selected for leaf in fan.leaves]
    hubs = [fan.hub for fan in selected]
    if len(set((*leaves, *hubs))) != 6:
        raise ValueError("closed cap normal form requires disjoint fan vertices")
    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    if set(degrees.values()) - {3, 4, 5}:
        raise ValueError("closed cap normal form requires degrees in {3,4,5}")
    for fan in selected:
        if fan.hub not in rotation or any(leaf not in rotation for leaf in fan.leaves):
            raise ValueError("cap fan names a missing vertex")
        if degrees[fan.hub] != 4 or any(degrees[leaf] != 3 for leaf in fan.leaves):
            raise ValueError("cap fan must have a degree-4 hub and degree-3 leaves")
        if any(leaf not in rotation[fan.hub] for leaf in fan.leaves):
            raise ValueError("cap fan edge is missing")

    leaf_set = set(leaves)
    hub_set = set(hubs)
    old_order = [
        *leaves,
        *sorted(
            vertex
            for vertex, degree in degrees.items()
            if degree == 3 and vertex not in leaf_set
        ),
        *hubs,
        *sorted(
            vertex
            for vertex, degree in degrees.items()
            if degree == 4 and vertex not in hub_set
        ),
        *sorted(vertex for vertex, degree in degrees.items() if degree == 5),
    ]
    if len(old_order) != len(rotation) or len(set(old_order)) != len(rotation):
        raise ValueError("closed cap relabel order did not partition the vertices")
    old_to_new = {vertex: label for label, vertex in enumerate(old_order)}
    desired_first = {leaves[0]: hubs[0], hubs[0]: leaves[0]}
    relabelled: blocks.Rotation = {}
    for old_vertex in old_order:
        first = desired_first.get(old_vertex, min(rotation[old_vertex]))
        relabelled[old_to_new[old_vertex]] = tuple(
            old_to_new[neighbor]
            for neighbor in _rotate_to(rotation[old_vertex], first)
        )
    return relabelled


def dart_involution_from_rotation(rotation: blocks.Rotation) -> list[int]:
    """Return the fixed-slot dart involution of a contiguous labelled map."""

    if sorted(rotation) != list(range(len(rotation))):
        raise ValueError("rotation labels must be exactly 0 through n-1")
    starts: list[int] = []
    next_dart = 0
    dart_for: dict[tuple[int, int], int] = {}
    for vertex in range(len(rotation)):
        starts.append(next_dart)
        for offset, neighbor in enumerate(rotation[vertex]):
            dart_for[(vertex, neighbor)] = next_dart + offset
        next_dart += len(rotation[vertex])
    alpha = [-1] * next_dart
    for vertex in range(len(rotation)):
        for offset, neighbor in enumerate(rotation[vertex]):
            alpha[starts[vertex] + offset] = dart_for[(neighbor, vertex)]
    if any(mate < 0 for mate in alpha):
        raise ValueError("rotation does not determine a complete dart involution")
    return alpha


def strict_block_profile_from_rotation(
    rotation: blocks.Rotation,
) -> tuple[list[int], list[int], list[int]]:
    """Return the exact fixed-slot Boolean profile of a strict block rotation.

    This pure helper is intentionally shared by the canonical known-block
    control and its local regression test.  It derives face multiplicities
    from the rotation rather than trusting any certificate annotation.
    """

    blocks.validate_block(rotation)
    if sorted(rotation) != list(range(len(rotation))):
        raise ValueError("rotation labels must be exactly 0 through n-1")
    degrees = [len(rotation[vertex]) for vertex in range(len(rotation))]
    faces = [len(face) for face in blocks.trace_faces(rotation).faces]
    return degrees, faces, dart_involution_from_rotation(rotation)


def closed_profile_from_rotation(
    rotation: blocks.Rotation,
) -> tuple[list[int], list[int], list[int]]:
    """Return the Boolean profile of a contiguous labelled closed APG map."""

    if sorted(rotation) != list(range(len(rotation))):
        raise ValueError("rotation labels must be exactly 0 through n-1")
    degrees = [len(rotation[vertex]) for vertex in range(len(rotation))]
    if set(degrees) - {3, 4, 5}:
        raise ValueError("closed cap control has a forbidden vertex degree")
    faces = [len(face) for face in blocks.trace_faces(rotation).faces]
    if set(faces) - {3, 4, 5}:
        raise ValueError("closed cap control has a forbidden face size")
    return degrees, faces, dart_involution_from_rotation(rotation)
