#!/usr/bin/env python3
"""Linux-only exact k3 expansion of the 64-state spherical radius-2 frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import time
from pathlib import Path

import block_tools as bt
import map_search
import near_opening
import three_edge_rematch as k3


def canonical_manifest(frontier: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "state_sha256": state["state_sha256"],
            "breakdown": state["breakdown"],
        }
        for state in frontier
    ]


def manifest_sha256(frontier: list[dict[str, object]]) -> str:
    payload = (
        json.dumps(canonical_manifest(frontier), sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_spec(path: Path, *, require_state_hash: bool = True) -> dict[str, object]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("format") != "apg-three-edge-spherical-radius3-v1":
        raise ValueError("unsupported spherical radius-3 specification")
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
        raise ValueError("spherical radius-3 specification is incomplete")
    if spec["parent_count"] != 64:
        raise ValueError("radius 3 requires exactly 64 parents")
    if spec["parent_score_histogram"] != {"780": 6, "800": 58}:
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


def build_radius3_state(spec: dict[str, object], root: Path) -> dict[str, object]:
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
    result = parent_log.get("result", {})
    frontier = result.get("frontier_states")
    if not isinstance(frontier, list) or len(frontier) != 64:
        raise ValueError("parent frontier must contain exactly 64 states")
    if result.get("frontier_state_count") != 64 or not result.get("frontier_truncated"):
        raise ValueError("parent frontier metadata changed")
    if manifest_sha256(frontier) != spec["parent_frontier_manifest_sha256"]:
        raise ValueError("parent frontier manifest changed")
    ordering = [(state["breakdown"]["total"], state["state_sha256"]) for state in frontier]
    if ordering != sorted(ordering):
        raise ValueError("parent deterministic frontier ordering changed")
    scores = {key: 0 for key in spec["parent_score_histogram"]}
    states = []
    for state in frontier:
        alpha = state.get("alpha")
        if not isinstance(alpha, list):
            raise ValueError("parent alpha is absent")
        state_hash = near_opening._state_sha256(alpha)
        if state_hash != state.get("state_sha256"):
            raise ValueError("parent alpha hash changed")
        breakdown = map_search.score_breakdown(fixed, alpha)
        if breakdown != state.get("breakdown"):
            raise ValueError("parent breakdown changed")
        score_key = str(breakdown["total"])
        if score_key not in scores:
            raise ValueError("unexpected parent score")
        scores[score_key] += 1
        if not map_search._abstract_graph_ok(fixed, alpha):
            raise ValueError("parent is not abstract-valid")
        if k3.plane_valid_gate(fixed, alpha) != (True, None):
            raise ValueError("nonspherical state cannot enter radius 3")
        if k3.euler_characteristic(fixed, alpha) != 2:
            raise ValueError("parent Euler characteristic changed")
        if len(k3.edge_pairs(alpha)) != 46:
            raise ValueError("parent edge count changed")
        states.append(
            {
                "alpha": alpha,
                "state_sha256": state_hash,
                "breakdown": breakdown,
                "abstract_graph_valid": True,
                "spherical": True,
                "euler_characteristic": 2,
                "sphere_gate_reason": None,
            }
        )
    if scores != spec["parent_score_histogram"]:
        raise ValueError("parent score histogram changed")
    return {
        "format": "apg-fixed-alpha-state-v1",
        "claim_scope": spec["claim_scope"],
        "parent_result_file": spec["parent_result_file"],
        "parent_result_sha256": spec["parent_result_sha256"],
        "parent_frontier_manifest_sha256": spec["parent_frontier_manifest_sha256"],
        "fixed_state_file": spec["fixed_state_file"],
        "fixed_state_sha256": spec["fixed_state_sha256"],
        "fixed_rotation": fixed_payload["fixed_rotation"],
        "fixed_rotation_hash": fixed_payload["fixed_rotation_hash"],
        "base_alpha_sha256": fixed_payload["base_alpha_sha256"],
        "order": len(fixed.cycles),
        "edges": 46,
        "states": states,
    }


def load_radius3_parents(
    state_path: Path,
) -> tuple[map_search.FixedMap, list[list[int]], dict[str, object]]:
    fixed, parents, payload = k3.load_state_file(state_path)
    if len(parents) != 64:
        raise ValueError("radius 3 requires exactly 64 parents")
    for state, alpha in zip(payload["states"], parents):
        if not state.get("abstract_graph_valid"):
            raise ValueError("radius-3 parent is not abstract-valid")
        if not state.get("spherical") or state.get("euler_characteristic") != 2:
            raise ValueError("nonspherical state cannot enter radius 3")
        if k3.plane_valid_gate(fixed, alpha) != (True, None):
            raise ValueError("radius-3 parent fails the exact plane gate")
    return fixed, parents, payload


def validate_result(spec: dict[str, object], result: dict[str, object]) -> None:
    if result["parent_count"] != 64 or result["edges"] != 46:
        raise AssertionError("result parent or edge count changed")
    if result["triples"] != 971_520 or result["matchings_per_triple"] != 8:
        raise AssertionError("result transition identity changed")
    if result["expected_attempts"] != 7_772_160:
        raise AssertionError("result expected-attempt count changed")
    counts = result["counts"]
    if counts["attempts"] != spec["total_attempts"]:
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
    payload = build_radius3_state(spec, root)
    state_path = root / spec["target_state_file"]
    bt.write_json(state_path, payload)
    state_hash = k3.file_sha256(state_path)
    if state_hash != spec["target_state_sha256"]:
        raise ValueError("generated radius-3 state hash changed")
    load_radius3_parents(state_path)
    record = {
        "format": "apg-three-edge-spherical-radius3-stage-v1",
        "environment": environment_record(),
        "replay": f"python3 order26_three_edge_spherical_radius3.py stage --spec {spec_path}",
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
        raise ValueError("radius-3 target state file hash changed")
    fixed, parents, _ = load_radius3_parents(state_path)
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
        "format": "apg-three-edge-spherical-radius3-result-v1",
        "claim_scope": spec["claim_scope"],
        "environment": environment_record(),
        "replay": f"python3 order26_three_edge_spherical_radius3.py run --spec {spec_path}",
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
        raise SystemExit("order26_three_edge_spherical_radius3.py is Linux-only")
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
