from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/p16"
import sys

sys.path.insert(0, str(TOOLS))
import build_widget_shell_contract as contract_builder  # noqa: E402
import validate_widget_shell as validator  # noqa: E402
import widget_shell as shell  # noqa: E402


class WidgetShellTests(unittest.TestCase):
    def policy(self) -> dict:
        return json.loads(shell.POLICY_PATH.read_text(encoding="utf-8"))

    def test_policy_and_dependency_locks_are_exact(self) -> None:
        policy = self.policy()
        self.assertEqual([], shell.validate_policy(policy))
        self.assertEqual([], shell.validate_dependencies(policy))

    def test_two_concept_images_are_byte_and_dimension_locked(self) -> None:
        for item in self.policy()["design_sources"]:
            value = (ROOT / item["path"]).read_bytes()
            self.assertEqual(item["bytes"], len(value))
            self.assertEqual(item["sha256"], shell.sha256_bytes(value))
            self.assertEqual((item["width"], item["height"]), shell.png_dimensions(value))

    def test_bundle_is_self_contained_bounded_and_protocol_complete(self) -> None:
        value = shell.BUNDLE_PATH.read_bytes()
        self.assertEqual([], shell.validate_bundle_bytes(value))
        self.assertLessEqual(len(value), 700000)

    def test_external_reference_and_unsafe_eval_are_rejected(self) -> None:
        base = shell.BUNDLE_PATH.read_bytes()
        for hostile in (
            b'<script src="https://cdn.test/widget.js"></script>',
            b"<script>new Function('return private')</script>",
            b"<iframe srcdoc='private'></iframe>",
            b'<a href="https://external.test/">external</a>',
            b'<form action="/submit"></form>',
            b'<meta http-equiv="refresh" content="0;url=/next">',
            b"<script>localStorage.setItem('x','private')</script>",
        ):
            self.assertTrue(shell.validate_bundle_bytes(base + hostile))

    def test_public_p15_tools_have_no_widget_metadata(self) -> None:
        self.assertEqual([], shell.validate_public_catalog())

    def test_authored_browser_sources_have_no_network_or_storage_path(self) -> None:
        self.assertEqual([], shell.validate_authored_browser_sources())

    def test_css_contract_has_responsive_focus_reduced_motion_and_aa_contrast(self) -> None:
        self.assertEqual([], shell.validate_css_contract())
        self.assertGreaterEqual(shell.contrast_ratio("#117a4b", "#ffffff"), 4.5)
        self.assertGreaterEqual(shell.contrast_ratio("#111722", "#78aef7"), 4.5)

    def test_ui_contamination_detector_finds_modern_and_legacy_keys(self) -> None:
        self.assertTrue(shell._contains_resource_uri({"_meta": {"ui": {"resourceUri": "ui://bad"}}}))
        self.assertTrue(shell._contains_resource_uri({"_meta": {"ui/resourceUri": "ui://bad"}}))

    def test_policy_rejects_expanded_csp_and_dependency_drift(self) -> None:
        policy = self.policy()
        expanded = copy.deepcopy(policy)
        expanded["csp"]["connectDomains"] = ["https://unreviewed.test"]
        self.assertIn("policy.csp", shell.validate_policy(expanded))
        drifted = copy.deepcopy(policy)
        drifted["dependencies"][0]["version"] = "latest"
        self.assertIn("policy.dependencies", shell.validate_policy(drifted))

    def test_policy_rejects_concept_digest_drift(self) -> None:
        policy = self.policy()
        policy["design_sources"][0]["sha256"] = "0" * 64
        self.assertIn("policy.design.digest", shell.validate_policy(policy))

    def test_policy_rejects_visual_capture_digest_drift(self) -> None:
        policy = self.policy()
        policy["visual_qa"]["captures"][0]["sha256"] = "0" * 64
        self.assertIn("policy.visual_qa.digest", shell.validate_policy(policy))

    def test_bundle_size_limit_is_fail_closed(self) -> None:
        self.assertIn("bundle.bytes", shell.validate_bundle_bytes(b"x" * 700001))

    def test_predecessor_and_catalog_digests_are_exact(self) -> None:
        self.assertEqual(shell.EXPECTED_PREDECESSOR_SHA256, shell.sha256_bytes(shell.PREDECESSOR_PATH.read_bytes()))
        self.assertEqual(shell.EXPECTED_CATALOG_SHA256, shell.sha256_bytes(shell.CATALOG_PATH.read_bytes()))

    def test_generated_contract_is_exact_and_preserves_open_claims(self) -> None:
        expected = contract_builder.build_contract()
        actual = json.loads(contract_builder.CONTRACT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(expected, actual)
        self.assertEqual([], validator.validate(actual))
        for key in (
            "actual_chatgpt_host_render_tested", "developer_mode_tested", "registered_plugin_tested",
            "hangul_or_com_invoked", "file_transfer_tested", "public_or_production_ready",
            "hangul_2022_2024_or_other_pc_tested",
        ):
            self.assertFalse(actual["claims"][key])


if __name__ == "__main__":
    unittest.main()
