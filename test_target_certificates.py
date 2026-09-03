"""The definition-of-done gate for Conjecture 10.2.

Twenty-six target orders, each with an explicit plane rotation system, each
put to **both** independent verifiers in fresh processes, plus the profile
identities recomputed here rather than trusted from either verifier's output.

This file is deliberately paranoid.  The whole claim rests on these
certificates, so nothing about them is taken on faith: not the manifest, not
the orders, not the counts, and not the verifiers' own summaries.
"""
from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

import certificate_tools as certs
import fast_apg_check

HERE = Path(__file__).resolve().parent
TARGETS_DIR = HERE / "certificates" / "targets"

TARGETS = (
    list(range(46, 57)) + list(range(67, 75)) + list(range(88, 93)) + [109, 110]
)


def test_the_target_set_is_the_conjecture_s_open_set() -> None:
    """Read the set out of PRIOR_ART.md rather than restating the literal.

    Comparing `TARGETS` with a second spelling of its own definition is a
    tautology: edit both and the test still passes.  The frozen statement of
    the conjecture's open orders lives in PRIOR_ART.md, so that is what this
    compares against.
    """

    assert len(TARGETS) == 26
    frozen = (HERE / "PRIOR_ART.md").read_text()
    block = frozen.split("T = {")[1].split("}")[0]
    quoted = {int(token) for token in re.findall(r"\d+", block)}
    assert quoted == set(TARGETS), (
        "the gate's target set no longer matches the frozen statement in PRIOR_ART.md"
    )


def test_every_target_order_has_a_certificate() -> None:
    present = sorted(
        int(path.stem.split("_")[1]) for path in TARGETS_DIR.glob("TARGET_*.json")
    )
    assert present == sorted(TARGETS)


def test_the_manifest_matches_the_files() -> None:
    lines = (TARGETS_DIR / "SHA256SUMS").read_text().split("\n")
    recorded = {}
    for line in lines:
        if not line.strip():
            continue
        digest, name = line.split()
        name = name.lstrip("*")
        assert "/" not in name and ".." not in name, f"manifest escapes the directory: {name}"
        recorded[name] = digest
    # Counting entries is not enough: a manifest of 25 targets plus one file
    # from elsewhere would pass that and leave a target unhashed.
    assert set(recorded) == {f"TARGET_{order}.json" for order in TARGETS}
    for name, digest in recorded.items():
        actual = hashlib.sha256((TARGETS_DIR / name).read_bytes()).hexdigest()
        assert actual == digest, f"{name} does not match its manifest entry"


@pytest.mark.parametrize("order", TARGETS)
def test_both_independent_verifiers_accept(order: int) -> None:
    """The load-bearing gate. Two separate implementations, fresh processes."""

    path = TARGETS_DIR / f"TARGET_{order}.json"
    for checker, arguments in (
        ("verify.py", ["--expect-order", str(order), str(path)]),
        ("verify_darts.py", [str(path)]),
    ):
        completed = subprocess.run(
            [sys.executable, str(HERE / checker), *arguments],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, f"{checker} rejected order {order}: {completed.stdout}{completed.stderr}"


@pytest.mark.parametrize("order", TARGETS)
def test_the_profile_identities_hold_when_recomputed(order: int) -> None:
    """Recomputed here, not read out of a verifier's summary line."""

    degrees, alpha = certs.alpha_from_certificate(TARGETS_DIR / f"TARGET_{order}.json")
    assert len(degrees) == order
    counts = collections.Counter(degrees)
    assert set(counts) <= {3, 4, 5}
    r = counts[3]
    assert counts[5] == r - 4, "v5 = r - 4 failed"
    assert counts[4] == order - 2 * r + 4, "v4 = n - 2r + 4 failed"
    assert sum(degrees) == 2 * (2 * order - 2), "E = 2n - 2 failed"
    # Euler, from the reconstructed faces rather than from the profile.
    _, vertex_of, _, sigma_inverse = certs.cycles_from_degrees(degrees)
    phi = [sigma_inverse[alpha[d]] for d in range(len(alpha))]
    seen: dict[int, int] = {}
    faces = 0
    for dart in range(len(alpha)):
        if dart in seen:
            continue
        cursor = dart
        while cursor not in seen:
            seen[cursor] = faces
            cursor = phi[cursor]
        faces += 1
    assert faces == order, "F = n failed"
    assert order - (2 * order - 2) + faces == 2, "V - E + F = 2 failed"


def test_the_certificates_are_distinct_objects() -> None:
    digests = {
        order: hashlib.sha256((TARGETS_DIR / f"TARGET_{order}.json").read_bytes()).hexdigest()
        for order in TARGETS
    }
    assert len(set(digests.values())) == 26


@pytest.mark.parametrize("order", [46, 74, 110])
def test_a_tampered_certificate_is_rejected(order: int, tmp_path: Path) -> None:
    """A negative control: the gate must fail on a corrupted witness.

    Swapping two neighbours in one rotation keeps the graph and every degree
    but changes the embedding, so a passing verifier here would mean the
    facial conditions are not really being checked.
    """

    data = json.loads((TARGETS_DIR / f"TARGET_{order}.json").read_text())
    row = next(r for r in data["vertices"] if len(r["clockwise"]) >= 4)
    row["clockwise"][1], row["clockwise"][2] = row["clockwise"][2], row["clockwise"][1]
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    reports = certs.run_verifiers(tampered, order)
    accepted = [str(report["checker"]) for report in reports if report["passed"]]
    assert not accepted, f"tampered rotation accepted by: {', '.join(accepted)}"
    assert len(reports) == 2, "the control must exercise both verifiers"


def test_the_gate_runs_without_the_sat_dependency() -> None:
    """The gate must not need ``python-sat``, which README.md also promises.

    ``exact_map_cnf`` imports ``pysat`` at module scope, so importing it from
    here would make the load-bearing gate uncollectable on any checkout that
    has not installed the solver -- the gate would fail before either verifier
    ran.  The negative control is the block: with ``pysat`` made unimportable,
    this module and everything it uses must still import.
    """

    probe = """
import sys


class _NoPysat:
    def find_spec(self, name, path=None, target=None):
        if name == "pysat" or name.startswith("pysat."):
            raise ImportError("pysat is blocked by the gate self-check")
        return None


sys.meta_path.insert(0, _NoPysat())
sys.path.insert(0, %r)
import certificate_tools  # noqa: F401
import test_target_certificates  # noqa: F401
assert "pysat" not in sys.modules
print("clean")
""" % str(HERE)
    completed = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        check=False,
        cwd=HERE,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.strip().endswith("clean")

    # Importing is not running.  A runtime-only `pysat` import inside a
    # verifier would leave the check above green while the documented gate
    # fails, so the whole file is executed under the same block.
    run = subprocess.run(
        [sys.executable, "-c", RUN_GATE_UNDER_BLOCK % (str(HERE), str(TARGETS_DIR))],
        capture_output=True,
        text=True,
        check=False,
        cwd=HERE,
    )
    assert run.returncode == 0, run.stdout[-4000:] + run.stderr[-4000:]
    assert run.stdout.strip().endswith("gate ran")


RUN_GATE_UNDER_BLOCK = """
import sys


class _NoPysat:
    def find_spec(self, name, path=None, target=None):
        if name == "pysat" or name.startswith("pysat."):
            raise ImportError("pysat is blocked by the gate self-check")
        return None


sys.meta_path.insert(0, _NoPysat())
sys.path.insert(0, %r)

import collections
from pathlib import Path

import certificate_tools as certs
import fast_apg_check

for order in (46, 74, 110):
    path = Path(%r) / ("TARGET_" + str(order) + ".json")
    reports = certs.run_verifiers(path, order)
    assert len(reports) == 2, reports
    assert all(r["passed"] for r in reports), reports
    assert fast_apg_check.accepts_certificate(path)
    degrees, alpha = certs.alpha_from_certificate(path)
    counts = collections.Counter(degrees)
    assert len(degrees) == order
    assert counts[5] == counts[3] - 4
    assert counts[4] == order - 2 * counts[3] + 4
    assert sum(degrees) == 2 * (2 * order - 2)
assert "pysat" not in sys.modules
print("gate ran")
"""


@pytest.mark.parametrize("order", TARGETS)
def test_the_third_checker_accepts_every_target(order: int) -> None:
    """The handoff claims a third checker; run it here so the claim is a gate.

    `fast_apg_check` works on darts and a fixed-point-free involution rather
    than on the certificate's adjacency rows, and predates both verifiers.  It
    is a third *implementation*, not a third kind of evidence -- see
    `test_the_two_verifiers_are_not_independent_evidence`.
    """

    assert fast_apg_check.accepts_certificate(TARGETS_DIR / f"TARGET_{order}.json")


@pytest.mark.parametrize("order", [46, 74, 110])
def test_the_third_checker_rejects_a_tampered_certificate(order: int, tmp_path: Path) -> None:
    data = json.loads((TARGETS_DIR / f"TARGET_{order}.json").read_text())
    row = next(r for r in data["vertices"] if len(r["clockwise"]) >= 4)
    row["clockwise"][1], row["clockwise"][2] = row["clockwise"][2], row["clockwise"][1]
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    assert not fast_apg_check.accepts_certificate(tampered)


def _face_partition(rotation: dict, turn: int) -> set:
    darts = {(v, u) for v, ring in rotation.items() for u in ring}
    seen: set = set()
    faces = []
    for start in sorted(darts):
        if start in seen:
            continue
        dart = start
        walk = []
        while dart not in seen:
            seen.add(dart)
            walk.append(dart)
            u, v = dart
            ring = rotation[v]
            ring_index = ring.index(u)
            dart = (v, ring[(ring_index + turn) % len(ring)])
        faces.append(frozenset(walk))
    return set(faces)


@pytest.mark.parametrize("order", TARGETS)
def test_the_two_verifiers_are_not_independent_evidence(order: int) -> None:
    """State the relationship between the verifiers instead of assuming it.

    `verify.py` turns to the predecessor, `verify_darts.py` to the successor.
    That was recorded as evidence of independence; it is the opposite. The two
    traversals produce *the same face partition*, each face traced backwards
    relative to the other, so they cannot disagree about face sizes, face
    repetitions, or face adjacency on any input whatsoever.

    They are two implementations of one check: worth having against coding
    error, worthless against a shared misreading of Definition 2.1. Asserting
    the identity here keeps that honest -- and if a future change ever makes
    the two genuinely different, this test fails and says so.
    """

    data = json.loads((TARGETS_DIR / f"TARGET_{order}.json").read_text())
    rotation = {row["id"]: list(row["clockwise"]) for row in data["vertices"]}
    predecessor = _face_partition(rotation, -1)
    successor = _face_partition(rotation, +1)
    reversed_successor = {
        frozenset((v, u) for (u, v) in face) for face in successor
    }
    assert predecessor == reversed_successor
