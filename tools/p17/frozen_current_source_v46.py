"""Verify immutable v46 remote credential lifecycle source and evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import frozen_current_source_v45 as predecessor  # noqa: E402


QUALIFICATION_COMMIT = "b20874ab16f605f126047a58f8b65d35202dc4e6"
BASE_COMMIT = "a13ec5ca0e21c64f4d84ac734ad601252fb21074"
QUALIFICATION_ID = "p17.current-workspace-source.v46.20260911"
SCOPE = "p17_exact_remote_credential_lifecycle_successor_only"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v46-20260911/contract.json"
)
CONTRACT_BYTES = 7_081
CONTRACT_SHA256 = "191ace02e3effd4af3b526b0963abb7f7f82b26aa45037d3e5ed23ce326447b3"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v46-20260911/"
    "current-host.json"
)
CURRENT_BYTES = 16_576
CURRENT_SHA256 = "f5041d64d2285b3c84e43e6f7b55d8df21d66c3b84f351770e47105e485787fc"
PREDECESSOR_RELATIVE = "protocol/private/p17-frozen-current-source-v45-v1.json"
PREDECESSOR_SHA256 = "45fddeb30186f254ca0570e6e9d456e7409312320fdcc47188cddc97a032a818"
RUN_ID = "bc1bdc271d4b464db1c9cbc0a1da0d46"
RECEIPT_RELATIVE = (
    "artifacts/p17/current-workspace-source-runs/" f"{RUN_ID}/receipt.json"
)
RECEIPT_BYTES = 12_008
RECEIPT_SHA256 = "385b1d07a43a883e1786585f13f84dee70d4503b750826e4ca2e14958239a861"
COMPONENT_CONTRACT_RELATIVE = "protocol/private/p17-remote-credential-lifecycle-v1.json"
COMPONENT_CONTRACT_BYTES = 4_104
COMPONENT_CONTRACT_SHA256 = (
    "2f8ad8175baaec7a52aa7490030ae63d892ba81473f0d51e5c20ab455c2559a2"
)
COMPONENT_EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-lifecycle/"
    "p17-remote-credential-lifecycle.current-20260911.v1.json"
)
COMPONENT_EVIDENCE_BYTES = 1_883
COMPONENT_EVIDENCE_SHA256 = (
    "d0f557f48cb5f2e9ce72cef8dbf047a0991f84036637ef17df62f6b60683c21c"
)
EXPECTED_IMPLEMENTATION_COUNT = 10
EXPECTED_RUNTIME_QUALIFICATION_COUNT = 2
EXPECTED_SUCCESSOR_COUNT = 28
EXPECTED_GUARD_COUNT = 3
EXPECTED_GUARD_PATHS = tuple(
    sorted(
        (
            "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V46.md",
            "tools/p17/current_workspace_source_qualification_v46.py",
            "tools/p17/tests/test_current_workspace_source_qualification_v46.py",
        )
    )
)
EXPECTED_CLAIMS = {
    **predecessor.EXPECTED_CLAIMS,
    "p17_remote_credential_lifecycle_current_pc_pure_component_verified": True,
    "p17_remote_credential_lifecycle_issue_refresh_rotate_revoke_component_verified": True,
    "p17_remote_credential_lifecycle_synthetic_ephemeral_issuer_only": True,
    "p17_remote_credential_lifecycle_complete_policy_and_state_binding_verified": True,
    "p17_external_credential_issuer_verified": False,
    "p17_windows_atomic_vault_state_integration_verified": False,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceV46Error(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceV46Error(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(
    root: Path, revision: str, relative: str, maximum: int = 4_000_000
) -> bytes:
    try:
        return predecessor.git_blob(root, revision, relative, maximum)
    except predecessor.FrozenSourceV45Error as error:
        raise FrozenSourceV46Error(str(error)) from error


def verify_commit(root: Path, revision: str) -> None:
    try:
        predecessor.verify_commit(root, revision)
    except predecessor.FrozenSourceV45Error as error:
        raise FrozenSourceV46Error(str(error)) from error


def require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    try:
        predecessor.require_ancestor(root, ancestor, descendant)
    except predecessor.FrozenSourceV45Error as error:
        raise FrozenSourceV46Error(str(error)) from error


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "json.duplicate")
        result[key] = value
    return result


def json_blob(
    root: Path,
    revision: str,
    relative: str,
    expected_bytes: int,
    expected_sha256: str,
) -> dict[str, Any]:
    raw = git_blob(root, revision, relative, 512_000)
    require(len(raw) == expected_bytes, "json.bytes")
    require(digest(raw) == expected_sha256, "json.digest")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise FrozenSourceV46Error("json.invalid") from error
    require(isinstance(value, dict), "json.object")
    return value


def validate_locked_sources(
    root: Path,
    revision: str,
    sources: Any,
    expected_count: int,
    code: str,
) -> set[str]:
    require(
        isinstance(sources, list) and len(sources) == expected_count,
        f"{code}.count",
    )
    paths: set[str] = set()
    for entry in sources:
        require(
            isinstance(entry, dict) and set(entry) == {"path", "bytes", "sha256"},
            f"{code}.shape",
        )
        relative = entry.get("path")
        expected_bytes = entry.get("bytes")
        expected_sha256 = entry.get("sha256")
        require(
            isinstance(relative, str)
            and relative not in paths
            and type(expected_bytes) is int
            and 0 < expected_bytes <= 4_000_000
            and isinstance(expected_sha256, str)
            and HEX64.fullmatch(expected_sha256) is not None,
            f"{code}.identity",
        )
        raw = git_blob(root, revision, relative)
        require(len(raw) == expected_bytes, f"{code}.bytes")
        require(digest(raw) == expected_sha256, f"{code}.digest")
        paths.add(relative)
    return paths


def validate_successors(root: Path, successors: Any) -> set[str]:
    require(
        isinstance(successors, list) and len(successors) == EXPECTED_SUCCESSOR_COUNT,
        "successor.count",
    )
    paths: set[str] = set()
    for entry in successors:
        require(
            isinstance(entry, dict)
            and set(entry)
            == {
                "accepted_predecessor_sha256s",
                "composition_predecessor_sha256",
                "current_sha256",
                "path",
            },
            "successor.shape",
        )
        relative = entry.get("path")
        accepted = entry.get("accepted_predecessor_sha256s")
        composition = entry.get("composition_predecessor_sha256")
        current = entry.get("current_sha256")
        require(
            isinstance(relative, str)
            and relative not in paths
            and isinstance(accepted, list)
            and 0 < len(accepted) <= 8
            and len(set(accepted)) == len(accepted)
            and all(
                isinstance(value, str) and HEX64.fullmatch(value) for value in accepted
            )
            and composition in accepted
            and isinstance(current, str)
            and HEX64.fullmatch(current) is not None,
            "successor.identity",
        )
        require(
            digest(git_blob(root, BASE_COMMIT, relative)) == current,
            "successor.history",
        )
        paths.add(relative)
    return paths


def validate_receipt(receipt: dict[str, Any]) -> None:
    require(
        receipt.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-check/v1"
        and receipt.get("run_id") == RUN_ID
        and receipt.get("source_commit") == BASE_COMMIT
        and receipt.get("decision") == "PASS"
        and receipt.get("passed") is True
        and receipt.get("check_count") == 11
        and receipt.get("successor_count") == EXPECTED_SUCCESSOR_COUNT
        and receipt.get("cargo_metadata_projection_sha256")
        == "eed4e4cdc90e9f5de93d73da8654d096aaae4f2b70d33ad8fde952eecc83b782"
        and receipt.get("cargo_workspace_member_count") == 28,
        "receipt.identity",
    )
    for claim in (
        "actual_hangul",
        "registered_host",
        "production",
        "other_pc_or_version",
        "phase_complete",
    ):
        require(receipt.get(claim) is False, f"receipt.{claim}")


def validate_component_evidence(root: Path) -> None:
    contract = json_blob(
        root,
        BASE_COMMIT,
        COMPONENT_CONTRACT_RELATIVE,
        COMPONENT_CONTRACT_BYTES,
        COMPONENT_CONTRACT_SHA256,
    )
    evidence = json_blob(
        root,
        BASE_COMMIT,
        COMPONENT_EVIDENCE_RELATIVE,
        COMPONENT_EVIDENCE_BYTES,
        COMPONENT_EVIDENCE_SHA256,
    )
    gate = contract.get("gate_decision")
    claims = evidence.get("claims")
    require(
        isinstance(gate, dict)
        and gate.get("component") == "pass"
        and gate.get("current_pc_pure_rust") is True
        and gate.get("actual_external_issuer") is False
        and gate.get("actual_external_remote_network") is False
        and gate.get("real_service_credential") is False
        and gate.get("windows_atomic_vault_state_integration") is False
        and gate.get("registered_host") is False
        and gate.get("production") is False
        and gate.get("p17_06_complete") is False
        and gate.get("product_complete") is False,
        "component.contract",
    )
    require(
        isinstance(claims, dict)
        and claims.get("current_pc_pure_rust_component") is True
        and claims.get("synthetic_ephemeral_issuer_only") is True
        and claims.get("actual_external_issuer") is False
        and claims.get("actual_external_remote_network") is False
        and claims.get("real_service_credential") is False
        and claims.get("windows_atomic_vault_state_integration") is False
        and claims.get("registered_host") is False
        and claims.get("production") is False
        and claims.get("p17_06_complete") is False
        and claims.get("product_complete") is False,
        "component.evidence",
    )


def verify(root: Path = ROOT) -> dict[str, Any]:
    verify_commit(root, BASE_COMMIT)
    verify_commit(root, QUALIFICATION_COMMIT)
    require_ancestor(root, BASE_COMMIT, QUALIFICATION_COMMIT)
    try:
        predecessor_result = predecessor.verify(root)
    except predecessor.FrozenSourceV45Error as error:
        raise FrozenSourceV46Error(str(error)) from error
    require(predecessor_result.get("state") == "pass", "predecessor.verify")
    validate_component_evidence(root)
    contract = json_blob(
        root,
        QUALIFICATION_COMMIT,
        CONTRACT_RELATIVE,
        CONTRACT_BYTES,
        CONTRACT_SHA256,
    )
    current = json_blob(
        root,
        QUALIFICATION_COMMIT,
        CURRENT_RELATIVE,
        CURRENT_BYTES,
        CURRENT_SHA256,
    )
    receipt = json_blob(
        root,
        QUALIFICATION_COMMIT,
        RECEIPT_RELATIVE,
        RECEIPT_BYTES,
        RECEIPT_SHA256,
    )
    validate_receipt(receipt)
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-qualification/v46"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("base_commit") == BASE_COMMIT
        and contract.get("source_successor_count") == EXPECTED_SUCCESSOR_COUNT,
        "contract.identity",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-current/v46"
        and current.get("qualification_id") == QUALIFICATION_ID
        and current.get("scope") == SCOPE
        and current.get("base_commit") == BASE_COMMIT,
        "current.identity",
    )
    predecessor_identity = {
        "path": PREDECESSOR_RELATIVE,
        "sha256": PREDECESSOR_SHA256,
    }
    require(contract.get("predecessor") == predecessor_identity, "contract.predecessor")
    require(current.get("predecessor") == predecessor_identity, "current.predecessor")
    require(contract.get("claims") == EXPECTED_CLAIMS, "contract.claims")
    require(current.get("claims") == EXPECTED_CLAIMS, "current.claims")
    require(
        contract.get("evidence")
        == {
            "path": CURRENT_RELATIVE,
            "sha256": CURRENT_SHA256,
            "run_id": RUN_ID,
            "receipt_path": RECEIPT_RELATIVE,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "contract.evidence",
    )
    require(
        current.get("evidence")
        == {
            "path": RECEIPT_RELATIVE,
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "current.evidence",
    )
    successor_paths = validate_successors(root, receipt.get("successors"))
    require(
        current.get("source_successors") == receipt.get("successors"),
        "current.successors",
    )
    implementation_paths = validate_locked_sources(
        root,
        BASE_COMMIT,
        contract.get("implementation_sources"),
        EXPECTED_IMPLEMENTATION_COUNT,
        "implementation",
    )
    require(
        current.get("implementation_sources") == contract.get("implementation_sources"),
        "current.implementation",
    )
    runtime_paths = validate_locked_sources(
        root,
        BASE_COMMIT,
        contract.get("runtime_qualification_sources"),
        EXPECTED_RUNTIME_QUALIFICATION_COUNT,
        "runtime",
    )
    require(
        current.get("runtime_qualification_sources")
        == contract.get("runtime_qualification_sources"),
        "current.runtime",
    )
    guard_paths = validate_locked_sources(
        root,
        QUALIFICATION_COMMIT,
        contract.get("guard_sources"),
        EXPECTED_GUARD_COUNT,
        "guard",
    )
    require(tuple(sorted(guard_paths)) == EXPECTED_GUARD_PATHS, "guard.paths")
    return {
        "schema_version": "hwpx-agent.p17-frozen-current-source-v46-verification/v1",
        "state": "pass",
        "qualification_id": QUALIFICATION_ID,
        "qualification_commit": QUALIFICATION_COMMIT,
        "base_commit": BASE_COMMIT,
        "implementation_source_count": len(implementation_paths),
        "runtime_qualification_source_count": len(runtime_paths),
        "source_successor_count": len(successor_paths),
        "guard_source_count": len(guard_paths),
        "claim_count": len(EXPECTED_CLAIMS),
        "receipt_blob_verified": True,
        "credential_lifecycle_component_verified": True,
        "complete_policy_and_state_binding_verified": True,
        "synthetic_ephemeral_issuer_only": True,
        "actual_external_issuer": False,
        "real_service_credential": False,
        "windows_atomic_vault_state_integration": False,
        "credential_issuance_or_rotation": False,
        "actual_external_remote_network": False,
        "actual_hangul": False,
        "production": False,
        "p17_06_complete": False,
        "product_complete": False,
        "mutable_worktree_sources_read": False,
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_current_source_v46.py verify")
    try:
        result = verify()
    except FrozenSourceV46Error as error:
        print(f"P17_FROZEN_CURRENT_SOURCE_V46_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
