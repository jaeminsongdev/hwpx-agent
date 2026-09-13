#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
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
CONTRACT = "protocol/private/p06-table-number-format-hwpx-v1.json"
PREDECESSOR = "protocol/private/p06-table-number-format-v1.json"
MIGRATION = "protocol/migrations/p06-table-number-format-v1-to-hwpx-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_NUMBER_FORMAT_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_NUMBER_FORMAT_HWPX_REPORT.md"
RECEIPT = (
    "implementation/p06/evidence/target/"
    "p06-table-number-format.current-2020.attempt05.v1.json"
)
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-number-format-source-20260913-05"

FEATURE = {"feature_id": "TABLE-049", "capability_id": "table.number_format"}
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
        "sha256": "9f862bb2772c95271d3e97089c3ca29b88aa138e7fae524e8461bcf77ddac042",
        "bytes": 16437,
    },
    "ungrouped": {
        "path": f"{TARGET_DIRECTORY}/ungrouped.hwpx",
        "sha256": "fa859aaff54cdc7faa8c5d55639040f0e6cc450691d61889356a59db4abbced9",
        "bytes": 16581,
    },
    "grouped": {
        "path": f"{TARGET_DIRECTORY}/grouped.hwpx",
        "sha256": "c5f0a1881f0c7d4b4fc0105bd76f3929a3f0b4d64da756dd124a4cd66d122027",
        "bytes": 16753,
    },
    "watchdog": {
        "path": f"{TARGET_DIRECTORY}/watchdog.json",
        "sha256": "0eb1512c809198b90a38bae938746cecde8a212e279abd1ee6303691f8b397f5",
        "bytes": 2384,
    },
    "inner_trace": {
        "path": f"{TARGET_DIRECTORY}/watchdog.json.inner.29128.json",
        "sha256": "601336498a9303b21d42def380a5a93596820fec72938eb2301bf9014101835f",
        "bytes": 1813,
    },
    "progress": {
        "path": f"{TARGET_DIRECTORY}/watchdog.json.progress.jsonl",
        "sha256": "02f9a6be1870015a8e8d140487498abf052b5eb3d55f9e4e84af2d39cdf53a17",
        "bytes": 15743,
    },
}
SOURCE_LOCKS = {
    PREDECESSOR: "92a14a276dada1ba9c7e9013d529e6e1af445ed5da017ae2c996af67f3f8c46a",
    "crates/domain-ir/src/table_number_format.rs": (
        "1da392052e8e5dc9866746a43faa29a61a8b947af15ac69c2161d3a430e79921"
    ),
    "crates/hwpx-package/src/table_formula/number_format_hwpx.rs": (
        "e46c93c8cfcadd968fff5d4e078c422ff8a8f20a14322590e8ec136c11ae315a"
    ),
    "crates/hwpx-package/src/table_formula.rs": (
        "bc500aa8da4bea9e31f633e820164f41be7635a324f7378f6ce352e024a5d803"
    ),
    "crates/hwpx-package/src/lib.rs": (
        "1745b58853e0dbee8c7361fb691e3e59c70b2f7883e42ade0316242533ee9f22"
    ),
    "crates/hwpx-package/tests/table_number_format_hwpx.rs": (
        "3706b38080a4df8775b0252295d147d4af947092217224c0bb80f6d261994084"
    ),
    "crates/hwpx-package/examples/p06_09_table_number_format_source_oracle.rs": (
        "e42a24aa8bb4cdaf03e8115da1785bc18f7b3933f063ec466e3555d9c324977c"
    ),
    "implementation/p06/tools/run-hancom-2020-table-number-format-source.ps1": (
        "406338a4ee518b8aeca91a8191fba5d8ef617fb2249c85ecfb80ce7d5abee1ba"
    ),
    "implementation/p06/tools/create-hancom-2020-table-number-format-source.ps1": (
        "1a2cfae33cf83288952d4d5ad81533f9a08d667a4a7a9c22c1f2548b95df04fa"
    ),
    "implementation/p06/tests/Test-Hancom2020TableNumberFormatSource.ps1": (
        "30aace65779b18628b3dc869f5aa5dfbdca986e6caebb3ad806be317ed2b8b7d"
    ),
}
NATIVE_READBACK = {
    "profile_id": "hwpx-agent.table-number-format-hwpx.hancom-2020/1",
    "entry_count": 11,
    "formula_fields": 6,
    "dimensions": [6, 3],
    "result_formats": ["%g,", "%.0f,", "%.1f,", "%.2f,", "%.3f,", "%.4f,"],
    "baseline_section_sha256": (
        "9d63efc4bde39bd018199a626cdfdd59f9679959464bf5bd026c951492882675"
    ),
    "ungrouped_section_sha256": (
        "a06bdfd184a1b79c3a9f55ef7c6f72e706d52ba0d379586e14b483dc497e435e"
    ),
    "grouped_section_sha256": (
        "da87209c4f0e0c5af19ccbed42e3f63da2ee9f73c7915361a1748c616dc5317b"
    ),
    "baseline_state_sha256": (
        "90370c286e2162b247b5fa0dc9f931c8f8fca0dde5413c781570441dd9381c06"
    ),
    "ungrouped_state_sha256": (
        "f60dfccc58d1561afb8a7f562b42446a9a4d64412470eaa6d8c53dd8d7a03fdf"
    ),
    "grouped_state_sha256": (
        "0bbfd7f98cb3332fecf4b50cb6da0f76467bfcab331a5ad16e3c7594cce95328"
    ),
    "grid_sha256": "a304515706a9ae0e7bcec9584488dc7ca4854f808ada02494be5d0e865070ba4",
    "semantic_document_flow_sha256": (
        "8fe776ef1af4600c8cbad0d53f5315c2c440c044e51f39b6acd1cbe72262ad3c"
    ),
    "baseline_raw_flow_sha256": (
        "65156375b5fa6d997831d33c9ae7f1076e4fb9526affa9fe3239a921233be219"
    ),
    "ungrouped_raw_flow_sha256": (
        "ce467bd2a29b5a72d2253a669977a6d6ca3a29c170504f35b2eae7952b47d395"
    ),
    "grouped_raw_flow_sha256": (
        "59930650ad42f21b7d1baa68b9485299e440c55a8499091b230acbf39c0fbb6b"
    ),
    "formula_ast_preserved": True,
    "numeric_cache_preserved": True,
    "grid_preserved": True,
    "outside_owned_bytes_preserved": True,
}
DIRECT_DIFFERENTIAL = {
    "grouped_section_exact_match": True,
    "ungrouped_section_exact_match": True,
    "grouped_number_format_modified_text_count": 18,
    "ungrouped_number_format_modified_text_count": 19,
    "auxiliary_general_grouping_modified_text_count": 1,
    "unowned_bytes_preserved": True,
    "document_flow_preserved": True,
}
EXPECTED_EVIDENCE = {
    "domain_tests": 12,
    "adapter_tests": 6,
    "source_static_tests": 24,
    "contract_tests": 4,
    "feature_count": 1,
    "backend": "direct_hwpx",
    "direct_stage": "integration_passed",
    "fixture_classes": ["boundary", "happy_path", "negative", "preservation", "security"],
    "validations": ["formula_readback", "schema", "semantic_reopen"],
}
RECEIPT_VERIFICATION = {
    key: EXPECTED_EVIDENCE[key]
    for key in (
        "domain_tests",
        "adapter_tests",
        "source_static_tests",
        "contract_tests",
        "fixture_classes",
        "validations",
    )
}
SEMANTIC_FIELDS = {
    "native_profile": {
        "table": "one_complete_unmerged_6_by_3_grid_with_six_exact_formula_owners",
        "formula": "selected_native_formulas_equal_SUM_LEFT_with_unambiguous_grouped_integer_cache",
        "result_formats": ["%g,", "%.0f,", "%.1f,", "%.2f,", "%.3f,", "%.4f,"],
        "grouping": "visible_text_is_exact_grouped_or_plain_equivalent_and_general_preserves_observed_mode",
        "ownership": "only_selected_command_result_format_last_result_and_visible_result_text_spans",
    },
    "transition": {
        "general": "native_percent_g_comma_with_observed_grouping_preserved",
        "fixed_number": "native_percent_dot_zero_to_four_f_comma_with_typed_grouping",
        "idempotence": "already_requested_native_state_returns_zero_edits",
        "native_differential": "grouped_and_ungrouped_direct_sections_equal_corresponding_hancom_sections",
    },
    "binding": {
        "request": "exact_section_selected_state_grid_semantic_document_flow_and_domain_plan_sha256",
        "build": "recheck_all_request_bindings_and_native_profile_before_edit",
        "readback": "reopen_selected_formula_format_grouping_grid_and_unowned_bytes_before_return",
        "serialization": "bounded_deterministic_strict_json_with_duplicate_and_unknown_key_rejection",
    },
    "preservation": {
        "formula": "owner_ast_numeric_cache_formula_source_and_field_identity_exact",
        "grid": "dimensions_coordinates_spans_and_nonmerged_coverage_exact",
        "section": "all_bytes_outside_four_selected_text_spans_per_formula_exact",
        "flow": "semantic_spine_manifest_digest_exact_with_raw_source_flow_hashes_retained",
    },
    "receipt": {
        "path": RECEIPT,
        "hashes": "source_output_section_state_grid_flow_plan_unowned_and_raw_source_flow_sha256",
        "counts": "selected_formula_cells_modified_text_spans_and_source_progress",
        "debug": "all_hashes_formula_metadata_document_content_and_raw_xml_redacted",
    },
}
FAILURE_POLICY = [
    "invalid_duplicate_unknown_empty_or_oversized_json_rejected",
    "invalid_or_stale_section_state_grid_flow_or_plan_digest_rejected",
    "merged_incomplete_or_ambiguous_grid_rejected",
    "missing_extra_duplicate_or_unselected_formula_owner_rejected",
    "unsupported_formula_result_format_command_last_result_or_visible_grouping_rejected",
    "percent_scientific_non_integer_or_more_than_four_decimal_target_rejected",
    "plan_changes_to_ast_cache_owner_or_selection_rejected",
    "overlapping_or_oversized_text_edits_rejected",
    "semantic_readback_or_unowned_byte_drift_rejected",
    "no_partial_section_or_receipt_returned",
]
GATE_DECISION = {
    "TABLE-049": "integration_passed",
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
    "percent_or_scientific_native_mapping": False,
    "non_integer_native_mapping": False,
    "other_pc_or_hancom_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_formula/number_format_hwpx.rs": (
        'TABLE_NUMBER_FORMAT_HWPX_SCHEMA_VERSION: &str =',
        '"hwpx-agent.table-number-format-hwpx/v1"',
        '"hwpx-agent.table-number-format-hwpx.hancom-2020/1"',
        "pub struct TableNumberFormatHwpxReadback",
        "pub struct TableNumberFormatHwpxRequestDraft",
        "pub struct TableNumberFormatHwpxLoweringReceipt",
        "pub fn lower_in_section_with_receipt(",
        "fn parse_native_format(",
        "fn validate_plan_against_source(",
        "fn native_edits(",
    ),
    "crates/hwpx-package/src/table_formula.rs": (
        "mod number_format_hwpx;",
        "pub use number_format_hwpx::{",
    ),
    "crates/hwpx-package/src/lib.rs": (
        "TABLE_NUMBER_FORMAT_HWPX_PROFILE_ID",
        "TableNumberFormatHwpxLowerer",
        "TableNumberFormatHwpxReader",
    ),
    "crates/hwpx-package/tests/table_number_format_hwpx.rs": (
        "integer_format_changes_exact_native_fields_and_preserves_everything_else",
        "general_preserves_native_grouping_and_same_format_is_idempotent",
        "all_exact_number_tokens_and_negative_integer_are_supported",
        "request_and_build_reject_section_state_grid_flow_and_plan_drift",
        "unsupported_native_and_target_profiles_fail_closed",
        "strict_json_and_debug_redaction_fail_closed",
        "<redacted>",
    ),
    "crates/hwpx-package/examples/p06_09_table_number_format_source_oracle.rs": (
        "hwpx-agent.p06-09-table-number-format-source-oracle/v1",
        "grouped_section_exact_match",
        "ungrouped_section_exact_match",
        "source_flow_digest",
        "direct_output_package_save_reopen",
    ),
    "implementation/p06/tools/run-hancom-2020-table-number-format-source.ps1": (
        "grouping_remove_general",
        "progress_valid",
        "remaining_hwp_process_count",
    ),
    "implementation/p06/tools/create-hancom-2020-table-number-format-source.ps1": (
        "TableDeleteComma",
        "TableInsertComma",
        "TableCellBlock",
        "Assert-ActionEnabled",
    ),
    "implementation/p06/tests/Test-Hancom2020TableNumberFormatSource.ps1": (
        "grouping_remove_general",
        "TableDeleteComma",
        "TableInsertComma",
        "DeleteThousandsSeparator|InsertThousandsSeparator",
    ),
    POLICY: (
        "direct_hwpx / integration_passed",
        "Attempt `20260913-05`",
        "grouped and\nungrouped results match",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "6/6 PASS",
        "24/24 PASS",
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
        "schema_version", "profile_id", "predecessor", "scope", "feature",
        "source_lock_canonicalization", "source_locks", "exact_target",
        "successful_attempt", "native_profile", "transition", "binding",
        "preservation", "receipt", "expected_evidence", "failure_policy",
        "migration", "policy", "report", "gate_decision", "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    expected = {
        "schema_version": "hwpx-agent.table-number-format-hwpx-contract/v1",
        "profile_id": "hwpx-agent.table-number-format-hwpx.hancom-2020/1",
        "predecessor": {
            "path": PREDECESSOR,
            "sha256": SOURCE_LOCKS[PREDECESSOR],
            "state": "immutable_pure_planner_contract",
        },
        "scope": (
            "p06_09_exact_current_pc_hancom_2020_native_source_and_preserving_section_integration"
        ),
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "feature": FEATURE,
        "exact_target": TARGET,
        "successful_attempt": {
            "id": "20260913-05",
            "directory": TARGET_DIRECTORY,
            "state": "pass",
            "progress_events": 50,
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
    for key, value in SEMANTIC_FIELDS.items():
        if contract.get(key) != value:
            add_error(errors, key)
    failure = contract.get("failure_policy")
    if failure != FAILURE_POLICY:
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
        progress = [
            load_json_bytes(line)
            for line in exact_bytes(root, ARTIFACTS["progress"]["path"]).splitlines()
        ]
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "runtime_json")
        return
    expected = {
        "state": "pass", "table_create": "pass", "operand_cells_written": 12,
        "formula_actions_passed": 6, "manual_format_dialogs_passed": 6,
        "delete_grouping_actions_passed": 6, "insert_grouping_actions_passed": 6,
        "format_case_count": 6,
    }
    for key, value in expected.items():
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
    if not isinstance(summary, dict) or any((
        summary.get("timed_out") is not False,
        summary.get("child_exit_code") != 0,
        summary.get("progress_valid") is not True,
        summary.get("progress_event_count") != 50,
        summary.get("progress_last_phase") != "terminal",
        summary.get("progress_last_state") != "pass",
        summary.get("remaining_hwp_process_count") != 0,
        summary.get("inner_trace_preserved") is not True,
    )):
        add_error(errors, "watchdog_summary")
    allowed = {
        "preflight", "com_create", "table_create", "formula_author", "baseline_save",
        "manual_format_general", "manual_format_integer", "manual_format_decimal_1",
        "manual_format_decimal_2", "manual_format_decimal_3", "manual_format_decimal_4",
        "grouping_remove_general", "grouping_remove_integer", "grouping_remove_decimal_1",
        "grouping_remove_decimal_2", "grouping_remove_decimal_3", "grouping_remove_decimal_4",
        "ungrouped_save", "grouping_add_general", "grouping_add_integer",
        "grouping_add_decimal_1", "grouping_add_decimal_2", "grouping_add_decimal_3",
        "grouping_add_decimal_4", "grouped_save", "terminal",
    }
    if len(progress) != 50:
        add_error(errors, "progress_count")
    for index, event in enumerate(progress, 1):
        if (
            not isinstance(event, dict)
            or event.get("sequence") != index
            or event.get("phase") not in allowed
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
            return set(names), archive.read("Contents/section0.xml"), archive.read("Contents/content.hpf")
    except (OSError, KeyError, ValueError, zipfile.BadZipFile):
        add_error(errors, "native_package")
        return None


def semantic_flow_digest(data: bytes) -> str:
    text = data.decode("utf-8")
    pattern = r'(<opf:meta name="ModifiedDate" content="text">)[^<]*(</opf:meta>)'
    text, count = re.subn(pattern, r"\1<save-time>\2", text)
    if count != 1:
        raise ValueError("ModifiedDate")
    text = text.replace(
        '<opf:itemref idref="header"/>',
        '<opf:itemref idref="header" linear="yes"/>',
    )
    return digest(text.encode("utf-8"))


def formula_fields(section: bytes) -> list[tuple[str, str, str]]:
    text = section.decode("utf-8")
    blocks = re.findall(r'<hp:fieldBegin[^>]*type="FORMULA"[\s\S]*?</hp:fieldBegin></hp:ctrl><hp:t>([^<]*)</hp:t>', text)
    full = re.findall(r'<hp:fieldBegin[^>]*type="FORMULA"[\s\S]*?</hp:fieldBegin>', text)
    if len(blocks) != 6 or len(full) != 6:
        raise ValueError("formula count")
    result: list[tuple[str, str, str]] = []
    for block, visible in zip(full, blocks, strict=True):
        result_format = re.search(r'name="ResultFormat">([^<]*)<', block)
        last_result = re.search(r'name="LastResult">([^<]*)<', block)
        if result_format is None or last_result is None:
            raise ValueError("formula parameter")
        result.append((result_format.group(1), last_result.group(1), visible))
    return result


def redacted_section(section: bytes) -> bytes:
    text = section.decode("utf-8")
    patterns = (
        r'(<hp:stringParam name="Command">)[^<]*(</hp:stringParam>)',
        r'(<hp:stringParam name="ResultFormat">)[^<]*(</hp:stringParam>)',
        r'(<hp:stringParam name="LastResult">)[^<]*(</hp:stringParam>)',
        r'(</hp:fieldBegin></hp:ctrl><hp:t>)[^<]*(</hp:t><hp:ctrl><hp:fieldEnd)',
    )
    for pattern in patterns:
        text = re.sub(pattern, r"\1__OWNED__\2", text)
    return text.encode("utf-8")


def validate_native_packages(root: Path, errors: list[str]) -> None:
    packages = [read_package(root, ARTIFACTS[name], errors) for name in ("baseline", "ungrouped", "grouped")]
    if any(value is None for value in packages):
        return
    baseline, ungrouped, grouped = packages  # type: ignore[misc]
    if baseline[0] != ungrouped[0] or baseline[0] != grouped[0]:
        add_error(errors, "native_entry_set")
    sections = [baseline[1], ungrouped[1], grouped[1]]
    expected_section_hashes = [
        NATIVE_READBACK["baseline_section_sha256"],
        NATIVE_READBACK["ungrouped_section_sha256"],
        NATIVE_READBACK["grouped_section_sha256"],
    ]
    if [digest(value) for value in sections] != expected_section_hashes:
        add_error(errors, "native_section_digest")
    if len({redacted_section(value) for value in sections}) != 1:
        add_error(errors, "native_unowned_section")
    try:
        fields = [formula_fields(value) for value in sections]
        flow_hashes = [digest(baseline[2]), digest(ungrouped[2]), digest(grouped[2])]
        semantic_hashes = [semantic_flow_digest(value[2]) for value in (baseline, ungrouped, grouped)]
    except (UnicodeDecodeError, ValueError):
        add_error(errors, "native_semantics")
        return
    tokens = NATIVE_READBACK["result_formats"]
    if [value[0] for value in fields[0]] != ["%g,"] * 6:
        add_error(errors, "native_baseline_format")
    if [value[0] for value in fields[1]] != tokens or [value[0] for value in fields[2]] != tokens:
        add_error(errors, "native_target_format")
    if any(last != visible for _, last, visible in fields[0] + fields[2]):
        add_error(errors, "native_grouped_visible")
    if any("," in visible for _, _, visible in fields[1]):
        add_error(errors, "native_ungrouped_visible")
    if flow_hashes != [
        NATIVE_READBACK["baseline_raw_flow_sha256"],
        NATIVE_READBACK["ungrouped_raw_flow_sha256"],
        NATIVE_READBACK["grouped_raw_flow_sha256"],
    ] or semantic_hashes != [NATIVE_READBACK["semantic_document_flow_sha256"]] * 3:
        add_error(errors, "native_flow")


def validate_receipt(root: Path, errors: list[str]) -> None:
    try:
        receipt = load_json_bytes(exact_bytes(root, RECEIPT, 512_000))
        if not isinstance(receipt, dict):
            raise ValueError("receipt root")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "evidence_receipt")
        return
    expected_keys = {
        "schema_version", "evidence_id", "scope", "feature", "attempt",
        "native_readback", "direct_differential", "verification", "historical_attempts",
        "privacy", "gate_decision", "not_claimed",
    }
    if set(receipt) != expected_keys:
        add_error(errors, "evidence_receipt_shape")
    if (
        receipt.get("schema_version") != "hwpx-agent.p06-09-table-number-format-current-2020-evidence/v1"
        or receipt.get("feature") != FEATURE
        or receipt.get("native_readback") != NATIVE_READBACK
        or receipt.get("direct_differential") != DIRECT_DIFFERENTIAL
        or receipt.get("verification") != RECEIPT_VERIFICATION
        or receipt.get("gate_decision") != GATE_DECISION
        or receipt.get("not_claimed") != NOT_CLAIMED
    ):
        add_error(errors, "evidence_receipt")
    attempt = receipt.get("attempt")
    if not isinstance(attempt, dict) or (
        attempt.get("id") != "20260913-05"
        or attempt.get("directory") != TARGET_DIRECTORY
        or attempt.get("target") != TARGET
        or attempt.get("artifacts") != {**ARTIFACTS, "progress": {**ARTIFACTS["progress"], "events": 50}}
    ):
        add_error(errors, "evidence_attempt")
    privacy = receipt.get("privacy")
    if not isinstance(privacy, dict) or any(value is not False for value in privacy.values()):
        add_error(errors, "evidence_privacy")
    if receipt.get("historical_attempts") != {
        "failed_or_interrupted_ids": ["01", "02", "03", "04"],
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
        "exact section, selected native formula state, complete unmerged grid",
        "Change only the selected fields' `Command`, `ResultFormat`, `LastResult`",
        "may not be inferred",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, evidence_files: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-number-format-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "evidence_files": evidence_files,
        "implementation_files": implementation_files,
        "features": 1,
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
        "P06_TABLE_NUMBER_FORMAT_HWPX_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"evidence_files={validation['evidence_files']} "
        f"implementation_files={validation['implementation_files']}"
    )
