#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import unicodedata

from jsonschema import Draft202012Validator, FormatChecker
import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.build_candidates import load_source_lock
from tools.p02.extract_help import (
    ExtractionError,
    publish_no_overwrite,
    read_regular_file,
    resolve_output,
)
from tools.p02.review_capabilities import (
    CATALOG_SCHEMA_PATH as REVIEWED_CATALOG_SCHEMA_PATH,
    load_matrix,
)
from tools.p02.validate_source_records import SCHEMA_PATH as SOURCE_RECORD_SCHEMA_PATH
from tools.p02.validate_source_records import semantic_errors

BINDING_SCHEMA_PATH = (
    REPOSITORY_ROOT
    / "protocol"
    / "json-schema"
    / "automation-binding-registry-v1.schema.json"
)
TARGET_PROFILE_SCHEMA_PATH = REPOSITORY_ROOT / "specs" / "target-profile.schema.json"
GENERATOR_ID = "target-automation-binding-generator"
GENERATOR_VERSION = "0.1.0"
MAX_REVIEWED_CATALOG_BYTES = 128 * 1024 * 1024
MAX_AUTOMATION_RECORDS_BYTES = 16 * 1024 * 1024
MAX_TARGET_PROFILE_BYTES = 2 * 1024 * 1024
REQUIRED_SUPPORT_LEVELS = {"AUTOMATION_FULL", "HYBRID"}


@dataclass(frozen=True)
class BindingConfig:
    source_lock: Path
    automation_records: Path
    automation_records_sha256: str
    reviewed_catalog: Path
    reviewed_catalog_sha256: str
    matrix: Path
    matrix_sha256: str
    expected_matrix_count: int
    target_profile: Path
    target_profile_sha256: str
    expected_profile_id: str
    expected_exact_build: str
    expected_locale: str
    expected_architecture: str
    expected_automation_release_state: str
    output_root: Path
    output_relative: str


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_sha256(value: str, label: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ExtractionError(f"{label} expected SHA-256 is malformed")


def parse_json(content: bytes, label: str) -> object:
    try:
        return json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExtractionError(f"{label} is not valid UTF-8 JSON: {error}") from error


def schema_violations(value: object, schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return [
        error.message
        for error in Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(value)
    ]


def read_locked(path: Path, expected_sha256: str, maximum: int, label: str) -> bytes:
    validate_sha256(expected_sha256, label)
    content = read_regular_file(path, maximum)
    actual = sha256_bytes(content)
    if actual != expected_sha256:
        raise ExtractionError(
            f"{label} SHA-256 mismatch: expected {expected_sha256}, actual {actual}"
        )
    return content


def load_reviewed_catalog(path: Path, expected_sha256: str) -> tuple[bytes, dict]:
    content = read_locked(
        path, expected_sha256, MAX_REVIEWED_CATALOG_BYTES, "reviewed catalog"
    )
    value = parse_json(content, "reviewed catalog")
    if not isinstance(value, dict):
        raise ExtractionError("reviewed catalog root must be an object")
    violations = schema_violations(value, REVIEWED_CATALOG_SCHEMA_PATH)
    if violations:
        raise ExtractionError("reviewed catalog schema invalid: " + "; ".join(violations[:20]))
    if value["runtime_qualification"]["state"] != "unverified":
        raise ExtractionError("reviewed catalog unexpectedly claims runtime qualification")
    if value["coverage"]["unresolved_node_count"] != 0:
        raise ExtractionError("reviewed catalog contains unresolved nodes")
    return content, value


def load_automation_records(
    path: Path,
    expected_sha256: str,
    source_lock_id: str,
    source_entries: dict[str, dict],
) -> tuple[bytes, list[dict], bool]:
    content = read_locked(
        path, expected_sha256, MAX_AUTOMATION_RECORDS_BYTES, "automation records"
    )
    value = parse_json(content, "automation records")
    if not isinstance(value, list) or not value or len(value) > 100_000:
        raise ExtractionError("automation records root/cardinality is invalid")
    schema = json.loads(SOURCE_RECORD_SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    seen_ids: set[str] = set()
    ordinals: list[int] = []
    restricted = False
    for index, record in enumerate(value):
        if not isinstance(record, dict):
            raise ExtractionError(f"automation record {index} is not an object")
        violations = [error.message for error in validator.iter_errors(record)]
        violations.extend(semantic_errors(record))
        if violations:
            raise ExtractionError(
                f"automation record {index} invalid: " + "; ".join(violations[:20])
            )
        if record["source_lock_id"] != source_lock_id:
            raise ExtractionError(f"automation record {index} source_lock_id mismatch")
        if record["source_kind"] not in {
            "action_table",
            "parameter_table",
            "automation_object",
            "automation_event",
        }:
            raise ExtractionError(f"automation record {index} has an invalid source_kind")
        record_id = record["record_id"]
        if record_id in seen_ids:
            raise ExtractionError(f"automation records duplicate record_id: {record_id}")
        seen_ids.add(record_id)
        ordinals.append(record["extraction"]["record_ordinal"])
        source_entry = source_entries.get(record["source_id"])
        if source_entry is None or source_entry["sha256"] != record["source_sha256"]:
            raise ExtractionError(f"automation record {index} source identity mismatch")
        restricted = restricted or source_entry["license_state"] == "restricted"
    if ordinals != list(range(len(value))):
        raise ExtractionError("automation record ordinals are not contiguous in file order")
    return content, value, restricted


def load_target_profile(
    path: Path,
    expected_sha256: str,
    config: BindingConfig,
) -> tuple[bytes, dict]:
    content = read_locked(
        path, expected_sha256, MAX_TARGET_PROFILE_BYTES, "target profile"
    )
    try:
        value = yaml.safe_load(content.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as error:
        raise ExtractionError(f"target profile is not valid UTF-8 YAML: {error}") from error
    if not isinstance(value, dict):
        raise ExtractionError("target profile root must be an object")
    violations = schema_violations(value, TARGET_PROFILE_SCHEMA_PATH)
    if violations:
        raise ExtractionError("target profile schema invalid: " + "; ".join(violations[:20]))
    expected = {
        "profile_id": config.expected_profile_id,
        "exact_build": config.expected_exact_build,
        "locale": config.expected_locale,
    }
    for field, expected_value in expected.items():
        if str(value.get(field)) != expected_value:
            raise ExtractionError(f"target profile exact identity mismatch: {field}")
    constraints = value.get("constraints")
    if not isinstance(constraints, dict):
        raise ExtractionError("target profile constraints are missing")
    if constraints.get("executable_architecture") != config.expected_architecture:
        raise ExtractionError("target profile exact identity mismatch: architecture")
    if (
        constraints.get("desktop_automation_release_state")
        != config.expected_automation_release_state
    ):
        raise ExtractionError("target profile automation release state mismatch")
    if value.get("license_state") != "approved":
        raise ExtractionError("target profile license_state is not approved")
    if constraints.get("runtime_probe_scope") != "exact_identity_on_current_development_pc":
        raise ExtractionError("target profile runtime probe scope is not current-PC exact identity")
    if constraints.get("production_release_state") != "disabled":
        raise ExtractionError("target profile production route must remain disabled")
    return content, value


def validate_raw_identifier(value: str, label: str) -> None:
    if not value or len(value) > 512:
        raise ExtractionError(f"{label} length is invalid")
    if any(unicodedata.category(character) in {"Cc", "Cf", "Cs"} for character in value):
        raise ExtractionError(f"{label} contains prohibited control/format characters")


def parameter_set_from_record(record: dict) -> tuple[str | None, str]:
    parameters = record["parameters"]
    if len(parameters) != 1 or parameters[0]["declared_type"] != "ParameterSet ID":
        raise ExtractionError(
            f"action record has no singular documented ParameterSet signal: {record['record_id']}"
        )
    raw = parameters[0]["original_name"]
    validate_raw_identifier(raw, "ParameterSet identifier")
    if raw == "-":
        return None, "source_declares_none"
    return raw, "documented_candidate"


def make_source_refs(
    disposition: dict,
    record: dict,
    reviewed_catalog_sha256: str,
    automation_records_sha256: str,
) -> list[dict]:
    return [
        {
            "kind": "reviewed_catalog_node",
            "artifact_sha256": reviewed_catalog_sha256,
            "node_id": disposition["node_id"],
            "record_id": disposition["record_id"],
            "source_id": disposition["source_id"],
            "source_sha256": None,
        },
        {
            "kind": "automation_source_record",
            "artifact_sha256": automation_records_sha256,
            "node_id": None,
            "record_id": record["record_id"],
            "source_id": record["source_id"],
            "source_sha256": record["source_sha256"],
        },
    ]


def build_binding(
    row: dict,
    disposition: dict | None,
    automation_by_id: dict[str, dict],
    target: dict,
    reviewed_catalog_sha256: str,
    automation_records_sha256: str,
) -> dict:
    capability_id = row["capability_id"]
    binding = {
        "binding_key": (
            f"{capability_id}@{target['profile_id']}/{target['exact_build']}/{target['locale']}"
        ),
        "feature_id": row["feature_id"],
        "capability_id": capability_id,
        "scope_class": row["scope_class"],
        "support_level": row["support_level"],
        "preferred_backend": row["preferred_backend"],
        "fallback_backend": row["fallback_backend"],
        "target_profile_id": target["profile_id"],
        "runtime_support_state": "unverified",
        "routing_enabled": False,
        "probe": {
            "state": "not_run",
            "fixture_id": None,
            "pre_snapshot": None,
            "post_snapshot": None,
            "expected_effect": capability_id,
            "modal_risk": "unknown",
            "external_side_effect_risk": "unknown",
        },
    }
    if disposition is None:
        return {
            **binding,
            "status": "unavailable_with_reason",
            "unavailable_reason": "no_reviewed_action_mapping",
            "invocation": None,
            "source_refs": [],
            "raw_identifiers_present": False,
        }
    record = automation_by_id.get(disposition["record_id"])
    if record is None:
        raise ExtractionError(
            f"reviewed action mapping record is missing: {disposition['record_id']}"
        )
    if (
        record["source_kind"] != "action_table"
        or record["source_id"] != disposition["source_id"]
    ):
        raise ExtractionError(
            f"reviewed action mapping source identity mismatch: {disposition['node_id']}"
        )
    action_id = record["original_name"]
    validate_raw_identifier(action_id, "Action identifier")
    parameter_set_id, parameter_set_state = parameter_set_from_record(record)
    return {
        **binding,
        "status": "candidate_unverified",
        "unavailable_reason": None,
        "invocation": {
            "kind": "action",
            "action_id": action_id,
            "parameter_set_id": parameter_set_id,
            "parameter_set_state": parameter_set_state,
            "parameter_map": [],
            "parameter_map_state": "pending_runtime_probe",
        },
        "source_refs": make_source_refs(
            disposition,
            record,
            reviewed_catalog_sha256,
            automation_records_sha256,
        ),
        "raw_identifiers_present": True,
    }


def build_registry(
    source_lock_id: str,
    automation_records: list[dict],
    automation_records_sha256: str,
    reviewed_catalog: dict,
    reviewed_catalog_sha256: str,
    matrix_rows: list[dict],
    matrix_sha256: str,
    target_profile: dict,
    target_profile_sha256: str,
    architecture: str,
    automation_restricted: bool,
) -> dict:
    if reviewed_catalog["source_lock_id"] != source_lock_id:
        raise ExtractionError("reviewed catalog source_lock_id mismatch")
    if reviewed_catalog["canonical_matrix"]["sha256"] != matrix_sha256:
        raise ExtractionError("reviewed catalog canonical matrix SHA-256 mismatch")
    graph_inputs = set(reviewed_catalog["candidate_graph"]["input_sha256"])
    if automation_records_sha256 not in graph_inputs:
        raise ExtractionError("automation records are not an input to the reviewed catalog")
    automation_by_id = {record["record_id"]: record for record in automation_records}
    mapped_by_capability: dict[str, dict] = {}
    for disposition in reviewed_catalog["node_dispositions"]:
        if disposition["status"] != "mapped":
            continue
        capability = disposition["capability"]
        capability_id = capability["capability_id"]
        if capability_id in mapped_by_capability:
            raise ExtractionError(
                f"multiple reviewed nodes map to one capability: {capability_id}"
            )
        mapped_by_capability[capability_id] = disposition
    required_rows = sorted(
        (
            row
            for row in matrix_rows
            if row["support_level"] in REQUIRED_SUPPORT_LEVELS
        ),
        key=lambda row: row["capability_id"],
    )
    matrix_by_capability = {row["capability_id"]: row for row in matrix_rows}
    for capability_id, disposition in mapped_by_capability.items():
        row = matrix_by_capability.get(capability_id)
        if row is None:
            raise ExtractionError(f"reviewed catalog maps unknown capability: {capability_id}")
        capability = disposition["capability"]
        for field in (
            "feature_id",
            "scope_class",
            "support_level",
            "preferred_backend",
            "fallback_backend",
        ):
            if capability[field] != row[field]:
                raise ExtractionError(
                    f"reviewed capability projection differs from matrix: {capability_id}/{field}"
                )
    target = {
        "profile_id": target_profile["profile_id"],
        "product": target_profile["product"],
        "major_release": str(target_profile["major_release"]),
        "exact_build": target_profile["exact_build"],
        "locale": target_profile["locale"],
        "architecture": architecture,
        "profile_sha256": target_profile_sha256,
        "license_state": target_profile["license_state"],
        "automation_release_state": target_profile["constraints"][
            "desktop_automation_release_state"
        ],
        "image_digest": target_profile.get("image_digest"),
        "routing_enabled": False,
    }
    bindings = [
        build_binding(
            row,
            mapped_by_capability.get(row["capability_id"]),
            automation_by_id,
            target,
            reviewed_catalog_sha256,
            automation_records_sha256,
        )
        for row in required_rows
    ]
    capability_ids = [binding["capability_id"] for binding in bindings]
    if len(capability_ids) != len(set(capability_ids)):
        raise ExtractionError("binding registry contains duplicate capabilities")
    candidate_count = sum(
        binding["status"] == "candidate_unverified" for binding in bindings
    )
    restricted_derivative = (
        reviewed_catalog["restricted_derivative"] or automation_restricted
    )
    registry = {
        "schema_version": "hwpx-agent.automation-binding-registry/v1",
        "source_lock_id": source_lock_id,
        "generator": {
            "generator_id": GENERATOR_ID,
            "generator_version": GENERATOR_VERSION,
            "raw_identifier_policy": "restricted_private_only",
            "runtime_execution_performed": False,
        },
        "restricted_derivative": restricted_derivative,
        "target": target,
        "inputs": {
            "reviewed_catalog_sha256": reviewed_catalog_sha256,
            "canonical_matrix_sha256": matrix_sha256,
            "automation_records_sha256": automation_records_sha256,
        },
        "runtime_qualification": {
            "state": "not_run",
            "probe_required": True,
            "qualified_binding_count": 0,
        },
        "bindings": bindings,
        "coverage": {
            "required_capability_count": len(required_rows),
            "automation_full_count": sum(
                row["support_level"] == "AUTOMATION_FULL" for row in required_rows
            ),
            "hybrid_count": sum(
                row["support_level"] == "HYBRID" for row in required_rows
            ),
            "binding_count": len(bindings),
            "candidate_unverified_count": candidate_count,
            "unavailable_count": len(bindings) - candidate_count,
            "unresolved_count": 0,
            "duplicate_capability_count": 0,
            "raw_identifier_binding_count": sum(
                binding["raw_identifiers_present"] for binding in bindings
            ),
            "runtime_qualified_count": 0,
            "routing_enabled_count": 0,
        },
    }
    violations = schema_violations(registry, BINDING_SCHEMA_PATH)
    if violations:
        raise ExtractionError("binding registry schema invalid: " + "; ".join(violations[:20]))
    expected_support_counts = Counter(
        row["support_level"] for row in required_rows
    )
    if registry["coverage"]["automation_full_count"] != expected_support_counts[
        "AUTOMATION_FULL"
    ] or registry["coverage"]["hybrid_count"] != expected_support_counts["HYBRID"]:
        raise ExtractionError("binding registry support coverage mismatch")
    return registry


def serialize_registry(registry: dict) -> bytes:
    return (
        json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def run(config: BindingConfig) -> dict:
    source_lock_content = read_regular_file(config.source_lock, 8 * 1024 * 1024)
    source_lock_id, source_entries = load_source_lock(config.source_lock)
    reviewed_content, reviewed_catalog = load_reviewed_catalog(
        config.reviewed_catalog, config.reviewed_catalog_sha256
    )
    matrix_content, matrix_rows = load_matrix(
        config.matrix, config.matrix_sha256, config.expected_matrix_count
    )
    automation_content, automation_records, automation_restricted = (
        load_automation_records(
            config.automation_records,
            config.automation_records_sha256,
            source_lock_id,
            source_entries,
        )
    )
    profile_content, target_profile = load_target_profile(
        config.target_profile, config.target_profile_sha256, config
    )
    if target_profile.get("source_lock_id") != source_lock_id:
        raise ExtractionError("target profile source_lock_id mismatch")
    registry = build_registry(
        source_lock_id,
        automation_records,
        config.automation_records_sha256,
        reviewed_catalog,
        config.reviewed_catalog_sha256,
        matrix_rows,
        config.matrix_sha256,
        target_profile,
        config.target_profile_sha256,
        config.expected_architecture,
        automation_restricted,
    )
    if registry["restricted_derivative"] and os.path.normcase(
        str(config.output_root.absolute())
    ) != os.path.normcase(
        str((REPOSITORY_ROOT / "implementation" / "p02" / "evidence").absolute())
    ):
        raise ExtractionError(
            "restricted binding registry may publish only to implementation/p02/evidence"
        )
    locked = (
        (config.source_lock, source_lock_content, 8 * 1024 * 1024, "source lock"),
        (
            config.reviewed_catalog,
            reviewed_content,
            MAX_REVIEWED_CATALOG_BYTES,
            "reviewed catalog",
        ),
        (config.matrix, matrix_content, 8 * 1024 * 1024, "canonical matrix"),
        (
            config.automation_records,
            automation_content,
            MAX_AUTOMATION_RECORDS_BYTES,
            "automation records",
        ),
        (
            config.target_profile,
            profile_content,
            MAX_TARGET_PROFILE_BYTES,
            "target profile",
        ),
    )
    for path, original, maximum, label in locked:
        if read_regular_file(path, maximum) != original:
            raise ExtractionError(f"{label} changed during binding generation")
    payload = serialize_registry(registry)
    output = resolve_output(config.output_root, config.output_relative)
    publish_no_overwrite(output, payload)
    return {
        "schema_version": "hwpx-agent.binding-generation-receipt/v1",
        "source_lock_id": source_lock_id,
        "target_profile_id": target_profile["profile_id"],
        "target_exact_build": target_profile["exact_build"],
        "target_locale": target_profile["locale"],
        "target_architecture": config.expected_architecture,
        "restricted_derivative": registry["restricted_derivative"],
        "coverage": registry["coverage"],
        "output_relative": config.output_relative,
        "output_sha256": sha256_bytes(payload),
        "runtime_execution_performed": False,
        "routing_enabled": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-lock", type=Path, required=True)
    parser.add_argument("--automation-records", type=Path, required=True)
    parser.add_argument("--automation-records-sha256", required=True)
    parser.add_argument("--reviewed-catalog", type=Path, required=True)
    parser.add_argument("--reviewed-catalog-sha256", required=True)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--matrix-sha256", required=True)
    parser.add_argument("--expected-matrix-count", type=int, required=True)
    parser.add_argument("--target-profile", type=Path, required=True)
    parser.add_argument("--target-profile-sha256", required=True)
    parser.add_argument("--expected-profile-id", required=True)
    parser.add_argument("--expected-exact-build", required=True)
    parser.add_argument("--expected-locale", required=True)
    parser.add_argument("--expected-architecture", choices=["x86", "x64", "arm64"], required=True)
    parser.add_argument("--expected-automation-release-state", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--output-relative", required=True)
    arguments = parser.parse_args()
    try:
        receipt = run(
            BindingConfig(
                source_lock=arguments.source_lock,
                automation_records=arguments.automation_records,
                automation_records_sha256=arguments.automation_records_sha256,
                reviewed_catalog=arguments.reviewed_catalog,
                reviewed_catalog_sha256=arguments.reviewed_catalog_sha256,
                matrix=arguments.matrix,
                matrix_sha256=arguments.matrix_sha256,
                expected_matrix_count=arguments.expected_matrix_count,
                target_profile=arguments.target_profile,
                target_profile_sha256=arguments.target_profile_sha256,
                expected_profile_id=arguments.expected_profile_id,
                expected_exact_build=arguments.expected_exact_build,
                expected_locale=arguments.expected_locale,
                expected_architecture=arguments.expected_architecture,
                expected_automation_release_state=arguments.expected_automation_release_state,
                output_root=arguments.output_root,
                output_relative=arguments.output_relative,
            )
        )
    except ExtractionError as error:
        print(
            json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
