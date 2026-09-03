#!/usr/bin/env python3
"""Linux-only final exact radius-3 expansion of the order-34 frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import block_tools as bt
import map_search
import near_open_beam
import near_open_order34_radius2
import near_opening


FRONTIER_SIZE = 64
EXPECTED_PARENT_MANIFEST_SHA256 = (
    "749a08fb462ac4655ab8ac16c2cd4f98da1e32a2bb538edf75f00b268a26e694"
)
EXPECTED_ATTEMPTS = 242048


def parent_manifest_sha256(states: list[dict[str, object]]) -> str:
    payload = [
        {
            "state_sha256": state["state_sha256"],
            "score_breakdown": state["breakdown"],
        }
        for state in states
    ]
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def load_order34_radius2_frontier(
    seed_path: Path,
    seed: dict[str, object],
    k4_log: dict[str, object],
    radius2_log: dict[str, object],
) -> tuple[map_search.FixedMap, list[dict[str, object]]]:
    """Replay every recorded order-34 radius-2 parent hash and score."""

    fixed, k4_parents = near_open_order34_radius2.load_order34_k4_frontier(
        seed_path, seed, k4_log
    )
    result = radius2_log.get("result")
    if not isinstance(result, dict) or not result.get("complete"):
        raise ValueError("order-34 radius-2 result is absent or incomplete")
    if result.get("parent_state_hashes") != [
        parent["state_sha256"] for parent in k4_parents
    ]:
        raise ValueError("order-34 radius-2 parent hashes do not reproduce")
    states = result.get("frontier_states")
    if not isinstance(states, list) or len(states) != FRONTIER_SIZE:
        raise ValueError("order-34 radius-2 frontier must contain 64 states")
    keys: list[tuple[int, str]] = []
    for state in states:
        alpha = state.get("alpha")
        if not isinstance(alpha, list) or len(alpha) != len(fixed.dart_vertex):
            raise ValueError("order-34 radius-2 frontier alpha is malformed")
        digest = near_opening._state_sha256(alpha)
        if digest != state.get("state_sha256"):
            raise ValueError("order-34 radius-2 frontier hash does not reproduce")
        breakdown = map_search.score_breakdown(fixed, alpha)
        if breakdown != state.get("breakdown"):
            raise ValueError("order-34 radius-2 frontier score does not reproduce")
        if not map_search._abstract_graph_ok(fixed, alpha):
            raise ValueError("order-34 radius-2 frontier is not graph-valid")
        keys.append((breakdown["total"], digest))
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise ValueError("order-34 radius-2 frontier is not ordered and distinct")
    manifest = parent_manifest_sha256(states)
    if manifest != EXPECTED_PARENT_MANIFEST_SHA256:
        raise ValueError(f"order-34 radius-2 manifest changed: {manifest}")
    return fixed, states


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("near_open_order34_radius3.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=Path)
    parser.add_argument("--k4-log", required=True, type=Path)
    parser.add_argument("--radius2-log", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    k4_log = json.loads(args.k4_log.read_text(encoding="utf-8"))
    radius2_log = json.loads(args.radius2_log.read_text(encoding="utf-8"))
    fixed, parents = load_order34_radius2_frontier(
        args.seed, seed, k4_log, radius2_log
    )
    successes, stats = near_open_beam.expand_two_edge_beam(fixed, parents)
    expected_attempts = (
        stats["parent_states_expanded"]
        * stats["edge_pairs_per_parent"]
        * stats["pairings_per_edge_pair"]
    )
    self_check = {
        "kernel_is_linux": platform.system() == "Linux",
        "source_hash_matches": seed["source"]["sha256"]
        == near_open_order34_radius2.EXPECTED_SOURCE_SHA256,
        "seed_file_hash_matches": near_open_order34_radius2.file_sha256(args.seed)
        == near_open_order34_radius2.EXPECTED_SEED_FILE_SHA256,
        "seed_state_hash_matches": seed["state_sha256"]
        == near_open_order34_radius2.EXPECTED_SEED_STATE_SHA256,
        "parent_frontier_replayed": len(parents) == FRONTIER_SIZE,
        "parent_manifest_matches": parent_manifest_sha256(parents)
        == EXPECTED_PARENT_MANIFEST_SHA256,
        "edges_per_parent": stats["edges_per_parent"],
        "edge_pairs_per_parent": stats["edge_pairs_per_parent"],
        "pairings_per_edge_pair": stats["pairings_per_edge_pair"],
        "expected_transition_attempts": expected_attempts,
        "transition_count_matches": stats["counts"]["transition_attempts"]
        == expected_attempts
        == EXPECTED_ATTEMPTS,
        "complete": stats["complete"],
    }
    required = {
        "kernel_is_linux": True,
        "source_hash_matches": True,
        "seed_file_hash_matches": True,
        "seed_state_hash_matches": True,
        "parent_frontier_replayed": True,
        "parent_manifest_matches": True,
        "edges_per_parent": near_open_order34_radius2.EXPECTED_EDGES_PER_PARENT,
        "edge_pairs_per_parent": near_open_order34_radius2.EXPECTED_EDGE_PAIRS_PER_PARENT,
        "pairings_per_edge_pair": 2,
        "expected_transition_attempts": EXPECTED_ATTEMPTS,
        "transition_count_matches": True,
        "complete": True,
    }
    if self_check != required:
        raise AssertionError(f"order-34 radius-3 self-check failed: {self_check}")
    for index, block in enumerate(successes):
        bt.write_json(args.output_directory / f"block_{index:04d}.json", block)
    replay = (
        f"python3 near_open_order34_radius3.py --seed {args.seed} "
        f"--k4-log {args.k4_log} --radius2-log {args.radius2_log} "
        f"--output-directory {args.output_directory} --log {args.log}"
    )
    bt.write_json(
        args.log,
        {
            "claim_scope": (
                "Complete final exact two-edge radius-3 expansion of all 64 "
                "states in the recorded order-34 radius-2 frontier. A miss is "
                "bounded to this seed family and is not nonexistence."
            ),
            "decision": {
                "order34_seed_family_closed": not successes,
                "next_radius_started": False,
                "radius4_forbidden_by_operator": True,
                "reason": (
                    "Witness found; stop for verification/reporting."
                    if successes
                    else "No witness at final bounded radius 3; close this order-34 seed family regardless of numeric improvement."
                ),
            },
            "source": radius2_log["source"],
            "seed_file_sha256": near_open_order34_radius2.file_sha256(args.seed),
            "fans": radius2_log["fans"],
            "environment": {
                "hostname": platform.node(),
                "kernel": platform.platform(),
            },
            "replay": replay,
            "self_check": self_check,
            "result": stats,
        },
    )
    print(
        f"PASS order34 radius3 complete={stats['complete']} "
        f"successes={len(successes)} best_score={stats['best_score']} "
        f"log={args.log}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
