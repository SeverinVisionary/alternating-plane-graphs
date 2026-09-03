#!/usr/bin/env python3
"""Linux-only exact two-edge radius-3 expansion of a radius-2 frontier."""

from __future__ import annotations

import argparse
import json
import platform
from pathlib import Path

import block_tools as bt
import near_open_beam


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("near_open_radius3.py is Linux-only")
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
    fixed, parents = near_open_beam.load_radius2_frontier(seed, k4_log, radius2_log)
    successes, stats = near_open_beam.expand_two_edge_beam(fixed, parents)
    expected_attempts = (
        stats["parent_states_expanded"]
        * stats["edge_pairs_per_parent"]
        * stats["pairings_per_edge_pair"]
    )
    self_check = {
        "kernel_is_linux": platform.system() == "Linux",
        "parent_frontier_replayed": len(parents) == 64,
        "expected_transition_attempts": expected_attempts,
        "transition_count_matches": stats["counts"]["transition_attempts"]
        == expected_attempts,
        "complete": stats["complete"],
    }
    if not all(self_check.values()):
        raise AssertionError(f"radius-3 Linux self-check failed: {self_check}")
    for index, block in enumerate(successes):
        bt.write_json(args.output_directory / f"block_{index:04d}.json", block)
    replay = (
        f"python3 near_open_radius3.py --seed {args.seed} --k4-log {args.k4_log} "
        f"--radius2-log {args.radius2_log} --output-directory "
        f"{args.output_directory} --log {args.log}"
    )
    bt.write_json(
        args.log,
        {
            "claim_scope": (
                "Complete exact two-edge radius-3 expansion of the recorded "
                "64-state radius-2 frontier. A miss is bounded to this public "
                "seed family and is not nonexistence."
            ),
            "source": radius2_log["source"],
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
        f"PASS radius3 complete={stats['complete']} successes={len(successes)} "
        f"best_score={stats['best_score']} log={args.log}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
