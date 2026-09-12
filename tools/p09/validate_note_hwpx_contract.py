#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-note-hwpx-v1.json"
QUALIFICATION = "implementation/p09/evidence/p09-15-note-hwpx-source-qualification.v1.json"
MIGRATION = "protocol/migrations/p09-note-hwpx-v0-to-v1.md"
POLICY = "implementation/p09/P09-15_NOTE_HWPX_POLICY.md"
REPORT = "implementation/p09/P09-15_NOTE_HWPX_REPORT.md"
PROFILE = "hwpx-agent.note-hwpx.hwpml-2011-inline-note-payload/v1"
OFFICIAL_REPOSITORY = "https://github.com/hancom-io/hwpx-owpml-model.git"
OFFICIAL_COMMIT = "1453388472c703a4b299a0834f425cdac16644b9"
BASE_COMMIT = "fd6274c"

SOURCE_SHA256 = {
    "docs/03_document_model/09_fields_controls_references.md": "3068742808467f298d289c7401980c617981d748dfa73422bab8f7174ef10a20",
    "docs/04_feature_catalog/10_ref.md": "34cfc9283d16b96bdb16d0ffec7a485f4b72548a49ec70fec2968b3c657743e4",
    "docs/04_feature_catalog/contracts/10_ref_contracts.md": "7062034902932355ac8e6c38a4798dd314f39c44518b7e85c26fe71a7a72cc29",
    "docs/09_roadmap/P09_fields_forms_notes_references.md": "0f4068c4dc5484cc348a145c892a2e1d2d3896d421b77c2fa23bb123956f4b55",
}
IMPLEMENTATION_SHA256 = {
    "crates/domain-ir/src/note_engine.rs": "f31db3149e58e161af396e0611b9a3f85a36bf9c68de39e776ea0b2b9fee469f",
    "crates/domain-ir/tests/note_engine.rs": "a5a0ec5057e63688d8775e9bbfee1dd81ce0041267aefef8b05bb3e69d9bccc4",
    "crates/hwpx-package/src/note_hwpx.rs": "4be3f345b92e8f17a7e41e2c1e360e9a12a251ff8c14ae7fceb56a4247ff41ad",
    "crates/hwpx-package/tests/note_hwpx.rs": "2a653139d6cd77a1b5b79121696ab7ffc4caadf4a003fcde2f2cae09b8fd7f71",
}
OFFICIAL_SHA256 = {
    "OWPML/Class/Para/NoteType.h": "3ff35f5926ecdbd08d144dc52165d31ecc25e9d99929dae6d3da1ae3fcdd03b8",
    "OWPML/Class/Para/NoteType.cpp": "df20a88cafb301c4b7b8ece5fbcb20a9cb69cfea6ffcb48a37751d0b16336b15",
    "OWPML/Class/Para/ParaListType.h": "e25e4eb302e770fa913355aa04e30355d6523313a945f1033e6e092c7a937c91",
    "OWPML/Class/Para/ParaListType.cpp": "64dc1b0276f857d25fe3db1d89786020aeb426a7cb920696becad26e8a88c6f0",
    "OWPML/Class/Para/PType.h": "9443763a3b463447479dd26c0f8781fcd7b25f536d8f362832855247a773011b",
    "OWPML/Class/Para/PType.cpp": "acf53f6ce80d7e043e541ddc5a5beb8b5d9e2e7971720fc088b895bfc10a41d4",
    "OWPML/Class/Para/RunType.h": "d794636b3c03756f464b13629156f2258e818f3f67f9f9dd41f38cb6a5a2a432",
    "OWPML/Class/Para/RunType.cpp": "dbaa0fe2b553dccc13381c856fd9c188185a16bf63685f575acf6bf2c9b88dee",
    "OWPML/Class/Para/t.h": "e3ee45308a16a0b006ae57750a94d3019a4f220f3c6c20bd04a0deb0cd22c1bc",
    "OWPML/Class/Para/t.cpp": "c368eafe7af47555dd9e7c6b8ea1695c564854313a280c1e51099e80224d8e1e",
}
FEATURE_CAPABILITIES = {
    "REF-021": "ref.footnote_insert",
    "REF-022": "ref.endnote_insert",
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/note_engine.rs": (
        'Self::Footnote => "ref.footnote_insert"',
        'Self::Endnote => "ref.endnote_insert"',
        "source_document_flow_sha256",
        "target_document_flow_sha256",
    ),
    "crates/domain-ir/tests/note_engine.rs": (
        "inserts_footnote_and_endnote_with_exact_capability_and_native_tag",
        "request_plan_and_build_recheck_exact_state_and_document_flow",
    ),
    "crates/hwpx-package/src/note_hwpx.rs": (
        "NOTE_HWPX_PROFILE_ID",
        "source_note_wrapper_sha256",
        "insert_payload_sha256",
        "payload_digests_from_document",
        "validate_plain_text_payload_document",
        "verify_preservation",
        "tampered_private_plan_binding_is_rejected",
        "<redacted>",
    ),
    "crates/hwpx-package/tests/note_hwpx.rs": (
        "inserts_exact_footnote_and_endnote_with_full_body_and_marker_state",
        "complete_existing_note_projection_detects_marker_body_style_and_anchor_drift",
        "payload_profile_rejects_unknown_graph_missing_fields_and_astral_marker",
        "request_and_build_reject_section_payload_state_flow_and_map_drift",
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


def bounded_file(root: Path, relative: str, maximum: int = 32 * 1024 * 1024) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ContractError(f"invalid_file:{relative}")
    return path


def load(root: Path, relative: str) -> Any:
    data = bounded_file(root, relative).read_bytes()
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=duplicate_guard)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"invalid_json:{relative}") from error


def canonical_digest(path: Path) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def raw_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_boundary() -> dict[str, Any]:
    return {
        "direct_stage": "two_rows_closed_plain_text_static_section_integration_passed",
        "integration_rows": 2,
        "static_section_hwpx": True,
        "typed_target_projection_readback": True,
        "footnote_endnote_insert": True,
        "outside_delta_byte_preserved": True,
        "complete_state_flow_map_and_payload_bound": True,
        "arbitrary_rich_note_body": False,
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


def expected_claims() -> dict[str, Any]:
    return {
        "two_row_closed_plain_text_static_section_integration": True,
        "typed_target_projection_readback": True,
        "outside_delta_byte_preserved": True,
        "complete_state_flow_map_and_payload_bound": True,
        "arbitrary_rich_note_body": False,
        "complete_package_hwpx": False,
        "actual_hwpx": False,
        "actual_hangul": False,
        "semantic_reopen": False,
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
    validate_contract(contract, errors)
    source_count = validate_locks(root, contract.get("source_locks"), SOURCE_SHA256, True, errors)
    implementation_count = validate_implementation(root, errors)
    qualification_ok = validate_qualification(qualification, errors)
    validate_documents(root, errors)
    return result(errors, source_count, implementation_count, qualification_ok)


def validate_contract(contract: Any, errors: list[str]) -> None:
    keys = {
        "schema_version", "task", "source_lock_canonicalization", "source_qualification",
        "migration", "policy", "report", "source_locks", "implementation_files", "profile",
        "feature_capabilities", "admitted_profile", "planning", "failure_policy",
        "evidence_boundary", "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != keys:
        errors.append("contract_shape")
        return
    if contract["schema_version"] != "hwpx-agent.p09-note-hwpx-contract/v1":
        errors.append("schema_version")
    if contract["task"] != "P09-15" or contract["profile"] != PROFILE:
        errors.append("identity")
    if contract["source_lock_canonicalization"] != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    if contract["source_qualification"] != QUALIFICATION or contract["migration"] != MIGRATION:
        errors.append("artifact_identity")
    if contract["policy"] != POLICY or contract["report"] != REPORT:
        errors.append("document_identity")
    if contract["implementation_files"] != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    if contract["feature_capabilities"] != FEATURE_CAPABILITIES:
        errors.append("features")
    if not isinstance(contract["admitted_profile"], dict) or len(contract["admitted_profile"]) != 9:
        errors.append("admitted_profile")
    if not isinstance(contract["planning"], dict) or not all(contract["planning"].values()):
        errors.append("planning")
    if not isinstance(contract["failure_policy"], list) or len(contract["failure_policy"]) != 9:
        errors.append("failure_policy")
    if contract["evidence_boundary"] != expected_boundary():
        errors.append("claim_promotion")
    if contract["gate_decision"] != {
        "component": "pass",
        "static_section_direct_hwpx": "pass",
        "ref_021_stage": "integration_passed",
        "ref_022_stage": "integration_passed",
        "current_target": "not_run",
        "release_green_rows": 0,
        "p09": "in_progress",
        "product_complete": False,
    }:
        errors.append("gate_decision")


def validate_locks(
    root: Path, value: Any, expected: dict[str, str], canonical: bool, errors: list[str]
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
            actual = (
                canonical_digest(bounded_file(root, relative))
                if canonical
                else raw_digest(bounded_file(root, relative))
            )
            if actual != digest:
                errors.append("source_lock_digest")
        except (OSError, ContractError):
            errors.append("source_lock_path")
    if declared != expected:
        errors.append("source_lock_set")
    return len(declared)


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


def validate_qualification(value: Any, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append("qualification_shape")
        return False
    if (
        value.get("schema_version")
        != "hwpx-agent.p09-note-hwpx-source-qualification/v1"
        or value.get("task") != "P09-15"
        or value.get("base_commit") != BASE_COMMIT
        or value.get("profile") != PROFILE
    ):
        errors.append("qualification_identity")
    official = value.get("official_source")
    if (
        not isinstance(official, dict)
        or official.get("repository") != OFFICIAL_REPOSITORY
        or official.get("commit") != OFFICIAL_COMMIT
        or official.get("reviewed_sha256") != OFFICIAL_SHA256
    ):
        errors.append("qualification_official")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    if value.get("tests") != {
        "note_engine_domain": "9/9 PASS",
        "note_hwpx_public": "7/7 PASS",
        "note_hwpx_private_tamper": "1/1 PASS",
        "fixture_classes": ["boundary", "happy_path", "negative", "preservation"],
        "focused_clippy": "PASS",
    }:
        errors.append("qualification_tests")
    if value.get("claims") != expected_claims():
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_documents(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("There is no accepted v0", "fail closed", "no partial output"),
        POLICY: (
            "closed plain-text note static-section integration pass",
            "actual_hangul=false",
            "product_complete=false",
        ),
        REPORT: ("7/7 PASS", "actual_hwpx=false", "green_rows=0"),
    }
    for relative, markers in expected.items():
        try:
            text = bounded_file(root, relative).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("document_marker")
        except (OSError, UnicodeDecodeError, ContractError):
            errors.append("document_path")


def result(errors: list[str], sources: int, implementation: int, qualification: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p09-note-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": sources,
        "implementation_locks": implementation,
        "source_qualification": qualification,
        "integration_rows": 2,
        "static_section_hwpx": True,
        "arbitrary_rich_note_body": False,
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
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
