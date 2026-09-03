#!/usr/bin/env python3
"""Linux-only complete mandatory-defect k5 stage and target driver."""

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
import five_edge_rematch as k5
import mandatory_defect_rematch as prior
import map_search
import near_open_search
import near_opening
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
SEED_IDS = ["26a", "26b", "29a", "29b", "33"]
RESULT_COUNTER_NAMES = (
    "selections", "attempts", "graph_invalid_prunes",
    "abstract_graph_prunes", "nonspherical_prunes", "raw_plane_valid",
    "per_seed_duplicates", "global_duplicates", "distinct_plane_valid",
    "score_zero", "zero_score_block_tools_rejections",
    "zero_score_blocks_rejections", "zero_score_validation_rejections",
    "zero_score_cross_validated",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":")
    ).encode()).hexdigest()


def load_spec(path: Path, *, require_frozen: bool = True) -> dict[str, object]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("format") != "apg-mandatory-defect-k5-v1":
        raise ValueError("unsupported mandatory k5 specification")
    seeds = spec.get("seeds")
    if not isinstance(seeds, list) or [seed.get("id") for seed in seeds] != SEED_IDS:
        raise ValueError("five mandatory k5 seeds are missing or reordered")
    if spec.get("matchings_per_selection") != 544 or k5.inclusion_exclusion_count() != 544:
        raise ValueError("mandatory k5 matching count changed")
    selections = 0
    attempts = 0
    for seed in seeds:
        auxiliary = seed["auxiliary_edges"]
        expected_selections = math.comb(auxiliary, 3)
        expected_attempts = expected_selections * 544
        if seed["selections"] != expected_selections or seed["attempts"] != expected_attempts:
            raise ValueError("per-seed mandatory k5 budget changed")
        selections += expected_selections
        attempts += expected_attempts
    if selections != 96_544 or spec.get("total_selections") != selections:
        raise ValueError("mandatory k5 selection budget changed")
    if attempts != 52_519_936 or spec.get("total_attempts") != attempts:
        raise ValueError("mandatory k5 attempt budget changed")
    for key in ("prior_result_file", "parent_state_file"):
        expected = spec[key.replace("file", "sha256")]
        if file_sha256(ROOT / spec[key]) != expected:
            raise ValueError(f"{key} bytes changed")
    parent_payload = json.loads((ROOT / spec["parent_state_file"]).read_text(encoding="utf-8"))
    parent_records = parent_payload.get("parents", [])
    if len(parent_records) != len(seeds):
        raise ValueError("mandatory k5 parent count changed")
    for entry, parent in zip(seeds, parent_records):
        frozen = [item["dart_pair"] for item in parent["mandatory_defects"]]
        if entry.get("mandatory_dart_pairs") != frozen:
            raise ValueError("mandatory k5 defect identity changed")
        if entry.get("auxiliary_edges") != len(parent["auxiliary_edges"]):
            raise ValueError("mandatory k5 auxiliary family changed")
    calibration = spec["calibration"]
    for stem in ("state", "certificate", "log"):
        if file_sha256(ROOT / calibration[f"{stem}_file"]) != calibration[f"{stem}_file_sha256"]:
            raise ValueError(f"k5 calibration {stem} bytes changed")
    if require_frozen:
        for key in ("target_state_sha256", "target_manifest_sha256"):
            if spec.get(key) == "0" * 64:
                raise ValueError(f"{key} is not frozen")
    return spec


def target_manifest(parents: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = (
        "id", "order", "state_sha256", "fixed_rotation_hash",
        "mandatory_dart_pairs", "auxiliary_edges", "auxiliary_edge_count",
        "selections", "matchings_per_selection", "attempts",
    )
    return [{key: parent[key] for key in keys} for parent in parents]


def load_frozen_parents(
    spec: dict[str, object], *, rebuild_sources: bool,
) -> list[tuple[map_search.FixedMap, list[int], dict[str, object]]]:
    old_spec = prior.load_spec(ROOT / spec["prior_spec_file"])
    payload_path = ROOT / spec["parent_state_file"]
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if payload.get("parent_manifest_sha256") != spec["parent_manifest_sha256"]:
        raise ValueError("parent manifest changed")
    if rebuild_sources:
        rebuilt = prior.build_target_state(old_spec, ROOT)
        if rebuilt != payload:
            raise ValueError("source/seed/parent reconstruction changed")
    loaded = prior.validate_target_state(old_spec, payload)
    for (fixed, alpha, parent), entry in zip(loaded, spec["seeds"]):
        mandatory = [item["dart_pair"] for item in parent["mandatory_defects"]]
        checks = {
            "id": parent["id"], "order": parent["order"],
            "state_sha256": parent["state_sha256"],
            "fixed_rotation_hash": parent["fixed_rotation_hash"],
            "mandatory_dart_pairs": mandatory,
            "auxiliary_edges": len(parent["auxiliary_edges"]),
        }
        for key, value in checks.items():
            if entry[key] != value:
                raise ValueError(f"mandatory k5 parent drift: {entry['id']} {key}")
        if k3.euler_characteristic(fixed, alpha) != 2:
            raise ValueError("mandatory k5 parent Euler characteristic changed")
    return loaded


def build_target_state(spec: dict[str, object]) -> dict[str, object]:
    loaded = load_frozen_parents(spec, rebuild_sources=True)
    parents: list[dict[str, object]] = []
    for (fixed, alpha, parent), entry in zip(loaded, spec["seeds"]):
        mandatory = tuple(tuple(item["dart_pair"]) for item in parent["mandatory_defects"])
        auxiliary = tuple(tuple(edge) for edge in parent["auxiliary_edges"])
        if set(auxiliary) != set(k3.edge_pairs(alpha)) - set(mandatory):
            raise ValueError("mandatory k5 auxiliary family was filtered")
        selections = math.comb(len(auxiliary), 3)
        record = {
            "id": parent["id"], "order": parent["order"],
            "state_sha256": parent["state_sha256"],
            "fixed_rotation_hash": parent["fixed_rotation_hash"],
            "mandatory_dart_pairs": [list(pair) for pair in mandatory],
            "auxiliary_edges": [list(edge) for edge in auxiliary],
            "auxiliary_edge_count": len(auxiliary),
            "selections": selections, "matchings_per_selection": 544,
            "attempts": selections * 544,
        }
        if record["attempts"] != entry["attempts"]:
            raise ValueError("mandatory k5 derived attempt count changed")
        parents.append(record)
    manifest = canonical_sha256(target_manifest(parents))
    return {
        "format": "apg-mandatory-defect-k5-target-v1",
        "claim_scope": "Pre-compute exact mandatory-defect k5 target; zero target rematchings executed.",
        "parent_state_file": spec["parent_state_file"],
        "parent_state_sha256": spec["parent_state_sha256"],
        "parent_manifest_sha256": spec["parent_manifest_sha256"],
        "parents": parents,
        "target_manifest_sha256": manifest,
        "total_selections": sum(parent["selections"] for parent in parents),
        "matchings_per_selection": 544,
        "total_attempts": sum(parent["attempts"] for parent in parents),
    }


def validate_target_state(
    spec: dict[str, object], payload: dict[str, object],
) -> list[tuple[map_search.FixedMap, list[int], dict[str, object]]]:
    if payload.get("format") != "apg-mandatory-defect-k5-target-v1":
        raise ValueError("mandatory k5 target format changed")
    parents = payload.get("parents")
    if not isinstance(parents, list) or [p.get("id") for p in parents] != SEED_IDS:
        raise ValueError("mandatory k5 target parents are missing or reordered")
    if canonical_sha256(target_manifest(parents)) != spec["target_manifest_sha256"]:
        raise ValueError("mandatory k5 target manifest changed")
    if payload.get("target_manifest_sha256") != spec["target_manifest_sha256"]:
        raise ValueError("embedded mandatory k5 target manifest changed")
    if payload.get("total_selections") != 96_544 or payload.get("total_attempts") != 52_519_936:
        raise ValueError("mandatory k5 target budget changed")
    loaded = load_frozen_parents(spec, rebuild_sources=False)
    for target, (_, alpha, parent), entry in zip(parents, loaded, spec["seeds"]):
        if target["id"] != entry["id"] or target["state_sha256"] != parent["state_sha256"]:
            raise ValueError("mandatory k5 target parent identity changed")
        if target["fixed_rotation_hash"] != parent["fixed_rotation_hash"]:
            raise ValueError("mandatory k5 fixed rotation changed")
        mandatory = tuple(tuple(item["dart_pair"]) for item in parent["mandatory_defects"])
        auxiliary = tuple(tuple(edge) for edge in target["auxiliary_edges"])
        if tuple(map(tuple, target["mandatory_dart_pairs"])) != mandatory:
            raise ValueError("mandatory k5 defects changed")
        if set(auxiliary) != set(k3.edge_pairs(alpha)) - set(mandatory):
            raise ValueError("mandatory k5 auxiliary family was filtered")
        if list(auxiliary) != list(map(tuple, parent["auxiliary_edges"])):
            raise ValueError("mandatory k5 auxiliary ordering changed")
        if target["attempts"] != math.comb(len(auxiliary), 3) * 544:
            raise ValueError("mandatory k5 target per-seed budget changed")
    return loaded


def state_namespace(seed_id: str, rotation_hash: str, alpha: list[int]) -> str:
    return f"{seed_id}:{rotation_hash}:{near_opening._state_sha256(alpha)}"


def score_plane_candidate(
    fixed: map_search.FixedMap, alpha: list[int],
) -> tuple[dict[str, int] | None, str | None]:
    """Gate abstract topology and the exact sphere before any scoring."""

    valid, reason = k3.plane_valid_gate(fixed, alpha)
    if not valid:
        return None, reason
    return map_search.score_breakdown(fixed, alpha), None


def enumerate_target(
    loaded: list[tuple[map_search.FixedMap, list[int], dict[str, object]]],
    target_payload: dict[str, object], *, frontier_limit: int,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    started = time.monotonic()
    global_seen: set[str] = set()
    histogram: Counter[int] = Counter()
    frontier: list[dict[str, object]] = []
    global_counts: Counter[str] = Counter()
    per_seed: list[dict[str, object]] = []
    successes: dict[str, dict[str, object]] = {}
    success_checks: dict[str, dict[str, object]] = {}
    for (fixed, alpha, parent), staged in zip(loaded, target_payload["parents"]):
        counts: Counter[str] = Counter()
        local_seen: set[tuple[int, ...]] = set()
        mandatory = tuple(map(tuple, staged["mandatory_dart_pairs"]))
        auxiliary = tuple(map(tuple, staged["auxiliary_edges"]))
        for triple in itertools.combinations(auxiliary, 3):
            counts["selections"] += 1
            selected = mandatory + triple
            for matching in k5.deranged_matchings(selected):
                counts["attempts"] += 1
                candidate = k5.apply_rematching(alpha, selected, matching)
                breakdown, reason = score_plane_candidate(fixed, candidate)
                if breakdown is None:
                    counts["graph_invalid_prunes"] += 1
                    counts[f"{reason}_prunes"] += 1
                    continue
                counts["raw_plane_valid"] += 1
                local_key = tuple(candidate)
                if local_key in local_seen:
                    counts["per_seed_duplicates"] += 1
                    continue
                local_seen.add(local_key)
                namespace = state_namespace(parent["id"], parent["fixed_rotation_hash"], candidate)
                if namespace in global_seen:
                    counts["global_duplicates"] += 1
                    continue
                global_seen.add(namespace)
                counts["distinct_plane_valid"] += 1
                histogram[breakdown["total"]] += 1
                state = k3.serialize_state(fixed, candidate, breakdown)
                state.update(
                    seed_id=parent["id"],
                    fixed_rotation_hash=parent["fixed_rotation_hash"],
                    state_namespace=namespace,
                )
                frontier.append(state)
                frontier.sort(key=lambda item: (
                    item["breakdown"]["total"], item["seed_id"],
                    item["fixed_rotation_hash"], item["state_sha256"],
                ))
                if len(frontier) > frontier_limit:
                    frontier.pop()
                if breakdown["total"] == 0:
                    counts["score_zero"] += 1
                    rotation = map_search.rotation_from_state(fixed, candidate)
                    block = near_open_search._independently_validate_zero(
                        rotation,
                        provenance={"method": "mandatory-defect-k5", "seed_id": parent["id"]},
                        counts=counts,
                    )
                    if block is not None:
                        block_hash = bt.canonical_map_hash(block)
                        successes[block_hash] = block
                        success_checks[block_hash] = near_open_search._close_and_verify(block)
        if counts["selections"] != staged["selections"] or counts["attempts"] != staged["attempts"]:
            raise AssertionError("mandatory k5 per-seed enumeration incomplete")
        for name in RESULT_COUNTER_NAMES:
            counts.setdefault(name, 0)
        for key, value in counts.items():
            global_counts[key] += value
        per_seed.append({"id": parent["id"], "counts": dict(sorted(counts.items()))})
    if global_counts["attempts"] != 52_519_936:
        raise AssertionError("mandatory k5 total enumeration incomplete")
    ordered = sorted(frontier, key=lambda item: (
        item["breakdown"]["total"], item["seed_id"],
        item["fixed_rotation_hash"], item["state_sha256"],
    ))
    best_score = ordered[0]["breakdown"]["total"] if ordered else None
    return ({
        "complete": True, "expected_selections": 96_544,
        "matchings_per_selection": 544, "expected_attempts": 52_519_936,
        "counts": dict(sorted(global_counts.items())), "per_seed": per_seed,
        "score_histogram_distinct": {str(k): histogram[k] for k in sorted(histogram)},
        "frontier_limit": frontier_limit, "frontier_states": ordered,
        "frontier_state_count": len(ordered),
        "frontier_truncated": len(global_seen) > frontier_limit,
        "best_score": best_score,
        "best_state_hashes": sorted(
            state["state_sha256"] for state in ordered
            if state["breakdown"]["total"] == best_score
        ) if best_score is not None else [],
        "success_hashes": sorted(successes),
        "success_checks": {key: success_checks[key] for key in sorted(success_checks)},
        "wall_seconds": time.monotonic() - started,
    }, successes)


def validate_result(
    spec: dict[str, object], result: dict[str, object],
    target_payload: dict[str, object],
    loaded: list[tuple[map_search.FixedMap, list[int], dict[str, object]]] | None = None,
) -> None:
    if not result.get("complete") or result.get("expected_attempts") != 52_519_936:
        raise ValueError("mandatory k5 result is incomplete")
    required = {
        "complete", "expected_selections", "matchings_per_selection",
        "expected_attempts", "counts", "per_seed",
        "score_histogram_distinct", "frontier_limit", "frontier_states",
        "frontier_state_count", "frontier_truncated", "best_score",
        "best_state_hashes", "success_hashes", "success_checks",
    }
    if not required.issubset(result):
        raise ValueError("mandatory k5 result omits exact fields")
    if result.get("expected_selections") != 96_544 or result.get("matchings_per_selection") != 544:
        raise ValueError("mandatory k5 result selection identity changed")
    counts = result.get("counts", {})
    if not isinstance(counts, dict):
        raise ValueError("mandatory k5 counters are malformed")
    if not set(RESULT_COUNTER_NAMES).issubset(counts):
        raise ValueError("mandatory k5 result omits exact counters")
    if counts.get("attempts") != 52_519_936 or counts.get("selections") != 96_544:
        raise ValueError("mandatory k5 result budget is incomplete")
    if counts.get("abstract_graph_prunes", 0) + counts.get("nonspherical_prunes", 0) != counts.get("graph_invalid_prunes", 0):
        raise ValueError("mandatory k5 prune accounting does not close")
    if counts.get("graph_invalid_prunes", 0) + counts.get("raw_plane_valid", 0) != counts["attempts"]:
        raise ValueError("mandatory k5 plane accounting does not close")
    if counts.get("per_seed_duplicates", 0) + counts.get("global_duplicates", 0) + counts.get("distinct_plane_valid", 0) != counts.get("raw_plane_valid", 0):
        raise ValueError("mandatory k5 dedup accounting does not close")
    per_seed = result.get("per_seed", [])
    if [item.get("id") for item in per_seed] != SEED_IDS:
        raise ValueError("mandatory k5 result seeds changed")
    for item, staged in zip(per_seed, target_payload["parents"]):
        seed_counts = item["counts"]
        if not set(RESULT_COUNTER_NAMES).issubset(seed_counts):
            raise ValueError("mandatory k5 per-seed result omits exact counters")
        if seed_counts.get("selections") != staged["selections"] or seed_counts.get("attempts") != staged["attempts"]:
            raise ValueError("mandatory k5 per-seed result budget changed")
        if seed_counts.get("abstract_graph_prunes", 0) + seed_counts.get("nonspherical_prunes", 0) != seed_counts.get("graph_invalid_prunes", 0):
            raise ValueError("mandatory k5 per-seed prune accounting does not close")
        if seed_counts.get("graph_invalid_prunes", 0) + seed_counts.get("raw_plane_valid", 0) != seed_counts["attempts"]:
            raise ValueError("mandatory k5 per-seed plane accounting does not close")
        if seed_counts.get("per_seed_duplicates", 0) + seed_counts.get("global_duplicates", 0) + seed_counts.get("distinct_plane_valid", 0) != seed_counts.get("raw_plane_valid", 0):
            raise ValueError("mandatory k5 per-seed dedup accounting does not close")
    counter_names = set(counts)
    for item in per_seed:
        if not isinstance(item.get("counts"), dict):
            raise ValueError("mandatory k5 per-seed counters are malformed")
        counter_names.update(item["counts"])
    for name in counter_names:
        values = [item["counts"].get(name, 0) for item in per_seed]
        global_value = counts.get(name, 0)
        if not isinstance(global_value, int) or isinstance(global_value, bool) or global_value < 0:
            raise ValueError(f"mandatory k5 global counter is invalid: {name}")
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in values):
            raise ValueError(f"mandatory k5 per-seed counter is invalid: {name}")
        if global_value != sum(values):
            raise ValueError(f"mandatory k5 per-seed/global counter mismatch: {name}")
    histogram = result.get("score_histogram_distinct", {})
    if not isinstance(histogram, dict):
        raise ValueError("mandatory k5 score histogram is malformed")
    for score, value in histogram.items():
        if (
            not isinstance(score, str) or not score.isdigit()
            or str(int(score)) != score
            or not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            raise ValueError("mandatory k5 score histogram is invalid")
    if sum(histogram.values()) != counts.get("distinct_plane_valid", 0):
        raise ValueError("mandatory k5 score histogram does not close")
    if histogram.get("0", 0) != counts.get("score_zero", 0):
        raise ValueError("mandatory k5 score-zero histogram does not close")
    frontier = result.get("frontier_states", [])
    frontier_limit = result.get("frontier_limit")
    if not isinstance(frontier_limit, int) or isinstance(frontier_limit, bool) or frontier_limit <= 0:
        raise ValueError("mandatory k5 frontier limit is invalid")
    if frontier_limit != spec["frontier_limit"]:
        raise ValueError("mandatory k5 frontier limit changed")
    ordered = sorted(frontier, key=lambda item: (
        item["breakdown"]["total"], item["seed_id"],
        item["fixed_rotation_hash"], item["state_sha256"],
    ))
    if frontier != ordered or result.get("frontier_state_count") != len(frontier):
        raise ValueError("mandatory k5 frontier changed")
    expected_frontier_count = min(counts.get("distinct_plane_valid", 0), frontier_limit)
    if len(frontier) != expected_frontier_count:
        raise ValueError("mandatory k5 deterministic frontier is incomplete")
    if result.get("frontier_truncated") != (counts.get("distinct_plane_valid", 0) > frontier_limit):
        raise ValueError("mandatory k5 frontier truncation changed")
    best_score = frontier[0]["breakdown"]["total"] if frontier else None
    best_hashes = sorted(
        state["state_sha256"] for state in frontier
        if state["breakdown"]["total"] == best_score
    ) if best_score is not None else []
    if result.get("best_score") != best_score or result.get("best_state_hashes") != best_hashes:
        raise ValueError("mandatory k5 best-state manifest changed")
    if loaded is None:
        loaded = validate_target_state(spec, target_payload)
    parent_by_id = {
        parent["id"]: (fixed, parent) for fixed, _, parent in loaded
    }
    namespaces: set[str] = set()
    for state in frontier:
        seed_id = state.get("seed_id")
        if seed_id not in parent_by_id:
            raise ValueError("mandatory k5 frontier seed namespace changed")
        fixed, parent = parent_by_id[seed_id]
        if state.get("fixed_rotation_hash") != parent["fixed_rotation_hash"]:
            raise ValueError("mandatory k5 frontier fixed-map namespace changed")
        alpha = state.get("alpha")
        if not isinstance(alpha, list) or near_opening._state_sha256(alpha) != state.get("state_sha256"):
            raise ValueError("mandatory k5 frontier state hash changed")
        valid, reason = k3.plane_valid_gate(fixed, alpha)
        if not valid:
            raise ValueError(f"mandatory k5 frontier is not plane-valid: {reason}")
        if map_search.score_breakdown(fixed, alpha) != state.get("breakdown"):
            raise ValueError("mandatory k5 frontier score changed")
        replayed_rotation = map_search.rotation_from_state(fixed, alpha)
        expected_rotation_rows = [
            {"id": vertex, "clockwise": replayed_rotation[vertex]}
            for vertex in sorted(replayed_rotation)
        ]
        if expected_rotation_rows != state.get("rotation"):
            raise ValueError("mandatory k5 frontier rotation changed")
        namespace = state_namespace(seed_id, parent["fixed_rotation_hash"], alpha)
        if state.get("state_namespace") != namespace:
            raise ValueError("mandatory k5 frontier exact namespace changed")
        if namespace in namespaces:
            raise ValueError("mandatory k5 frontier exact state is duplicated")
        namespaces.add(namespace)
    if counts.get("zero_score_validation_rejections", 0) + counts.get("zero_score_cross_validated", 0) != counts.get("score_zero", 0):
        raise ValueError("mandatory k5 score-zero accounting does not close")
    success_hashes = result.get("success_hashes", [])
    if success_hashes != sorted(set(success_hashes)):
        raise ValueError("mandatory k5 success hashes are not sorted and unique")
    if set(result.get("success_checks", {})) != set(success_hashes):
        raise ValueError("mandatory k5 success checks changed")


def validate_result_record(
    spec: dict[str, object], record: dict[str, object], root: Path = ROOT,
) -> None:
    if record.get("format") != "apg-mandatory-defect-k5-result-v1":
        raise ValueError("mandatory k5 result record format changed")
    if record.get("spec_sha256") != file_sha256(root / record["spec"]):
        raise ValueError("mandatory k5 result spec bytes changed")
    if record.get("target_state_sha256") != file_sha256(root / record["target_state_file"]):
        raise ValueError("mandatory k5 target bytes changed")
    payload = json.loads((root / record["target_state_file"]).read_text(encoding="utf-8"))
    loaded = validate_target_state(spec, payload)
    validate_result(spec, record["result"], payload, loaded)
    validate_certificate_manifest(record["result"], record.get("certificates", {}), root)


def validate_certificate_manifest(
    result: dict[str, object], certificates: object, root: Path = ROOT,
) -> None:
    """Replay every reported success through both validators and both closers."""

    hashes = result["success_hashes"]
    if not isinstance(certificates, dict) or set(certificates) != set(hashes):
        raise ValueError("mandatory k5 certificate manifest changed")
    for block_hash in hashes:
        entry = certificates[block_hash]
        path = root / entry["path"]
        if file_sha256(path) != entry["sha256"]:
            raise ValueError("mandatory k5 certificate bytes changed")
        block = bt.load_json(path)
        bt.validate_block(block)
        blocks.validate_block(blocks.normalize_rotation(bt._rotation_from_rows(block["vertices"])))
        if bt.canonical_map_hash(block) != block_hash:
            raise ValueError("mandatory k5 certificate hash changed")
        if near_open_search._close_and_verify(block) != result["success_checks"][block_hash]:
            raise ValueError("mandatory k5 validator/closer checks changed")


def stage(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    payload = build_target_state(spec)
    if payload["target_manifest_sha256"] != spec["target_manifest_sha256"]:
        raise ValueError("built mandatory k5 manifest changed")
    bt.write_json(ROOT / spec["target_state_file"], payload)
    if file_sha256(ROOT / spec["target_state_file"]) != spec["target_state_sha256"]:
        raise ValueError("mandatory k5 target bytes changed")
    validate_target_state(spec, payload)
    record = {
        "format": "apg-mandatory-defect-k5-stage-v1",
        "claim_scope": "Pre-compute stage only; zero mandatory k5 target rematchings executed.",
        "environment": {"hostname": platform.node(), "uname": platform.uname()._asdict()},
        "replay": f"python3 mandatory_defect_k5.py stage --spec {spec_path}",
        "spec_sha256": file_sha256(spec_path),
        "target_state_sha256": spec["target_state_sha256"],
        "target_manifest_sha256": spec["target_manifest_sha256"],
        "parent_manifest_sha256": spec["parent_manifest_sha256"],
        "total_selections": 96_544, "matchings_per_selection": 544,
        "total_attempts": 52_519_936, "target_rematchings_executed": 0,
    }
    bt.write_json(ROOT / spec["stage_log"], record)
    return record


def run(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    target_path = ROOT / spec["target_state_file"]
    if file_sha256(target_path) != spec["target_state_sha256"]:
        raise ValueError("mandatory k5 target bytes changed")
    payload = json.loads(target_path.read_text(encoding="utf-8"))
    loaded = validate_target_state(spec, payload)
    result, successes = enumerate_target(loaded, payload, frontier_limit=spec["frontier_limit"])
    validate_result(spec, result, payload, loaded)
    certificates = {}
    for block_hash, block in sorted(successes.items()):
        path = ROOT / spec["certificate_directory"] / f"{block_hash}.json"
        bt.write_json(path, block)
        certificates[block_hash] = {"path": str(path.relative_to(ROOT)), "sha256": file_sha256(path)}
    record = {
        "format": "apg-mandatory-defect-k5-result-v1",
        "spec": str(spec_path), "spec_sha256": file_sha256(spec_path),
        "target_state_file": spec["target_state_file"],
        "target_state_sha256": file_sha256(target_path),
        "result": result, "certificates": certificates,
    }
    validate_result_record(spec, record)
    bt.write_json(ROOT / spec["result_log"], record)
    return record


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("mandatory_defect_k5.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("stage", "run"):
        child = sub.add_parser(command)
        child.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    record = stage(args.spec) if args.command == "stage" else run(args.spec)
    if args.command == "stage":
        print(f"PASS stage selections={record['total_selections']} attempts={record['total_attempts']} executed=0")
    else:
        print(f"PASS attempts={record['result']['counts']['attempts']} zero={record['result']['counts'].get('score_zero', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
