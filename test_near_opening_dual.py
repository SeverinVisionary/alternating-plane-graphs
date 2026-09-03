from __future__ import annotations

import json
import unittest
from pathlib import Path

import blocks
import near_opening
from conftest import requires_upstream_corpus


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "certificates/search_seeds/upstream/28_26-26.plc"
SEED = ROOT / "results/near_openings/order26_28_fans_1_26.json"
SOURCE_SHA256 = "adf39c3bb116a259efedaa6f9bb5c42734f262652dbe3fafd8fe5aafec17799c"
SOURCE_URL = "https://www.althofer.de/apg/apgs/28_26-26.plc"
EXPECTED_STATE_SHA256 = (
    "27d8e3b580147da90d04e1be6340f3401f7a33f665fe82012cbef1234050b1b5"
)


class NearOpenDualSetupTests(unittest.TestCase):
    @requires_upstream_corpus
    def test_exact_source_and_seed_replay(self) -> None:
        self.assertEqual(near_opening.file_sha256(SOURCE), SOURCE_SHA256)
        expected = json.loads(SEED.read_text(encoding="utf-8"))
        replayed = near_opening.make_seed(
            SOURCE,
            expected_sha256=SOURCE_SHA256,
            source_url=SOURCE_URL,
            first=blocks.ClosureFan(1, (2, 4)),
            second=blocks.ClosureFan(26, (15, 25)),
        )
        self.assertEqual(replayed, expected)
        self.assertEqual(replayed["state_sha256"], EXPECTED_STATE_SHA256)
        self.assertEqual(
            replayed["score_breakdown"],
            {
                "abstract_graph": 160,
                "equal_face": 0,
                "face_distribution": 0,
                "hex": 120,
                "total": 370,
                "white": 90,
            },
        )
        self.assertEqual(len(replayed["source_rotation"]), 26)
        self.assertEqual(len(replayed["opened_rotation"]), 26)
        self.assertEqual(replayed["source"]["verified_apg"], True)
        self.assertEqual(
            replayed["claim_scope"],
            "Diagnostic near-opening seed; not a strict block witness.",
        )


if __name__ == "__main__":
    unittest.main()
