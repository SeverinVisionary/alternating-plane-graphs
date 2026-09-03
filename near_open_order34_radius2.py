#!/usr/bin/env python3
"""Linux-only exact radius-2 expansion of the order-34 k4 frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import block_tools as bt
import map_search
import near_open_beam


FRONTIER_SIZE = 64
EXPECTED_SOURCE_SHA256 = (
    "1f2670651eb62019115375bacd8335aaedf3e711ec6e9f4173ca1fce5e605f76"
)
EXPECTED_SEED_FILE_SHA256 = (
    "2d86c0b12ac046602516c435c319ef87efe98d6bac837546fb775f6fdf71178e"
)
EXPECTED_SEED_STATE_SHA256 = (
    "938ee94260c196b7f4fb9aef81ca3fab0aaeb67b92dc2bf520cb087a029aaa93"
)
EXPECTED_PARENT_MANIFEST_SHA256 = (
    "1f5d7f9c56720ce8ef0797706dfdb143050707ee80948144c0801f6a5b536678"
)
EXPECTED_EDGES_PER_PARENT = 62
EXPECTED_EDGE_PAIRS_PER_PARENT = 1891
EXPECTED_ATTEMPTS = 242048


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def load_order34_k4_frontier(
    seed_path: Path, seed: dict[str, object], k4_log: dict[str, object]
) -> tuple[map_search.FixedMap, list[dict[str, object]]]:
    """Replay the exact order-34 seed and all recorded k4 frontier states."""

    if file_sha256(seed_path) != EXPECTED_SEED_FILE_SHA256:
        raise ValueError("order-34 seed file hash changed")
    source = seed.get("source")
    if not isinstance(source, dict):
        raise ValueError("order-34 seed source is absent")
    if source.get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("order-34 source hash changed")
    if seed.get("state_sha256") != EXPECTED_SEED_STATE_SHA256:
        raise ValueError("order-34 seed state hash changed")
    log_source = k4_log.get("source")
    if not isinstance(log_source, dict):
        raise ValueError("order-34 k4 source is absent")
    if log_source.get("sha256") != EXPECTED_SOURCE_SHA256:
        raise ValueError("order-34 k4 source hash changed")
    if log_source.get("state_sha256") != EXPECTED_SEED_STATE_SHA256:
        raise ValueError("order-34 k4 seed-state hash changed")
    fixed, parents = near_open_beam.load_frontier(seed, k4_log)
    if len(parents) != FRONTIER_SIZE:
        raise ValueError("order-34 k4 frontier must contain exactly 64 states")
    manifest = parent_manifest_sha256(parents)
    if manifest != EXPECTED_PARENT_MANIFEST_SHA256:
        raise ValueError(f"order-34 k4 frontier manifest changed: {manifest}")
    return fixed, parents


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("near_open_order34_radius2.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=Path)
    parser.add_argument("--k4-log", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    k4_log = json.loads(args.k4_log.read_text(encoding="utf-8"))
    fixed, parents = load_order34_k4_frontier(args.seed, seed, k4_log)
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
        "seed_file_hash_matches": file_sha256(args.seed)
        == EXPECTED_SEED_FILE_SHA256,
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
        "seed_file_hash_matches": True,
        "seed_state_hash_matches": True,
        "parent_frontier_replayed": True,
        "parent_manifest_matches": True,
        "edges_per_parent": EXPECTED_EDGES_PER_PARENT,
        "edge_pairs_per_parent": EXPECTED_EDGE_PAIRS_PER_PARENT,
        "pairings_per_edge_pair": 2,
        "expected_transition_attempts": EXPECTED_ATTEMPTS,
        "transition_count_matches": True,
        "complete": True,
    }
    if self_check != required:
        raise AssertionError(f"order-34 radius-2 self-check failed: {self_check}")
    for index, block in enumerate(successes):
        bt.write_json(args.output_directory / f"block_{index:04d}.json", block)
    improved = bool(successes) or stats["descent_below_parent_minimum"]
    replay = (
        f"python3 near_open_order34_radius2.py --seed {args.seed} "
        f"--k4-log {args.k4_log} --output-directory {args.output_directory} "
        f"--log {args.log}"
    )
    bt.write_json(
        args.log,
        {
            "claim_scope": (
                "Complete exact two-edge radius-2 expansion of all 64 states "
                "in the recorded order-34 k4 frontier. A miss is bounded to "
                "this seed family and is not nonexistence."
            ),
            "decision": {
                "order34_seed_family_closed": not improved,
                "next_radius_started": False,
                "reason": (
                    "Witness or improvement found; stop for one final bounded decision."
                    if improved
                    else "No witness and no improvement below 1500; close this bounded order-34 seed family."
                ),
            },
            "source": k4_log["source"],
            "seed_file_sha256": file_sha256(args.seed),
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
        f"PASS order34 radius2 complete={stats['complete']} "
        f"successes={len(successes)} best_score={stats['best_score']} "
        f"log={args.log}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
