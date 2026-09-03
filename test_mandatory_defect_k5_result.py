from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import mandatory_defect_k5 as target


ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "jobs/mandatory_defect_26_29_33_k5.json"
STATE = ROOT / "results/targets/mandatory_defect_26_29_33_k5.json"
RESULT = ROOT / "results/logs/mandatory_defect_26_29_33_k5_result.json"
RESULT_SHA = "393f4493bc8e18afd1af053e030d9aff58d69ee62d0364492d915cd787710e27"

PER_SEED = {
    "26a": (13_244, 7_204_736, 7_179_714, 25_021, 1),
    "26b": (13_244, 7_204_736, 7_179_726, 25_008, 2),
    "29a": (19_600, 10_662_400, 10_616_998, 45_402, 0),
    "29b": (19_600, 10_662_400, 10_622_889, 39_510, 1),
    "33": (30_856, 16_785_664, 16_726_060, 59_604, 0),
}

FRONTIER = [
    (760, "26b", "cfb1ed2569a86f70b3727914cb323a658d02b0c8be743bd401c4ecbfa2fef7e0"),
    (780, "26b", "68d8473b3da57db5d07155d2a468731d8cfbafbbd8376cbc8fe657132f6a5554"),
    (800, "26a", "137111b13b71eaaf73783e418320d79d62e448ee547d4d95c5c2fce11a23d459"),
    (1620, "29b", "442d60134fbe5bd2fc2da81ceec4b65ebfe4c5ea44aa7cf3abd062ed0dc82840"),
]


class MandatoryDefectK5ResultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = target.load_spec(SPEC)
        self.record = json.loads(RESULT.read_text(encoding="utf-8"))
        self.payload = json.loads(STATE.read_text(encoding="utf-8"))

    def test_result_bytes_and_complete_global_accounting_are_frozen(self) -> None:
        self.assertEqual(target.file_sha256(RESULT), RESULT_SHA)
        result = self.record["result"]
        self.assertEqual(result["expected_selections"], 96_544)
        self.assertEqual(result["expected_attempts"], 52_519_936)
        self.assertEqual(result["matchings_per_selection"], 544)
        self.assertEqual(result["counts"], {
            "abstract_graph_prunes": 52_325_387,
            "attempts": 52_519_936,
            "distinct_plane_valid": 4,
            "global_duplicates": 0,
            "graph_invalid_prunes": 52_519_932,
            "nonspherical_prunes": 194_545,
            "per_seed_duplicates": 0,
            "raw_plane_valid": 4,
            "score_zero": 0,
            "selections": 96_544,
            "zero_score_block_tools_rejections": 0,
            "zero_score_blocks_rejections": 0,
            "zero_score_cross_validated": 0,
            "zero_score_validation_rejections": 0,
        })

    def test_per_seed_counts_histogram_and_frontier_are_frozen(self) -> None:
        result = self.record["result"]
        for item in result["per_seed"]:
            selections, attempts, abstract, nonspherical, plane = PER_SEED[item["id"]]
            counts = item["counts"]
            self.assertEqual(counts["selections"], selections)
            self.assertEqual(counts["attempts"], attempts)
            self.assertEqual(counts["abstract_graph_prunes"], abstract)
            self.assertEqual(counts["nonspherical_prunes"], nonspherical)
            self.assertEqual(counts["raw_plane_valid"], plane)
            self.assertEqual(counts["distinct_plane_valid"], plane)
            self.assertEqual(counts["graph_invalid_prunes"], attempts - plane)
        self.assertEqual(result["score_histogram_distinct"], {
            "760": 1, "780": 1, "800": 1, "1620": 1,
        })
        actual = [
            (state["breakdown"]["total"], state["seed_id"], state["state_sha256"])
            for state in result["frontier_states"]
        ]
        self.assertEqual(actual, FRONTIER)
        self.assertEqual(result["frontier_state_count"], 4)
        self.assertFalse(result["frontier_truncated"])
        self.assertEqual(result["best_score"], 760)
        self.assertEqual(result["best_state_hashes"], [FRONTIER[0][2]])

    def test_result_replays_every_frontier_and_certificate_gate(self) -> None:
        target.validate_result_record(self.spec, self.record, ROOT)
        self.assertEqual(self.record["result"]["success_hashes"], [])
        self.assertEqual(self.record["result"]["success_checks"], {})
        self.assertEqual(self.record["certificates"], {})

    def test_counter_histogram_frontier_and_certificate_drift_are_rejected(self) -> None:
        for mutation in ("counter", "histogram", "frontier", "certificate"):
            changed = copy.deepcopy(self.record)
            if mutation == "counter":
                changed["result"]["counts"]["abstract_graph_prunes"] -= 1
            elif mutation == "histogram":
                changed["result"]["score_histogram_distinct"]["760"] = 2
            elif mutation == "frontier":
                changed["result"]["frontier_states"][0]["breakdown"]["white"] += 1
            else:
                changed["certificates"]["0" * 64] = {"path": "missing", "sha256": "0" * 64}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                target.validate_result_record(self.spec, changed, ROOT)


if __name__ == "__main__":
    unittest.main()
