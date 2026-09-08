#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-pagination-hwpx-v1.json"
REPORT = "implementation/p06/P06-07_TABLE_PAGINATION_HWPX_ADAPTER_REPORT.md"
MIGRATION = "protocol/migrations/p06-table-pagination-v1-to-hwpx-v1.md"

SOURCE_LOCKS = {
    "protocol/private/p06-table-pagination-v1.json":
        "b9315b6d6010703ca246497a8ec3395517a48230255197e81a2560f3436d70a8",
    "implementation/p06/P06-07_TABLE_PAGINATION_POLICY.md":
        "426b44021d7e9e0097bd33031c4ca3b20b131f8f78e0e537d4b2204037871f9a",
    "crates/hwpx-package/src/table_pagination.rs":
        "d667a4e34248379c6139ac62d1e0b385541d6dd959aeb8444b143077c6578e04",
    "crates/hwpx-package/tests/table_pagination.rs":
        "7485a352eef9f75aa1abb0016eb114cb227f13a49b7e0fbd178e648c6d01daf1",
}

IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_pagination.rs": (
        "hwpx-agent.table-pagination-hwpx.hancom-2020/1",
        "read_repeat_header_rows",
        "CaptionContentMismatch",
        "RequiredKeep",
        "push_changed_attribute_edit",
    ),
    "crates/hwpx-package/tests/table_pagination.rs": (
        "reads_all_native_page_break_mappings",
        "lowers_a_contiguous_multirow_header_prefix",
        "updates_existing_caption_without_changing_its_content",
        "enforces_finite_input_table_grid_and_dimension_limits",
    ),
    REPORT: (
        "PASS for the bounded static adapter component",
        "P06-07 remains in progress",
        "boundary-page suite",
    ),
    MIGRATION: (
        "additive current-PC Hangul 2020 adapter boundary",
        "required_keep",
        "Other PCs and Hangul",
    ),
}


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("duplicate JSON key")
        output[key] = value
    return output


def safe_path(root: Path, relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
        raise ValueError("unsafe path")
    path = (root / Path(*candidate.parts)).resolve()
    if root.resolve() not in path.parents:
        raise ValueError("outside root")
    return path


def bounded_bytes(root: Path, relative: str, limit: int = 4 * 1024 * 1024) -> bytes:
    path = safe_path(root, relative)
    size = path.stat().st_size
    if size <= 0 or size > limit:
        raise ValueError("file size")
    data = path.read_bytes()
    if len(data) != size:
        raise ValueError("file changed while reading")
    return data


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json(bounded_bytes(root, CONTRACT, 512_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0)
    validate_contract(contract, errors)
    source_count = validate_source_locks(root, contract, errors)
    implementation_count = validate_markers(root, errors)
    return result(sorted(set(errors)), source_count, implementation_count)


def validate_contract(contract: dict[str, Any], errors: list[str]) -> None:
    expected_keys = {
        "schema_version", "model_schema_version", "observation_schema_version",
        "adapter_profile_id", "scope", "predecessor", "source_lock_canonicalization",
        "source_locks", "native_mapping", "owned_attribute_values", "preservation_policy",
        "finite_limits", "static_verification", "gate_decision", "failure_policy",
        "migration", "report", "not_claimed",
    }
    if set(contract) != expected_keys:
        errors.append("contract_shape")
    exact = {
        "schema_version": "hwpx-agent.p06-07-table-pagination-hwpx-contract/v1",
        "model_schema_version": "hwpx-agent.table-pagination/v1",
        "observation_schema_version": "hwpx-agent.table-pagination-observation/v1",
        "adapter_profile_id": "hwpx-agent.table-pagination-hwpx.hancom-2020/1",
        "scope": "p06_07_bounded_current_pc_hancom_2020_static_hwpx_adapter_component",
        "source_lock_canonicalization": "exact_file_bytes_sha256",
        "migration": MIGRATION,
        "report": REPORT,
    }
    for key, value in exact.items():
        if contract.get(key) != value:
            errors.append(key)
    if contract.get("predecessor") != {
        "path": "protocol/private/p06-table-pagination-v1.json",
        "sha256": SOURCE_LOCKS["protocol/private/p06-table-pagination-v1.json"],
        "state": "immutable_pure_pagination_contract",
    }:
        errors.append("predecessor")
    mapping = contract.get("native_mapping")
    if not isinstance(mapping, dict) or mapping.get("page_break") != {
        "CELL": "allow", "TABLE": "avoid_row", "NONE": "avoid_table",
        "required_keep": "reject_no_exact_table_attribute",
    } or mapping.get("repeat_header") \
            != "table_boolean_plus_contiguous_uniform_cell_header_prefix" \
            or mapping.get("caption_creation_or_removal") != "reject":
        errors.append("native_mapping")
    verification = contract.get("static_verification")
    if not isinstance(verification, dict) \
            or verification.get("focused_rust_tests") != 10 \
            or set(verification.values()) != {10, "pass"}:
        errors.append("static_verification")
    if contract.get("gate_decision") != {
        "pure_pagination_validator": "pass",
        "static_hwpx_adapter_component": "pass",
        "actual_hancom_2020_boundary_page_suite": "not_run",
        "actual_hancom_2020_save_reopen_pdf_oracle": "not_run",
        "p06_07": "in_progress",
        "p06": "in_progress",
    }:
        errors.append("gate_decision")
    not_claimed = contract.get("not_claimed")
    if not isinstance(not_claimed, dict) or set(not_claimed.values()) != {False}:
        errors.append("not_claimed")


def validate_source_locks(root: Path, contract: dict[str, Any], errors: list[str]) -> int:
    locks = contract.get("source_locks")
    if not isinstance(locks, list):
        errors.append("source_locks_shape")
        return 0
    actual: dict[str, str] = {}
    for item in locks:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_locks_shape")
            continue
        path, digest = item.get("path"), item.get("sha256")
        if not isinstance(path, str) or not isinstance(digest, str) or path in actual:
            errors.append("source_locks_shape")
            continue
        actual[path] = digest
        try:
            if sha256(bounded_bytes(root, path)) != digest:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_path_or_encoding")
    if actual != SOURCE_LOCKS:
        errors.append("source_locks_exact")
    return len(actual)


def validate_markers(root: Path, errors: list[str]) -> int:
    count = 0
    for path, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_bytes(root, path).decode("utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path_or_encoding")
            continue
        count += 1
        if any(marker not in text for marker in markers):
            errors.append("implementation_markers")
    return count


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-07-table-pagination-hwpx-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": errors,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "static_hwpx_adapter_component": "pass" if not errors else "not_proven",
        "actual_hancom_2020_boundary_page_suite": "not_run",
        "actual_hancom_2020_save_reopen_pdf_oracle": "not_run",
        "p06_07": "in_progress",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
