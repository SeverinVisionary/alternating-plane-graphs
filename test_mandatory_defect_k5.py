from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

import mandatory_defect_k5 as target
import near_opening
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "jobs/mandatory_defect_26_29_33_k5.json"
STATE = ROOT / "results/targets/mandatory_defect_26_29_33_k5.json"
STAGE = ROOT / "results/logs/mandatory_defect_26_29_33_k5_stage.json"
SPEC_SHA = "a18ea38665b2dc6c4b66d1e50f9644bcaa535eb4a678164e37161da82d68c0c4"
TARGET_SHA = "2ac057daf35896a46711ef4d8b6a5fc10720d885fd08fd59289da6cf862ad28b"
TARGET_MANIFEST = "a7d3190ce26764995c6080a9b7dd28d1a27f10864570549b1fbba069a3f8d50e"
RADIUS4 = ROOT / "results/logs/order26_three_edge_spherical_radius4.json"
GENUS_ONE = ROOT / "results/logs/order26_near_open_radius5.json"
CALIBRATION_LOG = ROOT / "results/logs/D24_five_edge_calibration.json"
CALIBRATION_CERTIFICATE = ROOT / "results/calibration/D24_five_edge_recovered.json"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class MandatoryDefectK5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = target.load_spec(SPEC)
        self.payload = json.loads(STATE.read_text(encoding="utf-8"))

    def write_spec(self, value: dict[str, object]) -> Path:
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "spec.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def complete_result_fixture(self) -> dict[str, object]:
        """Use a real plane-valid state from the exact order-26 fixed map."""

        source = json.loads(RADIUS4.read_text(encoding="utf-8"))["result"]["frontier_states"][0]
        state = copy.deepcopy(source)
        parent = self.payload["parents"][0]
        state.update(
            seed_id="26a",
            fixed_rotation_hash=parent["fixed_rotation_hash"],
            state_namespace=target.state_namespace("26a", parent["fixed_rotation_hash"], state["alpha"]),
        )
        per_seed = []
        global_counts: Counter[str] = Counter()
        for index, staged in enumerate(self.payload["parents"]):
            raw = 1 if index == 0 else 0
            counts = {
                "abstract_graph_prunes": staged["attempts"] - raw,
                "attempts": staged["attempts"],
                "distinct_plane_valid": raw,
                "graph_invalid_prunes": staged["attempts"] - raw,
                "raw_plane_valid": raw,
                "selections": staged["selections"],
            }
            for name in target.RESULT_COUNTER_NAMES:
                counts.setdefault(name, 0)
            per_seed.append({"id": staged["id"], "counts": counts})
            global_counts.update(counts)
        return {
            "complete": True,
            "expected_selections": 96_544,
            "matchings_per_selection": 544,
            "expected_attempts": 52_519_936,
            "counts": dict(global_counts),
            "per_seed": per_seed,
            "score_histogram_distinct": {"510": 1},
            "frontier_limit": 64,
            "frontier_states": [state],
            "frontier_state_count": 1,
            "frontier_truncated": False,
            "best_score": 510,
            "best_state_hashes": [state["state_sha256"]],
            "success_hashes": [],
            "success_checks": {},
        }

    def test_target_bytes_manifests_and_exact_budgets_are_frozen(self) -> None:
        self.assertEqual(target.file_sha256(SPEC), SPEC_SHA)
        self.assertEqual(target.file_sha256(STATE), TARGET_SHA)
        self.assertEqual(self.spec["target_manifest_sha256"], TARGET_MANIFEST)
        self.assertEqual(self.payload["target_manifest_sha256"], TARGET_MANIFEST)
        self.assertEqual(self.spec["parent_manifest_sha256"], "fd975d8752589565d7c8a7a7d69b8c4d8f55f5f76b9b2b706d6a7d4c2536149a")
        self.assertEqual(self.spec["total_selections"], 96_544)
        self.assertEqual(self.spec["total_attempts"], 52_519_936)

    def test_all_sources_parents_defects_and_full_auxiliary_sets_replay(self) -> None:
        loaded = target.validate_target_state(self.spec, self.payload)
        expected = [("26a",44,13244,7204736),("26b",44,13244,7204736),("29a",50,19600,10662400),("29b",50,19600,10662400),("33",58,30856,16785664)]
        self.assertEqual([(p["id"],p["auxiliary_edge_count"],p["selections"],p["attempts"]) for p in self.payload["parents"]], expected)
        for (fixed, alpha, parent), staged in zip(loaded, self.payload["parents"]):
            mandatory = {tuple(item["dart_pair"]) for item in parent["mandatory_defects"]}
            self.assertEqual(set(map(tuple, staged["auxiliary_edges"])), set(k3.edge_pairs(alpha)) - mandatory)
            self.assertEqual(k3.euler_characteristic(fixed, alpha), 2)

    def test_stage_executes_zero_target_rematchings(self) -> None:
        """``stage`` writes into the tree, so the writes are mocked here.

        Without the mock this test rewrites the committed cloud-run artifacts
        in place with this host's `platform.node()` and `platform.uname()`,
        silently replacing the Linux provenance of the run that produced them
        -- and the next `git add` commits the contamination.  The sibling
        `test_mandatory_defect_rematch.py` already mocks the writer; this one
        did not.  The digests below are the control: they must not move.
        """

        before = (_digest(STATE), _digest(STAGE))
        with (
            mock.patch.object(target, "enumerate_target", side_effect=AssertionError("compute called")) as enum,
            mock.patch.object(target.bt, "write_json") as write_json,
        ):
            record = target.stage(SPEC)
        enum.assert_not_called()
        self.assertEqual(write_json.call_count, 4)
        written = [Path(call.args[0]) for call in write_json.call_args_list]
        self.assertIn(STATE, written)
        self.assertIn(STAGE, written)
        self.assertEqual(record["target_rematchings_executed"], 0)
        self.assertEqual(record["total_attempts"], 52_519_936)
        self.assertEqual(
            (_digest(STATE), _digest(STAGE)),
            before,
            "staging rewrote a committed artifact; its cloud provenance is now this host's",
        )
        for path in written:
            self.assertTrue(path.exists(), f"{path} is written by stage but not committed")

    def test_stage_log_is_precompute_only(self) -> None:
        record = json.loads(STAGE.read_text(encoding="utf-8"))
        self.assertEqual(record["format"], "apg-mandatory-defect-k5-stage-v1")
        self.assertEqual(record["spec_sha256"], SPEC_SHA)
        self.assertEqual(record["target_state_sha256"], TARGET_SHA)
        self.assertEqual(record["target_manifest_sha256"], TARGET_MANIFEST)
        self.assertEqual(record["target_rematchings_executed"], 0)

    def test_missing_reordered_parent_defect_auxiliary_and_budget_drift_rejected(self) -> None:
        for mutation in ("missing", "reorder", "defect", "aux", "budget", "matching"):
            changed = copy.deepcopy(self.spec)
            if mutation == "missing": changed["seeds"].pop()
            elif mutation == "reorder": changed["seeds"][0],changed["seeds"][1]=changed["seeds"][1],changed["seeds"][0]
            elif mutation == "defect": changed["seeds"][0]["mandatory_dart_pairs"][0][0] += 1
            elif mutation == "aux": changed["seeds"][0]["auxiliary_edges"] -= 1
            elif mutation == "budget": changed["total_attempts"] -= 1
            else: changed["matchings_per_selection"] = 543
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                target.load_spec(self.write_spec(changed))

    def test_target_payload_drift_and_auxiliary_filtering_are_rejected(self) -> None:
        for mutation in ("parent", "defect", "aux"):
            payload = copy.deepcopy(self.payload)
            if mutation == "parent": payload["parents"].pop()
            elif mutation == "defect": payload["parents"][0]["mandatory_dart_pairs"][0][0] += 1
            else: payload["parents"][0]["auxiliary_edges"].pop()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                target.validate_target_state(self.spec, payload)

    def test_fixed_rotation_and_seed_are_part_of_namespace(self) -> None:
        alpha = self.payload["parents"][0]["auxiliary_edges"]
        self.assertNotEqual(target.state_namespace("26a", "r", alpha), target.state_namespace("26b", "r", alpha))
        self.assertNotEqual(target.state_namespace("26a", "r", alpha), target.state_namespace("26a", "s", alpha))

    def test_nonplane_candidate_is_never_scored(self) -> None:
        fixed, alpha, _ = target.load_frozen_parents(self.spec, rebuild_sources=False)[0]
        with mock.patch("mandatory_defect_k5.map_search.score_breakdown", side_effect=AssertionError("scored")) as score:
            breakdown, reason = target.score_plane_candidate(fixed, alpha)
        score.assert_not_called(); self.assertIsNone(breakdown); self.assertEqual(reason, "abstract_graph")

    def test_incomplete_result_and_certificate_mismatch_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "incomplete"):
            target.validate_result(self.spec, {"complete": False}, self.payload)
        record = {"format":"apg-mandatory-defect-k5-result-v1","spec":str(SPEC.relative_to(ROOT)),"spec_sha256":target.file_sha256(SPEC),"target_state_file":str(STATE.relative_to(ROOT)),"target_state_sha256":TARGET_SHA,"result":{"complete":False},"certificates":{}}
        with self.assertRaises(ValueError): target.validate_result_record(self.spec, record)

    def test_structurally_complete_result_replays_real_plane_frontier(self) -> None:
        fixture = self.complete_result_fixture()
        target.validate_result(self.spec, fixture, self.payload)
        fixed = target.load_frozen_parents(self.spec, rebuild_sources=False)[0][0]
        state = fixture["frontier_states"][0]
        self.assertEqual(k3.plane_valid_gate(fixed, state["alpha"]), (True, None))
        self.assertEqual(state["breakdown"]["total"], 510)

    def test_counter_prune_histogram_frontier_and_namespace_mutations_fail(self) -> None:
        mutations: dict[str, object] = {}

        changed = self.complete_result_fixture()
        changed["counts"]["zero_score_blocks_rejections"] = 1
        mutations["per-seed/global counter mismatch"] = changed

        changed = self.complete_result_fixture()
        changed["per_seed"][0]["counts"]["abstract_graph_prunes"] -= 1
        mutations["per-seed prune mismatch"] = changed

        changed = self.complete_result_fixture()
        changed["counts"]["score_zero"] = 1
        changed["counts"]["zero_score_validation_rejections"] = 1
        changed["per_seed"][0]["counts"]["score_zero"] = 1
        changed["per_seed"][0]["counts"]["zero_score_validation_rejections"] = 1
        changed["score_histogram_distinct"] = {"0": 0, "510": 1}
        mutations["histogram zero mismatch"] = changed

        changed = self.complete_result_fixture()
        changed["score_histogram_distinct"] = {"0510": 1}
        mutations["malformed histogram"] = changed

        changed = self.complete_result_fixture()
        changed["frontier_states"] = []
        changed["frontier_state_count"] = 0
        changed["best_score"] = None
        changed["best_state_hashes"] = []
        mutations["wrong frontier length"] = changed

        changed = self.complete_result_fixture()
        changed["frontier_limit"] = 0
        mutations["invalid frontier limit"] = changed

        changed = self.complete_result_fixture()
        changed["frontier_truncated"] = True
        mutations["wrong truncation"] = changed

        changed = self.complete_result_fixture()
        changed["best_score"] = 511
        mutations["wrong best identity"] = changed

        changed = self.complete_result_fixture()
        changed["frontier_states"][0]["seed_id"] = "missing"
        mutations["wrong seed"] = changed

        changed = self.complete_result_fixture()
        changed["frontier_states"][0]["fixed_rotation_hash"] = "0" * 64
        mutations["wrong fixed map"] = changed

        changed = self.complete_result_fixture()
        changed["frontier_states"][0]["state_sha256"] = "0" * 64
        mutations["bad state hash"] = changed

        changed = self.complete_result_fixture()
        changed["frontier_states"][0]["state_namespace"] = "wrong"
        mutations["bad namespace"] = changed

        changed = self.complete_result_fixture()
        changed["frontier_states"][0]["breakdown"]["white"] += 1
        mutations["bad score"] = changed

        changed = self.complete_result_fixture()
        changed["frontier_states"][0]["rotation"][0]["clockwise"][0] += 1
        mutations["bad serialized rotation"] = changed

        changed = self.complete_result_fixture()
        genus = json.loads(GENUS_ONE.read_text(encoding="utf-8"))["result"]["frontier_states"][0]
        changed["frontier_states"][0]["alpha"] = genus["alpha"]
        changed["frontier_states"][0]["state_sha256"] = near_opening._state_sha256(genus["alpha"])
        changed["frontier_states"][0]["state_namespace"] = target.state_namespace(
            "26a", changed["frontier_states"][0]["fixed_rotation_hash"], genus["alpha"]
        )
        mutations["nonspherical frontier"] = changed

        changed = self.complete_result_fixture()
        duplicate = copy.deepcopy(changed["frontier_states"][0])
        changed["frontier_states"].append(duplicate)
        changed["frontier_state_count"] = 2
        changed["score_histogram_distinct"] = {"510": 2}
        changed["counts"]["raw_plane_valid"] += 1
        changed["counts"]["distinct_plane_valid"] += 1
        changed["counts"]["abstract_graph_prunes"] -= 1
        seed_counts = changed["per_seed"][0]["counts"]
        seed_counts["raw_plane_valid"] += 1
        seed_counts["distinct_plane_valid"] += 1
        seed_counts["abstract_graph_prunes"] -= 1
        changed["best_state_hashes"] = [duplicate["state_sha256"], duplicate["state_sha256"]]
        mutations["duplicate namespace"] = changed

        for name, value in mutations.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                target.validate_result(self.spec, value, self.payload)

    def test_success_hash_order_checks_and_certificate_replay_are_strict(self) -> None:
        fixture = self.complete_result_fixture()
        fixture["success_hashes"] = ["b", "a", "a"]
        fixture["success_checks"] = {"a": {}, "b": {}}
        with self.assertRaisesRegex(ValueError, "sorted and unique"):
            target.validate_result(self.spec, fixture, self.payload)

        calibration = json.loads(CALIBRATION_LOG.read_text(encoding="utf-8"))
        block_hash = calibration["recovered_D24_hash"]
        success = {
            "success_hashes": [block_hash],
            "success_checks": calibration["result"]["success_checks"],
        }
        certificates = {
            block_hash: {
                "path": str(CALIBRATION_CERTIFICATE.relative_to(ROOT)),
                "sha256": target.file_sha256(CALIBRATION_CERTIFICATE),
            }
        }
        target.validate_certificate_manifest(success, certificates, ROOT)
        with self.assertRaisesRegex(ValueError, "certificate manifest"):
            target.validate_certificate_manifest(success, {}, ROOT)
        wrong = copy.deepcopy(success)
        wrong["success_checks"][block_hash]["block_tools_closed_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "validator/closer"):
            target.validate_certificate_manifest(wrong, certificates, ROOT)


if __name__ == "__main__":
    unittest.main()
