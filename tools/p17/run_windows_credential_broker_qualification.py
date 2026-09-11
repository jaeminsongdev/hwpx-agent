"""Run the explicit current-PC Windows credential broker qualification once."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "artifacts/p17/windows-credential-broker-runs"
EVIDENCE = (
    ROOT
    / "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v2.json"
)
PREDECESSOR_EVIDENCE = (
    ROOT
    / "implementation/p17/evidence/credential-broker/"
    "p17-remote-credential-broker.current-20260911.v1.json"
)
PREDECESSOR_EVIDENCE_SHA256 = (
    "2eb5b8ae7db88fb2a79227e8fc3ab966e5415e0107bbde0de2e6a2b49a903af3"
)
PREFIX = "HWPX_AGENT_WINDOWS_CREDENTIAL_BROKER_RECEIPT="
COMMAND = [
    "cargo",
    "test",
    "-p",
    "windows-credential-custody",
    "--test",
    "windows_broker_tls",
    "--locked",
    "--offline",
    "current_user_broker_pinned_tls_issue_and_revoke",
    "--",
    "--ignored",
    "--exact",
    "--nocapture",
]


class QualificationError(ValueError):
    """Bounded failure without secret-bearing payloads."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_new(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(value)


def parse_receipt(stdout: str) -> dict[str, Any]:
    lines = [line for line in stdout.splitlines() if line.startswith(PREFIX)]
    if len(lines) != 1:
        raise QualificationError("receipt.count")
    try:
        value = json.loads(lines[0][len(PREFIX) :])
    except json.JSONDecodeError as error:
        raise QualificationError("receipt.json") from error
    if not isinstance(value, dict):
        raise QualificationError("receipt.object")
    expected_claims = {
        "existing_credentials_enumerated": False,
        "external_remote_network": False,
        "loopback_transport_only": True,
        "p17_06_complete": False,
        "product_complete": False,
        "production": False,
        "real_service_credential": False,
        "registered_host": False,
        "synthetic_ephemeral_issuer_only": True,
    }
    expected_checks = {
        "access_jws_verified": True,
        "append_only_records": 7,
        "issuer_request_digest_bound": True,
        "pending_persisted_before_dispatch": True,
        "post_cleanup_absent": True,
        "product_provider_read": True,
        "product_vault_deleted": True,
        "product_vault_written_and_observed": True,
        "revocation_jws_verified": True,
        "unique_target_preflight_absent": True,
    }
    target_digest = value.get("credential_target_sha256")
    if (
        value.get("schema_version")
        != "hwpx-agent.windows-credential-broker-runtime/v1"
        or value.get("backend") != "windows_credential_manager"
        or value.get("transport") != "pinned_loopback_tls_1_3"
        or value.get("checks") != expected_checks
        or value.get("claims") != expected_claims
        or not isinstance(target_digest, str)
        or len(target_digest) != 64
        or any(character not in "0123456789abcdef" for character in target_digest)
    ):
        raise QualificationError("receipt.contract")
    return value


def main() -> int:
    if EVIDENCE.exists():
        print(
            "P17_WINDOWS_CREDENTIAL_BROKER_QUALIFICATION_FAIL:evidence.exists",
            file=sys.stderr,
        )
        return 1
    if (
        not PREDECESSOR_EVIDENCE.is_file()
        or digest(PREDECESSOR_EVIDENCE.read_bytes()) != PREDECESSOR_EVIDENCE_SHA256
    ):
        print(
            "P17_WINDOWS_CREDENTIAL_BROKER_QUALIFICATION_FAIL:predecessor",
            file=sys.stderr,
        )
        return 1
    run_id = uuid.uuid4().hex
    run_directory = RUNS / run_id
    environment = os.environ.copy()
    environment["CARGO_NET_OFFLINE"] = "true"
    completed = subprocess.run(
        COMMAND,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    stdout = completed.stdout
    stderr = completed.stderr
    execution = {
        "schema_version": "hwpx-agent.windows-credential-broker-execution/v1",
        "run_id": run_id,
        "command": COMMAND,
        "return_code": completed.returncode,
        "stdout_sha256": digest(stdout.encode("utf-8")),
        "stderr_sha256": digest(stderr.encode("utf-8")),
        "passed": completed.returncode == 0,
    }
    write_new(run_directory / "execution.json", canonical(execution))
    if completed.returncode != 0:
        print(
            f"P17_WINDOWS_CREDENTIAL_BROKER_QUALIFICATION_FAIL:{run_id}",
            file=sys.stderr,
        )
        return 1
    try:
        receipt = parse_receipt(stdout)
    except QualificationError as error:
        print(
            f"P17_WINDOWS_CREDENTIAL_BROKER_QUALIFICATION_FAIL:{run_id}:{error}",
            file=sys.stderr,
        )
        return 1
    receipt_bytes = canonical(receipt)
    receipt_relative = (
        f"artifacts/p17/windows-credential-broker-runs/{run_id}/receipt.json"
    )
    write_new(run_directory / "receipt.json", receipt_bytes)
    evidence = {
        "schema_version": "hwpx-agent.remote-credential-broker-evidence/v1",
        "evidence_id": f"p17.remote-credential-broker.current-20260911.{run_id[:8]}",
        "scope": "current_pc_pinned_loopback_issuer_windows_vault_state_component",
        "predecessor_evidence": {
            "path": (
                "implementation/p17/evidence/credential-broker/"
                "p17-remote-credential-broker.current-20260911.v1.json"
            ),
            "sha256": PREDECESSOR_EVIDENCE_SHA256,
        },
        "target": {
            "operating_system": "Windows",
            "credential_store": "Windows Credential Manager",
            "state_store": "append_only_synced_no_overwrite_hard_link_log",
            "transport": "pinned_leaf_tls_1_3_loopback",
            "issuer": "synthetic_ephemeral_ed25519",
        },
        "execution": {
            "run_id": run_id,
            "test": "current_user_broker_pinned_tls_issue_and_revoke",
            "locked": True,
            "offline": True,
            "passed": True,
            "receipt_path": receipt_relative,
            "receipt_sha256": digest(receipt_bytes),
            "credential_target_sha256": receipt["credential_target_sha256"],
        },
        "checks": receipt["checks"],
        "privacy": {
            "raw_access_token_persisted_outside_vault": False,
            "raw_authorization_header_in_evidence": False,
            "raw_target_name_in_evidence": False,
            "existing_credentials_enumerated": False,
            "user_document_accessed": False,
        },
        "claims": {
            "actual_current_pc_windows_vault_write_read_delete": True,
            "actual_current_pc_broker_issue_and_revoke": True,
            "actual_pinned_loopback_tls_1_3": True,
            "append_only_vault_state_reconciliation": True,
            "synthetic_ephemeral_issuer_only": True,
            "actual_windows_refresh_or_rotate": False,
            "power_loss_durability_qualified": False,
            "external_issuer": False,
            "external_remote_network": False,
            "real_service_credential": False,
            "registered_host": False,
            "production": False,
            "p17_06_complete": False,
            "product_complete": False,
        },
    }
    try:
        write_new(EVIDENCE, canonical(evidence))
    except FileExistsError:
        print(
            f"P17_WINDOWS_CREDENTIAL_BROKER_QUALIFICATION_FAIL:{run_id}:evidence.exists",
            file=sys.stderr,
        )
        return 1
    print(canonical(evidence).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
