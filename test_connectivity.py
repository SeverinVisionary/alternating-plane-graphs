"""Gates for the 3-connectivity work behind Conjecture 10.3.

Conjecture 10.3 of the primary paper is a *different* conjecture from 10.2: it
asks for a 3-connected alternating plane graph on every order from 19 up, over
the full APG class rather than the `(3,4,5)` subclass.  A settled 10.2 only
helps if the graphs it produces are 3-connected, which is a fact about them and
has to be checked.

Three things are gated here.  That the connectivity code is right (a brute
force, a face-local reduction, and a graph with a real 2-cut to catch a
reduction that reports nothing).  That every `(3,4,5)`-APG this repository
holds -- 26 target certificates, 23 published planar-code graphs, and members
of the spliced family -- is 3-connected.  And the arithmetic of what that
leaves open, so the residue cannot quietly shrink.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import connectivity as cn
import fast_apg_check
import import_planar_code as ipc
import pumping_splice as ps
import witness_coverage as wc

HERE = Path(__file__).resolve().parent
TARGETS = HERE / "certificates" / "targets"
CENSUS = HERE / "certificates" / "census_sources"
UPSTREAM = HERE / "certificates" / "known" / "upstream"

TARGET_ORDERS = ps.TARGET_ORDERS

# A theta graph: three internally disjoint u-v paths.  `{u, v}` is a genuine
# 2-cut, and it sits non-consecutively on all three faces.
THETA = {0: [2, 3, 4], 1: [2, 4, 3], 2: [0, 1], 3: [0, 1], 4: [0, 1]}
# The 3-cube, 3-connected, as a control in the other direction.
CUBE = {
    0: [1, 3, 4], 1: [0, 5, 2], 2: [1, 6, 3], 3: [2, 7, 0],
    4: [0, 7, 5], 5: [4, 6, 1], 6: [5, 7, 2], 7: [6, 4, 3],
}


def _planar_code(path: Path) -> dict[int, list[int]]:
    return {index + 1: ring for index, ring in enumerate(ipc.decode_first(path))}


# --------------------------------------------------------------------------
# The connectivity code itself


def test_the_theta_graph_is_not_three_connected() -> None:
    assert not cn.is_three_connected(THETA)
    assert cn.separating_pairs_on_faces(THETA) == [(0, 1)]


def test_the_cube_is_three_connected() -> None:
    assert cn.is_three_connected(CUBE)
    assert cn.separating_pairs_on_faces(CUBE) == []


@pytest.mark.parametrize("order", TARGET_ORDERS)
def test_the_face_local_reduction_agrees_with_brute_force(order: int) -> None:
    """The reduction is a lemma, so it must never be the only thing consulted."""

    rotation = cn.load_rotation(TARGETS / f"TARGET_{order}.json")
    assert cn.is_three_connected(rotation) == (
        not cn.separating_pairs_on_faces(rotation)
    )


def test_the_reduction_would_notice_a_separating_pair_it_was_handed() -> None:
    """Control against a reduction that silently generates no candidates."""

    candidates = set()
    for walk in cn.faces(THETA):
        size = len(walk)
        for i in range(size):
            for j in range(i + 1, size):
                if (j - i) % size not in (1, size - 1):
                    candidates.add(tuple(sorted((walk[i], walk[j]))))
    assert (0, 1) in candidates


# --------------------------------------------------------------------------
# What is 3-connected


@pytest.mark.parametrize("order", TARGET_ORDERS)
def test_every_target_certificate_is_three_connected(order: int) -> None:
    assert cn.is_three_connected(cn.load_rotation(TARGETS / f"TARGET_{order}.json"))


@pytest.mark.parametrize(
    "path", sorted(CENSUS.glob("*.plc")) + sorted(UPSTREAM.glob("*.plc")),
    ids=lambda p: p.name,
)
def test_every_published_witness_is_three_connected(path: Path) -> None:
    assert cn.is_three_connected(_planar_code(path))


@pytest.mark.parametrize("base,delta", [(90, 0), (90, 4), (109, 0), (109, 4), (110, 0), (110, 4)])
def test_members_of_the_spliced_family_are_three_connected(base: int, delta: int) -> None:
    assert cn.is_three_connected(ps.splice(base, delta))


# --------------------------------------------------------------------------
# What that leaves open


def test_the_three_connected_orders_and_the_residue() -> None:
    """The bookkeeping for Conjecture 10.3, derived from files, not asserted.

    History worth keeping, because each step was a real miss.  The first version
    scanned two directories and hard-coded the answer, missing
    `certificates/search_seeds/` -- published witnesses at 21, 22, 23, 25 -- and
    reported fourteen orders when it was ten.  Seven more fell to Section-8
    closures built from blocks already on disk, and 37 and 38 to disk surgery on
    graphs already on disk.  Only order 19 is left, and only because no
    (3,4,5)-APG exists there at all.
    """

    assert wc.residue() == []
    # 19 is covered, but never from the (3,4,5) subclass: no (3,4,5)-APG exists
    # on 18 or 19 vertices, so its witnesses are general alternating plane
    # graphs.  `test_conjecture_10_3.py` checks that distinction directly.
    assert 19 in wc.stored_orders()


def test_every_stored_witness_is_three_connected() -> None:
    """Every *witness* is; the class as a whole is not -- see the next test."""

    rows = wc.witnesses()
    assert rows, "no witnesses found; the scan is broken, not the repository"
    bad = [name for order in rows for name, ok in rows[order] if not ok]
    assert bad == []


def test_the_order_46_counterexample_is_a_valid_apg_that_is_not_three_connected() -> None:
    """The claim "every (3,4,5)-APG is 3-connected" is FALSE, and this is why.

    Verified here independently of the reviewer that produced it: all three checkers
    accept it, and brute force over all pairs rejects 3-connectivity.
    """

    path = HERE / "certificates" / "counterexamples" / "APG46_two_cut.json"
    assert fast_apg_check.accepts_certificate(path)
    rotation = cn.load_rotation(path)
    assert len(rotation) == 46
    assert not cn.is_three_connected(rotation)
    assert cn.separating_pairs_on_faces(rotation) == [(1, 2)]
    # Non-adjacent, both degree five, two components of 22 -- the open case of
    # THREE_CONNECTIVITY_CLAIM.md, not Case A or Case B, which stay proved.
    graph = cn.adjacency(rotation)
    assert 2 not in graph[1]
    assert len(graph[1]) == len(graph[2]) == 5
    rest = {v: graph[v] - {1, 2} for v in graph if v not in (1, 2)}
    seen, parts = set(), []
    for start in rest:
        if start in seen:
            continue
        stack, part = [start], set()
        while stack:
            vertex = stack.pop()
            if vertex in part:
                continue
            part.add(vertex)
            seen.add(vertex)
            stack.extend(rest[vertex] - part)
        parts.append(part)
    assert sorted(len(part) for part in parts) == [22, 22]
    # Both cut vertices have at least two neighbours on each side, so this is
    # neither Case A (one neighbour) nor Case B (two arcs of length two).
    assert sorted(len(graph[1] & part) for part in parts) == [2, 3]
    assert sorted(len(graph[2] & part) for part in parts) == [2, 3]


def test_the_counterexample_is_never_counted_as_a_witness() -> None:
    """It is a valid (3,4,5)-APG at order 46; coverage must not pick it up."""

    names = [name for rows in wc.witnesses().values() for name, _ in rows]
    assert not any("counterexample" in name for name in names)
    assert "APG46_two_cut.json" in wc.counterexamples()


def test_the_scan_finds_the_directories_that_were_missed() -> None:
    """Control against the scan silently narrowing again."""

    names = [name for rows in wc.witnesses().values() for name, _ in rows]
    for marker in ("search_seeds", "census_sources", "known", "targets"):
        assert any(marker in name for name in names), marker
    assert {21, 22, 23, 25} <= wc.stored_orders()
