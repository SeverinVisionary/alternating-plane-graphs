#!/usr/bin/env python3
"""Which orders have a 3-connected APG witness *on disk*, derived not asserted.

The first pass at this scanned two directories and hard-coded the answer, and
so missed `certificates/search_seeds/`, which holds published witnesses at
orders 21, 22, 23 and 25.  The residue for Conjecture 10.3 was reported as
fourteen orders when it was ten.  This module walks every certificate in the
tree instead, verifies each one is a closed `(3,4,5)`-APG before counting it,
and unions the result with the spliced family.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import connectivity as cn
import general_apg
import import_planar_code as ipc
from certificate_tools import alpha_from_certificate

HERE = Path(__file__).resolve().parent
CERTIFICATES = HERE / "certificates"
FORMAT = "apg-plane-rotation-v1"
# Valid (3,4,5)-APGs that are deliberately *not* witnesses: they refute a claim
# rather than support one, and must never be counted as Conjecture 10.3
# coverage.  See certificates/counterexamples/PROVENANCE.md.
# `upstream` holds the source bytes for decoded JSON siblings; counting both
# double-lists the same graph and leaves `.plc` paths where callers expect a
# certificate.
EXCLUDED = ("counterexamples", "upstream")
# `pumping_splice.floor_delta` puts the family floor at these orders by residue.
FAMILY_FLOORS = (48, 50, 52)
HORIZON = 400


def _is_alternating(rotation: dict[int, list[int]]) -> bool:
    """Definition 2.1, decided on a rotation given as neighbour lists.

    The planar-code branch used to count a file without checking it was an APG
    at all.  Every stored source happens to be one, but a coverage scan must not
    take that on faith.
    """

    import json
    import tempfile

    certificate = {
        "format": FORMAT,
        "vertices": [
            {"id": vertex, "clockwise": list(ring)}
            for vertex, ring in sorted(rotation.items())
        ],
    }
    for row in certificate["vertices"]:
        ring = row["clockwise"]
        start = ring.index(min(ring))
        row["clockwise"] = ring[start:] + ring[:start]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(certificate, handle)
        path = Path(handle.name)
    try:
        degrees, alpha = alpha_from_certificate(path)
        return general_apg.is_apg(degrees, alpha)
    finally:
        path.unlink(missing_ok=True)


@lru_cache(maxsize=1)
def witnesses() -> dict[int, tuple[tuple[str, bool], ...]]:
    """Every stored `(3,4,5)`-APG, by order, with its 3-connectivity.

    Cached: the scan runs `is_three_connected` on every certificate up to order
    110, which is cubic, and three separate gates ask for it.
    """

    found: dict[int, list[tuple[str, bool]]] = {}
    for path in sorted(CERTIFICATES.rglob("*.json")):
        if any(part in EXCLUDED for part in path.parts):
            continue
        try:
            data = json.loads(path.read_text())
        except (ValueError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict) or data.get("format") != FORMAT:
            continue
        # Conjecture 10.3 is about Definition 2.1, so the scan counts general
        # alternating plane graphs, not only the (3,4,5) subclass.  Order 19 can
        # only be witnessed by a general one.
        degrees, alpha = alpha_from_certificate(path)
        if not general_apg.is_apg(degrees, alpha):
            continue
        rotation = cn.load_rotation(path)
        found.setdefault(len(rotation), []).append(
            (str(path.relative_to(HERE)), cn.is_three_connected(rotation))
        )
    for path in sorted(CERTIFICATES.rglob("*.plc")):
        if any(part in EXCLUDED for part in path.parts):
            continue
        rotation = {index + 1: ring for index, ring in enumerate(ipc.decode_first(path))}
        if not _is_alternating(rotation):
            continue
        found.setdefault(len(rotation), []).append(
            (str(path.relative_to(HERE)), cn.is_three_connected(rotation))
        )
    return {order: tuple(rows) for order, rows in found.items()}


def counterexamples() -> dict[str, dict]:
    """The excluded objects, so a gate can assert what they are rather than skip them."""

    out = {}
    for path in sorted((CERTIFICATES / "counterexamples").glob("*.json")):
        out[path.name] = cn.load_rotation(path)
    return out


def stored_orders() -> set[int]:
    return {order for order, rows in witnesses().items() if any(ok for _, ok in rows)}


def family_orders(horizon: int = HORIZON) -> set[int]:
    covered: set[int] = set()
    for floor_order in FAMILY_FLOORS:
        covered |= set(range(floor_order, horizon, 3))
    return covered


def verified_orders() -> set[int]:
    """Orders with a 3-connected witness this repository actually checks.

    Stored certificates plus the Section-8 closures composed at run time.  The
    periodic family is deliberately excluded.  `family_orders` is arithmetic
    over `FAMILY_FLOORS` and reads no file, so it reports coverage whether or
    not any witness exists at those orders; and its 3-connectivity rests on the
    induction in `family_connectivity.py`, which was found unproved on
    2026-09-05.  Anything asserted about Conjecture 10.3's evidence has to be
    asserted about this set, not about `residue`.
    """

    return stored_orders() | section8_orders()


def verified_residue(horizon: int = HORIZON) -> list[int]:
    """Orders from 19 up with no *checked* 3-connected witness in this repository."""

    return sorted(set(range(19, horizon)) - verified_orders())


def section8_orders() -> set[int]:
    """Orders closed by a Section-8 closure built at run time, not stored.

    `section8_witnesses.py` composes the strict blocks in `results/blocks/`
    rather than committing the closures, so a scan of certificate files cannot
    see them.
    """

    import section8_witnesses

    return set(section8_witnesses.RECIPES)


def residue(horizon: int = HORIZON) -> list[int]:
    """Orders from 19 up not claimed by any source, checked or theorem-derived.

    **This is not a measurement of the evidence.**  Two of the three terms are
    scans; `family_orders` is arithmetic, and it carries the orders whose
    3-connectivity was withdrawn on 2026-09-05.  Deleting every stored witness
    at 48 and at every order from 50 up leaves this function returning `[]`
    unchanged.  Use `verified_residue` for what the repository establishes.
    """

    covered = stored_orders() | family_orders(horizon) | section8_orders()
    return sorted(set(range(19, horizon)) - covered)


def main() -> int:
    rows = witnesses()
    for order in sorted(rows):
        for name, ok in rows[order]:
            print(f"{order:>4}  {'3-connected' if ok else 'NOT 3-connected':<16} {name}")
    print()
    print("stored orders:", sorted(stored_orders()))
    print("residue for Conjecture 10.3:", residue())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
