#!/usr/bin/env python3
"""What the 26 certificates are made of, read off the certificates alone.

The construction claims each target is ``capM + t periods + capP``.  That is a
statement about how the witnesses were *built*; this module tests whether it is
visible in the finished objects, using nothing but the committed rotation
systems -- no generator, no cap file, no strip code.

Method.  Give each vertex a local signature: its degree together with the cyclic
sequence of its neighbours' degrees, canonicalised under rotation and reflection
(so it does not depend on where a certificate happens to start its clockwise
list, nor on mirror image).  Three signatures mark the strip period:

    degree 3 : (4, 5, 5)          degree 4 : (3, 5, 5, 5)
    degree 5 : (3, 4, 3, 4, 4)

The degree-5 one is the reliable marker -- the degree-3 and degree-4 ones also
occur inside caps -- so the period count is read from it, and the *cap
remainder* is the signature multiset with ``t`` copies of all three period
signatures removed.

What comes out is sharper than the construction narrative:

* the cap remainder is **constant within each residue class mod 3**, at 33, 40
  and 32 vertices for residues 0, 1 and 2 -- three cap pairs, exactly as
  claimed, and each one really is the same object at every ``t``;
* ``n = 3t + cap`` holds exactly at all 26 orders, and ``t`` rises by ``dn/3``;
* **order 46 is a boundary case.**  It is the ``t = 2`` member of residue 1 and
  its cap remainder differs from the ``t >= 3`` members in three degree-4
  signature counts, though not in size.  At the minimum period count the two
  caps are close enough to change each other's local structure.

That last point is the one a pumping lemma has to face: the statement
"cap + t periods + cap is a (3,4,5)-APG" cannot be proved uniformly from an
interface argument alone unless it either starts at ``t >= 3`` or handles
``t = 2`` separately, because at ``t = 2`` the interface is not the only thing
the two caps see.  It is not evidence against the certificates -- both verifiers
accept order 46 -- but it says where the general proof has to do real work.

The measured ``t`` ranges are 5..19 (residue 0), 2..23 (residue 1) and 5..26
(residue 2), which is wider than the "t from 2 to 22" recorded in SEARCH_STATUS.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path
from typing import Mapping, Sequence

HERE = Path(__file__).resolve().parent
TARGETS_DIR = HERE / "certificates" / "targets"

TARGET_ORDERS = (
    tuple(range(46, 57)) + tuple(range(67, 75)) + tuple(range(88, 93)) + (109, 110)
)

PERIOD_SIGNATURES = (
    (3, (4, 5, 5)),
    (4, (3, 5, 5, 5)),
    (5, (3, 4, 3, 4, 4)),
)
PERIOD_MARKER = (5, (3, 4, 3, 4, 4))

# Measured, not assumed; the tests pin them.
CAP_SIZE_BY_RESIDUE = {0: 33, 1: 40, 2: 32}


def signature(rotation: Mapping[int, Sequence[int]], degrees: Mapping[int, int], vertex: int):
    """Degree, plus the neighbour-degree cycle up to rotation and reflection."""

    cycle = [degrees[neighbour] for neighbour in rotation[vertex]]
    length = len(cycle)
    rotations = (
        tuple(order[index:] + order[:index])
        for order in (cycle, cycle[::-1])
        for index in range(length)
    )
    return (degrees[vertex], min(rotations))


def load_rotation(path: Path) -> tuple[dict[int, list[int]], dict[int, int]]:
    data = json.loads(path.read_text())
    rotation = {row["id"]: list(row["clockwise"]) for row in data["vertices"]}
    return rotation, {vertex: len(cycle) for vertex, cycle in rotation.items()}


def decompose(path: Path) -> dict[str, object]:
    """Split one certificate into ``t`` periods plus a cap remainder."""

    rotation, degrees = load_rotation(path)
    counts = collections.Counter(signature(rotation, degrees, v) for v in rotation)
    periods = counts[PERIOD_MARKER]
    remainder = dict(counts)
    for marker in PERIOD_SIGNATURES:
        remainder[marker] = remainder.get(marker, 0) - periods
    remainder = {sig: count for sig, count in remainder.items() if count}
    if any(count < 0 for count in remainder.values()):
        raise ValueError(f"{path.name}: fewer period signatures than periods")
    return {
        "order": len(rotation),
        "periods": periods,
        "cap": remainder,
        "cap_size": sum(remainder.values()),
    }


def decompose_targets() -> dict[int, dict[str, object]]:
    return {
        order: decompose(TARGETS_DIR / f"TARGET_{order}.json") for order in TARGET_ORDERS
    }


def cap_key(cap: Mapping[object, int]) -> tuple:
    return tuple(sorted((repr(sig), count) for sig, count in cap.items()))


def families() -> dict[int, dict[tuple, list[int]]]:
    """Residue class mod 3 -> cap remainder -> the orders sharing it."""

    grouped: dict[int, dict[tuple, list[int]]] = collections.defaultdict(dict)
    for order, record in decompose_targets().items():
        grouped[order % 3].setdefault(cap_key(record["cap"]), []).append(order)
    return {residue: dict(caps) for residue, caps in grouped.items()}


def main() -> int:
    for residue, caps in sorted(families().items()):
        print(f"residue {residue} (cap {CAP_SIZE_BY_RESIDUE[residue]} vertices)")
        for orders in caps.values():
            records = decompose_targets()
            spread = [records[order]["periods"] for order in orders]
            print(f"  orders {orders}")
            print(f"  t      {spread}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
