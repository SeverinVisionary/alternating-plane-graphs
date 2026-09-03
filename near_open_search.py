#!/usr/bin/env python3
"""Cloud-only exact k-edge repair of a published near-block opening.

The input is a SHA-256-gated near-opening seed produced by ``near_opening.py``.
A targeted repair keeps two named offending edges in every move, adds two
degree-(3,5) donor edges, and enumerates every perfect rematching of the eight
selected darts. Every zero-score state is passed to the exact block validator;
a miss is only an exhaustive result for this one k=4 move family.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
import time
from collections import Counter
from collections.abc import Iterable, Iterator
from pathlib import Path

import block_tools as bt
import blocks
import map_search
import near_opening
import verify


BEST_STATE_LOG_LIMIT = 64


def _close_and_verify(block: dict[str, object]) -> dict[str, object]:
    """Close through both implementations and run the final verifier twice."""

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


def _independently_validate_zero(
    rotation: dict[int, list[int]],
    *,
    provenance: dict[str, object],
    counts: Counter[str],
) -> dict[str, object] | None:
    """Run both block validators even when either one rejects the zero."""

    block = None
    block_tools_ok = False
    blocks_ok = False
    try:
        block = bt.block_from_rotation(rotation, provenance=provenance)
        bt.validate_block(block)
        block_tools_ok = True
    except bt.BlockError:
        counts["zero_score_block_tools_rejections"] += 1
    try:
        blocks.validate_block(blocks.normalize_rotation(rotation))
        blocks_ok = True
    except blocks.BlockError:
        counts["zero_score_blocks_rejections"] += 1
    if not (block_tools_ok and blocks_ok):
        counts["zero_score_validation_rejections"] += 1
        return None
    counts["zero_score_cross_validated"] += 1
    return block


def perfect_matchings(items: Iterable[int]) -> Iterator[tuple[tuple[int, int], ...]]:
    """Yield every perfect matching of distinct items deterministically."""

    remaining = tuple(items)
    if len(remaining) % 2:
        raise ValueError("a perfect matching requires an even number of items")
    if not remaining:
        yield ()
        return
    first = remaining[0]
    for index in range(1, len(remaining)):
        second = remaining[index]
        rest = remaining[1:index] + remaining[index + 1 :]
        for suffix in perfect_matchings(rest):
            yield ((first, second), *suffix)


def _parse_pair(value: str) -> tuple[int, int]:
    try:
        left, right = (int(part) for part in value.split(","))
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError("expected U,V") from error
    if left == right:
        raise argparse.ArgumentTypeError("an edge needs two distinct endpoints")
    return (min(left, right), max(left, right))


def _edge_representatives(
    fixed: map_search.FixedMap, alpha: list[int]
) -> dict[tuple[int, int], int]:
    result: dict[tuple[int, int], int] = {}
    for dart, mate in enumerate(alpha):
        if dart > mate:
            continue
        u = fixed.dart_vertex[dart] + 1
        v = fixed.dart_vertex[mate] + 1
        result[(min(u, v), max(u, v))] = dart
    return result


def predicted_k4_structure(
    fixed: map_search.FixedMap,
    alpha: list[int],
    *,
    mandatory_edges: tuple[tuple[int, int], tuple[int, int]],
) -> dict[str, object]:
    """Record the structural defect and the endpoint-count k=3 obstruction."""

    normalized = tuple((min(u, v), max(u, v)) for u, v in mandatory_edges)
    edges = _edge_representatives(fixed, alpha)
    if any(edge not in edges for edge in normalized):
        raise bt.BlockError("predicted mandatory edge is absent")
    degree_patterns = Counter(
        tuple(sorted((fixed.vertex_degree[u - 1], fixed.vertex_degree[v - 1])))
        for u, v in edges
    )
    other_edges = [edge for edge in edges if edge not in normalized]
    maximum_degree5_endpoints = max(
        sum(fixed.vertex_degree[vertex - 1] == 5 for vertex in edge)
        for edge in other_edges
    )
    mandatory_degree_pairs = [
        [fixed.vertex_degree[u - 1], fixed.vertex_degree[v - 1]]
        for u, v in normalized
    ]
    shared = set(normalized[0]).intersection(normalized[1])
    if len(shared) != 1:
        raise bt.BlockError("mandatory defect edges must share one vertex")
    shared_vertex = next(iter(shared))
    offending_whites = [
        next(vertex for vertex in edge if vertex != shared_vertex)
        for edge in normalized
    ]
    return {
        "hexagons": near_opening._hexagons(fixed, alpha),
        "mandatory_edges": [list(edge) for edge in normalized],
        "mandatory_degree_pairs": mandatory_degree_pairs,
        "shared_vertex": shared_vertex,
        "shared_vertex_degree": fixed.vertex_degree[shared_vertex - 1],
        "offending_white_vertices": offending_whites,
        "offending_white_degrees": [
            fixed.vertex_degree[vertex - 1] for vertex in offending_whites
        ],
        "edge_degree_pattern_counts": {
            f"{left},{right}": count
            for (left, right), count in sorted(degree_patterns.items())
        },
        "other_edge_count": len(other_edges),
        "maximum_degree5_endpoints_from_one_additional_edge": (
            maximum_degree5_endpoints
        ),
        "degree5_endpoints_required": 2,
        "k3_impossible": maximum_degree5_endpoints < 2,
    }


def targeted_k4_repairs(
    fixed: map_search.FixedMap,
    alpha: list[int],
    *,
    mandatory_edges: tuple[tuple[int, int], tuple[int, int]],
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Exhaust the two-offender plus two (3,5)-donor rematch family."""

    started = time.monotonic()
    edge_darts = _edge_representatives(fixed, alpha)
    normalized_mandatory = tuple(
        (min(u, v), max(u, v)) for u, v in mandatory_edges
    )
    if normalized_mandatory[0] == normalized_mandatory[1]:
        raise bt.BlockError("mandatory edges must be distinct")
    try:
        mandatory_darts = tuple(edge_darts[edge] for edge in normalized_mandatory)
    except KeyError as error:
        raise bt.BlockError(f"missing mandatory edge {error.args[0]}") from error

    donor_darts = []
    for edge, dart in sorted(edge_darts.items()):
        if edge in normalized_mandatory:
            continue
        degrees = sorted(fixed.vertex_degree[vertex - 1] for vertex in edge)
        if degrees == [3, 5]:
            donor_darts.append(dart)

    counts: Counter[str] = Counter()
    score_counts: Counter[int] = Counter()
    survivors: dict[tuple[int, ...], dict[str, object]] = {}
    successes: dict[str, dict[str, object]] = {}
    success_checks: dict[str, dict[str, object]] = {}
    for donor_pair in itertools.combinations(donor_darts, 2):
        counts["donor_pair_attempts"] += 1
        selected_edges = (*mandatory_darts, *donor_pair)
        selected_darts = tuple(
            dart
            for representative in selected_edges
            for dart in (representative, alpha[representative])
        )
        if len(set(selected_darts)) != 8:
            counts["pruned_overlapping_selected_edges"] += 1
            continue
        old_pairs = {
            frozenset((representative, alpha[representative]))
            for representative in selected_edges
        }
        for matching in perfect_matchings(selected_darts):
            counts["perfect_rematching_attempts"] += 1
            if {frozenset(pair) for pair in matching} == old_pairs:
                counts["pruned_original_matching"] += 1
                continue
            candidate = list(alpha)
            for left, right in matching:
                candidate[left] = right
                candidate[right] = left
            if not map_search._abstract_graph_ok(fixed, candidate):
                counts["pruned_abstract_graph"] += 1
                continue
            counts["graph_valid_candidates"] += 1
            key = tuple(candidate)
            if key in survivors:
                counts["duplicate_graph_valid_candidates"] += 1
                continue
            counts["distinct_graph_valid_candidates"] += 1
            breakdown = map_search.score_breakdown(fixed, candidate)
            candidate_score = breakdown["total"]
            score_counts[candidate_score] += 1
            payload = {
                "alpha": candidate,
                "state_sha256": near_opening._state_sha256(candidate),
                "breakdown": breakdown,
                "donor_edges": [
                    list(edge)
                    for edge, dart in edge_darts.items()
                    if dart in donor_pair
                ],
                "matching": [list(pair) for pair in matching],
            }
            survivors[key] = payload
            if candidate_score != 0:
                continue
            counts["zero_score_candidates"] += 1
            rotation = map_search.rotation_from_state(fixed, candidate)
            block = _independently_validate_zero(
                rotation,
                provenance={
                    "method": "targeted-near-opening-k4-rematch",
                    "mandatory_edges": [list(edge) for edge in normalized_mandatory],
                    "donor_edges": payload["donor_edges"],
                },
                counts=counts,
            )
            if block is None:
                continue
            block_hash = bt.canonical_map_hash(block)
            successes.setdefault(block_hash, block)
            success_checks.setdefault(block_hash, _close_and_verify(block))

    ordered_survivors = sorted(
        survivors.values(),
        key=lambda state: (state["breakdown"]["total"], state["state_sha256"]),
    )
    frontier = ordered_survivors[:BEST_STATE_LOG_LIMIT]
    best_score = ordered_survivors[0]["breakdown"]["total"] if ordered_survivors else None
    best_state_count = sum(
        state["breakdown"]["total"] == best_score for state in ordered_survivors
    )
    for key in (
        "donor_pair_attempts",
        "perfect_rematching_attempts",
        "pruned_original_matching",
        "pruned_overlapping_selected_edges",
        "pruned_abstract_graph",
        "graph_valid_candidates",
        "duplicate_graph_valid_candidates",
        "distinct_graph_valid_candidates",
        "zero_score_candidates",
        "zero_score_block_tools_rejections",
        "zero_score_blocks_rejections",
        "zero_score_validation_rejections",
        "zero_score_cross_validated",
    ):
        counts.setdefault(key, 0)
    stats: dict[str, object] = {
        "mandatory_edges": [list(edge) for edge in normalized_mandatory],
        "donor_edges": len(donor_darts),
        "counts": dict(sorted(counts.items())),
        "score_histogram": {str(key): score_counts[key] for key in sorted(score_counts)},
        "best_score": best_score,
        "best_state_count": best_state_count,
        "frontier_limit": BEST_STATE_LOG_LIMIT,
        "frontier_state_count": len(frontier),
        "frontier_truncated": len(ordered_survivors) > BEST_STATE_LOG_LIMIT,
        "frontier_states": frontier,
        "success_hashes": sorted(successes),
        "success_checks": success_checks,
        "wall_seconds": time.monotonic() - started,
    }
    return [successes[key] for key in sorted(successes)], stats


def main() -> int:
    if platform.system() == "Darwin":
        raise SystemExit("near_open_search.py is cloud-only; refusing to run on Darwin")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, type=Path)
    parser.add_argument(
        "--mandatory-edge", action="append", required=True, type=_parse_pair
    )
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()
    if len(args.mandatory_edge) != 2:
        parser.error("exactly two --mandatory-edge values are required")
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    fixed, alpha = near_opening.state_from_seed(seed)
    initial_breakdown = map_search.score_breakdown(fixed, alpha)
    structure = predicted_k4_structure(
        fixed,
        alpha,
        mandatory_edges=tuple(args.mandatory_edge),
    )
    if not structure["k3_impossible"]:
        raise AssertionError("predicted k=3 endpoint obstruction did not reproduce")
    successes, stats = targeted_k4_repairs(
        fixed,
        alpha,
        mandatory_edges=tuple(args.mandatory_edge),
    )
    for index, block in enumerate(successes):
        bt.write_json(args.output_directory / f"block_{index:04d}.json", block)
    bt.write_json(
        args.log,
        {
            "claim_scope": (
                "Exhaustive only for this published embedding, fan pair, two "
                "mandatory edges, two degree-(3,5) donor edges, and one k=4 rematch."
            ),
            "source": {
                **seed["source"],
                "seed_path": str(args.seed),
                "state_sha256": seed["state_sha256"],
            },
            "fans": seed["fans"],
            "opened_rotation": seed["opened_rotation"],
            "initial_breakdown": initial_breakdown,
            "structural_prediction": structure,
            "k3_impossibility": {
                "derived": True,
                "enumerated": False,
                "reason": (
                    "The two offending white darts require two degree-5 donor "
                    "endpoints. One additional admissible degree-(3,5) edge "
                    "supplies only one, while a degree-(5,5) edge is forbidden."
                ),
            },
            "environment": {
                "hostname": platform.node(),
                "kernel": platform.platform(),
            },
            "replay": (
                "python3 near_open_search.py --seed "
                f"{args.seed} "
                + " ".join(
                    f"--mandatory-edge {left},{right}"
                    for left, right in args.mandatory_edge
                )
                + " "
                f"--output-directory {args.output_directory} --log {args.log}"
            ),
            "result": stats,
        },
    )
    print(
        f"PASS exhaustive k4 lane: successes={len(successes)} "
        f"best_score={stats['best_score']} log={args.log}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
