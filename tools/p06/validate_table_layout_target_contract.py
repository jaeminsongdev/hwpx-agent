#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any


def load_base_validator() -> Any:
    path = Path(__file__).resolve().with_name("validate_table_layout_contract.py")
    specification = importlib.util.spec_from_file_location("p06_table_layout_target_base", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("table layout target base validator load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


base = load_base_validator()
ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-layout-target-v1.json")
MIGRATION_RELATIVE = PurePosixPath("protocol/migrations/p06-table-layout-target-v0-to-v1.md")
SOURCE_PATH = "fixtures/target-build/p06-04-cell-style-source-20260907-04/source.hwpx"
SOURCE_SHA256 = "814c481da946e760b2bc3b90b996863786652001e49f8b2b422e13c3d3e477a4"
RECEIPT_PATH = (
    "artifacts/p06/font-metric-runs/4b9b0cac589946918140abc4a12c1be1/receipt.json"
)
RECEIPT_SHA256 = "c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab"
TARGET_DIRECTORY = "fixtures/target-build/p06-05-table-layout-20260907-03"
TARGET_FILES = ["target.hwpx", "target-repeat.hwpx", "target-current.hwpx"]
TARGET_SHA256 = "b2887c929cdeb81fa1f5f3bac086265e19fb92a8bbf063f75e5ab0fbfa5cb299"
TRACE_PATH = (
    "fixtures/target-build/p06-05-table-layout-20260907-02/"
    "target-text-discovery-trace-01.json"
)
TRACE_SHA256 = "42a15b0f44fd34c2a46466ff81b6108f661f04f09fcc395aa5e8212583bd06fa"
EXPECTED_SOURCE_LOCKS = {
    "protocol/private/p06-table-layout-hwpx-v2.json": (
        "6ce63a1ba5749aaa5f593add993bbb4fc68c86ec485837cc4c00e5e5f44a6008"
    ),
    "crates/hwpx-package/examples/p06_05_table_layout_target_fixture.rs": (
        "96c654e0b063303cde61c9d958f0120fb12e7737b01b3c98d3dcf58632746274"
    ),
    "implementation/p06/tools/run-hancom-2020-table-layout-readback.ps1": (
        "17f7b99adb0c1ba3cfaf46f6ff7067d1c16c27d3699e12b4fe4550cef782f169"
    ),
}
EXPECTED_NOT_CLAIMED = {
    "new_target_hancom_2020_open": False,
    "new_target_hancom_2020_save_reopen": False,
    "new_target_hancom_2020_geometry_or_wrapping": False,
    "new_target_pdf_visual_oracle": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_version": False,
    "p06_05_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/examples/p06_05_table_layout_target_fixture.rs": (
        "hwpx-agent.p06-05-table-layout-target/v2",
        "exactly_one_line_cache_span",
        "edits.push((line_cache, Vec::new()))",
        "TextProfile::Source =>",
        "TextProfile::Target =>",
        "structured_text_rewrite_invalidates_four_line_caches",
        ".create_new(true)",
    ),
    MIGRATION_RELATIVE.as_posix(): (
        "hp:linesegarray",
        "Open=false",
        "There is no automatic migration",
        "remain unclaimed",
    ),
    "implementation/p06/P06-05_TARGET_FIXTURE.md": (
        "Superseded attempt 01 evidence",
        TARGET_SHA256,
        "**NOT RUN**",
        "P06-05 is not complete",
    ),
    "implementation/p06/P06-05_TARGET_ATTEMPT01_DIAGNOSTIC.md": (
        "TABLE_LAYOUT_READBACK_INPUT_OPEN_RETURNED_FALSE",
        TRACE_SHA256,
        "immutable failed evidence",
        "no\nsemantic or visual claim",
    ),
    "implementation/p06/P06-05_HWPX_LAYOUT_POLICY.md": (
        "derived cache",
        "hwpx-agent.p06-05-table-layout-target-contract/v1",
        "returned `Open=false`",
        "**NOT RUN**",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = base.load_contract(base.bounded_file(root, CONTRACT_RELATIVE.as_posix(), 256_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, evidence_files=0,
                      implementation_files=0)

    expected_scalars = {
        "schema_version": "hwpx-agent.p06-05-table-layout-target-contract/v1",
        "model_schema_version": "hwpx-agent.p06-05-table-layout-target/v2",
        "scope": "p06_05_exact_current_pc_hancom_2020_product_target_assembly",
        "prerequisites": [
            "hwpx-agent.table-layout-hwpx.hancom-2020/2",
            "hwpx-agent.p06-05-current-font-metric-receipt/v1",
            "exact_p06_04_current_pc_synthetic_source",
        ],
        "source_lock_canonicalization": "utf8_lf_sha256",
        "migration": MIGRATION_RELATIVE.as_posix(),
        "not_claimed": EXPECTED_NOT_CLAIMED,
    }
    for key, expected in expected_scalars.items():
        if contract.get(key) != expected:
            errors.append(key)

    required_objects = {
        "exact_inputs": {
            "source_path", "source_sha256", "font_receipt_path", "font_receipt_sha256",
            "component_contract_sha256",
        },
        "text_profile": {
            "ordered_cell_ids", "ordered_text_sha256", "text_set_sha256",
            "character_property_binding",
        },
        "layout_profile": {
            "grid_sha256", "plan_sha256", "table_width_hwpunit", "table_height_hwpunit",
            "column_widths_micrometers", "row_heights_micrometers", "inner_margin_hwpunit",
        },
        "layout_cache_policy": {
            "source_admission", "mutation", "target_readback", "reason", "repair",
        },
        "publication": {
            "directory", "files", "sha256", "write_mode", "byte_deterministic", "git_tracked",
        },
        "superseded_diagnostic": {
            "builder_schema", "target_sha256", "trace_path", "trace_sha256", "result",
            "error_code", "semantic_evidence",
        },
    }
    for key, expected_keys in required_objects.items():
        value = contract.get(key)
        if not isinstance(value, dict) or set(value) != expected_keys:
            errors.append(key)

    if contract.get("exact_inputs") != {
        "source_path": SOURCE_PATH,
        "source_sha256": SOURCE_SHA256,
        "font_receipt_path": RECEIPT_PATH,
        "font_receipt_sha256": RECEIPT_SHA256,
        "component_contract_sha256": EXPECTED_SOURCE_LOCKS[
            "protocol/private/p06-table-layout-hwpx-v2.json"
        ],
    }:
        errors.append("exact_inputs")

    text_profile = contract.get("text_profile")
    if not isinstance(text_profile, dict) or text_profile.get("ordered_cell_ids") != [
        "cell-a", "cell-b", "cell-c", "cell-d"
    ] or text_profile.get("ordered_text_sha256") != [
        "df47d07aa15a6493ed52bcddfbd594ff255d9566138ab7137f90b13fedd2ed98",
        "b81461d5ac0a8865284ef84c147e0743da482750e1a499d80126e31c7324ee7b",
        "25dfcb4b0c5e694cf7bf977f1870cd2025fa363bfa2a26118ea00f305a3afdd3",
        "d932f7dee69be5f5763a0647e1ed14067e5231e783b4039a9aabbf8387405845",
    ] or text_profile.get("text_set_sha256") != (
        "4edc218a49149201f2c37504a489594f4bb92951c0414437ca66934d9441522d"
    ):
        errors.append("text_profile")

    layout_profile = contract.get("layout_profile")
    expected_layout = {
        "grid_sha256": "2c21be8ef4d42da0b4c387395a235a9978bf53c7480f4159f815795799633c49",
        "plan_sha256": "bef03b662eadb78284d0fc7e5057fde2063f0f7cd249ea88551a5207487ba69b",
        "table_width_hwpunit": 19843,
        "table_height_hwpunit": 5200,
        "column_widths_micrometers": [52990, 17010],
        "row_heights_micrometers": [13758, 4586],
        "inner_margin_hwpunit": [510, 510, 141, 141],
    }
    if layout_profile != expected_layout:
        errors.append("layout_profile")

    publication = contract.get("publication")
    expected_publication = {
        "directory": TARGET_DIRECTORY,
        "files": TARGET_FILES,
        "sha256": TARGET_SHA256,
        "write_mode": "three_independent_create_new_writes",
        "byte_deterministic": True,
        "git_tracked": False,
    }
    if publication != expected_publication:
        errors.append("publication")

    diagnostic = contract.get("superseded_diagnostic")
    if not isinstance(diagnostic, dict) or diagnostic.get("trace_path") != TRACE_PATH or (
        diagnostic.get("trace_sha256") != TRACE_SHA256
        or diagnostic.get("target_sha256")
        != "a678588188593c250b33205f1660fef6c301280cd5ae30deb4b6a03f185055bc"
        or diagnostic.get("error_code") != "TABLE_LAYOUT_READBACK_INPUT_OPEN_RETURNED_FALSE"
        or diagnostic.get("semantic_evidence") != "none"
    ):
        errors.append("superseded_diagnostic")

    failure_policy = contract.get("failure_policy")
    if not isinstance(failure_policy, list) or len(failure_policy) < 8 or any(
        not isinstance(item, str) or not item for item in failure_policy
    ):
        errors.append("failure_policy")

    source_locks = contract.get("source_locks")
    source_count = len(source_locks) if isinstance(source_locks, list) else 0
    declared: dict[str, str] = {}
    if not isinstance(source_locks, list):
        errors.append("source_locks_shape")
    else:
        for entry in source_locks:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                errors.append("source_lock_shape")
                continue
            relative = entry.get("path")
            expected = entry.get("sha256")
            if not isinstance(relative, str) or not isinstance(expected, str) or relative in declared:
                errors.append("source_lock_types_or_duplicate")
                continue
            declared[relative] = expected
            try:
                actual = base.sha256_utf8_lf(base.bounded_file(root, relative, 512_000))
            except (OSError, UnicodeDecodeError, ValueError):
                errors.append("source_lock_path_or_encoding")
                continue
            if actual != expected:
                errors.append("source_lock_digest")
        if declared != EXPECTED_SOURCE_LOCKS:
            errors.append("source_locks_exact")

    evidence = {
        SOURCE_PATH: SOURCE_SHA256,
        RECEIPT_PATH: RECEIPT_SHA256,
        TRACE_PATH: TRACE_SHA256,
        **{f"{TARGET_DIRECTORY}/{name}": TARGET_SHA256 for name in TARGET_FILES},
    }
    evidence_files = 0
    for relative, expected in evidence.items():
        try:
            path = base.bounded_file(root, relative, 8 * 1024 * 1024)
            evidence_files += 1
            if sha256_file(path) != expected:
                errors.append("evidence_digest")
        except (OSError, ValueError):
            errors.append("evidence_path")

    try:
        trace = json.loads(
            base.bounded_file(root, TRACE_PATH, 256_000).read_text(encoding="utf-8"),
            object_pairs_hook=base.reject_duplicate_keys,
        )
        if not isinstance(trace, dict) or trace.get("state") != "failed" or (
            trace.get("failed_phase") != "open_input"
            or trace.get("error_code") != "TABLE_LAYOUT_READBACK_INPUT_OPEN_RETURNED_FALSE"
            or trace.get("input_unchanged") is not True
            or trace.get("output_saved") is not False
            or trace.get("render_pdf_saved") is not False
        ):
            errors.append("diagnostic_trace_semantics")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("diagnostic_trace_json")

    implementation_files = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = base.bounded_file(root, relative, 512_000).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
            continue
        implementation_files += 1
        if any(marker not in source for marker in markers):
            errors.append("implementation_marker")

    return result(
        errors=sorted(set(errors)),
        source_locks=source_count,
        evidence_files=evidence_files,
        implementation_files=implementation_files,
    )


def result(*, errors: list[str], source_locks: int, evidence_files: int,
           implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-layout-target-v1-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": errors,
        "source_locks": source_locks,
        "evidence_files": evidence_files,
        "implementation_files": implementation_files,
    }


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_LAYOUT_TARGET_V1_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"evidence_files={report['evidence_files']} "
        f"implementation_files={report['implementation_files']}"
    )
