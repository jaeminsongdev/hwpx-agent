#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PRIVATE_BOUNDARY = ROOT / "implementation" / "p07" / "evidence" / "private"
SOURCE_RECORDS = (
    ROOT
    / "implementation"
    / "p02"
    / "evidence"
    / "automation"
    / "automation-pdf.records.v1.json"
)
EXPECTED_SOURCE_RECORDS_SHA256 = (
    "03db035d408d03ce3f78d4eca8ca76d7f9e8076ef8fadd49d8f3ed4b885317b5"
)
REQUEST_SCHEMA_VERSION = "hwpx-agent.p07-06-equation-automation-probe-request/v1"
RECEIPT_SCHEMA_VERSION = "hwpx-agent.p07-06-equation-automation-probe-plan-receipt/v1"
SOURCE_LOCK_ID = "source-lock-P00-20260901-v9-final-current-scope"
MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_SCRIPT_BYTES = 1024 * 1024
MAX_OUTPUT_BYTES = 4 * 1024 * 1024
DIGEST = re.compile(r"^[0-9a-f]{64}$")
PARENT_HARNESS = (
    ROOT
    / "implementation"
    / "p07"
    / "tools"
    / "run-hancom-2020-equation-automation-probe.ps1"
)
CHILD_HARNESS = PARENT_HARNESS.with_name(
    "run-hancom-2020-equation-automation-probe-child.ps1"
)

# Opaque record identities select the exact source rows. Raw Action, ParameterSet and item values
# are read only from the hash-pinned private P02 source and are emitted only into private evidence.
ACTION_RECORD_IDS = {
    "eq.insert_native": "source:action_table:d3d3d2c48b0c2b6a1cf87abf",
    "eq.edit_native": "source:action_table:90998f7fdc62212300deffba",
}
SELECTION_ACTION_RECORD_ID = "source:action_table:9322e7d8e4da8c6bdbc69630"
ITEM_RECORD_IDS = {
    "script": "source:parameter_table:f072c3d0d3be0a13fb6bc4ee",
    "base_unit": "source:parameter_table:ae65c7323c27e094d6450711",
    "color": "source:parameter_table:d40bc1f524de1b1328a9b9e7",
    "line_mode": "source:parameter_table:f6ffd553c05eafc436522dfb",
    "version": "source:parameter_table:24927e11567448dddebb6b0a",
    "apply_to": "source:parameter_table:7026ac0a2975e1e7b7a13495",
    "visual_script": "source:parameter_table:10837ad83fac2beffa719be7",
    "font_name": "source:parameter_table:4a695a021029db0deff4dd90",
}
EXPECTED_ITEM_TYPES = {
    "script": "PIT_BSTR",
    "base_unit": "PIT_I4",
    "color": "PIT_I4",
    "line_mode": "PIT_I4",
    "version": "PIT_BSTR",
    "apply_to": "PIT_UI4",
    "visual_script": "PIT_BSTR",
    "font_name": "PIT_BSTR",
}


class ProbeBuildError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ProbeBuildError("duplicate JSON key")
        result[key] = value
    return result


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_bounded_regular(path: Path, maximum: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ProbeBuildError("input is not a regular file")
    size = path.stat().st_size
    if size <= 0 or size > maximum:
        raise ProbeBuildError("input size is outside the finite bound")
    return path.read_bytes()


def load_source_records(path: Path, expected_sha256: str) -> tuple[bytes, list[dict[str, Any]]]:
    if not DIGEST.fullmatch(expected_sha256):
        raise ProbeBuildError("source digest is malformed")
    raw = read_bounded_regular(path, MAX_SOURCE_BYTES)
    if sha256(raw) != expected_sha256:
        raise ProbeBuildError("source digest mismatch")
    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProbeBuildError("source JSON is invalid") from error
    if not isinstance(value, list) or not value:
        raise ProbeBuildError("source record root is invalid")
    if not all(isinstance(item, dict) for item in value):
        raise ProbeBuildError("source record is invalid")
    return raw, value


def require_private_output(path: Path, boundary: Path = PRIVATE_BOUNDARY) -> Path:
    resolved_boundary = boundary.resolve()
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(resolved_boundary)
    except ValueError as error:
        raise ProbeBuildError("output escapes private evidence boundary") from error
    cursor = resolved.parent
    while True:
        if cursor.exists() and cursor.is_symlink():
            raise ProbeBuildError("output ancestry contains a symlink")
        if cursor == resolved_boundary:
            break
        if cursor.parent == cursor:
            raise ProbeBuildError("output boundary is not an ancestor")
        cursor = cursor.parent
    return resolved


def resolve_bindings(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or record_id in by_id:
            raise ProbeBuildError("source record identity is malformed or duplicated")
        by_id[record_id] = record

    actions: dict[str, dict[str, str]] = {}
    parameter_set: str | None = None
    for capability_id, record_id in ACTION_RECORD_IDS.items():
        record = by_id.get(record_id)
        if record is None or record.get("source_lock_id") != SOURCE_LOCK_ID:
            raise ProbeBuildError("required action source record is absent or drifted")
        if record.get("source_kind") != "action_table":
            raise ProbeBuildError("required action source kind drifted")
        name = record.get("original_name")
        parameters = record.get("parameters")
        if (
            not isinstance(name, str)
            or not name
            or not isinstance(parameters, list)
            or len(parameters) != 1
            or not isinstance(parameters[0], dict)
            or parameters[0].get("declared_type") != "ParameterSet ID"
            or not isinstance(parameters[0].get("original_name"), str)
        ):
            raise ProbeBuildError("required action source shape drifted")
        candidate_set = parameters[0]["original_name"]
        if parameter_set is None:
            parameter_set = candidate_set
        elif candidate_set != parameter_set:
            raise ProbeBuildError("equation actions use different ParameterSet identities")
        actions[capability_id] = {
            "capability_id": capability_id,
            "action_id": name,
            "parameter_set_id": candidate_set,
            "source_record_id": record_id,
        }

    selection_record = by_id.get(SELECTION_ACTION_RECORD_ID)
    selection_parameters = (
        None if selection_record is None else selection_record.get("parameters")
    )
    if (
        selection_record is None
        or selection_record.get("source_lock_id") != SOURCE_LOCK_ID
        or selection_record.get("source_kind") != "action_table"
        or not isinstance(selection_record.get("original_name"), str)
        or not selection_record["original_name"]
        or not isinstance(selection_parameters, list)
        or len(selection_parameters) != 1
        or not isinstance(selection_parameters[0], dict)
        or selection_parameters[0].get("declared_type") != "ParameterSet ID"
        or selection_parameters[0].get("original_name") != "-"
    ):
        raise ProbeBuildError("required selection source record is absent or drifted")

    if parameter_set is None:
        raise ProbeBuildError("equation ParameterSet was not resolved")
    items: dict[str, dict[str, str]] = {}
    expected_section_prefix = f"{parameter_set} |"
    for argument_id, record_id in ITEM_RECORD_IDS.items():
        record = by_id.get(record_id)
        parameters = None if record is None else record.get("parameters")
        locator = None if record is None else record.get("locator")
        if (
            record is None
            or record.get("source_lock_id") != SOURCE_LOCK_ID
            or record.get("source_kind") != "parameter_table"
            or not isinstance(locator, dict)
            or not isinstance(locator.get("section"), str)
            or not locator["section"].startswith(expected_section_prefix)
            or not isinstance(parameters, list)
            or len(parameters) != 1
            or not isinstance(parameters[0], dict)
            or parameters[0].get("declared_type") != EXPECTED_ITEM_TYPES[argument_id]
            or record.get("original_name") != parameters[0].get("original_name")
            or not isinstance(record.get("original_name"), str)
            or not record["original_name"]
        ):
            raise ProbeBuildError("required ParameterSet item source shape drifted")
        items[argument_id] = {
            "argument_id": argument_id,
            "item_name": record["original_name"],
            "source_record_id": record_id,
            "declared_type": EXPECTED_ITEM_TYPES[argument_id],
        }

    if actions["eq.insert_native"]["action_id"] == actions["eq.edit_native"]["action_id"]:
        raise ProbeBuildError("insert and edit action identities are not distinct")
    return {
        "actions": actions,
        "selection": {
            "operation_id": "select_inserted_control_reverse",
            "action_id": selection_record["original_name"],
            "parameter_set_id": None,
            "source_record_id": SELECTION_ACTION_RECORD_ID,
        },
        "items": items,
        "readback": {
            "capability_id": "eq.roundtrip_readback",
            "action_source": "eq.edit_native",
            "method": "get_default_without_execute",
        },
    }


def validate_script(value: str, digest: str) -> tuple[str, int]:
    if not isinstance(value, str) or not value:
        raise ProbeBuildError("script is empty")
    encoded = value.encode("utf-8")
    if len(encoded) > MAX_SCRIPT_BYTES or any(
        ord(character) < 32 and character not in "\n\t" for character in value
    ):
        raise ProbeBuildError("script is outside the finite text profile")
    if not DIGEST.fullmatch(digest) or sha256(encoded) != digest:
        raise ProbeBuildError("script digest mismatch")
    return digest, len(encoded)


def build_request(
    records: list[dict[str, Any]],
    source_records_sha256: str,
    initial_script: str,
    initial_script_sha256: str,
    initial_semantic_sha256: str,
    edited_script: str,
    edited_script_sha256: str,
    edited_semantic_sha256: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not DIGEST.fullmatch(source_records_sha256):
        raise ProbeBuildError("source digest is malformed")
    initial_digest, initial_bytes = validate_script(initial_script, initial_script_sha256)
    edited_digest, edited_bytes = validate_script(edited_script, edited_script_sha256)
    if initial_script == edited_script or initial_semantic_sha256 == edited_semantic_sha256:
        raise ProbeBuildError("initial and edited programs are not distinct")
    for digest in (initial_semantic_sha256, edited_semantic_sha256):
        if not DIGEST.fullmatch(digest):
            raise ProbeBuildError("semantic digest is malformed")

    bindings = resolve_bindings(records)
    binding_set_sha256 = sha256(canonical_bytes(bindings))
    harness = {
        "parent_sha256": sha256(read_bounded_regular(PARENT_HARNESS, MAX_OUTPUT_BYTES)),
        "child_sha256": sha256(read_bounded_regular(CHILD_HARNESS, MAX_OUTPUT_BYTES)),
    }
    seed = canonical_bytes(
        {
            "source_records_sha256": source_records_sha256,
            "binding_set_sha256": binding_set_sha256,
            "initial_script_sha256": initial_digest,
            "initial_semantic_sha256": initial_semantic_sha256,
            "edited_script_sha256": edited_digest,
            "edited_semantic_sha256": edited_semantic_sha256,
            "harness": harness,
        }
    )
    request_id = f"p07-06-{sha256(seed)[:24]}"
    request = {
        "schema_version": REQUEST_SCHEMA_VERSION,
        "request_id": request_id,
        "source": {
            "source_lock_id": SOURCE_LOCK_ID,
            "source_records_sha256": source_records_sha256,
            "binding_set_sha256": binding_set_sha256,
        },
        "harness": harness,
        "target": {
            "profile_id": "hancom-hangul-2020-secondary",
            "product": "Hancom Hangul 2020",
            "exact_build": "11.0.0.9136",
            "locale": "ko-KR",
            "architecture": "x86",
            "registry_view": "Registry32",
            "client_apartment_state": "STA",
            "prog_id": "HWPFrame.HwpObject.2",
            "expected_executable_sha256": (
                "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
            ),
        },
        "bindings": bindings,
        "program": {
            "initial": {
                "script": initial_script,
                "script_sha256": initial_digest,
                "semantic_sha256": initial_semantic_sha256,
            },
            "edited": {
                "script": edited_script,
                "script_sha256": edited_digest,
                "semantic_sha256": edited_semantic_sha256,
            },
            "style": {
                "base_unit": 1000,
                "color_bbggrr": 0,
                "line_mode": 0,
                "version": "Equation Version 60",
                "apply_to": 0,
                "font_name": "HancomEQN",
            },
        },
        "policy": {
            "disposable_blank_document_only": True,
            "execute_capabilities": ["eq.insert_native", "eq.edit_native"],
            "readback_capability": "eq.roundtrip_readback",
            "readback_method": "get_default_without_execute",
            "save_reopen_required": True,
            "timeout_seconds": 180,
            "no_fallback_after_possible_effect": True,
            "computer_use_click_or_type": False,
        },
    }
    request_bytes = canonical_bytes(request)
    if len(request_bytes) > MAX_OUTPUT_BYTES:
        raise ProbeBuildError("request exceeds output bound")
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "request_id": request_id,
        "request_sha256": sha256(request_bytes),
        "source_records_sha256": source_records_sha256,
        "binding_set_sha256": binding_set_sha256,
        "harness": harness,
        "action_binding_count": 3,
        "item_binding_count": len(ITEM_RECORD_IDS),
        "capabilities": [
            "eq.edit_native",
            "eq.insert_native",
            "eq.roundtrip_readback",
        ],
        "program": {
            "initial_script_sha256": initial_digest,
            "initial_script_bytes": initial_bytes,
            "initial_semantic_sha256": initial_semantic_sha256,
            "edited_script_sha256": edited_digest,
            "edited_script_bytes": edited_bytes,
            "edited_semantic_sha256": edited_semantic_sha256,
        },
        "privacy": {
            "restricted_request": True,
            "raw_action_identifiers_present": False,
            "raw_parameter_identifiers_present": False,
            "script_values_present": False,
            "absolute_paths_present": False,
        },
        "runtime": "not_run",
        "production": False,
    }
    return request, receipt


def publish_no_overwrite(path: Path, value: Any) -> None:
    data = canonical_bytes(value)
    if len(data) > MAX_OUTPUT_BYTES:
        raise ProbeBuildError("output exceeds finite bound")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-records", type=Path, default=SOURCE_RECORDS)
    parser.add_argument(
        "--expected-source-records-sha256",
        default=EXPECTED_SOURCE_RECORDS_SHA256,
    )
    parser.add_argument("--initial-script", required=True)
    parser.add_argument("--initial-script-sha256", required=True)
    parser.add_argument("--initial-semantic-sha256", required=True)
    parser.add_argument("--edited-script", required=True)
    parser.add_argument("--edited-script-sha256", required=True)
    parser.add_argument("--edited-semantic-sha256", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    try:
        _, records = load_source_records(
            arguments.source_records,
            arguments.expected_source_records_sha256,
        )
        request, receipt = build_request(
            records,
            arguments.expected_source_records_sha256,
            arguments.initial_script,
            arguments.initial_script_sha256,
            arguments.initial_semantic_sha256,
            arguments.edited_script,
            arguments.edited_script_sha256,
            arguments.edited_semantic_sha256,
        )
        directory = require_private_output(arguments.output_directory)
        if directory.name != request["request_id"]:
            raise ProbeBuildError("output directory does not match deterministic request identity")
        publish_no_overwrite(directory / "request.json", request)
        publish_no_overwrite(directory / "plan-receipt.json", receipt)
    except (OSError, ProbeBuildError) as error:
        print(f"P07_EQUATION_AUTOMATION_PROBE_BUILD_FAILED {error}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
