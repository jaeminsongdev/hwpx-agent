#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-cross-reference-v1.json"
MIGRATION = "protocol/migrations/p09-cross-reference-v0-to-v1.md"
POLICY = "implementation/p09/P09-06_CROSS_REFERENCE_POLICY.md"
REPORT = "implementation/p09/P09-06_CROSS_REFERENCE_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-06-cross-reference-source-qualification.v1.json"
BASE_COMMIT = "e398a19"
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
    "OWPML/Class/Para/ParameterList.h": "e06d765a4d435efc10404a56c58d2894e4fb5830e3128fef316b176768543807",
    "OWPML/Class/Para/ParameterList.cpp": "a8d68844c27deb9bd150f9f8fd4ed4450a6b8d3b5a026e35004c200f3fde6d21",
    "OWPML/Class/Para/ctrl.h": "e043d1b8a570724179ba7f57f1521dbb65a2c393ba116dbb0d2c3bae2277cc7e",
    "OWPML/Class/Para/ctrl.cpp": "a928569df0b890d8a58470a70a1501520bfb4d8af121df58eeb1fd8b9e0eed1d",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b4726732a47175205a7e35f3aa8e018e66b2a0fbada144bebeac3f395540c058",
    "crates/domain-ir/src/cross_reference.rs": "90f2dfb5efed392b6083b5f7fe67dc812fb96dc1866c7015c0e8cd885de05059",
    "crates/domain-ir/tests/cross_reference.rs": "5355358f79cd92c8f77a4b109414bc9dadb6a214b12622883d84625ee0884bde",
}
CAPABILITIES = {"REF-035": "ref.crossref_insert"}
EXCLUDED = {"REF-036": "P11", "REF-037_to_REF-040": "P09-07"}
TARGET_KINDS = ["bookmark", "heading", "numbered_paragraph", "caption", "footnote", "endnote"]
DISPLAY_KINDS = [
    "target_text", "target_name", "number_only", "label_and_number", "page_number",
    "relative_position",
]
EXACT_STRUCTURES = ["fieldBegin/CROSSREF", "fieldEnd"]
QUALIFIED_FACTS = {
    "cross_reference_control_tags": ["fieldBegin", "fieldEnd"],
    "cross_reference_field_type": "CROSSREF",
    "field_begin_attributes": ["id", "type", "name", "editable", "dirty", "zorder", "fieldid"],
    "field_begin_children": ["parameters", "subList", "metaTag"],
    "field_end_attributes": ["beginIDRef", "fieldid"],
    "unverified_native_bindings": [
        "crossref_parameter_keys", "target_kind_encoding", "display_kind_encoding",
        "anchor_binding", "cached_value_encoding", "update_semantics",
    ],
}
STATE_BINDING = {
    "inventory": "ordered_complete_sections_targets_cross_references_and_occupied_non_crossref_ids",
    "section": "identity_paragraph_count_run_inline_topology_opaque_state_and_lock",
    "target": "logical_identity_kind_anchor_semantic_name_text_label_number_page_dependencies_opaque_state_and_lock",
    "cross_reference": "logical_begin_control_field_identity_anchor_containment_target_display_update_cache_native_pair_opaque_state_and_lock",
    "target_graph": "complete_dangling_free_acyclic_dependency_and_containment_edges",
    "cache": "display_specific_target_projection_digest_display_value_digest_and_exact_current_or_stale_status",
    "occupied_native_ids": "sorted_complete_non_crossref_begin_control_field_id_and_field_name_digest_inventories",
    "document": "non_crossref_content_unrelated_field_bookmark_note_object_numbering_style_relationship_resource_protection_and_opaque_digests",
    "request_and_build": "exact_source_state_and_document_flow_rechecked_and_plan_binding_sealed",
    "preservation": "only_ordered_cross_reference_insertion_may_change_state",
}
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "empty_section_inventory_and_invalid_or_duplicate_identity_or_anchor_rejected",
    "invalid_native_field_pair_occupied_id_collision_digest_or_opaque_state_rejected",
    "missing_duplicate_self_referential_or_cyclic_target_graph_rejected",
    "incompatible_display_kind_or_inexact_containment_rejected",
    "stale_or_inconsistent_cache_rejected_for_insertion",
    "document_and_section_protection_rejected",
    "invalid_insertion_index_rejected",
    "source_state_and_document_flow_drift_rejected_at_request_plan_and_build",
    "sealed_plan_tamper_and_recomputed_target_mismatch_rejected",
    "sections_targets_occupied_ids_unrelated_inventories_and_opaque_state_preserved",
    "identities_anchors_digests_cached_values_and_payloads_redacted_from_debug",
    "no_raw_xml_action_path_partial_result_implicit_native_parameter_mapping_or_update_claim",
]
CLAIMS = {
    "unit_model_implemented": True,
    "ref_035_unit_passed": True,
    "official_structure_source_qualified": True,
    "target_graph_fixtures": True,
    "cache_projection_fixtures": True,
    "cycle_and_dangling_fixtures": True,
    "complete_bound_state_preserved": True,
    "request_and_build_drift_rejected": True,
    "native_crossref_parameters_verified": False,
    "ref_036_update_implemented": False,
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
    "p09_06_green": False,
    "p09_complete": False,
    "production_ready": False,
    "product_complete": False,
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ["mod cross_reference;", "pub use cross_reference::{"],
    "crates/domain-ir/src/cross_reference.rs": [
        'CROSS_REFERENCE_SCHEMA_VERSION: &str = "hwpx-agent.cross-reference/v1"',
        '"ref.crossref_insert"', "UnverifiedFieldParameters", "validate_acyclic_graph",
        "target_projection_sha256", "DocumentFlowDrift", "PlanTampered", "<redacted>",
    ],
    "crates/domain-ir/tests/cross_reference.rs": [
        "all_target_and_display_families_insert_with_exact_current_cache",
        "target_dependencies_and_contained_reference_cycles_fail_closed",
        "request_plan_and_build_recheck_exact_state_and_flow",
        "strict_json_limits_errors_and_debug_are_bounded_and_redacted",
    ],
}


def duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def file(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> Path:
    resolved_root = root.resolve()
    candidate = resolved_root / relative
    resolved = candidate.resolve()
    if resolved_root != resolved and resolved_root not in resolved.parents:
        raise ValueError("path escapes root")
    if candidate.is_symlink() or not resolved.is_file() or not 0 < resolved.stat().st_size <= maximum:
        raise ValueError("invalid bounded file")
    return resolved


def load(root: Path, relative: str) -> Any:
    return json.loads(
        file(root, relative).read_bytes(),
        object_pairs_hook=duplicate_rejecting_object,
    )


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, False)

    expected_keys = {
        "schema_version", "task", "scope", "source_lock_canonicalization",
        "source_qualification", "migration", "policy", "report", "source_locks",
        "capability_features", "excluded_capabilities", "model", "official_model",
        "implementation_files", "target_kinds", "display_kinds", "state_binding",
        "failure_policy", "evidence_boundary", "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_keys:
        errors.append("contract_shape")
    identities = {
        "schema_version": "hwpx-agent.cross-reference-contract/v1",
        "task": "P09-06",
        "scope": "complete_typed_component_model_for_ref_035",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
    }
    for key, expected in identities.items():
        if contract.get(key) != expected:
            errors.append("contract_identity")

    expected_locks = [{"path": path, "sha256": digest} for path, digest in SOURCE_SHA256.items()]
    if contract.get("source_locks") != expected_locks:
        errors.append("source_locks")
    for path, digest in SOURCE_SHA256.items():
        try:
            if canonical_digest(file(root, path)) != digest:
                errors.append("source_lock_digest")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("source_lock_digest")

    if contract.get("capability_features") != CAPABILITIES:
        errors.append("capabilities")
    if contract.get("excluded_capabilities") != EXCLUDED:
        errors.append("exclusions")
    if contract.get("model") != "hwpx-agent.cross-reference/v1":
        errors.append("model")
    if contract.get("target_kinds") != TARGET_KINDS or contract.get("display_kinds") != DISPLAY_KINDS:
        errors.append("target_or_display_kinds")
    expected_official = {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "exact_native_structures": EXACT_STRUCTURES,
        "field_begin_attributes": QUALIFIED_FACTS["field_begin_attributes"],
        "field_begin_children": QUALIFIED_FACTS["field_begin_children"],
        "field_end_attributes": QUALIFIED_FACTS["field_end_attributes"],
        "semantic_binding": "unverified_field_parameters",
    }
    if contract.get("official_model") != expected_official:
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
    expected_gate = {
        "component": "pass",
        "official_structure": "partially_qualified",
        "native_crossref_parameters": "unverified",
        "ref_036_update": "not_implemented_p11_owned",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p09_06": "typed_component_pass_native_parameter_lowering_direct_hwpx_and_target_not_run",
        "p09_06_green": False,
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
    if value.get("schema_version") != "hwpx-agent.p09-cross-reference-source-qualification/v1":
        errors.append("qualification_schema")
    if value.get("task") != "P09-06" or value.get("base_commit") != BASE_COMMIT:
        errors.append("qualification_identity")
    official = value.get("official_model")
    if not isinstance(official, dict) or official != {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_sha256": OFFICIAL_SOURCE_SHA256,
        "qualified_facts": QUALIFIED_FACTS,
    }:
        errors.append("qualification_official_sources")
    if value.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_sources")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    expected_tests = {
        "public_cross_reference": "10/10 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "11/11 PASS",
        "private_contract": "5/5 PASS",
        "test_kind": "typed_component_target_dag_cache_projection_and_pinned_source_metadata",
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
        POLICY: ("REF-035", "REF-036", "UnverifiedFieldParameters", "product_complete=false"),
        REPORT: ("10/10 PASS", "5/5 PASS", "actual_hangul=false", "P09-07"),
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
        "schema_version": "hwpx-agent.p09-cross-reference-validation/v1",
        "task": "P09-06",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "official_source_files": official_sources,
        "implementation_files": len(IMPLEMENTATION_SHA256),
        "source_qualification_verified": qualification_verified,
        "capabilities": len(CAPABILITIES),
        "native_crossref_parameters": "unverified",
        "ref_036_update": "not_implemented_p11_owned",
        "direct_stage": "unit_passed",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "reference_update": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_06_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    outcome = validate()
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if outcome["state"] == "pass" else 1)
