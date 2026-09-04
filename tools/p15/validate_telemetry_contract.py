from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-telemetry-contract-v1.json"
POLICY_PATH = ROOT / "protocol/mcp/p15-telemetry-policy-v1.json"
P15_07_CONTRACT_PATH = ROOT / "implementation/p15/p15-quota-contract-v1.json"
P15_07_REVISION = "e15921a59d45056c46b8ae94b6f6af778746c534"
P15_07_CONTRACT_SHA256 = (
    "787f88e79b0b1aa1dff483237cf60e9a30526ab686481ec779fe04a3cd3db872"
)
P15_09_SUPERSEDING_VALIDATOR = "tools/p15/validate_inspector_staging_contract.py"
P15_08_AUDITED_REVISION = "9f9c6932518175906842a2cbb5915a0fb96d0d49"
P15_09_SUPERSEDED_PATHS = {
    "Cargo.toml",
    "security/dependency-policy.json",
    "Cargo.lock",
    "tools/p15/validate_quota_contract.py",
    "tools/p15/build_telemetry_contract.py",
    "tools/p15/validate_telemetry_contract.py",
}

EXPECTED_KEYS = {
    "correlation_fields",
    "dashboard_dimensions",
    "dashboard_schema_version",
    "handler_sequence_preserved",
    "identifier_protection",
    "limits",
    "p15_07_audited_source_commit",
    "p15_07_contract_sha256",
    "public_meta_keys",
    "public_trace_id_exposed",
    "required_behaviors",
    "rust_regression_tests",
    "rust_telemetry_tests",
    "schema_version",
    "scope",
    "source_locks",
    "target_profile",
    "tenant_classes",
    "telemetry_policy_sha256",
    "tool_catalog_sha256",
    "trace_schema_version",
    "trace_stages",
}
EXPECTED_CORRELATION_FIELDS = [
    "request_id",
    "job_id",
    "execution_id",
    "revision_id",
    "evidence_id",
]
EXPECTED_DASHBOARD_DIMENSIONS = [
    "tool",
    "tenant_class",
    "job",
    "backend",
    "capability",
    "validation_state",
]
EXPECTED_TENANT_CLASSES = ["unattributed", "local_reference"]
EXPECTED_STAGES = [
    "mcp_request",
    "capability_plan",
    "job",
    "backend_execution",
    "validation_step",
    "artifact_commit",
]
EXPECTED_BEHAVIORS = [
    "one_complete_trace_per_public_result",
    "fixed_six_stage_hierarchy_with_explicit_not_applicable",
    "whole_trace_fifo_eviction_at_bounded_capacity",
    "tool_latency_and_status_by_closed_tenant_class",
    "job_backend_capability_and_validation_sli",
    "process_salted_identifier_and_capability_digests",
    "no_body_credential_path_identity_or_backend_error_retention",
    "telemetry_does_not_reorder_or_duplicate_gateway_dispatch",
    "invalid_gateway_output_is_not_copied_into_telemetry",
    "deterministic_dashboard_from_retained_complete_traces",
]
EXPECTED_POLICY = {
    "correlation_fields": EXPECTED_CORRELATION_FIELDS,
    "dashboard_dimensions": EXPECTED_DASHBOARD_DIMENSIONS,
    "max_capability_routes_per_trace": 128,
    "schema_version": "hwpx-agent.telemetry-policy/v1",
    "tenant_classes": EXPECTED_TENANT_CLASSES,
    "trace_capacity": 2_048,
    "trace_stages": EXPECTED_STAGES,
}
EXPECTED_SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "deny.toml",
    "security/dependency-policy.json",
    "docs/02_architecture/08_observability.md",
    "docs/09_roadmap/P15_remote_mcp_control_plane.md",
    "docs/10_operations/05_observability_incidents.md",
    "specs/work-breakdown-structure.json",
    "protocol/mcp/p15-public-tools-v1.json",
    "protocol/mcp/p15-public-error-catalog-v2.json",
    "protocol/mcp/p15-quota-policy-v1.json",
    "protocol/mcp/p15-telemetry-policy-v1.json",
    "implementation/p15/p15-quota-contract-v1.json",
    "implementation/p15/P15-08_TELEMETRY.md",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/catalog.rs",
    "crates/mcp-control-plane/src/error_catalog.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/src/policy.rs",
    "crates/mcp-control-plane/src/quota.rs",
    "crates/mcp-control-plane/src/strict_json.rs",
    "crates/mcp-control-plane/src/telemetry.rs",
    "crates/mcp-control-plane/src/async_jobs.rs",
    "crates/mcp-control-plane/src/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "crates/mcp-control-plane/tests/async_job_ux.rs",
    "crates/mcp-control-plane/tests/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/error_mapping.rs",
    "crates/mcp-control-plane/tests/quota_service.rs",
    "crates/mcp-control-plane/tests/telemetry.rs",
    "tools/p15/build_quota_contract.py",
    "tools/p15/validate_quota_contract.py",
    "tools/p15/build_telemetry_contract.py",
    "tools/p15/validate_telemetry_contract.py",
    "tools/p15/tests/test_quota_contract.py",
    "tools/p15/tests/test_telemetry_contract.py",
]


def load_json(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def sha256(path: Path) -> str:
    content = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(content).hexdigest()


def safe_sha256(path: Path, errors: list[str], label: str) -> str:
    try:
        return sha256(path)
    except Exception:
        errors.append(label)
        return ""


def bounded_file(root: Path, relative: str) -> Path:
    value = Path(relative)
    if not relative or "\\" in relative or value.is_absolute() or ".." in value.parts:
        raise ValueError("source path is not bounded")
    resolved_root = root.resolve(strict=True)
    candidate = root / value
    if candidate.is_symlink() or (
        hasattr(candidate, "is_junction") and candidate.is_junction()
    ):
        raise ValueError("source path is linked")
    resolved = candidate.resolve(strict=True)
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise ValueError("source path escapes repository")
    if not 0 < resolved.stat().st_size <= 4_000_000:
        raise ValueError("source file shape is invalid")
    return resolved


def historical_p15_07_is_intact(root: Path, contract: dict[str, Any]) -> bool:
    locks = contract.get("source_locks")
    if not isinstance(locks, list):
        return False
    for entry in locks:
        if not isinstance(entry, dict):
            return False
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected, str):
            return False
        result = subprocess.run(
            ["git", "show", f"{P15_07_REVISION}:{relative}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        normalized = result.stdout.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        if result.returncode != 0 or hashlib.sha256(normalized).hexdigest() != expected:
            return False
    return True


def validate_p15_09_supersession(root: Path) -> list[str]:
    validator_path = root / P15_09_SUPERSEDING_VALIDATOR
    specification = importlib.util.spec_from_file_location(
        "p15_inspector_staging_superseding_validator", validator_path
    )
    if specification is None or specification.loader is None:
        return ["p15_09_supersession.validator_load"]
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
        supersession_errors = module.validate(root)
    except Exception:
        return ["p15_09_supersession.validation"]
    if supersession_errors:
        return ["p15_09_supersession.contract"]
    return []


def historical_p15_08_source_matches(root: Path, relative: str, expected: str) -> bool:
    result = subprocess.run(
        ["git", "show", f"{P15_08_AUDITED_REVISION}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    content = result.stdout.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return result.returncode == 0 and hashlib.sha256(content).hexdigest() == expected


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    p15_09_supersession_errors = validate_p15_09_supersession(root)
    try:
        contract = load_json(root / CONTRACT_PATH.relative_to(ROOT))
    except Exception as error:
        return [f"contract.load:{type(error).__name__}"]
    if set(contract) != EXPECTED_KEYS:
        errors.append("contract.keys")
    if contract.get("schema_version") != "hwpx-agent.p15-telemetry-contract/v1":
        errors.append("contract.schema_version")
    if contract.get("scope") != "current_pc_hancom_2020_local_telemetry_reference":
        errors.append("contract.scope")
    if contract.get("target_profile") != "hancom-hangul-2020-secondary":
        errors.append("contract.target_profile")
    if contract.get("p15_07_audited_source_commit") != P15_07_REVISION:
        errors.append("contract.predecessor")
    if contract.get("p15_07_contract_sha256") != P15_07_CONTRACT_SHA256:
        errors.append("contract.predecessor_digest")
    predecessor_path = root / P15_07_CONTRACT_PATH.relative_to(ROOT)
    try:
        predecessor = load_json(predecessor_path)
    except Exception:
        predecessor = {}
        errors.append("predecessor.load")
    if safe_sha256(predecessor_path, errors, "predecessor.digest_read") != P15_07_CONTRACT_SHA256:
        errors.append("predecessor.digest")
    if predecessor and not historical_p15_07_is_intact(root, predecessor):
        errors.append("predecessor.historical_sources")
    if contract.get("required_behaviors") != EXPECTED_BEHAVIORS:
        errors.append("contract.behaviors")
    if contract.get("handler_sequence_preserved") is not True:
        errors.append("contract.handler_sequence")
    if contract.get("identifier_protection") != "process_salted_sha256":
        errors.append("contract.identifier_protection")
    if contract.get("public_trace_id_exposed") is not False:
        errors.append("contract.public_trace")
    if contract.get("public_meta_keys") != ["hwpx/telemetryPolicySha256"]:
        errors.append("contract.public_meta")
    if contract.get("trace_schema_version") != "hwpx-agent.telemetry-trace/v1":
        errors.append("contract.trace_schema")
    if contract.get("dashboard_schema_version") != "hwpx-agent.telemetry-dashboard/v1":
        errors.append("contract.dashboard_schema")
    if contract.get("rust_telemetry_tests") != 8 or contract.get("rust_regression_tests") != 53:
        errors.append("contract.rust_tests")

    try:
        policy = load_json(root / POLICY_PATH.relative_to(ROOT))
    except Exception as error:
        policy = {}
        errors.append(f"policy.load:{type(error).__name__}")
    if policy != EXPECTED_POLICY:
        errors.append("policy.content")
    policy_hash = safe_sha256(
        root / POLICY_PATH.relative_to(ROOT), errors, "policy.digest_read"
    )
    if contract.get("telemetry_policy_sha256") != policy_hash:
        errors.append("contract.policy_digest")
    if contract.get("correlation_fields") != EXPECTED_CORRELATION_FIELDS:
        errors.append("contract.correlation")
    if contract.get("dashboard_dimensions") != EXPECTED_DASHBOARD_DIMENSIONS:
        errors.append("contract.dashboard_dimensions")
    if contract.get("tenant_classes") != EXPECTED_TENANT_CLASSES:
        errors.append("contract.tenant_classes")
    if contract.get("trace_stages") != EXPECTED_STAGES:
        errors.append("contract.trace_stages")
    if contract.get("limits") != {
        "capability_routes_per_trace": 128,
        "traces": 2_048,
    }:
        errors.append("contract.limits")
    if contract.get("tool_catalog_sha256") != (
        "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
    ):
        errors.append("contract.tool_catalog_digest")

    locks = contract.get("source_locks")
    if not isinstance(locks, list) or len(locks) != len(EXPECTED_SOURCE_PATHS):
        errors.append("contract.source_locks")
    else:
        seen: set[str] = set()
        for index, entry in enumerate(locks):
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                errors.append(f"source_lock[{index}].shape")
                continue
            relative = entry.get("path")
            expected = entry.get("sha256")
            if (
                not isinstance(relative, str)
                or relative in seen
                or relative != EXPECTED_SOURCE_PATHS[index]
            ):
                errors.append(f"source_lock[{index}].path")
                continue
            seen.add(relative)
            try:
                source = bounded_file(root, relative)
            except Exception:
                errors.append(f"source_lock[{index}].bounded")
                continue
            if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
                errors.append(f"source_lock[{index}].digest_shape")
            elif sha256(source) != expected:
                if relative not in P15_09_SUPERSEDED_PATHS or p15_09_supersession_errors:
                    errors.append(f"source_lock[{index}].digest")
                elif not historical_p15_08_source_matches(root, relative, expected):
                    errors.append(f"source_lock[{index}].historical_digest")

    telemetry = (root / "crates/mcp-control-plane/src/telemetry.rs").read_text(
        encoding="utf-8"
    )
    for token in [
        "pub struct InMemoryTelemetry",
        "pub struct TelemetryDashboard",
        "pub struct TelemetryTrace",
        "pub const MAX_TELEMETRY_TRACES: usize = 2_048",
        "pub const MAX_CAPABILITY_ROUTES_PER_TRACE: usize = 128",
        "TraceObservation::new",
        "digest_identifier(&self.salt",
        "self.traces.pop_front()",
        "TelemetryStage::ArtifactCommit",
        "TelemetrySpanState::NotApplicable",
        "Some(Self::Hancom2020)",
    ]:
        if token not in telemetry:
            errors.append(f"telemetry.token:{token}")
    if TELEMETRY_POLICY_DIGEST_TOKEN(policy_hash) not in telemetry:
        errors.append("telemetry.policy_digest")
    for forbidden in [
        "authorization_header",
        "arguments_json",
        "project_id",
        "TenantId",
        "SubjectDigest",
        "signed_url",
        "document_body",
        "raw_xml",
        "renderer",
    ]:
        if forbidden in telemetry:
            errors.append(f"telemetry.forbidden:{forbidden}")

    handler = (root / "crates/mcp-control-plane/src/handler.rs").read_text(
        encoding="utf-8"
    )
    wrapper_sequence = [
        ".begin_trace(",
        "self.handle_observed(",
        "observation.finish(",
        "self.telemetry.commit(",
    ]
    wrapper_positions = [handler.find(token) for token in wrapper_sequence]
    if any(position < 0 for position in wrapper_positions) or wrapper_positions != sorted(
        wrapper_positions
    ):
        errors.append("handler.telemetry_wrapper_order")
    boundary_sequence = [
        "authenticate_public_mcp(",
        "parse_unique_value(",
        "input_is_valid(",
        "observation.observe_validated_input(",
        ".policy.authorize(",
        "observation.mark_policy_completed(",
        ".admit(&context, tool, &arguments, now_unix_seconds)",
        "observation.mark_dispatch_attempted(",
        ".gateway.dispatch(",
        "observation.mark_dispatch_returned(",
        "output_is_valid(",
        "correlation.matches(",
        "observation.observe_validated_output(",
    ]
    positions = [handler.find(token) for token in boundary_sequence]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        errors.append("handler.execution_order")
    if handler.count("self.gateway.dispatch(call)") != 1:
        errors.append("handler.dispatch_count")
    if handler.count('"hwpx/telemetryPolicySha256"') != 2:
        errors.append("handler.telemetry_meta")
    for forbidden in ['"hwpx/traceId"', '"hwpx/trace_id"']:
        if forbidden in handler:
            errors.append(f"handler.public_trace:{forbidden}")

    tests = (root / "crates/mcp-control-plane/tests/telemetry.rs").read_text(
        encoding="utf-8"
    )
    if tests.count("#[test]") != 8:
        errors.append("rust_tests.count")
    for token in [
        "successful_document_trace_has_complete_ordered_hierarchy_and_correlations",
        "public_result_exposes_policy_digest_but_never_internal_trace_id",
        "telemetry_never_retains_bearer_arguments_or_backend_error_text",
        "capability_routes_are_digest_keyed_and_backend_aggregated",
        "bounded_ring_evicts_only_whole_oldest_traces",
        "invalid_backend_output_records_failed_validation_after_one_dispatch",
    ]:
        if token not in tests:
            errors.append(f"rust_tests.token:{token}")
    return errors


def TELEMETRY_POLICY_DIGEST_TOKEN(value: str) -> str:
    return f'pub const TELEMETRY_POLICY_SHA256: &str =\n    "{value}";'


def main() -> int:
    errors = validate()
    print(
        json.dumps(
            {
                "dashboard_dimensions": len(EXPECTED_DASHBOARD_DIMENSIONS),
                "errors": errors,
                "rust_telemetry_tests": 8,
                "schema_version": "hwpx-agent.p15-telemetry-validation/v1",
                "source_files": len(EXPECTED_SOURCE_PATHS),
                "state": "pass" if not errors else "fail",
                "trace_stages": len(EXPECTED_STAGES),
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
