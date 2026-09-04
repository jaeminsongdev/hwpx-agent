from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-async-job-contract-v1.json"
CATALOG_PATH = ROOT / "protocol/mcp/p15-public-tools-v1.json"

SOURCE_PATHS = [
    "Cargo.toml",
    "Cargo.lock",
    "deny.toml",
    "security/dependency-policy.json",
    "protocol/mcp/p15-public-tools-v1.json",
    "implementation/p15/p15-public-tool-schema-contract-v1.json",
    "implementation/p15/p15-handler-contract-v1.json",
    "implementation/p15/P15-04_ASYNC_JOB_POLICY.md",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/catalog.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/src/policy.rs",
    "crates/mcp-control-plane/src/strict_json.rs",
    "crates/mcp-control-plane/src/async_jobs.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "crates/mcp-control-plane/tests/async_job_ux.rs",
    "tools/p15/build_handler_contract.py",
    "tools/p15/validate_handler_contract.py",
    "tools/p15/build_async_job_contract.py",
    "tools/p15/validate_async_job_contract.py",
    "tools/p15/tests/test_handler_contract.py",
    "tools/p15/tests/test_async_job_contract.py",
]


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_contract(root: Path = ROOT) -> dict[str, Any]:
    return {
        "async_submission_tools": [
            "document_create",
            "document_edit",
            "document_transform",
            "document_validate",
            "document_render",
            "document_export",
        ],
        "catalog_sha256": sha256_file(root / CATALOG_PATH.relative_to(ROOT)),
        "client_event_meta_key": "hwpx/jobEvents",
        "handler_sequence_preserved": True,
        "journal": {
            "append_only": True,
            "checksum": "sha256",
            "file_name": "p15-job-journal-v1.jsonl",
            "fsync_before_publish": True,
            "schema_version": "hwpx-agent.p15-job-journal/v1",
        },
        "job_tools": ["job_get", "job_cancel"],
        "limits": {
            "event_page": 200,
            "events_per_job": 256,
            "jobs": 4_096,
            "journal_bytes": 67_108_864,
            "journal_entries": 65_536,
            "journal_entry_bytes": 1_048_576,
            "progress_events_per_job": 248,
            "result_artifacts": 128,
        },
        "p15_03_implementation_commit": (
            "9e7ed73524be0049292fbdf45f2170df6f997fae"
        ),
        "required_behaviors": [
            "deterministic_idempotent_job_id",
            "ordered_bounded_progress_events",
            "cursor_bound_to_job_and_sequence",
            "queued_cancel_immediate",
            "active_cancel_at_safe_point",
            "committing_cancel_rejected",
            "exactly_one_terminal_receipt",
            "restart_replay_fail_closed",
            "raw_arguments_and_cancel_reason_not_journaled",
        ],
        "rust_async_job_tests": 11,
        "schema_version": "hwpx-agent.p15-async-job-contract/v1",
        "scope": "current_pc_hancom_2020_local_durable_job_reference",
        "source_locks": [
            {"path": relative, "sha256": sha256_file(root / relative)}
            for relative in SOURCE_PATHS
        ],
        "target_profile": "hancom-hangul-2020-secondary",
    }


def write_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    expected = canonical_bytes(build_contract())
    if arguments.write:
        write_atomic(CONTRACT_PATH, expected)
        print(json.dumps({"state": "written", "sources": len(SOURCE_PATHS)}))
        return 0
    actual = CONTRACT_PATH.read_bytes() if CONTRACT_PATH.is_file() else b""
    errors = [] if actual == expected else ["async job contract drift"]
    print(
        json.dumps(
            {
                "errors": errors,
                "sources": len(SOURCE_PATHS),
                "state": "pass" if not errors else "fail",
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
