#!/usr/bin/env python3
"""Census of the 19 public APG source embeddings used by the opening scan.

The census is deliberately source-indexed and deterministic.  It verifies the
raw planar-code bytes against the recorded SHA-256 manifest, reconstructs the
rotation system, and records exact structural signatures before any opening
fan is considered.  A zero opening count is only a bounded source-corpus
result; it is not a nonexistence statement for blocks.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import blocks
import verify
from import_planar_code import decode_first
from structural_audit import (
    _edge_formula,
    _h55_components,
    _matrix,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_MANIFEST = ROOT / "results" / "logs" / "milestone3_alternative_order_opening_scan.json"
DEFAULT_SOURCE_DIR = ROOT / "certificates" / "census_sources"


def _display_path(path: Path) -> str:
    """Keep default artifact paths portable across checkouts."""

    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def _load_manifest(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records = data.get("records") if isinstance(data, dict) else None
    if not isinstance(records, list) or len(records) != 19:
        raise ValueError("the alternative-order manifest must contain 19 records")
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("manifest records must be objects")
        required = {"file", "order", "raw_sha256", "source_url"}
        if not required.issubset(record):
            raise ValueError(f"manifest record is missing one of {sorted(required)}")
    return records


def _rotation_from_planar_code(path: Path) -> blocks.Rotation:
    rotations = decode_first(path)
    return blocks.normalize_rotation(
        {vertex: tuple(neighbors) for vertex, neighbors in enumerate(rotations, start=1)}
    )


def _closed_stats(rotation: blocks.Rotation) -> dict[str, Any]:
    trace = blocks.trace_faces(rotation)
    faces = trace.faces
    degrees = {vertex: len(neighbors) for vertex, neighbors in rotation.items()}
    order = len(rotation)
    edges = sum(degrees.values()) // 2
    vertex_counts = dict(sorted(Counter(degrees.values()).items()))
    face_counts = dict(sorted(Counter(map(len, faces)).items()))
    r = vertex_counts.get(3, 0)

    vertex_pentagons = {
        vertex: sum(vertex in face for face in faces if len(face) == 5)
        for vertex, degree in degrees.items()
        if degree == 5
    }
    face_degree5 = {
        index: sum(degrees[vertex] == 5 for vertex in face)
        for index, face in enumerate(faces)
        if len(face) == 5
    }
    t_vertex = sum(value == 1 for value in vertex_pentagons.values())
    t_face = sum(value == 1 for value in face_degree5.values())

    corner_counts: Counter[tuple[int, int]] = Counter()
    for face in faces:
        for vertex in face:
            corner_counts[(degrees[vertex], len(face))] += 1
    corner_matrix = [
        [corner_counts[(degree, size)] for size in (3, 4, 5)]
        for degree in (3, 4, 5)
    ]

    edge_counts: Counter[tuple[tuple[int, int], tuple[int, int]]] = Counter()
    for vertex, neighbors in rotation.items():
        for neighbor in neighbors:
            if vertex >= neighbor:
                continue
            left_face = trace.face_of[(vertex, neighbor)]
            right_face = trace.face_of[(neighbor, vertex)]
            endpoint_type = tuple(sorted((degrees[vertex], degrees[neighbor])))
            face_type = tuple(
                sorted((len(faces[left_face]), len(faces[right_face])))
            )
            edge_counts[(endpoint_type, face_type)] += 1
    edge_matrix = _matrix(edge_counts)
    h55 = _h55_components(faces, degrees)

    fans = blocks.candidate_closure_fans(rotation)
    disjoint_pairs = [
        (first, second)
        for first, second in itertools.combinations(fans, 2)
        if not first.whites.intersection(second.whites)
    ]
    strict_blocks = blocks.opening_scan(rotation)
    relaxed_blocks = blocks.relaxed_opening_scan(rotation)
    mirrored = blocks.mirror_rotation(rotation)
    mirrored_strict_blocks = blocks.opening_scan(mirrored)
    mirrored_relaxed_blocks = blocks.relaxed_opening_scan(mirrored)
    signature = {
        "r": r,
        "t_vertex": t_vertex,
        "t_face": t_face,
        "h55_component_sizes": [component["node_count"] for component in h55],
        "fan_candidates": len(fans),
        "disjoint_fan_pairs": len(disjoint_pairs),
        "strict_blocks": len(strict_blocks),
        "relaxed_openings": len(relaxed_blocks),
        "mirrored_strict_blocks": len(mirrored_strict_blocks),
        "mirrored_relaxed_openings": len(mirrored_relaxed_blocks),
    }
    return {
        "order": order,
        "edges": edges,
        "faces": len(faces),
        "euler": order - edges + len(faces),
        "vertex_counts": vertex_counts,
        "face_counts": face_counts,
        "r": r,
        "t_vertex": t_vertex,
        "t_face": t_face,
        "corner_matrix": corner_matrix,
        "edge_matrix": edge_matrix,
        "edge_formula": _edge_formula(order, r, t_vertex),
        "edge_formula_matches": edge_matrix == _edge_formula(order, r, t_vertex),
        "h55_components": list(h55),
        "signature": signature,
        "relaxed_openings": len(relaxed_blocks),
        "mirrored_strict_openings": len(mirrored_strict_blocks),
        "mirrored_relaxed_openings": len(mirrored_relaxed_blocks),
    }


def build_census(
    *, manifest_path: Path = DEFAULT_MANIFEST,
    source_dir: Path = DEFAULT_SOURCE_DIR,
) -> dict[str, Any]:
    records = _load_manifest(manifest_path)
    output_records: list[dict[str, Any]] = []
    for record in records:
        filename = str(record["file"])
        path = source_dir / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        raw = path.read_bytes()
        raw_sha256 = hashlib.sha256(raw).hexdigest()
        if raw_sha256 != record["raw_sha256"]:
            raise ValueError(
                f"{filename}: SHA-256 {raw_sha256} != manifest {record['raw_sha256']}"
            )
        rotation = _rotation_from_planar_code(path)
        certificate = blocks.rotation_to_certificate(rotation)
        try:
            summary = verify.verify_certificate(
                certificate, expected_order=int(record["order"])
            )
        except (verify.VerificationError, ValueError) as exc:
            output_records.append(
                {
                    "file": filename,
                    "source_url": record["source_url"],
                    "raw_sha256": raw_sha256,
                    "verified": False,
                    "verification_error": str(exc),
                }
            )
            continue

        output_records.append(
            {
                "file": filename,
                "source_url": record["source_url"],
                "raw_sha256": raw_sha256,
                "verified": True,
                "stats": _closed_stats(rotation),
            }
        )

    valid = [record for record in output_records if record["verified"]]
    strict_total = sum(
        int(record["stats"]["signature"]["strict_blocks"]) for record in valid
    )
    signature_groups: Counter[str] = Counter(
        json.dumps(record["stats"]["signature"], sort_keys=True)
        for record in valid
    )
    grouped = [
        {"count": count, "signature": json.loads(signature)}
        for signature, count in sorted(signature_groups.items())
    ]
    return {
        "claim_scope": (
            "Census of the 19 manifest-listed public source embeddings only; "
            "zero strict openings is not block nonexistence."
        ),
        "manifest": _display_path(manifest_path),
        "source_dir": _display_path(source_dir),
        "records": output_records,
        "summary": {
            "published_embeddings": len(output_records),
            "verified_embeddings": len(valid),
            "verification_failures": len(output_records) - len(valid),
            "strict_blocks_total": strict_total,
            "signature_groups": grouped,
        },
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(sys.argv[1:] if argv is None else argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    result = build_census(manifest_path=args.manifest, source_dir=args.source_dir)
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
