from __future__ import annotations

import copy
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import four_edge_rematch as k4
import mandatory_defect_rematch as target
import near_open_search
import three_edge_rematch as k3


ROOT = Path(__file__).resolve().parent
SPEC = ROOT / "jobs/mandatory_defect_26_29_33.json"
STATE = ROOT / "results/targets/mandatory_defect_26_29_33_parents.json"
STAGE = ROOT / "results/logs/mandatory_defect_26_29_33_stage.json"
RESULT = ROOT / "results/logs/mandatory_defect_26_29_33_result.json"
SPEC_SHA = "e3d3c4d417c00aabce50bea56591a3e8b3dbda837eec7f5f6d2f4aa99f1a428b"
STATE_SHA = "8eb46f4665eefb4889f51b514430a28954bb092183e1efc0542d6c3d8d76cf8c"
PARENT_MANIFEST = "fd975d8752589565d7c8a7a7d69b8c4d8f55f5f76b9b2b706d6a7d4c2536149a"
RESULT_SHA = "9b85bdc57c4ccf4760f0260cd3282ee94dc94aef9a7d85f6390ceea449f576a3"


EXPECTED = {
    "26a": ("9115b20cf204b1ff18b321142d6bf5c13eaf0501336382aa98283d69a36ac23b", 370, [[22, 23], [22, 25]], [[81, 84], [82, 88]], True, 352, 56_760),
    "26b": ("27d8e3b580147da90d04e1be6340f3401f7a33f665fe82012cbef1234050b1b5", 370, [[2, 3], [3, 4]], [[2, 4], [7, 8]], True, 352, 56_760),
    "29a": ("47094c88eb367991684df1a4994132da5ca7221d4a2c40393b60f8490d97b998", 880, [[13, 14], [14, 15]], [[46, 50], [48, 51]], True, 400, 73_500),
    "29b": ("34078a0bb5633707ab9fdc262750c42527bea38d510d5fccac54ae3a34e8c067", 880, [[3, 4], [7, 21]], [[10, 11], [25, 75]], False, 400, 73_500),
    "33": ("41a2273e6b35c77ffc8d10ff8d5eb68b4831fb8b79dc79eb53c1bcdcf89fd7b6", 460, [[2, 5], [4, 5]], [[3, 11], [9, 14]], True, 464, 99_180),
}


class MandatoryDefectRematchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = target.load_spec(SPEC)
        self.payload = json.loads(STATE.read_text(encoding="utf-8"))

    def write_spec(self, value: dict[str, object]) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "spec.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_spec_state_manifest_and_exact_budgets_are_frozen(self) -> None:
        self.assertEqual(target.file_sha256(SPEC), SPEC_SHA)
        self.assertEqual(target.file_sha256(STATE), STATE_SHA)
        self.assertEqual(self.spec["parent_manifest_sha256"], PARENT_MANIFEST)
        self.assertEqual(self.payload["parent_manifest_sha256"], PARENT_MANIFEST)
        self.assertEqual(self.spec["k3_total_attempts"], 1_968)
        self.assertEqual(self.spec["k4_total_attempts"], 359_700)
        self.assertEqual(self.spec["combined_total_attempts"], 361_668)
        self.assertEqual([seed["id"] for seed in self.spec["seeds"]], ["26a", "26b", "29a", "29b", "33"])

    def test_all_source_certificates_seeds_topology_and_defects_replay(self) -> None:
        loaded = target.validate_target_state(self.spec, self.payload)
        self.assertEqual(len(loaded), 5)
        for (_, alpha, parent), entry in zip(loaded, self.spec["seeds"]):
            expected = EXPECTED[parent["id"]]
            self.assertEqual(parent["state_sha256"], expected[0])
            self.assertEqual(parent["breakdown"]["total"], expected[1])
            self.assertEqual([d["labeled_edge"] for d in parent["mandatory_defects"]], expected[2])
            self.assertEqual([d["dart_pair"] for d in parent["mandatory_defects"]], expected[3])
            self.assertEqual(parent["defects_share_vertex"], expected[4])
            self.assertEqual(parent["k3_attempts"], expected[5])
            self.assertEqual(parent["k4_attempts"], expected[6])
            self.assertFalse(parent["abstract_valid"])
            self.assertEqual(parent["euler_characteristic"], 2)
            self.assertEqual(len(parent["mandatory_defects"]), 2)
            self.assertEqual(len(parent["auxiliary_edges"]), len(alpha) // 2 - 2)
            self.assertEqual(target.canonical_sha256(parent["source_certificate"]), entry["source_certificate_sha256"])
        self.assertFalse(self.payload["parents"][3]["defects_share_vertex"])

    def test_order29_generated_seeds_replay_exact_hashes(self) -> None:
        expected = {
            "29a": "8a5ec34f00f28d4287bcf1e78796377ae8580b835b4374de7bc5a5fce620814a",
            "29b": "b37625328b2f195c539c05fbde08cb1c9234dbdec3bd89b158f5f8e7d2b24bc3",
        }
        for entry in self.spec["seeds"][2:4]:
            rebuilt = target.build_certificate_seed(entry, ROOT)
            committed = json.loads((ROOT / entry["seed_path"]).read_text(encoding="utf-8"))
            self.assertEqual(rebuilt, committed)
            self.assertEqual(target.file_sha256(ROOT / entry["seed_path"]), expected[entry["id"]])

    def test_k3_k4_count_identities_and_all_auxiliary_edges(self) -> None:
        for parent in self.payload["parents"]:
            edges = parent["current_edge_count"]
            self.assertEqual(parent["k3_auxiliary_choices"], edges - 2)
            self.assertEqual(parent["k3_matchings_per_choice"], 8)
            self.assertEqual(parent["k3_attempts"], (edges - 2) * 8)
            self.assertEqual(parent["k4_auxiliary_pairs"], math.comb(edges - 2, 2))
            self.assertEqual(parent["k4_matchings_per_pair"], 60)
            self.assertEqual(parent["k4_attempts"], math.comb(edges - 2, 2) * 60)
            mandatory = {tuple(d["dart_pair"]) for d in parent["mandatory_defects"]}
            current = set(k3.edge_pairs(parent["alpha"]))
            self.assertEqual(set(map(tuple, parent["auxiliary_edges"])), current - mandatory)

    def test_stage_executes_zero_target_rematchings(self) -> None:
        with (
            mock.patch.object(target, "enumerate_lane", side_effect=AssertionError("compute called")) as enum,
            mock.patch.object(target.bt, "write_json") as write_json,
        ):
            record = target.stage(SPEC)
        enum.assert_not_called()
        self.assertEqual(write_json.call_count, 4)
        self.assertEqual(record["target_rematchings_executed"], 0)
        self.assertEqual(record["combined_total_attempts"], 361_668)

    def test_committed_stage_log_freezes_zero_compute_and_all_manifests(self) -> None:
        record = json.loads(STAGE.read_text(encoding="utf-8"))
        self.assertEqual(record["format"], "apg-mandatory-defect-k3-k4-stage-v1")
        self.assertEqual(record["spec_sha256"], SPEC_SHA)
        self.assertEqual(record["target_state_sha256"], STATE_SHA)
        self.assertEqual(record["parent_manifest_sha256"], PARENT_MANIFEST)
        self.assertEqual(record["seed_count"], 5)
        self.assertEqual(record["k3_total_attempts"], 1_968)
        self.assertEqual(record["k4_total_attempts"], 359_700)
        self.assertEqual(record["combined_total_attempts"], 361_668)
        self.assertEqual(record["target_rematchings_executed"], 0)

    def test_source_seed_hash_fan_missing_and_reordered_drift_are_rejected(self) -> None:
        for mutation in ("seed_hash", "fans", "missing", "reordered"):
            changed = copy.deepcopy(self.spec)
            if mutation == "seed_hash":
                changed["seeds"][0]["seed_file_sha256"] = "0" * 64
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    target.build_target_state(changed, ROOT)
                continue
            if mutation == "fans":
                changed["seeds"][0]["fans"][0]["hub"] = 2
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                    target.build_target_state(changed, ROOT)
                continue
            if mutation == "missing":
                changed["seeds"].pop()
            else:
                changed["seeds"][0], changed["seeds"][1] = changed["seeds"][1], changed["seeds"][0]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                target.load_spec(self.write_spec(changed))

    def test_defect_and_auxiliary_drift_are_rejected(self) -> None:
        for mutation in ("missing_defect", "extra_defect", "filtered_auxiliary"):
            changed = copy.deepcopy(self.payload)
            if mutation == "missing_defect":
                changed["parents"][0]["mandatory_defects"].pop()
            elif mutation == "extra_defect":
                changed["parents"][0]["mandatory_defects"].append(copy.deepcopy(changed["parents"][0]["mandatory_defects"][0]))
            else:
                changed["parents"][0]["auxiliary_edges"].pop()
            changed["parent_manifest_sha256"] = target.canonical_sha256(target.parent_manifest(changed["parents"]))
            spec = dict(self.spec)
            spec["parent_manifest_sha256"] = changed["parent_manifest_sha256"]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                target.validate_target_state(spec, changed)

    def test_retained_original_edges_are_rejected_in_both_primitives(self) -> None:
        parent = self.payload["parents"][0]
        alpha = parent["alpha"]
        mandatory = tuple(tuple(d["dart_pair"]) for d in parent["mandatory_defects"])
        aux = tuple(map(tuple, parent["auxiliary_edges"]))
        selected3 = mandatory + (aux[0],)
        (a, b), (c, d) = selected3[1:]
        retained3 = k3.normalize_matching((selected3[0], (a, c), (b, d)))
        with self.assertRaisesRegex(ValueError, "retained"):
            k3.apply_rematching(alpha, selected3, retained3)
        selected4 = mandatory + aux[:2]
        retained4 = (selected4[0], *k3.deranged_matchings(selected4[1:])[0])
        with self.assertRaisesRegex(ValueError, "retained"):
            k4.apply_rematching(alpha, selected4, retained4)

    def test_fixed_map_identity_is_part_of_global_dedup_key(self) -> None:
        alpha = self.payload["parents"][0]["alpha"]
        self.assertNotEqual(target.exact_state_key("a", alpha), target.exact_state_key("b", alpha))
        self.assertEqual(target.exact_state_key("a", alpha), target.exact_state_key("a", list(alpha)))

    def test_nonplane_parent_cannot_be_scored(self) -> None:
        fixed, alpha, _ = target.validate_target_state(self.spec, self.payload)[0]
        with self.assertRaisesRegex(ValueError, "plane gate"):
            target.score_plane_candidate(fixed, alpha)

    def test_budget_drift_incomplete_output_and_certificate_mismatch_are_rejected(self) -> None:
        for key in ("k3_total_attempts", "k4_total_attempts", "combined_total_attempts"):
            changed = copy.deepcopy(self.spec)
            changed[key] -= 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                target.load_spec(self.write_spec(changed))
        with self.assertRaisesRegex(ValueError, "incomplete"):
            target.validate_lane_result({"complete": False}, 1_968)
        lane = {
            "complete": True,
            "lane": "k3",
            "expected_attempts": 1_968,
            "counts": {
                "attempts": 1_968,
                "abstract_graph_prunes": 1_968,
                "nonspherical_prunes": 0,
                "graph_invalid_prunes": 1_968,
                "raw_plane_valid": 0,
            },
            "per_seed": [],
            "score_histogram_distinct": {},
            "frontier_limit": 64,
            "frontier_states": [],
            "frontier_state_count": 0,
            "frontier_truncated": False,
            "best_score": None,
            "best_state_hashes": [],
            "success_hashes": ["0" * 64],
            "success_checks": {},
        }
        with self.assertRaisesRegex(ValueError, "success checks"):
            target.validate_lane_result(lane, 1_968)

    def synthetic_lane(self, lane: str) -> dict[str, object]:
        expected_key = f"{lane}_attempts"
        per_seed = []
        for parent in self.payload["parents"]:
            attempts = parent[expected_key]
            per_seed.append({
                "id": parent["id"],
                "counts": {
                    "abstract_graph_prunes": attempts,
                    "attempts": attempts,
                    "graph_invalid_prunes": attempts,
                },
            })
        total = self.spec[f"{lane}_total_attempts"]
        return {
            "complete": True,
            "lane": lane,
            "expected_attempts": total,
            "counts": {
                "abstract_graph_prunes": total,
                "attempts": total,
                "graph_invalid_prunes": total,
            },
            "per_seed": per_seed,
            "score_histogram_distinct": {},
            "frontier_limit": 64,
            "frontier_states": [],
            "frontier_state_count": 0,
            "frontier_truncated": False,
            "best_score": None,
            "best_state_hashes": [],
            "success_hashes": [],
            "success_checks": {},
            "wall_seconds": 0.0,
        }

    def synthetic_record(self) -> dict[str, object]:
        return {
            "format": "apg-mandatory-defect-k3-k4-result-v1",
            "spec": str(SPEC.relative_to(ROOT)),
            "spec_sha256": SPEC_SHA,
            "target_state_file": str(STATE.relative_to(ROOT)),
            "target_state_sha256": STATE_SHA,
            "parent_manifest_sha256": PARENT_MANIFEST,
            "combined_expected_attempts": 361_668,
            "k3": self.synthetic_lane("k3"),
            "k4": self.synthetic_lane("k4"),
            "certificates": {},
        }

    def test_result_record_replays_bytes_per_seed_plane_dedup_and_histogram(self) -> None:
        record = self.synthetic_record()
        target.validate_result_record(self.spec, record, ROOT)
        mutations = {
            "spec_hash": lambda value: value.update(spec_sha256="0" * 64),
            "state_hash": lambda value: value.update(target_state_sha256="0" * 64),
            "manifest": lambda value: value.update(parent_manifest_sha256="0" * 64),
            "combined": lambda value: value.update(combined_expected_attempts=361_667),
            "seed_attempt": lambda value: value["k3"]["per_seed"][0]["counts"].update(attempts=351),
            "plane": lambda value: value["k3"]["counts"].update(graph_invalid_prunes=1_967),
            "dedup": lambda value: value["k3"]["counts"].update(raw_plane_valid=1),
            "histogram": lambda value: value["k3"].update(score_histogram_distinct={"10": 1}),
        }
        for name, mutate in mutations.items():
            changed = copy.deepcopy(record)
            mutate(changed)
            with self.subTest(name=name), self.assertRaises(ValueError):
                target.validate_result_record(self.spec, changed, ROOT)

    def test_frontier_namespace_hash_score_best_and_truncation_are_replayed(self) -> None:
        record = self.synthetic_record()
        loaded = target.validate_target_state(self.spec, self.payload)
        selected_parent_index = 0
        fixed, candidate, parent = loaded[selected_parent_index]
        breakdown = parent["breakdown"]
        state = k3.serialize_state(fixed, candidate, breakdown)
        state.update(seed_id=parent["id"], fixed_rotation_hash=parent["fixed_rotation_hash"])
        lane = record["k3"]
        lane["counts"] = {
            "abstract_graph_prunes": 1_967,
            "attempts": 1_968,
            "distinct_plane_valid": 1,
            "graph_invalid_prunes": 1_967,
            "raw_plane_valid": 1,
        }
        selected_counts = lane["per_seed"][selected_parent_index]["counts"]
        selected_attempts = selected_counts["attempts"]
        lane["per_seed"][selected_parent_index]["counts"] = {
            "abstract_graph_prunes": selected_attempts - 1,
            "attempts": selected_attempts,
            "distinct_plane_valid": 1,
            "graph_invalid_prunes": selected_attempts - 1,
            "raw_plane_valid": 1,
        }
        lane["score_histogram_distinct"] = {str(breakdown["total"]): 1}
        lane["frontier_states"] = [state]
        lane["frontier_state_count"] = 1
        lane["best_score"] = breakdown["total"]
        lane["best_state_hashes"] = [state["state_sha256"]]
        with mock.patch.object(k3, "plane_valid_gate", return_value=(True, None)):
            target.validate_result_record(self.spec, record, ROOT)
            for name, mutate in {
                "seed": lambda item: item.update(seed_id="29b"),
                "rotation": lambda item: item.update(fixed_rotation_hash="0" * 64),
                "alpha_hash": lambda item: item.update(state_sha256="0" * 64),
            }.items():
                changed = copy.deepcopy(record)
                mutate(changed["k3"]["frontier_states"][0])
                with self.subTest(name=name), self.assertRaises(ValueError):
                    target.validate_result_record(self.spec, changed, ROOT)
            for name in ("best", "truncation"):
                changed = copy.deepcopy(record)
                if name == "best":
                    changed["k3"]["best_score"] += 1
                else:
                    changed["k3"]["frontier_truncated"] = True
                with self.subTest(name=name), self.assertRaises(ValueError):
                    target.validate_result_record(self.spec, changed, ROOT)

    def test_every_reported_success_replays_certificate_and_exact_closer_checks(self) -> None:
        record = self.synthetic_record()
        block = target.bt.load_json(ROOT / "results/blocks/D24.json")
        block_hash = target.bt.canonical_map_hash(block)
        checks = near_open_search._close_and_verify(block)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "jobs").mkdir()
            (root / "results/targets").mkdir(parents=True)
            (root / "certificates").mkdir()
            (root / "jobs/spec.json").write_bytes(SPEC.read_bytes())
            (root / "results/targets/state.json").write_bytes(STATE.read_bytes())
            cert = root / "certificates/block.json"
            cert.write_text(json.dumps(block), encoding="utf-8")
            record["spec"] = "jobs/spec.json"
            record["target_state_file"] = "results/targets/state.json"
            record["certificates"] = {
                block_hash: {"path": "certificates/block.json", "sha256": target.file_sha256(cert)}
            }
            record["k3"]["success_hashes"] = [block_hash]
            record["k3"]["success_checks"] = {block_hash: checks}
            with mock.patch.object(target, "validate_target_state", return_value=[
                (None, [], parent) for parent in self.payload["parents"]
            ]):
                target.validate_result_record(self.spec, record, root)
                changed = copy.deepcopy(record)
                changed["k3"]["success_checks"][block_hash]["blocks_verified"] = False
                with self.assertRaisesRegex(ValueError, "closer"):
                    target.validate_result_record(self.spec, changed, root)

    def test_complete_committed_k3_k4_result_is_byte_frozen_and_replays(self) -> None:
        self.assertEqual(target.file_sha256(RESULT), RESULT_SHA)
        record = json.loads(RESULT.read_text(encoding="utf-8"))
        target.validate_result_record(self.spec, record, ROOT)
        self.assertEqual(record["spec_sha256"], SPEC_SHA)
        self.assertEqual(record["target_state_sha256"], STATE_SHA)
        self.assertEqual(record["parent_manifest_sha256"], PARENT_MANIFEST)
        self.assertEqual(record["combined_expected_attempts"], 361_668)
        self.assertEqual(record["k3"]["counts"], {
            "abstract_graph_prunes": 1_968,
            "attempts": 1_968,
            "graph_invalid_prunes": 1_968,
        })
        self.assertEqual(
            [item["counts"]["attempts"] for item in record["k3"]["per_seed"]],
            [352, 352, 400, 400, 464],
        )
        self.assertEqual(record["k4"]["counts"], {
            "abstract_graph_prunes": 358_458,
            "attempts": 359_700,
            "graph_invalid_prunes": 359_700,
            "nonspherical_prunes": 1_242,
        })
        self.assertEqual(
            [item["counts"]["attempts"] for item in record["k4"]["per_seed"]],
            [56_760, 56_760, 73_500, 73_500, 99_180],
        )
        self.assertEqual(
            [item["counts"].get("nonspherical_prunes", 0) for item in record["k4"]["per_seed"]],
            [204, 204, 294, 244, 296],
        )
        for lane in ("k3", "k4"):
            result = record[lane]
            self.assertEqual(result["score_histogram_distinct"], {})
            self.assertEqual(result["frontier_states"], [])
            self.assertEqual(result["frontier_state_count"], 0)
            self.assertFalse(result["frontier_truncated"])
            self.assertIsNone(result["best_score"])
            self.assertEqual(result["best_state_hashes"], [])
            self.assertEqual(result["success_hashes"], [])
            self.assertEqual(result["success_checks"], {})
        self.assertEqual(record["certificates"], {})

    def test_committed_result_rejects_hash_accounting_frontier_and_success_drift(self) -> None:
        record = json.loads(RESULT.read_text(encoding="utf-8"))
        mutations = {
            "spec": lambda value: value.update(spec_sha256="0" * 64),
            "state": lambda value: value.update(target_state_sha256="0" * 64),
            "per_seed": lambda value: value["k4"]["per_seed"][4]["counts"].update(attempts=99_179),
            "plane": lambda value: value["k4"]["counts"].update(nonspherical_prunes=1_241),
            "histogram": lambda value: value["k4"].update(score_histogram_distinct={"0": 1}),
            "frontier": lambda value: value["k4"].update(frontier_truncated=True),
            "success": lambda value: value["k4"].update(success_hashes=["0" * 64]),
        }
        for name, mutate in mutations.items():
            changed = copy.deepcopy(record)
            mutate(changed)
            with self.subTest(name=name), self.assertRaises(ValueError):
                target.validate_result_record(self.spec, changed, ROOT)


if __name__ == "__main__":
    unittest.main()
