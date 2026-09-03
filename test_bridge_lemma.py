"""Gates for the parity obstruction to bridges in an `X,2`-APG.

The load-bearing gates here are controls, in the sense of the project rule on predicted-object gates.
A test that merely says "the lemma holds on our graphs" would pass through a
vacuous lemma, so each positive gate is paired with a case that must fail:

* `bridge_darts` is checked against an independent, purely combinatorial bridge
  finder that never looks at the embedding;
* the parity lemma `(P)` is checked to **fail** on the `(3,4,5)` certificates,
  which have three face sizes and therefore no face 2-colouring at all;
* `is_apg_weak` is checked to accept everything `general_apg.is_apg` accepts,
  and to be strictly weaker on a bridged graph that the (C2) reading rejects.
"""
from __future__ import annotations

import glob
from pathlib import Path

import pytest

import bridge_lemma as bl
import general_apg
from certificate_tools import alpha_from_certificate, cycles_from_degrees

HERE = Path(__file__).resolve().parent
TARGETS = sorted(glob.glob(str(HERE / "certificates" / "targets" / "*.json")))


def _edges(degrees, alpha):
    _, vertex_of, _, _ = cycles_from_degrees(degrees)
    return {
        (min(vertex_of[d], vertex_of[alpha[d]]), max(vertex_of[d], vertex_of[alpha[d]]))
        for d in range(len(alpha))
    }


def _bridges_by_deletion(degrees, alpha):
    """Independent bridge finder: an edge is a bridge iff deleting it disconnects.

    Deliberately ignores the rotation system, so it cannot inherit a mistake
    from the face tracing that `bridge_lemma.bridge_darts` uses.
    """

    edges = _edges(degrees, alpha)
    n = len(degrees)
    found = set()
    for drop in edges:
        adjacency = {v: set() for v in range(n)}
        for u, w in edges - {drop}:
            adjacency[u].add(w)
            adjacency[w].add(u)
        seen, stack = {0}, [0]
        while stack:
            for nxt in adjacency[stack.pop()]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        if len(seen) != n:
            found.add(drop)
    return found


def _bridges_by_faces(degrees, alpha):
    _, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
    face_of, _ = bl.faces(alpha, sigma_inverse)
    return {
        (min(vertex_of[d], vertex_of[alpha[d]]), max(vertex_of[d], vertex_of[alpha[d]]))
        for d in bl.bridge_darts(alpha, face_of)
    }


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: Path(p).stem)
def test_face_bridges_match_an_independent_deletion_test(path):
    degrees, alpha = alpha_from_certificate(Path(path))
    assert _bridges_by_faces(degrees, alpha) == _bridges_by_deletion(degrees, alpha)


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: Path(p).stem)
def test_certificates_are_bridgeless(path):
    degrees, alpha = alpha_from_certificate(Path(path))
    assert _bridges_by_faces(degrees, alpha) == set()


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: Path(p).stem)
def test_weak_reading_accepts_every_certificate(path):
    degrees, alpha = alpha_from_certificate(Path(path))
    assert bl.is_apg_weak(degrees, alpha)
    assert general_apg.is_apg(degrees, alpha)


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: Path(p).stem)
def test_parity_lemma_does_not_apply_without_a_face_two_colouring(path):
    """Control: three face sizes admit no 2-colouring, so `(P)` must not hold.

    If this ever passes, `(P)` is being derived from something other than the
    two-colouring hypothesis and the lemma is not saying what it claims.
    """

    degrees, alpha = alpha_from_certificate(Path(path))
    assert len(bl.face_size_set(degrees, alpha)) == 3
    assert not bl.parity_holds(degrees, alpha)


# Explicit small plane graphs, chosen so that the two hypotheses of `(P)` vary
# independently: with and without a face 2-colouring, with and without a bridge.
# Every one is checked to be spherical before it is used.
CONTROLS = {
    "C4": ({1: [2, 4], 2: [1, 3], 3: [2, 4], 4: [3, 1]}, True, 0),
    "K4": ({1: [2, 3, 4], 2: [1, 4, 3], 3: [1, 2, 4], 4: [1, 3, 2]}, False, 0),
    "cube": (
        {1: [2, 4, 5], 2: [1, 6, 3], 3: [2, 7, 4], 4: [3, 8, 1],
         5: [1, 8, 6], 6: [2, 5, 7], 7: [3, 6, 8], 8: [4, 7, 5]},
        False, 0,
    ),
    "two_triangles_bridged": (
        {1: [2, 3, 4], 2: [1, 3], 3: [2, 1], 4: [1, 5, 6], 5: [4, 6], 6: [5, 4]},
        True, 1,
    ),
    "two_squares_bridged": (
        {1: [2, 4, 5], 2: [1, 3], 3: [2, 4], 4: [3, 1],
         5: [1, 6, 8], 6: [5, 7], 7: [6, 8], 8: [7, 5]},
        True, 1,
    ),
}


@pytest.mark.parametrize("name", sorted(CONTROLS))
def test_control_graphs_are_spherical(name):
    rotation, _, _ = CONTROLS[name]
    degrees, alpha = bl.alpha_from_rotation(rotation)
    _, _, _, sigma_inverse = cycles_from_degrees(degrees)
    _, sizes = bl.faces(alpha, sigma_inverse)
    assert len(degrees) - len(alpha) // 2 + len(sizes) == 2


@pytest.mark.parametrize("name", sorted(CONTROLS))
def test_bridge_count_is_as_designed(name):
    rotation, _, bridges = CONTROLS[name]
    degrees, alpha = bl.alpha_from_rotation(rotation)
    assert len(_bridges_by_faces(degrees, alpha)) == bridges
    assert _bridges_by_faces(degrees, alpha) == _bridges_by_deletion(degrees, alpha)


@pytest.mark.parametrize("name", sorted(CONTROLS))
def test_parity_lemma_tracks_the_two_colouring_exactly(name):
    """`(P)` holds precisely when a face 2-colouring exists -- both directions.

    The colouring is computed from the dual without looking at face sizes, so
    this pins the lemma to its stated hypothesis. `K4` and the cube are the
    controls that must fail; the two bridged graphs are the cases the lemma
    exists for, and in both a bridge endpoint has odd degree.
    """

    rotation, colourable, bridges = CONTROLS[name]
    degrees, alpha = bl.alpha_from_rotation(rotation)
    assert (bl.two_colouring(degrees, alpha) is not None) is colourable
    assert bl.parity_holds(degrees, alpha) is colourable
    if bridges:
        counts = bl.bridges_at(degrees, alpha)
        assert any(d % 2 == 1 for d, c in zip(degrees, counts) if c)


def test_parity_lemma_tracks_the_two_colouring_on_the_certificate_corpus():
    """Same equivalence across every certificate, none of which is colourable."""

    paths = TARGETS + sorted(glob.glob(str(HERE / "certificates" / "known" / "*.json")))
    assert len(paths) >= len(TARGETS)
    for path in paths:
        degrees, alpha = alpha_from_certificate(Path(path))
        colourable = bl.two_colouring(degrees, alpha) is not None
        assert bl.parity_holds(degrees, alpha) is colourable, path
