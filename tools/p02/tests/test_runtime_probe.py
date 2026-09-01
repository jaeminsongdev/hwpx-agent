from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.p02.plan_runtime_probe import ProbePlanConfig, build_request, serialize
from tools.p02.verify_runtime_probe import ProbeVerificationConfig, verify


ROOT = Path(__file__).resolve().parents[3]
PROFILE_PATH = ROOT / "implementation/p00/target-profile.yaml"
CONTRACTS_PATH = ROOT / "specs/capability-contracts.generated.json"
PROFILE_SHA = hashlib.sha256(PROFILE_PATH.read_bytes()).hexdigest()
CONTRACTS_SHA = hashlib.sha256(CONTRACTS_PATH.read_bytes()).hexdigest()
EXECUTABLE_SHA = "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"


def source_refs() -> list[dict]:
    return [
        {
            "kind": "reviewed_catalog_node",
            "artifact_sha256": "1" * 64,
            "node_id": "node:" + "1" * 24,
            "record_id": None,
            "source_id": None,
            "source_sha256": None,
        },
        {
            "kind": "automation_source_record",
            "artifact_sha256": "2" * 64,
            "node_id": None,
            "record_id": "synthetic-record",
            "source_id": "synthetic-source",
            "source_sha256": "3" * 64,
        },
    ]


def binding(
    feature_id: str,
    capability_id: str,
    scope_class: str,
    action_id: str,
    parameter_set_id: str | None,
) -> dict:
    parameter_state = (
        "documented_candidate" if parameter_set_id is not None else "source_declares_none"
    )
    return {
        "binding_key": (
            f"{capability_id}@hancom-hangul-2020-secondary/11.0.0.9136/ko-KR"
        ),
        "feature_id": feature_id,
        "capability_id": capability_id,
        "scope_class": scope_class,
        "support_level": "AUTOMATION_FULL",
        "preferred_backend": "desktop_automation",
        "fallback_backend": "",
        "target_profile_id": "hancom-hangul-2020-secondary",
        "status": "candidate_unverified",
        "unavailable_reason": None,
        "invocation": {
            "kind": "action",
            "action_id": action_id,
            "parameter_set_id": parameter_set_id,
            "parameter_set_state": parameter_state,
            "parameter_map": [],
            "parameter_map_state": "pending_runtime_probe",
        },
        "source_refs": source_refs(),
        "raw_identifiers_present": True,
        "runtime_support_state": "unverified",
        "routing_enabled": False,
        "probe": {
            "state": "not_run",
            "fixture_id": None,
            "pre_snapshot": None,
            "post_snapshot": None,
            "expected_effect": capability_id,
            "modal_risk": "unknown",
            "external_side_effect_risk": "unknown",
        },
    }


def synthetic_registry() -> dict:
    bindings = [
        binding("EDIT-004", "edit.copy", "editor_workflow", "SyntheticCopy", None),
        binding("EDIT-016", "edit.go_to", "editor_workflow", "SyntheticGoto", "SyntheticGotoSet"),
        binding("EDIT-002", "edit.redo", "editor_workflow", "SyntheticRedo", None),
        binding("EDIT-001", "edit.undo", "editor_workflow", "SyntheticUndo", None),
    ]
    return {
        "schema_version": "hwpx-agent.automation-binding-registry/v1",
        "source_lock_id": "source-lock-synthetic-p02-runtime",
        "generator": {
            "generator_id": "target-automation-binding-generator",
            "generator_version": "0.1.0",
            "raw_identifier_policy": "restricted_private_only",
            "runtime_execution_performed": False,
        },
        "restricted_derivative": True,
        "target": {
            "profile_id": "hancom-hangul-2020-secondary",
            "product": "Hancom Hangul 2020",
            "major_release": "2020",
            "exact_build": "11.0.0.9136",
            "locale": "ko-KR",
            "architecture": "x86",
            "profile_sha256": PROFILE_SHA,
            "license_state": "approved",
            "automation_release_state": "allowed_for_bounded_personal_noncommercial_local_validation_only",
            "image_digest": None,
            "routing_enabled": False,
        },
        "inputs": {
            "reviewed_catalog_sha256": "4" * 64,
            "canonical_matrix_sha256": "5" * 64,
            "automation_records_sha256": "6" * 64,
        },
        "runtime_qualification": {
            "state": "not_run",
            "probe_required": True,
            "qualified_binding_count": 0,
        },
        "bindings": bindings,
        "coverage": {
            "required_capability_count": 4,
            "automation_full_count": 4,
            "hybrid_count": 0,
            "binding_count": 4,
            "candidate_unverified_count": 4,
            "unavailable_count": 0,
            "unresolved_count": 0,
            "duplicate_capability_count": 0,
            "raw_identifier_binding_count": 4,
            "runtime_qualified_count": 0,
            "routing_enabled_count": 0,
        },
    }


def contracts() -> dict[str, dict]:
    root = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
    return {row["capability_id"]: row for row in root["contracts"]}


def plan_config(registry_sha: str) -> ProbePlanConfig:
    return ProbePlanConfig(
        registry=Path("unused-registry"),
        registry_sha256=registry_sha,
        target_profile=PROFILE_PATH,
        profile_sha256=PROFILE_SHA,
        contracts=CONTRACTS_PATH,
        contracts_sha256=CONTRACTS_SHA,
        request_id="a" * 32,
        fixture_id="b" * 32,
        timeout_seconds=120,
        output_root=Path("unused-output"),
        output_relative="unused.json",
    )


def passing_trace(request: dict, request_sha: str, registry_sha: str) -> dict:
    input_sha = "a" * 64
    rows = []
    for probe in request["probes"]:
        capability_id = probe["capability_id"]
        row = {
            "binding_key": probe["binding_key"],
            "feature_id": probe["feature_id"],
            "capability_id": capability_id,
            "planned_execution": probe["execution_plan"],
            "disposition": probe["planned_disposition"],
            "reason_code": probe["reason_code"],
            "default_read_state": (
                "not_applicable"
                if probe["parameter_set_state"] == "source_declares_none"
                else "not_run"
            ),
            "default_member_count": 0,
            "default_shape_sha256": None,
            "execute_state": "not_run",
            "return_value_kind": "not_run",
            "pre_snapshot_sha256": None,
            "post_snapshot_sha256": None,
            "expected_effect_observed": False,
            "error_type": None,
            "error_hresult": None,
            "error_message_sha256": None,
        }
        if capability_id == "edit.go_to":
            row["default_read_state"] = "pass"
            row["default_member_count"] = 3
            row["default_shape_sha256"] = "d" * 64
            row["reason_code"] = "safe_default_read_pass_execution_not_run"
        elif capability_id == "edit.undo":
            row.update(
                disposition="verified",
                reason_code="fixture_removed_exact_2020",
                execute_state="pass",
                return_value_kind="true",
                pre_snapshot_sha256=input_sha,
                post_snapshot_sha256="b" * 64,
                expected_effect_observed=True,
            )
        elif capability_id == "edit.redo":
            row.update(
                disposition="verified",
                reason_code="fixture_restored_exact_2020",
                execute_state="pass",
                return_value_kind="true",
                pre_snapshot_sha256="b" * 64,
                post_snapshot_sha256=input_sha,
                expected_effect_observed=True,
            )
        rows.append(row)
    phases = {
        name: "pass"
        for name in (
            "com_create",
            "version_check",
            "document_add",
            "fixture_insert",
            "default_parameter_read",
            "undo_canary",
            "redo_canary",
            "hwpx_save",
            "document_close_before_reopen",
            "hwpx_reopen",
            "semantic_reopen",
            "document_close",
            "quit",
        )
    }
    return {
        "schema_version": "hwpx-agent.runtime-probe-trace/v1",
        "request_id": request["request_id"],
        "request_sha256": request_sha,
        "registry_sha256": registry_sha,
        "target_profile_id": "hancom-hangul-2020-secondary",
        "exact_build": "11.0.0.9136",
        "apartment_state": "STA",
        "automation_version_normalized": "11.0.0.9136",
        "fixture": {
            "fixture_id": request["fixture"]["fixture_id"],
            "input_sha256": input_sha,
            "bootstrap_default_member_count": 3,
            "bootstrap_default_shape_sha256": "f" * 64,
            "undo_snapshot_sha256": "b" * 64,
            "redo_snapshot_sha256": input_sha,
            "reopen_snapshot_sha256": input_sha,
            "output_hwpx_sha256": "c" * 64,
            "reopen_exact_match": True,
        },
        "phases": phases,
        "probe_results": rows,
        "state": "pass",
        "error_code": None,
        "failed_phase": None,
        "exception_type": None,
        "exception_hresult": None,
        "exception_message_sha256": None,
        "quit_invoked": True,
        "user_document_opened": False,
        "external_network_invoked": False,
        "registry_or_system_setting_changed": False,
    }


def passing_receipt(request: dict, request_sha: str, trace_sha: str, registry_sha: str) -> dict:
    return {
        "schema_version": "hwpx-agent.runtime-probe-receipt/v1",
        "request_id": request["request_id"],
        "request_sha256": request_sha,
        "trace_sha256": trace_sha,
        "registry_sha256": registry_sha,
        "profile_sha256": PROFILE_SHA,
        "state": "pass",
        "error_code": None,
        "target": {
            "profile_id": "hancom-hangul-2020-secondary",
            "observed_file_version": "11.0.0.9136",
            "observed_executable_sha256": EXECUTABLE_SHA,
            "automation_version_normalized": "11.0.0.9136",
            "identity_match": True,
            "registry_view": "Registry32",
            "client_apartment_state": "STA",
        },
        "runtime": {
            "timeout_seconds": 120,
            "timed_out": False,
            "child_exit_code": 0,
            "unexpected_window_observed": False,
            "observed_process_count": 2,
            "cleaned_process_count": 0,
            "cleanup_refused_count": 0,
            "cleanup_error_count": 0,
            "remaining_hwp_process_count": 0,
        },
        "coverage": {
            "candidate_count": 4,
            "verified": 2,
            "failed": 0,
            "blocked_by_risk": 1,
            "not_run": 1,
        },
        "privacy": {
            "restricted_output": True,
            "raw_identifiers_present": False,
            "default_values_present": False,
            "absolute_private_paths_present": False,
            "user_document_opened": False,
            "external_network_invoked": False,
            "registry_or_system_setting_changed": False,
            "computer_use_click_or_type_invoked": False,
        },
    }


class RuntimeProbeTests(unittest.TestCase):
    def test_plan_is_bounded_and_deterministic(self) -> None:
        registry = synthetic_registry()
        registry_sha = hashlib.sha256(serialize(registry)).hexdigest()
        first = build_request(plan_config(registry_sha), registry, contracts())
        second = build_request(plan_config(registry_sha), deepcopy(registry), contracts())
        self.assertEqual(serialize(first), serialize(second))
        self.assertEqual(first["coverage"], {
            "candidate_count": 4,
            "safe_canary_count": 2,
            "default_read_count": 1,
            "blocked_by_risk_count": 1,
            "planned_not_run_count": 1,
        })
        self.assertEqual(
            {row["capability_id"] for row in first["probes"] if row["execution_plan"] == "safe_canary"},
            {"edit.undo", "edit.redo"},
        )

    def test_verifier_accepts_complete_synthetic_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = synthetic_registry()
            registry_bytes = serialize(registry)
            registry_sha = hashlib.sha256(registry_bytes).hexdigest()
            request = build_request(plan_config(registry_sha), registry, contracts())
            request_bytes = serialize(request)
            request_sha = hashlib.sha256(request_bytes).hexdigest()
            trace = passing_trace(request, request_sha, registry_sha)
            trace_bytes = serialize(trace)
            trace_sha = hashlib.sha256(trace_bytes).hexdigest()
            receipt = passing_receipt(request, request_sha, trace_sha, registry_sha)
            paths = {
                "registry": root / "registry.json",
                "request": root / "request.json",
                "trace": root / "trace.json",
                "receipt": root / "receipt.json",
            }
            paths["registry"].write_bytes(registry_bytes)
            paths["request"].write_bytes(request_bytes)
            paths["trace"].write_bytes(trace_bytes)
            paths["receipt"].write_bytes(serialize(receipt))
            result = verify(
                ProbeVerificationConfig(
                    registry=paths["registry"],
                    registry_sha256=registry_sha,
                    target_profile=PROFILE_PATH,
                    profile_sha256=PROFILE_SHA,
                    contracts=CONTRACTS_PATH,
                    contracts_sha256=CONTRACTS_SHA,
                    request=paths["request"],
                    trace=paths["trace"],
                    receipt=paths["receipt"],
                )
            )
            self.assertEqual(result["state"], "pass", result["errors"])

    def test_verifier_rejects_semantic_reopen_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = synthetic_registry()
            registry_bytes = serialize(registry)
            registry_sha = hashlib.sha256(registry_bytes).hexdigest()
            request = build_request(plan_config(registry_sha), registry, contracts())
            request_bytes = serialize(request)
            request_sha = hashlib.sha256(request_bytes).hexdigest()
            trace = passing_trace(request, request_sha, registry_sha)
            trace["fixture"]["reopen_snapshot_sha256"] = "e" * 64
            trace_bytes = serialize(trace)
            trace_sha = hashlib.sha256(trace_bytes).hexdigest()
            receipt = passing_receipt(request, request_sha, trace_sha, registry_sha)
            paths = {
                "registry": root / "registry.json",
                "request": root / "request.json",
                "trace": root / "trace.json",
                "receipt": root / "receipt.json",
            }
            paths["registry"].write_bytes(registry_bytes)
            paths["request"].write_bytes(request_bytes)
            paths["trace"].write_bytes(trace_bytes)
            paths["receipt"].write_bytes(serialize(receipt))
            result = verify(
                ProbeVerificationConfig(
                    registry=paths["registry"],
                    registry_sha256=registry_sha,
                    target_profile=PROFILE_PATH,
                    profile_sha256=PROFILE_SHA,
                    contracts=CONTRACTS_PATH,
                    contracts_sha256=CONTRACTS_SHA,
                    request=paths["request"],
                    trace=paths["trace"],
                    receipt=paths["receipt"],
                )
            )
            self.assertEqual(result["state"], "failed")
            self.assertTrue(any("semantic chain" in error for error in result["errors"]))

    def test_verifier_accepts_isolated_default_binding_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = synthetic_registry()
            registry_bytes = serialize(registry)
            registry_sha = hashlib.sha256(registry_bytes).hexdigest()
            request = build_request(plan_config(registry_sha), registry, contracts())
            request_bytes = serialize(request)
            request_sha = hashlib.sha256(request_bytes).hexdigest()
            trace = passing_trace(request, request_sha, registry_sha)
            default_result = next(
                row for row in trace["probe_results"] if row["capability_id"] == "edit.go_to"
            )
            default_result.update(
                disposition="failed",
                reason_code="default_read_parameter_set_resolve_failed",
                default_read_state="failed",
                default_member_count=0,
                default_shape_sha256=None,
                error_type="Synthetic.ComException",
                error_hresult=-1,
                error_message_sha256="9" * 64,
            )
            trace_bytes = serialize(trace)
            trace_sha = hashlib.sha256(trace_bytes).hexdigest()
            receipt = passing_receipt(request, request_sha, trace_sha, registry_sha)
            receipt["coverage"].update(failed=1, not_run=0)
            paths = {
                "registry": root / "registry.json",
                "request": root / "request.json",
                "trace": root / "trace.json",
                "receipt": root / "receipt.json",
            }
            paths["registry"].write_bytes(registry_bytes)
            paths["request"].write_bytes(request_bytes)
            paths["trace"].write_bytes(trace_bytes)
            paths["receipt"].write_bytes(serialize(receipt))
            result = verify(
                ProbeVerificationConfig(
                    registry=paths["registry"],
                    registry_sha256=registry_sha,
                    target_profile=PROFILE_PATH,
                    profile_sha256=PROFILE_SHA,
                    contracts=CONTRACTS_PATH,
                    contracts_sha256=CONTRACTS_SHA,
                    request=paths["request"],
                    trace=paths["trace"],
                    receipt=paths["receipt"],
                )
            )
            self.assertEqual(result["state"], "pass", result["errors"])


if __name__ == "__main__":
    unittest.main()
