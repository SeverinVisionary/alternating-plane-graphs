"""Exact arithmetic for the Section 8 two-hexagon block construction.

Joining blocks of orders ``b_1, ..., b_k`` identifies three vertices at each
of the ``k - 1`` joins.  Closing the two remaining hexagons changes no vertex
count, so the resulting APG has order

    3 + sum(b_i - 3).

This module deliberately knows nothing about graph search or certificate
verification.  It only freezes the order arithmetic used by the cloud job.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from itertools import combinations


TARGET_ORDERS = (
    *range(46, 57),
    *range(67, 75),
    *range(88, 93),
    109,
    110,
)

PUBLISHED_BLOCK_ORDERS = (21, 22, 23, 24)
PROPOSED_BLOCK_ORDERS = (25, 29, 34)
# The active Boolean pilot has a different all-target triple.  These are only
# arithmetic target orders until the cloud search emits and verifies concrete
# blocks; do not confuse this constant with a certificate inventory.
BOOLEAN_PRIMARY_T0_BLOCK_ORDERS = (28, 29, 31)
ALTERNATIVE_BLOCK_ORDER_RANGE = tuple(range(25, 37))


def apg_order(block_orders: Iterable[int]) -> int:
    """Return the closed APG order obtained from a nonempty block chain."""

    orders = tuple(block_orders)
    if not orders:
        raise ValueError("a block chain must contain at least one block")
    if any(order < 4 for order in orders):
        raise ValueError("every block order must be at least 4")
    return 3 + sum(order - 3 for order in orders)


def representation(target: int, block_orders: Iterable[int]) -> tuple[int, ...] | None:
    """Find a deterministic shortest nondecreasing block-order representation."""

    orders = tuple(sorted(set(block_orders)))
    if target < 4 or not orders:
        return None

    increments = tuple(order - 3 for order in orders)
    wanted = target - 3
    best: list[tuple[int, ...] | None] = [None] * (wanted + 1)
    best[0] = ()

    for order, increment in zip(orders, increments):
        for new_total in range(increment, wanted + 1):
            prefix = best[new_total - increment]
            if prefix is None:
                continue
            candidate = (*prefix, order)
            incumbent = best[new_total]
            if incumbent is None or (len(candidate), candidate) < (len(incumbent), incumbent):
                best[new_total] = candidate

    return best[wanted]


def t_total(block_orders: Iterable[int], block_t: Mapping[int, int]) -> int:
    """Return the additive degree-5/pentagon-incidence budget of a chain.

    The four published blocks have ``t=0``.  A newly found strict block can
    have positive ``t`` when it is intended only for a bounded construction,
    so order arithmetic alone is not enough to certify a target composition.
    ``block_t`` must therefore contain every order in the proposed chain.
    """

    total = 0
    for order in block_orders:
        try:
            value = block_t[order]
        except KeyError as exc:
            raise ValueError(f"missing t value for block order {order}") from exc
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"t value for block order {order} must be a nonnegative integer")
        total += value
    return total


def representation_with_t_budget(
    target: int,
    block_t: Mapping[int, int],
    *,
    max_t: int = 4,
) -> tuple[int, ...] | None:
    """Find a deterministic target representation with additive ``t <= max_t``.

    This is intentionally separate from :func:`representation`: the latter
    freezes only order coverage, while this function is the mandatory finite
    composition check once a candidate block's audited ``t`` is known.
    """

    if target < 4:
        return None
    if not isinstance(max_t, int) or isinstance(max_t, bool) or max_t < 0:
        raise ValueError("max_t must be a nonnegative integer")

    entries = tuple(sorted(block_t.items()))
    if not entries:
        return None
    for order, value in entries:
        if order < 4:
            raise ValueError("every block order must be at least 4")
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("block t values must be nonnegative integers")

    wanted = target - 3
    best: list[list[tuple[int, ...] | None]] = [
        [None for _ in range(max_t + 1)] for _ in range(wanted + 1)
    ]
    best[0][0] = ()
    for order, value in entries:
        increment = order - 3
        for total in range(increment, wanted + 1):
            for spent in range(value, max_t + 1):
                prefix = best[total - increment][spent - value]
                if prefix is None:
                    continue
                candidate = (*prefix, order)
                incumbent = best[total][spent]
                if incumbent is None or (len(candidate), candidate) < (
                    len(incumbent),
                    incumbent,
                ):
                    best[total][spent] = candidate

    candidates = [
        (len(blocks), blocks, spent)
        for spent, blocks in enumerate(best[wanted])
        if blocks is not None
    ]
    if not candidates:
        return None
    return min(candidates)[1]


def target_representations_with_t_budget(
    block_t: Mapping[int, int],
    *,
    max_t: int = 4,
) -> dict[int, tuple[int, ...]]:
    """Return a checked finite-chain representation for every target order."""

    result: dict[int, tuple[int, ...]] = {}
    for target in TARGET_ORDERS:
        blocks = representation_with_t_budget(target, block_t, max_t=max_t)
        if blocks is None:
            raise ValueError(
                f"target {target} has no representation within t budget {max_t}"
            )
        result[target] = blocks
    return result


def boolean_primary_t0_target_representations() -> dict[int, tuple[int, ...]]:
    """Freeze the active Boolean pilot's conditional all-target coverage.

    This proves only the Section-8 order arithmetic conditional on certified
    ``t=0`` blocks at orders 28, 29, and 31.  It does not assert that any of
    those blocks exists; their exact-map certificates remain the cloud job's
    positive-witness objective.
    """

    return target_representations_with_t_budget(
        {
            order: 0
            for order in (*PUBLISHED_BLOCK_ORDERS, *BOOLEAN_PRIMARY_T0_BLOCK_ORDERS)
        },
        max_t=0,
    )


def target_representations() -> dict[int, tuple[int, ...]]:
    """Represent all 26 targets using the published and three proposed blocks."""

    available = (*PUBLISHED_BLOCK_ORDERS, *PROPOSED_BLOCK_ORDERS)
    result: dict[int, tuple[int, ...]] = {}
    for target in TARGET_ORDERS:
        blocks = representation(target, available)
        if blocks is None:  # pragma: no cover - guarded by the regression test
            raise AssertionError(f"target {target} is not represented")
        result[target] = blocks
    return result


def covering_new_block_triples() -> tuple[tuple[int, int, int], ...]:
    """List every three-order extension in 25..36 covering all 26 targets."""

    result: list[tuple[int, int, int]] = []
    for proposed in combinations(ALTERNATIVE_BLOCK_ORDER_RANGE, 3):
        available = (*PUBLISHED_BLOCK_ORDERS, *proposed)
        if all(representation(target, available) is not None for target in TARGET_ORDERS):
            result.append(proposed)
    return tuple(result)


if __name__ == "__main__":
    for order, blocks in target_representations().items():
        print(f"{order}: {' + '.join(map(str, blocks))} -> {apg_order(blocks)}")
