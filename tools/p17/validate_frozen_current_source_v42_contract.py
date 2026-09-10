"""Validate the frozen P17 current workspace source v42 private contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_v42 as frozen  # noqa: E402


CONTRACT_RELATIVE = "protocol/private/p17-frozen-current-source-v42-v1.json"
SOURCE_PATHS = (
    "implementation/p17/P17_FROZEN_CURRENT_WORKSPACE_SOURCE_V42.md",
    "protocol/migrations/p17-current-workspace-source-v42-to-frozen-v1.md",
    "protocol/private/p17-frozen-durable-git-mirror-pull-v17-v1.json",
    "tools/p17/frozen_current_source_v42.py",
    "tools/p17/tests/test_frozen_current_source_v42.py",
    "tools/p17/tests/test_frozen_current_source_v42_contract.py",
    "tools/p17/validate_frozen_current_source_v42_contract.py",
)
INVARIANTS = (
    "bounded_git_blob_reads",
    "committed_source_and_receipt_blobs_verified",
    "duplicate_json_keys_rejected",
    "exact_commit_ids_and_ancestry",
    "frozen_durable_pull_v17_verified",
    "frozen_v41_predecessor_verified",
    "no_mutable_worktree_authority",
    "typed_bounded_fail_closed_errors",
)
CLAIMS = {
    "actual_hangul": False,
    "actual_remote_network": False,
    "durable_pull_current_pc_runtime_verified": True,
    "historical_v42_committed_source_state_verified": True,
    "mutable_worktree_product_sources_authoritative": False,
    "p17_06_complete": False,
    "persistent_credential_custody": False,
    "production": False,
    "product_complete": False,
    "receipt_blob_verified": True,
}


class ContractError(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ContractError(code)


def digest(path: Path) -> str:
    require(path.is_file() and 0 < path.stat().st_size <= 4_000_000, "source.file")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def source_locks(root: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": relative,
            "bytes": (root / relative).stat().st_size,
            "sha256": digest(root / relative),
        }
        for relative in SOURCE_PATHS
    ]


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
            "runtime_frozen_contract",
            "invariants",
            "source_locks",
        },
        "contract.fields",
    )
    require(
        contract.get("schema_version") == "hwpx-agent.p17-frozen-current-source-v42/v1"
        and contract.get("contract_id") == "p17.frozen-current-source.v42.v1"
        and contract.get("scope")
        == "immutable_git_blob_durable_pull_source_and_runtime_qualification_verification",
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
            "implementation_source_count": 29,
            "runtime_qualification_source_count": 6,
            "source_successor_count": 28,
            "guard_source_count": 3,
            "claim_count": 62,
        },
        "contract.qualification",
    )
    runtime_contract = root / "protocol/private/p17-frozen-durable-git-mirror-pull-v17-v1.json"
    require(
        contract.get("runtime_frozen_contract")
        == {
            "path": runtime_contract.relative_to(root).as_posix(),
            "sha256": digest(runtime_contract),
        },
        "contract.runtime",
    )
    require(contract.get("invariants") == list(INVARIANTS), "contract.invariants")
    require(contract.get("source_locks") == source_locks(root), "contract.sources")


def verify(root: Path = ROOT) -> dict[str, Any]:
    contract = load_unique(root / CONTRACT_RELATIVE)
    validate_document(contract, root)
    try:
        result = frozen.verify(root)
    except frozen.FrozenSourceV42Error as error:
        raise ContractError(f"frozen.{error}") from error
    require(result.get("state") == "pass", "frozen.state")
    return contract


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["verify"]):
        raise SystemExit("usage: validate_frozen_current_source_v42_contract.py [verify]")
    verified = verify()
    print(
        "P17_FROZEN_CURRENT_SOURCE_V42_CONTRACT_PASS "
        f"sources={len(verified['source_locks'])}"
    )
