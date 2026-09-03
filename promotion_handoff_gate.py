#!/usr/bin/env python3
"""Bind Boolean cap-search artifacts to portable strict-block inputs.

The cap-motif cloud search has two distinct certificate boundaries.  A raw
Boolean ``CANDIDATE`` is only a proposed closed map; the exact-map
postprocessor must reopen it, validate the strict Section-8 block, and pass
the nine-closure and portable ``t=0`` gates.  Conversely, a standalone
``opened_block.json`` is not evidence that it came from that certified route.

This module is the fail-closed handoff between those boundaries and the
all-target composer.  It accepts a small, portable input manifest whose paths
are relative to the manifest itself, verifies the exact raw/postprocess/opened
artifact bindings, and writes an eligible-block ledger.  The ledger contains
no target witness claim; the composer and a separate final audit remain
mandatory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path

import blocks


INPUT_FORMAT = "apg-boolean-block-handoff-input-v1"
LEDGER_FORMAT = "apg-boolean-block-handoff-v1"
FROZEN_PROFILES = {28: 12, 29: 12, 31: 12}
PUBLISHED_BLOCK_SOURCES = {
    21: "A21.json",
    22: "B22.json",
    23: "C23.json",
    24: "D24.json",
}
ROOT = Path(__file__).resolve().parent
VERIFY = ROOT / "verify.py"
VERIFY_DARTS = ROOT / "verify_darts.py"


class HandoffError(RuntimeError):
    """A cloud block artifact is not eligible for target promotion."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build one JSON object while refusing ambiguous duplicate members."""

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


def _read_json(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise HandoffError(f"cannot read {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HandoffError(f"{label} at {path} is not a JSON object")
    return value


def _relative_artifact_path(root: Path, raw: object, *, label: str) -> Path:
    """Resolve one portable handoff path without allowing archive escape."""

    if not isinstance(raw, str) or not raw:
        raise HandoffError(f"{label} must be a nonempty relative path")
    candidate = Path(raw)
    if candidate.is_absolute():
        raise HandoffError(f"{label} must be relative to the input manifest")
    resolved = (root / candidate).resolve()
    if resolved != root and root not in resolved.parents:
        raise HandoffError(f"{label} escapes the input artifact package")
    if not resolved.is_file():
        raise HandoffError(f"{label} is not a regular file: {resolved}")
    return resolved


def _portable_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError as exc:  # guarded by _relative_artifact_path
        raise AssertionError("artifact unexpectedly escaped package root") from exc


def _require(value: object, condition: bool, message: str) -> None:
    if not condition:
        raise HandoffError(message)


def _cap_fans_from_raw(
    record: Mapping[str, object], *, order: int
) -> tuple[blocks.ClosureFan, blocks.ClosureFan]:
    value = record.get("cap_fans")
    if not isinstance(value, list) or len(value) != 2:
        raise HandoffError(f"block {order} raw record must name exactly two cap fans")
    fans: list[blocks.ClosureFan] = []
    for item in value:
        if not isinstance(item, dict):
            raise HandoffError(f"block {order} raw cap fan is not an object")
        center = item.get("center")
        leaves = item.get("leaves")
        if (
            not isinstance(center, int)
            or isinstance(center, bool)
            or not isinstance(leaves, list)
            or len(leaves) != 2
            or any(not isinstance(leaf, int) or isinstance(leaf, bool) for leaf in leaves)
        ):
            raise HandoffError(f"block {order} raw cap fan has malformed vertices")
        fans.append(blocks.ClosureFan(center, (leaves[0], leaves[1])))
    if len({vertex for fan in fans for vertex in fan.whites}) != 6:
        raise HandoffError(f"block {order} raw cap fans do not name six distinct vertices")
    return fans[0], fans[1]


def _require_candidate_raw(
    record: Mapping[str, object], *, order: int, expected_r: int
) -> tuple[
    dict[str, object],
    dict[str, object],
    blocks.Rotation,
    tuple[blocks.ClosureFan, blocks.ClosureFan],
]:
    """Check the frozen Boolean profile and return its normalized witness."""

    _require(
        record,
        record.get("format") == "apg-exact-map-bool-sat-v1",
        f"block {order} raw record has the wrong format",
    )
    _require(record, record.get("lane") == "closed", f"block {order} raw lane is not closed")
    _require(record, record.get("order") == order, f"block {order} raw order mismatches")
    _require(record, record.get("r") == expected_r, f"block {order} raw r mismatches")
    _require(
        record,
        record.get("disposition") == "CANDIDATE",
        f"block {order} raw record is not a positive candidate",
    )
    _require(record, record.get("canonical") is True, f"block {order} raw record is not canonical")
    _require(
        record,
        record.get("require_cap_fans") is True,
        f"block {order} raw record did not require marked cap fans",
    )
    _require(
        record,
        record.get("require_t0") is True,
        f"block {order} raw record did not require portable t=0",
    )
    raw_certificate = record.get("certificate")
    if not isinstance(raw_certificate, dict):
        raise HandoffError(f"block {order} raw certificate is not an object")
    try:
        rotation = blocks.rotation_from_certificate(raw_certificate)
    except (TypeError, ValueError, blocks.BlockError) as exc:
        raise HandoffError(f"block {order} raw certificate is invalid: {exc}") from exc
    if len(rotation) != order:
        raise HandoffError(f"block {order} raw certificate has order {len(rotation)}")
    return (
        blocks.rotation_to_certificate(rotation),
        raw_certificate,
        rotation,
        _cap_fans_from_raw(record, order=order),
    )


def _run_checker(
    checker: Path, certificate: Path, *, expected_order: int
) -> dict[str, object]:
    command = [
        sys.executable,
        str(checker),
        str(certificate),
        "--expect-order",
        str(expected_order),
    ]
    completed = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "checker": checker.name,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def _raw_checker_pair(
    certificate: dict[str, object], *, expected_order: int
) -> list[dict[str, object]]:
    """Recheck the raw closed candidate without trusting saved checker logs."""

    with tempfile.TemporaryDirectory(prefix="apg-handoff-raw-check-") as directory:
        path = Path(directory) / "candidate.json"
        _write_json(path, certificate)
        return [
            _run_checker(VERIFY, path, expected_order=expected_order),
            _run_checker(VERIFY_DARTS, path, expected_order=expected_order),
        ]


def _closure_gate(postprocess: Mapping[str, object], *, order: int) -> None:
    closures = postprocess.get("closures")
    if not isinstance(closures, list) or len(closures) != 9:
        raise HandoffError(f"block {order} postprocess lacks exactly nine closures")
    observed: set[tuple[int, int]] = set()
    for closure in closures:
        if not isinstance(closure, dict):
            raise HandoffError(f"block {order} postprocess has a malformed closure record")
        hub_indices = closure.get("hub_indices")
        if (
            not isinstance(hub_indices, list)
            or len(hub_indices) != 2
            or any(not isinstance(value, int) or isinstance(value, bool) for value in hub_indices)
        ):
            raise HandoffError(f"block {order} postprocess has malformed closure indices")
        observed.add((hub_indices[0], hub_indices[1]))
        if closure.get("passed") is not True:
            raise HandoffError(f"block {order} has a failed postprocess closure")
    if observed != {(first, second) for first in range(3) for second in range(3)}:
        raise HandoffError(f"block {order} postprocess closure set is not the full 3x3 grid")


def _require_certified_postprocess(
    postprocess: Mapping[str, object],
    *,
    raw_sha256: str,
    raw_certificate: dict[str, object],
    raw_fans: tuple[blocks.ClosureFan, blocks.ClosureFan],
    opened_path: Path,
    order: int,
    expected_r: int,
) -> None:
    """Verify every source-bound gate promised by the Boolean dispatch."""

    _require(
        postprocess,
        postprocess.get("format") == "apg-exact-map-postprocess-v1",
        f"block {order} postprocess has the wrong format",
    )
    _require(
        postprocess,
        postprocess.get("lane") == "closed",
        f"block {order} postprocess lane is not closed",
    )
    _require(
        postprocess,
        postprocess.get("expected_order") == order,
        f"block {order} postprocess expected order mismatches",
    )
    _require(
        postprocess,
        postprocess.get("expected_block_t") == 0,
        f"block {order} postprocess did not require t=0",
    )
    _require(
        postprocess,
        postprocess.get("solver_disposition") == "CANDIDATE",
        f"block {order} postprocess does not bind a positive raw candidate",
    )
    _require(
        postprocess,
        postprocess.get("disposition") == "CERTIFIED",
        f"block {order} postprocess is not CERTIFIED",
    )
    _require(
        postprocess,
        postprocess.get("source_record_sha256") == raw_sha256,
        f"block {order} raw/postprocess SHA-256 binding mismatches",
    )
    candidate = postprocess.get("candidate")
    if not isinstance(candidate, dict):
        raise HandoffError(f"block {order} postprocess lacks its normalized closed candidate")
    if candidate.get("sha256") != hashlib.sha256(_json_bytes(raw_certificate)).hexdigest():
        raise HandoffError(f"block {order} postprocess candidate does not bind the raw rotation")

    closed_r_gate = postprocess.get("closed_r_gate")
    _require(
        postprocess,
        isinstance(closed_r_gate, dict) and closed_r_gate.get("passed") is True,
        f"block {order} closed r gate did not pass",
    )
    r_gate = postprocess.get("r_gate")
    _require(
        postprocess,
        isinstance(r_gate, dict)
        and r_gate.get("requested") == expected_r
        and r_gate.get("passed") is True,
        f"block {order} all-closure r gate did not pass",
    )
    cap_opening = postprocess.get("cap_opening")
    _require(
        postprocess,
        isinstance(cap_opening, dict) and cap_opening.get("passed") is True,
        f"block {order} cap opening did not pass",
    )
    expected_fans = [
        {"center": fan.hub, "leaves": list(fan.leaves)} for fan in raw_fans
    ]
    _require(
        postprocess,
        isinstance(cap_opening, dict) and cap_opening.get("fans") == expected_fans,
        f"block {order} postprocess cap-fan provenance mismatches the raw record",
    )
    block_validation = postprocess.get("block_validation")
    _require(
        postprocess,
        isinstance(block_validation, dict) and block_validation.get("passed") is True,
        f"block {order} strict block validation did not pass",
    )
    structural = postprocess.get("structural_audit")
    _require(
        postprocess,
        isinstance(structural, dict) and structural.get("status") == "COMPLETED",
        f"block {order} structural audit did not complete",
    )
    t_gate = postprocess.get("block_t_gate")
    _require(
        postprocess,
        isinstance(t_gate, dict)
        and t_gate.get("requested") == 0
        and t_gate.get("passed") is True,
        f"block {order} portable t=0 gate did not pass",
    )
    _require(
        postprocess,
        postprocess.get("closure_count") == 9,
        f"block {order} postprocess closure count is not nine",
    )
    _closure_gate(postprocess, order=order)

    opened = postprocess.get("opened_block")
    if not isinstance(opened, dict):
        raise HandoffError(f"block {order} postprocess did not export opened_block.json")
    opened_sha = _sha256(opened_path)
    _require(
        postprocess,
        opened.get("format") == blocks.APG_FORMAT
        and opened.get("order") == order
        and opened.get("sha256") == opened_sha,
        f"block {order} opened-block metadata does not bind supplied artifact",
    )


def _load_opened_strict_block(
    path: Path, *, order: int
) -> tuple[dict[str, object], blocks.Block]:
    raw = _read_json(path, label=f"block {order} opened block")
    if set(raw) != {"format", "vertices"} or raw.get("format") != blocks.APG_FORMAT:
        raise HandoffError(f"block {order} opened artifact is not a plain APG rotation certificate")
    try:
        rotation = blocks.rotation_from_certificate(raw)
        if blocks.rotation_to_certificate(rotation) != raw:
            raise blocks.BlockError("opened rotation is not canonical JSON")
        if len(rotation) != order:
            raise blocks.BlockError(f"opened rotation has order {len(rotation)}")
        sockets = blocks.validate_block(rotation)
    except (TypeError, ValueError, blocks.BlockError) as exc:
        raise HandoffError(f"block {order} opened artifact is not a strict Section-8 block: {exc}") from exc
    return raw, blocks.Block(rotation, sockets)


def _parse_input_profiles(
    input_value: Mapping[str, object], *, expected_profiles: Mapping[int, int]
) -> dict[int, Mapping[str, object]]:
    if input_value.get("format") != INPUT_FORMAT:
        raise HandoffError(f"handoff input format must be {INPUT_FORMAT!r}")
    profiles = input_value.get("profiles")
    if not isinstance(profiles, dict):
        raise HandoffError("handoff input must contain a profiles object")
    parsed: dict[int, Mapping[str, object]] = {}
    for raw_order, entry in profiles.items():
        try:
            order = int(raw_order)
        except (TypeError, ValueError) as exc:
            raise HandoffError(f"handoff profile key {raw_order!r} is not an integer") from exc
        if str(order) != raw_order or order in parsed:
            raise HandoffError(f"handoff profile key {raw_order!r} is not canonical")
        if not isinstance(entry, dict):
            raise HandoffError(f"handoff profile {order} is not an object")
        parsed[order] = entry
    if set(parsed) != set(expected_profiles):
        raise HandoffError(
            "handoff profiles must be exactly "
            + ", ".join(map(str, sorted(expected_profiles)))
        )
    return parsed


def _export_published_blocks(root: Path) -> dict[str, object]:
    """Materialize the four committed controls in the canonical handoff schema.

    These files originate in the authenticated source checkout, not in the
    cloud-result archive.  Their original bytes and canonicalized strict-block
    copies are both hashed so the all-target composer can consume the same
    plain APG rotation format as newly found Boolean blocks.
    """

    exported: dict[str, object] = {}
    for order, filename in PUBLISHED_BLOCK_SOURCES.items():
        source = ROOT / "results" / "blocks" / filename
        raw = _read_json(source, label=f"published block {order}")
        rows = raw.get("vertices")
        try:
            rotation = blocks.rotation_from_certificate(
                {"format": blocks.APG_FORMAT, "vertices": rows}
            )
            if len(rotation) != order:
                raise blocks.BlockError(f"published block has order {len(rotation)}")
            sockets = blocks.validate_block(rotation)
        except (TypeError, ValueError, blocks.BlockError) as exc:
            raise HandoffError(f"published block {order} is not a strict control: {exc}") from exc
        path = root / "published_blocks" / f"strict_block_{order}.json"
        canonical_sha = _write_json(path, blocks.rotation_to_certificate(rotation))
        exported[str(order)] = {
            "order": order,
            "source_repo_path": str(source.relative_to(ROOT)),
            "source_sha256": _sha256(source),
            "opened_block_path": _portable_path(root, path),
            "opened_block_sha256": canonical_sha,
            "strict_block_validation": {
                "passed": True,
                "sockets": [
                    {"boundary": list(socket.boundary), "whites": list(socket.whites)}
                    for socket in sockets
                ],
            },
        }
    return exported


def audit_handoff_input(
    input_manifest: Path | str,
    output_ledger: Path | str,
    *,
    expected_profiles: Mapping[int, int] | None = None,
) -> dict[str, object]:
    """Write a source-bound eligible-block ledger or an incomplete audit.

    ``expected_profiles`` is injectable only for compact published controls.
    Production callers leave it unset, freezing the `(28,12),(29,12),(31,12)`
    Boolean triple.
    """

    frozen = dict(FROZEN_PROFILES if expected_profiles is None else expected_profiles)
    if not frozen or any(
        not isinstance(order, int)
        or isinstance(order, bool)
        or not isinstance(r, int)
        or isinstance(r, bool)
        for order, r in frozen.items()
    ):
        raise ValueError("expected profiles must be a nonempty integer order-to-r map")
    input_path = Path(input_manifest).resolve()
    output_path = Path(output_ledger).resolve()
    root = input_path.parent.resolve()
    if output_path.parent != root:
        raise ValueError(
            "handoff ledger must be written beside its input manifest so all artifact paths stay portable"
        )
    result: dict[str, object] = {
        "format": LEDGER_FORMAT,
        "disposition": "INCOMPLETE",
        "input_manifest": str(input_path),
        "input_manifest_sha256": _sha256(input_path),
        "required_profiles": [
            {"order": order, "r": frozen[order]} for order in sorted(frozen)
        ],
        "blocks": {},
        "published_blocks": {},
        "block_input_eligible": False,
        "target_certificate_exists": False,
        "nonexistence_claimed": False,
    }
    try:
        input_value = _read_json(input_path, label="handoff input manifest")
        entries = _parse_input_profiles(input_value, expected_profiles=frozen)
        block_entries: dict[str, object] = {}
        result["blocks"] = block_entries
        for order in sorted(frozen):
            entry = entries[order]
            if set(entry) != {"raw_record", "postprocess_record", "opened_block"}:
                raise HandoffError(
                    f"handoff profile {order} must name only raw_record, postprocess_record, and opened_block"
                )
            raw_path = _relative_artifact_path(
                root, entry["raw_record"], label=f"block {order} raw_record"
            )
            postprocess_path = _relative_artifact_path(
                root, entry["postprocess_record"], label=f"block {order} postprocess_record"
            )
            opened_path = _relative_artifact_path(
                root, entry["opened_block"], label=f"block {order} opened_block"
            )
            raw_sha = _sha256(raw_path)
            post_sha = _sha256(postprocess_path)
            opened_sha = _sha256(opened_path)
            raw = _read_json(raw_path, label=f"block {order} raw record")
            postprocess = _read_json(postprocess_path, label=f"block {order} postprocess record")
            normalized_raw, raw_certificate, raw_rotation, raw_fans = (
                _require_candidate_raw(raw, order=order, expected_r=frozen[order])
            )
            _require_certified_postprocess(
                postprocess,
                raw_sha256=raw_sha,
                raw_certificate=normalized_raw,
                raw_fans=raw_fans,
                opened_path=opened_path,
                order=order,
                expected_r=frozen[order],
            )
            opened_certificate, _opened_block = _load_opened_strict_block(
                opened_path, order=order
            )
            try:
                expected_opened = blocks.rotation_to_certificate(
                    blocks.open_cap_fans(raw_rotation, raw_fans).rotation
                )
            except (TypeError, ValueError, blocks.BlockError) as exc:
                raise HandoffError(
                    f"block {order} raw cap fans do not reopen to a strict block: {exc}"
                ) from exc
            if opened_certificate != expected_opened:
                raise HandoffError(
                    f"block {order} opened artifact does not equal the raw cap reopening"
                )
            # Check the retained raw object verbatim.  It may normalize to the
            # same mathematical rotation after parsing while still violating
            # the canonical rotation-certificate boundary (or sphere
            # embedding) that the Boolean postprocessor claimed to certify.
            raw_checker_runs = _raw_checker_pair(raw_certificate, expected_order=order)
            if not all(run["passed"] for run in raw_checker_runs):
                raise HandoffError(
                    f"block {order} raw closed candidate failed an independent checker"
                )
            block_entries[str(order)] = {
                "order": order,
                "r": frozen[order],
                "raw_record_path": _portable_path(root, raw_path),
                "raw_record_sha256": raw_sha,
                "raw_candidate_checker_runs": raw_checker_runs,
                "postprocess_path": _portable_path(root, postprocess_path),
                "postprocess_sha256": post_sha,
                "opened_block_path": _portable_path(root, opened_path),
                "opened_block_sha256": opened_sha,
                "postprocess_disposition": "CERTIFIED",
                "cap_opening_passed": True,
                "block_validation_passed": True,
                "block_t_gate_passed": True,
                "r_gate_passed": True,
                "closure_count": 9,
                "closures_passed": True,
            }
        result["disposition"] = "ELIGIBLE"
        result["block_input_eligible"] = True
        result["published_blocks"] = _export_published_blocks(root)
    except HandoffError as exc:
        result["reason"] = str(exc)
        _write_json(output_path, result)
        raise
    _write_json(output_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = audit_handoff_input(args.input_manifest, args.output)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, HandoffError) as exc:
        print(f"INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
