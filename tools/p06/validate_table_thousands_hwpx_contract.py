#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any
import zipfile

try:
    from tools.p06.validate_table_geometry_contract import (
        add_error,
        bounded_file,
        canonical_sha256,
        reject_duplicate_keys,
    )
except ModuleNotFoundError:
    from validate_table_geometry_contract import (  # type: ignore[no-redef]
        add_error,
        bounded_file,
        canonical_sha256,
        reject_duplicate_keys,
    )


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-thousands-hwpx-v1.json"
PREDECESSOR = "protocol/private/p06-table-thousands-v1.json"
MIGRATION = "protocol/migrations/p06-table-thousands-v1-to-hwpx-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_THOUSANDS_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_THOUSANDS_HWPX_REPORT.md"
RECEIPT = (
    "implementation/p06/evidence/target/"
    "p06-table-thousands.current-2020.attempt11.v1.json"
)
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-thousands-source-20260913-11"

FEATURES = [
    {"feature_id": "TABLE-032", "capability_id": "table.thousands_add"},
    {"feature_id": "TABLE-033", "capability_id": "table.thousands_remove"},
]
TARGET = {
    "product": "Hancom Hangul 2020",
    "prog_id": "HWPFrame.HwpObject.2",
    "registry_view": "Registry32",
    "client": "windows_powershell_x86_sta",
    "build": "11.0.0.9136",
    "architecture": "x86",
    "locale": "ko-KR",
    "executable_sha256": (
        "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
    ),
}
ARTIFACTS = {
    "baseline": {
        "path": f"{TARGET_DIRECTORY}/baseline.hwpx",
        "sha256": "8b125fd14e69612b7896f22f7a8e93180709ae41c675aba5166a03820aa1ff7c",
        "bytes": 14021,
    },
    "removed": {
        "path": f"{TARGET_DIRECTORY}/removed.hwpx",
        "sha256": "985e5a87f4396cc113203e00acae2b2868b515c409c07b51d167dc496081519a",
        "bytes": 13987,
    },
    "added": {
        "path": f"{TARGET_DIRECTORY}/added.hwpx",
        "sha256": "15166fd74bc5f9cee21df4833b3d994e78edec2c700a4a612bc63e3be987a419",
        "bytes": 14021,
    },
    "watchdog": {
        "path": f"{TARGET_DIRECTORY}/watchdog.json",
        "sha256": "50c234656d623d324a5bddf13b6b00623af038eeb970d97e78dc3d77b499255a",
        "bytes": 2284,
    },
    "inner_trace": {
        "path": f"{TARGET_DIRECTORY}/watchdog.json.inner.2816.json",
        "sha256": "134d641d16830a9d06572e24250c389262ecdf447236acb9f970626b433d2656",
        "bytes": 1711,
    },
    "progress": {
        "path": f"{TARGET_DIRECTORY}/watchdog.json.progress.jsonl",
        "sha256": "339531323f079e522fbd634af5675ab8e62d6803a1d6cdba0ce9b3ce537a4c85",
        "bytes": 6691,
    },
}
SOURCE_LOCKS = {
    PREDECESSOR: "40962ec31a4079c38a9e979c32744bb0e171b1469ad09f5f8a13b7befe90896d",
    "crates/domain-ir/src/table_thousands.rs": (
        "5c94390f6925641f1c88940cdb184112fdf92f2c141ecd117b7210f00e8ae513"
    ),
    "crates/hwpx-package/src/table_formula/thousands_hwpx.rs": (
        "f89da32df37600cd9b567984f278a9bf3af58fc35c3555fb0107f4e85bb6fc72"
    ),
    "crates/hwpx-package/src/table_formula.rs": (
        "a9713fcf485797b979f77f0748be11c2c47375a6426e89002cfc504c7db5cbe0"
    ),
    "crates/hwpx-package/src/lib.rs": (
        "dfe19ae6b2fb7b044c831ddcafbeba7cb5f4a30e9c2b69508ad81f5fd05395cc"
    ),
    "crates/hwpx-package/tests/table_thousands_hwpx.rs": (
        "d16dd36791f66b51f63058c27db21099cc875d851d29413b63f569457d8d691e"
    ),
    "crates/hwpx-package/examples/p06_09_table_thousands_source_oracle.rs": (
        "5b9a802cb97a42e26fe4f59404a5783d8216f93bc4aee5cfd3d2000d05f015d5"
    ),
    "implementation/p06/tools/run-hancom-2020-table-thousands-source.ps1": (
        "9e5544f3d3bee530119e2f3a0cc590ddf4646028efb2de23454b1861d177394b"
    ),
    "implementation/p06/tools/create-hancom-2020-table-thousands-source.ps1": (
        "918fda61a1786c9c0fa9c4419e639ab7a91f2616833e31527081d9a563a291a2"
    ),
    "implementation/p06/tests/Test-Hancom2020TableThousandsSource.ps1": (
        "9aeaff93619ed22610b64675287d31da10b63d513ac61ddea4d28f58c4c0300c"
    ),
}
NATIVE_READBACK = {
    "profile_id": "hwpx-agent.table-thousands-hwpx.hancom-2020/1",
    "entry_count": 11,
    "formula_fields": 1,
    "dimensions": [1, 3],
    "baseline_section_sha256": (
        "5219797343842c6c0b8574fc009a94321156536f8dcc9ece86b5463dc343ec7b"
    ),
    "removed_section_sha256": (
        "23bfe50d5d91d0d8b2daa5cbef77a8abaff17b0081e38902ed0170c63c23b4fb"
    ),
    "added_section_sha256": (
        "5219797343842c6c0b8574fc009a94321156536f8dcc9ece86b5463dc343ec7b"
    ),
    "baseline_state_sha256": (
        "0c580fa4bf57b0aa6bdb8ac1a904342051abb5a650729d755681f8f45e09fe2f"
    ),
    "removed_state_sha256": (
        "6f40fc6850ba1828391010de820560ef3748a2da8248dedfd1a0969956ac7da5"
    ),
    "added_state_sha256": (
        "0c580fa4bf57b0aa6bdb8ac1a904342051abb5a650729d755681f8f45e09fe2f"
    ),
    "grid_sha256": "9f788492324db31aa6e8c7c5728b7856e60874be3be295d125094c477586314c",
    "document_flow_sha256": (
        "5b6f074bb798241259accdba49969063d5b3747d3884463dce1052004f6585ec"
    ),
    "baseline_and_added_sections_equal": True,
    "formula_ast_preserved": True,
    "numeric_cache_preserved": True,
    "grid_preserved": True,
}
DIRECT_DIFFERENTIAL = {
    "remove_section_exact_match": True,
    "add_section_exact_match": True,
    "remove_modified_text_count": 1,
    "add_modified_text_count": 1,
    "unowned_bytes_preserved": True,
    "document_flow_preserved": True,
}
EXPECTED_EVIDENCE = {
    "domain_tests": 9,
    "adapter_tests": 6,
    "source_static_tests": 23,
    "contract_tests": 4,
    "feature_count": 2,
    "backend": "direct_hwpx",
    "direct_stage": "integration_passed",
    "fixture_classes": ["boundary", "happy_path", "negative", "preservation", "security"],
    "validations": ["formula_readback", "schema", "semantic_reopen"],
}
GATE_DECISION = {
    "TABLE-032": "integration_passed",
    "TABLE-033": "integration_passed",
    "actual_hancom_2020_native_source": "pass",
    "direct_section_differential": "pass",
    "direct_output_package_save_reopen": "not_run",
    "direct_output_render": "not_run",
    "rollback_or_retry": "not_run",
    "automation_runtime": "not_run",
    "release_differential": "not_run",
    "p06_09": "in_progress",
    "p06": "in_progress",
}
NOT_CLAIMED = {
    "direct_output_package_save_reopen": False,
    "direct_output_render": False,
    "rollback_or_retry": False,
    "product_automation_route_runtime": False,
    "release_differential": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_hancom_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}

IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_formula/thousands_hwpx.rs": (
        'TABLE_THOUSANDS_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-thousands-hwpx/v1"',
        'TABLE_THOUSANDS_HWPX_PROFILE_ID: &str = "hwpx-agent.table-thousands-hwpx.hancom-2020/1"',
        "pub struct TableThousandsHwpxReadback",
        "pub struct TableThousandsHwpxRequestDraft",
        "impl fmt::Debug for TableThousandsHwpxRequestDraft",
        "pub struct TableThousandsHwpxLoweringReceipt",
        "pub fn lower_in_section_with_receipt(",
        "fn parse_grouped_result(",
        "fn validate_plan_against_source(",
    ),
    "crates/hwpx-package/src/table_formula.rs": ("mod thousands_hwpx;", "pub use thousands_hwpx::{"),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_THOUSANDS_HWPX_PROFILE_ID",
        "TableThousandsHwpxLowerer",
        "TableThousandsHwpxReader",
    ),
    "crates/hwpx-package/tests/table_thousands_hwpx.rs": (
        "remove_changes_only_visible_result_and_preserves_native_metadata",
        "add_restores_exact_grouped_bytes_and_same_mode_is_idempotent",
        "negative_decimal_grouping_is_exact_and_non_format_state_is_preserved",
        "request_and_build_both_reject_section_flow_and_plan_drift",
        "malformed_or_ambiguous_native_profiles_fail_closed",
        "strict_json_rejects_duplicate_unknown_and_invalid_digest_fields",
        "<redacted>",
    ),
    "crates/hwpx-package/examples/p06_09_table_thousands_source_oracle.rs": (
        "hwpx-agent.p06-09-table-thousands-source-oracle/v1",
        "remove_section_exact_match",
        "add_section_exact_match",
        "direct_output_package_save_reopen",
    ),
    "implementation/p06/tools/run-hancom-2020-table-thousands-source.ps1": (
        "formula_cell_select",
        "progress_valid",
        "remaining_hwp_process_count",
    ),
    "implementation/p06/tools/create-hancom-2020-table-thousands-source.ps1": (
        "TableDeleteComma",
        "TableInsertComma",
        "TableCellBlock",
    ),
    "implementation/p06/tests/Test-Hancom2020TableThousandsSource.ps1": (
        "'baseline_save', 'formula_cell_select', 'delete_thousands'",
        "TableDeleteComma",
        "TableInsertComma",
    ),
    POLICY: (
        "exact current-target native-source HWPX integration passed",
        "direct_hwpx / integration_passed",
        "Attempts 01-10 remain failed",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "6/6 PASS",
        "23/23 PASS",
        "green rows: remains 0/61",
    ),
}


def load_json_bytes(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)


def exact_bytes(root: Path, relative: str, maximum: int = 8 * 1024 * 1024) -> bytes:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("unsafe path")
    path = root.joinpath(*pure.parts)
    stat = path.lstat()
    if path.is_symlink() or not path.is_file() or stat.st_size == 0 or stat.st_size > maximum:
        raise ValueError("not a bounded regular file")
    data = path.read_bytes()
    if len(data) != stat.st_size:
        raise ValueError("file changed during read")
    return data


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json_bytes(exact_bytes(root, CONTRACT, 512_000))
        if not isinstance(contract, dict):
            raise ValueError("contract root")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0)

    validate_contract(contract, errors)
    source_count = validate_source_locks(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    evidence_count = validate_evidence_files(root, errors)
    validate_runtime_records(root, errors)
    validate_native_packages(root, errors)
    validate_receipt(root, errors)
    validate_migration(root, errors)
    return result(errors, source_count, evidence_count, implementation_count)


def validate_contract(contract: dict[str, Any], errors: list[str]) -> None:
    expected_keys = {
        "schema_version", "profile_id", "predecessor", "scope", "features",
        "source_lock_canonicalization", "source_locks", "exact_target",
        "successful_attempt", "native_profile", "transition", "binding",
        "preservation", "receipt", "expected_evidence", "failure_policy",
        "migration", "policy", "report", "gate_decision", "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    expected = {
        "schema_version": "hwpx-agent.table-thousands-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-thousands-hwpx.hancom-2020/1",
        "predecessor": {
            "path": PREDECESSOR,
            "sha256": SOURCE_LOCKS[PREDECESSOR],
            "state": "immutable_pure_planner_contract",
        },
        "scope": (
            "p06_09_exact_current_pc_hancom_2020_native_source_and_preserving_section_integration"
        ),
        "features": FEATURES,
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "exact_target": TARGET,
        "successful_attempt": {
            "id": "20260913-11",
            "directory": TARGET_DIRECTORY,
            "state": "pass",
            "progress_events": 22,
            "artifacts": ARTIFACTS,
        },
        "expected_evidence": EXPECTED_EVIDENCE,
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "gate_decision": GATE_DECISION,
        "not_claimed": NOT_CLAIMED,
    }
    for key, value in expected.items():
        if contract.get(key) != value:
            add_error(errors, key)

    semantic_fields = {
        "native_profile": {
            "table": "one_complete_unmerged_1_by_3_grid_with_exact_selected_formula_owner",
            "formula": "selected_native_formula_equals_SUM_LEFT",
            "metadata": "result_format_formula_last_result_command_and_field_identity_are_exact_and_unmodified",
            "grouping": "grouped_last_result_is_unambiguous_and_visible_text_is_grouped_or_plain_equivalent",
            "ownership": "only_selected_visible_result_text_spans_are_owned",
        },
        "transition": {
            "add": "replace_plain_visible_result_with_exact_grouped_last_result",
            "remove": "replace_grouped_visible_result_with_exact_plain_equivalent",
            "idempotence": "already_requested_visible_state_returns_zero_edits",
            "native_differential": "both_direct_output_sections_equal_corresponding_hancom_authored_sections",
        },
        "binding": {
            "request": "exact_section_selected_state_grid_document_flow_and_plan_sha256",
            "build": "recheck_all_request_bindings_and_native_profile_before_edit",
            "readback": "reopen_selected_formula_grid_and_unowned_bytes_before_return",
            "serialization": "bounded_deterministic_strict_json_with_duplicate_and_unknown_key_rejection",
        },
        "preservation": {
            "formula": "owner_ast_numeric_cache_decimal_places_and_all_native_metadata_exact",
            "grid": "dimensions_coordinates_spans_and_nonmerged_coverage_exact",
            "section": "all_bytes_outside_selected_visible_results_exact",
            "flow": "caller_bound_document_flow_digest_exact",
        },
        "receipt": {
            "path": RECEIPT,
            "hashes": "source_output_section_state_grid_flow_plan_and_unowned_sha256",
            "counts": "selected_formula_cells_and_modified_text_spans",
            "debug": "all_hashes_formula_metadata_document_content_and_raw_xml_redacted",
        },
    }
    for key, value in semantic_fields.items():
        if contract.get(key) != value:
            add_error(errors, key)
    failure = contract.get("failure_policy")
    if (
        not isinstance(failure, list)
        or len(failure) != 10
        or len(set(failure)) != 10
        or any(not isinstance(item, str) or not item for item in failure)
    ):
        add_error(errors, "failure_policy")


def validate_source_locks(root: Path, value: Any, errors: list[str]) -> int:
    expected = [{"path": path, "sha256": sha256} for path, sha256 in SOURCE_LOCKS.items()]
    if value != expected:
        add_error(errors, "source_locks_exact")
    for path, expected_sha in SOURCE_LOCKS.items():
        try:
            actual = canonical_sha256(bounded_file(root, path, 4_000_000))
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "source_lock_path")
            continue
        if actual != expected_sha:
            add_error(errors, "source_lock_digest")
    return len(SOURCE_LOCKS)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for path, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_file(root, path, 4_000_000).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "implementation_path")
            continue
        if any(marker not in text for marker in markers):
            add_error(errors, "implementation_marker")
    return len(IMPLEMENTATION_MARKERS)


def validate_evidence_files(root: Path, errors: list[str]) -> int:
    for item in ARTIFACTS.values():
        try:
            data = exact_bytes(root, item["path"])
        except (OSError, ValueError):
            add_error(errors, "evidence_path")
            continue
        if len(data) != item["bytes"] or digest(data) != item["sha256"]:
            add_error(errors, "evidence_digest")
    return len(ARTIFACTS)


def validate_runtime_records(root: Path, errors: list[str]) -> None:
    try:
        watchdog = load_json_bytes(exact_bytes(root, ARTIFACTS["watchdog"]["path"]))
        inner = load_json_bytes(exact_bytes(root, ARTIFACTS["inner_trace"]["path"]))
        progress_lines = exact_bytes(root, ARTIFACTS["progress"]["path"]).splitlines()
        progress = [load_json_bytes(line) for line in progress_lines]
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "runtime_json")
        return

    worker_expected = {
        "state": "pass", "table_create": "pass", "operand_cells_written": 2,
        "formula_action": "pass", "formula_cell_selection": "pass",
        "delete_thousands_action": "pass", "insert_thousands_action": "pass",
    }
    for key, value in worker_expected.items():
        if watchdog.get(key) != value or inner.get(key) != value:
            add_error(errors, "runtime_state")
    for value in (watchdog, inner):
        if (
            value.get("target_build") != TARGET["build"]
            or value.get("executable_sha256") != TARGET["executable_sha256"]
            or value.get("raw_document_text_present") is not False
            or value.get("raw_formula_or_command_present") is not False
            or value.get("user_document_opened") is not False
            or value.get("external_network_invoked") is not False
            or value.get("registry_or_system_setting_changed") is not False
            or value.get("computer_use_click_or_type_invoked") is not False
        ):
            add_error(errors, "runtime_safety")
    summary = watchdog.get("watchdog")
    if not isinstance(summary, dict) or any(
        (
            summary.get("timed_out") is not False,
            summary.get("child_exit_code") != 0,
            summary.get("progress_valid") is not True,
            summary.get("progress_event_count") != 22,
            summary.get("progress_last_phase") != "terminal",
            summary.get("progress_last_state") != "pass",
            summary.get("remaining_hwp_process_count") != 0,
            summary.get("inner_trace_preserved") is not True,
        )
    ):
        add_error(errors, "watchdog_summary")

    allowed_phases = {
        "preflight", "com_create", "table_create", "formula_operands", "formula_author",
        "formula_cell_select", "baseline_save", "delete_thousands", "removed_save",
        "insert_thousands", "added_save", "terminal",
    }
    if len(progress) != 22:
        add_error(errors, "progress_count")
    for index, event in enumerate(progress, 1):
        if (
            not isinstance(event, dict)
            or event.get("sequence") != index
            or event.get("phase") not in allowed_phases
            or event.get("state") not in {"running", "pass"}
            or event.get("raw_document_text_present") is not False
            or event.get("raw_formula_or_command_present") is not False
        ):
            add_error(errors, "progress_event")
    if not progress or progress[-1].get("phase") != "terminal" or progress[-1].get("state") != "pass":
        add_error(errors, "progress_terminal")


def read_package(root: Path, item: dict[str, Any], errors: list[str]) -> tuple[set[str], bytes, bytes] | None:
    try:
        data = exact_bytes(root, item["path"])
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or len(names) != 11:
                raise ValueError("entry set")
            if any(
                PurePosixPath(name).is_absolute()
                or any(part in {"", ".", ".."} for part in PurePosixPath(name).parts)
                for name in names
            ):
                raise ValueError("unsafe entry")
            section = archive.read("Contents/section0.xml")
            flow = archive.read("Contents/content.hpf")
        return set(names), section, flow
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        add_error(errors, "native_package")
        return None


def validate_native_packages(root: Path, errors: list[str]) -> None:
    packages = [read_package(root, ARTIFACTS[name], errors) for name in ("baseline", "removed", "added")]
    if any(value is None for value in packages):
        return
    baseline, removed, added = packages  # type: ignore[misc]
    if baseline[0] != removed[0] or baseline[0] != added[0]:
        add_error(errors, "native_entry_set")
    if baseline[2] != removed[2] or baseline[2] != added[2] or digest(baseline[2]) != NATIVE_READBACK["document_flow_sha256"]:
        add_error(errors, "native_flow")
    if (
        digest(baseline[1]) != NATIVE_READBACK["baseline_section_sha256"]
        or digest(removed[1]) != NATIVE_READBACK["removed_section_sha256"]
        or digest(added[1]) != NATIVE_READBACK["added_section_sha256"]
    ):
        add_error(errors, "native_section_digest")
    grouped = b"<hp:t>4,600</hp:t>"
    plain = b"<hp:t>4600</hp:t>"
    if (
        baseline[1] != added[1]
        or baseline[1].count(grouped) != 1
        or removed[1] != baseline[1].replace(grouped, plain, 1)
        or baseline[1].count(b'type="FORMULA"') != 1
        or b'rowCnt="1" colCnt="3"' not in baseline[1]
    ):
        add_error(errors, "native_transition")
    for marker in (
        b'name="Formula">=SUM(LEFT)',
        b'name="ResultFormat">%g,',
        b'name="LastResult">4,600',
        b'name="Command">=SUM(LEFT)??%g,;;4,600',
    ):
        if marker not in baseline[1] or marker not in removed[1] or marker not in added[1]:
            add_error(errors, "native_metadata")


def validate_receipt(root: Path, errors: list[str]) -> None:
    try:
        receipt = load_json_bytes(exact_bytes(root, RECEIPT, 512_000))
        if not isinstance(receipt, dict):
            raise ValueError("receipt root")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "evidence_receipt")
        return
    expected_keys = {
        "schema_version", "evidence_id", "scope", "features", "attempt",
        "native_readback", "direct_differential", "verification", "historical_attempts",
        "privacy", "gate_decision", "not_claimed",
    }
    if set(receipt) != expected_keys:
        add_error(errors, "evidence_receipt_shape")
    if (
        receipt.get("schema_version") != "hwpx-agent.p06-09-table-thousands-current-2020-evidence/v1"
        or receipt.get("features") != FEATURES
        or receipt.get("native_readback") != NATIVE_READBACK
        or receipt.get("direct_differential") != DIRECT_DIFFERENTIAL
        or receipt.get("gate_decision") != GATE_DECISION
        or receipt.get("not_claimed") != NOT_CLAIMED
    ):
        add_error(errors, "evidence_receipt")
    attempt = receipt.get("attempt")
    if not isinstance(attempt, dict) or (
        attempt.get("id") != "20260913-11"
        or attempt.get("directory") != TARGET_DIRECTORY
        or attempt.get("target") != TARGET
        or attempt.get("artifacts") != {**ARTIFACTS, "progress": {**ARTIFACTS["progress"], "events": 22}}
    ):
        add_error(errors, "evidence_attempt")
    verification = receipt.get("verification")
    if verification != {
        "adapter_tests": 6,
        "source_static_tests": 23,
        "psscriptanalyzer_findings": 0,
        "fixture_classes": ["boundary", "happy_path", "negative", "preservation", "security"],
        "validations": ["formula_readback", "schema", "semantic_reopen"],
    }:
        add_error(errors, "evidence_verification")
    privacy = receipt.get("privacy")
    if not isinstance(privacy, dict) or any(value is not False for value in privacy.values()):
        add_error(errors, "evidence_privacy")
    historical = receipt.get("historical_attempts")
    if historical != {
        "failed_or_interrupted_ids": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"],
        "attempt10_decision": "failed_watchdog_phase_vocabulary_not_relabelled",
        "promoted_to_pass": 0,
    }:
        add_error(errors, "evidence_history")


def validate_migration(root: Path, errors: list[str]) -> None:
    try:
        text = bounded_file(root, MIGRATION, 256_000).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        add_error(errors, "migration_path")
        return
    for marker in (
        "Before this profile",
        "exact section, selected state, grid, document flow and domain plan",
        "Change only the selected visible-result text span",
        "may not be inferred",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(
    errors: list[str], source_locks: int, evidence_files: int, implementation_files: int
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-thousands-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "evidence_files": evidence_files,
        "implementation_files": implementation_files,
        "features": 2,
        "direct_stage": "integration_passed" if not unique else "not_proven",
        "actual_hancom_native_source": not unique,
        "direct_output_package_save_reopen": False,
        "direct_output_render": False,
        "automation_runtime": "not_run",
        "p06_09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_THOUSANDS_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"evidence_files={validation['evidence_files']} "
        f"implementation_files={validation['implementation_files']}"
    )
