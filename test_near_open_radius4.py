from __future__ import annotations

import json
import unittest
from pathlib import Path

import near_open_radius4


ROOT = Path(__file__).resolve().parent


class NearOpenRadius4Tests(unittest.TestCase):
    def test_all_64_parent_hashes_scores_and_exact_attempt_count(self) -> None:
        seed = json.loads(
            (ROOT / "results/near_openings/order26_27_fans_1_24.json").read_text(
                encoding="utf-8"
            )
        )
        k4_log = json.loads(
            (ROOT / "results/logs/order26_near_open_k4.json").read_text(
                encoding="utf-8"
            )
        )
        radius2_log = json.loads(
            (ROOT / "results/logs/order26_near_open_radius2.json").read_text(
                encoding="utf-8"
            )
        )
        radius3_log = json.loads(
            (ROOT / "results/logs/order26_near_open_radius3.json").read_text(
                encoding="utf-8"
            )
        )
        _, parents = near_open_radius4.load_radius3_frontier(
            seed, k4_log, radius2_log, radius3_log
        )
        self.assertEqual(len(parents), 64)
        self.assertEqual(
            near_open_radius4.parent_manifest_sha256(parents),
            near_open_radius4.EXPECTED_PARENT_MANIFEST_SHA256,
        )
        radius4_log = json.loads(
            (ROOT / "results/logs/order26_near_open_radius4.json").read_text(
                encoding="utf-8"
            )
        )
        result = radius4_log["result"]
        self.assertEqual(result["parent_state_hashes"], [
            parent["state_sha256"] for parent in parents
        ])
        self.assertEqual(result["counts"]["transition_attempts"], 132480)
        self.assertEqual(result["parent_states_expanded"], 64)
        self.assertTrue(result["complete"])


if __name__ == "__main__":
    unittest.main()
