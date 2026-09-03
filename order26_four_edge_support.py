#!/usr/bin/env python3
"""Linux-only exact localized k4 stage and target runner for order 26.

The staged parent family is the complete set of 56 score-510 plane-valid states
from the closed k3 radius-4 frontier.  Target mode enumerates every four-edge
subset of each state's exact equal-face/bad-white defect support.  Staging and
running are separate commands; staging performs no rematching enumeration.
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
import four_edge_rematch as k4
import map_search
import near_open_search
import three_edge_rematch as k3


EXPECTED_BREAKDOWN = {
    "abstract_graph": 0,
    "equal_face": 120,
    "face_distribution": 0,
    "hex": 0,
    "total": 510,
    "white": 390,
}


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def parent_manifest(states: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = (
        "state_sha256",
        "alpha",
        "breakdown",
        "parent_index",
        "selected_pairs",
        "matching",
    )
    return [{key: state[key] for key in keys} for state in states]


def support_diagnostics(
    fixed: map_search.FixedMap, alpha: list[int]
) -> dict[str, object]:
    """Independently decompose the selector support for a frozen parent."""

    faces, face_of = map_search._faces(fixed, alpha)
    lengths = [len(face) for face in faces]
    current = k3.edge_pairs(alpha)
    equal_edges = tuple(
        edge
        for edge in current
        if face_of[edge[0]] == face_of[edge[1]]
        or lengths[face_of[edge[0]]] == lengths[face_of[edge[1]]]
    )
    bad_vertices = tuple(
        vertex
        for vertex, cycle in enumerate(fixed.cycles)
        if fixed.vertex_degree[vertex] == 2
        and sorted(lengths[face_of[dart]] for dart in cycle) != [5, 6]
    )
    bad_incident = tuple(
        edge
        for edge in current
        if any(fixed.dart_vertex[dart] in bad_vertices for dart in edge)
    )
    support = tuple(sorted(set(equal_edges) | set(bad_incident)))
    selected = k4.equal_white_defect_support_edges(fixed, alpha)
    if selected != support:
        raise ValueError("selector differs from independently derived defect support")
    return {
        "support_edges": [list(edge) for edge in support],
        "equal_face_edges": [list(edge) for edge in equal_edges],
        "bad_white_vertices_zero_based": list(bad_vertices),
        "bad_white_vertices_labels": [vertex + 1 for vertex in bad_vertices],
        "bad_white_incident_edges": [list(edge) for edge in bad_incident],
    }


def support_manifest(states: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = (
        "state_sha256",
        "support_edges",
        "equal_face_edges",
        "bad_white_vertices_zero_based",
        "bad_white_vertices_labels",
        "bad_white_incident_edges",
    )
    return [{key: state[key] for key in keys} for state in states]


def load_spec(path: Path, *, require_target_hash: bool = True) -> dict[str, object]:
    spec = json.loads(path.read_text(encoding="utf-8"))
    if spec.get("format") != "apg-four-edge-order26-support-v1":
        raise ValueError("unsupported order-26 localized k4 specification")
    required = {
        "claim_scope", "input_commit", "parent_result_file",
        "parent_result_sha256", "fixed_state_file", "fixed_state_sha256",
        "fixed_rotation_hash", "base_alpha_sha256", "parent_count",
        "parent_score_histogram", "parent_manifest_sha256",
        "support_manifest_sha256", "support_edges_per_parent",
        "equal_face_edges_per_parent", "bad_white_vertices_per_parent",
        "quadruples_per_parent", "total_quadruples",
        "matchings_per_quadruple", "total_attempts", "frontier_limit",
        "target_state_file", "target_state_sha256", "stage_log",
        "result_log", "certificate_directory",
    }
    if not required.issubset(spec):
        raise ValueError("order-26 localized k4 specification is incomplete")
    if spec["parent_count"] != 56 or spec["parent_score_histogram"] != {"510": 56}:
        raise ValueError("parent population changed")
    if spec["support_edges_per_parent"] != 12:
        raise ValueError("support size changed")
    if spec["equal_face_edges_per_parent"] != 6:
        raise ValueError("equal-face edge count changed")
    if spec["bad_white_vertices_per_parent"] != 4:
        raise ValueError("bad-white count changed")
    quadruples = math.comb(12, 4)
    if quadruples != 495 or spec["quadruples_per_parent"] != quadruples:
        raise ValueError("quadruples-per-parent identity changed")
    total_quadruples = 56 * quadruples
    if total_quadruples != 27_720 or spec["total_quadruples"] != total_quadruples:
        raise ValueError("total quadruple identity changed")
    if spec["matchings_per_quadruple"] != 60:
        raise ValueError("deranged matching count changed")
    attempts = total_quadruples * 60
    if attempts != 1_663_200 or spec["total_attempts"] != attempts:
        raise ValueError("exact target budget changed")
    if spec["frontier_limit"] != 64:
        raise ValueError("frontier limit must be 64")
    if require_target_hash and (
        not isinstance(spec["target_state_sha256"], str)
        or len(spec["target_state_sha256"]) != 64
    ):
        raise ValueError("target state SHA-256 is not frozen")
    return spec


def build_target_state(spec: dict[str, object], root: Path) -> dict[str, object]:
    parent_path = root / spec["parent_result_file"]
    if k4.file_sha256(parent_path) != spec["parent_result_sha256"]:
        raise ValueError("parent result bytes changed")
    fixed_path = root / spec["fixed_state_file"]
    if k4.file_sha256(fixed_path) != spec["fixed_state_sha256"]:
        raise ValueError("fixed-state provenance changed")
    fixed, _, fixed_payload = k3.load_state_file(fixed_path)
    if fixed_payload["fixed_rotation_hash"] != spec["fixed_rotation_hash"]:
        raise ValueError("fixed rotation hash changed")
    if fixed_payload["base_alpha_sha256"] != spec["base_alpha_sha256"]:
        raise ValueError("base alpha hash changed")

    result_payload = json.loads(parent_path.read_text(encoding="utf-8"))
    source_states = result_payload["result"]["frontier_states"]
    parents = sorted(
        (state for state in source_states if state["breakdown"]["total"] == 510),
        key=lambda state: (state["breakdown"]["total"], state["state_sha256"]),
    )
    if len(parents) != 56:
        raise ValueError("expected exactly 56 score-510 parents")
    if canonical_sha256(parent_manifest(parents)) != spec["parent_manifest_sha256"]:
        raise ValueError("parent order/content manifest changed")

    staged: list[dict[str, object]] = []
    for source in parents:
        alpha = list(source["alpha"])
        if source["breakdown"] != EXPECTED_BREAKDOWN:
            raise ValueError("parent score breakdown changed")
        if k3.plane_valid_gate(fixed, alpha) != (True, None):
            raise ValueError("non-plane parent cannot enter localized k4 stage")
        if map_search.score_breakdown(fixed, alpha) != EXPECTED_BREAKDOWN:
            raise ValueError("replayed parent score changed")
        diagnostics = support_diagnostics(fixed, alpha)
        if len(diagnostics["support_edges"]) != 12:
            raise ValueError("localized support is not exactly 12 edges")
        if len(diagnostics["equal_face_edges"]) != 6:
            raise ValueError("equal-face edge count is not exactly six")
        if len(diagnostics["bad_white_vertices_zero_based"]) != 4:
            raise ValueError("bad-white vertex count is not exactly four")
        state = dict(source)
        state.update(diagnostics)
        state["abstract_graph_valid"] = True
        state["spherical"] = True
        state["euler_characteristic"] = 2
        staged.append(state)
    if canonical_sha256(support_manifest(staged)) != spec["support_manifest_sha256"]:
        raise ValueError("support manifest changed")
    return {
        "format": "apg-fixed-alpha-state-v1",
        "claim_scope": spec["claim_scope"],
        "order": 26,
        "edges": 46,
        "parent_result_file": spec["parent_result_file"],
        "parent_result_sha256": spec["parent_result_sha256"],
        "fixed_state_file": spec["fixed_state_file"],
        "fixed_state_sha256": spec["fixed_state_sha256"],
        "fixed_rotation_hash": spec["fixed_rotation_hash"],
        "fixed_rotation": fixed_payload["fixed_rotation"],
        "base_alpha_sha256": spec["base_alpha_sha256"],
        "parent_manifest_sha256": spec["parent_manifest_sha256"],
        "support_manifest_sha256": spec["support_manifest_sha256"],
        "states": staged,
    }


def validate_target_state(
    spec: dict[str, object], payload: dict[str, object]
) -> tuple[map_search.FixedMap, list[list[int]]]:
    if payload.get("format") != "apg-fixed-alpha-state-v1":
        raise ValueError("target state format changed")
    states = payload.get("states")
    if not isinstance(states, list) or len(states) != 56:
        raise ValueError("target state requires exactly 56 parents")
    rotation = bt._rotation_from_rows(payload["fixed_rotation"])
    fixed, base_alpha = map_search.rotation_to_map(rotation)
    if bt.canonical_map_hash({"vertices": payload["fixed_rotation"]}) != spec["fixed_rotation_hash"]:
        raise ValueError("target fixed rotation changed")
    if __import__("near_opening")._state_sha256(base_alpha) != spec["base_alpha_sha256"]:
        raise ValueError("target base alpha changed")
    if canonical_sha256(parent_manifest(states)) != spec["parent_manifest_sha256"]:
        raise ValueError("target parent manifest changed")
    alphas: list[list[int]] = []
    for state in states:
        alpha = list(state["alpha"])
        if __import__("near_opening")._state_sha256(alpha) != state["state_sha256"]:
            raise ValueError("target parent state hash changed")
        if k3.plane_valid_gate(fixed, alpha) != (True, None):
            raise ValueError("non-plane parent cannot enter target frontier")
        if state["breakdown"] != EXPECTED_BREAKDOWN:
            raise ValueError("forbidden target score component or total")
        if map_search.score_breakdown(fixed, alpha) != EXPECTED_BREAKDOWN:
            raise ValueError("target parent score replay changed")
        diagnostics = support_diagnostics(fixed, alpha)
        for key, value in diagnostics.items():
            if state.get(key) != value:
                raise ValueError(f"target support field changed: {key}")
        alphas.append(alpha)
    if canonical_sha256(support_manifest(states)) != spec["support_manifest_sha256"]:
        raise ValueError("target support manifest changed")
    return fixed, alphas


def validate_result(spec: dict[str, object], result: dict[str, object]) -> None:
    if not result.get("complete"):
        raise ValueError("localized k4 result is incomplete")
    required = {
        "mode", "parent_count", "edges", "support_edge_counts",
        "quadruples", "matchings_per_quadruple", "expected_attempts", "counts",
        "score_histogram_distinct", "best_score", "frontier_limit",
        "frontier_states", "frontier_state_count", "frontier_truncated",
        "success_hashes", "success_checks", "candidate_outcomes",
    }
    if not required.issubset(result):
        raise ValueError("localized k4 result omits required exact output")
    expected = {
        "mode": "support-all-quadruples",
        "parent_count": 56,
        "edges": 46,
        "quadruples": 27_720,
        "matchings_per_quadruple": 60,
        "expected_attempts": 1_663_200,
        "frontier_limit": 64,
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise ValueError(f"localized k4 result identity changed: {key}")
    if result.get("support_edge_counts") != [12] * 56:
        raise ValueError("result support counts changed")
    counts = result.get("counts", {})
    required_counts = set(k4.COUNTER_NAMES)
    if not required_counts.issubset(counts):
        raise ValueError("localized k4 result omits exact counters")
    if counts.get("attempts") != spec["total_attempts"]:
        raise ValueError("result attempt count is incomplete")
    if counts.get("abstract_graph_prunes", 0) + counts.get("nonspherical_prunes", 0) != counts.get("graph_invalid_prunes", 0):
        raise ValueError("abstract/spherical prune accounting does not close")
    if counts.get("graph_invalid_prunes", 0) + counts.get("raw_plane_valid", 0) != counts["attempts"]:
        raise ValueError("plane-gate accounting does not close")
    if counts.get("duplicates", 0) + counts.get("distinct_plane_valid", 0) != counts.get("raw_plane_valid", 0):
        raise ValueError("deduplication accounting does not close")
    histogram_total = sum(result["score_histogram_distinct"].values())
    if histogram_total != counts.get("distinct_plane_valid", 0):
        raise ValueError("distinct score histogram does not close")
    if result["frontier_state_count"] != len(result["frontier_states"]):
        raise ValueError("frontier count does not match serialized states")
    ordered = sorted(
        result["frontier_states"],
        key=lambda state: (state["breakdown"]["total"], state["state_sha256"]),
    )
    if result["frontier_states"] != ordered:
        raise ValueError("frontier is not in deterministic score/hash order")
    if result["frontier_state_count"] > result["frontier_limit"]:
        raise ValueError("frontier exceeds its exact limit")
    if result["frontier_truncated"] != (
        counts["distinct_plane_valid"] > result["frontier_limit"]
    ):
        raise ValueError("frontier truncation flag is inconsistent")
    expected_best = ordered[0]["breakdown"]["total"] if ordered else None
    if result["best_score"] != expected_best:
        raise ValueError("best score does not match deterministic frontier")
    if counts["zero_score_validation_rejections"] + counts["zero_score_cross_validated"] != counts["score_zero"]:
        raise ValueError("score-zero validation accounting does not close")
    success_hashes = result["success_hashes"]
    if success_hashes != sorted(set(success_hashes)):
        raise ValueError("success hashes are not unique and sorted")
    if set(result["success_checks"]) != set(success_hashes):
        raise ValueError("success checks do not match cross-validated hashes")


def validate_result_record(
    spec: dict[str, object], record: dict[str, object], root: Path
) -> None:
    """Replay a committed result and every cross-validated certificate."""

    if record.get("format") != "apg-four-edge-order26-support-result-v1":
        raise ValueError("localized k4 result record format changed")
    if record.get("spec_sha256") != k4.file_sha256(root / record["spec"]):
        raise ValueError("localized k4 result spec hash changed")
    state_path = root / record["target_state_file"]
    if record.get("target_state_sha256") != k4.file_sha256(state_path):
        raise ValueError("localized k4 result target-state hash changed")
    result = record.get("result")
    if not isinstance(result, dict):
        raise ValueError("localized k4 result payload is missing")
    validate_result(spec, result)
    certificates = record.get("certificates")
    if not isinstance(certificates, dict):
        raise ValueError("localized k4 certificate manifest is missing")
    success_hashes = result["success_hashes"]
    if set(certificates) != set(success_hashes):
        raise ValueError("certificate manifest does not match success hashes")
    for block_hash in success_hashes:
        entry = certificates[block_hash]
        path = root / entry["path"]
        if k4.file_sha256(path) != entry["sha256"]:
            raise ValueError("cross-validated certificate bytes changed")
        block = bt.load_json(path)
        bt.validate_block(block)
        if bt.canonical_map_hash(block) != block_hash:
            raise ValueError("cross-validated certificate hash changed")
        if near_open_search._close_and_verify(block) != result["success_checks"][block_hash]:
            raise ValueError("validator/closer certificate checks changed")


def environment_record() -> dict[str, object]:
    return {"hostname": platform.node(), "uname": platform.uname()._asdict()}


def stage(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    root = Path(__file__).resolve().parent
    payload = build_target_state(spec, root)
    validate_target_state(spec, payload)
    state_path = root / spec["target_state_file"]
    bt.write_json(state_path, payload)
    state_hash = k4.file_sha256(state_path)
    if state_hash != spec["target_state_sha256"]:
        raise ValueError("generated target state hash changed")
    record = {
        "format": "apg-four-edge-order26-support-stage-v1",
        "claim_scope": "Pre-compute stage only; no localized k4 target enumeration was run.",
        "environment": environment_record(),
        "replay": f"python3 order26_four_edge_support.py stage --spec {spec_path}",
        "spec": str(spec_path),
        "spec_sha256": k4.file_sha256(spec_path),
        "target_state_file": spec["target_state_file"],
        "target_state_sha256": state_hash,
        "parent_manifest_sha256": spec["parent_manifest_sha256"],
        "support_manifest_sha256": spec["support_manifest_sha256"],
        "identities": {
            "parents": 56, "score_histogram": {"510": 56},
            "support_edges_per_parent": 12,
            "equal_face_edges_per_parent": 6,
            "bad_white_vertices_per_parent": 4,
            "quadruples_per_parent": 495,
            "total_quadruples": 27_720,
            "matchings_per_quadruple": 60,
            "total_attempts": 1_663_200,
        },
    }
    bt.write_json(root / spec["stage_log"], record)
    return record


def run(spec_path: Path) -> dict[str, object]:
    spec = load_spec(spec_path)
    root = Path(__file__).resolve().parent
    state_path = root / spec["target_state_file"]
    if k4.file_sha256(state_path) != spec["target_state_sha256"]:
        raise ValueError("target state bytes changed")
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    fixed, parents = validate_target_state(spec, payload)
    started = time.monotonic()
    result, successes = k4.enumerate_four_edge_rematchings(
        fixed, parents, selected_quadruple=None, support_mode=True,
        frontier_limit=spec["frontier_limit"],
    )
    validate_result(spec, result)
    certificates = {}
    for block_hash in sorted(successes):
        path = root / spec["certificate_directory"] / f"{block_hash}.json"
        bt.write_json(path, successes[block_hash])
        certificates[block_hash] = {
            "path": str(path.relative_to(root)),
            "sha256": k4.file_sha256(path),
        }
    record = {
        "format": "apg-four-edge-order26-support-result-v1",
        "claim_scope": spec["claim_scope"],
        "environment": environment_record(),
        "replay": f"python3 order26_four_edge_support.py run --spec {spec_path}",
        "spec": str(spec_path), "spec_sha256": k4.file_sha256(spec_path),
        "target_state_file": spec["target_state_file"],
        "target_state_sha256": k4.file_sha256(state_path),
        "certificates": certificates, "result": result,
        "driver_wall_seconds": time.monotonic() - started,
    }
    bt.write_json(root / spec["result_log"], record)
    return record


def main() -> int:
    if platform.system() != "Linux":
        raise SystemExit("order26_four_edge_support.py is Linux-only")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("stage", "run"):
        child = sub.add_parser(command)
        child.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "stage":
        record = stage(args.spec)
        print(
            f"PASS staged parents={record['identities']['parents']} "
            f"attempts={record['identities']['total_attempts']}"
        )
        return 0
    record = run(args.spec)
    result = record["result"]
    print(
        f"PASS attempts={result['counts']['attempts']} "
        f"distinct={result['counts']['distinct_plane_valid']} "
        f"best={result['best_score']} zero={result['counts']['score_zero']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
