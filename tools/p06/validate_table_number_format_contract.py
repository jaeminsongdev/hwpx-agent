#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.p06.validate_table_geometry_contract import (
    add_error,
    bounded_file,
    canonical_sha256,
    reject_duplicate_keys,
)


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-number-format-v1.json"
MIGRATION = "protocol/migrations/p06-table-number-format-v0-to-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_NUMBER_FORMAT_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_NUMBER_FORMAT_REPORT.md"
EXPECTED_SOURCE_PATHS = {
    "WORK_BREAKDOWN_STRUCTURE.csv",
    "docs/04_feature_catalog/07_table.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-formula-v1.json",
    "implementation/p00/source-archive/original/web/KS_X_6101_MachineReadable_Content_20260901.json",
    "implementation/p02/evidence/automation/automation-pdf.records.v1.json",
}
EXPECTED_FORMAT_CHOICES = [
    "general",
    "integer",
    "decimal_1",
    "decimal_2",
    "decimal_3",
    "decimal_4",
]
OFFICIAL_HELP_URL = (
    "https://help.hancom.com/hoffice/multi/ko_kr/hwp/table/calculation/calculation.htm"
)
EXPECTED_LIMITS = {
    "input_bytes": 33_554_432,
    "cells": 1_000_000,
    "selected_cells": 4096,
    "identifier_bytes": 256,
    "serialized_bytes": 134_217_728,
    "formula_decimal_places": 12,
}
EXPECTED_NOT_CLAIMED = {
    "visible_text_number_parsing_or_rewrite": False,
    "currency_date_or_custom_number_format": False,
    "formula_evaluation_or_cache_oracle": False,
    "full_target_result_format_mapping": False,
    "hwpx_number_format_lowering_or_readback": False,
    "hancom_2020_target_build": False,
    "semantic_reopen_or_formula_readback": False,
    "pagination_or_render": False,
    "automation_or_differential": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production_ready": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_number_format.rs": (
        'TABLE_NUMBER_FORMAT_SCHEMA_VERSION: &str = "hwpx-agent.table-number-format/v1"',
        'TABLE_NUMBER_FORMAT_CAPABILITY_ID: &str = "table.number_format"',
        "pub struct TableNumberFormatState",
        "pub struct TableNumberFormatRequest",
        "pub struct TableNumberFormatPlan",
        "pub struct TableNumberFormatBuilder",
        "expected_source_state_sha256",
        "expected_document_flow_sha256",
        "non_formula_payload_sha256",
        "properties_sha256",
        "pub fn from_json",
        "pub fn canonical_sha256",
        "pub const fn code",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_number_format;",
        "TableNumberFormatBuilder",
        "TableNumberFormatState",
        "TABLE_NUMBER_FORMAT_SCHEMA_VERSION",
    ),
    "crates/domain-ir/tests/table_number_format.rs": (
        "all_supported_formats_change_only_selected_formula_format",
        "request_rejects_state_grid_identity_and_flow_drift",
        "build_rechecks_late_state_grid_and_flow_drift",
        "state_rejects_incomplete_duplicate_misaligned_and_wrong_formula_owner",
        "selection_requires_unique_formula_master_cells",
        "merged_master_is_exact_but_covered_nonmaster_slot_is_rejected",
        "strict_json_rejects_unknown_duplicate_version_and_bad_digest",
        "input_and_output_bounds_are_enforced",
        "debug_redacts_identifiers_digests_formula_and_cache",
    ),
    POLICY: (
        "complete ordered master-cell snapshot",
        "Both request admission",
        "The preserving adapter owns only",
        "`TABLE-049` advances to `direct_hwpx / integration_passed`",
        "product\ncompletion remain open",
    ),
    REPORT: (
        "12/12 PASS",
        "24/24 PASS",
        "Direct stage: `integration_passed`",
        "The new HWPX adapter binds",
        "Attempt 05 passed",
        "green 0/61",
    ),
    "implementation/p06/tools/create-hancom-2020-table-number-format-source.ps1": (
        "hwpx-agent.p06-09-hancom-2020-table-number-format-source/v1",
        "$creation.Rows = $formatCases.Count",
        "$creation.Cols = 3",
        "TableFormulaSumHor",
        "ModifyCtrl",
        "TableCellBlock",
        "TableDeleteComma",
        "TableInsertComma",
        "grouping_remove_",
        "Invoke-ActionRun -Hwp $hwp -Action 'Cancel'",
        "manual_ui_source_authoring_required = $true",
        "computer_use_click_or_type_invoked = $false",
    ),
    "implementation/p06/tools/run-hancom-2020-table-number-format-source.ps1": (
        "hwpx-agent.p06-09-hancom-2020-table-number-format-source-watchdog/v1",
        "[ValidateRange(30, 900)][int]$TimeoutSeconds = 900",
        "Stop-OwnedHancomProcess",
        "manual_format_dialogs_passed -eq 6",
        "insert_grouping_actions_passed -eq 6",
        "TABLE_NUMBER_FORMAT_SOURCE_TIMEOUT",
    ),
    "implementation/p06/tests/Test-Hancom2020TableNumberFormatSource.ps1": (
        "hwpx-agent.p06-09-table-number-format-source-static-tests/v1",
        "exact_format_case_order",
        "no_guessed_native_format",
        "user_ui_not_computer_use",
        "preflight_fails_before_com",
    ),
}


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        text = bounded_file(root, CONTRACT, 512_000).read_text(encoding="utf-8")
        contract = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0)
    if not isinstance(contract, dict):
        return result(["contract_shape"], 0, 0)

    expected_keys = {
        "schema_version", "model_schema_version", "scope", "feature",
        "source_lock_canonicalization", "source_locks", "official_format_evidence",
        "official_ui_reference", "target_direct_profile", "source_qualification",
        "migration", "policy", "report", "implementation_files", "state", "semantics",
        "binding", "preservation", "default_limits", "failure_policy", "not_claimed",
        "gate_decision",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    exact = {
        "schema_version": "hwpx-agent.table-number-format-contract/v1",
        "model_schema_version": "hwpx-agent.table-number-format/v1",
        "scope": "p06_09_pure_exact_state_formula_cell_number_format_component_current_pc_local_development",
        "feature": {"feature_id": "TABLE-049", "capability_id": "table.number_format"},
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "migration": MIGRATION,
        "policy": POLICY,
        "report": REPORT,
        "implementation_files": sorted(IMPLEMENTATION_MARKERS),
        "default_limits": EXPECTED_LIMITS,
        "not_claimed": EXPECTED_NOT_CLAIMED,
        "gate_decision": {
            "component": "pass",
            "direct_stage": "unit_passed",
            "actual_hwpx": False,
            "actual_hangul": False,
            "p06_09": "in_progress",
            "product_complete": False,
        },
    }
    for key, expected in exact.items():
        actual = contract.get(key)
        if key == "implementation_files" and isinstance(actual, list):
            actual = sorted(actual)
        if actual != expected:
            add_error(errors, key)

    expected_objects = {
        "official_format_evidence": {"source", "section", "proved_standard_tokens", "exact_hancom_2020_full_mapping"},
        "official_ui_reference": {
            "url", "scope", "observed_format_choices", "grouping_control",
            "exact_installed_build_proof",
        },
        "target_direct_profile": {
            "product", "target_build", "architecture", "locale", "format_choices",
            "grouping_states", "combination_count", "percent", "scientific",
            "native_result_format_mapping",
        },
        "source_qualification": {
            "state", "worker", "watchdog", "static_test", "static_cases",
            "powershell_7_static", "windows_powershell_5_1_x86_static",
            "new_disposable_table", "formula_actions", "manual_format_dialogs",
            "grouping_remove_actions", "grouping_add_actions", "outputs",
            "native_format_strings_authored_by", "computer_use_click_or_type", "runtime",
            "attempts", "last_attempt", "qualifying_actual_hwpx", "qualifying_actual_hangul",
        },
        "state": {"table", "coverage", "cell", "formula", "merged_cell"},
        "semantics": {"selection", "formats", "mutation", "idempotence"},
        "binding": {"request", "build", "state_digest", "grid_digest", "document_flow"},
        "preservation": {"selected_formula", "unselected_formula", "cell", "table", "flow"},
    }
    for key, fields in expected_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != fields:
            add_error(errors, key)
    evidence = contract.get("official_format_evidence")
    if isinstance(evidence, dict):
        if evidence.get("section") != "10.7.3.5.2":
            add_error(errors, "official_section")
        if evidence.get("proved_standard_tokens") != ["%g", "%.0f", "%.1f", "%.2f", "%.3f", "%.4f"]:
            add_error(errors, "official_tokens")
        if evidence.get("exact_hancom_2020_full_mapping") != "not_proven":
            add_error(errors, "target_mapping_claim")
    reference = contract.get("official_ui_reference")
    if isinstance(reference, dict):
        if reference != {
            "url": OFFICIAL_HELP_URL,
            "scope": "calculation_dialog_result_format_choices_and_grouping_checkbox_only",
            "observed_format_choices": EXPECTED_FORMAT_CHOICES,
            "grouping_control": "independent_checkbox",
            "exact_installed_build_proof": False,
        }:
            add_error(errors, "official_ui_reference")
    target_profile = contract.get("target_direct_profile")
    if isinstance(target_profile, dict):
        expected_profile = {
            "product": "Hancom Hangul 2020",
            "target_build": "11.0.0.9136",
            "architecture": "x86",
            "locale": "ko-KR",
            "format_choices": EXPECTED_FORMAT_CHOICES,
            "grouping_states": ["off", "on"],
            "combination_count": 12,
            "percent": "rejected_without_separate_exact_target_ui_evidence",
            "scientific": "rejected_without_separate_exact_target_ui_evidence",
            "native_result_format_mapping": "not_proven",
        }
        if target_profile != expected_profile:
            add_error(errors, "target_direct_profile")
    qualification = contract.get("source_qualification")
    if isinstance(qualification, dict):
        expected_qualification = {
            "state": "attempted_incomplete",
            "worker": "implementation/p06/tools/create-hancom-2020-table-number-format-source.ps1",
            "watchdog": "implementation/p06/tools/run-hancom-2020-table-number-format-source.ps1",
            "static_test": "implementation/p06/tests/Test-Hancom2020TableNumberFormatSource.ps1",
            "static_cases": 24,
            "powershell_7_static": "pass",
            "windows_powershell_5_1_x86_static": "pass",
            "new_disposable_table": {"rows": 6, "columns": 3},
            "formula_actions": 6,
            "manual_format_dialogs": 6,
            "grouping_remove_actions": 6,
            "grouping_add_actions": 6,
            "outputs": ["baseline", "ungrouped", "grouped"],
            "native_format_strings_authored_by": "user_in_hancom_visible_dialog",
            "computer_use_click_or_type": False,
            "runtime": "attempt_01_interrupted_at_manual_format_general",
            "attempts": 1,
            "last_attempt": {
                "progress_events": 10,
                "last_phase": "manual_format_general",
                "last_state": "running",
                "baseline_artifact_created": True,
                "ungrouped_artifact_created": False,
                "grouped_artifact_created": False,
                "final_watchdog_receipt_created": False,
                "exact_owned_hwp_process_cleaned": True,
                "remaining_hwp_processes": 0,
                "failure_evidence_preserved": True,
            },
            "qualifying_actual_hwpx": False,
            "qualifying_actual_hangul": False,
        }
        if qualification != expected_qualification:
            add_error(errors, "source_qualification")
    semantics = contract.get("semantics")
    if isinstance(semantics, dict):
        if semantics.get("formats") != ["general", "number", "percent", "scientific"]:
            add_error(errors, "format_set")
        if semantics.get("mutation") != "selected_formula_number_format_only":
            add_error(errors, "mutation")
    binding = contract.get("binding")
    if isinstance(binding, dict):
        if "rechecked" not in str(binding.get("build")):
            add_error(errors, "build_recheck")
    preservation = contract.get("preservation")
    if isinstance(preservation, dict):
        if preservation.get("selected_formula") != "owner_ast_and_cache_exact":
            add_error(errors, "formula_preservation")

    failure_policy = contract.get("failure_policy")
    if (
        not isinstance(failure_policy, list)
        or len(failure_policy) != 14
        or len(set(failure_policy)) != 14
        or any(not isinstance(item, str) or not item for item in failure_policy)
    ):
        add_error(errors, "failure_policy")

    source_count = validate_source_locks(root, contract.get("source_locks"), errors)
    implementation_count = validate_implementation(root, errors)
    validate_migration(root, errors)
    return result(errors, source_count, implementation_count)


def validate_source_locks(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        add_error(errors, "source_lock_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            add_error(errors, "source_lock_shape")
            continue
        path = item.get("path")
        digest = item.get("sha256")
        if (
            not isinstance(path, str)
            or path in declared
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            add_error(errors, "source_lock_identity")
            continue
        declared[path] = digest
        try:
            actual = canonical_sha256(bounded_file(root, path, 32_000_000))
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "source_lock_path")
            continue
        if actual != digest:
            add_error(errors, "source_lock_digest")
    if set(declared) != EXPECTED_SOURCE_PATHS:
        add_error(errors, "source_lock_paths_exact")
    return len(declared)


def validate_implementation(root: Path, errors: list[str]) -> int:
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_file(root, relative, 2_000_000).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "implementation_path")
            continue
        if any(marker not in text for marker in markers):
            add_error(errors, "implementation_marker")
    return len(IMPLEMENTATION_MARKERS)


def validate_migration(root: Path, errors: list[str]) -> None:
    try:
        text = bounded_file(root, MIGRATION, 256_000).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, ValueError):
        add_error(errors, "migration_path")
        return
    for marker in (
        "hwpx-agent.table-number-format/v1",
        "complete logical master-cell snapshot",
        "returns no partial plan",
        "separately versioned direct adapter",
    ):
        if marker not in text:
            add_error(errors, "migration_marker")


def result(errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-number-format-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "features": 1,
        "direct_stage": "unit_passed" if not unique else "not_proven",
        "actual_hwpx": False,
        "actual_hangul": False,
        "p06_09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_NUMBER_FORMAT_CONTRACT_PASS "
        f"features={validation['features']} source_locks={validation['source_locks']} "
        f"implementation_files={validation['implementation_files']}"
    )
