#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any


def load_base_validator() -> Any:
    path = Path(__file__).resolve().with_name("validate_table_layout_contract.py")
    specification = importlib.util.spec_from_file_location("p06_table_layout_validator", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("table layout validator load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


base = load_base_validator()
ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-font-metric-receipt-v1.json")
MIGRATION = "protocol/migrations/p06-font-metric-receipt-v0-to-v1.md"
EXPECTED_SOURCE_PATHS = {
    "docs/03_document_model/06_table_model.md",
    "docs/12_implementation_guides/05_page_table_layout_algorithms.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "protocol/private/p06-table-layout-v1.json",
    "protocol/private/p06-table-layout-hwpx-v1.json",
    "implementation/p00/target-profile.yaml",
    "implementation/p00/font-printer-manifest.yaml",
}
EXPECTED_CAPABILITIES = [
    "table.width_height",
    "table.column_fixed_width",
    "table.autofit_content",
    "table.autofit_page",
]
EXPECTED_LIMITS = {
    "input_bytes": 262_144,
    "cells": 4,
    "dimension_micrometers": 1_000_000_000,
}
EXPECTED_ACTUAL = {
    "windows_powershell_5_1_run_id": "4b9b0cac589946918140abc4a12c1be1",
    "windows_powershell_5_1_receipt_sha256": (
        "c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab"
    ),
    "powershell_7_run_id": "cb76a3477e2c4bcdac78b6647e187acf",
    "powershell_7_receipt_sha256": (
        "329d424445c463bae9c84215cc627a1e9b1b1e3287de6f8d1eb01439ccdde6f3"
    ),
    "measurement_set_sha256": "96e3ad33591b098d3ca15c88242303aa7b11dc1730cf2a499273afe3ad7790a9",
    "cell_count": 4,
    "static_checks_each": "16_of_16_passed",
    "python_verifier_each": "passed",
    "rust_actual_receipt_consumer_each": "passed",
    "artifact_git_tracked": False,
    "actual_hangul_renderer": False,
}
EXPECTED_NOT_CLAIMED = {
    "actual_hangul_text_layout_equivalence": False,
    "actual_hangul_2020_renderer_oracle": False,
    "pdf_render_equivalence": False,
    "font_copy_embedding_or_redistribution": False,
    "arbitrary_text_font_or_point_size": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_04_complete": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "implementation/p06/tools/measure-hancom-2020-layout-font.ps1": (
        "PrivateFontCollection",
        "acceptedFamilyNames",
        "GenericTypographic",
        "MeasureString",
        "'[^\\x00-\\x7F]'",
        "FileMode]::CreateNew",
        "repeat_count = 2",
        "actual_hangul_renderer = $false",
    ),
    "implementation/p06/tools/verify-current-font-metric-receipt.py": (
        "duplicate_guard",
        "EXPECTED_HWP_SHA256",
        "EXPECTED_FONT_SHA256",
        "EXPECTED_MEASUREMENT_SET_SHA256",
        "measurement.digest",
        '"actual_hangul_renderer", "other_pc_or_version", "product_complete"',
    ),
    "implementation/p06/tests/Test-Hancom2020LayoutFontMetric.ps1": (
        "cross_run_deterministic",
        "no_raw_text",
        "no_completion_promotion",
    ),
    "crates/hwpx-package/src/font_metric_receipt.rs": (
        "CURRENT_FONT_METRIC_PROFILE_ID",
        "EXPECTED_MEASUREMENT_SET_SHA256",
        "pub struct CurrentFontMetricReceipt",
        "FontMetricStatus::Verified",
        "source_sha256: Some(self.receipt_sha256.clone())",
        "MeasurementDigestMismatch",
    ),
    "crates/hwpx-package/tests/font_metric_receipt.rs": (
        "exact_current_receipt_is_redacted_and_yields_verified_metrics",
        "verified_receipt_composes_with_the_table_layout_solver",
        "target_claim_digest_and_cell_drift_fail_closed",
        "malformed_ambiguous_or_oversized_json_is_rejected",
    ),
    "crates/hwpx-package/examples/p06_05_verify_current_font_metric_receipt.rs": (
        "font_metric_run_id_invalid",
        "CurrentFontMetricReceipt::parse",
        '"actual_hangul_renderer\\":false',
    ),
    "implementation/p06/P06-05_FONT_METRIC_POLICY.md": (
        "PrivateFontCollection",
        "separately qualified fixed",
        "No user document is opened",
        "Not claimed yet",
    ),
    "crates/hwpx-package/Cargo.toml": (
        "serde.workspace = true",
        "serde_json.workspace = true",
    ),
}


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=base.reject_duplicate_keys
    )
    if not isinstance(value, dict):
        raise ValueError("contract root")
    return value


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_contract(base.bounded_file(root, CONTRACT_RELATIVE.as_posix(), 256_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, implementation_files=0)

    expected_scalars = {
        "schema_version": "hwpx-agent.font-metric-receipt-contract/v1",
        "model_schema_version": "hwpx-agent.p06-05-current-font-metric-receipt/v1",
        "scope": "p06_05_current_pc_hancom_2020_named_synthetic_font_metric_component",
        "prerequisites": [
            "hwpx-agent.table-layout/v1",
            "current_pc_exact_hancom_2020_target_profile",
            "installed_HANBatang_ttf_identity",
        ],
        "source_lock_canonicalization": "utf8_lf_sha256",
        "component_capabilities": EXPECTED_CAPABILITIES,
        "default_limits": EXPECTED_LIMITS,
        "actual_evidence": EXPECTED_ACTUAL,
        "migration": MIGRATION,
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)

    required_objects = {
        "exact_target": {
            "profile_id", "hangul_build", "architecture", "executable_sha256",
            "font_file_name", "font_file_bytes", "font_file_sha256", "font_family",
        },
        "measurement_profile": {
            "profile_id", "provider", "dpi", "font_size_millipoints", "repeat_count",
            "conversion", "font_source", "family_name_admission",
        },
        "named_fixture": {
            "scope", "ordered_cell_ids", "measurement_set_sha256", "cell_count",
            "raw_text_in_receipt",
        },
        "admission": {"json", "identity", "cells", "digest", "claims"},
        "solver_binding": {"status", "profile", "source", "text", "margins"},
        "privacy_and_side_effects": {
            "user_document", "font_copy_or_redistribution", "hangul_process", "ui_input",
            "network", "registry_or_system_setting", "publication",
        },
    }
    for key, expected_keys in required_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_keys:
            errors.append(key)
    fixture = contract.get("named_fixture")
    if not isinstance(fixture, dict) or fixture.get("ordered_cell_ids") != [
        "cell-a", "cell-b", "cell-c", "cell-d"
    ]:
        errors.append("named_fixture_identity")
    for key, minimum in (("validation_order", 7), ("failure_policy", 8)):
        value = contract.get(key)
        if (
            not isinstance(value, list)
            or len(value) < minimum
            or any(not isinstance(item, str) or not item for item in value)
        ):
            errors.append(key)

    source_locks = contract.get("source_locks")
    source_count = len(source_locks) if isinstance(source_locks, list) else 0
    declared: set[str] = set()
    if not isinstance(source_locks, list):
        errors.append("source_locks_shape")
    else:
        for entry in source_locks:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                errors.append("source_lock_shape")
                continue
            relative = entry.get("path")
            digest = entry.get("sha256")
            if not isinstance(relative, str) or not isinstance(digest, str) or relative in declared:
                errors.append("source_lock_types_or_duplicate")
                continue
            declared.add(relative)
            try:
                actual = base.sha256_utf8_lf(base.bounded_file(root, relative))
            except (OSError, UnicodeDecodeError, ValueError):
                errors.append("source_lock_path_or_encoding")
                continue
            if actual != digest:
                errors.append("source_lock_digest")
        if declared != EXPECTED_SOURCE_PATHS:
            errors.append("source_lock_paths_exact")

    try:
        migration = base.bounded_file(root, MIGRATION, 256_000).read_text(encoding="utf-8")
        for marker in (
            "hwpx-agent.p06-05-current-font-metric-receipt/v1",
            "Merely",
            "FontMetricStatus::Verified",
            "new contract version",
        ):
            if marker not in migration:
                errors.append("migration_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        errors.append("migration_path")

    implementation_files = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = base.bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
            continue
        implementation_files += 1
        if any(marker not in source for marker in markers):
            errors.append("implementation_marker")

    return result(
        errors=sorted(set(errors)),
        source_locks=source_count,
        implementation_files=implementation_files,
    )


def result(*, errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-font-metric-contract-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": errors,
        "source_locks": source_locks,
        "implementation_files": implementation_files,
    }


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_FONT_METRIC_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"implementation_files={report['implementation_files']}"
    )
