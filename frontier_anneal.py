#!/usr/bin/env python3
"""Linux-only deterministic annealing from a committed exact map state.

Normal frontier mode requires a SHA-256-gated near-opening seed and a named,
graph-valid state in a committed frontier log.  The separate D24 calibration
mode replays the committed score-820 perturbation, whose initial abstract graph
is deliberately invalid, and requires exact recovery of the known D24 block.
Every proposed state must pass the abstract-graph gate before it can be scored
or accepted.  Every score zero is independently checked by both block
validators and every valid zero is closed and finally verified both ways.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import time
from collections import Counter
from pathlib import Path

import block_tools as bt
import map_search
import near_open_search
import near_opening


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def temperature_at(
    step: int,
    steps: int,
    start: float,
    end: float,
    schedule: str,
) -> float:
    if steps < 1:
        raise ValueError("steps must be positive")
    if start <= 0 or end <= 0:
        raise ValueError("temperatures must be positive")
    if schedule not in {"geometric", "linear"}:
        raise ValueError("schedule must be geometric or linear")
    fraction = step / max(1, steps - 1)
    if schedule == "geometric":
        return start * (end / start) ** fraction
    return start + (end - start) * fraction


def _find_frontier_state(
    frontier_log: dict[str, object], state_sha256: str
) -> dict[str, object]:
    result = frontier_log.get("result")
    if not isinstance(result, dict) or not result.get("complete", True):
        raise ValueError("frontier result is absent or incomplete")
    states = result.get("frontier_states")
    if not isinstance(states, list):
        raise ValueError("frontier states are absent")
    matches = [state for state in states if state.get("state_sha256") == state_sha256]
    if len(matches) != 1:
        raise ValueError("named state must occur exactly once in frontier")
    return matches[0]


def load_frontier_state(
    seed_path: Path,
    frontier_log_path: Path,
    *,
    expected_seed_sha256: str,
    state_sha256: str,
) -> tuple[map_search.FixedMap, list[int], dict[str, object]]:
    """Load and replay one exact graph-valid state from a frontier log."""

    actual_seed_sha256 = file_sha256(seed_path)
    if actual_seed_sha256 != expected_seed_sha256:
        raise ValueError("frontier seed file hash changed")
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    frontier_log = json.loads(frontier_log_path.read_text(encoding="utf-8"))
    logged_seed_hash = frontier_log.get("seed_file_sha256")
    if logged_seed_hash is not None and logged_seed_hash != actual_seed_sha256:
        raise ValueError("frontier log seed file hash changed")
    source = frontier_log.get("source")
    if not isinstance(source, dict):
        raise ValueError("frontier source provenance is absent")
    if source.get("state_sha256") != seed.get("state_sha256"):
        raise ValueError("frontier seed-state hash changed")
    if source.get("sha256") != seed.get("source", {}).get("sha256"):
        raise ValueError("frontier upstream-source hash changed")
    fixed, _ = near_opening.state_from_seed(seed)
    state = _find_frontier_state(frontier_log, state_sha256)
    alpha = state.get("alpha")
    if not isinstance(alpha, list) or len(alpha) != len(fixed.dart_vertex):
        raise ValueError("frontier alpha is malformed")
    if near_opening._state_sha256(alpha) != state_sha256:
        raise ValueError("frontier state hash does not reproduce")
    breakdown = map_search.score_breakdown(fixed, alpha)
    if breakdown != state.get("breakdown"):
        raise ValueError("frontier state score does not reproduce")
    if not map_search._abstract_graph_ok(fixed, alpha):
        raise ValueError("frontier state is not abstract-graph-valid")
    return fixed, list(alpha), {
        "mode": "frontier",
        "seed_path": str(seed_path),
        "seed_file_sha256": actual_seed_sha256,
        "seed_state_sha256": seed["state_sha256"],
        "frontier_log": str(frontier_log_path),
        "frontier_log_sha256": file_sha256(frontier_log_path),
        "state_sha256": state_sha256,
        "score_breakdown": breakdown,
        "abstract_graph_valid": True,
    }


def load_d24_calibration_state(
    base_path: Path, perturbation_log_path: Path
) -> tuple[map_search.FixedMap, list[int], dict[str, object]]:
    """Replay the exact committed score-820 D24 perturbation."""

    block = bt.load_json(base_path)
    perturbation = json.loads(perturbation_log_path.read_text(encoding="utf-8"))
    base_rotation_hash = bt.canonical_map_hash(block)
    if base_rotation_hash != perturbation.get("base_rotation_hash"):
        raise ValueError("D24 base rotation hash changed")
    fixed, _ = map_search.rotation_to_map(bt._rotation_from_rows(block["vertices"]))
    alpha = perturbation.get("perturbed_alpha")
    if not isinstance(alpha, list) or len(alpha) != len(fixed.dart_vertex):
        raise ValueError("D24 perturbation alpha is malformed")
    alpha_sha256 = near_opening._state_sha256(alpha)
    if alpha_sha256 != perturbation.get("alpha_sha256"):
        raise ValueError("D24 perturbation alpha hash changed")
    breakdown = map_search.score_breakdown(fixed, alpha)
    if breakdown != perturbation.get("perturbed_components"):
        raise ValueError("D24 perturbation score changed")
    if breakdown["total"] != 820:
        raise ValueError("D24 calibration must start at score 820")
    return fixed, list(alpha), {
        "mode": "d24-calibration",
        "base": str(base_path),
        "base_file_sha256": file_sha256(base_path),
        "base_rotation_hash": base_rotation_hash,
        "perturbation_log": str(perturbation_log_path),
        "perturbation_log_sha256": file_sha256(perturbation_log_path),
        "state_sha256": alpha_sha256,
        "score_breakdown": breakdown,
        "abstract_graph_valid": map_search._abstract_graph_ok(fixed, alpha),
    }


def _serialize_state(
    fixed: map_search.FixedMap, alpha: list[int], breakdown: dict[str, int]
) -> dict[str, object]:
    rotation = map_search.rotation_from_state(fixed, alpha)
    return {
        "alpha": list(alpha),
        "state_sha256": near_opening._state_sha256(alpha),
        "score_breakdown": dict(breakdown),
        "rotation": [
            {"id": vertex, "clockwise": rotation[vertex]}
            for vertex in sorted(rotation)
        ],
    }


def anneal(
    fixed: map_search.FixedMap,
    initial_alpha: list[int],
    *,
    seed: int,
    steps: int,
    temperature_start: float,
    temperature_end: float,
    schedule: str,
) -> tuple[dict[str, object] | None, dict[str, object], dict[str, object]]:
    """Run deterministic graph-valid two-edge Metropolis annealing."""

    started = time.monotonic()
    if steps < 1:
        raise ValueError("steps must be positive")
    temperature_at(0, steps, temperature_start, temperature_end, schedule)
    rng = random.Random(seed)
    current = list(initial_alpha)
    current_breakdown = map_search.score_breakdown(fixed, current)
    current_score = current_breakdown["total"]
    best = list(current)
    best_breakdown = dict(current_breakdown)
    best_score = current_score
    counts: Counter[str] = Counter()
    success: dict[str, object] | None = None
    success_checks: dict[str, object] = {}
    recovery_step: int | None = None
    recovery_temperature: float | None = None

    for step_index in range(steps):
        counts["move_attempts"] += 1
        candidate = map_search.switch_move(fixed, current, rng)
        if candidate is None or not map_search._abstract_graph_ok(fixed, candidate):
            counts["graph_invalid_rejections"] += 1
            continue
        counts["graph_valid_candidates"] += 1
        candidate_breakdown = map_search.score_breakdown(fixed, candidate)
        counts["score_evaluations"] += 1
        candidate_score = candidate_breakdown["total"]
        temperature = temperature_at(
            step_index,
            steps,
            temperature_start,
            temperature_end,
            schedule,
        )
        difference = candidate_score - current_score
        accepted = difference <= 0 or rng.random() < math.exp(-difference / temperature)
        if accepted:
            current = candidate
            current_score = candidate_score
            current_breakdown = candidate_breakdown
            counts["accepted_moves"] += 1
            if difference < 0:
                counts["accepted_improving"] += 1
            elif difference == 0:
                counts["accepted_equal"] += 1
            else:
                counts["accepted_worsening"] += 1
        else:
            counts["metropolis_rejections"] += 1
        if candidate_score < best_score:
            best = list(candidate)
            best_score = candidate_score
            best_breakdown = dict(candidate_breakdown)
            counts["best_improvements"] += 1
        if candidate_score != 0:
            continue
        counts["zero_score_candidates"] += 1
        rotation = map_search.rotation_from_state(fixed, candidate)
        block = near_open_search._independently_validate_zero(
            rotation,
            provenance={
                "method": "frontier-two-edge-anneal",
                "seed": seed,
                "step": step_index + 1,
                "temperature": temperature,
                "temperature_schedule": schedule,
            },
            counts=counts,
        )
        if block is None:
            continue
        success = block
        success_checks = near_open_search._close_and_verify(block)
        recovery_step = step_index + 1
        recovery_temperature = temperature
        best = list(candidate)
        best_score = 0
        best_breakdown = dict(candidate_breakdown)
        break

    for name in (
        "move_attempts",
        "graph_invalid_rejections",
        "graph_valid_candidates",
        "score_evaluations",
        "accepted_moves",
        "accepted_improving",
        "accepted_equal",
        "accepted_worsening",
        "metropolis_rejections",
        "best_improvements",
        "zero_score_candidates",
        "zero_score_block_tools_rejections",
        "zero_score_blocks_rejections",
        "zero_score_validation_rejections",
        "zero_score_cross_validated",
    ):
        counts.setdefault(name, 0)
    best_state = _serialize_state(fixed, best, best_breakdown)
    result = {
        "seed": seed,
        "steps_requested": steps,
        "steps_executed": counts["move_attempts"],
        "temperature": {
            "schedule": schedule,
            "start": temperature_start,
            "end": temperature_end,
            "first_effective": temperature_at(
                0, steps, temperature_start, temperature_end, schedule
            ),
            "last_configured": temperature_at(
                steps - 1, steps, temperature_start, temperature_end, schedule
            ),
            "recovery": recovery_temperature,
        },
        "initial_state": _serialize_state(fixed, initial_alpha, map_search.score_breakdown(fixed, initial_alpha)),
        "best_state": best_state,
        "current_state": _serialize_state(fixed, current, current_breakdown),
        "counts": dict(sorted(counts.items())),
        "success": success is not None,
        "success_block_hash": bt.canonical_map_hash(success) if success else None,
        "success_checks": success_checks,
        "recovery_step": recovery_step,
        "wall_seconds": time.monotonic() - started,
    }
    return success, result, best_state


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("frontier_anneal.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("frontier", "d24-calibration"), required=True)
    parser.add_argument("--seed-file", type=Path)
    parser.add_argument("--seed-file-sha256")
    parser.add_argument("--frontier-log", type=Path)
    parser.add_argument("--state-sha256")
    parser.add_argument("--base", type=Path)
    parser.add_argument("--perturbation-log", type=Path)
    parser.add_argument("--rng-seed", required=True, type=int)
    parser.add_argument("--steps", required=True, type=int)
    parser.add_argument("--temperature-start", required=True, type=float)
    parser.add_argument("--temperature-end", required=True, type=float)
    parser.add_argument("--schedule", choices=("geometric", "linear"), default="geometric")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()

    if args.mode == "frontier":
        if not all((args.seed_file, args.seed_file_sha256, args.frontier_log, args.state_sha256)):
            parser.error("frontier mode requires seed file/hash, frontier log, and state hash")
        fixed, alpha, input_record = load_frontier_state(
            args.seed_file,
            args.frontier_log,
            expected_seed_sha256=args.seed_file_sha256,
            state_sha256=args.state_sha256,
        )
    else:
        if not args.base or not args.perturbation_log:
            parser.error("D24 calibration requires --base and --perturbation-log")
        fixed, alpha, input_record = load_d24_calibration_state(
            args.base, args.perturbation_log
        )

    success, result, _ = anneal(
        fixed,
        alpha,
        seed=args.rng_seed,
        steps=args.steps,
        temperature_start=args.temperature_start,
        temperature_end=args.temperature_end,
        schedule=args.schedule,
    )
    if args.mode == "d24-calibration":
        expected = input_record["base_rotation_hash"]
        recovered = result["success_block_hash"]
        if success is None or recovered != expected:
            raise AssertionError(
                f"D24 calibration failed: expected {expected}, recovered {recovered}"
            )
        result["known_answer"] = {
            "expected_rotation_hash": expected,
            "recovered_rotation_hash": recovered,
            "exact_D24_recovered": True,
        }
    if success is not None:
        bt.write_json(args.output, success)
    replay_parts = [
        "python3 frontier_anneal.py",
        "--mode", args.mode,
    ]
    if args.mode == "frontier":
        replay_parts += [
            "--seed-file", str(args.seed_file),
            "--seed-file-sha256", args.seed_file_sha256,
            "--frontier-log", str(args.frontier_log),
            "--state-sha256", args.state_sha256,
        ]
    else:
        replay_parts += [
            "--base", str(args.base),
            "--perturbation-log", str(args.perturbation_log),
        ]
    replay_parts += [
        "--rng-seed", str(args.rng_seed),
        "--steps", str(args.steps),
        "--temperature-start", str(args.temperature_start),
        "--temperature-end", str(args.temperature_end),
        "--schedule", args.schedule,
        "--output", str(args.output),
        "--log", str(args.log),
    ]
    bt.write_json(
        args.log,
        {
            "claim_scope": (
                "Known-answer D24 calibration only; no order-26/30/33/34 target annealing."
                if args.mode == "d24-calibration"
                else "Deterministic annealing from one exact committed frontier state."
            ),
            "environment": {
                "hostname": platform.node(),
                "kernel": platform.platform(),
            },
            "input": input_record,
            "replay": " ".join(replay_parts),
            "result": result,
        },
    )
    print(
        f"PASS mode={args.mode} success={result['success']} "
        f"step={result['recovery_step']} best={result['best_state']['score_breakdown']['total']}"
    )
    return 0 if success is not None else 2


if __name__ == "__main__":
    raise SystemExit(main())
