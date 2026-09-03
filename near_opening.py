#!/usr/bin/env python3
"""Import, score, and rank deterministic public near-opening block seeds.

The public input remains a closed APG.  A seed deletes two named closure fans
from its exact planar-code rotation, but deliberately does not require the
opened map to be a strict block.  Scores are diagnostics only: a zero is always
revalidated by both independent block implementations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path
from typing import Iterable

import block_tools as bt
import blocks
import import_planar_code
import map_search
import verify


FORMAT = "apg-near-opening-seed-v1"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def import_rotation(path: Path, expected_sha256: str) -> blocks.Rotation:
    actual = file_sha256(path)
    if actual != expected_sha256:
        raise ValueError(
            f"source SHA-256 mismatch for {path}: expected {expected_sha256}, got {actual}"
        )
    rows = import_planar_code.decode_first(path)
    rotation = blocks.normalize_rotation(
        {vertex: row for vertex, row in enumerate(rows, start=1)}
    )
    verify.verify_certificate(blocks.rotation_to_certificate(rotation))
    return rotation


def _fan_payload(fan: blocks.ClosureFan) -> dict[str, object]:
    return {"hub": fan.hub, "leaves": list(fan.leaves)}


def _fan_from_values(hub: int, leaves: Iterable[int]) -> blocks.ClosureFan:
    pair = tuple(sorted(leaves))
    if len(pair) != 2 or pair[0] == pair[1]:
        raise ValueError("a fan must name two distinct leaves")
    return blocks.ClosureFan(hub, pair)


def _hexagons(fixed: map_search.FixedMap, alpha: list[int]) -> list[list[int]]:
    faces, _ = map_search._faces(fixed, alpha)
    return [
        [fixed.dart_vertex[dart] + 1 for dart in face]
        for face in faces
        if len(face) == 6
    ]


def _state_sha256(alpha: list[int]) -> str:
    encoded = json.dumps(alpha, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def open_fans(
    rotation: blocks.Rotation,
    first: blocks.ClosureFan,
    second: blocks.ClosureFan,
) -> blocks.Rotation:
    available = set(blocks.candidate_closure_fans(rotation))
    if first not in available or second not in available:
        raise blocks.BlockError("named fan is not a closure-fan candidate")
    if first.whites.intersection(second.whites):
        raise blocks.BlockError("closure fans are not vertex-disjoint")
    return blocks._delete_edges(rotation, (*first.edges, *second.edges))


def score_opening(
    rotation: blocks.Rotation,
    first: blocks.ClosureFan,
    second: blocks.ClosureFan,
) -> tuple[blocks.Rotation, dict[str, int], list[int], map_search.FixedMap]:
    opened = open_fans(rotation, first, second)
    fixed, alpha = map_search.rotation_to_map(
        {vertex: list(neighbors) for vertex, neighbors in opened.items()}
    )
    return opened, map_search.score_breakdown(fixed, alpha), alpha, fixed


def make_seed(
    path: Path,
    *,
    expected_sha256: str,
    source_url: str,
    first: blocks.ClosureFan,
    second: blocks.ClosureFan,
) -> dict[str, object]:
    rotation = import_rotation(path, expected_sha256)
    opened, breakdown, alpha, fixed = score_opening(rotation, first, second)
    return {
        "format": FORMAT,
        "source": {
            "file": path.name,
            "order": len(rotation),
            "sha256": expected_sha256,
            "url": source_url,
            "verified_apg": True,
        },
        "fans": [_fan_payload(first), _fan_payload(second)],
        "source_rotation": blocks.rotation_to_certificate(rotation)["vertices"],
        "opened_rotation": blocks.rotation_to_certificate(opened)["vertices"],
        "score_breakdown": breakdown,
        "state_sha256": _state_sha256(alpha),
        "hexagons": _hexagons(fixed, alpha),
        "claim_scope": "Diagnostic near-opening seed; not a strict block witness.",
    }


def state_from_seed(seed: dict[str, object]) -> tuple[map_search.FixedMap, list[int]]:
    if seed.get("format") != FORMAT:
        raise ValueError(f"near-opening format must be {FORMAT!r}")
    rotation = bt._rotation_from_rows(seed.get("opened_rotation"))
    fixed, alpha = map_search.rotation_to_map(rotation)
    breakdown = map_search.score_breakdown(fixed, alpha)
    if breakdown != seed.get("score_breakdown"):
        raise ValueError("near-opening score does not reproduce")
    if _state_sha256(alpha) != seed.get("state_sha256"):
        raise ValueError("near-opening alpha hash does not reproduce")
    return fixed, alpha


def rank_openings(
    path: Path, expected_sha256: str, source_url: str = ""
) -> dict[str, object]:
    rotation = import_rotation(path, expected_sha256)
    fans = blocks.candidate_closure_fans(rotation)
    records: list[dict[str, object]] = []
    for first, second in combinations(fans, 2):
        if first.whites.intersection(second.whites):
            continue
        opened, breakdown, alpha, _ = score_opening(rotation, first, second)
        independent_zero = None
        if breakdown["total"] == 0:
            bt_ok = blocks_ok = False
            try:
                bt.block_from_rotation(
                    {vertex: list(neighbors) for vertex, neighbors in opened.items()}
                )
                bt_ok = True
            except bt.BlockError:
                pass
            try:
                blocks.validate_block(opened)
                blocks_ok = True
            except blocks.BlockError:
                pass
            independent_zero = {"block_tools": bt_ok, "blocks": blocks_ok}
        records.append(
            {
                "fans": [_fan_payload(first), _fan_payload(second)],
                "score_breakdown": breakdown,
                "state_sha256": _state_sha256(alpha),
                "zero_validation": independent_zero,
            }
        )
    records.sort(
        key=lambda record: (
            record["score_breakdown"]["total"],
            tuple(
                (fan["hub"], *fan["leaves"])
                for fan in record["fans"]
            ),
            record["state_sha256"],
        )
    )
    return {
        "source_file": path.name,
        "source_sha256": expected_sha256,
        "source_url": source_url,
        "order": len(rotation),
        "fan_candidates": len(fans),
        "disjoint_fan_pairs": len(records),
        "records": records,
    }


def _parse_fan(value: str) -> blocks.ClosureFan:
    try:
        hub_text, leaves_text = value.split(":", 1)
        leaves = [int(item) for item in leaves_text.split(",")]
        return _fan_from_values(int(hub_text), leaves)
    except (TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError("fan must be HUB:LEAF,LEAF") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--source-url", default="")
    parser.add_argument("--fan", action="append", type=_parse_fan, default=[])
    parser.add_argument("--rank", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.rank:
        if args.fan:
            parser.error("--rank and --fan are mutually exclusive")
        payload = rank_openings(args.source, args.sha256, args.source_url)
    else:
        if len(args.fan) != 2:
            parser.error("exactly two --fan arguments are required")
        payload = make_seed(
            args.source,
            expected_sha256=args.sha256,
            source_url=args.source_url,
            first=args.fan[0],
            second=args.fan[1],
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
