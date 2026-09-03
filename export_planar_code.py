#!/usr/bin/env python3
"""Write a certificate out as planar_code, for checking by other people's tools.

Every verifier in this repository was written here, so an independent reader has
only our word that a certificate is the plane map we say it is.  planar_code is
the format `plantri`, House of Graphs and the source paper's authors all read,
so exporting to it lets a certificate be checked by software that has never seen
this project.  That is the point of this module; nothing here verifies anything.

`import_planar_code.decode_first` is the inverse, and it **canonicalises**: it
rotates each neighbour list to begin at its smallest entry.  That is a choice of
starting point, not a change of plane map -- a rotation system is cyclic, so any
starting point describes the same embedding.  This writer emits the same
canonical form, which makes decode-then-encode idempotent and lets the gates in
`test_export_planar_code.py` compare bytes rather than structures.

    python3 export_planar_code.py certificates/targets/TARGET_46.json out.plc
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HEADER = b">>planar_code<<"


def canonical(rotations: list[list[int]]) -> list[list[int]]:
    """Rotate each ring to start at its smallest entry, as the decoder does."""

    out = []
    for ring in rotations:
        if ring:
            start = ring.index(min(ring))
            ring = ring[start:] + ring[:start]
        out.append(list(ring))
    return out


def encode(rotations: list[list[int]], header: bool = True) -> bytes:
    """One graph in planar_code, one byte per integer.

    Refuses anything the one-byte encoding cannot represent rather than
    silently truncating: order and every vertex label must be at most 255.
    """

    order = len(rotations)
    if not 0 < order < 256:
        raise ValueError(f"order {order} is outside the one-byte planar_code range")
    for ring in rotations:
        for neighbour in ring:
            if not 0 < neighbour < 256:
                raise ValueError(f"vertex label {neighbour} is outside the one-byte range")
            if neighbour > order:
                raise ValueError(f"vertex label {neighbour} exceeds the order {order}")
    body = bytearray()
    body.append(order)
    for ring in canonical(rotations):
        body.extend(ring)
        body.append(0)
    return (HEADER if header else b"") + bytes(body)


def rotations_from_certificate(path: Path) -> list[list[int]]:
    """Neighbour rings in vertex-id order, as planar_code needs them.

    planar_code identifies a vertex by its position in the file, so this
    refuses a certificate whose ids are not exactly `1..n`; relabelling one
    silently would produce a file describing a different graph.
    """

    data = json.loads(Path(path).read_text())
    if data.get("format") != "apg-plane-rotation-v1":
        raise ValueError(f"{path} is not an apg-plane-rotation-v1 certificate")
    rings = {row["id"]: list(row["clockwise"]) for row in data["vertices"]}
    if sorted(rings) != list(range(1, len(rings) + 1)):
        raise ValueError(f"{path} does not label its vertices 1..n")
    return [rings[vertex] for vertex in range(1, len(rings) + 1)]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--no-header", action="store_true", help="omit >>planar_code<<")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        encode(rotations_from_certificate(args.certificate), header=not args.no_header)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
