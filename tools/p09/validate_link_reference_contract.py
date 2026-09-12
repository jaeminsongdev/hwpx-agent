#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-link-reference-v1.json"
MIGRATION = "protocol/migrations/p09-link-reference-v0-to-v1.md"
POLICY = "implementation/p09/P09-05_LINK_REFERENCE_POLICY.md"
REPORT = "implementation/p09/P09-05_LINK_REFERENCE_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-05-link-reference-source-qualification.v1.json"
BASE_COMMIT = "bd168dd"
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
    "OWPML/Class/Para/bookmark.h": "b3aa6c83671e924e09dffb8206c67ab0b48102927888393e33d4f358d0e940e0",
    "OWPML/Class/Para/bookmark.cpp": "c3a3d60c5bd7350e2700fae76686e4e555fddb125b9402844c711b8449268807",
    "OWPML/Class/Para/fieldBegin.h": "b216be07244a7a0c50f7dd2f40140d9ff202fefbb9b1b6092559dcd1aa08ad4f",
    "OWPML/Class/Para/fieldBegin.cpp": "22e5f613788a88ca003b5f0c23fe1d4333eadd21e9a3ca18d426d262a9e79450",
    "OWPML/Class/Para/fieldEnd.h": "88dd97103c537674dba0b3ac917b81ec5223fd3a518652330decb233b556791c",
    "OWPML/Class/Para/fieldEnd.cpp": "2937fbca1ff5b99bb05672544dd079c4165c7ada174edbb654873aecb7f8018d",
    "OWPML/Class/Para/ParameterList.h": "e06d765a4d435efc10404a56c58d2894e4fb5830e3128fef316b176768543807",
    "OWPML/Class/Para/ParameterList.cpp": "a8d68844c27deb9bd150f9f8fd4ed4450a6b8d3b5a026e35004c200f3fde6d21",
    "OWPML/Class/Para/ctrl.h": "e043d1b8a570724179ba7f57f1521dbb65a2c393ba116dbb0d2c3bae2277cc7e",
    "OWPML/Class/Para/ctrl.cpp": "a928569df0b890d8a58470a70a1501520bfb4d8af121df58eeb1fd8b9e0eed1d",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "79301eb04cbef5277ea279ea5e0147deb5ce8a012bd5a01a6d5052f29eee9c21",
    "crates/domain-ir/src/link_reference.rs": "db6178b4c399a9c58773d39ed3609a8878aeeb1873b30c64fd248129e00c900f",
    "crates/domain-ir/tests/link_reference.rs": "c3fc396288a57b5e25d0bab0a7f05748b9a2c55450698ddfa88421da0c28ad46",
}
CAPABILITIES = {
    "REF-031": "ref.bookmark_insert",
    "REF-032": "ref.bookmark_delete",
    "REF-033": "ref.hyperlink_insert",
    "REF-034": "ref.hyperlink_edit",
}
EXCLUDED = {"REF-035": "P09-06", "REF-036": "P11"}
EXACT_STRUCTURES = ["bookmark/name", "fieldBegin/HYPERLINK", "fieldEnd"]
QUALIFIED_FACTS = {
    "bookmark_tag": "bookmark",
    "bookmark_attributes": ["name"],
    "hyperlink_control_tags": ["fieldBegin", "fieldEnd"],
    "hyperlink_field_type": "HYPERLINK",
    "field_begin_attributes": ["id", "type", "name", "editable", "dirty", "zorder", "fieldid"],
    "field_begin_children": ["parameters", "subList", "metaTag"],
    "field_end_attributes": ["beginIDRef", "fieldid"],
    "unverified_native_bindings": [
        "hyperlink_parameter_keys", "target_serialization", "display_range_semantics",
        "external_document_relationship",
    ],
}
STATE_BINDING = {
    "inventory": "ordered_complete_sections_bookmarks_hyperlinks_and_external_policy",
    "section": "identity_paragraph_count_run_inline_topology_opaque_state_and_lock",
    "bookmark": "logical_identity_exact_nfc_name_ordered_anchor_native_tag_opaque_state_and_lock",
    "hyperlink": "logical_begin_control_field_identity_anchor_target_display_native_pair_opaque_state_and_lock",
    "occupied_native_ids": "sorted_complete_non_hyperlink_begin_control_and_field_id_inventories",
    "target": "live_internal_bookmark_or_exactly_approved_safe_https_mailto_or_path_free_managed_document",
    "document": "non_reference_content_unrelated_field_style_object_relationship_resource_protection_and_opaque_digests",
    "request_and_build": "exact_source_state_and_document_flow_rechecked_and_plan_binding_sealed",
    "preservation": "only_named_insert_delete_or_target_display_transition_may_change_state",
}
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "empty_section_inventory_and_invalid_or_colliding_identity_anchor_or_name_rejected",
    "invalid_native_field_pair_occupied_id_collision_digest_or_opaque_state_rejected",
    "dangling_internal_target_and_referenced_bookmark_delete_rejected",
    "http_file_path_credentials_whitespace_backslash_and_malformed_email_rejected",
    "external_target_requires_enabled_kind_and_exact_target_digest_approval",
    "document_section_bookmark_and_hyperlink_protection_rejected",
    "missing_ambiguous_invalid_insertion_and_noop_targets_rejected",
    "source_state_and_document_flow_drift_rejected_at_request_and_build",
    "sealed_plan_tamper_and_recomputed_target_mismatch_rejected",
    "unrelated_inventory_identity_anchor_native_opaque_policy_and_document_state_change_rejected",
    "names_targets_artifacts_anchors_digests_and_payloads_redacted_from_debug",
    "no_raw_xml_action_path_partial_result_or_implicit_native_parameter_mapping",
]
CLAIMS = {
    "unit_model_implemented": True,
    "four_capabilities_unit_passed": True,
    "official_structure_source_qualified": True,
    "external_policy_fixtures": True,
    "dangling_reference_fixtures": True,
    "complete_bound_state_preserved": True,
    "request_and_build_drift_rejected": True,
    "native_hyperlink_parameters_verified": False,
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
    "p09_05_green": False,
    "p09_complete": False,
    "production_ready": False,
    "product_complete": False,
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ("mod link_reference;", "LinkReferenceBuilder", "HyperlinkTarget"),
    "crates/domain-ir/src/link_reference.rs": (
        'LINK_REFERENCE_SCHEMA_VERSION: &str = "hwpx-agent.link-reference/v1"',
        "pub enum LinkReferenceOperation", "UnverifiedFieldParameters",
        "external_approval_sha256", "occupied_non_hyperlink_begin_control_ids",
        "pub struct LinkReferenceBuilder",
        "fn reject_duplicate_json_keys(", "<redacted>",
    ),
    "crates/domain-ir/tests/link_reference.rs": (
        "bookmark_delete_rejects_dangling_internal_hyperlink",
        "inserts_internal_https_mailto_and_managed_document_targets",
        "unsafe_unapproved_and_malformed_external_targets_fail_closed",
        "request_plan_and_build_recheck_exact_state_and_flow",
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
    if contract.get("schema_version") != "hwpx-agent.link-reference-contract/v1":
        errors.append("schema_version")
    if contract.get("task") != "P09-05" or contract.get("scope") != (
        "complete_typed_component_models_for_ref_031_through_ref_034"
    ):
        errors.append("identity")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    paths = (
        contract.get("source_qualification"), contract.get("migration"),
        contract.get("policy"), contract.get("report"),
    )
    if paths != (QUALIFICATION, MIGRATION, POLICY, REPORT):
        errors.append("contract_paths")
    else:
        for path in paths:
            try:
                file(root, path)
            except (OSError, ValueError):
                errors.append("contract_paths")
                break

    expected_locks = [{"path": path, "sha256": digest} for path, digest in SOURCE_SHA256.items()]
    if contract.get("source_locks") != expected_locks:
        errors.append("source_locks")
    for path, digest in SOURCE_SHA256.items():
        try:
            if canonical_digest(file(root, path)) != digest:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_digest")

    if contract.get("capability_features") != CAPABILITIES:
        errors.append("capabilities")
    if contract.get("excluded_capabilities") != EXCLUDED:
        errors.append("exclusions")
    if contract.get("model") != "hwpx-agent.link-reference/v1":
        errors.append("model")
    official = contract.get("official_model")
    expected_official = {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "exact_native_structures": EXACT_STRUCTURES,
        "field_begin_attributes": QUALIFIED_FACTS["field_begin_attributes"],
        "field_begin_children": QUALIFIED_FACTS["field_begin_children"],
        "field_end_attributes": QUALIFIED_FACTS["field_end_attributes"],
        "semantic_binding": "unverified_field_parameters",
    }
    if official != expected_official:
        errors.append("official_model")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    if contract.get("state_binding") != STATE_BINDING:
        errors.append("state_binding")
    if contract.get("failure_policy") != FAILURE_POLICY:
        errors.append("failure_policy")

    boundary = contract.get("evidence_boundary")
    expected_boundary = {
        **CLAIMS,
        "focused_rust_tests": "11/11 PASS",
        "private_contract_tests": "5/5 PASS",
        "direct_stage": "unit_passed",
    }
    if boundary != expected_boundary:
        errors.append("evidence_boundary")
    expected_gate = {
        "component": "pass",
        "official_structure": "partially_qualified",
        "native_hyperlink_parameters": "unverified",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p09_05": "typed_component_pass_native_parameter_lowering_direct_hwpx_and_target_not_run",
        "p09_05_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }
    if contract.get("gate_decision") != expected_gate:
        errors.append("gate_decision")

    for path, digest in IMPLEMENTATION_SHA256.items():
        try:
            target = file(root, path)
            if canonical_digest(target) != digest:
                errors.append("implementation_digest")
            text = target.read_text(encoding="utf-8")
            if any(marker not in text for marker in MARKERS[path]):
                errors.append("implementation_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_digest")

    qualification_verified = validate_qualification(root, errors)
    validate_text_artifacts(root, errors)
    return result(errors, len(SOURCE_SHA256), len(OFFICIAL_SOURCE_SHA256), qualification_verified)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    expected_keys = {
        "schema_version", "task", "base_commit", "scope", "official_model", "source_sha256",
        "implementation_sha256", "tests", "claims",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        errors.append("qualification_shape")
    if value.get("schema_version") != "hwpx-agent.p09-link-reference-source-qualification/v1":
        errors.append("qualification_schema")
    if value.get("task") != "P09-05" or value.get("base_commit") != BASE_COMMIT:
        errors.append("qualification_identity")
    official = value.get("official_model")
    if not isinstance(official, dict) or official.get("repository") != OFFICIAL_REPOSITORY or (
        official.get("commit") != OFFICIAL_COMMIT
        or official.get("canonicalization") != "utf8_text_crlf_to_lf_sha256"
        or official.get("source_sha256") != OFFICIAL_SOURCE_SHA256
        or official.get("qualified_facts") != QUALIFIED_FACTS
    ):
        errors.append("qualification_official_sources")
    if value.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_sources")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    expected_tests = {
        "public_link_reference": "10/10 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "11/11 PASS",
        "private_contract": "5/5 PASS",
        "test_kind": "typed_component_state_external_policy_and_pinned_source_metadata",
        "network_used": False,
        "licensed_application_used": False,
        "hwpx_written": False,
    }
    if value.get("tests") != expected_tests:
        errors.append("qualification_tests")
    if value.get("claims") != CLAIMS:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_text_artifacts(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("no accepted v0", "unverified_field_parameters", "No defaults"),
        POLICY: ("REF-031", "REF-034", "UnverifiedFieldParameters", "product_complete=false"),
        REPORT: ("10/10 PASS", "5/5 PASS", "actual_hangul=false", "P09-06"),
    }
    for path, markers in expected.items():
        try:
            text = file(root, path).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("text_artifact")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("text_artifact")


def result(
    errors: list[str], source_locks: int, official_sources: int, qualification_verified: bool
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p09-link-reference-validation/v1",
        "task": "P09-05",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "official_source_files": official_sources,
        "implementation_files": len(IMPLEMENTATION_SHA256),
        "source_qualification_verified": qualification_verified,
        "capabilities": len(CAPABILITIES),
        "native_hyperlink_parameters": "unverified",
        "direct_stage": "unit_passed",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "reference_update": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_05_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    outcome = validate()
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if outcome["state"] == "pass" else 1)
