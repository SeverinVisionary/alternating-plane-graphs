#!/usr/bin/env python3
"""Boolean finite-domain search for (3,4,5)-alternating plane maps.

The first exact-map pilot represented a dart involution with nested Z3 arrays.
That is faithful but produces tens of millions of array terms before the
solver reaches the useful combinatorics.  This encoder keeps the same positive
search contract while representing the involution as a Boolean perfect
matching.  Face lengths are attached to darts and exact face periods are
enforced through the induced permutation ``phi = sigma^{-1} alpha``.

The model is intentionally an over-approximation with respect to connectivity:
the independent postprocessor remains the only admissible boundary for a
positive certificate.  Solver ``unknown`` and bounded ``unsat`` are search
evidence, never nonexistence claims.
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

import blocks
from boolean_socket_canonical import (
    canonical_closed_cap_fans,
    canonical_two_socket_face_darts,
    canonical_two_socket_pairs,
    canonicalize_closed_cap_rotation,
    canonicalize_two_socket_rotation,
    closed_profile_from_rotation,
    strict_block_profile_from_rotation,
)
from exact_map_sat import (
    _solver_statistics,
    cycles_from_degrees,
    dump_rotation,
    profile_block,
    profile_closed,
)
from section8_profiles import strict_portable_t0_profile_is_feasible


def profile_from_rows(rows: object) -> tuple[list[int], list[int], list[int]]:
    """Return ``(degrees, face_lengths, alpha)`` from fixed rotation rows.

    The solver then pins every matching variable to this independently parsed
    rotation, so a satisfiable result tests the Boolean encoding rather than
    searching for another map.  The row starts are intentionally preserved:
    a canonical known-block control uses them as its fixed dart slots.
    """

    if not isinstance(rows, list) or not rows:
        raise ValueError("known certificate has no vertices")
    rows_by_label = {row["id"]: row for row in rows}
    labels = sorted(rows_by_label)
    if labels != list(range(min(labels), min(labels) + len(labels))):
        raise ValueError("known certificate labels are not a contiguous range")
    offset = labels[0]
    dense = {label: label - offset for label in labels}
    degrees = [len(rows_by_label[label]["clockwise"]) for label in labels]
    cycles, vertex_of, sigma_inverse = cycles_from_degrees(degrees)
    lookup: dict[tuple[int, int], int] = {}
    for vertex, cycle in enumerate(cycles):
        neighbors = rows_by_label[vertex + offset]["clockwise"]
        if not isinstance(neighbors, list) or len(neighbors) != len(cycle):
            raise ValueError("known certificate row does not match its degree")
        for dart, neighbor in zip(cycle, neighbors):
            if neighbor not in dense:
                raise ValueError("known certificate names a missing vertex")
            lookup[(vertex, dense[neighbor])] = dart
    alpha = [-1] * len(vertex_of)
    for dart, vertex in enumerate(vertex_of):
        target = rows_by_label[vertex + offset]["clockwise"][
            cycles[vertex].index(dart)
        ]
        alpha[dart] = lookup[(dense[target], vertex)]

    phi = [sigma_inverse[alpha[dart]] for dart in range(len(alpha))]
    seen: set[int] = set()
    face_lengths: list[int] = []
    for start in range(len(phi)):
        if start in seen:
            continue
        dart = start
        length = 0
        while dart not in seen:
            seen.add(dart)
            length += 1
            dart = phi[dart]
        if dart != start:
            raise ValueError("known certificate permutation is not a cycle partition")
        face_lengths.append(length)
    return degrees, face_lengths, alpha


def profile_from_certificate(path: Path) -> tuple[list[int], list[int], list[int]]:
    """Return ``(degrees, face_lengths, alpha)`` for a rotation certificate."""

    data = json.loads(path.read_text(encoding="utf-8"))
    return profile_from_rows(data.get("vertices") if isinstance(data, dict) else None)


class BooleanMapEncoding:
    """Build the Boolean matching and dart-face-period model."""

    def __init__(
        self,
        degrees: list[int],
        face_lengths: list[int],
        *,
        open_block: bool,
        canonical: bool = True,
        fixed_alpha: list[int] | None = None,
        require_t0: bool = False,
        cap_fans: tuple[tuple[int, tuple[int, int]], ...] = (),
    ) -> None:
        self.degrees = degrees
        self.face_lengths = face_lengths
        self.open_block = open_block
        self.canonical = canonical
        self.require_t0 = require_t0
        self.cap_fans = cap_fans
        self.require_residual_h55_2regular = (
            open_block
            and canonical
            and require_t0
            and degrees.count(5) >= 8
        )
        self.require_residual_h55_c4 = (
            self.require_residual_h55_2regular and degrees.count(5) == 8
        )
        self.phi_powers: list[list[z3.ArithRef]] = []
        self.cycles, self.vertex_of, self.sigma_inverse = cycles_from_degrees(degrees)
        self.dart_count = len(self.vertex_of)
        self.vertex_count = len(degrees)
        self.allowed_lengths = tuple(sorted(set(face_lengths)))
        self.max_length = max(self.allowed_lengths)
        self.sigma = [0] * self.dart_count
        for cycle in self.cycles:
            for index, dart in enumerate(cycle):
                self.sigma[dart] = cycle[(index + 1) % len(cycle)]

        self.solver = z3.Solver()
        self.pairs: dict[tuple[int, int], z3.BoolRef] = {}
        for d in range(self.dart_count):
            for e in range(d + 1, self.dart_count):
                if self._allowed_pair(d, e):
                    self.pairs[(d, e)] = z3.Bool(f"m_{d}_{e}")

        self._build_matching_and_simplicity()
        self._build_cap_fan_constraints()
        self._build_degree_edge_counts()
        self.phi = [z3.Int(f"phi_{d}") for d in range(self.dart_count)]
        self._build_face_permutation()
        self.face_length = [z3.Int(f"flen_{d}") for d in range(self.dart_count)]
        self._build_face_periods()
        self._build_cap_facial_constraints()
        if open_block:
            self._build_socket_constraints()
        if require_t0 and (open_block or cap_fans):
            self._build_t0_vertex_pentagon_constraints()
        self._build_face_edge_counts()
        if canonical:
            self._build_canonical_constraints()
        if self.require_residual_h55_2regular:
            self._build_residual_h55_2regular_constraints()
        if fixed_alpha is not None:
            if len(fixed_alpha) != self.dart_count:
                raise ValueError("fixed matching has the wrong dart count")
            for dart, mate in enumerate(fixed_alpha):
                if dart < mate:
                    self.solver.add(self.pair(dart, mate))

    def _allowed_pair(self, d: int, e: int) -> bool:
        u, v = self.vertex_of[d], self.vertex_of[e]
        if u == v:
            return False
        du, dv = self.degrees[u], self.degrees[v]
        if du == dv:
            return False
        if self.open_block and (du == 2 or dv == 2) and {du, dv} != {2, 5}:
            return False
        return True

    def pair(self, d: int, e: int) -> z3.BoolRef:
        """Return the Boolean variable for the unordered dart pair."""

        if d == e:
            return z3.BoolVal(False)
        key = (d, e) if d < e else (e, d)
        return self.pairs.get(key, z3.BoolVal(False))

    def choices(self, d: int) -> list[z3.BoolRef]:
        """Return only real matching variables incident with dart ``d``."""

        return [variable for (left, right), variable in self.pairs.items() if d in (left, right)]

    def _build_matching_and_simplicity(self) -> None:
        darts_by_vertex: list[list[int]] = [[] for _ in range(self.vertex_count)]
        for dart, vertex in enumerate(self.vertex_of):
            darts_by_vertex[vertex].append(dart)

        # Every dart has exactly one allowed mate.  Because each pair variable
        # occurs in the equations for both endpoints, this is an involution.
        for d in range(self.dart_count):
            self.solver.add(z3.PbEq([(choice, 1) for choice in self.choices(d)], 1))

        # Target-vertex one-hot indicators make the no-parallel-edge gate
        # linear and avoid nested array selects.
        target: dict[tuple[int, int], z3.BoolRef] = {}
        for d in range(self.dart_count):
            for vertex, darts in enumerate(darts_by_vertex):
                indicator = z3.Bool(f"target_{d}_{vertex}")
                target[(d, vertex)] = indicator
                choices = [
                    self.pairs[(min(d, e), max(d, e))]
                    for e in darts
                    if (min(d, e), max(d, e)) in self.pairs
                ]
                self.solver.add(indicator == z3.Or(choices))
            self.solver.add(
                z3.PbEq(
                    [(target[(d, vertex)], 1) for vertex in range(self.vertex_count)],
                    1,
                )
            )

        for cycle in self.cycles:
            for index, d in enumerate(cycle):
                for e in cycle[index + 1 :]:
                    for vertex in range(self.vertex_count):
                        self.solver.add(
                            z3.Or(
                                z3.Not(target[(d, vertex)]),
                                z3.Not(target[(e, vertex)]),
                            )
                        )

    def _edge_exists(self, first_vertex: int, second_vertex: int) -> z3.BoolRef:
        """Return the simple-edge predicate between two labelled vertices."""

        if not (0 <= first_vertex < self.vertex_count and 0 <= second_vertex < self.vertex_count):
            return z3.BoolVal(False)
        terms = [
            self.pair(first_dart, second_dart)
            for first_dart in self.cycles[first_vertex]
            for second_dart in self.cycles[second_vertex]
        ]
        return z3.Or(terms) if terms else z3.BoolVal(False)

    def _build_cap_fan_constraints(self) -> None:
        """Mark two closed 4--(3,3) cap interfaces without assuming faces.

        The closed-cap Boolean lane is a positive over-approximation: these
        four marked edges may or may not open to two strict Section 8 sockets.
        Every positive candidate is reopened and checked independently by
        ``exact_map_postprocess.py`` before it can become a block witness.
        """

        if not self.cap_fans:
            return
        if self.open_block:
            raise ValueError("cap-fan constraints are valid only for a closed map")
        if len(self.cap_fans) != 2:
            raise ValueError("closed cap search requires exactly two cap fans")
        vertices: list[int] = []
        for hub, leaves in self.cap_fans:
            if (
                isinstance(hub, bool)
                or not isinstance(hub, int)
                or len(leaves) != 2
                or any(isinstance(leaf, bool) or not isinstance(leaf, int) for leaf in leaves)
            ):
                raise ValueError("cap fan labels must be one hub and two integer leaves")
            if not (0 <= hub < self.vertex_count) or any(
                not 0 <= leaf < self.vertex_count for leaf in leaves
            ):
                raise ValueError("cap fan labels lie outside the vertex set")
            if self.degrees[hub] != 4 or any(self.degrees[leaf] != 3 for leaf in leaves):
                raise ValueError("cap fan must have a degree-4 hub and degree-3 leaves")
            vertices.extend((hub, *leaves))
        if len(set(vertices)) != 6:
            raise ValueError("the two cap fans must have six distinct vertices")
        for hub, leaves in self.cap_fans:
            for leaf in leaves:
                self.solver.add(self._edge_exists(hub, leaf))

            # This is the full *graph* interface of a cap obtained by closing
            # a strict Section-8 socket.  It is a necessary condition for a
            # positive reopening, not a facial claim: the postprocessor still
            # independently removes the marked chords and validates the two
            # resulting socket hexagons.  Compared with four bare hub--leaf
            # edges, these exact degree-five overlaps substantially eliminate
            # closed maps that cannot possibly be the desired capped block.
            left, right = leaves
            degree5_neighbours: dict[int, list[z3.BoolRef]] = {}
            for vertex in (hub, left, right):
                degree5_neighbours[vertex] = [
                    self._edge_exists(vertex, candidate)
                    for candidate, degree in enumerate(self.degrees)
                    if degree == 5
                ]
                self.solver.add(
                    z3.PbEq(
                        [(edge, 1) for edge in degree5_neighbours[vertex]], 2
                    )
                )
            for first, second in ((hub, left), (left, right), (hub, right)):
                common = [
                    z3.And(first_edge, second_edge)
                    for first_edge, second_edge in zip(
                        degree5_neighbours[first], degree5_neighbours[second]
                    )
                ]
                self.solver.add(z3.PbEq([(edge, 1) for edge in common], 1))
            for hub_edge, left_edge, right_edge in zip(
                degree5_neighbours[hub],
                degree5_neighbours[left],
                degree5_neighbours[right],
            ):
                self.solver.add(z3.Not(z3.And(hub_edge, left_edge, right_edge)))

    def _cap_edge_dart_pairs(
        self, hub: int, leaf: int
    ) -> tuple[tuple[int, int, z3.BoolRef], ...]:
        """Return every dart-pair choice representing one marked cap edge."""

        return tuple(
            (hub_dart, leaf_dart, self.pair(hub_dart, leaf_dart))
            for hub_dart in self.cycles[hub]
            for leaf_dart in self.cycles[leaf]
            if (min(hub_dart, leaf_dart), max(hub_dart, leaf_dart)) in self.pairs
        )

    def _build_cap_facial_constraints(self) -> None:
        """Require the necessary triangular/quadrilateral cap face motif.

        Closing a strict Section-8 socket at one white adds two chords. Each
        chord has a triangle on one side and the same quadrilateral on the
        other; the latter contains both chords. This is only a necessary
        closed-map condition: the postprocessor still proves strict reopening.
        """

        if not self.cap_fans:
            return
        if len(self.phi_powers) < 4:
            raise ValueError("cap-facial constraints require face powers through 3")
        for hub, (left, right) in self.cap_fans:
            left_choices = self._cap_edge_dart_pairs(hub, left)
            right_choices = self._cap_edge_dart_pairs(hub, right)
            for first_dart, first_mate, first_edge in left_choices:
                self.solver.add(
                    z3.Implies(
                        first_edge,
                        z3.Or(
                            z3.And(
                                self.face_length[first_dart] == 3,
                                self.face_length[first_mate] == 4,
                            ),
                            z3.And(
                                self.face_length[first_dart] == 4,
                                self.face_length[first_mate] == 3,
                            ),
                        ),
                    )
                )
            for second_dart, second_mate, second_edge in right_choices:
                self.solver.add(
                    z3.Implies(
                        second_edge,
                        z3.Or(
                            z3.And(
                                self.face_length[second_dart] == 3,
                                self.face_length[second_mate] == 4,
                            ),
                            z3.And(
                                self.face_length[second_dart] == 4,
                                self.face_length[second_mate] == 3,
                            ),
                        ),
                    )
                )
            for first_dart, first_mate, first_edge in left_choices:
                for second_dart, second_mate, second_edge in right_choices:
                    shared_quad = z3.Or(
                        *(
                            z3.And(
                                self.face_length[first_side] == 4,
                                self.face_length[second_side] == 4,
                                z3.Or(
                                    *(
                                        self.phi_powers[step][first_side]
                                        == second_side
                                        for step in range(1, 4)
                                    )
                                ),
                            )
                            for first_side in (first_dart, first_mate)
                            for second_side in (second_dart, second_mate)
                        )
                    )
                    self.solver.add(
                        z3.Implies(z3.And(first_edge, second_edge), shared_quad)
                    )

    @staticmethod
    def _three_class_counts(incidence: dict[int, int]) -> dict[tuple[int, int], int]:
        """Solve the three unequal-class edge equations exactly."""

        a, b, c = sorted(incidence)
        numerators = (
            incidence[a] + incidence[b] - incidence[c],
            incidence[a] + incidence[c] - incidence[b],
            incidence[b] + incidence[c] - incidence[a],
        )
        if any(numerator % 2 for numerator in numerators):
            raise ValueError("nonintegral unequal-class edge count")
        values = {
            (a, b): numerators[0] // 2,
            (a, c): numerators[1] // 2,
            (b, c): numerators[2] // 2,
        }
        if any(value < 0 for value in values.values()):
            raise ValueError("negative unequal-class edge count")
        return values

    def _build_degree_edge_counts(self) -> None:
        """Add the forced edge counts between degree classes."""

        incidence = {
            degree: sum(
                degree_value
                for degree_value in self.degrees
                if degree_value == degree
            )
            for degree in sorted(set(self.degrees))
        }
        if self.open_block:
            forced = {(2, 5): incidence[2]}
            residual = {degree: value for degree, value in incidence.items() if degree != 2}
            # Every degree-2 stub is already consumed by a forced 2--5 edge.
            # The remaining three-class equations must use only the residual
            # degree-5 stubs, exactly as the face-side calculation below
            # subtracts the forced 5--6 incidence.
            residual[5] -= incidence[2]
            counts = {**forced, **self._three_class_counts(residual)}
        else:
            counts = self._three_class_counts(incidence)
        for (left_degree, right_degree), expected in counts.items():
            terms = [
                variable
                for (d, e), variable in self.pairs.items()
                if {self.degrees[self.vertex_of[d]], self.degrees[self.vertex_of[e]]}
                == {left_degree, right_degree}
            ]
            self.solver.add(z3.PbEq([(term, 1) for term in terms], expected))

    def successor_choice(self, d: int, target_dart: int) -> z3.BoolRef:
        """Boolean condition that ``phi(d) == target_dart``."""

        # phi(d) = sigma^{-1}(alpha(d)); alpha(d)=sigma(target_dart).
        return self.pair(d, self.sigma[target_dart])

    def _build_face_permutation(self) -> None:
        for d, phi_d in enumerate(self.phi):
            self.solver.add(phi_d >= 0, phi_d < self.dart_count)
            self.solver.add(
                phi_d
                == z3.Sum(
                    [
                        z3.If(self.successor_choice(d, target), target, 0)
                        for target in range(self.dart_count)
                    ]
                )
            )

    def _build_face_periods(self) -> None:
        for dart, length in enumerate(self.face_length):
            self.solver.add(
                z3.Or([length == allowed for allowed in self.allowed_lengths])
            )
        for allowed in self.allowed_lengths:
            expected = self.face_lengths.count(allowed)
            self.solver.add(
                z3.Sum(
                    [z3.If(length == allowed, 1, 0) for length in self.face_length]
                )
                == allowed * expected
            )

        # Face length is constant along phi.  Stating this as one implication
        # per matching choice is considerably smaller than a nested arithmetic
        # array-select expression and is equivalent because phi is one-hot.
        for d in range(self.dart_count):
            for target in range(self.dart_count):
                self.solver.add(
                    z3.Implies(
                        self.successor_choice(d, target),
                        self.face_length[d] == self.face_length[target],
                    )
                )

        powers: list[list[z3.IntRef]] = [
            [z3.IntVal(dart) for dart in range(self.dart_count)]
        ]
        powers.append(self.phi)
        for exponent in range(2, self.max_length + 1):
            row = [z3.Int(f"phi_{exponent}_{d}") for d in range(self.dart_count)]
            powers.append(row)
            for d in range(self.dart_count):
                self.solver.add(row[d] >= 0, row[d] < self.dart_count)
                self.solver.add(
                    row[d]
                    == z3.Sum(
                        [
                            z3.If(powers[exponent - 1][d] == target, self.phi[target], 0)
                            for target in range(self.dart_count)
                        ]
                    )
                )

        # The cap-facial normal form uses these short face walks to state that
        # the two marked chords lie on the same quadrilateral.
        self.phi_powers = powers

        # Exact periods rule out a shorter cycle dividing the requested face
        # length.  Counts above then give the exact number of cycles of each
        # size without introducing arbitrary face labels.
        for d in range(self.dart_count):
            for length in self.allowed_lengths:
                condition = self.face_length[d] == length
                self.solver.add(z3.Implies(condition, powers[length][d] == d))
                for exponent in range(1, length):
                    self.solver.add(z3.Implies(condition, powers[exponent][d] != d))

        # A facial walk may not revisit a vertex.  For every dart and every
        # pair of positions that can lie on its face, compare the source
        # vertex at those positions.  ``powers[0]`` is a constant row.
        vertex_at: list[list[z3.ArithRef]] = []
        for d in range(self.dart_count):
            row: list[z3.ArithRef] = [z3.IntVal(self.vertex_of[d])]
            for exponent in range(1, self.max_length):
                row.append(
                    z3.Sum(
                        [
                            z3.If(powers[exponent][d] == target, self.vertex_of[target], 0)
                            for target in range(self.dart_count)
                        ]
                    )
                )
            vertex_at.append(row)
            for right in range(1, self.max_length):
                for left in range(right):
                    self.solver.add(
                        z3.Implies(
                            self.face_length[d] > right,
                            vertex_at[d][left] != vertex_at[d][right],
                        )
                    )

        # Opposite darts of an edge border faces of different sizes.
        for (d, e), variable in self.pairs.items():
            self.solver.add(z3.Implies(variable, self.face_length[d] != self.face_length[e]))

    def _build_socket_constraints(self) -> None:
        # Each degree-2 white lies on exactly one socket.  Its other incident
        # face is the pentagon opposite a socket edge, so *one*, not both, of
        # its darts belongs to a length-6 face.  Requiring both would consume
        # all twelve hexagon darts with degree-2 vertices and accidentally
        # rule out every genuine alternating 2/5 socket.
        darts_by_vertex: list[list[int]] = [[] for _ in range(self.vertex_count)]
        for dart, vertex in enumerate(self.vertex_of):
            darts_by_vertex[vertex].append(dart)
        for vertex, darts in enumerate(darts_by_vertex):
            degree = self.degrees[vertex]
            if degree == 2:
                self.solver.add(
                    z3.PbEq(
                        [(self.face_length[dart] == 6, 1) for dart in darts], 1
                    )
                )
            elif degree != 5:
                for dart in darts:
                    self.solver.add(self.face_length[dart] != 6)

        # The two hexagons are therefore alternating 2/5 cycles.  The exact
        # face counts give six white darts over the two six-cycles, and this
        # successor condition forces three 2's and three 5's on each one.
        for dart, vertex in enumerate(self.vertex_of):
            degree = self.degrees[vertex]
            for target in range(self.dart_count):
                choice = self.successor_choice(dart, target)
                self.solver.add(
                    z3.Implies(
                        z3.And(choice, self.face_length[dart] == 6),
                        self.degrees[self.vertex_of[target]] != degree,
                    )
                )

        # Every socket boundary edge has a pentagon on its other side.
        for (d, e), variable in self.pairs.items():
            self.solver.add(
                z3.Implies(
                    z3.And(variable, self.face_length[d] == 6),
                    self.face_length[e] == 5,
                )
            )
            self.solver.add(
                z3.Implies(
                    z3.And(variable, self.face_length[e] == 6),
                    self.face_length[d] == 5,
                )
            )

    def _build_t0_vertex_pentagon_constraints(self) -> None:
        """Require the portable ``t=0`` branch for a strict block or its cap.

        Capping changes neither degree-5 vertices nor pentagonal faces.  With
        simple facial walks, a degree-5 vertex has one dart for each incident
        face, so its number of pentagonal darts is its degree in the
        degree-5/pentagon incidence graph.  On the ``t=0`` branch that count
        is exactly two at every degree-5 vertex.

        This is intentionally opt-in: finite-use strict blocks may have
        positive ``t`` and remain valid APG building blocks for a bounded
        composition.  Capping changes no degree-5 vertex or pentagonal face,
        so the same local condition is necessary in a marked closed-cap model
        that is intended to reopen to a portable block.
        """

        for vertex, degree in enumerate(self.degrees):
            if degree != 5:
                continue
            darts = self.cycles[vertex]
            self.solver.add(
                z3.PbEq(
                    [(self.face_length[dart] == 5, 1) for dart in darts], 2
                )
            )

    def _build_residual_h55_2regular_constraints(self) -> None:
        """Propagate the strict portable residual 2-regular ``H55``.

        The canonical socket normal form reserves the first six degree-five
        vertices for the two isolated port cycles.  On the already-required
        ``t=0`` branch, every residual degree-five vertex has two pentagonal
        darts.  Requiring each such dart to share its pentagonal face with
        exactly one dart of another residual vertex expresses the derived
        2-regular residual incidence graph without assigning artificial face
        labels.  Face simplicity and the exact face-period constraints make
        this a representation-invariant propagation condition for genuine
        strict blocks; it is intentionally unavailable for arbitrary closed
        maps and finite-use branches.  With two residual vertices (``r=12``),
        this is exactly the earlier residual ``K2,2 = C4`` condition.
        """

        degree5_vertices = [
            vertex for vertex, degree in enumerate(self.degrees) if degree == 5
        ]
        if len(degree5_vertices) < 8:
            raise ValueError("the residual H55 gate requires at least eight degree-five vertices")
        residual_vertices = degree5_vertices[6:]
        if len(residual_vertices) < 2:
            raise ValueError("canonical ports must leave at least two residual degree-five vertices")
        if len(self.phi_powers) < 5:
            raise ValueError("the residual H55 gate requires pentagon face powers")

        for source_vertex in residual_vertices:
            other_vertices = [
                vertex for vertex in residual_vertices if vertex != source_vertex
            ]
            for source_dart in self.cycles[source_vertex]:
                same_pentagon = [
                    z3.And(
                        self.face_length[source_dart] == 5,
                        self.face_length[other_dart] == 5,
                        z3.Or(
                            *(
                                self.phi_powers[step][source_dart] == other_dart
                                for step in range(1, 5)
                            )
                        ),
                    )
                    for other_vertex in other_vertices
                    for other_dart in self.cycles[other_vertex]
                ]
                self.solver.add(
                    z3.Implies(
                        self.face_length[source_dart] == 5,
                        z3.PbEq([(shared, 1) for shared in same_pentagon], 1),
                    )
                )

    def _build_face_edge_counts(self) -> None:
        """Add the forced edge counts between unequal face-size classes."""

        incidence = {
            length: length * self.face_lengths.count(length)
            for length in self.allowed_lengths
        }
        if self.open_block:
            # The two hexagons have twelve boundary darts, all opposite
            # pentagons by the strict socket constraints.
            forced = {(5, 6): incidence[6]}
            residual = {length: value for length, value in incidence.items() if length != 6}
            residual[5] -= incidence[6]
            counts = {**forced, **self._three_class_counts(residual)}
        else:
            counts = self._three_class_counts(incidence)
        for (left_length, right_length), expected in counts.items():
            terms = []
            for (d, e), variable in self.pairs.items():
                terms.append(
                    z3.And(
                        variable,
                        z3.Or(
                            z3.And(
                                self.face_length[d] == left_length,
                                self.face_length[e] == right_length,
                            ),
                            z3.And(
                                self.face_length[d] == right_length,
                                self.face_length[e] == left_length,
                            ),
                        ),
                    )
                )
            self.solver.add(z3.PbEq([(term, 1) for term in terms], expected))

    def _build_canonical_constraints(self) -> None:
        if self.open_block:
            # A strict block's two alternating socket hexagons can be
            # independently renamed and every local dart cycle rotated.  The
            # twelve pairs below are consequently a pure representation normal
            # form, not a restriction on the underlying block class.  See
            # BOOLEAN_SOCKET_CANONICALIZATION.md and its published-block gate.
            for dart, mate in canonical_two_socket_pairs(self.degrees):
                self.solver.add(self.pair(dart, mate))
            socket_cycles, pentagon_darts = canonical_two_socket_face_darts(
                self.degrees
            )
            for cycle in socket_cycles:
                for dart in cycle:
                    self.solver.add(self.face_length[dart] == 6)
            for dart in pentagon_darts:
                self.solver.add(self.face_length[dart] == 5)
            return
        r = self.degrees.count(3)
        first_degree4 = 3 * r
        first_degree5 = first_degree4 + 4 * self.degrees.count(4)
        self.solver.add(z3.Or(self.pair(0, first_degree4), self.pair(0, first_degree5)))

    def alpha_from_model(self, model: z3.ModelRef) -> list[int]:
        alpha = [-1] * self.dart_count
        for (d, e), variable in self.pairs.items():
            if z3.is_true(model.eval(variable, model_completion=True)):
                alpha[d] = e
                alpha[e] = d
        if any(mate < 0 for mate in alpha):
            raise ValueError("model did not assign a complete dart matching")
        return alpha


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lane", choices=("closed", "block"))
    parser.add_argument("--r", type=int)
    parser.add_argument("--closed-order", type=int, default=46)
    parser.add_argument("--block-order", type=int, default=27)
    parser.add_argument("--known-certificate", type=Path)
    parser.add_argument(
        "--known-block",
        type=Path,
        help="pin a published open strict block as an encoding control",
    )
    parser.add_argument(
        "--known-cap-block",
        type=Path,
        help=(
            "close a published strict block, relabel its two marked cap fans, "
            "and pin the resulting closed-map cap-normal-form control"
        ),
    )
    parser.add_argument(
        "--canonicalize-known-block",
        action="store_true",
        help=(
            "relabel a --known-block into the complete socket normal form and "
            "exercise canonical=True on the fixed control"
        ),
    )
    parser.add_argument("--timeout-s", type=int, required=True)
    parser.add_argument("--random-seed", type=int, default=0)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--no-canonical", action="store_true")
    parser.add_argument(
        "--require-cap-fans",
        action="store_true",
        help=(
            "for a closed map, require two marked degree-4 to degree-3/3 cap "
            "fans; a positive model must still reopen to a strict block"
        ),
    )
    parser.add_argument(
        "--require-t0",
        action="store_true",
        help=(
            "restrict a strict block or marked closed cap to the portable t=0 "
            "branch; this is not a nonexistence filter for finite-use blocks"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.threads < 1:
        parser.error("--threads must be positive")
    if sum(
        path is not None
        for path in (args.known_certificate, args.known_block, args.known_cap_block)
    ) > 1:
        parser.error("choose at most one known control")
    if args.canonicalize_known_block and args.known_block is None:
        parser.error("--canonicalize-known-block requires --known-block")
    if args.canonicalize_known_block and args.no_canonical:
        parser.error("--canonicalize-known-block cannot be combined with --no-canonical")
    if args.known_cap_block is not None and args.no_canonical:
        parser.error("--known-cap-block cannot be combined with --no-canonical")
    cap_fans: tuple[tuple[int, tuple[int, int]], ...] = ()
    known_path = args.known_certificate or args.known_block
    if args.known_cap_block is not None:
        if args.lane is not None or args.r is not None:
            parser.error("a known control cannot be combined with --lane/--r")
        data = json.loads(args.known_cap_block.read_text(encoding="utf-8"))
        rows = data.get("vertices") if isinstance(data, dict) else None
        rotation = blocks.rotation_from_certificate(
            {"format": blocks.APG_FORMAT, "vertices": rows}
        )
        sockets = blocks.validate_block(rotation)
        block = blocks.Block(rotation, sockets)
        source_fans = tuple(
            blocks.ClosureFan(
                hub=sorted(socket.whites)[0],
                leaves=tuple(sorted(socket.whites)[1:]),
            )
            for socket in sockets
        )
        closed_rotation = blocks.close_block_with_hubs(block, (0, 0))
        canonical_rotation = canonicalize_closed_cap_rotation(
            closed_rotation, source_fans
        )
        degrees, faces, fixed_alpha = closed_profile_from_rotation(
            canonical_rotation
        )
        cap_fans = canonical_closed_cap_fans(degrees)
        open_block = False
        lane = "closed"
        r_value = degrees.count(3)
    elif known_path is not None:
        if args.lane is not None or args.r is not None:
            parser.error("a known control cannot be combined with --lane/--r")
        open_block = args.known_block is not None
        if args.canonicalize_known_block:
            data = json.loads(known_path.read_text(encoding="utf-8"))
            rows = data.get("vertices") if isinstance(data, dict) else None
            rotation = blocks.rotation_from_certificate(
                {"format": blocks.APG_FORMAT, "vertices": rows}
            )
            canonical_rotation = canonicalize_two_socket_rotation(rotation)
            degrees, faces, fixed_alpha = strict_block_profile_from_rotation(
                canonical_rotation
            )
        else:
            degrees, faces, fixed_alpha = profile_from_certificate(known_path)
        # Use the normal block lane so its record can pass through the same
        # strict validator, nine closures, and independent checkers as a
        # discovered open candidate.  The explicit control tag distinguishes
        # it from a target-search record.
        lane = "block" if open_block else "known"
        r_value = degrees.count(3) + 4 if open_block else degrees.count(3)
    elif args.lane == "closed":
        if args.r is None:
            parser.error("closed lane requires --r")
        try:
            degrees, faces = profile_closed(args.closed_order, args.r)
        except ValueError as exc:
            parser.error(str(exc))
        fixed_alpha = None
        open_block = False
        lane = args.lane
        r_value = args.r
    else:
        if args.lane != "block":
            parser.error("one of --lane or --known-certificate is required")
        if args.r is None:
            parser.error("block lane requires --r")
        try:
            degrees, faces = profile_block(args.block_order, args.r)
        except ValueError as exc:
            parser.error(str(exc))
        fixed_alpha = None
        open_block = True
        lane = args.lane
        r_value = args.r

    if args.require_cap_fans:
        if open_block:
            parser.error("--require-cap-fans is valid only for a closed map")
        if args.known_certificate is not None:
            parser.error(
                "a cap-fan known control must use --known-cap-block, not --known-certificate"
            )
        if not cap_fans:
            try:
                cap_fans = canonical_closed_cap_fans(degrees)
            except ValueError as exc:
                parser.error(str(exc))

    if args.require_t0:
        if not open_block and not cap_fans:
            parser.error("--require-t0 is valid only for an open block or marked cap")
        if not strict_portable_t0_profile_is_feasible(len(degrees), r_value):
            parser.error(
                "the requested profile fails the portable strict t=0 profile gate "
                f"(order={len(degrees)}, r={r_value})"
            )

    canonical = (not args.no_canonical) and (
        fixed_alpha is None
        or args.canonicalize_known_block
        or args.known_cap_block is not None
    )
    started = time.time()
    encoding = BooleanMapEncoding(
        degrees,
        faces,
        open_block=open_block,
        canonical=canonical,
        fixed_alpha=fixed_alpha,
        require_t0=args.require_t0,
        cap_fans=cap_fans,
    )
    constraint_count = len(encoding.solver.assertions())
    encoding.solver.set(
        timeout=args.timeout_s * 1000,
        random_seed=args.random_seed,
        threads=args.threads,
    )
    result = encoding.solver.check()
    record: dict[str, object] = {
        "format": "apg-exact-map-bool-sat-v1",
        "lane": lane,
        "r": r_value,
        "order": len(degrees),
        "disposition": "INCOMPLETE",
        "z3_result": str(result),
        "timeout_seconds": args.timeout_s,
        "wall_seconds": time.time() - started,
        "z3_version": z3.get_version_string(),
        "python": sys.version,
        "platform": platform.platform(),
        "encoding": "boolean-dart-matching-plus-face-period",
        "encoding_constraint_count": constraint_count,
        "heuristic": False,
        "random_seed": args.random_seed,
        "threads": args.threads,
        "canonical": canonical,
        "require_t0": args.require_t0,
        "require_residual_h55_2regular": encoding.require_residual_h55_2regular,
        "require_residual_h55_c4": encoding.require_residual_h55_c4,
        "require_cap_fans": bool(cap_fans),
        "require_cap_interface": bool(cap_fans),
        "require_cap_facets": bool(cap_fans),
        "explicit_connectivity": False,
        "solver_statistics": _solver_statistics(encoding.solver.statistics()),
    }
    if args.known_block is not None:
        record["control"] = (
            "published-strict-block-canonicalized"
            if args.canonicalize_known_block
            else "published-strict-block"
        )
    elif args.known_certificate is not None:
        record["control"] = "published-closed-map"
    elif args.known_cap_block is not None:
        record["control"] = "published-strict-block-capped-cap-normalized"
    if cap_fans:
        record["cap_fans"] = [
            {"center": hub, "leaves": list(leaves)} for hub, leaves in cap_fans
        ]
    if result == z3.sat:
        record["disposition"] = "CANDIDATE"
        record["certificate"] = dump_rotation(degrees, encoding.alpha_from_model(encoding.solver.model()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items() if key != "certificate"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
