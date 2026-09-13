#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from tools.p06 import plan_table_automation_candidate_32_batch as planner
except ModuleNotFoundError:
    import plan_table_automation_candidate_32_batch as planner  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]
ATTEMPT = (
    ROOT
    / "fixtures/target-build/p06-09-table-automation-candidate-32-20260914-02"
)
REQUEST = ATTEMPT / "request.json"
CONTROLS = ATTEMPT / "fixture-controls.private.json"
TRACE = ATTEMPT / "trace.json"
PROGRESS = ATTEMPT / "trace.json.progress.jsonl"
RECEIPT = ATTEMPT / "receipt.json"
CHILD = ROOT / (
    "implementation/p06/tools/"
    "run-hancom-2020-table-automation-candidate-32-surface-child.ps1"
)
OUTPUT = ROOT / (
    "implementation/p06/evidence/target/"
    "p06-table-automation-candidate-32-surface.current-2020.attempt01.v1.json"
)
EXPECTED_SHA256 = {
    REQUEST: "8ad49a2a9f1057fd3e474fd5a56b4ff838e383f821a09f525ce9d9d72a2cbfd4",
    CONTROLS: "f491e8651ffc84c215b929779afaffa0dd99a4cfa3171f6a8e55928412af7e8a",
    TRACE: "2b6a81b35831972218f7d40d281421539efb21d3d94c760c0fe3508c8a02fda5",
    PROGRESS: "5c0b246d84644b19406b75b66925d7403e85c6ace31fa2eddd8d40d06d503f57",
    RECEIPT: "8cc86420e8820d030d5081dad5c2e22e3790fe4ed11b889a227d06c3dda0be40",
}
EXPECTED_CHILD_SHA256 = (
    "4c6ecb8e422b88ce44e43c03403afa438c29d8fe0c7f0973d01658e524cdfb30"
)


class Candidate32EvidenceError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Candidate32EvidenceError("duplicate_json_key")
        value[key] = item
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_locked_json(path: Path) -> tuple[dict[str, Any], bytes]:
    if path not in EXPECTED_SHA256 or not path.is_file() or path.is_symlink():
        raise Candidate32EvidenceError("locked_input_path")
    data = path.read_bytes()
    if not data or len(data) > 8 * 1024 * 1024:
        raise Candidate32EvidenceError("locked_input_size")
    if sha256_bytes(data) != EXPECTED_SHA256[path]:
        raise Candidate32EvidenceError("locked_input_digest")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Candidate32EvidenceError("locked_input_json") from error
    if not isinstance(value, dict):
        raise Candidate32EvidenceError("locked_input_root")
    return value, data


def validate_progress(data: bytes) -> None:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise Candidate32EvidenceError("progress_utf8") from error
    if len(lines) != 164:
        raise Candidate32EvidenceError("progress_count")
    for index, line in enumerate(lines, 1):
        try:
            event = json.loads(line, object_pairs_hook=reject_duplicate_keys)
        except json.JSONDecodeError as error:
            raise Candidate32EvidenceError("progress_json") from error
        if (
            not isinstance(event, dict)
            or event.get("schema_version")
            != "hwpx-agent.p06-09-table-automation-candidate-32-progress/v1"
            or event.get("sequence") != index
            or event.get("candidate_under_probe_executed") is not False
            or event.get("raw_action_or_parameter_identifier_present") is not False
        ):
            raise Candidate32EvidenceError("progress_boundary")
    if lines:
        final = json.loads(lines[-1], object_pairs_hook=reject_duplicate_keys)
        if final.get("phase") != "quit" or final.get("state") != "pass":
            raise Candidate32EvidenceError("progress_final")


def build_evidence() -> dict[str, Any]:
    request, request_bytes = load_locked_json(REQUEST)
    controls, controls_bytes = load_locked_json(CONTROLS)
    trace, trace_bytes = load_locked_json(TRACE)
    receipt, receipt_bytes = load_locked_json(RECEIPT)
    if sha256_bytes(PROGRESS.read_bytes()) != EXPECTED_SHA256[PROGRESS]:
        raise Candidate32EvidenceError("progress_digest")
    progress_bytes = PROGRESS.read_bytes()
    validate_progress(progress_bytes)
    child_text = CHILD.read_text(encoding="utf-8").replace("\r\n", "\n")
    if sha256_bytes(child_text.encode("utf-8")) != EXPECTED_CHILD_SHA256:
        raise Candidate32EvidenceError("child_source_digest")

    expected_features = [feature_id for feature_id, _, _ in planner.EXPECTED_ROWS]
    expected_capabilities = [capability_id for _, capability_id, _ in planner.EXPECTED_ROWS]
    expected_contexts = [context for _, _, context in planner.EXPECTED_ROWS]
    request_cases = request.get("cases")
    trace_cases = trace.get("cases")
    if (
        request.get("schema_version") != planner.REQUEST_SCHEMA
        or request.get("case_count") != 32
        or request.get("fixture_policy", {}).get(
            "table_create_fixture_action_execute_count"
        )
        != 30
        or request.get("promotion", {}).get("runtime_support_state") != "not_eligible"
        or not isinstance(request_cases, list)
        or not isinstance(trace_cases, list)
        or len(request_cases) != 32
        or len(trace_cases) != 32
    ):
        raise Candidate32EvidenceError("request_or_trace_shape")

    raw_values = {
        value
        for case in request_cases
        for value in (case.get("action_id"), case.get("parameter_set_id"))
        if isinstance(value, str) and value
    }
    raw_values.update(
        value
        for key, value in controls.items()
        if key != "schema_version" and isinstance(value, str) and value
    )
    trace_text = trace_bytes.decode("utf-8")
    receipt_text = receipt_bytes.decode("utf-8")
    progress_text = progress_bytes.decode("utf-8")
    if any(
        raw in text
        for raw in raw_values
        for text in (trace_text, receipt_text, progress_text)
    ):
        raise Candidate32EvidenceError("private_identifier_leak")

    public_cases: list[dict[str, Any]] = []
    for index, (request_case, trace_case) in enumerate(
        zip(request_cases, trace_cases, strict=True), 1
    ):
        feature_id = expected_features[index - 1]
        capability_id = expected_capabilities[index - 1]
        context = expected_contexts[index - 1]
        parameter_state = request_case.get("parameter_set_state")
        expected_default = (
            "pass" if parameter_state == "documented_candidate" else "not_applicable"
        )
        if (
            request_case.get("index") != index
            or request_case.get("feature_id") != feature_id
            or request_case.get("capability_id") != capability_id
            or request_case.get("selection_context") != context
            or request_case.get("execute_candidate_under_probe") is not False
            or trace_case.get("index") != index
            or trace_case.get("feature_id") != feature_id
            or trace_case.get("capability_id") != capability_id
            or trace_case.get("selection_context") != context
            or trace_case.get("action_id_sha256")
            != sha256_bytes(request_case["action_id"].encode("utf-8"))
            or trace_case.get("action_created") is not True
            or trace_case.get("context_prepared") is not True
            or trace_case.get("get_default_state") != expected_default
            or trace_case.get("candidate_under_probe_execute_state") != "not_run"
            or trace_case.get("document_closed_without_save") is not True
            or trace_case.get("state")
            not in {"surface_present_enabled", "surface_present_disabled_in_context"}
        ):
            raise Candidate32EvidenceError("case_boundary")
        public_cases.append(
            {
                "index": index,
                "feature_id": feature_id,
                "capability_id": capability_id,
                "selection_context": context,
                "is_action_enable": trace_case["is_action_enable"],
                "get_default_state": trace_case["get_default_state"],
                "state": trace_case["state"],
            }
        )

    enabled = sum(case["is_action_enable"] is True for case in public_cases)
    if (
        trace.get("state") != "pass"
        or trace.get("completed_case_count") != 32
        or enabled != 22
        or trace.get("enabled_case_count") != enabled
        or trace.get("default_read_passed") != 14
        or trace.get("table_create_fixture_action_execute_count") != 30
        or trace.get("fixture_control_action_execute_count") != 176
        or trace.get("candidate_under_probe_execute_count") != 0
        or receipt.get("state") != "pass"
        or receipt.get("trace_valid") is not True
        or receipt.get("remaining_hwp_process_count") != 0
        or receipt.get("raw_action_or_parameter_identifier_present_in_trace") is not False
        or receipt.get("runtime_support_state") != "not_eligible"
        or receipt.get("routing_enabled") is not False
    ):
        raise Candidate32EvidenceError("result_boundary")

    return {
        "schema_version": (
            "hwpx-agent.p06-09-table-automation-candidate-32-surface-evidence/v1"
        ),
        "state": "component_pass",
        "scope": "exact_target_read_only_candidate_surface_inventory_not_runtime_support",
        "target": {
            **planner.EXPECTED_TARGET,
            "client": "windows_powershell_x86_sta",
            "executable_sha256": planner.EXPECTED_EXECUTABLE_SHA256,
        },
        "evidence": {
            "request_sha256": sha256_bytes(request_bytes),
            "fixture_controls_sha256": sha256_bytes(controls_bytes),
            "child_source_sha256": EXPECTED_CHILD_SHA256,
            "trace_sha256": sha256_bytes(trace_bytes),
            "progress_sha256": sha256_bytes(progress_bytes),
            "receipt_sha256": sha256_bytes(receipt_bytes),
        },
        "summary": {
            "case_count": 32,
            "completed_case_count": 32,
            "enabled_in_context_count": enabled,
            "disabled_in_context_count": 32 - enabled,
            "default_read_passed_count": 14,
            "table_create_fixture_action_execute_count": 30,
            "fixture_control_action_execute_count": 176,
            "candidate_under_probe_execute_count": 0,
            "progress_event_count": 164,
        },
        "cases": public_cases,
        "safety": {
            "user_document_opened": False,
            "file_open_or_save_invoked": False,
            "external_network_invoked": False,
            "registry_or_system_setting_changed": False,
            "computer_use_click_or_type_invoked": False,
            "raw_action_identifiers_present": False,
            "raw_parameter_set_identifiers_present": False,
            "remaining_hwp_process_count": 0,
        },
        "promotion": {
            "surface_inventory": "component_pass",
            "runtime_support_state": "unverified",
            "routing_enabled": False,
            "differential_state": "not_run",
            "p06_09": "in_progress",
            "p06": "in_progress",
            "product_complete": False,
        },
    }


def main() -> int:
    evidence = build_evidence()
    payload = (
        json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")
    with OUTPUT.open("xb") as stream:
        stream.write(payload)
        stream.flush()
    print(
        "P06_TABLE_AUTOMATION_CANDIDATE_32_SURFACE_EVIDENCE_PASS "
        f"cases=32 enabled=22 output_sha256={sha256_bytes(payload)} "
        "runtime_support=unverified routing=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
