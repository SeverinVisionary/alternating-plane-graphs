#!/usr/bin/env python3
"""Measure how much of each exact-map encoding is integer arithmetic.

This is the replay script for the table in ``SOLVER_CORE_DIAGNOSIS.md``.  It
builds the Z3 encodings at the recorded target profiles and reports, per
profile, the assertion count, the number of distinct AST nodes reachable from
the assertion set, the Boolean matching variables, and the uninterpreted
constants of integer sort.  It then builds the pure-CNF encoding at the closed
control profiles for comparison.

It measures formula shape only.  It runs no search and makes no claim about
whether any profile is satisfiable.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def measure_z3(degrees: list[int], faces: list[int], *, open_block: bool, **kwargs) -> dict[str, object]:
    import z3

    from exact_map_bool_sat import BooleanMapEncoding

    started = time.monotonic()
    encoding = BooleanMapEncoding(degrees, faces, open_block=open_block, **kwargs)
    build_seconds = time.monotonic() - started

    assertions = encoding.solver.assertions()
    seen: set[int] = set()
    integer_constants: set[str] = set()
    stack = list(assertions)
    while stack:
        node = stack.pop()
        key = node.get_id()
        if key in seen:
            continue
        seen.add(key)
        if (
            z3.is_const(node)
            and node.decl().kind() == z3.Z3_OP_UNINTERPRETED
            and node.sort().kind() == z3.Z3_INT_SORT
        ):
            integer_constants.add(str(node))
        stack.extend(node.children())

    return {
        "engine": "z3/exact_map_bool_sat",
        "darts": encoding.dart_count,
        "build_seconds": round(build_seconds, 2),
        "assertions": len(assertions),
        "distinct_ast_nodes": len(seen),
        "boolean_matching_variables": len(encoding.pairs),
        "integer_variables": len(integer_constants),
    }


def measure_cnf(order: int, r: int) -> dict[str, object]:
    from exact_map_cnf import ClosedMapCNF, closed_profile

    degrees, faces = closed_profile(order, r)
    started = time.monotonic()
    encoding = ClosedMapCNF(degrees, faces)
    build_seconds = time.monotonic() - started
    record: dict[str, object] = {"engine": "cnf/exact_map_cnf", "build_seconds": round(build_seconds, 2)}
    record.update(encoding.statistics())
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--skip-z3", action="store_true")
    arguments = parser.parse_args()

    from exact_map_sat import profile_block, profile_closed

    results: dict[str, dict[str, object]] = {}
    if not arguments.skip_z3:
        degrees, faces = profile_closed(20, 9)
        results["z3 closed(20,9)"] = measure_z3(degrees, faces, open_block=False)
        for order in (28, 29, 31):
            degrees, faces = profile_block(order, 12)
            results[f"z3 block({order},12) t0"] = measure_z3(
                degrees, faces, open_block=True, require_t0=True
            )
    for order, r in ((17, 8), (20, 9), (46, 18)):
        results[f"cnf closed({order},{r})"] = measure_cnf(order, r)

    for name, record in results.items():
        print(f"{name}: {record}", flush=True)
    if arguments.output:
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "tool": "measure_encoding_cost.py",
            "note": "formula-shape measurement only; no search was run",
            "results": results,
        }
        arguments.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
