from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import block_tools as bt
import frontier_anneal


ROOT = Path(__file__).resolve().parent
D24 = ROOT / "results/blocks/D24.json"
D24_PERTURBATION = (
    ROOT / "results/logs/score_breakdown_D24_positive_switch_seed0.json"
)
ORDER34_SEED = ROOT / "results/near_openings/order34_51_fans_8_32.json"
ORDER34_RADIUS3 = ROOT / "results/logs/order34_near_open_radius3.json"
CALIBRATION_BLOCK = ROOT / "results/calibration/frontier_anneal_D24_seed0.json"
CALIBRATION_LOG = ROOT / "results/logs/frontier_anneal_D24_seed0.json"


class FrontierAnnealTests(unittest.TestCase):
    def test_d24_calibration_input_replays_exactly(self) -> None:
        fixed, alpha, record = frontier_anneal.load_d24_calibration_state(
            D24, D24_PERTURBATION
        )
        self.assertEqual(len(fixed.cycles), 24)
        self.assertEqual(len(alpha), 84)
        self.assertEqual(
            record["base_file_sha256"],
            "9210f91150f77ec8e951a272816c3d4f736153fbbbfac0e707576e5aec1b6ab8",
        )
        self.assertEqual(
            record["perturbation_log_sha256"],
            "2c3c08f4b5dbb0b6e9aa3d2756acdee3bd70a72a7a59718212f1b571e7015eb3",
        )
        self.assertEqual(
            record["base_rotation_hash"],
            "fae4bc323d2f570b0dcc8aa47a17152abb466a1297d7ca1a2c75fb1743372cdc",
        )
        self.assertEqual(
            record["state_sha256"],
            "2847ed3d2d64043d6a126b312a751e8b578c21b2fa945a2ffb059b3888887033",
        )
        self.assertEqual(record["score_breakdown"]["total"], 820)
        self.assertFalse(record["abstract_graph_valid"])

    def test_committed_frontier_state_replays_without_target_annealing(self) -> None:
        fixed, alpha, record = frontier_anneal.load_frontier_state(
            ORDER34_SEED,
            ORDER34_RADIUS3,
            expected_seed_sha256=(
                "2d86c0b12ac046602516c435c319ef87efe98d6bac837546fb775f6fdf71178e"
            ),
            state_sha256=(
                "52525556412673bb467f5e916f910e790a005dedee76db3017c653149c562338"
            ),
        )
        self.assertEqual(len(fixed.cycles), 34)
        self.assertEqual(len(alpha), 124)
        self.assertEqual(record["score_breakdown"]["total"], 750)
        self.assertTrue(record["abstract_graph_valid"])

    def test_frontier_seed_and_state_hash_mismatches_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "seed file hash"):
            frontier_anneal.load_frontier_state(
                ORDER34_SEED,
                ORDER34_RADIUS3,
                expected_seed_sha256="0" * 64,
                state_sha256="52525556412673bb467f5e916f910e790a005dedee76db3017c653149c562338",
            )
        with self.assertRaisesRegex(ValueError, "exactly once"):
            frontier_anneal.load_frontier_state(
                ORDER34_SEED,
                ORDER34_RADIUS3,
                expected_seed_sha256=(
                    "2d86c0b12ac046602516c435c319ef87efe98d6bac837546fb775f6fdf71178e"
                ),
                state_sha256="0" * 64,
            )

    def test_corrupt_d24_alpha_hash_is_rejected(self) -> None:
        payload = json.loads(D24_PERTURBATION.read_text(encoding="utf-8"))
        payload["alpha_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "alpha hash"):
                frontier_anneal.load_d24_calibration_state(D24, path)

    def test_temperature_schedules_and_invalid_parameters(self) -> None:
        self.assertEqual(
            frontier_anneal.temperature_at(0, 1000, 200.0, 0.5, "geometric"),
            200.0,
        )
        self.assertAlmostEqual(
            frontier_anneal.temperature_at(999, 1000, 200.0, 0.5, "geometric"),
            0.5,
        )
        self.assertEqual(
            frontier_anneal.temperature_at(0, 1000, 200.0, 0.5, "linear"),
            200.0,
        )
        self.assertEqual(
            frontier_anneal.temperature_at(999, 1000, 200.0, 0.5, "linear"),
            0.5,
        )
        with self.assertRaises(ValueError):
            frontier_anneal.temperature_at(0, 0, 200.0, 0.5, "geometric")
        with self.assertRaises(ValueError):
            frontier_anneal.temperature_at(0, 10, 0.0, 0.5, "geometric")

    def test_graph_invalid_candidates_are_counted_and_rejected(self) -> None:
        fixed, alpha, _ = frontier_anneal.load_d24_calibration_state(
            D24, D24_PERTURBATION
        )
        with mock.patch(
            "frontier_anneal.map_search.switch_move", return_value=list(alpha)
        ):
            success, result, _ = frontier_anneal.anneal(
                fixed,
                alpha,
                seed=99,
                steps=3,
                temperature_start=10.0,
                temperature_end=1.0,
                schedule="linear",
            )
        self.assertIsNone(success)
        self.assertEqual(result["counts"]["move_attempts"], 3)
        self.assertEqual(result["counts"]["graph_invalid_rejections"], 3)
        self.assertEqual(result["counts"]["score_evaluations"], 0)
        self.assertEqual(result["counts"]["accepted_moves"], 0)

    def test_d24_recovery_is_deterministic_and_independently_verified(self) -> None:
        fixed, alpha, record = frontier_anneal.load_d24_calibration_state(
            D24, D24_PERTURBATION
        )
        runs = []
        for _ in range(2):
            success, result, _ = frontier_anneal.anneal(
                fixed,
                alpha,
                seed=0,
                steps=1000,
                temperature_start=200.0,
                temperature_end=0.5,
                schedule="geometric",
            )
            self.assertIsNotNone(success)
            result.pop("wall_seconds")
            runs.append(result)
        self.assertEqual(runs[0], runs[1])
        result = runs[0]
        self.assertEqual(result["recovery_step"], 1)
        self.assertEqual(result["counts"]["move_attempts"], 1)
        self.assertEqual(result["counts"]["accepted_moves"], 1)
        self.assertEqual(result["counts"]["accepted_improving"], 1)
        self.assertEqual(result["counts"]["zero_score_cross_validated"], 1)
        self.assertEqual(result["success_block_hash"], record["base_rotation_hash"])
        self.assertEqual(result["temperature"]["recovery"], 200.0)
        self.assertTrue(result["success_checks"]["block_tools_verified"])
        self.assertTrue(result["success_checks"]["blocks_verified"])
        block = bt.load_json(D24)
        self.assertEqual(result["best_state"]["score_breakdown"]["total"], 0)
        self.assertEqual(bt.canonical_map_hash(block), result["success_block_hash"])

    def test_committed_calibration_artifacts_replay_exact_result(self) -> None:
        log = json.loads(CALIBRATION_LOG.read_text(encoding="utf-8"))
        result = log["result"]
        self.assertEqual(log["input"]["score_breakdown"]["total"], 820)
        self.assertFalse(log["input"]["abstract_graph_valid"])
        self.assertEqual(result["seed"], 0)
        self.assertEqual(result["steps_requested"], 1000)
        self.assertEqual(result["steps_executed"], 1)
        self.assertEqual(result["recovery_step"], 1)
        self.assertEqual(result["counts"]["move_attempts"], 1)
        self.assertEqual(result["counts"]["accepted_moves"], 1)
        self.assertEqual(result["counts"]["accepted_improving"], 1)
        self.assertEqual(result["counts"]["graph_invalid_rejections"], 0)
        self.assertEqual(result["counts"]["zero_score_cross_validated"], 1)
        self.assertEqual(result["temperature"]["start"], 200.0)
        self.assertEqual(result["temperature"]["end"], 0.5)
        self.assertEqual(result["temperature"]["schedule"], "geometric")
        self.assertEqual(result["temperature"]["recovery"], 200.0)
        self.assertTrue(result["known_answer"]["exact_D24_recovered"])
        self.assertTrue(result["success_checks"]["block_tools_verified"])
        self.assertTrue(result["success_checks"]["blocks_verified"])
        recovered = bt.load_json(CALIBRATION_BLOCK)
        self.assertEqual(bt.canonical_map_hash(recovered), result["success_block_hash"])
        self.assertEqual(
            result["success_checks"]["block_tools_closed_sha256"],
            result["success_checks"]["blocks_closed_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
