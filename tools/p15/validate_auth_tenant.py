from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-auth-tenant-v1.json"
RUST_PATH = ROOT / "crates/auth-middleware/src/lib.rs"

EXPECTED_SOURCE_PATHS = [
    ".gitignore",
    "Cargo.lock",
    "Cargo.toml",
    "crates/auth-middleware/Cargo.toml",
    "crates/auth-middleware/src/lib.rs",
    "implementation/p15/P15-01_AUTH_POLICY.md",
    "tools/p14/validate_cancel_cleanup.py",
    "tools/p14/validate_retention_local_mirror.py",
    "tools/p15/validate_auth_tenant.py",
]

EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "scope",
    "official_source",
    "boundary",
    "jwt",
    "limits",
    "scopes",
    "required_behaviors",
    "rust_tests",
    "source_locks",
}

EXPECTED_BEHAVIORS = [
    "exact_https_resource_metadata",
    "signature_before_trust",
    "exact_issuer_key_binding",
    "exact_single_audience",
    "expiry_not_before_issue_and_lifetime",
    "issuer_subject_to_tenant_mapping",
    "tenant_role_scope_ceiling",
    "token_scope_subset_of_grant",
    "required_scope_subset_of_token",
    "public_user_internal_service_separation",
    "service_token_single_use_after_all_checks",
    "issuer_token_id_revocation",
    "secret_and_identity_redacted_debug",
]

EXPECTED_SCOPES = [
    "artifact.read",
    "artifact.write",
    "job.cancel",
    "job.submit",
    "mirror.sync",
    "project.read",
    "project.write",
    "retention.manage",
]

EXPECTED_LIMITS = {
    "bearer_token_bytes": 8192,
    "claims_json_bytes": 4096,
    "clock_skew_seconds": 300,
    "header_json_bytes": 1024,
    "hmac_key_bytes_max": 128,
    "hmac_key_bytes_min": 32,
    "issuer_bytes": 256,
    "key_id_bytes": 64,
    "principal_records": 4096,
    "revocation_records": 8192,
    "scope_count": 32,
    "service_token_lifetime_seconds": 300,
    "service_token_replay_records": 8192,
    "signing_key_records": 64,
    "subject_bytes": 200,
    "token_id_bytes": 128,
    "user_token_lifetime_seconds": 3600,
}

REQUIRED_RUST_TOKENS = [
    "pub struct AuthMiddleware",
    "pub struct PrincipalGrant",
    "pub struct AuthContext",
    "pub fn authenticate_public_mcp",
    "pub fn authenticate_internal_service_once",
    "pub fn revoke_token_id",
    "verify_slice(&signature)",
    "#[serde(deny_unknown_fields)]",
    'PrincipalKind::User => "at+jwt"',
    'PrincipalKind::Service => "hwpx-service+jwt"',
    "external_identity_digest",
    "internal_subject_digest",
    "self.consumed_service_tokens",
    "AuthRegistryLimits",
    "MAX_CONSUMED_SERVICE_TOKENS",
    "retain(|_, expires_at| *expires_at > now_unix_seconds)",
    "self.revoked_tokens.contains",
    "claims.aud != self.canonical_resource",
    "required_scopes.is_subset(&verified.scopes)",
    "verified.scopes.is_subset(&binding.allowed_scopes)",
    "tenant_role.allows(*scope)",
    'field("secret", &"<redacted>")',
    'field("subject", &"<redacted>")',
    'field("token_sha256", &"<redacted>")',
]

REQUIRED_RETENTION_SUPERSESSION_TOKENS = [
    'P14_09_IMPLEMENTATION_REVISION = "1d5de34121a8ba7cb9fc651cb90d63d7973db2dc"',
    "P15_SUPERSEDING_CONTRACT",
    "P15_SUPERSEDING_VALIDATOR",
    "P15_SUPERSEDED_PATHS",
    '"Cargo.lock"',
    '"Cargo.toml"',
    '"tools/p14/validate_retention_local_mirror.py"',
    '"git"',
    '"show"',
]

REQUIRED_CANCEL_SUPERSESSION_TOKENS = [
    'P14_08_IMPLEMENTATION_REVISION = "8d03bb6b4fb69e73f8921aa26484b400dadf941b"',
    "P15_SUPERSEDING_CONTRACT",
    "P15_SUPERSEDING_VALIDATOR",
    "P15_SUPERSEDED_PATHS",
    '".gitignore"',
    '"tools/p14/validate_cancel_cleanup.py"',
    '"git"',
    '"show"',
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_contract(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError("auth tenant contract root must be an object")
    return value


def bounded_source_file(root: Path, relative: str, maximum_bytes: int) -> Path:
    value = Path(relative)
    if (
        not relative
        or "\\" in relative
        or value.is_absolute()
        or ".." in value.parts
    ):
        raise ValueError(f"source path is not repository-relative: {relative}")
    candidate = root / value
    if candidate.is_symlink() or (
        hasattr(candidate, "is_junction") and candidate.is_junction()
    ):
        raise ValueError(f"source path is a link or junction: {relative}")
    resolved_root = root.resolve(strict=True)
    resolved = candidate.resolve(strict=True)
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise ValueError(f"source path is not a repository file: {relative}")
    if not 0 < resolved.stat().st_size <= maximum_bytes:
        raise ValueError(f"source path exceeds its size bound: {relative}")
    return resolved


def validate_contract(contract: dict[str, Any], rust_text: str, root: Path) -> list[str]:
    errors: list[str] = []
    if set(contract) != EXPECTED_TOP_LEVEL_KEYS:
        errors.append("top_level_keys")
    if contract.get("schema_version") != "hwpx-agent.p15-auth-tenant/v1":
        errors.append("schema_version")
    if contract.get("scope") != "current_pc_local_resource_server_reference":
        errors.append("scope")

    source = contract.get("official_source")
    if source != {
        "retrieved_on": "2026-09-04",
        "url": "https://developers.openai.com/plugins/build/auth",
    }:
        errors.append("official_source")

    boundary = contract.get("boundary")
    if boundary != {
        "authorization_server_implemented": False,
        "production_jwks_implemented": False,
        "public_mcp_principal_kind": "user",
        "internal_service_principal_kind": "service",
        "service_tokens_accepted_from_openai_host": False,
        "service_tokens_single_use": True,
    }:
        errors.append("boundary")

    jwt = contract.get("jwt")
    expected_claims = [
        "aud",
        "exp",
        "iat",
        "iss",
        "jti",
        "nbf",
        "scope",
        "sub",
        "tenant_id",
        "token_kind",
    ]
    if not isinstance(jwt, dict):
        errors.append("jwt")
    else:
        if set(jwt) != {
            "local_reference_algorithm",
            "user_typ",
            "service_typ",
            "required_claims",
            "unknown_claims_rejected",
            "duplicate_claims_rejected",
            "multi_audience_rejected",
        }:
            errors.append("jwt.keys")
        if jwt.get("local_reference_algorithm") != "HS256":
            errors.append("jwt.algorithm")
        if jwt.get("user_typ") != "at+jwt" or jwt.get("service_typ") != "hwpx-service+jwt":
            errors.append("jwt.typ")
        if jwt.get("required_claims") != expected_claims:
            errors.append("jwt.required_claims")
        for field in (
            "unknown_claims_rejected",
            "duplicate_claims_rejected",
            "multi_audience_rejected",
        ):
            if jwt.get(field) is not True:
                errors.append(f"jwt.{field}")

    if contract.get("limits") != EXPECTED_LIMITS:
        errors.append("limits")
    if contract.get("scopes") != EXPECTED_SCOPES:
        errors.append("scopes")
    if contract.get("rust_tests") != 17:
        errors.append("rust_tests")

    behaviors = contract.get("required_behaviors")
    if behaviors != EXPECTED_BEHAVIORS:
        errors.append("required_behaviors")

    locks = contract.get("source_locks")
    if not isinstance(locks, list) or len(locks) != len(EXPECTED_SOURCE_PATHS):
        errors.append("source_locks")
    else:
        seen: set[str] = set()
        observed_paths: list[str] = []
        for index, lock in enumerate(locks):
            if not isinstance(lock, dict) or set(lock) != {"path", "sha256"}:
                errors.append(f"source_locks[{index}]")
                continue
            relative = lock.get("path")
            expected = lock.get("sha256")
            if (
                not isinstance(relative, str)
                or relative in seen
                or relative != EXPECTED_SOURCE_PATHS[index]
            ):
                errors.append(f"source_locks[{index}].path")
                continue
            if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
                errors.append(f"source_locks[{index}].sha256")
                continue
            seen.add(relative)
            observed_paths.append(relative)
            try:
                path = bounded_source_file(root, relative, 2 * 1024 * 1024)
            except (OSError, ValueError):
                errors.append(f"source_locks[{index}].missing")
                continue
            if expected != sha256_file(path):
                errors.append(f"source_locks[{index}].sha256")
        if observed_paths != EXPECTED_SOURCE_PATHS:
            errors.append("source_locks.paths")

    cargo_manifest = (root / "Cargo.toml").read_text(encoding="utf-8")
    cargo_lock = (root / "Cargo.lock").read_text(encoding="utf-8")
    retention_supersession = (
        root / "tools/p14/validate_retention_local_mirror.py"
    ).read_text(
        encoding="utf-8"
    )
    cancel_supersession = (root / "tools/p14/validate_cancel_cleanup.py").read_text(
        encoding="utf-8"
    )
    if '"crates/auth-middleware"' not in cargo_manifest:
        errors.append("workspace.auth_member")
    if 'name = "auth-middleware"' not in cargo_lock:
        errors.append("lock.auth_package")
    for label, text, tokens in (
        (
            "retention",
            retention_supersession,
            REQUIRED_RETENTION_SUPERSESSION_TOKENS,
        ),
        ("cancel", cancel_supersession, REQUIRED_CANCEL_SUPERSESSION_TOKENS),
    ):
        for token in tokens:
            if token not in text:
                errors.append(f"supersession_token:{label}:{token}")

    for token in REQUIRED_RUST_TOKENS:
        if token not in rust_text:
            errors.append(f"rust_token:{token}")
    forbidden = ["client_secret=", "access_token=", "BEGIN PRIVATE KEY"]
    for token in forbidden:
        if token in rust_text:
            errors.append(f"rust_forbidden:{token}")
    return errors


def main() -> int:
    contract = load_contract(CONTRACT_PATH)
    errors = validate_contract(contract, RUST_PATH.read_text(encoding="utf-8"), ROOT)
    result = {
        "schema_version": "hwpx-agent.p15-auth-tenant-validation/v1",
        "state": "pass" if not errors else "fail",
        "source_files": len(contract.get("source_locks", [])),
        "scopes": len(contract.get("scopes", [])),
        "rust_tests": contract.get("rust_tests"),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
