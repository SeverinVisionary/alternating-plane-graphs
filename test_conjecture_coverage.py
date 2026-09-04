"""Does the certificate set actually settle Conjecture 10.2?

The claim is not "26 witnesses exist" but "the conjecture is closed".  That is
a statement about a union of intervals, and it is checkable.  The source
paper's own coverage, quoted verbatim in PRIOR_ART.md and read from the PDF on
2026-09-01:

    exhaustive search      no (3,4,5)-APG below 17, none on 18 or 19
    heuristic search       all n in [20, 42]
    Section 8 construction n in [21,24] u [39,45] u [57,66] u [75,87] u [93,108]
    Theorem 8.1            all n >= 111

leaving `[46,56] u [67,74] u [88,92] u {109,110}` unknown -- the 26 target
orders.  This file checks that the union really is everything from 20 up, so a
missing order cannot hide behind the word "settles".

**Three of those four rows are the source paper's results, not this
repository's.**  That is a legitimate division of labour, but "settles" then
means "settles, given the 2015 paper", which is a weaker claim than it sounds.
So the union is measured twice: once as above, and once using only what this
deposit establishes on its own -- the 26 certificates plus the periodic capping
lemma, which yields order 48 and every order from 50 up without reference to
Theorem 8.1.  The second measurement is the honest headline, and it is
`test_the_deposit_alone_covers_every_order_from_46_up`.
"""
from __future__ import annotations

import json
from pathlib import Path

import witness_coverage

HERE = Path(__file__).resolve().parent
TARGETS_DIR = HERE / "certificates" / "targets"

HEURISTIC = set(range(20, 43))
SECTION_8 = (
    set(range(21, 25)) | set(range(39, 46)) | set(range(57, 67))
    | set(range(75, 88)) | set(range(93, 109))
)
THEOREM_8_1 = set(range(111, 400))          # "for any n >= 111"; 400 is a test horizon
PAPER_OPEN = (
    set(range(46, 57)) | set(range(67, 75)) | set(range(88, 93)) | {109, 110}
)


def _certificate_orders() -> set[int]:
    orders = set()
    for path in TARGETS_DIR.glob("TARGET_*.json"):
        data = json.loads(path.read_text())
        orders.add(len(data["vertices"]))
    return orders


def test_the_paper_leaves_exactly_the_26_orders_open() -> None:
    covered = HEURISTIC | SECTION_8 | THEOREM_8_1
    gap = set(range(20, 400)) - covered
    assert gap == PAPER_OPEN
    assert len(gap) == 26


def test_the_certificates_cover_exactly_the_open_orders() -> None:
    """Not a subset and not a superset: exactly the open set."""

    assert _certificate_orders() == PAPER_OPEN


def test_together_they_close_the_conjecture() -> None:
    covered = HEURISTIC | SECTION_8 | THEOREM_8_1 | _certificate_orders()
    assert set(range(20, 400)) <= covered, sorted(set(range(20, 400)) - covered)


def test_the_control_fails_if_one_certificate_is_removed() -> None:
    """Without this, the union test would pass on any superset of the gap."""

    for missing in (46, 74, 110):
        weakened = _certificate_orders() - {missing}
        covered = HEURISTIC | SECTION_8 | THEOREM_8_1 | weakened
        assert missing not in covered, f"order {missing} is covered by something else"


# --- what this deposit establishes without leaning on the 2015 paper ---------
#
# `witness_coverage.family_orders` is the periodic capping lemma's reach: floors
# at 48, 50 and 52 with step 3, i.e. {48} u [50, horizon).  It is proved in
# `PUMPING_LEMMA_STATUS.md`, not sampled, so the horizon is a test bound rather
# than a limit of the claim.

HORIZON = 400


def _deposit_only_orders() -> set[int]:
    return _certificate_orders() | witness_coverage.family_orders(HORIZON)


def test_the_deposit_alone_covers_every_order_from_46_up() -> None:
    """The certificates and the capping lemma, with nothing inherited.

    Everything from 46 up is closed by this repository on its own.  Orders 20
    to 45 remain the source paper's -- its heuristic search and its Section-8
    construction -- and this deposit does not re-establish them.

    One honest qualification, carried from the manuscript's deletion remark: the
    family's floor orders and 57, 58, 59, 61, 63 rest on machine-verified
    splices rather than on the capping lemma *as stated*, because the locality
    argument is written for insertion and `|D| >= 5` does not reach them that
    way.  That is still this repository's own evidence rather than the paper's,
    so the claim above stands -- but it is a mix of theorem and verified
    computation, not the theorem alone.
    """

    covered = _deposit_only_orders()
    assert set(range(46, HORIZON)) <= covered, sorted(set(range(46, HORIZON)) - covered)


def test_orders_20_to_45_are_exactly_what_is_inherited() -> None:
    """Name the debt precisely, so it cannot quietly grow or shrink."""

    inherited = sorted(set(range(20, HORIZON)) - _deposit_only_orders())
    assert inherited == list(range(20, 46))


def test_the_capping_lemma_makes_theorem_8_1_redundant_above_49() -> None:
    """Without this, wiring the lemma in would be decoration.

    Theorem 8.1 is the paper's `n >= 111`.  Dropping it entirely must leave the
    conjecture closed anyway, because the lemma already covers everything from
    50 up.
    """

    without_8_1 = HEURISTIC | SECTION_8 | _deposit_only_orders()
    assert set(range(20, HORIZON)) <= without_8_1, sorted(
        set(range(20, HORIZON)) - without_8_1
    )


def test_the_control_fails_without_the_capping_lemma() -> None:
    """The lemma must be doing the work, not the finite certificate list.

    The paper's finite constructions and the 26 certificates interlock to cover
    20 to 110 exactly, and stop there.  Everything above needs either the
    paper's Theorem 8.1 or this repository's capping lemma, so 111 is precisely
    where the infinite claim has to come from somewhere.
    """

    without_lemma = HEURISTIC | SECTION_8 | _certificate_orders()
    gap = sorted(set(range(20, HORIZON)) - without_lemma)
    assert gap, "the certificates alone should not reach the horizon"
    assert min(gap) == 111
    assert set(range(20, 111)) <= without_lemma
