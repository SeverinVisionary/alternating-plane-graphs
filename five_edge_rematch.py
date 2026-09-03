#!/usr/bin/env python3
"""Linux-only exact five-edge deranged-rematching primitive and D24 gate."""

from __future__ import annotations

import argparse
import hashlib
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
    "attempts", "graph_invalid_prunes", "abstract_graph_prunes",
    "nonspherical_prunes", "raw_plane_valid", "duplicates",
    "distinct_plane_valid", "score_zero",
    "zero_score_block_tools_rejections", "zero_score_blocks_rejections",
    "zero_score_validation_rejections", "zero_score_cross_validated",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inclusion_exclusion_count() -> int:
    """Return the number of ten-dart matchings avoiding five forbidden pairs."""

    double_factorials = (945, 105, 15, 3, 1, 1)
    return sum(
        (-1) ** retained * math.comb(5, retained) * double_factorials[retained]
        for retained in range(6)
    )


def _strict_matching(
    pairs: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    *, label: str,
) -> tuple[tuple[int, int], ...]:
    if not isinstance(pairs, (tuple, list)) or len(pairs) != 5:
        raise ValueError(f"{label} must contain exactly five pairs")
    normalized: list[tuple[int, int]] = []
    for pair in pairs:
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            raise ValueError(f"{label} contains a malformed pair")
        left, right = pair
        if not isinstance(left, int) or not isinstance(right, int):
            raise ValueError(f"{label} darts must be integers")
        if left < 0 or right < 0 or left == right:
            raise ValueError(f"{label} contains an invalid dart pair")
        normalized.append((min(left, right), max(left, right)))
    result = tuple(sorted(normalized))
    if len(set(result)) != 5:
        raise ValueError(f"{label} contains duplicate pairs")
    if len({dart for pair in result for dart in pair}) != 10:
        raise ValueError(f"{label} must contain five disjoint pairs")
    return result


def deranged_matchings(
    original_pairs: tuple[tuple[int, int], ...] | list[tuple[int, int]],
) -> tuple[tuple[tuple[int, int], ...], ...]:
    """Return all 544 normalized matchings retaining no original pair."""

    original = _strict_matching(original_pairs, label="original matching")
    darts = sorted(dart for pair in original for dart in pair)
    old = {frozenset(pair) for pair in original}
    result = tuple(sorted({
        _strict_matching(matching, label="replacement matching")
        for matching in near_open_search.perfect_matchings(darts)
        if not any(frozenset(pair) in old for pair in matching)
    }))
    if inclusion_exclusion_count() != 544 or len(result) != 544:
        raise AssertionError(f"expected 544 deranged matchings, got {len(result)}")
    if any(
        any(frozenset(pair) in old for pair in matching)
        for matching in result
    ):
        raise AssertionError("deranged matching retained an original edge")
    return result


def apply_rematching(
    alpha: list[int],
    original_pairs: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    matching: tuple[tuple[int, int], ...] | list[tuple[int, int]],
) -> list[int]:
    """Apply one genuinely five-edge replacement to an exact alpha state."""

    original = _strict_matching(original_pairs, label="original matching")
    replacement = _strict_matching(matching, label="replacement matching")
    selected = {dart for pair in original for dart in pair}
    if {dart for pair in replacement for dart in pair} != selected:
        raise ValueError("replacement must match exactly the ten selected darts")
    if any(right >= len(alpha) for left, right in original):
        raise ValueError("selected dart is outside alpha")
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


def enumerate_fixed_quintuple(
    fixed: map_search.FixedMap,
    parent_alpha: list[int],
    selected_quintuple: tuple[tuple[int, int], ...],
    *, frontier_limit: int = 544,
    record_outcomes: bool = True,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    """Exhaust the 544 inverses of one exact current five-edge set."""

    selected = _strict_matching(selected_quintuple, label="selected matching")
    current = set(k3.edge_pairs(parent_alpha))
    if any(pair not in current for pair in selected):
        raise ValueError("selected pair is not a current edge")
    if frontier_limit < 1:
        raise ValueError("frontier limit must be positive")
    started = time.monotonic()
    counts: Counter[str] = Counter()
    histogram: Counter[int] = Counter()
    seen: set[tuple[int, ...]] = set()
    frontier: list[dict[str, object]] = []
    outcomes: list[dict[str, object]] = []
    successes: dict[str, dict[str, object]] = {}
    success_checks: dict[str, dict[str, object]] = {}
    for matching_index, matching in enumerate(deranged_matchings(selected)):
        counts["attempts"] += 1
        candidate = apply_rematching(parent_alpha, selected, matching)
        valid, reason = k3.plane_valid_gate(fixed, candidate)
        outcome: dict[str, object] = {
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
        state.update(matching=[list(pair) for pair in matching])
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
                    "method": "exact-five-edge-deranged-rematching",
                    "selected_pairs": [list(pair) for pair in selected],
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
    ordered = sorted(frontier, key=lambda item: (item["breakdown"]["total"], item["state_sha256"]))
    result = {
        "complete": True,
        "mode": "fixed-quintuple",
        "edges": len(parent_alpha) // 2,
        "selected_pairs": [list(pair) for pair in selected],
        "quintuples": 1,
        "matchings_per_quintuple": 544,
        "expected_attempts": 544,
        "counts": dict(sorted(counts.items())),
        "score_histogram_distinct": {str(k): histogram[k] for k in sorted(histogram)},
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
    if counts["attempts"] != 544:
        raise AssertionError("fixed k5 attempt count changed")
    return result, successes


def construct_d24_calibration(
    base_path: Path, four_edge_state_path: Path,
) -> dict[str, object]:
    """Find the first anchored plane-valid positive D24 k5 perturbation."""

    block = bt.load_json(base_path)
    bt.validate_block(block)
    rotation = bt._rotation_from_rows(block["vertices"])
    fixed, base_alpha = map_search.rotation_to_map(rotation)
    four = json.loads(four_edge_state_path.read_text(encoding="utf-8"))
    anchor = tuple(k3.normalize_matching(four["construction"]["base_selected_pairs"]))
    if (
        len(anchor) != 4
        or len({dart for pair in anchor for dart in pair}) != 8
        or any(pair not in k3.edge_pairs(base_alpha) for pair in anchor)
    ):
        raise ValueError("committed four-edge calibration anchor changed")
    scan: Counter[str] = Counter()
    for fifth in k3.edge_pairs(base_alpha):
        if fifth in anchor:
            continue
        selected = _strict_matching(anchor + (fifth,), label="selected matching")
        scan["fifth_edges"] += 1
        for matching in deranged_matchings(selected):
            scan["rematchings"] += 1
            candidate = apply_rematching(base_alpha, selected, matching)
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
            for inverse in deranged_matchings(matching):
                recovered = apply_rematching(candidate, matching, inverse)
                reverse_valid, _ = k3.plane_valid_gate(fixed, recovered)
                if reverse_valid and map_search.score_breakdown(fixed, recovered)["total"] == 0:
                    zero_alphas.append(recovered)
            if len(zero_alphas) != 1 or zero_alphas[0] != base_alpha:
                scan["unique_recovery_rejections"] += 1
                continue
            return {
                "format": "apg-fixed-alpha-state-v1",
                "claim_scope": "Known-answer D24 exact five-edge calibration state only.",
                "base_file": str(base_path),
                "base_file_sha256": file_sha256(base_path),
                "four_edge_state_file": str(four_edge_state_path),
                "four_edge_state_sha256": file_sha256(four_edge_state_path),
                "fixed_rotation_hash": bt.canonical_map_hash(block),
                "fixed_rotation": block["vertices"],
                "base_alpha_sha256": near_opening._state_sha256(base_alpha),
                "construction": {
                    "scan_order": "committed k4 base pairs plus each other D24 edge, then lexicographic k5 matchings",
                    "scan_counts": dict(sorted(scan.items())),
                    "base_selected_pairs": [list(pair) for pair in selected],
                    "applied_rematching": [list(pair) for pair in matching],
                    "retained_original_pairs": 0,
                    "genuinely_five_edge": True,
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
    raise AssertionError("anchored D24 scan found no suitable k5 perturbation")


def environment_record() -> dict[str, object]:
    return {"hostname": platform.node(), "uname": platform.uname()._asdict()}


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("five_edge_rematch.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--four-edge-state", type=Path, required=True)
    parser.add_argument("--state-output", type=Path, required=True)
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    state = construct_d24_calibration(args.base, args.four_edge_state)
    bt.write_json(args.state_output, state)
    fixed, alphas, replayed = k3.load_state_file(args.state_output)
    selected = tuple(tuple(pair) for pair in replayed["calibration_selected_current_pairs"])
    result, successes = enumerate_fixed_quintuple(fixed, alphas[0], selected)
    base_hash = state["fixed_rotation_hash"]
    if result["counts"]["score_zero"] != 1 or result["success_hashes"] != [base_hash]:
        raise AssertionError("D24 was not uniquely recovered and cross-validated")
    recovered = successes[base_hash]
    bt.write_json(args.certificate, recovered)
    replay = (
        f"python3 five_edge_rematch.py --base {args.base} "
        f"--four-edge-state {args.four_edge_state} --state-output {args.state_output} "
        f"--certificate {args.certificate} --log {args.log}"
    )
    bt.write_json(args.log, {
        "format": "apg-five-edge-calibration-v1",
        "environment": environment_record(),
        "replay": replay,
        "state_file": str(args.state_output),
        "state_file_sha256": file_sha256(args.state_output),
        "certificate_file": str(args.certificate),
        "certificate_file_sha256": file_sha256(args.certificate),
        "construction": state["construction"],
        "result": result,
        "outcome_manifest_sha256": hashlib.sha256(json.dumps(
            result["candidate_outcomes"], sort_keys=True, separators=(",", ":")
        ).encode()).hexdigest(),
        "recovered_D24_hash": bt.canonical_map_hash(recovered),
    })
    print(
        f"PASS attempts={result['counts']['attempts']} "
        f"plane_valid={result['counts']['raw_plane_valid']} "
        f"zero={result['counts']['score_zero']} recovered={base_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
