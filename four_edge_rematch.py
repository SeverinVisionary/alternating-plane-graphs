#!/usr/bin/env python3
"""Linux-only exact four-edge deranged-rematching enumeration.

The vertex permutation of a fixed combinatorial map never changes.  A move
selects four current alpha pairs and replaces them by one of the 60 perfect
matchings of their eight darts that retains none of the selected pairs.  Every
candidate passes exact abstract-graph and Euler-sphere gates before scoring.
"""

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
import map_search
import near_open_search
import near_opening
import three_edge_rematch as k3


COUNTER_NAMES = (
    "attempts",
    "graph_invalid_prunes",
    "abstract_graph_prunes",
    "nonspherical_prunes",
    "raw_plane_valid",
    "duplicates",
    "distinct_plane_valid",
    "score_zero",
    "zero_score_block_tools_rejections",
    "zero_score_blocks_rejections",
    "zero_score_validation_rejections",
    "zero_score_cross_validated",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inclusion_exclusion_count() -> int:
    """Number of eight-dart perfect matchings avoiding four forbidden pairs."""

    odd_double_factorials = (105, 15, 3, 1, 1)
    return sum(
        (-1) ** retained * math.comb(4, retained) * odd_double_factorials[retained]
        for retained in range(5)
    )


def deranged_matchings(
    original_pairs: tuple[tuple[int, int], ...] | list[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return all 60 perfect matchings retaining no original dart pair."""

    original = k3.normalize_matching(original_pairs)
    darts = {dart for pair in original for dart in pair}
    if len(original) != 4 or len(darts) != 8:
        raise ValueError("exactly four disjoint original pairs are required")
    old = {frozenset(pair) for pair in original}
    result = tuple(
        sorted(
            {
                k3.normalize_matching(matching)
                for matching in near_open_search.perfect_matchings(sorted(darts))
                if not any(frozenset(pair) in old for pair in matching)
            }
        )
    )
    if inclusion_exclusion_count() != 60 or len(result) != 60:
        raise AssertionError(f"expected 60 deranged matchings, got {len(result)}")
    for matching in result:
        if any(frozenset(pair) in old for pair in matching):
            raise AssertionError("deranged matching retained an original edge")
    return result


def apply_rematching(
    alpha: list[int],
    original_pairs: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    matching: tuple[tuple[int, int], ...] | list[tuple[int, int]],
) -> list[int]:
    original = k3.normalize_matching(original_pairs)
    replacement = k3.normalize_matching(matching)
    if len(original) != 4 or len(replacement) != 4:
        raise ValueError("four original and replacement pairs are required")
    selected = {dart for pair in original for dart in pair}
    if len(selected) != 8 or {dart for pair in replacement for dart in pair} != selected:
        raise ValueError("replacement must match exactly the eight selected darts")
    for left, right in original:
        if alpha[left] != right or alpha[right] != left:
            raise ValueError("selected pair is not a current edge")
    old = {frozenset(pair) for pair in original}
    if any(frozenset(pair) in old for pair in replacement):
        raise ValueError("replacement retained an original edge")
    candidate = list(alpha)
    for left, right in replacement:
        candidate[left] = right
        candidate[right] = left
    k3.edge_pairs(candidate)
    return candidate


def equal_white_defect_support_edges(
    fixed: map_search.FixedMap, alpha: list[int]
) -> tuple[tuple[int, int], ...]:
    """Return exactly the equal-face and bad-white incident current edges.

    This localized selector is defined only on a plane-valid state whose
    face-distribution, abstract-graph, and hex score components are all zero.
    """

    valid, reason = k3.plane_valid_gate(fixed, alpha)
    if not valid:
        raise ValueError(f"selector requires a plane-valid parent ({reason})")
    breakdown = map_search.score_breakdown(fixed, alpha)
    required_zero = ("face_distribution", "abstract_graph", "hex")
    nonzero = {name: breakdown[name] for name in required_zero if breakdown[name] != 0}
    if nonzero:
        raise ValueError(f"selector precondition has nonzero components: {nonzero}")

    faces, face_of = map_search._faces(fixed, alpha)
    lengths = [len(face) for face in faces]
    support: set[tuple[int, int]] = set()
    current_edges = k3.edge_pairs(alpha)
    for edge in current_edges:
        left, right = edge
        left_face, right_face = face_of[left], face_of[right]
        if left_face == right_face or lengths[left_face] == lengths[right_face]:
            support.add(edge)

    bad_white_vertices: set[int] = set()
    for vertex, cycle in enumerate(fixed.cycles):
        if fixed.vertex_degree[vertex] != 2:
            continue
        incident = sorted(lengths[face_of[dart]] for dart in cycle)
        if incident != [5, 6]:
            bad_white_vertices.add(vertex)
    for edge in current_edges:
        if any(fixed.dart_vertex[dart] in bad_white_vertices for dart in edge):
            support.add(edge)
    return tuple(sorted(support))


def enumerate_four_edge_rematchings(
    fixed: map_search.FixedMap,
    parent_alphas: list[list[int]],
    *,
    selected_quadruple: tuple[tuple[int, int], ...] | None,
    support_mode: bool,
    frontier_limit: int,
    record_outcomes: bool = False,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    """Enumerate one fixed quadruple or all quadruples in strict support."""

    if (selected_quadruple is None) == (not support_mode):
        raise ValueError("choose exactly one of fixed-quadruple or support mode")
    if frontier_limit < 1:
        raise ValueError("frontier limit must be positive")
    started = time.monotonic()
    counts: Counter[str] = Counter()
    histogram: Counter[int] = Counter()
    seen: set[tuple[int, ...]] = set()
    frontier: list[dict[str, object]] = []
    successes: dict[str, dict[str, object]] = {}
    success_checks: dict[str, dict[str, object]] = {}
    outcomes: list[dict[str, object]] = []
    edge_count: int | None = None
    quadruple_count = 0
    support_counts: list[int] = []

    for parent_index, alpha in enumerate(parent_alphas):
        current_edges = k3.edge_pairs(alpha)
        edge_count = len(current_edges) if edge_count is None else edge_count
        if edge_count != len(current_edges):
            raise ValueError("all parents must have the same edge count")
        if support_mode:
            support = equal_white_defect_support_edges(fixed, alpha)
            support_counts.append(len(support))
            quadruples = itertools.combinations(support, 4)
        else:
            normalized = k3.normalize_matching(selected_quadruple or ())
            if len(normalized) != 4 or any(pair not in current_edges for pair in normalized):
                raise ValueError("fixed selected pair is not a parent edge")
            support_counts.append(4)
            quadruples = (normalized,)
        for quadruple in quadruples:
            quadruple_count += 1
            for matching_index, matching in enumerate(deranged_matchings(quadruple)):
                counts["attempts"] += 1
                candidate = apply_rematching(alpha, quadruple, matching)
                valid, reason = k3.plane_valid_gate(fixed, candidate)
                outcome = {
                    "parent_index": parent_index,
                    "selected_pairs": [list(pair) for pair in k3.normalize_matching(quadruple)],
                    "matching_index": matching_index,
                    "matching": [list(pair) for pair in matching],
                    "state_sha256": near_opening._state_sha256(candidate),
                    "plane_valid": valid,
                }
                if not valid:
                    counts["graph_invalid_prunes"] += 1
                    counts[f"{reason}_prunes"] += 1
                    outcome["prune_reason"] = reason
                    if record_outcomes:
                        outcomes.append(outcome)
                    continue
                counts["raw_plane_valid"] += 1
                key = tuple(candidate)
                if key in seen:
                    counts["duplicates"] += 1
                    outcome["duplicate"] = True
                    if record_outcomes:
                        outcomes.append(outcome)
                    continue
                seen.add(key)
                counts["distinct_plane_valid"] += 1
                breakdown = map_search.score_breakdown(fixed, candidate)
                histogram[breakdown["total"]] += 1
                state = k3.serialize_state(fixed, candidate, breakdown)
                state.update(
                    parent_index=parent_index,
                    selected_pairs=[list(pair) for pair in k3.normalize_matching(quadruple)],
                    matching=[list(pair) for pair in matching],
                )
                frontier.append(state)
                frontier.sort(key=lambda item: (item["breakdown"]["total"], item["state_sha256"]))
                if len(frontier) > frontier_limit:
                    frontier.pop()
                outcome.update(duplicate=False, breakdown=breakdown)
                if breakdown["total"] == 0:
                    counts["score_zero"] += 1
                    rotation = map_search.rotation_from_state(fixed, candidate)
                    block = near_open_search._independently_validate_zero(
                        rotation,
                        provenance={
                            "method": "exact-four-edge-deranged-rematching",
                            "parent_index": parent_index,
                            "selected_pairs": outcome["selected_pairs"],
                            "matching": outcome["matching"],
                        },
                        counts=counts,
                    )
                    outcome["cross_validated"] = block is not None
                    if block is not None:
                        block_hash = bt.canonical_map_hash(block)
                        successes[block_hash] = block
                        success_checks[block_hash] = near_open_search._close_and_verify(block)
                if record_outcomes:
                    outcomes.append(outcome)

    for name in COUNTER_NAMES:
        counts.setdefault(name, 0)
    ordered = sorted(frontier, key=lambda state: (state["breakdown"]["total"], state["state_sha256"]))
    result = {
        "complete": True,
        "mode": "support-all-quadruples" if support_mode else "fixed-quadruple",
        "parent_count": len(parent_alphas),
        "edges": edge_count or 0,
        "support_edge_counts": support_counts,
        "quadruples": quadruple_count,
        "matchings_per_quadruple": 60,
        "expected_attempts": quadruple_count * 60,
        "counts": dict(sorted(counts.items())),
        "score_histogram_distinct": {str(score): count for score, count in sorted(histogram.items())},
        "best_score": ordered[0]["breakdown"]["total"] if ordered else None,
        "frontier_limit": frontier_limit,
        "frontier_states": ordered,
        "frontier_state_count": len(ordered),
        "frontier_truncated": counts["distinct_plane_valid"] > frontier_limit,
        "success_hashes": sorted(successes),
        "success_checks": {key: success_checks[key] for key in sorted(success_checks)},
        "candidate_outcomes": outcomes if record_outcomes else [],
        "wall_seconds": time.monotonic() - started,
    }
    if counts["attempts"] != result["expected_attempts"]:
        raise AssertionError("attempt count does not match quadruples times sixty")
    return result, successes


def construct_d24_calibration(base_path: Path) -> dict[str, object]:
    """Find the first deterministic plane-valid positive D24 k=4 perturbation."""

    block = bt.load_json(base_path)
    bt.validate_block(block)
    rotation = bt._rotation_from_rows(block["vertices"])
    fixed, base_alpha = map_search.rotation_to_map(rotation)
    scan: Counter[str] = Counter()
    for quadruple in itertools.combinations(k3.edge_pairs(base_alpha), 4):
        scan["edge_quadruples"] += 1
        for matching in deranged_matchings(quadruple):
            scan["rematchings"] += 1
            candidate = apply_rematching(base_alpha, quadruple, matching)
            valid, reason = k3.plane_valid_gate(fixed, candidate)
            if not valid:
                scan["graph_invalid"] += 1
                scan[f"{reason}_prunes"] += 1
                continue
            scan["plane_valid"] += 1
            breakdown = map_search.score_breakdown(fixed, candidate)
            if breakdown["total"] == 0:
                scan["score_zero_skipped"] += 1
                continue
            zero_alphas: list[list[int]] = []
            for reverse in deranged_matchings(matching):
                recovered = apply_rematching(candidate, matching, reverse)
                reverse_valid, _ = k3.plane_valid_gate(fixed, recovered)
                if reverse_valid and map_search.score_breakdown(fixed, recovered)["total"] == 0:
                    zero_alphas.append(recovered)
            if len(zero_alphas) != 1 or zero_alphas[0] != base_alpha:
                scan["unique_recovery_rejections"] += 1
                continue
            return {
                "format": "apg-fixed-alpha-state-v1",
                "claim_scope": "Known-answer D24 exact four-edge calibration state only.",
                "base_file": str(base_path),
                "base_file_sha256": file_sha256(base_path),
                "fixed_rotation_hash": bt.canonical_map_hash(block),
                "fixed_rotation": block["vertices"],
                "base_alpha_sha256": near_opening._state_sha256(base_alpha),
                "construction": {
                    "scan_order": "lexicographic edge quadruples then lexicographic deranged matchings",
                    "scan_counts": dict(sorted(scan.items())),
                    "base_selected_pairs": [list(pair) for pair in k3.normalize_matching(quadruple)],
                    "applied_rematching": [list(pair) for pair in matching],
                    "retained_original_pairs": 0,
                    "genuinely_four_edge": True,
                },
                "calibration_selected_current_pairs": [list(pair) for pair in matching],
                "states": [{
                    "alpha": candidate,
                    "state_sha256": near_opening._state_sha256(candidate),
                    "breakdown": breakdown,
                    "abstract_graph_valid": True,
                    "spherical": True,
                    "euler_characteristic": 2,
                }],
            }
    raise AssertionError("deterministic D24 scan found no suitable perturbation")


def parse_dart_pair(value: str) -> tuple[int, int]:
    return k3.parse_dart_pair(value)


def environment_record() -> dict[str, object]:
    return {"hostname": platform.node(), "uname": platform.uname()._asdict()}


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("four_edge_rematch.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    calibrate = subparsers.add_parser("calibrate")
    calibrate.add_argument("--base", type=Path, required=True)
    calibrate.add_argument("--state-output", type=Path, required=True)
    calibrate.add_argument("--certificate", type=Path, required=True)
    calibrate.add_argument("--log", type=Path, required=True)
    enum = subparsers.add_parser("enumerate")
    enum.add_argument("--state-file", type=Path, required=True)
    enum.add_argument("--mode", choices=("fixed-quadruple", "support-all-quadruples"), required=True)
    enum.add_argument("--selected-pair", action="append", type=parse_dart_pair)
    enum.add_argument("--frontier-limit", type=int, required=True)
    enum.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "calibrate":
        state = construct_d24_calibration(args.base)
        bt.write_json(args.state_output, state)
        fixed, alphas, replayed = k3.load_state_file(args.state_output)
        selected = tuple(tuple(pair) for pair in replayed["calibration_selected_current_pairs"])
        result, successes = enumerate_four_edge_rematchings(
            fixed, alphas, selected_quadruple=selected, support_mode=False,
            frontier_limit=60, record_outcomes=True,
        )
        base_hash = state["fixed_rotation_hash"]
        if result["counts"]["score_zero"] != 1 or result["success_hashes"] != [base_hash]:
            raise AssertionError("D24 was not uniquely recovered and cross-validated")
        recovered = successes[base_hash]
        bt.write_json(args.certificate, recovered)
        replay = (
            f"python3 four_edge_rematch.py calibrate --base {args.base} "
            f"--state-output {args.state_output} --certificate {args.certificate} --log {args.log}"
        )
        bt.write_json(args.log, {
            "format": "apg-four-edge-calibration-v1",
            "environment": environment_record(),
            "replay": replay,
            "state_file": str(args.state_output),
            "state_file_sha256": file_sha256(args.state_output),
            "construction": state["construction"],
            "result": result,
            "recovered_D24_hash": bt.canonical_map_hash(recovered),
        })
        print(
            f"PASS attempts={result['counts']['attempts']} plane_valid={result['counts']['raw_plane_valid']} "
            f"zero={result['counts']['score_zero']} recovered={base_hash}"
        )
        return 0

    fixed, alphas, _ = k3.load_state_file(args.state_file)
    fixed_mode = args.mode == "fixed-quadruple"
    if fixed_mode:
        if args.selected_pair is None or len(args.selected_pair) != 4:
            parser.error("fixed-quadruple mode requires exactly four --selected-pair values")
        selected = tuple(args.selected_pair)
    else:
        if args.selected_pair:
            parser.error("support-all-quadruples mode does not accept --selected-pair")
        selected = None
    result, _ = enumerate_four_edge_rematchings(
        fixed, alphas, selected_quadruple=selected, support_mode=not fixed_mode,
        frontier_limit=args.frontier_limit,
    )
    bt.write_json(args.log, {
        "format": "apg-four-edge-enumeration-v1",
        "environment": environment_record(),
        "state_file": str(args.state_file),
        "state_file_sha256": file_sha256(args.state_file),
        "result": result,
    })
    print(
        f"PASS mode={result['mode']} attempts={result['counts']['attempts']} "
        f"best={result['best_score']} zero={result['counts']['score_zero']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
