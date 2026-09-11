"""Verify immutable v47 credential broker source and current-PC evidence."""

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

from tools.p17 import frozen_current_source_v46 as predecessor  # noqa: E402


QUALIFICATION_COMMIT = "e736c62f309f77b77680e71c9ad334dda047e372"
BASE_COMMIT = "27406fa409c99ecb5435d4373ae49ee4bae7d5ae"
QUALIFICATION_ID = "p17.current-workspace-source.v47.20260911"
SCOPE = "p17_exact_remote_credential_broker_current_pc_successor_only"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v47-20260911/contract.json"
)
CONTRACT_BYTES = 9_872
CONTRACT_SHA256 = "be2c4d63ef4ea843bde8df7c0ce57cb479dc0270a32217d55c708d4d7800246d"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v47-20260911/"
    "current-host.json"
)
CURRENT_BYTES = 19_367
CURRENT_SHA256 = "792364fcce59f0ceb1b027bc48ac657f081298246275482782e938c3000db613"
PREDECESSOR_RELATIVE = "protocol/private/p17-frozen-current-source-v46-v1.json"
PREDECESSOR_SHA256 = "f6a562a9c215a64e8abaf662fe7e1f1ed3ad59abf847320933f6e13e9c2313dd"
RUN_ID = "c5cf7a8fe7414221a625c79e50cb0228"
RECEIPT_RELATIVE = (
    "artifacts/p17/current-workspace-source-runs/" f"{RUN_ID}/receipt.json"
)
RECEIPT_BYTES = 12_008
RECEIPT_SHA256 = "a879ddf0753dcd3d6b2484c794860f94de3aaa177e864e85f05f016f4c60fbd9"
COMPONENT_CONTRACT_RELATIVE = "protocol/private/p17-remote-credential-broker-v1.json"
COMPONENT_CONTRACT_BYTES = 7_510
COMPONENT_CONTRACT_SHA256 = (
    "67556534c456459ebc494f38577750ef96788f0d67bc4738535781682cfb3a79"
)
COMPONENT_EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v2.json"
)
COMPONENT_EVIDENCE_BYTES = 2_147
COMPONENT_EVIDENCE_SHA256 = (
    "bf04b47fefa81ed8c1eb894069e8b24de927ca0d26a6654c4bf8814c9b6fe37f"
)
EXPECTED_IMPLEMENTATION_COUNT = 22
EXPECTED_RUNTIME_QUALIFICATION_COUNT = 5
EXPECTED_SUCCESSOR_COUNT = 28
EXPECTED_GUARD_COUNT = 3
EXPECTED_GUARD_PATHS = tuple(
    sorted(
        (
            "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V47.md",
            "tools/p17/current_workspace_source_qualification_v47.py",
            "tools/p17/tests/test_current_workspace_source_qualification_v47.py",
        )
    )
)
EXPECTED_CLAIMS = {
    **predecessor.EXPECTED_CLAIMS,
    "p17_credential_broker_all_lifecycle_operations_pure_model_verified": True,
    "p17_credential_broker_append_only_reconciliation_model_verified": True,
    "p17_credential_broker_current_pc_windows_issue_revoke_verified": True,
    "p17_credential_broker_pinned_loopback_tls_current_pc_verified": True,
    "p17_credential_broker_synthetic_ephemeral_issuer_only": True,
    "p17_external_credential_issuer_verified": False,
    "p17_windows_atomic_vault_state_integration_verified": False,
    "p17_real_client_assertion_verified": False,
    "p17_windows_power_loss_durability_verified": False,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceV47Error(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceV47Error(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(
    root: Path, revision: str, relative: str, maximum: int = 4_000_000
) -> bytes:
    try:
        return predecessor.git_blob(root, revision, relative, maximum)
    except predecessor.FrozenSourceV46Error as error:
        raise FrozenSourceV47Error(str(error)) from error


def verify_commit(root: Path, revision: str) -> None:
    try:
        predecessor.verify_commit(root, revision)
    except predecessor.FrozenSourceV46Error as error:
        raise FrozenSourceV47Error(str(error)) from error


def require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    try:
        predecessor.require_ancestor(root, ancestor, descendant)
    except predecessor.FrozenSourceV46Error as error:
        raise FrozenSourceV47Error(str(error)) from error


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
        raise FrozenSourceV47Error("json.invalid") from error
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
        == "f2408aef11e450532da8b1274829844eb9c0bb532cb3e1b6d752fbe5d1bb3803"
        and receipt.get("cargo_workspace_member_count") == 30,
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
        and gate.get("current_pc_pure_failure_recovery_model") is True
        and gate.get("current_pc_pinned_loopback_issuer_transport") is True
        and gate.get("current_pc_windows_vault_state_issue_revoke") is True
        and gate.get("actual_windows_refresh_or_rotate") is False
        and gate.get("power_loss_durability") is False
        and gate.get("external_issuer") is False
        and gate.get("external_remote_network") is False
        and gate.get("real_client_assertion") is False
        and gate.get("real_service_credential") is False
        and gate.get("registered_host") is False
        and gate.get("production") is False
        and gate.get("p17_06_complete") is False
        and gate.get("product_complete") is False,
        "component.contract",
    )
    require(
        isinstance(claims, dict)
        and claims.get("actual_current_pc_broker_issue_and_revoke") is True
        and claims.get("actual_current_pc_windows_vault_write_read_delete") is True
        and claims.get("actual_pinned_loopback_tls_1_3") is True
        and claims.get("append_only_vault_state_reconciliation") is True
        and claims.get("synthetic_ephemeral_issuer_only") is True
        and claims.get("actual_windows_refresh_or_rotate") is False
        and claims.get("power_loss_durability_qualified") is False
        and claims.get("external_issuer") is False
        and claims.get("external_remote_network") is False
        and claims.get("real_service_credential") is False
        and claims.get("registered_host") is False
        and claims.get("production") is False
        and claims.get("p17_06_complete") is False
        and claims.get("product_complete") is False,
        "component.evidence",
    )
    require(
        evidence.get("predecessor_evidence")
        == {
            "path": (
                "implementation/p17/evidence/credential-broker/"
                "p17-remote-credential-broker.current-20260911.v1.json"
            ),
            "sha256": (
                "2eb5b8ae7db88fb2a79227e8fc3ab966e5415e0107bbde0de2e6a2b49a903af3"
            ),
        },
        "component.predecessor_evidence",
    )


def verify(root: Path = ROOT) -> dict[str, Any]:
    verify_commit(root, BASE_COMMIT)
    verify_commit(root, QUALIFICATION_COMMIT)
    require_ancestor(root, BASE_COMMIT, QUALIFICATION_COMMIT)
    try:
        predecessor_result = predecessor.verify(root)
    except predecessor.FrozenSourceV46Error as error:
        raise FrozenSourceV47Error(str(error)) from error
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
        == "hwpx-agent.p17-current-workspace-source-qualification/v47"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("base_commit") == BASE_COMMIT
        and contract.get("source_successor_count") == EXPECTED_SUCCESSOR_COUNT,
        "contract.identity",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-current/v47"
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
        "schema_version": "hwpx-agent.p17-frozen-current-source-v47-verification/v1",
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
        "credential_broker_component_verified": True,
        "all_lifecycle_operations_pure_model_verified": True,
        "current_pc_windows_issue_revoke_verified": True,
        "pinned_loopback_tls_current_pc_verified": True,
        "append_only_reconciliation_model_verified": True,
        "synthetic_ephemeral_issuer_only": True,
        "actual_external_issuer": False,
        "real_client_assertion": False,
        "real_service_credential": False,
        "windows_atomic_vault_state_integration": False,
        "windows_power_loss_durability": False,
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
        raise SystemExit("usage: frozen_current_source_v47.py verify")
    try:
        result = verify()
    except FrozenSourceV47Error as error:
        print(f"P17_FROZEN_CURRENT_SOURCE_V47_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
