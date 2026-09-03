#!/usr/bin/env python3
"""Perform the separate exact-26 audit required before ``MANIFEST_COMPLETE``.

``compose_target_witnesses.py`` intentionally stops one boundary short of a
completion claim.  This auditor re-reads its durable package, checks that the
frozen target set is exact, reconstructs every source block and composition
trace, rechecks hashes and predicted Section-8 profiles, and runs both APG
verifiers again in fresh subprocesses.  Only a successful production audit of
all 26 frozen orders writes ``MANIFEST_COMPLETE``.

The optional representation mapping is for small published controls.  A
control audit is useful for testing the machinery, but it deliberately never
writes the production completion marker.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import block_arithmetic
import blocks
import compose_target_witnesses as promotion
import structural_audit


ROOT = Path(__file__).resolve().parent
VERIFY = ROOT / "verify.py"
VERIFY_DARTS = ROOT / "verify_darts.py"
MANIFEST_NAME = promotion.MANIFEST_NAME
COMPLETE_MARKER = promotion.COMPLETE_MARKER
FINAL_AUDIT_NAME = "final_audit.json"
FINAL_AUDIT_FORMAT = "apg-target-promotion-final-audit-v1"


class FinalAuditError(RuntimeError):
    """The promotion package is not eligible for an all-target claim."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Refuse an object whose raw JSON spelling has ambiguous semantics."""

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(token: str) -> object:
    raise ValueError(f"non-JSON numeric constant {token!r}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_json_bytes(value))
    return _sha256(path)


def _read_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise FinalAuditError(f"cannot read {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise FinalAuditError(f"{label} at {path} is not a JSON object")
    return value


def _safe_path(root: Path, value: object, *, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise FinalAuditError(f"{label} must be a nonempty package-relative path")
    candidate = Path(value)
    if candidate.is_absolute():
        raise FinalAuditError(f"{label} must be package-relative")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise FinalAuditError(f"{label} escapes the promotion package") from exc
    if not resolved.is_file():
        raise FinalAuditError(f"{label} is not a regular file: {resolved}")
    return resolved


def _require_digest(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise FinalAuditError(f"{label} is not a lowercase SHA-256 digest")
    return value


def _hash_bound_path(
    root: Path, entry: Mapping[str, object], *, path_field: str, sha_field: str, label: str
) -> Path:
    path = _safe_path(root, entry.get(path_field), label=path_field)
    expected = _require_digest(entry.get(sha_field), label=sha_field)
    if _sha256(path) != expected:
        raise FinalAuditError(f"{label} SHA-256 mismatch")
    return path


def _canonical_map_sha(certificate: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(
            certificate, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("ascii")
    ).hexdigest()


def _run_checker(
    checker: Path, certificate: Path, *, expected_order: int
) -> dict[str, object]:
    command = [
        sys.executable,
        str(checker),
        str(certificate.resolve()),
        "--expect-order",
        str(expected_order),
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return {
            "checker": checker.name,
            "command": command,
            "returncode": None,
            "stdout": "",
            "stderr": f"could not launch checker: {exc}",
            "passed": False,
        }
    return {
        "checker": checker.name,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def _checker_pair(certificate: Path, *, expected_order: int) -> list[dict[str, object]]:
    return [
        _run_checker(VERIFY, certificate, expected_order=expected_order),
        _run_checker(VERIFY_DARTS, certificate, expected_order=expected_order),
    ]


def _normalize_representations(
    representations: Mapping[int, Sequence[int]] | None,
) -> tuple[dict[int, tuple[int, ...]], bool]:
    if representations is None:
        return block_arithmetic.boolean_primary_t0_target_representations(), True
    if not isinstance(representations, Mapping) or not representations:
        raise FinalAuditError("representations must be a nonempty target-to-chain mapping")
    result: dict[int, tuple[int, ...]] = {}
    for target, raw_chain in sorted(representations.items()):
        if not isinstance(target, int) or isinstance(target, bool) or target < 4:
            raise FinalAuditError(f"invalid control target order {target!r}")
        if isinstance(raw_chain, (str, bytes)) or not isinstance(raw_chain, Sequence):
            raise FinalAuditError(f"control target {target} chain is not a sequence")
        chain = tuple(raw_chain)
        if not chain or any(
            not isinstance(order, int) or isinstance(order, bool) or order < 4
            for order in chain
        ):
            raise FinalAuditError(f"control target {target} has an invalid chain")
        if block_arithmetic.apg_order(chain) != target:
            raise FinalAuditError(f"control target {target} chain has the wrong Section-8 order")
        result[target] = chain
    return result, False


def _block_t0_profile(block: blocks.Block, *, order: int) -> tuple[int, int]:
    """Independently reconstruct the exact portable t/r data for one block."""

    try:
        audit = structural_audit.analyze_block(structural_audit.audit_data_from_block(block))
    except (TypeError, ValueError, blocks.BlockError) as exc:
        raise FinalAuditError(f"block {order} structural audit failed: {exc}") from exc
    variants = audit.get("variants") if isinstance(audit, dict) else None
    if not isinstance(variants, list) or len(variants) != 9:
        raise FinalAuditError(f"block {order} structural audit does not contain nine closures")
    r_values: set[int] = set()
    for variant in variants:
        if not isinstance(variant, dict):
            raise FinalAuditError(f"block {order} structural audit has a malformed closure")
        value = variant.get("r")
        if not isinstance(value, int) or isinstance(value, bool):
            raise FinalAuditError(f"block {order} structural audit lacks an integer r")
        if variant.get("t_vertex") != 0 or variant.get("t_face") != 0:
            raise FinalAuditError(f"block {order} is not portable t=0 across all closures")
        r_values.add(value)
    if len(r_values) != 1:
        raise FinalAuditError(f"block {order} does not have one closure-invariant r")
    return next(iter(r_values)), 0


def _load_blocks(
    root: Path, manifest: Mapping[str, object], required_orders: set[int]
) -> tuple[dict[int, blocks.Block], dict[int, int], list[dict[str, object]]]:
    raw_entries = manifest.get("blocks")
    if not isinstance(raw_entries, dict):
        raise FinalAuditError("promotion manifest blocks must be an object")
    block_t = manifest.get("block_t")
    if not isinstance(block_t, dict):
        raise FinalAuditError("promotion manifest lacks its audited block_t map")
    result: dict[int, blocks.Block] = {}
    r_values: dict[int, int] = {}
    audits: list[dict[str, object]] = []
    for order in sorted(required_orders):
        entry = raw_entries.get(str(order))
        if not isinstance(entry, dict):
            raise FinalAuditError(f"promotion manifest omits block {order}")
        certificate_path = _hash_bound_path(
            root,
            entry,
            path_field="canonical_certificate_path",
            sha_field="canonical_certificate_sha256",
            label=f"block {order} canonical certificate",
        )
        certificate = _read_object(certificate_path, label=f"block {order} canonical certificate")
        try:
            rotation = blocks.rotation_from_certificate(certificate)
            if blocks.rotation_to_certificate(rotation) != certificate:
                raise blocks.BlockError("certificate is not canonical")
            if len(rotation) != order:
                raise blocks.BlockError(f"certificate has order {len(rotation)}")
            sockets = blocks.validate_block(rotation)
        except (TypeError, ValueError, blocks.BlockError) as exc:
            raise FinalAuditError(f"block {order} fails strict Section-8 validation: {exc}") from exc
        strict = entry.get("strict_block_validation")
        if not isinstance(strict, dict) or strict.get("passed") is not True:
            raise FinalAuditError(f"block {order} manifest does not record strict validation")
        r, t = _block_t0_profile(blocks.Block(rotation, sockets), order=order)
        if entry.get("r") != r or entry.get("t") != t or block_t.get(str(order)) != t:
            raise FinalAuditError(f"block {order} manifest t/r evidence disagrees with independent audit")
        closure_entries = entry.get("closure_checks")
        if not isinstance(closure_entries, list) or len(closure_entries) != 9:
            raise FinalAuditError(f"block {order} manifest does not retain nine closure checks")
        expected_closures = {
            hub_indices: closed
            for hub_indices, closed in blocks.close_block_variants(blocks.Block(rotation, sockets))
        }
        seen: set[tuple[int, int]] = set()
        closure_audits: list[dict[str, object]] = []
        for closure_entry in closure_entries:
            if not isinstance(closure_entry, dict):
                raise FinalAuditError(f"block {order} has a malformed closure entry")
            raw_hubs = closure_entry.get("hub_indices")
            if (
                not isinstance(raw_hubs, list)
                or len(raw_hubs) != 2
                or any(not isinstance(value, int) or isinstance(value, bool) for value in raw_hubs)
            ):
                raise FinalAuditError(f"block {order} closure has malformed hub indices")
            hubs = (raw_hubs[0], raw_hubs[1])
            if hubs not in expected_closures or hubs in seen:
                raise FinalAuditError(f"block {order} closure grid is incomplete or duplicated")
            seen.add(hubs)
            closed_path = _hash_bound_path(
                root,
                closure_entry,
                path_field="certificate_path",
                sha_field="certificate_sha256",
                label=f"block {order} closure {hubs}",
            )
            closed_certificate = _read_object(closed_path, label=f"block {order} closure {hubs}")
            expected_certificate = blocks.rotation_to_certificate(expected_closures[hubs])
            if closed_certificate != expected_certificate:
                raise FinalAuditError(f"block {order} closure {hubs} does not replay from its strict block")
            checks_path = _hash_bound_path(
                root,
                closure_entry,
                path_field="checks_path",
                sha_field="checks_sha256",
                label=f"block {order} closure {hubs} saved checker record",
            )
            saved_checks = _read_object(checks_path, label=f"block {order} closure {hubs} saved checker record")
            if closure_entry.get("passed") is not True or saved_checks.get("passed") is not True:
                raise FinalAuditError(f"block {order} closure {hubs} lacks saved passing checker evidence")
            fresh_checks = _checker_pair(closed_path, expected_order=order)
            if not all(check["passed"] for check in fresh_checks):
                raise FinalAuditError(f"block {order} closure {hubs} failed a fresh independent checker")
            closure_audits.append(
                {"hub_indices": list(hubs), "checker_runs": fresh_checks, "passed": True}
            )
        if seen != set(expected_closures):
            raise FinalAuditError(f"block {order} closure records do not cover the 3x3 grid")
        result[order] = blocks.Block(rotation, sockets)
        r_values[order] = r
        audits.append(
            {
                "order": order,
                "certificate_path": str(certificate_path.relative_to(root)),
                "certificate_sha256": _sha256(certificate_path),
                "r": r,
                "t": t,
                "closure_audits": closure_audits,
                "passed": True,
            }
        )
    return result, r_values, audits


def _expected_profile(
    target: int, chain: tuple[int, ...], r_values: Mapping[int, int], block_t: Mapping[int, int]
) -> dict[str, object]:
    r = sum(r_values[order] - 4 for order in chain) + 4
    t_total = block_arithmetic.t_total(chain, block_t)
    if target - 2 * r + 4 < 0:
        raise FinalAuditError(f"target {target} has an impossible predicted r={r}")
    counts = {"3": r, "4": target - 2 * r + 4, "5": r - 4}
    return {"r": r, "t_total": t_total, "vertex_counts": counts, "face_counts": dict(counts)}


def _observed_profile(rotation: blocks.Rotation) -> dict[str, object]:
    degrees = [len(neighbors) for neighbors in rotation.values()]
    faces = blocks.trace_faces(rotation).faces
    return {
        "vertex_counts": {str(size): degrees.count(size) for size in (3, 4, 5)},
        "face_counts": {str(size): sum(len(face) == size for face in faces) for size in (3, 4, 5)},
    }


def _audit_targets(
    root: Path,
    manifest: Mapping[str, object],
    expected: Mapping[int, tuple[int, ...]],
    source_blocks: Mapping[int, blocks.Block],
    r_values: Mapping[int, int],
    *,
    t_budget: int,
) -> list[dict[str, object]]:
    raw_orders = manifest.get("target_orders")
    targets = manifest.get("targets")
    if raw_orders != list(expected) or not isinstance(targets, list) or len(targets) != len(expected):
        raise FinalAuditError("promotion manifest does not contain exactly the expected target orders")
    entries: dict[int, Mapping[str, object]] = {}
    for entry in targets:
        if not isinstance(entry, dict):
            raise FinalAuditError("promotion manifest has a malformed target entry")
        order = entry.get("order")
        if not isinstance(order, int) or isinstance(order, bool) or order in entries:
            raise FinalAuditError("promotion manifest has duplicate or invalid target orders")
        entries[order] = entry
    if set(entries) != set(expected):
        raise FinalAuditError("promotion target records have a missing order or an extra order")

    block_t = {order: 0 for order in source_blocks}
    audits: list[dict[str, object]] = []
    for target in expected:
        entry = entries[target]
        chain = expected[target]
        if entry.get("block_chain") != list(chain):
            raise FinalAuditError(f"target {target} block chain differs from frozen arithmetic")
        certificate_path = _hash_bound_path(
            root,
            entry,
            path_field="certificate_path",
            sha_field="certificate_sha256",
            label=f"target {target} certificate",
        )
        certificate = _read_object(certificate_path, label=f"target {target} certificate")
        try:
            rotation = blocks.rotation_from_certificate(certificate)
        except (TypeError, ValueError, blocks.BlockError) as exc:
            raise FinalAuditError(f"target {target} certificate cannot be parsed: {exc}") from exc
        if len(rotation) != target or blocks.rotation_to_certificate(rotation) != certificate:
            raise FinalAuditError(f"target {target} certificate has the wrong order or is not canonical")
        canonical_sha = _canonical_map_sha(certificate)
        if entry.get("canonical_plane_map_sha256") != canonical_sha:
            raise FinalAuditError(f"target {target} canonical plane-map SHA-256 mismatch")

        expected_profile = _expected_profile(target, chain, r_values, block_t)
        observed_profile = _observed_profile(rotation)
        if expected_profile["t_total"] > t_budget:
            raise FinalAuditError(f"target {target} exceeds the declared t budget")
        if entry.get("expected_profile") != expected_profile or entry.get("observed_profile") != observed_profile:
            raise FinalAuditError(f"target {target} profile evidence does not match independent reconstruction")
        composition = entry.get("composition")
        if not isinstance(composition, dict):
            raise FinalAuditError(f"target {target} has no composition evidence")
        if composition.get("arithmetic_chain") != list(chain):
            raise FinalAuditError(f"target {target} composition has the wrong arithmetic chain")
        if composition.get("selected_closure_hub_indices") != [0, 0] or composition.get("replay_verified") is not True:
            raise FinalAuditError(f"target {target} composition lacks the required replay gate")
        trace = composition.get("selected_trace")
        if not isinstance(trace, dict):
            raise FinalAuditError(f"target {target} composition trace is malformed")
        # The trace is a labelled permutation of the frozen arithmetic chain,
        # not merely evidence for *some* chain with the same net Section-8
        # order and r/t profile.  For example, published (21, 24) and
        # (22, 23) both close at order 42 with the same portable profile.  A
        # genuine certificate from the latter must not be relabelled as the
        # former in a frozen-chain completion package.
        raw_trace_sequence = trace.get("block_order_sequence")
        raw_trace_steps = trace.get("steps")
        if (
            not isinstance(raw_trace_sequence, list)
            or any(
                not isinstance(order, int) or isinstance(order, bool)
                for order in raw_trace_sequence
            )
            or not isinstance(raw_trace_steps, list)
            or len(raw_trace_steps) != len(raw_trace_sequence) - 1
        ):
            raise FinalAuditError(f"target {target} composition trace has an invalid shape")
        if len(raw_trace_sequence) != len(chain) or sorted(raw_trace_sequence) != sorted(chain):
            raise FinalAuditError(
                f"target {target} composition trace block-order sequence differs from frozen arithmetic"
            )
        try:
            replayed = promotion.replay_composition_trace(source_blocks, trace)
        except promotion.PromotionError as exc:
            raise FinalAuditError(
                f"target {target} composition trace cannot replay: {exc}"
            ) from exc
        replayed_open_sha = _canonical_map_sha(blocks.rotation_to_certificate(replayed.rotation))
        if composition.get("selected_open_block_canonical_sha256") != replayed_open_sha:
            raise FinalAuditError(f"target {target} selected open-map hash does not replay")
        if blocks.rotation_to_certificate(blocks.close_block(replayed)) != certificate:
            raise FinalAuditError(f"target {target} selected composition trace does not replay its certificate")

        checks_path = _hash_bound_path(
            root,
            entry,
            path_field="checks_path",
            sha_field="checks_sha256",
            label=f"target {target} saved checker record",
        )
        saved_checks = _read_object(checks_path, label=f"target {target} saved checker record")
        if entry.get("passed") is not True or saved_checks.get("passed") is not True:
            raise FinalAuditError(f"target {target} lacks saved passing checker evidence")
        fresh_checks = _checker_pair(certificate_path, expected_order=target)
        if not all(check["passed"] for check in fresh_checks):
            raise FinalAuditError(f"target {target} failed a fresh independent checker")
        audits.append(
            {
                "order": target,
                "certificate_path": str(certificate_path.relative_to(root)),
                "certificate_sha256": _sha256(certificate_path),
                "canonical_plane_map_sha256": canonical_sha,
                "expected_profile": expected_profile,
                "observed_profile": observed_profile,
                "checker_runs": fresh_checks,
                "passed": True,
            }
        )
    return audits


def _recheck_production_source_gate(
    root: Path, manifest: Mapping[str, object], source_blocks: Mapping[int, blocks.Block]
) -> dict[str, object]:
    source_gate = manifest.get("source_gate")
    if not isinstance(source_gate, dict) or source_gate.get("required") is not True or source_gate.get("passed") is not True:
        raise FinalAuditError("production manifest lacks a passing source-gate record")
    raw_path = source_gate.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        raise FinalAuditError("production source-gate record lacks its ledger path")
    ledger_path = _safe_path(root, raw_path, label="production source-gate ledger")
    expected_sha = _require_digest(source_gate.get("sha256"), label="source-gate ledger SHA-256")
    if not ledger_path.is_file() or _sha256(ledger_path) != expected_sha:
        raise FinalAuditError("production source-gate ledger is unavailable or hash-mismatched")
    loaded: dict[int, promotion.LoadedBlock] = {}
    ledger = _read_object(ledger_path, label="source-gate ledger")
    for order in (*block_arithmetic.PUBLISHED_BLOCK_ORDERS, *block_arithmetic.BOOLEAN_PRIMARY_T0_BLOCK_ORDERS):
        group = "published_blocks" if order in block_arithmetic.PUBLISHED_BLOCK_ORDERS else "blocks"
        entries = ledger.get(group)
        if not isinstance(entries, dict) or not isinstance(entries.get(str(order)), dict):
            raise FinalAuditError(f"source-gate ledger omits block {order}")
        raw_block_path = entries[str(order)].get("opened_block_path")
        if not isinstance(raw_block_path, str) or Path(raw_block_path).is_absolute():
            raise FinalAuditError(f"source-gate ledger block {order} has a nonportable opened path")
        candidate = (ledger_path.parent / raw_block_path).resolve()
        try:
            candidate.relative_to(ledger_path.parent.resolve())
        except ValueError as exc:
            raise FinalAuditError(f"source-gate ledger block {order} escapes its package") from exc
        loaded[order] = promotion._load_block(order, candidate)
        if blocks.rotation_to_certificate(loaded[order].block.rotation) != blocks.rotation_to_certificate(source_blocks[order].rotation):
            raise FinalAuditError(f"source-gate ledger block {order} differs from the promotion package")
    try:
        checked = promotion._verify_default_handoff(ledger_path, loaded)
    except promotion.PromotionError as exc:
        raise FinalAuditError(f"production source-gate replay failed: {exc}") from exc
    return checked


def audit_promotion_package(
    promotion_dir: Path | str,
    *,
    representations: Mapping[int, Sequence[int]] | None = None,
    output: Path | str | None = None,
) -> dict[str, object]:
    """Recheck a promotion package and conditionally write its completion marker."""

    root = Path(promotion_dir).resolve()
    if not root.is_dir():
        raise FinalAuditError(f"promotion directory is not a directory: {root}")
    safe_output = root / FINAL_AUDIT_NAME
    if output is None:
        output_path = safe_output
    else:
        raw_output = Path(output)
        candidate = (root / raw_output) if not raw_output.is_absolute() else raw_output
        output_path = candidate.resolve()
        if output_path != safe_output:
            raise FinalAuditError(
                "final audit output is fixed to the new package-relative final_audit.json"
            )
    if output_path.exists():
        raise FinalAuditError("final_audit.json already exists; refuse to overwrite a prior audit")
    expected, production = _normalize_representations(representations)
    result: dict[str, object] = {
        "format": FINAL_AUDIT_FORMAT,
        "disposition": "INCOMPLETE",
        "production_exact_26": production,
        "target_orders": list(expected),
        "target_certificate_count": 0,
        "block_audits": [],
        "target_audits": [],
        "manifest_complete_marker": {
            "path": COMPLETE_MARKER,
            "written": False,
        },
    }
    try:
        marker_path = root / COMPLETE_MARKER
        if marker_path.exists():
            raise FinalAuditError("MANIFEST_COMPLETE already exists; refuse to bless a stale package")
        manifest_path = root / MANIFEST_NAME
        manifest = _read_object(manifest_path, label="promotion manifest")
        result["promotion_manifest"] = {
            "path": MANIFEST_NAME,
            "sha256": _sha256(manifest_path),
        }
        if manifest.get("format") != "apg-target-promotion-manifest-v1":
            raise FinalAuditError("promotion manifest has the wrong format")
        if manifest.get("disposition") != "PROMOTED_PENDING_SEPARATE_FINAL_AUDIT":
            raise FinalAuditError("promotion manifest is not pending separate final audit")
        marker = manifest.get("manifest_complete_marker")
        if not isinstance(marker, dict) or marker.get("written") is not False:
            raise FinalAuditError("composer manifest incorrectly claims completion")
        t_budget = manifest.get("t_budget")
        if not isinstance(t_budget, int) or isinstance(t_budget, bool) or t_budget < 0 or t_budget > 4:
            raise FinalAuditError("promotion manifest has an invalid finite t budget")
        if production and t_budget != 0:
            raise FinalAuditError("Boolean-primary production promotion must retain t_budget=0")
        required_orders = {order for chain in expected.values() for order in chain}
        source_blocks, r_values, block_audits = _load_blocks(root, manifest, required_orders)
        result["block_audits"] = block_audits
        if production:
            result["source_gate_recheck"] = _recheck_production_source_gate(
                root, manifest, source_blocks
            )
        target_audits = _audit_targets(
            root,
            manifest,
            expected,
            source_blocks,
            r_values,
            t_budget=t_budget,
        )
        result["target_audits"] = target_audits
        result["target_certificate_count"] = len(target_audits)
        if production:
            if tuple(expected) != block_arithmetic.TARGET_ORDERS or len(target_audits) != 26:
                raise FinalAuditError("production final audit does not have exactly the frozen 26 targets")
            result["disposition"] = "CERTIFIED_26_TARGETS"
            result["manifest_complete_marker"] = {"path": COMPLETE_MARKER, "written": True}
            audit_sha = _write_json(output_path, result)
            marker_path.write_text(
                "APG_TARGET_PROMOTION_COMPLETE_V1\n"
                f"manifest_sha256={result['promotion_manifest']['sha256']}\n"  # type: ignore[index]
                f"final_audit_sha256={audit_sha}\n",
                encoding="utf-8",
            )
            return result
        result["disposition"] = "CERTIFIED_CONTROL_ONLY"
        result["reason"] = "bounded control audit; not the frozen 26-target completion claim"
    except FinalAuditError as exc:
        result["reason"] = str(exc)
    _write_json(output_path, result)
    if result["disposition"] == "INCOMPLETE":
        raise FinalAuditError(str(result["reason"]))
    return result


def _load_representation_file(path: Path) -> dict[int, tuple[int, ...]]:
    raw = _read_object(path, label="representation map")
    parsed: dict[int, tuple[int, ...]] = {}
    for raw_target, raw_chain in raw.items():
        try:
            target = int(raw_target)
        except (TypeError, ValueError) as exc:
            raise FinalAuditError(f"representation target {raw_target!r} is not an integer") from exc
        if not isinstance(raw_chain, list):
            raise FinalAuditError(f"representation chain for {target} is not a JSON list")
        parsed[target] = tuple(raw_chain)
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("promotion_dir", type=Path)
    parser.add_argument(
        "--representations",
        type=Path,
        help="bounded control mapping only; omitting it performs the frozen 26-target audit",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        representations = (
            _load_representation_file(args.representations)
            if args.representations is not None
            else None
        )
        result = audit_promotion_package(
            args.promotion_dir, representations=representations
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, FinalAuditError) as exc:
        print(f"INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
