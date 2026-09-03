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
"""
from __future__ import annotations

import json
from pathlib import Path

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
