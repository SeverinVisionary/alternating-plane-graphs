"""Gates for the counting proof of Conjecture 10.1.

The argument in `conjecture_10_1.py` is four lines of counting for a conjecture
that stood for eleven years, so the burden here is to make each step falsifiable
rather than to restate it.  Three kinds of gate:

* the arithmetic, over a wide range rather than the one case that matters;
* the standard facts the proof leans on, checked on real graphs -- bipartite
  plane graphs have even faces, and a plane graph's dual is bipartite exactly
  when the graph is Eulerian;
* the conclusion, against every alternating plane graph this repository holds:
  none may have only two distinct degrees or only two distinct face sizes.
"""
from __future__ import annotations

import collections
from fractions import Fraction

import pytest

import conjecture_10_1 as c101
import connectivity as cn
import import_planar_code as ipc
import witness_coverage as wc


def _rotation(name: str):
    """Load a scanned witness, which may be JSON or planar code."""

    path = wc.HERE / name
    if path.suffix == ".plc":
        return {index + 1: ring for index, ring in enumerate(ipc.decode_first(path))}
    return cn.load_rotation(path)


# --------------------------------------------------------------------------
# The arithmetic


def test_no_degree_or_face_pair_survives_the_counting_bound() -> None:
    assert c101.surviving_pairs(bound=200) == []


def test_the_only_tight_pair_is_three_four_and_it_fails_by_eulers_two() -> None:
    """Where the argument is tight, and why it still closes.

    The pair here is the *degree* pair (3,4), giving `v = 7e/12`; the face bound
    `f <= 5e/12` comes separately from face sizes 4 and 6.  Equality in the sum
    needs both at once, and even then Euler's `v + f = e + 2` fails by 2.
    """

    assert c101.tight_pair() == (3, 4)
    assert c101.share(3, 4) + c101.EVEN_DISTINCT == c101.EDGE_BUDGET
    assert c101.is_impossible(3, 4)


def test_the_two_sides_are_the_papers_own_inequality() -> None:
    """`(9.4)`: each edge lies between an r-face and an s-face, 4 <= r < s."""

    assert c101.EVEN_DISTINCT == Fraction(1, 4) + Fraction(1, 6) == Fraction(5, 12)
    assert c101.UNRESTRICTED == Fraction(1, 3) + Fraction(1, 4) == Fraction(7, 12)


def test_every_edge_contributes_at_most_one_and_euler_needs_more() -> None:
    """The whole proof, as one inequality applied to both halves.

    `v + f` is a sum over edges of four reciprocals, and Euler makes that total
    `e + 2`, so some edge must contribute more than 1.  Neither half allows it.
    """

    # Half one: degrees (3,4) unconstrained, face sizes even and distinct (4,6).
    assert c101.edge_contribution((3, 4), (4, 6)) == c101.EDGE_BUDGET
    # Half two: face sizes (3,4) unconstrained, degrees even and distinct (4,6).
    assert c101.edge_contribution((4, 6), (3, 4)) == c101.EDGE_BUDGET
    # Any other admissible combination is strictly smaller.
    assert c101.edge_contribution((3, 5), (4, 6)) < c101.EDGE_BUDGET
    assert c101.edge_contribution((4, 5), (4, 6)) < c101.EDGE_BUDGET


def test_the_chain_reproduces_lemma_9_2_exactly() -> None:
    """Calibration against a result the paper proves, on the weak class.

    Lemma 9.2 (pp. 357-358): no weak alternating plane graph has degrees 2 and
    k for k >= 12.  The same chain must exclude exactly that range -- and must
    NOT exclude k <= 10, for which the paper exhibits weak 2,k-APGs (Table 5,
    Figures 8-9).  It shows the contradiction turns on `d1 >= 3` rather than on
    an over-count that would also have killed the small-k weak graphs.

    It is NOT a proof that every step is right: a spuriously stronger bound such
    as 5/12 - 1/1000 passes the same test, as the companion gate shows.
    """

    assert [k for k in range(3, 40) if c101.excluded_weak_two_k(k)] == list(range(12, 40))
    for k in range(3, 11):
        assert not c101.excluded_weak_two_k(k), f"would contradict the paper at k={k}"
    # k = 11 is left open by this chain; the paper needs Lemma 9.4 for it.
    assert not c101.excluded_weak_two_k(11)


def test_the_calibration_cannot_detect_a_spurious_strengthening() -> None:
    """The limit of the calibration, gated so the write-up cannot overclaim."""

    spurious = c101.EVEN_DISTINCT - Fraction(1, 1000)
    excluded = [k for k in range(3, 40)
                if c101.share(2, k) + spurious <= c101.EDGE_BUDGET]
    assert excluded == list(range(12, 40)), "a wrong bound passes calibration too"


def test_the_bound_is_not_vacuous() -> None:
    """The face bound is load-bearing: without it, degree pairs survive.

    Dropping `(9.5)` to the naive `f <= e/2` (faces of size at least 4, ignoring
    that two 4-faces cannot be adjacent) lets (3,4) and (3,5) through.
    """

    naive = Fraction(1, 2)
    for pair in ((3, 4), (3, 5)):
        # Survives the naive cap: faces at least 4 on both sides of every edge.
        assert c101.share(*pair) + naive > c101.EDGE_BUDGET
        # Dies once adjacent faces must have *distinct* even sizes, 4 and 6.
        assert c101.is_impossible(*pair)


@pytest.mark.parametrize("a,b", [(3, 4), (3, 5), (3, 100), (4, 5), (10, 11)])
def test_every_named_pair_is_excluded(a: int, b: int) -> None:
    assert c101.is_impossible(a, b)


# --------------------------------------------------------------------------
# The standard facts, on real graphs


def _degree_classes(rotation) -> int:
    return len({len(ring) for ring in rotation.values()})


def _face_classes(rotation) -> int:
    return len({len(walk) for walk in cn.faces(rotation)})


def test_a_bipartite_plane_graph_has_only_even_faces() -> None:
    """Step 2 of half one, on the cube -- bipartite, all faces size 4."""

    cube = {
        0: [1, 3, 4], 1: [0, 5, 2], 2: [1, 6, 3], 3: [2, 7, 0],
        4: [0, 7, 5], 5: [4, 6, 1], 6: [5, 7, 2], 7: [6, 4, 3],
    }
    assert all(len(walk) % 2 == 0 for walk in cn.faces(cube))


def test_the_dual_is_bipartite_exactly_when_the_graph_is_eulerian() -> None:
    """Step 2 of half two, on the octahedron (Eulerian) and the cube (not)."""

    octahedron = {
        0: [1, 2, 3, 4], 1: [0, 4, 5, 2], 2: [0, 1, 5, 3],
        3: [0, 2, 5, 4], 4: [0, 3, 5, 1], 5: [1, 4, 3, 2],
    }
    assert all(len(ring) % 2 == 0 for ring in octahedron.values())
    # Its dual is the cube, which is bipartite; face sizes are all 3 here, so
    # the octahedron is not itself an APG -- only the standard fact is at issue.
    assert {len(walk) for walk in cn.faces(octahedron)} == {3}


# --------------------------------------------------------------------------
# The conclusion, against every graph held here


def test_no_stored_alternating_plane_graph_has_only_two_degree_classes() -> None:
    rows = wc.witnesses()
    assert rows
    for order, entries in rows.items():
        for name, _ in entries:
            rotation = _rotation(name)
            assert _degree_classes(rotation) != 2, f"{name} would refute 10.1"


def test_no_stored_alternating_plane_graph_has_only_two_face_classes() -> None:
    rows = wc.witnesses()
    for order, entries in rows.items():
        for name, _ in entries:
            rotation = _rotation(name)
            assert _face_classes(rotation) != 2, f"{name} would refute 10.1"


def test_the_counterexample_graph_is_checked_too() -> None:
    """It refutes a different claim; it must not refute this one."""

    rotation = cn.load_rotation(
        wc.HERE / "certificates" / "counterexamples" / "APG46_two_cut.json"
    )
    assert _degree_classes(rotation) == 3
    assert _face_classes(rotation) == 3


def test_the_scan_actually_looked_at_something() -> None:
    counts = collections.Counter(
        _degree_classes(_rotation(name))
        for entries in wc.witnesses().values()
        for name, _ in entries
    )
    assert sum(counts.values()) > 40
    assert min(counts) >= 3


# --- The weak-reading closure of half two -------------------------------------
#
# These gate the argument that removes (C2) as a hypothesis.  The controls
# matter more than the positive checks: a bound that is merely asserted, or a
# count that would close for any numbers at all, would prove nothing.

def test_step_one_bounds_are_the_exhaustive_maxima():
    """Each class bound must be the true maximum over its class, not a guess.

    Searched directly over degrees and face sizes rather than read off the
    docstring.  `1/x` is decreasing so a small window is exhaustive.
    """

    from fractions import Fraction as F
    import conjecture_10_1 as c

    degrees, sizes = range(3, 14), range(3, 24)

    def worst(deg_ok, side_ok):
        return max(
            F(1, a) + F(1, b) + F(1, p) + F(1, q)
            for a in degrees for b in degrees if deg_ok(a, b)
            for p in sizes for q in sizes if side_ok(p, q)
        )

    big = c.BRIDGE_FACE_MIN
    assert worst(lambda a, b: a != b,
                 lambda p, q: p == q and p >= big) - 1 == c.bridge_excess()
    assert worst(lambda a, b: a != b and a >= 4 and b >= 4,
                 lambda p, q: p != q and max(p, q) >= big) - 1 == c.heavy_edge_excess()
    assert worst(lambda a, b: a != b and (a == 3 or b == 3),
                 lambda p, q: p != q and max(p, q) >= big) - 1 == c.light_edge_excess()


def test_only_the_degree_three_class_can_be_positive():
    import conjecture_10_1 as c

    assert c.bridge_excess() < 0
    assert c.heavy_edge_excess() < 0
    assert c.light_edge_excess() > 0


def test_the_count_closes_at_every_bridge_count():
    import conjecture_10_1 as c
    from fractions import Fraction

    for bridges in range(1, 2000):
        assert c.bridged_case_is_impossible(bridges)
        assert c.closing_bound(bridges) == Fraction(-bridges, 12)
    assert c.bridgeless_case_is_impossible()


def test_the_sharp_tether_is_two_not_four():
    """Condition (c) makes a bridge's two ends differ in degree.

    So at most one end has degree 3, and only that end can carry positive
    edges. An adversarial review of the first version of this argument found it
    had used the loose bound of four.
    """

    import conjecture_10_1 as c

    assert c.POSITIVE_EDGES_PER_BRIDGE == 2
    assert c.LOOSE_POSITIVE_EDGES_PER_BRIDGE == 4
    assert c.closing_bound(1) < 0
    assert c.closing_bound(1, per_bridge=c.LOOSE_POSITIVE_EDGES_PER_BRIDGE) == 0


def test_the_closure_fails_if_the_tether_is_loosened_far_enough():
    """Control: the argument must depend on the tether, not hold regardless.

    Both 2 and 4 close, 4 only just. At five per bridge the bound turns
    positive and proves nothing, which is what makes Step 2 the substance.
    """

    import conjecture_10_1 as c
    from fractions import Fraction

    assert c.closing_bound(1, per_bridge=5) > 0
    assert c.closing_bound(1000, per_bridge=5) > Fraction(2)


def test_the_closure_depends_on_a_bridge_face_bound_but_not_on_eight():
    """Control, and a measure of how much room Step 0 leaves.

    Step 0 gives `s2 >= 8`. The count survives `s2 >= 7`, so the bound is not
    needed at full strength; it fails at `s2 >= 6`, so some bound is
    indispensable.
    """

    import conjecture_10_1 as c

    assert c.closing_bound(1, face_min=8) < 0
    assert c.closing_bound(1, face_min=7) < 0
    assert c.closing_bound(1, face_min=6) > 0
    assert c.closing_bound(1, face_min=4) > 0


def test_half_one_also_closes_under_the_weak_reading():
    """The `2,Y` half without (C2), directly rather than via a leaf block.

    An earlier argument went through a leaf block of the bridge tree and was
    wrong: the attachment vertex loses its bridge inside the block, so a
    degree-3 attachment vertex has degree 2 there and the vertex bound fails.
    Bipartiteness plus Step 0 settle it with no decomposition.
    """

    from fractions import Fraction
    import conjecture_10_1 as c

    bridge = c.share(3, 4) + Fraction(2, c.BRIDGE_FACE_MIN)
    non_bridge = c.share(3, 4) + c.share(4, 6)
    assert bridge <= c.EDGE_BUDGET
    assert non_bridge <= c.EDGE_BUDGET
    assert bridge == Fraction(5, 6)
    assert non_bridge == Fraction(1)


def test_half_one_weak_reading_control_the_bridge_face_bound_is_needed():
    """Control: with no lower bound on the bridge face the bridge edge exceeds 1."""

    from fractions import Fraction
    import conjecture_10_1 as c

    assert c.share(3, 4) + Fraction(2, 4) > c.EDGE_BUDGET
