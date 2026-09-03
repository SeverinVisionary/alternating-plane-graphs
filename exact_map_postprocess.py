#!/usr/bin/env python3
"""Turn an exact-map SAT candidate into a checked certificate record.

The solver is intentionally only a model finder.  This module is the
certificate boundary: it serializes every candidate, invokes both independent
APG checkers in fresh processes, and, for an open two-socket block, validates
the block and all nine cap-hub closures.  A missing checker, failed check, or
partial closure set remains ``INCOMPLETE``; it is never converted to an
existence or nonexistence claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import blocks
import structural_audit


ROOT = Path(__file__).resolve().parent
VERIFY = ROOT / "verify.py"
VERIFY_DARTS = ROOT / "verify_darts.py"


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Refuse an ambiguous raw solver record before normalizing its witness."""

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_nonstandard_json_constant(token: str) -> object:
    raise ValueError(f"non-JSON numeric constant {token!r}")


def _read_json_object(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_json_keys,
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"cannot read {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} at {path} is not a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _sha256(path)


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


def _checker_pair(certificate: Path, *, expected_order: int) -> list[dict[str, object]]:
    return [
        _run_checker(VERIFY, certificate, expected_order=expected_order),
        _run_checker(VERIFY_DARTS, certificate, expected_order=expected_order),
    ]


def _rotation_certificate(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("solver record certificate is not an object")
    if value.get("format") != "apg-plane-rotation-v1":
        raise ValueError("solver record certificate has the wrong format")
    rows = value.get("vertices")
    if not isinstance(rows, list) or not rows:
        raise ValueError("solver record certificate has no vertices")
    # Round-trip through the independent block parser only for normalization;
    # the final acceptance still comes from the two fresh checker processes.
    rotation = blocks.rotation_from_certificate(value)
    return blocks.rotation_to_certificate(rotation)


def _certificate_r(certificate: dict[str, object]) -> int:
    """Return the degree-three count reconstructed from a normalized witness."""

    rows = certificate.get("vertices")
    if not isinstance(rows, list):  # guarded by _rotation_certificate
        raise ValueError("normalized certificate has no vertex rows")
    return sum(
        isinstance(row, dict)
        and isinstance(row.get("clockwise"), list)
        and len(row["clockwise"]) == 3
        for row in rows
    )


def _socket_summary(sockets: tuple[blocks.Socket, blocks.Socket]) -> list[dict[str, object]]:
    return [
        {"boundary": list(socket.boundary), "whites": list(socket.whites)}
        for socket in sockets
    ]


def _cap_fans_from_record(value: object) -> tuple[blocks.ClosureFan, blocks.ClosureFan]:
    """Parse the four marked closed-cap edges retained in a solver record."""

    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("cap-fan record must contain exactly two fans")
    fans: list[blocks.ClosureFan] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("cap-fan record item must be an object")
        hub = item.get("center")
        leaves = item.get("leaves")
        if (
            isinstance(hub, bool)
            or not isinstance(hub, int)
            or not isinstance(leaves, list)
            or len(leaves) != 2
            or any(isinstance(leaf, bool) or not isinstance(leaf, int) for leaf in leaves)
        ):
            raise ValueError("cap-fan record needs one integer center and two integer leaves")
        fans.append(blocks.ClosureFan(hub=hub, leaves=(leaves[0], leaves[1])))
    if len({vertex for fan in fans for vertex in fan.whites}) != 6:
        raise ValueError("cap-fan record must name six distinct vertices")
    return fans[0], fans[1]


def postprocess_record(
    record_path: Path,
    output_path: Path,
    *,
    expected_order: int | None = None,
    expected_block_t: int | None = None,
) -> dict[str, object]:
    """Postprocess one solver record and write a deterministic audit record."""

    # The checker subprocesses intentionally run from ``ROOT`` to isolate them
    # from a caller's working directory.  Normalize both caller-supplied paths
    # before deriving certificate paths so a normal repo-root CLI invocation
    # cannot make those subprocesses look for ``results/...`` below ROOT.
    record_path = record_path.resolve()
    output_path = output_path.resolve()
    record = _read_json_object(record_path, label="solver record")
    lane = record.get("lane")
    if lane not in {"closed", "block"}:
        raise ValueError("solver record lane must be 'closed' or 'block'")
    cap_fan_search = record.get("require_cap_fans") is True
    require_t0 = record.get("require_t0") is True
    # The solver CLI permits ``--require-t0`` for a closed map only when its
    # two cap fans are explicitly marked.  Enforce the same provenance rule at
    # the certificate boundary: otherwise a malformed closed record could be
    # labelled with a block-only t=0 condition but bypass reopening and the
    # nine-closure audit below.
    if require_t0 and lane == "closed" and not cap_fan_search:
        raise ValueError("a require_t0 closed record must mark cap fans")
    if expected_block_t is not None:
        if lane != "block" and not cap_fan_search:
            raise ValueError("--expected-block-t is valid only for a block or cap-fan record")
        if (
            not isinstance(expected_block_t, int)
            or isinstance(expected_block_t, bool)
            or expected_block_t < 0
        ):
            raise ValueError("expected block t must be a nonnegative integer")
    if require_t0:
        if expected_block_t is None:
            expected_block_t = 0
        elif expected_block_t != 0:
            raise ValueError("a require_t0 solver record cannot expect nonzero block t")
    claimed_r = record.get("r")
    valid_claimed_r = (
        isinstance(claimed_r, int)
        and not isinstance(claimed_r, bool)
        and claimed_r >= 0
    )
    inferred_order = int(record.get("order", 46 if lane == "closed" else 27))
    target_order = inferred_order if expected_order is None else expected_order

    result: dict[str, object] = {
        "format": "apg-exact-map-postprocess-v1",
        "source_record": str(record_path),
        "source_record_sha256": _sha256(record_path),
        "lane": lane,
        "r": record.get("r"),
        "expected_order": target_order,
        "solver_disposition": record.get("disposition"),
        "disposition": "INCOMPLETE",
    }
    if expected_block_t is not None:
        result["expected_block_t"] = expected_block_t

    if record.get("disposition") != "CANDIDATE":
        result["reason"] = "solver record did not emit a positive candidate"
        _write_json(output_path, result)
        return result

    try:
        certificate = _rotation_certificate(record.get("certificate"))
    except (TypeError, ValueError, blocks.BlockError) as exc:
        result["reason"] = f"candidate normalization failed: {exc}"
        _write_json(output_path, result)
        return result

    artifact_dir = output_path.parent / (output_path.stem + "_certificates")
    candidate_path = artifact_dir / "candidate.json"
    candidate_sha = _write_json(candidate_path, certificate)
    result["candidate"] = {
        "path": str(candidate_path),
        "sha256": candidate_sha,
    }

    block: blocks.Block | None = None
    if lane == "closed":
        observed_r = _certificate_r(certificate)
        closed_r_gate = {
            "requested": claimed_r,
            "observed": observed_r,
            "passed": valid_claimed_r and observed_r == claimed_r,
        }
        if not closed_r_gate["passed"]:
            result["r_gate"] = closed_r_gate
            result["reason"] = "certificate degree-three count does not match solver record"
            _write_json(output_path, result)
            return result
        checks = _checker_pair(candidate_path, expected_order=target_order)
        result["checker_runs"] = checks
        if not all(check["passed"] for check in checks):
            result["reason"] = "one or more independent closed-map checkers failed"
            _write_json(output_path, result)
            return result
        if not cap_fan_search:
            result["r_gate"] = closed_r_gate
            result["disposition"] = "CERTIFIED"
            _write_json(output_path, result)
            return result
        result["closed_r_gate"] = closed_r_gate
        try:
            fans = _cap_fans_from_record(record.get("cap_fans"))
            rotation = blocks.rotation_from_certificate(certificate)
            block = blocks.open_cap_fans(rotation, fans)
        except (TypeError, ValueError, blocks.BlockError) as exc:
            result["cap_opening"] = {"passed": False, "reason": str(exc)}
            result["reason"] = "certified closed candidate did not reopen to a strict block"
            _write_json(output_path, result)
            return result
        result["cap_opening"] = {
            "passed": True,
            "fans": [
                {"center": fan.hub, "leaves": list(fan.leaves)}
                for fan in fans
            ],
            "sockets": _socket_summary(block.sockets),
        }
    else:
        # An open block is not itself a closed APG.  Validate the strict
        # Section-8 interface first, then run every 3x3 cap-hub closure.
        try:
            rotation = blocks.rotation_from_certificate(certificate)
            sockets = blocks.validate_block(rotation)
            block = blocks.Block(rotation, sockets)
        except (TypeError, ValueError, blocks.BlockError) as exc:
            result["reason"] = f"strict block validation failed: {exc}"
            _write_json(output_path, result)
            return result

    if block is None:
        raise AssertionError("block boundary did not construct a block")
    sockets = block.sockets

    result["block_validation"] = {
        "passed": True,
        "sockets": _socket_summary(sockets),
    }

    # A strict block can be a valid finite witness while still being a poor
    # candidate for the unbounded Section-8 construction.  Preserve the exact
    # H55/t evidence for every positive model, but never turn a structural
    # observation into an extra acceptance condition: the two independent
    # rotation verifiers remain the mathematical certificate boundary.
    try:
        result["structural_audit"] = {
            "status": "COMPLETED",
            "value": structural_audit.analyze_block(
                structural_audit.audit_data_from_block(block)
            ),
        }
    except (TypeError, ValueError, blocks.BlockError) as exc:
        result["structural_audit"] = {
            "status": "BLOCKED",
            "reason": f"structural audit failed without invalidating the block: {exc}",
        }

    if expected_block_t is not None:
        audit = result["structural_audit"]
        if not isinstance(audit, dict) or audit.get("status") != "COMPLETED":
            result["block_t_gate"] = {
                "requested": expected_block_t,
                "passed": False,
                "reason": "structural audit did not complete",
            }
            result["reason"] = "expected block t could not be checked"
            _write_json(output_path, result)
            return result
        value = audit.get("value")
        variants = value.get("variants") if isinstance(value, dict) else None
        observed: list[dict[str, object]] = []
        if isinstance(variants, list):
            for variant in variants:
                if not isinstance(variant, dict):
                    continue
                observed.append(
                    {
                        "hub_indices": variant.get("hub_indices"),
                        "t_vertex": variant.get("t_vertex"),
                        "t_face": variant.get("t_face"),
                    }
                )
        passed = len(observed) == 9 and all(
            item["t_vertex"] == expected_block_t
            and item["t_face"] == expected_block_t
            for item in observed
        )
        result["block_t_gate"] = {
            "requested": expected_block_t,
            "observed": observed,
            "passed": passed,
        }
        if not passed:
            result["reason"] = "all cap-hub closures did not match expected block t"
            _write_json(output_path, result)
            return result

    audit = result["structural_audit"]
    value = audit.get("value") if isinstance(audit, dict) else None
    variants_for_r = value.get("variants") if isinstance(value, dict) else None
    observed_r_values = (
        [variant.get("r") for variant in variants_for_r if isinstance(variant, dict)]
        if isinstance(variants_for_r, list)
        else []
    )
    result["r_gate"] = {
        "requested": claimed_r,
        "observed": observed_r_values,
        "passed": (
            valid_claimed_r
            and len(observed_r_values) == 9
            and all(value == claimed_r for value in observed_r_values)
        ),
    }
    if not result["r_gate"]["passed"]:
        result["reason"] = "all cap-hub closures did not match solver r profile"
        _write_json(output_path, result)
        return result

    closures: list[dict[str, object]] = []
    try:
        variants = blocks.close_block_variants(block)
    except (TypeError, ValueError, blocks.BlockError) as exc:
        result["reason"] = f"closure enumeration failed: {exc}"
        result["closure_count"] = 0
        _write_json(output_path, result)
        return result

    for hub_indices, closed_rotation in variants:
        label = f"closure_{hub_indices[0]}_{hub_indices[1]}.json"
        closed_path = artifact_dir / label
        closed_certificate = blocks.rotation_to_certificate(closed_rotation)
        closed_sha = _write_json(closed_path, closed_certificate)
        checks = _checker_pair(closed_path, expected_order=target_order)
        closures.append(
            {
                "hub_indices": list(hub_indices),
                "path": str(closed_path),
                "sha256": closed_sha,
                "checker_runs": checks,
                "passed": all(check["passed"] for check in checks),
            }
        )

    result["closure_count"] = len(closures)
    result["closures"] = closures
    if len(closures) == 9 and all(item["passed"] for item in closures):
        if lane == "closed" and cap_fan_search:
            # This is deliberately an *open-block* certificate, not a closed
            # APG target witness.  Crucially, it is exported only after the
            # raw candidate has passed every reopening, structural, t/r, and
            # nine-closure gate above.  A later separately source-gated
            # promotion job can bind this hash to the certified postprocess
            # record; an incomplete postprocess must leave no reusable block
            # artifact behind.
            opened_block_path = artifact_dir / "opened_block.json"
            opened_block_sha = _write_json(
                opened_block_path, blocks.rotation_to_certificate(block.rotation)
            )
            result["opened_block"] = {
                "path": str(opened_block_path),
                "sha256": opened_block_sha,
                "order": len(block.rotation),
                "format": blocks.APG_FORMAT,
            }
        result["disposition"] = "CERTIFIED"
    else:
        result["reason"] = "not all nine cap-hub closures passed both checkers"
    _write_json(output_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="exact_map_sat.py JSON record")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--expected-order",
        type=int,
        help="override the lane default (46 for closed, 27 for block); useful for controls",
    )
    parser.add_argument(
        "--expected-block-t",
        type=int,
        help="require this t value in every cap-hub closure of a block candidate",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        result = postprocess_record(
            args.record,
            args.output,
            expected_order=args.expected_order,
            expected_block_t=args.expected_block_t,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["disposition"] == "CERTIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
