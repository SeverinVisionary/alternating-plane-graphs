#!/usr/bin/env python3
"""Linux-only exact three-edge deranged-rematching enumeration.

The vertex permutation of a fixed combinatorial map never changes.  A move
selects three current alpha pairs and replaces them by one of the eight perfect
matchings of their six darts that retains none of the selected pairs.  Every
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


COUNTER_NAMES = (
    "attempts",
    "graph_invalid_prunes",
    "abstract_graph_prunes",
    "nonspherical_prunes",
    "raw_graph_valid",
    "duplicates",
    "distinct_graph_valid",
    "score_zero",
    "zero_score_block_tools_rejections",
    "zero_score_blocks_rejections",
    "zero_score_validation_rejections",
    "zero_score_cross_validated",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def edge_pairs(alpha: list[int]) -> tuple[tuple[int, int], ...]:
    pairs = tuple((dart, mate) for dart, mate in enumerate(alpha) if dart < mate)
    if len(pairs) * 2 != len(alpha):
        raise ValueError("alpha is not a fixed-point-free involution")
    for left, right in pairs:
        if left == right or alpha[right] != left:
            raise ValueError("alpha is not a fixed-point-free involution")
    return pairs


def normalize_matching(
    matching: tuple[tuple[int, int], ...] | list[tuple[int, int]],
) -> tuple[tuple[int, int], ...]:
    return tuple(sorted((min(left, right), max(left, right)) for left, right in matching))


def deranged_matchings(
    original_pairs: tuple[tuple[int, int], tuple[int, int], tuple[int, int]]
    | list[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return the eight perfect matchings retaining no original dart pair."""

    original = normalize_matching(original_pairs)
    if len(original) != 3 or len({dart for pair in original for dart in pair}) != 6:
        raise ValueError("exactly three disjoint original pairs are required")
    old = {frozenset(pair) for pair in original}
    darts = tuple(sorted(dart for pair in original for dart in pair))
    matchings = {
        normalize_matching(matching)
        for matching in near_open_search.perfect_matchings(darts)
        if not any(frozenset(pair) in old for pair in matching)
    }
    result = tuple(sorted(matchings))
    if len(result) != 8:
        raise AssertionError(f"expected 8 deranged matchings, got {len(result)}")
    for matching in result:
        if any(frozenset(pair) in old for pair in matching):
            raise AssertionError("deranged matching retained an original edge")
    return result


def apply_rematching(
    alpha: list[int],
    original_pairs: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    matching: tuple[tuple[int, int], ...] | list[tuple[int, int]],
) -> list[int]:
    original = normalize_matching(original_pairs)
    replacement = normalize_matching(matching)
    if len(original) != 3 or len(replacement) != 3:
        raise ValueError("three original and replacement pairs are required")
    selected = {dart for pair in original for dart in pair}
    if len(selected) != 6 or {dart for pair in replacement for dart in pair} != selected:
        raise ValueError("replacement must match exactly the six selected darts")
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
    edge_pairs(candidate)
    return candidate


def euler_characteristic(fixed: map_search.FixedMap, alpha: list[int]) -> int:
    faces, _ = map_search._faces(fixed, alpha)
    return len(fixed.cycles) - len(alpha) // 2 + len(faces)


def plane_valid_gate(
    fixed: map_search.FixedMap, alpha: list[int]
) -> tuple[bool, str | None]:
    if not map_search._abstract_graph_ok(fixed, alpha):
        return False, "abstract_graph"
    if euler_characteristic(fixed, alpha) != 2:
        return False, "nonspherical"
    return True, None


def exact_graph_gate(
    fixed: map_search.FixedMap, alpha: list[int]
) -> tuple[bool, str | None]:
    """Compatibility alias; new code should use ``plane_valid_gate``."""

    return plane_valid_gate(fixed, alpha)


def serialize_state(
    fixed: map_search.FixedMap, alpha: list[int], breakdown: dict[str, int]
) -> dict[str, object]:
    rotation = map_search.rotation_from_state(fixed, alpha)
    return {
        "alpha": list(alpha),
        "state_sha256": near_opening._state_sha256(alpha),
        "breakdown": dict(breakdown),
        "abstract_graph_valid": True,
        "spherical": True,
        "euler_characteristic": 2,
        "rotation": [
            {"id": vertex, "clockwise": rotation[vertex]}
            for vertex in sorted(rotation)
        ],
    }


def load_state_file(
    path: Path,
) -> tuple[map_search.FixedMap, list[list[int]], dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("format") != "apg-fixed-alpha-state-v1":
        raise ValueError("unsupported fixed-alpha state format")
    rows = payload.get("fixed_rotation")
    if not isinstance(rows, list):
        raise ValueError("fixed rotation is absent")
    rotation = bt._rotation_from_rows(rows)
    rotation_hash = bt.canonical_map_hash({"vertices": rows})
    if rotation_hash != payload.get("fixed_rotation_hash"):
        raise ValueError("fixed rotation hash changed")
    fixed, base_alpha = map_search.rotation_to_map(rotation)
    if near_opening._state_sha256(base_alpha) != payload.get("base_alpha_sha256"):
        raise ValueError("base alpha hash changed")
    states = payload.get("states")
    if not isinstance(states, list) or not states:
        raise ValueError("state list is absent")
    alphas: list[list[int]] = []
    for state in states:
        alpha = state.get("alpha")
        if not isinstance(alpha, list) or len(alpha) != len(base_alpha):
            raise ValueError("state alpha is malformed")
        if near_opening._state_sha256(alpha) != state.get("state_sha256"):
            raise ValueError("state alpha hash changed")
        abstract_valid = map_search._abstract_graph_ok(fixed, alpha)
        exact_valid, exact_reason = plane_valid_gate(fixed, alpha)
        spherical = abstract_valid and exact_valid
        euler = euler_characteristic(fixed, alpha) if abstract_valid else None
        expected_abstract = state.get(
            "abstract_graph_valid", state.get("graph_valid")
        )
        if abstract_valid != expected_abstract:
            raise ValueError("state abstract-graph validity changed")
        if "spherical" in state and spherical != state["spherical"]:
            raise ValueError("state sphericity changed")
        if "euler_characteristic" in state and euler != state["euler_characteristic"]:
            raise ValueError("state Euler characteristic changed")
        if "sphere_gate_reason" in state and exact_reason != state["sphere_gate_reason"]:
            raise ValueError("state sphere-gate reason changed")
        if abstract_valid:
            breakdown = map_search.score_breakdown(fixed, alpha)
            if breakdown != state.get("breakdown"):
                raise ValueError("state score changed")
        alphas.append(list(alpha))
    return fixed, alphas, payload


def enumerate_three_edge_rematchings(
    fixed: map_search.FixedMap,
    parent_alphas: list[list[int]],
    *,
    selected_triple: tuple[tuple[int, int], ...] | None,
    frontier_limit: int,
    record_outcomes: bool = False,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    """Enumerate one fixed triple or every edge triple for each parent."""

    if frontier_limit < 1:
        raise ValueError("frontier limit must be positive")
    started = time.monotonic()
    counts: Counter[str] = Counter()
    score_histogram: Counter[int] = Counter()
    seen: set[tuple[int, ...]] = set()
    frontier: list[dict[str, object]] = []
    successes: dict[str, dict[str, object]] = {}
    success_checks: dict[str, dict[str, object]] = {}
    outcomes: list[dict[str, object]] = []
    edge_count = None
    triple_count = 0

    for parent_index, alpha in enumerate(parent_alphas):
        current_edges = edge_pairs(alpha)
        if edge_count is None:
            edge_count = len(current_edges)
        elif edge_count != len(current_edges):
            raise ValueError("all parents must have the same edge count")
        if selected_triple is None:
            triples = itertools.combinations(current_edges, 3)
        else:
            normalized = normalize_matching(selected_triple)
            if any(pair not in current_edges for pair in normalized):
                raise ValueError("fixed selected pair is not a parent edge")
            triples = (normalized,)
        for triple in triples:
            triple_count += 1
            matchings = deranged_matchings(triple)
            for matching_index, matching in enumerate(matchings):
                counts["attempts"] += 1
                candidate = apply_rematching(alpha, triple, matching)
                valid, prune_reason = plane_valid_gate(fixed, candidate)
                outcome = {
                    "parent_index": parent_index,
                    "selected_pairs": [list(pair) for pair in normalize_matching(triple)],
                    "matching_index": matching_index,
                    "matching": [list(pair) for pair in matching],
                    "state_sha256": near_opening._state_sha256(candidate),
                    "graph_valid": valid,
                }
                if not valid:
                    counts["graph_invalid_prunes"] += 1
                    counts[f"{prune_reason}_prunes"] += 1
                    outcome["prune_reason"] = prune_reason
                    if record_outcomes:
                        outcomes.append(outcome)
                    continue
                counts["raw_graph_valid"] += 1
                key = tuple(candidate)
                if key in seen:
                    counts["duplicates"] += 1
                    outcome["duplicate"] = True
                    if record_outcomes:
                        outcomes.append(outcome)
                    continue
                counts["distinct_graph_valid"] += 1
                seen.add(key)
                breakdown = map_search.score_breakdown(fixed, candidate)
                score = breakdown["total"]
                score_histogram[score] += 1
                state = serialize_state(fixed, candidate, breakdown)
                state["parent_index"] = parent_index
                state["selected_pairs"] = [list(pair) for pair in normalize_matching(triple)]
                state["matching"] = [list(pair) for pair in matching]
                frontier.append(state)
                frontier.sort(
                    key=lambda item: (
                        item["breakdown"]["total"], item["state_sha256"]
                    )
                )
                if len(frontier) > frontier_limit:
                    frontier.pop()
                outcome["duplicate"] = False
                outcome["breakdown"] = breakdown
                if score == 0:
                    counts["score_zero"] += 1
                    rotation = map_search.rotation_from_state(fixed, candidate)
                    block = near_open_search._independently_validate_zero(
                        rotation,
                        provenance={
                            "method": "exact-three-edge-deranged-rematching",
                            "parent_index": parent_index,
                            "selected_pairs": [list(pair) for pair in normalize_matching(triple)],
                            "matching": [list(pair) for pair in matching],
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
    ordered_states = sorted(
        frontier,
        key=lambda state: (state["breakdown"]["total"], state["state_sha256"]),
    )
    result = {
        "complete": True,
        "mode": "fixed-triple" if selected_triple is not None else "all-triples",
        "parent_count": len(parent_alphas),
        "edges": edge_count or 0,
        "triples": triple_count,
        "matchings_per_triple": 8,
        "expected_attempts": triple_count * 8,
        "counts": dict(sorted(counts.items())),
        "score_histogram_distinct": {
            str(score): count for score, count in sorted(score_histogram.items())
        },
        "best_score": ordered_states[0]["breakdown"]["total"] if ordered_states else None,
        "frontier_limit": frontier_limit,
        "frontier_states": ordered_states,
        "frontier_state_count": len(ordered_states),
        "frontier_truncated": counts["distinct_graph_valid"] > frontier_limit,
        "success_hashes": sorted(successes),
        "success_checks": {key: success_checks[key] for key in sorted(success_checks)},
        "candidate_outcomes": outcomes if record_outcomes else [],
        "wall_seconds": time.monotonic() - started,
    }
    if counts["attempts"] != result["expected_attempts"]:
        raise AssertionError("attempt count does not match triples times eight")
    return result, successes


def construct_d24_calibration(base_path: Path) -> dict[str, object]:
    """Find the first deterministic graph-valid positive D24 k=3 perturbation."""

    block = bt.load_json(base_path)
    bt.validate_block(block)
    rotation = bt._rotation_from_rows(block["vertices"])
    fixed, base_alpha = map_search.rotation_to_map(rotation)
    base_hash = bt.canonical_map_hash(block)
    base_state_hash = near_opening._state_sha256(base_alpha)
    scan_counts: Counter[str] = Counter()
    for triple in itertools.combinations(edge_pairs(base_alpha), 3):
        scan_counts["edge_triples"] += 1
        for matching in deranged_matchings(triple):
            scan_counts["rematchings"] += 1
            candidate = apply_rematching(base_alpha, triple, matching)
            valid, reason = plane_valid_gate(fixed, candidate)
            if not valid:
                scan_counts["graph_invalid"] += 1
                scan_counts[f"{reason}_prunes"] += 1
                continue
            scan_counts["graph_valid"] += 1
            breakdown = map_search.score_breakdown(fixed, candidate)
            if breakdown["total"] == 0:
                scan_counts["score_zero_skipped"] += 1
                continue
            reverse_matchings = deranged_matchings(matching)
            zero_alphas = []
            for reverse in reverse_matchings:
                reverse_candidate = apply_rematching(candidate, matching, reverse)
                reverse_valid, _ = plane_valid_gate(fixed, reverse_candidate)
                if reverse_valid and map_search.score_breakdown(fixed, reverse_candidate)["total"] == 0:
                    zero_alphas.append(reverse_candidate)
            if len(zero_alphas) != 1 or zero_alphas[0] != base_alpha:
                scan_counts["unique_recovery_rejections"] += 1
                continue
            return {
                "format": "apg-fixed-alpha-state-v1",
                "claim_scope": "Known-answer D24 exact three-edge calibration state only.",
                "base_file": str(base_path),
                "base_file_sha256": file_sha256(base_path),
                "fixed_rotation_hash": base_hash,
                "fixed_rotation": block["vertices"],
                "base_alpha_sha256": base_state_hash,
                "construction": {
                    "scan_order": "lexicographic edge triples then lexicographic deranged matchings",
                    "scan_counts": dict(sorted(scan_counts.items())),
                    "base_selected_pairs": [list(pair) for pair in normalize_matching(triple)],
                    "applied_rematching": [list(pair) for pair in matching],
                    "retained_original_pairs": 0,
                    "genuinely_three_edge": True,
                },
                "calibration_selected_current_pairs": [list(pair) for pair in matching],
                "states": [
                    {
                        "alpha": candidate,
                        "state_sha256": near_opening._state_sha256(candidate),
                        "breakdown": breakdown,
                        "graph_valid": True,
                    }
                ],
            }
    raise AssertionError("deterministic D24 scan found no suitable perturbation")


def parse_dart_pair(value: str) -> tuple[int, int]:
    try:
        left, right = (int(part) for part in value.split(","))
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError("expected DART,DART") from error
    if left == right:
        raise argparse.ArgumentTypeError("dart pair needs distinct darts")
    return min(left, right), max(left, right)


def environment_record() -> dict[str, object]:
    return {"hostname": platform.node(), "uname": platform.uname()._asdict()}


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("three_edge_rematch.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    calibrate = subparsers.add_parser("calibrate")
    calibrate.add_argument("--base", type=Path, required=True)
    calibrate.add_argument("--state-output", type=Path, required=True)
    calibrate.add_argument("--certificate", type=Path, required=True)
    calibrate.add_argument("--log", type=Path, required=True)
    enumerate_parser = subparsers.add_parser("enumerate")
    enumerate_parser.add_argument("--state-file", type=Path, required=True)
    enumerate_parser.add_argument("--mode", choices=("fixed-triple", "all-triples"), required=True)
    enumerate_parser.add_argument("--selected-pair", action="append", type=parse_dart_pair)
    enumerate_parser.add_argument("--frontier-limit", type=int, required=True)
    enumerate_parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "calibrate":
        state_payload = construct_d24_calibration(args.base)
        bt.write_json(args.state_output, state_payload)
        fixed, alphas, replayed = load_state_file(args.state_output)
        selected = tuple(tuple(pair) for pair in replayed["calibration_selected_current_pairs"])
        result, successes = enumerate_three_edge_rematchings(
            fixed,
            alphas,
            selected_triple=selected,
            frontier_limit=8,
            record_outcomes=True,
        )
        base_hash = state_payload["fixed_rotation_hash"]
        if result["counts"]["score_zero"] != 1 or result["success_hashes"] != [base_hash]:
            raise AssertionError("D24 was not uniquely recovered and cross-validated")
        recovered = successes[base_hash]
        bt.write_json(args.certificate, recovered)
        replay = (
            f"python3 three_edge_rematch.py calibrate --base {args.base} "
            f"--state-output {args.state_output} --certificate {args.certificate} "
            f"--log {args.log}"
        )
        bt.write_json(
            args.log,
            {
                "format": "apg-three-edge-calibration-v1",
                "environment": environment_record(),
                "replay": replay,
                "state_file": str(args.state_output),
                "state_file_sha256": file_sha256(args.state_output),
                "construction": state_payload["construction"],
                "result": result,
                "recovered_D24_hash": bt.canonical_map_hash(recovered),
            },
        )
        print(
            f"PASS attempts={result['counts']['attempts']} valid={result['counts']['raw_graph_valid']} "
            f"zero={result['counts']['score_zero']} recovered={base_hash}"
        )
        return 0

    fixed, alphas, _ = load_state_file(args.state_file)
    if args.mode == "fixed-triple":
        if args.selected_pair is None or len(args.selected_pair) != 3:
            parser.error("fixed-triple mode requires exactly three --selected-pair values")
        selected = tuple(args.selected_pair)
    else:
        if args.selected_pair:
            parser.error("all-triples mode does not accept --selected-pair")
        selected = None
    result, _ = enumerate_three_edge_rematchings(
        fixed,
        alphas,
        selected_triple=selected,
        frontier_limit=args.frontier_limit,
    )
    bt.write_json(
        args.log,
        {
            "format": "apg-three-edge-enumeration-v1",
            "environment": environment_record(),
            "state_file": str(args.state_file),
            "state_file_sha256": file_sha256(args.state_file),
            "result": result,
        },
    )
    print(
        f"PASS mode={result['mode']} attempts={result['counts']['attempts']} "
        f"best={result['best_score']} zero={result['counts']['score_zero']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
