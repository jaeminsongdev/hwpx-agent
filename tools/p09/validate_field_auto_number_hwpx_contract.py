#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any
import zipfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-field-auto-number-hwpx-v1.json"
QUALIFICATION = (
    "implementation/p09/evidence/"
    "p09-16-field-auto-number-hwpx-source-qualification.v1.json"
)
MIGRATION = "protocol/migrations/p09-field-auto-number-hwpx-v0-to-v1.md"
POLICY = "implementation/p09/P09-16_FIELD_AUTO_NUMBER_HWPX_POLICY.md"
REPORT = "implementation/p09/P09-16_FIELD_AUTO_NUMBER_HWPX_REPORT.md"
PROFILE = "hwpx-agent.field-auto-number-hwpx.hwpml-2011-digit/v1"
OFFICIAL_REPOSITORY = "https://github.com/hancom-io/hwpx-owpml-model.git"
OFFICIAL_COMMIT = "1453388472c703a4b299a0834f425cdac16644b9"
BASE_COMMIT = "1f8cd23da15d2e517e0e5640eae2bffe2c19af3f"
FIXTURE = (
    "fixtures/target-build/p05-08-current-2020-20260907-v12/"
    "p05-08-header-footer-output-attempt02.hwpx"
)
FIXTURE_SECTION = "Contents/section0.xml"
FIXTURE_AUTHORITY = "implementation/p05/P05-08_HANCOM2020_MASTER_PAGE_REPAIR.md"

SOURCE_SHA256 = {
    "docs/03_document_model/09_fields_controls_references.md": (
        "3068742808467f298d289c7401980c617981d748dfa73422bab8f7174ef10a20"
    ),
    "docs/04_feature_catalog/10_ref.md": (
        "34cfc9283d16b96bdb16d0ffec7a485f4b72548a49ec70fec2968b3c657743e4"
    ),
    "docs/04_feature_catalog/contracts/10_ref_contracts.md": (
        "7062034902932355ac8e6c38a4798dd314f39c44518b7e85c26fe71a7a72cc29"
    ),
    "docs/09_roadmap/P09_fields_forms_notes_references.md": (
        "0f4068c4dc5484cc348a145c892a2e1d2d3896d421b77c2fa23bb123956f4b55"
    ),
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/field_engine.rs": (
        "c9c77c27f741cb985de6da734a14fdf28917d89500d25a73a8cce2d7e2ad5da5"
    ),
    "crates/domain-ir/tests/field_engine.rs": (
        "15a3f49dab9aed32f087ec7aceb1c3d38617681f01162ce4415fe4b77338abb1"
    ),
    "crates/hwpx-package/src/field_auto_number_hwpx.rs": (
        "2927752005e5a1f2914089935dcec21fd61239f44e9861dabca8a505e5b05288"
    ),
    "crates/hwpx-package/tests/field_auto_number_hwpx.rs": (
        "3151a26ce5fc826c0a78d94da40de922903bee5c0344c05260a01d94ba85dc70"
    ),
}
PUBLIC_EXPORT = {
    "path": "crates/hwpx-package/src/lib.rs",
    "markers": ["mod field_auto_number_hwpx;", "pub use field_auto_number_hwpx::{"],
}
OFFICIAL_SHA256 = {
    "OWPML/Class/enumdef.h": (
        "1c86392c934ac85f7ddd85c710b76be7649403a8404bce146db52558a0b95457"
    ),
    "OWPML/Class/Para/AutoNumNewNumType.h": (
        "2dbef2bf7771a97501517ba8c0cf0bea2e0ec425048416854a283a119447533a"
    ),
    "OWPML/Class/Para/AutoNumNewNumType.cpp": (
        "58dd79b1e927b832868cf77c4ff089a3cab269c327a23e0a5aac0e21ecefbcf8"
    ),
    "OWPML/Class/Para/AutoNumFormatType.h": (
        "68ff9aee1b497be0f5be24b451bdd0810e93eb781b9c801651efc4dbbf43a155"
    ),
    "OWPML/Class/Para/AutoNumFormatType.cpp": (
        "86752d873fe366e3f72d8e9f50a71d8e29cfec712663fbaf4079d7a664c67a2c"
    ),
    "OWPML/Class/Para/ctrl.h": (
        "e043d1b8a570724179ba7f57f1521dbb65a2c393ba116dbb0d2c3bae2277cc7e"
    ),
    "OWPML/Class/Para/ctrl.cpp": (
        "a928569df0b890d8a58470a70a1501520bfb4d8af121df58eeb1fd8b9e0eed1d"
    ),
}
FIXTURE_SHA256 = "2fd7af9efb54132160b617b7b28399804596115fb2758bf193e5b0cd830838ac"
FIXTURE_SECTION_SHA256 = "2eb80a4b707984bc5dca382735d62f9898f1a8b56c36f6e9af1118be4b8aeccb"
FEATURE_CAPABILITIES = {
    "REF-006": "ref.field_page_number",
    "REF-008": "ref.field_object_number",
    "REF-009": "ref.field_update",
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/field_engine.rs": (
        'Self::PageNumber { .. } => "ref.field_page_number"',
        'Self::ObjectNumber { .. } => "ref.field_object_number"',
        'Self::UpdateResult { .. } => "ref.field_update"',
        "source_document_flow_sha256",
        "target_document_flow_sha256",
    ),
    "crates/domain-ir/tests/field_engine.rs": (
        "inserts_all_eight_field_kinds_with_distinct_capability_ids",
        "updates_cached_result_with_explicit_context_and_preserves_every_unrelated_binding",
        "request_plan_and_build_recheck_exact_state_and_document_flow",
    ),
    "crates/hwpx-package/src/field_auto_number_hwpx.rs": (
        "FIELD_AUTO_NUMBER_HWPX_PROFILE_ID",
        "source_wrapper_sha256",
        "field_transition",
        "verify_preservation",
        "sealed_plan_tampering_is_rejected",
        "<redacted>",
    ),
    "crates/hwpx-package/tests/field_auto_number_hwpx.rs": (
        "inserts_page_and_all_three_object_number_kinds_with_exact_projection",
        "updates_only_the_exact_numeric_attribute_and_reads_back_target_state",
        "rejects_noncanonical_or_extended_native_shapes",
        "source_flow_and_paragraph_map_drift_fail_before_output",
        "alternate_namespace_prefixes_are_preserved",
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


def bounded_file(root: Path, relative: str, maximum: int = 64 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ContractError(f"invalid_file:{relative}")
    return path


def load(root: Path, relative: str) -> Any:
    try:
        return json.loads(
            bounded_file(root, relative).read_text(encoding="utf-8"),
            object_pairs_hook=duplicate_guard,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"invalid_json:{relative}") from error


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def expected_boundary() -> dict[str, Any]:
    return {
        "direct_stage": "three_rows_static_section_integration_passed",
        "integration_rows": 3,
        "static_section_hwpx": True,
        "typed_target_projection_readback": True,
        "page_and_object_auto_number_insert": True,
        "exact_numeric_result_update": True,
        "outside_delta_byte_preserved": True,
        "complete_state_flow_map_and_projection_bound": True,
        "existing_fixture_page_digit_source_qualified": True,
        "object_number_target_qualified": False,
        "complete_package_hwpx": False,
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
            qualification_override
            if qualification_override is not None
            else load(root, QUALIFICATION)
        )
    except (OSError, ContractError):
        return result(["contract_or_qualification_json"], 0, 0, False)
    validate_contract(root, contract, errors)
    source_count = validate_locks(root, contract.get("source_locks"), SOURCE_SHA256, True, errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(root, qualification, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


def validate_contract(root: Path, contract: Any, errors: list[str]) -> None:
    keys = {
        "schema_version", "task", "source_lock_canonicalization", "source_qualification",
        "migration", "policy", "report", "source_locks", "implementation_files", "public_export", "profile",
        "feature_capabilities", "admitted_profile", "planning", "failure_policy",
        "evidence_boundary", "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != keys:
        errors.append("contract_shape")
        return
    if contract["schema_version"] != "hwpx-agent.p09-field-auto-number-hwpx-contract/v1":
        errors.append("schema_version")
    if contract["task"] != "P09-16" or contract["profile"] != PROFILE:
        errors.append("identity")
    if contract["source_lock_canonicalization"] != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    if (
        contract["source_qualification"],
        contract["migration"],
        contract["policy"],
        contract["report"],
    ) != (QUALIFICATION, MIGRATION, POLICY, REPORT):
        errors.append("document_paths")
    if contract["implementation_files"] != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    validate_public_export(root, contract.get("public_export"), errors)
    if contract["feature_capabilities"] != FEATURE_CAPABILITIES:
        errors.append("features")
    admitted = contract["admitted_profile"]
    if (
        not isinstance(admitted, dict)
        or admitted.get("native_types") != ["PAGE", "PICTURE", "TABLE", "EQUATION"]
        or admitted.get("format")
        != {
            "type": "DIGIT",
            "userChar": "",
            "prefixChar": "",
            "suffixChar": "",
            "supscript": "0",
        }
        or admitted.get("number") != "canonical_nonnegative_signed_32_bit_decimal"
    ):
        errors.append("native_profile")
    if not isinstance(contract["failure_policy"], list) or len(contract["failure_policy"]) != 8:
        errors.append("failure_policy")
    if contract["evidence_boundary"] != expected_boundary():
        errors.append("claim_promotion")
    if contract["gate_decision"] != {
        "component": "pass",
        "static_section_direct_hwpx": "pass",
        "ref_006_stage": "integration_passed",
        "ref_008_stage": "integration_passed",
        "ref_009_stage": "integration_passed",
        "current_target": "not_run",
        "release_green_rows": 0,
        "p09": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")


def validate_locks(
    root: Path,
    value: Any,
    expected: dict[str, str],
    canonical: bool,
    errors: list[str],
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
        if (
            not isinstance(relative, str)
            or relative in declared
            or not isinstance(digest, str)
            or not DIGEST.fullmatch(digest)
        ):
            errors.append("source_lock_identity")
            continue
        declared[relative] = digest
        try:
            path = bounded_file(root, relative)
            actual = canonical_digest(path) if canonical else raw_digest(path)
            if actual != digest:
                errors.append("source_lock_digest")
        except (OSError, ContractError):
            errors.append("source_lock_path")
    if declared != expected:
        errors.append("source_lock_set")
    return len(declared)


def validate_public_export(root: Path, value: Any, errors: list[str]) -> None:
    if value != PUBLIC_EXPORT:
        errors.append("public_export")
        return
    try:
        source = bounded_file(root, PUBLIC_EXPORT["path"]).read_text(encoding="utf-8")
        if any(marker not in source for marker in PUBLIC_EXPORT["markers"]):
            errors.append("public_export")
    except (OSError, UnicodeDecodeError, ContractError):
        errors.append("public_export")


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


def validate_qualification(root: Path, value: Any, errors: list[str]) -> bool:
    keys = {
        "schema_version", "task", "base_commit", "profile", "official_source",
        "existing_fixture", "implementation_sha256", "public_export", "tests", "claims",
    }
    if not isinstance(value, dict) or set(value) != keys:
        errors.append("qualification_shape")
        return False
    if (
        value["schema_version"]
        != "hwpx-agent.p09-field-auto-number-hwpx-source-qualification/v1"
        or value["task"] != "P09-16"
        or value["base_commit"] != BASE_COMMIT
        or value["profile"] != PROFILE
    ):
        errors.append("qualification_identity")
    official = value["official_source"]
    if (
        not isinstance(official, dict)
        or official.get("repository") != OFFICIAL_REPOSITORY
        or official.get("commit") != OFFICIAL_COMMIT
        or official.get("reviewed_sha256") != OFFICIAL_SHA256
    ):
        errors.append("qualification_official")
    else:
        base = (
            root
            / "fixtures/target-build/official-source-cache/hwpx-owpml-model-145338"
        )
        for relative, digest in OFFICIAL_SHA256.items():
            try:
                if raw_digest(bounded_file(base, relative)) != digest:
                    errors.append("qualification_official_digest")
            except (OSError, ContractError):
                errors.append("qualification_official_path")
    fixture = value["existing_fixture"]
    if fixture != {
        "package_path": FIXTURE,
        "package_sha256": FIXTURE_SHA256,
        "section_entry": FIXTURE_SECTION,
        "section_sha256": FIXTURE_SECTION_SHA256,
        "authority_report": FIXTURE_AUTHORITY,
        "qualification": "licensed_hangul_2020_save_reopen_PAGE_DIGIT_lexical_shape_only",
        "generated_by_this_adapter": False,
        "object_number_target_qualified": False,
    }:
        errors.append("qualification_fixture")
    else:
        try:
            fixture_path = bounded_file(root, FIXTURE)
            if raw_digest(fixture_path) != FIXTURE_SHA256:
                errors.append("qualification_fixture_digest")
            with zipfile.ZipFile(fixture_path) as archive:
                entries = [
                    entry
                    for entry in archive.infolist()
                    if entry.filename == FIXTURE_SECTION
                ]
                if (
                    len(entries) != 1
                    or entries[0].flag_bits & 0x1
                    or entries[0].file_size <= 0
                    or entries[0].file_size > 1024 * 1024
                ):
                    raise ContractError("invalid_fixture_section")
                section = archive.read(entries[0])
            fixture_text = section.decode("utf-8")
            if (
                hashlib.sha256(section).hexdigest() != FIXTURE_SECTION_SHA256
                or '<hp:autoNum num="1" numType="PAGE">' not in fixture_text
                or 'type="DIGIT" userChar="" prefixChar="" suffixChar="" supscript="0"'
                not in fixture_text
            ):
                errors.append("qualification_fixture_digest")
            authority = bounded_file(root, FIXTURE_AUTHORITY).read_text(encoding="utf-8")
            if FIXTURE_SHA256 not in authority or "licensed Hangul 2020" not in authority:
                errors.append("qualification_fixture_authority")
        except (OSError, UnicodeDecodeError, ContractError, zipfile.BadZipFile):
            errors.append("qualification_fixture_path")
    if value["implementation_sha256"] != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    if value["public_export"] != {**PUBLIC_EXPORT, "verified": True}:
        errors.append("qualification_public_export")
    if value["tests"] != {
        "field_engine_domain": "8/8 PASS",
        "field_auto_number_hwpx_public": "8/8 PASS",
        "field_auto_number_hwpx_private_tamper": "1/1 PASS",
        "focused_total": "17/17 PASS",
        "fixture_classes": ["boundary", "happy_path", "negative", "preservation"],
        "focused_clippy": "PASS",
    }:
        errors.append("qualification_tests")
    if value["claims"] != {
        "three_row_closed_digit_static_section_integration": True,
        "typed_target_projection_readback": True,
        "outside_delta_byte_preserved": True,
        "complete_state_flow_map_and_projection_bound": True,
        "existing_fixture_page_digit_source_qualified": True,
        "existing_fixture_generated_by_adapter": False,
        "object_number_target_qualified": False,
        "complete_package_hwpx": False,
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
        "green_rows": 0,
        "p09_complete": False,
        "production_ready": False,
        "product_complete": False,
    }:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "fail closed", "silently normalized"),
        POLICY: ("three_rows_closed_digit_static_section_integration_pass", "actual_hangul=false", "product_complete=false"),
        REPORT: ("8/8 PASS", "reference_update=false", "green_rows=0"),
    }
    for relative, markers in expected.items():
        try:
            text = bounded_file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ContractError):
            errors.append("document_path")


def result(
    errors: list[str], sources: int, implementation: int, qualification: bool
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p09-field-auto-number-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_locks": implementation,
        "source_qualification": qualification,
        "integration_rows": 3,
        "static_section_hwpx": True,
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "semantic_reopen": "not_run",
        "field_readback": "not_run",
        "reference_update": "not_run",
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
