#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-reference-auxiliary-v1.json"
MIGRATION = "protocol/migrations/p09-reference-auxiliary-v0-to-v1.md"
POLICY = "implementation/p09/P09-10_REFERENCE_AUXILIARY_POLICY.md"
REPORT = "implementation/p09/P09-10_REFERENCE_AUXILIARY_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-10-reference-auxiliary-source-qualification.v1.json"
BASE_COMMIT = "3fac12b"
OFFICIAL_REPOSITORY = "https://github.com/hancom-io/hwpx-owpml-model.git"
OFFICIAL_COMMIT = "1453388472c703a4b299a0834f425cdac16644b9"

SOURCE_SHA256 = {
    "docs/04_feature_catalog/10_ref.md": "34cfc9283d16b96bdb16d0ffec7a485f4b72548a49ec70fec2968b3c657743e4",
    "docs/04_feature_catalog/contracts/10_ref_contracts.md": "7062034902932355ac8e6c38a4798dd314f39c44518b7e85c26fe71a7a72cc29",
    "docs/09_roadmap/P09_fields_forms_notes_references.md": "0f4068c4dc5484cc348a145c892a2e1d2d3896d421b77c2fa23bb123956f4b55",
    "docs/03_document_model/09_fields_controls_references.md": "3068742808467f298d289c7401980c617981d748dfa73422bab8f7174ef10a20",
}
OFFICIAL_SOURCE_SHA256 = {
    "OWPML/Class/enumdef.h": "3420084332110524192a098b8b16e97bb4e00eb116c178f39afe2f002a74c481",
    "OWPML/Class/Para/caption.h": "2b640a044c2298afd0915a5449de468d049ca6c0fa446c9583a889c0eb76107f",
    "OWPML/Class/Para/caption.cpp": "e58b86035f98ddb636feaf682f79466855b39099af583f07251a36c3452c9487",
    "OWPML/Class/Para/fieldBegin.h": "c190fa337476a82f8ef2673c6f7c966baa63764af317d7ed33fd8418e779263e",
    "OWPML/Class/Para/fieldBegin.cpp": "953968d5759b0134cbbe30174bfbbf8558d46d8c5f26513293c978fd5aef63b2",
    "OWPML/Class/Para/fieldEnd.h": "26cdab03328535db43f0efe1ee215906ad6852fbf93b18998a677ea4d36c590d",
    "OWPML/Class/Para/fieldEnd.cpp": "40d2398164c8d59ae84b7538c98c4cc8e501d7b1ea909318ae63006144c7e3fe",
    "OWPML/Class/Head/docoptionLinkInfo.h": "2192376c447c5858a5a0e6c787b2a5919212e40be5cb87d6340a1dae1460c088",
    "OWPML/Class/Head/docoptionLinkInfo.cpp": "6a58e78202833840c9ad279f849f73e9d047d9d7f02d7c0dd48a594917406335",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b4726732a47175205a7e35f3aa8e018e66b2a0fbada144bebeac3f395540c058",
    "crates/domain-ir/src/reference_auxiliary.rs": "04e3c23493732cf35e4cfdff83314d55b725c1e419b524a1ef00ca9c60f66777",
    "crates/domain-ir/tests/reference_auxiliary.rs": "af73840e97cd0fd1d71b80588a7f9e3771072e8723aadc588c1c173b147b2396",
}
CAPABILITIES = {
    "REF-048": "ref.caption_sequence",
    "REF-049": "ref.date_time_format",
    "REF-050": "ref.file_name_literal",
    "REF-051": "ref.correction_mark",
    "REF-052": "ref.data_link",
    "REF-053": "ref.reference_validate",
}
UNVERIFIED_BINDINGS = [
    "caption_sublist_numbering",
    "date_and_doc_date_parameter_keys",
    "path_literal_freeze_semantics",
    "proofreading_parameter_and_metadata_keys",
    "data_link_access_update_semantics",
    "broken_reference_validator_or_repair_action",
]
QUALIFIED_FACTS = {
    "caption_envelope_attributes": ["side", "fullSz", "width", "gap", "lastWidth", "subList"],
    "date_field_types": ["DATE", "DOC_DATE"],
    "path_field_type": "PATH",
    "proofreading_field_type_count": 19,
    "document_link_attributes": ["path", "pageInherit", "footnoteInherit"],
    "unverified_native_bindings": UNVERIFIED_BINDINGS,
}
STATE_BINDING = {
    "caption": "complete_targets_sequences_bindings_document_order_restart_numbers_cache_native_envelope_opaque_and_locks",
    "date_time": "existing_date_or_doc_date_identity_anchor_format_locale_timezone_calendar_cache_generic_pair_opaque_and_lock",
    "file_name_literal": "leaf_text_exact_utf8_digest_source_revision_anchor_styles_opaque_and_lock_without_path",
    "correction_mark": "all_19_official_kinds_anchor_logical_native_pair_author_time_content_parameters_opaque_and_lock",
    "data_link": "encrypted_artifact_envelope_allowlist_location_revision_relationship_all_inheritance_combinations_availability_opaque_and_lock",
    "validation": "complete_targets_edges_typed_issues_cycles_cache_and_external_data_availability",
    "document": "sections_native_ids_all_p09_object_numbering_style_relationship_resource_protection_and_opaque_inventories",
    "request_and_build": "exact_source_state_and_document_flow_rechecked_and_plan_binding_sealed",
}
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "caption_kind_target_order_number_projection_native_envelope_and_lock_drift_rejected",
    "date_field_identity_pair_format_locale_timezone_cache_and_lock_drift_rejected",
    "filename_paths_control_characters_digest_mismatch_duplicate_identity_and_locked_section_rejected",
    "correction_unknown_kind_native_collision_pair_timestamp_digest_and_locked_section_rejected",
    "data_link_unencrypted_malformed_digest_noop_and_locked_replacement_rejected",
    "reference_graph_duplicate_identity_anchor_or_digest_rejected",
    "validation_report_digest_drift_rejected_without_mutation",
    "source_state_and_document_flow_drift_rejected_at_request_plan_and_build",
    "sealed_plan_tamper_and_recomputed_target_mismatch_rejected",
    "complete_unrelated_state_preserved",
    "identities_text_filenames_locations_parameters_and_digests_redacted_from_debug",
    "no_raw_xml_action_path_partial_result_update_repair_lowerer_or_target_claim",
]
CLAIMS = {
    "unit_model_implemented": True,
    "ref_048_unit_passed": True,
    "ref_049_unit_passed": True,
    "ref_050_unit_passed": True,
    "ref_051_unit_passed": True,
    "ref_052_unit_passed": True,
    "ref_053_unit_passed": True,
    "official_envelopes_and_enums_qualified": True,
    "native_parameter_semantics_verified": False,
    "date_evaluation_implemented": False,
    "dynamic_path_field_implemented": False,
    "data_link_access_implemented": False,
    "reference_repair_implemented": False,
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
    "p09_10_green": False,
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
        return result(errors, False)

    if set(contract) != {
        "schema_version", "task", "scope", "source_lock_canonicalization",
        "source_qualification", "migration", "policy", "report", "source_locks",
        "capability_features", "model", "official_model", "implementation_files",
        "state_binding", "failure_policy", "evidence_boundary", "gate_decision",
    }:
        errors.append("contract_shape")
    expected_scalars = {
        "schema_version": "hwpx-agent.reference-auxiliary-contract/v1",
        "task": "P09-10",
        "scope": "complete_typed_component_models_for_ref_048_through_ref_053",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "model": "hwpx-agent.reference-auxiliary/v1",
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(f"contract_{key}")
    if not exact_source_locks(contract.get("source_locks")):
        errors.append("source_locks")
    if contract.get("capability_features") != CAPABILITIES:
        errors.append("capabilities")
    if contract.get("official_model") != {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "qualified": "caption_field_and_link_envelopes_plus_closed_field_enums",
        "native_parameter_binding": "unverified",
    }:
        errors.append("official_contract")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    if contract.get("state_binding") != STATE_BINDING:
        errors.append("state_binding")
    if contract.get("failure_policy") != FAILURE_POLICY:
        errors.append("failure_policy")
    if contract.get("evidence_boundary") != {
        **CLAIMS,
        "focused_rust_tests": "15/15 PASS",
        "private_contract_tests": "5/5 PASS",
        "direct_stage": "unit_passed",
    }:
        errors.append("evidence_boundary")
    if contract.get("gate_decision") != {
        "component": "pass",
        "official_structure": "envelopes_and_enums_only",
        "native_parameters": "unverified",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p09_10": "six_typed_components_pass_native_direct_and_target_not_run",
        "p09_10_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")

    for path, expected in {**SOURCE_SHA256, **IMPLEMENTATION_SHA256}.items():
        try:
            actual = digest(root / path)
        except (OSError, UnicodeError):
            actual = None
        if actual != expected:
            errors.append(f"digest:{path}")

    if set(qualification) != {
        "schema_version", "task", "base_commit", "scope", "source_lock_canonicalization",
        "official_model", "official_source_sha256", "qualified_facts", "source_sha256",
        "implementation_sha256", "tests", "claims",
    }:
        errors.append("qualification_shape")
    expected_qualification_scalars = {
        "schema_version": "hwpx-agent.p09-reference-auxiliary-source-qualification/v1",
        "task": "P09-10",
        "base_commit": BASE_COMMIT,
        "scope": "p09_owned_ref_048_through_ref_053_typed_components_and_pinned_official_envelopes_only",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
    }
    for key, expected in expected_qualification_scalars.items():
        if qualification.get(key) != expected:
            errors.append(f"qualification_{key}")
    if qualification.get("official_model") != {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "checkout_clean": True,
        "network_used": False,
    }:
        errors.append("qualification_official")
    if qualification.get("official_source_sha256") != OFFICIAL_SOURCE_SHA256:
        errors.append("qualification_official_sha256")
    if qualification.get("qualified_facts") != QUALIFIED_FACTS:
        errors.append("qualification_facts")
    if qualification.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_source_sha256")
    if qualification.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation_sha256")
    if qualification.get("tests") != {
        "public_reference_auxiliary": "14/14 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "15/15 PASS",
        "private_contract": "5/5 PASS",
        "network_used": False,
        "licensed_application_used": False,
        "hwpx_written": False,
        "raw_external_path_used": False,
    }:
        errors.append("qualification_tests")
    if qualification.get("claims") != CLAIMS:
        errors.append("qualification_claims")

    markers = {
        MIGRATION: ["no accepted predecessor", "19 closed", "raw linked-document paths", "does not prove"],
        POLICY: ["REF-048", "REF-053", "19 official", "remain unverified"],
        REPORT: ["14/14 PASS", "six rows unit-only", "direct_hwpx", "false/not_run"],
        "crates/domain-ir/src/reference_auxiliary.rs": [
            "hwpx-agent.reference-auxiliary/v1", "ref.caption_sequence", "ref.date_time_format",
            "ref.file_name_literal", "ref.correction_mark", "ref.data_link",
            "ref.reference_validate", "UnverifiedSubListNumbering", "reject_duplicate_json_keys",
        ],
        "crates/domain-ir/tests/reference_auxiliary.rs": [
            "caption_sequence_restarts_per_section_and_preserves_every_other_inventory",
            "correction_mark_covers_all_official_kinds_and_native_pairs",
            "reference_validator_reports_missing_inactive_kind_stale_cycle_and_data_link",
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
        "schema_version": "hwpx-agent.p09-reference-auxiliary-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": len(SOURCE_SHA256),
        "official_source_files": len(OFFICIAL_SOURCE_SHA256),
        "implementation_files": len(IMPLEMENTATION_SHA256),
        "source_qualification_verified": qualification_verified,
        "capabilities": len(CAPABILITIES),
        "native_parameter_semantics": "unverified",
        "direct_stage": "unit_passed",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "reference_update": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_10_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    outcome = validate()
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if outcome["state"] == "pass" else 1)
