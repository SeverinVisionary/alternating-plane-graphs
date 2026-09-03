#!/usr/bin/env python3
"""Section-8 closures at the orders Conjecture 10.3 was still missing.

The residue for Conjecture 10.3 was `19, 24, 37, 38, 39, 40, 41, 43, 44, 45`.
Seven of those are reachable from blocks this repository already holds, with no
new search and nothing downloaded: `results/blocks/` has strict two-socket
blocks at orders 21, 22, 23 and 24, and Section 8 of the paper composes them by
identifying three vertices at each join, so a chain of blocks of orders
`21, 22, 23, 24` closes to order `18a + 19b + 20c + 21d + 3`.

    single block, closed        21, 22, 23, 24
    two blocks, composed        39, 40, 41, 42, 43, 44, 45

`34` and `35` are not sums of `18, 19, 20, 21`, so orders 37 and 38 are out of
reach here -- which is exactly why the paper's own Section-8 coverage list reads
`[21,24] u [39,45] u [57,66] u [75,87] u [93,108]` and skips them.

This is the paper's construction, not a new one.  What is new is that the
closures are *checked*: Section 10 asserts the Section-8 graphs are 3-connected
and Conjecture 10.3 turns on that, so `test_section8_witnesses.py` puts every
closure to all three certificate checkers and to the brute-force connectivity
test rather than taking the assertion.
"""
from __future__ import annotations

import json
from pathlib import Path

import block_tools as bt

HERE = Path(__file__).resolve().parent
BLOCKS = HERE / "results" / "blocks"

# order -> the block chain whose closure has that order
RECIPES: dict[int, tuple[str, ...]] = {
    21: ("A21",),
    22: ("B22",),
    23: ("C23",),
    24: ("D24",),
    39: ("A21", "A21"),
    40: ("A21", "B22"),
    41: ("A21", "C23"),
    42: ("A21", "D24"),
    43: ("B22", "D24"),
    44: ("C23", "D24"),
    45: ("D24", "D24"),
}
# The orders this module is here for: the rest were already covered.
NEW_ORDERS = (24, 39, 40, 41, 43, 44, 45)


def block(name: str) -> dict:
    return bt.load_json(BLOCKS / f"{name}.json")


def witness(order: int) -> dict:
    """The closed `(3,4,5)`-APG certificate at `order`, built from the blocks."""

    chain = RECIPES[order]
    composed = block(chain[0])
    for name in chain[1:]:
        composed = bt.compose_two(composed, block(name))
    certificate = bt.close_block(composed)
    if len(certificate["vertices"]) != order:
        raise ValueError(
            f"chain {chain} closed to {len(certificate['vertices'])}, not {order}"
        )
    return certificate


def main() -> int:
    import connectivity as cn

    for order in sorted(RECIPES):
        certificate = witness(order)
        rotation = {row["id"]: row["clockwise"] for row in certificate["vertices"]}
        print(f"order {order:>3}  chain {'+'.join(RECIPES[order]):<10} "
              f"3-connected={cn.is_three_connected(rotation)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
