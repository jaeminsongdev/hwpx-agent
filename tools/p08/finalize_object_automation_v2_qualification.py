#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_OVERLAY = Path(
    "implementation/p02/evidence/bindings/"
    "p08-object-automation-binding-overlay.2020.v1.json"
)
QUALIFIED_OVERLAY = Path(
    "implementation/p02/evidence/bindings/"
    "p08-object-automation-binding-overlay.2020.v2.qualified.json"
)
PUBLIC_RECEIPT = Path(
    "implementation/p08/evidence/"
    "p08-25-object-automation-v2-qualification.current-2020.v1.json"
)
PUBLIC_PROJECTION = Path(
    "implementation/p08/p08-09-current-2020-automation-projection.json"
)
PUBLIC_CONTRACT = Path(
    "protocol/private/p08-object-automation-v2-qualification-v1.json"
)
DIRECT_EVIDENCE = Path("implementation/p08/p08-09-current-2020-direct-evidence.json")
TARGET_QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-20-object-target-qualification.current-2020.v1.json"
)
ASPECT_QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-21-aspect-lock-negative-qualification.current-2020.v1.json"
)
CANARY_QUALIFICATION = Path(
    "implementation/p08/evidence/"
    "p08-24-object-shape-canary.current-2020.v1.json"
)
CAPABILITY_CONTRACTS = Path("specs/capability-contracts.generated.json")
ISOLATION_CHILD = Path(
    "implementation/p08/tools/run-hancom-2020-object-property-isolation-child.ps1"
)

PASS_RUN = Path(
    "implementation/p08/evidence/private/"
    "p08-25-object-property-isolation-20260915-15"
)
NEGATIVE_RUNS = {
    "OBJ-003": Path(
        "implementation/p08/evidence/private/"
        "p08-25-object-property-isolation-20260915-16"
    ),
    "OBJ-012": Path(
        "implementation/p08/evidence/private/"
        "p08-25-object-property-isolation-20260915-13"
    ),
    "OBJ-025": Path(
        "implementation/p08/evidence/private/"
        "p08-25-object-property-isolation-20260915-11"
    ),
    "OBJ-040": Path(
        "implementation/p08/evidence/private/"
        "p08-25-object-property-isolation-20260915-14"
    ),
    "OBJ-043": Path(
        "implementation/p08/evidence/private/"
        "p08-25-object-property-isolation-20260915-11"
    ),
}
TIMEOUT_RUN = Path(
    "implementation/p08/evidence/private/"
    "p08-25-object-property-isolation-20260915-12"
)

TARGET = {
    "profile_id": "hancom-hangul-2020-secondary",
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "locale": "ko-KR",
    "architecture": "x86",
    "scope": "current_pc_personal_local_development",
}
TARGET_EXECUTABLE_SHA256 = (
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
)
OVERLAY_SHA256 = "8fd12846d8f998018d79ec872abfab18af8fc2d1d8753a6c5801312ce3b9908f"
PASS_CHILD_SHA256 = "297b318d22b0b0c842b209de2cd994b2f22366d3b158de218546a3a3f8938b11"

ISOLATION_PASS_IDS = (
    "OBJ-001", "OBJ-002", "OBJ-007", "OBJ-010", "OBJ-014", "OBJ-015",
    "OBJ-016", "OBJ-017", "OBJ-018", "OBJ-019", "OBJ-020", "OBJ-021",
    "OBJ-022", "OBJ-023", "OBJ-024", "OBJ-027", "OBJ-028", "OBJ-029",
    "OBJ-030", "OBJ-031", "OBJ-032", "OBJ-034", "OBJ-035", "OBJ-036",
    "OBJ-037", "OBJ-039", "OBJ-041", "OBJ-042", "OBJ-047",
)
CANARY_PASS_IDS = ("OBJ-013", "OBJ-026", "OBJ-033", "OBJ-038", "OBJ-045")
VERIFIED_IDS = tuple(sorted((*ISOLATION_PASS_IDS, *CANARY_PASS_IDS)))
UNAVAILABLE_REASONS = {
    "OBJ-003": "parameterized_gallery_action_returned_false_without_effect",
    "OBJ-012": "form_insert_default_parameter_set_unavailable_on_exact_target",
    "OBJ-025": "selected_textbox_property_route_produced_no_semantic_effect",
    "OBJ-040": "eligible_programmatic_multi_shape_selection_unavailable_on_2020",
    "OBJ-043": "known_modal_edit_points_route_produced_no_semantic_effect",
    "OBJ-044": "exact_target_capability_unavailable",
    "OBJ-046": "no_exact_per_object_printable_automation_surface",
    "OBJ-048": "complete_hyperlink_parameter_route_remained_modal_and_timed_out",
}
P11_CANDIDATES = (
    "OBJ-006", "OBJ-049", "OBJ-050", "OBJ-051", "OBJ-052",
    "OBJ-053", "OBJ-054", "OBJ-055", "OBJ-056",
)
P11_DENIED = ("OBJ-011", "OBJ-057")
P11_UNAVAILABLE = ("OBJ-004", "OBJ-005", "OBJ-008", "OBJ-009", "OBJ-058")

TRACE_SCHEMA = "hwpx-agent.p08-object-property-isolation-private/v1"
RECEIPT_SCHEMA = "hwpx-agent.p08-object-automation-v2-qualification/v1"
OVERLAY_SCHEMA = "hwpx-agent.p08-object-automation-binding-overlay/v2"
PROJECTION_SCHEMA = "hwpx-agent.p08-object-automation-projection/v2"
CONTRACT_SCHEMA = "hwpx-agent.p08-object-automation-v2-qualification-contract/v1"


class QualificationError(ValueError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path, *, root: Path = ROOT) -> str:
    absolute = root / path
    if not absolute.is_file():
        raise QualificationError(f"missing_file:{path.as_posix()}")
    return hashlib.sha256(absolute.read_bytes()).hexdigest()


def load_json(path: Path, *, root: Path = ROOT) -> Any:
    absolute = root / path
    if not absolute.is_file() or absolute.stat().st_size > 32 * 1024 * 1024:
        raise QualificationError(f"missing_or_large_json:{path.as_posix()}")
    try:
        return json.loads(absolute.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"invalid_json:{path.as_posix()}") from error


def _candidate_routes(root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    candidate = load_json(CANDIDATE_OVERLAY, root=root)
    if not isinstance(candidate, dict) or candidate.get("schema_version") \
            != "hwpx-agent.p08-object-automation-binding-overlay/v1":
        raise QualificationError("candidate_overlay_schema")
    if file_sha256(CANDIDATE_OVERLAY, root=root) != OVERLAY_SHA256:
        raise QualificationError("candidate_overlay_drift")
    routes = candidate.get("routes")
    if not isinstance(routes, list) or len(routes) != 42:
        raise QualificationError("candidate_route_coverage")
    output: dict[str, dict[str, Any]] = {}
    for route in routes:
        if not isinstance(route, dict):
            raise QualificationError("candidate_route_shape")
        feature_id = route.get("feature_id")
        if not isinstance(feature_id, str) or feature_id in output:
            raise QualificationError("candidate_route_identity")
        if feature_id in UNAVAILABLE_REASONS:
            if feature_id in {"OBJ-044", "OBJ-046"}:
                if route.get("state") != "unavailable_with_reason":
                    raise QualificationError("candidate_static_unavailable_state")
            elif route.get("state") != "candidate_unverified":
                raise QualificationError("candidate_runtime_unavailable_state")
        elif route.get("state") != "candidate_unverified":
            raise QualificationError("candidate_verified_state")
        output[feature_id] = route
    expected = {
        "OBJ-001", "OBJ-002", "OBJ-003", "OBJ-007", "OBJ-010", "OBJ-012",
        "OBJ-013", "OBJ-014", "OBJ-015", "OBJ-016", "OBJ-017", "OBJ-018",
        "OBJ-019", "OBJ-020", "OBJ-021", "OBJ-022", "OBJ-023", "OBJ-024",
        "OBJ-025", "OBJ-026", "OBJ-027", "OBJ-028", "OBJ-029", "OBJ-030",
        "OBJ-031", "OBJ-032", "OBJ-033", "OBJ-034", "OBJ-035", "OBJ-036",
        "OBJ-037", "OBJ-038", "OBJ-039", "OBJ-040", "OBJ-041", "OBJ-042",
        "OBJ-043", "OBJ-044", "OBJ-045", "OBJ-046", "OBJ-047", "OBJ-048",
    }
    if set(output) != expected:
        raise QualificationError("candidate_route_set")
    return candidate, output


def _validate_batch_receipt(
    receipt: Any,
    *,
    expected_features: tuple[str, ...],
    overlay_sha256: str,
) -> None:
    if not isinstance(receipt, dict) or receipt.get("schema_version") \
            != "hwpx-agent.p08-object-property-isolation-batch-receipt/v1":
        raise QualificationError("batch_receipt_schema")
    config = receipt.get("configuration")
    if not isinstance(config, dict) \
            or tuple(config.get("feature_ids", ())) != expected_features \
            or config.get("overlay_sha256") != overlay_sha256 \
            or config.get("hwp_file_open_allowed") is not True \
            or config.get("hwp_file_open_scope") \
            != "project_owned_p08_20_readback_fixtures_only" \
            or config.get("document_save_allowed") is not False \
            or config.get("candidate_execute_allowed") is not True:
        raise QualificationError("batch_receipt_configuration")
    results = receipt.get("results")
    if not isinstance(results, list) or tuple(
        item.get("feature_id") for item in results if isinstance(item, dict)
    ) != expected_features:
        raise QualificationError("batch_receipt_results")
    for item in results:
        cleanup = item.get("cleanup") if isinstance(item, dict) else None
        if not isinstance(cleanup, dict) or cleanup.get("refused") != 0 \
                or cleanup.get("errors") != 0 or cleanup.get("remaining_owned") != 0:
            raise QualificationError("batch_receipt_cleanup")


def _validate_pass_trace(trace: Any, feature_id: str, capability_id: str) -> dict[str, Any]:
    if not isinstance(trace, dict) or trace.get("schema_version") != TRACE_SCHEMA \
            or trace.get("feature_id") != feature_id \
            or trace.get("capability_id") != capability_id:
        raise QualificationError("pass_trace_identity")
    before = trace.get("before_sha256")
    after = trace.get("after_sha256")
    if trace.get("state") != "pass" \
            or trace.get("target_build") != TARGET["build"] \
            or trace.get("target_executable_sha256") != TARGET_EXECUTABLE_SHA256 \
            or trace.get("hwp_process_identity_verified") is not True \
            or trace.get("execute_return") is not True \
            or trace.get("effect_observed") is not True \
            or not isinstance(before, str) or not isinstance(after, str) or before == after \
            or trace.get("document_save_count") != 0 \
            or trace.get("hwp_file_open_count") not in {0, 1} \
            or trace.get("approved_fixture_open_count") != trace.get("hwp_file_open_count") \
            or trace.get("rollback_mode") != "discard_unsaved_disposable_document" \
            or trace.get("rollback_verified") is not True \
            or trace.get("quit_invoked") is not True \
            or trace.get("error_code") is not None:
        raise QualificationError(f"pass_trace_state:{feature_id}")
    return {
        "state": "verified_current_target",
        "target_build": TARGET["build"],
        "target_executable_sha256": TARGET_EXECUTABLE_SHA256,
        "semantic_effect_observed": True,
        "semantic_undo_verified": trace.get("undo_semantic_verified") is True,
        "raw_undo_exact": trace.get("undo_raw_exact") is True,
        "approved_fixture_open_count": trace.get("approved_fixture_open_count"),
        "document_save_count": 0,
        "rollback_mode": "discard_unsaved_disposable_document",
        "rollback_verified": True,
    }


def _isolation_runtime(
    root: Path,
    routes: dict[str, dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    receipt_path = PASS_RUN / "runtime-receipt.json"
    receipt = load_json(receipt_path, root=root)
    _validate_batch_receipt(
        receipt,
        expected_features=ISOLATION_PASS_IDS,
        overlay_sha256=OVERLAY_SHA256,
    )
    config = receipt["configuration"]
    if receipt.get("state") != "pass" or receipt.get("completed_feature_count") != 29 \
            or receipt.get("passed_feature_count") != 29 \
            or receipt.get("timed_out_feature_count") != 0 \
            or config.get("child_sha256") != PASS_CHILD_SHA256:
        raise QualificationError("pass_batch_state")
    if file_sha256(ISOLATION_CHILD, root=root) != PASS_CHILD_SHA256:
        raise QualificationError("pass_child_source_drift")
    result_by_id = {item["feature_id"]: item for item in receipt["results"]}
    output: dict[str, dict[str, Any]] = {}
    trace_digests: dict[str, str] = {}
    for feature_id in ISOLATION_PASS_IDS:
        trace_path = PASS_RUN / f"{feature_id.lower()}-trace.private.json"
        trace = load_json(trace_path, root=root)
        runtime = _validate_pass_trace(
            trace,
            feature_id,
            routes[feature_id]["capability_id"],
        )
        trace_sha256 = file_sha256(trace_path, root=root)
        result = result_by_id[feature_id]
        if result.get("state") != "pass" or result.get("child_exit_code") != 0 \
                or result.get("timed_out") is not False \
                or result.get("trace_sha256") != trace_sha256 \
                or result.get("effect_observed") is not True:
            raise QualificationError(f"pass_batch_result:{feature_id}")
        runtime["trace_sha256"] = trace_sha256
        output[feature_id] = runtime
        trace_digests[feature_id] = trace_sha256
    return output, {
        "runtime_receipt_sha256": file_sha256(receipt_path, root=root),
        "progress_sha256": receipt.get("progress_sha256"),
        "child_sha256": config.get("child_sha256"),
        "trace_sha256_by_feature": trace_digests,
    }


def _canary_runtime(root: Path, routes: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], str]:
    evidence = load_json(CANARY_QUALIFICATION, root=root)
    if not isinstance(evidence, dict) or evidence.get("state") != "pass" \
            or evidence.get("target", {}).get("build") != TARGET["build"] \
            or evidence.get("target", {}).get("executable_sha256") != TARGET_EXECUTABLE_SHA256:
        raise QualificationError("canary_identity")
    execution = evidence.get("execution", {})
    boundaries = evidence.get("boundaries", {})
    if execution.get("canary_case_count") != 5 \
            or execution.get("effect_observed_count") != 5 \
            or execution.get("semantic_undo_verified_count") != 5 \
            or execution.get("document_save_count") != 0 \
            or execution.get("remaining_owned_hwp_processes") != 0 \
            or boundaries.get("fixture_or_user_document_opened_by_hwp") is not False \
            or boundaries.get("document_saved") is not False:
        raise QualificationError("canary_execution")
    cases = evidence.get("cases")
    if not isinstance(cases, list) or {case.get("feature_id") for case in cases} \
            != set(CANARY_PASS_IDS):
        raise QualificationError("canary_coverage")
    output: dict[str, dict[str, Any]] = {}
    for case in cases:
        feature_id = case["feature_id"]
        if case.get("capability_id") != routes[feature_id]["capability_id"] \
                or case.get("state") != "pass" \
                or case.get("is_action_enable") is not True \
                or case.get("effect_observed") is not True \
                or case.get("undo_semantic_verified") is not True:
            raise QualificationError(f"canary_case_state:{feature_id}")
        output[feature_id] = {
            "state": "verified_current_target",
            "target_build": TARGET["build"],
            "target_executable_sha256": TARGET_EXECUTABLE_SHA256,
            "semantic_effect_observed": True,
            "semantic_undo_verified": True,
            "raw_undo_exact": case.get("undo_raw_exact") is True,
            "approved_fixture_open_count": 0,
            "document_save_count": 0,
            "rollback_mode": "semantic_undo_then_discard_unsaved_disposable_document",
            "rollback_verified": True,
            "qualification_sha256": file_sha256(CANARY_QUALIFICATION, root=root),
        }
    return output, file_sha256(CANARY_QUALIFICATION, root=root)


def _negative_runtime(root: Path, routes: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    expected_states = {
        "OBJ-003": "failed",
        "OBJ-012": "failed",
        "OBJ-025": "no_qualified_effect",
        "OBJ-040": "no_qualified_effect",
        "OBJ-043": "no_qualified_effect",
    }
    output: dict[str, dict[str, Any]] = {}
    for feature_id, run in NEGATIVE_RUNS.items():
        receipt_path = run / "runtime-receipt.json"
        trace_path = run / f"{feature_id.lower()}-trace.private.json"
        receipt = load_json(receipt_path, root=root)
        trace = load_json(trace_path, root=root)
        if not isinstance(receipt, dict) or receipt.get("state") != "completed_with_failures":
            raise QualificationError(f"negative_receipt_state:{feature_id}")
        config = receipt.get("configuration", {})
        if config.get("overlay_sha256") != OVERLAY_SHA256 \
                or config.get("hwp_file_open_allowed") is not True \
                or config.get("hwp_file_open_scope") \
                != "project_owned_p08_20_readback_fixtures_only" \
                or config.get("document_save_allowed") is not False \
                or config.get("candidate_execute_allowed") is not True:
            raise QualificationError(f"negative_receipt_configuration:{feature_id}")
        results = receipt.get("results")
        if not isinstance(results, list):
            raise QualificationError(f"negative_result_shape:{feature_id}")
        result = next((item for item in results if item.get("feature_id") == feature_id), None)
        cleanup = result.get("cleanup", {}) if isinstance(result, dict) else {}
        if not isinstance(result, dict) or result.get("state") != expected_states[feature_id] \
                or result.get("effect_observed") is not False \
                or result.get("timed_out") is not False \
                or cleanup.get("remaining_owned") != 0 or cleanup.get("errors") != 0:
            raise QualificationError(f"negative_result_state:{feature_id}")
        if not isinstance(trace, dict) or trace.get("schema_version") != TRACE_SCHEMA \
                or trace.get("feature_id") != feature_id \
                or trace.get("capability_id") != routes[feature_id]["capability_id"] \
                or trace.get("target_build") != TARGET["build"] \
                or trace.get("target_executable_sha256") != TARGET_EXECUTABLE_SHA256 \
                or trace.get("effect_observed") is not False \
                or trace.get("document_save_count") != 0 \
                or trace.get("approved_fixture_open_count") != trace.get("hwp_file_open_count"):
            raise QualificationError(f"negative_trace_state:{feature_id}")
        trace_sha256 = file_sha256(trace_path, root=root)
        if result.get("trace_sha256") != trace_sha256:
            raise QualificationError(f"negative_trace_digest:{feature_id}")
        output[feature_id] = {
            "state": "unavailable_with_reason",
            "reason": UNAVAILABLE_REASONS[feature_id],
            "runtime_receipt_sha256": file_sha256(receipt_path, root=root),
            "trace_sha256": trace_sha256,
            "semantic_effect_observed": False,
            "document_save_count": 0,
            "remaining_owned_hwp_processes": 0,
        }

    timeout_path = TIMEOUT_RUN / "runtime-receipt.json"
    timeout = load_json(timeout_path, root=root)
    timeout_config = timeout.get("configuration", {}) if isinstance(timeout, dict) else {}
    results = timeout.get("results") if isinstance(timeout, dict) else None
    result = next(
        (item for item in results if item.get("feature_id") == "OBJ-048"),
        None,
    ) if isinstance(results, list) else None
    cleanup = result.get("cleanup", {}) if isinstance(result, dict) else {}
    if timeout.get("state") != "completed_with_failures" \
            or timeout_config.get("overlay_sha256") != OVERLAY_SHA256 \
            or timeout_config.get("document_save_allowed") is not False \
            or timeout_config.get("hwp_file_open_scope") \
            != "project_owned_p08_20_readback_fixtures_only" \
            or not isinstance(result, dict) or result.get("state") != "timed_out" \
            or result.get("timed_out") is not True or result.get("trace_sha256") is not None \
            or result.get("effect_observed") is not False \
            or cleanup.get("cleaned") != 1 or cleanup.get("remaining_owned") != 0 \
            or cleanup.get("errors") != 0:
        raise QualificationError("hyperlink_timeout_state")
    output["OBJ-048"] = {
        "state": "unavailable_with_reason",
        "reason": UNAVAILABLE_REASONS["OBJ-048"],
        "runtime_receipt_sha256": file_sha256(timeout_path, root=root),
        "trace_sha256": None,
        "semantic_effect_observed": False,
        "document_save_count": 0,
        "remaining_owned_hwp_processes": 0,
        "exact_owned_processes_cleaned": 1,
    }

    aspect = load_json(ASPECT_QUALIFICATION, root=root)
    if aspect.get("feature_id") != "OBJ-044" \
            or aspect.get("decision", {}).get("status") != "CAPABILITY_UNAVAILABLE_FOR_TARGET" \
            or aspect.get("decision", {}).get("automation_binding") != "unavailable_with_reason":
        raise QualificationError("aspect_unavailable_state")
    output["OBJ-044"] = {
        "state": "target_capability_unavailable",
        "reason": UNAVAILABLE_REASONS["OBJ-044"],
        "qualification_sha256": file_sha256(ASPECT_QUALIFICATION, root=root),
        "semantic_effect_observed": False,
        "document_save_count": 0,
        "remaining_owned_hwp_processes": 0,
    }
    output["OBJ-046"] = {
        "state": "unavailable_with_reason",
        "reason": UNAVAILABLE_REASONS["OBJ-046"],
        "candidate_overlay_sha256": OVERLAY_SHA256,
        "semantic_effect_observed": False,
        "document_save_count": 0,
        "remaining_owned_hwp_processes": 0,
    }
    return output


def _direct_oracle_digests(root: Path) -> dict[str, str]:
    evidence = load_json(DIRECT_EVIDENCE, root=root)
    target = load_json(TARGET_QUALIFICATION, root=root)
    if evidence.get("target_profile_id") != TARGET["profile_id"] \
            or evidence.get("target_qualification_file") != TARGET_QUALIFICATION.as_posix() \
            or target.get("execution", {}).get("effective_cases_passed") != 41 \
            or target.get("oracle", {}).get("semantic_reopen_passed") != 41 \
            or target.get("claims", {}).get("direct_stage") != "oracle_verified":
        raise QualificationError("direct_oracle_target_state")
    feature_ids = set(target.get("feature_ids", ()))
    if feature_ids != set(VERIFIED_IDS) | (set(UNAVAILABLE_REASONS) - {"OBJ-044"}):
        raise QualificationError("direct_oracle_target_coverage")
    output: dict[str, str] = {}
    for profile in evidence.get("profiles", ()):
        if not isinstance(profile, dict):
            raise QualificationError("direct_profile_shape")
        for feature_id in profile.get("feature_ids", ()):
            if feature_id in feature_ids:
                if profile.get("backend") != "direct_hwpx" \
                        or profile.get("stage") != "oracle_verified":
                    raise QualificationError(f"direct_profile_state:{feature_id}")
                if feature_id in output:
                    raise QualificationError(f"direct_profile_collision:{feature_id}")
                output[feature_id] = digest_value(
                    {
                        "feature_id": feature_id,
                        "profile": profile,
                        "target_qualification_sha256": file_sha256(
                            TARGET_QUALIFICATION,
                            root=root,
                        ),
                    }
                )
    if set(output) != feature_ids:
        raise QualificationError("direct_profile_coverage")
    return output


def _capability_contract_digests(root: Path) -> dict[str, str]:
    document = load_json(CAPABILITY_CONTRACTS, root=root)
    contracts = document.get("contracts") if isinstance(document, dict) else None
    if not isinstance(contracts, list):
        raise QualificationError("capability_contract_shape")
    output = {
        item["feature_id"]: digest_value(item)
        for item in contracts
        if isinstance(item, dict) and item.get("phase") == "P08"
    }
    if set(output) != set(VERIFIED_IDS) | set(UNAVAILABLE_REASONS):
        raise QualificationError("capability_contract_coverage")
    return output


def build_outputs(root: Path = ROOT) -> dict[str, Any]:
    candidate, routes = _candidate_routes(root)
    runtime_rows, isolation_locks = _isolation_runtime(root, routes)
    canary_rows, canary_sha256 = _canary_runtime(root, routes)
    runtime_rows.update(canary_rows)
    if set(runtime_rows) != set(VERIFIED_IDS):
        raise QualificationError("runtime_verified_coverage")
    unavailable_rows = _negative_runtime(root, routes)
    if set(unavailable_rows) != set(UNAVAILABLE_REASONS):
        raise QualificationError("runtime_unavailable_coverage")
    direct_digests = _direct_oracle_digests(root)
    contract_digests = _capability_contract_digests(root)

    rows: list[dict[str, Any]] = []
    for feature_id in sorted(routes):
        route = routes[feature_id]
        mapping_sha256 = digest_value(
            {
                key: route.get(key)
                for key in (
                    "feature_id", "capability_id", "mapping_mode", "source_kind",
                    "source_name", "source_id", "record_id", "node_id", "source_sha256",
                )
            }
        )
        if feature_id in runtime_rows:
            differential = {
                "state": "exact_match",
                "comparison_profile": (
                    "same_capability_contract_exact_target_semantic_effect_v1"
                ),
                "direct_stage": "oracle_verified",
                "automation_stage": "verified_current_target",
            }
            runtime = runtime_rows[feature_id]
        elif feature_id == "OBJ-044":
            differential = {
                "state": "not_applicable_target_capability_unavailable",
                "comparison_profile": None,
                "direct_stage": "target_capability_unavailable",
                "automation_stage": "target_capability_unavailable",
            }
            runtime = unavailable_rows[feature_id]
        else:
            differential = {
                "state": "not_applicable_fallback_unavailable",
                "comparison_profile": None,
                "direct_stage": "oracle_verified",
                "automation_stage": "unavailable_with_reason",
            }
            runtime = unavailable_rows[feature_id]
        rows.append(
            {
                "feature_id": feature_id,
                "capability_id": route["capability_id"],
                "binding_mapping_sha256": mapping_sha256,
                "capability_contract_sha256": contract_digests[feature_id],
                "direct_oracle_basis_sha256": direct_digests.get(feature_id),
                "automation_runtime": runtime,
                "differential": differential,
            }
        )

    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "evidence_id": "p08-object-automation-v2-current-2020-attempt01",
        "recorded_date": "2026-09-15",
        "scope": "p08_exact_current_target_42_row_route_qualification",
        "target": TARGET,
        "source_locks": {
            "candidate_overlay_sha256": OVERLAY_SHA256,
            "target_qualification_sha256": file_sha256(TARGET_QUALIFICATION, root=root),
            "aspect_qualification_sha256": file_sha256(ASPECT_QUALIFICATION, root=root),
            "canary_qualification_sha256": canary_sha256,
            **isolation_locks,
        },
        "rows": rows,
        "summary": {
            "p08_rows": 42,
            "direct_oracle_verified": 41,
            "target_capability_unavailable": 1,
            "automation_runtime_verified": 34,
            "automation_unavailable_with_reason": 8,
            "differential_exact_match": 34,
            "differential_not_applicable_fallback_unavailable": 7,
            "differential_not_applicable_target_unavailable": 1,
            "routing_enabled": 34,
            "p08_green_rows": 41,
            "p08_phase_gate": "pass_with_target_unavailable",
        },
        "safety": {
            "user_document_opened": False,
            "opened_files_scope": "project_owned_p08_20_readback_fixtures_only",
            "document_saved": False,
            "external_network_invoked": False,
            "registry_or_system_setting_changed": False,
            "computer_use_click_or_type_invoked": False,
            "remaining_owned_hwp_processes": 0,
        },
        "privacy": {
            "absolute_private_paths": False,
            "document_content": False,
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
        },
        "not_claimed": {
            "other_pc_or_version": False,
            "arbitrary_user_document_compatibility": False,
            "p11_complete": False,
            "production_ready": False,
            "product_complete": False,
        },
    }
    receipt_sha256 = digest_value(receipt)

    qualified = deepcopy(candidate)
    qualified["schema_version"] = OVERLAY_SCHEMA
    qualified["coverage"] = {
        "p08_rows": 42,
        "verified_current_target": 34,
        "unavailable_with_reason": 8,
        "candidate_unverified": 0,
        "routing_enabled": 34,
    }
    qualified["runtime_qualification"] = {
        "state": "pass_with_unavailable_routes",
        "receipt_sha256": receipt_sha256,
        "verified_current_target": 34,
        "unavailable_with_reason": 8,
    }
    qualified["routing_enabled"] = True
    qualified["qualification_receipt_sha256"] = receipt_sha256
    qualified["routes"] = []
    for route in candidate["routes"]:
        item = deepcopy(route)
        feature_id = item["feature_id"]
        if feature_id in runtime_rows:
            item["state"] = "verified_current_target"
            item["runtime_support_state"] = "verified_current_target"
            item["routing_enabled"] = True
            item["unavailable_reason"] = None
        else:
            item["state"] = "unavailable_with_reason"
            item["runtime_support_state"] = "unavailable_with_reason"
            item["routing_enabled"] = False
            item["unavailable_reason"] = UNAVAILABLE_REASONS[feature_id]
        qualified["routes"].append(item)

    projection = {
        "schema_version": PROJECTION_SCHEMA,
        "target_profile_id": TARGET["profile_id"],
        "verified_current_target": list(VERIFIED_IDS),
        "unavailable_with_reason": UNAVAILABLE_REASONS,
        "candidate_unverified": list(P11_CANDIDATES),
        "denied_by_policy": list(P11_DENIED),
        "unbound_unavailable": list(P11_UNAVAILABLE),
        "differential_exact_match": list(VERIFIED_IDS),
        "differential_not_applicable_fallback_unavailable": sorted(
            set(UNAVAILABLE_REASONS) - {"OBJ-044"}
        ),
        "differential_not_applicable_target_unavailable": ["OBJ-044"],
        "runtime_support_state": "partially_verified_current_target",
        "routing_enabled_count": 34,
        "actual_target_profile": True,
        "qualification_receipt_sha256": receipt_sha256,
        "qualified_overlay_sha256": None,
        "raw_action_identifiers": False,
        "raw_parameter_identifiers": False,
    }
    qualified_sha256 = digest_value(qualified)
    projection["qualified_overlay_sha256"] = qualified_sha256
    projection_sha256 = digest_value(projection)

    contract = {
        "schema_version": CONTRACT_SCHEMA,
        "scope": "p08_exact_current_target_automation_v2_fail_closed_qualification",
        "target": TARGET,
        "source_lock_canonicalization": "raw_file_sha256_for_private_runtime_and_canonical_json_sha256_for_outputs",
        "source_locks": {
            "candidate_overlay_sha256": OVERLAY_SHA256,
            "target_qualification_sha256": file_sha256(TARGET_QUALIFICATION, root=root),
            "aspect_qualification_sha256": file_sha256(ASPECT_QUALIFICATION, root=root),
            "canary_qualification_sha256": canary_sha256,
            "capability_contracts_sha256": file_sha256(CAPABILITY_CONTRACTS, root=root),
            "direct_evidence_sha256": file_sha256(DIRECT_EVIDENCE, root=root),
            "isolation_child_sha256": file_sha256(ISOLATION_CHILD, root=root),
            "finalizer_sha256": file_sha256(
                Path("tools/p08/finalize_object_automation_v2_qualification.py"),
                root=root,
            ),
            **isolation_locks,
            "negative_runtime_receipt_sha256_by_feature": {
                feature_id: row.get("runtime_receipt_sha256")
                for feature_id, row in unavailable_rows.items()
                if row.get("runtime_receipt_sha256") is not None
            },
            "negative_trace_sha256_by_feature": {
                feature_id: row.get("trace_sha256")
                for feature_id, row in unavailable_rows.items()
                if row.get("trace_sha256") is not None
            },
        },
        "output_locks": {
            "public_receipt_sha256": receipt_sha256,
            "qualified_overlay_sha256": qualified_sha256,
            "public_projection_sha256": projection_sha256,
        },
        "accepted_states": {
            "verified_current_target": list(VERIFIED_IDS),
            "unavailable_with_reason": UNAVAILABLE_REASONS,
            "target_capability_unavailable": ["OBJ-044"],
        },
        "phase_gate": {
            "p08_supported_rows": 41,
            "p08_green_rows": 41,
            "p08_target_unavailable_rows": 1,
            "state": "pass_with_target_unavailable",
            "p11_rows_deferred": 16,
        },
        "privacy": receipt["privacy"],
    }
    return {
        "receipt": receipt,
        "qualified_overlay": qualified,
        "projection": projection,
        "contract": contract,
    }


def write_outputs(outputs: dict[str, Any], *, root: Path = ROOT) -> None:
    paths = {
        "receipt": PUBLIC_RECEIPT,
        "qualified_overlay": QUALIFIED_OVERLAY,
        "projection": PUBLIC_PROJECTION,
        "contract": PUBLIC_CONTRACT,
    }
    for key, relative in paths.items():
        absolute = root / relative
        absolute.parent.mkdir(parents=True, exist_ok=True)
        absolute.write_bytes(canonical_bytes(outputs[key]))


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize P08 object automation v2 evidence")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    try:
        outputs = build_outputs()
        if arguments.write:
            write_outputs(outputs)
    except (QualificationError, OSError) as error:
        print(json.dumps({"state": "fail", "error": str(error)}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "state": "written" if arguments.write else "pass",
                "p08_rows": 42,
                "automation_runtime_verified": 34,
                "automation_unavailable_with_reason": 8,
                "p08_green_rows": 41,
                "p08_phase_gate": "pass_with_target_unavailable",
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
