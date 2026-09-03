#!/usr/bin/env python3
"""Fail-closed intake audit for the direct Boolean residual-H55 r=12 Cloud run.

The Cloud job is allowed to return bounded ``unknown`` records.  This auditor
checks their source/environment and checksums, proves the two required positive
controls again, and classifies the three target records without ever treating
``unknown`` or ``unsat`` as nonexistence.  A positive target must carry a
CERTIFIED direct-block postprocess record whose nine freshly reconstructed
closures pass both independent APG checkers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import tarfile
from pathlib import Path

import blocks


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[1]
VERIFY = ROOT / "verify.py"
VERIFY_DARTS = ROOT / "verify_darts.py"
TARGETS = (28, 29, 31)


class AuditError(RuntimeError):
    """The Cloud artifact package cannot support an r=12 search disposition."""


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    answer: dict[str, object] = {}
    for key, value in pairs:
        if key in answer:
            raise ValueError(f"duplicate JSON object key {key!r}")
        answer[key] = value
    return answer


def _constant(token: str) -> object:
    raise ValueError(f"non-JSON numeric constant {token!r}")


def _read(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise AuditError(f"cannot read {label} at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{label} at {path} is not a JSON object")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _portable(path: Path, *, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise AuditError(f"artifact is outside the retained package: {path}") from exc


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _inside(root: Path, candidate: Path, *, label: str) -> Path:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise AuditError(f"{label} escapes the retained log directory") from exc
    if not candidate.is_file():
        raise AuditError(f"{label} is not a regular file: {candidate}")
    return candidate


def _verify_manifest(log_dir: Path, *, portable_root: Path, manifest: Path | None = None) -> tuple[dict[str, object], set[Path]]:
    manifest = log_dir / "SHA256SUMS" if manifest is None else manifest.resolve()
    if not manifest.is_file():
        raise AuditError("retained log directory lacks SHA256SUMS")
    rows = manifest.read_text(encoding="utf-8").splitlines()
    expected: dict[Path, str] = {}
    pattern = re.compile(r"^([0-9a-f]{64})  (.+)$")
    for row in rows:
        match = pattern.fullmatch(row)
        if match is None:
            raise AuditError("SHA256SUMS contains a malformed row")
        name = Path(match.group(2))
        if name.is_absolute():
            raise AuditError("SHA256SUMS contains an absolute path")
        candidate = (REPO_ROOT / name).resolve() if name.parts[:1] == ("research",) else (log_dir / name).resolve()
        archive = (log_dir.parents[1] / f"{log_dir.name}.tar.gz").resolve()
        try:
            candidate.relative_to(log_dir)
        except ValueError:
            if candidate != archive:
                raise AuditError("SHA256SUMS artifact escapes the retained log directory")
        if not candidate.is_file():
            raise AuditError(f"SHA256SUMS artifact is not a regular file: {candidate}")
        if candidate in expected:
            raise AuditError("SHA256SUMS names an artifact more than once")
        expected[candidate] = match.group(1)
    if not expected:
        raise AuditError("SHA256SUMS is empty")
    bad = [str(path) for path, digest in expected.items() if _sha(path) != digest]
    if bad:
        raise AuditError("SHA256SUMS mismatch: " + ", ".join(bad))
    return ({
        "path": _portable(manifest, root=portable_root),
        "sha256": _sha(manifest),
        "entries": len(expected),
        "artifact_paths": sorted(_portable(path, root=portable_root) for path in expected),
        "passed": True,
    }, set(expected))


def _checker(checker: Path, certificate: Path, *, order: int) -> dict[str, object]:
    completed = subprocess.run([sys.executable, str(checker), str(certificate), "--expect-order", str(order)], cwd=str(ROOT), text=True, capture_output=True, check=False)
    return {"checker": checker.name, "returncode": completed.returncode, "passed": completed.returncode == 0}


def _check_closed_certificate(certificate: dict[str, object], *, order: int) -> list[dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="apg-r12-intake-") as name:
        path = Path(name) / "certificate.json"
        _write(path, certificate)
        runs = [_checker(VERIFY, path, order=order), _checker(VERIFY_DARTS, path, order=order)]
    _require(all(run["passed"] for run in runs), f"order {order} certificate failed an independent verifier")
    return runs


def _check_direct_postprocess(raw_path: Path, raw: dict[str, object], post_path: Path, *, order: int, r: int) -> dict[str, object]:
    certificate = raw.get("certificate")
    if not isinstance(certificate, dict):
        raise AuditError(f"order {order} positive raw record lacks a certificate")
    try:
        rotation = blocks.rotation_from_certificate(certificate)
        normalized = blocks.rotation_to_certificate(rotation)
        if normalized != certificate or len(rotation) != order:
            raise blocks.BlockError("raw strict block is not canonical at the expected order")
        block = blocks.Block(rotation, blocks.validate_block(rotation))
    except (TypeError, ValueError, blocks.BlockError) as exc:
        raise AuditError(f"order {order} positive raw record is not a strict block: {exc}") from exc
    post = _read(post_path, label=f"order {order} postprocess")
    _require(post.get("format") == "apg-exact-map-postprocess-v1" and post.get("lane") == "block", f"order {order} postprocess is not direct-block provenance")
    _require(post.get("disposition") == "CERTIFIED" and post.get("solver_disposition") == "CANDIDATE", f"order {order} postprocess is not CERTIFIED")
    _require(post.get("source_record_sha256") == _sha(raw_path), f"order {order} postprocess does not bind raw record bytes")
    _require(post.get("r") == r and post.get("expected_order") == order and post.get("expected_block_t") == 0, f"order {order} postprocess profile mismatches")
    for key in ("block_validation", "block_t_gate", "r_gate"):
        _require(isinstance(post.get(key), dict) and post[key].get("passed") is True, f"order {order} postprocess {key} did not pass")
    _require(isinstance(post.get("structural_audit"), dict) and post["structural_audit"].get("status") == "COMPLETED", f"order {order} structural audit did not complete")
    closures = post.get("closures")
    _require(post.get("closure_count") == 9 and isinstance(closures, list) and len(closures) == 9, f"order {order} postprocess lacks nine closures")
    retained: dict[tuple[int, int], str] = {}
    for row in closures:
        if not isinstance(row, dict) or row.get("passed") is not True:
            raise AuditError(f"order {order} postprocess reports a failed closure")
        hubs = row.get("hub_indices")
        if not isinstance(hubs, list) or len(hubs) != 2 or any(not isinstance(value, int) or isinstance(value, bool) for value in hubs):
            raise AuditError(f"order {order} postprocess has malformed closure indices")
        digest = row.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise AuditError(f"order {order} postprocess has malformed closure SHA-256")
        retained[(hubs[0], hubs[1])] = digest
    expected_grid = {(a, b) for a in range(3) for b in range(3)}
    _require(set(retained) == expected_grid, f"order {order} postprocess closure grid is incomplete")
    fresh: list[dict[str, object]] = []
    for hubs, closed in blocks.close_block_variants(block):
        certificate_value = blocks.rotation_to_certificate(closed)
        with tempfile.TemporaryDirectory(prefix="apg-r12-closure-") as name:
            path = Path(name) / f"closure_{hubs[0]}_{hubs[1]}.json"
            _write(path, certificate_value)
            digest = _sha(path)
            runs = [_checker(VERIFY, path, order=order), _checker(VERIFY_DARTS, path, order=order)]
        _require(retained[hubs] == digest, f"order {order} retained closure does not match fresh reconstruction")
        _require(all(run["passed"] for run in runs), f"order {order} fresh closure failed an independent verifier")
        fresh.append({"hub_indices": list(hubs), "sha256": digest, "checker_runs": runs, "passed": True})
    return {"postprocess_sha256": _sha(post_path), "fresh_closures": fresh, "passed": True}


def audit(log_dir: Path | str, output: Path | str, *, source_commit: str, source_tree: str, manifest_path: Path | str | None = None) -> dict[str, object]:
    """Audit one retained r12 Cloud directory and write its explicit disposition."""

    log_dir, output = Path(log_dir).resolve(), Path(output).resolve()
    if output.parent != log_dir:
        raise ValueError("audit output must be written inside the retained log directory")
    try:
        log_dir.relative_to(REPO_ROOT)
        portable_root = REPO_ROOT
    except ValueError:
        # Unit fixtures intentionally live in a temporary package.  Production
        # Cloud artifacts stay bound to REPO_ROOT above, while this keeps every
        # persisted test artifact relative rather than leaking a host pathname.
        portable_root = log_dir.parent
    result: dict[str, object] = {"format": "apg-bool-r12-residual-h55-intake-audit-v1", "disposition": "INVALID", "log_dir": _portable(log_dir, root=portable_root), "source_commit": source_commit, "source_tree": source_tree, "manifest": {}, "controls": {}, "targets": {}, "target_certificate_exists": False, "nonexistence_claimed": False}
    try:
        _require(re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None and re.fullmatch(r"[0-9a-f]{40}", source_tree) is not None, "expected source commit/tree must be full lowercase SHA-1 values")
        if manifest_path is None:
            sidecar = log_dir.parents[1] / f"{log_dir.name}_SHA256SUMS"
            manifest_path = sidecar if sidecar.is_file() else None
        manifest, listed = _verify_manifest(
            log_dir, portable_root=portable_root, manifest=None if manifest_path is None else Path(manifest_path)
        )
        result["manifest"] = manifest
        def require_listed(path: Path) -> None:
            _require(path.resolve() in listed, f"required artifact is not listed in SHA256SUMS: {path.name}")
        source_gate_path = log_dir / "source_gate.log"
        if not source_gate_path.is_file():
            source_gate_path = log_dir / "environment_source_gate.log"
        source_gate = source_gate_path.read_text(encoding="utf-8")
        require_listed(source_gate_path)
        environment_path = log_dir / "pre_job_environment.log"
        environment = environment_path.read_text(encoding="utf-8") if environment_path.is_file() else source_gate
        if environment_path.is_file():
            require_listed(environment_path)
        _require("Linux" in environment and "git fsck --full" in source_gate and source_commit in source_gate and source_tree in source_gate, "environment/source gate does not bind Linux, fsck, commit, and tree")
        archive = log_dir.parents[1] / f"{log_dir.name}.tar.gz"
        if archive.is_file():
            require_listed(archive)
            try:
                with tarfile.open(archive, "r:gz") as bundle:
                    names = set(bundle.getnames())
            except (OSError, tarfile.TarError) as exc:
                raise AuditError(f"retained archive is unreadable: {exc}") from exc
            _require(any(name.endswith("/RUN_REPORT.md") for name in names), "retained archive lacks RUN_REPORT.md")
            result["archive"] = {"path": _portable(archive, root=portable_root), "sha256": _sha(archive), "readable": True}
        order20_path = log_dir / "bool_known_order20.json"
        require_listed(order20_path)
        order20 = _read(order20_path, label="order-20 control")
        _require(order20.get("disposition") == "CANDIDATE" and order20.get("require_residual_h55_2regular", False) is False and order20.get("require_residual_h55_c4") is False, "order-20 control does not prove residual gates disabled")
        control20 = order20.get("certificate")
        _require(isinstance(control20, dict), "order-20 control lacks a certificate")
        result["controls"]["20"] = {"checker_runs": _check_closed_certificate(control20, order=20), "passed": True}
        raw_a21 = log_dir / "bool_known_A21.json"
        require_listed(raw_a21)
        require_listed(log_dir / "bool_known_A21_postprocess.json")
        a21 = _read(raw_a21, label="A21 direct control")
        _require(a21.get("disposition") == "CANDIDATE" and a21.get("canonical") is True and a21.get("require_t0") is True and a21.get("r") == 10 and a21.get("require_residual_h55_2regular", False) is False and a21.get("require_residual_h55_c4") is False, "A21 control does not prove profile-specific residual gates")
        result["controls"]["21"] = _check_direct_postprocess(raw_a21, a21, log_dir / "bool_known_A21_postprocess.json", order=21, r=10)
        target_entries: dict[str, object] = {}
        result["targets"] = target_entries
        positive = 0
        for order in TARGETS:
            raw_path = log_dir / f"bool_r12_h55_b_{order}_r12_t0_seed0.json"
            require_listed(raw_path)
            raw = _read(raw_path, label=f"target {order} raw record")
            _require(raw.get("format") == "apg-exact-map-bool-sat-v1" and raw.get("lane") == "block" and raw.get("order") == order and raw.get("r") == 12 and raw.get("canonical") is True and raw.get("require_t0") is True and raw.get("require_residual_h55_2regular", True) is True and raw.get("require_residual_h55_c4") is True, f"target {order} raw record does not bind the required r12 profile")
            disposition = raw.get("disposition")
            _require(disposition in {"INCOMPLETE", "CANDIDATE"}, f"target {order} has unsupported raw disposition {disposition!r}")
            entry: dict[str, object] = {"raw_record_sha256": _sha(raw_path), "raw_disposition": disposition, "z3_result": raw.get("z3_result"), "block_certificate_exists": False, "target_certificate_exists": False, "nonexistence_claimed": False}
            if disposition == "CANDIDATE":
                post_path = log_dir / f"bool_r12_h55_b_{order}_r12_t0_seed0_postprocess.json"
                require_listed(post_path)
                entry["direct_block_audit"] = _check_direct_postprocess(raw_path, raw, post_path, order=order, r=12)
                entry["block_certificate_exists"] = True
                positive += 1
            target_entries[str(order)] = entry
        result["disposition"] = "VALIDATED_BLOCK_CERTIFICATES" if positive else "VALIDATED_INCOMPLETE"
        result["block_certificate_count"] = positive
    except AuditError as exc:
        result["reason"] = str(exc)
        _write(output, result)
        raise
    _write(output, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-tree", required=True)
    parser.add_argument("--manifest", type=Path, help="optional SHA256SUMS path; defaults to the log-local or results-sidecar manifest")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        value = audit(args.log_dir, args.output, source_commit=args.source_commit, source_tree=args.source_tree, manifest_path=args.manifest)
    except (OSError, UnicodeError, ValueError, AuditError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
