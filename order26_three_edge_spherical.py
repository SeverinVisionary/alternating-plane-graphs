#!/usr/bin/env python3
"""Linux-only staging and execution from the order-26 spherical k3 frontier."""

from __future__ import annotations

import argparse
import json
import math
import platform
import time
from pathlib import Path

import block_tools as bt
import map_search
import near_opening
import three_edge_rematch as k3


def load_spec(path: Path, *, require_state_hash: bool = True) -> dict[str, object]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("format") != "apg-three-edge-spherical-continuation-v1":
        raise ValueError("unsupported spherical continuation specification")
    required = {
        "input_commit",
        "parent_result_file",
        "parent_result_sha256",
        "fixed_state_file",
        "fixed_state_sha256",
        "fixed_rotation_hash",
        "base_alpha_sha256",
        "parent_state_sha256",
        "expected_parent_score",
        "expected_parent_euler_characteristic",
        "mode",
        "parent_count",
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
        raise ValueError("spherical continuation specification is incomplete")
    parents = spec["parent_state_sha256"]
    if not isinstance(parents, list) or len(parents) != 6 or parents != sorted(parents):
        raise ValueError("six unique parents in deterministic hash order are required")
    if len(set(parents)) != 6:
        raise ValueError("spherical parents must be unique")
    if spec["mode"] != "all-triples":
        raise ValueError("continuation must use all-triples mode")
    if spec["parent_count"] != 6 or spec["edges_per_parent"] != 46:
        raise ValueError("parent or edge count changed")
    triples = math.comb(spec["edges_per_parent"], 3)
    if triples != 15_180 or spec["triples_per_parent"] != triples:
        raise ValueError("triples-per-parent identity changed")
    total_triples = spec["parent_count"] * triples
    if total_triples != 91_080 or spec["total_triples"] != total_triples:
        raise ValueError("total triple identity changed")
    if spec["matchings_per_triple"] != 8:
        raise ValueError("deranged matching count changed")
    total_attempts = total_triples * spec["matchings_per_triple"]
    if total_attempts != 728_640 or spec["total_attempts"] != total_attempts:
        raise ValueError("total attempt identity changed")
    if spec["frontier_limit"] != 64:
        raise ValueError("frontier limit must be exactly 64")
    if spec["expected_parent_euler_characteristic"] != 2:
        raise ValueError("spherical parents must have Euler characteristic 2")
    if require_state_hash and (
        not isinstance(spec["target_state_sha256"], str)
        or len(spec["target_state_sha256"]) != 64
    ):
        raise ValueError("target state SHA-256 is not frozen")
    return spec


def build_spherical_state(spec: dict[str, object], root: Path) -> dict[str, object]:
    result_path = root / spec["parent_result_file"]
    fixed_state_path = root / spec["fixed_state_file"]
    if k3.file_sha256(result_path) != spec["parent_result_sha256"]:
        raise ValueError("parent result file hash changed")
    if k3.file_sha256(fixed_state_path) != spec["fixed_state_sha256"]:
        raise ValueError("fixed state file hash changed")
    fixed, _, fixed_payload = k3.load_state_file(fixed_state_path)
    if fixed_payload["fixed_rotation_hash"] != spec["fixed_rotation_hash"]:
        raise ValueError("fixed rotation hash changed")
    if fixed_payload["base_alpha_sha256"] != spec["base_alpha_sha256"]:
        raise ValueError("base alpha hash changed")
    parent_log = json.loads(result_path.read_text(encoding="utf-8"))
    frontier = parent_log.get("result", {}).get("frontier_states")
    if not isinstance(frontier, list):
        raise ValueError("parent frontier is absent")
    by_hash = {state.get("state_sha256"): state for state in frontier}
    if len(by_hash) != len(frontier):
        raise ValueError("parent frontier contains duplicate hashes")
    if sorted(by_hash) != spec["parent_state_sha256"]:
        raise ValueError("parent frontier hash set changed")
    states = []
    for state_hash in spec["parent_state_sha256"]:
        state = by_hash[state_hash]
        alpha = state.get("alpha")
        if not isinstance(alpha, list):
            raise ValueError("parent alpha is absent")
        if near_opening._state_sha256(alpha) != state_hash:
            raise ValueError("parent alpha hash changed")
        breakdown = map_search.score_breakdown(fixed, alpha)
        if breakdown != state.get("breakdown") or breakdown["total"] != spec["expected_parent_score"]:
            raise ValueError("parent breakdown changed")
        abstract_valid = map_search._abstract_graph_ok(fixed, alpha)
        plane_valid, reason = k3.plane_valid_gate(fixed, alpha)
        euler = k3.euler_characteristic(fixed, alpha)
        if not abstract_valid or not plane_valid or reason is not None or euler != 2:
            raise ValueError("nonspherical state cannot enter spherical continuation")
        if len(k3.edge_pairs(alpha)) != spec["edges_per_parent"]:
            raise ValueError("parent edge count changed")
        states.append(
            {
                "alpha": alpha,
                "state_sha256": state_hash,
                "breakdown": breakdown,
                "graph_valid": True,
                "abstract_graph_valid": True,
                "spherical": True,
                "euler_characteristic": 2,
                "sphere_gate_reason": None,
            }
        )
    return {
        "format": "apg-fixed-alpha-state-v1",
        "claim_scope": spec["claim_scope"],
        "parent_result_file": spec["parent_result_file"],
        "parent_result_sha256": spec["parent_result_sha256"],
        "fixed_state_file": spec["fixed_state_file"],
        "fixed_state_sha256": spec["fixed_state_sha256"],
        "fixed_rotation": fixed_payload["fixed_rotation"],
        "fixed_rotation_hash": fixed_payload["fixed_rotation_hash"],
        "base_alpha_sha256": fixed_payload["base_alpha_sha256"],
        "order": len(fixed.cycles),
        "edges": len(k3.edge_pairs(states[0]["alpha"])),
        "states": states,
    }


def load_spherical_parents(
    state_path: Path,
) -> tuple[map_search.FixedMap, list[list[int]], dict[str, object]]:
    fixed, parents, payload = k3.load_state_file(state_path)
    for state, alpha in zip(payload["states"], parents):
        if not state.get("abstract_graph_valid"):
            raise ValueError("spherical parent is not abstract-valid")
        if not state.get("spherical") or state.get("euler_characteristic") != 2:
            raise ValueError("nonspherical state cannot enter spherical continuation")
        if k3.plane_valid_gate(fixed, alpha) != (True, None):
            raise ValueError("spherical parent fails the exact plane gate")
    return fixed, parents, payload


def validate_result(spec: dict[str, object], result: dict[str, object]) -> None:
    if result["parent_count"] != spec["parent_count"]:
        raise AssertionError("result parent count changed")
    if result["edges"] != spec["edges_per_parent"]:
        raise AssertionError("result edge count changed")
    if result["triples"] != spec["total_triples"]:
        raise AssertionError("result triple count changed")
    if result["matchings_per_triple"] != 8 or result["expected_attempts"] != 728_640:
        raise AssertionError("result transition identity changed")
    counts = result["counts"]
    if counts["attempts"] != 728_640:
        raise AssertionError("result did not exhaust every attempt")
    if counts["graph_invalid_prunes"] + counts["raw_graph_valid"] != counts["attempts"]:
        raise AssertionError("plane-gate accounting is incomplete")
    if counts["duplicates"] + counts["distinct_graph_valid"] != counts["raw_graph_valid"]:
        raise AssertionError("global exact-state dedup accounting is incomplete")


def environment_record() -> dict[str, object]:
    return {"hostname": platform.node(), "uname": platform.uname()._asdict()}


def stage(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    root = Path(__file__).resolve().parent
    payload = build_spherical_state(spec, root)
    state_path = root / spec["target_state_file"]
    bt.write_json(state_path, payload)
    state_hash = k3.file_sha256(state_path)
    if state_hash != spec["target_state_sha256"]:
        raise ValueError("generated spherical target state hash changed")
    load_spherical_parents(state_path)
    record = {
        "format": "apg-three-edge-spherical-stage-v1",
        "environment": environment_record(),
        "replay": f"python3 order26_three_edge_spherical.py stage --spec {spec_path}",
        "spec": str(spec_path),
        "spec_sha256": k3.file_sha256(spec_path),
        "target_state_file": spec["target_state_file"],
        "target_state_sha256": state_hash,
        "identities": {
            "parents": 6,
            "edges_per_parent": 46,
            "triples_per_parent": 15_180,
            "total_triples": 91_080,
            "matchings_per_triple": 8,
            "total_attempts": 728_640,
        },
    }
    bt.write_json(root / spec["stage_log"], record)
    return record


def run(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    root = Path(__file__).resolve().parent
    state_path = root / spec["target_state_file"]
    if k3.file_sha256(state_path) != spec["target_state_sha256"]:
        raise ValueError("spherical target state file hash changed")
    fixed, parents, _ = load_spherical_parents(state_path)
    started = time.monotonic()
    result, successes = k3.enumerate_three_edge_rematchings(
        fixed,
        parents,
        selected_triple=None,
        frontier_limit=spec["frontier_limit"],
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
        "format": "apg-three-edge-spherical-result-v1",
        "claim_scope": spec["claim_scope"],
        "environment": environment_record(),
        "replay": f"python3 order26_three_edge_spherical.py run --spec {spec_path}",
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
        raise SystemExit("order26_three_edge_spherical.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("stage", "run"):
        child = subparsers.add_parser(command)
        child.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "stage":
        record = stage(args.spec)
        print(f"PASS staged spherical parents={record['identities']['parents']} attempts={record['identities']['total_attempts']}")
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
