from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest

from tools.p06 import plan_table_automation_candidate_32_batch as planner


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / (
    "implementation/p06/tools/"
    "run-hancom-2020-table-automation-candidate-32-surface.ps1"
)
CHILD = ROOT / (
    "implementation/p06/tools/"
    "run-hancom-2020-table-automation-candidate-32-surface-child.ps1"
)
BUILDER = ROOT / "tools/p06/build_table_automation_candidate_32_surface_evidence.py"
PUBLIC_EVIDENCE = ROOT / (
    "implementation/p06/evidence/target/"
    "p06-table-automation-candidate-32-surface.current-2020.attempt01.v1.json"
)
EXPECTED_REQUEST_SHA256 = (
    "8ad49a2a9f1057fd3e474fd5a56b4ff838e383f821a09f525ce9d9d72a2cbfd4"
)
EXPECTED_FIXTURE_CONTROLS_SHA256 = (
    "f491e8651ffc84c215b929779afaffa0dd99a4cfa3171f6a8e55928412af7e8a"
)
EXPECTED_CHILD_SOURCE_SHA256 = (
    "4c6ecb8e422b88ce44e43c03403afa438c29d8fe0c7f0973d01658e524cdfb30"
)


class Candidate32SurfaceScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = PARENT.read_text(encoding="utf-8")
        cls.child = CHILD.read_text(encoding="utf-8")
        cls.builder = BUILDER.read_text(encoding="utf-8")
        cls.evidence_text = PUBLIC_EVIDENCE.read_text(encoding="utf-8")
        cls.evidence = json.loads(cls.evidence_text)

    def test_exact_private_input_and_child_identities_are_locked(self) -> None:
        self.assertIn(EXPECTED_REQUEST_SHA256, self.parent)
        self.assertIn(EXPECTED_FIXTURE_CONTROLS_SHA256, self.parent)
        self.assertIn(EXPECTED_CHILD_SOURCE_SHA256, self.parent)
        self.assertIn("Get-NormalizedTextSha256 -Path $childPath", self.parent)
        self.assertIn(
            "p06-09-table-automation-candidate-32-20260914-02", self.parent
        )

    def test_one_session_32_isolated_documents_contract_matches(self) -> None:
        strategy = "one_hwp_session_32_isolated_disposable_documents"
        self.assertIn(strategy, self.parent)
        self.assertIn(strategy, self.child)
        self.assertIn("for ($index = 0; $index -lt 32; $index += 1)", self.child)
        self.assertIn("$document = $documents.Add($false)", self.child)
        self.assertIn("$document.Close($false)", self.child)

    def test_exact_candidate_feature_and_context_order_is_locked(self) -> None:
        features = re.search(
            r"\$expectedFeatures = @\((.*?)\)\r?\n\$expectedContexts", self.child, re.S
        )
        contexts = re.search(
            r"\$expectedContexts = @\((.*?)\)\r?\n\$expectedControlKeys", self.child, re.S
        )
        self.assertIsNotNone(features)
        self.assertIsNotNone(contexts)
        assert features is not None and contexts is not None
        self.assertEqual(
            tuple(re.findall(r"'(TABLE-\d{3})'", features.group(1))),
            tuple(feature_id for feature_id, _, _ in planner.EXPECTED_ROWS),
        )
        self.assertEqual(
            tuple(re.findall(r"'([a-z_]+)'", contexts.group(1))),
            tuple(context for _, _, context in planner.EXPECTED_ROWS),
        )

    def test_candidate_under_probe_is_never_executed(self) -> None:
        self.assertNotIn("$action.Execute(", self.child)
        self.assertNotIn("HAction.Execute([string]$case.action_id", self.child)
        self.assertIn("HAction.Execute($fixtureCreateAction", self.child)
        self.assertIn("candidate_under_probe_execute_count = 0", self.child)
        self.assertIn("candidate_under_probe_execute_allowed = $false", self.parent)

    def test_fixture_execution_is_exact_and_non_promoting(self) -> None:
        self.assertIn("table_create_fixture_action_execute_count += 1", self.child)
        self.assertIn("table_create_fixture_action_execute_count -ne 30", self.child)
        self.assertIn("fixture_control_action_execute_count -ne 176", self.child)
        self.assertIn("table_create_fixture_action_execute_count -eq 30", self.parent)
        self.assertIn("fixture_control_action_execute_count -eq 176", self.parent)
        self.assertIn("runtime_support_state = 'not_eligible'", self.parent)
        self.assertIn("routing_enabled = $false", self.parent)

    def test_probe_is_batched_and_read_only(self) -> None:
        for marker in (
            "$hwp.IsActionEnable([string]$case.action_id)",
            "$hwp.CreateAction([string]$case.action_id)",
            "$action.CreateSet()",
            "$action.GetDefault($actionSet)",
        ):
            self.assertIn(marker, self.child)
        self.assertIn("user_document_opened = $false", self.child)
        self.assertIn("file_open_or_save_invoked = $false", self.child)
        self.assertIn("external_network_invoked = $false", self.child)
        self.assertIn("registry_or_system_setting_changed = $false", self.child)

    def test_trace_redacts_identifiers_and_runtime_errors(self) -> None:
        self.assertIn("action_id_sha256 = Get-Sha256String", self.child)
        self.assertIn("parameter_set_id_sha256 = if", self.child)
        self.assertIn("Get-RedactedErrorCode", self.child)
        self.assertNotIn("$trace.error_code = [string]$_.Exception.Message", self.child)
        self.assertIn("raw_action_or_parameter_identifier_present = $false", self.child)
        self.assertIn("$rawIdentifiersAbsent", self.parent)

    def test_private_fixture_controls_are_data_not_public_literals(self) -> None:
        self.assertIn("$fixtureControls.PSObject.Properties", self.parent)
        self.assertIn("$controls.PSObject.Properties", self.child)
        self.assertIn("$controls.table_cell_block_row", self.child)
        self.assertIn("$controls.table_cell_block_column", self.child)

    def test_windows_powershell_51_compatibility_markers(self) -> None:
        for forbidden in ("::HashData", "::ToHexString", "ConvertFrom-Json -Depth"):
            self.assertNotIn(forbidden, self.child)
        self.assertIn("[Security.Cryptography.SHA256]::Create()", self.child)
        self.assertIn("WindowsPowerShell\\v1.0\\powershell.exe", self.parent)
        self.assertIn("'-STA'", self.parent)

    def test_configuration_only_path_precedes_mutation(self) -> None:
        config_index = self.parent.index("if ($ValidateConfigurationOnly)")
        output_index = self.parent.index("$tracePath = Join-Path")
        start_index = self.parent.index("[void]$child.Start()")
        self.assertLess(config_index, output_index)
        self.assertLess(config_index, start_index)
        config_block = self.parent[config_index:output_index]
        self.assertIn("hwp_invoked = $false", config_block)
        self.assertIn("output_written = $false", config_block)

    def test_actual_run_refuses_preexisting_hwp_and_is_bounded(self) -> None:
        refusal = self.parent.index("CANDIDATE_32_PREEXISTING_HWP_PROCESS")
        start = self.parent.index("[void]$child.Start()")
        self.assertLess(refusal, start)
        self.assertIn("$child.WaitForExit($TimeoutSeconds * 1000)", self.parent)
        self.assertIn("Stop-OwnedHwpProcesses", self.parent)
        self.assertIn("[IO.FileMode]::CreateNew", self.parent)

    def test_child_source_hash_matches_wrapper_lock(self) -> None:
        normalized = self.child.replace("\r\n", "\n").encode("utf-8")
        self.assertEqual(hashlib.sha256(normalized).hexdigest(), EXPECTED_CHILD_SOURCE_SHA256)

    def test_evidence_builder_locks_and_redacts_private_inputs(self) -> None:
        for expected in (
            EXPECTED_REQUEST_SHA256,
            EXPECTED_FIXTURE_CONTROLS_SHA256,
            EXPECTED_CHILD_SOURCE_SHA256,
            "2b6a81b35831972218f7d40d281421539efb21d3d94c760c0fe3508c8a02fda5",
            "8cc86420e8820d030d5081dad5c2e22e3790fe4ed11b889a227d06c3dda0be40",
        ):
            self.assertIn(expected, self.builder)
        self.assertIn("private_identifier_leak", self.builder)
        self.assertIn('with OUTPUT.open("xb")', self.builder)

    def test_public_evidence_is_exact_and_non_promoting(self) -> None:
        evidence = self.evidence
        self.assertEqual(evidence["state"], "component_pass")
        self.assertEqual(evidence["summary"]["case_count"], 32)
        self.assertEqual(evidence["summary"]["completed_case_count"], 32)
        self.assertEqual(evidence["summary"]["enabled_in_context_count"], 22)
        self.assertEqual(evidence["summary"]["disabled_in_context_count"], 10)
        self.assertEqual(evidence["summary"]["default_read_passed_count"], 14)
        self.assertEqual(
            evidence["summary"]["table_create_fixture_action_execute_count"], 30
        )
        self.assertEqual(evidence["summary"]["fixture_control_action_execute_count"], 176)
        self.assertEqual(evidence["summary"]["candidate_under_probe_execute_count"], 0)
        self.assertEqual(
            tuple(case["feature_id"] for case in evidence["cases"]),
            tuple(feature_id for feature_id, _, _ in planner.EXPECTED_ROWS),
        )
        self.assertNotIn('"action_id"', self.evidence_text)
        self.assertNotIn('"parameter_set_id"', self.evidence_text)
        self.assertFalse(evidence["safety"]["raw_action_identifiers_present"])
        self.assertFalse(evidence["safety"]["raw_parameter_set_identifiers_present"])
        self.assertEqual(evidence["promotion"]["runtime_support_state"], "unverified")
        self.assertFalse(evidence["promotion"]["routing_enabled"])
        self.assertEqual(evidence["promotion"]["differential_state"], "not_run")
        self.assertFalse(evidence["promotion"]["product_complete"])


if __name__ == "__main__":
    unittest.main()
