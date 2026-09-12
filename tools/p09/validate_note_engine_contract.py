#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-note-engine-v1.json"
MIGRATION = "protocol/migrations/p09-note-engine-v0-to-v1.md"
POLICY = "implementation/p09/P09-03_NOTE_ENGINE_POLICY.md"
REPORT = "implementation/p09/P09-03_NOTE_ENGINE_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-03-note-engine-source-qualification.v1.json"
BASE_COMMIT = "bb42f464177409f645abd14fd8ba3dde71a2e2f9"
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
    "OWPML/Class/Para/NoteType.h": "3ff35f5926ecdbd08d144dc52165d31ecc25e9d99929dae6d3da1ae3fcdd03b8",
    "OWPML/Class/Para/NoteType.cpp": "df20a88cafb301c4b7b8ece5fbcb20a9cb69cfea6ffcb48a37751d0b16336b15",
    "OWPML/Class/Para/NoteShapeType.h": "c9ebea06c20c91d722d9c783876d4034dc58212084407a42972cf53182f71f27",
    "OWPML/Class/Para/NoteShapeType.cpp": "c8a18df0a7cd52b11547d6907f95c140d678e2c3f382f6529bff0b80f1718b2c",
    "OWPML/Class/Para/FootNoteShapeType.h": "a5efbfaa9db0dd6a1a233ce97f691cbc90202bcd5733c283d95713fcfa91df7f",
    "OWPML/Class/Para/FootNoteShapeType.cpp": "7c8be1736acc678d3f999e35c5c8c270d2d88e87f4223df63961bf78f701f35d",
    "OWPML/Class/Para/EndNoteShapeType.h": "2637b8ec023743601fd0b53e4234dec0ff95b039475500f6fb041e7152b21c61",
    "OWPML/Class/Para/EndNoteShapeType.cpp": "7836b3fd07695c59641ad39f88c955b302b576bb2aaf4ca638d26338ad99d75e",
    "OWPML/Class/Para/AutoNumFormatType.h": "68ff9aee1b497be0f5be24b451bdd0810e93eb781b9c801651efc4dbbf43a155",
    "OWPML/Class/Para/AutoNumFormatType.cpp": "86752d873fe366e3f72d8e9f50a71d8e29cfec712663fbaf4079d7a664c67a2c",
    "OWPML/Class/Para/numbering.h": "f2d4e6c81666d13fe9fbb4587ca1760ee1a33a4d78ab74f0d7ef31192103a6ea",
    "OWPML/Class/Para/numbering.cpp": "8dfaddd4b264bbd227e8508741f242e10888ee54cbcee1605cf979b505405c8c",
    "OWPML/Class/Para/placement.h": "503ecd5d3a618eac50f7848ea57e1373a5cf6efd6f6be3bd1cab32377270af45",
    "OWPML/Class/Para/placement.cpp": "7f83f80ffde5a7b14261f486b922837d73ea4fb16b07ddcb4eac54baf07cae43",
    "OWPML/Class/Para/noteLine.h": "f87c1c9887e6960ee9b7c643696f0bb96509fa607c83a2d5a2b0e467dc1f3858",
    "OWPML/Class/Para/noteLine.cpp": "aac39f8f49ab5437de10cf8d7525b72d257af8340eb9d66e86f3c3df19487046",
    "OWPML/Class/Para/noteSpacing.h": "d32b35e476b52e7876b9386856c9baf931fb8035e77e738b6d81a2a0cd96d267",
    "OWPML/Class/Para/noteSpacing.cpp": "0f55b926460bca90c3e76035291d314e7672cdf65c8a057b1533b9139b9ee598",
    "OWPML/Class/Para/ctrl.h": "e043d1b8a570724179ba7f57f1521dbb65a2c393ba116dbb0d2c3bae2277cc7e",
    "OWPML/Class/Para/ctrl.cpp": "a928569df0b890d8a58470a70a1501520bfb4d8af121df58eeb1fd8b9e0eed1d",
    "OWPML/Class/Para/SectionDefinitionType.h": "5e0862cbaf02ff2cf12b9dc3c86828e0856a4210d4d9c319a0c2877138f62acc",
    "OWPML/Class/Para/SectionDefinitionType.cpp": "4cfcca9bee299c3fbfe2cf2e2e3ec09027a4fa8c404cbb68f141cb584058c7e4",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "8f6953c06520772c50032e135738e15582e11d1aa8a28977ec06d10ca2084f23",
    "crates/domain-ir/src/note_engine.rs": "d1a3fc49f848349cab43b10ed408c315d2befe1ddbb6844e2c24d6637f00dc85",
    "crates/domain-ir/tests/note_engine.rs": "a5a0ec5057e63688d8775e9bbfee1dd81ce0041267aefef8b05bb3e69d9bccc4",
}
CAPABILITIES = {
    "REF-021": "ref.footnote_insert",
    "REF-022": "ref.endnote_insert",
    "REF-023": "ref.note_style",
    "REF-024": "ref.note_convert",
    "REF-025": "ref.note_export",
}
EXACT_TAGS = ["footNote", "endNote"]
NUMBER_FORMATS = [
    "DIGIT", "CIRCLED_DIGIT", "ROMAN_CAPITAL", "ROMAN_SMALL", "LATIN_CAPITAL",
    "LATIN_SMALL", "CIRCLED_LATIN_CAPITAL", "CIRCLED_LATIN_SMALL", "HANGUL_SYLLABLE",
    "CIRCLED_HANGUL_SYLLABLE", "HANGUL_JAMO", "CIRCLED_HANGUL_JAMO",
    "HANGUL_PHONETIC", "IDEOGRAPH", "CIRCLED_IDEOGRAPH", "DECAGON_CIRCLE",
    "DECAGON_CIRCLE_HANJA", "SYMBOL", "USER_CHAR", "SYMBOL2", "IMAGE", "2DIGIT",
]
LINE_TYPES = [
    "NONE", "SOLID", "DOT", "DASH", "DASH_DOT", "DASH_DOT_DOT", "LONG_DASH",
    "CIRCLE", "DOUBLE_SLIM", "SLIM_THICK", "THICK_SLIM", "SLIM_THICK_SLIM", "WAVE",
    "DOUBLEWAVE", "THICK3D", "THICKREV3D", "3D", "REV3D",
]
LINE_WIDTHS = [
    "0.1", "0.12", "0.15", "0.2", "0.25", "0.3", "0.4", "0.5", "0.6", "0.7",
    "1.0", "1.5", "2.0", "3.0", "4.0", "5.0",
]
QUALIFIED_FACTS = {
    "run_tags": EXACT_TAGS,
    "note_attributes": ["flag", "number", "userChar", "prefixChar", "suffixChar", "instId", "subList"],
    "section_style_tags": ["footNotePr", "endNotePr"],
    "shared_style_children": ["autoNumFormat", "noteLine", "noteSpacing"],
    "number_formats": NUMBER_FORMATS,
    "line_types": LINE_TYPES,
    "line_widths_mm": LINE_WIDTHS,
    "footnote_numbering": ["CONTINUOUS", "ON_SECTION", "ON_PAGE"],
    "endnote_numbering": ["CONTINUOUS", "ON_SECTION"],
    "footnote_placement": ["EACH_COLUMN", "MERGED_COLUMN", "RIGHT_MOST_COLUMN"],
    "endnote_placement": ["END_OF_DOCUMENT", "END_OF_SECTION"],
    "native_note_export_element": None,
}
STATE_BINDING = {
    "note_inventory": "ordered_complete_logical_native_anchor_kind_tag_marker_body_style_opaque_and_lock_state",
    "section_state": "ordered_complete_footnote_and_endnote_style_opaque_and_lock_state",
    "document_state": "non_note_content_style_numbering_reference_resource_protection_and_opaque_document_digests",
    "export": "read_only_document_ordered_identity_kind_and_digest_manifest_without_raw_content_or_file_write",
    "request_and_build": "exact_source_state_and_document_flow_rechecked_and_plan_plus_export_binding_sealed",
    "preservation": "only_named_insert_style_or_conversion_transition_may_change_state",
}
FAILURE_POLICY = [
    "zero_inconsistent_or_over_ceiling_limits_rejected",
    "duplicate_unknown_missing_malformed_or_oversized_json_rejected",
    "empty_sections_or_invalid_colliding_identity_anchor_native_id_or_tag_rejected",
    "invalid_marker_character_digest_body_style_or_opaque_state_rejected",
    "family_incompatible_numbering_placement_or_note_style_rejected_without_coercion",
    "invalid_insertion_index_missing_target_and_noop_rejected",
    "document_section_note_and_style_protection_rejected",
    "empty_duplicate_missing_or_over_ceiling_export_selection_rejected",
    "source_state_and_document_flow_drift_rejected_at_request_and_build",
    "plan_and_export_manifest_binding_tamper_rejected",
    "unrelated_note_section_and_document_state_change_rejected",
    "identities_anchors_markers_bodies_styles_selections_and_digests_redacted_from_debug",
    "no_raw_xml_body_export_file_write_partial_result_or_implicit_family_fallback",
]
CLAIMS = {
    "unit_model_implemented": True,
    "five_capabilities_unit_passed": True,
    "official_model_source_qualified": True,
    "complete_bound_state_preserved": True,
    "note_style_and_protection_fixtures": True,
    "request_and_build_drift_rejected": True,
    "digest_manifest_export": True,
    "actual_note_export": False,
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
    "p09_03_green": False,
    "p09_complete": False,
    "production_ready": False,
    "product_complete": False,
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ("mod note_engine;", "NoteBuilder", "NoteDocumentState"),
    "crates/domain-ir/src/note_engine.rs": (
        'NOTE_ENGINE_SCHEMA_VERSION: &str = "hwpx-agent.note-engine/v1"',
        "pub enum NoteKind", "pub enum NoteOperation", "pub struct NoteBuilder",
        "DigestManifestV1", "fn reject_duplicate_json_keys(", "<redacted>",
    ),
    "crates/domain-ir/tests/note_engine.rs": (
        "inserts_footnote_and_endnote_with_exact_capability_and_native_tag",
        "digest_manifest_export_is_deterministic_document_ordered_and_state_preserving",
        "protection_noop_and_export_selection_fail_without_partial_state",
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
        "capability_features", "model", "official_model", "implementation_files",
        "state_binding", "failure_policy", "evidence_boundary", "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_root:
        errors.append("contract_shape")
    if contract.get("schema_version") != "hwpx-agent.note-engine-contract/v1":
        errors.append("schema_version")
    if contract.get("task") != "P09-03" or contract.get("scope") != (
        "complete_typed_component_models_for_ref_021_through_ref_025"
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
    if contract.get("model") != "hwpx-agent.note-engine/v1":
        errors.append("model")
    if contract.get("official_model") != {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "exact_native_tags": EXACT_TAGS,
        "number_format_count": 22,
        "line_type_count": 18,
        "line_width_count": 16,
        "note_export_binding": "digest_manifest_only",
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
        "note_export": "digest_manifest_only",
        "actual_target": "not_run",
        "p09_03": "typed_component_pass_direct_hwpx_real_export_and_target_evidence_not_run",
        "p09_03_green": False,
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
    if value.get("schema_version") != "hwpx-agent.p09-note-engine-source-qualification/v1":
        errors.append("qualification_schema")
    if value.get("task") != "P09-03" or value.get("base_commit") != BASE_COMMIT:
        errors.append("qualification_identity")
    if value.get("scope") != "five_ref_021_to_ref_025_typed_note_component_and_digest_manifest_only":
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
        "public_note_engine": "8/8 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "9/9 PASS",
        "private_contract": "5/5 PASS",
        "test_kind": "typed_component_state_and_pinned_source_metadata",
        "network_used": False,
        "licensed_application_used": False,
        "external_note_file_written": False,
    }:
        errors.append("qualification_tests")
    if value.get("claims") != CLAIMS:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "fail closed", "digest-manifest projection"),
        POLICY: ("five_capabilities_unit_passed=true", "actual_note_export=false", "Reasoning level: `max`"),
        REPORT: ("9/9 PASS", "digest manifest only", "product_complete=false"),
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
        "schema_version": "hwpx-agent.p09-note-engine-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "official_source_files": len(OFFICIAL_SOURCE_SHA256),
        "implementation_files": implementation,
        "source_qualification_verified": qualification,
        "task": "P09-03",
        "capabilities": 5,
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "note_export": "digest_manifest_only" if not unique else "not_proven",
        "actual_note_export": "not_run",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_03_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    result_value = validate()
    print(json.dumps(result_value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if result_value["state"] == "pass" else 1)
