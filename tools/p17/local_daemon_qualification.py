"""Freeze and verify the P17-03 current-PC local daemon qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = ROOT / "implementation/p17/qualification/local-daemon-v1-20260906"
RUN_ID = "4b1c023ca40c4a02b6dc25ac77ca656b"
BASE_COMMIT = "ca1a332505c07454b517fd780b369fae184e2975"
RECEIPT_SHA256 = "d290e57a81d2b912b1902baf6b85073192fdc1582475112f0c957a133cb53a92"
EXPECTED_CHECKS = (
    "clean_tracked_source",
    "locked_offline_binary_build",
    "authenticated_health_redacted",
    "wrong_session_rejected",
    "bounded_existing_file_admitted",
    "traversal_rejected",
    "new_output_name_admitted",
    "overwrite_rejected",
    "unknown_request_field_rejected",
    "graceful_eof_shutdown",
    "temporary_resources_cleaned",
)
CLAIMS = {
    "local_daemon": True,
    "workspace_sandbox": True,
    "process_scoped_auth": True,
    "bounded_health_config": True,
    "actual_codex_plugin": False,
    "persistent_credentials": False,
    "postgres_lifecycle": False,
    "actual_hangul": False,
    "network_used": False,
    "phase_complete": False,
}
RUNTIME_SOURCES = (
    "Cargo.toml",
    "Cargo.lock",
    "crates/local-companion-daemon/Cargo.toml",
    "crates/local-companion-daemon/src/lib.rs",
    "crates/local-companion-daemon/src/main.rs",
    "crates/local-companion-daemon/tests/binary_smoke.rs",
    "crates/local-companion-daemon/tests/sandbox.rs",
    "protocol/private/p17-local-daemon-v1.json",
    "tools/p17/run_local_daemon_checks.py",
    "tools/p17/tests/test_local_daemon_checks.py",
)
GUARD_SOURCES = (
    "tools/p17/local_daemon_qualification.py",
    "tools/p17/tests/test_local_daemon_qualification.py",
    "implementation/p17/P17-03_LOCAL_DAEMON_V1.md",
)


class QualificationError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(document: object) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def load_document(path: Path, code: str) -> dict[str, Any]:
    require(path.is_file() and 0 < path.stat().st_size <= 256_000, f"{code}.file")
    try:
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise QualificationError(f"{code}.parse") from error
    require(isinstance(document, dict), f"{code}.type")
    require(raw == canonical(document), f"{code}.canonical")
    return document


def source_lock(root: Path, relative: str) -> dict[str, object]:
    path = root / relative
    require(path.is_file(), "source.missing")
    return {"path": relative, "bytes": path.stat().st_size, "sha256": digest(path)}


def expected_receipt() -> dict[str, Any]:
    return {
        "actual_codex_plugin": False,
        "actual_hangul": False,
        "check_count": len(EXPECTED_CHECKS),
        "checks": list(EXPECTED_CHECKS),
        "decision": "PASS",
        "network_used": False,
        "passed": True,
        "resources_cleaned": True,
        "run_id": RUN_ID,
        "schema_version": "hwpx-agent.p17-local-daemon-check/v1",
        "scope": "current_pc_synthetic_workspace_local_daemon_only",
        "source_commit": BASE_COMMIT,
        "tracked_clean": True,
    }


def validate_receipt(receipt: dict[str, Any]) -> None:
    require(
        set(receipt)
        == {
            "actual_codex_plugin",
            "actual_hangul",
            "check_count",
            "checks",
            "decision",
            "network_used",
            "passed",
            "resources_cleaned",
            "run_id",
            "schema_version",
            "scope",
            "source_commit",
            "tracked_clean",
        },
        "receipt.fields",
    )
    require(receipt == expected_receipt(), "receipt.claims")


def receipt_path(root: Path) -> Path:
    return root / "artifacts/p17/local-daemon-runs" / RUN_ID / "receipt.json"


def qualify() -> tuple[Path, Path]:
    path = receipt_path(ROOT)
    receipt = load_document(path, "receipt")
    validate_receipt(receipt)
    require(digest(path) == RECEIPT_SHA256, "receipt.digest")
    runtime_locks = [source_lock(ROOT, relative) for relative in RUNTIME_SOURCES]
    current = {
        "schema_version": "hwpx-agent.p17-local-daemon-current/v1",
        "run_id": RUN_ID,
        "source_commit": BASE_COMMIT,
        "scope": receipt["scope"],
        "checks": list(EXPECTED_CHECKS),
        "check_count": len(EXPECTED_CHECKS),
        "resources_cleaned": True,
        "claims": CLAIMS,
        "receipt": {
            "path": receipt_path(ROOT).relative_to(ROOT).as_posix(),
            "sha256": RECEIPT_SHA256,
        },
        "source_hashes": {
            entry["path"]: entry["sha256"] for entry in runtime_locks
        },
    }
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(canonical(current))
    contract = expected_contract(ROOT, current_path)
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(contract))
    return current_path, contract_path


def expected_contract(root: Path, current_path: Path) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p17-local-daemon-qualification/v1",
        "qualification_id": "p17.local-daemon.v1.20260906",
        "base_commit": BASE_COMMIT,
        "scope": "current_pc_bounded_local_daemon_successor_only",
        "claims": CLAIMS,
        "evidence": {
            "path": (
                "implementation/p17/qualification/"
                "local-daemon-v1-20260906/current-host.json"
            ),
            "canonical_sha256": digest(current_path),
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "runtime_sources": [source_lock(root, relative) for relative in RUNTIME_SOURCES],
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
    }


def verify(root: Path = ROOT) -> dict[str, Any]:
    directory = root / QUALIFICATION.relative_to(ROOT)
    current_path = directory / "current-host.json"
    contract_path = directory / "contract.json"
    current = load_document(current_path, "current")
    contract = load_document(contract_path, "contract")
    require(
        set(current)
        == {
            "check_count",
            "checks",
            "claims",
            "receipt",
            "resources_cleaned",
            "run_id",
            "schema_version",
            "scope",
            "source_commit",
            "source_hashes",
        }
        and current.get("schema_version") == "hwpx-agent.p17-local-daemon-current/v1"
        and current.get("run_id") == RUN_ID
        and current.get("source_commit") == BASE_COMMIT
        and current.get("scope") == "current_pc_synthetic_workspace_local_daemon_only"
        and current.get("checks") == list(EXPECTED_CHECKS)
        and current.get("check_count") == len(EXPECTED_CHECKS)
        and current.get("resources_cleaned") is True
        and current.get("claims") == CLAIMS
        and current.get("receipt")
        == {
            "path": f"artifacts/p17/local-daemon-runs/{RUN_ID}/receipt.json",
            "sha256": RECEIPT_SHA256,
        },
        "current.exact",
    )
    runtime_locks = [source_lock(root, relative) for relative in RUNTIME_SOURCES]
    require(
        current.get("source_hashes")
        == {entry["path"]: entry["sha256"] for entry in runtime_locks},
        "current.sources",
    )
    require(contract == expected_contract(root, current_path), "contract.exact")
    return contract


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: local_daemon_qualification.py RUN_ID|verify")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_LOCAL_DAEMON_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_LOCAL_DAEMON_QUALIFICATION_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    else:
        raise SystemExit("usage: local_daemon_qualification.py RUN_ID|verify")
