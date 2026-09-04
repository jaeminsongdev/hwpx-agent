from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "implementation/p15/p15-async-job-contract-v1.json"
P15_04_AUDITED_REVISION = "4c6224f6001c5daadaaaec907c0bba86db7c6c0f"
P15_05_SUPERSEDING_VALIDATOR = "tools/p15/validate_artifact_delivery_contract.py"
P15_05_SUPERSEDED_PATHS = {
    "Cargo.lock",
    "Cargo.toml",
    "security/dependency-policy.json",
    "crates/mcp-control-plane/Cargo.toml",
    "crates/mcp-control-plane/src/lib.rs",
    "crates/mcp-control-plane/src/handler.rs",
    "crates/mcp-control-plane/tests/handler_contract.rs",
    "tools/p15/validate_handler_contract.py",
    "tools/p15/build_async_job_contract.py",
    "tools/p15/validate_async_job_contract.py",
}

EXPECTED_KEYS = {
    "async_submission_tools",
    "catalog_sha256",
    "client_event_meta_key",
    "handler_sequence_preserved",
    "journal",
    "job_tools",
    "limits",
    "p15_03_implementation_commit",
    "required_behaviors",
    "rust_async_job_tests",
    "schema_version",
    "scope",
    "source_locks",
    "target_profile",
}
EXPECTED_ASYNC_TOOLS = [
    "document_create",
    "document_edit",
    "document_transform",
    "document_validate",
    "document_render",
    "document_export",
]
EXPECTED_BEHAVIORS = [
    "deterministic_idempotent_job_id",
    "ordered_bounded_progress_events",
    "cursor_bound_to_job_and_sequence",
    "queued_cancel_immediate",
    "active_cancel_at_safe_point",
    "committing_cancel_rejected",
    "exactly_one_terminal_receipt",
    "restart_replay_fail_closed",
    "raw_arguments_and_cancel_reason_not_journaled",
]
EXPECTED_SOURCE_PATHS = [
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


def load_json(path: Path) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)
    if not isinstance(value, dict):
        raise ValueError("contract root must be an object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bounded_file(root: Path, relative: str) -> Path:
    value = Path(relative)
    if not relative or "\\" in relative or value.is_absolute() or ".." in value.parts:
        raise ValueError("source path is not bounded")
    resolved_root = root.resolve(strict=True)
    candidate = root / value
    if candidate.is_symlink() or (
        hasattr(candidate, "is_junction") and candidate.is_junction()
    ):
        raise ValueError("source path is linked")
    resolved = candidate.resolve(strict=True)
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise ValueError("source path escapes repository")
    if not 0 < resolved.stat().st_size <= 2_000_000:
        raise ValueError("source file shape is invalid")
    return resolved


def validate_p15_05_supersession(root: Path) -> list[str]:
    validator_path = root / P15_05_SUPERSEDING_VALIDATOR
    specification = importlib.util.spec_from_file_location(
        "p15_artifact_delivery_superseding_validator", validator_path
    )
    if specification is None or specification.loader is None:
        return ["p15_05_supersession.validator_load"]
    module = importlib.util.module_from_spec(specification)
    try:
        specification.loader.exec_module(module)
        errors = module.validate(root)
    except Exception:
        return ["p15_05_supersession.validation"]
    if errors:
        return ["p15_05_supersession.contract"]
    return []


def historical_source_matches(root: Path, relative: str, expected: str) -> bool:
    result = subprocess.run(
        ["git", "show", f"{P15_04_AUDITED_REVISION}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    return result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    p15_05_supersession_errors = validate_p15_05_supersession(root)
    try:
        contract = load_json(root / CONTRACT_PATH.relative_to(ROOT))
    except Exception as error:
        return [f"contract.load:{type(error).__name__}"]

    if set(contract) != EXPECTED_KEYS:
        errors.append("contract.keys")
    if contract.get("schema_version") != "hwpx-agent.p15-async-job-contract/v1":
        errors.append("contract.schema_version")
    if contract.get("scope") != "current_pc_hancom_2020_local_durable_job_reference":
        errors.append("contract.scope")
    if contract.get("target_profile") != "hancom-hangul-2020-secondary":
        errors.append("contract.target_profile")
    if contract.get("p15_03_implementation_commit") != (
        "9e7ed73524be0049292fbdf45f2170df6f997fae"
    ):
        errors.append("contract.predecessor")
    if contract.get("catalog_sha256") != (
        "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001"
    ):
        errors.append("contract.catalog_sha256")
    if contract.get("catalog_sha256") != sha256(
        root / "protocol/mcp/p15-public-tools-v1.json"
    ):
        errors.append("contract.catalog_drift")
    if contract.get("async_submission_tools") != EXPECTED_ASYNC_TOOLS:
        errors.append("contract.async_tools")
    if contract.get("job_tools") != ["job_get", "job_cancel"]:
        errors.append("contract.job_tools")
    if contract.get("client_event_meta_key") != "hwpx/jobEvents":
        errors.append("contract.event_meta")
    if contract.get("handler_sequence_preserved") is not True:
        errors.append("contract.handler_sequence")
    if contract.get("journal") != {
        "append_only": True,
        "checksum": "sha256",
        "file_name": "p15-job-journal-v1.jsonl",
        "fsync_before_publish": True,
        "schema_version": "hwpx-agent.p15-job-journal/v1",
    }:
        errors.append("contract.journal")
    if contract.get("limits") != {
        "event_page": 200,
        "events_per_job": 256,
        "jobs": 4_096,
        "journal_bytes": 67_108_864,
        "journal_entries": 65_536,
        "journal_entry_bytes": 1_048_576,
        "progress_events_per_job": 248,
        "result_artifacts": 128,
    }:
        errors.append("contract.limits")
    if contract.get("required_behaviors") != EXPECTED_BEHAVIORS:
        errors.append("contract.behaviors")
    if contract.get("rust_async_job_tests") != 11:
        errors.append("contract.rust_tests")

    locks = contract.get("source_locks")
    if not isinstance(locks, list) or len(locks) != len(EXPECTED_SOURCE_PATHS):
        errors.append("contract.source_locks")
    else:
        seen: set[str] = set()
        for index, entry in enumerate(locks):
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                errors.append(f"source_lock[{index}].shape")
                continue
            relative = entry.get("path")
            expected = entry.get("sha256")
            if (
                not isinstance(relative, str)
                or relative in seen
                or relative != EXPECTED_SOURCE_PATHS[index]
            ):
                errors.append(f"source_lock[{index}].path")
                continue
            seen.add(relative)
            try:
                source = bounded_file(root, relative)
            except Exception:
                errors.append(f"source_lock[{index}].bounded")
                continue
            if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
                errors.append(f"source_lock[{index}].digest_shape")
            elif sha256(source) != expected:
                if relative not in P15_05_SUPERSEDED_PATHS or p15_05_supersession_errors:
                    errors.append(f"source_lock[{index}].digest")
                elif not historical_source_matches(root, relative, expected):
                    errors.append(f"source_lock[{index}].historical_digest")

    source = (root / "crates/mcp-control-plane/src/async_jobs.rs").read_text(
        encoding="utf-8"
    )
    required_tokens = [
        'const JOURNAL_SCHEMA_VERSION: &str = "hwpx-agent.p15-job-journal/v1";',
        'const JOURNAL_FILE_NAME: &str = "p15-job-journal-v1.jsonl";',
        "OpenOptions::new()",
        ".append(true)",
        "stream.sync_all()",
        "parse_unique_value(&buffer)",
        "validate_evolution(previous, &entry.job)",
        'derive_id("job_"',
        "CancellationPending",
        "acknowledge_cancellation",
        "terminal_receipt",
        '"hwpx/jobEvents"',
        "make_cursor(&job.job_id",
        "reason_sha256",
    ]
    for token in required_tokens:
        if token not in source:
            errors.append(f"async_jobs.token:{token}")
    for forbidden in ["unsafe {", "std::process", "Command::", "HAction", "raw_xml"]:
        if forbidden in source:
            errors.append(f"async_jobs.forbidden:{forbidden}")
    if "reason: String" in source or "arguments: Value" in source:
        errors.append("async_jobs.raw_payload_persistence")
    if source.count("ToolKind::DocumentCreate") < 2:
        errors.append("async_jobs.submission_tools")

    handler = (root / "crates/mcp-control-plane/src/handler.rs").read_text(
        encoding="utf-8"
    )
    if handler.count("self.gateway.dispatch(call)") != 1:
        errors.append("handler.dispatch_count")
    for token in [
        "ToolServiceOutput",
        "job_event_page.is_some() && tool != ToolKind::JobGet",
        "output_is_valid(&output)",
        "correlation.matches(&output)",
    ]:
        if token not in handler:
            errors.append(f"handler.token:{token}")
    order = [
        handler.find(".policy.authorize("),
        handler.find("self.gateway.dispatch(call)"),
        handler.find("output_is_valid(&output)"),
        handler.find("correlation.matches(&output)"),
    ]
    if any(position < 0 for position in order) or order != sorted(order):
        errors.append("handler.order")

    rust_tests = (root / "crates/mcp-control-plane/tests/async_job_ux.rs").read_text(
        encoding="utf-8"
    )
    if rust_tests.count("#[test]") != 11:
        errors.append("rust_tests.count")
    for token in [
        "submit_progress_poll_terminal_and_restart_is_end_to_end",
        "all_six_long_running_tools_return_schema_valid_durable_jobs",
        "running_cancel_waits_for_safe_point_and_blocks_progress",
        "cancel_after_success_returns_the_single_terminal_receipt",
        "malformed_or_duplicate_journal_data_fails_reopen",
    ]:
        if token not in rust_tests:
            errors.append(f"rust_tests.token:{token}")
    return errors


def main() -> int:
    errors = validate()
    print(
        json.dumps(
            {
                "async_submission_tools": 6,
                "errors": errors,
                "job_tools": 2,
                "rust_async_job_tests": 11,
                "schema_version": "hwpx-agent.p15-async-job-validation/v1",
                "source_files": len(EXPECTED_SOURCE_PATHS),
                "state": "pass" if not errors else "fail",
            },
            sort_keys=True,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
