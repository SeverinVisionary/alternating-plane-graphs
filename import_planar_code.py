#!/usr/bin/env python3
"""One-way fixture importer: first planar_code graph to normalized JSON.

This is only a provenance aid for published known-answer fixtures.  Candidate
certificates are verified directly by verify.py and never depend on this file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


HEADER = b">>planar_code<<"
FORMAT = "apg-plane-rotation-v1"


def _read_uint(data: bytes, offset: int, width: int) -> tuple[int, int]:
    end = offset + width
    if end > len(data):
        raise ValueError("truncated planar_code integer")
    return int.from_bytes(data[offset:end], "big"), end


def decode_first(path: Path) -> list[list[int]]:
    data = path.read_bytes()
    offset = 0
    if data.startswith(HEADER):
        offset = len(HEADER)
    if offset >= len(data):
        raise ValueError("planar_code file contains no graph")

    marker = data[offset]
    offset += 1
    if marker:
        order = marker
        width = 1
    else:
        order, offset = _read_uint(data, offset, 2)
        width = 2
    if order <= 0:
        raise ValueError("invalid zero order")

    rotations: list[list[int]] = []
    for _ in range(order):
        neighbors: list[int] = []
        while True:
            value, offset = _read_uint(data, offset, width)
            if value == 0:
                break
            neighbors.append(value)
        if neighbors:
            minimum = min(neighbors)
            start = neighbors.index(minimum)
            neighbors = neighbors[start:] + neighbors[:start]
        rotations.append(neighbors)
    return rotations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rotations = decode_first(args.input)
    certificate = {
        "format": FORMAT,
        "vertices": [
            {"clockwise": neighbors, "id": vertex}
            for vertex, neighbors in enumerate(rotations, start=1)
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
