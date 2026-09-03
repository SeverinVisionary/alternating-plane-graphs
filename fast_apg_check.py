#!/usr/bin/env python3
"""A third, dart-side implementation of the (3,4,5)-APG check.

Lifted out of ``test_exact_map_cnf.py`` so the definition-of-done gate can
actually run it: the handoff claimed a third checker had accepted all 26
certificates, but nothing outside the SAT-lane test suite -- which needs
``python-sat`` -- ever called it.  Standard library only.
"""
from __future__ import annotations

from pathlib import Path

from certificate_tools import alpha_from_certificate, cycles_from_degrees

ALLOWED = frozenset({3, 4, 5})


def is_apg(degrees: list[int], alpha: list[int]) -> bool:
    """Decide whether ``(degrees, alpha)`` is a closed (3,4,5)-APG.

    A third implementation of the certificate check, written for the mutation
    search before either verifier existed and never derived from them.  It
    works on darts and a fixed-point-free involution rather than on the
    certificate's adjacency rows, so it shares no parsing, no traversal code
    and no data layout with `verify.py` or `verify_darts.py` -- but it is still
    the same *mathematics*: trace faces from the rotation, count, compare.
    Three implementations catch three ways of coding it wrong; none of them
    catches a shared misreading of the definition.
    """

    # Definition 3.1 restricts degrees and face sizes to {3,4,5}.  This check
    # was missing until 2026-09-01: the function relied on
    # `sorted(sizes) == sorted(degrees)` below, which is Theorem 3.2 -- a
    # *consequence* for graphs already known to be in the class, not a test of
    # membership.  It therefore accepted alternating plane graphs with a
    # degree-6 vertex and a 6-face whenever the two multisets happened to
    # coincide, which they do for three of the five APGs on 19 vertices.
    if any(degree not in ALLOWED for degree in degrees):
        return False
    cycles, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
    edge_count: dict[tuple[int, int], int] = {}
    for dart, mate in enumerate(alpha):
        u, v = vertex_of[dart], vertex_of[mate]
        if u == v or degrees[u] == degrees[v]:
            return False
        if dart < mate:
            key = (min(u, v), max(u, v))
            edge_count[key] = edge_count.get(key, 0) + 1
            if edge_count[key] > 1:
                return False

    phi = [sigma_inverse[alpha[dart]] for dart in range(len(alpha))]
    face_of: dict[int, int] = {}
    faces: list[list[int]] = []
    for dart in range(len(alpha)):
        if dart in face_of:
            continue
        walk, cursor = [], dart
        while cursor not in face_of:
            face_of[cursor] = len(faces)
            walk.append(cursor)
            cursor = phi[cursor]
        faces.append(walk)
    sizes = [len(face) for face in faces]
    if any(size not in ALLOWED for size in sizes):
        return False
    if sorted(sizes) != sorted(degrees):
        return False
    for face in faces:
        corners = [vertex_of[dart] for dart in face]
        if len(set(corners)) != len(corners):
            return False
    for dart, mate in enumerate(alpha):
        if sizes[face_of[dart]] == sizes[face_of[mate]]:
            return False

    reached = {0}
    stack = [0]
    while stack:
        vertex = stack.pop()
        for dart in cycles[vertex]:
            other = vertex_of[alpha[dart]]
            if other not in reached:
                reached.add(other)
                stack.append(other)
    if len(reached) != len(degrees):
        return False
    return len(degrees) - len(alpha) // 2 + len(faces) == 2


def accepts_certificate(path: Path) -> bool:
    """Run the dart-side check straight off a certificate file."""

    degrees, alpha = alpha_from_certificate(Path(path))
    return is_apg(degrees, alpha)
