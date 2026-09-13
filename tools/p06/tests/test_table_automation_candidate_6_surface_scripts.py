from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
PARENT = ROOT / "implementation/p06/tools/run-hancom-2020-table-automation-candidate-6-surface.ps1"
CHILD = ROOT / "implementation/p06/tools/run-hancom-2020-table-automation-candidate-6-surface-child.ps1"
PLANNER = ROOT / "tools/p06/plan_table_automation_candidate_6_batch.py"
PUBLIC_EVIDENCE = ROOT / (
    "implementation/p06/evidence/target/"
    "p06-table-automation-candidate-6-surface.current-2020.attempt02.v1.json"
)
EXPECTED_REQUEST_SHA256 = (
    "d9588469b901ec31136e15f657b772f93872943c0411ac7b4794ba4feca31355"
)
EXPECTED_CHILD_SOURCE_SHA256 = (
    "bc26252065a2f060b9cd718e3876600ee098a9b9ea28562268a912ace77f0eab"
)
EXPECTED_FEATURES = (
    "TABLE-010",
    "TABLE-015",
    "TABLE-016",
    "TABLE-017",
    "TABLE-046",
    "TABLE-048",
)


class CandidateSixSurfaceScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parent = PARENT.read_text(encoding="utf-8")
        cls.child = CHILD.read_text(encoding="utf-8")
        cls.planner = PLANNER.read_text(encoding="utf-8")
        cls.evidence_text = PUBLIC_EVIDENCE.read_text(encoding="utf-8")
        cls.evidence = json.loads(cls.evidence_text)

    def test_exact_create_new_request_identity_is_locked(self) -> None:
        self.assertIn(EXPECTED_REQUEST_SHA256, self.parent)
        self.assertIn(EXPECTED_REQUEST_SHA256, self.child)
        self.assertIn(EXPECTED_CHILD_SOURCE_SHA256, self.parent)
        self.assertIn("Get-NormalizedTextSha256 -Path $childPath", self.parent)
        self.assertIn(
            "p06-09-table-automation-candidate-6-20260914-02", self.parent
        )
        self.assertIn(
            "p06-09-table-automation-candidate-6-20260914-02", self.child
        )

    def test_one_session_six_isolated_documents_contract_matches(self) -> None:
        strategy = "one_hwp_session_six_generated_3x3_documents"
        self.assertIn(strategy, self.planner)
        self.assertIn(strategy, self.parent)
        self.assertIn(strategy, self.child)
        self.assertIn("for ($index = 0; $index -lt 6; $index += 1)", self.child)
        self.assertIn("$document = $documents.Add($false)", self.child)
        self.assertIn("$document.Close($false)", self.child)

    def test_exact_candidate_feature_order_is_locked(self) -> None:
        match = re.search(r"\$expectedFeatures = @\((.*?)\)\r?\n", self.child)
        self.assertIsNotNone(match)
        self.assertEqual(
            tuple(re.findall(r"'((?:TABLE)-\d{3})'", match.group(1))),
            EXPECTED_FEATURES,
        )

    def test_candidate_actions_are_never_executed(self) -> None:
        self.assertNotIn("$action.Execute(", self.child)
        self.assertNotIn("$hwp.HAction.Execute([string]$case.action_id", self.child)
        self.assertEqual(self.child.count("$hwp.HAction.Execute('TableCreate'"), 1)
        self.assertIn("candidate_action_execute_count = 0", self.child)
        self.assertIn("candidate_action_execute_allowed = $false", self.parent)

    def test_probe_is_batched_and_read_only(self) -> None:
        for marker in (
            "$hwp.IsActionEnable([string]$case.action_id)",
            "$hwp.CreateAction([string]$case.action_id)",
            "$action.CreateSet()",
            "$action.GetDefault($actionSet)",
        ):
            self.assertIn(marker, self.child)
        self.assertIn("user_document_opened = $false", self.child)
        self.assertIn("external_network_invoked = $false", self.child)
        self.assertIn("registry_or_system_setting_changed = $false", self.child)

    def test_trace_redacts_identifiers_and_runtime_errors(self) -> None:
        self.assertIn("action_id_sha256 = Get-Sha256String", self.child)
        self.assertIn("parameter_set_id_sha256 = if", self.child)
        self.assertIn("Get-RedactedErrorCode", self.child)
        self.assertNotIn("$trace.error_code = [string]$_.Exception.Message", self.child)
        self.assertIn("raw_action_identifier_present = $false", self.child)
        self.assertIn("raw_action_or_parameter_identifier_present_in_trace", self.parent)

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
        refusal = self.parent.index("CANDIDATE_SURFACE_PREEXISTING_HWP_PROCESS")
        start = self.parent.index("[void]$child.Start()")
        self.assertLess(refusal, start)
        self.assertIn("$child.WaitForExit($TimeoutSeconds * 1000)", self.parent)
        self.assertIn("Stop-OwnedHwpProcesses", self.parent)
        self.assertIn("[IO.FileMode]::CreateNew", self.parent)

    def test_receipt_cannot_promote_runtime_or_routing(self) -> None:
        self.assertIn("scope = 'read_only_action_surface_batch_not_runtime_support'", self.parent)
        self.assertIn("runtime_support_state = 'not_eligible'", self.parent)
        self.assertIn("routing_enabled = $false", self.parent)
        self.assertIn("candidate_action_execute_count -eq 0", self.parent)

    def test_public_evidence_is_exact_and_non_promoting(self) -> None:
        evidence = self.evidence
        self.assertEqual(evidence["state"], "component_pass")
        self.assertEqual(evidence["evidence"]["request_sha256"], EXPECTED_REQUEST_SHA256)
        self.assertEqual(evidence["summary"]["case_count"], 6)
        self.assertEqual(evidence["summary"]["completed_case_count"], 6)
        self.assertEqual(evidence["summary"]["enabled_in_context_count"], 5)
        self.assertEqual(evidence["summary"]["disabled_in_context_count"], 1)
        self.assertEqual(evidence["summary"]["default_read_passed_count"], 4)
        self.assertEqual(evidence["summary"]["candidate_action_execute_count"], 0)
        self.assertEqual(
            tuple(case["feature_id"] for case in evidence["cases"]),
            EXPECTED_FEATURES,
        )
        self.assertEqual(
            [case["feature_id"] for case in evidence["cases"] if not case["is_action_enable"]],
            ["TABLE-017"],
        )
        self.assertNotIn('"action_id"', self.evidence_text)
        self.assertNotIn('"parameter_set_id"', self.evidence_text)
        self.assertFalse(evidence["safety"]["raw_action_identifiers_present"])
        self.assertFalse(evidence["safety"]["raw_parameter_set_identifiers_present"])
        self.assertEqual(evidence["promotion"]["runtime_support_state"], "unverified")
        self.assertFalse(evidence["promotion"]["routing_enabled"])
        self.assertEqual(evidence["promotion"]["differential_state"], "not_run")
        self.assertFalse(evidence["promotion"]["product_complete"])

    def test_tracked_script_hashes_are_stable_values(self) -> None:
        for path in (PARENT, CHILD):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertRegex(digest, r"[0-9a-f]{64}\Z")


if __name__ == "__main__":
    unittest.main()
