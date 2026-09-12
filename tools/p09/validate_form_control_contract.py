#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-form-control-v1.json"
MIGRATION = "protocol/migrations/p09-form-control-v0-to-v1.md"
POLICY = "implementation/p09/P09-02_FORM_CONTROL_POLICY.md"
REPORT = "implementation/p09/P09-02_FORM_CONTROL_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-02-form-control-source-qualification.v1.json"
BASE_COMMIT = "093d7586e3bf5b83496caa31b225eef69aa447e8"
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
    "OWPML/Class/Para/AbstractFormObjectType.h": "949c9d96ece2cbd7a23779dd310471318d74fc91235f236d1a47247de138625b",
    "OWPML/Class/Para/AbstractFormObjectType.cpp": "f516fbeef26442f06d3e9e12d580a391c9323313a956509cfcaf88bf2c727e4a",
    "OWPML/Class/Para/AbstractButtonObjectType.h": "f72fb5348fcaa5647a111a09deda60c32a1df254e3e4f80e1cdf9f2647629505",
    "OWPML/Class/Para/AbstractButtonObjectType.cpp": "bbb88be28709bfd5874ae09a9882ce63d5e95ef54bc47dc0433883e87b46c18d",
    "OWPML/Class/Para/EditType.h": "37d3c6096ddc9b5ba914c33e4ea0db4ef510be8930fdcacbed7ddfc95076e65c",
    "OWPML/Class/Para/EditType.cpp": "62017660ff9bf4f666e4f95cfd9ac46d441b73392656ea2a1faae536693bf240",
    "OWPML/Class/Para/ComboBoxType.h": "8666e9153b9d302298479a5e9034ac9061cd752fe26907ea74ed9aea65c60f2a",
    "OWPML/Class/Para/ComboBoxType.cpp": "03461aab75f354a9741cbf8757659569711c1e102f2f3a20c84c84d184ed2f70",
    "OWPML/Class/Para/ListBoxType.h": "b75489e478cff3fc6cef09720fd0b8185eded4fd127f86b2bf93cc03e6e3c6a0",
    "OWPML/Class/Para/ListBoxType.cpp": "9d893daa4b287c5dd7d6a1183d7219a94263c17bc0077ee813b6863a56c3fd3b",
    "OWPML/Class/Para/ListItemType.h": "2f44a7a828b7e4fae342ed2ae423002bd0a7902e185e154bb97756d27829f816",
    "OWPML/Class/Para/ListItemType.cpp": "b409900db1d81b7942b1f6ca439a7f853eed902dbd780c7831635f203f3e991a",
    "OWPML/Class/Para/formCharPr.h": "46233e1a0abe9615f61b1cfbd1a5838e0e24cdef25a989c79f128ebdbe39f2b5",
    "OWPML/Class/Para/formCharPr.cpp": "a3f4054d614a77a3676508200de63ca07d9727d8e99eb5aa0928a22d777fc436",
    "OWPML/Class/Para/RunType.cpp": "dbaa0fe2b553dccc13381c856fd9c188185a16bf63685f575acf6bf2c9b88dee",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b13dcc56b5938d524084179b6c31e1c51bbc0fbd716146f47fcb89fa73cdb8d0",
    "crates/domain-ir/src/form_control.rs": "19e4c23c1318d477fd85a851d9f0e76dbe70012d9295b8202b162247105fabb5",
    "crates/domain-ir/tests/form_control.rs": "11af786a06c4792a30546f6e73e4123eb33b573b84eb69c2a2b9c05f3ed750b5",
}
CAPABILITIES = {
    "REF-011": "ref.form_text",
    "REF-012": "ref.form_checkbox",
    "REF-013": "ref.form_radio",
    "REF-014": "ref.form_combo",
    "REF-015": "ref.form_list",
    "REF-017": "ref.form_date",
    "REF-018": "ref.form_properties",
    "REF-019": "ref.form_tab_order",
}
EXCLUDED = {"REF-016": "ref.form_button", "REF-020": "ref.form_data_binding"}
EXACT_TAGS = ["edit", "checkBtn", "radioBtn", "comboBox", "listBox"]
STATE_BINDING = {
    "control_inventory": "ordered_complete_logical_native_anchor_binding_common_payload_shape_opaque_native_remainder_and_unknown_state",
    "document_state": "non_form_content_style_border_resource_reference_protection_and_opaque_document_digests",
    "input_state": "current_default_validation_and_all_kind_specific_properties",
    "active_content": "digest_only_command_reference_with_no_raw_command_or_execution",
    "request_and_build": "exact_source_state_and_document_flow_rechecked_and_plan_binding_sealed",
    "preservation": "only_named_insert_property_or_complete_tab_order_transition_may_change_state",
}
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "invalid_or_colliding_identity_anchor_name_native_id_or_tab_order_rejected",
    "incompatible_or_unverified_native_binding_rejected_without_fallback",
    "invalid_color_digest_text_date_item_selection_radio_or_validation_state_rejected",
    "incomplete_duplicate_noncontiguous_or_protected_tab_order_rejected",
    "protected_property_change_and_control_kind_change_rejected",
    "invalid_insertion_index_missing_target_and_noop_rejected",
    "source_state_and_document_flow_drift_rejected_at_request_and_build",
    "plan_binding_tamper_rejected",
    "unrelated_control_shape_native_and_document_state_change_rejected",
    "names_values_defaults_captions_selections_identities_anchors_commands_and_digests_redacted_from_debug",
    "no_raw_command_execution_partial_result_or_implicit_date_fallback",
]
CLAIMS = {
    "unit_model_implemented": True,
    "eight_capabilities_unit_passed": True,
    "official_model_source_qualified": True,
    "complete_bound_state_preserved": True,
    "input_and_protection_fixtures": True,
    "request_and_build_drift_rejected": True,
    "date_native_binding_verified": False,
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
    "p09_02_green": False,
    "p09_complete": False,
    "production_ready": False,
    "product_complete": False,
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": (
        "mod form_control;",
        "FormControlBuilder",
        "FormDocumentState",
    ),
    "crates/domain-ir/src/form_control.rs": (
        'FORM_CONTROL_SCHEMA_VERSION: &str = "hwpx-agent.form-control/v1"',
        "pub enum FormControlPayload",
        "pub enum FormControlOperation",
        "pub struct FormControlBuilder",
        "UnverifiedDateControl",
        "fn reject_duplicate_json_keys(",
        "<redacted>",
    ),
    "crates/domain-ir/tests/form_control.rs": (
        "inserts_six_controls_with_exact_capabilities_and_explicit_date_nonbinding",
        "complete_tab_order_is_atomic_contiguous_and_preserves_every_non_tab_property",
        "input_selection_radio_and_date_boundaries_fail_closed",
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
        "capability_features", "excluded_p11_capabilities", "model", "official_model",
        "implementation_files", "state_binding", "failure_policy", "evidence_boundary",
        "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_root:
        errors.append("contract_shape")
    if contract.get("schema_version") != "hwpx-agent.form-control-contract/v1":
        errors.append("schema_version")
    if contract.get("task") != "P09-02" or contract.get("scope") != (
        "complete_typed_component_models_for_ref_011_through_ref_019_excluding_p11_ref_016"
    ):
        errors.append("identity")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    if (
        contract.get("source_qualification"), contract.get("migration"),
        contract.get("policy"), contract.get("report"),
    ) != (QUALIFICATION, MIGRATION, POLICY, REPORT):
        errors.append("document_paths")
    if contract.get("capability_features") != CAPABILITIES:
        errors.append("capability_mapping")
    if contract.get("excluded_p11_capabilities") != EXCLUDED:
        errors.append("excluded_capabilities")
    if contract.get("model") != "hwpx-agent.form-control/v1":
        errors.append("model")
    if contract.get("official_model") != {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "exact_native_tags": EXACT_TAGS,
        "date_native_binding": "unverified",
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
        "focused_rust_tests": "9/9 PASS",
        "private_contract_tests": "5/5 PASS",
        "direct_stage": "unit_passed",
    }
    if contract.get("evidence_boundary") != expected_boundary:
        errors.append("evidence_boundary")
    if contract.get("gate_decision") != {
        "component": "pass",
        "official_model": "qualified",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p09_02": "typed_component_pass_direct_hwpx_and_target_evidence_not_run",
        "p09_02_green": False,
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
    if value.get("schema_version") != "hwpx-agent.p09-form-control-source-qualification/v1":
        errors.append("qualification_schema")
    if value.get("task") != "P09-02" or value.get("base_commit") != BASE_COMMIT:
        errors.append("qualification_identity")
    if value.get("scope") != "eight_ref_011_to_ref_019_non_p11_typed_form_component_models_only":
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
    if official.get("qualified_facts") != {
        "run_tags": EXACT_TAGS,
        "common_attributes": ["name", "foreColor", "backColor", "groupName", "tabStop", "editable", "tabOrder", "enabled", "borderTypeIDRef", "drawFrame", "printable", "command"],
        "form_char_properties": ["charPrIDRef", "followContext", "autoSz", "wordWrap"],
        "button_attributes": ["caption", "value", "radioGroupName", "triState", "backStyle"],
        "edit_attributes": ["multiLine", "passwordChar", "maxLength", "scrollBars", "tabKeyBehavior", "numOnly", "readOnly", "alignText"],
        "combo_attributes": ["listBoxRows", "listBoxWidth", "editEnable", "selectedValue", "listItem"],
        "list_attributes": ["itemHeight", "topIdx", "selectedValue", "listItem"],
        "date_native_tag": None,
    }:
        errors.append("qualification_official_facts")
    if value.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_sources")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    if value.get("tests") != {
        "public_form_control": "8/8 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "9/9 PASS",
        "private_contract": "5/5 PASS",
        "test_kind": "typed_component_state_and_pinned_source_metadata",
        "network_used": False,
        "licensed_application_used": False,
    }:
        errors.append("qualification_tests")
    if value.get("claims") != CLAIMS:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "fail closed", "unverified_date_control"),
        POLICY: ("eight_capabilities_unit_passed=true", "date_native_binding_verified=false", "Reasoning level: `max`"),
        REPORT: ("9/9 PASS", "field_readback=false", "product_complete=false"),
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
        "schema_version": "hwpx-agent.p09-form-control-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "official_source_files": len(OFFICIAL_SOURCE_SHA256),
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P09-02",
        "capabilities": 8,
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "date_native_binding": "unverified",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_02_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    result_value = validate()
    print(json.dumps(result_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if result_value["state"] == "pass" else 1)
