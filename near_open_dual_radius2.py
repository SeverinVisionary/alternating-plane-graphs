#!/usr/bin/env python3
"""Linux-only exact radius-2 expansion of the dual order-26 k4 frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import block_tools as bt
import map_search
import near_open_beam
import near_opening


FRONTIER_SIZE = 64
EXPECTED_SOURCE_SHA256 = (
    "adf39c3bb116a259efedaa6f9bb5c42734f262652dbe3fafd8fe5aafec17799c"
)
EXPECTED_SEED_STATE_SHA256 = (
    "27d8e3b580147da90d04e1be6340f3401f7a33f665fe82012cbef1234050b1b5"
)
EXPECTED_PARENT_MANIFEST_SHA256 = (
    "9554901a8d5a265f5a8f48c174d0f031f06255d24df66ecf05fa3dba694b1e7f"
)
EXPECTED_ATTEMPTS = 132480


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


def load_dual_k4_frontier(
    seed: dict[str, object], k4_log: dict[str, object]
) -> tuple[map_search.FixedMap, list[dict[str, object]]]:
    """Replay the exact dual seed and all 64 recorded k4 frontier states."""

    source = seed.get("source")
    if not isinstance(source, dict):
        raise ValueError("dual seed source is absent")
    if source.get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("dual seed source hash changed")
    if seed.get("state_sha256") != EXPECTED_SEED_STATE_SHA256:
        raise ValueError("dual seed state hash changed")
    log_source = k4_log.get("source")
    if not isinstance(log_source, dict):
        raise ValueError("dual k4 source is absent")
    if log_source.get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("dual k4 source hash changed")
    if log_source.get("state_sha256") != EXPECTED_SEED_STATE_SHA256:
        raise ValueError("dual k4 seed-state hash changed")
    fixed, parents = near_open_beam.load_frontier(seed, k4_log)
    if len(parents) != FRONTIER_SIZE:
        raise ValueError("dual k4 frontier must contain exactly 64 states")
    manifest = parent_manifest_sha256(parents)
    if manifest != EXPECTED_PARENT_MANIFEST_SHA256:
        raise ValueError(f"dual k4 frontier manifest changed: {manifest}")
    return fixed, parents


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("near_open_dual_radius2.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=Path)
    parser.add_argument("--k4-log", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    k4_log = json.loads(args.k4_log.read_text(encoding="utf-8"))
    fixed, parents = load_dual_k4_frontier(seed, k4_log)
    successes, stats = near_open_beam.expand_two_edge_beam(fixed, parents)
    expected_attempts = (
        stats["parent_states_expanded"]
        * stats["edge_pairs_per_parent"]
        * stats["pairings_per_edge_pair"]
    )
    self_check = {
        "kernel_is_linux": platform.system() == "Linux",
        "source_hash_matches": seed["source"]["sha256"]
        == EXPECTED_SOURCE_SHA256,
        "seed_state_hash_matches": seed["state_sha256"]
        == EXPECTED_SEED_STATE_SHA256,
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
        "seed_state_hash_matches": True,
        "parent_frontier_replayed": True,
        "parent_manifest_matches": True,
        "edges_per_parent": 46,
        "edge_pairs_per_parent": 1035,
        "pairings_per_edge_pair": 2,
        "expected_transition_attempts": EXPECTED_ATTEMPTS,
        "transition_count_matches": True,
        "complete": True,
    }
    if self_check != required:
        raise AssertionError(f"dual radius-2 Linux self-check failed: {self_check}")
    for index, block in enumerate(successes):
        bt.write_json(args.output_directory / f"block_{index:04d}.json", block)
    replay = (
        f"python3 near_open_dual_radius2.py --seed {args.seed} "
        f"--k4-log {args.k4_log} --output-directory {args.output_directory} "
        f"--log {args.log}"
    )
    bt.write_json(
        args.log,
        {
            "claim_scope": (
                "Complete exact two-edge radius-2 expansion of all 64 states "
                "in the recorded dual order-26 k4 frontier. A miss is bounded "
                "to this seed family and is not nonexistence."
            ),
            "source": k4_log["source"],
            "fans": k4_log["fans"],
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
        f"PASS dual radius2 complete={stats['complete']} "
        f"successes={len(successes)} best_score={stats['best_score']} "
        f"log={args.log}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
