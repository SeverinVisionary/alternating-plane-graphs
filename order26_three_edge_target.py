#!/usr/bin/env python3
"""Linux-only staging and exact execution for the order-26 k3 target gate."""

from __future__ import annotations

import argparse
import json
import math
import platform
import time
from pathlib import Path

import block_tools as bt
import frontier_anneal
import map_search
import near_opening
import three_edge_rematch as k3


def load_spec(path: Path, *, require_state_hash: bool = True) -> dict[str, object]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("format") != "apg-three-edge-target-spec-v1":
        raise ValueError("unsupported target specification")
    required = {
        "input_commit",
        "source",
        "seed_file",
        "seed_file_sha256",
        "base_state_sha256",
        "fixed_rotation_hash",
        "frontier_log",
        "frontier_log_sha256",
        "parent_state_sha256",
        "expected_parent_score",
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
        raise ValueError("target specification has missing explicit fields")
    if spec["mode"] != "all-triples":
        raise ValueError("target mode must be all-triples")
    parents = spec["parent_state_sha256"]
    if not isinstance(parents, list) or len(parents) != 6 or len(set(parents)) != 6:
        raise ValueError("exactly six unique parents are required")
    if spec["parent_count"] != 6 or spec["edges_per_parent"] != 46:
        raise ValueError("order-26 parent/edge counts changed")
    triples = math.comb(spec["edges_per_parent"], 3)
    if triples != 15_180 or spec["triples_per_parent"] != triples:
        raise ValueError("triples-per-parent identity changed")
    derived_total_triples = spec["parent_count"] * triples
    if spec["total_triples"] != derived_total_triples or derived_total_triples != 91_080:
        raise ValueError("total triple count changed")
    if spec["matchings_per_triple"] != 8:
        raise ValueError("deranged matching count changed")
    derived_total_attempts = spec["total_triples"] * spec["matchings_per_triple"]
    if spec["total_attempts"] != derived_total_attempts or derived_total_attempts != 728_640:
        raise ValueError("total attempt identity changed")
    if spec["frontier_limit"] != 64:
        raise ValueError("frontier limit must be exactly 64")
    if require_state_hash and (
        not isinstance(spec["target_state_sha256"], str)
        or len(spec["target_state_sha256"]) != 64
    ):
        raise ValueError("target state SHA-256 is not frozen")
    return spec


def build_target_state(spec: dict[str, object], root: Path) -> dict[str, object]:
    seed_path = root / spec["seed_file"]
    frontier_path = root / spec["frontier_log"]
    if k3.file_sha256(seed_path) != spec["seed_file_sha256"]:
        raise ValueError("seed file hash changed")
    if k3.file_sha256(frontier_path) != spec["frontier_log_sha256"]:
        raise ValueError("frontier log hash changed")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    if seed.get("source") != {**spec["source"], "verified_apg": True}:
        raise ValueError("seed source provenance changed")
    if seed.get("state_sha256") != spec["base_state_sha256"]:
        raise ValueError("seed base state hash changed")
    fixed, base_alpha = near_opening.state_from_seed(seed)
    if len(fixed.cycles) != spec["source"]["order"]:
        raise ValueError("seed order changed")
    if len(k3.edge_pairs(base_alpha)) != spec["edges_per_parent"]:
        raise ValueError("seed edge count changed")
    if near_opening._state_sha256(base_alpha) != spec["base_state_sha256"]:
        raise ValueError("base alpha hash changed")
    opened_rotation = bt._rotation_from_rows(seed["opened_rotation"])
    replay_rotation = map_search.rotation_from_state(fixed, base_alpha)
    if opened_rotation != replay_rotation:
        raise ValueError("opened rotation does not replay from fixed map")
    fixed_rotation_hash = bt.canonical_map_hash({"vertices": seed["opened_rotation"]})
    if fixed_rotation_hash != spec["fixed_rotation_hash"]:
        raise ValueError("fixed rotation hash changed")

    states = []
    for state_hash in spec["parent_state_sha256"]:
        parent_fixed, alpha, record = frontier_anneal.load_frontier_state(
            seed_path,
            frontier_path,
            expected_seed_sha256=spec["seed_file_sha256"],
            state_sha256=state_hash,
        )
        if parent_fixed.cycles != fixed.cycles:
            raise ValueError("parent fixed vertex cycles changed")
        if record["score_breakdown"]["total"] != spec["expected_parent_score"]:
            raise ValueError("parent score changed")
        if len(k3.edge_pairs(alpha)) != spec["edges_per_parent"]:
            raise ValueError("parent edge count changed")
        abstract_valid = map_search._abstract_graph_ok(fixed, alpha)
        if not abstract_valid:
            raise ValueError("parent abstract-graph gate failed")
        spherical, reason = k3.plane_valid_gate(fixed, alpha)
        states.append(
            {
                "alpha": alpha,
                "state_sha256": state_hash,
                "breakdown": record["score_breakdown"],
                "graph_valid": True,
                "abstract_graph_valid": True,
                "spherical": spherical,
                "sphere_gate_reason": reason,
            }
        )
    return {
        "format": "apg-fixed-alpha-state-v1",
        "claim_scope": spec["claim_scope"],
        "source": spec["source"],
        "seed_file": spec["seed_file"],
        "seed_file_sha256": spec["seed_file_sha256"],
        "frontier_log": spec["frontier_log"],
        "frontier_log_sha256": spec["frontier_log_sha256"],
        "fixed_rotation": seed["opened_rotation"],
        "fixed_rotation_hash": fixed_rotation_hash,
        "base_alpha_sha256": near_opening._state_sha256(base_alpha),
        "order": len(fixed.cycles),
        "edges": len(k3.edge_pairs(base_alpha)),
        "states": states,
    }


def validate_result(spec: dict[str, object], result: dict[str, object]) -> None:
    if result["parent_count"] != spec["parent_count"]:
        raise AssertionError("result parent count changed")
    if result["edges"] != spec["edges_per_parent"]:
        raise AssertionError("result edge count changed")
    if result["triples"] != spec["total_triples"]:
        raise AssertionError("result triple count changed")
    if result["matchings_per_triple"] != spec["matchings_per_triple"]:
        raise AssertionError("result matching count changed")
    if result["expected_attempts"] != spec["total_attempts"]:
        raise AssertionError("result expected-attempt count changed")
    counts = result["counts"]
    if counts["attempts"] != spec["total_attempts"]:
        raise AssertionError("result did not exhaust every attempt")
    if counts["graph_invalid_prunes"] + counts["raw_graph_valid"] != counts["attempts"]:
        raise AssertionError("graph gate accounting is incomplete")
    if counts["duplicates"] + counts["distinct_graph_valid"] != counts["raw_graph_valid"]:
        raise AssertionError("global exact-state dedup accounting is incomplete")


def environment_record() -> dict[str, object]:
    return {"hostname": platform.node(), "uname": platform.uname()._asdict()}


def stage(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    root = Path(__file__).resolve().parent
    state_payload = build_target_state(spec, root)
    state_path = root / spec["target_state_file"]
    bt.write_json(state_path, state_payload)
    state_hash = k3.file_sha256(state_path)
    if state_hash != spec["target_state_sha256"]:
        raise ValueError("generated target state hash changed")
    replay = f"python3 order26_three_edge_target.py stage --spec {spec_path}"
    payload = {
        "format": "apg-three-edge-target-stage-v1",
        "environment": environment_record(),
        "replay": replay,
        "spec": str(spec_path),
        "spec_sha256": k3.file_sha256(spec_path),
        "target_state_file": spec["target_state_file"],
        "target_state_sha256": state_hash,
        "identities": {
            "parents": spec["parent_count"],
            "edges_per_parent": spec["edges_per_parent"],
            "triples_per_parent": spec["triples_per_parent"],
            "total_triples": spec["total_triples"],
            "matchings_per_triple": spec["matchings_per_triple"],
            "total_attempts": spec["total_attempts"],
        },
    }
    bt.write_json(root / spec["stage_log"], payload)
    return payload


def run(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    root = Path(__file__).resolve().parent
    state_path = root / spec["target_state_file"]
    if k3.file_sha256(state_path) != spec["target_state_sha256"]:
        raise ValueError("target state file hash changed")
    fixed, parents, _ = k3.load_state_file(state_path)
    started = time.monotonic()
    result, successes = k3.enumerate_three_edge_rematchings(
        fixed,
        parents,
        selected_triple=None,
        frontier_limit=spec["frontier_limit"],
    )
    validate_result(spec, result)
    certificate_directory = root / spec["certificate_directory"]
    certificates = {}
    for block_hash in sorted(successes):
        path = certificate_directory / f"{block_hash}.json"
        bt.write_json(path, successes[block_hash])
        certificates[block_hash] = {
            "path": str(path.relative_to(root)),
            "sha256": k3.file_sha256(path),
        }
    replay = f"python3 order26_three_edge_target.py run --spec {spec_path}"
    payload = {
        "format": "apg-three-edge-target-result-v1",
        "claim_scope": spec["claim_scope"],
        "environment": environment_record(),
        "replay": replay,
        "spec": str(spec_path),
        "spec_sha256": k3.file_sha256(spec_path),
        "target_state_file": spec["target_state_file"],
        "target_state_sha256": k3.file_sha256(state_path),
        "certificates": certificates,
        "result": result,
        "driver_wall_seconds": time.monotonic() - started,
    }
    bt.write_json(root / spec["result_log"], payload)
    return payload


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("order26_three_edge_target.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("stage", "run"):
        child = subparsers.add_parser(command)
        child.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "stage":
        payload = stage(args.spec)
        print(
            f"PASS staged parents={payload['identities']['parents']} "
            f"attempts={payload['identities']['total_attempts']}"
        )
        return 0
    payload = run(args.spec)
    result = payload["result"]
    print(
        f"PASS parents={result['parent_count']} attempts={result['counts']['attempts']} "
        f"distinct={result['counts']['distinct_graph_valid']} "
        f"best={result['best_score']} zero={result['counts']['score_zero']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
