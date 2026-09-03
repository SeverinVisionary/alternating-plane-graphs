"""Gates for the periodic capping lemma, now that it is a construction.

`PUMPING_LEMMA_STATUS.md` used to list four unverified hypotheses, no
implementation of the splice, and no value for `q`.  The construction in
`pumping_splice.py` supplies all three, so what has to be gated here is not
"does it run" but the three things a referee would attack:

* the hypothesis the proof rests on -- that the deep block really is periodic,
  so that a bounded window of a spliced map is a translated window of the
  certificate;
* that the spliced maps are `(3,4,5)`-APGs according to the independent
  verifiers, at the claimed orders, including far outside the certificate range;
* that the splice is not vacuous -- that it reproduces the certificates it did
  not start from, and that breaking a cap breaks the result.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import connectivity
import fast_apg_check
import pumping_splice as ps
import verify
import verify_darts

HERE = Path(__file__).resolve().parent
TARGETS = HERE / "certificates" / "targets"

# Orders whose alignment reaches a deep interior at all; 46, 47, 49, 50, 52 and
# 55 are the short strips `strip_alignment.py` already records as ragged.
SPLICEABLE = tuple(o for o in ps.TARGET_ORDERS if o not in (46, 47, 49, 50, 52, 55))
# Order 48's strip has a single deep copy, so "the deep block is periodic" has
# nothing to compare there; it still splices upwards off that one template.
PERIODIC = tuple(o for o in SPLICEABLE if o != 48)
REPRESENTATIVES = (90, 109, 110)          # deepest strip in each residue class
FLOOR_ORDER_BY_RESIDUE = {0: 48, 1: 52, 2: 50}


def _rotation(certificate: dict) -> dict[int, list[int]]:
    return {row["id"]: list(row["clockwise"]) for row in certificate["vertices"]}


def _canonical(rotation: dict[int, list[int]]):
    """Canonical form of a rotation system up to relabelling and reflection."""

    best = None
    for mirror in (False, True):
        rings = {
            vertex: (list(reversed(ring)) if mirror else list(ring))
            for vertex, ring in rotation.items()
        }
        for root in rings:
            for start in range(len(rings[root])):
                label, queue, code = {root: 0}, [(root, start)], []
                while queue:
                    vertex, offset = queue.pop(0)
                    ring = rings[vertex]
                    row = []
                    for step in range(len(ring)):
                        neighbour = ring[(offset + step) % len(ring)]
                        if neighbour not in label:
                            label[neighbour] = len(label)
                            queue.append((neighbour, rings[neighbour].index(vertex)))
                        row.append(label[neighbour])
                    code.append(tuple(row))
                if len(label) != len(rings):
                    continue
                code = tuple(code)
                if best is None or code < best:
                    best = code
    return best


def _accept(certificate: dict, order: int, tmp_path: Path) -> None:
    """Both independent verifiers plus the third dart-side checker."""

    path = tmp_path / "spliced.json"
    path.write_text(json.dumps(certificate))
    verify.verify_certificate(verify.load_certificate(path), expected_order=order)
    verify_darts.check(verify_darts.load(path), expected_order=order)
    assert fast_apg_check.accepts_certificate(path)


# --------------------------------------------------------------------------
# The hypothesis the proof rests on


@pytest.mark.parametrize("order", PERIODIC)
def test_the_deep_block_is_periodic(order: int) -> None:
    """Deep rotations are translates of one another, so windows translate."""

    assert ps.deep_block_is_periodic(order)


def test_periodicity_is_reported_as_unchecked_when_there_is_one_deep_copy() -> None:
    """Not a pass by default: a single deep copy cannot witness a period."""

    assert len(ps.deep_copies(ps.symbolic(48)[1])) == 1
    assert not ps.deep_block_is_periodic(48)


@pytest.mark.parametrize("order", REPRESENTATIVES)
def test_every_face_stays_inside_a_short_window_of_copies(order: int) -> None:
    """The locality step: face size <= 5 and edge offset <= 2 bound the span.

    This is what lets a finite check about one certificate carry to the whole
    family.  If a facial walk could span an unbounded number of copies, no
    amount of local agreement would settle the spliced map's faces.
    """

    rotation = ps.splice(order, 3)
    spans = []
    for walk in connectivity.faces(rotation):
        copies = [vertex[2] for vertex in walk if vertex[0] == "S"]
        if copies:
            spans.append(max(copies) - min(copies))
    assert spans and max(spans) <= 3, max(spans)


# --------------------------------------------------------------------------
# The spliced maps really are APGs


@pytest.mark.parametrize("order", SPLICEABLE)
def test_splice_at_zero_reproduces_the_certificate(order: int) -> None:
    stored = connectivity.load_rotation(TARGETS / f"TARGET_{order}.json")
    assert _canonical(_rotation(ps.certificate(order, 0))) == _canonical(stored)


@pytest.mark.parametrize("order", REPRESENTATIVES)
def test_the_family_verifies_from_the_floor_upwards(order: int, tmp_path) -> None:
    floor = ps.floor_delta(order)
    for delta in range(floor, floor + 12):
        certificate = ps.certificate(order, delta)
        expected = order + 3 * delta
        assert len(certificate["vertices"]) == expected
        _accept(certificate, expected, tmp_path)


@pytest.mark.parametrize("order,delta", [(90, 100), (109, 100), (110, 100)])
def test_the_family_verifies_far_outside_the_certificate_range(
    order: int, delta: int, tmp_path
) -> None:
    """Order ~400: the paper's Theorem 8.1 range, reached from one certificate."""

    certificate = ps.certificate(order, delta)
    _accept(certificate, order + 3 * delta, tmp_path)


def test_the_floor_is_the_same_order_for_every_member_of_a_residue_class() -> None:
    """`q` in the lemma: where deletion would eat a copy that is not deep."""

    floors: dict[int, set[int]] = {}
    for order in SPLICEABLE:
        floors.setdefault(order % 3, set()).add(order + 3 * ps.floor_delta(order))
    assert {residue: sorted(v) for residue, v in floors.items()} == {
        residue: [order] for residue, order in FLOOR_ORDER_BY_RESIDUE.items()
    }


def test_the_family_covers_every_order_from_50_up_and_48() -> None:
    reached = set()
    for floor_order in FLOOR_ORDER_BY_RESIDUE.values():
        reached |= set(range(floor_order, 400, 3))
    assert set(range(50, 400)) <= reached
    assert 48 in reached
    # Not a superset claim: 49 is genuinely outside the family.
    assert 49 not in reached and 47 not in reached


# --------------------------------------------------------------------------
# The splice is not vacuous


@pytest.mark.parametrize(
    "order,delta",
    [(110, -20), (110, -19), (110, -18), (109, -19), (92, -14), (90, -14), (72, -8)],
)
def test_splicing_down_reproduces_a_certificate_it_did_not_start_from(
    order: int, delta: int
) -> None:
    """The strongest check available: caps extracted at one order rebuild another.

    `TARGET_110` shortened by twenty periods is `TARGET_50`, and so is
    `TARGET_92` shortened by fourteen.  Two independently searched certificates
    decompose into the same two caps and the same period.
    """

    target = order + 3 * delta
    stored = connectivity.load_rotation(TARGETS / f"TARGET_{target}.json")
    assert _canonical(_rotation(ps.certificate(order, delta))) == _canonical(stored)


def test_a_damaged_cap_is_rejected(tmp_path) -> None:
    """Negative control: the verifiers are doing work here, not rubber-stamping."""

    rotation = ps.splice(110, 2)
    caps = [vertex for vertex in rotation if vertex[0] == "C"]
    victim = caps[0]
    damaged = dict(rotation)
    ring = list(damaged[victim])
    damaged[victim] = [ring[1], ring[0]] + ring[2:]
    labels = {vertex: index for index, vertex in enumerate(sorted(damaged, key=str))}
    certificate = {
        "format": "apg-plane-rotation-v1",
        "vertices": [
            {"id": labels[v], "clockwise": [labels[n] for n in damaged[v]]}
            for v in sorted(damaged, key=lambda k: labels[k])
        ],
    }
    for row in certificate["vertices"]:
        ring = row["clockwise"]
        start = ring.index(min(ring))
        row["clockwise"] = ring[start:] + ring[:start]
    path = tmp_path / "damaged.json"
    path.write_text(json.dumps(certificate))
    with pytest.raises(Exception):
        verify.verify_certificate(verify.load_certificate(path), expected_order=116)


def test_deleting_past_the_floor_is_refused_rather_than_silently_wrong() -> None:
    floor = ps.floor_delta(110)
    with pytest.raises(ValueError):
        ps.splice(110, floor - 1)
