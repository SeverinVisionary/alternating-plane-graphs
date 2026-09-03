#!/usr/bin/env python3
"""Fail-closed promotion of portable Section-8 blocks to APG witnesses.

The Boolean cap search writes a strict reopened block as an ordinary
``apg-plane-rotation-v1`` certificate.  That object is deliberately *not* a
closed APG certificate: it has the six degree-two socket whites required by
Section 8.  This module consumes those strict block certificates, revalidates
their interface and portable ``t=0`` condition, then composes and closes the
frozen Boolean-primary chains.

The final acceptance boundary is intentionally outside the composer: every
generated closed target is passed to both independent checkers in new Python
processes.  The composer never writes ``MANIFEST_COMPLETE``.  A separate final
audit may do that only after it has checked the full result package.

The public :func:`promote_target_witnesses` accepts a custom representation map
for small known-answer tests.  Production callers omit it, which freezes the
exact 26-target mapping in
``block_arithmetic.boolean_primary_t0_target_representations()``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import permutations
from pathlib import Path

import block_arithmetic
import blocks
import structural_audit


ROOT = Path(__file__).resolve().parent
VERIFY = ROOT / "verify.py"
VERIFY_DARTS = ROOT / "verify_darts.py"
MANIFEST_NAME = "manifest.json"
COMPLETE_MARKER = "MANIFEST_COMPLETE"
PUBLISHED_BLOCK_SOURCE_NAMES = {
    21: "A21.json",
    22: "B22.json",
    23: "C23.json",
    24: "D24.json",
}


class PromotionError(RuntimeError):
    """A source block or generated target did not pass a required gate."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguity before a source-handoff object reaches a checker."""

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(token: str) -> object:
    raise ValueError(f"non-JSON numeric constant {token!r}")


@dataclass(frozen=True)
class LoadedBlock:
    """A canonical strict block with source-integrity metadata."""

    order: int
    source_path: Path
    source_sha256: str
    block: blocks.Block
    certificate: dict[str, object]
    t0_audit: dict[str, object]
    r: int


@dataclass(frozen=True)
class _CompositionState:
    """One labelled representative and a replay trace for a canonical map class."""

    block: blocks.Block
    trace: dict[str, object]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _sha256(path)


def _canonical_file_sha256(value: object) -> str:
    """SHA-256 of this repository's deterministic pretty-JSON serializer."""

    encoded = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _certificate_key(certificate: dict[str, object]) -> bytes:
    """Return a stable ordering key for a normalized rotation certificate."""

    return json.dumps(
        certificate, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")


def _socket_summary(
    sockets: tuple[blocks.Socket, blocks.Socket],
) -> list[dict[str, object]]:
    return [
        {"boundary": list(socket.boundary), "whites": list(socket.whites)}
        for socket in sockets
    ]


def _is_plain_apg_certificate(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"format", "vertices"}
        and value.get("format") == blocks.APG_FORMAT
    )


def _portable_t0_audit(block: blocks.Block, *, order: int) -> dict[str, object]:
    """Reconstruct the nine closures and require the portable ``t=0`` gate.

    The arithmetic selector has ``t=0`` in its name for a reason: a merely
    strict finite-use block cannot be silently reused in the all-target chain.
    This independent structural reconstruction is intentionally repeated here
    even when a cloud postprocessor previously checked the source certificate.
    It does not replace the two subprocess checker gates recorded below.
    """

    try:
        audit = structural_audit.analyze_block(
            structural_audit.audit_data_from_block(block)
        )
    except (TypeError, ValueError, blocks.BlockError) as exc:
        raise PromotionError(f"block {order} structural t=0 audit failed: {exc}") from exc

    variants = audit.get("variants") if isinstance(audit, dict) else None
    observed: list[dict[str, object]] = []
    if isinstance(variants, list):
        for item in variants:
            if isinstance(item, dict):
                observed.append(
                    {
                        "hub_indices": item.get("hub_indices"),
                        "r": item.get("r"),
                        "t_vertex": item.get("t_vertex"),
                        "t_face": item.get("t_face"),
                    }
                )
    r_values = {
        item["r"]
        for item in observed
        if isinstance(item["r"], int) and not isinstance(item["r"], bool)
    }
    passed = (
        len(observed) == 9
        and len(r_values) == 1
        and all(item["t_vertex"] == 0 and item["t_face"] == 0 for item in observed)
    )
    summary: dict[str, object] = {
        "method": "structural_audit.analyze_block",
        "variant_count": audit.get("variant_count") if isinstance(audit, dict) else None,
        "all_invariants_equal": (
            audit.get("all_invariants_equal") if isinstance(audit, dict) else None
        ),
        "closures": observed,
        "r": next(iter(r_values)) if len(r_values) == 1 else None,
        "t": 0,
        "passed": passed,
    }
    if not passed:
        raise PromotionError(
            f"block {order} is not a portable t=0 block across all nine closures"
        )
    return summary


def _load_block(order: int, source_path: Path) -> LoadedBlock:
    """Read one exact-map reopened strict block in APG rotation format."""

    if not isinstance(order, int) or isinstance(order, bool) or order < 4:
        raise PromotionError(f"block order must be an integer at least 4, got {order!r}")
    source_path = source_path.resolve()
    raw = _read_json_object(source_path, label=f"block {order}")
    if not _is_plain_apg_certificate(raw):
        raise PromotionError(
            f"block {order} must be a plain {blocks.APG_FORMAT} strict-block certificate"
        )
    try:
        rotation = blocks.rotation_from_certificate(raw)
        canonical = blocks.rotation_to_certificate(rotation)
        if canonical != raw:
            raise blocks.BlockError("source rotation is not canonical JSON")
        if len(rotation) != order:
            raise blocks.BlockError(
                f"certificate order {len(rotation)} does not match keyed order {order}"
            )
        sockets = blocks.validate_block(rotation)
    except (TypeError, ValueError, blocks.BlockError) as exc:
        raise PromotionError(f"block {order} fails strict Section-8 validation: {exc}") from exc
    block = blocks.Block(rotation, sockets)
    t0_audit = _portable_t0_audit(block, order=order)
    r = t0_audit.get("r")
    if not isinstance(r, int) or isinstance(r, bool):
        raise PromotionError(f"block {order} t=0 audit did not reconstruct one degree-three count")
    return LoadedBlock(
        order=order,
        source_path=source_path,
        source_sha256=_sha256(source_path),
        block=block,
        certificate=canonical,
        t0_audit=t0_audit,
        r=r,
    )


def _normalize_representations(
    representations: Mapping[int, Sequence[int]],
) -> dict[int, tuple[int, ...]]:
    """Validate the selected deterministic target chains before composing."""

    if not isinstance(representations, Mapping) or not representations:
        raise PromotionError("representations must be a nonempty target-to-chain mapping")

    normalized: dict[int, tuple[int, ...]] = {}
    for target, chain in sorted(representations.items()):
        if not isinstance(target, int) or isinstance(target, bool) or target < 4:
            raise PromotionError(f"invalid target order {target!r}")
        if isinstance(chain, (str, bytes)) or not isinstance(chain, Iterable):
            raise PromotionError(f"target {target} chain must be an iterable of block orders")
        values = tuple(chain)
        if not values or any(
            not isinstance(order, int) or isinstance(order, bool) or order < 4
            for order in values
        ):
            raise PromotionError(f"target {target} has an invalid block chain {values!r}")
        if block_arithmetic.apg_order(values) != target:
            raise PromotionError(
                f"target {target} chain {values!r} has Section-8 order "
                f"{block_arithmetic.apg_order(values)}, not {target}"
            )
        normalized[target] = values

    return normalized


def _parse_block_mapping(
    block_certificates: Mapping[int, Path | str],
) -> dict[int, Path]:
    if not isinstance(block_certificates, Mapping):
        raise PromotionError("block certificates must be keyed by integer order")
    parsed: dict[int, Path] = {}
    for order, raw_path in block_certificates.items():
        if not isinstance(order, int) or isinstance(order, bool) or order < 4:
            raise PromotionError(f"invalid block-certificate order {order!r}")
        if order in parsed:
            raise PromotionError(f"duplicate block certificate order {order}")
        if not isinstance(raw_path, (str, Path)):
            raise PromotionError(f"block {order} path is not a filesystem path")
        parsed[order] = Path(raw_path)
    return parsed


def _read_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise PromotionError(f"cannot read {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PromotionError(f"{label} at {path} is not a JSON object")
    return value


def _require_sha256(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise PromotionError(f"{label} is not a lowercase SHA-256 digest")
    return value


def _resolve_handoff_artifact(
    ledger_parent: Path, value: object, *, label: str
) -> Path:
    """Resolve a portable ledger-relative artifact without allowing escape."""

    if not isinstance(value, str) or not value:
        raise PromotionError(f"{label} must be a nonempty ledger-relative path")
    raw_path = Path(value)
    if raw_path.is_absolute():
        raise PromotionError(f"{label} must be relative to the handoff ledger")
    resolved_parent = ledger_parent.resolve()
    resolved = (resolved_parent / raw_path).resolve()
    try:
        resolved.relative_to(resolved_parent)
    except ValueError as exc:
        raise PromotionError(f"{label} escapes the handoff ledger directory") from exc
    return resolved


def _raw_cap_fans(value: object) -> tuple[blocks.ClosureFan, blocks.ClosureFan]:
    if not isinstance(value, list) or len(value) != 2:
        raise PromotionError("raw Boolean record must retain exactly two cap fans")
    fans: list[blocks.ClosureFan] = []
    for item in value:
        if not isinstance(item, dict):
            raise PromotionError("raw cap-fan entry is not an object")
        center = item.get("center")
        leaves = item.get("leaves")
        if (
            not isinstance(center, int)
            or isinstance(center, bool)
            or not isinstance(leaves, list)
            or len(leaves) != 2
            or any(not isinstance(leaf, int) or isinstance(leaf, bool) for leaf in leaves)
        ):
            raise PromotionError("raw cap-fan entry must name one center and two leaves")
        fans.append(blocks.ClosureFan(center, (leaves[0], leaves[1])))
    if len({vertex for fan in fans for vertex in fan.whites}) != 6:
        raise PromotionError("raw cap fans must name six distinct vertices")
    return fans[0], fans[1]


def _fresh_raw_closed_candidate_checks(
    certificate: object, *, expected_order: int
) -> dict[str, object]:
    """Run both standalone checkers on the retained raw closed certificate.

    The handoff ledger may contain historical checker logs, but those are not
    an acceptance boundary for the composer.  In particular,
    ``rotation_from_certificate`` deliberately normalizes cyclic rotations;
    a malformed raw record can therefore be reopenable through ``blocks``
    while its *actual* source certificate is not accepted by either APG
    verifier.  Serialize the retained object verbatim (apart from deterministic
    JSON whitespace) in a new temporary file and rerun both independent
    checkers before trusting the raw-to-opened provenance chain.
    """

    with tempfile.TemporaryDirectory(prefix="apg-promotion-raw-check-") as directory:
        path = Path(directory) / "raw_closed_candidate.json"
        certificate_sha256 = _write_json(path, certificate)
        checker_runs = _checker_pair(path, expected_order=expected_order)
    return {
        "serialized_certificate_sha256": certificate_sha256,
        "expected_order": expected_order,
        "checker_runs": checker_runs,
        "passed": all(run["passed"] for run in checker_runs),
    }


def _verify_handoff_entry(
    order: int,
    source: LoadedBlock,
    entry: object,
    *,
    ledger_parent: Path,
    expected_r: int = 12,
) -> dict[str, object]:
    """Bind an imported reopened block to raw Boolean and postprocess evidence."""

    if not isinstance(entry, dict):
        raise PromotionError(f"handoff ledger block {order} is not an object")
    required_claims: dict[str, object] = {
        "order": order,
        "r": expected_r,
        "postprocess_disposition": "CERTIFIED",
        "cap_opening_passed": True,
        "block_validation_passed": True,
        "block_t_gate_passed": True,
        "r_gate_passed": True,
        "closure_count": 9,
        "closures_passed": True,
    }
    for field, expected in required_claims.items():
        if entry.get(field) != expected:
            raise PromotionError(
                f"handoff ledger block {order} has {field}={entry.get(field)!r}, expected {expected!r}"
            )

    opened_path = _resolve_handoff_artifact(
        ledger_parent, entry.get("opened_block_path"), label=f"handoff block {order} opened_block_path"
    )
    postprocess_path = _resolve_handoff_artifact(
        ledger_parent, entry.get("postprocess_path"), label=f"handoff block {order} postprocess_path"
    )
    raw_path = _resolve_handoff_artifact(
        ledger_parent, entry.get("raw_record_path"), label=f"handoff block {order} raw_record_path"
    )
    opened_sha = _require_sha256(
        entry.get("opened_block_sha256"), label=f"handoff block {order} opened_block_sha256"
    )
    postprocess_sha = _require_sha256(
        entry.get("postprocess_sha256"), label=f"handoff block {order} postprocess_sha256"
    )
    raw_sha = _require_sha256(
        entry.get("raw_record_sha256"), label=f"handoff block {order} raw_record_sha256"
    )
    if opened_path != source.source_path or opened_sha != source.source_sha256:
        raise PromotionError(
            f"handoff ledger block {order} does not bind the supplied opened-block path and SHA-256"
        )
    if _sha256(postprocess_path) != postprocess_sha:
        raise PromotionError(f"handoff ledger block {order} postprocess SHA-256 mismatch")
    if _sha256(raw_path) != raw_sha:
        raise PromotionError(f"handoff ledger block {order} raw-record SHA-256 mismatch")

    postprocess = _read_json_object(postprocess_path, label="postprocess record")
    if postprocess.get("format") != "apg-exact-map-postprocess-v1":
        raise PromotionError(f"handoff ledger block {order} has the wrong postprocess format")
    if postprocess.get("disposition") != "CERTIFIED" or postprocess.get("lane") != "closed":
        raise PromotionError(f"handoff ledger block {order} postprocess record is not CERTIFIED closed")
    if (
        postprocess.get("r") != expected_r
        or postprocess.get("expected_order") != order
        or postprocess.get("expected_block_t") != 0
        or postprocess.get("solver_disposition") != "CANDIDATE"
    ):
        raise PromotionError(f"handoff ledger block {order} postprocess profile provenance mismatches")
    for gate_name in ("closed_r_gate", "r_gate", "block_t_gate"):
        gate = postprocess.get(gate_name)
        if not isinstance(gate, dict) or gate.get("passed") is not True:
            raise PromotionError(f"handoff ledger block {order} postprocess {gate_name} did not pass")
    block_t_gate = postprocess["block_t_gate"]
    if block_t_gate.get("requested") != 0:
        raise PromotionError(f"handoff ledger block {order} postprocess did not require t=0")
    cap_opening = postprocess.get("cap_opening")
    block_validation = postprocess.get("block_validation")
    if not isinstance(cap_opening, dict) or cap_opening.get("passed") is not True:
        raise PromotionError(f"handoff ledger block {order} postprocess cap opening did not pass")
    if not isinstance(block_validation, dict) or block_validation.get("passed") is not True:
        raise PromotionError(f"handoff ledger block {order} postprocess block validation did not pass")
    structural = postprocess.get("structural_audit")
    if not isinstance(structural, dict) or structural.get("status") != "COMPLETED":
        raise PromotionError(f"handoff ledger block {order} postprocess structural audit did not complete")
    closures = postprocess.get("closures")
    if (
        postprocess.get("closure_count") != 9
        or not isinstance(closures, list)
        or len(closures) != 9
        or any(not isinstance(item, dict) or item.get("passed") is not True for item in closures)
    ):
        raise PromotionError(f"handoff ledger block {order} postprocess lacks nine passing closures")
    closure_grid = {
        tuple(item.get("hub_indices", ()))
        for item in closures
        if isinstance(item, dict)
        and isinstance(item.get("hub_indices"), list)
        and len(item["hub_indices"]) == 2
    }
    if closure_grid != {(first, second) for first in range(3) for second in range(3)}:
        raise PromotionError(f"handoff ledger block {order} postprocess closure grid is not complete")
    opened = postprocess.get("opened_block")
    if (
        not isinstance(opened, dict)
        or opened.get("sha256") != source.source_sha256
        or opened.get("order") != order
        or opened.get("format") != blocks.APG_FORMAT
    ):
        raise PromotionError(
            f"handoff ledger block {order} postprocess opened-block metadata does not bind supplied bytes"
        )
    if postprocess.get("source_record_sha256") != raw_sha:
        raise PromotionError(f"handoff ledger block {order} raw-record SHA is not bound by postprocess")

    raw = _read_json_object(raw_path, label="raw Boolean record")
    if (
        raw.get("format") != "apg-exact-map-bool-sat-v1"
        or raw.get("disposition") != "CANDIDATE"
        or raw.get("lane") != "closed"
        or raw.get("order") != order
        or raw.get("r") != expected_r
        or raw.get("canonical") is not True
        or raw.get("require_cap_fans") is not True
        or raw.get("require_t0") is not True
    ):
        raise PromotionError(f"handoff ledger block {order} raw Boolean record fails source-gate fields")
    raw_candidate_checks = _fresh_raw_closed_candidate_checks(
        raw.get("certificate"), expected_order=order
    )
    if raw_candidate_checks["passed"] is not True:
        raise PromotionError(
            f"handoff ledger block {order} raw closed candidate failed fresh independent checkers"
        )
    try:
        raw_rotation = blocks.rotation_from_certificate(raw.get("certificate"))
        raw_fans = _raw_cap_fans(raw.get("cap_fans"))
        reopened = blocks.open_cap_fans(
            raw_rotation,
            raw_fans,
        )
    except (TypeError, ValueError, blocks.BlockError) as exc:
        raise PromotionError(
            f"handoff ledger block {order} raw candidate does not reopen through its retained cap fans: {exc}"
        ) from exc
    normalized_raw = blocks.rotation_to_certificate(raw_rotation)
    candidate = postprocess.get("candidate")
    if (
        not isinstance(candidate, dict)
        or candidate.get("sha256") != _canonical_file_sha256(normalized_raw)
    ):
        raise PromotionError(
            f"handoff ledger block {order} postprocess candidate does not bind raw closed rotation"
        )
    expected_fans = [
        {"center": fan.hub, "leaves": list(fan.leaves)} for fan in raw_fans
    ]
    if cap_opening.get("fans") != expected_fans:
        raise PromotionError(
            f"handoff ledger block {order} postprocess cap-fan provenance does not bind raw record"
        )
    if blocks.rotation_to_certificate(reopened.rotation) != source.certificate:
        raise PromotionError(
            f"handoff ledger block {order} raw cap opening does not equal supplied opened-block bytes"
        )
    return {
        "order": order,
        "r": expected_r,
        "opened_block_path": str(opened_path.relative_to(ledger_parent.resolve())),
        "opened_block_sha256": source.source_sha256,
        "postprocess_path": str(postprocess_path.relative_to(ledger_parent.resolve())),
        "postprocess_sha256": postprocess_sha,
        "raw_record_path": str(raw_path.relative_to(ledger_parent.resolve())),
        "raw_record_sha256": raw_sha,
        "raw_closed_candidate_checks": raw_candidate_checks,
        "passed": True,
    }


def _verify_published_handoff_entry(
    order: int,
    source: LoadedBlock,
    entry: object,
    *,
    ledger_parent: Path,
) -> dict[str, object]:
    """Bind a published A--D open rotation to its portable ledger artifact."""

    if not isinstance(entry, dict):
        raise PromotionError(f"handoff ledger published block {order} is not an object")
    if entry.get("order") != order:
        raise PromotionError(f"handoff ledger published block {order} has the wrong order")
    expected_name = PUBLISHED_BLOCK_SOURCE_NAMES.get(order)
    if expected_name is None:  # pragma: no cover - caller freezes A--D orders
        raise PromotionError(f"published block order {order} has no frozen source name")
    expected_repo_path = f"results/blocks/{expected_name}"
    source_repo_path = entry.get("source_repo_path")
    if source_repo_path != expected_repo_path:
        raise PromotionError(
            f"handoff ledger published block {order} source_repo_path is not {expected_repo_path}"
        )
    source_sha = _require_sha256(
        entry.get("source_sha256"), label=f"handoff published block {order} source_sha256"
    )
    opened_path = _resolve_handoff_artifact(
        ledger_parent,
        entry.get("opened_block_path"),
        label=f"handoff published block {order} opened_block_path",
    )
    opened_sha = _require_sha256(
        entry.get("opened_block_sha256"),
        label=f"handoff published block {order} opened_block_sha256",
    )
    strict = entry.get("strict_block_validation")
    if not isinstance(strict, dict) or strict.get("passed") is not True:
        raise PromotionError(
            f"handoff ledger published block {order} does not claim strict validation"
        )
    if opened_path != source.source_path or opened_sha != source.source_sha256:
        raise PromotionError(
            f"handoff ledger published block {order} does not bind supplied opened-block path and SHA-256"
        )
    source_path = (ROOT / expected_repo_path).resolve()
    if not source_path.is_file():
        raise PromotionError(f"frozen published source is missing: {source_path}")
    if _sha256(source_path) != source_sha:
        raise PromotionError(
            f"handoff ledger published block {order} source SHA-256 does not match frozen source"
        )
    historical = _read_json_object(source_path, label=f"published source block {order}")
    rows = historical.get("vertices")
    try:
        source_rotation = blocks.rotation_from_certificate(
            {"format": blocks.APG_FORMAT, "vertices": rows}
        )
        source_sockets = blocks.validate_block(source_rotation)
    except (TypeError, ValueError, blocks.BlockError) as exc:
        raise PromotionError(
            f"frozen published block {order} fails strict validation: {exc}"
        ) from exc
    if blocks.rotation_to_certificate(source_rotation) != source.certificate:
        raise PromotionError(
            f"handoff ledger published block {order} opened bytes do not equal frozen source rotation"
        )
    if strict.get("sockets") != _socket_summary(source_sockets):
        raise PromotionError(
            f"handoff ledger published block {order} strict-socket record does not match frozen source"
        )
    return {
        "order": order,
        "source_repo_path": source_repo_path,
        "source_sha256": source_sha,
        "opened_block_path": str(opened_path.relative_to(ledger_parent.resolve())),
        "opened_block_sha256": source.source_sha256,
        "strict_block_validation": strict,
        "passed": True,
    }


def _verify_default_handoff(
    ledger_path: Path | str,
    loaded: Mapping[int, LoadedBlock],
) -> dict[str, object]:
    ledger_path = Path(ledger_path).resolve()
    ledger = _read_json_object(ledger_path, label="handoff ledger")
    if ledger.get("format") != "apg-boolean-block-handoff-v1":
        raise PromotionError("handoff ledger has the wrong format")
    if ledger.get("disposition") != "ELIGIBLE" or ledger.get("block_input_eligible") is not True:
        raise PromotionError("handoff ledger is not ELIGIBLE for production target promotion")
    entries = ledger.get("blocks")
    if not isinstance(entries, dict):
        raise PromotionError("handoff ledger blocks must be an object keyed by order")
    published_entries = ledger.get("published_blocks")
    if not isinstance(published_entries, dict):
        raise PromotionError("handoff ledger published_blocks must be an object keyed by order")
    verified: dict[str, object] = {}
    for order in block_arithmetic.BOOLEAN_PRIMARY_T0_BLOCK_ORDERS:
        entry = entries.get(str(order))
        if entry is None:
            raise PromotionError(f"handoff ledger omits required Boolean block {order}")
        verified[str(order)] = _verify_handoff_entry(
            order, loaded[order], entry, ledger_parent=ledger_path.parent, expected_r=12
        )
    verified_published: dict[str, object] = {}
    for order in block_arithmetic.PUBLISHED_BLOCK_ORDERS:
        entry = published_entries.get(str(order))
        if entry is None:
            raise PromotionError(f"handoff ledger omits required published block {order}")
        verified_published[str(order)] = _verify_published_handoff_entry(
            order, loaded[order], entry, ledger_parent=ledger_path.parent
        )
    return {
        "required": True,
        "path": str(ledger_path),
        "sha256": _sha256(ledger_path),
        "format": ledger["format"],
        "blocks": verified,
        "published_blocks": verified_published,
        "passed": True,
    }


def _materialize_source_handoff(
    output_dir: Path, source_gate: Mapping[str, object]
) -> dict[str, object]:
    """Copy a verified default ledger and every referenced artifact into output.

    A target package must not depend on the original cloud checkout remaining
    mounted.  The ledger's artifact paths are deliberately relative to its
    parent, so copying the ledger as ``source_handoff/handoff-ledger.json`` and
    retaining those relative paths makes the gate independently replayable
    from the promoted package.  This routine does *not* copy descriptive
    ``source_repo_path`` entries for A--D: those are frozen repository paths,
    not ledger-relative artifacts.
    """

    original_ledger = source_gate.get("path")
    if not isinstance(original_ledger, str):
        raise PromotionError("verified default source gate lacks its ledger path")
    ledger_path = Path(original_ledger).resolve()
    expected_ledger_sha = _require_sha256(
        source_gate.get("sha256"), label="verified default source-gate ledger SHA-256"
    )
    if _sha256(ledger_path) != expected_ledger_sha:
        raise PromotionError("verified default source-gate ledger changed before package materialization")

    handoff_dir = output_dir / "source_handoff"
    handoff_dir.mkdir(parents=True, exist_ok=False)
    copied_ledger = handoff_dir / "handoff-ledger.json"
    shutil.copyfile(ledger_path, copied_ledger)
    if _sha256(copied_ledger) != expected_ledger_sha:
        raise PromotionError("copied source-handoff ledger SHA-256 mismatch")

    artifact_specs: list[tuple[str, str, str]] = []
    raw_blocks = source_gate.get("blocks")
    if not isinstance(raw_blocks, dict):
        raise PromotionError("verified default source gate lacks Boolean block records")
    for order, record in sorted(raw_blocks.items(), key=lambda item: int(item[0])):
        if not isinstance(record, dict):
            raise PromotionError(f"verified source-gate Boolean block {order} is malformed")
        for path_key, sha_key in (
            ("raw_record_path", "raw_record_sha256"),
            ("postprocess_path", "postprocess_sha256"),
            ("opened_block_path", "opened_block_sha256"),
        ):
            path_value = record.get(path_key)
            sha_value = record.get(sha_key)
            if not isinstance(path_value, str):
                raise PromotionError(
                    f"verified source-gate Boolean block {order} lacks {path_key}"
                )
            artifact_specs.append((str(order), path_key, path_value))
            _require_sha256(
                sha_value,
                label=f"verified source-gate Boolean block {order} {sha_key}",
            )

    published_blocks = source_gate.get("published_blocks")
    if not isinstance(published_blocks, dict):
        raise PromotionError("verified default source gate lacks published block records")
    for order, record in sorted(published_blocks.items(), key=lambda item: int(item[0])):
        if not isinstance(record, dict):
            raise PromotionError(f"verified source-gate published block {order} is malformed")
        path_value = record.get("opened_block_path")
        if not isinstance(path_value, str):
            raise PromotionError(
                f"verified source-gate published block {order} lacks opened_block_path"
            )
        _require_sha256(
            record.get("opened_block_sha256"),
            label=f"verified source-gate published block {order} opened_block_sha256",
        )
        artifact_specs.append((str(order), "opened_block_path", path_value))

    # Keep an exact copy once even if a malicious ledger reused one path.  The
    # source verifier has already asserted each associated digest; recheck it
    # here before and after copying so a replacement between the two phases is
    # a closed gate, not an untracked provenance drift.
    copied_paths: set[str] = set()
    ledger_parent = ledger_path.parent.resolve()
    for order, path_key, relative_path in artifact_specs:
        source_path = _resolve_handoff_artifact(
            ledger_parent,
            relative_path,
            label=f"verified source-gate block {order} {path_key}",
        )
        destination = (handoff_dir / relative_path).resolve()
        try:
            destination.relative_to(handoff_dir.resolve())
        except ValueError as exc:
            raise PromotionError(
                f"verified source-gate block {order} {path_key} escapes package handoff directory"
            ) from exc
        if relative_path in copied_paths:
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination)
        copied_paths.add(relative_path)

    # The copied ledger remains byte-identical, so paths inside it now resolve
    # beneath ``source_handoff``.  Hash every copied artifact against the
    # source-gate digest rather than trusting the successful copy syscall.
    for record in raw_blocks.values():
        if not isinstance(record, dict):  # defensive under optimized Python too
            raise PromotionError("verified source-gate Boolean block changed shape")
        for path_key, sha_key in (
            ("raw_record_path", "raw_record_sha256"),
            ("postprocess_path", "postprocess_sha256"),
            ("opened_block_path", "opened_block_sha256"),
        ):
            relative_path = record.get(path_key)
            expected_sha = record.get(sha_key)
            if not isinstance(relative_path, str):
                raise PromotionError(f"verified source-gate Boolean block lacks {path_key}")
            expected_sha = _require_sha256(
                expected_sha,
                label=f"verified source-gate Boolean block {sha_key}",
            )
            copied = _resolve_handoff_artifact(
                handoff_dir,
                relative_path,
                label=f"copied source-handoff {path_key}",
            )
            if _sha256(copied) != expected_sha:
                raise PromotionError(
                    f"copied source-handoff {path_key} SHA-256 mismatch"
                )
    for record in published_blocks.values():
        if not isinstance(record, dict):  # defensive under optimized Python too
            raise PromotionError("verified source-gate published block changed shape")
        relative_path = record.get("opened_block_path")
        if not isinstance(relative_path, str):
            raise PromotionError("verified source-gate published block lacks opened_block_path")
        expected_sha = _require_sha256(
            record.get("opened_block_sha256"),
            label="verified source-gate published block opened_block_sha256",
        )
        copied = _resolve_handoff_artifact(
            handoff_dir,
            relative_path,
            label="copied published opened_block_path",
        )
        if _sha256(copied) != expected_sha:
            raise PromotionError("copied published opened-block SHA-256 mismatch")

    # Keep the immutable origin only as descriptive provenance.  Final audit
    # consumes the package-relative path and digest below.
    materialized = dict(source_gate)
    materialized["source_ledger_path"] = str(ledger_path)
    materialized["source_ledger_sha256"] = expected_ledger_sha
    materialized["path"] = str(copied_ledger.relative_to(output_dir))
    materialized["sha256"] = _sha256(copied_ledger)
    materialized["artifact_copy_count"] = len(copied_paths)
    materialized["materialized"] = True
    return materialized


def _prepare_output_directory(output_dir: Path) -> None:
    """Reject stale output rather than mixing old and new witness evidence."""

    if output_dir.exists():
        if not output_dir.is_dir():
            raise PromotionError(f"output path is not a directory: {output_dir}")
        if any(output_dir.iterdir()):
            raise PromotionError(
                f"output directory must be empty to prevent stale artifacts: {output_dir}"
            )
    else:
        output_dir.mkdir(parents=True, exist_ok=False)


def _run_checker(
    checker: Path, certificate: Path, *, expected_order: int
) -> dict[str, object]:
    """Invoke exactly one independent checker in a fresh subprocess."""

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
        # Treat a missing/unlaunchable verifier exactly like a negative check,
        # so the caller records an INCOMPLETE manifest rather than falling
        # through to an accidental success without independent evidence.
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


def _unique_permutations(chain: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(set(permutations(chain))))


def _compose_chain(
    blocks_by_order: Mapping[int, LoadedBlock], chain: tuple[int, ...]
) -> tuple[blocks.Block, blocks.Rotation, dict[str, object]]:
    """Run deterministic DFS over all finite gluing choices until a witness.

    The branch order is complete—unique source-order permutations, both
    initial orientations, then every reflection/socket/shift variant returned
    by :func:`blocks.compose_blocks_all_variants`—but it stops at the first
    fully closable positive branch.  This avoids materialising up to
    ``48**3`` labelled intermediates for a four-block target.  If every branch
    fails, the result is only an incomplete composition attempt, never a
    nonexistence claim.
    """

    permutations_to_try = _unique_permutations(chain)
    telemetry = {
        "order_permutation_count": len(permutations_to_try),
        "order_permutations_started": 0,
        "open_states_visited": 0,
        "two_block_variant_sets_enumerated": 0,
        "two_block_variants_visited": 0,
    }

    def search(
        state: _CompositionState,
        order_sequence: tuple[int, ...],
        next_index: int,
    ) -> tuple[_CompositionState, blocks.Rotation] | None:
        telemetry["open_states_visited"] = int(telemetry["open_states_visited"]) + 1
        if next_index == len(order_sequence):
            try:
                return state, blocks.close_block(state.block)
            except blocks.BlockError:
                return None
        attach_order = order_sequence[next_index]
        try:
            variants = blocks.compose_blocks_all_variants(
                state.block, blocks_by_order[attach_order].block
            )
        except blocks.BlockError:
            return None
        telemetry["two_block_variant_sets_enumerated"] = (
            int(telemetry["two_block_variant_sets_enumerated"]) + 1
        )
        for variant in variants:
            telemetry["two_block_variants_visited"] = (
                int(telemetry["two_block_variants_visited"]) + 1
            )
            steps = list(state.trace["steps"])
            steps.append(
                {
                    "attach_order": attach_order,
                    "inner_reflected": variant.inner_reflected,
                    "outer_reflected": variant.outer_reflected,
                    "inner_socket": variant.inner_socket,
                    "outer_socket": variant.outer_socket,
                    "shift": variant.shift,
                }
            )
            result = search(
                _CompositionState(
                    block=variant.block,
                    trace={
                        "block_order_sequence": list(order_sequence),
                        "initial_reflected": state.trace["initial_reflected"],
                        "steps": steps,
                    },
                ),
                order_sequence,
                next_index + 1,
            )
            if result is not None:
                return result
        return None

    for order_sequence in permutations_to_try:
        telemetry["order_permutations_started"] = int(telemetry["order_permutations_started"]) + 1
        for initial_reflected in (False, True):
            source = blocks_by_order[order_sequence[0]].block
            initial = blocks.mirror_block(source) if initial_reflected else source
            result = search(
                _CompositionState(
                    block=initial,
                    trace={
                        "block_order_sequence": list(order_sequence),
                        "initial_reflected": initial_reflected,
                        "steps": [],
                    },
                ),
                order_sequence,
                1,
            )
            if result is not None:
                selected_state, closed = result
                return selected_state.block, closed, {
                    "arithmetic_chain": list(chain),
                    "search": telemetry,
                    "selected_trace": selected_state.trace,
                    "selected_closure_hub_indices": [0, 0],
                }
    raise PromotionError(f"no closable composition across all variants for arithmetic chain {chain!r}")


def replay_composition_trace(
    source_blocks: Mapping[int, blocks.Block], trace: Mapping[str, object]
) -> blocks.Block:
    """Replay one selected DFS trace using only the public block operations.

    This turns the manifest's selected trace into a certificate gate rather
    than a prose description.  A later reflection applies to the *entire*
    accumulated prefix, exactly as recorded by ``CompositionVariant``.
    """

    raw_sequence = trace.get("block_order_sequence")
    raw_steps = trace.get("steps")
    initial_reflected = trace.get("initial_reflected")
    if (
        not isinstance(raw_sequence, list)
        or not raw_sequence
        or any(not isinstance(order, int) or isinstance(order, bool) for order in raw_sequence)
        or not isinstance(raw_steps, list)
        or len(raw_steps) != len(raw_sequence) - 1
        or not isinstance(initial_reflected, bool)
    ):
        raise PromotionError("composition replay trace has an invalid top-level shape")
    try:
        current = source_blocks[raw_sequence[0]]
    except KeyError as exc:
        raise PromotionError(f"composition replay is missing source block {raw_sequence[0]}") from exc
    if initial_reflected:
        current = blocks.mirror_block(current)

    for expected_order, raw_step in zip(raw_sequence[1:], raw_steps):
        if not isinstance(raw_step, dict):
            raise PromotionError("composition replay step is not an object")
        fields = (
            "attach_order",
            "inner_reflected",
            "outer_reflected",
            "inner_socket",
            "outer_socket",
            "shift",
        )
        if set(raw_step) != set(fields) or raw_step["attach_order"] != expected_order:
            raise PromotionError("composition replay step does not match its order sequence")
        if (
            not isinstance(raw_step["inner_reflected"], bool)
            or not isinstance(raw_step["outer_reflected"], bool)
            or raw_step["inner_socket"] not in {0, 1}
            or raw_step["outer_socket"] not in {0, 1}
            or raw_step["shift"] not in {0, 1, 2}
        ):
            raise PromotionError("composition replay step has invalid alignment fields")
        try:
            outer = source_blocks[expected_order]
        except KeyError as exc:
            raise PromotionError(f"composition replay is missing source block {expected_order}") from exc
        inner = blocks.mirror_block(current) if raw_step["inner_reflected"] else current
        if raw_step["outer_reflected"]:
            outer = blocks.mirror_block(outer)
        try:
            alignments = blocks.compose_blocks_alignments(
                inner,
                outer,
                inner_socket=raw_step["inner_socket"],
                outer_socket=raw_step["outer_socket"],
            )
        except blocks.BlockError as exc:
            raise PromotionError(f"composition replay cannot compose one recorded step: {exc}") from exc
        matching = [block for shift, block in alignments if shift == raw_step["shift"]]
        if len(matching) != 1:
            raise PromotionError("composition replay did not recover its recorded cyclic shift")
        current = matching[0]
    return current


def _target_profile(
    target: int,
    chain: tuple[int, ...],
    loaded: Mapping[int, LoadedBlock],
    block_t: Mapping[int, int],
) -> dict[str, object]:
    """Derive the Section-8 target histogram and additive t budget exactly."""

    r = sum(loaded[order].r - 4 for order in chain) + 4
    t_total = block_arithmetic.t_total(chain, block_t)
    if r < 4 or target - 2 * r + 4 < 0:
        raise PromotionError(
            f"target {target} chain {chain!r} has an impossible predicted r={r}"
        )
    # JSON object keys are strings.  Keep the in-memory manifest in that same
    # canonical form so its returned value exactly matches its durable file.
    counts = {"3": r, "4": target - 2 * r + 4, "5": r - 4}
    return {
        "r": r,
        "t_total": t_total,
        "vertex_counts": counts,
        "face_counts": dict(counts),
    }


def _observed_profile(rotation: blocks.Rotation) -> dict[str, object]:
    degrees = [len(neighbors) for neighbors in rotation.values()]
    faces = blocks.trace_faces(rotation).faces
    return {
        "vertex_counts": {str(size): degrees.count(size) for size in (3, 4, 5)},
        "face_counts": {
            str(size): sum(len(face) == size for face in faces) for size in (3, 4, 5)
        },
    }


def _checker_versions() -> dict[str, dict[str, str]]:
    return {
        checker.name: {"path": str(checker.resolve()), "sha256": _sha256(checker)}
        for checker in (VERIFY, VERIFY_DARTS)
    }


def _write_incomplete_manifest(
    output_dir: Path, manifest: dict[str, object], reason: str
) -> None:
    manifest["disposition"] = "INCOMPLETE"
    manifest["reason"] = reason
    manifest["manifest_complete_marker"] = {
        "path": COMPLETE_MARKER,
        "written": False,
        "reason": "a promotion gate failed",
    }
    _write_json(output_dir / MANIFEST_NAME, manifest)


def promote_target_witnesses(
    block_certificates: Mapping[int, Path | str],
    output_dir: Path | str,
    *,
    representations: Mapping[int, Sequence[int]] | None = None,
    handoff_audit: Path | str | None = None,
) -> dict[str, object]:
    """Compose strict portable blocks into independently checked APG targets.

    ``block_certificates`` maps a block order to an exact-map-style reopened
    strict APG rotation certificate.  The default representation selector is
    the frozen Boolean-primary ``(28,29,31)`` all-target arithmetic map and
    requires a verified ``apg-boolean-block-handoff-v1`` ledger.  Pass a
    custom mapping only for a bounded control; custom controls may use bare
    published block paths and never claim the production source gate.

    On a post-output failure, ``manifest.json`` records ``INCOMPLETE`` and all
    checker evidence generated up to the gate.  The function raises
    :class:`PromotionError` and never writes ``MANIFEST_COMPLETE``.
    """

    default_mode = representations is None
    supplied = _parse_block_mapping(block_certificates)
    if default_mode:
        required_orders = tuple(
            sorted(
                (*block_arithmetic.PUBLISHED_BLOCK_ORDERS, *block_arithmetic.BOOLEAN_PRIMARY_T0_BLOCK_ORDERS)
            )
        )
    else:
        selected = _normalize_representations(representations)
        if set(block_arithmetic.TARGET_ORDERS).issubset(selected):
            raise PromotionError(
                "a caller-supplied map covering all 26 frozen targets must use default production mode with --handoff-audit"
            )
        required_orders = tuple(
            sorted({order for chain in selected.values() for order in chain})
        )
    missing = tuple(order for order in required_orders if order not in supplied)
    if missing:
        joined = ", ".join(map(str, missing))
        raise PromotionError(f"missing required strict-block certificate order(s): {joined}")

    # Complete all source validation before creating the result directory: a
    # missing/malformed block must not look like a partial target package.
    loaded = {order: _load_block(order, supplied[order]) for order in required_orders}
    block_t = {
        order: int(loaded[order].t0_audit["t"])
        for order in required_orders
    }
    if default_mode:
        if handoff_audit is None:
            raise PromotionError(
                "default 26-target promotion requires a source-gated --handoff-audit ledger"
            )
        # Use the imported audit result, not a conditional arithmetic label,
        # to construct the actual t=0 map.  The frozen helper is a regression
        # comparison only; if either diverges, no target package is emitted.
        concrete = block_arithmetic.target_representations_with_t_budget(
            block_t, max_t=0
        )
        frozen = block_arithmetic.boolean_primary_t0_target_representations()
        if concrete != frozen:
            raise PromotionError(
                "concrete imported t=0 block map differs from the frozen Boolean-primary selector"
            )
        selected = _normalize_representations(concrete)
        if tuple(selected) != block_arithmetic.TARGET_ORDERS:
            raise PromotionError("concrete t=0 selector does not cover exactly the 26 frozen targets")
        source_gate = _verify_default_handoff(handoff_audit, loaded)
    else:
        if handoff_audit is not None:
            raise PromotionError(
                "--handoff-audit is reserved for the default 26-target production promotion"
            )
        source_gate = {
            "required": False,
            "passed": False,
            "reason": "bounded caller-supplied representation control",
        }
    output = Path(output_dir).resolve()
    _prepare_output_directory(output)
    if default_mode:
        # A production result package must carry its exact source handoff,
        # rather than point a final audit at an ephemeral cloud checkout.
        source_gate = _materialize_source_handoff(output, source_gate)
    manifest: dict[str, object] = {
        "format": "apg-target-promotion-manifest-v1",
        "disposition": "INCOMPLETE",
        "selector": (
            "block_arithmetic.boolean_primary_t0_target_representations"
            if representations is None
            else "caller-supplied deterministic representation mapping"
        ),
        "target_orders": list(selected),
        "block_t": {str(order): block_t[order] for order in required_orders},
        "t_budget": 0,
        "source_gate": source_gate,
        "replay": {
            "composer_path": str(Path(__file__).resolve()),
            "composer_sha256": _sha256(Path(__file__).resolve()),
            "checker_versions": _checker_versions(),
        },
        "blocks": {},
        "targets": [],
        "manifest_complete_marker": {
            "path": COMPLETE_MARKER,
            "written": False,
            "reason": "this composer deliberately leaves final completion to a separate audit",
        },
    }

    try:
        block_entries: dict[str, object] = {}
        manifest["blocks"] = block_entries
        for order in required_orders:
            source = loaded[order]
            canonical_path = output / "blocks" / f"strict_block_{order}.json"
            canonical_sha = _write_json(canonical_path, source.certificate)
            closure_entries: list[dict[str, object]] = []
            block_entry: dict[str, object] = {
                "source_path": str(source.source_path),
                "source_sha256": source.source_sha256,
                "canonical_certificate_path": str(canonical_path.relative_to(output)),
                "canonical_certificate_sha256": canonical_sha,
                "strict_block_validation": {
                    "passed": True,
                    "sockets": _socket_summary(source.block.sockets),
                },
                "portable_t0_audit": source.t0_audit,
                "r": source.r,
                "t": block_t[order],
                "closure_checks": closure_entries,
            }
            # Retain a failure's exact source and checker artifacts in the
            # incomplete manifest; only the final success disposition waits.
            block_entries[str(order)] = block_entry
            try:
                closures = blocks.close_block_variants(source.block)
            except blocks.BlockError as exc:
                raise PromotionError(
                    f"block {order} cannot enumerate all cap-hub closures: {exc}"
                ) from exc
            for hub_indices, closed in closures:
                closure_path = (
                    output
                    / "blocks"
                    / "closures"
                    / f"block_{order}_closure_{hub_indices[0]}_{hub_indices[1]}.json"
                )
                closure_sha = _write_json(
                    closure_path, blocks.rotation_to_certificate(closed)
                )
                checks = _checker_pair(closure_path, expected_order=order)
                check_path = (
                    output
                    / "blocks"
                    / "checks"
                    / f"block_{order}_closure_{hub_indices[0]}_{hub_indices[1]}.json"
                )
                check_sha = _write_json(
                    check_path,
                    {
                        "format": "apg-block-closure-check-v1",
                        "order": order,
                        "hub_indices": list(hub_indices),
                        "certificate": {
                            "path": str(closure_path.relative_to(output)),
                            "sha256": closure_sha,
                        },
                        "checker_runs": checks,
                        "passed": all(check["passed"] for check in checks),
                    },
                )
                closure_entries.append(
                    {
                        "hub_indices": list(hub_indices),
                        "certificate_path": str(closure_path.relative_to(output)),
                        "certificate_sha256": closure_sha,
                        "checks_path": str(check_path.relative_to(output)),
                        "checks_sha256": check_sha,
                        "passed": all(check["passed"] for check in checks),
                    }
                )
                if not closure_entries[-1]["passed"]:
                    raise PromotionError(
                        f"block {order} closure {hub_indices} failed an independent checker"
                    )
            if len(closure_entries) != 9:
                raise PromotionError(
                    f"block {order} exposed {len(closure_entries)} cap-hub closures, expected 9"
                )

        target_entries: list[dict[str, object]] = []
        manifest["targets"] = target_entries
        for target, chain in selected.items():
            composed, closed, composition = _compose_chain(loaded, chain)
            if len(composed.rotation) != target:
                raise PromotionError(
                    f"target {target} composition has order {len(composed.rotation)}, not {target}"
                )
            replayed = replay_composition_trace(
                {order: source.block for order, source in loaded.items()},
                composition["selected_trace"],
            )
            if replayed.rotation != composed.rotation:
                raise PromotionError(
                    f"target {target} selected composition trace does not replay its open rotation"
                )
            replayed_closed = blocks.close_block(replayed)
            if replayed_closed != closed:
                raise PromotionError(
                    f"target {target} selected composition trace does not replay its closed rotation"
                )
            open_map_sha = hashlib.sha256(
                _certificate_key(blocks.rotation_to_certificate(composed.rotation))
            ).hexdigest()
            composition["selected_open_block_canonical_sha256"] = open_map_sha
            composition["replay_verified"] = True
            expected_profile = _target_profile(target, chain, loaded, block_t)
            observed_profile = _observed_profile(closed)
            if (
                observed_profile["vertex_counts"] != expected_profile["vertex_counts"]
                or observed_profile["face_counts"] != expected_profile["face_counts"]
            ):
                raise PromotionError(
                    f"target {target} certificate histogram does not match its source-chain prediction"
                )
            if expected_profile["t_total"] != 0:
                raise PromotionError(
                    f"target {target} source chain exceeds the portable t=0 budget"
                )
            certificate_path = output / "certificates" / f"apg_{target}.json"
            certificate = blocks.rotation_to_certificate(closed)
            certificate_sha = _write_json(certificate_path, certificate)
            canonical_map_sha = hashlib.sha256(_certificate_key(certificate)).hexdigest()
            checks = _checker_pair(certificate_path, expected_order=target)
            checks_path = output / "checks" / f"apg_{target}.json"
            checks_sha = _write_json(
                checks_path,
                {
                    "format": "apg-target-check-v1",
                    "order": target,
                        "certificate": {
                            "path": str(certificate_path.relative_to(output)),
                            "sha256": certificate_sha,
                            "canonical_plane_map_sha256": canonical_map_sha,
                        },
                        "expected_profile": expected_profile,
                        "observed_profile": observed_profile,
                        "checker_runs": checks,
                    "passed": all(check["passed"] for check in checks),
                },
            )
            entry: dict[str, object] = {
                "order": target,
                "block_chain": list(chain),
                "certificate_path": str(certificate_path.relative_to(output)),
                "certificate_sha256": certificate_sha,
                "canonical_plane_map_sha256": canonical_map_sha,
                "checks_path": str(checks_path.relative_to(output)),
                "checks_sha256": checks_sha,
                "expected_profile": expected_profile,
                "observed_profile": observed_profile,
                "composition": composition,
                "replay": {
                    "composer_sha256": _sha256(Path(__file__).resolve()),
                    "checker_versions": _checker_versions(),
                },
                "passed": all(check["passed"] for check in checks),
            }
            target_entries.append(entry)
            if not entry["passed"]:
                raise PromotionError(f"target {target} failed an independent checker")
        manifest["disposition"] = "PROMOTED_PENDING_SEPARATE_FINAL_AUDIT"
        _write_json(output / MANIFEST_NAME, manifest)
        return manifest
    except PromotionError as exc:
        _write_incomplete_manifest(output, manifest, str(exc))
        raise


def _parse_block_argument(value: str) -> tuple[int, Path]:
    order_text, separator, path_text = value.partition("=")
    if not separator or not order_text or not path_text:
        raise argparse.ArgumentTypeError("--block must have the form ORDER=PATH")
    try:
        order = int(order_text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("block ORDER must be an integer") from exc
    if order < 4:
        raise argparse.ArgumentTypeError("block ORDER must be at least 4")
    return order, Path(path_text)


def _load_representation_file(path: Path) -> dict[int, tuple[int, ...]]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PromotionError(f"cannot read representations file {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PromotionError("representations JSON must be an object keyed by target order")
    parsed: dict[int, tuple[int, ...]] = {}
    for raw_target, raw_chain in raw.items():
        try:
            target = int(raw_target)
        except (TypeError, ValueError) as exc:
            raise PromotionError(f"representation target {raw_target!r} is not an integer") from exc
        if isinstance(raw_chain, (str, bytes)) or not isinstance(raw_chain, list):
            raise PromotionError(f"representation chain for {target} must be a JSON array")
        parsed[target] = tuple(raw_chain)
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--block",
        action="append",
        type=_parse_block_argument,
        required=True,
        metavar="ORDER=PATH",
        help="strict reopened APG rotation certificate; may be repeated",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--representations",
        type=Path,
        help="optional JSON target-to-chain map for a bounded control; defaults to the frozen 26-target Boolean map",
    )
    parser.add_argument(
        "--handoff-audit",
        type=Path,
        help=(
            "required for the default 26-target promotion: portable "
            "apg-boolean-block-handoff-v1 source-gate ledger"
        ),
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    source_blocks: dict[int, Path] = {}
    for order, path in args.block:
        if order in source_blocks:
            parser.error(f"duplicate --block order {order}")
        source_blocks[order] = path
    try:
        selected = (
            _load_representation_file(args.representations)
            if args.representations is not None
            else None
        )
        manifest = promote_target_witnesses(
            source_blocks,
            args.output_dir,
            representations=selected,
            handoff_audit=args.handoff_audit,
        )
    except PromotionError as exc:
        print(f"INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
