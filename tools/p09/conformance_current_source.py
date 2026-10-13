"""Versioned original-conformance source proof; never native or product authority."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from reference_conformance import ConformanceError, canonical_bytes

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tools.p09.comment_current_source import bounded_file, duplicate_guard

PROFILE = "current_source_v2"
CURRENT_MATRIX = "implementation/p09/evidence/conformance/p09-reference-conformance.current-source-2020.v2.json"
QUALIFICATION = "implementation/p09/evidence/p09-92-conformance-current-source.qualification.v2.json"
QUALIFICATION_BYTES = 87548
QUALIFICATION_SHA256 = "ace2f794eebffd52e95095cfc43d0a81c09791453f28127adbbaf6afdde0501e"
UPSTREAM_PROFILES = [
    {
        "validator": "tools/p09/validate_field_core_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_form_control_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_note_engine_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_comment_model_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-comment-model-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_link_reference_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_cross_reference_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_toc_index_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_citation_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_mail_merge_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_reference_auxiliary_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_form_control_hwpx_contract.py",
        "arguments": [],
        "expected_schema": "hwpx-agent.p09-form-control-hwpx-validation/v1",
        "source_profile": "historical_unchanged_fixture_source"
    },
    {
        "validator": "tools/p09/validate_bookmark_hwpx_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_note_hwpx_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_hyperlink_hwpx_contract.py",
        "arguments": [
            "--current-source-v2"
        ],
        "expected_schema": "hwpx-agent.p09-original-component-current-source-validation/v2",
        "source_profile": "current_source_v2"
    },
    {
        "validator": "tools/p09/validate_field_auto_number_hwpx_contract.py",
        "arguments": [],
        "expected_schema": "hwpx-agent.p09-field-auto-number-hwpx-validation/v1",
        "source_profile": "historical_unchanged_fixture_source"
    }
]


def cli_profile(arguments: list[str]) -> str:
    if not arguments:
        return "historical_v1"
    return PROFILE if arguments == ["--current-source-v2"] else "unsupported"


def _verify_bundle(root: Path) -> dict[str, Any]:
    raw = bounded_file(root, QUALIFICATION, QUALIFICATION_BYTES)
    if len(raw) != QUALIFICATION_BYTES or hashlib.sha256(raw).hexdigest() != QUALIFICATION_SHA256:
        raise ValueError("conformance_current_receipt_digest")
    proof = json.loads(raw, object_pairs_hook=duplicate_guard)
    if proof["schema_version"] != "hwpx-agent.p09-reference-conformance-current-source-qualification/v2":
        raise ValueError("conformance_current_receipt_schema")
    if proof["profile_id"] != PROFILE or proof["upstream_profiles"] != UPSTREAM_PROFILES:
        raise ValueError("conformance_current_receipt_profile")
    pins = proof["raw_pins"]
    if len(pins) != proof["raw_pin_count"] or len({pin["path"] for pin in pins}) != len(pins):
        raise ValueError("conformance_current_pin_set")
    files: dict[str, bytes] = {}
    for pin in pins:
        if set(pin) != {"path", "bytes", "sha256"} or type(pin["bytes"]) is not int:
            raise ValueError("conformance_current_pin_shape")
        data = bounded_file(root, pin["path"])
        if len(data) != pin["bytes"] or hashlib.sha256(data).hexdigest() != pin["sha256"]:
            raise ValueError("conformance_current_raw_drift")
        files[pin["path"]] = data
    wrapper = json.loads(files[CURRENT_MATRIX], object_pairs_hook=duplicate_guard)
    if (
        wrapper["schema_version"] != "hwpx-agent.p09-reference-conformance-current-source-matrix/v2"
        or wrapper["profile_id"] != PROFILE
        or wrapper["upstream_profiles"] != UPSTREAM_PROFILES
        or wrapper["native_admission"] != "INPUT_CHANGED_RE_ADMISSION_REQUIRED"
        or wrapper["P09_gate"] != "OPEN" or wrapper["P10_new_implementation"] is not False
        or wrapper["goal_status"] != "active"
        or wrapper["matrix"]["summary"]["required_rows"] != 53
        or wrapper["matrix"]["summary"]["p09_owned_rows"] != 46
        or wrapper["matrix"]["summary"]["p11_deferred_rows"] != 7
        or wrapper["matrix"]["summary"]["green_rows"] != 0
    ):
        raise ValueError("conformance_current_wrapper")
    for path, expected in proof["canonical_sha256"].items():
        actual = hashlib.sha256(files[path].decode("utf-8").replace("\r\n", "\n").encode("utf-8")).hexdigest()
        if actual != expected:
            raise ValueError("conformance_current_canonical_drift")
    if proof["gate"] != {
        "P09": "OPEN", "A12": "OPEN", "A13": "OPEN",
        "P26": "failed_semantic_non_green", "P62": "UNRESOLVED",
        "native_admission": "INPUT_CHANGED_RE_ADMISSION_REQUIRED",
        "full_native34": "NOT_RUN", "P10_new_implementation": False,
        "goal_status": "active",
    }:
        raise ValueError("conformance_current_gate_promotion")
    if any(proof["claims"][name] is not False for name in [
        "native_semantic_acceptance", "actual_hangul", "actual_SQL",
        "p09_complete", "product_complete", "P10_new_implementation",
    ]):
        raise ValueError("conformance_current_claim_promotion")
    return {"proof": proof, "matrix_wrapper": wrapper}


def verify_bundle(root: Path) -> dict[str, Any]:
    try:
        return _verify_bundle(root)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        raise ConformanceError("current_source_v2_qualification") from error


def current_matrix_bytes(root: Path) -> bytes:
    return canonical_bytes(verify_bundle(root)["matrix_wrapper"]["matrix"])


def admitted_validator_digest(root: Path) -> str:
    return verify_bundle(root)["proof"]["canonical_sha256"]["tools/p09/validate_reference_conformance_contract.py"]


def upstream_arguments(validator: str) -> list[str]:
    for profile in UPSTREAM_PROFILES:
        if profile["validator"] == validator:
            return list(profile["arguments"])
    raise ConformanceError("current_source_upstream_unknown")


def validate_upstream_payload(validator: str, payload: dict[str, Any]) -> None:
    profile = next((p for p in UPSTREAM_PROFILES if p["validator"] == validator), None)
    if profile is None:
        raise ConformanceError("current_source_upstream_unknown")
    if (
        payload.get("state") != "pass" or payload.get("schema_version") != profile["expected_schema"]
        or payload.get("product_complete") is not False
        or any(payload.get(name) != "not_run" for name in ["actual_hwpx", "actual_hangul", "render", "automation", "differential"])
        or any(value for key, value in payload.items() if key.endswith("_green") or key == "green_rows")
    ):
        raise ConformanceError("current_source_upstream_shape_or_promotion")
    if profile["arguments"]:
        if payload.get("source_profile") != PROFILE or payload.get("current_source_qualification_verified") is not True:
            raise ConformanceError("current_source_upstream_unqualified")
        expected_pins = 32 if "comment_model" in validator else 172
        if payload.get("current_source_raw_pins") != expected_pins:
            raise ConformanceError("current_source_upstream_pin_scope")
        if "comment_model" not in validator:
            expected_family = Path(validator).stem.removeprefix("validate_").removesuffix("_contract")
            if payload.get("current_source_family") != expected_family:
                raise ConformanceError("current_source_upstream_family")
