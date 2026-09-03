#!/usr/bin/env python3
"""Cloud-only exact two-edge radius-2 expansion of a k=4 frontier beam."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import platform
import time
from collections import Counter
from pathlib import Path

import block_tools as bt
import blocks
import map_search
import near_open_search
import near_opening
import verify


BEST_STATE_LOG_LIMIT = 64


def load_frontier(
    seed: dict[str, object], k4_log: dict[str, object]
) -> tuple[map_search.FixedMap, list[dict[str, object]]]:
    fixed, _ = near_opening.state_from_seed(seed)
    result = k4_log.get("result")
    if not isinstance(result, dict):
        raise ValueError("k=4 log has no result")
    states = result.get("frontier_states")
    if not isinstance(states, list) or len(states) != 64:
        raise ValueError("radius-2 lane requires the complete 64-state frontier")
    keys: list[tuple[int, str]] = []
    for state in states:
        alpha = state.get("alpha")
        if not isinstance(alpha, list) or len(alpha) != len(fixed.dart_vertex):
            raise ValueError("frontier alpha is malformed")
        digest = near_opening._state_sha256(alpha)
        if digest != state.get("state_sha256"):
            raise ValueError("frontier alpha hash does not reproduce")
        breakdown = map_search.score_breakdown(fixed, alpha)
        if breakdown != state.get("breakdown"):
            raise ValueError("frontier score does not reproduce")
        if not map_search._abstract_graph_ok(fixed, alpha):
            raise ValueError("frontier state is not abstract-graph-valid")
        keys.append((breakdown["total"], digest))
    if keys != sorted(keys) or len(set(digest for _, digest in keys)) != len(keys):
        raise ValueError("frontier is not deterministically ordered and distinct")
    return fixed, states


def load_radius2_frontier(
    seed: dict[str, object],
    k4_log: dict[str, object],
    radius2_log: dict[str, object],
) -> tuple[map_search.FixedMap, list[dict[str, object]]]:
    """Replay the complete deterministic radius-2 frontier contract."""

    fixed, parents = load_frontier(seed, k4_log)
    result = radius2_log.get("result")
    if not isinstance(result, dict) or not result.get("complete"):
        raise ValueError("radius-2 result is absent or incomplete")
    if result.get("parent_state_hashes") != [
        parent["state_sha256"] for parent in parents
    ]:
        raise ValueError("radius-2 parent hashes do not reproduce")
    states = result.get("frontier_states")
    if not isinstance(states, list) or len(states) != BEST_STATE_LOG_LIMIT:
        raise ValueError("radius-2 frontier must contain exactly 64 states")
    keys: list[tuple[int, str]] = []
    for state in states:
        alpha = state.get("alpha")
        if not isinstance(alpha, list) or len(alpha) != len(fixed.dart_vertex):
            raise ValueError("radius-2 frontier alpha is malformed")
        digest = near_opening._state_sha256(alpha)
        if digest != state.get("state_sha256"):
            raise ValueError("radius-2 frontier hash does not reproduce")
        breakdown = map_search.score_breakdown(fixed, alpha)
        if breakdown != state.get("breakdown"):
            raise ValueError("radius-2 frontier score does not reproduce")
        if not map_search._abstract_graph_ok(fixed, alpha):
            raise ValueError("radius-2 frontier is not abstract-graph-valid")
        keys.append((breakdown["total"], digest))
    if keys != sorted(keys) or len(set(keys)) != len(keys):
        raise ValueError("radius-2 frontier is not ordered and distinct")
    return fixed, states


def two_edge_rematchings(alpha: list[int]):
    edges = tuple(dart for dart, mate in enumerate(alpha) if dart < mate)
    for first, second in itertools.combinations(edges, 2):
        first_mate, second_mate = alpha[first], alpha[second]
        yield (first, second), ((first, second), (first_mate, second_mate))
        yield (first, second), ((first, second_mate), (first_mate, second))


def _candidate(
    alpha: list[int], matching: tuple[tuple[int, int], tuple[int, int]]
) -> list[int]:
    result = list(alpha)
    for left, right in matching:
        result[left] = right
        result[right] = left
    return result


def _close_and_verify(block: dict[str, object]) -> dict[str, object]:
    rotation = bt._rotation_from_rows(block["vertices"])
    closed_bt = bt.close_block(block)
    verify.verify_certificate(closed_bt, expected_order=len(rotation))
    independent_rotation = blocks.normalize_rotation(rotation)
    sockets = blocks.validate_block(independent_rotation)
    independent_block = blocks.Block(independent_rotation, sockets)
    closed_independent = blocks.rotation_to_certificate(
        blocks.close_block(independent_block)
    )
    verify.verify_certificate(closed_independent, expected_order=len(rotation))
    return {
        "block_tools_closed_sha256": hashlib.sha256(
            json.dumps(closed_bt, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "blocks_closed_sha256": hashlib.sha256(
            json.dumps(
                closed_independent, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest(),
        "block_tools_verified": True,
        "blocks_verified": True,
    }


def expand_two_edge_beam(
    fixed: map_search.FixedMap,
    parents: list[dict[str, object]],
    *,
    max_parents: int | None = None,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    started = time.monotonic()
    if max_parents is not None and max_parents < 1:
        raise ValueError("max_parents must be positive")
    selected_parents = parents if max_parents is None else parents[:max_parents]
    counts: Counter[str] = Counter()
    score_counts: Counter[int] = Counter()
    distinct: dict[tuple[int, ...], dict[str, object]] = {}
    successes: dict[str, dict[str, object]] = {}
    success_checks: dict[str, dict[str, object]] = {}

    for parent in selected_parents:
        counts["parents"] += 1
        parent_alpha = parent["alpha"]
        parent_hash = parent["state_sha256"]
        for selected_edges, matching in two_edge_rematchings(parent_alpha):
            counts["transition_attempts"] += 1
            candidate = _candidate(parent_alpha, matching)
            if not map_search._abstract_graph_ok(fixed, candidate):
                counts["pruned_abstract_graph"] += 1
                continue
            counts["raw_graph_valid_transitions"] += 1
            key = tuple(candidate)
            if key in distinct:
                counts["duplicate_graph_valid_states"] += 1
                continue
            counts["distinct_graph_valid_states"] += 1
            breakdown = map_search.score_breakdown(fixed, candidate)
            score_counts[breakdown["total"]] += 1
            digest = near_opening._state_sha256(candidate)
            payload = {
                "alpha": candidate,
                "state_sha256": digest,
                "breakdown": breakdown,
                "parent_state_sha256": parent_hash,
                "selected_edge_darts": list(selected_edges),
                "matching": [list(pair) for pair in matching],
            }
            distinct[key] = payload
            if breakdown["total"] != 0:
                continue
            counts["zero_score_candidates"] += 1
            rotation = map_search.rotation_from_state(fixed, candidate)
            block = near_open_search._independently_validate_zero(
                rotation,
                provenance={
                    "method": "near-opening-k4-frontier-two-edge-radius2",
                    "parent_state_sha256": parent_hash,
                    "selected_edge_darts": payload["selected_edge_darts"],
                    "matching": payload["matching"],
                },
                counts=counts,
            )
            if block is None:
                continue
            block_hash = bt.canonical_map_hash(block)
            successes.setdefault(block_hash, block)
            success_checks.setdefault(block_hash, _close_and_verify(block))

    for key in (
        "parents",
        "transition_attempts",
        "pruned_abstract_graph",
        "raw_graph_valid_transitions",
        "duplicate_graph_valid_states",
        "distinct_graph_valid_states",
        "zero_score_candidates",
        "zero_score_block_tools_rejections",
        "zero_score_blocks_rejections",
        "zero_score_validation_rejections",
        "zero_score_cross_validated",
    ):
        counts.setdefault(key, 0)
    ordered = sorted(
        distinct.values(),
        key=lambda state: (state["breakdown"]["total"], state["state_sha256"]),
    )
    best_score = ordered[0]["breakdown"]["total"] if ordered else None
    best_states = [
        state for state in ordered if state["breakdown"]["total"] == best_score
    ]
    frontier = ordered[:BEST_STATE_LOG_LIMIT]
    parent_minimum = min(
        parent["breakdown"]["total"] for parent in selected_parents
    )
    return [successes[key] for key in sorted(successes)], {
        "parent_states_available": len(parents),
        "parent_states_expanded": len(selected_parents),
        "parent_state_hashes": [parent["state_sha256"] for parent in selected_parents],
        "edges_per_parent": sum(1 for dart, mate in enumerate(parents[0]["alpha"]) if dart < mate),
        "edge_pairs_per_parent": math.comb(
            sum(1 for dart, mate in enumerate(parents[0]["alpha"]) if dart < mate), 2
        ),
        "pairings_per_edge_pair": 2,
        "complete": max_parents is None or len(selected_parents) == len(parents),
        "counts": dict(sorted(counts.items())),
        "score_histogram_distinct": {
            str(score): score_counts[score] for score in sorted(score_counts)
        },
        "best_score": best_score,
        "best_state_count": len(best_states),
        "best_states_truncated": len(best_states) > BEST_STATE_LOG_LIMIT,
        "best_states": best_states[:BEST_STATE_LOG_LIMIT],
        "frontier_limit": BEST_STATE_LOG_LIMIT,
        "frontier_state_count": len(frontier),
        "frontier_truncated": len(ordered) > BEST_STATE_LOG_LIMIT,
        "frontier_states": frontier,
        "parent_minimum_score": parent_minimum,
        "descent_below_parent_minimum": best_score is not None and best_score < parent_minimum,
        "descent_below_radius1_minimum": best_score is not None and best_score < parent_minimum,
        "success_hashes": sorted(successes),
        "success_checks": success_checks,
        "wall_seconds": time.monotonic() - started,
    }


def main() -> int:
    if platform.system() == "Darwin":
        raise SystemExit("near_open_beam.py is cloud-only; refusing to run on Darwin")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=Path)
    parser.add_argument("--k4-log", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--max-parents", type=int)
    args = parser.parse_args()
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    k4_log = json.loads(args.k4_log.read_text(encoding="utf-8"))
    fixed, parents = load_frontier(seed, k4_log)
    successes, stats = expand_two_edge_beam(
        fixed, parents, max_parents=args.max_parents
    )
    for index, block in enumerate(successes):
        bt.write_json(args.output_directory / f"block_{index:04d}.json", block)
    replay = (
        f"python3 near_open_beam.py --seed {args.seed} --k4-log {args.k4_log} "
        f"--output-directory {args.output_directory} --log {args.log}"
        + (f" --max-parents {args.max_parents}" if args.max_parents is not None else "")
    )
    bt.write_json(
        args.log,
        {
            "claim_scope": (
                "Exact two-edge radius-2 expansion of the recorded 64-state "
                "k=4 frontier when result.complete is true. A miss is bounded "
                "to this seed family and is not nonexistence."
            ),
            "source": k4_log["source"],
            "fans": k4_log["fans"],
            "environment": {
                "hostname": platform.node(),
                "kernel": platform.platform(),
            },
            "replay": replay,
            "result": stats,
        },
    )
    print(
        f"PASS radius2 complete={stats['complete']} successes={len(successes)} "
        f"best_score={stats['best_score']} log={args.log}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
