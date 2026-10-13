#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-toc-index-v1.json"
MIGRATION = "protocol/migrations/p09-toc-index-v0-to-v1.md"
POLICY = "implementation/p09/P09-07_TOC_INDEX_POLICY.md"
REPORT = "implementation/p09/P09-07_TOC_INDEX_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-07-toc-index-source-qualification.v1.json"
BASE_COMMIT = "3da904c"
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
    "OWPML/Class/Para/titleMark.h": "96e93397d4bc5d7378e495c2901a2304a93cb3338fc91bfd0ecf4843992f82c9",
    "OWPML/Class/Para/titleMark.cpp": "c365e996a0591f5827d043ba634c9f20761ba5a0a6f530211d61f32d16839e45",
    "OWPML/Class/Para/indexmark.h": "f30aee048c18371642b290eae8e2ba4bf93baa31db138e71c8d2e6e0b5613118",
    "OWPML/Class/Para/indexmark.cpp": "8d2c6aa819ffbf2b19fd4f6e3aadd773f49d868959f47bdf244b35d4a723fd89",
    "OWPML/Class/Para/firstKey.h": "fe5c598514352fd986f0fa66854e272dff0cb16734eb29e6670db6c70043b584",
    "OWPML/Class/Para/firstKey.cpp": "a17b5e06a5eeaac61e690d7410fb79a36abfa7389585eeed846bf6bfa8c4d0a7",
    "OWPML/Class/Para/secondKey.h": "40fa0ff955661b4aec5c69ca664547eaa47633bf3df17ecd25cc7975fdaa8f0b",
    "OWPML/Class/Para/secondKey.cpp": "a5c4bceb31943ebab36968d0f3addf23d5aebb50eaf4b06f6db03289e913a974",
    "OWPML/Class/Para/fieldBegin.h": "b216be07244a7a0c50f7dd2f40140d9ff202fefbb9b1b6092559dcd1aa08ad4f",
    "OWPML/Class/Para/fieldEnd.h": "88dd97103c537674dba0b3ac917b81ec5223fd3a518652330decb233b556791c",
    "OWPML/Class/Para/ctrl.h": "e043d1b8a570724179ba7f57f1521dbb65a2c393ba116dbb0d2c3bae2277cc7e",
    "OWPML/Class/Para/t.h": "e3ee45308a16a0b006ae57750a94d3019a4f220f3c6c20bd04a0deb0cd22c1bc",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/lib.rs": "b4726732a47175205a7e35f3aa8e018e66b2a0fbada144bebeac3f395540c058",
    "crates/domain-ir/src/toc_index.rs": "f7fe0a171b51cb508f7d0445614f20fc40b5036fc2ac1e92110af0b8166fe718",
    "crates/domain-ir/tests/toc_index.rs": "83ca0c65d6186eaa1048a9f87af6d420eac82a3e0dec54626649d59469ef2008",
}
CAPABILITIES = {
    "REF-037": "ref.toc_mark",
    "REF-038": "ref.toc_hide_mark",
    "REF-039": "ref.toc_create",
    "REF-041": "ref.index_mark",
    "REF-042": "ref.index_create",
}
EXCLUDED = {"REF-040": "P11", "REF-043_to_REF-045": "P09-08_or_P11"}
EXACT_STRUCTURES = [
    "titleMark/ignore", "indexmark/firstKey/secondKey",
    "fieldBegin/TABLEOFCONTENTS", "fieldEnd",
]
QUALIFIED_FACTS = {
    "toc_mark": {"tag": "titleMark", "attribute": "ignore", "default": False},
    "index_mark": {
        "tag": "indexmark", "children": ["firstKey", "secondKey"],
        "key_payload": "string_value",
    },
    "toc_generated_field": {
        "begin": "fieldBegin", "type": "TABLEOFCONTENTS", "end": "fieldEnd",
    },
    "unverified_native_bindings": [
        "toc_parameter_keys", "toc_source_selection", "level_and_style_encoding",
        "leader_and_numbering_encoding", "generated_body_layout", "index_collation",
        "index_duplicate_page_policy", "index_generated_range", "update_semantics",
    ],
}
CLAIMS = {
    "unit_model_implemented": True,
    "ref_037_unit_passed": True,
    "ref_038_unit_passed": True,
    "ref_039_unit_passed": True,
    "ref_041_unit_passed": True,
    "ref_042_unit_passed": True,
    "official_structure_source_qualified": True,
    "multilevel_toc_fixtures": True,
    "index_subentry_fixtures": True,
    "cache_projection_fixtures": True,
    "complete_bound_state_preserved": True,
    "request_and_build_drift_rejected": True,
    "native_generation_semantics_verified": False,
    "ref_040_update_implemented": False,
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
    "p09_07_green": False,
    "p09_complete": False,
    "production_ready": False,
    "product_complete": False,
}
MARKERS = {
    "crates/domain-ir/src/lib.rs": ["mod toc_index;", "pub use toc_index::{"],
    "crates/domain-ir/src/toc_index.rs": [
        'TOC_INDEX_SCHEMA_VERSION: &str = "hwpx-agent.toc-index/v1"',
        '"ref.toc_mark"', '"ref.toc_hide_mark"', '"ref.toc_create"',
        '"ref.index_mark"', '"ref.index_create"', "UnverifiedFieldParameters",
        "UnverifiedGeneratedRange", "reclassify_toc_blocks", "DocumentFlowDrift",
        "PlanTampered", "<redacted>",
    ],
    "crates/domain-ir/tests/toc_index.rs": [
        "all_p09_owned_capabilities_build_with_multilevel_state",
        "source_or_index_mark_changes_make_generated_cache_stale",
        "request_and_build_recheck_state_and_flow_drift",
        "unrelated_state_is_preserved_and_debug_is_redacted",
    ],
}


def duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


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
    return json.loads(file(root, relative).read_bytes(), object_pairs_hook=duplicate_rejecting_object)


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load(root, CONTRACT)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], False)

    expected_keys = {
        "schema_version", "task", "scope", "source_lock_canonicalization",
        "source_qualification", "migration", "policy", "report", "source_locks",
        "capability_features", "excluded_capabilities", "model", "official_model",
        "implementation_files", "state_binding", "failure_policy", "evidence_boundary",
        "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != expected_keys:
        errors.append("contract_shape")
    expected_identity = {
        "schema_version": "hwpx-agent.toc-index-contract/v1",
        "task": "P09-07",
        "scope": "complete_typed_component_model_for_ref_037_038_039_041_042",
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_qualification": QUALIFICATION,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "model": "hwpx-agent.toc-index/v1",
    }
    if any(contract.get(key) != value for key, value in expected_identity.items()):
        errors.append("contract_identity")
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
    expected_official = {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "exact_native_structures": EXACT_STRUCTURES,
        "toc_semantic_binding": "unverified_field_parameters",
        "index_semantic_binding": "unverified_generated_range",
    }
    if contract.get("official_model") != expected_official:
        errors.append("official_model")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    boundary = contract.get("evidence_boundary")
    expected_boundary = {
        **CLAIMS,
        "focused_rust_tests": "14/14 PASS",
        "private_contract_tests": "5/5 PASS",
        "direct_stage": "unit_passed",
    }
    if boundary != expected_boundary:
        errors.append("evidence_boundary")
    expected_gate = {
        "component": "pass",
        "official_structure": "partially_qualified",
        "native_generation_semantics": "unverified",
        "ref_040_update": "not_implemented_p11_owned",
        "direct_stage": "unit_passed",
        "actual_target": "not_run",
        "p09_07": "typed_component_pass_native_generation_direct_hwpx_and_target_not_run",
        "p09_07_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }
    if contract.get("gate_decision") != expected_gate:
        errors.append("gate_decision")
    failure_policy = contract.get("failure_policy")
    if not isinstance(failure_policy, list) or len(failure_policy) != 15 or len(set(failure_policy)) != 15:
        errors.append("failure_policy")
    state_binding = contract.get("state_binding")
    if not isinstance(state_binding, dict) or set(state_binding) != {
        "inventory", "toc_source", "toc_mark", "index_mark", "toc_settings",
        "index_settings", "cache", "occupied_native_ids", "document", "request_and_build",
        "preservation",
    }:
        errors.append("state_binding")

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
    return result(errors, qualification_verified)


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "task", "base_commit", "scope", "official_model", "source_sha256",
        "implementation_sha256", "tests", "claims",
    }:
        errors.append("qualification_shape")
    if value.get("schema_version") != "hwpx-agent.p09-toc-index-source-qualification/v1" \
            or value.get("task") != "P09-07" or value.get("base_commit") != BASE_COMMIT:
        errors.append("qualification_identity")
    official = value.get("official_model")
    expected_official = {
        "repository": OFFICIAL_REPOSITORY,
        "commit": OFFICIAL_COMMIT,
        "canonicalization": "utf8_text_crlf_to_lf_sha256",
        "source_sha256": OFFICIAL_SOURCE_SHA256,
        "qualified_facts": QUALIFIED_FACTS,
    }
    if official != expected_official:
        errors.append("qualification_official_sources")
    if value.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_source_locks")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation_locks")
    tests = value.get("tests")
    expected_tests = {
        "public_toc_index": "13/13 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "14/14 PASS",
        "private_contract": "5/5 PASS",
        "test_kind": "typed_component_multilevel_toc_index_projection_preservation_and_pinned_source_metadata",
        "network_used": False,
        "licensed_application_used": False,
        "hwpx_written": False,
    }
    if tests != expected_tests:
        errors.append("qualification_tests")
    if value.get("claims") != CLAIMS:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_text_artifacts(root: Path, errors: list[str]) -> None:
    markers = {
        MIGRATION: ["hwpx-agent.toc-index/v1", "unverified", "REF-040"],
        POLICY: ["REF-037", "REF-042", "UnverifiedFieldParameters", "product_complete=false"],
        REPORT: ["13/13 PASS", "REF-040", "direct_hwpx"],
    }
    for path, required in markers.items():
        try:
            text = file(root, path).read_text(encoding="utf-8")
            if any(marker not in text for marker in required):
                errors.append("text_artifact_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("text_artifact_marker")


def result(errors: list[str], qualification_verified: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p09-toc-index-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": len(SOURCE_SHA256),
        "official_source_files": len(OFFICIAL_SOURCE_SHA256),
        "implementation_files": len(IMPLEMENTATION_SHA256),
        "source_qualification_verified": qualification_verified,
        "capabilities": len(CAPABILITIES),
        "native_generation_semantics": "unverified",
        "ref_040_update": "not_implemented_p11_owned",
        "direct_stage": "unit_passed",
        "direct_hwpx": "not_run",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "field_readback": "not_run",
        "reference_update": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_07_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    outcome = validate()
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if outcome["state"] == "pass" else 1)
