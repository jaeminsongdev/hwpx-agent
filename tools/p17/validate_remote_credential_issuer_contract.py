"""Validate the exact P17 independently bound credential issuer component."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import sys
import tomllib
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = "protocol/private/p17-remote-credential-issuer-v1.json"
EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-issuer/"
    "p17-remote-credential-issuer.current-20260911.v1.json"
)
ISSUER_SOURCE = "crates/remote-credential-issuer/src/lib.rs"
ISSUER_TEST_SOURCE = "crates/remote-credential-issuer/tests/issuer.rs"
ISSUER_MANIFEST = "crates/remote-credential-issuer/Cargo.toml"

EXPECTED_IMPLEMENTATION_FILES = [
    "Cargo.toml",
    "Cargo.lock",
    ISSUER_MANIFEST,
    ISSUER_SOURCE,
    ISSUER_TEST_SOURCE,
    "crates/remote-credential-lifecycle/src/lib.rs",
    "crates/remote-credential-broker/src/lib.rs",
    "crates/remote-credential-wire/src/lib.rs",
    "crates/remote-tls-transport/src/lib.rs",
    "implementation/p17/P17-06_REMOTE_CREDENTIAL_ISSUER_V23.md",
    EVIDENCE_RELATIVE,
    "protocol/migrations/p17-remote-credential-issuer-v1.md",
    CONTRACT_RELATIVE,
    "tools/p17/tests/test_remote_credential_issuer_contract.py",
    "tools/p17/validate_remote_credential_issuer_contract.py",
]
ISSUER_TESTS = {
    "append_failure_is_unavailable_and_retry_commits_once",
    "assertion_jti_cannot_authorize_a_different_request",
    "assertion_signature_identity_time_and_request_binding_fail_closed",
    "durable_and_memory_history_tamper_fail_unavailable",
    "durable_store_bounds_abandoned_temporary_files",
    "durable_store_allows_only_one_writer_per_sequence_slot",
    "durable_store_reopens_and_replays_without_secret_state",
    "exact_assertion_retry_is_byte_exact_without_second_record",
    "fresh_assertion_retry_is_durable_and_byte_exact",
    "independent_tls13_server_interoperates_with_pinned_client",
    "invalid_state_transition_never_calls_signer_or_mutates_state",
    "issue_refresh_rotate_and_revoke_are_exact_and_client_verifiable",
    "malformed_noncanonical_and_policy_drifted_requests_are_rejected",
    "policy_bounds_and_debug_output_are_fail_closed_and_redacted",
    "signer_failures_are_unavailable_without_records",
    "tls_server_configuration_and_bind_scope_fail_closed",
    "wire_adapter_maps_completed_rejection_and_unavailable",
}
EXPECTED_AUTHENTICATION = {
    "authorization_scheme": "Bearer",
    "compact_jws_maximum_bytes": 8192,
    "algorithm": "EdDSA",
    "type": "hwpx-agent-issuer-client+jwt",
    "maximum_client_keys": 8,
    "canonical_unpadded_base64url": True,
    "canonical_json_and_unknown_field_rejection": True,
    "exact_key_id_issuer_subject_audience_scope": True,
    "required_scope": "credential.manage",
    "exact_request_sha256_binding": True,
    "jti_length_range": [16, 120],
    "nbf_equals_iat": True,
    "maximum_assertion_lifetime_seconds": 600,
    "clock_skew_seconds_ceiling": 300,
    "jti_may_authorize_only_one_request": True,
    "signature_verified_before_claim_acceptance": True,
}
EXPECTED_LIFECYCLE = {
    "request_schema": "hwpx-agent.remote-credential-lifecycle-request/v1",
    "request_maximum_bytes": 16384,
    "request_age_seconds_range": [30, 600],
    "operations": ["issue", "refresh", "rotate", "revoke"],
    "issue": "absent_to_generation_1_key_generation_1",
    "refresh": "active_increments_generation_only",
    "rotate": "active_increments_generation_and_key_generation",
    "revoke": "active_to_terminal_revoked",
    "invalid_state_rejected_before_signer": True,
    "client_lifecycle_cross_compatibility_tested": True,
}
EXPECTED_SIGNING = {
    "response_schema": "hwpx-agent.remote-credential-issuer-response/v1",
    "response_maximum_bytes": 8192,
    "access_type": "hwpx-agent-service+jwt",
    "revocation_type": "hwpx-agent-revocation+jwt",
    "service_scope": "mirror.sync",
    "operator_supplied_signer_boundary": True,
    "signer_exact_key_id_required": True,
    "returned_signature_reverified_with_pinned_public_key": True,
    "raw_private_signing_key_owned_by_core": False,
    "response_request_sha256_bound": True,
    "retry_rebuild_must_match_recorded_response_sha256": True,
    "explicit_request_bound_rejection_only": True,
}
EXPECTED_STATE_STORE = {
    "record_schema": "hwpx-agent.remote-credential-issuer-record/v1",
    "mode": "append_only_immutable_record_per_file",
    "maximum_record_bytes": 65536,
    "maximum_log_records": 65536,
    "maximum_abandoned_temporary_files": 64,
    "same_directory_synced_temporary_file": True,
    "fixed_sequence_only_final_slot": True,
    "no_overwrite_hard_link_publication": True,
    "compare_and_append_revision": True,
    "concurrent_same_sequence_single_winner": True,
    "contiguous_sequence_required": True,
    "canonical_json_required": True,
    "policy_predecessor_state_response_and_signer_bound": True,
    "same_assertion_retry_adds_record": False,
    "fresh_assertion_retry_adds_replay_record": True,
    "raw_assertion_operation_id_token_or_receipt_stored": False,
    "process_restart_recovery_modeled": True,
    "directory_fsync_or_power_loss_qualified": False,
    "hostile_privileged_rewrite_resistance_claimed": False,
    "cross_system_transaction_claimed": False,
}
EXPECTED_TRANSPORT = {
    "wire_request_magic": "HWPXCIQ1",
    "wire_response_magic": "HWPXCIP1",
    "tls_version": "1.3_only",
    "opaque_bounded_certificate_and_private_key_config": True,
    "leaf_certificate_sha256_exposed_for_out_of_band_pin": True,
    "certificate_chain_count_range": [1, 4],
    "certificate_chain_maximum_bytes": 65536,
    "private_key_maximum_bytes": 16384,
    "bind_scopes": ["explicit_deployment", "loopback_qualification"],
    "explicit_deployment_requires_exact_nonloopback_nonzero_endpoint": True,
    "one_framed_exchange_per_accepted_connection": True,
    "pinned_client_loopback_tls_interoperation_tested": True,
    "actual_external_endpoint_tested": False,
}
EXPECTED_DEPLOYMENT = {
    "status": "not_run",
    "service_process_packaged": False,
    "independently_operated_host_available": False,
    "exact_dns_and_endpoint_available": False,
    "ca_tls_chain_and_protected_key_available": False,
    "real_client_assertion_key_and_signer_available": False,
    "protected_issuer_signer_or_hsm_kms_available": False,
    "dedicated_state_directory_acl_backup_available": False,
    "firewall_and_leaf_pin_distribution_complete": False,
    "registered_sync_host_available": False,
    "approved_external_run_and_cleanup_plan_available": False,
}
EXPECTED_DEPENDENCIES = {
    "base64": "0.23.1",
    "getrandom": "0.4.3",
    "hex": "0.4.3",
    "ring": "0.17.14",
    "rustls": "0.23.43",
    "serde": "1.0.229",
    "serde_json": "1.0.151",
    "sha2": "0.11.0",
    "thiserror": "2.0.20",
    "zeroize": "1.9.0",
}
EXPECTED_GATE = {
    "component": "pass",
    "current_pc_issuer_core": True,
    "current_pc_independently_bound_tls_service": True,
    "current_pc_pinned_loopback_tls_1_3": True,
    "current_pc_synthetic_all_four_lifecycle_operations": True,
    "external_independently_operated_issuer": False,
    "external_remote_network": False,
    "real_client_assertion": False,
    "real_service_credential": False,
    "external_signer_hsm_or_kms": False,
    "power_loss_durability": False,
    "registered_host": False,
    "production": False,
    "p17_06_complete": False,
    "product_complete": False,
}
EXPECTED_TARGET = {
    "operating_system": "Microsoft Windows 11 Pro",
    "rust_version": "1.96.0",
    "network": "loopback_only",
    "tls": "synthetic_ephemeral_tls_1_3_leaf_pinned",
    "client_assertion_keys": "synthetic_ephemeral_ed25519",
    "issuer_signing_key": "synthetic_ephemeral_ed25519_test_signer",
    "state_store": "temporary_directory_append_only_file_log",
}
EXPECTED_EXECUTION = {
    "test_command": (
        "cargo test -p remote-credential-issuer --all-targets --locked --offline"
    ),
    "test_state": "pass",
    "tests_passed": 17,
    "tests_failed": 0,
    "tests_ignored": 0,
    "clippy_command": (
        "cargo clippy -p remote-credential-issuer --all-targets --locked --offline -- "
        "-D warnings"
    ),
    "clippy_state": "pass",
}
EXPECTED_CHECKS = {
    "all_four_lifecycle_operations_client_verified": True,
    "client_assertion_signature_identity_time_scope_and_request_verified": True,
    "assertion_jti_one_request_only": True,
    "invalid_transition_rejected_before_signer": True,
    "signer_key_id_and_returned_signature_reverified": True,
    "same_and_fresh_assertion_retry_exact": True,
    "append_failure_and_conflict_fail_closed": True,
    "durable_reopen_and_history_tamper_fail_closed": True,
    "abandoned_temporary_file_boundaries_fail_closed": True,
    "concurrent_32_writer_sequence_slot_single_winner": True,
    "raw_secrets_and_operation_id_absent_from_state_log": True,
    "wire_completed_rejected_and_unavailable_distinct": True,
    "tls_1_3_server_config_and_bind_scope_fail_closed": True,
    "real_pinned_client_to_issuer_server_loopback_interoperation": True,
    "bounded_json_jws_files_and_debug_redaction": True,
}
EXPECTED_PRIVACY = {
    "raw_client_assertion_recorded": False,
    "raw_access_token_or_revocation_receipt_recorded": False,
    "private_signing_or_tls_key_recorded": False,
    "real_identity_or_endpoint_recorded": False,
    "user_document_accessed": False,
    "existing_credential_enumerated_or_modified": False,
}
EXPECTED_EVIDENCE_DEPLOYMENT = {
    "status": "not_run",
    "independently_operated_host": False,
    "external_dns_endpoint_and_network": False,
    "ca_tls_chain_and_protected_key": False,
    "real_client_assertion": False,
    "real_service_credential": False,
    "external_signer_hsm_or_kms": False,
    "dedicated_state_acl_backup_and_power_loss": False,
    "registered_sync_host": False,
    "operations_review": False,
}
EXPECTED_CLAIMS = {
    "current_pc_issuer_component": True,
    "current_pc_independently_bound_tls_service": True,
    "current_pc_synthetic_all_four_operations": True,
    "current_pc_pinned_loopback_tls_1_3": True,
    "process_restart_recovery_model": True,
    "external_independently_operated_issuer": False,
    "external_remote_network": False,
    "real_client_assertion": False,
    "real_service_credential": False,
    "external_signer_hsm_or_kms": False,
    "power_loss_durability_qualified": False,
    "registered_host": False,
    "production": False,
    "p17_06_complete": False,
    "product_complete": False,
}


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
        == "hwpx-agent.remote-credential-issuer-contract/v1",
        "contract.schema",
    )
    require(
        contract.get("scope")
        == "current_pc_independently_bound_synthetic_credential_issuer_service_component",
        "contract.scope",
    )
    require(contract.get("authentication") == EXPECTED_AUTHENTICATION, "contract.auth")
    require(contract.get("lifecycle") == EXPECTED_LIFECYCLE, "contract.lifecycle")
    require(contract.get("response_signing") == EXPECTED_SIGNING, "contract.signing")
    require(contract.get("state_store") == EXPECTED_STATE_STORE, "contract.store")
    require(contract.get("service_transport") == EXPECTED_TRANSPORT, "contract.transport")
    require(
        contract.get("deployment_qualification") == EXPECTED_DEPLOYMENT,
        "contract.deployment",
    )
    require(contract.get("dependencies") == EXPECTED_DEPENDENCIES, "contract.dependencies")
    require(
        contract.get("implementation_files") == EXPECTED_IMPLEMENTATION_FILES,
        "contract.files",
    )
    require(
        contract.get("evidence")
        == {
            "path": EVIDENCE_RELATIVE,
            "focused_rust_tests": 17,
            "focused_clippy_denies_warnings": True,
            "synthetic_loopback_tls_only": True,
            "external_deployment_status": "not_run",
        },
        "contract.evidence",
    )
    require(contract.get("gate_decision") == EXPECTED_GATE, "contract.gate")


def validate_evidence_document(evidence: dict[str, Any], raw: bytes) -> None:
    require(
        evidence.get("schema_version")
        == "hwpx-agent.remote-credential-issuer-evidence/v1",
        "evidence.schema",
    )
    require(
        evidence.get("scope")
        == "current_pc_independently_bound_synthetic_credential_issuer_service_component",
        "evidence.scope",
    )
    require(evidence.get("target") == EXPECTED_TARGET, "evidence.target")
    require(evidence.get("execution") == EXPECTED_EXECUTION, "evidence.execution")
    require(evidence.get("checks") == EXPECTED_CHECKS, "evidence.checks")
    require(evidence.get("privacy") == EXPECTED_PRIVACY, "evidence.privacy")
    require(
        evidence.get("deployment_qualification") == EXPECTED_EVIDENCE_DEPLOYMENT,
        "evidence.deployment",
    )
    require(evidence.get("claims") == EXPECTED_CLAIMS, "evidence.claims")
    for secret_marker in (
        b"Bearer ",
        b"BEGIN PRIVATE KEY",
        b"PRIVATE KEY-----",
        b"aaa.bbb.ccc",
        b"operation-tls-server-0001",
    ):
        require(secret_marker not in raw, "evidence.secret")


def validate_source_text(source: str, tests: str) -> None:
    markers = [
        "#![forbid(unsafe_code)]",
        "const MAX_ASSERTION_BYTES: usize = 8_192;",
        "const MAX_REQUEST_BYTES: usize = 16_384;",
        "const MAX_RECORD_BYTES: usize = 65_536;",
        "const MAX_LOG_RECORDS: u64 = 65_536;",
        "const MAX_TEMP_FILES: usize = 64;",
        "UnparsedPublicKey::new(&ED25519",
        "require_canonical_json",
        "claims.request_sha256 != request_sha256",
        "request_admitted(&history.state, &request)",
        "valid_transition(&record.before, &record.request, &record.after)",
        "signer.key_id() != policy.signing_key.key_id",
        ".verify(signing_input.as_bytes(), signature.as_slice())",
        "temporary.sync_all()",
        "fs::hard_link",
        'format!("{sequence:020}.json")',
        "create_new(true)",
        "RecordKind::Replay",
        "restore_history(&self.policy, &stored)",
        "pub struct CredentialIssuerTlsServer",
        "pub struct IssuerTlsServerConfig",
        "IssuerBindScope::ExplicitDeployment",
        "IssuerBindScope::LoopbackQualification",
        "with_protocol_versions(&[&version::TLS13])",
        "send_close_notify()",
    ]
    for marker in markers:
        require(marker in source, "source.marker")
    require(
        source.count("UnparsedPublicKey::new(&ED25519") == 2
        and 'format!("{sequence:020}-{record_sha256}.json")' not in source
        and "fs::rename" not in source
        and "unsafe {" not in source
        and "unsafe fn" not in source,
        "source.weakening",
    )
    names = set(
        re.findall(r"(?m)^fn ([a-z0-9_]+)\(\) -> TestResult(?:<[^>]+>)? \{", tests)
    )
    require(ISSUER_TESTS <= names, "source.tests")
    for marker in [
        "const WRITERS: usize = 32;",
        "PinnedCredentialIssuerTlsTransport::new",
        "EndpointScope::LoopbackQualification",
        "verify_access_token(&lifecycle, &pending, token, NOW)",
        "assert_eq!(completed, 1);",
        "assert_eq!(conflicts, WRITERS - 1);",
    ]:
        require(marker in tests, "source.test_marker")


def validate_source_state(root: Path, contract: dict[str, Any]) -> None:
    for relative in contract["implementation_files"]:
        bounded_file(root, relative)
    workspace = tomllib.loads(bounded_file(root, "Cargo.toml").read_text("utf-8"))
    members = workspace.get("workspace", {}).get("members", [])
    dependencies = workspace.get("workspace", {}).get("dependencies", {})
    require("crates/remote-credential-issuer" in members, "source.workspace_member")
    expected_workspace = {
        "base64": {
            "version": "=0.23.1",
            "default-features": False,
            "features": ["std"],
        },
        "getrandom": {"version": "=0.4.3", "features": ["std"]},
        "hex": "=0.4.3",
        "ring": "=0.17.14",
        "rustls": {
            "version": "=0.23.43",
            "default-features": False,
            "features": ["ring", "std"],
        },
        "serde": {"version": "=1.0.229", "features": ["derive"]},
        "serde_json": "=1.0.151",
        "sha2": "=0.11.0",
        "thiserror": "=2.0.20",
        "zeroize": "=1.9.0",
    }
    for name, expected in expected_workspace.items():
        require(dependencies.get(name) == expected, f"source.workspace_dependency.{name}")
    manifest = tomllib.loads(bounded_file(root, ISSUER_MANIFEST).read_text("utf-8"))
    require(
        set(manifest.get("dependencies", {}))
        == {
            "base64",
            "getrandom",
            "hex",
            "remote-credential-wire",
            "ring",
            "rustls",
            "serde",
            "serde_json",
            "sha2",
            "thiserror",
            "zeroize",
        },
        "source.manifest_dependencies",
    )
    require(
        set(manifest.get("dev-dependencies", {}))
        == {
            "rcgen",
            "remote-credential-broker",
            "remote-credential-lifecycle",
            "remote-tls-transport",
            "tempfile",
        },
        "source.manifest_dev_dependencies",
    )
    lock = tomllib.loads(bounded_file(root, "Cargo.lock").read_text("utf-8"))
    versions = {
        (package.get("name"), package.get("version"))
        for package in lock.get("package", [])
    }
    for name, version in EXPECTED_DEPENDENCIES.items():
        require((name, version) in versions, f"source.lock.{name}")
    issuer_package = next(
        (
            package
            for package in lock.get("package", [])
            if package.get("name") == "remote-credential-issuer"
        ),
        None,
    )
    require(isinstance(issuer_package, dict), "source.lock_issuer")
    require(
        {str(item).split(" ", 1)[0] for item in issuer_package.get("dependencies", [])}
        >= {
            "base64",
            "getrandom",
            "hex",
            "remote-credential-wire",
            "ring",
            "rustls",
            "serde",
            "serde_json",
            "sha2",
            "thiserror",
            "zeroize",
        },
        "source.lock_issuer_dependencies",
    )
    validate_source_text(
        bounded_file(root, ISSUER_SOURCE).read_text("utf-8"),
        bounded_file(root, ISSUER_TEST_SOURCE).read_text("utf-8"),
    )


def verify(root: Path = ROOT) -> dict[str, Any]:
    contract, _ = load_json_strict(bounded_file(root, CONTRACT_RELATIVE), "contract")
    evidence, evidence_raw = load_json_strict(
        bounded_file(root, EVIDENCE_RELATIVE), "evidence"
    )
    validate_contract_document(contract)
    validate_evidence_document(evidence, evidence_raw)
    validate_source_state(root, contract)
    return {
        "schema_version": "hwpx-agent.remote-credential-issuer-validation/v1",
        "state": "pass",
        "checked_files": len(EXPECTED_IMPLEMENTATION_FILES),
        "issuer_rust_tests": len(ISSUER_TESTS),
        "current_pc_independently_bound_tls_service": True,
        "pinned_loopback_tls_1_3": True,
        "external_independently_operated_issuer": False,
        "external_remote_network": False,
        "real_client_assertion": False,
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
        print(f"P17_REMOTE_CREDENTIAL_ISSUER_FAIL:{error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
