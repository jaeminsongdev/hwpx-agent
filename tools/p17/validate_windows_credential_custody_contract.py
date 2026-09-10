"""Validate the P17 Windows Credential Manager custody contract and evidence."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import sys
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = "protocol/private/p17-windows-credential-custody-v1.json"
EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-custody/"
    "p17-windows-credential-custody.current-20260911.v1.json"
)
EXPECTED_IMPLEMENTATION_FILES = [
    "Cargo.toml",
    "Cargo.lock",
    "crates/local-sync/src/adapter.rs",
    "crates/windows-credential-custody/Cargo.toml",
    "crates/windows-credential-custody/src/lib.rs",
    "crates/windows-credential-custody/tests/windows_credential_custody.rs",
    "implementation/p17/P17-06_WINDOWS_CREDENTIAL_CUSTODY_V18.md",
    EVIDENCE_RELATIVE,
    "protocol/migrations/p17-windows-credential-custody-v1.md",
    "tools/p17/tests/test_windows_credential_custody_contract.py",
    "tools/p17/validate_windows_credential_custody_contract.py",
]
EXPECTED_CHECKS = {
    "unique_target_preflight_absent": True,
    "synthetic_secret_written": True,
    "product_provider_read": True,
    "authorization_shape_accepted": True,
    "provider_single_attempt": True,
    "secret_persisted_after_read": True,
    "debug_redacted": True,
    "credential_deleted": True,
    "post_cleanup_absent": True,
}
EXPECTED_PRIVACY = {
    "raw_credential": False,
    "raw_authorization_header": False,
    "raw_target_name": False,
    "existing_credentials_enumerated": False,
    "user_document_accessed": False,
}
EXPECTED_CLAIMS = {
    "actual_current_pc_windows_credential_manager": True,
    "actual_local_persistence_write_read_delete": True,
    "persistent_credential_custody_mechanism": True,
    "synthetic_credential_only": True,
    "real_service_credential": False,
    "credential_issuance_or_rotation": False,
    "actual_remote_network": False,
    "registered_host": False,
    "production": False,
    "actual_hangul": False,
    "p17_06_complete": False,
    "product_complete": False,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ContractError(ValueError):
    """Bounded fail-closed validation error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError(code)


def load_json_strict(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    require(0 < len(raw) <= 131_072, f"{code}.size")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            require(key not in value, f"{code}.duplicate")
            value[key] = item
        return value

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError(f"{code}.json") from error
    require(isinstance(value, dict), f"{code}.object")
    return value, raw


def validate_relative(relative: str) -> None:
    require(
        isinstance(relative, str)
        and 0 < len(relative) <= 240
        and "\\" not in relative
        and ":" not in relative
        and "\0" not in relative,
        "path.shape",
    )
    value = PurePosixPath(relative)
    require(
        not value.is_absolute()
        and value.as_posix() == relative
        and all(part not in ("", ".", "..") for part in value.parts),
        "path.escape",
    )


def bounded_file(root: Path, relative: str) -> Path:
    validate_relative(relative)
    resolved_root = root.resolve(strict=True)
    cursor = resolved_root
    for part in relative.split("/"):
        cursor /= part
        require(
            not cursor.is_symlink()
            and not (hasattr(cursor, "is_junction") and cursor.is_junction()),
            "path.link",
        )
    path = cursor.resolve(strict=True)
    require(
        resolved_root in path.parents
        and path.is_file()
        and 0 < path.stat().st_size <= 4_000_000,
        "path.file",
    )
    return path


def validate_contract_document(contract: dict[str, Any]) -> None:
    require(
        contract.get("schema_version")
        == "hwpx-agent.windows-credential-custody-contract/v1",
        "contract.schema",
    )
    require(
        contract.get("scope")
        == "current_pc_windows_credential_manager_retrieval_component",
        "contract.scope",
    )
    platform = contract.get("platform")
    require(
        platform
        == {
            "operating_system": "Windows",
            "store": "Windows Credential Manager",
            "credential_type": "generic",
            "persistence": "local_machine_current_user_until_delete",
            "maximum_secret_bytes": 2560,
        },
        "contract.platform",
    )
    require(
        contract.get("dependencies")
        == {
            "keyring_core": "1.0.0",
            "windows_native_keyring_store": "1.1.0",
            "default_features": False,
            "target_dependency": "cfg(windows)",
        },
        "contract.dependencies",
    )
    locator = contract.get("locator")
    require(
        isinstance(locator, dict)
        and locator.get("service_and_account_are_opaque_non_secret_identifiers") is True
        and locator.get("maximum_bytes_each") == 120
        and locator.get("allowed_ascii") == "A-Z a-z 0-9 . _ -"
        and locator.get("target_template")
        == "hwpx-agent.remote-sync:{account}:{service}"
        and locator.get("target_is_debug_redacted") is True
        and locator.get("credential_enumeration") is False,
        "contract.locator",
    )
    retrieval = contract.get("retrieval")
    require(
        isinstance(retrieval, dict)
        and retrieval.get("product_write_or_delete_api") is False
        and retrieval.get("credential_contains") == "jwt_body_without_bearer_prefix"
        and retrieval.get("authorization_header_is_reconstructed_in_zeroizing_memory")
        is True
        and retrieval.get("retrieved_and_malformed_secret_bytes_are_zeroized") is True
        and retrieval.get("provider_attempts_per_instance") == 1
        and retrieval.get("unavailable_and_rejected_are_distinct") is True
        and retrieval.get("debug_discloses_secret_or_locator") is False,
        "contract.retrieval",
    )
    require(
        contract.get("implementation_files") == EXPECTED_IMPLEMENTATION_FILES,
        "contract.implementation_files",
    )
    evidence = contract.get("evidence")
    require(
        isinstance(evidence, dict)
        and evidence.get("path") == EVIDENCE_RELATIVE
        and evidence.get("exact_current_pc_synthetic_qualification") is True
        and evidence.get("routine_workspace_test_is_ignored") is True
        and evidence.get("explicit_qualification_test_passed") is True
        and evidence.get("owned_credential_cleaned") is True,
        "contract.evidence",
    )
    failures = contract.get("failure_policy")
    require(
        isinstance(failures, list)
        and len(failures) == 7
        and len(set(failures)) == len(failures),
        "contract.failure_policy",
    )
    authorities = contract.get("external_authorities")
    require(
        isinstance(authorities, list)
        and len(authorities) == 2
        and authorities[0].get("url")
        == "https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw"
        and authorities[1].get("url")
        == "https://docs.rs/windows-native-keyring-store/1.1.0/windows_native_keyring_store/",
        "contract.authorities",
    )
    require(
        contract.get("gate_decision")
        == {
            "component": "pass",
            "actual_current_pc_persistent_store_mechanism": True,
            "real_service_credential": False,
            "credential_issuance_or_rotation": False,
            "actual_remote_tls": False,
            "registered_host": False,
            "production": False,
            "p17_06_complete": False,
            "product_complete": False,
        },
        "contract.gate",
    )


def validate_evidence_document(evidence: dict[str, Any], raw: bytes) -> None:
    require(
        evidence.get("schema_version")
        == "hwpx-agent.windows-credential-custody-evidence/v1",
        "evidence.schema",
    )
    require(
        evidence.get("scope")
        == "current_pc_current_user_windows_credential_manager_synthetic_component",
        "evidence.scope",
    )
    target = evidence.get("target")
    require(
        target
        == {
            "operating_system": "Windows",
            "credential_store": "Windows Credential Manager",
            "persistence": "local_machine_current_user_until_delete",
            "keyring_core_version": "1.0.0",
            "windows_native_keyring_store_version": "1.1.0",
        },
        "evidence.target",
    )
    execution = evidence.get("execution")
    require(
        isinstance(execution, dict)
        and execution.get("test")
        == "current_user_store_is_persistent_redacted_and_single_attempt"
        and execution.get("locked") is True
        and execution.get("offline") is True
        and execution.get("passed") is True
        and HEX64.fullmatch(execution.get("credential_target_sha256", "")) is not None,
        "evidence.execution",
    )
    require(evidence.get("checks") == EXPECTED_CHECKS, "evidence.checks")
    require(evidence.get("privacy") == EXPECTED_PRIVACY, "evidence.privacy")
    require(evidence.get("claims") == EXPECTED_CLAIMS, "evidence.claims")
    require(
        b"Bearer " not in raw
        and b"aaa.bbb.ccc" not in raw
        and b"hwpx-agent.remote-sync:" not in raw,
        "evidence.raw_secret_or_target",
    )


def validate_source_state(root: Path, contract: dict[str, Any]) -> None:
    for relative in contract["implementation_files"]:
        bounded_file(root, relative)

    workspace = tomllib.loads(bounded_file(root, "Cargo.toml").read_text("utf-8"))
    dependencies = workspace.get("workspace", {}).get("dependencies", {})
    require(dependencies.get("keyring-core") == "=1.0.0", "source.keyring_core")
    require(
        dependencies.get("windows-native-keyring-store")
        == {"version": "=1.1.0", "default-features": False},
        "source.windows_store",
    )
    custody_manifest = tomllib.loads(
        bounded_file(root, "crates/windows-credential-custody/Cargo.toml").read_text("utf-8")
    )
    windows = custody_manifest.get("target", {}).get("cfg(windows)", {}).get(
        "dependencies", {}
    )
    require(
        windows.get("keyring-core") == {"workspace": True}
        and windows.get("windows-native-keyring-store") == {"workspace": True},
        "source.windows_target_dependencies",
    )
    lock = tomllib.loads(bounded_file(root, "Cargo.lock").read_text("utf-8"))
    versions = {
        package.get("name"): package.get("version") for package in lock.get("package", [])
    }
    require(
        versions.get("keyring-core") == "1.0.0"
        and versions.get("windows-native-keyring-store") == "1.1.0",
        "source.lock",
    )
    source = bounded_file(
        root, "crates/windows-credential-custody/src/lib.rs"
    ).read_text("utf-8")
    test = bounded_file(
        root, "crates/windows-credential-custody/tests/windows_credential_custody.rs"
    ).read_text("utf-8")
    for marker in [
        "const MAX_TOKEN_BYTES: usize = 2_560;",
        "Zeroizing::new",
        "A provider instance consumes its",
        "one retrieval attempt",
        "fn map_read_error",
        "CredentialFailure::Unavailable",
        "CredentialFailure::Rejected",
    ]:
        require(marker in source, "source.marker")
    for marker in [
        '#[ignore = "creates and deletes one unique synthetic Windows Credential Manager entry"]',
        '("persistence", "Local")',
        "Err(keyring_core::Error::NoEntry)",
        "HWPX_AGENT_CREDENTIAL_CUSTODY_RECEIPT=",
    ]:
        require(marker in test, "source.test_marker")


def verify(root: Path = ROOT) -> dict[str, Any]:
    contract, _ = load_json_strict(bounded_file(root, CONTRACT_RELATIVE), "contract")
    evidence, evidence_raw = load_json_strict(
        bounded_file(root, EVIDENCE_RELATIVE), "evidence"
    )
    validate_contract_document(contract)
    validate_evidence_document(evidence, evidence_raw)
    validate_source_state(root, contract)
    return {
        "schema_version": "hwpx-agent.windows-credential-custody-validation/v1",
        "state": "pass",
        "checked_files": len(EXPECTED_IMPLEMENTATION_FILES),
        "actual_current_pc_store_mechanism": True,
        "real_service_credential": False,
        "actual_remote_network": False,
        "production": False,
        "p17_06_complete": False,
        "product_complete": False,
    }


def main() -> int:
    try:
        result = verify()
    except (ContractError, OSError, tomllib.TOMLDecodeError) as error:
        print(f"P17_WINDOWS_CREDENTIAL_CUSTODY_FAIL:{error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
