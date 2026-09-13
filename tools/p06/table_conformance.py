#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any


REPORT_SCHEMA_VERSION = "hwpx-agent.table-conformance-report/v1"
EVIDENCE_SCHEMA_VERSION = "hwpx-agent.table-conformance-evidence/v1"
PROJECTION_SCHEMA_VERSION = "hwpx-agent.table-automation-projection/v1"
AUTOMATION_REGISTRY_SCHEMAS = {
    "hwpx-agent.automation-binding-registry/v1",
    "hwpx-agent.p06-table-automation-binding-overlay/v1",
}
TARGET_PROFILE_ID = "hancom-hangul-2020-secondary"
TARGET_BUILD = "11.0.0.9136"
TARGET_ARCHITECTURE = "x86"
TARGET_LOCALE = "ko-KR"
EXPECTED_FEATURE_COUNT = 61
MAX_JSON_BYTES = 32 * 1024 * 1024
MAX_EVIDENCE_FILES = 512
MAX_EVIDENCE_RECORDS = EXPECTED_FEATURE_COUNT

STAGE_RANK = {
    "cataloged": 0,
    "unit_passed": 1,
    "integration_passed": 2,
    "oracle_verified": 3,
}
AUTOMATION_STATUSES = {
    "candidate_unverified",
    "unavailable_with_reason",
    "verified_current_target",
}
RUNTIME_STATES = {
    "unverified",
    "verified_current_target",
    "failed_current_target",
    "blocked_by_policy",
    "unverified_not_run",
}
DIFFERENTIAL_STATES = {"not_run", "exact_match", "mismatch"}
BACKENDS = {"component_only", "direct_hwpx"}
FIXTURE_CLASSES = (
    "happy_path",
    "boundary",
    "negative",
    "preservation",
    "target_build",
    "security",
)
FEATURE_ID_PATTERN = re.compile(r"TABLE-(?:00[1-9]|0[1-5][0-9]|06[01])\Z")
CAPABILITY_ID_PATTERN = re.compile(r"table\.[a-z0-9_]+\Z")
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")


class ConformanceError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ConformanceError("duplicate_json_key")
        value[key] = item
    return value


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def bounded_repo_file(root: Path, relative: str, maximum: int = MAX_JSON_BYTES) -> Path:
    candidate = PurePosixPath(relative)
    if (
        candidate.is_absolute()
        or not candidate.parts
        or any(part in ("", ".", "..") for part in candidate.parts)
        or "\\" in relative
        or ":" in relative
        or "\0" in relative
    ):
        raise ConformanceError("unsafe_path")
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in candidate.parts:
        cursor /= part
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            raise ConformanceError("linked_path")
    path = cursor.resolve(strict=True)
    if resolved_root not in path.parents or not path.is_file():
        raise ConformanceError("outside_or_missing_path")
    size = path.stat().st_size
    if size <= 0 or size > maximum:
        raise ConformanceError("file_size_limit")
    return path


def load_json_file(root: Path, relative: str, maximum: int = MAX_JSON_BYTES) -> tuple[Any, str]:
    path = bounded_repo_file(root, relative, maximum)
    data = path.read_bytes()
    if len(data) != path.stat().st_size:
        raise ConformanceError("file_changed_during_read")
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConformanceError("invalid_json") from error
    return value, sha256_bytes(data)


def exact_target(value: Any) -> dict[str, str]:
    expected = {
        "profile_id": TARGET_PROFILE_ID,
        "product": "Hancom Hangul 2020",
        "build": TARGET_BUILD,
        "locale": TARGET_LOCALE,
        "architecture": TARGET_ARCHITECTURE,
        "scope": "current_pc_personal_local_development",
    }
    if value != expected:
        raise ConformanceError("target_mismatch")
    return expected


def build_automation_projection(registry: Any, registry_sha256: str) -> dict[str, Any]:
    if not isinstance(registry, dict) or registry.get("schema_version") \
            not in AUTOMATION_REGISTRY_SCHEMAS:
        raise ConformanceError("registry_schema")
    target = registry.get("target")
    if not isinstance(target, dict):
        raise ConformanceError("registry_target")
    projected_target = {
        "profile_id": target.get("profile_id"),
        "product": target.get("product"),
        "build": target.get("exact_build"),
        "locale": target.get("locale"),
        "architecture": target.get("architecture"),
        "scope": "current_pc_personal_local_development",
    }
    exact_target(projected_target)
    bindings = registry.get("bindings")
    if not isinstance(bindings, list) or len(bindings) > 10_000:
        raise ConformanceError("registry_bindings")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for binding in bindings:
        if not isinstance(binding, dict):
            raise ConformanceError("registry_binding_shape")
        feature_id = binding.get("feature_id")
        if not isinstance(feature_id, str) or not FEATURE_ID_PATTERN.fullmatch(feature_id):
            continue
        if feature_id in seen:
            raise ConformanceError("duplicate_table_binding")
        seen.add(feature_id)
        if binding.get("target_profile_id") != projected_target["profile_id"]:
            raise ConformanceError("table_binding_target")
        status = binding.get("status")
        runtime_state = binding.get("runtime_support_state")
        routing_enabled = binding.get("routing_enabled")
        if status not in AUTOMATION_STATUSES or runtime_state not in RUNTIME_STATES \
                or not isinstance(routing_enabled, bool):
            raise ConformanceError("table_binding_state")
        capability_id = binding.get("capability_id")
        if not isinstance(capability_id, str) or not CAPABILITY_ID_PATTERN.fullmatch(capability_id):
            raise ConformanceError("table_capability_id")
        rows.append(
            {
                "feature_id": feature_id,
                "capability_id": capability_id,
                "binding_status": status,
                "runtime_support_state": runtime_state,
                "routing_enabled": routing_enabled,
            }
        )
    rows.sort(key=lambda item: item["feature_id"])
    if len(rows) != EXPECTED_FEATURE_COUNT:
        raise ConformanceError("table_binding_coverage")
    return {
        "schema_version": PROJECTION_SCHEMA_VERSION,
        "source_registry_sha256": registry_sha256,
        "target": projected_target,
        "row_count": len(rows),
        "rows": rows,
        "privacy": {
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
        },
    }


def validate_projection(value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "source_registry_sha256",
        "target",
        "row_count",
        "rows",
        "privacy",
    }:
        raise ConformanceError("projection_shape")
    if value["schema_version"] != PROJECTION_SCHEMA_VERSION:
        raise ConformanceError("projection_schema")
    if not isinstance(value["source_registry_sha256"], str) \
            or not SHA256_PATTERN.fullmatch(value["source_registry_sha256"]):
        raise ConformanceError("projection_source_digest")
    exact_target(value["target"])
    if value["privacy"] != {
        "raw_action_identifiers": False,
        "raw_parameter_identifiers": False,
        "raw_probe_values": False,
    }:
        raise ConformanceError("projection_privacy")
    rows = value["rows"]
    if not isinstance(rows, list) or value["row_count"] != EXPECTED_FEATURE_COUNT \
            or len(rows) != EXPECTED_FEATURE_COUNT:
        raise ConformanceError("projection_count")
    expected_keys = {
        "feature_id",
        "capability_id",
        "binding_status",
        "runtime_support_state",
        "routing_enabled",
    }
    output: dict[str, dict[str, Any]] = {}
    last = ""
    for row in rows:
        if not isinstance(row, dict) or set(row) != expected_keys:
            raise ConformanceError("projection_row_shape")
        feature_id = row["feature_id"]
        capability_id = row["capability_id"]
        if not isinstance(feature_id, str) or not FEATURE_ID_PATTERN.fullmatch(feature_id) \
                or feature_id <= last or feature_id in output:
            raise ConformanceError("projection_row_order")
        if not isinstance(capability_id, str) or not CAPABILITY_ID_PATTERN.fullmatch(capability_id):
            raise ConformanceError("projection_capability")
        if row["binding_status"] not in AUTOMATION_STATUSES \
                or row["runtime_support_state"] not in RUNTIME_STATES \
                or not isinstance(row["routing_enabled"], bool):
            raise ConformanceError("projection_row_state")
        output[feature_id] = row
        last = feature_id
    return output


def validate_evidence(root: Path, value: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "target",
        "required_fixture_classes",
        "records",
        "not_claimed",
    }:
        raise ConformanceError("evidence_shape")
    if value["schema_version"] != EVIDENCE_SCHEMA_VERSION:
        raise ConformanceError("evidence_schema")
    exact_target(value["target"])
    if value["required_fixture_classes"] != list(FIXTURE_CLASSES):
        raise ConformanceError("evidence_fixture_policy")
    if value["not_claimed"] != {
        "p06_07_renderer_gate": False,
        "p06_09_complete": False,
        "p06_phase_complete": False,
        "production": False,
        "other_pc_or_version": False,
        "product_complete": False,
    }:
        raise ConformanceError("evidence_nonclaim")
    records = value["records"]
    if not isinstance(records, list) or len(records) > MAX_EVIDENCE_RECORDS:
        raise ConformanceError("evidence_record_limit")
    expected_keys = {
        "feature_ids",
        "backend",
        "stage",
        "validations_passed",
        "fixture_classes_passed",
        "negative_passed",
        "rollback_or_retry_passed",
        "differential_state",
        "evidence_files",
    }
    output: dict[str, dict[str, Any]] = {}
    evidence_file_count = 0
    for record in records:
        if not isinstance(record, dict) or set(record) != expected_keys:
            raise ConformanceError("evidence_record_shape")
        feature_ids = record["feature_ids"]
        if not isinstance(feature_ids, list) or not feature_ids \
                or feature_ids != sorted(set(feature_ids)):
            raise ConformanceError("evidence_feature_ids")
        if record["backend"] not in BACKENDS or record["stage"] not in STAGE_RANK \
                or record["stage"] == "cataloged":
            raise ConformanceError("evidence_stage")
        if record["backend"] == "component_only" \
                and STAGE_RANK[record["stage"]] > STAGE_RANK["unit_passed"]:
            raise ConformanceError("component_stage_overclaim")
        validations = record["validations_passed"]
        fixtures = record["fixture_classes_passed"]
        if not isinstance(validations, list) or validations != sorted(set(validations)) \
                or any(not isinstance(item, str) or not item for item in validations):
            raise ConformanceError("evidence_validations")
        if not isinstance(fixtures, list) or fixtures != sorted(set(fixtures)) \
                or any(item not in FIXTURE_CLASSES for item in fixtures):
            raise ConformanceError("evidence_fixtures")
        if not isinstance(record["negative_passed"], bool) \
                or not isinstance(record["rollback_or_retry_passed"], bool) \
                or record["differential_state"] not in DIFFERENTIAL_STATES:
            raise ConformanceError("evidence_boolean_or_differential")
        files = record["evidence_files"]
        if not isinstance(files, list) or not files:
            raise ConformanceError("evidence_files")
        evidence_file_count += len(files)
        if evidence_file_count > MAX_EVIDENCE_FILES:
            raise ConformanceError("evidence_file_limit")
        checked_files: list[dict[str, str]] = []
        seen_paths: set[str] = set()
        for item in files:
            if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
                raise ConformanceError("evidence_file_shape")
            relative = item["path"]
            digest = item["sha256"]
            if not isinstance(relative, str) or relative in seen_paths \
                    or not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
                raise ConformanceError("evidence_file_identity")
            seen_paths.add(relative)
            if sha256_file(bounded_repo_file(root, relative, 4 * 1024 * 1024)) != digest:
                raise ConformanceError("evidence_file_digest")
            checked_files.append({"path": relative, "sha256": digest})
        for feature_id in feature_ids:
            if not isinstance(feature_id, str) or not FEATURE_ID_PATTERN.fullmatch(feature_id) \
                    or feature_id in output:
                raise ConformanceError("evidence_feature_duplicate_or_invalid")
            output[feature_id] = {
                **{key: record[key] for key in expected_keys if key not in {"feature_ids", "evidence_files"}},
                "evidence_files": checked_files,
            }
    return output


def _catalog_rows(catalog: Any) -> list[dict[str, Any]]:
    if not isinstance(catalog, list):
        raise ConformanceError("catalog_shape")
    rows = [item for item in catalog if isinstance(item, dict) and item.get("phase") == "P06"]
    rows.sort(key=lambda item: item.get("feature_id", ""))
    if len(rows) != EXPECTED_FEATURE_COUNT:
        raise ConformanceError("catalog_table_count")
    expected_ids = [f"TABLE-{index:03d}" for index in range(1, EXPECTED_FEATURE_COUNT + 1)]
    if [row.get("feature_id") for row in rows] != expected_ids:
        raise ConformanceError("catalog_feature_sequence")
    seen_capabilities: set[str] = set()
    for row in rows:
        capability_id = row.get("capability_id")
        if not isinstance(capability_id, str) or not CAPABILITY_ID_PATTERN.fullmatch(capability_id) \
                or capability_id in seen_capabilities:
            raise ConformanceError("catalog_capability")
        seen_capabilities.add(capability_id)
        if row.get("support_level") != "HYBRID" or row.get("preferred_backend") != "direct_hwpx" \
                or row.get("fallback_backend") != "desktop_automation":
            raise ConformanceError("catalog_route_policy")
    return rows


def _contract_rows(contracts: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(contracts, dict) or contracts.get("schema_version") \
            != "hwpx-agent.capability-contract-registry/v1":
        raise ConformanceError("contracts_schema")
    values = contracts.get("contracts")
    if not isinstance(values, list):
        raise ConformanceError("contracts_shape")
    rows: dict[str, dict[str, Any]] = {}
    for item in values:
        if not isinstance(item, dict) or item.get("phase") != "P06":
            continue
        feature_id = item.get("feature_id")
        if not isinstance(feature_id, str) or feature_id in rows:
            raise ConformanceError("contract_feature_id")
        if not isinstance(item.get("args_schema"), dict) or not item["args_schema"]:
            raise ConformanceError("contract_operation_schema")
        steps = item.get("validation_steps")
        fixtures = item.get("release_gate", {}).get("required_fixture_classes")
        if not isinstance(steps, list) or not isinstance(fixtures, list):
            raise ConformanceError("contract_gate_shape")
        rows[feature_id] = item
    if len(rows) != EXPECTED_FEATURE_COUNT:
        raise ConformanceError("contract_table_count")
    return rows


def build_report(
    *,
    root: Path,
    catalog: Any,
    catalog_sha256: str,
    contracts: Any,
    contracts_sha256: str,
    projection: Any,
    projection_sha256: str,
    evidence: Any,
    evidence_sha256: str,
) -> dict[str, Any]:
    catalog_rows = _catalog_rows(catalog)
    contract_rows = _contract_rows(contracts)
    automation_rows = validate_projection(projection)
    evidence_rows = validate_evidence(root, evidence)
    report_rows: list[dict[str, Any]] = []
    blocker_counter: Counter[str] = Counter()
    for catalog_row in catalog_rows:
        feature_id = catalog_row["feature_id"]
        capability_id = catalog_row["capability_id"]
        contract = contract_rows.get(feature_id)
        automation = automation_rows.get(feature_id)
        if contract is None or automation is None \
                or contract.get("capability_id") != capability_id \
                or automation.get("capability_id") != capability_id:
            raise ConformanceError("cross_source_identity_mismatch")
        required_validations = [step.get("id") for step in contract["validation_steps"]]
        if any(not isinstance(item, str) or not item for item in required_validations) \
                or len(set(required_validations)) != len(required_validations):
            raise ConformanceError("contract_validation_ids")
        required_fixtures = contract["release_gate"]["required_fixture_classes"]
        direct = evidence_rows.get(feature_id)
        stage = direct["stage"] if direct else "cataloged"
        backend = direct["backend"] if direct else "component_only"
        passed_validations = direct["validations_passed"] if direct else []
        passed_fixtures = direct["fixture_classes_passed"] if direct else []
        differential_state = direct["differential_state"] if direct else "not_run"
        blockers: list[str] = []
        if direct is None:
            blockers.append("direct_evidence_missing")
        elif backend != "direct_hwpx":
            blockers.append("direct_backend_unbound")
        if stage != "oracle_verified":
            blockers.append("direct_oracle_not_verified")
        for validation in required_validations:
            if validation not in passed_validations:
                blockers.append(f"validation_missing:{validation}")
        for fixture in required_fixtures:
            if fixture not in passed_fixtures:
                blockers.append(f"fixture_missing:{fixture}")
        if direct is None or not direct["negative_passed"]:
            blockers.append("negative_not_passed")
        if direct is None or not direct["rollback_or_retry_passed"]:
            blockers.append("rollback_or_retry_not_passed")
        if automation["binding_status"] == "unavailable_with_reason":
            blockers.append("automation_binding_unavailable")
        elif automation["binding_status"] != "verified_current_target":
            blockers.append("automation_binding_unverified")
        if automation["runtime_support_state"] != "verified_current_target":
            blockers.append("automation_runtime_unverified")
        if differential_state != "exact_match":
            blockers.append("differential_not_passed")
        blockers = list(dict.fromkeys(blockers))
        blocker_counter.update(blocker.split(":", 1)[0] for blocker in blockers)
        report_rows.append(
            {
                "feature_id": feature_id,
                "capability_id": capability_id,
                "required_validations": required_validations,
                "required_fixture_classes": required_fixtures,
                "direct": {
                    "backend": backend,
                    "stage": stage,
                    "validations_passed": passed_validations,
                    "fixture_classes_passed": passed_fixtures,
                    "negative_passed": direct["negative_passed"] if direct else False,
                    "rollback_or_retry_passed": (
                        direct["rollback_or_retry_passed"] if direct else False
                    ),
                    "evidence_files": direct["evidence_files"] if direct else [],
                },
                "automation": {
                    "binding_status": automation["binding_status"],
                    "runtime_support_state": automation["runtime_support_state"],
                    "routing_enabled": automation["routing_enabled"],
                },
                "differential_state": differential_state,
                "gate_state": "green" if not blockers else "non_green",
                "blockers": blockers,
            }
        )
    green = sum(row["gate_state"] == "green" for row in report_rows)
    stage_counts = Counter(row["direct"]["stage"] for row in report_rows)
    for stage in STAGE_RANK:
        stage_counts.setdefault(stage, 0)
    binding_counts = Counter(row["automation"]["binding_status"] for row in report_rows)
    differential_counts = Counter(row["differential_state"] for row in report_rows)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "scope": "p06_09_current_pc_hancom_2020_fail_closed_matrix",
        "target": exact_target(projection["target"]),
        "sources": {
            "feature_catalog_sha256": catalog_sha256,
            "capability_contracts_sha256": contracts_sha256,
            "automation_projection_sha256": projection_sha256,
            "automation_source_registry_sha256": projection["source_registry_sha256"],
            "direct_evidence_sha256": evidence_sha256,
        },
        "summary": {
            "required_rows": EXPECTED_FEATURE_COUNT,
            "green_rows": green,
            "non_green_rows": EXPECTED_FEATURE_COUNT - green,
            "direct_stage_counts": dict(sorted(stage_counts.items())),
            "automation_binding_counts": dict(sorted(binding_counts.items())),
            "differential_counts": dict(sorted(differential_counts.items())),
            "blocker_counts": dict(sorted(blocker_counter.items())),
            "required_matrix": "green" if green == EXPECTED_FEATURE_COUNT else "non_green",
            "p06_09": "pass" if green == EXPECTED_FEATURE_COUNT else "in_progress",
            "p06_phase": "in_progress",
            "product_complete": False,
        },
        "rows": report_rows,
        "privacy": {
            "raw_action_identifiers": False,
            "raw_parameter_identifiers": False,
            "raw_probe_values": False,
            "document_content": False,
            "absolute_private_paths": False,
        },
    }


def load_and_build(
    root: Path,
    *,
    catalog_path: str,
    contracts_path: str,
    projection_path: str,
    evidence_path: str,
) -> dict[str, Any]:
    catalog, catalog_digest = load_json_file(root, catalog_path)
    contracts, contracts_digest = load_json_file(root, contracts_path)
    projection, projection_digest = load_json_file(root, projection_path)
    evidence, evidence_digest = load_json_file(root, evidence_path)
    return build_report(
        root=root,
        catalog=catalog,
        catalog_sha256=catalog_digest,
        contracts=contracts,
        contracts_sha256=contracts_digest,
        projection=projection,
        projection_sha256=projection_digest,
        evidence=evidence,
        evidence_sha256=evidence_digest,
    )


def write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(data)
