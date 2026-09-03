"""Certificate-side helpers, standard library only.

These three helpers are what the definition-of-done gate
(``test_target_certificates.py``) needs, and they carry no solver dependency:
the certificates are checked by ``verify.py`` and ``verify_darts.py``, neither
of which imports anything outside the standard library either.  They live here
rather than in ``exact_map_cnf`` so that a checkout without ``python-sat`` can
still run the gate that the whole claim rests on -- which is what
``README.md`` promises and what a reviewer will try first.

``exact_map_cnf`` re-exports all three, so the CNF lane keeps its old names.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

HERE = Path(__file__).resolve().parent

def cycles_from_degrees(degrees: Sequence[int]) -> tuple[list[list[int]], list[int], list[int], list[int]]:
    """Fixed vertex slots: darts are grouped per vertex in a fixed cyclic order.

    This is a labelling convention, not a restriction: every rotation system on
    this degree multiset admits such a labelling.
    """

    cycles: list[list[int]] = []
    vertex_of: list[int] = []
    for vertex, degree in enumerate(degrees):
        cycle = list(range(len(vertex_of), len(vertex_of) + degree))
        cycles.append(cycle)
        vertex_of.extend([vertex] * degree)
    sigma = [0] * len(vertex_of)
    sigma_inverse = [0] * len(vertex_of)
    for cycle in cycles:
        for index, dart in enumerate(cycle):
            sigma[dart] = cycle[(index + 1) % len(cycle)]
            sigma_inverse[dart] = cycle[(index - 1) % len(cycle)]
    return cycles, vertex_of, sigma, sigma_inverse


def alpha_from_certificate(path: Path) -> tuple[list[int], list[int]]:
    """Re-embed a certificate into the shared dart slots.

    Returns ``(degrees, alpha)``.  Vertices are re-labelled into the fixed
    degree-sorted slots and each vertex keeps the certificate's clockwise
    order, so the result is the same plane map in this convention.
    """

    data = json.loads(path.read_text())
    rotation = {row["id"]: list(row["clockwise"]) for row in data["vertices"]}
    degree_of = {vertex: len(row) for vertex, row in rotation.items()}
    slots = sorted(rotation, key=lambda vertex: (degree_of[vertex], vertex))
    relabel = {vertex: index for index, vertex in enumerate(slots)}
    degrees = [degree_of[vertex] for vertex in slots]
    cycles, _, _, _ = cycles_from_degrees(degrees)
    alpha = [-1] * sum(degrees)
    for index, vertex in enumerate(slots):
        for position, neighbour in enumerate(rotation[vertex]):
            other = relabel[neighbour]
            back = rotation[neighbour].index(vertex)
            alpha[cycles[index][position]] = cycles[other][back]
    if any(mate < 0 for mate in alpha) or any(alpha[alpha[d]] != d for d in range(len(alpha))):
        raise ValueError(f"{path} is not a symmetric rotation system")
    return degrees, alpha


def run_verifiers(certificate: Path, order: int) -> list[dict[str, object]]:
    """Run both independent checkers in fresh processes."""

    reports = []
    for checker, arguments in (
        ("verify.py", ["--expect-order", str(order), str(certificate)]),
        ("verify_darts.py", ["--expect-order", str(order), str(certificate)]),
    ):
        completed = subprocess.run(
            [sys.executable, str(HERE / checker), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        reports.append(
            {
                "checker": checker,
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
                "passed": completed.returncode == 0,
            }
        )
    return reports
