from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-artifact-delivery-contract-v1.json"
P15_05_AUDITED_REVISION = "dde79ff3fa86953c7f3e6e8e2402479eddee813e"
P15_06_SUPERSEDING_VALIDATOR = "tools/p15/validate_error_mapping_contract.py"
P15_06_SUPERSEDED_PATHS = {
    "Cargo.lock",
    "Cargo.toml",
    "security/dependency-policy.json",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "tools/p15/build_artifact_delivery_contract.py",
    "tools/p15/validate_async_job_contract.py",
    "tools/p15/validate_artifact_delivery_contract.py",
}

EXPECTED_KEYS = {
    "artifact_tool",
    "catalog_sha256",
    "client_delivery_meta_key",
    "content_attachment_type",
    "limits",
    "p15_04_audited_source_commit",
    "required_behaviors",
    "rust_artifact_delivery_tests",
    "schema_version",
    "scope",
    "source_locks",
    "target_profile",
}
EXPECTED_BEHAVIORS = [
    "frozen_artifact_get_schema",
    "tenant_project_artifact_binding",
    "artifact_acl_rechecked",
    "binding_generation_revokes_old_url",
    "signed_url_only_in_client_meta",
    "subject_project_content_and_expiry_signed",
    "single_bounded_byte_range",
    "current_acl_state_and_digest_rechecked_at_redemption",
    "model_visible_content_has_no_token_or_bytes",
]
EXPECTED_SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "deny.toml",
    "security/dependency-policy.json",
    "docs/06_mcp_api/01_tool_surface.md",
    "docs/06_mcp_api/02_tool_contracts.md",
    "docs/06_mcp_api/06_jobs_artifacts.md",
    "docs/12_implementation_guides/09_project_jobs_storage.md",
    "protocol/mcp/p15-public-tools-v1.json",
    "implementation/p14/postgres/p14-artifact-service-v1.json",
    "implementation/p15/p15-auth-tenant-v1.json",
    "implementation/p15/p15-public-tool-schema-contract-v1.json",
    "implementation/p15/p15-handler-contract-v1.json",
    "implementation/p15/p15-async-job-contract-v1.json",
    "implementation/p15/P15-05_ARTIFACT_DELIVERY_POLICY.md",
    "crates/artifact-service/Cargo.toml",
    "crates/artifact-service/src/lib.rs",
    "crates/artifact-service/src/crypto.rs",
    "crates/artifact-service/src/service.rs",
    "crates/artifact-service/src/signed_url.rs",
    "crates/artifact-service/src/store.rs",
    "crates/artifact-service/src/types.rs",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/catalog.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/src/policy.rs",
    "crates/mcp-control-plane/src/strict_json.rs",
    "crates/mcp-control-plane/src/async_jobs.rs",
    "crates/mcp-control-plane/src/artifact_delivery.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "crates/mcp-control-plane/tests/async_job_ux.rs",
    "crates/mcp-control-plane/tests/artifact_delivery.rs",
    "tools/p15/build_async_job_contract.py",
    "tools/p15/validate_async_job_contract.py",
    "tools/p15/build_artifact_delivery_contract.py",
    "tools/p15/validate_artifact_delivery_contract.py",
    "tools/p15/tests/test_async_job_contract.py",
    "tools/p15/tests/test_artifact_delivery_contract.py",
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
        raise ValueError("contract root must be an object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    if not 0 < resolved.stat().st_size <= 2_000_000:
        raise ValueError("source file shape is invalid")
    return resolved


def artifact_tool(catalog: dict[str, Any]) -> dict[str, Any] | None:
    tools = catalog.get("tools")
    if not isinstance(tools, list):
        return None
    matches = [tool for tool in tools if isinstance(tool, dict) and tool.get("name") == "artifact_get"]
    return matches[0] if len(matches) == 1 else None


def validate_p15_06_supersession(root: Path) -> list[str]:
    validator_path = root / P15_06_SUPERSEDING_VALIDATOR
    specification = importlib.util.spec_from_file_location(
        "p15_error_mapping_superseding_validator", validator_path
    )
    if specification is None or specification.loader is None:
        return ["p15_06_supersession.validator_load"]
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
        errors = module.validate(root)
    except Exception:
        return ["p15_06_supersession.validation"]
    if errors:
        return ["p15_06_supersession.contract"]
    return []


def historical_source_matches(root: Path, relative: str, expected: str) -> bool:
    result = subprocess.run(
        ["git", "show", f"{P15_05_AUDITED_REVISION}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    p15_06_supersession_errors = validate_p15_06_supersession(root)
    try:
        contract = load_json(root / CONTRACT_PATH.relative_to(ROOT))
    except Exception as error:
        return [f"contract.load:{type(error).__name__}"]
    if set(contract) != EXPECTED_KEYS:
        errors.append("contract.keys")
    if contract.get("schema_version") != "hwpx-agent.p15-artifact-delivery-contract/v1":
        errors.append("contract.schema_version")
    if contract.get("scope") != "current_pc_hancom_2020_local_artifact_delivery_reference":
        errors.append("contract.scope")
    if contract.get("target_profile") != "hancom-hangul-2020-secondary":
        errors.append("contract.target_profile")
    if contract.get("p15_04_audited_source_commit") != (
        "4c6224f6001c5daadaaaec907c0bba86db7c6c0f"
    ):
        errors.append("contract.predecessor")
    if contract.get("artifact_tool") != "artifact_get":
        errors.append("contract.artifact_tool")
    if contract.get("client_delivery_meta_key") != "hwpx/artifactDelivery":
        errors.append("contract.meta_key")
    if contract.get("content_attachment_type") != "resource_link":
        errors.append("contract.attachment_type")
    if contract.get("limits") != {
        "bindings": 65_536,
        "default_ttl_seconds": 120,
        "max_range_bytes": 67_108_864,
        "max_ttl_seconds": 900,
        "max_url_bytes": 2_048,
        "min_ttl_seconds": 30,
    }:
        errors.append("contract.limits")
    if contract.get("required_behaviors") != EXPECTED_BEHAVIORS:
        errors.append("contract.behaviors")
    if contract.get("rust_artifact_delivery_tests") != 13:
        errors.append("contract.rust_tests")

    catalog_path = root / "protocol/mcp/p15-public-tools-v1.json"
    try:
        catalog = load_json(catalog_path)
    except Exception:
        errors.append("catalog.load")
        catalog = {}
    expected_catalog = "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
    if contract.get("catalog_sha256") != expected_catalog or sha256(catalog_path) != expected_catalog:
        errors.append("contract.catalog_sha256")
    tool = artifact_tool(catalog)
    if tool is None:
        errors.append("catalog.artifact_get")
    else:
        input_schema = tool.get("inputSchema")
        output_schema = tool.get("outputSchema")
        if not isinstance(input_schema, dict) or not isinstance(output_schema, dict):
            errors.append("catalog.artifact_schema")
        else:
            ttl = input_schema.get("properties", {}).get("delivery_ttl_seconds")
            delivery = output_schema.get("properties", {}).get("delivery")
            if ttl != {"maximum": 900, "minimum": 30, "type": "integer"}:
                errors.append("catalog.ttl")
            if delivery != {
                "enum": ["metadata", "preview_in_meta", "attachment_in_content"],
                "type": "string",
            }:
                errors.append("catalog.delivery")
            if "signed_url" in json.dumps(output_schema, sort_keys=True).lower():
                errors.append("catalog.signed_url_exposure")

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
                if relative not in P15_06_SUPERSEDED_PATHS or p15_06_supersession_errors:
                    errors.append(f"source_lock[{index}].digest")
                elif not historical_source_matches(root, relative, expected):
                    errors.append(f"source_lock[{index}].historical_digest")

    source = (root / "crates/mcp-control-plane/src/artifact_delivery.rs").read_text(
        encoding="utf-8"
    )
    required_tokens = [
        'const DELIVERY_META_KEY: &str = "hwpx/artifactDelivery";',
        "SignedArtifactUrl(Zeroizing<String>)",
        ".verify_slice(&signature)",
        "binding_generation",
        "pub fn revoke(",
        "pub fn redeem_range(",
        "RangeNotSatisfiable",
        'strip_prefix("bytes=")',
        "ContentDigest::of(&payload)",
        '"resource_link"',
        '"hwpx-artifact://download/{}"',
        "StorageState::Available",
        "ValidationState::Verified",
        "ArtifactAuthScope::DocumentRead",
    ]
    for token in required_tokens:
        if token not in source:
            errors.append(f"artifact_delivery.token:{token}")
    for forbidden in ["unsafe {", "std::process", "Command::", "HAction", "raw_xml"]:
        if forbidden in source:
            errors.append(f"artifact_delivery.forbidden:{forbidden}")

    handler = (root / "crates/mcp-control-plane/src/handler.rs").read_text(encoding="utf-8")
    if handler.count("self.gateway.dispatch(call)") != 1:
        errors.append("handler.dispatch_count")
    for token in [
        "artifact_delivery.is_some() && tool != ToolKind::ArtifactGet",
        "output_is_valid(&output)",
        "correlation.matches(&output)",
        "delivery.append_to_result(&mut content, &mut meta)",
    ]:
        if token not in handler:
            errors.append(f"handler.token:{token}")
    order = [
        handler.find("self.gateway.dispatch(call)"),
        handler.find("output_is_valid(&output)"),
        handler.find("correlation.matches(&output)"),
        handler.find("delivery.append_to_result(&mut content, &mut meta)"),
    ]
    if any(position < 0 for position in order) or order != sorted(order):
        errors.append("handler.order")

    rust_tests = (root / "crates/mcp-control-plane/tests/artifact_delivery.rs").read_text(
        encoding="utf-8"
    )
    if rust_tests.count("#[test]") != 13:
        errors.append("rust_tests.count")
    for token in [
        "preview_keeps_signed_url_in_client_only_meta",
        "attachment_uses_resource_link_without_leaking_token_into_content",
        "project_binding_revocation_invalidates_an_issued_token",
        "current_acl_is_rechecked_when_token_is_redeemed",
        "closed_open_suffix_and_clamped_ranges_are_exact",
        "token_is_valid_through_expiry_then_rejected",
    ]:
        if token not in rust_tests:
            errors.append(f"rust_tests.token:{token}")
    return errors


def main() -> int:
    errors = validate()
    print(
        json.dumps(
            {
                "artifact_tool": "artifact_get",
                "errors": errors,
                "rust_artifact_delivery_tests": 13,
                "schema_version": "hwpx-agent.p15-artifact-delivery-validation/v1",
                "source_files": len(EXPECTED_SOURCE_PATHS),
                "state": "pass" if not errors else "fail",
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
