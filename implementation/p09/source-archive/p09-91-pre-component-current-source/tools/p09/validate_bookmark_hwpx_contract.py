#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-bookmark-hwpx-v1.json"
QUALIFICATION = "implementation/p09/evidence/p09-13-bookmark-hwpx-source-qualification.v1.json"
MIGRATION = "protocol/migrations/p09-bookmark-hwpx-v0-to-v1.md"
POLICY = "implementation/p09/P09-13_BOOKMARK_HWPX_POLICY.md"
REPORT = "implementation/p09/P09-13_BOOKMARK_HWPX_REPORT.md"
PROFILE = "hwpx-agent.bookmark-hwpx.hwpml-2011-point-marker/v1"
OFFICIAL_REPOSITORY = "https://github.com/hancom-io/hwpx-owpml-model.git"
OFFICIAL_COMMIT = "1453388472c703a4b299a0834f425cdac16644b9"
BASE_COMMIT = "459ee3393de633d6cde541b37a811e51ecbef948"

SOURCE_SHA256 = {
    "docs/03_document_model/09_fields_controls_references.md": "3068742808467f298d289c7401980c617981d748dfa73422bab8f7174ef10a20",
    "docs/04_feature_catalog/10_ref.md": "34cfc9283d16b96bdb16d0ffec7a485f4b72548a49ec70fec2968b3c657743e4",
    "docs/04_feature_catalog/contracts/10_ref_contracts.md": "7062034902932355ac8e6c38a4798dd314f39c44518b7e85c26fe71a7a72cc29",
    "docs/09_roadmap/P09_fields_forms_notes_references.md": "0f4068c4dc5484cc348a145c892a2e1d2d3896d421b77c2fa23bb123956f4b55",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/link_reference.rs": "fd2e80c05810eea21b085499bab4f9bf95b8329287adc55fd46e240eb113766f",
    "crates/domain-ir/tests/link_reference.rs": "1514ff19e9c2041335ad62033767c2042056e0a1d3de3c1e69b6a2029107d252",
    "crates/hwpx-package/src/bookmark_hwpx.rs": "becab3bed9a44156f6a744cc9fb59690ae3da850b964fc4506e16cf9afec1210",
    "crates/hwpx-package/tests/bookmark_hwpx.rs": "e27df62629c93e89cf503406acb5946bb9fd7b6bdb65783bb13eb5546563ccf3",
}
OFFICIAL_SHA256 = {
    "OWPML/Class/Para/bookmark.h": "b3aa6c83671e924e09dffb8206c67ab0b48102927888393e33d4f358d0e940e0",
    "OWPML/Class/Para/bookmark.cpp": "c3a3d60c5bd7350e2700fae76686e4e555fddb125b9402844c711b8449268807",
    "OWPML/Class/Para/ctrl.h": "e043d1b8a570724179ba7f57f1521dbb65a2c393ba116dbb0d2c3bae2277cc7e",
    "OWPML/Class/Para/ctrl.cpp": "a928569df0b890d8a58470a70a1501520bfb4d8af121df58eeb1fd8b9e0eed1d",
    "OWPML/Class/Para/RunType.h": "d794636b3c03756f464b13629156f2258e818f3f67f9f9dd41f38cb6a5a2a432",
    "OWPML/Class/Para/RunType.cpp": "dbaa0fe2b553dccc13381c856fd9c188185a16bf63685f575acf6bf2c9b88dee",
}
FEATURE_CAPABILITIES = {
    "REF-031": "ref.bookmark_insert",
    "REF-032": "ref.bookmark_delete",
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/link_reference.rs": (
        'Self::InsertBookmark { .. } => "ref.bookmark_insert"',
        'Self::DeleteBookmark { .. } => "ref.bookmark_delete"',
        "source_document_flow_sha256",
        "target_document_flow_sha256",
    ),
    "crates/domain-ir/tests/link_reference.rs": (
        "bookmark_insert_and_unreferenced_delete_are_exact_and_preserving",
        "request_plan_and_build_recheck_exact_state_and_flow",
    ),
    "crates/hwpx-package/src/bookmark_hwpx.rs": (
        "BOOKMARK_HWPX_PROFILE_ID",
        "source_bookmark_wrapper_sha256",
        "bookmark_transition",
        "verify_preservation",
        "tampered_private_plan_binding_is_rejected",
        "<redacted>",
    ),
    "crates/hwpx-package/tests/bookmark_hwpx.rs": (
        "reads_exact_point_markers_and_preserves_order_and_boundaries",
        "ref_031_inserts_one_marker_at_exact_content_boundary",
        "ref_032_deletes_only_the_exact_wrapper",
        "same_boundary_insertion_respects_complete_bookmark_inventory_order",
        "source_state_flow_plan_and_finite_limits_are_bound",
    ),
}
DIGEST = re.compile(r"^[0-9a-f]{64}$")


class ContractError(ValueError):
    pass


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def bounded_file(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ContractError(f"invalid_file:{relative}")
    return path


def load(root: Path, relative: str) -> Any:
    data = bounded_file(root, relative).read_bytes()
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=duplicate_guard)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"invalid_json:{relative}") from error


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_boundary() -> dict[str, Any]:
    return {
        "direct_stage": "two_rows_static_section_integration_passed",
        "integration_rows": 2,
        "static_section_hwpx": True,
        "typed_target_projection_readback": True,
        "point_bookmark_insert_delete": True,
        "outside_delta_byte_preserved": True,
        "complete_state_and_flow_bound": True,
        "ranged_bookmarks": False,
        "complete_package_hwpx": False,
        "actual_hwpx": False,
        "actual_hangul": False,
        "save_reopen": False,
        "field_readback": False,
        "reference_update": False,
        "hancom_open": False,
        "render": False,
        "automation": False,
        "differential": False,
        "green_rows": 0,
        "p09_complete": False,
        "production_ready": False,
        "product_complete": False,
    }


def validate(
    root: Path = ROOT,
    *,
    contract_override: dict[str, Any] | None = None,
    qualification_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = contract_override if contract_override is not None else load(root, CONTRACT)
        qualification = (
            qualification_override if qualification_override is not None else load(root, QUALIFICATION)
        )
    except (OSError, ContractError):
        return result(["contract_or_qualification_json"], 0, 0, False)
    validate_contract(contract, errors)
    source_count = validate_locks(root, contract.get("source_locks"), SOURCE_SHA256, True, errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(qualification, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


def validate_contract(contract: Any, errors: list[str]) -> None:
    keys = {
        "schema_version", "task", "source_lock_canonicalization", "source_qualification",
        "migration", "policy", "report", "source_locks", "implementation_files", "profile",
        "feature_capabilities", "admitted_profile", "planning", "failure_policy",
        "evidence_boundary", "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != keys:
        errors.append("contract_shape")
        return
    if contract["schema_version"] != "hwpx-agent.p09-bookmark-hwpx-contract/v1":
        errors.append("schema_version")
    if contract["task"] != "P09-13" or contract["profile"] != PROFILE:
        errors.append("identity")
    if contract["source_lock_canonicalization"] != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    if (contract["source_qualification"], contract["migration"], contract["policy"], contract["report"]) != (
        QUALIFICATION, MIGRATION, POLICY, REPORT
    ):
        errors.append("document_paths")
    if contract["implementation_files"] != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    if contract["feature_capabilities"] != FEATURE_CAPABILITIES:
        errors.append("features")
    admitted = contract["admitted_profile"]
    if not isinstance(admitted, dict) or admitted.get("native_shape") != "direct_run_child_ctrl_with_one_empty_name_only_bookmark":
        errors.append("native_profile")
    if not isinstance(contract["failure_policy"], list) or len(contract["failure_policy"]) != 7:
        errors.append("failure_policy")
    if contract["evidence_boundary"] != expected_boundary():
        errors.append("claim_promotion")
    if contract["gate_decision"] != {
        "component": "pass",
        "static_section_direct_hwpx": "pass",
        "ref_031_stage": "integration_passed",
        "ref_032_stage": "integration_passed",
        "current_target": "not_run",
        "release_green_rows": 0,
        "p09": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")


def validate_locks(
    root: Path, value: Any, expected: dict[str, str], canonical: bool, errors: list[str]
) -> int:
    if not isinstance(value, list):
        errors.append("source_lock_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        relative, digest = item.get("path"), item.get("sha256")
        if not isinstance(relative, str) or relative in declared or not isinstance(digest, str) or not DIGEST.fullmatch(digest):
            errors.append("source_lock_identity")
            continue
        declared[relative] = digest
        try:
            actual = canonical_digest(bounded_file(root, relative)) if canonical else raw_digest(bounded_file(root, relative))
            if actual != digest:
                errors.append("source_lock_digest")
        except (OSError, ContractError):
            errors.append("source_lock_path")
    if declared != expected:
        errors.append("source_lock_set")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, expected in IMPLEMENTATION_SHA256.items():
        try:
            path = bounded_file(root, relative)
            if raw_digest(path) != expected:
                errors.append("implementation_digest")
            text = path.read_text(encoding="utf-8")
            if any(marker not in text for marker in IMPLEMENTATION_MARKERS[relative]):
                errors.append("implementation_marker")
        except (OSError, UnicodeDecodeError, ContractError):
            errors.append("implementation_path")
    return len(IMPLEMENTATION_SHA256)


def validate_qualification(value: Any, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append("qualification_shape")
        return False
    if value.get("schema_version") != "hwpx-agent.p09-bookmark-hwpx-source-qualification/v1" or value.get("task") != "P09-13" or value.get("base_commit") != BASE_COMMIT or value.get("profile") != PROFILE:
        errors.append("qualification_identity")
    official = value.get("official_source")
    if not isinstance(official, dict) or official.get("repository") != OFFICIAL_REPOSITORY or official.get("commit") != OFFICIAL_COMMIT or official.get("reviewed_sha256") != OFFICIAL_SHA256:
        errors.append("qualification_official")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    if value.get("tests") != {
        "link_reference_domain": "10/10 PASS",
        "bookmark_hwpx_public": "8/8 PASS",
        "bookmark_hwpx_private_tamper": "1/1 PASS",
        "fixture_classes": ["boundary", "happy_path", "negative", "preservation"],
        "focused_clippy": "PASS",
    }:
        errors.append("qualification_tests")
    if value.get("claims") != {
        "two_row_static_section_integration": True,
        "typed_target_projection_readback": True,
        "outside_delta_byte_preserved": True,
        "complete_state_and_flow_bound": True,
        "actual_hwpx": False,
        "actual_hangul": False,
        "save_reopen": False,
        "render": False,
        "automation": False,
        "differential": False,
        "green_rows": 0,
        "p09_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "fail closed", "no partial output"),
        POLICY: ("two_rows_static_section_integration_pass", "actual_hangul=false", "product_complete=false"),
        REPORT: ("8/8 PASS", "actual_hwpx=false", "green_rows=0"),
    }
    for relative, markers in expected.items():
        try:
            text = bounded_file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ContractError):
            errors.append("document_path")


def result(errors: list[str], sources: int, implementation: int, qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p09-bookmark-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_locks": implementation,
        "source_qualification": qualification,
        "integration_rows": 2,
        "static_section_hwpx": True,
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "green_rows": 0,
        "p09": "in_progress",
        "product_complete": False,
    }


def main() -> int:
    response = validate()
    print(json.dumps(response, sort_keys=True, separators=(",", ":")))
    return 0 if response["state"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
