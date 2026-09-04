from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-handler-contract-v1.json"
EXPECTED_KEYS = {
    "catalog_sha256",
    "error_envelope_version",
    "handler_sequence",
    "jsonschema_crate",
    "limits",
    "rust_contract_tests",
    "schema_version",
    "scope",
    "source_locks",
    "target_profile",
}
EXPECTED_SEQUENCE = [
    "transport_admission",
    "authenticate_public_user",
    "parse_unique_json",
    "validate_input_schema",
    "authorize_tenant_project_subject",
    "dispatch_exactly_once",
    "validate_output_schema",
    "validate_result_correlation",
    "return_bounded_mcp_result",
]
P15_03_IMPLEMENTATION_REVISION = "9e7ed73524be0049292fbdf45f2170df6f997fae"
P15_04_SUPERSEDING_VALIDATOR = "tools/p15/validate_async_job_contract.py"
P15_04_SUPERSEDED_PATHS = {
    "Cargo.lock",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "tools/p15/build_handler_contract.py",
    "tools/p15/validate_handler_contract.py",
}


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
    candidate = (root / value).resolve(strict=True)
    if resolved_root not in candidate.parents or not candidate.is_file():
        raise ValueError("source path escapes repository")
    if candidate.is_symlink() or not 0 < candidate.stat().st_size <= 2_000_000:
        raise ValueError("source file shape is invalid")
    return candidate


def validate_p15_04_supersession(root: Path) -> list[str]:
    validator_path = root / P15_04_SUPERSEDING_VALIDATOR
    specification = importlib.util.spec_from_file_location(
        "p15_async_job_superseding_validator", validator_path
    )
    if specification is None or specification.loader is None:
        return ["p15_04_supersession.validator_load"]
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
        errors = module.validate(root)
    except Exception:
        return ["p15_04_supersession.validation"]
    if errors:
        return ["p15_04_supersession.contract"]
    return []


def historical_source_matches(root: Path, relative: str, expected: str) -> bool:
    result = subprocess.run(
        ["git", "show", f"{P15_03_IMPLEMENTATION_REVISION}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    p15_04_supersession_errors = validate_p15_04_supersession(root)
    try:
        contract = load_json(root / CONTRACT_PATH.relative_to(ROOT))
    except Exception as error:
        return [f"contract.load:{type(error).__name__}"]
    if set(contract) != EXPECTED_KEYS:
        errors.append("contract.keys")
    if contract.get("schema_version") != "hwpx-agent.p15-handler-contract/v1":
        errors.append("contract.schema_version")
    if contract.get("scope") != "current_pc_hancom_2020_in_process_reference_handlers":
        errors.append("contract.scope")
    if contract.get("target_profile") != "hancom-hangul-2020-secondary":
        errors.append("contract.target_profile")
    if contract.get("handler_sequence") != EXPECTED_SEQUENCE:
        errors.append("contract.sequence")
    if contract.get("limits") != {
        "argument_json_bytes": 262_144,
        "policy_memberships": 16_384,
        "policy_projects": 4_096,
        "public_tools": 18,
    }:
        errors.append("contract.limits")
    if contract.get("jsonschema_crate") != {
        "default_features": False,
        "version": "0.53.0",
    }:
        errors.append("contract.jsonschema")
    catalog_path = root / "protocol/mcp/p15-public-tools-v1.json"
    if contract.get("catalog_sha256") != sha256(catalog_path):
        errors.append("contract.catalog_sha256")

    locks = contract.get("source_locks")
    if not isinstance(locks, list) or len(locks) != 19:
        errors.append("contract.source_locks")
    else:
        seen: set[str] = set()
        for index, entry in enumerate(locks):
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                errors.append(f"source_lock[{index}].shape")
                continue
            relative = entry.get("path")
            expected = entry.get("sha256")
            if not isinstance(relative, str) or relative in seen:
                errors.append(f"source_lock[{index}].path")
                continue
            seen.add(relative)
            try:
                source = bounded_file(root, relative)
            except Exception:
                errors.append(f"source_lock[{index}].bounded")
                continue
            if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
                errors.append(f"source_lock[{index}].digest_shape")
            elif sha256(source) != expected:
                if relative not in P15_04_SUPERSEDED_PATHS or p15_04_supersession_errors:
                    errors.append(f"source_lock[{index}].digest")
                elif not historical_source_matches(root, relative, expected):
                    errors.append(f"source_lock[{index}].historical_digest")

    handler = (root / "crates/mcp-control-plane/src/handler.rs").read_text(encoding="utf-8")
    sequence_tokens = [
        "authenticate_public_mcp(",
        "parse_unique_value(",
        "input_is_valid(",
        ".policy.authorize(",
        ".gateway.dispatch(",
        "output_is_valid(",
        "correlation.matches(",
        "McpToolResult::success(",
    ]
    positions = [handler.find(token) for token in sequence_tokens]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        errors.append("handler.execution_order")
    for forbidden in ["unsafe {", "std::process", "Command::", "HAction", "raw_xml"]:
        if forbidden in handler:
            errors.append(f"handler.forbidden:{forbidden}")
    if handler.count("self.gateway.dispatch(call)") != 1:
        errors.append("handler.dispatch_count")
    if handler.count("Zeroizing") < 3:
        errors.append("handler.zeroizing_buffers")

    strict_json = (root / "crates/mcp-control-plane/src/strict_json.rs").read_text(
        encoding="utf-8"
    )
    if "duplicate JSON object key" not in strict_json or "deserializer.end()" not in strict_json:
        errors.append("strict_json.boundary")

    crate_toml = (root / "crates/mcp-control-plane/Cargo.toml").read_text(encoding="utf-8")
    workspace_toml = (root / "Cargo.toml").read_text(encoding="utf-8")
    if "jsonschema.workspace = true" not in crate_toml:
        errors.append("crate.jsonschema_dependency")
    if not re.search(
        r'jsonschema\s*=\s*\{\s*version\s*=\s*"=0\.53\.0",\s*default-features\s*=\s*false\s*\}',
        workspace_toml,
    ):
        errors.append("workspace.jsonschema_pin")

    rust_tests = (root / "crates/mcp-control-plane/tests/handler_contract.rs").read_text(
        encoding="utf-8"
    )
    observed_tests = rust_tests.count("#[test]")
    if contract.get("rust_contract_tests") != observed_tests or observed_tests != 16:
        errors.append("contract.rust_test_count")
    return errors


def main() -> int:
    errors = validate()
    print(
        json.dumps(
            {
                "errors": errors,
                "handler_sequence_steps": len(EXPECTED_SEQUENCE),
                "rust_contract_tests": 16,
                "schema_version": "hwpx-agent.p15-handler-validation/v1",
                "source_files": 19,
                "state": "pass" if not errors else "fail",
                "tools": 18,
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
