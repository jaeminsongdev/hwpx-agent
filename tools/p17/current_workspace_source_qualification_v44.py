"""Bind the exact certificate-pinned TLS transport and loopback component evidence."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.p17 import durable_git_mirror_pull_qualification as foundation  # noqa: E402
from tools.p17 import frozen_current_source_v43 as predecessor  # noqa: E402
from tools.p17 import run_current_workspace_source_checks as acceptance  # noqa: E402
from tools.p17 import validate_remote_tls_transport_contract as tls  # noqa: E402


BASE = "implementation/p17/qualification/current-workspace-source-v44-20260911"
QUALIFICATION = ROOT / BASE
RUN_ID = "60508db167ec4d8ea8789a7daee4fe9c"
BASE_COMMIT = "45426cac614a1da3fc3f69f10a49e7f7876d8c2f"
RECEIPT_SHA256 = "264784f7951fe4aa073f21e4428417aaf335826b25455e00963552ebe6e89be5"
PREVIOUS_QUALIFICATION = (
    "protocol/private/p17-frozen-current-source-v43-v1.json",
    "af03c0679f8e8e1a1e28557f6cfc4baccba6696af131a95967c67bca626bfd29",
)
IMPLEMENTATION_PATHS = (
    "Cargo.toml",
    "Cargo.lock",
    "PLANS.md",
    "crates/remote-tls-transport/Cargo.toml",
    "crates/remote-tls-transport/src/lib.rs",
    "crates/remote-tls-transport/tests/pinned_tls.rs",
    "protocol/migrations/p17-remote-tls-transport-v1.md",
    "protocol/private/p17-remote-tls-transport-v1.json",
    "tools/p17/tests/test_remote_tls_transport_contract.py",
    "tools/p17/validate_remote_tls_transport_contract.py",
)
RUNTIME_QUALIFICATION_PATHS = (
    "implementation/p17/P17-06_REMOTE_TLS_TRANSPORT_V19.md",
    "implementation/p17/evidence/remote-tls/"
    "p17-remote-tls-transport.current-20260911.v1.json",
)
GUARD_SOURCES = (
    "tools/p17/current_workspace_source_qualification_v44.py",
    "tools/p17/tests/test_current_workspace_source_qualification_v44.py",
    "implementation/p17/P17_CURRENT_WORKSPACE_SOURCE_V44.md",
)
CLAIMS = {
    **predecessor.EXPECTED_CLAIMS,
    "p17_remote_tls_transport_current_pc_loopback_qualified": True,
    "p17_remote_tls_transport_synthetic_certificate_only": True,
    "p17_remote_tls_transport_external_network_verified": False,
    "p17_real_service_certificate_verified": False,
    "p17_real_service_credential_verified": False,
    "p17_credential_issuance_rotation_verified": False,
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
        == "5db5c23673a4c593bf4bb7050ffa538328be5f334fdb57a76e496a6ae86daf2d",
        "receipt.cargo",
    )
    foundation.require(
        receipt.get("cargo_workspace_member_count") == 27,
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
    result = tls.verify(root)
    foundation.require(
        result.get("state") == "pass"
        and result.get("current_pc_loopback_tls13") is True
        and result.get("actual_external_remote_network") is False
        and result.get("production") is False
        and result.get("p17_06_complete") is False
        and result.get("product_complete") is False,
        "runtime.claims",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-current/v44",
        "qualification_id": "p17.current-workspace-source.v44.20260911",
        "scope": "p17_exact_remote_tls_transport_source_and_loopback_successor_only",
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
        "schema_version": "hwpx-agent.p17-current-workspace-source-qualification/v44",
        "qualification_id": "p17.current-workspace-source.v44.20260911",
        "scope": "p17_exact_remote_tls_transport_source_and_loopback_successor_only",
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
    usage = "usage: current_workspace_source_qualification_v44.py qualify|verify"
    if sys.argv[1:] == ["qualify"]:
        current_file, contract_file = qualify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V44_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1:] == ["verify"]:
        verified = verify()
        print(
            "P17_CURRENT_WORKSPACE_SOURCE_V44_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit(usage)
