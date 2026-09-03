from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import block_tools as bt
import map_search
import topology_semantics_audit as audit


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results/logs/historical_near_open_topology_audit.json"

EXPECTED = {
    "order26_near_open_k4": ({"-2": 59, "0": 5}, {"0": 1}),
    "order26_near_open_radius2": ({"-2": 29, "0": 35}, {"0": 1}),
    "order26_near_open_radius3": ({"-2": 2, "0": 62}, {"0": 2}),
    "order26_near_open_radius4": ({"-2": 19, "0": 45}, {"0": 1}),
    "order26_near_open_radius5": ({"0": 64}, {"0": 6}),
    "order26_dual_near_open_k4": ({"-2": 61, "0": 3}, {"0": 1}),
    "order26_dual_near_open_radius2": ({"-2": 21, "0": 43}, {"0": 1}),
    "order26_dual_near_open_radius3": ({"-2": 8, "0": 56}, {"0": 8}),
    "order30_near_open_k4": ({"-2": 63, "0": 1}, {"0": 1}),
    "order30_near_open_radius2": ({"-2": 46, "0": 18}, {"0": 1}),
    "order30_near_open_radius3": ({"0": 64}, {"0": 2}),
    "order33_near_open_k4": ({"-2": 61, "0": 3}, {"0": 1}),
    "order33_near_open_radius2": ({"-2": 38, "0": 26}, {"0": 7}),
    "order34_near_open_k4": ({"-2": 64}, {"-2": 2}),
    "order34_near_open_radius2": ({"-2": 63, "0": 1}, {"-2": 1}),
    "order34_near_open_radius3": ({"-2": 63, "0": 1}, {"-2": 3}),
}


class TopologySemanticsAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = json.loads(RESULT.read_text(encoding="utf-8"))

    def records(self) -> dict[str, dict[str, object]]:
        return {
            Path(record["path"]).stem: record
            for family in self.result["families"].values()
            for record in family["files"]
        }

    def test_committed_audit_rebuilds_exactly(self) -> None:
        self.assertEqual(audit.build_audit(ROOT), self.result)
        self.assertEqual(self.result["file_count"], 16)
        self.assertEqual(self.result["frontier_state_count"], 16 * 64)

    def test_every_hash_score_abstract_gate_and_chi_histogram_are_frozen(self) -> None:
        records = self.records()
        self.assertEqual(set(records), set(EXPECTED))
        for name, (chi, minimum_chi) in EXPECTED.items():
            record = records[name]
            self.assertEqual(record["frontier_count"], 64)
            self.assertEqual(record["chi_histogram"], chi)
            self.assertEqual(record["minimum_score_chi_histogram"], minimum_chi)
            self.assertEqual(record["plane_valid_count"], 0)
            self.assertTrue(all(state["abstract_valid"] for state in record["states"]))
            self.assertTrue(all(not state["plane_valid"] for state in record["states"]))
            self.assertTrue(all(state["euler_characteristic"] != 2 for state in record["states"]))

    def test_dispatcher_key_histograms_are_exact(self) -> None:
        records = self.records()
        self.assertEqual(records["order30_near_open_radius3"]["chi_histogram"], {"0": 64})
        self.assertEqual(records["order33_near_open_radius2"]["chi_histogram"], {"-2": 38, "0": 26})
        self.assertEqual(records["order34_near_open_radius3"]["chi_histogram"], {"-2": 63, "0": 1})

    def test_fixed_rotations_and_source_logs_are_byte_frozen(self) -> None:
        for family in self.result["families"].values():
            base = ROOT / family["base_log"]
            self.assertEqual(audit.file_sha256(base), family["base_log_sha256"])
            rotation = bt._rotation_from_rows(family["fixed_rotation"])
            fixed, alpha = map_search.rotation_to_map(rotation)
            self.assertEqual(len(fixed.cycles), len(family["fixed_rotation"]))
            self.assertEqual(__import__("near_opening")._state_sha256(alpha), family["base_alpha_sha256"])

    def test_hash_or_score_drift_is_rejected(self) -> None:
        family = self.result["families"]["order26_near_open"]
        fixed, _ = map_search.rotation_to_map(bt._rotation_from_rows(family["fixed_rotation"]))
        source = json.loads((ROOT / family["base_log"]).read_text(encoding="utf-8"))["result"]["frontier_states"][0]
        for field in ("alpha", "breakdown"):
            changed = copy.deepcopy(source)
            if field == "alpha":
                changed["alpha"][0], changed["alpha"][1] = changed["alpha"][1], changed["alpha"][0]
            else:
                changed["breakdown"]["total"] += 1
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit.audit_state(fixed, changed, 0)


if __name__ == "__main__":
    unittest.main()
