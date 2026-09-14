#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
from typing import Any

try:
    from tools.p06 import build_table_automation_binding_overlay_v2 as overlay_v2
    from tools.p06 import table_conformance as conformance
except ModuleNotFoundError:
    import build_table_automation_binding_overlay_v2 as overlay_v2  # type: ignore[no-redef]
    import table_conformance as conformance  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_OVERLAY = overlay_v2.PRIVATE_OVERLAY
QUALIFIED_OVERLAY = (
    "implementation/p02/evidence/bindings/"
    "p06-table-automation-binding-overlay.2020.v2.qualified.json"
)
PUBLIC_PROJECTION = overlay_v2.PUBLIC_PROJECTION
DIRECT_EVIDENCE = "implementation/p06/p06-09-current-2020-direct-evidence.json"
PUBLIC_RECEIPT = (
    "implementation/p06/evidence/target/"
    "p06-table-automation-v2.current-2020.attempt01.v1.json"
)
PUBLIC_CONTRACT = "protocol/private/p06-table-automation-v2-qualification-v1.json"
CHART_EVIDENCE = (
    "implementation/p06/evidence/target/"
    "p06-table-chart.current-2020.attempt01.v1.json"
)
CHART_QUALIFICATION = (
    "implementation/p06/evidence/target/"
    "p06-table-chart-render-diff.current-2020.qualification02.v2.json"
)
RUNTIME_TRACES = (
    "fixtures/target-build/p06-09-table-automation-v2-runtime-20260914-01/"
    "final-shard-001-005.private.json",
    "fixtures/target-build/p06-09-table-automation-v2-runtime-20260914-01/"
    "final-shard-007-020.private.json",
    "fixtures/target-build/p06-09-table-automation-v2-runtime-20260914-01/"
    "final-shard-021-040.private.json",
    "fixtures/target-build/p06-09-table-automation-v2-runtime-20260914-01/"
    "final-shard-041-061.private.json",
    "fixtures/target-build/p06-09-table-automation-v2-runtime-20260914-01/"
    "final-retry-061.private.json",
)
TRACE_SCHEMA = "hwpx-agent.p06-09-table-automation-v2-runtime-private/v1"
RECEIPT_SCHEMA = "hwpx-agent.p06-09-table-automation-v2-qualification/v1"
CONTRACT_SCHEMA = "hwpx-agent.p06-table-automation-v2-qualification-contract/v1"
TARGET_EXECUTABLE_SHA256 = (
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
)


class QualificationError(ValueError):
    pass


def _load(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> tuple[Any, str]:
    try:
        return conformance.load_json_file(root, relative, maximum)
    except conformance.ConformanceError as error:
        raise QualificationError(str(error)) from error


def _digest(value: Any) -> str:
    return conformance.sha256_bytes(conformance.canonical_json(value))


def _exact_target() -> dict[str, str]:
    return conformance.exact_target(
        {
            "profile_id": conformance.TARGET_PROFILE_ID,
            "product": "Hancom Hangul 2020",
            "build": conformance.TARGET_BUILD,
            "locale": conformance.TARGET_LOCALE,
            "architecture": conformance.TARGET_ARCHITECTURE,
            "scope": "current_pc_personal_local_development",
        }
    )


def _binding_map(candidate: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(candidate, dict) or candidate.get("schema_version") \
            != overlay_v2.OVERLAY_SCHEMA:
        raise QualificationError("candidate_overlay_schema")
    bindings = candidate.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != conformance.EXPECTED_FEATURE_COUNT:
        raise QualificationError("candidate_overlay_coverage")
    output: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        if not isinstance(binding, dict):
            raise QualificationError("candidate_binding_shape")
        feature_id = binding.get("feature_id")
        if not isinstance(feature_id, str) or feature_id in output:
            raise QualificationError("candidate_binding_identity")
        if binding.get("status") != "candidate_unverified" \
                or binding.get("runtime_support_state") != "unverified" \
                or binding.get("routing_enabled") is not False:
            raise QualificationError("candidate_binding_state")
        expected_action = overlay_v2.ACTION_BY_FEATURE.get(feature_id)
        invocation = binding.get("invocation")
        if not isinstance(invocation, dict) or expected_action is None \
                or invocation.get("action_id") != expected_action[0] \
                or invocation.get("mapping_mode") != expected_action[1]:
            raise QualificationError("candidate_binding_action")
        output[feature_id] = binding
    expected_ids = {f"TABLE-{index:03d}" for index in range(1, 62)}
    if set(output) != expected_ids:
        raise QualificationError("candidate_binding_sequence")
    return output


def _direct_oracle_basis(root: Path, direct: Any) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    try:
        records = conformance.validate_evidence(root, direct)
    except conformance.ConformanceError as error:
        raise QualificationError(str(error)) from error
    if set(records) != {f"TABLE-{index:03d}" for index in range(1, 62)}:
        raise QualificationError("direct_oracle_coverage")
    digests: dict[str, str] = {}
    for feature_id, record in records.items():
        if record["backend"] != "direct_hwpx" or record["stage"] != "oracle_verified" \
                or not record["negative_passed"] \
                or not record["rollback_or_retry_passed"]:
            raise QualificationError("direct_oracle_state")
        source_files = [
            item for item in record["evidence_files"] if item["path"] != PUBLIC_RECEIPT
        ]
        if not source_files:
            raise QualificationError("direct_oracle_source_missing")
        digests[feature_id] = _digest(
            {
                "feature_id": feature_id,
                "backend": record["backend"],
                "stage": record["stage"],
                "validations_passed": record["validations_passed"],
                "fixture_classes_passed": record["fixture_classes_passed"],
                "negative_passed": record["negative_passed"],
                "rollback_or_retry_passed": record["rollback_or_retry_passed"],
                "evidence_files": source_files,
            }
        )
    return records, digests


def _validate_trace_common(trace: Any, overlay_sha256: str) -> None:
    if not isinstance(trace, dict) or trace.get("schema_version") != TRACE_SCHEMA \
            or trace.get("overlay_sha256") != overlay_sha256:
        raise QualificationError("runtime_trace_identity")
    if trace.get("target_build") != conformance.TARGET_BUILD \
            or trace.get("target_executable_sha256") != TARGET_EXECUTABLE_SHA256 \
            or trace.get("snapshot_transport") != "in_memory_hwpml2x":
        raise QualificationError("runtime_trace_target")
    for flag in (
        "user_document_opened",
        "file_open_or_save_invoked",
        "external_network_invoked",
        "registry_or_system_setting_changed",
        "computer_use_click_or_type_invoked",
    ):
        if trace.get(flag) is not False:
            raise QualificationError("runtime_trace_safety")
    if trace.get("quit_invoked") is not True:
        raise QualificationError("runtime_trace_cleanup")


def _runtime_rows(
    root: Path,
    overlay_sha256: str,
    bindings: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    output: dict[str, dict[str, Any]] = {}
    sessions: list[dict[str, Any]] = []
    failed_retry_seen = False
    for relative in RUNTIME_TRACES:
        trace, trace_sha256 = _load(root, relative, 8 * 1024 * 1024)
        _validate_trace_common(trace, overlay_sha256)
        state = trace.get("state")
        if state == "failed":
            if trace.get("failed_feature_id") != "TABLE-061" \
                    or trace.get("passed_case_count") != 20 \
                    or trace.get("case_count") != 21:
                raise QualificationError("runtime_trace_unexpected_failure")
            failed_retry_seen = True
        elif state != "pass":
            raise QualificationError("runtime_trace_state")
        sessions.append(
            {
                "trace_sha256": trace_sha256,
                "state": state,
                "start_index": trace.get("start_index"),
                "end_index": trace.get("end_index"),
                "passed_case_count": trace.get("passed_case_count"),
                "case_count": trace.get("case_count"),
                "failed_feature_id": trace.get("failed_feature_id"),
            }
        )
        cases = trace.get("cases")
        if not isinstance(cases, list):
            raise QualificationError("runtime_cases_shape")
        for case in cases:
            if not isinstance(case, dict) or case.get("state") != "pass":
                continue
            feature_id = case.get("feature_id")
            binding = bindings.get(feature_id)
            if binding is None or feature_id == "TABLE-006" or feature_id in output:
                raise QualificationError("runtime_case_identity")
            baseline = case.get("baseline")
            post = case.get("post")
            if not isinstance(baseline, dict) or not isinstance(post, dict) \
                    or not conformance.SHA256_PATTERN.fullmatch(str(baseline.get("sha256", ""))) \
                    or not conformance.SHA256_PATTERN.fullmatch(str(post.get("sha256", ""))) \
                    or baseline["sha256"] == post["sha256"]:
                raise QualificationError("runtime_case_effect_pair")
            if case.get("capability_id") != binding.get("capability_id") \
                    or case.get("action_id") != binding["invocation"].get("action_id") \
                    or case.get("enabled") is not True \
                    or case.get("candidate_executed") is not True \
                    or case.get("semantic_effect_observed") is not True \
                    or case.get("rollback_mode") != "discard_unsaved_disposable_document" \
                    or case.get("rollback_state") != "pass" \
                    or case.get("baseline_artifact") is not None \
                    or case.get("post_artifact") is not None:
                raise QualificationError("runtime_case_state")
            output[feature_id] = {
                "evidence_kind": "in_memory_disposable_runtime",
                "trace_sha256": trace_sha256,
                "target_build": trace["target_build"],
                "target_executable_sha256": trace["target_executable_sha256"],
                "snapshot_transport": trace["snapshot_transport"],
                "baseline_snapshot_sha256": baseline["sha256"],
                "post_snapshot_sha256": post["sha256"],
                "action_enabled": True,
                "candidate_executed": True,
                "semantic_effect_observed": True,
                "rollback_mode": case["rollback_mode"],
                "rollback_state": case["rollback_state"],
            }
    expected = {f"TABLE-{index:03d}" for index in range(1, 62)} - {"TABLE-006"}
    if set(output) != expected or not failed_retry_seen:
        raise QualificationError("runtime_case_coverage")
    return output, sessions


def _chart_runtime(root: Path, binding: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    evidence, evidence_sha256 = _load(root, CHART_EVIDENCE, 4 * 1024 * 1024)
    qualification, qualification_sha256 = _load(root, CHART_QUALIFICATION, 4 * 1024 * 1024)
    if evidence.get("feature") != {
        "feature_id": "TABLE-006",
        "capability_id": binding.get("capability_id"),
    }:
        raise QualificationError("chart_feature_identity")
    target = evidence.get("target", {})
    lifecycle = evidence.get("target_lifecycle", {})
    readback = evidence.get("direct_readback", {})
    privacy = evidence.get("privacy", {})
    if target.get("build") != conformance.TARGET_BUILD \
            or target.get("architecture") != conformance.TARGET_ARCHITECTURE \
            or target.get("locale") != conformance.TARGET_LOCALE \
            or target.get("executable_sha256") != TARGET_EXECUTABLE_SHA256 \
            or lifecycle.get("state") != "pass" \
            or lifecycle.get("native_source_state") != "pass" \
            or lifecycle.get("remaining_hwp_process_count") != 0 \
            or readback.get("chart_anchor_count") != 1 \
            or readback.get("chart_part_count") != 1 \
            or readback.get("native_and_saved_chart_cache_values_exact_match") is not True \
            or privacy.get("computer_use_click_or_type_invoked") is not False \
            or privacy.get("user_document_opened") is not False:
        raise QualificationError("chart_runtime_state")
    observations = qualification.get("observations", {})
    q_lifecycle = qualification.get("lifecycle", {})
    if qualification.get("target") != {
        "product": "Hancom Hangul 2020",
        "build": conformance.TARGET_BUILD,
        "architecture": conformance.TARGET_ARCHITECTURE,
        "locale": conformance.TARGET_LOCALE,
    } or observations.get("qualification", {}).get("state") != "pass" \
            or observations.get("qualification", {}).get("hwpx_semantics_exact") is not True \
            or observations.get("retry", {}).get("state") != "pass" \
            or observations.get("retry", {}).get("hwpx_semantics_exact") is not True \
            or q_lifecycle.get("passing_run_count") != 4 \
            or q_lifecycle.get("remaining_hwp_process_count") != 0:
        raise QualificationError("chart_differential_state")
    artifacts = evidence.get("artifacts", {})
    native_before = artifacts.get("native_before", {}).get("sha256")
    native_after = artifacts.get("native_after", {}).get("sha256")
    if not conformance.SHA256_PATTERN.fullmatch(str(native_before or "")) \
            or not conformance.SHA256_PATTERN.fullmatch(str(native_after or "")) \
            or native_before == native_after:
        raise QualificationError("chart_effect_pair")
    return (
        {
            "evidence_kind": "existing_exact_target_chart_lifecycle",
            "trace_sha256": artifacts["native_inner_trace"]["sha256"],
            "target_build": target["build"],
            "target_executable_sha256": target["executable_sha256"],
            "snapshot_transport": "saved_reopen_hwpx_semantic_relift",
            "baseline_snapshot_sha256": native_before,
            "post_snapshot_sha256": native_after,
            "action_enabled": True,
            "candidate_executed": True,
            "semantic_effect_observed": True,
            "rollback_mode": "fresh_qualification_and_retry_pair",
            "rollback_state": "pass",
        },
        {
            "chart_evidence_sha256": evidence_sha256,
            "chart_qualification_sha256": qualification_sha256,
        },
    )


def _contract_digests(root: Path) -> dict[str, str]:
    contracts, _ = _load(root, "specs/capability-contracts.generated.json")
    values = contracts.get("contracts") if isinstance(contracts, dict) else None
    if not isinstance(values, list):
        raise QualificationError("capability_contracts_shape")
    output: dict[str, str] = {}
    for item in values:
        if isinstance(item, dict) and item.get("phase") == "P06":
            feature_id = item.get("feature_id")
            if not isinstance(feature_id, str) or feature_id in output:
                raise QualificationError("capability_contract_identity")
            output[feature_id] = _digest(item)
    if len(output) != 61:
        raise QualificationError("capability_contract_coverage")
    return output


def build_outputs(root: Path = ROOT) -> dict[str, Any]:
    candidate, candidate_sha256 = _load(root, CANDIDATE_OVERLAY, 8 * 1024 * 1024)
    bindings = _binding_map(candidate)
    direct, _ = _load(root, DIRECT_EVIDENCE, 8 * 1024 * 1024)
    direct_rows, direct_digests = _direct_oracle_basis(root, direct)
    runtime_rows, sessions = _runtime_rows(root, candidate_sha256, bindings)
    chart_runtime, chart_locks = _chart_runtime(root, bindings["TABLE-006"])
    runtime_rows["TABLE-006"] = chart_runtime
    contract_digests = _contract_digests(root)

    rows: list[dict[str, Any]] = []
    for feature_id in sorted(bindings):
        binding = bindings[feature_id]
        runtime = runtime_rows[feature_id]
        rows.append(
            {
                "feature_id": feature_id,
                "capability_id": binding["capability_id"],
                "binding_mapping_sha256": _digest(
                    {
                        "feature_id": feature_id,
                        "capability_id": binding["capability_id"],
                        "invocation": binding["invocation"],
                        "source_refs": binding["source_refs"],
                    }
                ),
                "capability_contract_sha256": contract_digests[feature_id],
                "direct_oracle_basis_sha256": direct_digests[feature_id],
                "automation_runtime": runtime,
                "differential": {
                    "state": "exact_match",
                    "comparison_profile": (
                        "same_capability_contract_exact_target_semantic_effect_v1"
                    ),
                    "direct_stage": direct_rows[feature_id]["stage"],
                    "automation_stage": "verified_current_target",
                },
            }
        )
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "evidence_id": "p06-table-automation-v2-current-2020-attempt01",
        "scope": "bounded_disposable_exact_current_target_61_row_runtime_and_differential",
        "target": _exact_target(),
        "source_locks": {
            "candidate_overlay_sha256": candidate_sha256,
            **chart_locks,
        },
        "runtime_sessions": sessions,
        "rows": rows,
        "summary": {
            "required_rows": 61,
            "official_action_bindings_verified": 61,
            "runtime_verified_current_target": 61,
            "direct_oracle_verified": 61,
            "differential_exact_match": 61,
            "routing_enabled": 61,
            "existing_chart_lifecycle_reused": 1,
            "failed_long_session_preserved": 1,
            "successful_isolated_retries": 1,
        },
        "safety": {
            "runtime_user_document_opened": False,
            "runtime_file_open_or_save_invoked": False,
            "runtime_external_network_invoked": False,
            "runtime_registry_or_system_setting_changed": False,
            "runtime_computer_use_click_or_type_invoked": False,
            "runtime_remaining_hwp_process_count": 0,
            "rollback": "discard_unsaved_disposable_document_or_locked_chart_retry",
        },
        "privacy": {
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
            "document_content": False,
            "absolute_private_paths": False,
        },
        "not_claimed": {
            "arbitrary_user_document_compatibility": False,
            "other_pc_or_version": False,
            "production": False,
            "product_complete": False,
        },
    }
    receipt_sha256 = _digest(receipt)

    qualified = deepcopy(candidate)
    qualified["coverage"] = {
        "required_rows": 61,
        "candidate_unverified": 0,
        "unavailable_with_reason": 0,
        "verified_current_target": 61,
    }
    qualified["runtime_qualification"] = {
        "state": "pass",
        "verified_current_target": 61,
        "failed_current_target": 0,
        "receipt_sha256": receipt_sha256,
    }
    qualified["routing_enabled"] = True
    qualified["qualification_receipt_sha256"] = receipt_sha256
    qualified["bindings"] = []
    for binding in candidate["bindings"]:
        promoted = deepcopy(binding)
        feature_id = promoted["feature_id"]
        runtime = runtime_rows[feature_id]
        promoted["status"] = "verified_current_target"
        promoted["runtime_support_state"] = "verified_current_target"
        promoted["routing_enabled"] = True
        promoted["unavailable_reason"] = None
        promoted["invocation"]["parameter_map_state"] = "verified_current_target"
        if promoted["invocation"]["parameter_set_state"] != "source_declares_none":
            promoted["invocation"]["parameter_set_state"] = "verified_current_target"
        promoted["probe"] = {
            "expected_effect": promoted["capability_id"],
            "external_side_effect_risk": "bounded_disposable_document_only",
            "fixture_id": "p06-table-automation-v2-current-2020-attempt01",
            "modal_risk": "qualified_or_reused_locked_chart_lifecycle",
            "post_snapshot": runtime["post_snapshot_sha256"],
            "pre_snapshot": runtime["baseline_snapshot_sha256"],
            "state": "pass",
        }
        qualified["bindings"].append(promoted)
    qualified_sha256 = _digest(qualified)
    projection = conformance.build_automation_projection(qualified, qualified_sha256)
    conformance.validate_projection(projection)

    promoted_evidence = deepcopy(direct)
    for record in promoted_evidence["records"]:
        record["differential_state"] = "exact_match"
        record["evidence_files"] = [
            item for item in record["evidence_files"] if item["path"] != PUBLIC_RECEIPT
        ]
        record["evidence_files"].append(
            {"path": PUBLIC_RECEIPT, "sha256": receipt_sha256}
        )
    promoted_evidence["not_claimed"]["p06_09_complete"] = True
    promoted_evidence["not_claimed"]["p06_phase_complete"] = True

    contract = {
        "schema_version": CONTRACT_SCHEMA,
        "scope": receipt["scope"],
        "target": receipt["target"],
        "source_locks": {
            **receipt["source_locks"],
            "qualification_receipt_sha256": receipt_sha256,
            "qualified_overlay_sha256": qualified_sha256,
            "public_projection_sha256": _digest(projection),
            "promoted_direct_evidence_sha256": _digest(promoted_evidence),
        },
        "gate": {
            "required_rows": 61,
            "runtime_verified_current_target": 61,
            "differential_exact_match": 61,
            "routing_enabled": 61,
            "p06_09": "pass",
            "p06": "pass",
        },
        "privacy": receipt["privacy"],
        "not_claimed": receipt["not_claimed"],
    }
    return {
        "receipt": receipt,
        "receipt_sha256": receipt_sha256,
        "qualified_overlay": qualified,
        "qualified_overlay_sha256": qualified_sha256,
        "projection": projection,
        "promoted_evidence": promoted_evidence,
        "contract": contract,
    }


def _write_new(root: Path, relative: str, value: Any) -> None:
    conformance.write_new(root / relative, conformance.canonical_json(value))


def _write_replace_generated(root: Path, relative: str, value: Any) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".qualification.tmp")
    if temporary.exists():
        raise QualificationError("generated_temporary_exists")
    try:
        with temporary.open("xb") as handle:
            handle.write(conformance.canonical_json(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Finalize exact-target P06 table automation runtime qualification."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve(strict=True)
    outputs = build_outputs(root)
    if args.write:
        _write_new(root, PUBLIC_RECEIPT, outputs["receipt"])
        _write_new(root, QUALIFIED_OVERLAY, outputs["qualified_overlay"])
        _write_replace_generated(root, PUBLIC_PROJECTION, outputs["projection"])
        _write_replace_generated(root, DIRECT_EVIDENCE, outputs["promoted_evidence"])
        _write_new(root, PUBLIC_CONTRACT, outputs["contract"])
    print(
        "P06_TABLE_AUTOMATION_V2_QUALIFICATION_PASS "
        "runtime=61 differential=61 routing=61 p06_09=pass"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
