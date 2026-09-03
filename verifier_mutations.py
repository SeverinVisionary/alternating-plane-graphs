#!/usr/bin/env python3
"""Mutation testing for the two certificate verifiers.

A review leg deleted one APG condition at a time from `verify.py` and
`verify_darts.py` and re-ran the definition-of-done gate: **all thirteen
mutants passed**.  The gate has one negative control -- a rotation
transposition -- and that control is rejected by the Euler check alone, so
every other condition could be removed without a test noticing.

This module closes that hole generically rather than one hand-built
counterexample at a time.  For each `_fail(...)` site in a verifier it builds a
mutant with that single call replaced by `pass`, loads it in-process, and runs
a corpus of deliberately broken certificates through it.  A condition is
*controlled* when some corpus member's verdict changes once it is removed --
accepted where the pristine verifier rejected, or rejected for a different
reason.  A condition nothing in the corpus reaches is reported by name.

The corpus is built by perturbing real certificates, so it needs no separate
source of valid APGs.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Callable, Iterator

HERE = Path(__file__).resolve().parent
TARGETS_DIR = HERE / "certificates" / "targets"

VERIFIERS = ("verify.py", "verify_darts.py")

# Defensive branches: reachable only if an earlier invariant is already broken,
# so no input can single them out.  Each is listed with why it cannot be
# controlled, rather than being silently excluded.
UNREACHABLE = {
    "verify.py": {
        "facial walk reached nonexistent dart": "symmetry is checked first, so every dart exists",
        "not every directed edge belongs to exactly one reconstructed face": "the walk loop is exhaustive by construction",
        "sum of degrees is odd": "symmetric adjacency forces an even degree sum",
    },
    "verify_darts.py": {
        "not every dart received a face": "the traversal drains `unvisited` by construction",
        "dart permutation cycle merged before returning to its start": "a permutation cycle cannot merge",
        "edge {source}-{target} has one incident face": "each dart lies in exactly one face",
    },
}


def _fail_sites(source: str) -> list[tuple[int, str]]:
    """Line numbers of `_fail(` calls, each with its whole call text.

    Multi-line calls are joined, so every site gets a distinct key: several
    conditions in `verify.py` open with a bare ``_fail(`` and would otherwise
    collide.
    """

    lines = source.split("\n")
    sites = []
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("_fail(") or stripped.startswith("_fail(message"):
            continue
        depth = 0
        parts = []
        for cursor in range(index - 1, len(lines)):
            parts.append(lines[cursor].strip())
            depth += lines[cursor].count("(") - lines[cursor].count(")")
            if depth <= 0:
                break
        sites.append((index, " ".join(parts)))
    return sites


def _mutate(source: str, line_number: int) -> str:
    """Replace the `_fail(...)` statement starting at ``line_number`` with `pass`."""

    lines = source.split("\n")
    index = line_number - 1
    indent = len(lines[index]) - len(lines[index].lstrip())
    # A call may span several lines; consume until brackets balance.
    depth = 0
    end = index
    for cursor in range(index, len(lines)):
        depth += lines[cursor].count("(") - lines[cursor].count(")")
        end = cursor
        if depth <= 0:
            break
    return "\n".join(lines[:index] + [" " * indent + "pass"] + lines[end + 1 :])


def _load(source: str, name: str):
    """Execute a verifier's source as a throwaway module.

    It has to be registered in ``sys.modules`` while it runs: the verifiers use
    dataclasses, and dataclass field resolution looks its own module up there.
    """

    safe = re.sub(r"[^0-9A-Za-z_]", "_", name)
    spec = importlib.util.spec_from_loader(safe, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__dict__["__file__"] = str(HERE / name.split(":")[0])
    sys.modules[safe] = module
    try:
        exec(compile(source, safe, "exec"), module.__dict__)
    finally:
        sys.modules.pop(safe, None)
    return module


def _verdict(module, data: object, expected_order: int | None) -> str:
    """`"accept"` or the failure message, whatever the verifier's exception is."""

    try:
        if hasattr(module, "verify_certificate"):
            module.verify_certificate(data, expected_order=expected_order)
        else:
            module.check(data, expected_order=expected_order)
    except SystemExit as exc:  # pragma: no cover - not raised by either verifier
        return f"exit:{exc}"
    except Exception as exc:
        return f"{type(exc).__name__}:{exc}"
    return "accept"


def corpus() -> Iterator[tuple[str, object, int | None]]:
    """Deliberately broken certificates, each named by what was done to it."""

    base = json.loads((TARGETS_DIR / "TARGET_46.json").read_text())

    def edit(name: str, mutate: Callable[[dict], object], order: int | None = 46):
        data = copy.deepcopy(base)
        result = mutate(data)
        return (name, data if result is None else result, order)

    def row(data: dict, label: int) -> dict:
        return next(r for r in data["vertices"] if r["id"] == label)

    yield ("pristine", copy.deepcopy(base), 46)
    yield edit("transposed-rotation", lambda d: row(d, 6)["clockwise"].__setitem__(
        slice(1, 3), row(d, 6)["clockwise"][1:3][::-1]))
    yield edit("dropped-neighbour", lambda d: row(d, 6)["clockwise"].pop())
    yield edit("duplicated-neighbour", lambda d: row(d, 5)["clockwise"].__setitem__(1, row(d, 5)["clockwise"][0]))
    yield edit("self-loop", lambda d: row(d, 5)["clockwise"].__setitem__(1, 5))
    yield edit("unnormalized-rotation", lambda d: row(d, 5).__setitem__(
        "clockwise", row(d, 5)["clockwise"][1:] + row(d, 5)["clockwise"][:1]))
    yield edit("missing-vertex", lambda d: row(d, 5)["clockwise"].__setitem__(0, 999))
    yield edit("asymmetric-edge", lambda d: row(d, 5)["clockwise"].__setitem__(0, 7))
    yield edit("wrong-expected-order", lambda d: None, 45)
    yield edit("dropped-row", lambda d: d["vertices"].pop())
    yield edit("duplicate-label", lambda d: row(d, 5).__setitem__("id", 4))
    yield edit("unsorted-rows", lambda d: d["vertices"].__setitem__(
        slice(0, 2), d["vertices"][:2][::-1]))
    yield edit("non-integer-label", lambda d: row(d, 5).__setitem__("id", "5"))
    yield edit("empty-rotation", lambda d: row(d, 5).__setitem__("clockwise", []))
    yield edit("extra-key", lambda d: row(d, 5).__setitem__("note", "x"))
    yield edit("bad-format", lambda d: d.__setitem__("format", "nope"))
    yield edit("extra-top-level-key", lambda d: d.__setitem__("extra", 1))
    yield ("not-an-object", [1, 2, 3], None)
    yield ("empty-vertices", {"format": base["format"], "vertices": []}, None)
    yield edit("degree-six", _degree_six)
    yield edit("equal-degree-edge", _equal_degree_edge)
    yield edit("edge-removed", _remove_one_edge)
    yield ("disjoint-union", _disjoint_union(), None)
    yield edit("non-integer-neighbour", lambda d: row(d, 5)["clockwise"].__setitem__(1, "7"))
    yield ("octahedron", _platonic(OCTAHEDRON), None)
    yield ("cube", _platonic(CUBE), None)


def _degree_six(data: dict) -> None:
    """Give one vertex a sixth neighbour, reciprocally, so symmetry survives."""

    rows = {r["id"]: r for r in data["vertices"]}
    a, b = 6, 9  # both degree 5 in TARGET_46, not adjacent
    if b in rows[a]["clockwise"]:
        raise AssertionError("corpus assumption broken: 6 and 9 are adjacent")
    rows[a]["clockwise"].append(b)
    rows[b]["clockwise"].append(a)
    for label in (a, b):
        ring = rows[label]["clockwise"]
        smallest = ring.index(min(ring))
        rows[label]["clockwise"] = ring[smallest:] + ring[:smallest]


def _equal_degree_edge(data: dict) -> None:
    """Rewire one edge so it joins two vertices of equal degree."""

    rows = {r["id"]: r for r in data["vertices"]}
    degrees = {label: len(row["clockwise"]) for label, row in rows.items()}
    for label, row in rows.items():
        for position, neighbour in enumerate(row["clockwise"]):
            for candidate, candidate_degree in degrees.items():
                if (
                    candidate not in (label, neighbour)
                    and candidate_degree == degrees[label]
                    and candidate not in row["clockwise"]
                    and label not in rows[candidate]["clockwise"]
                ):
                    row["clockwise"][position] = candidate
                    rows[candidate]["clockwise"].append(label)
                    back = rows[neighbour]["clockwise"]
                    back[back.index(label)] = candidate
                    rows[candidate]["clockwise"].append(neighbour)
                    return
    raise AssertionError("corpus assumption broken: no equal-degree rewiring found")


# Two plane maps that are not APGs but pass every structural check: symmetric,
# normalized, connected, simple, sphere embeddings with all degrees and all
# face sizes inside {3,4,5}.  They exist to reach the alternation gates, which
# nothing derived from a real certificate gets to -- a perturbed APG trips an
# earlier check first.
OCTAHEDRON = {1: [2, 3, 4, 5], 2: [1, 5, 6, 3], 3: [1, 2, 6, 4],
              4: [1, 3, 6, 5], 5: [1, 4, 6, 2], 6: [2, 5, 4, 3]}
CUBE = {1: [2, 4, 5], 2: [1, 6, 3], 3: [2, 7, 4], 4: [1, 3, 8],
        5: [1, 8, 6], 6: [2, 5, 7], 7: [3, 6, 8], 8: [4, 7, 5]}


def _platonic(rotation: dict[int, list[int]]) -> dict:
    return {
        "format": "apg-plane-rotation-v1",
        "vertices": [
            {"id": label, "clockwise": list(ring)} for label, ring in sorted(rotation.items())
        ],
    }


def _remove_one_edge(data: dict) -> None:
    """Delete one edge between a degree-4 and a degree-5 vertex, both ways.

    Removing an edge merges two faces, so `V - E + F` still equals 2 and the
    map stays symmetric, connected and normalized: the object survives every
    early check and lands on the face-size and alternation gates, which nothing
    else in the corpus reaches.
    """

    rows = {r["id"]: r for r in data["vertices"]}
    degrees = {label: len(r["clockwise"]) for label, r in rows.items()}
    for label, r in sorted(rows.items()):
        for neighbour in r["clockwise"]:
            if {degrees[label], degrees[neighbour]} == {4, 5}:
                rows[label]["clockwise"].remove(neighbour)
                rows[neighbour]["clockwise"].remove(label)
                for end in (label, neighbour):
                    ring = rows[end]["clockwise"]
                    smallest = ring.index(min(ring))
                    rows[end]["clockwise"] = ring[smallest:] + ring[:smallest]
                return
    raise AssertionError("corpus assumption broken: no 4-5 edge found")


def _disjoint_union() -> dict:
    """Two valid certificates side by side: connected is the only broken clause."""

    first = json.loads((TARGETS_DIR / "TARGET_46.json").read_text())
    second = json.loads((TARGETS_DIR / "TARGET_47.json").read_text())
    shift = max(r["id"] for r in first["vertices"])
    rows = list(first["vertices"])
    for r in second["vertices"]:
        rows.append(
            {"id": r["id"] + shift, "clockwise": [n + shift for n in r["clockwise"]]}
        )
    return {"format": first["format"], "vertices": rows}


def controlled_sites(verifier: str) -> dict[str, bool]:
    """For each `_fail` site, whether some corpus member exercises it."""

    source = (HERE / verifier).read_text()
    pristine = _load(source, verifier)
    cases = list(corpus())
    baseline = {name: _verdict(pristine, data, order) for name, data, order in cases}

    outcome: dict[str, bool] = {}
    for line_number, text in _fail_sites(source):
        mutant = _load(_mutate(source, line_number), f"{verifier}::mutant{line_number}")
        changed = any(
            _verdict(mutant, data, order) != baseline[name] for name, data, order in cases
        )
        outcome[f"{verifier}: {text}"] = changed
    return outcome


def main() -> int:
    failures = 0
    for verifier in VERIFIERS:
        print(f"== {verifier}")
        for site, controlled in controlled_sites(verifier).items():
            text = site.split(": ", 1)[1]
            exempt = any(reason in text for reason in UNREACHABLE[verifier])
            flag = "ok " if controlled else ("exempt" if exempt else "UNCONTROLLED")
            if not controlled and not exempt:
                failures += 1
            print(f"  {flag:12s} {site}")
    print(f"uncontrolled sites: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
