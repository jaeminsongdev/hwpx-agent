#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-mail-merge-v1.json"
MIGRATION = "protocol/migrations/p09-mail-merge-v0-to-v1.md"
POLICY = "implementation/p09/P09-09_MAIL_MERGE_POLICY.md"
REPORT = "implementation/p09/P09-09_MAIL_MERGE_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-09-mail-merge-source-qualification.v1.json"
BASE_COMMIT = "16bf4c9"
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
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b13dcc56b5938d524084179b6c31e1c51bbc0fbd716146f47fcb89fa73cdb8d0",
    "crates/domain-ir/src/mail_merge.rs": "54a55e4c32adf3905c76c20790b84117b8943442667e8bfd92cf67f717859581",
    "crates/domain-ir/tests/mail_merge.rs": "0d24c59a611cb73950a1b5bdca4a58932c2e3f85e3d87bec5885832b1a05df3d",
}
CAPABILITIES = {"REF-046": "ref.mailmerge_field"}
EXCLUDED = {"REF-047": "P11"}
EXACT_STRUCTURES = ["fieldBegin/MAILMERGE", "fieldEnd"]
UNVERIFIED_BINDINGS = [
    "mailmerge_parameter_keys",
    "provider_schema",
    "source_column_encoding",
    "placeholder_body",
    "preview_semantics",
    "record_iteration",
    "single_or_multiple_document_output",
    "label_layout_and_rendering",
]
STATE_BINDING = {
    "inventory": "ordered_complete_sections_data_sources_fields_and_non_mailmerge_native_ids",
    "source": "encrypted_external_artifact_provider_version_locale_schema_record_count_row_identity_access_pii_columns_opaque_and_lock",
    "column": "logical_identity_provider_key_display_name_type_nullability_sensitivity_semantic_format_opaque_and_lock",
    "field": "logical_and_native_identity_anchor_exact_source_column_current_projection_placeholder_generic_native_pair_opaque_and_lock",
    "projection": "source_identity_provider_version_locale_schema_and_selected_complete_column_only",
    "preserved_generation_state": "preview_batch_output_and_label_layout_inventory_digests_only",
    "document": "topology_non_mailmerge_content_fields_references_notes_toc_citations_objects_numbering_styles_relationships_resources_protection_and_opaque_state",
    "request_and_build": "exact_source_state_and_document_flow_rechecked_and_plan_binding_sealed",
    "privacy": "no_plaintext_rows_paths_credentials_or_provider_values",
}
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "plaintext_or_unencrypted_source_rejected",
    "missing_ambiguous_duplicate_or_over_ceiling_source_column_or_record_state_rejected",
    "duplicate_provider_column_key_rejected",
    "malformed_locale_digest_opaque_state_and_native_pair_rejected",
    "stale_or_inconsistent_new_field_projection_rejected",
    "native_control_field_and_name_collisions_rejected",
    "document_and_target_section_protection_rejected_without_partial_state",
    "source_state_and_document_flow_drift_rejected_at_request_plan_and_build",
    "sealed_plan_tamper_and_recomputed_target_mismatch_rejected",
    "complete_source_generation_inventory_and_unrelated_state_preserved",
    "identities_provider_keys_names_rows_native_parameters_paths_credentials_and_digests_redacted_from_debug",
    "no_raw_xml_action_path_partial_result_implicit_provider_mapping_generation_preview_or_label_claim",
]
CLAIMS = {
    "unit_model_implemented": True,
    "ref_046_unit_passed": True,
    "official_field_structure_qualified": True,
    "encrypted_source_metadata_bound": True,
    "typed_schema_and_record_count_bound": True,
    "row_identity_and_pii_policy_bound": True,
    "plaintext_rows_stored": False,
    "native_parameter_semantics_verified": False,
    "provider_mapping_verified": False,
    "preview_execution_implemented": False,
    "batch_generation_implemented": False,
    "label_layout_execution_implemented": False,
    "ref_047_generate_implemented": False,
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
    "p09_09_green": False,
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
    expected_scalars = {
        "schema_version": "hwpx-agent.mail-merge-contract/v1",
        "task": "P09-09",
        "scope": "complete_typed_component_model_for_ref_046_only",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "model": "hwpx-agent.mail-merge/v1",
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(f"contract_{key}")
    if not exact_source_locks(contract.get("source_locks")):
        errors.append("source_locks")
    if contract.get("capability_features") != CAPABILITIES:
        errors.append("capabilities")
    if contract.get("excluded_capabilities") != EXCLUDED:
        errors.append("excluded_capabilities")
    if contract.get("official_model") != {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "exact_native_structures": EXACT_STRUCTURES,
        "native_parameter_binding": "unverified_field_parameters",
        "provider_mapping": "unverified",
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
        "focused_rust_tests": "12/12 PASS",
        "private_contract_tests": "5/5 PASS",
        "direct_stage": "unit_passed",
    }:
        errors.append("evidence_boundary")
    if contract.get("gate_decision") != {
        "component": "pass",
        "official_structure": "field_type_only",
        "native_parameters": "unverified",
        "provider_mapping": "unverified",
        "ref_047_generate": "not_implemented_p11_owned",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p09_09": "typed_component_pass_native_provider_generation_direct_and_target_not_run",
        "p09_09_green": False,
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

    expected_qualification_keys = {
        "schema_version", "task", "base_commit", "scope", "official_model",
        "official_source_sha256", "qualified_facts", "source_sha256",
        "implementation_sha256", "tests", "claims",
    }
    if set(qualification) != expected_qualification_keys:
        errors.append("qualification_shape")
    expected_qualification_scalars = {
        "schema_version": "hwpx-agent.p09-mail-merge-source-qualification/v1",
        "task": "P09-09",
        "base_commit": BASE_COMMIT,
        "scope": "p09_owned_ref_046_typed_component_and_pinned_official_field_structure_only",
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
    if qualification.get("qualified_facts") != {
        "field_type": "MAILMERGE",
        "native_envelope": {"begin": "fieldBegin", "end": "fieldEnd"},
        "unverified_native_bindings": UNVERIFIED_BINDINGS,
    }:
        errors.append("qualification_facts")
    if qualification.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_source_sha256")
    if qualification.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation_sha256")
    if qualification.get("tests") != {
        "public_mail_merge": "11/11 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "12/12 PASS",
        "private_contract": "5/5 PASS",
        "network_used": False,
        "licensed_application_used": False,
        "hwpx_written": False,
        "plaintext_rows_used": False,
    }:
        errors.append("qualification_tests")
    if qualification.get("claims") != CLAIMS:
        errors.append("qualification_claims")

    markers = {
        MIGRATION: ["no accepted predecessor", "encrypted artifact", "REF-047", "No migration may claim"],
        POLICY: ["only REF-046", "unverified_field_parameters", "REF-047", "does not"],
        REPORT: ["11/11 PASS", "REF-047", "unverified", "direct_hwpx"],
        "crates/domain-ir/src/mail_merge.rs": [
            "hwpx-agent.mail-merge/v1", "ref.mailmerge_field", "UnverifiedFieldParameters",
            "encrypted_artifact", "reject_duplicate_json_keys", "PlanTampered",
        ],
        "crates/domain-ir/tests/mail_merge.rs": [
            "encrypted_source_schema_record_count_and_privacy_metadata_are_mandatory",
            "projection_binds_schema_and_selected_column_but_not_rows_or_unselected_columns",
            "request_plan_and_build_recheck_exact_state_and_document_flow",
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
        "schema_version": "hwpx-agent.p09-mail-merge-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": len(SOURCE_SHA256),
        "official_source_files": len(OFFICIAL_SOURCE_SHA256),
        "implementation_files": len(IMPLEMENTATION_SHA256),
        "source_qualification_verified": qualification_verified,
        "capabilities": len(CAPABILITIES),
        "native_parameter_semantics": "unverified",
        "provider_mapping": "unverified",
        "preview_execution": "not_run",
        "batch_generation": "not_run",
        "label_layout_execution": "not_run",
        "direct_stage": "unit_passed",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "reference_update": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_09_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    outcome = validate()
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if outcome["state"] == "pass" else 1)
