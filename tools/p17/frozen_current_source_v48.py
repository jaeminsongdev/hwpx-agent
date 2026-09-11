"""Verify immutable v48 credential issuer and fixed-slot broker source."""

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

from tools.p17 import frozen_current_source_v47 as predecessor  # noqa: E402


QUALIFICATION_COMMIT = "74dd5a8da92d681af26d436f0322d48c591a609b"
BASE_COMMIT = "56e83b3cc68fbab299cb444f0aba38e4dd456a22"
QUALIFICATION_ID = "p17.current-workspace-source.v48.20260911"
SCOPE = "p17_exact_credential_issuer_and_fixed_slot_broker_successor_only"
CONTRACT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v48-20260911/contract.json"
)
CONTRACT_BYTES = 12_826
CONTRACT_SHA256 = "92ed2a96e5fd4529934ab60fbca34d4ca41e8776e83b2d781edaaa9216310196"
CURRENT_RELATIVE = (
    "implementation/p17/qualification/current-workspace-source-v48-20260911/"
    "current-host.json"
)
CURRENT_BYTES = 22_321
CURRENT_SHA256 = "f60e5a5f2a0756e37be67a380e3d0b787de8ac738c094f8cd137bed417f866c7"
PREDECESSOR_RELATIVE = "protocol/private/p17-frozen-current-source-v47-v1.json"
PREDECESSOR_SHA256 = "18d5e35d37ce8fcb1bcefffab9821297d545895d09385a90a0173a77cc244826"
RUN_ID = "0d9724bd6bf44aec9c2d38457bb14e96"
RECEIPT_RELATIVE = (
    "artifacts/p17/current-workspace-source-runs/" f"{RUN_ID}/receipt.json"
)
RECEIPT_BYTES = 12_008
RECEIPT_SHA256 = "87d590ef72b94c9efbe681ce2dcfd7ff73bbbc38edd7f38aaf3c9ec778dc5a20"
BROKER_CONTRACT_RELATIVE = "protocol/private/p17-remote-credential-broker-v2.json"
BROKER_CONTRACT_BYTES = 4_085
BROKER_CONTRACT_SHA256 = "06273c600477c0f1315bef1ab8127db3e193789b9eb8b8a1eb90dcbf8e585720"
BROKER_EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v3.json"
)
BROKER_EVIDENCE_BYTES = 1_678
BROKER_EVIDENCE_SHA256 = "ce951d35dbaf64baf35e33e2c31554b3c9b45fd1db1bbf3e72a530ebdc64df75"
ISSUER_CONTRACT_RELATIVE = "protocol/private/p17-remote-credential-issuer-v1.json"
ISSUER_CONTRACT_BYTES = 6_495
ISSUER_CONTRACT_SHA256 = "b2cb067f8ec4de6d4e165d2cf26d3afe4dce24f9a0c88c39960e58f05313477e"
ISSUER_EVIDENCE_RELATIVE = (
    "implementation/p17/evidence/credential-issuer/"
    "p17-remote-credential-issuer.current-20260911.v1.json"
)
ISSUER_EVIDENCE_BYTES = 3_199
ISSUER_EVIDENCE_SHA256 = "88bf83e227ee935433ace0cf72b8af4790718d4c272a0763591f0a193bd77f8e"
EXPECTED_IMPLEMENTATION_COUNT = 33
EXPECTED_RUNTIME_QUALIFICATION_COUNT = 9
EXPECTED_SUCCESSOR_COUNT = 28
EXPECTED_GUARD_COUNT = 3
EXPECTED_GUARD_PATHS = tuple(
    sorted(
        (
            "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V48.md",
            "tools/p17/current_workspace_source_qualification_v48.py",
            "tools/p17/tests/test_current_workspace_source_qualification_v48.py",
        )
    )
)
EXPECTED_CLAIMS = {
    **predecessor.EXPECTED_CLAIMS,
    "p17_remote_credential_issuer_service_component_verified": True,
    "p17_client_assertion_signature_and_freshness_component_verified": True,
    "p17_issuer_all_lifecycle_operations_verified": True,
    "p17_issuer_operator_signer_boundary_verified": True,
    "p17_independently_bound_tls_issuer_current_pc_verified": True,
    "p17_issuer_synthetic_loopback_only": True,
    "p17_broker_fixed_sequence_slot_verified": True,
    "p17_broker_32_writer_single_winner_verified": True,
    "p17_external_independently_operated_issuer_verified": False,
    "p17_external_signer_hsm_kms_verified": False,
    "p17_external_credential_issuer_verified": False,
    "p17_real_client_assertion_verified": False,
    "p17_real_service_credential_verified": False,
    "p17_windows_power_loss_durability_verified": False,
    "p17_git_mirror_remote_network_verified": False,
    "p17_06_complete": False,
    "actual_hangul": False,
    "registered_host": False,
    "production": False,
    "other_pc_or_version": False,
    "product_complete": False,
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class FrozenSourceV48Error(ValueError):
    """Fail-closed error containing only a bounded diagnostic code."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise FrozenSourceV48Error(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(
    root: Path, revision: str, relative: str, maximum: int = 4_000_000
) -> bytes:
    try:
        return predecessor.git_blob(root, revision, relative, maximum)
    except predecessor.FrozenSourceV47Error as error:
        raise FrozenSourceV48Error(str(error)) from error


def verify_commit(root: Path, revision: str) -> None:
    try:
        predecessor.verify_commit(root, revision)
    except predecessor.FrozenSourceV47Error as error:
        raise FrozenSourceV48Error(str(error)) from error


def require_ancestor(root: Path, ancestor: str, descendant: str) -> None:
    try:
        predecessor.require_ancestor(root, ancestor, descendant)
    except predecessor.FrozenSourceV47Error as error:
        raise FrozenSourceV48Error(str(error)) from error


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
        raise FrozenSourceV48Error("json.invalid") from error
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
            and all(isinstance(value, str) and HEX64.fullmatch(value) for value in accepted)
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
        == "17b1e64243d58c10fc1666c2fc96c01ab4289ba277cafb6b79ac2d51726ed19d"
        and receipt.get("cargo_workspace_member_count") == 31,
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
    broker_contract = json_blob(
        root,
        BASE_COMMIT,
        BROKER_CONTRACT_RELATIVE,
        BROKER_CONTRACT_BYTES,
        BROKER_CONTRACT_SHA256,
    )
    broker_evidence = json_blob(
        root,
        BASE_COMMIT,
        BROKER_EVIDENCE_RELATIVE,
        BROKER_EVIDENCE_BYTES,
        BROKER_EVIDENCE_SHA256,
    )
    issuer_contract = json_blob(
        root,
        BASE_COMMIT,
        ISSUER_CONTRACT_RELATIVE,
        ISSUER_CONTRACT_BYTES,
        ISSUER_CONTRACT_SHA256,
    )
    issuer_evidence = json_blob(
        root,
        BASE_COMMIT,
        ISSUER_EVIDENCE_RELATIVE,
        ISSUER_EVIDENCE_BYTES,
        ISSUER_EVIDENCE_SHA256,
    )
    broker_gate = broker_contract.get("gate_decision")
    broker_claims = broker_evidence.get("claims")
    require(
        isinstance(broker_gate, dict)
        and broker_gate.get("component") == "pass"
        and broker_gate.get("fixed_sequence_publication_slot") is True
        and broker_gate.get("power_loss_durability") is False
        and broker_gate.get("external_issuer") is False
        and broker_gate.get("production") is False
        and broker_gate.get("p17_06_complete") is False
        and broker_gate.get("product_complete") is False,
        "component.broker_contract",
    )
    require(
        isinstance(broker_claims, dict)
        and broker_claims.get("fixed_sequence_slot_component") is True
        and broker_claims.get("actual_current_pc_windows_vault_write_read_delete") is True
        and broker_claims.get("actual_pinned_loopback_tls_1_3") is True
        and broker_claims.get("power_loss_durability_qualified") is False
        and broker_claims.get("external_issuer") is False
        and broker_claims.get("production") is False
        and broker_claims.get("p17_06_complete") is False
        and broker_claims.get("product_complete") is False,
        "component.broker_evidence",
    )
    issuer_gate = issuer_contract.get("gate_decision")
    issuer_claims = issuer_evidence.get("claims")
    issuer_checks = issuer_evidence.get("checks")
    require(
        isinstance(issuer_gate, dict)
        and issuer_gate.get("component") == "pass"
        and issuer_gate.get("current_pc_independently_bound_tls_service") is True
        and issuer_gate.get("external_independently_operated_issuer") is False
        and issuer_gate.get("external_remote_network") is False
        and issuer_gate.get("real_client_assertion") is False
        and issuer_gate.get("real_service_credential") is False
        and issuer_gate.get("external_signer_hsm_or_kms") is False
        and issuer_gate.get("power_loss_durability") is False
        and issuer_gate.get("production") is False
        and issuer_gate.get("p17_06_complete") is False
        and issuer_gate.get("product_complete") is False,
        "component.issuer_contract",
    )
    require(
        isinstance(issuer_claims, dict)
        and isinstance(issuer_checks, dict)
        and issuer_claims.get("current_pc_issuer_component") is True
        and issuer_claims.get("current_pc_independently_bound_tls_service") is True
        and issuer_claims.get("current_pc_synthetic_all_four_operations") is True
        and issuer_checks.get(
            "client_assertion_signature_identity_time_scope_and_request_verified"
        )
        is True
        and issuer_checks.get("all_four_lifecycle_operations_client_verified") is True
        and issuer_checks.get("signer_key_id_and_returned_signature_reverified") is True
        and issuer_checks.get("concurrent_32_writer_sequence_slot_single_winner") is True
        and issuer_claims.get("external_independently_operated_issuer") is False
        and issuer_claims.get("external_remote_network") is False
        and issuer_claims.get("real_client_assertion") is False
        and issuer_claims.get("real_service_credential") is False
        and issuer_claims.get("external_signer_hsm_or_kms") is False
        and issuer_claims.get("power_loss_durability_qualified") is False
        and issuer_claims.get("production") is False
        and issuer_claims.get("p17_06_complete") is False
        and issuer_claims.get("product_complete") is False,
        "component.issuer_evidence",
    )


def verify(root: Path = ROOT) -> dict[str, Any]:
    verify_commit(root, BASE_COMMIT)
    verify_commit(root, QUALIFICATION_COMMIT)
    require_ancestor(root, BASE_COMMIT, QUALIFICATION_COMMIT)
    try:
        predecessor_result = predecessor.verify(root)
    except predecessor.FrozenSourceV47Error as error:
        raise FrozenSourceV48Error(str(error)) from error
    require(predecessor_result.get("state") == "pass", "predecessor.verify")
    validate_component_evidence(root)
    contract = json_blob(
        root, QUALIFICATION_COMMIT, CONTRACT_RELATIVE, CONTRACT_BYTES, CONTRACT_SHA256
    )
    current = json_blob(
        root, QUALIFICATION_COMMIT, CURRENT_RELATIVE, CURRENT_BYTES, CURRENT_SHA256
    )
    receipt = json_blob(
        root, QUALIFICATION_COMMIT, RECEIPT_RELATIVE, RECEIPT_BYTES, RECEIPT_SHA256
    )
    validate_receipt(receipt)
    require(
        contract.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-qualification/v48"
        and contract.get("qualification_id") == QUALIFICATION_ID
        and contract.get("scope") == SCOPE
        and contract.get("base_commit") == BASE_COMMIT
        and contract.get("source_successor_count") == EXPECTED_SUCCESSOR_COUNT,
        "contract.identity",
    )
    require(
        current.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-current/v48"
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
        "schema_version": "hwpx-agent.p17-frozen-current-source-v48-verification/v1",
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
        "credential_issuer_component_verified": True,
        "client_assertion_component_verified": True,
        "independently_bound_tls_issuer_current_pc_verified": True,
        "credential_broker_fixed_sequence_slot_verified": True,
        "broker_concurrent_writers_verified": 32,
        "current_pc_windows_issue_revoke_verified": True,
        "actual_external_independently_operated_issuer": False,
        "external_signer_hsm_kms": False,
        "real_client_assertion": False,
        "real_service_credential": False,
        "windows_power_loss_durability": False,
        "actual_external_remote_network": False,
        "actual_hangul": False,
        "production": False,
        "p17_06_complete": False,
        "product_complete": False,
        "mutable_worktree_sources_read": False,
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["verify"]:
        raise SystemExit("usage: frozen_current_source_v48.py verify")
    try:
        result = verify()
    except FrozenSourceV48Error as error:
        print(f"P17_FROZEN_CURRENT_SOURCE_V48_FAIL code={error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
