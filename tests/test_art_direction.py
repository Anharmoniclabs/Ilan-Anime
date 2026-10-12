"""Contract tests use declarations only; fixtures are not claims about real art."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from production.validate_art_direction import ArtDirectionError, validate_report


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "production/art_direction.json").read_text())


def accepted_report(mode="STORY_FRAME"):
    spec = CONTRACT["modes"][mode]
    digest = "a" * 64
    sources = []
    for tier in spec["required_source_tiers"]:
        source = CONTRACT["source_precedence"][tier - 1]
        sources.append({"tier": tier, "id": source["id"], "status": "approved",
                        "usage": "authoritative", "reference": f"references/tier-{tier}.txt"})
    criteria = {criterion: {"decision": "pass", "observation": f"Inspected {criterion}",
                             "evidence_paths": [f"reviews/{criterion}.png"]}
                for criterion in spec["required_criteria"]}
    return {
        "contract_id": CONTRACT["contract_id"], "contract_version": CONTRACT["version"],
        "asset": {"id": "asset-v003", "path": "assets/asset-v003.png", "sha256": digest,
                  "mode": mode, "source_status": "candidate", "creator_id": "artist-1",
                  "requested_scope": "A bounded synthetic test fixture"},
        "sources": sources, "criteria": criteria,
        "technical_review": {"decision": "approve", "reviewer_id": "reviewer-1",
                             "reviewer_role": "art-director", "observation": "Independent review",
                             "asset_sha256": digest},
        "author_approval": {"decision": "approved", "author_id": "luis-m-minier",
                            "author_statement": "Approved exact fixture digest",
                            "approval_reference": "approvals/asset-v003.txt", "asset_sha256": digest},
        "promotion": {"target_status": "canonical"}
    }


class ArtDirectionTests(unittest.TestCase):
    def test_all_modes_pass_complete_contract(self):
        for mode in CONTRACT["modes"]:
            with self.subTest(mode=mode):
                result = validate_report(accepted_report(mode), CONTRACT)
                self.assertTrue(result["valid"])
                self.assertEqual(mode, result["mode"])
                self.assertEqual("canonical", result["promotion"])

    def test_failed_criterion_cannot_be_averaged_away(self):
        report = accepted_report()
        report["criteria"]["identity"]["decision"] = "fail"
        with self.assertRaisesRegex(ArtDirectionError, "identity.*must be pass"):
            validate_report(report, CONTRACT)

    def test_no_evidence_fails(self):
        report = accepted_report()
        report["criteria"]["style"]["evidence_paths"] = []
        with self.assertRaisesRegex(ArtDirectionError, "evidence_paths"):
            validate_report(report, CONTRACT)

    def test_no_author_approval_fails(self):
        report = accepted_report()
        del report["author_approval"]
        with self.assertRaisesRegex(ArtDirectionError, "author_approval"):
            validate_report(report, CONTRACT)

    def test_author_approval_is_digest_bound(self):
        report = accepted_report()
        report["author_approval"]["asset_sha256"] = "b" * 64
        with self.assertRaisesRegex(ArtDirectionError, "author approval.*digest"):
            validate_report(report, CONTRACT)

    def test_rejected_asset_cannot_be_promoted(self):
        report = accepted_report()
        report["asset"]["source_status"] = "rejected"
        with self.assertRaisesRegex(ArtDirectionError, "rejected assets are terminal"):
            validate_report(report, CONTRACT)

    def test_rejected_reference_cannot_be_authoritative(self):
        report = accepted_report()
        report["sources"][0]["status"] = "rejected"
        with self.assertRaisesRegex(ArtDirectionError, "authoritative sources must be approved"):
            validate_report(report, CONTRACT)

    def test_source_precedence_and_required_tiers(self):
        report = accepted_report()
        report["sources"] = list(reversed(report["sources"]))
        with self.assertRaisesRegex(ArtDirectionError, "precedence order"):
            validate_report(report, CONTRACT)
        report = accepted_report()
        report["sources"] = report["sources"][1:]
        with self.assertRaisesRegex(ArtDirectionError, "missing authoritative source tiers"):
            validate_report(report, CONTRACT)

    def test_creator_cannot_technically_approve_own_asset(self):
        report = accepted_report()
        report["technical_review"]["reviewer_id"] = report["asset"]["creator_id"]
        with self.assertRaisesRegex(ArtDirectionError, "independent"):
            validate_report(report, CONTRACT)

    def test_unsafe_evidence_path_fails(self):
        report = accepted_report()
        report["criteria"]["style"]["evidence_paths"] = ["../outside.png"]
        with self.assertRaisesRegex(ArtDirectionError, "repository-relative"):
            validate_report(report, CONTRACT)

    def test_input_is_not_mutated(self):
        report = accepted_report()
        before = deepcopy(report)
        validate_report(report, CONTRACT)
        self.assertEqual(before, report)


if __name__ == "__main__":
    unittest.main()
