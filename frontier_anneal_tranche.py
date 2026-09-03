#!/usr/bin/env python3
"""Linux-only exact replay and bounded frontier-annealing tranche runner."""

from __future__ import annotations

import argparse
import json
import platform
import time
from collections import Counter
from pathlib import Path

import block_tools as bt
import frontier_anneal


COUNTER_NAMES = (
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
)


def load_spec(path: Path) -> dict[str, object]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("format") != "apg-frontier-anneal-tranche-v1":
        raise ValueError("unsupported tranche format")
    required = {
        "input_commit",
        "seed_file",
        "seed_file_sha256",
        "frontier_log",
        "expected_initial_score",
        "total_requested_steps",
        "jobs",
    }
    if not required.issubset(spec):
        raise ValueError("tranche specification has missing explicit fields")
    jobs = spec["jobs"]
    if not isinstance(jobs, list) or len(jobs) != 12:
        raise ValueError("tranche must contain exactly twelve jobs")
    job_ids = [job.get("job_id") for job in jobs]
    if len(set(job_ids)) != 12:
        raise ValueError("tranche job IDs must be unique")
    total = 0
    for job in jobs:
        for field in (
            "job_id",
            "state_index",
            "state_sha256",
            "lane",
            "rng_seed",
            "steps",
            "schedule",
            "temperature_start",
            "temperature_end",
        ):
            if field not in job:
                raise ValueError(f"job lacks explicit {field}")
        if job["schedule"] != "geometric":
            raise ValueError("production jobs must explicitly use geometric schedule")
        total += job["steps"]
    if total != 3_000_000 or total != spec["total_requested_steps"]:
        raise ValueError("tranche requested-step total must be exactly 3000000")
    return spec


def replay_jobs(spec: dict[str, object], root: Path) -> list[dict[str, object]]:
    seed_path = root / spec["seed_file"]
    frontier_path = root / spec["frontier_log"]
    records = []
    for job in spec["jobs"]:
        fixed, alpha, record = frontier_anneal.load_frontier_state(
            seed_path,
            frontier_path,
            expected_seed_sha256=spec["seed_file_sha256"],
            state_sha256=job["state_sha256"],
        )
        if record["score_breakdown"]["total"] != spec["expected_initial_score"]:
            raise ValueError(f"{job['job_id']} initial score changed")
        records.append({"job": job, "fixed": fixed, "alpha": alpha, "input": record})
    return records


def aggregate_results(
    spec: dict[str, object], lane_records: list[dict[str, object]]
) -> dict[str, object]:
    totals: Counter[str] = Counter()
    histogram: Counter[int] = Counter()
    lane_manifest = []
    global_minimum = None
    global_best = {}
    total_wall = 0.0
    for lane in lane_records:
        result = lane["result"]
        counts = result["counts"]
        totals.update({name: counts.get(name, 0) for name in COUNTER_NAMES})
        score = result["best_state"]["score_breakdown"]["total"]
        state_hash = result["best_state"]["state_sha256"]
        histogram[score] += 1
        total_wall += result.get("wall_seconds", 0.0)
        if global_minimum is None or score < global_minimum:
            global_minimum = score
            global_best = {state_hash: result["best_state"]}
        elif score == global_minimum:
            global_best[state_hash] = result["best_state"]
        job = lane["job"]
        lane_manifest.append(
            {
                "job_id": job["job_id"],
                "state_index": job["state_index"],
                "input_state_sha256": job["state_sha256"],
                "lane": job["lane"],
                "rng_seed": job["rng_seed"],
                "steps_requested": result["steps_requested"],
                "steps_executed": result["steps_executed"],
                "temperature": result["temperature"],
                "counts": counts,
                "best_score": score,
                "best_state_sha256": state_hash,
                "current_score": result["current_state"]["score_breakdown"]["total"],
                "current_state_sha256": result["current_state"]["state_sha256"],
                "success": result["success"],
                "success_block_hash": result["success_block_hash"],
            }
        )
    completed = len(lane_records)
    success = any(lane["result"]["success"] for lane in lane_records)
    return {
        "complete": success or completed == len(spec["jobs"]),
        "stopped_early_for_success": success and completed < len(spec["jobs"]),
        "jobs_requested": len(spec["jobs"]),
        "jobs_completed": completed,
        "total_steps_requested": spec["total_requested_steps"],
        "total_steps_executed": totals["move_attempts"],
        "counts": dict(sorted(totals.items())),
        "best_score_histogram": {
            str(score): count for score, count in sorted(histogram.items())
        },
        "global_minimum_score": global_minimum,
        "global_best_states": [global_best[key] for key in sorted(global_best)],
        "lane_manifest": lane_manifest,
        "success": success,
        "bounded_claim": (
            "A witness was found within this explicitly bounded tranche."
            if success
            else "No witness was found in this 12-lane, 3000000-requested-move tranche; this is not nonexistence."
        ),
        "lane_wall_seconds_sum": total_wall,
    }


def run_tranche(
    spec_path: Path, output_directory: Path, aggregate_log: Path
) -> dict[str, object]:
    if platform.system() != "Linux":
        raise SystemExit("frontier_anneal_tranche.py is Linux-only")
    root = Path(__file__).resolve().parent
    spec = load_spec(spec_path)
    replayed = replay_jobs(spec, root)
    output_directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    lane_records = []
    for replay in replayed:
        job = replay["job"]
        success, result, _ = frontier_anneal.anneal(
            replay["fixed"],
            replay["alpha"],
            seed=job["rng_seed"],
            steps=job["steps"],
            temperature_start=job["temperature_start"],
            temperature_end=job["temperature_end"],
            schedule=job["schedule"],
        )
        lane_log = {
            "format": "apg-frontier-anneal-lane-v1",
            "claim_scope": "One bounded order-26 frontier-annealing lane; no witness is not nonexistence.",
            "job": job,
            "input": replay["input"],
            "result": result,
        }
        bt.write_json(output_directory / f"{job['job_id']}.json", lane_log)
        lane_records.append({"job": job, "result": result})
        print(
            f"DONE {job['job_id']} attempts={result['steps_executed']} "
            f"accepted={result['counts']['accepted_moves']} "
            f"best={result['best_state']['score_breakdown']['total']} "
            f"zero={result['counts']['zero_score_candidates']}"
        , flush=True)
        if success is not None:
            bt.write_json(output_directory / f"{job['job_id']}-witness.json", success)
            break
    aggregate = aggregate_results(spec, lane_records)
    aggregate["wall_seconds"] = time.monotonic() - started
    replay_command = (
        f"python3 frontier_anneal_tranche.py --spec {spec_path} "
        f"--output-directory {output_directory} --aggregate-log {aggregate_log}"
    )
    payload = {
        "format": "apg-frontier-anneal-tranche-result-v1",
        "spec": str(spec_path),
        "spec_sha256": frontier_anneal.file_sha256(spec_path),
        "environment": {
            "uname": platform.uname()._asdict(),
            "hostname": platform.node(),
        },
        "replay": replay_command,
        "result": aggregate,
    }
    bt.write_json(aggregate_log, payload)
    return payload


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("frontier_anneal_tranche.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--aggregate-log", type=Path, required=True)
    args = parser.parse_args()
    payload = run_tranche(args.spec, args.output_directory, args.aggregate_log)
    result = payload["result"]
    print(
        f"PASS jobs={result['jobs_completed']} attempts={result['total_steps_executed']} "
        f"best={result['global_minimum_score']} success={result['success']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
