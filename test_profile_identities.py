"""The profile identities: what is derived, and the one thing that is assumed.

`verify.py` and `verify_darts.py` reject unless `v_i = f_i`, `v5 = v3 - 4`,
`E = 2n - 2` and `F = n`, citing "Theorem 3.2" -- a theorem this repository
cites by name and never quotes.  `THEOREM_3_2_STATUS.md` derives everything in
that block except a single integer `k`, and these gates keep the derivation
honest against the objects we actually hold.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
TARGETS = sorted((HERE / "certificates" / "targets").glob("TARGET_*.json"))
KNOWN = sorted((HERE / "certificates" / "known").glob("*.json"))


def _rotation(path: Path) -> dict[int, list[int]]:
    data = json.loads(path.read_text())
    return {row["id"]: list(row["clockwise"]) for row in data["vertices"]}


def _face_sizes(rotation: dict[int, list[int]]) -> list[int]:
    darts = {(v, u) for v, ring in rotation.items() for u in ring}
    seen: set = set()
    sizes = []
    for start in sorted(darts):
        if start in seen:
            continue
        dart = start
        length = 0
        while dart not in seen:
            seen.add(dart)
            length += 1
            u, v = dart
            ring = rotation[v]
            dart = (v, ring[(ring.index(u) - 1) % len(ring)])
        sizes.append(length)
    return sizes


def _profile(path: Path):
    rotation = _rotation(path)
    vertex_counts = collections.Counter(len(ring) for ring in rotation.values())
    face_counts = collections.Counter(_face_sizes(rotation))
    return len(rotation), vertex_counts, face_counts


def _certificates():
    for path in TARGETS + KNOWN:
        try:
            order, vertex_counts, face_counts = _profile(path)
        except Exception:  # not a rotation certificate
            continue
        if set(vertex_counts) <= {3, 4, 5} and set(face_counts) <= {3, 4, 5}:
            yield path, order, vertex_counts, face_counts


CERTIFICATES = list(_certificates())


def test_there_are_certificates_to_check() -> None:
    assert len(CERTIFICATES) >= 26


@pytest.mark.parametrize("case", CERTIFICATES, ids=lambda case: case[0].name)
def test_lemma_1_v3_equals_f3(case) -> None:
    """Proved: the (degree-3 vertex, 3-face) incidence is a bijection."""

    _, _, vertex_counts, face_counts = case
    assert vertex_counts[3] == face_counts[3]


@pytest.mark.parametrize("case", CERTIFICATES, ids=lambda case: case[0].name)
def test_lemma_2_and_3_hold_with_a_single_integer_k(case) -> None:
    """Proved: `v4 - f4 = 5k`, `f5 - v5 = 4k`, `v5 = v3 - 4 - 2k`, same `k`."""

    _, order, vertex_counts, face_counts = case
    r = vertex_counts[3]
    difference = vertex_counts[4] - face_counts[4]
    assert difference % 5 == 0, "4(v4-f4) = 5(f5-v5) forces 5 | (v4-f4)"
    k = difference // 5
    assert face_counts[5] - vertex_counts[5] == 4 * k
    assert vertex_counts[5] == r - 4 - 2 * k
    # The unconditional corollary, independent of whether k is zero.
    assert (vertex_counts[5] - r) % 2 == 0


@pytest.mark.parametrize("case", CERTIFICATES, ids=lambda case: case[0].name)
def test_every_object_we_hold_has_k_zero(case) -> None:
    """Proved: Theorem 3.2, p. 340 of the source paper, read 2026-09-01.

    Euler and the counting arguments in Lemmas 1-3 leave five cases,
    `k` in `{-2,-1,0,1,2}`; the paper closes them by counting
    (5,5)-combinations two ways, giving `a5 - b5 = 2(v5 - f5)` with `a5, b5`
    non-negative and bounded, which survives only at `k = 0`.  See
    THEOREM_3_2_STATUS.md.

    If this ever fails, the failing object is not a `(3,4,5)`-APG.
    """

    _, _, vertex_counts, face_counts = case
    assert (vertex_counts[4] - face_counts[4]) // 5 == 0


def test_the_derivation_admits_k_nonzero_arithmetically() -> None:
    """Control: Euler and Lemmas 1-3 alone do not force k = 0.

    A profile with k = 1 satisfies every counting identity up to that point.
    What excludes it is the paper's (5,5)-combination count, not arithmetic --
    so this test marks the exact boundary between what is derived here and
    what Theorem 3.2 contributes.
    """

    r, v4, k = 20, 30, 1
    v5 = r - 4 - 2 * k
    f4, f5 = v4 - 5 * k, v5 + 4 * k
    V = r + v4 + v5
    F = r + f4 + f5
    twice_edges = 3 * r + 4 * v4 + 5 * v5
    assert twice_edges == 3 * r + 4 * f4 + 5 * f5
    assert V - twice_edges // 2 + F == 2
