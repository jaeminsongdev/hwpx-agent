#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-citation-v1.json"
MIGRATION = "protocol/migrations/p09-citation-v0-to-v1.md"
POLICY = "implementation/p09/P09-08_CITATION_POLICY.md"
REPORT = "implementation/p09/P09-08_CITATION_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-08-citation-source-qualification.v1.json"
BASE_COMMIT = "50ceaef"
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
    "OWPMLApi/OWPMLDocumentDef.h": "45c9e8d171efd5233017f4cdc0154ce8cd082cbd43430b2cdc80581cb48e6d52",
    "OWPMLApi/OWPMLSerialize.h": "a3941b5cd15c263aad194ba2714f41a543505ab5ef804e639c09008bd2a58439",
    "OWPMLApi/OWPMLSerialize.cpp": "f5845f9f74f632b04d637f9f4a14a333bc30fbac9e675f7cbe0664df4c2515c3",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b4726732a47175205a7e35f3aa8e018e66b2a0fbada144bebeac3f395540c058",
    "crates/domain-ir/src/citation.rs": "50fb5bdc5376eb639c24aa0f9a3811e4aeee2b84ca1470a0e7dc0d5f7c523e13",
    "crates/domain-ir/tests/citation.rs": "54b4c44ea134612a7f44c465a97eac2da1d49ab91eaad1ae86bf849549a8c195",
}
CAPABILITIES = {"REF-044": "ref.citation_insert"}
EXCLUDED = {"REF-043": "P11", "REF-045": "P11"}
EXACT_STRUCTURES = [
    "fieldBegin/CITATION",
    "fieldEnd",
    "Custom/bibliography.xml",
    "manifest-id/bibliography",
    "media-type/application-xml",
]
QUALIFIED_FACTS = {
    "field_types": ["CITATION", "BIBLIOGRAPHY"],
    "citation_field": {"begin": "fieldBegin", "type": "CITATION", "end": "fieldEnd"},
    "bibliography_part": {
        "path": "Custom/bibliography.xml",
        "manifest_id": "bibliography",
        "media_type": "application/xml",
    },
    "bibliography_reader": "stub_returns_true_without_parsing",
    "bibliography_writer": "copies_existing_decompressed_part",
    "unverified_native_bindings": [
        "bibliography_record_xml",
        "provider_schema",
        "provider_record_key_mapping",
        "citation_parameter_keys",
        "citation_source_reference_encoding",
        "locator_prefix_suffix_encoding",
        "citation_visible_body",
        "refresh_semantics",
        "generated_bibliography_layout",
    ],
}
STATE_BINDING = {
    "inventory": "ordered_complete_sections_optional_bibliography_all_citations_and_occupied_non_citation_ids",
    "bibliography": "logical_identity_exact_qualified_package_binding_whole_part_digest_provider_version_locale_style_all_sources_opaque_state_and_lock",
    "source": "logical_identity_provider_key_semantic_display_raw_opaque_state_and_lock",
    "citation": "logical_and_native_identity_anchor_ordered_distinct_existing_sources_display_options_cache_native_pair_opaque_state_and_lock",
    "cache": "provider_version_locale_style_selected_source_records_in_citation_order_and_display_options",
    "occupied_native_ids": "sorted_complete_non_citation_control_field_id_and_field_name_digest_inventories",
    "document": "run_inline_page_topology_non_citation_content_unrelated_field_reference_note_toc_index_object_numbering_style_relationship_resource_protection_and_opaque_digests",
    "request_and_build": "exact_source_state_and_document_flow_rechecked_and_plan_binding_sealed",
    "preservation": "only_owned_ordered_citation_inventory_may_change",
}
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "empty_section_inventory_and_invalid_duplicate_or_colliding_identity_anchor_or_native_id_rejected",
    "missing_ambiguous_duplicate_or_over_ceiling_source_references_rejected",
    "duplicate_catalog_source_identity_and_provider_key_rejected",
    "malformed_locale_digest_opaque_state_display_options_and_native_pair_rejected",
    "stale_or_inconsistent_new_citation_cache_rejected",
    "document_and_target_section_protection_rejected_without_partial_state",
    "source_state_and_document_flow_drift_rejected_at_request_plan_and_build",
    "sealed_plan_tamper_and_recomputed_target_mismatch_rejected",
    "complete_bibliography_and_unrelated_inventories_preserved",
    "identities_provider_keys_records_field_names_display_text_parameters_and_digests_redacted_from_debug",
    "no_raw_xml_action_path_partial_result_implicit_provider_mapping_manage_generate_or_refresh_claim",
]
CLAIMS = {
    "unit_model_implemented": True,
    "ref_044_unit_passed": True,
    "official_structure_source_qualified": True,
    "opaque_bibliography_part_preserved": True,
    "ordered_multi_source_citation_fixtures": True,
    "selected_source_cache_projection_fixtures": True,
    "complete_bound_state_preserved": True,
    "request_and_build_drift_rejected": True,
    "bibliography_format_semantics_verified": False,
    "citation_parameter_semantics_verified": False,
    "ref_043_manage_implemented": False,
    "ref_045_generate_implemented": False,
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
    "p09_08_green": False,
    "p09_complete": False,
    "production_ready": False,
    "product_complete": False,
}


def digest(path: Path) -> str:
    value = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: Path, errors: list[str], code: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append(code)
        return None


def exact_source_locks(value: Any) -> bool:
    if not isinstance(value, list) or len(value) != len(SOURCE_SHA256):
        return False
    pairs = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            return False
        pairs.append((item["path"], item["sha256"]))
    return len({path for path, _ in pairs}) == len(pairs) and dict(pairs) == SOURCE_SHA256


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    contract = read_json(root / CONTRACT, errors, "contract_json")
    qualification = read_json(root / QUALIFICATION, errors, "qualification_json")
    if not isinstance(contract, dict) or not isinstance(qualification, dict):
        return result(errors or ["missing_artifact"], False)

    expected_contract_keys = {
        "schema_version", "task", "scope", "source_lock_canonicalization",
        "source_qualification", "migration", "policy", "report", "source_locks",
        "capability_features", "excluded_capabilities", "model", "official_model",
        "implementation_files", "state_binding", "failure_policy", "evidence_boundary",
        "gate_decision",
    }
    if set(contract) != expected_contract_keys:
        errors.append("contract_shape")
    scalar_expected = {
        "schema_version": "hwpx-agent.citation-contract/v1",
        "task": "P09-08",
        "scope": "complete_typed_component_model_for_ref_044_only",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "model": "hwpx-agent.citation/v1",
    }
    for key, expected in scalar_expected.items():
        if contract.get(key) != expected:
            errors.append(f"contract_{key}")
    if not exact_source_locks(contract.get("source_locks")):
        errors.append("source_locks")
    if contract.get("capability_features") != CAPABILITIES:
        errors.append("capabilities")
    if contract.get("excluded_capabilities") != EXCLUDED:
        errors.append("excluded_capabilities")
    expected_official_contract = {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "exact_native_structures": EXACT_STRUCTURES,
        "bibliography_format_binding": "unverified_opaque_part",
        "citation_semantic_binding": "unverified_field_parameters",
    }
    if contract.get("official_model") != expected_official_contract:
        errors.append("official_contract")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    if contract.get("state_binding") != STATE_BINDING:
        errors.append("state_binding")
    if contract.get("failure_policy") != FAILURE_POLICY:
        errors.append("failure_policy")
    expected_evidence = {
        **CLAIMS,
        "focused_rust_tests": "12/12 PASS",
        "private_contract_tests": "5/5 PASS",
        "direct_stage": "unit_passed",
    }
    if contract.get("evidence_boundary") != expected_evidence:
        errors.append("evidence_boundary")
    expected_gate = {
        "component": "pass",
        "official_structure": "partially_qualified",
        "bibliography_format_semantics": "unverified",
        "citation_parameter_semantics": "unverified",
        "ref_043_manage": "not_implemented_p11_owned",
        "ref_045_generate": "not_implemented_p11_owned",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p09_08": "typed_component_pass_native_format_direct_hwpx_and_target_not_run",
        "p09_08_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }
    if contract.get("gate_decision") != expected_gate:
        errors.append("gate_decision")

    for path, expected in {**SOURCE_SHA256, **IMPLEMENTATION_SHA256}.items():
        target = root / path
        try:
            actual = digest(target)
        except (OSError, UnicodeError):
            actual = None
        if actual != expected:
            errors.append(f"digest:{path}")

    expected_qualification_keys = {
        "schema_version", "task", "base_commit", "scope", "official_model",
        "source_sha256", "implementation_sha256", "tests", "claims",
    }
    if set(qualification) != expected_qualification_keys:
        errors.append("qualification_shape")
    expected_qualification_scalars = {
        "schema_version": "hwpx-agent.p09-citation-source-qualification/v1",
        "task": "P09-08",
        "base_commit": BASE_COMMIT,
        "scope": "ref_044_typed_citation_insert_component_with_complete_opaque_provider_state_and_unverified_native_parameters",
    }
    for key, expected in expected_qualification_scalars.items():
        if qualification.get(key) != expected:
            errors.append(f"qualification_{key}")
    expected_official_qualification = {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "canonicalization": "raw_file_sha256",
        "source_sha256": OFFICIAL_SOURCE_SHA256,
        "qualified_facts": QUALIFIED_FACTS,
    }
    if qualification.get("official_model") != expected_official_qualification:
        errors.append("qualification_official")
    if qualification.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_source_sha256")
    if qualification.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation_sha256")
    expected_tests = {
        "public_citation": "11/11 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "12/12 PASS",
        "private_contract": "5/5 PASS",
        "test_kind": "typed_component_existing_source_projection_preservation_and_pinned_source_metadata",
        "network_used": False,
        "licensed_application_used": False,
        "hwpx_written": False,
    }
    if qualification.get("tests") != expected_tests:
        errors.append("qualification_tests")
    if qualification.get("claims") != CLAIMS:
        errors.append("qualification_claims")

    markers = {
        MIGRATION: ["no accepted predecessor", "REF-043", "REF-045", "No migration may claim"],
        POLICY: ["only REF-044", "unverified_opaque_part", "unverified_field_parameters", "does not mean"],
        REPORT: ["11/11 PASS", "REF-043", "REF-045", "direct_hwpx"],
        "crates/domain-ir/src/citation.rs": [
            "hwpx-agent.citation/v1", "ref.citation_insert", "UnverifiedOpaquePart",
            "UnverifiedFieldParameters", "reject_duplicate_json_keys", "PlanTampered",
        ],
        "crates/domain-ir/tests/citation.rs": [
            "projection_binds_only_selected_records_in_citation_order",
            "stale_or_inconsistent_new_cache_is_rejected",
            "insertion_preserves_catalog_and_all_unrelated_state_and_debug_is_redacted",
        ],
    }
    for path, required in markers.items():
        try:
            text = (root / path).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append(f"artifact:{path}")
            continue
        if any(marker not in text for marker in required):
            errors.append(f"marker:{path}")

    return result(errors, not any(error.startswith("qualification_") for error in errors))


def result(errors: list[str], qualification_verified: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p09-citation-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": len(SOURCE_SHA256),
        "official_source_files": len(OFFICIAL_SOURCE_SHA256),
        "implementation_files": len(IMPLEMENTATION_SHA256),
        "source_qualification_verified": qualification_verified,
        "capabilities": len(CAPABILITIES),
        "bibliography_format_semantics": "unverified",
        "citation_parameter_semantics": "unverified",
        "direct_stage": "unit_passed",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "reference_update": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_08_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    outcome = validate()
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if outcome["state"] == "pass" else 1)
