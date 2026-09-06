"""Freeze and verify the P17-05 local workflow MCP qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import run_local_workflow_checks as host_checks


ROOT = Path(__file__).resolve().parents[2]
QUALIFICATION = ROOT / "implementation/p17/qualification/local-workflow-v1-20260906"
RUN_ID = "bf248400ce1c4985bb2353aa9209ec02"
BASE_COMMIT = "e1e3edaa7e830cc05086bc1af2847bdbf00c8506"
RECEIPT_SHA256 = "36641be1a6bf7d37c3a796c624cfcb885b6c650acffac14e3d4d8fe1b55fe721"
CLAIMS = {
    "actual_mcp_stdio": True,
    "actual_codex_client": False,
    "actual_personal_plugin": False,
    "actual_git_commit": False,
    "actual_hangul": False,
    "network_used": False,
    "path_free_public_inputs": True,
    "source_preserved": True,
    "phase_complete": False,
}
RUNTIME_SOURCES = (
    "Cargo.toml",
    "Cargo.lock",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "crates/local-workflow/Cargo.toml",
    "crates/local-workflow/src/lib.rs",
    "crates/local-workflow/tests/workflow.rs",
    "crates/local-companion-daemon/Cargo.toml",
    "crates/local-companion-daemon/src/lib.rs",
    "crates/local-companion-daemon/src/main.rs",
    "crates/local-companion-daemon/tests/binary_smoke.rs",
    "crates/local-companion-daemon/tests/sandbox.rs",
    "protocol/private/p17-local-workflow-v1.json",
    "protocol/private/p17-local-daemon-v1.json",
    "protocol/private/p17-local-daemon-v2.json",
    "protocol/private/p17-local-mcp-v1.json",
    "protocol/private/p17-local-mcp-v2.json",
    "web/local-companion-mcp/package.json",
    "web/local-companion-mcp/tsconfig.json",
    "web/local-companion-mcp/src/server.ts",
    "web/local-companion-mcp/src/server.test.ts",
    "tools/p17/run_local_workflow_checks.py",
    "tools/p17/tests/test_local_workflow_checks.py",
)
GUARD_SOURCES = (
    "tools/p17/local_workflow_qualification.py",
    "tools/p17/tests/test_local_workflow_qualification.py",
    "implementation/p17/P17-05_LOCAL_WORKFLOW_MCP_V2.md",
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


def receipt_path(root: Path) -> Path:
    return root / "artifacts/p17/local-workflow-runs" / RUN_ID / "receipt.json"


def expected_receipt() -> dict[str, Any]:
    return {
        "actual_codex_client": False,
        "actual_git_commit": False,
        "actual_hangul": False,
        "actual_mcp_stdio": True,
        "actual_personal_plugin": False,
        "check_count": len(host_checks.CHECKS),
        "checks": list(host_checks.CHECKS),
        "decision": "PASS",
        "network_used": False,
        "passed": True,
        "resources_cleaned": True,
        "run_id": RUN_ID,
        "schema_version": "hwpx-agent.p17-local-workflow-check/v1",
        "scope": "current_pc_local_stdio_mcp_path_free_workflow",
        "source_commit": BASE_COMMIT,
        "tracked_clean": True,
    }


def validate_receipt(receipt: dict[str, Any]) -> None:
    require(receipt == expected_receipt(), "receipt.exact")


def git_blob(relative: str) -> bytes:
    executable = shutil.which("git")
    require(executable is not None, "git.missing")
    completed = subprocess.run(
        [executable, "show", f"{BASE_COMMIT}:{relative}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(completed.returncode == 0, "base.source")
    return completed.stdout


def require_runtime_matches_base() -> None:
    for relative in RUNTIME_SOURCES:
        current = (ROOT / relative).read_bytes()
        require(current == git_blob(relative), "base.drift")


def current_document(runtime_locks: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema_version": "hwpx-agent.p17-local-workflow-current/v1",
        "scope": "current_pc_local_stdio_mcp_path_free_workflow",
        "run_id": RUN_ID,
        "source_commit": BASE_COMMIT,
        "checks": list(host_checks.CHECKS),
        "claims": CLAIMS,
        "receipt": {
            "path": f"artifacts/p17/local-workflow-runs/{RUN_ID}/receipt.json",
            "sha256": RECEIPT_SHA256,
        },
        "source_hashes": {entry["path"]: entry["sha256"] for entry in runtime_locks},
    }


def expected_contract(root: Path, current_path: Path) -> dict[str, object]:
    return {
        "schema_version": "hwpx-agent.p17-local-workflow-qualification/v1",
        "qualification_id": "p17.local-workflow.v1.20260906",
        "base_commit": BASE_COMMIT,
        "scope": "current_pc_local_stdio_mcp_path_free_workflow_only",
        "claims": CLAIMS,
        "evidence": {
            "path": (
                "implementation/p17/qualification/"
                "local-workflow-v1-20260906/current-host.json"
            ),
            "canonical_sha256": digest(current_path),
            "run_id": RUN_ID,
            "receipt_sha256": RECEIPT_SHA256,
        },
        "runtime_sources": [source_lock(root, relative) for relative in RUNTIME_SOURCES],
        "guard_sources": [source_lock(root, relative) for relative in GUARD_SOURCES],
    }


def qualify() -> tuple[Path, Path]:
    receipt = load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt)
    require(digest(receipt_path(ROOT)) == RECEIPT_SHA256, "receipt.digest")
    require_runtime_matches_base()
    runtime_locks = [source_lock(ROOT, relative) for relative in RUNTIME_SOURCES]
    QUALIFICATION.mkdir(parents=True, exist_ok=True)
    current_path = QUALIFICATION / "current-host.json"
    current_path.write_bytes(canonical(current_document(runtime_locks)))
    contract_path = QUALIFICATION / "contract.json"
    contract_path.write_bytes(canonical(expected_contract(ROOT, current_path)))
    return current_path, contract_path


def verify(root: Path = ROOT) -> dict[str, Any]:
    directory = root / QUALIFICATION.relative_to(ROOT)
    current_path = directory / "current-host.json"
    contract_path = directory / "contract.json"
    current = load_document(current_path, "current")
    contract = load_document(contract_path, "contract")
    runtime_locks = [source_lock(root, relative) for relative in RUNTIME_SOURCES]
    require(current == current_document(runtime_locks), "current.exact")
    require(contract == expected_contract(root, current_path), "contract.exact")
    return contract


def verify_host() -> None:
    verify()
    receipt = load_document(receipt_path(ROOT), "receipt")
    validate_receipt(receipt)
    require(digest(receipt_path(ROOT)) == RECEIPT_SHA256, "receipt.digest")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: local_workflow_qualification.py RUN_ID|verify|verify-host")
    if sys.argv[1] == RUN_ID:
        current_file, contract_file = qualify()
        print(
            "P17_LOCAL_WORKFLOW_QUALIFICATION_PASS "
            f"current={current_file.name} contract={contract_file.name}"
        )
    elif sys.argv[1] == "verify":
        verified = verify()
        print(
            "P17_LOCAL_WORKFLOW_VERIFY_PASS "
            f"qualification={verified['qualification_id']}"
        )
    elif sys.argv[1] == "verify-host":
        verify_host()
        print("P17_LOCAL_WORKFLOW_HOST_VERIFY_PASS")
    else:
        raise SystemExit("usage: local_workflow_qualification.py RUN_ID|verify|verify-host")
