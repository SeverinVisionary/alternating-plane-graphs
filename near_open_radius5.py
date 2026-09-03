#!/usr/bin/env python3
"""Linux-only exact two-edge radius-5 expansion of a radius-4 frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import block_tools as bt
import map_search
import near_open_beam
import near_open_radius4
import near_opening


FRONTIER_SIZE = 64
EXPECTED_PARENT_MANIFEST_SHA256 = (
    "e1cd11caecae717cdf2eb38d50823cf49793cc0099a7169671d00450b8453ea9"
)


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


def load_radius4_frontier(
    seed: dict[str, object],
    k4_log: dict[str, object],
    radius2_log: dict[str, object],
    radius3_log: dict[str, object],
    radius4_log: dict[str, object],
) -> tuple[map_search.FixedMap, list[dict[str, object]]]:
    """Replay all 64 radius-4 hashes, scores, and graph-validity gates."""

    fixed, radius3_parents = near_open_radius4.load_radius3_frontier(
        seed, k4_log, radius2_log, radius3_log
    )
    result = radius4_log.get("result")
    if not isinstance(result, dict) or not result.get("complete"):
        raise ValueError("radius-4 result is absent or incomplete")
    if result.get("parent_state_hashes") != [
        parent["state_sha256"] for parent in radius3_parents
    ]:
        raise ValueError("radius-4 parent hashes do not reproduce")
    states = result.get("frontier_states")
    if not isinstance(states, list) or len(states) != FRONTIER_SIZE:
        raise ValueError("radius-4 frontier must contain exactly 64 states")
    keys: list[tuple[int, str]] = []
    for state in states:
        alpha = state.get("alpha")
        if not isinstance(alpha, list) or len(alpha) != len(fixed.dart_vertex):
            raise ValueError("radius-4 frontier alpha is malformed")
        digest = near_opening._state_sha256(alpha)
        if digest != state.get("state_sha256"):
            raise ValueError("radius-4 frontier hash does not reproduce")
        breakdown = map_search.score_breakdown(fixed, alpha)
        if breakdown != state.get("breakdown"):
            raise ValueError("radius-4 frontier score does not reproduce")
        if not map_search._abstract_graph_ok(fixed, alpha):
            raise ValueError("radius-4 frontier is not abstract-graph-valid")
        keys.append((breakdown["total"], digest))
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise ValueError("radius-4 frontier is not ordered and distinct")
    manifest = parent_manifest_sha256(states)
    if manifest != EXPECTED_PARENT_MANIFEST_SHA256:
        raise ValueError(f"radius-4 parent manifest changed: {manifest}")
    return fixed, states


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("near_open_radius5.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=Path)
    parser.add_argument("--k4-log", required=True, type=Path)
    parser.add_argument("--radius2-log", required=True, type=Path)
    parser.add_argument("--radius3-log", required=True, type=Path)
    parser.add_argument("--radius4-log", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    k4_log = json.loads(args.k4_log.read_text(encoding="utf-8"))
    radius2_log = json.loads(args.radius2_log.read_text(encoding="utf-8"))
    radius3_log = json.loads(args.radius3_log.read_text(encoding="utf-8"))
    radius4_log = json.loads(args.radius4_log.read_text(encoding="utf-8"))
    fixed, parents = load_radius4_frontier(
        seed, k4_log, radius2_log, radius3_log, radius4_log
    )
    successes, stats = near_open_beam.expand_two_edge_beam(fixed, parents)
    expected_attempts = (
        stats["parent_states_expanded"]
        * stats["edge_pairs_per_parent"]
        * stats["pairings_per_edge_pair"]
    )
    self_check = {
        "kernel_is_linux": platform.system() == "Linux",
        "parent_frontier_replayed": len(parents) == FRONTIER_SIZE,
        "parent_manifest_matches": parent_manifest_sha256(parents)
        == EXPECTED_PARENT_MANIFEST_SHA256,
        "expected_transition_attempts": expected_attempts,
        "transition_count_matches": stats["counts"]["transition_attempts"]
        == expected_attempts,
        "complete": stats["complete"],
    }
    if not all(
        value
        for key, value in self_check.items()
        if key != "expected_transition_attempts"
    ):
        raise AssertionError(f"radius-5 Linux self-check failed: {self_check}")
    for index, block in enumerate(successes):
        bt.write_json(args.output_directory / f"block_{index:04d}.json", block)
    replay = (
        f"python3 near_open_radius5.py --seed {args.seed} --k4-log {args.k4_log} "
        f"--radius2-log {args.radius2_log} --radius3-log {args.radius3_log} "
        f"--radius4-log {args.radius4_log} "
        f"--output-directory {args.output_directory} --log {args.log}"
    )
    bt.write_json(
        args.log,
        {
            "claim_scope": (
                "Complete exact two-edge radius-5 expansion of the recorded "
                "64-state radius-4 frontier. A miss is bounded to this public "
                "seed family and is not nonexistence. This is the final radius "
                "for this seed family."
            ),
            "source": radius4_log["source"],
            "fans": radius4_log["fans"],
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
        f"PASS radius5 complete={stats['complete']} successes={len(successes)} "
        f"best_score={stats['best_score']} log={args.log}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
