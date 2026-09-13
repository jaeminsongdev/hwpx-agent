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
REQUEST_SCHEMA = "hwpx-agent.p06-09-table-automation-candidate-6-request/v1"
ATTEMPT_RE = re.compile(
    r"p06-09-table-automation-candidate-6-[0-9]{8}-[0-9]{2}\Z"
)
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
MAX_JSON_BYTES = 32 * 1024 * 1024

EXPECTED_TARGET = {
    "profile_id": "hancom-hangul-2020-secondary",
    "product": "Hancom Hangul 2020",
    "build": "11.0.0.9136",
    "locale": "ko-KR",
    "architecture": "x86",
}
EXPECTED_ROWS = (
    ("TABLE-010", "table.split_table", "current_row_boundary"),
    ("TABLE-015", "table.delete_columns", "current_column_block"),
    ("TABLE-016", "table.split_cell", "single_cell"),
    ("TABLE-017", "table.merge_cells", "adjacent_two_cell_block"),
    ("TABLE-046", "table.cell_border", "single_cell"),
    ("TABLE-048", "table.cell_fill", "single_cell"),
)
EXPECTED_PARAMETER_STATE = {
    "TABLE-010": "source_declares_none",
    "TABLE-015": "documented_candidate",
    "TABLE-016": "documented_candidate",
    "TABLE-017": "source_declares_none",
    "TABLE-046": "documented_candidate",
    "TABLE-048": "documented_candidate",
}
REGISTRY_ROOT_KEYS = {
    "schema_version",
    "source_lock_id",
    "restricted_derivative",
    "generator",
    "inputs",
    "target",
    "bindings",
    "coverage",
    "runtime_qualification",
}
PROJECTION_ROOT_KEYS = {
    "schema_version",
    "target",
    "source_registry_sha256",
    "row_count",
    "rows",
    "privacy",
}


class CandidateBatchPlanError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CandidateBatchPlanError("duplicate_json_key")
        result[key] = value
    return result


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def bounded_regular(path: Path, root: Path, maximum: int) -> Path:
    resolved_root = root.resolve(strict=True)
    candidate = path if path.is_absolute() else ROOT / path
    lexical = candidate.absolute()
    try:
        relative = lexical.relative_to(resolved_root)
    except ValueError as error:
        raise CandidateBatchPlanError("path_outside_boundary") from error
    cursor = resolved_root
    for part in relative.parts:
        cursor /= part
        if _is_link(cursor):
            raise CandidateBatchPlanError("linked_path")
    resolved = lexical.resolve(strict=True)
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise CandidateBatchPlanError("path_outside_or_not_file")
    size = resolved.stat().st_size
    if size <= 0 or size > maximum:
        raise CandidateBatchPlanError("file_size_limit")
    return resolved


def read_json(path: Path, expected_sha256: str) -> tuple[dict[str, Any], bytes]:
    if SHA256_RE.fullmatch(expected_sha256) is None:
        raise CandidateBatchPlanError("expected_sha256_invalid")
    resolved = bounded_regular(path, ROOT, MAX_JSON_BYTES)
    data = resolved.read_bytes()
    if len(data) != resolved.stat().st_size:
        raise CandidateBatchPlanError("file_changed_during_read")
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise CandidateBatchPlanError("input_sha256_mismatch")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CandidateBatchPlanError("invalid_json") from error
    if not isinstance(value, dict):
        raise CandidateBatchPlanError("json_root_not_object")
    return value, data


def require_target(registry: dict[str, Any], projection: dict[str, Any]) -> None:
    target = registry.get("target")
    projected = projection.get("target")
    if not isinstance(target, dict) or not isinstance(projected, dict):
        raise CandidateBatchPlanError("target_missing")
    expected_registry = {
        "profile_id": EXPECTED_TARGET["profile_id"],
        "product": EXPECTED_TARGET["product"],
        "major_release": "2020",
        "exact_build": EXPECTED_TARGET["build"],
        "locale": EXPECTED_TARGET["locale"],
        "architecture": EXPECTED_TARGET["architecture"],
        "license_state": "approved",
        "routing_enabled": False,
    }
    if any(target.get(key) != value for key, value in expected_registry.items()):
        raise CandidateBatchPlanError("registry_target_mismatch")
    if projected != {
        **EXPECTED_TARGET,
        "scope": "current_pc_personal_local_development",
    }:
        raise CandidateBatchPlanError("projection_target_mismatch")


def build_request(
    registry: dict[str, Any],
    registry_sha256: str,
    projection: dict[str, Any],
    projection_sha256: str,
) -> dict[str, Any]:
    if set(registry) != REGISTRY_ROOT_KEYS or set(projection) != PROJECTION_ROOT_KEYS:
        raise CandidateBatchPlanError("input_shape_mismatch")
    if (
        registry.get("restricted_derivative") is not True
        or registry.get("runtime_qualification")
        != {"state": "not_run", "probe_required": True, "qualified_binding_count": 0}
        or projection.get("source_registry_sha256") != registry_sha256
        or projection.get("row_count") != 61
        or projection.get("privacy")
        != {
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
        }
    ):
        raise CandidateBatchPlanError("input_boundary_mismatch")
    require_target(registry, projection)

    expected_identity = {(feature, capability) for feature, capability, _ in EXPECTED_ROWS}
    registry_rows = [
        row
        for row in registry.get("bindings", [])
        if (row.get("feature_id"), row.get("capability_id")) in expected_identity
    ]
    projection_rows = [
        row
        for row in projection.get("rows", [])
        if (row.get("feature_id"), row.get("capability_id")) in expected_identity
    ]
    registry_by_identity = {
        (row.get("feature_id"), row.get("capability_id")): row
        for row in registry_rows
        if isinstance(row, dict)
    }
    projection_by_identity = {
        (row.get("feature_id"), row.get("capability_id")): row
        for row in projection_rows
        if isinstance(row, dict)
    }
    if (
        len(registry_rows) != 6
        or len(registry_by_identity) != 6
        or len(projection_rows) != 6
        or len(projection_by_identity) != 6
        or set(registry_by_identity) != expected_identity
        or set(projection_by_identity) != expected_identity
    ):
        raise CandidateBatchPlanError("candidate_identity_mismatch")

    cases: list[dict[str, Any]] = []
    action_ids: set[str] = set()
    for feature_id, capability_id, context in EXPECTED_ROWS:
        identity = (feature_id, capability_id)
        source = registry_by_identity[identity]
        public = projection_by_identity[identity]
        invocation = source.get("invocation")
        if (
            source.get("status") != "candidate_unverified"
            or source.get("binding_key")
            != (
                f"{capability_id}@hancom-hangul-2020-secondary/"
                "11.0.0.9136/ko-KR"
            )
            or source.get("scope_class") != "artifact_semantics"
            or source.get("runtime_support_state") != "unverified"
            or source.get("routing_enabled") is not False
            or not isinstance(invocation, dict)
            or invocation.get("kind") != "action"
            or not isinstance(invocation.get("action_id"), str)
            or not invocation["action_id"]
            or invocation.get("parameter_set_state")
            != EXPECTED_PARAMETER_STATE[feature_id]
            or invocation.get("parameter_map_state") != "pending_runtime_probe"
            or invocation.get("parameter_map") != []
            or public
            != {
                "feature_id": feature_id,
                "capability_id": capability_id,
                "binding_status": "candidate_unverified",
                "runtime_support_state": "unverified",
                "routing_enabled": False,
            }
        ):
            raise CandidateBatchPlanError("candidate_boundary_mismatch")
        action_id = invocation["action_id"]
        if action_id in action_ids:
            raise CandidateBatchPlanError("candidate_action_id_duplicate")
        action_ids.add(action_id)
        parameter_set_id = invocation.get("parameter_set_id")
        if (
            EXPECTED_PARAMETER_STATE[feature_id] == "source_declares_none"
            and parameter_set_id is not None
        ) or (
            EXPECTED_PARAMETER_STATE[feature_id] == "documented_candidate"
            and (not isinstance(parameter_set_id, str) or not parameter_set_id)
        ):
            raise CandidateBatchPlanError("parameter_set_boundary_mismatch")
        cases.append(
            {
                "index": len(cases) + 1,
                "feature_id": feature_id,
                "capability_id": capability_id,
                "binding_key": source.get("binding_key"),
                "action_id": action_id,
                "parameter_set_id": parameter_set_id,
                "parameter_set_state": invocation["parameter_set_state"],
                "selection_context": context,
                "surface_probe": "is_action_enable_and_default_read_only",
                "execute": False,
            }
        )

    return {
        "schema_version": REQUEST_SCHEMA,
        "state": "planned",
        "scope": "exact_current_pc_hancom_2020_table_candidate_6_surface_batch",
        "target": {
            **EXPECTED_TARGET,
            "prog_id": "HWPFrame.HwpObject.2",
            "registry_view": "Registry32",
            "client": "windows_powershell_x86_sta",
            "executable_sha256": (
                "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
            ),
        },
        "inputs": {
            "private_registry_sha256": registry_sha256,
            "public_projection_sha256": projection_sha256,
        },
        "session_strategy": "one_hwp_session_one_generated_3x3_table",
        "case_count": 6,
        "cases": cases,
        "policy": {
            "candidate_action_execute_allowed": False,
            "default_read_allowed": True,
            "user_document_open_allowed": False,
            "external_network_allowed": False,
            "registry_or_system_setting_write_allowed": False,
            "computer_use_click_or_type_allowed": False,
            "preexisting_hwp_process_policy": "refuse",
            "unexpected_window_policy": "stop_unverified",
            "publication": "create_new_exact_attempt_only",
        },
        "promotion": {
            "action_identifier_presence": "eligible_after_runtime_pass",
            "parameter_set_surface": "eligible_after_runtime_pass",
            "parameter_map": "not_eligible",
            "runtime_support_state": "not_eligible",
            "routing_enabled": False,
            "differential": "not_run",
            "p06": "in_progress",
        },
    }


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def publish_request(attempt_name: str, request: dict[str, Any]) -> tuple[Path, str]:
    if ATTEMPT_RE.fullmatch(attempt_name) is None:
        raise CandidateBatchPlanError("attempt_name_invalid")
    directory = TARGET_ROOT / attempt_name
    if directory.exists() or _is_link(directory):
        raise CandidateBatchPlanError("attempt_already_exists")
    directory.mkdir(mode=0o700)
    if directory.resolve(strict=True).parent != TARGET_ROOT or _is_link(directory):
        raise CandidateBatchPlanError("attempt_directory_invalid")
    output = directory / "request.json"
    payload = canonical_json(request)
    with output.open("xb") as stream:
        stream.write(payload)
        stream.flush()
    return output, hashlib.sha256(payload).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan one non-executing runtime surface probe for six table candidates."
    )
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--registry-sha256", required=True)
    parser.add_argument("--projection", required=True, type=Path)
    parser.add_argument("--projection-sha256", required=True)
    parser.add_argument("--attempt-name", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry, registry_bytes = read_json(args.registry, args.registry_sha256)
    projection, projection_bytes = read_json(args.projection, args.projection_sha256)
    request = build_request(
        registry, args.registry_sha256, projection, args.projection_sha256
    )
    if bounded_regular(args.registry, ROOT, MAX_JSON_BYTES).read_bytes() != registry_bytes:
        raise CandidateBatchPlanError("registry_changed_during_plan")
    if bounded_regular(args.projection, ROOT, MAX_JSON_BYTES).read_bytes() != projection_bytes:
        raise CandidateBatchPlanError("projection_changed_during_plan")
    output, request_sha256 = publish_request(args.attempt_name, request)
    print(
        "P06_TABLE_AUTOMATION_CANDIDATE_6_BATCH_PLANNED "
        f"cases=6 request_sha256={request_sha256} "
        "candidate_execute=false runtime_support_promotion=false"
    )
    if output.name != "request.json":
        raise CandidateBatchPlanError("published_request_name_mismatch")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
