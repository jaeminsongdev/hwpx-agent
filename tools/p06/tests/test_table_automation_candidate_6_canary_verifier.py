from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p06 import verify_table_automation_candidate_6_canary as verifier


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def scan(seed: str, *, normal: int = 2, paragraph: int = 1) -> dict[str, object]:
    return {
        "sha256": digest(f"scan:{seed}"),
        "text_sha256": digest(f"text:{seed}"),
        "text_utf16_length": 10,
        "call_count": normal + paragraph + 3,
        "terminal_code": 1,
        "control_enter_count": 1,
        "control_exit_count": 1,
        "normal_text_chunk_count": normal,
        "next_paragraph_count": paragraph,
    }


def snapshot(seed: str, style_seed: str | None = None) -> dict[str, object]:
    scan_value = scan(seed)
    style = (
        None
        if style_seed is None
        else {"sha256": digest(f"style:{style_seed}"), "item_count": 3}
    )
    style_sha = "<not_applicable>" if style is None else style["sha256"]
    return {
        "sha256": digest(f"scan={scan_value['sha256']}\nstyle={style_sha}"),
        "scan": scan_value,
        "style": style,
    }


def fixture() -> dict[str, object]:
    action_ids = [f"PrivateAction{index}" for index in range(1, 7)]
    cases = []
    for index, ((feature, capability, _), selection) in enumerate(
        zip(verifier.EXPECTED_CASES, verifier.EXPECTED_SELECTIONS, strict=True), start=1
    ):
        invocation = {"kind": "run"}
        if index in {2, 3, 5, 6}:
            invocation = {
                "kind": "execute_default_set",
                "items": [{"name": "Synthetic", "value": index}],
            }
        if index == 5:
            invocation["items"] = [
                {
                    "name": "Synthetic",
                    "value_call": {"name": "SyntheticCall", "args": []},
                }
            ]
        cases.append(
            {
                "index": index,
                "feature_id": feature,
                "capability_id": capability,
                "action_id": action_ids[index - 1],
                "selection": selection,
                "invocation": invocation,
            }
        )
    request = {
        "schema_version": verifier.REQUEST_SCHEMA,
        "state": "planned",
        "scope": "exact_current_pc_disposable_in_memory_canary",
        "target": {
            "prog_id": "HWPFrame.HwpObject.2",
            "build": verifier.EXPECTED_BUILD,
            "architecture": "x86",
            "client": "windows_powershell_x86_sta",
            "executable_sha256": verifier.EXPECTED_EXECUTABLE_SHA256,
        },
        "inputs": {
            "source_request_sha256": "1" * 64,
            "surface_trace_sha256": "2" * 64,
            "surface_receipt_sha256": "3" * 64,
            "merge_context_trace_sha256": "4" * 64,
        },
        "session_strategy": "one_hwp_session_six_isolated_generated_3x3_documents",
        "fixture": {
            "rows": 3,
            "cols": 3,
            "cell_text_strategy": "unique_ascii_marker_per_cell",
        },
        "cases": cases,
        "policy": {
            "candidate_action_execute_count": 6,
            "fixture_action_execute_allowed": True,
            "undo_required_after_each_case": True,
            "exact_pre_post_undo_snapshot_required": True,
            "user_document_open_allowed": False,
            "file_open_or_save_allowed": False,
            "external_network_allowed": False,
            "registry_or_system_setting_write_allowed": False,
            "computer_use_click_or_type_allowed": False,
            "preexisting_hwp_process_policy": "refuse",
            "publication": "private_create_new_attempt_only",
        },
        "promotion": {
            "runtime_support_state": "component_canary_only",
            "routing_enabled": False,
            "differential_state": "not_run",
            "p06": "in_progress",
        },
    }
    request_bytes = (json.dumps(request, separators=(",", ":")) + "\n").encode()
    request_sha = hashlib.sha256(request_bytes).hexdigest()

    trace_cases = []
    public_cases = []
    contexts = (
        "current_row_boundary",
        "single_cell_block",
        "single_cell_block",
        "two_extension_multi_cell_block",
        "single_cell_block",
        "single_cell_block",
    )
    for index, ((feature, capability, channel), context) in enumerate(
        zip(verifier.EXPECTED_CASES, contexts, strict=True), start=1
    ):
        if channel == "document_scan":
            baseline = snapshot(f"baseline-{index}")
            post = snapshot(f"post-{index}")
        else:
            baseline = snapshot("stable", f"baseline-{index}")
            post = snapshot("stable", f"post-{index}")
        row = {
            "index": index,
            "feature_id": feature,
            "capability_id": capability,
            "selection_prepared": True,
            "action_enabled_before": True,
            "action_enabled_after_baseline_snapshot": True,
            "candidate_executed": True,
            "snapshot_changed": True,
            "undo_executed": True,
            "undo_exact": True,
            "baseline": baseline,
            "post": post,
            "undo": deepcopy(baseline),
            "state": "pass",
            "error_code": None,
            "exception_type": None,
            "exception_hresult": None,
        }
        trace_cases.append(row)
        public_cases.append(
            {
                "index": index,
                "feature_id": feature,
                "capability_id": capability,
                "selection_context": context,
                "enabled_before": True,
                "enabled_after_baseline_snapshot": True,
                "candidate_executed": True,
                "effect_channel": channel,
                "baseline_sha256": baseline["sha256"],
                "post_sha256": post["sha256"],
                "undo_sha256": baseline["sha256"],
                "effect_observed": True,
                "undo_exact": True,
                "state": "pass",
            }
        )
    trace = {
        "schema_version": verifier.TRACE_SCHEMA,
        "state": "pass",
        "request_sha256": request_sha,
        "target_build": verifier.EXPECTED_BUILD,
        "target_executable_sha256": verifier.EXPECTED_EXECUTABLE_SHA256,
        "hwp_process_id": 1234,
        "case_count": 6,
        "completed_case_count": 6,
        "passed_case_count": 6,
        "candidate_action_execute_count": 6,
        "cases": trace_cases,
        "user_document_opened": False,
        "file_open_or_save_invoked": False,
        "external_network_invoked": False,
        "registry_or_system_setting_changed": False,
        "computer_use_click_or_type_invoked": False,
        "quit_invoked": True,
        "error_code": None,
    }
    trace_bytes = (json.dumps(trace, separators=(",", ":")) + "\n").encode()
    trace_sha = hashlib.sha256(trace_bytes).hexdigest()
    public = {
        "schema_version": verifier.PUBLIC_SCHEMA,
        "state": "component_canary_pass",
        "scope": (
            "exact_current_pc_disposable_in_memory_effect_and_undo_canary_"
            "not_product_runtime_support"
        ),
        "recorded_at_utc": "2026-09-13T15:54:27Z",
        "target": {
            "profile_id": "hancom-hangul-2020-secondary",
            "product": "Hancom Hangul 2020",
            "build": verifier.EXPECTED_BUILD,
            "locale": "ko-KR",
            "architecture": "x86",
            "client": "windows_powershell_x86_sta",
            "executable_sha256": verifier.EXPECTED_EXECUTABLE_SHA256,
        },
        "evidence": {
            "source_surface_request_sha256": "1" * 64,
            "source_surface_trace_sha256": "2" * 64,
            "source_surface_receipt_sha256": "3" * 64,
            "snapshot_probe_trace_sha256": "4" * 64,
            "canary_request_sha256": request_sha,
            "canary_harness_sha256": "5" * 64,
            "canary_trace_sha256": trace_sha,
            "independent_invariant_validation": "pass",
            "independent_verifier": {
                "path": verifier.VERIFIER_PATH,
                "source_sha256": verifier.canonical_text_sha256(
                    ROOT / verifier.VERIFIER_PATH
                ),
                "test_count": 7,
                "state": "pass",
            },
        },
        "session": {
            "strategy": "one_hwp_session_six_isolated_generated_3x3_documents",
            "case_isolation": "fresh_disposable_document_per_case",
            "snapshot_method": (
                "whole_document_scan_status_and_text_hash_plus_selected_style_hash_"
                "when_applicable"
            ),
            "remaining_hwp_process_count": 0,
        },
        "summary": {
            "case_count": 6,
            "completed_case_count": 6,
            "passed_case_count": 6,
            "enabled_before_count": 6,
            "enabled_after_baseline_snapshot_count": 6,
            "candidate_action_execute_count": 6,
            "effect_observed_count": 6,
            "scan_effect_count": 4,
            "style_effect_count": 2,
            "undo_executed_count": 6,
            "undo_exact_count": 6,
        },
        "cases": public_cases,
        "safety": {
            "raw_action_identifiers_present": False,
            "raw_parameter_set_identifiers_present": False,
            "user_document_opened": False,
            "file_open_or_save_invoked": False,
            "external_network_invoked": False,
            "registry_or_system_setting_changed": False,
            "computer_use_click_or_type_invoked": False,
            "quit_invoked": True,
        },
        "promotion": {
            "component_canary": "pass",
            "product_runtime_support_state": "unverified",
            "routing_enabled": False,
            "differential_state": "not_run",
            "remaining_22_target_lifecycle_state": "blocked_on_user_owned_allow_all",
            "p06_09": "in_progress",
            "p06": "in_progress",
            "product_complete": False,
        },
    }
    public_bytes = (json.dumps(public, separators=(",", ":")) + "\n").encode()
    return {
        "request": request,
        "request_bytes": request_bytes,
        "request_sha": request_sha,
        "trace": trace,
        "trace_bytes": trace_bytes,
        "trace_sha": trace_sha,
        "public": public,
        "public_bytes": public_bytes,
    }


class CandidateCanaryVerifierTests(unittest.TestCase):
    def call(self, value: dict[str, object]) -> dict[str, object]:
        return verifier.verify(
            value["request"],
            value["request_bytes"],
            value["request_sha"],
            value["trace"],
            value["trace_bytes"],
            value["trace_sha"],
            value["public"],
            value["public_bytes"],
        )

    def test_complete_chain_passes_without_product_promotion(self) -> None:
        value = fixture()
        result = self.call(value)
        self.assertEqual(result["state"], "pass")
        self.assertEqual(result["undo_exact_count"], 6)
        self.assertEqual(result["runtime_support_state"], "unverified")
        self.assertEqual(result["differential_state"], "not_run")

    def test_snapshot_composite_tamper_fails(self) -> None:
        value = fixture()
        value["trace"]["cases"][0]["baseline"]["sha256"] = "f" * 64
        with self.assertRaisesRegex(
            verifier.CanaryVerificationError, "snapshot_composite_sha256"
        ):
            self.call(value)

    def test_scan_only_and_style_only_effects_are_distinct(self) -> None:
        value = fixture()
        value["trace"]["cases"][4]["post"]["scan"] = deepcopy(
            value["trace"]["cases"][0]["post"]["scan"]
        )
        with self.assertRaisesRegex(
            verifier.CanaryVerificationError, "snapshot_composite_sha256|style_effect_boundary"
        ):
            self.call(value)

    def test_non_exact_undo_fails(self) -> None:
        value = fixture()
        value["trace"]["cases"][2]["undo"] = deepcopy(
            value["trace"]["cases"][2]["post"]
        )
        with self.assertRaisesRegex(verifier.CanaryVerificationError, "undo_not_exact"):
            self.call(value)

    def test_raw_action_identifier_in_trace_fails(self) -> None:
        value = fixture()
        value["trace_bytes"] += b"PrivateAction1"
        with self.assertRaisesRegex(
            verifier.CanaryVerificationError, "raw_private_identifier_in_trace"
        ):
            self.call(value)

    def test_public_projection_mismatch_fails(self) -> None:
        value = fixture()
        value["public"]["cases"][0]["post_sha256"] = "e" * 64
        with self.assertRaisesRegex(
            verifier.CanaryVerificationError, "public_case_projection"
        ):
            self.call(value)

    def test_product_promotion_claim_fails(self) -> None:
        value = fixture()
        value["public"]["promotion"]["product_runtime_support_state"] = (
            "verified_current_target"
        )
        with self.assertRaisesRegex(verifier.CanaryVerificationError, "public_boundary"):
            self.call(value)


if __name__ == "__main__":
    unittest.main()
