"""Gates for the order-37 and order-38 witnesses, and for a checker defect.

These two orders were the last `(3,4,5)` orders Conjecture 10.3 was missing:
out of reach of the Section-8 arithmetic (34 and 35 are not sums of
18, 19, 20, 21) and not held anywhere in this repository.  They are closed by
disk surgery on graphs that *were* held.

The same session found a real defect in `fast_apg_check.is_apg`, which is one of
the three checkers the certificate gate leans on.  It never tested that degrees
and face sizes lie in `{3,4,5}` -- it relied on `sorted(sizes) == sorted(degrees)`,
which is Theorem 3.2, a consequence for graphs already known to be in the class
rather than a test of membership.  So it accepted alternating plane graphs with a
degree-6 vertex and a 6-face whenever the two multisets coincided.  The
regression fixture below is such a graph.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import connectivity as cn
import fast_apg_check
import general_apg
import verify
import verify_darts
from certificate_tools import alpha_from_certificate

HERE = Path(__file__).resolve().parent
SURGERY = HERE / "certificates" / "surgery"

WITNESSES = {"APG37_3conn.json": 37, "APG38_3conn.json": 38, "APG38_3conn_b.json": 38}

# An alternating plane graph on 19 vertices with a degree-6 vertex and a 6-face,
# so it is NOT a (3,4,5)-APG; its degree and face-size multisets coincide, which
# is exactly what the old `fast_apg_check` mistook for membership.
# Provenance: decoded during an independent review from Althofer's public table.
# The graph itself is not redistributed here -- only this inline rotation, which
# is a re-expression in this repository's own convention. It exists solely as a
# regression fixture for the membership check.
DEGREE_SIX_APG = {
    1: [2, 3, 4, 5, 6], 2: [1, 7, 8, 3], 3: [1, 2, 9], 4: [1, 10, 11],
    5: [1, 11, 6], 6: [1, 5, 12, 13], 7: [2, 13, 14, 15, 8], 8: [2, 7, 9],
    9: [3, 8, 16, 10], 10: [4, 9, 16, 17, 18, 11], 11: [4, 10, 19, 5],
    12: [6, 19, 18, 14, 13], 13: [6, 12, 7], 14: [7, 12, 15],
    15: [7, 14, 17, 16], 16: [9, 15, 10], 17: [10, 15, 18],
    18: [10, 17, 12, 19], 19: [11, 18, 12],
}


@pytest.mark.parametrize("name,order", sorted(WITNESSES.items()))
def test_the_surgery_witness_passes_every_checker(name: str, order: int) -> None:
    path = SURGERY / name
    verify.verify_certificate(verify.load_certificate(path), expected_order=order)
    verify_darts.check(verify_darts.load(path), expected_order=order)
    assert fast_apg_check.accepts_certificate(path)
    degrees, alpha = alpha_from_certificate(path)
    assert general_apg.is_apg(degrees, alpha)


@pytest.mark.parametrize("name,order", sorted(WITNESSES.items()))
def test_the_surgery_witness_is_three_connected(name: str, order: int) -> None:
    rotation = cn.load_rotation(SURGERY / name)
    assert len(rotation) == order
    assert cn.is_three_connected(rotation)
    assert cn.separating_pairs_on_faces(rotation) == []


def test_the_two_order_38_witnesses_are_different_graphs() -> None:
    import test_pumping_splice as tps

    left = cn.load_rotation(SURGERY / "APG38_3conn.json")
    right = cn.load_rotation(SURGERY / "APG38_3conn_b.json")
    assert tps._canonical(left) != tps._canonical(right)


# --------------------------------------------------------------------------
# The checker defect


def _fixture_alpha(tmp_path: Path):
    certificate = {
        "format": "apg-plane-rotation-v1",
        "vertices": [
            {"id": vertex, "clockwise": ring}
            for vertex, ring in sorted(DEGREE_SIX_APG.items())
        ],
    }
    for row in certificate["vertices"]:
        ring = row["clockwise"]
        row["clockwise"] = ring[ring.index(min(ring)):] + ring[:ring.index(min(ring))]
    path = tmp_path / "degree_six.json"
    path.write_text(json.dumps(certificate))
    return path


def test_the_fixture_really_is_an_alternating_plane_graph(tmp_path) -> None:
    """Otherwise the next test would pass for the wrong reason."""

    path = _fixture_alpha(tmp_path)
    degrees, alpha = alpha_from_certificate(path)
    assert general_apg.is_apg(degrees, alpha)
    assert max(degrees) == 6
    assert cn.is_three_connected(cn.load_rotation(path))


def test_the_third_checker_now_rejects_degrees_outside_three_four_five(tmp_path) -> None:
    """The regression: this returned True before 2026-09-01."""

    degrees, alpha = alpha_from_certificate(_fixture_alpha(tmp_path))
    assert not fast_apg_check.is_apg(degrees, alpha)


def test_the_fix_did_not_cost_any_certificate() -> None:
    import pumping_splice as ps

    for order in ps.TARGET_ORDERS:
        assert fast_apg_check.accepts_certificate(
            HERE / "certificates" / "targets" / f"TARGET_{order}.json"
        )
