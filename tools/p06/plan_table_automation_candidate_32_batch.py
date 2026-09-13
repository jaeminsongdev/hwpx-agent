#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

try:
    from tools.p06 import build_table_automation_binding_overlay as binding_overlay
    from tools.p06 import table_conformance as conformance
except ModuleNotFoundError:
    import build_table_automation_binding_overlay as binding_overlay  # type: ignore[no-redef]
    import table_conformance as conformance  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]
TARGET_ROOT = (ROOT / "fixtures" / "target-build").resolve(strict=True)
REQUEST_SCHEMA = "hwpx-agent.p06-09-table-automation-candidate-32-request/v1"
ATTEMPT_RE = re.compile(
    r"p06-09-table-automation-candidate-32-[0-9]{8}-[0-9]{2}\Z"
)
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
MAX_JSON_BYTES = 32 * 1024 * 1024
EXPECTED_EXECUTABLE_SHA256 = (
    "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
)
EXPECTED_TARGET = {
    "profile_id": "hancom-hangul-2020-secondary",
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "locale": "ko-KR",
    "architecture": "x86",
}
EXPECTED_ROWS = (
    ("TABLE-001", "table.create", "blank_document"),
    ("TABLE-002", "table.draw", "current_table"),
    ("TABLE-003", "table.eraser", "current_table"),
    ("TABLE-004", "table.text_to_table", "selected_text"),
    ("TABLE-005", "table.table_to_text", "current_table"),
    ("TABLE-007", "table.properties", "current_table"),
    ("TABLE-010", "table.split_table", "current_row_boundary"),
    ("TABLE-011", "table.join_table", "current_table"),
    ("TABLE-014", "table.delete_rows", "current_row_block"),
    ("TABLE-015", "table.delete_columns", "current_column_block"),
    ("TABLE-016", "table.split_cell", "single_cell_block"),
    ("TABLE-017", "table.merge_cells", "adjacent_two_cell_block"),
    ("TABLE-018", "table.equal_row_height", "rectangular_cell_block"),
    ("TABLE-019", "table.equal_column_width", "rectangular_cell_block"),
    ("TABLE-020", "table.table_style", "current_table"),
    ("TABLE-021", "table.transpose", "current_table"),
    ("TABLE-022", "table.block_sum", "numeric_cell_block"),
    ("TABLE-023", "table.block_average", "numeric_cell_block"),
    ("TABLE-024", "table.block_product", "numeric_cell_block"),
    ("TABLE-025", "table.horizontal_sum", "numeric_cell_block"),
    ("TABLE-026", "table.vertical_sum", "numeric_cell_block"),
    ("TABLE-027", "table.horizontal_average", "numeric_cell_block"),
    ("TABLE-028", "table.vertical_average", "numeric_cell_block"),
    ("TABLE-029", "table.horizontal_product", "numeric_cell_block"),
    ("TABLE-030", "table.vertical_product", "numeric_cell_block"),
    ("TABLE-031", "table.formula", "single_cell_block"),
    ("TABLE-032", "table.thousands_add", "numeric_cell_block"),
    ("TABLE-033", "table.thousands_remove", "numeric_cell_block"),
    ("TABLE-036", "table.inline_floating", "current_table"),
    ("TABLE-046", "table.cell_border", "single_cell_block"),
    ("TABLE-048", "table.cell_fill", "single_cell_block"),
    ("TABLE-057", "table.auto_fill", "numeric_cell_block"),
)


class Candidate32PlanError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise Candidate32PlanError("duplicate_json_key")
        value[key] = item
    return value


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def bounded_regular(path: Path, root: Path, maximum: int) -> Path:
    boundary = root.resolve(strict=True)
    candidate = path if path.is_absolute() else boundary / path
    lexical = candidate.absolute()
    try:
        relative = lexical.relative_to(boundary)
    except ValueError as error:
        raise Candidate32PlanError("path_outside_boundary") from error
    cursor = boundary
    for part in relative.parts:
        cursor /= part
        if _is_link(cursor):
            raise Candidate32PlanError("linked_path")
    resolved = lexical.resolve(strict=True)
    if boundary not in resolved.parents or not resolved.is_file():
        raise Candidate32PlanError("path_outside_or_not_file")
    size = resolved.stat().st_size
    if size <= 0 or size > maximum:
        raise Candidate32PlanError("file_size_limit")
    return resolved


def read_json(path: Path, expected_sha256: str) -> tuple[dict[str, Any], bytes]:
    if SHA256_RE.fullmatch(expected_sha256) is None:
        raise Candidate32PlanError("expected_sha256_invalid")
    resolved = bounded_regular(path, ROOT, MAX_JSON_BYTES)
    data = resolved.read_bytes()
    if (
        len(data) != resolved.stat().st_size
        or hashlib.sha256(data).hexdigest() != expected_sha256
    ):
        raise Candidate32PlanError("input_sha256_mismatch")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise Candidate32PlanError("invalid_json") from error
    if not isinstance(value, dict):
        raise Candidate32PlanError("json_root_not_object")
    return value, data


def _require_target(overlay: dict[str, Any], projection: dict[str, Any]) -> None:
    target = overlay.get("target")
    if not isinstance(target, dict):
        raise Candidate32PlanError("target_missing")
    expected_private = {
        "profile_id": EXPECTED_TARGET["profile_id"],
        "product": EXPECTED_TARGET["product"],
        "major_release": "2020",
        "exact_build": EXPECTED_TARGET["build"],
        "locale": EXPECTED_TARGET["locale"],
        "architecture": EXPECTED_TARGET["architecture"],
        "license_state": "approved",
        "routing_enabled": False,
    }
    if any(target.get(key) != expected for key, expected in expected_private.items()):
        raise Candidate32PlanError("private_target_mismatch")
    if projection.get("target") != {
        **EXPECTED_TARGET,
        "scope": "current_pc_personal_local_development",
    }:
        raise Candidate32PlanError("projection_target_mismatch")


def build_request(
    private_overlay: dict[str, Any],
    private_overlay_sha256: str,
    projection: dict[str, Any],
    projection_sha256: str,
    public_contract: dict[str, Any],
    public_contract_sha256: str,
) -> dict[str, Any]:
    if (
        private_overlay.get("schema_version") != binding_overlay.OVERLAY_SCHEMA
        or private_overlay.get("restricted_derivative") is not True
        or private_overlay.get("routing_enabled") is not False
        or private_overlay.get("coverage")
        != {
                "required_rows": 61,
                "candidate_unverified": 32,
                "unavailable_with_reason": 29,
        }
        or private_overlay.get("runtime_qualification")
        != {
                "state": "not_run",
                "verified_current_target": 0,
                "failed_current_target": 0,
        }
    ):
        raise Candidate32PlanError("private_overlay_boundary")
    if private_overlay.get("review_contract_sha256") != public_contract_sha256:
        raise Candidate32PlanError("review_contract_digest_mismatch")
    try:
        contract_mappings = binding_overlay.validate_public_contract_shape(public_contract)
        projection_rows = conformance.validate_projection(projection)
    except (binding_overlay.OverlayError, conformance.ConformanceError) as error:
        raise Candidate32PlanError("public_input_invalid") from error
    if projection.get("source_registry_sha256") != private_overlay_sha256:
        raise Candidate32PlanError("projection_source_digest_mismatch")
    _require_target(private_overlay, projection)

    all_features = {f"TABLE-{index:03d}" for index in range(1, 62)}
    projection_candidates = [
        row
        for row in projection_rows.values()
        if row["binding_status"] == "candidate_unverified"
    ]
    projection_unavailable = [
        row
        for row in projection_rows.values()
        if row["binding_status"] == "unavailable_with_reason"
    ]
    if (
        set(projection_rows) != all_features
        or len(projection_candidates) != 32
        or len(projection_unavailable) != 29
        or any(
            row["runtime_support_state"] != "unverified"
            or row["routing_enabled"] is not False
            for row in projection_rows.values()
        )
    ):
        raise Candidate32PlanError("projection_all_rows_boundary")

    expected = {(feature_id, capability_id) for feature_id, capability_id, _ in EXPECTED_ROWS}
    contract_identity = set(contract_mappings.items())
    projection_identity = {
        (feature_id, row["capability_id"])
        for feature_id, row in projection_rows.items()
        if row["binding_status"] == "candidate_unverified"
    }
    bindings = private_overlay.get("bindings")
    if (
        not isinstance(bindings, list)
        or len(bindings) != 61
        or any(not isinstance(row, dict) for row in bindings)
    ):
        raise Candidate32PlanError("private_bindings_shape")
    private_by_feature = {
        row.get("feature_id"): row for row in bindings if isinstance(row, dict)
    }
    if (
        set(private_by_feature) != all_features
        or len(private_by_feature) != 61
        or any(
            row.get("capability_id")
            != projection_rows[feature_id]["capability_id"]
            or row.get("runtime_support_state") != "unverified"
            or row.get("routing_enabled") is not False
            for feature_id, row in private_by_feature.items()
        )
        or sum(
            row.get("status") == "unavailable_with_reason"
            for row in private_by_feature.values()
        )
        != 29
    ):
        raise Candidate32PlanError("private_all_rows_boundary")
    private_source_rows = [
        row
        for row in bindings
        if isinstance(row, dict) and row.get("status") == "candidate_unverified"
    ]
    private_rows = {
        (row.get("feature_id"), row.get("capability_id")): row
        for row in private_source_rows
    }
    if (
        contract_identity != expected
        or projection_identity != expected
        or set(private_rows) != expected
        or len(private_source_rows) != 32
        or len(private_rows) != 32
    ):
        raise Candidate32PlanError("candidate_identity_mismatch")
    contract_rows = {
        row["feature_id"]: row for row in public_contract["mappings"]
    }

    cases: list[dict[str, Any]] = []
    action_ids: set[str] = set()
    documented_parameter_sets = 0
    for feature_id, capability_id, context in EXPECTED_ROWS:
        source = private_rows[(feature_id, capability_id)]
        public = projection_rows[feature_id]
        proof = contract_rows[feature_id]
        invocation = source.get("invocation")
        if (
            source.get("binding_key")
            != f"{capability_id}@hancom-hangul-2020-secondary/11.0.0.9136/ko-KR"
            or source.get("runtime_support_state") != "unverified"
            or source.get("routing_enabled") is not False
            or source.get("raw_identifiers_present") is not True
            or not isinstance(invocation, dict)
            or invocation.get("kind") != "action"
            or invocation.get("parameter_map") != []
            or invocation.get("parameter_map_state") != "pending_runtime_probe"
            or invocation.get("parameter_set_state") != proof["parameter_set_state"]
            or public
            != {
                    "feature_id": feature_id,
                    "capability_id": capability_id,
                    "binding_status": "candidate_unverified",
                    "runtime_support_state": "unverified",
                    "routing_enabled": False,
            }
        ):
            raise Candidate32PlanError("candidate_boundary_mismatch")
        action_id = invocation.get("action_id")
        parameter_set_id = invocation.get("parameter_set_id")
        parameter_state = invocation["parameter_set_state"]
        if (
            not isinstance(action_id, str)
            or not action_id
            or action_id in action_ids
            or hashlib.sha256(action_id.encode("utf-8")).hexdigest()
            != proof["action_identifier_sha256"]
        ):
            raise Candidate32PlanError("candidate_action_identity")
        if parameter_state == "source_declares_none":
            if parameter_set_id is not None or proof["parameter_signal_sha256"] != (
                hashlib.sha256(b"-").hexdigest()
            ):
                raise Candidate32PlanError("parameter_set_boundary")
        elif parameter_state == "documented_candidate":
            if (
                not isinstance(parameter_set_id, str)
                or not parameter_set_id
                or hashlib.sha256(parameter_set_id.encode("utf-8")).hexdigest()
                != proof["parameter_signal_sha256"]
            ):
                raise Candidate32PlanError("parameter_set_boundary")
            documented_parameter_sets += 1
        else:
            raise Candidate32PlanError("parameter_state_unknown")
        action_ids.add(action_id)
        cases.append(
            {
                "index": len(cases) + 1,
                "feature_id": feature_id,
                "capability_id": capability_id,
                "action_id": action_id,
                "parameter_set_id": parameter_set_id,
                "parameter_set_state": parameter_state,
                "selection_context": context,
                "surface_probe": "is_action_enable_and_default_read_only",
                "execute_candidate_under_probe": False,
            }
        )

    return {
        "schema_version": REQUEST_SCHEMA,
        "state": "planned",
        "scope": "exact_current_pc_candidate_32_surface_inventory_not_runtime_support",
        "target": {
            **EXPECTED_TARGET,
            "prog_id": "HWPFrame.HwpObject.2",
            "registry_view": "Registry32",
            "client": "windows_powershell_x86_sta",
            "executable_sha256": EXPECTED_EXECUTABLE_SHA256,
        },
        "inputs": {
            "private_overlay_sha256": private_overlay_sha256,
            "public_projection_sha256": projection_sha256,
            "public_review_contract_sha256": public_contract_sha256,
        },
        "session_strategy": "one_hwp_session_32_isolated_disposable_documents",
        "case_count": 32,
        "documented_parameter_set_count": documented_parameter_sets,
        "cases": cases,
        "fixture_policy": {
            "blank_document_case_count": 1,
            "selected_text_case_count": 1,
            "generated_table_context_case_count": 30,
            "table_create_fixture_action_execute_count": 30,
            "fixture_action_is_also_candidate": True,
            "fixture_execution_qualifies_runtime": False,
        },
        "policy": {
            "candidate_under_probe_execute_allowed": False,
            "default_read_allowed": True,
            "disposable_fixture_action_execute_allowed": True,
            "user_document_open_allowed": False,
            "file_open_or_save_allowed": False,
            "external_network_allowed": False,
            "registry_or_system_setting_write_allowed": False,
            "computer_use_click_or_type_allowed": False,
            "preexisting_hwp_process_policy": "refuse",
            "unexpected_window_policy": "stop_unverified",
            "publication": "private_create_new_attempt_only",
        },
        "promotion": {
            "surface_inventory": "eligible_after_complete_pass",
            "runtime_support_state": "not_eligible",
            "routing_enabled": False,
            "differential": "not_run",
            "p06_09": "in_progress",
            "p06": "in_progress",
        },
    }


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def publish_request(attempt_name: str, request: dict[str, Any]) -> tuple[Path, str]:
    if ATTEMPT_RE.fullmatch(attempt_name) is None:
        raise Candidate32PlanError("attempt_name_invalid")
    directory = TARGET_ROOT / attempt_name
    if directory.exists() or _is_link(directory):
        raise Candidate32PlanError("attempt_already_exists")
    directory.mkdir(mode=0o700)
    if directory.resolve(strict=True).parent != TARGET_ROOT or _is_link(directory):
        raise Candidate32PlanError("attempt_directory_invalid")
    output = directory / "request.json"
    payload = canonical_json(request)
    with output.open("xb") as stream:
        stream.write(payload)
        stream.flush()
    return output, hashlib.sha256(payload).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan one non-promoting surface inventory for all 32 P06 candidates."
    )
    parser.add_argument("--private-overlay", required=True, type=Path)
    parser.add_argument("--private-overlay-sha256", required=True)
    parser.add_argument("--projection", required=True, type=Path)
    parser.add_argument("--projection-sha256", required=True)
    parser.add_argument("--review-contract", required=True, type=Path)
    parser.add_argument("--review-contract-sha256", required=True)
    parser.add_argument("--attempt-name", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    private_overlay, private_bytes = read_json(
        args.private_overlay, args.private_overlay_sha256
    )
    projection, projection_bytes = read_json(args.projection, args.projection_sha256)
    contract, contract_bytes = read_json(
        args.review_contract, args.review_contract_sha256
    )
    request = build_request(
        private_overlay,
        args.private_overlay_sha256,
        projection,
        args.projection_sha256,
        contract,
        args.review_contract_sha256,
    )
    for path, before in (
        (args.private_overlay, private_bytes),
        (args.projection, projection_bytes),
        (args.review_contract, contract_bytes),
    ):
        if bounded_regular(path, ROOT, MAX_JSON_BYTES).read_bytes() != before:
            raise Candidate32PlanError("input_changed_during_plan")
    output, request_sha256 = publish_request(args.attempt_name, request)
    if output.name != "request.json":
        raise Candidate32PlanError("published_request_name_mismatch")
    print(
        "P06_TABLE_AUTOMATION_CANDIDATE_32_BATCH_PLANNED "
        f"cases=32 request_sha256={request_sha256} "
        "candidate_under_probe_execute=false runtime_support_promotion=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
