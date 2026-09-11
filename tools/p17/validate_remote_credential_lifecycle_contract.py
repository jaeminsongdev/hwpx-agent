"""Validate the P17 remote credential lifecycle contract and pure component evidence."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import sys
import tomllib
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = "protocol/private/p17-remote-credential-lifecycle-v1.json"
EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-lifecycle/"
    "p17-remote-credential-lifecycle.current-20260911.v1.json"
)
SOURCE_RELATIVE = "crates/remote-credential-lifecycle/src/lib.rs"
TEST_RELATIVE = "crates/remote-credential-lifecycle/tests/lifecycle.rs"
EXPECTED_IMPLEMENTATION_FILES = [
    "Cargo.toml",
    "Cargo.lock",
    "crates/remote-credential-lifecycle/Cargo.toml",
    SOURCE_RELATIVE,
    TEST_RELATIVE,
    "implementation/p17/P17-06_REMOTE_CREDENTIAL_LIFECYCLE_V21.md",
    EVIDENCE_RELATIVE,
    "protocol/migrations/p17-remote-credential-lifecycle-v1.md",
    "tools/p17/tests/test_remote_credential_lifecycle_contract.py",
    "tools/p17/validate_remote_credential_lifecycle_contract.py",
]
EXPECTED_DEPENDENCIES = {
    "base64": "0.23.1",
    "ring": "0.17.14",
    "serde": "1.0.229",
    "serde_json": "1.0.151",
    "sha2": "0.11.0",
    "zeroize": "1.9.0",
}
EXPECTED_POLICY = {
    "issuer_scheme": "https",
    "issuer_transport_endpoint_verified_here": False,
    "pinned_signature_algorithm": "Ed25519",
    "maximum_pinned_keys": 8,
    "complete_policy_binding": True,
    "key_material_bound_by_sha256": True,
    "minimum_lifetime_seconds_floor": 60,
    "maximum_lifetime_seconds_ceiling": 86400,
    "refresh_before_seconds_floor": 30,
    "clock_skew_seconds_ceiling": 300,
    "pending_timeout_seconds_range": [30, 600],
}
EXPECTED_TRANSITIONS = {
    "issue": "absent_to_generation_1_key_generation_1",
    "refresh": "due_unexpired_active_increments_token_generation_only",
    "rotate": "unexpired_active_increments_token_and_key_generation",
    "revoke": "active_including_expired_to_terminal_signed_revoked_state",
    "revoked_state_is_terminal": True,
    "refresh_token_modeled_or_stored": False,
    "prior_exact_token_replay_accepted": False,
    "prior_jti_reuse_accepted": False,
    "prior_operation_id_reuse_accepted": False,
    "generation_overflow_accepted": False,
}
EXPECTED_JWT = {
    "compact_jws_maximum_bytes": 2560,
    "base64url": "canonical_unpadded",
    "algorithm": "EdDSA",
    "access_type": "hwpx-agent-service+jwt",
    "revocation_type": "hwpx-agent-revocation+jwt",
    "required_scope": "mirror.sync",
    "exact_issuer_subject_audience": True,
    "exact_operation_request_and_generation_binding": True,
    "unknown_or_duplicate_claims": "reject",
    "signature_verified_before_claim_acceptance": True,
}
EXPECTED_DURABILITY = {
    "pending_contains_complete_prior_nonsecret_state": True,
    "pending_must_be_persisted_before_dispatch": True,
    "retry_reuses_exact_request_bytes_until_deadline": True,
    "definitive_authenticated_rejection_restores_prior_state": True,
    "ambiguous_or_unavailable_outcome_keeps_pending": True,
    "secret_is_zeroized_and_not_serialized": True,
    "atomic_vault_and_state_adapter_implemented_here": False,
}
EXPECTED_GATE = {
    "component": "pass",
    "current_pc_pure_rust": True,
    "actual_external_issuer": False,
    "actual_external_remote_network": False,
    "real_service_credential": False,
    "windows_atomic_vault_state_integration": False,
    "registered_host": False,
    "production": False,
    "p17_06_complete": False,
    "product_complete": False,
}
EXPECTED_CHECKS = {
    "issue_refresh_rotate_and_revoke_transitions": True,
    "complete_policy_and_prior_state_binding": True,
    "exact_retry_request_and_pending_restore": True,
    "canonical_bounded_json_and_jws": True,
    "pinned_ed25519_signature_and_explicit_types": True,
    "exact_identity_scope_operation_request_and_generation_claims": True,
    "lifetime_clock_due_expiry_deadline_and_overflow_boundaries": True,
    "prior_token_and_jti_replay_rejected": True,
    "prior_operation_id_reuse_rejected": True,
    "definitive_rejection_and_ambiguous_outcome_separated": True,
    "terminal_signed_revocation": True,
    "secret_zeroized_unserialized_and_debug_redacted": True,
}
EXPECTED_PRIVACY = {
    "raw_access_token_recorded": False,
    "authorization_header_recorded": False,
    "private_signing_key_recorded": False,
    "real_identity_recorded": False,
    "remote_endpoint_recorded": False,
    "user_document_accessed": False,
}
EXPECTED_CLAIMS = {
    "current_pc_pure_rust_component": True,
    "synthetic_ephemeral_issuer_only": True,
    "actual_external_issuer": False,
    "actual_external_remote_network": False,
    "real_service_credential": False,
    "windows_atomic_vault_state_integration": False,
    "registered_host": False,
    "production": False,
    "actual_hangul": False,
    "p17_06_complete": False,
    "product_complete": False,
}
EXPECTED_TESTS = {
    "issue_is_signed_bound_canonical_and_retry_stable",
    "refresh_is_due_only_and_advances_token_not_key_generation",
    "rotation_advances_both_generations_and_rejects_wrong_generation",
    "signed_revocation_is_distinct_and_terminal",
    "wrong_signature_key_algorithm_type_and_malformed_jws_fail_closed",
    "issuer_subject_audience_scope_request_and_operation_are_exact",
    "lifetime_clock_and_pending_deadline_boundaries_fail_closed",
    "definitive_rejection_restores_exact_state_but_unknown_outcome_stays_pending",
    "pending_json_rejects_unknown_duplicate_noncanonical_drift_and_oversize",
    "policy_and_operation_boundaries_are_exact",
    "arithmetic_overflow_is_rejected",
    "pending_binds_all_keys_and_lifetime_policy",
    "persisted_active_state_must_match_complete_policy",
    "debug_state_request_and_metadata_never_disclose_secrets_or_identities",
    "expired_active_state_refuses_refresh_and_rotation_but_allows_revocation",
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
        set(contract)
        == {
            "schema_version",
            "scope",
            "dependencies",
            "policy",
            "transitions",
            "jwt",
            "durability_boundary",
            "implementation_files",
            "external_authorities",
            "gate_decision",
        },
        "contract.shape",
    )
    require(
        contract.get("schema_version")
        == "hwpx-agent.remote-credential-lifecycle-contract/v1",
        "contract.schema",
    )
    require(
        contract.get("scope") == "pure_credential_issue_refresh_rotate_revoke_component",
        "contract.scope",
    )
    require(contract.get("dependencies") == EXPECTED_DEPENDENCIES, "contract.dependencies")
    require(contract.get("policy") == EXPECTED_POLICY, "contract.policy")
    require(contract.get("transitions") == EXPECTED_TRANSITIONS, "contract.transitions")
    require(contract.get("jwt") == EXPECTED_JWT, "contract.jwt")
    require(
        contract.get("durability_boundary") == EXPECTED_DURABILITY,
        "contract.durability",
    )
    require(
        contract.get("implementation_files") == EXPECTED_IMPLEMENTATION_FILES,
        "contract.files",
    )
    authorities = contract.get("external_authorities")
    require(
        isinstance(authorities, list)
        and len(authorities) == 3
        and [item.get("url") for item in authorities]
        == [
            "https://www.rfc-editor.org/rfc/rfc6749.html",
            "https://www.rfc-editor.org/rfc/rfc8725.html",
            "https://www.rfc-editor.org/rfc/rfc7519.html",
        ],
        "contract.authorities",
    )
    require(contract.get("gate_decision") == EXPECTED_GATE, "contract.gate")


def validate_evidence_document(evidence: dict[str, Any], raw: bytes) -> None:
    require(
        set(evidence)
        == {"schema_version", "scope", "target", "command", "result", "checks", "privacy", "claims"},
        "evidence.shape",
    )
    require(
        evidence.get("schema_version")
        == "hwpx-agent.remote-credential-lifecycle-evidence/v1",
        "evidence.schema",
    )
    require(
        evidence.get("scope") == "current_pc_pure_credential_lifecycle_component",
        "evidence.scope",
    )
    require(
        evidence.get("target")
        == {
            "operating_system": "Windows",
            "rust_version": "1.96.0",
            "network": "not_used",
            "issuer_keys": "ephemeral_test_only",
            "credential_store": "not_used",
        },
        "evidence.target",
    )
    require(
        evidence.get("command")
        == "cargo test -p remote-credential-lifecycle --all-targets --locked --offline",
        "evidence.command",
    )
    require(
        evidence.get("result")
        == {"state": "pass", "passed": 15, "failed": 0, "ignored": 0},
        "evidence.result",
    )
    require(evidence.get("checks") == EXPECTED_CHECKS, "evidence.checks")
    require(evidence.get("privacy") == EXPECTED_PRIVACY, "evidence.privacy")
    require(evidence.get("claims") == EXPECTED_CLAIMS, "evidence.claims")
    lowered = raw.lower()
    for forbidden in (
        b"bearer ",
        b"authorization:",
        b"begin private key",
        b"begin certificate",
        b"aaa.bbb.ccc",
    ):
        require(forbidden not in lowered, "evidence.secret")


def validate_source_text(source: str, tests: str) -> None:
    required_source = [
        "const POLICY_BINDING_SCHEMA_VERSION",
        "public_key_sha256: digest_bytes(&key.public_key)",
        "(CredentialState::Absent, LifecycleOperation::Issue) => Ok((1, 1, None))",
        "(CredentialState::Active { credential }, LifecycleOperation::Refresh)",
        "(CredentialState::Active { credential }, LifecycleOperation::Rotate)",
        "(CredentialState::Active { credential }, LifecycleOperation::Revoke)",
        ".checked_add(1)",
        "UnparsedPublicKey::new(&ED25519, key.public_key)",
        "header.alg != \"EdDSA\" || header.typ != expected_type",
        "require_canonical_json(&header_bytes, &header)?",
        "require_canonical_json(&claims_bytes, &claims)?",
        "URL_SAFE_NO_PAD.encode(&decoded) != segment",
        "pending.prior_credential_sha256.as_deref() == Some(credential_sha256.as_str())",
        "prior.credential_id_sha256 == credential_id_sha256",
        "credential.credential_id_sha256 == receipt_id_sha256",
        "credential.last_operation_id_sha256 == digest_bytes(operation_id.as_bytes())",
        "credential.key_generation > credential.generation",
        "credential.refresh_at != expected_refresh_at",
        "lifetime < policy.minimum_lifetime_seconds",
        "lifetime > policy.maximum_lifetime_seconds",
        "!known_issuer_key",
        "iat_with_skew < pending.requested_at",
        "issued_with_skew < pending.requested_at",
        "pub struct VerifiedCredential",
        "secret: Zeroizing<String>",
        "finish_non_exhaustive()",
        "Ok(pending.before)",
        "#[serde(deny_unknown_fields)]",
    ]
    for index, token in enumerate(required_source):
        require(token in source, f"source.required.{index}")
    for forbidden in (
        "HS256",
        "RS256",
        "refresh_token",
        "println!",
        "eprintln!",
        "dbg!",
        ".unwrap()",
        ".expect(",
    ):
        require(forbidden not in source, "source.forbidden")
    require(
        source.index("UnparsedPublicKey::new(&ED25519, key.public_key)")
        < source.index("Ok((header, claims_bytes))"),
        "source.signature_order",
    )
    names = set(re.findall(r"#\[test\]\s*fn\s+([a-z0-9_]+)", tests))
    require(names == EXPECTED_TESTS, "tests.coverage")


def validate_manifests(root: Path) -> None:
    workspace = tomllib.loads(bounded_file(root, "Cargo.toml").read_text("utf-8"))
    require(
        workspace["workspace"]["members"].count("crates/remote-credential-lifecycle") == 1,
        "manifest.member",
    )
    dependencies = workspace["workspace"]["dependencies"]
    require(
        dependencies.get("base64")
        == {"version": "=0.23.1", "default-features": False, "features": ["std"]},
        "manifest.base64",
    )
    for name, version in {
        "ring": "=0.17.14",
        "serde_json": "=1.0.151",
        "sha2": "=0.11.0",
        "zeroize": "=1.9.0",
    }.items():
        require(dependencies.get(name) == version, f"manifest.{name}")
    require(
        dependencies.get("serde") == {"version": "=1.0.229", "features": ["derive"]},
        "manifest.serde",
    )
    crate = tomllib.loads(
        bounded_file(root, "crates/remote-credential-lifecycle/Cargo.toml").read_text("utf-8")
    )
    require(
        crate.get("dependencies")
        == {
            "base64": {"workspace": True},
            "hex": {"workspace": True},
            "ring": {"workspace": True},
            "serde": {"workspace": True},
            "serde_json": {"workspace": True},
            "sha2": {"workspace": True},
            "thiserror": {"workspace": True},
            "zeroize": {"workspace": True},
        },
        "crate.dependencies",
    )
    require(
        crate.get("dev-dependencies") == {"getrandom": {"workspace": True}},
        "crate.dev_dependencies",
    )
    lock = tomllib.loads(bounded_file(root, "Cargo.lock").read_text("utf-8"))
    package = [
        item for item in lock.get("package", []) if item.get("name") == "remote-credential-lifecycle"
    ]
    require(len(package) == 1 and package[0].get("version") == "0.1.0", "lock.package")
    require(
        package[0].get("dependencies")
        == [
            "base64 0.23.1",
            "getrandom 0.4.3",
            "hex",
            "ring",
            "serde",
            "serde_json",
            "sha2",
            "thiserror",
            "zeroize",
        ],
        "lock.dependencies",
    )


def verify(root: Path = ROOT) -> dict[str, Any]:
    contract, _ = load_json_strict(bounded_file(root, CONTRACT_RELATIVE), "contract")
    evidence, evidence_raw = load_json_strict(
        bounded_file(root, EVIDENCE_RELATIVE), "evidence"
    )
    validate_contract_document(contract)
    validate_evidence_document(evidence, evidence_raw)
    for relative in EXPECTED_IMPLEMENTATION_FILES:
        bounded_file(root, relative)
    validate_manifests(root)
    source = bounded_file(root, SOURCE_RELATIVE).read_text("utf-8")
    tests = bounded_file(root, TEST_RELATIVE).read_text("utf-8")
    validate_source_text(source, tests)
    return {
        "state": "pass",
        "rust_tests": len(EXPECTED_TESTS),
        "actual_external_issuer": False,
        "actual_external_remote_network": False,
        "production": False,
        "p17_06_complete": False,
        "product_complete": False,
    }


def main() -> int:
    try:
        result = verify()
    except (ContractError, OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as error:
        print(f"P17_REMOTE_CREDENTIAL_LIFECYCLE_FAIL code={error}", file=sys.stderr)
        return 1
    print(
        "P17_REMOTE_CREDENTIAL_LIFECYCLE_PASS "
        f"rust_tests={result['rust_tests']} "
        f"external_issuer={str(result['actual_external_issuer']).lower()} "
        f"external_remote={str(result['actual_external_remote_network']).lower()} "
        f"production={str(result['production']).lower()} "
        f"p17_06_complete={str(result['p17_06_complete']).lower()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
