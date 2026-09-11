"""Validate the exact P17 credential issuer transport, broker and current-PC evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = "protocol/private/p17-remote-credential-broker-v1.json"
EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v2.json"
)
PREDECESSOR_EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v1.json"
)
PREDECESSOR_EVIDENCE_SHA256 = (
    "2eb5b8ae7db88fb2a79227e8fc3ab966e5415e0107bbde0de2e6a2b49a903af3"
)
BROKER_SOURCE = "crates/remote-credential-broker/src/lib.rs"
WIRE_SOURCE = "crates/remote-credential-wire/src/lib.rs"
TLS_SOURCE = "crates/remote-tls-transport/src/lib.rs"
WINDOWS_SOURCE = "crates/windows-credential-custody/src/lib.rs"
BROKER_TESTS = {
    "append_only_file_store_reopens_and_detects_record_tamper",
    "authenticated_definitive_rejection_alone_restores_prior_state",
    "authorization_and_all_debug_outputs_are_bounded_and_redacted",
    "durable_record_unknown_duplicate_noncanonical_and_chain_drift_are_rejected",
    "issuer_response_is_canonical_request_bound_and_redacted",
    "issue_persists_pending_and_prepared_before_stable_vault_state",
    "issue_refresh_rotate_and_revoke_share_one_exact_recovery_model",
    "policy_drift_or_orphaned_vault_fails_closed_without_overwrite",
    "prepared_access_recovers_before_and_after_ambiguous_vault_write",
    "refresh_rejection_preserves_exact_active_state_and_vault",
    "revocation_delete_ambiguity_recovers_to_terminal_state",
    "unavailable_peer_and_invalid_responses_never_restore_pending",
    "vault_write_then_stable_append_failure_recovers_without_reissue",
}
EXPECTED_IMPLEMENTATION_FILES = [
    "Cargo.toml",
    "Cargo.lock",
    "crates/remote-credential-lifecycle/Cargo.toml",
    "crates/remote-credential-lifecycle/src/lib.rs",
    "crates/remote-credential-lifecycle/tests/lifecycle.rs",
    "crates/remote-credential-wire/Cargo.toml",
    WIRE_SOURCE,
    "crates/remote-credential-broker/Cargo.toml",
    BROKER_SOURCE,
    "crates/remote-tls-transport/Cargo.toml",
    TLS_SOURCE,
    "crates/remote-tls-transport/tests/credential_issuer_tls.rs",
    "crates/windows-credential-custody/Cargo.toml",
    WINDOWS_SOURCE,
    "crates/windows-credential-custody/tests/windows_credential_custody.rs",
    "crates/windows-credential-custody/tests/windows_broker_tls.rs",
    "implementation/p17/P17-06_REMOTE_CREDENTIAL_BROKER_V22.md",
    PREDECESSOR_EVIDENCE_RELATIVE,
    EVIDENCE_RELATIVE,
    "protocol/migrations/p17-remote-credential-broker-v1.md",
    CONTRACT_RELATIVE,
    "tools/p17/run_windows_credential_broker_qualification.py",
    "tools/p17/tests/test_remote_credential_broker_contract.py",
    "tools/p17/validate_remote_credential_broker_contract.py",
]
EXPECTED_WIRE = {
    "request_magic": "HWPXCIQ1",
    "response_magic": "HWPXCIP1",
    "distinct_from_remote_sync_wire": True,
    "maximum_authorization_bytes": 8199,
    "maximum_request_bytes": 16384,
    "maximum_response_bytes": 8192,
    "credential_bearing_response_buffer_zeroized": True,
    "completed_response_requires_payload": True,
    "unavailable_response_requires_empty_payload": True,
}
EXPECTED_TRANSPORT = {
    "tls_version": "1.3_only",
    "ambient_trust_roots": False,
    "exact_leaf_certificate_sha256_pin": True,
    "dns_name_validity_signature_checks_retained": True,
    "endpoint_scopes": ["public_remote", "loopback_qualification"],
    "issuer_client_authorization": (
        "provider_supplied_bounded_compact_jws_bearer_per_exchange"
    ),
    "client_assertion_signature_or_freshness_qualified": False,
    "response_schema": "hwpx-agent.remote-credential-issuer-response/v1",
    "response_canonical_json": True,
    "response_request_sha256_bound": True,
    "outcomes": ["access", "revocation", "rejected"],
    "authenticated_explicit_rejection_is_definitive": True,
    "tls_frame_trailing_digest_or_json_failure_is_definitive": False,
}
EXPECTED_BROKER = {
    "operations": ["issue", "refresh", "rotate", "revoke"],
    "record_schema": "hwpx-agent.remote-credential-broker-record/v1",
    "maximum_record_bytes": 65536,
    "maximum_log_records": 65536,
    "phases": [
        "stable",
        "awaiting_issuer",
        "prepared_access",
        "prepared_revocation",
    ],
    "policy_binding_in_every_record": True,
    "complete_prior_nonsecret_state_in_pending": True,
    "raw_access_token_in_state_log": False,
    "pending_persisted_before_dispatch": True,
    "verified_metadata_persisted_before_vault_write_or_delete": True,
    "vault_result_observed_before_stable_commit": True,
    "only_definitive_rejection_restores_prior_state": True,
    "unavailable_peer_or_protocol_failure_retains_pending": True,
}
EXPECTED_STATE_STORE = {
    "mode": "append_only_immutable_records",
    "same_directory_synced_temporary_file": True,
    "no_overwrite_hard_link_publication": True,
    "compare_and_append_revision": True,
    "contiguous_sequence_required": True,
    "record_sha256_in_filename": True,
    "canonical_json_required": True,
    "unknown_duplicate_noncanonical_or_policy_drift": "reject",
    "cross_system_transaction_claimed": False,
    "process_crash_reconciliation_modeled": True,
    "power_loss_durability_qualified": False,
}
EXPECTED_WINDOWS = {
    "store": "Windows Credential Manager",
    "credential_type": "generic",
    "persistence": "local_machine_current_user_until_delete",
    "maximum_secret_bytes": 2560,
    "credential_contains": "jwt_body_without_bearer_prefix",
    "exact_target_only": True,
    "credential_enumeration": False,
    "observe_returns_only_absence_or_sha256": True,
    "store_and_delete_available_only_through_broker_vault_boundary": True,
    "retrieval_provider_remains_single_attempt": True,
    "secret_and_locator_debug_redacted": True,
}
EXPECTED_RECOVERY = {
    "vault_has_prepared_access_digest": "commit_active_without_second_issuer_call",
    "vault_has_prior_digest_after_prepared_access": (
        "replay_exact_request_and_require_exact_metadata"
    ),
    "vault_absent_after_prepared_revocation": "commit_terminal_revocation",
    "vault_has_prior_digest_after_prepared_revocation": (
        "delete_exact_target_then_observe_absence"
    ),
    "unexpected_vault_digest": "fail_closed_without_state_overwrite",
    "expired_awaiting_request": "retain_pending_and_fail_closed",
}
EXPECTED_DEPENDENCIES = {
    "getrandom": "0.4.3",
    "keyring_core": "1.0.0",
    "ring": "0.17.14",
    "rustls": "0.23.43",
    "serde": "1.0.229",
    "serde_json": "1.0.151",
    "sha2": "0.11.0",
    "windows_native_keyring_store": "1.1.0",
    "zeroize": "1.9.0",
}
EXPECTED_CHECKS = {
    "access_jws_verified": True,
    "append_only_records": 7,
    "issuer_request_digest_bound": True,
    "pending_persisted_before_dispatch": True,
    "post_cleanup_absent": True,
    "product_provider_read": True,
    "product_vault_deleted": True,
    "product_vault_written_and_observed": True,
    "revocation_jws_verified": True,
    "unique_target_preflight_absent": True,
}
EXPECTED_PRIVACY = {
    "raw_access_token_persisted_outside_vault": False,
    "raw_authorization_header_in_evidence": False,
    "raw_target_name_in_evidence": False,
    "existing_credentials_enumerated": False,
    "user_document_accessed": False,
}
EXPECTED_CLAIMS = {
    "actual_current_pc_broker_issue_and_revoke": True,
    "actual_current_pc_windows_vault_write_read_delete": True,
    "actual_pinned_loopback_tls_1_3": True,
    "actual_windows_refresh_or_rotate": False,
    "append_only_vault_state_reconciliation": True,
    "external_issuer": False,
    "external_remote_network": False,
    "p17_06_complete": False,
    "power_loss_durability_qualified": False,
    "product_complete": False,
    "production": False,
    "real_service_credential": False,
    "registered_host": False,
    "synthetic_ephemeral_issuer_only": True,
}
EXPECTED_RUNTIME_CLAIMS = {
    "existing_credentials_enumerated": False,
    "external_remote_network": False,
    "loopback_transport_only": True,
    "p17_06_complete": False,
    "product_complete": False,
    "production": False,
    "real_service_credential": False,
    "registered_host": False,
    "synthetic_ephemeral_issuer_only": True,
}
EXPECTED_GATE = {
    "component": "pass",
    "current_pc_pure_failure_recovery_model": True,
    "current_pc_pinned_loopback_issuer_transport": True,
    "current_pc_windows_vault_state_issue_revoke": True,
    "actual_windows_refresh_or_rotate": False,
    "power_loss_durability": False,
    "external_issuer": False,
    "external_remote_network": False,
    "real_client_assertion": False,
    "real_service_credential": False,
    "registered_host": False,
    "production": False,
    "p17_06_complete": False,
    "product_complete": False,
}
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ContractError(ValueError):
    """Bounded fail-closed validation error."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError(code)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


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
        and 0 < len(relative) <= 260
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
        == "hwpx-agent.remote-credential-broker-contract/v1",
        "contract.schema",
    )
    require(
        contract.get("scope")
        == "current_pc_pinned_issuer_transport_and_recoverable_windows_vault_state_component",
        "contract.scope",
    )
    require(contract.get("wire") == EXPECTED_WIRE, "contract.wire")
    require(
        contract.get("issuer_transport") == EXPECTED_TRANSPORT,
        "contract.transport",
    )
    require(contract.get("broker") == EXPECTED_BROKER, "contract.broker")
    require(
        contract.get("state_store") == EXPECTED_STATE_STORE,
        "contract.state_store",
    )
    require(contract.get("windows_vault") == EXPECTED_WINDOWS, "contract.windows")
    require(contract.get("recovery") == EXPECTED_RECOVERY, "contract.recovery")
    require(
        contract.get("dependencies") == EXPECTED_DEPENDENCIES,
        "contract.dependencies",
    )
    require(
        contract.get("implementation_files") == EXPECTED_IMPLEMENTATION_FILES,
        "contract.implementation_files",
    )
    require(
        contract.get("evidence")
        == {
            "path": EVIDENCE_RELATIVE,
            "predecessor_path": PREDECESSOR_EVIDENCE_RELATIVE,
            "predecessor_sha256": PREDECESSOR_EVIDENCE_SHA256,
            "routine_workspace_side_effect_test_is_ignored": True,
            "explicit_current_pc_qualification_passed": True,
            "unique_owned_credential_cleaned": True,
            "synthetic_loopback_issuer_only": True,
        },
        "contract.evidence",
    )
    authorities = contract.get("external_authorities")
    require(
        isinstance(authorities, list)
        and [item.get("url") for item in authorities]
        == [
            "https://www.rfc-editor.org/rfc/rfc6749.html",
            "https://www.rfc-editor.org/rfc/rfc8725.html",
            "https://learn.microsoft.com/en-us/windows/win32/api/wincred/ns-wincred-credentialw",
        ],
        "contract.authorities",
    )
    require(contract.get("gate_decision") == EXPECTED_GATE, "contract.gate")


def validate_evidence_document(
    root: Path, evidence: dict[str, Any], raw: bytes
) -> None:
    require(raw == canonical(evidence), "evidence.canonical")
    require(
        evidence.get("schema_version")
        == "hwpx-agent.remote-credential-broker-evidence/v1",
        "evidence.schema",
    )
    require(
        evidence.get("scope")
        == "current_pc_pinned_loopback_issuer_windows_vault_state_component",
        "evidence.scope",
    )
    require(
        evidence.get("predecessor_evidence")
        == {
            "path": PREDECESSOR_EVIDENCE_RELATIVE,
            "sha256": PREDECESSOR_EVIDENCE_SHA256,
        },
        "evidence.predecessor",
    )
    predecessor_raw = bounded_file(root, PREDECESSOR_EVIDENCE_RELATIVE).read_bytes()
    require(
        hashlib.sha256(predecessor_raw).hexdigest() == PREDECESSOR_EVIDENCE_SHA256,
        "evidence.predecessor_sha256",
    )
    require(
        evidence.get("target")
        == {
            "operating_system": "Windows",
            "credential_store": "Windows Credential Manager",
            "state_store": "append_only_synced_no_overwrite_hard_link_log",
            "transport": "pinned_leaf_tls_1_3_loopback",
            "issuer": "synthetic_ephemeral_ed25519",
        },
        "evidence.target",
    )
    execution = evidence.get("execution")
    require(isinstance(execution, dict), "evidence.execution")
    run_id = execution.get("run_id", "")
    receipt_relative = execution.get("receipt_path", "")
    require(
        HEX32.fullmatch(run_id) is not None
        and execution.get("test")
        == "current_user_broker_pinned_tls_issue_and_revoke"
        and execution.get("locked") is True
        and execution.get("offline") is True
        and execution.get("passed") is True
        and HEX64.fullmatch(execution.get("receipt_sha256", "")) is not None
        and HEX64.fullmatch(execution.get("credential_target_sha256", "")) is not None
        and receipt_relative
        == f"artifacts/p17/windows-credential-broker-runs/{run_id}/receipt.json",
        "evidence.execution",
    )
    require(
        evidence.get("evidence_id")
        == f"p17.remote-credential-broker.current-20260911.{run_id[:8]}",
        "evidence.id",
    )
    require(evidence.get("checks") == EXPECTED_CHECKS, "evidence.checks")
    require(evidence.get("privacy") == EXPECTED_PRIVACY, "evidence.privacy")
    require(evidence.get("claims") == EXPECTED_CLAIMS, "evidence.claims")
    receipt, receipt_raw = load_json_strict(
        bounded_file(root, receipt_relative), "receipt"
    )
    require(receipt_raw == canonical(receipt), "receipt.canonical")
    require(
        hashlib.sha256(receipt_raw).hexdigest() == execution["receipt_sha256"]
        and receipt.get("schema_version")
        == "hwpx-agent.windows-credential-broker-runtime/v1"
        and receipt.get("backend") == "windows_credential_manager"
        and receipt.get("transport") == "pinned_loopback_tls_1_3"
        and receipt.get("credential_target_sha256")
        == execution["credential_target_sha256"]
        and receipt.get("checks") == EXPECTED_CHECKS
        and receipt.get("claims") == EXPECTED_RUNTIME_CLAIMS,
        "receipt.contract",
    )
    for content in (raw, predecessor_raw, receipt_raw):
        require(
            b"Bearer " not in content
            and b"aaa.bbb.ccc" not in content
            and b"hwpx-agent.remote-sync:" not in content
            and b"BEGIN PRIVATE KEY" not in content,
            "evidence.secret_or_target",
        )


def validate_source_text(
    broker: str, wire: str, tls: str, windows: str, tests: str
) -> None:
    for marker in [
        "const MAX_RECORD_BYTES: usize = 65_536;",
        "const MAX_LOG_RECORDS: u64 = 65_536;",
        "enum DurablePhase",
        "AwaitingIssuer",
        "PreparedAccess",
        "PreparedRevocation",
        "temporary.sync_all()",
        "fs::hard_link",
        "create_new(true)",
        "validate_stored_history(&records)",
        "valid_temporary_name(&name)",
        "pending.retry_request",
        "IssuerReply::DefinitiveRejection",
        "self.require_vault_matches_state",
        "validate_prepared_access",
        "validate_prepared_revocation",
        'formatter.write_str("IssuerSecret(<redacted>)")',
    ]:
        require(marker in broker, "source.broker_marker")
    names = set(re.findall(r"(?m)^\s*fn ([a-z0-9_]+)\(\) \{", broker))
    require(BROKER_TESTS <= names, "source.broker_tests")
    for marker in [
        'b"HWPXCIQ1"',
        'b"HWPXCIP1"',
        "pub const MAX_RESPONSE_BYTES: usize = 8_192;",
        "payload: Zeroizing<Vec<u8>>",
        "ResponseStatus::Completed",
        "ResponseStatus::Unavailable",
    ]:
        require(marker in wire, "source.wire_marker")
    for marker in [
        "pub struct PinnedCredentialIssuerTlsTransport",
        "CredentialIssuerTransport for PinnedCredentialIssuerTlsTransport",
        "with_protocol_versions(&[&version::TLS13])",
        "with_root_certificates(roots)",
        "actual_leaf_sha256 != self.expected_leaf_sha256",
        "parse_issuer_response(request, payload)",
        "CredentialResponseStatus::Unavailable",
    ]:
        require(marker in tls, "source.tls_marker")
    require(
        tls.count("with_protocol_versions(&[&version::TLS13])") == 2,
        "source.tls13_count",
    )
    for marker in [
        "pub struct WindowsCredentialManagerVault",
        "impl CredentialVault for WindowsCredentialManagerVault",
        "fn observe(&mut self)",
        "fn store(&mut self, credential: &str)",
        "fn delete(&mut self)",
        '("persistence", "Local")',
        "credential_sha256: hex::encode(Sha256::digest",
    ]:
        require(marker in windows, "source.windows_marker")
    for marker in [
        '#[ignore = "creates and deletes one unique synthetic Windows Credential Manager entry"]',
        "fn current_user_broker_pinned_tls_issue_and_revoke()",
        "HWPX_AGENT_WINDOWS_CREDENTIAL_BROKER_RECEIPT=",
        "assert_eq!(record_count, 7);",
    ]:
        require(marker in tests, "source.windows_test_marker")
    require(
        "#![forbid(unsafe_code)]" in broker
        and "#![forbid(unsafe_code)]" in wire
        and "unsafe {" not in broker
        and "unsafe fn" not in broker
        and "unsafe {" not in wire
        and "unsafe fn" not in wire,
        "source.unsafe",
    )


def validate_source_state(root: Path, contract: dict[str, Any]) -> None:
    for relative in contract["implementation_files"]:
        bounded_file(root, relative)
    workspace = tomllib.loads(bounded_file(root, "Cargo.toml").read_text("utf-8"))
    members = workspace.get("workspace", {}).get("members", [])
    dependencies = workspace.get("workspace", {}).get("dependencies", {})
    require(
        "crates/remote-credential-broker" in members
        and "crates/remote-credential-wire" in members,
        "source.workspace_members",
    )
    expected_workspace = {
        "getrandom": {"version": "=0.4.3", "features": ["std"]},
        "keyring-core": "=1.0.0",
        "ring": "=0.17.14",
        "rustls": {
            "version": "=0.23.43",
            "default-features": False,
            "features": ["ring", "std"],
        },
        "serde": {"version": "=1.0.229", "features": ["derive"]},
        "serde_json": "=1.0.151",
        "sha2": "=0.11.0",
        "windows-native-keyring-store": {
            "version": "=1.1.0",
            "default-features": False,
        },
        "zeroize": "=1.9.0",
    }
    for name, expected in expected_workspace.items():
        require(dependencies.get(name) == expected, f"source.dependency.{name}")
    lock = tomllib.loads(bounded_file(root, "Cargo.lock").read_text("utf-8"))
    versions = {
        package.get("name"): package.get("version") for package in lock.get("package", [])
    }
    lock_names = {
        "keyring_core": "keyring-core",
        "windows_native_keyring_store": "windows-native-keyring-store",
    }
    for name, version in EXPECTED_DEPENDENCIES.items():
        require(
            versions.get(lock_names.get(name, name)) == version,
            f"source.lock.{name}",
        )
    validate_source_text(
        bounded_file(root, BROKER_SOURCE).read_text("utf-8"),
        bounded_file(root, WIRE_SOURCE).read_text("utf-8"),
        bounded_file(root, TLS_SOURCE).read_text("utf-8"),
        bounded_file(root, WINDOWS_SOURCE).read_text("utf-8"),
        bounded_file(
            root, "crates/windows-credential-custody/tests/windows_broker_tls.rs"
        ).read_text("utf-8"),
    )
    runner = bounded_file(
        root, "tools/p17/run_windows_credential_broker_qualification.py"
    ).read_text("utf-8")
    require(
        'with path.open("xb")' in runner
        and "if EVIDENCE.exists():" in runner
        and '"--ignored"' in runner
        and '"--locked"' in runner
        and '"--offline"' in runner,
        "source.runner",
    )


def verify(root: Path = ROOT) -> dict[str, Any]:
    contract, _ = load_json_strict(bounded_file(root, CONTRACT_RELATIVE), "contract")
    evidence, evidence_raw = load_json_strict(
        bounded_file(root, EVIDENCE_RELATIVE), "evidence"
    )
    validate_contract_document(contract)
    validate_evidence_document(root, evidence, evidence_raw)
    validate_source_state(root, contract)
    return {
        "schema_version": "hwpx-agent.remote-credential-broker-validation/v1",
        "state": "pass",
        "checked_files": len(EXPECTED_IMPLEMENTATION_FILES),
        "broker_rust_tests": len(BROKER_TESTS),
        "current_pc_windows_issue_revoke": True,
        "pinned_loopback_tls": True,
        "external_issuer": False,
        "real_service_credential": False,
        "power_loss_durability": False,
        "production": False,
        "p17_06_complete": False,
        "product_complete": False,
    }


def main() -> int:
    try:
        result = verify()
    except (ContractError, OSError, tomllib.TOMLDecodeError) as error:
        print(f"P17_REMOTE_CREDENTIAL_BROKER_FAIL:{error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
