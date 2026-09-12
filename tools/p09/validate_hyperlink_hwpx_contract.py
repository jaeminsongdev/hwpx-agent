#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p09-hyperlink-hwpx-v1.json"
MIGRATION = "protocol/migrations/p09-link-reference-v1-to-v2.md"
POLICY = "implementation/p09/P09-14_HYPERLINK_HWPX_POLICY.md"
REPORT = "implementation/p09/P09-14_HYPERLINK_HWPX_REPORT.md"
QUALIFICATION = "implementation/p09/evidence/p09-14-hyperlink-hwpx-source-qualification.v1.json"
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
    "crates/domain-ir/src/link_reference.rs": "fd2e80c05810eea21b085499bab4f9bf95b8329287adc55fd46e240eb113766f",
    "crates/domain-ir/tests/link_reference.rs": "1514ff19e9c2041335ad62033767c2042056e0a1d3de3c1e69b6a2029107d252",
    "crates/hwpx-package/src/lib.rs": "f97fe8a7fcd972280a0e3306953347c5663a84d592045f799edc0e6e12656f12",
    "crates/hwpx-package/src/hyperlink_hwpx.rs": "416572db4e7f37bcfb4a6dfb4976489099d0087b21e36109ebd967649146a1e3",
    "crates/hwpx-package/tests/hyperlink_hwpx.rs": "3b36d7ff7b920c28d0cc290f82548acbad9df00a62882adab8b273c2a5b8b518",
}
CAPABILITIES = {"REF-033": "ref.hyperlink_insert", "REF-034": "ref.hyperlink_edit"}
CLAIMS = {
    "source_qualification_only": True,
    "link_reference_v2": True,
    "direct_hwpx_implemented": True,
    "static_section_readback": True,
    "exact_outside_delta_preservation": True,
    "actual_hwpx": False,
    "actual_hangul": False,
    "generated_output_hancom_open": False,
    "save_reopen": False,
    "field_readback": False,
    "render": False,
    "automation": False,
    "differential": False,
    "p09_complete": False,
    "production_ready": False,
    "product_complete": False,
}
DIGEST = re.compile(r"^[0-9a-f]{64}$")


class DuplicateKey(ValueError):
    pass


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise DuplicateKey(key)
        output[key] = value
    return output


def file(root: Path, relative: str, maximum: int = 64 * 1024 * 1024) -> Path:
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
        return result(["contract_json_or_path"], False)
    required = {
        "schema_version", "task", "scope", "source_lock_canonicalization",
        "source_qualification", "migration", "policy", "report", "source_locks",
        "capability_features", "domain_model", "adapter_profile", "implementation_files",
        "native_profile", "state_binding", "failure_policy", "evidence_boundary", "gate_decision",
    }
    if not isinstance(contract, dict) or set(contract) != required:
        errors.append("contract_shape")
    if (
        contract.get("schema_version") != "hwpx-agent.p09-hyperlink-hwpx-contract/v1"
        or contract.get("task") != "P09-14"
        or contract.get("scope")
        != "ref_033_ref_034_exact_hangul_2020_https_current_tab_static_section_adapter"
    ):
        errors.append("contract_identity")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_mode")
    expected_paths = (QUALIFICATION, MIGRATION, POLICY, REPORT)
    actual_paths = tuple(contract.get(key) for key in ("source_qualification", "migration", "policy", "report"))
    if actual_paths != expected_paths:
        errors.append("contract_paths")
    else:
        for path in expected_paths:
            try:
                file(root, path)
            except (OSError, ValueError):
                errors.append("contract_paths")
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
    if contract.get("domain_model") != "hwpx-agent.link-reference/v2" or contract.get(
        "adapter_profile"
    ) != "hwpx-agent.hyperlink-hwpx.hangul-2020-https-current-tab/v1":
        errors.append("profiles")
    if contract.get("implementation_files") != list(IMPLEMENTATION_SHA256):
        errors.append("implementation_files")
    for path, digest in IMPLEMENTATION_SHA256.items():
        try:
            if not DIGEST.fullmatch(digest) or canonical_digest(file(root, path)) != digest:
                errors.append("implementation_digest")
        except (OSError, ValueError):
            errors.append("implementation_digest")
    validate_native_profile(contract.get("native_profile"), errors)
    validate_boundary(contract, errors)
    qualification_ok = validate_qualification(root, errors)
    validate_text(root, errors)
    return result(sorted(set(errors)), qualification_ok)


def validate_native_profile(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict) or value.get("field_runs") != [
        "begin_control_run", "existing_plain_text_display_run", "end_control_run"
    ]:
        errors.append("native_profile")
        return
    if value.get("begin_attributes") != {
        "type": "HYPERLINK", "name": "", "editable": "0", "dirty": "1", "zorder": "-1"
    }:
        errors.append("native_profile")
    if value.get("parameters") != [
        ["integerParam", "Prop", "0"],
        ["stringParam", "Command", "https\\://target;1;0;0;"],
        ["stringParam", "Path", "approved_https_uri"],
        ["stringParam", "Category", "HWPHYPERLINK_TYPE_URL"],
        ["stringParam", "TargetType", "HWPHYPERLINK_TARGET_BOOKMARK"],
        ["stringParam", "DocOpenType", "HWPHYPERLINK_JUMP_CURRENTTAB"],
    ]:
        errors.append("native_profile")
    if set(value) != {"field_runs", "begin_attributes", "parameters", "identity", "range", "edit"}:
        errors.append("native_profile")


def validate_boundary(contract: dict[str, Any], errors: list[str]) -> None:
    boundary = contract.get("evidence_boundary")
    expected = {
        "link_reference_v2": True,
        "direct_hwpx_implemented": True,
        "static_section_readback": True,
        "exact_outside_delta_preservation": True,
        "licensed_hangul_discovery_source_qualified": True,
        "private_discovery_committed": False,
        "generated_output_hancom_open": False,
        "actual_hwpx": False,
        "actual_hangul": False,
        "save_reopen": False,
        "field_readback": False,
        "render": False,
        "automation": False,
        "differential": False,
        "p09_14_green": False,
        "p09_complete": False,
        "production_ready": False,
        "product_complete": False,
        "focused_rust_tests": "19/19 PASS",
        "private_contract_tests": "4/4 PASS",
        "direct_stage": "integration_passed",
    }
    if boundary != expected:
        errors.append("claim_promotion")
    gate = contract.get("gate_decision")
    if not isinstance(gate, dict) or gate.get("actual_target") != "not_run" or any(
        gate.get(key) is not False for key in ("p09_14_green", "product_complete")
    ):
        errors.append("gate_promotion")


def validate_qualification(root: Path, errors: list[str]) -> bool:
    try:
        value = load(root, QUALIFICATION)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("qualification_json_or_path")
        return False
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "task", "base_commit", "scope", "target", "discovery",
        "official_model", "source_sha256", "implementation_sha256", "tests", "claims",
    }:
        errors.append("qualification_shape")
    if (
        value.get("schema_version")
        != "hwpx-agent.p09-hyperlink-hwpx-source-qualification/v1"
        or value.get("task") != "P09-14"
        or value.get("base_commit") != "994403f"
    ):
        errors.append("qualification_identity")
    target = value.get("target")
    if target != {
        "product": "Hancom Hangul 2020", "build": "11.0.0.9136",
        "architecture": "x86", "locale": "ko-KR",
    }:
        errors.append("qualification_target")
    discovery = value.get("discovery")
    if not isinstance(discovery, dict) or discovery.get("interaction_owner") != "user" or (
        discovery.get("private_before_after_present") is not True
        or discovery.get("private_artifacts_committed") is not False
        or discovery.get("generated_adapter_output_executed") is not False
    ):
        errors.append("qualification_discovery")
    official = value.get("official_model")
    if not isinstance(official, dict) or official.get("commit") != (
        "1453388472c703a4b299a0834f425cdac16644b9"
    ) or official.get("source_sha256") != OFFICIAL_SOURCE_SHA256:
        errors.append("qualification_official_sources")
    if value.get("source_sha256") != SOURCE_SHA256:
        errors.append("qualification_sources")
    if value.get("implementation_sha256") != IMPLEMENTATION_SHA256:
        errors.append("qualification_implementation")
    if value.get("tests") != {
        "public_link_reference": "10/10 PASS",
        "public_hyperlink_hwpx": "8/8 PASS",
        "private_plan_tamper": "1/1 PASS",
        "focused_total": "19/19 PASS",
        "private_contract": "4/4 PASS",
        "network_used": False,
        "licensed_application_used_for_discovery": True,
        "licensed_application_used_for_generated_output": False,
    }:
        errors.append("qualification_tests")
    if value.get("claims") != CLAIMS:
        errors.append("qualification_claims")
    return not any(error.startswith("qualification_") for error in errors)


def validate_text(root: Path, errors: list[str]) -> None:
    expected = {
        MIGRATION: ("link-reference/v2", "new_parameters_sha256", "fail closed"),
        POLICY: ("REF-033", "REF-034", "generated_output_hancom_open=false", "product_complete=false"),
        REPORT: ("10/10 PASS", "8/8 PASS", "actual_hangul=false", "integration_passed"),
    }
    for path, markers in expected.items():
        try:
            text = file(root, path).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                errors.append("text_artifact")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("text_artifact")


def result(errors: list[str], qualification_verified: bool) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p09-hyperlink-hwpx-validation/v1",
        "task": "P09-14",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": len(SOURCE_SHA256),
        "official_source_files": len(OFFICIAL_SOURCE_SHA256),
        "implementation_files": len(IMPLEMENTATION_SHA256),
        "source_qualification_verified": qualification_verified,
        "capabilities": len(CAPABILITIES),
        "direct_stage": "integration_passed",
        "actual_hwpx": "not_run",
        "actual_hangul": "not_run",
        "generated_output_hancom_open": "not_run",
        "save_reopen": "not_run",
        "field_readback": "not_run",
        "render": "not_run",
        "automation": "not_run",
        "differential": "not_run",
        "p09_14_green": False,
        "p09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    outcome = validate()
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    sys.exit(0 if outcome["state"] == "pass" else 1)
