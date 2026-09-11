"""Validate the P17 credential broker fixed-sequence publication successor."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tomllib
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = "protocol/private/p17-remote-credential-broker-v2.json"
PREDECESSOR_CONTRACT_RELATIVE = "protocol/private/p17-remote-credential-broker-v1.json"
PREDECESSOR_CONTRACT_SHA256 = (
    "67556534c456459ebc494f38577750ef96788f0d67bc4738535781682cfb3a79"
)
EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v3.json"
)
PREDECESSOR_EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v2.json"
)
PREDECESSOR_EVIDENCE_SHA256 = (
    "bf04b47fefa81ed8c1eb894069e8b24de927ca0d26a6654c4bf8814c9b6fe37f"
)
BROKER_SOURCE = "crates/remote-credential-broker/src/lib.rs"
EXPECTED_IMPLEMENTATION_FILES = [
    "Cargo.toml",
    "Cargo.lock",
    "crates/remote-credential-broker/Cargo.toml",
    BROKER_SOURCE,
    "implementation/p17/P17-06_REMOTE_CREDENTIAL_BROKER_V22.md",
    "implementation/p17/P17-06_REMOTE_CREDENTIAL_BROKER_V24.md",
    PREDECESSOR_EVIDENCE_RELATIVE,
    EVIDENCE_RELATIVE,
    "protocol/migrations/p17-remote-credential-broker-v1.md",
    "protocol/migrations/p17-remote-credential-broker-v2.md",
    PREDECESSOR_CONTRACT_RELATIVE,
    CONTRACT_RELATIVE,
    "tools/p17/tests/test_remote_credential_broker_v2_contract.py",
    "tools/p17/validate_remote_credential_broker_v2_contract.py",
]
EXPECTED_MIGRATION = {
    "path": "protocol/migrations/p17-remote-credential-broker-v2.md",
    "automatic_v1_directory_migration": False,
    "v1_digest_bearing_record_names_rejected": True,
    "existing_vault_target_reused_implicitly": False,
    "rollback_rewrites_or_deletes_state": False,
}
EXPECTED_STORE = {
    "record_schema_unchanged": "hwpx-agent.remote-credential-broker-record/v1",
    "mode": "append_only_immutable_records",
    "maximum_record_bytes": 65536,
    "maximum_log_records": 65536,
    "same_directory_synced_temporary_file": True,
    "no_overwrite_hard_link_publication": True,
    "compare_and_append_revision": True,
    "contiguous_sequence_required": True,
    "final_record_name": "zero_padded_20_digit_sequence_json",
    "record_sha256_in_filename": False,
    "record_sha256_derived_from_exact_bytes": True,
    "one_publication_slot_per_sequence": True,
    "canonical_json_required": True,
    "unknown_duplicate_noncanonical_or_policy_drift": "reject",
    "cross_system_transaction_claimed": False,
    "process_crash_reconciliation_modeled": True,
    "power_loss_durability_qualified": False,
}
EXPECTED_CONCURRENCY = {
    "writers": 32,
    "distinct_valid_record_bytes": True,
    "expected_winners": 1,
    "expected_conflicts": 31,
    "reopen_record_count": 1,
    "remaining_file_names": ["00000000000000000001.json"],
    "synthetic_file_state_only": True,
}
EXPECTED_UNCHANGED = {
    "wire": True,
    "issuer_transport": True,
    "broker_state_payload": True,
    "windows_vault": True,
    "recovery": True,
    "raw_access_token_in_state_log": False,
    "existing_credentials_enumerated": False,
}
EXPECTED_GATE = {
    "component": "pass",
    "fixed_sequence_publication_slot": True,
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
EXPECTED_CLAIMS = {
    "actual_current_pc_broker_issue_and_revoke": True,
    "actual_current_pc_windows_vault_write_read_delete": True,
    "actual_pinned_loopback_tls_1_3": True,
    "actual_windows_refresh_or_rotate": False,
    "external_issuer": False,
    "external_remote_network": False,
    "fixed_sequence_slot_component": True,
    "p17_06_complete": False,
    "power_loss_durability_qualified": False,
    "product_complete": False,
    "production": False,
    "real_service_credential": False,
    "registered_host": False,
    "synthetic_ephemeral_issuer_only": True,
}
EXPECTED_PRIVACY = {
    "existing_credentials_enumerated": False,
    "raw_access_token_persisted_outside_vault": False,
    "raw_authorization_header_in_evidence": False,
    "raw_target_name_in_evidence": False,
    "user_document_accessed": False,
}


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
        == "hwpx-agent.remote-credential-broker-contract/v2",
        "contract.schema",
    )
    require(
        contract.get("scope")
        == "fixed_sequence_publication_slot_component_with_exact_v1_predecessor",
        "contract.scope",
    )
    require(
        contract.get("predecessor")
        == {
            "path": PREDECESSOR_CONTRACT_RELATIVE,
            "sha256": PREDECESSOR_CONTRACT_SHA256,
            "state": "immutable_private_contract",
        },
        "contract.predecessor",
    )
    require(contract.get("migration") == EXPECTED_MIGRATION, "contract.migration")
    require(contract.get("state_store_successor") == EXPECTED_STORE, "contract.store")
    require(
        contract.get("concurrency_qualification") == EXPECTED_CONCURRENCY,
        "contract.concurrency",
    )
    require(
        contract.get("unchanged_v1_boundaries") == EXPECTED_UNCHANGED,
        "contract.unchanged",
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
            "runtime_reexecuted_for_successor": False,
            "runtime_claims_inherited_only_from_exact_predecessor": True,
            "new_direct_rust_component_test_passed": True,
        },
        "contract.evidence",
    )
    require(contract.get("gate_decision") == EXPECTED_GATE, "contract.gate")


def validate_evidence_document(evidence: dict[str, Any], raw: bytes) -> None:
    require(raw == canonical(evidence), "evidence.canonical")
    require(
        evidence.get("schema_version")
        == "hwpx-agent.remote-credential-broker-evidence/v2",
        "evidence.schema",
    )
    require(
        evidence.get("scope")
        == "fixed_sequence_publication_slot_component_with_exact_runtime_predecessor",
        "evidence.scope",
    )
    require(
        evidence.get("evidence_id")
        == "p17.remote-credential-broker.fixed-sequence-slot.20260911.v3",
        "evidence.id",
    )
    require(
        evidence.get("predecessor_evidence")
        == {
            "path": PREDECESSOR_EVIDENCE_RELATIVE,
            "sha256": PREDECESSOR_EVIDENCE_SHA256,
        },
        "evidence.predecessor",
    )
    require(
        evidence.get("state_store")
        == {
            "canonical_record_sha256_derived_from_bytes": True,
            "final_record_name": "zero_padded_20_digit_sequence_json",
            "one_publication_slot_per_sequence": True,
            "publication": (
                "same_directory_synced_temporary_then_no_overwrite_hard_link"
            ),
        },
        "evidence.store",
    )
    require(
        evidence.get("qualification")
        == {
            "command": (
                "cargo test -p remote-credential-broker --locked --offline "
                "append_only_file_store_allows_only_one_writer_per_sequence_slot"
            ),
            "conflicts": 31,
            "locked": True,
            "offline": True,
            "passed": True,
            "rust_tests_passed": 1,
            "synthetic_file_state_only": True,
            "winner_count": 1,
            "writers": 32,
        },
        "evidence.qualification",
    )
    require(evidence.get("privacy") == EXPECTED_PRIVACY, "evidence.privacy")
    require(evidence.get("claims") == EXPECTED_CLAIMS, "evidence.claims")


def validate_source_text(source: str) -> None:
    for marker in [
        'self.root.join(format!("{sequence:020}.json"))',
        "let record_sha256 = digest_bytes(bytes);",
        "temporary.sync_all()",
        "fs::hard_link(&temporary_path, &final_path)",
        "create_new(true)",
        "fn append_only_file_store_allows_only_one_writer_per_sequence_slot()",
        "const WRITERS: usize = 32;",
        "assert_eq!(completed, 1);",
        "assert_eq!(conflicts, WRITERS - 1);",
        'assert_eq!(names, ["00000000000000000001.json"]);',
    ]:
        require(marker in source, "source.marker")
    require(
        'format!("{sequence:020}-{record_sha256}.json")' not in source,
        "source.digest_filename",
    )
    require(
        "#![forbid(unsafe_code)]" in source
        and "unsafe {" not in source
        and "unsafe fn" not in source,
        "source.unsafe",
    )


def verify(root: Path = ROOT) -> dict[str, Any]:
    contract, _ = load_json_strict(bounded_file(root, CONTRACT_RELATIVE), "contract")
    evidence, evidence_raw = load_json_strict(
        bounded_file(root, EVIDENCE_RELATIVE), "evidence"
    )
    validate_contract_document(contract)
    validate_evidence_document(evidence, evidence_raw)
    predecessor_contract = bounded_file(root, PREDECESSOR_CONTRACT_RELATIVE).read_bytes()
    predecessor_evidence = bounded_file(root, PREDECESSOR_EVIDENCE_RELATIVE).read_bytes()
    require(
        hashlib.sha256(predecessor_contract).hexdigest()
        == PREDECESSOR_CONTRACT_SHA256,
        "predecessor.contract_sha256",
    )
    require(
        hashlib.sha256(predecessor_evidence).hexdigest()
        == PREDECESSOR_EVIDENCE_SHA256,
        "predecessor.evidence_sha256",
    )
    for relative in contract["implementation_files"]:
        bounded_file(root, relative)
    workspace = tomllib.loads(bounded_file(root, "Cargo.toml").read_text("utf-8"))
    require(
        "crates/remote-credential-broker"
        in workspace.get("workspace", {}).get("members", []),
        "source.workspace_member",
    )
    validate_source_text(bounded_file(root, BROKER_SOURCE).read_text("utf-8"))
    for content in (evidence_raw, predecessor_contract, predecessor_evidence):
        require(
            b"Bearer " not in content
            and b"aaa.bbb.ccc" not in content
            and b"hwpx-agent.remote-sync:" not in content
            and b"BEGIN PRIVATE KEY" not in content,
            "privacy.secret_or_target",
        )
    return {
        "schema_version": "hwpx-agent.remote-credential-broker-validation/v2",
        "state": "pass",
        "checked_files": len(EXPECTED_IMPLEMENTATION_FILES),
        "concurrent_writers": 32,
        "expected_winners": 1,
        "external_issuer": False,
        "power_loss_durability": False,
        "production": False,
        "p17_06_complete": False,
        "product_complete": False,
    }


def main() -> int:
    try:
        result = verify()
    except (ContractError, OSError, tomllib.TOMLDecodeError) as error:
        print(f"P17_REMOTE_CREDENTIAL_BROKER_V2_FAIL:{error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
