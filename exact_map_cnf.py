#!/usr/bin/env python3
"""Pure-CNF exact search for closed (3,4,5)-alternating plane maps.

Why this module exists
----------------------
``exact_map_sat.py`` and ``exact_map_bool_sat.py`` state the facial structure
with Z3 *integer* terms: ``phi``, ``face_length``, the ``phi_powers`` chain and
the ``vertex_at`` rows are ``z3.Int`` values defined by ``Sum(If(...))``
expressions over every dart.  That is quadratic-to-cubic in the dart count and
puts the whole facial argument inside linear-integer-arithmetic reasoning,
where a Boolean solver would use unit propagation.  Every target profile in the
recorded Cloud checkpoints returned ``unknown`` at its bound, with the same
disposition across three different structural strengthenings -- the signature of
a solver-core bottleneck rather than a missing constraint.

This module states the identical mathematics in conjunctive normal form only,
so a CDCL solver can propagate it:

* ``alpha`` is a Boolean perfect matching on darts (as before);
* ``phi = sigma^-1 alpha`` is *not* a variable -- ``phi(d) = t`` is literally the
  matching literal ``m[d, sigma(t)]``;
* faces are Boolean *labels* with prescribed sizes, propagated along ``phi``.

The "single cycle per label" property, which the integer encoding bought with
an explicit ``phi^k`` power chain, is here a theorem of the constraint set:
loops and parallel edges are excluded, so every ``phi``-orbit has length at
least three, and every label class has size at most five, so a class cannot
contain two orbits.  ``prove_label_class_is_one_orbit`` records that argument
as an executable check.

This is a *positive-witness* engine.  A solver timeout is ``INCOMPLETE``.
``unsat`` is a statement about this encoding at this profile, never a
nonexistence theorem about (3,4,5)-alternating plane graphs; the encoding adds
representation conventions (fixed vertex slots, ordered face labels) whose
soundness is argued per constraint below and gated by the two independent
verifiers on every emitted certificate.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Any, Iterable, Sequence

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Cadical195

from certificate_tools import (  # re-exported: the gate imports them from there
    alpha_from_certificate,
    cycles_from_degrees,
    run_verifiers,
)

HERE = Path(__file__).resolve().parent
ALLOWED = (3, 4, 5)


def closed_profile(order: int, r: int) -> tuple[list[int], list[int]]:
    """Return (vertex degrees, face sizes) for the closed profile ``(order, r)``.

    The identities ``v3 = f3 = r``, ``v5 = f5 = r - 4`` and
    ``v4 = f4 = order - 2r + 4`` are forced for any closed APG; see README.
    """

    n3, n4, n5 = r, order - 2 * r + 4, r - 4
    if order < 4 or min(n3, n4, n5) < 0:
        raise ValueError(f"invalid closed profile order={order}, r={r}")
    degrees = [3] * n3 + [4] * n4 + [5] * n5
    if len(degrees) != order or sum(degrees) != 4 * order - 4:
        raise AssertionError("closed profile count identity failed")
    return degrees, list(degrees)


def block_profile(order: int, r: int) -> tuple[list[int], list[int]]:
    """Return (degrees, face sizes) for the strict two-socket block profile.

    ``r`` is the parameter of a capped closure.  Capping turns the six
    degree-2 socket whites into four degree-3 and two degree-4 incidences, so
    the open block carries ``r - 4`` degree-3 and degree-5 vertices,
    ``order - 2r + 2`` degree-4 vertices, and two hexagonal socket faces.
    This mirrors ``exact_map_sat.profile_block`` exactly.
    """

    n3, n4, n5 = r - 4, order - 2 * r + 2, r - 4
    if order < 4 or min(n3, n4, n5) < 0:
        raise ValueError(f"invalid block profile order={order}, r={r}")
    degrees = [2] * 6 + [3] * n3 + [4] * n4 + [5] * n5
    faces = [3] * n3 + [4] * n4 + [5] * n5 + [6] * 2
    if len(degrees) != order or sum(degrees) != 4 * order - 12:
        raise AssertionError("block profile count identity failed")
    return degrees, faces


def feasible_r_values(order: int) -> list[int]:
    """Every ``r`` admitting a closed profile at this order."""

    return [r for r in range(4, order + 1) if order - 2 * r + 4 >= 0 and r - 4 >= 0]


def dump_rotation(degrees: Sequence[int], alpha: Sequence[int]) -> dict[str, object]:
    """Emit the certificate contract's JSON rotation system."""

    cycles, vertex_of, _, _ = cycles_from_degrees(degrees)
    rows = []
    for vertex, cycle in enumerate(cycles):
        neighbours = [vertex_of[alpha[d]] for d in cycle]
        smallest = neighbours.index(min(neighbours))
        rows.append({"id": vertex, "clockwise": neighbours[smallest:] + neighbours[:smallest]})
    return {"format": "apg-plane-rotation-v1", "vertices": rows}


def adjacency_from_alpha(degrees: Sequence[int], alpha: Sequence[int]) -> list[list[bool]]:
    """Vertex adjacency of the map given by ``alpha`` on this module's slots."""

    _, vertex_of, _, _ = cycles_from_degrees(degrees)
    count = len(degrees)
    matrix = [[False] * count for _ in range(count)]
    for dart, mate in enumerate(alpha):
        u, v = vertex_of[dart], vertex_of[mate]
        matrix[u][v] = True
        matrix[v][u] = True
    return matrix


def _transposition_comparison(
    matrix: list[list[bool]], v: int
) -> tuple[list[bool], list[bool]]:
    """The row-major coordinates on which swapping ``v`` and ``v + 1`` acts.

    Reading the upper triangle in row-major order, the transposition first
    touches ``(u, v)`` and ``(u, v + 1)`` inside every earlier row ``u``, then
    the tail of row ``v``.  Entry ``(v, v + 1)`` is fixed, and row ``v + 1``'s
    tail carries no information the tail of row ``v`` has not already decided.
    """

    count = len(matrix)
    left: list[bool] = []
    right: list[bool] = []
    for u in range(v):
        left.extend((matrix[u][v], matrix[u][v + 1]))
        right.extend((matrix[u][v + 1], matrix[u][v]))
    for w in range(v + 2, count):
        left.append(matrix[v][w])
        right.append(matrix[v + 1][w])
    return left, right


def _swap_vertex_slots(degrees: Sequence[int], alpha: Sequence[int], v: int) -> list[int]:
    """Exchange the dart blocks of the equal-degree vertices ``v`` and ``v+1``.

    The blocks have the same length and each stays cyclically ordered, so
    ``sigma`` is preserved and the result is the same plane map relabelled.
    """

    cycles, _, _, _ = cycles_from_degrees(degrees)
    if degrees[v] != degrees[v + 1]:
        raise ValueError(f"vertices {v} and {v + 1} have different degrees")
    swap = list(range(len(alpha)))
    for left, right in zip(cycles[v], cycles[v + 1]):
        swap[left], swap[right] = right, left
    relabelled = [0] * len(alpha)
    for dart, mate in enumerate(alpha):
        relabelled[swap[dart]] = swap[mate]
    return relabelled


def satisfies_vertex_lex_leader(degrees: Sequence[int], alpha: Sequence[int]) -> int | None:
    """Return the first violating slot, or ``None`` when the break is satisfied."""

    matrix = adjacency_from_alpha(degrees, alpha)
    for v in range(len(degrees) - 1):
        if degrees[v] != degrees[v + 1]:
            continue
        left, right = _transposition_comparison(matrix, v)
        if right > left:
            return v
    return None


def lex_leader_relabelling(
    degrees: Sequence[int], alpha: Sequence[int], *, step_limit: int = 100_000
) -> list[int]:
    """Relabel a map into a representative satisfying the lex-leader break.

    Whenever the constraint at slot ``v`` is violated, swapping ``v`` and
    ``v + 1`` makes the flattened adjacency matrix strictly lexicographically
    greater.  A strictly increasing walk through a finite totally ordered set
    terminates, so this always halts -- and it halts at a labelling with no
    violated adjacent transposition, which is exactly the constraint the
    encoder states.  This is the executable soundness control for
    ``ClosedMapCNF._break_vertex_symmetry``: the break can only be trusted
    because every map has such a representative.
    """

    current = list(alpha)
    for _ in range(step_limit):
        violation = satisfies_vertex_lex_leader(degrees, current)
        if violation is None:
            return current
        current = _swap_vertex_slots(degrees, current, violation)
    raise RuntimeError("lex-leader relabelling did not converge within the step limit")


def _solve_exactly(rows: list[list["object"]], unknowns: int):
    """Exact Gaussian elimination; ``None`` unless the system pins every value."""

    from fractions import Fraction

    matrix = [list(row) for row in rows]
    pivots: list[int] = []
    row_index = 0
    for column in range(unknowns):
        pivot = next(
            (i for i in range(row_index, len(matrix)) if matrix[i][column] != 0), None
        )
        if pivot is None:
            continue
        matrix[row_index], matrix[pivot] = matrix[pivot], matrix[row_index]
        scale = matrix[row_index][column]
        matrix[row_index] = [value / scale for value in matrix[row_index]]
        for other in range(len(matrix)):
            if other == row_index or matrix[other][column] == 0:
                continue
            factor = matrix[other][column]
            matrix[other] = [
                value - factor * lead
                for value, lead in zip(matrix[other], matrix[row_index])
            ]
        pivots.append(column)
        row_index += 1
    if len(pivots) != unknowns:
        return None
    for row in matrix[row_index:]:
        if row[-1] != 0:
            return None
    return [matrix[i][-1] for i in range(unknowns)]


def prove_label_class_is_one_orbit(max_face_size: int, min_orbit_length: int) -> bool:
    """The face-label classes are exactly the ``phi``-orbits.

    Every orbit lies inside one label class (labels propagate along ``phi``).
    A class holding two orbits would have at least ``2 * min_orbit_length``
    darts, so the encoding needs ``2 * min_orbit_length > max_face_size``.
    ``min_orbit_length = 3`` holds because loops (``phi(d) = d``) and parallel
    edges (``phi^2(d) = d`` is a digon) are both excluded outright.
    """

    return 2 * min_orbit_length > max_face_size


class ClosedMapCNF:
    """CNF for a closed (3,4,5)-APG on a fixed degree/face profile."""

    def __init__(
        self,
        degrees: Sequence[int],
        face_sizes: Sequence[int],
        *,
        open_block: bool = False,
        require_t0: bool = False,
        break_face_symmetry: bool = True,
        break_vertex_symmetry: bool = False,
        fixed_alpha: Sequence[int] | None = None,
    ) -> None:
        self.open_block = open_block
        self.require_t0 = require_t0
        self.degrees = list(degrees)
        self.face_sizes = sorted(face_sizes)
        self.cycles, self.vertex_of, self.sigma, self.sigma_inverse = cycles_from_degrees(self.degrees)
        self.dart_count = len(self.vertex_of)
        self.vertex_count = len(self.degrees)
        self.face_count = len(self.face_sizes)
        if sum(self.face_sizes) != self.dart_count:
            raise ValueError("face sizes must consume every dart exactly once")
        self.largest_face = max(self.face_sizes)
        # The size domain follows the profile: the block lane adds hexagons.
        self.allowed_sizes = tuple(sorted(set(self.face_sizes)))
        if self.largest_face > 6:
            raise ValueError(
                f"face size {self.largest_face} is outside the lanes this module "
                "encodes (closed {3,4,5} maps and two-socket blocks)"
            )
        if self.largest_face == 6 and not open_block:
            raise ValueError(
                "a size-six face needs an explicit orbit constraint; pass "
                "open_block=True to encode the two-socket block lane"
            )
        if not open_block and not prove_label_class_is_one_orbit(self.largest_face, 3):
            raise AssertionError("closed lane lost its one-orbit-per-class argument")

        self.pool = IDPool()
        self.clauses: list[list[int]] = []
        self._pair_index: dict[tuple[int, int], int] = {}

        self._declare_pairs()
        self._matching_is_a_perfect_involution()
        self._no_parallel_edges()
        self._build_degree_edge_counts()
        self._one_face_label_per_dart()
        self._labels_propagate_along_phi()
        self._label_class_sizes()
        self._no_repeated_vertex_on_a_face()
        self._adjacent_faces_have_different_sizes()
        self._triangles_have_one_corner_of_each_degree()
        if not open_block:
            # Both derivations below assume face sizes and degrees are exactly
            # {3,4,5}; the block lane has degree-2 whites and hexagons.
            self._degree_three_links_carry_every_size()
            self._forced_corner_counts()
        if self.largest_face == 6:
            self._hexagons_are_single_orbits()
        if open_block:
            self._build_socket_interface()
        if require_t0:
            self._degree_five_vertices_carry_two_pentagons()
        if break_face_symmetry:
            self._order_labels_by_least_dart()
        if break_vertex_symmetry:
            self._break_vertex_symmetry()
        if fixed_alpha is not None:
            self._fix_matching(fixed_alpha)

    # ---------------------------------------------------------------- variables

    def _allowed_pair(self, d: int, e: int) -> bool:
        u, v = self.vertex_of[d], self.vertex_of[e]
        # No loops, and adjacent vertices must have different degrees.
        if u == v:
            return False
        left, right = self.degrees[u], self.degrees[v]
        if left == right:
            return False
        if self.open_block and 2 in (left, right) and {left, right} != {2, 5}:
            # A socket white sits between two pentagon corners.
            return False
        return True

    def _declare_pairs(self) -> None:
        for d in range(self.dart_count):
            for e in range(d + 1, self.dart_count):
                if self._allowed_pair(d, e):
                    self._pair_index[(d, e)] = self.pool.id(f"m_{d}_{e}")
        self.pair_choices: list[list[int]] = [[] for _ in range(self.dart_count)]
        for (d, e), literal in self._pair_index.items():
            self.pair_choices[d].append(literal)
            self.pair_choices[e].append(literal)

    def pair(self, d: int, e: int) -> int | None:
        """Literal for ``alpha(d) = e``; ``None`` when the pair is excluded."""

        if d == e:
            return None
        return self._pair_index.get((d, e) if d < e else (e, d))

    def face(self, dart: int, label: int) -> int:
        return self.pool.id(f"f_{dart}_{label}")

    def size_at(self, dart: int, size: int) -> int:
        return self.pool.id(f"s_{dart}_{size}")

    # -------------------------------------------------------------- constraints

    def _exactly_one(self, literals: Sequence[int]) -> None:
        if not literals:
            raise ValueError("exactly-one over an empty domain is unsatisfiable")
        self.clauses.append(list(literals))
        self._at_most_one(literals)

    def _at_most_one(self, literals: Sequence[int]) -> None:
        if len(literals) <= 1:
            return
        if len(literals) <= 40:
            for i, left in enumerate(literals):
                for right in literals[i + 1 :]:
                    self.clauses.append([-left, -right])
            return
        encoded = CardEnc.atmost(
            lits=list(literals), bound=1, vpool=self.pool, encoding=EncType.seqcounter
        )
        self.clauses.extend(encoded.clauses)

    def _at_most(self, literals: Sequence[int], bound: int) -> None:
        if len(literals) <= bound:
            return
        encoded = CardEnc.atmost(
            lits=list(literals), bound=bound, vpool=self.pool, encoding=EncType.seqcounter
        )
        self.clauses.extend(encoded.clauses)

    def _at_least(self, literals: Sequence[int], bound: int) -> None:
        if bound <= 0:
            return
        if bound >= len(literals):
            for literal in literals:
                self.clauses.append([literal])
            return
        encoded = CardEnc.atleast(
            lits=list(literals), bound=bound, vpool=self.pool, encoding=EncType.seqcounter
        )
        self.clauses.extend(encoded.clauses)

    def _matching_is_a_perfect_involution(self) -> None:
        # Each pair variable occurs in the equation of both of its darts, so
        # "exactly one mate per dart" already forces alpha to be an involution.
        for d in range(self.dart_count):
            self._exactly_one(self.pair_choices[d])

    def _no_parallel_edges(self) -> None:
        by_vertex_pair: dict[tuple[int, int], list[int]] = {}
        for (d, e), literal in self._pair_index.items():
            u, v = self.vertex_of[d], self.vertex_of[e]
            key = (u, v) if u < v else (v, u)
            by_vertex_pair.setdefault(key, []).append(literal)
        for literals in by_vertex_pair.values():
            self._at_most_one(literals)

    def _one_face_label_per_dart(self) -> None:
        for d in range(self.dart_count):
            self._exactly_one([self.face(d, k) for k in range(self.face_count)])
        # Face size is a definition, not an extra degree of freedom.
        for d in range(self.dart_count):
            for size in self.allowed_sizes:
                labels = [k for k in range(self.face_count) if self.face_sizes[k] == size]
                for k in labels:
                    self.clauses.append([-self.face(d, k), self.size_at(d, size)])
                self.clauses.append([-self.size_at(d, size)] + [self.face(d, k) for k in labels])
            self._exactly_one([self.size_at(d, size) for size in self.allowed_sizes])

    def phi_edges(self) -> Iterable[tuple[int, int, int]]:
        """Yield ``(d, t, literal)`` with ``literal`` asserting ``phi(d) = t``.

        ``phi = sigma^-1 alpha``, so ``phi(d) = t`` is exactly
        ``alpha(d) = sigma(t)``: no auxiliary variable is introduced.
        """

        for (d, e), literal in self._pair_index.items():
            yield d, self.sigma_inverse[e], literal
            yield e, self.sigma_inverse[d], literal

    def _labels_propagate_along_phi(self) -> None:
        # phi(d) = t implies label(d) = label(t).  Exactly one label per dart
        # makes either implication direction sufficient on its own, but stating
        # both lets unit propagation run backwards along a facial walk as well
        # as forwards, which is where most of the pruning comes from.
        for d, t, literal in self.phi_edges():
            for k in range(self.face_count):
                self.clauses.append([-literal, -self.face(d, k), self.face(t, k)])
                self.clauses.append([-literal, self.face(d, k), -self.face(t, k)])

    def _label_class_sizes(self) -> None:
        # "At most" already forces equality, because every dart carries exactly
        # one label and the prescribed sizes sum to the dart count.  The lower
        # bound is therefore redundant -- and stating it anyway is what lets the
        # solver close a label class by propagation instead of by search.
        for k in range(self.face_count):
            literals = [self.face(d, k) for d in range(self.dart_count)]
            self._at_most(literals, self.face_sizes[k])
            self._at_least(literals, self.face_sizes[k])

    def degree_edge_counts(self) -> dict[tuple[int, int], int]:
        """The number of edges between each pair of degree classes is forced.

        Alternation puts every edge between two different degrees, so with
        ``n_L`` vertices of degree ``L`` the three counts satisfy
        ``3 n3 = e34 + e35``, ``4 n4 = e34 + e45`` and ``5 n5 = e35 + e45``.
        That is a nonsingular 3x3 system: the counts are determined by the
        profile, not merely bounded by it.
        """

        from fractions import Fraction

        present = sorted(set(self.degrees))
        unknowns = [
            (left, right)
            for index, left in enumerate(present)
            for right in present[index + 1 :]
            if self._degree_pair_is_allowed(left, right)
        ]
        rows: list[list[Fraction]] = []
        for degree in present:
            row = [
                Fraction(1) if degree in pair else Fraction(0) for pair in unknowns
            ]
            row.append(Fraction(degree * self.degrees.count(degree)))
            rows.append(row)
        solution = _solve_exactly(rows, len(unknowns))
        if solution is None:
            return {}
        counts: dict[tuple[int, int], int] = {}
        for pair, value in zip(unknowns, solution):
            if value.denominator != 1 or value < 0:
                return {}
            counts[pair] = int(value)
        return counts

    def _degree_pair_is_allowed(self, left: int, right: int) -> bool:
        if left == right:
            return False
        if self.open_block and 2 in (left, right) and {left, right} != {2, 5}:
            return False
        return True

    def _build_degree_edge_counts(self) -> None:
        buckets: dict[tuple[int, int], list[int]] = {}
        for (d, e), literal in self._pair_index.items():
            left = self.degrees[self.vertex_of[d]]
            right = self.degrees[self.vertex_of[e]]
            buckets.setdefault((min(left, right), max(left, right)), []).append(literal)
        for key, expected in self.degree_edge_counts().items():
            literals = buckets.get(key, [])
            if expected < 0 or expected > len(literals):
                raise ValueError(f"profile forces {expected} edges of type {key}")
            self._at_most(literals, expected)
            self._at_least(literals, expected)

    def _no_repeated_vertex_on_a_face(self) -> None:
        # verify.py rejects a facial walk that repeats a vertex.  Two darts of
        # the same vertex on one face is exactly that situation.
        for cycle in self.cycles:
            for i, left in enumerate(cycle):
                for right in cycle[i + 1 :]:
                    for k in range(self.face_count):
                        self.clauses.append([-self.face(left, k), -self.face(right, k)])

    def _adjacent_faces_have_different_sizes(self) -> None:
        for (d, e), literal in self._pair_index.items():
            for size in self.allowed_sizes:
                self.clauses.append([-literal, -self.size_at(d, size), -self.size_at(e, size)])

    def hexagon_position(self, dart: int, index: int) -> int:
        return self.pool.id(f"h_{dart}_{index}")

    def _hexagons_are_single_orbits(self) -> None:
        """Force each size-six label class to be one ``phi``-orbit, not two.

        Below size six the one-orbit property is free: orbits have length at
        least three and classes have size at most five.  A hexagonal class can
        instead be two triangles, which would satisfy every other constraint
        while describing a different map.

        The fix is a position in ``Z/6`` carried by each hexagonal dart, with
        ``pos(phi(d)) = pos(d) + 1``.  Walking an orbit of length ``L`` back to
        its start gives ``L = 0 mod 6``, so ``L >= 6``; the class has exactly
        six darts and contains the orbit, so ``L = 6`` and the class is that
        one orbit.  No "exactly one dart at position zero" clause is needed --
        the divisibility argument already closes it.
        """

        for dart in range(self.dart_count):
            on_hexagon = self.size_at(dart, 6)
            positions = [self.hexagon_position(dart, index) for index in range(6)]
            self.clauses.append([-on_hexagon] + positions)
            for index, position in enumerate(positions):
                self.clauses.append([-position, on_hexagon])
                for other in positions[index + 1 :]:
                    self.clauses.append([-position, -other])
        for d, t, literal in self.phi_edges():
            for index in range(6):
                self.clauses.append(
                    [
                        -literal,
                        -self.hexagon_position(d, index),
                        self.hexagon_position(t, (index + 1) % 6),
                    ]
                )

    def _build_socket_interface(self) -> None:
        """The two hexagons are the block's sockets, not ordinary faces.

        Ported from exact_map_bool_sat._build_socket_constraints, with its
        correction kept: a degree-2 white lies on *exactly one* hexagon, not
        two.  Its other incident face is the pentagon opposite a socket edge;
        requiring both darts would consume all twelve hexagon darts with
        degree-2 vertices and rule out every genuine alternating 2/5 socket.
        """

        for vertex, cycle in enumerate(self.cycles):
            degree = self.degrees[vertex]
            if degree == 2:
                self._exactly_one([self.size_at(dart, 6) for dart in cycle])
            elif degree != 5:
                # Only whites and pentagon corners sit on a socket hexagon.
                for dart in cycle:
                    self.clauses.append([-self.size_at(dart, 6)])

        # Each hexagon is an alternating 2/5 cycle: consecutive corners along a
        # socket differ in degree.  With six white darts spread over two
        # six-cycles this forces three 2s and three 5s on each.
        for d, t, literal in self.phi_edges():
            if self.degrees[self.vertex_of[d]] == self.degrees[self.vertex_of[t]]:
                self.clauses.append([-literal, -self.size_at(d, 6)])

        # Every socket boundary edge has a pentagon on its far side.
        for (d, e), literal in self._pair_index.items():
            self.clauses.append([-literal, -self.size_at(d, 6), self.size_at(e, 5)])
            self.clauses.append([-literal, -self.size_at(e, 6), self.size_at(d, 5)])

    def _degree_five_vertices_carry_two_pentagons(self) -> None:
        """The portable t = 0 branch, stated locally.

        With simple facial walks a degree-5 vertex has one dart per incident
        face, so its pentagonal-dart count is its degree in the
        degree-5/pentagon incidence graph; on the t = 0 branch that is
        exactly two.  Opt-in: a finite-use block may have positive t and
        still be a valid building block for a bounded composition.
        """

        for vertex, cycle in enumerate(self.cycles):
            if self.degrees[vertex] != 5:
                continue
            literals = [self.size_at(dart, 5) for dart in cycle]
            self._at_most(literals, 2)
            self._at_least(literals, 2)

    def _degree_three_links_carry_every_size(self) -> None:
        """The three faces at a degree-3 vertex have sizes exactly 3, 4 and 5.

        The three faces at ``v`` are distinct (no facial walk repeats a
        vertex) and pairwise adjacent, meeting along the three edges at ``v``,
        so their sizes are pairwise different -- and three pairwise different
        values from ``{3,4,5}`` are all of them.  Implied by the per-edge
        constraint, but a solver reaches it by search rather than by
        propagation unless it is stated.
        """

        for vertex, cycle in enumerate(self.cycles):
            if self.degrees[vertex] != 3:
                continue
            for size in ALLOWED:
                self._exactly_one([self.size_at(dart, size) for dart in cycle])

    def _triangles_have_one_corner_of_each_degree(self) -> None:
        """A triangular face has vertex degrees exactly 3, 4 and 5.

        Its three vertices are pairwise adjacent, so alternation makes their
        degrees pairwise different.
        """

        triangles = [k for k, size in enumerate(self.face_sizes) if size == 3]
        if not triangles:
            return
        for left in range(self.dart_count):
            for right in range(left + 1, self.dart_count):
                if self.degrees[self.vertex_of[left]] != self.degrees[self.vertex_of[right]]:
                    continue
                if self.vertex_of[left] == self.vertex_of[right]:
                    continue  # already excluded by the repeated-vertex clauses
                for k in triangles:
                    self.clauses.append([-self.face(left, k), -self.face(right, k)])

    def corner_counts(self) -> dict[tuple[int, int], int]:
        """Corner counts the profile forces, as ``(face size, vertex degree)``.

        Every triangle has exactly one corner of each degree and there are
        ``f3 = r`` triangles, so ``c[3][k] = r`` for each degree ``k``.  Every
        degree-3 vertex carries exactly one face of each size and there are
        ``n3 = r`` of them, so ``c[L][3] = r`` for each size ``L``.  The rest
        of the 3x3 table is not determined by the profile alone.
        """

        r = self.degrees.count(3)
        forced = {(3, degree): r for degree in ALLOWED}
        forced.update({(size, 3): r for size in ALLOWED})
        return forced

    def _forced_corner_counts(self) -> None:
        by_degree: dict[int, list[int]] = {degree: [] for degree in ALLOWED}
        for dart in range(self.dart_count):
            by_degree[self.degrees[self.vertex_of[dart]]].append(dart)
        for (size, degree), expected in self.corner_counts().items():
            literals = [self.size_at(dart, size) for dart in by_degree[degree]]
            if expected > len(literals):
                raise ValueError(
                    f"profile forces {expected} size-{size} corners at degree-{degree} "
                    f"vertices but only has {len(literals)} darts there"
                )
            self._at_most(literals, expected)
            self._at_least(literals, expected)

    def _order_labels_by_least_dart(self) -> None:
        """Labels of equal size are interchangeable; order them by least dart.

        This is a representation normal form, not a restriction: relabelling
        within a size class carries any solution to one that satisfies it.
        The prefix-OR chain keeps the encoding linear in ``darts x labels``.
        """

        by_size: dict[int, list[int]] = {}
        for k, size in enumerate(self.face_sizes):
            by_size.setdefault(size, []).append(k)
        for labels in by_size.values():
            prefix: dict[int, list[int]] = {}
            for k in labels:
                # prefix[k][d] is "some dart strictly below d carries label k".
                chain = [self.pool.id(f"pre_{k}_{d}") for d in range(self.dart_count + 1)]
                self.clauses.append([-chain[0]])
                for d in range(self.dart_count):
                    # chain[d + 1] <-> chain[d] or face(d, k)
                    self.clauses.append([-chain[d], chain[d + 1]])
                    self.clauses.append([-self.face(d, k), chain[d + 1]])
                    self.clauses.append([-chain[d + 1], chain[d], self.face(d, k)])
                prefix[k] = chain
            for position, k in enumerate(labels[1:], start=1):
                previous = labels[position - 1]
                for d in range(self.dart_count):
                    # The least dart of ``k`` comes after the least dart of
                    # ``previous``.
                    self.clauses.append([-self.face(d, k), prefix[previous][d]])

    def adjacent(self, u: int, v: int) -> int:
        left, right = (u, v) if u < v else (v, u)
        return self.pool.id(f"adj_{left}_{right}")

    def _define_adjacency(self) -> None:
        by_vertex_pair: dict[tuple[int, int], list[int]] = {}
        for (d, e), literal in self._pair_index.items():
            u, v = self.vertex_of[d], self.vertex_of[e]
            key = (u, v) if u < v else (v, u)
            by_vertex_pair.setdefault(key, []).append(literal)
        for (u, v), literals in by_vertex_pair.items():
            variable = self.adjacent(u, v)
            self.clauses.append([-variable] + literals)
            for literal in literals:
                self.clauses.append([-literal, variable])
        for u in range(self.vertex_count):
            for v in range(u + 1, self.vertex_count):
                if (u, v) not in by_vertex_pair:
                    self.clauses.append([-self.adjacent(u, v)])

    def _break_vertex_symmetry(self) -> None:
        """Partial lex-leader break over same-degree vertex transpositions.

        Swapping the dart blocks of two vertices of equal degree carries a
        model to a model: the blocks have equal length, ``sigma`` is preserved
        because each block stays cyclically ordered, and ``alpha`` and the face
        labels follow.  The transposition swaps the two adjacency rows and
        fixes every other entry, so requiring the adjacency matrix to be
        lexicographically at least its image under the transposition, in
        row-major order, selects one representative per orbit of the group
        generated by these adjacent transpositions.  It is a partial break --
        never claimed to be a complete canonical form.

        It is **off by default and ungated**.  An earlier draft compared only
        the two rows and dropped the coordinates the swap moves inside the
        earlier rows; those coordinates come first in row-major order, so that
        natural-looking constraint is *not* a valid lex-leader condition.  The
        version below is the corrected one, but "corrected by argument" is not
        the standard this repository accepts: there is as yet no executable
        control exhibiting a published APG relabelled to satisfy it.  Until
        that control exists, do not enable this for any run whose negative
        result would be reported.
        """

        self._define_adjacency()
        for v in range(self.vertex_count - 1):
            if self.degrees[v] != self.degrees[v + 1]:
                continue
            # The transposition also swaps the two columns inside every earlier
            # row, so those coordinates come first in row-major order and must
            # be compared before rows v and v+1.  Dropping them -- comparing
            # only the two rows -- is the natural-looking constraint and is
            # *not* a valid lex-leader condition.
            left: list[int] = []
            right: list[int] = []
            for u in range(v):
                left.extend((self.adjacent(u, v), self.adjacent(u, v + 1)))
                right.extend((self.adjacent(u, v + 1), self.adjacent(u, v)))
            for w in range(v + 2, self.vertex_count):
                left.append(self.adjacent(v, w))
                right.append(self.adjacent(v + 1, w))
            self._lex_at_least(left, right, tag=f"lex_{v}")

    def _lex_at_least(self, left: Sequence[int], right: Sequence[int], *, tag: str) -> None:
        """Assert ``left >=lex right`` with the standard equality-prefix chain."""

        # equal[i] means "the first i coordinates agree".
        equal = [self.pool.id(f"{tag}_eq_{i}") for i in range(len(left) + 1)]
        self.clauses.append([equal[0]])
        for i, (a, b) in enumerate(zip(left, right)):
            # equal[i] -> a >= b, i.e. not (a = 0 and b = 1).
            self.clauses.append([-equal[i], a, -b])
            # equal[i + 1] <-> equal[i] and a = b
            self.clauses.append([-equal[i + 1], equal[i]])
            self.clauses.append([-equal[i + 1], -a, b])
            self.clauses.append([-equal[i + 1], a, -b])
            self.clauses.append([equal[i + 1], -equal[i], a, b])
            self.clauses.append([equal[i + 1], -equal[i], -a, -b])

    def _fix_matching(self, alpha: Sequence[int]) -> None:
        if len(alpha) != self.dart_count:
            raise ValueError("fixed matching has the wrong dart count")
        for d, mate in enumerate(alpha):
            if d >= mate:
                continue
            literal = self.pair(d, mate)
            if literal is None:
                raise ValueError(f"fixed matching uses excluded pair ({d}, {mate})")
            self.clauses.append([literal])

    # ------------------------------------------------------------------ solving

    def alpha_from_model(self, model: set[int]) -> list[int]:
        alpha = [-1] * self.dart_count
        for (d, e), literal in self._pair_index.items():
            if literal in model:
                alpha[d] = e
                alpha[e] = d
        if any(mate < 0 for mate in alpha):
            raise ValueError("model did not assign a complete dart matching")
        return alpha

    def blocking_clause(self, alpha: Sequence[int]) -> list[int]:
        literals = []
        for d, mate in enumerate(alpha):
            if d < mate:
                literal = self.pair(d, mate)
                assert literal is not None
                literals.append(-literal)
        return literals

    def statistics(self) -> dict[str, int]:
        return {
            "darts": self.dart_count,
            "vertices": self.vertex_count,
            "faces": self.face_count,
            "matching_variables": len(self._pair_index),
            "variables": self.pool.top,
            "clauses": len(self.clauses),
        }


def environment_self_check(allow_darwin: bool = False) -> dict[str, str]:
    """the project rules section 11: heavy solver work never runs on the shared Mac."""

    record = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "node": platform.node(),
    }
    if record["system"] == "Darwin" and not allow_darwin:
        raise SystemExit(
            "STOP: refusing to run solver work on Darwin. Heavy compute belongs "
            "on an isolated Linux cloud worker (the project rules section 11)."
        )
    return record


def _solve_worker(clauses, outbox, inbox) -> None:
    """Run CaDiCaL in a child process so the time limit is a hard wall.

    pysat's CaDiCaL binding has no ``solve_limited``, and an in-process timer
    cannot interrupt it.  Enforcing the bound from the parent keeps the
    recorded ``INCOMPLETE`` disposition honest: it means the wall clock ran
    out, never that the solver reported anything.
    """

    solver = Cadical195(bootstrap_with=clauses)
    try:
        while True:
            if solver.solve() is False:
                outbox.put(("unsat", None))
                return
            outbox.put(("model", solver.get_model()))
            blocking = inbox.get()
            if blocking is None:
                return
            solver.add_clause(blocking)
    finally:
        solver.delete()


def search(
    order: int,
    r: int,
    *,
    timeout: float,
    certificate_directory: Path,
    max_models: int = 200,
    break_face_symmetry: bool = True,
    break_vertex_symmetry: bool = False,
) -> dict[str, Any]:
    import multiprocessing

    degrees, face_sizes = closed_profile(order, r)
    build_started = time.monotonic()
    encoding = ClosedMapCNF(
        degrees,
        face_sizes,
        break_face_symmetry=break_face_symmetry,
        break_vertex_symmetry=break_vertex_symmetry,
    )
    build_seconds = time.monotonic() - build_started

    record: dict[str, Any] = {
        "profile": {"order": order, "r": r},
        "encoding": "cnf-face-label-v1",
        "symmetry_breaks": {
            "face_labels": break_face_symmetry,
            "vertex_lex_leader": break_vertex_symmetry,
        },
        "build_seconds": round(build_seconds, 3),
        "statistics": encoding.statistics(),
        "timeout_seconds": timeout,
        "rejected_models": 0,
        "disposition": "INCOMPLETE",
        "reason": "timeout",
        "certificate": None,
        "verifiers": [],
        "nonexistence_claimed": False,
    }

    context = multiprocessing.get_context("fork")
    to_worker: Any = context.Queue()
    from_worker: Any = context.Queue()
    process = context.Process(
        target=_solve_worker, args=(encoding.clauses, from_worker, to_worker)
    )
    solve_started = time.monotonic()
    process.start()
    try:
        for _ in range(max_models):
            remaining = timeout - (time.monotonic() - solve_started)
            if remaining <= 0:
                break
            try:
                kind, payload = from_worker.get(timeout=remaining)
            except Exception:
                break
            if kind == "unsat":
                # Bounded-encoding unsat.  This encoding adds representation
                # conventions, so it is a statement about the encoding at this
                # profile and never a nonexistence theorem.
                record["disposition"] = "ENCODING_UNSAT"
                record["reason"] = "no model of this encoding at this profile"
                break
            alpha = encoding.alpha_from_model(set(payload))
            rotation = dump_rotation(degrees, alpha)
            certificate_directory.mkdir(parents=True, exist_ok=True)
            path = certificate_directory / f"apg_order{order}_r{r}.json"
            path.write_text(json.dumps(rotation, indent=2, sort_keys=True) + "\n")
            reports = run_verifiers(path, order)
            if all(report["passed"] for report in reports):
                record["disposition"] = "CERTIFIED"
                record["reason"] = "both independent verifiers passed"
                record["certificate"] = str(path)
                record["verifiers"] = reports
                break
            # The encoding does not state connectivity, so a disconnected map
            # of total genus one can satisfy it while failing Euler per
            # component.  Both verifiers reject those: block and continue
            # rather than trusting the solver.
            record["rejected_models"] += 1
            record["last_rejection"] = reports
            path.unlink(missing_ok=True)
            to_worker.put(encoding.blocking_clause(alpha))
        else:
            record["reason"] = f"model budget {max_models} exhausted"
    finally:
        record["solve_seconds"] = round(time.monotonic() - solve_started, 3)
        if process.is_alive():
            process.terminate()
        process.join(timeout=10)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--order", type=int, required=True)
    parser.add_argument("--r", type=int, action="append", help="repeatable; default is every feasible r")
    parser.add_argument("--timeout", type=float, default=600.0, help="seconds per profile")
    parser.add_argument("--certificates", type=Path, default=HERE / "results" / "cnf_candidates")
    parser.add_argument("--output", type=Path, help="write the JSON run record here")
    parser.add_argument("--no-face-symmetry-break", action="store_true")
    parser.add_argument(
        "--break-vertex-symmetry",
        action="store_true",
        help="ungated partial lex-leader break; see the method docstring before using it",
    )
    parser.add_argument("--allow-darwin", action="store_true", help="controls only; never for target compute")
    arguments = parser.parse_args()

    environment = environment_self_check(allow_darwin=arguments.allow_darwin)
    values = arguments.r if arguments.r else feasible_r_values(arguments.order)
    results = []
    for r in values:
        result = search(
            arguments.order,
            r,
            timeout=arguments.timeout,
            certificate_directory=arguments.certificates,
            break_face_symmetry=not arguments.no_face_symmetry_break,
            break_vertex_symmetry=arguments.break_vertex_symmetry,
        )
        results.append(result)
        print(
            f"order={arguments.order} r={r} -> {result['disposition']} "
            f"({result['solve_seconds']}s, {result['statistics']['clauses']} clauses)",
            flush=True,
        )
        if result["disposition"] == "CERTIFIED":
            break
    record = {
        "tool": "exact_map_cnf.py",
        "environment": environment,
        "order": arguments.order,
        "results": results,
        "nonexistence_claimed": False,
    }
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return 0 if any(item["disposition"] == "CERTIFIED" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
