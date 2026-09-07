"""Does the repository actually settle Conjecture 10.3?

> **Conjecture 10.3** (Althofer, Haugland, Scherer, Schneider, Van Cleemput,
> *Ars Math. Contemp.* **8** (2015) 337-363, p. 362.)
> For any `n >= 19` there exists a 3-connected alternating plane graph on `n`
> vertices.

The claim is not "many witnesses exist" but "every order from 19 up has one".
That is a statement about a union of sources, and it is checkable.  This file
checks it, and checks that each source really is doing the work attributed to
it -- removing any one of them must reopen an order.

The infinite tail is **not** established.  It rested on the induction in
`family_connectivity.py`, which was found unproved on 2026-09-05 and withdrawn.
What this file gates is therefore the *checked* evidence -- stored certificates
and the Section-8 closures -- and the exact set of orders the withdrawal
reopened.  `witness_coverage.residue` is kept but is no longer a headline: two
of its three terms are scans and the third is arithmetic, so it cannot see a
missing file at any order the family claims.
"""
from __future__ import annotations

import pytest

import connectivity as cn
import general_apg
import section8_witnesses as s8
import witness_coverage as wc
from certificate_tools import alpha_from_certificate

HORIZON = 400


# The 53 orders at or above 19 with a witness this repository checks, plus
# order 17 below the conjecture's range: the 54 of the manuscript's Theorem 6.1.
VERIFIED = (set(range(19, 57)) | set(range(67, 75))
            | set(range(88, 93)) | {109, 110})


def test_the_checked_witnesses_are_exactly_the_orders_the_theorem_claims() -> None:
    """What the deposit establishes, measured from files rather than asserted."""

    assert {o for o in wc.verified_orders() if o >= 19} == VERIFIED
    assert 17 in wc.verified_orders()
    assert len(VERIFIED) + 1 == 54


def test_the_withdrawal_reopened_exactly_these_orders() -> None:
    """Conjecture 10.3 is open here above 56, apart from three finite islands."""

    gap = wc.verified_residue(HORIZON)
    assert gap[:10] == list(range(57, 67))
    assert set(gap) == set(range(19, HORIZON)) - VERIFIED
    assert min(gap) == 57


def test_the_residue_cannot_see_a_missing_family_witness() -> None:
    """Why `residue` is no longer the headline gate.

    `family_orders` is `range(floor, horizon, 3)` over `FAMILY_FLOORS`; it reads
    no file.  So `residue` reports full coverage from order 48 up on the
    strength of a withdrawn theorem, and would go on reporting it if every
    stored witness above 47 were deleted.  This gate pins that, so the next
    reader does not mistake `residue() == []` for evidence.
    """

    assert wc.residue(HORIZON) == []

    # Delete every stored witness from 48 up and recompute the residue's union.
    thinned = {o for o in wc.verified_orders() if o < 48}
    blind = sorted(set(range(19, HORIZON)) - (thinned | wc.family_orders(HORIZON)))
    # One order reappears -- 49, the only one above 47 the family's floors and
    # step of 3 do not reach.  The other 327 do not, because the family term
    # claims them by arithmetic.
    assert blind == [49]
    assert len(wc.verified_residue(HORIZON)) == 328


def test_order_nineteen_is_witnessed_and_cannot_be_a_three_four_five_graph() -> None:
    """The boundary case, and the one order the settled 10.2 cannot reach."""

    rows = wc.witnesses()[19]
    assert rows, "no order-19 witness"
    assert all(three for _, three in rows)
    for name, _ in rows:
        path = wc.HERE / name
        degrees, alpha = alpha_from_certificate(path)
        assert general_apg.is_apg(degrees, alpha)
        # No (3,4,5)-APG exists on 19 vertices; each of these leaves the class.
        assert max(degrees) > 5 or max(
            len(walk) for walk in cn.faces(cn.load_rotation(path))
        ) > 5


def test_every_counted_witness_is_three_connected() -> None:
    rows = wc.witnesses()
    assert rows
    assert [name for order in rows for name, ok in rows[order] if not ok] == []


# --------------------------------------------------------------------------
# Each source must be load-bearing


def test_dropping_the_stored_certificates_reopens_orders() -> None:
    covered = wc.family_orders(HORIZON) | wc.section8_orders()
    gap = sorted(set(range(19, HORIZON)) - covered)
    assert gap[:8] == [19, 20, 25, 26, 27, 28, 29, 30]


def test_dropping_the_section_eight_closures_reopens_orders() -> None:
    covered = wc.stored_orders() | wc.family_orders(HORIZON)
    assert sorted(set(range(19, HORIZON)) - covered) == [24, 39, 40, 41, 43, 44, 45]


def test_dropping_the_spliced_family_reopens_the_infinite_tail() -> None:
    covered = wc.stored_orders() | wc.section8_orders()
    gap = sorted(set(range(19, HORIZON)) - covered)
    assert gap[:4] == [57, 58, 59, 60]
    assert len(gap) > 200, "the family is what carries the tail"


def test_the_surgery_witnesses_are_what_close_thirty_seven_and_thirty_eight() -> None:
    covered = (wc.family_orders(HORIZON) | wc.section8_orders()
               | {o for o in wc.stored_orders() if o not in (37, 38)})
    assert {37, 38} & covered == set()


@pytest.mark.parametrize("order", (19, 24, 37, 38, 45, 110))
def test_a_witness_at_each_formerly_open_order_is_actually_present(order: int) -> None:
    """Spot check by construction rather than by set arithmetic."""

    if order in s8.RECIPES and order not in wc.stored_orders():
        certificate = s8.witness(order)
        rotation = {row["id"]: row["clockwise"] for row in certificate["vertices"]}
    else:
        name = wc.witnesses()[order][0][0]
        rotation = cn.load_rotation(wc.HERE / name)
    assert len(rotation) == order
    assert cn.is_three_connected(rotation)
