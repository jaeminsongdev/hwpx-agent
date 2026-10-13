"""Explicit source admission for original P09 validators, never native authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tools.p09.comment_current_source import bounded_file, duplicate_guard

PROFILE = "current_source_v2"
QUALIFICATION = "implementation/p09/evidence/p09-91-component-current-source.qualification.v2.json"
QUALIFICATION_BYTES = 72953
QUALIFICATION_SHA256 = "a76704f0f7beecfdea8c0518121c18f97de9449afccfd5442b8a69bbef3af7e5"
OFFICIAL_CACHE = "fixtures/target-build/official-source-cache/hwpx-owpml-model-145338/"
IMPLEMENTATION_SHA256 = {
    "field_core": {
        "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
        "crates/domain-ir/src/field_engine.rs": "c9c77c27f741cb985de6da734a14fdf28917d89500d25a73a8cce2d7e2ad5da5",
        "crates/domain-ir/tests/field_engine.rs": "15a3f49dab9aed32f087ec7aceb1c3d38617681f01162ce4415fe4b77338abb1"
    },
    "form_control": {
        "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
        "crates/domain-ir/src/form_control.rs": "19e4c23c1318d477fd85a851d9f0e76dbe70012d9295b8202b162247105fabb5",
        "crates/domain-ir/tests/form_control.rs": "11af786a06c4792a30546f6e73e4123eb33b573b84eb69c2a2b9c05f3ed750b5"
    },
    "note_engine": {
        "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
        "crates/domain-ir/src/note_engine.rs": "f31db3149e58e161af396e0611b9a3f85a36bf9c68de39e776ea0b2b9fee469f",
        "crates/domain-ir/tests/note_engine.rs": "a5a0ec5057e63688d8775e9bbfee1dd81ce0041267aefef8b05bb3e69d9bccc4"
    },
    "link_reference": {
        "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
        "crates/domain-ir/src/link_reference.rs": "fd2e80c05810eea21b085499bab4f9bf95b8329287adc55fd46e240eb113766f",
        "crates/domain-ir/tests/link_reference.rs": "1514ff19e9c2041335ad62033767c2042056e0a1d3de3c1e69b6a2029107d252"
    },
    "cross_reference": {
        "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
        "crates/domain-ir/src/cross_reference.rs": "90f2dfb5efed392b6083b5f7fe67dc812fb96dc1866c7015c0e8cd885de05059",
        "crates/domain-ir/tests/cross_reference.rs": "5355358f79cd92c8f77a4b109414bc9dadb6a214b12622883d84625ee0884bde"
    },
    "toc_index": {
        "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
        "crates/domain-ir/src/toc_index.rs": "f7fe0a171b51cb508f7d0445614f20fc40b5036fc2ac1e92110af0b8166fe718",
        "crates/domain-ir/tests/toc_index.rs": "83ca0c65d6186eaa1048a9f87af6d420eac82a3e0dec54626649d59469ef2008"
    },
    "citation": {
        "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
        "crates/domain-ir/src/citation.rs": "50fb5bdc5376eb639c24aa0f9a3811e4aeee2b84ca1470a0e7dc0d5f7c523e13",
        "crates/domain-ir/tests/citation.rs": "54b4c44ea134612a7f44c465a97eac2da1d49ab91eaad1ae86bf849549a8c195"
    },
    "mail_merge": {
        "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
        "crates/domain-ir/src/mail_merge.rs": "54a55e4c32adf3905c76c20790b84117b8943442667e8bfd92cf67f717859581",
        "crates/domain-ir/tests/mail_merge.rs": "0d24c59a611cb73950a1b5bdca4a58932c2e3f85e3d87bec5885832b1a05df3d"
    },
    "reference_auxiliary": {
        "crates/domain-ir/src/lib.rs": "f7d26ac5a32f865e82f11ee7031e5ba17f40d679f523201ff33e60d3430aa791",
        "crates/domain-ir/src/reference_auxiliary.rs": "04e3c23493732cf35e4cfdff83314d55b725c1e419b524a1ef00ca9c60f66777",
        "crates/domain-ir/tests/reference_auxiliary.rs": "af73840e97cd0fd1d71b80588a7f9e3771072e8723aadc588c1c173b147b2396"
    },
    "bookmark_hwpx": {
        "crates/domain-ir/src/link_reference.rs": "fd2e80c05810eea21b085499bab4f9bf95b8329287adc55fd46e240eb113766f",
        "crates/domain-ir/tests/link_reference.rs": "1514ff19e9c2041335ad62033767c2042056e0a1d3de3c1e69b6a2029107d252",
        "crates/hwpx-package/src/bookmark_hwpx.rs": "87ef96beaf7e9f513cf61aa26e367e0d2a1df4b5b0d370971c0d7418b86e4c51",
        "crates/hwpx-package/tests/bookmark_hwpx.rs": "e27df62629c93e89cf503406acb5946bb9fd7b6bdb65783bb13eb5546563ccf3"
    },
    "note_hwpx": {
        "crates/domain-ir/src/note_engine.rs": "f31db3149e58e161af396e0611b9a3f85a36bf9c68de39e776ea0b2b9fee469f",
        "crates/domain-ir/tests/note_engine.rs": "a5a0ec5057e63688d8775e9bbfee1dd81ce0041267aefef8b05bb3e69d9bccc4",
        "crates/hwpx-package/src/note_hwpx.rs": "3364d95456e783633c77b044a223afa911c6c2035fe79c447c742bc4f40ce7c4",
        "crates/hwpx-package/tests/note_hwpx.rs": "2a653139d6cd77a1b5b79121696ab7ffc4caadf4a003fcde2f2cae09b8fd7f71"
    },
    "hyperlink_hwpx": {
        "crates/domain-ir/src/link_reference.rs": "fd2e80c05810eea21b085499bab4f9bf95b8329287adc55fd46e240eb113766f",
        "crates/domain-ir/tests/link_reference.rs": "1514ff19e9c2041335ad62033767c2042056e0a1d3de3c1e69b6a2029107d252",
        "crates/hwpx-package/src/hyperlink_hwpx.rs": "4e60e8c176d2bcdaac6c7b55ef3be0107c36b437250f501351ff1be02da7e99e",
        "crates/hwpx-package/tests/hyperlink_hwpx.rs": "3b36d7ff7b920c28d0cc290f82548acbad9df00a62882adab8b273c2a5b8b518"
    }
}
RAW_IMPLEMENTATION_FAMILIES = {"bookmark_hwpx", "note_hwpx"}


def cli_profile(arguments: list[str]) -> str:
    if not arguments:
        return "historical_v1"
    return PROFILE if arguments == ["--current-source-v2"] else "unsupported"


def canonical(data: bytes, *, remove_bom: bool = False) -> str:
    text = data.decode("utf-8-sig" if remove_bom else "utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def verify_receipt(root: Path, family: str) -> dict[str, Any]:
    raw = bounded_file(root, QUALIFICATION, QUALIFICATION_BYTES)
    if len(raw) != QUALIFICATION_BYTES or hashlib.sha256(raw).hexdigest() != QUALIFICATION_SHA256:
        raise ValueError("current_source_v2_receipt_digest")
    value = json.loads(raw, object_pairs_hook=duplicate_guard)
    if (
        value["schema_version"] != "hwpx-agent.p09-original-component-current-source-qualification/v2"
        or value["profile_id"] != PROFILE
        or set(value["families"]) != set(IMPLEMENTATION_SHA256)
        or family not in IMPLEMENTATION_SHA256
    ):
        raise ValueError("current_source_v2_profile")
    pins = value["raw_pins"]
    if len(pins) != 171 or len({p["path"] for p in pins}) != len(pins):
        raise ValueError("current_source_v2_coverage")
    raw_by_path: dict[str, bytes] = {}
    for pin in pins:
        if set(pin) != {"path", "bytes", "sha256"} or type(pin["bytes"]) is not int:
            raise ValueError("current_source_v2_pin_shape")
        data = bounded_file(root, pin["path"])
        if len(data) != pin["bytes"] or hashlib.sha256(data).hexdigest() != pin["sha256"]:
            raise ValueError("current_source_v2_raw_digest")
        raw_by_path[pin["path"]] = data
    for name, proof in value["families"].items():
        raw_mode = name in RAW_IMPLEMENTATION_FAMILIES
        if proof["implementation_sha256"] != IMPLEMENTATION_SHA256[name]:
            raise ValueError("current_source_v2_implementation_mapping")
        expected_mode = "raw_sha256" if raw_mode else "utf8_BOM_kept_CRLF_CR_to_LF_sha256"
        if proof["implementation_digest_mode"] != expected_mode:
            raise ValueError("current_source_v2_implementation_mode")
        for relative, expected in IMPLEMENTATION_SHA256[name].items():
            data = raw_by_path[relative]
            actual = hashlib.sha256(data).hexdigest() if raw_mode else canonical(data)
            if actual != expected:
                raise ValueError("current_source_v2_implementation")
        for relative, expected in proof["authoritative_source_sha256"].items():
            if canonical(raw_by_path[relative]) != expected:
                raise ValueError("current_source_v2_authoritative_source")
        remove_bom = name == "reference_auxiliary"
        official_mode = "utf8_BOM_removed_CRLF_CR_to_LF_sha256" if remove_bom else "utf8_BOM_kept_CRLF_CR_to_LF_sha256"
        if proof["official_source_digest_mode"] != official_mode:
            raise ValueError("current_source_v2_official_mode")
        for relative, expected in proof["official_source_sha256"].items():
            if canonical(raw_by_path[OFFICIAL_CACHE + relative], remove_bom=remove_bom) != expected:
                raise ValueError("current_source_v2_official_digest")
        if proof["component_tests"] != proof["public_Rust_tests"] + proof["private_Rust_tests"]:
            raise ValueError("current_source_v2_tests")
    tests = value["Rust_component_regression"]
    if (
        tests["focused_original_twelve"] != 128 or tests["total_passed"] != 137
        or tests["failed"] != 0 or tests["exit_codes"] != [0, 0, 0]
        or value["claims"]["native_semantic_acceptance"] is not False
        or value["claims"]["actual_hangul"] is not False
        or value["claims"]["actual_SQL"] is not False
        or value["claims"]["product_complete"] is not False
        or value["claims"]["p09_complete"] is not False
        or value["claims"]["P10_new_implementation"] is not False
        or value["gate"] != {
            "P09": "OPEN", "A12": "OPEN", "A13": "OPEN",
            "P26": "failed_semantic_non_green", "P62": "UNRESOLVED",
            "native_admission": "INPUT_CHANGED_RE_ADMISSION_REQUIRED",
            "full_native34": "NOT_RUN", "goal_status": "active",
        }
    ):
        raise ValueError("current_source_v2_promotion")
    return value


def verify(root: Path, family: str, errors: list[str]) -> bool:
    try:
        verify_receipt(root, family)
        return True
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        errors.append("current_source_v2_qualification")
        return False


def decorate(value: dict[str, Any], family: str, verified: bool) -> dict[str, Any]:
    # 원래 결과/오류/native/Gate 항목은 바꾸거나 제거하지 않는다.
    return {
        **value,
        "source_profile": PROFILE,
        "current_source_family": family,
        "current_source_qualification_verified": verified,
        "current_source_raw_pins": 171 if verified else 0,
        "historical_default_failure_retained": True,
        "native_or_product_gate_promoted": False,
    }

