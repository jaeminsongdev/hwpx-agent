#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

try:
    from tools.p06 import table_conformance as conformance
    from tools.p06.build_table_conformance_report import (
        DEFAULT_CATALOG,
        DEFAULT_CONTRACTS,
        DEFAULT_EVIDENCE,
        DEFAULT_PROJECTION,
    )
except ModuleNotFoundError:
    import table_conformance as conformance  # type: ignore[no-redef]
    from build_table_conformance_report import (  # type: ignore[no-redef]
        DEFAULT_CATALOG,
        DEFAULT_CONTRACTS,
        DEFAULT_EVIDENCE,
        DEFAULT_PROJECTION,
    )


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-conformance-v1.json"
REPORT = "implementation/p06/evidence/conformance/p06-table-conformance.current-2020.v1.json"
POLICY = "implementation/p06/P06-09_TABLE_CONFORMANCE_POLICY.md"
HUMAN_REPORT = "implementation/p06/P06-09_TABLE_CONFORMANCE_REPORT.md"
MIGRATION = "protocol/migrations/p06-table-conformance-v0-to-v1.md"
SCHEMA_CATALOG = "protocol/generated/typescript/schema-catalog-v5.json"
CATALOG_MIGRATION = "protocol/migrations/catalog-v4-to-v5.md"
CATALOG_BASELINE = "protocol/baseline/catalog-v5.lock.json"
PRIVATE_REGISTRY = "implementation/p02/evidence/bindings/automation-bindings.2020.v1.final.json"
SCHEMAS = (
    "protocol/json-schema/p06-table-automation-projection-v1.schema.json",
    "protocol/json-schema/p06-table-conformance-evidence-v1.schema.json",
    "protocol/json-schema/p06-table-conformance-report-v1.schema.json",
)
EXPECTED_SOURCE_PATHS = {
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/08_testing/03_feature_conformance.md",
    "docs/09_roadmap/P06_table_engine.md",
    "specs/feature-coverage-matrix.json",
    "specs/capability-contracts.generated.json",
    "implementation/p06/p06-09-current-2020-automation-projection.json",
    "implementation/p06/p06-09-current-2020-direct-evidence.json",
    REPORT,
    POLICY,
    HUMAN_REPORT,
    MIGRATION,
    SCHEMA_CATALOG,
    CATALOG_MIGRATION,
    CATALOG_BASELINE,
    *SCHEMAS,
    "protocol/generated/typescript/src/schema-models.ts",
    "protocol/generated/typescript/src/schema-models.test.ts",
    "tools/xtask/src/main.rs",
    "tools/p06/table_conformance.py",
    "tools/p06/build_table_conformance_report.py",
    "tools/p06/project_table_automation_bindings.py",
    "tools/p06/tests/test_table_conformance.py",
    "tools/p06/tests/test_table_conformance_contract.py",
    "tools/p06/validate_table_conformance_contract.py",
}


def add_error(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def load_contract(root: Path) -> dict[str, Any]:
    value, _ = conformance.load_json_file(root, CONTRACT, 512_000)
    if not isinstance(value, dict):
        raise conformance.ConformanceError("contract_shape")
    return value


def validate_contract_shape(contract: dict[str, Any], errors: list[str]) -> None:
    expected_keys = {
        "schema_version",
        "scope",
        "target",
        "row_policy",
        "green_rule",
        "expected_current_summary",
        "source_lock_canonicalization",
        "source_locks",
        "schemas",
        "migration",
        "schema_catalog",
        "catalog_migration",
        "catalog_baseline",
        "policy",
        "human_report",
        "machine_report",
        "privacy",
        "gate_decision",
        "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.p06-table-conformance-contract/v1",
        "scope": "p06_09_current_pc_hancom_2020_fail_closed_matrix",
        "source_lock_canonicalization": "exact_file_bytes_sha256",
        "schemas": list(SCHEMAS),
        "migration": MIGRATION,
        "schema_catalog": SCHEMA_CATALOG,
        "catalog_migration": CATALOG_MIGRATION,
        "catalog_baseline": CATALOG_BASELINE,
        "policy": POLICY,
        "human_report": HUMAN_REPORT,
        "machine_report": REPORT,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            add_error(errors, key)
    try:
        conformance.exact_target(contract.get("target"))
    except conformance.ConformanceError:
        add_error(errors, "target")
    if contract.get("row_policy") != {
        "feature_ids": "exactly_TABLE_001_through_TABLE_061_once_in_order",
        "missing_direct_evidence": "cataloged_non_green",
        "missing_automation_binding": "non_green",
        "missing_differential": "non_green",
        "all_rows_required": 61,
    }:
        add_error(errors, "row_policy")
    if contract.get("green_rule") != [
        "direct_hwpx_oracle_verified",
        "all_contract_validations_passed",
        "all_required_fixture_classes_passed",
        "negative_passed",
        "rollback_or_retry_passed",
        "automation_binding_verified_current_target",
        "automation_runtime_verified_current_target",
        "direct_automation_differential_exact_match",
    ]:
        add_error(errors, "green_rule")
    if contract.get("expected_current_summary") != {
        "required_rows": 61,
        "green_rows": 0,
        "non_green_rows": 61,
        "direct_stage_counts": {
            "cataloged": 33,
            "unit_passed": 13,
            "integration_passed": 4,
            "oracle_verified": 11,
        },
        "automation_binding_counts": {
            "candidate_unverified": 6,
            "unavailable_with_reason": 55,
        },
        "differential_counts": {"not_run": 61},
        "required_matrix": "non_green",
    }:
        add_error(errors, "expected_current_summary")
    if contract.get("privacy") != {
        "raw_action_identifiers": False,
        "raw_parameter_identifiers": False,
        "raw_probe_values": False,
        "document_content": False,
        "absolute_private_paths": False,
    }:
        add_error(errors, "privacy")
    if contract.get("gate_decision") != {
        "matrix_engine": "component_pass",
        "current_snapshot": "pass_truthful_non_green",
        "required_matrix": "non_green",
        "p06_07": "in_progress",
        "p06_09": "in_progress",
        "p06": "in_progress",
        "product_complete": False,
    }:
        add_error(errors, "gate_decision")
    if contract.get("not_claimed") != {
        "any_release_enabled_table_capability": False,
        "p06_07_complete": False,
        "p06_09_complete": False,
        "p06_phase_complete": False,
        "arbitrary_user_document_compatibility": False,
        "other_pc_or_version": False,
        "production": False,
        "product_complete": False,
    }:
        add_error(errors, "not_claimed")


def validate_source_locks(root: Path, contract: dict[str, Any], errors: list[str]) -> int:
    locks = contract.get("source_locks")
    if not isinstance(locks, list):
        add_error(errors, "source_locks_shape")
        return 0
    declared: dict[str, str] = {}
    for item in locks:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            add_error(errors, "source_lock_shape")
            continue
        path = item.get("path")
        expected = item.get("sha256")
        if not isinstance(path, str) or path in declared \
                or not isinstance(expected, str) \
                or not conformance.SHA256_PATTERN.fullmatch(expected):
            add_error(errors, "source_lock_identity")
            continue
        declared[path] = expected
        try:
            actual = conformance.sha256_file(conformance.bounded_repo_file(root, path))
        except (OSError, conformance.ConformanceError):
            add_error(errors, "source_lock_path")
            continue
        if actual != expected:
            add_error(errors, "source_lock_digest")
    if set(declared) != EXPECTED_SOURCE_PATHS:
        add_error(errors, "source_lock_paths_exact")
    return len(declared)


def load_schemas(root: Path, errors: list[str]) -> tuple[dict[str, Any], ...]:
    output: list[dict[str, Any]] = []
    for path in SCHEMAS:
        try:
            value, _ = conformance.load_json_file(root, path, 2 * 1024 * 1024)
            if not isinstance(value, dict):
                raise conformance.ConformanceError("schema_shape")
            Draft202012Validator.check_schema(value)
            output.append(value)
        except Exception:
            add_error(errors, "schema_invalid")
    return tuple(output)


def validate_instances(
    schemas: tuple[dict[str, Any], ...],
    projection: Any,
    evidence: Any,
    report: Any,
    errors: list[str],
) -> None:
    if len(schemas) != len(SCHEMAS):
        return
    registry = Registry()
    try:
        for schema in schemas:
            registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
        for schema, instance in zip(schemas, (projection, evidence, report), strict=True):
            violations = sorted(
                Draft202012Validator(schema, registry=registry).iter_errors(instance),
                key=lambda item: list(item.absolute_path),
            )
            if violations:
                add_error(errors, "instance_schema_invalid")
    except Exception:
        add_error(errors, "instance_schema_validation_failed")


def validate_private_projection_if_available(
    root: Path,
    projection: dict[str, Any],
    errors: list[str],
) -> str:
    try:
        private_path = conformance.bounded_repo_file(root, PRIVATE_REGISTRY)
    except (OSError, conformance.ConformanceError):
        return "not_available"
    try:
        registry_bytes = private_path.read_bytes()
        registry = json.loads(
            registry_bytes.decode("utf-8"),
            object_pairs_hook=conformance.reject_duplicate_keys,
        )
        rebuilt = conformance.build_automation_projection(
            registry, conformance.sha256_bytes(registry_bytes)
        )
        if conformance.canonical_json(rebuilt) != conformance.canonical_json(projection):
            add_error(errors, "private_projection_drift")
            return "fail"
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, conformance.ConformanceError):
        add_error(errors, "private_projection_validation")
        return "fail"
    return "pass"


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_contract(root)
    except (OSError, conformance.ConformanceError):
        return result(["contract_json_or_path"], 0, "not_checked")
    validate_contract_shape(contract, errors)
    source_count = validate_source_locks(root, contract, errors)
    schemas = load_schemas(root, errors)
    try:
        projection, _ = conformance.load_json_file(root, DEFAULT_PROJECTION)
        evidence, _ = conformance.load_json_file(root, DEFAULT_EVIDENCE)
        committed_report, _ = conformance.load_json_file(root, REPORT)
        conformance.validate_projection(projection)
        conformance.validate_evidence(root, evidence)
        rebuilt_report = conformance.load_and_build(
            root,
            catalog_path=DEFAULT_CATALOG,
            contracts_path=DEFAULT_CONTRACTS,
            projection_path=DEFAULT_PROJECTION,
            evidence_path=DEFAULT_EVIDENCE,
        )
        if conformance.canonical_json(rebuilt_report) != conformance.canonical_json(committed_report):
            add_error(errors, "report_drift")
        expected = contract.get("expected_current_summary", {})
        summary = committed_report.get("summary", {}) if isinstance(committed_report, dict) else {}
        for key, value in expected.items():
            if summary.get(key) != value:
                add_error(errors, "report_summary")
        validate_instances(schemas, projection, evidence, committed_report, errors)
        private_projection = validate_private_projection_if_available(root, projection, errors)
        for raw_marker in (b'"invocation":', b'"action_id":', b'"parameter_set_id":'):
            if raw_marker in conformance.canonical_json(projection) \
                    or raw_marker in conformance.canonical_json(committed_report):
                add_error(errors, "private_identifier_leak")
    except (OSError, KeyError, TypeError, conformance.ConformanceError):
        add_error(errors, "matrix_validation")
        private_projection = "not_checked"
    return result(errors, source_count, private_projection)


def result(errors: list[str], source_locks: int, private_projection: str) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-conformance-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "schemas": len(SCHEMAS),
        "private_registry_crosscheck": private_projection,
        "matrix_engine": "component_pass" if not unique else "not_proven",
        "required_matrix": "non_green",
        "green_rows": 0,
        "required_rows": 61,
        "p06_09": "in_progress",
        "p06": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_CONFORMANCE_CONTRACT_PASS "
        f"green={validation['green_rows']}/{validation['required_rows']} "
        f"required_matrix={validation['required_matrix']}"
    )
