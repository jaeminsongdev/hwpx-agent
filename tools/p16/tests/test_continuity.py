from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest


TOOLS = Path(__file__).resolve().parents[1]
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_continuity_contract as builder
import continuity
import validate_continuity as validator


class ContinuityTests(unittest.TestCase):
    @classmethod
    def policy(cls) -> dict[str, object]:
        return json.loads(continuity.POLICY_PATH.read_text(encoding="utf-8"))

    def test_policy_and_every_visual_digest_are_exact(self) -> None:
        self.assertEqual([], continuity.validate_policy(self.policy()))

    def test_policy_rejects_expanded_csp_and_action_budget(self) -> None:
        expanded = copy.deepcopy(self.policy())
        expanded["resource"]["csp"]["connectDomains"] = ["https://bad.test"]
        self.assertIn("policy.resource", continuity.validate_policy(expanded))
        actions = copy.deepcopy(self.policy())
        actions["bounds"]["primary_actions"] = 2
        self.assertIn("policy.bounds", continuity.validate_policy(actions))

    def test_policy_rejects_design_and_capture_drift(self) -> None:
        design = copy.deepcopy(self.policy())
        design["design_source"]["sha256"] = "0" * 64
        self.assertIn("policy.design.image.digest", continuity.validate_policy(design))
        capture = copy.deepcopy(self.policy())
        capture["visual_qa"]["captures"][0]["sha256"] = "0" * 64
        self.assertIn("policy.visual.image.digest", continuity.validate_policy(capture))

    def test_predecessor_and_public_catalog_are_exact(self) -> None:
        self.assertEqual([], continuity.validate_predecessor())
        self.assertEqual([], continuity.validate_public_catalog())

    def test_production_sources_have_no_network_storage_or_private_api(self) -> None:
        self.assertEqual([], continuity.validate_authored_sources())

    def test_runtime_evidence_directory_is_git_ignored_without_locking_gitignore(self) -> None:
        self.assertEqual([], continuity.validate_evidence_ignore())
        self.assertNotIn(".gitignore", builder.LOCAL_SOURCE_PATHS)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".gitignore").write_text("/implementation/p15/evidence/\n", encoding="utf-8")
            self.assertEqual(
                ["evidence_ignore.missing"],
                continuity.validate_evidence_ignore(root),
            )

    def test_bundle_is_bounded_self_contained_and_protocol_complete(self) -> None:
        policy = self.policy()
        bundles, errors = continuity.validate_bundles(policy)
        self.assertEqual([], errors)
        self.assertIsNotNone(bundles)
        self.assertLessEqual(bundles["resource"]["bytes"], 800000)

    def test_bundle_rejects_oversize_network_storage_and_private_path(self) -> None:
        self.assertIn("bundle.bytes", continuity.validate_bundle_bytes(b"x" * 800001))
        for fragment in (
            b"<iframe src='/private'>", b"localStorage.setItem('x','y')", b"D:\\private",
        ):
            self.assertTrue(
                any(error.startswith("bundle.forbidden") for error in continuity.validate_bundle_bytes(fragment))
            )

    def test_css_is_responsive_reduced_motion_and_aa(self) -> None:
        self.assertEqual([], continuity.validate_css())
        self.assertGreaterEqual(continuity.contrast_ratio("#8a4b00", "#ffffff"), 4.5)
        self.assertGreaterEqual(continuity.contrast_ratio("#ff8a80", "#171f2c"), 4.5)

    def test_complete_implementation_validation_passes(self) -> None:
        bundles, errors = continuity.validate_all()
        self.assertEqual([], errors)
        self.assertIsNotNone(bundles)

    def test_generated_contract_is_exact_and_preserves_open_claims(self) -> None:
        expected = builder.build_contract()
        actual = json.loads(builder.CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(expected, actual)
        self.assertEqual([], validator.validate(actual))
        self.assertTrue(all(value is False for value in actual["claims"].values()))

    def test_duplicate_json_keys_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"task":"P16-05","task":"bad"}', encoding="utf-8")
            value, errors = continuity.load_json(path)
            self.assertIsNone(value)
            self.assertEqual(["json.parse"], errors)

    def test_contract_locks_every_declared_source_once(self) -> None:
        self.assertEqual(len(builder.LOCAL_SOURCE_PATHS), len(set(builder.LOCAL_SOURCE_PATHS)))
        self.assertTrue(all((continuity.ROOT / path).is_file() for path in builder.LOCAL_SOURCE_PATHS))


if __name__ == "__main__":
    unittest.main()
