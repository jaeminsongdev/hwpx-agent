"""Validate the frozen P17 current workspace source v48 private contract."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_v48 as frozen  # noqa: E402


CONTRACT_RELATIVE = "protocol/private/p17-frozen-current-source-v48-v1.json"
FROZEN_AUTHORITY_COMMIT = "c0d872b78e11ad6bce0234d6444eca915299bb46"
SOURCE_PATHS = (
    "implementation/p17/P17_FROZEN_CURRENT_WORKSPACE_SOURCE_V48.md",
    "protocol/migrations/p17-current-workspace-source-v48-to-frozen-v1.md",
    "tools/p17/frozen_current_source_v48.py",
    "tools/p17/tests/test_frozen_current_source_v48.py",
)
INVARIANTS = (
    "bounded_git_blob_reads",
    "broker_fixed_sequence_slot_and_32_writer_result_verified",
    "committed_source_and_receipt_blobs_verified",
    "duplicate_json_keys_rejected",
    "exact_commit_ids_and_ancestry",
    "frozen_v47_predecessor_verified",
    "independently_bound_tls_issuer_component_verified",
    "no_mutable_worktree_authority",
    "remote_credential_issuer_and_broker_evidence_verified",
    "synthetic_loopback_credentials_only",
    "typed_bounded_fail_closed_errors",
)
CLAIMS = {
    "actual_external_independently_operated_issuer": False,
    "actual_external_remote_network": False,
    "actual_hangul": False,
    "broker_concurrent_writers_verified": 32,
    "broker_fixed_sequence_slot_verified": True,
    "client_assertion_component_verified": True,
    "credential_issuer_component_verified": True,
    "current_pc_windows_issue_revoke_verified": True,
    "external_signer_hsm_kms_verified": False,
    "historical_v48_committed_source_state_verified": True,
    "independently_bound_tls_issuer_current_pc_verified": True,
    "mutable_worktree_product_sources_authoritative": False,
    "p17_06_complete": False,
    "production": False,
    "product_complete": False,
    "real_client_assertion_verified": False,
    "real_service_credential_verified": False,
    "receipt_blob_verified": True,
    "synthetic_loopback_credentials_only": True,
    "windows_power_loss_durability_verified": False,
}


class ContractError(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError(code)


def source_locks(root: Path) -> list[dict[str, Any]]:
    locks: list[dict[str, Any]] = []
    for relative in SOURCE_PATHS:
        try:
            raw = frozen.git_blob(root, FROZEN_AUTHORITY_COMMIT, relative)
        except frozen.FrozenSourceV48Error as error:
            raise ContractError(f"source.{error}") from error
        locks.append(
            {
                "path": relative,
                "bytes": len(raw),
                "sha256": frozen.digest(raw),
            }
        )
    return locks


def load_unique(path: Path) -> dict[str, Any]:
    require(path.is_file() and 0 < path.stat().st_size <= 512_000, "contract.file")

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, "contract.duplicate")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContractError("contract.json") from error
    require(isinstance(value, dict), "contract.object")
    return value


def validate_document(contract: dict[str, Any], root: Path = ROOT) -> None:
    require(
        set(contract)
        == {
            "schema_version",
            "contract_id",
            "scope",
            "claims",
            "qualification",
            "component_contracts",
            "invariants",
            "source_locks",
        },
        "contract.fields",
    )
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-frozen-current-source-v48/v1"
        and contract.get("contract_id") == "p17.frozen-current-source.v48.v1"
        and contract.get("scope")
        == "immutable_git_blob_issuer_and_fixed_slot_broker_source_verification",
        "contract.identity",
    )
    require(contract.get("claims") == CLAIMS, "contract.claims")
    require(
        contract.get("qualification")
        == {
            "base_commit": frozen.BASE_COMMIT,
            "qualification_commit": frozen.QUALIFICATION_COMMIT,
            "qualification_id": frozen.QUALIFICATION_ID,
            "contract_path": frozen.CONTRACT_RELATIVE,
            "contract_sha256": frozen.CONTRACT_SHA256,
            "current_path": frozen.CURRENT_RELATIVE,
            "current_sha256": frozen.CURRENT_SHA256,
            "receipt_path": frozen.RECEIPT_RELATIVE,
            "receipt_sha256": frozen.RECEIPT_SHA256,
            "implementation_source_count": 33,
            "runtime_qualification_source_count": 9,
            "source_successor_count": 28,
            "guard_source_count": 3,
            "claim_count": len(frozen.EXPECTED_CLAIMS),
        },
        "contract.qualification",
    )
    require(
        contract.get("component_contracts")
        == [
            {
                "path": frozen.BROKER_CONTRACT_RELATIVE,
                "sha256": frozen.BROKER_CONTRACT_SHA256,
            },
            {
                "path": frozen.ISSUER_CONTRACT_RELATIVE,
                "sha256": frozen.ISSUER_CONTRACT_SHA256,
            },
        ],
        "contract.components",
    )
    require(contract.get("invariants") == list(INVARIANTS), "contract.invariants")
    require(contract.get("source_locks") == source_locks(root), "contract.sources")


def verify(root: Path = ROOT) -> dict[str, Any]:
    try:
        frozen.verify_commit(root, FROZEN_AUTHORITY_COMMIT)
        frozen.require_ancestor(
            root, frozen.QUALIFICATION_COMMIT, FROZEN_AUTHORITY_COMMIT
        )
    except frozen.FrozenSourceV48Error as error:
        raise ContractError(f"authority.{error}") from error
    contract = load_unique(root / CONTRACT_RELATIVE)
    validate_document(contract, root)
    try:
        result = frozen.verify(root)
    except frozen.FrozenSourceV48Error as error:
        raise ContractError(f"frozen.{error}") from error
    require(result.get("state") == "pass", "frozen.state")
    return contract


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["verify"]):
        raise SystemExit("usage: validate_frozen_current_source_v48_contract.py [verify]")
    verified = verify()
    print(
        "P17_FROZEN_CURRENT_SOURCE_V48_CONTRACT_PASS "
        f"sources={len(verified['source_locks'])}"
    )
