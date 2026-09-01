#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator, FormatChecker

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from tools.p02.build_bindings import (
    BINDING_SCHEMA_PATH,
    REQUIRED_SUPPORT_LEVELS,
    BindingConfig,
    load_automation_records,
    load_reviewed_catalog,
    load_target_profile,
)
from tools.p02.build_candidates import load_source_lock
from tools.p02.extract_help import ExtractionError, read_regular_file
from tools.p02.review_capabilities import load_matrix


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_output(content: bytes, errors: list[str]) -> dict:
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        errors.append(f"binding registry is not valid UTF-8 JSON: {error}")
        return {}
    if not isinstance(value, dict):
        errors.append("binding registry root is not an object")
        return {}
    schema = json.loads(BINDING_SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors.extend(
        f"binding registry schema: {error.message}"
        for error in Draft202012Validator(
            schema, format_checker=FormatChecker()
        ).iter_errors(value)
    )
    return value


def expected_target(profile: dict, profile_sha256: str, architecture: str) -> dict:
    return {
        "profile_id": profile["profile_id"],
        "product": profile["product"],
        "major_release": str(profile["major_release"]),
        "exact_build": profile["exact_build"],
        "locale": profile["locale"],
        "architecture": architecture,
        "profile_sha256": profile_sha256,
        "license_state": profile["license_state"],
        "automation_release_state": profile["constraints"][
            "desktop_automation_release_state"
        ],
        "image_digest": profile.get("image_digest"),
        "routing_enabled": False,
    }


def common_binding(row: dict, target: dict) -> dict:
    capability_id = row["capability_id"]
    return {
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


def expected_candidate(
    row: dict,
    target: dict,
    disposition: dict,
    record: dict,
    reviewed_sha256: str,
    automation_sha256: str,
) -> dict:
    parameters = record.get("parameters")
    if (
        not isinstance(parameters, list)
        or len(parameters) != 1
        or parameters[0].get("declared_type") != "ParameterSet ID"
    ):
        raise ExtractionError(
            f"mapped action lacks singular ParameterSet signal: {record.get('record_id')}"
        )
    raw_parameter_set = parameters[0].get("original_name")
    if not isinstance(raw_parameter_set, str):
        raise ExtractionError("mapped action ParameterSet signal is not a string")
    parameter_set_id = None if raw_parameter_set == "-" else raw_parameter_set
    parameter_set_state = (
        "source_declares_none"
        if parameter_set_id is None
        else "documented_candidate"
    )
    return {
        **common_binding(row, target),
        "status": "candidate_unverified",
        "unavailable_reason": None,
        "invocation": {
            "kind": "action",
            "action_id": record["original_name"],
            "parameter_set_id": parameter_set_id,
            "parameter_set_state": parameter_set_state,
            "parameter_map": [],
            "parameter_map_state": "pending_runtime_probe",
        },
        "source_refs": [
            {
                "kind": "reviewed_catalog_node",
                "artifact_sha256": reviewed_sha256,
                "node_id": disposition["node_id"],
                "record_id": disposition["record_id"],
                "source_id": disposition["source_id"],
                "source_sha256": None,
            },
            {
                "kind": "automation_source_record",
                "artifact_sha256": automation_sha256,
                "node_id": None,
                "record_id": record["record_id"],
                "source_id": record["source_id"],
                "source_sha256": record["source_sha256"],
            },
        ],
        "raw_identifiers_present": True,
    }


def expected_unavailable(row: dict, target: dict) -> dict:
    return {
        **common_binding(row, target),
        "status": "unavailable_with_reason",
        "unavailable_reason": "no_reviewed_action_mapping",
        "invocation": None,
        "source_refs": [],
        "raw_identifiers_present": False,
    }


def verify(output_path: Path, config: BindingConfig) -> dict:
    errors: list[str] = []
    output_content = read_regular_file(output_path, 128 * 1024 * 1024)
    registry = parse_output(output_content, errors)
    try:
        source_lock_id, source_entries = load_source_lock(config.source_lock)
        _, reviewed = load_reviewed_catalog(
            config.reviewed_catalog, config.reviewed_catalog_sha256
        )
        _, rows = load_matrix(
            config.matrix, config.matrix_sha256, config.expected_matrix_count
        )
        _, automation, automation_restricted = load_automation_records(
            config.automation_records,
            config.automation_records_sha256,
            source_lock_id,
            source_entries,
        )
        _, profile = load_target_profile(
            config.target_profile, config.target_profile_sha256, config
        )
    except ExtractionError as error:
        errors.append(f"locked input validation: {error}")
        return {
            "schema_version": "hwpx-agent.binding-registry-verification/v1",
            "errors": errors,
            "output_sha256": sha256_bytes(output_content),
        }
    if profile.get("source_lock_id") != source_lock_id:
        errors.append("target profile source_lock_id mismatch")
    if reviewed.get("source_lock_id") != source_lock_id:
        errors.append("reviewed catalog source_lock_id mismatch")
    if reviewed.get("canonical_matrix", {}).get("sha256") != config.matrix_sha256:
        errors.append("reviewed catalog canonical matrix reference mismatch")
    if config.automation_records_sha256 not in set(
        reviewed.get("candidate_graph", {}).get("input_sha256", [])
    ):
        errors.append("reviewed catalog does not reference automation records")

    target = expected_target(profile, config.target_profile_sha256, config.expected_architecture)
    required_rows = sorted(
        [row for row in rows if row["support_level"] in REQUIRED_SUPPORT_LEVELS],
        key=lambda row: row["capability_id"],
    )
    matrix_by_capability = {row["capability_id"]: row for row in rows}
    mapped: dict[str, dict] = {}
    for disposition in reviewed.get("node_dispositions", []):
        if disposition.get("status") != "mapped":
            continue
        capability = disposition.get("capability")
        if not isinstance(capability, dict):
            errors.append("mapped reviewed node lacks capability")
            continue
        capability_id = capability.get("capability_id")
        if capability_id in mapped:
            errors.append(f"duplicate reviewed capability mapping: {capability_id}")
        mapped[str(capability_id)] = disposition
        row = matrix_by_capability.get(str(capability_id))
        if row is None:
            errors.append(f"reviewed mapping absent from matrix: {capability_id}")
        elif any(
            capability.get(field) != row[field]
            for field in (
                "feature_id",
                "scope_class",
                "support_level",
                "preferred_backend",
                "fallback_backend",
            )
        ):
            errors.append(f"reviewed mapping projection mismatch: {capability_id}")
    automation_by_id = {record["record_id"]: record for record in automation}
    expected_bindings: list[dict] = []
    for row in required_rows:
        disposition = mapped.get(row["capability_id"])
        if disposition is None:
            expected_bindings.append(expected_unavailable(row, target))
            continue
        record = automation_by_id.get(disposition["record_id"])
        if record is None:
            errors.append(
                f"mapped automation record missing: {disposition['record_id']}"
            )
            expected_bindings.append(expected_unavailable(row, target))
            continue
        if (
            record.get("source_kind") != "action_table"
            or record.get("source_id") != disposition.get("source_id")
        ):
            errors.append(f"mapped automation source mismatch: {row['capability_id']}")
        try:
            expected_bindings.append(
                expected_candidate(
                    row,
                    target,
                    disposition,
                    record,
                    config.reviewed_catalog_sha256,
                    config.automation_records_sha256,
                )
            )
        except ExtractionError as error:
            errors.append(str(error))

    actual_bindings = registry.get("bindings", []) if registry else []
    actual_ids = [
        binding.get("capability_id")
        for binding in actual_bindings
        if isinstance(binding, dict)
    ]
    expected_ids = [binding["capability_id"] for binding in expected_bindings]
    if len(actual_ids) != len(set(actual_ids)):
        errors.append("binding registry capability IDs are duplicated")
    if actual_ids != expected_ids:
        errors.append("binding registry capability order/coverage mismatch")
    for index, expected in enumerate(expected_bindings):
        if index >= len(actual_bindings):
            break
        if actual_bindings[index] != expected:
            errors.append(f"binding mismatch: {expected['capability_id']}")

    candidate_count = sum(
        binding["status"] == "candidate_unverified" for binding in expected_bindings
    )
    restricted_derivative = (
        bool(reviewed.get("restricted_derivative")) or automation_restricted
    )
    support_counts = Counter(row["support_level"] for row in required_rows)
    expected_coverage = {
        "required_capability_count": len(required_rows),
        "automation_full_count": support_counts["AUTOMATION_FULL"],
        "hybrid_count": support_counts["HYBRID"],
        "binding_count": len(expected_bindings),
        "candidate_unverified_count": candidate_count,
        "unavailable_count": len(expected_bindings) - candidate_count,
        "unresolved_count": 0,
        "duplicate_capability_count": 0,
        "raw_identifier_binding_count": candidate_count,
        "runtime_qualified_count": 0,
        "routing_enabled_count": 0,
    }
    expected_top = {
        "schema_version": "hwpx-agent.automation-binding-registry/v1",
        "source_lock_id": source_lock_id,
        "generator": {
            "generator_id": "target-automation-binding-generator",
            "generator_version": "0.1.0",
            "raw_identifier_policy": "restricted_private_only",
            "runtime_execution_performed": False,
        },
        "restricted_derivative": restricted_derivative,
        "target": target,
        "inputs": {
            "reviewed_catalog_sha256": config.reviewed_catalog_sha256,
            "canonical_matrix_sha256": config.matrix_sha256,
            "automation_records_sha256": config.automation_records_sha256,
        },
        "runtime_qualification": {
            "state": "not_run",
            "probe_required": True,
            "qualified_binding_count": 0,
        },
        "coverage": expected_coverage,
    }
    for field, expected in expected_top.items():
        if registry.get(field) != expected:
            errors.append(f"binding registry top-level mismatch: {field}")

    return {
        "schema_version": "hwpx-agent.binding-registry-verification/v1",
        "errors": errors,
        "output_sha256": sha256_bytes(output_content),
        "reviewed_catalog_sha256": config.reviewed_catalog_sha256,
        "canonical_matrix_sha256": config.matrix_sha256,
        "automation_records_sha256": config.automation_records_sha256,
        "target_profile_sha256": config.target_profile_sha256,
        "binding_count": len(actual_bindings),
        "candidate_unverified_count": sum(
            isinstance(binding, dict)
            and binding.get("status") == "candidate_unverified"
            for binding in actual_bindings
        ),
        "unavailable_count": sum(
            isinstance(binding, dict)
            and binding.get("status") == "unavailable_with_reason"
            for binding in actual_bindings
        ),
        "runtime_qualified_count": 0,
        "routing_enabled_count": 0,
        "raw_identifier_values_emitted_in_receipt": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
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
    arguments = parser.parse_args()
    config = BindingConfig(
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
        output_root=arguments.output.parent,
        output_relative=arguments.output.name,
    )
    try:
        result = verify(arguments.output, config)
    except ExtractionError as error:
        print(
            json.dumps({"state": "failed", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["errors"] else 0
if __name__ == "__main__":
    raise SystemExit(main())
