#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TARGET_ROOT = (ROOT / "fixtures" / "target-build").resolve(strict=True)
PUBLIC_ROOT = (ROOT / "implementation" / "p06" / "evidence" / "target").resolve(
    strict=True
)
MAX_JSON_BYTES = 2 * 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")

REQUEST_SCHEMA = (
    "hwpx-agent.p06-09-table-automation-candidate-6-canary-request/v1"
)
TRACE_SCHEMA = (
    "hwpx-agent.p06-09-table-automation-candidate-6-canary-private-trace/v2"
)
PUBLIC_SCHEMA = (
    "hwpx-agent.p06-09-table-automation-candidate-6-canary-public-evidence/v1"
)
VERIFIER_PATH = "tools/p06/verify_table_automation_candidate_6_canary.py"
EXPECTED_BUILD = "11.0.0.9136"
EXPECTED_EXECUTABLE_SHA256 = (
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
)
EXPECTED_CASES = (
    ("TABLE-010", "table.split_table", "document_scan"),
    ("TABLE-015", "table.delete_columns", "document_scan"),
    ("TABLE-016", "table.split_cell", "document_scan"),
    ("TABLE-017", "table.merge_cells", "document_scan"),
    ("TABLE-046", "table.cell_border", "selected_style"),
    ("TABLE-048", "table.cell_fill", "selected_style"),
)
EXPECTED_SELECTIONS = (
    {"kind": "right_cell_repeat", "count": 3},
    {"kind": "cell_block_extend", "count": 0},
    {"kind": "cell_block_extend", "count": 0},
    {"kind": "cell_block_extend", "count": 2},
    {"kind": "cell_block_extend", "count": 0},
    {"kind": "cell_block_extend", "count": 0},
)
REQUEST_KEYS = {
    "schema_version",
    "state",
    "scope",
    "target",
    "inputs",
    "session_strategy",
    "fixture",
    "cases",
    "policy",
    "promotion",
}
TRACE_KEYS = {
    "schema_version",
    "state",
    "request_sha256",
    "target_build",
    "target_executable_sha256",
    "hwp_process_id",
    "case_count",
    "completed_case_count",
    "passed_case_count",
    "candidate_action_execute_count",
    "cases",
    "user_document_opened",
    "file_open_or_save_invoked",
    "external_network_invoked",
    "registry_or_system_setting_changed",
    "computer_use_click_or_type_invoked",
    "quit_invoked",
    "error_code",
}
TRACE_CASE_KEYS = {
    "index",
    "feature_id",
    "capability_id",
    "selection_prepared",
    "action_enabled_before",
    "action_enabled_after_baseline_snapshot",
    "candidate_executed",
    "snapshot_changed",
    "undo_executed",
    "undo_exact",
    "baseline",
    "post",
    "undo",
    "state",
    "error_code",
    "exception_type",
    "exception_hresult",
}
SNAPSHOT_KEYS = {"sha256", "scan", "style"}
SCAN_KEYS = {
    "sha256",
    "text_sha256",
    "text_utf16_length",
    "call_count",
    "terminal_code",
    "control_enter_count",
    "control_exit_count",
    "normal_text_chunk_count",
    "next_paragraph_count",
}
STYLE_KEYS = {"sha256", "item_count"}


class CanaryVerificationError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanaryVerificationError("duplicate_json_key")
        result[key] = value
    return result


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_text_sha256(path: Path) -> str:
    value = path.read_text(encoding="utf-8")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return sha256_text(normalized)


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def read_bounded_json(
    path: Path, boundary: Path, expected_sha256: str
) -> tuple[dict[str, Any], bytes]:
    if SHA256_RE.fullmatch(expected_sha256) is None:
        raise CanaryVerificationError("expected_sha256_invalid")
    root = boundary.resolve(strict=True)
    candidate = path if path.is_absolute() else ROOT / path
    lexical = candidate.absolute()
    try:
        relative = lexical.relative_to(root)
    except ValueError as error:
        raise CanaryVerificationError("path_outside_boundary") from error
    cursor = root
    for part in relative.parts:
        cursor /= part
        if _is_link(cursor):
            raise CanaryVerificationError("linked_path")
    resolved = lexical.resolve(strict=True)
    if root not in resolved.parents or not resolved.is_file():
        raise CanaryVerificationError("path_outside_or_not_file")
    size = resolved.stat().st_size
    if size <= 0 or size > MAX_JSON_BYTES:
        raise CanaryVerificationError("file_size_limit")
    data = resolved.read_bytes()
    if len(data) != size:
        raise CanaryVerificationError("file_changed_during_read")
    if sha256_bytes(data) != expected_sha256:
        raise CanaryVerificationError("input_sha256_mismatch")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CanaryVerificationError("invalid_json") from error
    if not isinstance(value, dict):
        raise CanaryVerificationError("json_root_not_object")
    return value, data


def require_exact_keys(value: Any, expected: set[str], code: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise CanaryVerificationError(code)
    return value


def require_sha256(value: Any, code: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise CanaryVerificationError(code)
    return value


def validate_request(request: dict[str, Any]) -> list[str]:
    require_exact_keys(request, REQUEST_KEYS, "request_shape")
    if (
        request.get("schema_version") != REQUEST_SCHEMA
        or request.get("state") != "planned"
        or request.get("scope") != "exact_current_pc_disposable_in_memory_canary"
        or request.get("session_strategy")
        != "one_hwp_session_six_isolated_generated_3x3_documents"
    ):
        raise CanaryVerificationError("request_identity")
    target = require_exact_keys(
        request.get("target"),
        {"prog_id", "build", "architecture", "client", "executable_sha256"},
        "request_target_shape",
    )
    if target != {
        "prog_id": "HWPFrame.HwpObject.2",
        "build": EXPECTED_BUILD,
        "architecture": "x86",
        "client": "windows_powershell_x86_sta",
        "executable_sha256": EXPECTED_EXECUTABLE_SHA256,
    }:
        raise CanaryVerificationError("request_target_identity")
    policy = request.get("policy")
    expected_policy = {
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
    }
    if policy != expected_policy:
        raise CanaryVerificationError("request_policy")
    if request.get("promotion") != {
        "runtime_support_state": "component_canary_only",
        "routing_enabled": False,
        "differential_state": "not_run",
        "p06": "in_progress",
    }:
        raise CanaryVerificationError("request_promotion")
    if request.get("fixture") != {
        "rows": 3,
        "cols": 3,
        "cell_text_strategy": "unique_ascii_marker_per_cell",
    }:
        raise CanaryVerificationError("request_fixture")
    inputs = request.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != {
        "source_request_sha256",
        "surface_trace_sha256",
        "surface_receipt_sha256",
        "merge_context_trace_sha256",
    }:
        raise CanaryVerificationError("request_inputs")
    for value in inputs.values():
        require_sha256(value, "request_input_sha256")

    cases = request.get("cases")
    if not isinstance(cases, list) or len(cases) != len(EXPECTED_CASES):
        raise CanaryVerificationError("request_case_count")
    private_identifiers: list[str] = []
    for index, ((feature, capability, _), selection) in enumerate(
        zip(EXPECTED_CASES, EXPECTED_SELECTIONS, strict=True), start=1
    ):
        case = require_exact_keys(
            cases[index - 1],
            {"index", "feature_id", "capability_id", "action_id", "selection", "invocation"},
            "request_case_shape",
        )
        if (
            case.get("index") != index
            or case.get("feature_id") != feature
            or case.get("capability_id") != capability
            or case.get("selection") != selection
        ):
            raise CanaryVerificationError("request_case_identity")
        action_id = case.get("action_id")
        if not isinstance(action_id, str) or not action_id or len(action_id) > 256:
            raise CanaryVerificationError("request_action_id")
        private_identifiers.append(action_id)
        invocation = case.get("invocation")
        if not isinstance(invocation, dict) or invocation.get("kind") not in {
            "run",
            "execute_default_set",
        }:
            raise CanaryVerificationError("request_invocation")
        if invocation.get("kind") == "run" and set(invocation) != {"kind"}:
            raise CanaryVerificationError("request_run_invocation_shape")
        if invocation.get("kind") == "execute_default_set":
            if not set(invocation).issubset({"kind", "item_set", "items"}):
                raise CanaryVerificationError("request_set_invocation_shape")
            items = invocation.get("items")
            if not isinstance(items, list) or len(items) > 64:
                raise CanaryVerificationError("request_set_items")
            for item in items:
                if not isinstance(item, dict) or not item or len(item) > 8:
                    raise CanaryVerificationError("request_set_item_shape")
                if set(item) not in ({"name", "value"}, {"name", "value_call"}):
                    raise CanaryVerificationError("request_set_item_fields")
                name = item.get("name")
                if not isinstance(name, str) or not name or len(name) > 256:
                    raise CanaryVerificationError("request_set_item_name")
                private_identifiers.append(name)
                value_call = item.get("value_call")
                if value_call is not None:
                    if not isinstance(value_call, dict) or set(value_call) != {
                        "name",
                        "args",
                    }:
                        raise CanaryVerificationError("request_value_call")
                    call_name = value_call.get("name")
                    call_args = value_call.get("args")
                    if (
                        not isinstance(call_name, str)
                        or not call_name
                        or len(call_name) > 256
                        or not isinstance(call_args, list)
                        or len(call_args) > 32
                    ):
                        raise CanaryVerificationError("request_value_call")
                    private_identifiers.append(call_name)
            if "item_set" in invocation and not isinstance(
                invocation.get("item_set"), dict
            ):
                raise CanaryVerificationError("request_item_set_shape")
    action_ids = [case["action_id"] for case in cases]
    if len(action_ids) != len(set(action_ids)):
        raise CanaryVerificationError("request_action_id_duplicate")
    return list(dict.fromkeys(private_identifiers))


def validate_scan(value: Any) -> dict[str, Any]:
    scan = require_exact_keys(value, SCAN_KEYS, "scan_shape")
    require_sha256(scan.get("sha256"), "scan_sha256")
    require_sha256(scan.get("text_sha256"), "scan_text_sha256")
    integer_keys = SCAN_KEYS - {"sha256", "text_sha256"}
    for key in integer_keys:
        item = scan.get(key)
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            raise CanaryVerificationError("scan_integer")
    if scan["terminal_code"] not in {0, 1} or scan["call_count"] <= 0:
        raise CanaryVerificationError("scan_terminal")
    counted = sum(
        scan[key]
        for key in (
            "control_enter_count",
            "control_exit_count",
            "normal_text_chunk_count",
            "next_paragraph_count",
        )
    )
    if counted + 1 != scan["call_count"]:
        raise CanaryVerificationError("scan_call_count")
    return scan


def validate_snapshot(value: Any, style_required: bool) -> dict[str, Any]:
    snapshot = require_exact_keys(value, SNAPSHOT_KEYS, "snapshot_shape")
    digest = require_sha256(snapshot.get("sha256"), "snapshot_sha256")
    scan = validate_scan(snapshot.get("scan"))
    style = snapshot.get("style")
    if style_required:
        style = require_exact_keys(style, STYLE_KEYS, "style_shape")
        require_sha256(style.get("sha256"), "style_sha256")
        if (
            not isinstance(style.get("item_count"), int)
            or isinstance(style.get("item_count"), bool)
            or style["item_count"] <= 0
        ):
            raise CanaryVerificationError("style_item_count")
        style_sha = style["sha256"]
    else:
        if style is not None:
            raise CanaryVerificationError("style_unexpected")
        style_sha = "<not_applicable>"
    expected = sha256_text(f"scan={scan['sha256']}\nstyle={style_sha}")
    if digest != expected:
        raise CanaryVerificationError("snapshot_composite_sha256")
    return snapshot


def validate_trace(
    trace: dict[str, Any],
    request_sha256: str,
    private_identifiers: list[str],
    trace_bytes: bytes,
) -> None:
    require_exact_keys(trace, TRACE_KEYS, "trace_shape")
    if (
        trace.get("schema_version") != TRACE_SCHEMA
        or trace.get("state") != "pass"
        or trace.get("request_sha256") != request_sha256
        or trace.get("target_build") != EXPECTED_BUILD
        or trace.get("target_executable_sha256") != EXPECTED_EXECUTABLE_SHA256
        or not isinstance(trace.get("hwp_process_id"), int)
        or isinstance(trace.get("hwp_process_id"), bool)
        or trace["hwp_process_id"] <= 0
        or trace.get("case_count") != 6
        or trace.get("completed_case_count") != 6
        or trace.get("passed_case_count") != 6
        or trace.get("candidate_action_execute_count") != 6
        or trace.get("user_document_opened") is not False
        or trace.get("file_open_or_save_invoked") is not False
        or trace.get("external_network_invoked") is not False
        or trace.get("registry_or_system_setting_changed") is not False
        or trace.get("computer_use_click_or_type_invoked") is not False
        or trace.get("quit_invoked") is not True
        or trace.get("error_code") is not None
    ):
        raise CanaryVerificationError("trace_boundary")
    for identifier in private_identifiers:
        if identifier.encode("utf-8") in trace_bytes:
            raise CanaryVerificationError("raw_private_identifier_in_trace")

    cases = trace.get("cases")
    if not isinstance(cases, list) or len(cases) != 6:
        raise CanaryVerificationError("trace_case_count")
    for index, (feature, capability, effect_channel) in enumerate(
        EXPECTED_CASES, start=1
    ):
        case = require_exact_keys(
            cases[index - 1], TRACE_CASE_KEYS, "trace_case_shape"
        )
        if (
            case.get("index") != index
            or case.get("feature_id") != feature
            or case.get("capability_id") != capability
            or case.get("selection_prepared") is not True
            or case.get("action_enabled_before") is not True
            or case.get("action_enabled_after_baseline_snapshot") is not True
            or case.get("candidate_executed") is not True
            or case.get("snapshot_changed") is not True
            or case.get("undo_executed") is not True
            or case.get("undo_exact") is not True
            or case.get("state") != "pass"
            or case.get("error_code") is not None
            or case.get("exception_type") is not None
            or case.get("exception_hresult") is not None
        ):
            raise CanaryVerificationError("trace_case_boundary")
        style_required = effect_channel == "selected_style"
        baseline = validate_snapshot(case.get("baseline"), style_required)
        post = validate_snapshot(case.get("post"), style_required)
        undo = validate_snapshot(case.get("undo"), style_required)
        if baseline != undo or baseline["sha256"] != undo["sha256"]:
            raise CanaryVerificationError("undo_not_exact")
        if baseline["sha256"] == post["sha256"]:
            raise CanaryVerificationError("effect_not_observed")
        if effect_channel == "document_scan":
            if baseline["scan"] == post["scan"]:
                raise CanaryVerificationError("scan_effect_not_observed")
        else:
            if baseline["scan"] != post["scan"] or baseline["style"] == post["style"]:
                raise CanaryVerificationError("style_effect_boundary")


def validate_public_evidence(
    public: dict[str, Any],
    public_bytes: bytes,
    request_sha256: str,
    trace_sha256: str,
    trace: dict[str, Any],
    private_identifiers: list[str],
) -> None:
    require_exact_keys(
        public,
        {
            "schema_version",
            "state",
            "scope",
            "recorded_at_utc",
            "target",
            "evidence",
            "session",
            "summary",
            "cases",
            "safety",
            "promotion",
        },
        "public_shape",
    )
    evidence = require_exact_keys(
        public.get("evidence"),
        {
            "source_surface_request_sha256",
            "source_surface_trace_sha256",
            "source_surface_receipt_sha256",
            "snapshot_probe_trace_sha256",
            "canary_request_sha256",
            "canary_harness_sha256",
            "canary_trace_sha256",
            "independent_invariant_validation",
            "independent_verifier",
        },
        "public_evidence_shape",
    )
    verifier_source_sha256 = canonical_text_sha256(ROOT / VERIFIER_PATH)
    if public.get("schema_version") != PUBLIC_SCHEMA:
        raise CanaryVerificationError("public_schema")
    if (
        public.get("state") != "component_canary_pass"
        or public.get("scope")
        != (
            "exact_current_pc_disposable_in_memory_effect_and_undo_canary_"
            "not_product_runtime_support"
        )
        or evidence.get("canary_request_sha256") != request_sha256
        or evidence.get("canary_trace_sha256") != trace_sha256
        or evidence.get("independent_invariant_validation") != "pass"
        or evidence.get("independent_verifier")
        != {
            "path": VERIFIER_PATH,
            "source_sha256": verifier_source_sha256,
            "test_count": 7,
            "state": "pass",
        }
        or public.get("promotion", {}).get("component_canary") != "pass"
        or public.get("promotion", {}).get("product_runtime_support_state") != "unverified"
        or public.get("promotion", {}).get("routing_enabled") is not False
        or public.get("promotion", {}).get("differential_state") != "not_run"
        or public.get("promotion", {}).get("p06_09") != "in_progress"
        or public.get("promotion", {}).get("p06") != "in_progress"
        or public.get("promotion", {}).get("product_complete") is not False
    ):
        raise CanaryVerificationError("public_boundary")
    target = public.get("target", {})
    if (
        target.get("build") != EXPECTED_BUILD
        or target.get("executable_sha256") != EXPECTED_EXECUTABLE_SHA256
        or target.get("architecture") != "x86"
        or target.get("client") != "windows_powershell_x86_sta"
    ):
        raise CanaryVerificationError("public_target")
    for key in (
        "source_surface_request_sha256",
        "source_surface_trace_sha256",
        "source_surface_receipt_sha256",
        "snapshot_probe_trace_sha256",
        "canary_request_sha256",
        "canary_harness_sha256",
        "canary_trace_sha256",
    ):
        require_sha256(evidence.get(key), "public_evidence_sha256")
    expected_summary = {
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
    }
    if public.get("summary") != expected_summary:
        raise CanaryVerificationError("public_summary")
    safety = public.get("safety", {})
    if safety != {
        "raw_action_identifiers_present": False,
        "raw_parameter_set_identifiers_present": False,
        "user_document_opened": False,
        "file_open_or_save_invoked": False,
        "external_network_invoked": False,
        "registry_or_system_setting_changed": False,
        "computer_use_click_or_type_invoked": False,
        "quit_invoked": True,
    }:
        raise CanaryVerificationError("public_safety")
    if public.get("session") != {
        "strategy": "one_hwp_session_six_isolated_generated_3x3_documents",
        "case_isolation": "fresh_disposable_document_per_case",
        "snapshot_method": (
            "whole_document_scan_status_and_text_hash_plus_selected_style_hash_"
            "when_applicable"
        ),
        "remaining_hwp_process_count": 0,
    }:
        raise CanaryVerificationError("public_session")
    for identifier in private_identifiers:
        if identifier.encode("utf-8") in public_bytes:
            raise CanaryVerificationError("raw_private_identifier_in_public_evidence")
    rows = public.get("cases")
    if not isinstance(rows, list) or len(rows) != 6:
        raise CanaryVerificationError("public_case_count")
    trace_rows = trace["cases"]
    selection_contexts = (
        "current_row_boundary",
        "single_cell_block",
        "single_cell_block",
        "two_extension_multi_cell_block",
        "single_cell_block",
        "single_cell_block",
    )
    for index, ((feature, capability, effect_channel), context) in enumerate(
        zip(EXPECTED_CASES, selection_contexts, strict=True), start=1
    ):
        row = rows[index - 1]
        source = trace_rows[index - 1]
        expected = {
            "index": index,
            "feature_id": feature,
            "capability_id": capability,
            "selection_context": context,
            "enabled_before": True,
            "enabled_after_baseline_snapshot": True,
            "candidate_executed": True,
            "effect_channel": effect_channel,
            "baseline_sha256": source["baseline"]["sha256"],
            "post_sha256": source["post"]["sha256"],
            "undo_sha256": source["undo"]["sha256"],
            "effect_observed": True,
            "undo_exact": True,
            "state": "pass",
        }
        if row != expected:
            raise CanaryVerificationError("public_case_projection")


def verify(
    request: dict[str, Any],
    request_bytes: bytes,
    request_sha256: str,
    trace: dict[str, Any],
    trace_bytes: bytes,
    trace_sha256: str,
    public: dict[str, Any],
    public_bytes: bytes,
) -> dict[str, Any]:
    private_identifiers = validate_request(request)
    validate_trace(trace, request_sha256, private_identifiers, trace_bytes)
    validate_public_evidence(
        public,
        public_bytes,
        request_sha256,
        trace_sha256,
        trace,
        private_identifiers,
    )
    if sha256_bytes(request_bytes) != request_sha256:
        raise CanaryVerificationError("request_wire_hash")
    if sha256_bytes(trace_bytes) != trace_sha256:
        raise CanaryVerificationError("trace_wire_hash")
    return {
        "schema_version": (
            "hwpx-agent.p06-09-table-automation-candidate-6-canary-verification/v1"
        ),
        "state": "pass",
        "scope": "component_canary_only_not_product_runtime_support",
        "request_sha256": request_sha256,
        "trace_sha256": trace_sha256,
        "verifier_source_sha256": canonical_text_sha256(ROOT / VERIFIER_PATH),
        "case_count": 6,
        "scan_effect_count": 4,
        "style_effect_count": 2,
        "undo_exact_count": 6,
        "raw_private_identifier_leak_count": 0,
        "runtime_support_state": "unverified",
        "routing_enabled": False,
        "differential_state": "not_run",
        "p06": "in_progress",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Independently verify the hash-bound six-table-candidate disposable canary."
        )
    )
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--request-sha256", required=True)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--trace-sha256", required=True)
    parser.add_argument("--public-evidence", required=True, type=Path)
    parser.add_argument("--public-evidence-sha256", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    request, request_bytes = read_bounded_json(
        args.request, TARGET_ROOT, args.request_sha256
    )
    trace, trace_bytes = read_bounded_json(args.trace, TARGET_ROOT, args.trace_sha256)
    public, public_bytes = read_bounded_json(
        args.public_evidence, PUBLIC_ROOT, args.public_evidence_sha256
    )
    result = verify(
        request,
        request_bytes,
        args.request_sha256,
        trace,
        trace_bytes,
        args.trace_sha256,
        public,
        public_bytes,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
