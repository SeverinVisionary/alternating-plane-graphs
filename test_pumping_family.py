"""Gates on the period/cap decomposition read off the certificates.

These test the *structure claim* -- "each target is capM + t periods + capP" --
against the finished objects, independently of the code that built them.  They
are deliberately exact: the cap sizes, the period counts and the one boundary
case are pinned, so a change in any certificate shows up here rather than in a
narrative sentence.
"""
from __future__ import annotations

import collections
import json

import pytest

import pumping_family as pf


DECOMPOSITION = pf.decompose_targets()


def test_every_target_is_periods_plus_cap() -> None:
    for order, record in DECOMPOSITION.items():
        assert record["order"] == order
        assert order == 3 * record["periods"] + record["cap_size"], (
            f"order {order} is not 3t + cap"
        )


@pytest.mark.parametrize("residue", sorted(pf.CAP_SIZE_BY_RESIDUE))
def test_the_cap_size_is_constant_within_a_residue_class(residue: int) -> None:
    sizes = {
        record["cap_size"]
        for order, record in DECOMPOSITION.items()
        if order % 3 == residue
    }
    assert sizes == {pf.CAP_SIZE_BY_RESIDUE[residue]}


@pytest.mark.parametrize("residue", sorted(pf.CAP_SIZE_BY_RESIDUE))
def test_the_period_count_rises_by_one_per_three_vertices(residue: int) -> None:
    orders = sorted(order for order in DECOMPOSITION if order % 3 == residue)
    for first, second in zip(orders, orders[1:]):
        gained = DECOMPOSITION[second]["periods"] - DECOMPOSITION[first]["periods"]
        assert gained == (second - first) // 3, (
            f"{first} -> {second} gained {gained} periods, expected {(second - first) // 3}"
        )


def test_two_residue_classes_are_a_single_pumped_family() -> None:
    """Residues 0 and 2: one cap remainder, every order the same object."""

    grouped = pf.families()
    for residue in (0, 2):
        assert len(grouped[residue]) == 1, (
            f"residue {residue} splits into {len(grouped[residue])} cap families"
        )


def test_order_46_is_the_documented_boundary_case() -> None:
    """Residue 1 splits, and the split is exactly ``t = 2`` against ``t >= 3``.

    Order 46 has the same cap *size* as the rest of its class but three
    different degree-4 signature counts: at the minimum period count the two
    caps are close enough to change each other's local structure.  That is the
    case a general pumping lemma has to treat separately, so it is pinned here
    rather than described.
    """

    grouped = pf.families()[1]
    assert len(grouped) == 2
    by_orders = {tuple(orders): key for key, orders in grouped.items()}
    assert (46,) in by_orders, "order 46 is no longer the odd one out in residue 1"

    boundary = dict(by_orders[(46,)])
    (rest_orders,) = [orders for orders in grouped.values() if orders != [46]]
    assert rest_orders == [49, 52, 55, 67, 70, 73, 88, 91, 109]
    bulk = dict(by_orders[tuple(rest_orders)])

    differences = {
        sig: (boundary.get(sig, 0), bulk.get(sig, 0))
        for sig in set(boundary) | set(bulk)
        if boundary.get(sig, 0) != bulk.get(sig, 0)
    }
    assert differences == {
        "(4, (3, 5, 3, 5))": (8, 9),
        "(4, (3, 5, 5, 5))": (6, 4),
        "(4, (5, 5, 5, 5))": (0, 1),
    }
    assert DECOMPOSITION[46]["periods"] == 2
    assert all(DECOMPOSITION[order]["periods"] >= 3 for order in rest_orders)


def test_the_measured_period_ranges() -> None:
    """Pinned because SEARCH_STATUS records 't from 2 to 22', which is narrower."""

    ranges = {}
    for order, record in DECOMPOSITION.items():
        ranges.setdefault(order % 3, []).append(record["periods"])
    assert {residue: (min(v), max(v)) for residue, v in ranges.items()} == {
        0: (5, 19),
        1: (2, 23),
        2: (5, 26),
    }


def test_the_signature_is_sensitive_to_the_embedding(tmp_path) -> None:
    """Negative control: the decomposition must not survive a re-embedding.

    Transposing two neighbours in one rotation keeps the graph and every degree
    and changes only the embedding.  If the signature multiset were blind to
    that, every result above would be a statement about degree sequences.
    """

    data = json.loads((pf.TARGETS_DIR / "TARGET_46.json").read_text())
    before = pf.decompose(pf.TARGETS_DIR / "TARGET_46.json")
    changed = 0
    for row in data["vertices"]:
        if len(row["clockwise"]) < 4:
            continue
        mutated = json.loads(json.dumps(data))
        target = next(r for r in mutated["vertices"] if r["id"] == row["id"])
        target["clockwise"][1], target["clockwise"][2] = (
            target["clockwise"][2],
            target["clockwise"][1],
        )
        path = tmp_path / f"mutated_{row['id']}.json"
        path.write_text(json.dumps(mutated, indent=2, sort_keys=True) + "\n")
        after = pf.decompose(path)
        if (after["periods"], after["cap"]) != (before["periods"], before["cap"]):
            changed += 1
    assert changed, "no single transposition changed the decomposition"
