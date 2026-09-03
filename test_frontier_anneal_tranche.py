from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import frontier_anneal
import frontier_anneal_tranche as tranche


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "jobs/order26_frontier_anneal_tranche01.json"
RESULT_PATH = ROOT / "results/logs/order26_frontier_anneal_tranche01.json"
LANE_DIRECTORY = ROOT / "results/frontier_anneal/order26_tranche01"
EXPECTED_STATES = [
    "5ea1cc9a0cce8ff69386b3bd0fe623d3efaa8fcdc429319474c9ab67297f1bc4",
    "a5522bf00ed7e9730583405e6fa72d62ec1fceb9a67638feed413fc9e6fd15f1",
    "d337ec944b935bb8f473e35269907cbb2413b9fa4488754df52372b9d6ebab4a",
    "e91984c9ca36143cfb7c128d56bdf7116e6c2d735b69e702b76c6c1fa9e066a8",
    "ee24f1a2e77f4fadba9904102a91d1670669e1ccaa55693e4fffa69eab652ced",
    "f47b7c1a84035d3c674dd54575c914dc3f39574251a3439d697d8a71328bac0e",
]
EXPECTED_RESULT_LANES = [
    ("state00-cool", 926, 492, 529, 1947, 166382, 83618, 81671, 830, "bc2c8c0c3225277e09271c71e4596135516ce7e5bb0be8034f999160b82aa7ed"),
    ("state00-hot", 1376, 2291, 2271, 5938, 167471, 82529, 76591, 1330, "6cba3ceceabe7c3367e5233adcf877c9a22f667d368db57cf65148f28eb207a4"),
    ("state01-cool", 941, 609, 603, 2153, 166692, 83308, 81155, 980, "da1ed502a72215177d3e12f912fbfcd89f7b22bad5707233b3e2444e91cc340f"),
    ("state01-hot", 1184, 2134, 2144, 5462, 166842, 83158, 77696, 870, "09471561825c6a44012f4028de70ce73d026bf6726eb77c3980a21ddd3c1bd83"),
    ("state02-cool", 1105, 728, 734, 2567, 167353, 82647, 80080, 1210, "32e1b49e174bd03ea3bc88bfed2656883c79a357a86b6ce9e06f475d6e607fd9"),
    ("state02-hot", 1164, 2167, 2169, 5500, 166753, 83247, 77747, 1060, "18e54ff894aad3d79150a52dcff6786daf667b0c4ce9b905a7ddef93ca2e8030"),
    ("state03-cool", 1189, 840, 802, 2831, 166491, 83509, 80678, 550, "8e4a373d56eebaec1c9ece2d0229067e36045a33f233c90b422afa3c21ae733c"),
    ("state03-hot", 1254, 2121, 2129, 5504, 166643, 83357, 77853, 1280, "c40562f5c7fc085435efd84f6e5b483264d52538c12c52913fbd5e330b736498"),
    ("state04-cool", 1162, 1091, 1058, 3311, 165160, 84840, 81529, 1060, "723c72fcaf399f209d7024f4a18b65c6cf137f7ac391965fa9951bfabbef700e"),
    ("state04-hot", 1271, 2154, 2114, 5539, 167137, 82863, 77324, 920, "afe2f915ac3d6071bcdf57f4e11d2a3953722bad16d5897ce20e61aa1a623f53"),
    ("state05-cool", 1048, 812, 772, 2632, 166114, 83886, 81254, 870, "d2d9520e03b84a362be44b5777c76ef07d264241ace4b8479765f27c18733d11"),
    ("state05-hot", 1172, 2146, 2102, 5420, 166196, 83804, 78384, 1220, "2d508e8dd17a078e395024dcc96b662fb43d8f97adcd987a62a0aa0c60320268"),
]


def fake_result(score: int, state_hash: str, *, success: bool = False) -> dict:
    counts = {name: 0 for name in tranche.COUNTER_NAMES}
    counts.update(
        {
            "move_attempts": 10,
            "graph_invalid_rejections": 2,
            "graph_valid_candidates": 8,
            "score_evaluations": 8,
            "accepted_moves": 5,
            "accepted_improving": 2,
            "accepted_equal": 1,
            "accepted_worsening": 2,
            "metropolis_rejections": 3,
            "zero_score_candidates": int(success),
            "zero_score_cross_validated": int(success),
        }
    )
    state = {
        "state_sha256": state_hash,
        "score_breakdown": {"total": score},
        "alpha": [],
        "rotation": [],
    }
    return {
        "steps_requested": 10,
        "steps_executed": 10,
        "temperature": {
            "schedule": "geometric",
            "start": 200.0,
            "end": 0.5,
            "first_effective": 200.0,
            "last_configured": 0.5,
            "recovery": 200.0 if success else None,
        },
        "counts": counts,
        "best_state": state,
        "current_state": state,
        "success": success,
        "success_block_hash": "f" * 64 if success else None,
        "wall_seconds": 1.25,
    }


class FrontierAnnealTrancheTests(unittest.TestCase):
    def test_spec_hash_jobs_seeds_temperatures_and_budget_are_frozen(self) -> None:
        self.assertEqual(
            hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest(),
            "ce515999a867e24b51508dfd5f1661dbd514d9ad4def75857e221295a1aac385",
        )
        spec = tranche.load_spec(SPEC_PATH)
        jobs = spec["jobs"]
        self.assertEqual(len(jobs), 12)
        self.assertEqual(len({job["job_id"] for job in jobs}), 12)
        self.assertEqual(sum(job["steps"] for job in jobs), 3_000_000)
        self.assertEqual(spec["total_requested_steps"], 3_000_000)
        for index, state_hash in enumerate(EXPECTED_STATES):
            pair = jobs[2 * index : 2 * index + 2]
            self.assertEqual([job["state_sha256"] for job in pair], [state_hash] * 2)
            self.assertEqual([job["lane"] for job in pair], ["cool", "hot"])
            self.assertEqual([job["rng_seed"] for job in pair], [2600 + index, 3600 + index])
            self.assertEqual([job["steps"] for job in pair], [250_000, 250_000])
            self.assertEqual([job["schedule"] for job in pair], ["geometric"] * 2)
            self.assertEqual(
                [(job["temperature_start"], job["temperature_end"]) for job in pair],
                [(200.0, 0.5), (800.0, 2.0)],
            )

    def test_all_six_exact_frontier_states_replay_at_score_470(self) -> None:
        spec = tranche.load_spec(SPEC_PATH)
        replayed = tranche.replay_jobs(spec, ROOT)
        self.assertEqual(len(replayed), 12)
        self.assertEqual(
            [replayed[2 * index]["job"]["state_sha256"] for index in range(6)],
            EXPECTED_STATES,
        )
        for item in replayed:
            self.assertEqual(item["input"]["score_breakdown"]["total"], 470)
            self.assertTrue(item["input"]["abstract_graph_valid"])

    def test_missing_parameter_or_wrong_total_is_rejected(self) -> None:
        original = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
        cases = []
        missing = copy.deepcopy(original)
        del missing["jobs"][0]["temperature_end"]
        cases.append(missing)
        wrong_total = copy.deepcopy(original)
        wrong_total["jobs"][0]["steps"] -= 1
        cases.append(wrong_total)
        with tempfile.TemporaryDirectory() as directory:
            for index, payload in enumerate(cases):
                path = Path(directory) / f"bad-{index}.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(ValueError):
                    tranche.load_spec(path)

    def test_aggregate_is_deterministic_and_no_witness_is_bounded(self) -> None:
        spec = tranche.load_spec(SPEC_PATH)
        lanes = []
        for index, job in enumerate(spec["jobs"]):
            lanes.append(
                {
                    "job": job,
                    "result": fake_result(420 if index < 2 else 430, f"{index:064x}"),
                }
            )
        first = tranche.aggregate_results(spec, lanes)
        second = tranche.aggregate_results(spec, copy.deepcopy(lanes))
        self.assertEqual(first, second)
        self.assertTrue(first["complete"])
        self.assertFalse(first["stopped_early_for_success"])
        self.assertFalse(first["success"])
        self.assertEqual(first["jobs_completed"], 12)
        self.assertEqual(first["total_steps_executed"], 120)
        self.assertEqual(first["counts"]["accepted_moves"], 60)
        self.assertEqual(first["best_score_histogram"], {"420": 2, "430": 10})
        self.assertEqual(first["global_minimum_score"], 420)
        self.assertEqual(len(first["global_best_states"]), 2)
        self.assertIn("not nonexistence", first["bounded_claim"])

    def test_aggregate_marks_early_cross_validated_success(self) -> None:
        spec = tranche.load_spec(SPEC_PATH)
        lanes = [{"job": spec["jobs"][0], "result": fake_result(0, "a" * 64, success=True)}]
        result = tranche.aggregate_results(spec, lanes)
        self.assertTrue(result["complete"])
        self.assertTrue(result["stopped_early_for_success"])
        self.assertTrue(result["success"])
        self.assertEqual(result["jobs_completed"], 1)
        self.assertEqual(result["counts"]["zero_score_cross_validated"], 1)

    def test_target_path_smoke_traverses_equal_and_worsening_moves(self) -> None:
        spec = tranche.load_spec(SPEC_PATH)
        replay = tranche.replay_jobs(spec, ROOT)[0]
        success, result, _ = frontier_anneal.anneal(
            replay["fixed"],
            replay["alpha"],
            seed=0,
            steps=200,
            temperature_start=1_000_000.0,
            temperature_end=1_000_000.0,
            schedule="geometric",
        )
        self.assertIsNone(success)
        counts = result["counts"]
        self.assertEqual(counts["move_attempts"], 200)
        self.assertEqual(counts["graph_valid_candidates"], 59)
        self.assertEqual(counts["score_evaluations"], 59)
        self.assertEqual(counts["accepted_equal"], 3)
        self.assertEqual(counts["accepted_worsening"], 34)
        self.assertEqual(counts["accepted_moves"], 58)

    def test_committed_tranche_aggregate_and_lane_results_are_frozen(self) -> None:
        payload = json.loads(RESULT_PATH.read_text(encoding="utf-8"))
        result = payload["result"]
        self.assertEqual(
            payload["spec_sha256"],
            "ce515999a867e24b51508dfd5f1661dbd514d9ad4def75857e221295a1aac385",
        )
        self.assertEqual(payload["environment"]["uname"]["system"], "Linux")
        self.assertEqual(result["jobs_requested"], 12)
        self.assertEqual(result["jobs_completed"], 12)
        self.assertEqual(result["total_steps_requested"], 3_000_000)
        self.assertEqual(result["total_steps_executed"], 3_000_000)
        self.assertFalse(result["success"])
        self.assertFalse(result["stopped_early_for_success"])
        self.assertEqual(result["global_minimum_score"], 470)
        self.assertEqual(result["best_score_histogram"], {"470": 12})
        self.assertEqual(
            result["counts"],
            {
                "accepted_equal": 13792,
                "accepted_improving": 17585,
                "accepted_moves": 48804,
                "accepted_worsening": 17427,
                "best_improvements": 0,
                "graph_invalid_rejections": 1999234,
                "graph_valid_candidates": 1000766,
                "metropolis_rejections": 951962,
                "move_attempts": 3000000,
                "score_evaluations": 1000766,
                "zero_score_block_tools_rejections": 0,
                "zero_score_blocks_rejections": 0,
                "zero_score_candidates": 0,
                "zero_score_cross_validated": 0,
                "zero_score_validation_rejections": 0,
            },
        )
        self.assertEqual(
            [state["state_sha256"] for state in result["global_best_states"]],
            EXPECTED_STATES,
        )
        for state in result["global_best_states"]:
            self.assertEqual(state["score_breakdown"]["total"], 470)

        manifest = result["lane_manifest"]
        self.assertEqual(len(manifest), 12)
        for index, expected in enumerate(EXPECTED_RESULT_LANES):
            (
                job_id,
                accepted_equal,
                accepted_improving,
                accepted_worsening,
                accepted_moves,
                graph_invalid,
                graph_valid,
                metropolis,
                current_score,
                current_hash,
            ) = expected
            lane = manifest[index]
            counts = lane["counts"]
            self.assertEqual(lane["job_id"], job_id)
            self.assertEqual(lane["steps_executed"], 250_000)
            self.assertEqual(lane["best_score"], 470)
            self.assertEqual(lane["best_state_sha256"], EXPECTED_STATES[index // 2])
            self.assertEqual(lane["current_score"], current_score)
            self.assertEqual(lane["current_state_sha256"], current_hash)
            self.assertEqual(counts["accepted_equal"], accepted_equal)
            self.assertEqual(counts["accepted_improving"], accepted_improving)
            self.assertEqual(counts["accepted_worsening"], accepted_worsening)
            self.assertEqual(counts["accepted_moves"], accepted_moves)
            self.assertEqual(counts["graph_invalid_rejections"], graph_invalid)
            self.assertEqual(counts["graph_valid_candidates"], graph_valid)
            self.assertEqual(counts["metropolis_rejections"], metropolis)
            self.assertEqual(counts["zero_score_candidates"], 0)
            lane_log = json.loads(
                (LANE_DIRECTORY / f"{job_id}.json").read_text(encoding="utf-8")
            )
            self.assertEqual(lane_log["job"]["job_id"], job_id)
            self.assertEqual(lane_log["input"]["state_sha256"], EXPECTED_STATES[index // 2])
            self.assertEqual(lane_log["input"]["score_breakdown"]["total"], 470)
            self.assertEqual(lane_log["result"]["counts"], counts)
            self.assertEqual(lane_log["result"]["best_state"], result["global_best_states"][index // 2])


if __name__ == "__main__":
    unittest.main()
