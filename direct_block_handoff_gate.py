#!/usr/bin/env python3
"""Bind direct open Boolean records to portable strict-block ledgers.

The residual-H55 Boolean search emits an *open* Section-8 block directly.
It therefore cannot use the cap-motif handoff: there is no closed raw map to
reopen and ``cap_opening`` would be false provenance.  This gate accepts only
a source-bound package of raw direct-block and postprocess records, recreates
every closure itself, and writes a portable ledger.  The ledger is deliberately
not an all-target existence claim; a later composer extension must explicitly
accept this distinct provenance route.
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


INPUT_FORMAT = "apg-direct-open-block-handoff-input-v1"
LEDGER_FORMAT = "apg-direct-open-block-handoff-v1"
FROZEN_PROFILES = {31: 13}
ROOT = Path(__file__).resolve().parent
VERIFY = ROOT / "verify.py"
VERIFY_DARTS = ROOT / "verify_darts.py"


class HandoffError(RuntimeError):
    """A direct Boolean artifact is not eligible for downstream use."""


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def _reject_nonstandard_json_constant(token: str) -> object:
    raise ValueError(f"non-JSON numeric constant {token!r}")


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise HandoffError(message)


def _relative_file(root: Path, value: object, *, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise HandoffError(f"{label} must be a nonempty relative path")
    raw = Path(value)
    if raw.is_absolute():
        raise HandoffError(f"{label} must be relative to the input manifest")
    path = (root / raw).resolve()
    if path != root and root not in path.parents:
        raise HandoffError(f"{label} escapes the input artifact package")
    if not path.is_file():
        raise HandoffError(f"{label} is not a regular file: {path}")
    return path


def _portable_path(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError as exc:  # guarded by _relative_file
        raise AssertionError("artifact unexpectedly escaped package root") from exc


def _source_binding() -> dict[str, str]:
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
        tree = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD^{tree}"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise HandoffError(f"cannot resolve current source commit and tree: {exc}") from exc
    if any(len(value) != 40 or any(ch not in "0123456789abcdef" for ch in value) for value in (commit, tree)):
        raise HandoffError("current source commit or tree is not a full lowercase Git SHA-1")
    return {"commit": commit, "tree": tree}


def _parse_input(
    input_value: Mapping[str, object], *, expected_profiles: Mapping[int, int]
) -> tuple[dict[int, Mapping[str, object]], dict[str, str]]:
    if set(input_value) != {"format", "source", "profiles"}:
        raise HandoffError("direct handoff input must contain only format, source, and profiles")
    if input_value.get("format") != INPUT_FORMAT:
        raise HandoffError(f"direct handoff input format must be {INPUT_FORMAT!r}")
    source = input_value.get("source")
    if not isinstance(source, dict) or set(source) != {"commit", "tree"}:
        raise HandoffError("direct handoff input source must contain only commit and tree")
    if source != _source_binding():
        raise HandoffError("direct handoff input source does not match the audited checkout")
    profiles = input_value.get("profiles")
    if not isinstance(profiles, dict):
        raise HandoffError("direct handoff input profiles must be an object")
    parsed: dict[int, Mapping[str, object]] = {}
    for text_order, entry in profiles.items():
        try:
            order = int(text_order)
        except (TypeError, ValueError) as exc:
            raise HandoffError(f"direct handoff profile key {text_order!r} is not an integer") from exc
        if str(order) != text_order or order in parsed or not isinstance(entry, dict):
            raise HandoffError(f"direct handoff profile {text_order!r} is not canonical")
        parsed[order] = entry
    if set(parsed) != set(expected_profiles):
        raise HandoffError(
            "direct handoff profiles must be exactly "
            + ", ".join(map(str, sorted(expected_profiles)))
        )
    return parsed, dict(source)


def _run_checker(checker: Path, certificate: Path, *, expected_order: int) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(checker), str(certificate), "--expect-order", str(expected_order)],
        cwd=str(ROOT), text=True, capture_output=True, check=False,
    )
    return {
        "checker": checker.name,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "passed": completed.returncode == 0,
    }


def _fresh_closure_checks(block: blocks.Block, *, order: int) -> tuple[list[dict[str, object]], dict[tuple[int, int], str]]:
    variants = blocks.close_block_variants(block)
    records: list[dict[str, object]] = []
    digests: dict[tuple[int, int], str] = {}
    with tempfile.TemporaryDirectory(prefix="apg-direct-handoff-closures-") as directory:
        root = Path(directory)
        for hubs, rotation in variants:
            certificate = blocks.rotation_to_certificate(rotation)
            path = root / f"closure_{hubs[0]}_{hubs[1]}.json"
            digest = _write_json(path, certificate)
            checks = [_run_checker(VERIFY, path, expected_order=order), _run_checker(VERIFY_DARTS, path, expected_order=order)]
            records.append({"hub_indices": list(hubs), "certificate_sha256": digest, "checker_runs": checks, "passed": all(item["passed"] for item in checks)})
            digests[hubs] = digest
    return records, digests


def _require_direct_raw(raw: Mapping[str, object], *, order: int, expected_r: int) -> tuple[dict[str, object], blocks.Block]:
    _require(raw.get("format") == "apg-exact-map-bool-sat-v1", f"block {order} raw record has the wrong format")
    _require(raw.get("lane") == "block", f"block {order} raw lane is not direct block")
    _require(raw.get("order") == order and raw.get("r") == expected_r, f"block {order} raw profile mismatches")
    _require(raw.get("disposition") == "CANDIDATE", f"block {order} raw record is not a positive candidate")
    _require(raw.get("canonical") is True and raw.get("require_t0") is True, f"block {order} raw record lacks canonical portable t=0 requirements")
    _require(raw.get("require_cap_fans") is False, f"block {order} raw record must not claim cap-fan provenance")
    _require(raw.get("require_residual_h55_2regular") is (expected_r >= 12), f"block {order} raw 2-regular propagation gate mismatches profile")
    _require(raw.get("require_residual_h55_c4") is (expected_r == 12), f"block {order} raw C4 propagation gate mismatches profile")
    certificate = raw.get("certificate")
    if not isinstance(certificate, dict):
        raise HandoffError(f"block {order} raw certificate is not an object")
    try:
        rotation = blocks.rotation_from_certificate(certificate)
        normalized = blocks.rotation_to_certificate(rotation)
        if normalized != certificate:
            raise blocks.BlockError("raw rotation is not canonical JSON")
        if len(rotation) != order:
            raise blocks.BlockError(f"raw rotation has order {len(rotation)}")
        sockets = blocks.validate_block(rotation)
    except (TypeError, ValueError, blocks.BlockError) as exc:
        raise HandoffError(f"block {order} raw record is not a strict canonical block: {exc}") from exc
    return normalized, blocks.Block(rotation, sockets)


def _require_postprocess(
    postprocess: Mapping[str, object], *, raw_sha: str, certificate: dict[str, object], order: int, expected_r: int, closure_digests: Mapping[tuple[int, int], str]
) -> None:
    _require(postprocess.get("format") == "apg-exact-map-postprocess-v1", f"block {order} postprocess has the wrong format")
    _require(postprocess.get("lane") == "block", f"block {order} postprocess is not direct block provenance")
    _require(postprocess.get("disposition") == "CERTIFIED" and postprocess.get("solver_disposition") == "CANDIDATE", f"block {order} postprocess is not CERTIFIED")
    _require(postprocess.get("source_record_sha256") == raw_sha, f"block {order} raw/postprocess SHA-256 binding mismatches")
    _require(postprocess.get("r") == expected_r and postprocess.get("expected_order") == order and postprocess.get("expected_block_t") == 0, f"block {order} postprocess profile provenance mismatches")
    _require("cap_opening" not in postprocess, f"block {order} direct postprocess must not claim cap opening")
    candidate = postprocess.get("candidate")
    _require(isinstance(candidate, dict) and candidate.get("sha256") == hashlib.sha256(_json_bytes(certificate)).hexdigest(), f"block {order} postprocess candidate does not bind raw block bytes")
    for name in ("block_validation", "block_t_gate", "r_gate"):
        gate = postprocess.get(name)
        _require(isinstance(gate, dict) and gate.get("passed") is True, f"block {order} postprocess {name} did not pass")
    _require(isinstance(postprocess.get("structural_audit"), dict) and postprocess["structural_audit"].get("status") == "COMPLETED", f"block {order} structural audit did not complete")
    closures = postprocess.get("closures")
    _require(postprocess.get("closure_count") == 9 and isinstance(closures, list) and len(closures) == 9, f"block {order} postprocess lacks nine closures")
    observed: set[tuple[int, int]] = set()
    for item in closures:
        if not isinstance(item, dict) or item.get("passed") is not True:
            raise HandoffError(f"block {order} postprocess has a failed closure")
        hubs = item.get("hub_indices")
        if not isinstance(hubs, list) or len(hubs) != 2 or any(not isinstance(value, int) or isinstance(value, bool) for value in hubs):
            raise HandoffError(f"block {order} postprocess has malformed closure indices")
        pair = (hubs[0], hubs[1])
        observed.add(pair)
        _require(item.get("sha256") == closure_digests.get(pair), f"block {order} postprocess closure bytes do not match fresh reconstruction")
    _require(observed == {(first, second) for first in range(3) for second in range(3)}, f"block {order} postprocess closure grid is not complete")


def audit_handoff_input(input_manifest: Path | str, output_ledger: Path | str, *, expected_profiles: Mapping[int, int] | None = None) -> dict[str, object]:
    """Write an eligible direct-block ledger or preserve an INCOMPLETE audit."""

    profiles = dict(FROZEN_PROFILES if expected_profiles is None else expected_profiles)
    if not profiles or any(not isinstance(order, int) or isinstance(order, bool) or not isinstance(r, int) or isinstance(r, bool) for order, r in profiles.items()):
        raise ValueError("expected profiles must be a nonempty integer order-to-r map")
    input_path, output_path = Path(input_manifest).resolve(), Path(output_ledger).resolve()
    root = input_path.parent
    if output_path.parent != root:
        raise ValueError("direct handoff ledger must be written beside its input manifest")
    result: dict[str, object] = {
        "format": LEDGER_FORMAT, "disposition": "INCOMPLETE", "input_manifest": str(input_path),
        "input_manifest_sha256": _sha256(input_path), "required_profiles": [{"order": order, "r": profiles[order]} for order in sorted(profiles)],
        "blocks": {}, "block_input_eligible": False, "target_certificate_exists": False, "nonexistence_claimed": False,
    }
    try:
        entries, source = _parse_input(_read_json(input_path, label="direct handoff input"), expected_profiles=profiles)
        result["source"] = source
        block_entries: dict[str, object] = {}
        result["blocks"] = block_entries
        for order, expected_r in sorted(profiles.items()):
            entry = entries[order]
            if set(entry) != {"raw_record", "postprocess_record"}:
                raise HandoffError(f"block {order} direct handoff entry must name only raw_record and postprocess_record")
            raw_path = _relative_file(root, entry["raw_record"], label=f"block {order} raw_record")
            post_path = _relative_file(root, entry["postprocess_record"], label=f"block {order} postprocess_record")
            raw_sha, post_sha = _sha256(raw_path), _sha256(post_path)
            certificate, block = _require_direct_raw(_read_json(raw_path, label=f"block {order} raw record"), order=order, expected_r=expected_r)
            closure_checks, closure_digests = _fresh_closure_checks(block, order=order)
            if not all(item["passed"] for item in closure_checks):
                raise HandoffError(f"block {order} fresh direct closures failed an independent checker")
            _require_postprocess(_read_json(post_path, label=f"block {order} postprocess record"), raw_sha=raw_sha, certificate=certificate, order=order, expected_r=expected_r, closure_digests=closure_digests)
            strict_path = root / "direct_blocks" / f"strict_block_{order}.json"
            strict_sha = _write_json(strict_path, certificate)
            block_entries[str(order)] = {
                "order": order, "r": expected_r,
                "raw_record_path": _portable_path(root, raw_path), "raw_record_sha256": raw_sha,
                "postprocess_path": _portable_path(root, post_path), "postprocess_sha256": post_sha,
                "strict_block_path": _portable_path(root, strict_path), "strict_block_sha256": strict_sha,
                "postprocess_disposition": "CERTIFIED", "direct_open_provenance": True,
                "block_validation_passed": True, "block_t_gate_passed": True, "r_gate_passed": True,
                "closure_count": 9, "closures_passed": True, "fresh_closure_checker_runs": closure_checks,
            }
        result["disposition"] = "ELIGIBLE"
        result["block_input_eligible"] = True
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
