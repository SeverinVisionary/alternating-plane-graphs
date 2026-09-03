#!/usr/bin/env python3
"""Replay topology semantics for every historical near-opening frontier."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import block_tools as bt
import map_search
import near_opening
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
AUDIT_GROUPS = {
    "order26_near_open": (
        "order26_near_open_k4",
        "order26_near_open_radius2",
        "order26_near_open_radius3",
        "order26_near_open_radius4",
        "order26_near_open_radius5",
    ),
    "order26_dual_near_open": (
        "order26_dual_near_open_k4",
        "order26_dual_near_open_radius2",
        "order26_dual_near_open_radius3",
    ),
    "order30_near_open": (
        "order30_near_open_k4",
        "order30_near_open_radius2",
        "order30_near_open_radius3",
    ),
    "order33_near_open": (
        "order33_near_open_k4",
        "order33_near_open_radius2",
    ),
    "order34_near_open": (
        "order34_near_open_k4",
        "order34_near_open_radius2",
        "order34_near_open_radius3",
    ),
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def audit_state(
    fixed: map_search.FixedMap, state: dict[str, object], index: int
) -> dict[str, object]:
    alpha = list(state["alpha"])
    if near_opening._state_sha256(alpha) != state["state_sha256"]:
        raise ValueError("historical frontier alpha hash changed")
    breakdown = map_search.score_breakdown(fixed, alpha)
    if breakdown != state["breakdown"]:
        raise ValueError("historical frontier score replay changed")
    abstract_valid = map_search._abstract_graph_ok(fixed, alpha)
    if not abstract_valid:
        raise ValueError("serialized historical frontier state is abstract-invalid")
    chi = k3.euler_characteristic(fixed, alpha)
    return {
        "index": index,
        "state_sha256": state["state_sha256"],
        "breakdown": breakdown,
        "abstract_valid": True,
        "euler_characteristic": chi,
        "plane_valid": chi == 2,
    }


def build_audit(root: Path = ROOT) -> dict[str, object]:
    families: dict[str, object] = {}
    all_files: list[dict[str, object]] = []
    for family, names in AUDIT_GROUPS.items():
        base_path = root / "results/logs" / f"{names[0]}.json"
        base = json.loads(base_path.read_text(encoding="utf-8"))
        opened_rotation = base.get("opened_rotation")
        if not isinstance(opened_rotation, list):
            raise ValueError(f"{names[0]} does not carry the fixed opened rotation")
        rotation = bt._rotation_from_rows(opened_rotation)
        fixed, base_alpha = map_search.rotation_to_map(rotation)
        family_record = {
            "base_log": str(base_path.relative_to(root)),
            "base_log_sha256": file_sha256(base_path),
            "fixed_rotation": opened_rotation,
            "fixed_rotation_hash": bt.canonical_map_hash({"vertices": opened_rotation}),
            "base_alpha_sha256": near_opening._state_sha256(base_alpha),
            "files": [],
        }
        for name in names:
            path = root / "results/logs" / f"{name}.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            frontier = payload["result"]["frontier_states"]
            states = [audit_state(fixed, state, i) for i, state in enumerate(frontier)]
            chi = Counter(state["euler_characteristic"] for state in states)
            minimum = min(state["breakdown"]["total"] for state in states)
            minimum_chi = Counter(
                state["euler_characteristic"]
                for state in states
                if state["breakdown"]["total"] == minimum
            )
            record = {
                "path": str(path.relative_to(root)),
                "file_sha256": file_sha256(path),
                "frontier_count": len(states),
                "minimum_score": minimum,
                "chi_histogram": {str(k): chi[k] for k in sorted(chi)},
                "minimum_score_chi_histogram": {
                    str(k): minimum_chi[k] for k in sorted(minimum_chi)
                },
                "plane_valid_count": chi.get(2, 0),
                "states": states,
                "state_manifest_sha256": canonical_sha256(states),
            }
            family_record["files"].append(record)
            all_files.append(record)
        families[family] = family_record
    manifest = [
        {
            "path": record["path"],
            "file_sha256": record["file_sha256"],
            "state_manifest_sha256": record["state_manifest_sha256"],
            "chi_histogram": record["chi_histogram"],
            "minimum_score_chi_histogram": record["minimum_score_chi_histogram"],
        }
        for record in all_files
    ]
    return {
        "format": "apg-historical-near-open-topology-audit-v1",
        "claim_scope": (
            "Exact semantic replay of serialized historical frontiers. These are "
            "abstract-map bounded searches; plane-valid requires Euler characteristic 2."
        ),
        "input_commit": "0928583fc81d5e93e1793ef68cf1005ef42164aa",
        "families": families,
        "file_count": len(all_files),
        "frontier_state_count": sum(record["frontier_count"] for record in all_files),
        "audit_manifest_sha256": canonical_sha256(manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_audit()
    bt.write_json(args.output, result)
    print(
        f"PASS files={result['file_count']} states={result['frontier_state_count']} "
        f"manifest={result['audit_manifest_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
