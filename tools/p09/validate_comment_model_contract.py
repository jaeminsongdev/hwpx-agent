#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-comment-model-v1.json"
MIGRATION = "protocol/migrations/p09-comment-model-v0-to-v1.md"
POLICY = "implementation/p09/P09-04_COMMENT_MODEL_POLICY.md"
REPORT = "implementation/p09/P09-04_COMMENT_MODEL_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-04-comment-model-source-qualification.v1.json"
BASE_COMMIT = "a29a5e023d219b505caeee71678bae3479e3b136"
OFFICIAL_REPOSITORY = "https://github.com/hancom-io/hwpx-owpml-model.git"
OFFICIAL_COMMIT = "1453388472c703a4b299a0834f425cdac16644b9"

SOURCE_SHA256 = {
    "docs/04_feature_catalog/10_ref.md": "34cfc9283d16b96bdb16d0ffec7a485f4b72548a49ec70fec2968b3c657743e4",
    "docs/04_feature_catalog/contracts/10_ref_contracts.md": "7062034902932355ac8e6c38a4798dd314f39c44518b7e85c26fe71a7a72cc29",
    "docs/09_roadmap/P09_fields_forms_notes_references.md": "0f4068c4dc5484cc348a145c892a2e1d2d3896d421b77c2fa23bb123956f4b55",
    "docs/03_document_model/09_fields_controls_references.md": "3068742808467f298d289c7401980c617981d748dfa73422bab8f7174ef10a20",
}
OFFICIAL_SOURCE_SHA256 = {
    "OWPML/Class/enumdef.h": "1c86392c934ac85f7ddd85c710b76be7649403a8404bce146db52558a0b95457",
    "OWPML/Class/Para/fieldBegin.h": "b216be07244a7a0c50f7dd2f40140d9ff202fefbb9b1b6092559dcd1aa08ad4f",
    "OWPML/Class/Para/fieldBegin.cpp": "22e5f613788a88ca003b5f0c23fe1d4333eadd21e9a3ca18d426d262a9e79450",
    "OWPML/Class/Para/fieldEnd.h": "88dd97103c537674dba0b3ac917b81ec5223fd3a518652330decb233b556791c",
    "OWPML/Class/Para/fieldEnd.cpp": "2937fbca1ff5b99bb05672544dd079c4165c7ada174edbb654873aecb7f8018d",
    "OWPML/Class/Para/hiddenComment.h": "2a545d1f1ae941841542b44c31e2c2393a2c6a3731e174240d8112f2e38d2ae7",
    "OWPML/Class/Para/hiddenComment.cpp": "263265fc0735d0248c5d02b59efcde9e0223bced1a8b53d3abbd5a026cee620f",
    "OWPML/Class/Para/ctrl.h": "e043d1b8a570724179ba7f57f1521dbb65a2c393ba116dbb0d2c3bae2277cc7e",
    "OWPML/Class/Para/ctrl.cpp": "a928569df0b890d8a58470a70a1501520bfb4d8af121df58eeb1fd8b9e0eed1d",
    "OWPML/Class/Head/MemoShapeType.h": "e62c220c87702b71045f9450f2e1008566ae7e987b58d7da4a5d526cfb31def3",
    "OWPML/Class/Head/MemoShapeType.cpp": "4bf16ef5e137e21c608182ed501798a72189ed8294ca609d4763a9047bc049fa",
    "OWPML/Class/Head/memoProperties.h": "8e24d3d3d1d4cff85204acf32971e71a42e2538852c8c20ac997aefe912f10d2",
    "OWPML/Class/Head/memoProperties.cpp": "db8b58ee6735ef18b1f3f3a1ff6d8dd1dfaa6ff9c0b8968b1175ea0aaff44bbf",
    "OWPML/Class/Head/MappingTableType.h": "e6fb943542970f2fd1538feaad254f31249f02ef93cfd08504e2422c5c495797",
    "OWPML/Class/Head/MappingTableType.cpp": "cc51ada34677b2e7670f9bb9f786fa79928c980e9cbe68924f8e2013b6682db2",
    "OWPML/Class/Para/SectionDefinitionType.h": "5e0862cbaf02ff2cf12b9dc3c86828e0856a4210d4d9c319a0c2877138f62acc",
    "OWPML/Class/Para/SectionDefinitionType.cpp": "4cfcca9bee299c3fbfe2cf2e2e3ec09027a4fa8c404cbb68f141cb584058c7e4",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "223c597e4c067566417237a852bed55d6f3893ac36418256c7943c0163724433",
    "crates/domain-ir/src/comment_model.rs": "aa332c72c54480442cf64bf540ce8e75d89817c6620c3fc0b4141bc299956e1b",
    "crates/domain-ir/tests/comment_model.rs": "70de531cc94ff4f0613129de589291b9fd8cb7de7414aa0a6c63d22d73b1b5b6",
}
CAPABILITIES = {
    "REF-026": "ref.hidden_explanation",
    "REF-027": "ref.comment_insert",
    "REF-028": "ref.comment_style",
    "REF-029": "ref.comment_show_hide",
    "REF-030": "ref.comment_resolve",
}
EXCLUDED = {"review.comment_delete": "P11"}
EXACT_STRUCTURES = [
    "hiddenComment/subList",
    "fieldBegin/MEMO",
    "fieldEnd",
    "memoProperties/memoPr",
    "memoShapeIDRef",
]
QUALIFIED_FACTS = {
    "hidden_explanation_tag": "hiddenComment",
    "hidden_explanation_children": ["subList"],
    "comment_control_tags": ["fieldBegin", "fieldEnd"],
    "comment_field_type": "MEMO",
    "field_begin_attributes": ["id", "type", "name", "editable", "dirty", "zorder", "fieldid"],
    "field_begin_children": ["parameters", "subList", "metaTag"],
    "field_end_attributes": ["beginIDRef", "fieldid"],
    "mapping_table_tag": "memoProperties",
    "memo_style_tag": "memoPr",
    "memo_style_attributes": [
        "id", "width", "lineWidth", "lineType", "lineColor", "fillColor", "activeColor", "memoType",
    ],
    "section_style_reference": "memoShapeIDRef",
    "line_type_count": 18,
    "line_width_count": 16,
    "memo_type_tokens": ["NOMAL", "USER_INSERT", "USER_DELETE", "USER_UPDATE"],
    "semantic_normal_mapping": "NOMAL_to_normal",
    "unverified_native_bindings": [
        "author", "created_at", "modified_at", "visibility", "resolved", "resolver", "resolved_at",
    ],
    "comment_delete_owner": "P11_review.comment_delete",
}
STATE_BINDING = {
    "inventory": "ordered_complete_sections_authors_styles_hidden_explanations_and_comments",
    "identity_anchor": "logical_begin_control_field_pair_and_exact_ordered_section_points",
    "payload": "body_plain_text_parameters_sublist_native_opaque_and_ordered_property_digests",
    "metadata": "typed_author_original_offset_timestamps_visibility_and_resolution_under_unverified_native_binding",
    "style": "memo_shape_id_width_line_width_line_type_colors_memo_type_section_reference_opaque_and_lock",
    "document": "non_comment_content_field_style_reference_resource_protection_and_opaque_document_digests",
    "request_and_build": "exact_source_state_and_document_flow_rechecked_and_plan_binding_sealed",
    "preservation": "only_named_hidden_insert_style_visibility_or_resolution_transition_may_change_state",
}
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "empty_section_or_style_inventory_and_invalid_or_colliding_identity_rejected",
    "invalid_ordered_anchor_section_author_style_or_native_pair_rejected",
    "invalid_digest_color_timestamp_resolution_or_opaque_state_rejected",
    "insert_requires_fresh_shown_unresolved_comment_and_exact_insertion_index",
    "document_section_style_explanation_and_comment_protection_rejected",
    "missing_ambiguous_and_noop_targets_rejected",
    "source_state_and_document_flow_drift_rejected_at_request_and_build",
    "sealed_plan_tamper_and_recomputed_target_mismatch_rejected",
    "unrelated_inventory_payload_reference_and_document_state_change_rejected",
    "identity_anchor_author_time_body_opaque_and_digest_values_redacted_from_debug",
    "no_raw_xml_partial_result_implicit_native_mapping_or_p11_delete_operation",
]
CLAIMS = {
    "unit_model_implemented": True,
    "five_capabilities_unit_passed": True,
    "official_structure_source_qualified": True,
    "complete_bound_state_preserved": True,
    "author_time_component_fixtures": True,
    "style_visibility_resolution_fixtures": True,
    "protection_fixtures": True,
    "request_and_build_drift_rejected": True,
    "p11_comment_delete_excluded": True,
    "native_author_time_binding_verified": False,
    "native_visibility_binding_verified": False,
    "native_resolution_binding_verified": False,
    "direct_hwpx": False,
    "actual_hwpx": False,
    "actual_hangul": False,
    "semantic_reopen": False,
    "field_readback": False,
    "reference_update": False,
    "hancom_open": False,
    "save_reopen": False,
    "render": False,
    "automation": False,
    "differential": False,
    "p09_04_green": False,
    "p09_complete": False,
    "production_ready": False,
    "product_complete": False,
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ("mod comment_model;", "CommentBuilder", "CommentDocumentState"),
    "crates/domain-ir/src/comment_model.rs": (
        'COMMENT_MODEL_SCHEMA_VERSION: &str = "hwpx-agent.comment-model/v1"',
        "pub enum CommentOperation",
        "UnverifiedMemoParameters",
        "pub struct CommentBuilder",
        "fn reject_duplicate_json_keys(",
        "<redacted>",
    ),
    "crates/domain-ir/tests/comment_model.rs": (
        "hidden_explanation_changes_only_enabled_and_binds_exact_capability",
        "insert_comment_binds_exact_identity_anchor_author_time_style_and_native_shape",
        "official_line_width_line_type_and_memo_type_catalogs_are_complete_and_distinct",
        "request_plan_and_build_recheck_exact_state_and_document_flow",
    ),
}
DIGEST = re.compile(r"^[0-9a-f]{64}$")


class DuplicateKey(ValueError):
    pass


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKey(key)
        result[key] = value
    return result


def file(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError("invalid bounded file")
    return path


def load(root: Path, relative: str) -> Any:
    return json.loads(file(root, relative).read_bytes(), object_pairs_hook=duplicate_guard)


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)

    expected_root = {
        "schema_version", "task", "scope", "source_lock_canonicalization",
        "source_qualification", "migration", "policy", "report", "source_locks",
        "capability_features", "excluded_capabilities", "model", "official_model",
        "implementation_files", "state_binding", "failure_policy", "evidence_boundary",
        "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_root:
        errors.append("contract_shape")
    if contract.get("schema_version") != "hwpx-agent.comment-model-contract/v1":
        errors.append("schema_version")
    if contract.get("task") != "P09-04" or contract.get("scope") != (
        "complete_typed_component_models_for_ref_026_through_ref_030_without_p11_delete"
    ):
        errors.append("identity")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    paths = (
        contract.get("source_qualification"), contract.get("migration"),
        contract.get("policy"), contract.get("report"),
    )
    if paths != (QUALIFICATION, MIGRATION, POLICY, REPORT):
        errors.append("document_paths")
    if contract.get("capability_features") != CAPABILITIES:
        errors.append("capability_mapping")
    if contract.get("excluded_capabilities") != EXCLUDED:
        errors.append("excluded_capability")
    if contract.get("model") != "hwpx-agent.comment-model/v1":
        errors.append("model")
    if contract.get("official_model") != {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "exact_native_structures": EXACT_STRUCTURES,
        "line_type_count": 18,
        "line_width_count": 16,
        "memo_type_count": 4,
        "semantic_binding": "unverified_memo_parameters",
    }:
        errors.append("official_model")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    if contract.get("state_binding") != STATE_BINDING:
        errors.append("state_binding")
    if contract.get("failure_policy") != FAILURE_POLICY:
        errors.append("failure_policy")
    expected_boundary = {
        **CLAIMS,
        "focused_rust_tests": "11/11 PASS",
        "private_contract_tests": "5/5 PASS",
        "direct_stage": "unit_passed",
    }
    if contract.get("evidence_boundary") != expected_boundary:
        errors.append("evidence_boundary")
    if contract.get("gate_decision") != {
        "component": "pass",
        "official_structure": "partially_qualified",
        "native_semantic_bindings": "unverified",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p09_04": "typed_component_pass_native_semantic_binding_direct_hwpx_and_target_not_run",
        "p09_04_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")

    source_count = validate_locks(root, contract.get("source_locks"), SOURCE_SHA256, errors, "source")
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


def validate_locks(
    root: Path,
    value: Any,
    expected: dict[str, str],
    errors: list[str],
    prefix: str,
) -> int:
    if not isinstance(value, list):
        errors.append(f"{prefix}_lock_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append(f"{prefix}_lock_shape")
            continue
        relative, digest = item.get("path"), item.get("sha256")
        if (
            not isinstance(relative, str) or relative in declared
            or not isinstance(digest, str) or not DIGEST.fullmatch(digest)
        ):
            errors.append(f"{prefix}_lock_identity")
            continue
        declared[relative] = digest
        try:
            if canonical_digest(file(root, relative)) != digest:
                errors.append(f"{prefix}_lock_digest")
        except (OSError, ValueError):
            errors.append(f"{prefix}_lock_path")
    if declared != expected:
        errors.append(f"{prefix}_lock_paths_exact")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, expected in IMPLEMENTATION_SHA256.items():
        try:
            path = file(root, relative)
            if canonical_digest(path) != expected:
                errors.append("implementation_digest")
            text = path.read_text(encoding="utf-8")
            if any(marker not in text for marker in MARKERS[relative]):
                errors.append("implementation_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
    return len(IMPLEMENTATION_SHA256)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "task", "base_commit", "scope", "official_model",
        "source_sha256", "implementation_sha256", "tests", "claims",
    }:
        errors.append("qualification_shape")
    if value.get("schema_version") != "hwpx-agent.p09-comment-model-source-qualification/v1":
        errors.append("qualification_schema")
    if value.get("task") != "P09-04" or value.get("base_commit") != BASE_COMMIT:
        errors.append("qualification_identity")
    if value.get("scope") != (
        "five_ref_026_to_ref_030_typed_comment_component_with_unverified_native_semantic_bindings"
    ):
        errors.append("qualification_scope")
    official = value.get("official_model")
    if not isinstance(official, dict) or set(official) != {
        "repository", "commit", "canonicalization", "source_sha256", "qualified_facts",
    }:
        errors.append("qualification_official_shape")
        official = {}
    if official.get("repository") != OFFICIAL_REPOSITORY or official.get("commit") != OFFICIAL_COMMIT:
        errors.append("qualification_official_identity")
    if official.get("canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("qualification_official_mode")
    if official.get("source_sha256") != OFFICIAL_SOURCE_SHA256:
        errors.append("qualification_official_sources")
    if official.get("qualified_facts") != QUALIFIED_FACTS:
        errors.append("qualification_official_facts")
    if value.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_sources")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    if value.get("tests") != {
        "public_comment_model": "10/10 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "11/11 PASS",
        "private_contract": "5/5 PASS",
        "test_kind": "typed_component_state_and_pinned_source_metadata",
        "network_used": False,
        "licensed_application_used": False,
        "hwpx_written": False,
    }:
        errors.append("qualification_tests")
    if value.get("claims") != CLAIMS:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "fail closed", "UnverifiedMemoParameters"),
        POLICY: (
            "five_capabilities_unit_passed=true",
            "native_author_time_binding_verified=false",
            "Reasoning level: `max`",
        ),
        REPORT: ("11/11 PASS", "Comment deletion", "product_complete=false"),
    }
    for relative, markers in expected.items():
        try:
            text = file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("document_path")


def result(errors: list[str], sources: int, implementation: int, qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p09-comment-model-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "official_source_files": len(OFFICIAL_SOURCE_SHA256),
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P09-04",
        "capabilities": 5,
        "p11_comment_delete": "excluded",
        "native_semantic_bindings": "unverified",
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_04_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    result_value = validate()
    print(json.dumps(result_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if result_value["state"] == "pass" else 1)
