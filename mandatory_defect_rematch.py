#!/usr/bin/env python3
"""Linux-only staged mandatory-defect k3/k4 search over five near openings."""

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
import four_edge_rematch as k4
import map_search
import near_open_search
import near_opening
import three_edge_rematch as k3
import verify


ROOT = Path(__file__).resolve().parent


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def fan_from_payload(value: dict[str, object]) -> blocks.ClosureFan:
    return blocks.ClosureFan(int(value["hub"]), tuple(sorted(value["leaves"])))


def certificate_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    return {"format": "apg-plane-rotation-v1", "vertices": rows}


def build_certificate_seed(entry: dict[str, object], root: Path) -> dict[str, object]:
    source_path = root / entry["source_certificate_path"]
    if file_sha256(source_path) != entry["source_certificate_file_sha256"]:
        raise ValueError("source certificate bytes changed")
    certificate = json.loads(source_path.read_text(encoding="utf-8"))
    verify.verify_certificate(certificate, expected_order=entry["order"])
    if canonical_sha256(certificate) != entry["source_certificate_sha256"]:
        raise ValueError("source certificate canonical hash changed")
    rotation = blocks.normalize_rotation(bt._rotation_from_rows(certificate["vertices"]))
    first, second = (fan_from_payload(fan) for fan in entry["fans"])
    opened, breakdown, alpha, fixed = near_opening.score_opening(
        rotation, first, second
    )
    seed = {
        "format": near_opening.FORMAT,
        "source": {
            "certificate_path": entry["source_certificate_path"],
            "certificate_file_sha256": entry["source_certificate_file_sha256"],
            "certificate_sha256": entry["source_certificate_sha256"],
            "file": entry["upstream"]["file"],
            "order": entry["order"],
            "sha256": entry["upstream"]["sha256"],
            "url": entry["upstream"]["url"],
            "verified_apg": True,
        },
        "fans": entry["fans"],
        "source_rotation": certificate["vertices"],
        "opened_rotation": blocks.rotation_to_certificate(opened)["vertices"],
        "score_breakdown": breakdown,
        "state_sha256": near_opening._state_sha256(alpha),
        "hexagons": near_opening._hexagons(fixed, alpha),
        "claim_scope": "Diagnostic near-opening seed; not a strict block witness.",
    }
    return seed


def load_or_create_seed(entry: dict[str, object], root: Path) -> dict[str, object]:
    path = root / entry["seed_path"]
    if entry["seed_kind"] == "certificate_opening":
        seed = build_certificate_seed(entry, root)
        bt.write_json(path, seed)
    elif entry["seed_kind"] == "committed_near_opening":
        seed = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError("unknown seed kind")
    if file_sha256(path) != entry["seed_file_sha256"]:
        raise ValueError("near-opening seed bytes changed")
    if seed.get("fans") != entry["fans"]:
        raise ValueError("near-opening fans changed")
    if seed.get("state_sha256") != entry["state_sha256"]:
        raise ValueError("near-opening state hash changed")
    if seed.get("score_breakdown") != entry["breakdown"]:
        raise ValueError("near-opening score changed")
    certificate = certificate_from_rows(seed["source_rotation"])
    verify.verify_certificate(certificate, expected_order=entry["order"])
    if canonical_sha256(certificate) != entry["source_certificate_sha256"]:
        raise ValueError("embedded source certificate changed")
    return seed


def abstract_defect_edges(
    fixed: map_search.FixedMap, alpha: list[int]
) -> list[dict[str, object]]:
    current = k3.edge_pairs(alpha)
    endpoint_counts: Counter[tuple[int, int]] = Counter()
    for left, right in current:
        u, v = fixed.dart_vertex[left], fixed.dart_vertex[right]
        endpoint_counts[(min(u, v), max(u, v))] += 1
    defects: list[dict[str, object]] = []
    adjacency = [set() for _ in fixed.cycles]
    for left, right in current:
        u, v = fixed.dart_vertex[left], fixed.dart_vertex[right]
        du, dv = fixed.vertex_degree[u], fixed.vertex_degree[v]
        reasons: list[str] = []
        if u == v:
            reasons.append("loop")
        if endpoint_counts[(min(u, v), max(u, v))] > 1:
            reasons.append("parallel")
        if du == 2 or dv == 2:
            if sorted((du, dv)) != [2, 5]:
                reasons.append("degree2_not_degree5")
        elif du == dv:
            reasons.append("equal_endpoint_degree")
        adjacency[u].add(v)
        adjacency[v].add(u)
        if reasons:
            defects.append({
                "labeled_edge": sorted((u + 1, v + 1)),
                "dart_pair": [left, right],
                "endpoint_degrees": [du, dv],
                "reasons": reasons,
            })
    reached: set[int] = set()
    stack = [0]
    while stack:
        vertex = stack.pop()
        if vertex in reached:
            continue
        reached.add(vertex)
        stack.extend(adjacency[vertex] - reached)
    if len(reached) != len(fixed.cycles):
        raise ValueError("near-opening has a component defect not represented by edges")
    return sorted(defects, key=lambda item: (item["labeled_edge"], item["dart_pair"]))


def auxiliary_edges(
    alpha: list[int], mandatory: tuple[tuple[int, int], ...]
) -> tuple[tuple[int, int], ...]:
    current = k3.edge_pairs(alpha)
    mandatory_set = set(k3.normalize_matching(mandatory))
    if len(mandatory_set) != 2 or not mandatory_set.issubset(current):
        raise ValueError("exactly two current mandatory defect edges are required")
    auxiliary = tuple(edge for edge in current if edge not in mandatory_set)
    if set(auxiliary) != set(current) - mandatory_set:
        raise AssertionError("auxiliary edge family was filtered")
    return auxiliary


def exact_state_key(rotation_hash: str, alpha: list[int]) -> str:
    return f"{rotation_hash}:{near_opening._state_sha256(alpha)}"


def score_plane_candidate(
    fixed: map_search.FixedMap, alpha: list[int]
) -> dict[str, int]:
    valid, reason = k3.plane_valid_gate(fixed, alpha)
    if not valid:
        raise ValueError(f"candidate must pass the plane gate before scoring: {reason}")
    return map_search.score_breakdown(fixed, alpha)


def parent_manifest(parents: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = (
        "id", "order", "seed_path", "seed_file_sha256", "state_sha256",
        "fixed_rotation_hash", "breakdown", "mandatory_defects",
        "current_edge_count", "auxiliary_edges", "k3_attempts", "k4_attempts",
    )
    return [{key: parent[key] for key in keys} for parent in parents]


def load_spec(path: Path, *, require_frozen: bool = True) -> dict[str, object]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("format") != "apg-mandatory-defect-k3-k4-v1":
        raise ValueError("unsupported mandatory-defect specification")
    seeds = spec.get("seeds")
    if not isinstance(seeds, list) or [seed.get("id") for seed in seeds] != [
        "26a", "26b", "29a", "29b", "33"
    ]:
        raise ValueError("five mandatory seeds are missing or reordered")
    k3_attempts = sum((seed["edges"] - 2) * 8 for seed in seeds)
    k4_attempts = sum(math.comb(seed["edges"] - 2, 2) * 60 for seed in seeds)
    if k3_attempts != 1_968 or spec.get("k3_total_attempts") != k3_attempts:
        raise ValueError("mandatory-k3 budget changed")
    if k4_attempts != 359_700 or spec.get("k4_total_attempts") != k4_attempts:
        raise ValueError("mandatory-k4 budget changed")
    if spec.get("combined_total_attempts") != 361_668:
        raise ValueError("combined mandatory-defect budget changed")
    for seed in seeds:
        if seed["k3_attempts"] != (seed["edges"] - 2) * 8:
            raise ValueError("per-seed k3 budget changed")
        if seed["k4_attempts"] != math.comb(seed["edges"] - 2, 2) * 60:
            raise ValueError("per-seed k4 budget changed")
    if require_frozen:
        for key in ("target_state_sha256", "parent_manifest_sha256"):
            if not isinstance(spec.get(key), str) or len(spec[key]) != 64:
                raise ValueError(f"{key} is not frozen")
    return spec


def build_target_state(spec: dict[str, object], root: Path = ROOT) -> dict[str, object]:
    parents: list[dict[str, object]] = []
    for entry in spec["seeds"]:
        seed = load_or_create_seed(entry, root)
        fixed, alpha = near_opening.state_from_seed(seed)
        chi = k3.euler_characteristic(fixed, alpha)
        if chi != 2:
            raise ValueError("opened seed must have Euler characteristic 2")
        if map_search._abstract_graph_ok(fixed, alpha):
            raise ValueError("opened seed must be abstract-invalid")
        defects = abstract_defect_edges(fixed, alpha)
        if len(defects) != 2:
            raise ValueError("opened seed must have exactly two abstract-defect edges")
        if [item["labeled_edge"] for item in defects] != entry["defect_labeled_edges"]:
            raise ValueError("mandatory labeled defects changed")
        mandatory = tuple(tuple(item["dart_pair"]) for item in defects)
        auxiliary = auxiliary_edges(alpha, mandatory)
        if len(alpha) // 2 != entry["edges"] or len(auxiliary) != entry["edges"] - 2:
            raise ValueError("current/auxiliary edge count changed")
        shared = bool(set(defects[0]["labeled_edge"]) & set(defects[1]["labeled_edge"]))
        if shared != entry["defects_share_vertex"]:
            raise ValueError("defect incidence pattern changed")
        parent = {
            "id": entry["id"],
            "order": entry["order"],
            "seed_path": entry["seed_path"],
            "seed_file_sha256": entry["seed_file_sha256"],
            "source_certificate": certificate_from_rows(seed["source_rotation"]),
            "source_certificate_sha256": entry["source_certificate_sha256"],
            "upstream": entry["upstream"],
            "fans": entry["fans"],
            "fixed_rotation": seed["opened_rotation"],
            "fixed_rotation_hash": bt.canonical_map_hash({"vertices": seed["opened_rotation"]}),
            "alpha": alpha,
            "state_sha256": entry["state_sha256"],
            "breakdown": entry["breakdown"],
            "abstract_valid": False,
            "euler_characteristic": 2,
            "mandatory_defects": defects,
            "defects_share_vertex": shared,
            "current_edge_count": len(alpha) // 2,
            "auxiliary_edges": [list(edge) for edge in auxiliary],
            "k3_auxiliary_choices": len(auxiliary),
            "k3_matchings_per_choice": 8,
            "k3_attempts": len(auxiliary) * 8,
            "k4_auxiliary_pairs": math.comb(len(auxiliary), 2),
            "k4_matchings_per_pair": 60,
            "k4_attempts": math.comb(len(auxiliary), 2) * 60,
        }
        parents.append(parent)
    return {
        "format": "apg-mandatory-defect-parent-state-v1",
        "claim_scope": "Pre-compute parent stage for complete mandatory k3 then k4 lanes.",
        "parents": parents,
        "parent_manifest_sha256": canonical_sha256(parent_manifest(parents)),
        "k3_total_attempts": sum(parent["k3_attempts"] for parent in parents),
        "k4_total_attempts": sum(parent["k4_attempts"] for parent in parents),
        "combined_total_attempts": sum(
            parent["k3_attempts"] + parent["k4_attempts"] for parent in parents
        ),
    }


def validate_target_state(
    spec: dict[str, object], payload: dict[str, object]
) -> list[tuple[map_search.FixedMap, list[int], dict[str, object]]]:
    parents = payload.get("parents")
    if not isinstance(parents, list) or [p.get("id") for p in parents] != [
        seed["id"] for seed in spec["seeds"]
    ]:
        raise ValueError("target parents are missing or reordered")
    if canonical_sha256(parent_manifest(parents)) != spec["parent_manifest_sha256"]:
        raise ValueError("target parent manifest changed")
    if payload.get("parent_manifest_sha256") != spec["parent_manifest_sha256"]:
        raise ValueError("embedded parent manifest changed")
    if payload.get("k3_total_attempts") != 1_968 or payload.get("k4_total_attempts") != 359_700:
        raise ValueError("target family budget changed")
    if payload.get("combined_total_attempts") != 361_668:
        raise ValueError("combined target budget changed")
    loaded = []
    for parent, entry in zip(parents, spec["seeds"]):
        if parent["fans"] != entry["fans"] or parent["state_sha256"] != entry["state_sha256"]:
            raise ValueError("target seed identity changed")
        fixed, alpha = map_search.rotation_to_map(bt._rotation_from_rows(parent["fixed_rotation"]))
        if near_opening._state_sha256(alpha) != parent["state_sha256"]:
            raise ValueError("target alpha hash changed")
        if k3.euler_characteristic(fixed, alpha) != 2 or map_search._abstract_graph_ok(fixed, alpha):
            raise ValueError("target parent topology/abstract semantics changed")
        defects = abstract_defect_edges(fixed, alpha)
        if defects != parent["mandatory_defects"] or len(defects) != 2:
            raise ValueError("target mandatory defects changed")
        mandatory = tuple(tuple(item["dart_pair"]) for item in defects)
        auxiliary = auxiliary_edges(alpha, mandatory)
        if [list(edge) for edge in auxiliary] != parent["auxiliary_edges"]:
            raise ValueError("target auxiliary family changed or was filtered")
        loaded.append((fixed, alpha, parent))
    return loaded


def stage(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    payload = build_target_state(spec)
    if payload["parent_manifest_sha256"] != spec["parent_manifest_sha256"]:
        raise ValueError("built parent manifest changed")
    bt.write_json(ROOT / spec["target_state_file"], payload)
    if file_sha256(ROOT / spec["target_state_file"]) != spec["target_state_sha256"]:
        raise ValueError("target-state bytes changed")
    validate_target_state(spec, payload)
    record = {
        "format": "apg-mandatory-defect-k3-k4-stage-v1",
        "claim_scope": "Stage only; zero target rematchings executed.",
        "environment": {"hostname": platform.node(), "system": platform.system()},
        "replay": f"python3 mandatory_defect_rematch.py stage --spec {spec_path}",
        "spec_sha256": file_sha256(spec_path),
        "target_state_sha256": spec["target_state_sha256"],
        "parent_manifest_sha256": spec["parent_manifest_sha256"],
        "seed_count": 5,
        "k3_total_attempts": 1_968,
        "k4_total_attempts": 359_700,
        "combined_total_attempts": 361_668,
        "target_rematchings_executed": 0,
    }
    bt.write_json(ROOT / spec["stage_log"], record)
    return record


def enumerate_lane(
    loaded: list[tuple[map_search.FixedMap, list[int], dict[str, object]]],
    *, lane: str, frontier_limit: int,
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    if lane not in ("k3", "k4"):
        raise ValueError("lane must be k3 or k4")
    started = time.monotonic()
    global_seen: set[str] = set()
    frontier: list[dict[str, object]] = []
    histogram: Counter[int] = Counter()
    global_counts: Counter[str] = Counter()
    per_seed: list[dict[str, object]] = []
    successes: dict[str, dict[str, object]] = {}
    success_checks: dict[str, dict[str, object]] = {}
    for fixed, alpha, parent in loaded:
        seed_counts: Counter[str] = Counter()
        seed_seen: set[tuple[int, ...]] = set()
        mandatory = tuple(tuple(item["dart_pair"]) for item in parent["mandatory_defects"])
        auxiliary = tuple(tuple(edge) for edge in parent["auxiliary_edges"])
        selections = (
            ((edge,), mandatory + (edge,)) for edge in auxiliary
        ) if lane == "k3" else (
            (pair, mandatory + pair) for pair in itertools.combinations(auxiliary, 2)
        )
        for _, selected in selections:
            matchings = k3.deranged_matchings(selected) if lane == "k3" else k4.deranged_matchings(selected)
            for matching in matchings:
                seed_counts["attempts"] += 1
                candidate = (
                    k3.apply_rematching(alpha, selected, matching)
                    if lane == "k3" else k4.apply_rematching(alpha, selected, matching)
                )
                valid, reason = k3.plane_valid_gate(fixed, candidate)
                if not valid:
                    seed_counts["graph_invalid_prunes"] += 1
                    seed_counts[f"{reason}_prunes"] += 1
                    continue
                seed_counts["raw_plane_valid"] += 1
                local_key = tuple(candidate)
                if local_key in seed_seen:
                    seed_counts["per_seed_duplicates"] += 1
                    continue
                seed_seen.add(local_key)
                key = exact_state_key(parent["fixed_rotation_hash"], candidate)
                if key in global_seen:
                    seed_counts["global_duplicates"] += 1
                    continue
                global_seen.add(key)
                seed_counts["distinct_plane_valid"] += 1
                breakdown = score_plane_candidate(fixed, candidate)
                histogram[breakdown["total"]] += 1
                state = k3.serialize_state(fixed, candidate, breakdown)
                state.update(seed_id=parent["id"], fixed_rotation_hash=parent["fixed_rotation_hash"])
                frontier.append(state)
                frontier.sort(key=lambda item: (item["breakdown"]["total"], item["fixed_rotation_hash"], item["state_sha256"]))
                if len(frontier) > frontier_limit:
                    frontier.pop()
                if breakdown["total"] == 0:
                    seed_counts["score_zero"] += 1
                    rotation = map_search.rotation_from_state(fixed, candidate)
                    block = near_open_search._independently_validate_zero(
                        rotation,
                        provenance={"method": f"mandatory-defect-{lane}", "seed_id": parent["id"]},
                        counts=seed_counts,
                    )
                    if block is not None:
                        block_hash = bt.canonical_map_hash(block)
                        successes[block_hash] = block
                        success_checks[block_hash] = near_open_search._close_and_verify(block)
        expected = parent[f"{lane}_attempts"]
        if seed_counts["attempts"] != expected:
            raise AssertionError("per-seed mandatory lane attempt count changed")
        for key, value in seed_counts.items():
            global_counts[key] += value
        per_seed.append({"id": parent["id"], "counts": dict(sorted(seed_counts.items()))})
    expected_total = 1_968 if lane == "k3" else 359_700
    if global_counts["attempts"] != expected_total:
        raise AssertionError("global mandatory lane attempt count changed")
    ordered_frontier = sorted(
        frontier,
        key=lambda item: (
            item["breakdown"]["total"],
            item["fixed_rotation_hash"],
            item["state_sha256"],
        ),
    )
    best_score = (
        ordered_frontier[0]["breakdown"]["total"]
        if ordered_frontier else None
    )
    best_hashes = sorted(
        state["state_sha256"] for state in ordered_frontier
        if state["breakdown"]["total"] == best_score
    )
    return ({
        "complete": True,
        "lane": lane,
        "expected_attempts": expected_total,
        "counts": dict(sorted(global_counts.items())),
        "per_seed": per_seed,
        "score_histogram_distinct": {str(k): histogram[k] for k in sorted(histogram)},
        "frontier_limit": frontier_limit,
        "frontier_states": ordered_frontier,
        "frontier_state_count": len(ordered_frontier),
        "frontier_truncated": len(global_seen) > frontier_limit,
        "best_score": best_score,
        "best_state_hashes": best_hashes,
        "success_hashes": sorted(successes),
        "success_checks": {key: success_checks[key] for key in sorted(success_checks)},
        "wall_seconds": time.monotonic() - started,
    }, successes)


def validate_lane_result(
    result: dict[str, object], expected: int, *,
    parents: list[dict[str, object]] | None = None,
) -> None:
    if not result.get("complete") or result.get("expected_attempts") != expected:
        raise ValueError("mandatory lane output is incomplete")
    required = {
        "lane", "counts", "per_seed", "score_histogram_distinct",
        "frontier_limit", "frontier_states", "frontier_state_count",
        "frontier_truncated", "best_score", "best_state_hashes",
        "success_hashes", "success_checks",
    }
    if not required.issubset(result):
        raise ValueError("mandatory lane output omits exact result fields")
    lane = result["lane"]
    if lane not in ("k3", "k4"):
        raise ValueError("mandatory lane identity changed")
    counts = result.get("counts", {})
    if counts.get("attempts") != expected:
        raise ValueError("mandatory lane attempt accounting is incomplete")
    if counts.get("abstract_graph_prunes", 0) + counts.get("nonspherical_prunes", 0) != counts.get("graph_invalid_prunes", 0):
        raise ValueError("mandatory lane prune accounting does not close")
    if counts.get("graph_invalid_prunes", 0) + counts.get("raw_plane_valid", 0) != expected:
        raise ValueError("mandatory lane plane accounting does not close")
    if (
        counts.get("per_seed_duplicates", 0)
        + counts.get("global_duplicates", 0)
        + counts.get("distinct_plane_valid", 0)
        != counts.get("raw_plane_valid", 0)
    ):
        raise ValueError("mandatory lane deduplication accounting does not close")
    per_seed = result["per_seed"]
    if parents is not None:
        expected_ids = [parent["id"] for parent in parents]
        if [item.get("id") for item in per_seed] != expected_ids:
            raise ValueError("mandatory lane per-seed identities changed")
        for item, parent in zip(per_seed, parents):
            seed_counts = item.get("counts", {})
            seed_expected = parent[f"{lane}_attempts"]
            if seed_counts.get("attempts") != seed_expected:
                raise ValueError("mandatory lane per-seed attempt count changed")
            if (
                seed_counts.get("abstract_graph_prunes", 0)
                + seed_counts.get("nonspherical_prunes", 0)
                != seed_counts.get("graph_invalid_prunes", 0)
            ):
                raise ValueError("mandatory lane per-seed prune accounting does not close")
            if (
                seed_counts.get("graph_invalid_prunes", 0)
                + seed_counts.get("raw_plane_valid", 0)
                != seed_expected
            ):
                raise ValueError("mandatory lane per-seed plane accounting does not close")
            if (
                seed_counts.get("per_seed_duplicates", 0)
                + seed_counts.get("global_duplicates", 0)
                + seed_counts.get("distinct_plane_valid", 0)
                != seed_counts.get("raw_plane_valid", 0)
            ):
                raise ValueError("mandatory lane per-seed deduplication does not close")
        all_count_names = set(counts)
        for item in per_seed:
            all_count_names.update(item["counts"])
        for name in all_count_names:
            if counts.get(name, 0) != sum(
                item["counts"].get(name, 0) for item in per_seed
            ):
                raise ValueError(f"mandatory lane per-seed/global counter mismatch: {name}")
    histogram = result["score_histogram_distinct"]
    if any(int(score) < 0 or value < 0 for score, value in histogram.items()):
        raise ValueError("mandatory lane score histogram is invalid")
    if sum(histogram.values()) != counts.get("distinct_plane_valid", 0):
        raise ValueError("mandatory lane distinct score histogram does not close")
    if histogram.get("0", 0) != counts.get("score_zero", 0):
        raise ValueError("mandatory lane score-zero histogram does not close")
    frontier = result["frontier_states"]
    if result["frontier_state_count"] != len(frontier):
        raise ValueError("mandatory lane frontier count changed")
    ordered = sorted(
        frontier,
        key=lambda state: (
            state["breakdown"]["total"],
            state["fixed_rotation_hash"],
            state["state_sha256"],
        ),
    )
    if frontier != ordered:
        raise ValueError("mandatory lane frontier ordering changed")
    if len(frontier) > result["frontier_limit"]:
        raise ValueError("mandatory lane frontier exceeds its limit")
    if result["frontier_truncated"] != (
        counts.get("distinct_plane_valid", 0) > result["frontier_limit"]
    ):
        raise ValueError("mandatory lane frontier truncation flag changed")
    expected_frontier_count = min(
        counts.get("distinct_plane_valid", 0), result["frontier_limit"]
    )
    if len(frontier) != expected_frontier_count:
        raise ValueError("mandatory lane deterministic frontier is incomplete")
    expected_best = frontier[0]["breakdown"]["total"] if frontier else None
    if result["best_score"] != expected_best:
        raise ValueError("mandatory lane best score changed")
    expected_best_hashes = sorted(
        state["state_sha256"] for state in frontier
        if state["breakdown"]["total"] == expected_best
    )
    if result["best_state_hashes"] != expected_best_hashes:
        raise ValueError("mandatory lane best-state hashes changed")
    if parents is not None:
        parent_by_id = {parent["id"]: parent for parent in parents}
        namespace_keys: set[str] = set()
        for state in frontier:
            seed_id = state.get("seed_id")
            if seed_id not in parent_by_id:
                raise ValueError("mandatory lane frontier seed namespace changed")
            parent = parent_by_id[seed_id]
            if state.get("fixed_rotation_hash") != parent["fixed_rotation_hash"]:
                raise ValueError("mandatory lane frontier fixed-map namespace changed")
            alpha = state.get("alpha")
            if near_opening._state_sha256(alpha) != state.get("state_sha256"):
                raise ValueError("mandatory lane frontier state hash changed")
            fixed, _ = map_search.rotation_to_map(
                bt._rotation_from_rows(parent["fixed_rotation"])
            )
            valid, reason = k3.plane_valid_gate(fixed, alpha)
            if not valid:
                raise ValueError(f"mandatory lane frontier is not plane-valid: {reason}")
            if map_search.score_breakdown(fixed, alpha) != state.get("breakdown"):
                raise ValueError("mandatory lane frontier score changed")
            namespace = exact_state_key(parent["fixed_rotation_hash"], alpha)
            if namespace in namespace_keys:
                raise ValueError("mandatory lane frontier exact state is duplicated")
            namespace_keys.add(namespace)
    if (
        counts.get("zero_score_validation_rejections", 0)
        + counts.get("zero_score_cross_validated", 0)
        != counts.get("score_zero", 0)
    ):
        raise ValueError("mandatory lane score-zero validation accounting does not close")
    success_hashes = result.get("success_hashes", [])
    if success_hashes != sorted(set(success_hashes)):
        raise ValueError("mandatory lane success hashes are not sorted and unique")
    if set(result.get("success_checks", {})) != set(success_hashes):
        raise ValueError("mandatory lane success checks mismatch")


def validate_result_record(spec: dict[str, object], record: dict[str, object], root: Path) -> None:
    if record.get("format") != "apg-mandatory-defect-k3-k4-result-v1":
        raise ValueError("mandatory result format changed")
    spec_path = root / record.get("spec", "")
    if not spec_path.is_file() or record.get("spec_sha256") != file_sha256(spec_path):
        raise ValueError("mandatory result spec bytes changed")
    state_path = root / record.get("target_state_file", "")
    if not state_path.is_file() or record.get("target_state_sha256") != file_sha256(state_path):
        raise ValueError("mandatory result target-state bytes changed")
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    loaded = validate_target_state(spec, payload)
    parents = [parent for _, _, parent in loaded]
    if record.get("parent_manifest_sha256") != spec["parent_manifest_sha256"]:
        raise ValueError("mandatory result parent manifest changed")
    if record.get("combined_expected_attempts") != spec["combined_total_attempts"]:
        raise ValueError("mandatory result combined budget changed")
    validate_lane_result(
        record["k3"], spec["k3_total_attempts"], parents=parents
    )
    validate_lane_result(
        record["k4"], spec["k4_total_attempts"], parents=parents
    )
    hashes = sorted(set(record["k3"]["success_hashes"]) | set(record["k4"]["success_hashes"]))
    if sorted(record.get("certificates", {})) != hashes:
        raise ValueError("mandatory result certificate manifest mismatch")
    for block_hash, entry in record["certificates"].items():
        path = root / entry["path"]
        if file_sha256(path) != entry["sha256"]:
            raise ValueError("mandatory result certificate bytes changed")
        block = bt.load_json(path)
        bt.validate_block(block)
        blocks.validate_block(blocks.normalize_rotation(bt._rotation_from_rows(block["vertices"])))
        if bt.canonical_map_hash(block) != block_hash:
            raise ValueError("mandatory result certificate hash changed")
        replayed_checks = near_open_search._close_and_verify(block)
        for lane in ("k3", "k4"):
            if block_hash in record[lane]["success_hashes"]:
                if record[lane]["success_checks"][block_hash] != replayed_checks:
                    raise ValueError("mandatory result validator/closer checks changed")


def run(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    path = ROOT / spec["target_state_file"]
    if file_sha256(path) != spec["target_state_sha256"]:
        raise ValueError("mandatory target-state bytes changed")
    payload = json.loads(path.read_text(encoding="utf-8"))
    loaded = validate_target_state(spec, payload)
    k3_result, k3_successes = enumerate_lane(loaded, lane="k3", frontier_limit=spec["frontier_limit"])
    k4_result, k4_successes = enumerate_lane(loaded, lane="k4", frontier_limit=spec["frontier_limit"])
    certificates = {}
    for block_hash, block in sorted({**k3_successes, **k4_successes}.items()):
        cert_path = ROOT / spec["certificate_directory"] / f"{block_hash}.json"
        bt.write_json(cert_path, block)
        certificates[block_hash] = {"path": str(cert_path.relative_to(ROOT)), "sha256": file_sha256(cert_path)}
    record = {
        "format": "apg-mandatory-defect-k3-k4-result-v1",
        "claim_scope": "Complete bounded mandatory-defect k3 and k4 lanes over five frozen near openings; a miss is not nonexistence.",
        "environment": {"hostname": platform.node(), "uname": platform.uname()._asdict()},
        "replay": f"python3 mandatory_defect_rematch.py run --spec {spec_path}",
        "spec": str(spec_path),
        "spec_sha256": file_sha256(spec_path),
        "target_state_file": spec["target_state_file"],
        "target_state_sha256": file_sha256(path),
        "parent_manifest_sha256": spec["parent_manifest_sha256"],
        "combined_expected_attempts": spec["combined_total_attempts"],
        "k3": k3_result,
        "k4": k4_result,
        "certificates": certificates,
    }
    validate_result_record(spec, record, ROOT)
    bt.write_json(ROOT / spec["result_log"], record)
    return record


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("mandatory_defect_rematch.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("stage", "run"):
        child = sub.add_parser(command)
        child.add_argument("--spec", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "stage":
        record = stage(args.spec)
        print(f"PASS stage seeds={record['seed_count']} executed=0 combined={record['combined_total_attempts']}")
    else:
        record = run(args.spec)
        print(f"PASS k3={record['k3']['counts']['attempts']} k4={record['k4']['counts']['attempts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
