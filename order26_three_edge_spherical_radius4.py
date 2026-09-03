#!/usr/bin/env python3
"""Linux-only exact k3 expansion of the 64-state spherical radius-3 frontier."""

from __future__ import annotations

import argparse
import json
import math
import platform
import time
from pathlib import Path

import block_tools as bt
import map_search
import order26_three_edge_spherical_radius3 as shared
import three_edge_rematch as k3


canonical_manifest = shared.canonical_manifest
manifest_sha256 = shared.manifest_sha256


def load_spec(path: Path, *, require_state_hash: bool = True) -> dict[str, object]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("format") != "apg-three-edge-spherical-radius4-v1":
        raise ValueError("unsupported spherical radius-4 specification")
    required = {
        "claim_scope",
        "input_commit",
        "parent_result_file",
        "parent_result_sha256",
        "parent_frontier_manifest_sha256",
        "fixed_state_file",
        "fixed_state_sha256",
        "fixed_rotation_hash",
        "base_alpha_sha256",
        "parent_count",
        "parent_score_histogram",
        "edges_per_parent",
        "triples_per_parent",
        "total_triples",
        "matchings_per_triple",
        "total_attempts",
        "frontier_limit",
        "target_state_file",
        "target_state_sha256",
        "stage_log",
        "result_log",
        "certificate_directory",
    }
    if not required.issubset(spec):
        raise ValueError("spherical radius-4 specification is incomplete")
    if spec["parent_count"] != 64:
        raise ValueError("radius 4 requires exactly 64 parents")
    if spec["parent_score_histogram"] != {"510": 4, "780": 60}:
        raise ValueError("parent score composition changed")
    if spec["edges_per_parent"] != 46:
        raise ValueError("edge count changed")
    triples = math.comb(46, 3)
    if triples != 15_180 or spec["triples_per_parent"] != triples:
        raise ValueError("triples-per-parent identity changed")
    total_triples = 64 * triples
    if total_triples != 971_520 or spec["total_triples"] != total_triples:
        raise ValueError("total triple identity changed")
    if spec["matchings_per_triple"] != 8:
        raise ValueError("deranged matching count changed")
    total_attempts = total_triples * 8
    if total_attempts != 7_772_160 or spec["total_attempts"] != total_attempts:
        raise ValueError("total attempt identity changed")
    if spec["frontier_limit"] != 64:
        raise ValueError("frontier limit must be exactly 64")
    if require_state_hash and (
        not isinstance(spec["target_state_sha256"], str)
        or len(spec["target_state_sha256"]) != 64
    ):
        raise ValueError("target state SHA-256 is not frozen")
    return spec


def build_radius4_state(spec: dict[str, object], root: Path) -> dict[str, object]:
    return shared.build_radius3_state(spec, root)


def load_radius4_parents(
    state_path: Path,
) -> tuple[map_search.FixedMap, list[list[int]], dict[str, object]]:
    fixed, parents, payload = k3.load_state_file(state_path)
    if len(parents) != 64:
        raise ValueError("radius 4 requires exactly 64 parents")
    for state, alpha in zip(payload["states"], parents):
        if not state.get("abstract_graph_valid"):
            raise ValueError("radius-4 parent is not abstract-valid")
        if not state.get("spherical") or state.get("euler_characteristic") != 2:
            raise ValueError("nonspherical state cannot enter radius 4")
        if k3.plane_valid_gate(fixed, alpha) != (True, None):
            raise ValueError("radius-4 parent fails the exact plane gate")
    return fixed, parents, payload


def validate_result(spec: dict[str, object], result: dict[str, object]) -> None:
    shared.validate_result(spec, result)


def environment_record() -> dict[str, object]:
    return {"hostname": platform.node(), "uname": platform.uname()._asdict()}


def stage(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    root = Path(__file__).resolve().parent
    payload = build_radius4_state(spec, root)
    state_path = root / spec["target_state_file"]
    bt.write_json(state_path, payload)
    state_hash = k3.file_sha256(state_path)
    if state_hash != spec["target_state_sha256"]:
        raise ValueError("generated radius-4 state hash changed")
    load_radius4_parents(state_path)
    record = {
        "format": "apg-three-edge-spherical-radius4-stage-v1",
        "environment": environment_record(),
        "replay": f"python3 order26_three_edge_spherical_radius4.py stage --spec {spec_path}",
        "spec": str(spec_path),
        "spec_sha256": k3.file_sha256(spec_path),
        "target_state_file": spec["target_state_file"],
        "target_state_sha256": state_hash,
        "parent_frontier_manifest_sha256": spec["parent_frontier_manifest_sha256"],
        "identities": {
            "parents": 64,
            "scores": spec["parent_score_histogram"],
            "edges_per_parent": 46,
            "triples_per_parent": 15_180,
            "total_triples": 971_520,
            "matchings_per_triple": 8,
            "total_attempts": 7_772_160,
        },
    }
    bt.write_json(root / spec["stage_log"], record)
    return record


def run(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    root = Path(__file__).resolve().parent
    state_path = root / spec["target_state_file"]
    if k3.file_sha256(state_path) != spec["target_state_sha256"]:
        raise ValueError("radius-4 target state file hash changed")
    fixed, parents, _ = load_radius4_parents(state_path)
    started = time.monotonic()
    result, successes = k3.enumerate_three_edge_rematchings(
        fixed, parents, selected_triple=None, frontier_limit=64
    )
    validate_result(spec, result)
    certificates = {}
    for block_hash in sorted(successes):
        path = root / spec["certificate_directory"] / f"{block_hash}.json"
        bt.write_json(path, successes[block_hash])
        certificates[block_hash] = {
            "path": str(path.relative_to(root)),
            "sha256": k3.file_sha256(path),
        }
    record = {
        "format": "apg-three-edge-spherical-radius4-result-v1",
        "claim_scope": spec["claim_scope"],
        "environment": environment_record(),
        "replay": f"python3 order26_three_edge_spherical_radius4.py run --spec {spec_path}",
        "spec": str(spec_path),
        "spec_sha256": k3.file_sha256(spec_path),
        "target_state_file": spec["target_state_file"],
        "target_state_sha256": k3.file_sha256(state_path),
        "certificates": certificates,
        "result": result,
        "driver_wall_seconds": time.monotonic() - started,
    }
    bt.write_json(root / spec["result_log"], record)
    return record


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("order26_three_edge_spherical_radius4.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("stage", "run"):
        child = subparsers.add_parser(command)
        child.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "stage":
        record = stage(args.spec)
        print(
            f"PASS staged parents={record['identities']['parents']} "
            f"attempts={record['identities']['total_attempts']}"
        )
        return 0
    record = run(args.spec)
    result = record["result"]
    print(
        f"PASS parents={result['parent_count']} attempts={result['counts']['attempts']} "
        f"distinct={result['counts']['distinct_graph_valid']} "
        f"best={result['best_score']} zero={result['counts']['score_zero']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
