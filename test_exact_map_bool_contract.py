#!/usr/bin/env python3
"""Published-interface controls for the Boolean exact-map block encoding.

These tests deliberately avoid importing ``exact_map_bool_sat`` because Z3 is
installed only in the isolated cloud worker.  They pin the geometric fact that
the Boolean socket constraints must encode: each degree-2 socket white is
incident with one hexagon and one pentagon, not two hexagons.
"""

from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

import blocks
import section8_profiles as profiles
from boolean_socket_canonical import (
    canonical_closed_cap_fans,
    canonical_two_socket_face_darts,
    canonical_two_socket_pairs,
    canonicalize_closed_cap_rotation,
    canonicalize_two_socket_rotation,
    closed_profile_from_rotation,
    dart_involution_from_rotation,
    marked_cap_facial_interface,
    marked_cap_interface,
    strict_block_profile_from_rotation,
)


ROOT = Path(__file__).resolve().parent


def _face_successor(degrees: list[int], alpha: list[int]) -> list[int]:
    """Reconstruct ``phi = sigma^-1 alpha`` from fixed local dart slots."""

    sigma_inverse = [-1] * len(alpha)
    start = 0
    for degree in degrees:
        for offset in range(degree):
            sigma_inverse[start + offset] = start + (offset - 1) % degree
        start += degree
    return [sigma_inverse[mate] for mate in alpha]


def _orbit_length(permutation: list[int], start: int) -> int:
    """Return the exact cycle length at ``start`` in a finite permutation."""

    seen: set[int] = set()
    dart = start
    while dart not in seen:
        seen.add(dart)
        dart = permutation[dart]
    if dart != start:
        raise AssertionError("permutation orbit did not return to its start")
    return len(seen)


def _face_lengths(permutation: list[int]) -> list[int]:
    """Return the exact face period at each dart of a permutation."""

    result = [0] * len(permutation)
    for start in range(len(permutation)):
        if result[start]:
            continue
        orbit: list[int] = []
        dart = start
        while dart not in orbit:
            orbit.append(dart)
            dart = permutation[dart]
        if dart != start:
            raise AssertionError("face successor did not return to its start")
        for member in orbit:
            result[member] = len(orbit)
    return result


class BooleanSocketContractTests(unittest.TestCase):
    def test_target_profiles_have_noncolliding_socket_pair_indices(self) -> None:
        for order, r in ((25, 11), (27, 12), (28, 12), (29, 12), (31, 12), (34, 13)):
            degrees = (
                [2] * 6
                + [3] * (r - 4)
                + [4] * (order - 2 * r + 2)
                + [5] * (r - 4)
            )
            with self.subTest(order=order, r=r):
                pairs = canonical_two_socket_pairs(degrees)
                socket_cycles, pentagon_darts = canonical_two_socket_face_darts(
                    degrees
                )
                darts = {dart for pair in pairs for dart in pair}
                self.assertEqual(len(pairs), 12)
                self.assertEqual(len(darts), 24)
                self.assertTrue(all(0 <= dart < sum(degrees) for dart in darts))
                self.assertEqual(len(socket_cycles), 2)
                self.assertTrue(all(len(cycle) == 6 for cycle in socket_cycles))
                self.assertEqual(len(pentagon_darts), 12)
                self.assertEqual(
                    darts,
                    {dart for cycle in socket_cycles for dart in cycle}
                    | set(pentagon_darts),
                )

    def test_published_blocks_admit_complete_two_socket_canonicalization(self) -> None:
        for path in sorted((ROOT / "results" / "blocks").glob("*.json")):
            data = json.loads(path.read_text())
            original = blocks.rotation_from_certificate(
                {"format": blocks.APG_FORMAT, "vertices": data["vertices"]}
            )
            for label, rotation in (
                ("original", original),
                ("mirror", blocks.mirror_rotation(original)),
            ):
                with self.subTest(block=path.name, orientation=label):
                    relabelled = canonicalize_two_socket_rotation(rotation)
                    degrees = [len(relabelled[vertex]) for vertex in range(len(relabelled))]
                    self.assertEqual(len(blocks.validate_block(relabelled)), 2)
                    alpha = dart_involution_from_rotation(relabelled)
                    profile_degrees, profile_faces, profile_alpha = (
                        strict_block_profile_from_rotation(relabelled)
                    )
                    self.assertEqual(profile_degrees, degrees)
                    self.assertEqual(profile_alpha, alpha)
                    self.assertEqual(
                        Counter(profile_faces),
                        Counter(len(face) for face in blocks.trace_faces(relabelled).faces),
                    )
                    phi = _face_successor(degrees, alpha)
                    pairs = canonical_two_socket_pairs(degrees)
                    socket_cycles, pentagon_darts = canonical_two_socket_face_darts(
                        degrees
                    )
                    self.assertEqual(len(pairs), 12)
                    self.assertEqual(len({dart for pair in pairs for dart in pair}), 24)
                    self.assertEqual(len(socket_cycles), 2)
                    self.assertEqual(len(pentagon_darts), 12)
                    for dart, mate in pairs:
                        self.assertEqual(alpha[dart], mate)
                        self.assertEqual(alpha[mate], dart)
                    starts: list[int] = []
                    next_dart = 0
                    for degree in degrees:
                        starts.append(next_dart)
                        next_dart += degree
                    blacks = [vertex for vertex, degree in enumerate(degrees) if degree == 5]
                    for socket_index in range(2):
                        w0, w1, w2 = (3 * socket_index, 3 * socket_index + 1, 3 * socket_index + 2)
                        b0, b1, b2 = blacks[
                            3 * socket_index : 3 * socket_index + 3
                        ]
                        expected_cycle = (
                            starts[w0],
                            starts[b0] + 4,
                            starts[w1] + 1,
                            starts[b1] + 4,
                            starts[w2] + 1,
                            starts[b2] + 4,
                        )
                        self.assertEqual(
                            tuple(phi[dart] for dart in expected_cycle),
                            expected_cycle[1:] + expected_cycle[:1],
                        )
                        self.assertIn(expected_cycle, socket_cycles)
                        self.assertTrue(
                            all(_orbit_length(phi, dart) == 6 for dart in expected_cycle)
                        )
                    self.assertEqual(
                        set(pentagon_darts),
                        {
                            alpha[dart]
                            for cycle in socket_cycles
                            for dart in cycle
                        },
                    )
                    self.assertTrue(
                        all(_orbit_length(phi, dart) == 5 for dart in pentagon_darts)
                    )

    def test_published_A21_whites_have_one_hexagonal_incidence_each(self) -> None:
        data = json.loads((ROOT / "results" / "blocks" / "A21.json").read_text())
        rotation = blocks.rotation_from_certificate(
            {
                "format": blocks.APG_FORMAT,
                "vertices": data["vertices"],
            }
        )
        sockets = blocks.validate_block(rotation)
        trace = blocks.trace_faces(rotation)
        degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
        hexagons = [face for face in trace.faces if len(face) == 6]
        self.assertEqual(len(hexagons), 2)

        whites = {white for socket in sockets for white in socket.whites}
        self.assertEqual(len(whites), 6)
        for white in whites:
            incident_sizes = [len(face) for face in trace.faces if white in face]
            self.assertEqual(sorted(incident_sizes), [5, 6])
            self.assertEqual(sum(white in face for face in hexagons), 1)

        for hexagon in hexagons:
            kinds = [degrees[vertex] for vertex in hexagon]
            self.assertTrue(
                all(
                    {kinds[index], kinds[(index + 1) % len(kinds)]} == {2, 5}
                    for index in range(len(kinds))
                )
            )

        degree_pairs = Counter(
            tuple(sorted((degrees[vertex], degrees[neighbor])))
            for vertex, neighbors in rotation.items()
            for neighbor in neighbors
            if vertex < neighbor
        )
        # The forced twelve 2--5 edges consume twelve degree-5 stubs.  The
        # Boolean encoding must solve its residual 3/4/5 equations from the
        # remaining (18, 12, 18) stubs, rather than the original degree-5
        # total of 30.
        self.assertEqual(
            degree_pairs,
            Counter({(2, 5): 12, (3, 4): 6, (3, 5): 12, (4, 5): 6}),
        )

        # ``--require-t0`` constrains this same local datum in the Boolean
        # model.  A degree-5 vertex has one dart per incident face, and all
        # facial walks are simple, so exactly two pentagonal incidences is the
        # portable t=0 branch independently measured here from A21.
        for vertex, degree in degrees.items():
            if degree == 5:
                self.assertEqual(
                    sum(vertex in face for face in trace.faces if len(face) == 5),
                    2,
                )

        face_pairs = Counter(
            tuple(
                sorted(
                    (
                        len(trace.faces[trace.face_of[(vertex, neighbor)]]),
                        len(trace.faces[trace.face_of[(neighbor, vertex)]]),
                    )
                )
            )
            for vertex, neighbors in rotation.items()
            for neighbor in neighbors
            if vertex < neighbor
        )
        self.assertEqual(
            face_pairs,
            Counter({(3, 4): 6, (3, 5): 12, (4, 5): 6, (5, 6): 12}),
        )
        self.assertTrue(profiles.t0_profile_is_feasible(21, 10))

    def test_closed_cap_normal_form_covers_published_strict_blocks(self) -> None:
        # Every strict block becomes a closed APG with two disjoint 4--(3,3)
        # cap fans under a chosen closure.  Relabelling those marked caps is
        # all the direct closed-cap Boolean lane assumes; reopening remains an
        # independent strict-block check in the postprocessor.
        for path in sorted((ROOT / "results" / "blocks").glob("*.json")):
            data = json.loads(path.read_text())
            original = blocks.rotation_from_certificate(
                {"format": blocks.APG_FORMAT, "vertices": data["vertices"]}
            )
            for label, rotation in (
                ("original", original),
                ("mirror", blocks.mirror_rotation(original)),
            ):
                with self.subTest(block=path.name, orientation=label):
                    sockets = blocks.validate_block(rotation)
                    for hub_indices, closed in blocks.close_block_variants(
                        blocks.Block(rotation, sockets)
                    ):
                        with self.subTest(hub_indices=hub_indices):
                            fans = tuple(
                                blocks.ClosureFan(
                                    hub=sorted(socket.whites)[hub_index],
                                    leaves=tuple(
                                        white
                                        for index, white in enumerate(sorted(socket.whites))
                                        if index != hub_index
                                    ),
                                )
                                for socket, hub_index in zip(sockets, hub_indices)
                            )
                            relabelled = canonicalize_closed_cap_rotation(closed, fans)
                            degrees, faces, alpha = closed_profile_from_rotation(relabelled)
                            cap_fans = canonical_closed_cap_fans(degrees)
                            self.assertEqual(degrees, sorted(degrees))
                            self.assertEqual(Counter(degrees), Counter(faces))
                            self.assertEqual(len(cap_fans), 2)
                            for hub, leaves in cap_fans:
                                self.assertEqual(degrees[hub], 4)
                                self.assertTrue(all(degrees[leaf] == 3 for leaf in leaves))
                                self.assertTrue(all(leaf in relabelled[hub] for leaf in leaves))
                            interface = marked_cap_interface(
                                relabelled,
                                tuple(
                                    blocks.ClosureFan(hub, leaves)
                                    for hub, leaves in cap_fans
                                ),
                            )
                            self.assertEqual(len(interface), 2)
                            facial_interface = marked_cap_facial_interface(
                                relabelled,
                                tuple(
                                    blocks.ClosureFan(hub, leaves)
                                    for hub, leaves in cap_fans
                                ),
                            )
                            self.assertEqual(len(facial_interface), 2)
                            self.assertTrue(
                                all(
                                    len(item["quadrilateral"]) == 4
                                    for item in facial_interface
                                )
                            )
                            # This is the same dart-level convention used by
                            # BooleanMapEncoding: phi = sigma^-1 alpha. It
                            # independently checks the two solver clauses,
                            # rather than only the vertex-face checker above.
                            phi = _face_successor(degrees, alpha)
                            face_lengths = _face_lengths(phi)
                            starts: list[int] = []
                            next_dart = 0
                            for degree in degrees:
                                starts.append(next_dart)
                                next_dart += degree
                            for hub, leaves in cap_fans:
                                quadrilateral_sides: list[int] = []
                                for leaf in leaves:
                                    hub_dart = starts[hub] + relabelled[hub].index(leaf)
                                    leaf_dart = alpha[hub_dart]
                                    self.assertEqual(
                                        {face_lengths[hub_dart], face_lengths[leaf_dart]},
                                        {3, 4},
                                    )
                                    quadrilateral_sides.append(
                                        hub_dart
                                        if face_lengths[hub_dart] == 4
                                        else leaf_dart
                                    )
                                current = quadrilateral_sides[0]
                                self.assertTrue(
                                    any(
                                        (current := phi[current])
                                        == quadrilateral_sides[1]
                                        for _ in range(3)
                                    )
                                )
                            self.assertEqual(
                                len(
                                    {
                                        value
                                        for item in interface
                                        for value in (
                                            item["outer_left"],
                                            item["centre"],
                                            item["outer_right"],
                                        )
                                    }
                                ),
                                6,
                            )
                            starts: list[int] = []
                            next_dart = 0
                            for degree in degrees:
                                starts.append(next_dart)
                                next_dart += degree
                            first_hub, first_leaves = cap_fans[0]
                            self.assertEqual(alpha[starts[first_leaves[0]]], starts[first_hub])

    def test_target_closed_cap_profiles_have_canonical_marked_fans(self) -> None:
        for order, r in ((21, 10), (28, 12), (29, 12), (31, 12)):
            degrees = [3] * r + [4] * (order - 2 * r + 4) + [5] * (r - 4)
            with self.subTest(order=order, r=r):
                fans = canonical_closed_cap_fans(degrees)
                self.assertEqual(fans[0], (r, (0, 1)))
                self.assertEqual(fans[1], (r + 1, (2, 3)))


if __name__ == "__main__":
    unittest.main()
