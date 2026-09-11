"""Bind the exact credential issuer and fixed-slot broker successor source."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import durable_git_mirror_pull_qualification as foundation  # noqa: E402
from tools.p17 import frozen_current_source_v47 as predecessor  # noqa: E402
from tools.p17 import run_current_workspace_source_checks as acceptance  # noqa: E402
from tools.p17 import validate_remote_credential_broker_contract as broker_v1_gate  # noqa: E402
from tools.p17 import validate_remote_credential_broker_v2_contract as broker_v2_gate  # noqa: E402
from tools.p17 import validate_remote_credential_issuer_contract as issuer_gate  # noqa: E402


BASE = "implementation/p17/qualification/current-workspace-source-v48-20260911"
QUALIFICATION = ROOT / BASE
RUN_ID = "0d9724bd6bf44aec9c2d38457bb14e96"
BASE_COMMIT = "56e83b3cc68fbab299cb444f0aba38e4dd456a22"
RECEIPT_SHA256 = "87d590ef72b94c9efbe681ce2dcfd7ff73bbbc38edd7f38aaf3c9ec778dc5a20"
PREVIOUS_QUALIFICATION = (
    "protocol/private/p17-frozen-current-source-v47-v1.json",
    "18d5e35d37ce8fcb1bcefffab9821297d545895d09385a90a0173a77cc244826",
)
IMPLEMENTATION_PATHS = (
    "Cargo.lock",
    "Cargo.toml",
    "PLANS.md",
    "crates/remote-credential-lifecycle/Cargo.toml",
    "crates/remote-credential-lifecycle/src/lib.rs",
    "crates/remote-credential-lifecycle/tests/lifecycle.rs",
    "crates/remote-credential-wire/Cargo.toml",
    "crates/remote-credential-wire/src/lib.rs",
    "crates/remote-credential-broker/Cargo.toml",
    "crates/remote-credential-broker/src/lib.rs",
    "crates/remote-credential-issuer/Cargo.toml",
    "crates/remote-credential-issuer/src/lib.rs",
    "crates/remote-credential-issuer/tests/issuer.rs",
    "crates/remote-tls-transport/Cargo.toml",
    "crates/remote-tls-transport/src/lib.rs",
    "crates/remote-tls-transport/tests/credential_issuer_tls.rs",
    "crates/windows-credential-custody/Cargo.toml",
    "crates/windows-credential-custody/src/lib.rs",
    "crates/windows-credential-custody/tests/windows_credential_custody.rs",
    "crates/windows-credential-custody/tests/windows_broker_tls.rs",
    "protocol/migrations/p17-remote-credential-broker-v1.md",
    "protocol/private/p17-remote-credential-broker-v1.json",
    "tools/p17/run_windows_credential_broker_qualification.py",
    "tools/p17/tests/test_remote_credential_broker_contract.py",
    "tools/p17/validate_remote_credential_broker_contract.py",
    "protocol/migrations/p17-remote-credential-issuer-v1.md",
    "protocol/private/p17-remote-credential-issuer-v1.json",
    "tools/p17/tests/test_remote_credential_issuer_contract.py",
    "tools/p17/validate_remote_credential_issuer_contract.py",
    "protocol/migrations/p17-remote-credential-broker-v2.md",
    "protocol/private/p17-remote-credential-broker-v2.json",
    "tools/p17/tests/test_remote_credential_broker_v2_contract.py",
    "tools/p17/validate_remote_credential_broker_v2_contract.py",
)
RUNTIME_QUALIFICATION_PATHS = (
    "implementation/p17/P17-06_REMOTE_CREDENTIAL_BROKER_V22.md",
    "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v1.json",
    "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v2.json",
    "artifacts/p17/windows-credential-broker-runs/"
    "917fb640c51e4fe8b17bbf1bbe5b2356/receipt.json",
    "artifacts/p17/windows-credential-broker-runs/"
    "a68c91c7a7ad4199b421fa0a031131b0/receipt.json",
    "implementation/p17/P17-06_REMOTE_CREDENTIAL_ISSUER_V23.md",
    "implementation/p17/evidence/credential-issuer/"
    "p17-remote-credential-issuer.current-20260911.v1.json",
    "implementation/p17/P17-06_REMOTE_CREDENTIAL_BROKER_V24.md",
    "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v3.json",
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v48.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v48.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V48.md",
)
CLAIMS = {
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


def receipt_path(root: Path) -> Path:
    return root / f"artifacts/p17/current-workspace-source-runs/{RUN_ID}/receipt.json"


def source_lock(
    root: Path, relative: str, *, committed: bool = False
) -> dict[str, Any]:
    path = foundation.bounded_file(root, relative)
    raw = path.read_bytes()
    if committed:
        foundation.require(
            raw == foundation.git_blob(root, BASE_COMMIT, relative),
            "implementation.history",
        )
    return {"path": relative, "bytes": len(raw), "sha256": foundation.digest(raw)}


def validate_predecessor(root: Path) -> None:
    predecessor.verify(root)
    path = foundation.bounded_file(root, PREVIOUS_QUALIFICATION[0], 512_000)
    foundation.require(
        foundation.digest(path.read_bytes()) == PREVIOUS_QUALIFICATION[1],
        "predecessor.digest",
    )


def expected_successors(root: Path) -> list[dict[str, Any]]:
    try:
        return acceptance.current_source_entries(root, BASE_COMMIT)
    except acceptance.AcceptanceError as error:
        raise foundation.QualificationError(f"successors.{error}") from error


def validate_receipt(receipt: dict[str, Any], root: Path) -> None:
    foundation.require(
        receipt.get("schema_version")
        == "hwpx-agent.p17-current-workspace-source-check/v1",
        "receipt.schema",
    )
    foundation.require(receipt.get("run_id") == RUN_ID, "receipt.run")
    foundation.require(receipt.get("source_commit") == BASE_COMMIT, "receipt.commit")
    foundation.require(receipt.get("decision") == "PASS", "receipt.decision")
    foundation.require(receipt.get("passed") is True, "receipt.passed")
    foundation.require(receipt.get("check_count") == 11, "receipt.checks")
    successors = expected_successors(root)
    foundation.require(receipt.get("successors") == successors, "receipt.successors")
    foundation.require(receipt.get("successor_count") == len(successors), "receipt.count")
    foundation.require(
        receipt.get("cargo_metadata_projection_sha256")
        == "17b1e64243d58c10fc1666c2fc96c01ab4289ba277cafb6b79ac2d51726ed19d",
        "receipt.cargo",
    )
    foundation.require(
        receipt.get("cargo_workspace_member_count") == 31,
        "receipt.members",
    )
    for claim in (
        "actual_hangul",
        "registered_host",
        "production",
        "other_pc_or_version",
        "phase_complete",
    ):
        foundation.require(receipt.get(claim) is False, f"receipt.{claim}")


def validate_runtime_qualification(root: Path) -> list[dict[str, Any]]:
    broker_v1 = broker_v1_gate.verify(root)
    foundation.require(
        broker_v1.get("state") == "pass"
        and broker_v1.get("broker_rust_tests") == 13
        and broker_v1.get("checked_files") == 24
        and broker_v1.get("current_pc_windows_issue_revoke") is True
        and broker_v1.get("pinned_loopback_tls") is True
        and broker_v1.get("external_issuer") is False
        and broker_v1.get("power_loss_durability") is False
        and broker_v1.get("production") is False
        and broker_v1.get("p17_06_complete") is False
        and broker_v1.get("product_complete") is False,
        "runtime.broker_v1_claims",
    )
    broker_v2 = broker_v2_gate.verify(root)
    foundation.require(
        broker_v2.get("state") == "pass"
        and broker_v2.get("checked_files") == 14
        and broker_v2.get("concurrent_writers") == 32
        and broker_v2.get("expected_winners") == 1
        and broker_v2.get("external_issuer") is False
        and broker_v2.get("power_loss_durability") is False
        and broker_v2.get("production") is False
        and broker_v2.get("p17_06_complete") is False
        and broker_v2.get("product_complete") is False,
        "runtime.broker_v2_claims",
    )
    issuer = issuer_gate.verify(root)
    foundation.require(
        issuer.get("state") == "pass"
        and issuer.get("checked_files") == 15
        and issuer.get("issuer_rust_tests") == 17
        and issuer.get("current_pc_independently_bound_tls_service") is True
        and issuer.get("pinned_loopback_tls_1_3") is True
        and issuer.get("external_independently_operated_issuer") is False
        and issuer.get("external_remote_network") is False
        and issuer.get("real_client_assertion") is False
        and issuer.get("real_service_credential") is False
        and issuer.get("power_loss_durability") is False
        and issuer.get("production") is False
        and issuer.get("p17_06_complete") is False
        and issuer.get("product_complete") is False,
        "runtime.issuer_claims",
    )
    return [
        source_lock(root, relative, committed=True)
        for relative in RUNTIME_QUALIFICATION_PATHS
    ]


def implementation_sources(root: Path) -> list[dict[str, Any]]:
    return [
        source_lock(root, relative, committed=True) for relative in IMPLEMENTATION_PATHS
    ]


def expected_current(root: Path) -> dict[str, Any]:
    receipt = foundation.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt, root)
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v48",
        "qualification_id": "p17.current-workspace-source.v48.20260911",
        "scope": "p17_exact_credential_issuer_and_fixed_slot_broker_successor_only",
        "base_commit": BASE_COMMIT,
        "predecessor": {
            "path": PREVIOUS_QUALIFICATION[0],
            "sha256": PREVIOUS_QUALIFICATION[1],
        },
        "evidence": {
            "path": receipt_path(root).relative_to(root).as_posix(),
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "source_successors": receipt["successors"],
        "implementation_sources": implementation_sources(root),
        "runtime_qualification_sources": validate_runtime_qualification(root),
        "claims": CLAIMS,
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v48",
        "qualification_id": "p17.current-workspace-source.v48.20260911",
        "scope": "p17_exact_credential_issuer_and_fixed_slot_broker_successor_only",
        "base_commit": BASE_COMMIT,
        "predecessor": {
            "path": PREVIOUS_QUALIFICATION[0],
            "sha256": PREVIOUS_QUALIFICATION[1],
        },
        "evidence": {
            "path": current_path.relative_to(root).as_posix(),
            "sha256": foundation.digest(current_path.read_bytes()),
            "run_id": RUN_ID,
            "receipt_path": receipt_path(root).relative_to(root).as_posix(),
            "receipt_sha256": RECEIPT_SHA256,
        },
        "source_successor_count": len(expected_successors(root)),
        "implementation_sources": implementation_sources(root),
        "runtime_qualification_sources": validate_runtime_qualification(root),
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
        "claims": CLAIMS,
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    validate_predecessor(root)
    receipt = foundation.load_document(receipt_path(root), "receipt")
    validate_receipt(receipt, root)
    foundation.require(
        foundation.digest(receipt_path(root).read_bytes()) == RECEIPT_SHA256,
        "receipt.digest",
    )
    current_path = foundation.bounded_file(root, f"{BASE}/current-host.json", 512_000)
    contract_path = foundation.bounded_file(root, f"{BASE}/contract.json", 512_000)
    current = foundation.load_document(current_path, "current")
    contract = foundation.load_document(contract_path, "contract")
    foundation.require(current == expected_current(root), "current.identity")
    foundation.require(
        contract == expected_contract(root, current_path), "contract.identity"
    )
    return contract


def qualify() -> tuple[Path, Path]:
    validate_predecessor(ROOT)
    receipt = foundation.load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt, ROOT)
    foundation.require(
        foundation.digest(receipt_path(ROOT).read_bytes()) == RECEIPT_SHA256,
        "receipt.digest",
    )
    implementation_sources(ROOT)
    validate_runtime_qualification(ROOT)
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(foundation.canonical(expected_current(ROOT)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(foundation.canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


if __name__ == "__main__":
    usage = "usage: current_workspace_source_qualification_v48.py qualify|verify"
    if sys.argv[1:] == ["qualify"]:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V48_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1:] == ["verify"]:
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V48_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
