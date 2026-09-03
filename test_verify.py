#!/usr/bin/env python3
"""Production-CLI tests for the independent (3,4,5)-APG verifier."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from conftest import requires_upstream_corpus


ROOT = Path(__file__).resolve().parent
VERIFY = ROOT / "verify.py"
IMPORTER = ROOT / "import_planar_code.py"
KNOWN = ROOT / "certificates" / "known"


def _load(name: str) -> dict[str, object]:
    return json.loads((KNOWN / name).read_text(encoding="utf-8"))


def _normalize(neighbors: list[int]) -> None:
    if not neighbors:
        return
    start = neighbors.index(min(neighbors))
    neighbors[:] = neighbors[start:] + neighbors[:start]


def _rows(certificate: dict[str, object]) -> dict[int, dict[str, object]]:
    return {row["id"]: row for row in certificate["vertices"]}  # type: ignore[index]


def _delete_edge(certificate: dict[str, object], u: int, v: int) -> None:
    rows = _rows(certificate)
    for a, b in ((u, v), (v, u)):
        neighbors = rows[a]["clockwise"]
        neighbors.remove(b)  # type: ignore[union-attr]
        _normalize(neighbors)  # type: ignore[arg-type]


def _flip_edge(
    source: dict[str, object],
    *,
    remove: tuple[int, int],
    add: tuple[int, int],
    insertion_positions: tuple[int, int],
) -> dict[str, object]:
    """Apply one deterministic embedded edge replacement used by negatives."""
    certificate = copy.deepcopy(source)
    _delete_edge(certificate, *remove)
    rows = _rows(certificate)
    for a, b, position in (
        (add[0], add[1], insertion_positions[0]),
        (add[1], add[0], insertion_positions[1]),
    ):
        neighbors = rows[a]["clockwise"]
        neighbors.insert(position, b)  # type: ignore[union-attr]
        _normalize(neighbors)  # type: ignore[arg-type]
    return certificate


class VerifierCliTests(unittest.TestCase):
    maxDiff = None

    def _run_data(
        self, certificate: object, *, expected_order: int | None = None
    ) -> subprocess.CompletedProcess[str]:
        return self._run_text(json.dumps(certificate), expected_order=expected_order)

    def _run_text(
        self, certificate_text: str, *, expected_order: int | None = None
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="apg-verifier-test-") as temp_dir:
            path = Path(temp_dir) / "certificate.json"
            path.write_text(certificate_text, encoding="utf-8")
            command = [sys.executable, str(VERIFY), str(path)]
            if expected_order is not None:
                command.extend(["--expect-order", str(expected_order)])
            return subprocess.run(command, text=True, capture_output=True, check=False)

    def _assert_rejected(self, certificate: object, message: str) -> None:
        result = self._run_data(certificate)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL", result.stderr)
        self.assertIn(message, result.stderr)

    def test_published_positive_controls_through_cli(self) -> None:
        controls = {
            "schneider17.json": 17,
            "ghent17.json": 17,
            "order20.json": 20,
            "order42.json": 42,
        }
        for name, order in controls.items():
            with self.subTest(name=name):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(VERIFY),
                        str(KNOWN / name),
                        "--expect-order",
                        str(order),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(f"PASS {KNOWN / name}: order={order}", result.stdout)
                self.assertEqual(result.stderr, "")

    @requires_upstream_corpus
    def test_published_planar_code_import_is_reproducible(self) -> None:
        pairs = {
            "01_17-17_schneider17.plc": "schneider17.json",
            "02_17-17_ghent17.plc": "ghent17.json",
            "08_20-20.plc": "order20.json",
            "86_42-42.plc": "order42.json",
        }
        with tempfile.TemporaryDirectory(prefix="apg-import-test-") as temp_dir:
            for source_name, json_name in pairs.items():
                with self.subTest(source=source_name):
                    output = Path(temp_dir) / json_name
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(IMPORTER),
                            str(KNOWN / "upstream" / source_name),
                            str(output),
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertEqual(output.read_bytes(), (KNOWN / json_name).read_bytes())

    def test_requires_integer_normalized_labels(self) -> None:
        certificate = _load("schneider17.json")
        certificate["vertices"][0]["id"] = True  # type: ignore[index]
        self._assert_rejected(certificate, "must be an integer (not boolean)")

        certificate = _load("schneider17.json")
        certificate["vertices"][0]["clockwise"][0] = "2"  # type: ignore[index]
        self._assert_rejected(certificate, "entries must be integer labels")

        certificate = _load("schneider17.json")
        neighbors = certificate["vertices"][0]["clockwise"]  # type: ignore[index]
        neighbors[:] = neighbors[1:] + neighbors[:1]
        self._assert_rejected(certificate, "rotation is not normalized")

    def test_rejects_loops_parallel_edges_and_asymmetry(self) -> None:
        certificate = _load("schneider17.json")
        row = certificate["vertices"][0]  # type: ignore[index]
        row["clockwise"].append(row["id"])
        _normalize(row["clockwise"])
        self._assert_rejected(certificate, "has a loop")

        certificate = _load("schneider17.json")
        row = certificate["vertices"][0]  # type: ignore[index]
        row["clockwise"].append(row["clockwise"][0])
        self._assert_rejected(certificate, "repeated neighbor (parallel edge)")

        certificate = _load("schneider17.json")
        rows = _rows(certificate)
        rows[1]["clockwise"].remove(2)  # type: ignore[union-attr]
        _normalize(rows[1]["clockwise"])  # type: ignore[arg-type]
        self._assert_rejected(certificate, "edge 2-1 is not symmetric")

    def test_rejects_disconnected_union(self) -> None:
        first = _load("schneider17.json")
        second = _load("ghent17.json")
        offset = 17
        shifted = []
        for original in second["vertices"]:  # type: ignore[index]
            shifted.append(
                {
                    "id": original["id"] + offset,
                    "clockwise": [neighbor + offset for neighbor in original["clockwise"]],
                }
            )
        first["vertices"].extend(shifted)  # type: ignore[union-attr]
        self._assert_rejected(first, "graph is disconnected")

    def test_rejects_forbidden_vertex_degree(self) -> None:
        certificate = _load("schneider17.json")
        _delete_edge(certificate, 1, 2)
        self._assert_rejected(certificate, "forbidden degree 2")

    def test_rejects_nonspherical_rotation(self) -> None:
        certificate = _load("order20.json")
        neighbors = certificate["vertices"][0]["clockwise"]  # type: ignore[index]
        neighbors[1], neighbors[2] = neighbors[2], neighbors[1]
        self._assert_rejected(certificate, "rotation system is not a sphere embedding")

    def test_rejects_forbidden_face_size(self) -> None:
        # Embedded replacement 9-10 -> 9-11 merges/splits the two incident
        # regions so one reconstructed face has size 6; all degrees remain 3/4/5.
        certificate = _flip_edge(
            _load("order20.json"),
            remove=(9, 10),
            add=(9, 11),
            insertion_positions=(1, 0),
        )
        self._assert_rejected(certificate, "forbidden size 6")

    def test_rejects_equal_sized_adjacent_faces(self) -> None:
        # This embedded replacement keeps every face size in {3,4,5} but makes
        # an edge separate two quadrilateral faces.
        certificate = _flip_edge(
            _load("order20.json"),
            remove=(1, 3),
            add=(3, 19),
            insertion_positions=(1, 0),
        )
        self._assert_rejected(certificate, "separates two faces of size 4")

    def test_rejects_equal_degree_adjacent_vertices(self) -> None:
        # This embedded replacement passes every topology and face gate but
        # leaves adjacent vertices 1 and 2 both of degree 4.
        certificate = _flip_edge(
            _load("order20.json"),
            remove=(2, 3),
            add=(3, 15),
            insertion_positions=(0, 1),
        )
        self._assert_rejected(certificate, "adjacent vertices 1 and 2 both have degree 4")

    def test_expected_order_is_an_independent_gate(self) -> None:
        result = self._run_data(_load("order20.json"), expected_order=21)
        self.assertEqual(result.returncode, 1)
        self.assertIn("order 20 does not equal expected order 21", result.stderr)

    def test_rejects_duplicate_json_members(self) -> None:
        encoded = (KNOWN / "order20.json").read_text(encoding="utf-8")
        needle = '  "format": "apg-plane-rotation-v1",'
        self.assertEqual(encoded.count(needle), 1)
        result = self._run_text(
            encoded.replace(
                needle,
                '  "format": "ambiguous",\n  "format": "apg-plane-rotation-v1",',
                1,
            )
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("duplicate JSON object key", result.stderr)


if __name__ == "__main__":
    unittest.main()
