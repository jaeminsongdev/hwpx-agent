#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from tools.p06 import validate_table_formula_hwpx_contract as predecessor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-formula-target-v2.json"
REPORT = "implementation/p06/P06-06_TARGET_READBACK_REPORT.md"
DIAGNOSTIC = "implementation/p06/P06-06_TARGET_ATTEMPTS_DIAGNOSTIC.md"
MIGRATION = "protocol/migrations/p06-table-formula-hwpx-v1-to-target-v2.md"
TARGET_DIRECTORY = "fixtures/target-build/p06-06-formula-target-20260907-01"
TARGET_FILES = (
    "target.hwpx",
    "target-repeat-a.hwpx",
    "target-repeat-b.hwpx",
    "target-idcheck.hwpx",
)
TARGET_PATHS = tuple(f"{TARGET_DIRECTORY}/{name}" for name in TARGET_FILES)
OUTPUT_PATH = f"{TARGET_DIRECTORY}/target-readback-output-04.hwpx"
PDF_PATH = f"{TARGET_DIRECTORY}/target-readback-output-04.pdf"
TRACE_PATH = f"{TARGET_DIRECTORY}/hancom-2020-trace-attempt04.json"
PROGRESS_PATH = f"{TRACE_PATH}.progress.jsonl"
TARGET_SHA256 = "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5"
OUTPUT_SHA256 = "8b33d2353ebec9eccbcbbde0c0b31eb440390ddf9c38bad7c064f179b1ab2325"
PDF_SHA256 = "e09e5a0d8acef22b146bb393a49dccf88a74e61b969c38aa83c7d5d79b0149f0"
TEXT_SHA256 = "91fd67b8cae0b9da6f05a8e960e061c239f58979cdfe19d4aabb40a445571644"
SOURCE_LOCK_COMMIT = "103bbf5b0448076e3f95db939b4d186100b6a4f4"

SOURCE_LOCKS = {
    "protocol/private/p06-table-formula-hwpx-v1.json":
        "fb1b0b53c51852d0e66999e2634d232885742d725064f065bb8db82a67784e8b",
    "tools/p06/validate_table_formula_hwpx_contract.py":
        "1d0b3e7db8b2d51e617dbb80999946b38473ef765c8f03ebeffb382c02b8c439",
    "crates/hwpx-package/src/table_formula.rs":
        "f9d802195d3f86fab07b1c0fcbb33131cf37b47db8910d348c6492693c394540",
    "crates/hwpx-package/src/table_layout.rs":
        "5a0ea2221982371766384536274e1c79e9dba01fa6b2ce2c3d6f56dd5b7329d0",
    "crates/hwpx-package/src/id_index.rs":
        "5a6014e211bf26ddedb1f7160b50357429b0394a2bc7a6e66da02c9cad2352d1",
    "crates/hwpx-package/examples/p06_06_table_formula_structural_target_fixture.rs":
        "89ea28960353b3db43a4974e0557df79b74af61915e0d7112332b0ad6cdefcd9",
    "crates/hwpx-package/examples/p06_06_table_formula_target_oracle.rs":
        "c2297d92919bb47cb622dd753508543c1e2ad059421796c56f69e1c6e5abdc9e",
    "implementation/p05/tools/invoke-hancom-2020-bounded-readback.ps1":
        "f13474940e14754a483409d428c814c2c05c6ca9428143aff73337a82f5fcf18",
    "implementation/p05/tools/run-hancom-2020-tab-readback.ps1":
        "e27582f85f2fd17824b9c8afd8b3cda922a448590104982266fc5b7f6bcd6d72",
    "implementation/p06/tools/run-hancom-2020-formula-target-readback.ps1":
        "72387acbc71f32bc99ea68e3c99495e550779005e4217886708940fd01095425",
    "implementation/p06/tests/Test-Hancom2020FormulaTargetReadback.ps1":
        "4e26c156fa3520547f00973be76b5924fb0de4330a16221785060e9a9b96caa3",
}

HISTORICAL = (
    (1, "hancom-2020-trace.json", 600,
     "dbd53c64046d354f8959b52024790b0aa6b90423b3b04e9830c9959b83118e03", 1370,
     "75484cc941f11c57b19c20fb68db9c9c8d96a244dac56e9ce990c2b00b8e95d4", 735),
    (2, "hancom-2020-trace-attempt02.json", 900,
     "934ffeea7c6e86b2721fc99f4fadb96775bca26fc5a8ef47388af9dd51a91214", 1370,
     "1524a4a683be1e1c71701930f3feff43f1c932a10c3d5a2c2e721d8dc407f515", 735),
    (3, "hancom-2020-trace-attempt03.json", 900,
     "934ffeea7c6e86b2721fc99f4fadb96775bca26fc5a8ef47388af9dd51a91214", 1370,
     "cc9bcda8a05fbef022b8dd549b5a973f3bf9f148069903fb952e9cd5424466e4", 735),
)

EVIDENCE: dict[str, tuple[str, int]] = {
    **{path: (TARGET_SHA256, 13103) for path in TARGET_PATHS},
    OUTPUT_PATH: (OUTPUT_SHA256, 14206),
    PDF_PATH: (PDF_SHA256, 9930),
    TRACE_PATH: ("8ac23180615e0b250961e2556ad338e2aab7e20d6f745bc12d09a457e169aa94", 2319),
    PROGRESS_PATH: ("7292e29c98e747ff86c2d8f35c28a9bb6c8248646be0cbc5e828e6a9f42f8fec", 5165),
}
for _, trace_name, _, trace_sha, trace_bytes, progress_sha, progress_bytes in HISTORICAL:
    trace_path = f"{TARGET_DIRECTORY}/{trace_name}"
    EVIDENCE[trace_path] = (trace_sha, trace_bytes)
    EVIDENCE[f"{trace_path}.progress.jsonl"] = (progress_sha, progress_bytes)

IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/examples/p06_06_table_formula_structural_target_fixture.rs": (
        "pure structural formula differential drifted",
        "IdRuleProfile::current_hancom_2020_formula_v3()",
        "SUM(A2:C2)",
        "write_create_new",
    ),
    "crates/hwpx-package/examples/p06_06_table_formula_target_oracle.rs": (
        "EXPECTED_ORACLE_SHA256",
        "section_equal_after_renderer_cache_strip=true",
        "strip_and_inspect_renderer_caches",
        "renderer_cache_attribute_drift_fails_closed",
    ),
    "crates/hwpx-package/src/id_index.rs": (
        "current_hancom_2020_formula_v3",
        "hancom-2020-hwpml-2011-formula/v3",
    ),
    "implementation/p05/tools/invoke-hancom-2020-bounded-readback.ps1": (
        "window_visible_for_user_access",
        "Stop-OwnedHancomProcesses",
        "progress_event_count",
    ),
    "implementation/p06/tools/run-hancom-2020-formula-target-readback.ps1": (
        "hwpx-agent.p06-06-hancom-2020-formula-target-readback/v1",
        "TABLE_FORMULA_TARGET_READBACK",
        "invoke-hancom-2020-bounded-readback.ps1",
    ),
    "implementation/p06/tests/Test-Hancom2020FormulaTargetReadback.ps1": (
        "preflight_fails_before_com",
        "no_ui_input",
        "no_network",
        "no_registry_write",
    ),
    REPORT: (
        "PASS for the exact current-PC Hangul 2020 P06-06 target",
        OUTPUT_SHA256,
        PDF_SHA256,
        "P06-07 through P06-09",
    ),
    DIAGNOSTIC: (
        "Decision for attempts 01-03: **NOT PASS**",
        "Attempt 04 completed",
        "does not modify or promote attempts 01-03",
    ),
    MIGRATION: (
        "There is no automatic migration",
        "source formula cache remains unverified",
        "Other PCs and Hangul versions",
    ),
}

PACKAGE_PARTS = {
    "mimetype", "version.xml", "Contents/header.xml", "Contents/section0.xml",
    "Preview/PrvText.txt", "settings.xml", "Preview/PrvImage.png",
    "META-INF/container.rdf", "Contents/content.hpf", "META-INF/container.xml",
    "META-INF/manifest.xml",
}
UNCHANGED_PARTS = {
    "mimetype", "version.xml", "META-INF/container.rdf", "META-INF/container.xml",
    "META-INF/manifest.xml",
}
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HH = "http://www.hancom.co.kr/hwpml/2011/head"
OPF = "http://www.idpf.org/2007/opf/"
HA = "http://www.hancom.co.kr/hwpml/2011/app"

TARGET_PREVIEW = b"<0><0><0><0><17><10><25><52>\r\n\r\n"
ORACLE_PREVIEW = b"<0><0><0><0>\r\n<17><10><25><52>\r\n\r\n"
VISIBLE_VALUES = ["0", "0", "0", "0", "17", "10", "25", "52"]
CELL_ADDRESSES = [(row, column) for row in range(2) for column in range(4)]
COMMON_LINE_ATTRIBUTES = {
    "textpos": "0", "vertsize": "1000", "textheight": "1000", "baseline": "850",
    "spacing": "600", "horzpos": "0", "flags": "393216",
}
CACHE_PATTERN = re.compile(
    rb'<hp:linesegarray><hp:lineseg textpos="0" vertpos="(?:0|3130)" '
    rb'vertsize="1000" textheight="1000" baseline="850" spacing="600" '
    rb'horzpos="0" horzsize="(?:0|9468|42520)" flags="393216"/>'
    rb'</hp:linesegarray>'
)


def tag(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)


def safe_path(root: Path, relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
        raise ValueError("unsafe path")
    path = (root / Path(*candidate.parts)).resolve()
    if root.resolve() not in path.parents:
        raise ValueError("outside root")
    return path


def bounded_bytes(root: Path, relative: str, limit: int = 64 * 1024 * 1024) -> bytes:
    path = safe_path(root, relative)
    item = path.stat()
    if item.st_size <= 0 or item.st_size > limit or path.is_symlink() or not path.is_file():
        raise ValueError("unsafe file")
    data = path.read_bytes()
    if len(data) != item.st_size:
        raise ValueError("file changed")
    return data


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_predecessor_paths() -> set[str]:
    return {
        predecessor.CONTRACT,
        predecessor.REPORT,
        predecessor.MIGRATION,
        *predecessor.SOURCE_LOCKS,
        *predecessor.EVIDENCE,
        *predecessor.IMPLEMENTATION_MARKERS,
    }


def expected_evidence() -> set[str]:
    return {*EVIDENCE, *predecessor.EVIDENCE}


def expected_validation_tree() -> set[str]:
    return {
        CONTRACT,
        REPORT,
        DIAGNOSTIC,
        MIGRATION,
        *SOURCE_LOCKS,
        *IMPLEMENTATION_MARKERS,
        *EVIDENCE,
        *expected_predecessor_paths(),
    }


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json(bounded_bytes(root, CONTRACT, 512_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0, "not_proven")
    validate_contract(contract, errors)
    source_count = validate_source_locks(root, contract, errors)
    predecessor_state, predecessor_evidence_count = validate_predecessor(root, errors)
    evidence_count = validate_evidence(root, errors) + predecessor_evidence_count
    validate_target_and_oracle(root, errors)
    validate_historical_attempts(root, errors)
    validate_trace(root, errors)
    validate_progress(root, errors)
    validate_pdf(root, errors)
    implementation_count = validate_markers(root, errors)
    return result(sorted(set(errors)), source_count, evidence_count, implementation_count,
                  predecessor_state)


def validate_contract(contract: dict[str, Any], errors: list[str]) -> None:
    expected_keys = {
        "schema_version", "model_schema_version", "adapter_profile_id", "scope",
        "predecessor", "prerequisites", "source_lock_canonicalization", "source_locks",
        "exact_source", "structural_target", "historical_attempts", "actual_oracle",
        "gate_decision", "failure_policy", "migration", "report", "not_claimed",
    }
    if not isinstance(contract, dict) or set(contract) != expected_keys:
        errors.append("contract_shape")
        return
    exact = {
        "schema_version": "hwpx-agent.p06-06-table-formula-target-contract/v2",
        "model_schema_version": "hwpx-agent.table-formula/v1",
        "adapter_profile_id": "hwpx-agent.table-formula-hwpx.hancom-2020/1",
        "scope": "p06_06_exact_current_pc_hancom_2020_structural_target_and_external_oracle",
        "source_lock_canonicalization": "exact_file_bytes_sha256",
        "migration": MIGRATION,
        "report": REPORT,
    }
    for key, value in exact.items():
        if contract.get(key) != value:
            errors.append(key)
    if contract.get("predecessor") != {
        "path": predecessor.CONTRACT,
        "sha256": SOURCE_LOCKS[predecessor.CONTRACT],
        "state": "immutable_source_capture_and_adapter_component_contract",
    }:
        errors.append("predecessor")
    if contract.get("prerequisites") != [
        "hwpx-agent.p06-06-table-formula-hwpx-contract/v1",
        "hwpx-agent.table-formula/v1",
        "hwpx-agent.table-formula-hwpx.hancom-2020/1",
        "hwpx-agent.id-index.hancom-2020-formula-additive/3",
        "exact_licensed_current_pc_hancom_2020_11.0.0.9136",
    ]:
        errors.append("prerequisites")
    source = contract.get("exact_source")
    if source != {
        "predecessor_validation": "pass_required",
        "path": predecessor.SOURCE_HWPX,
        "sha256": predecessor.EVIDENCE[predecessor.SOURCE_HWPX][0],
        "bytes": predecessor.EVIDENCE[predecessor.SOURCE_HWPX][1],
        "formula_cache_value": 42,
        "formula_cache_provenance": "unverified_source_capture",
    }:
        errors.append("exact_source")
    validate_structural_target_contract(contract.get("structural_target"), errors)
    validate_history_contract(contract.get("historical_attempts"), errors)
    validate_oracle_contract(contract.get("actual_oracle"), errors)
    if contract.get("gate_decision") != {
        "actual_hancom_2020_source_capture": "pass",
        "source_identity_adapter_check": "pass",
        "adapter_component": "pass",
        "row_column_structural_differential": "pass",
        "product_target_hancom_2020_oracle": "pass",
        "p06_06": "pass",
        "p06": "in_progress",
    }:
        errors.append("gate_decision")
    expected_failure_policy = [
        "wrong_predecessor_source_target_or_oracle_digest_rejects",
        "existing_target_or_runtime_output_path_rejects_without_overwrite",
        "source_and_target_are_rehashed_after_processing",
        "target_repeat_or_id_profile_drift_rejects",
        "unknown_formula_layout_or_package_shape_rejects",
        "oracle_formula_value_cell_geometry_or_content_drift_rejects",
        "oracle_section_must_equal_target_after_exact_ten_renderer_cache_elements_are_removed",
        "unexpected_header_content_settings_or_preview_drift_rejects",
        "runtime_trace_progress_pdf_or_process_residue_drift_rejects",
        "historical_failed_attempts_are_never_promoted_to_pass",
        "other_pc_or_hancom_version_evidence_is_never_inferred",
    ]
    if contract.get("failure_policy") != expected_failure_policy:
        errors.append("failure_policy")
    if contract.get("not_claimed") != {
        "arbitrary_native_formula_syntax": False,
        "arbitrary_user_document_compatibility": False,
        "generic_formula_cache_verification": False,
        "other_pc_or_hancom_version": False,
        "p06_complete": False,
        "production": False,
        "product_complete": False,
    }:
        errors.append("not_claimed")


def validate_structural_target_contract(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("structural_target")
        return
    checks = (
        value.get("execution_base_commit") == "a5c8e9389f75a52e253a3e9cc40da908d02e1fac",
        value.get("directory") == TARGET_DIRECTORY,
        value.get("files") == list(TARGET_FILES),
        value.get("sha256") == TARGET_SHA256,
        value.get("bytes") == 13103,
        value.get("write_mode") == "four_independent_create_new_writes",
        value.get("byte_deterministic") is True,
        value.get("git_tracked") is False,
        value.get("rows") == 2 and value.get("columns") == 4,
        value.get("cell_addresses") == [[row, column] for row, column in CELL_ADDRESSES],
        value.get("visible_values") == VISIBLE_VALUES,
        value.get("formula_owner") == {"row": 1, "column": 3},
        value.get("locale_neutral_formula") == "SUM(A2:C2)",
        value.get("formula_sha256")
        == "dc20d6bd96ba46fd4395e3d4f91169ccaca755f0888988667d9d38d312d4abe4",
        value.get("formula_cache_value") == 52,
        value.get("formula_cache_pre_runtime_provenance") == "unverified",
        value.get("table_width_hwpunit") == 41952,
        value.get("table_height_hwpunit") == 2564,
        value.get("cell_widths_hwpunit") == [10488] * 8,
        value.get("cell_heights_hwpunit") == [282] * 8,
        value.get("inner_margin_hwpunit") == [510, 510, 141, 141],
        value.get("content_sha256")
        == "fadae4f5979e992d2683c169134ac6f62a15677122934d9c6df7c86a3dd1be21",
        value.get("cell_text_set_sha256")
        == "b9b6348c2973b6ab37d3b10d0ae4e659d8c9e478766b0c264fe91f28fc0b1f9c",
        value.get("section_sha256")
        == "50bcce77389351567952af296a70ccd8d2742e49b439153b887c3bb5490085cf",
        value.get("formula_unowned_sha256")
        == "b5ec122b6e6a4e9bde237810dee42acc7d6f0cb5ab0b5ee6803f772baa1e7e06",
        value.get("cell_line_cache_counts") == [0] * 8,
    )
    expected_keys = {
        "execution_base_commit", "directory", "files", "sha256", "bytes", "write_mode",
        "byte_deterministic", "git_tracked", "rows", "columns", "cell_addresses",
        "visible_values", "formula_owner", "locale_neutral_formula", "formula_sha256",
        "formula_cache_value", "formula_cache_pre_runtime_provenance",
        "table_width_hwpunit", "table_height_hwpunit", "cell_widths_hwpunit",
        "cell_heights_hwpunit", "inner_margin_hwpunit", "content_sha256",
        "cell_text_set_sha256", "section_sha256", "formula_unowned_sha256",
        "cell_line_cache_counts",
    }
    if set(value) != expected_keys or not all(checks):
        errors.append("structural_target")


def expected_history_contract() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for attempt, name, timeout, trace_sha, trace_bytes, progress_sha, progress_bytes in HISTORICAL:
        trace_path = f"{TARGET_DIRECTORY}/{name}"
        output.append({
            "attempt": attempt,
            "trace_path": trace_path,
            "trace_sha256": trace_sha,
            "trace_bytes": trace_bytes,
            "progress_path": f"{trace_path}.progress.jsonl",
            "progress_sha256": progress_sha,
            "progress_bytes": progress_bytes,
            "timeout_seconds": timeout,
            "last_validated_event": "open_input/running",
            "decision": "failed_timeout_not_promoted",
        })
    return output


def validate_history_contract(value: Any, errors: list[str]) -> None:
    if value != expected_history_contract():
        errors.append("historical_attempts")


def validate_oracle_contract(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("actual_oracle")
        return
    exact = {
        "output_hwpx_path": OUTPUT_PATH,
        "output_hwpx_sha256": OUTPUT_SHA256,
        "output_hwpx_bytes": 14206,
        "output_pdf_path": PDF_PATH,
        "output_pdf_sha256": PDF_SHA256,
        "output_pdf_bytes": 9930,
        "trace_path": TRACE_PATH,
        "trace_sha256": EVIDENCE[TRACE_PATH][0],
        "trace_bytes": 2319,
        "progress_path": PROGRESS_PATH,
        "progress_sha256": EVIDENCE[PROGRESS_PATH][0],
        "progress_bytes": 5165,
        "hancom_file_version": "11.0.0.9136",
        "hancom_executable_sha256":
            "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        "visible_text_sha256_before_and_after": TEXT_SHA256,
        "formula_sha256":
            "dc20d6bd96ba46fd4395e3d4f91169ccaca755f0888988667d9d38d312d4abe4",
        "formula_unowned_sha256":
            "110f4885d3f4a4a29e57275a116fc82675a0d51394f4df12ee2111b0f94ca4ce",
        "content_sha256":
            "fadae4f5979e992d2683c169134ac6f62a15677122934d9c6df7c86a3dd1be21",
        "cell_text_set_sha256":
            "b9b6348c2973b6ab37d3b10d0ae4e659d8c9e478766b0c264fe91f28fc0b1f9c",
        "formula_cache_value": 52,
        "formula_cache_oracle": "verified_external_receipt",
        "rows": 2,
        "columns": 4,
        "table_width_hwpunit": 41952,
        "table_height_hwpunit": 2564,
        "target_cell_dimensions_preserved": True,
        "target_inner_margin_preserved": True,
        "cell_line_cache_counts": [1] * 8,
        "cell_line_cache_widths_hwpunit": [9468] * 8,
        "section_line_cache_count": 10,
        "section_renderer_cache_sha256":
            "97a35d87c56678bb03bf9994d8351f96be006b4f0689f231b6f85dd76c6c4e49",
        "section_sha256":
            "2f7faaa8e7b8def434a1c3726aa03ddb5230e288e64fd8f7b9c21fd9a274bcb7",
        "section_equal_to_target_after_exact_renderer_cache_strip": True,
        "package_part_count": 11,
        "unchanged_parts": [
            "mimetype", "version.xml", "META-INF/container.rdf", "META-INF/container.xml",
            "META-INF/manifest.xml",
        ],
        "header_change":
            "three_unsupported_levels_7_8_9_switches_resolved_to_exact_default_fallbacks",
        "content_hpf_change": "modified_date_and_header_spine_linear_only",
        "settings_change": "caret_position_only",
        "preview_text_change": "exact_crlf_row_boundary_inserted",
        "preview_image_change": "hancom_renderer_regenerated",
        "input_unchanged": True,
        "save_reopen_pass": True,
        "pdf_signature_valid": True,
        "pdf_visual_review":
            "pass_one_page_2x4_all_eight_values_visible_no_clipping_no_overlap",
        "remaining_hwp_process_count": 0,
    }
    if value != exact:
        errors.append("actual_oracle")


def validate_source_locks(root: Path, contract: dict[str, Any], errors: list[str]) -> int:
    locks = contract.get("source_locks")
    if not isinstance(locks, list):
        errors.append("source_locks_shape")
        return 0
    actual: dict[str, str] = {}
    for item in locks:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_locks_shape")
            continue
        path, digest = item.get("path"), item.get("sha256")
        if not isinstance(path, str) or not isinstance(digest, str) or path in actual:
            errors.append("source_locks_shape")
            continue
        actual[path] = digest
        try:
            if sha256(source_lock_bytes(root, path, 8 * 1024 * 1024)) != digest:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_path_or_encoding")
    if actual != SOURCE_LOCKS:
        errors.append("source_locks_exact")
    return len(actual)


def source_lock_bytes(root: Path, relative: str, maximum: int) -> bytes:
    """Reads historical locks from their immutable qualification commit when Git is available."""
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
        raise ValueError("unsafe source-lock path")
    if not (root / ".git").exists():
        return bounded_bytes(root, relative, maximum)
    completed = subprocess.run(
        ["git", "-C", str(root), "show", f"{SOURCE_LOCK_COMMIT}:{relative}"],
        check=False,
        capture_output=True,
        timeout=15,
    )
    if completed.returncode != 0 or not completed.stdout or len(completed.stdout) > maximum:
        raise ValueError("immutable source-lock blob unavailable")
    return completed.stdout


def validate_predecessor(root: Path, errors: list[str]) -> tuple[str, int]:
    report = predecessor.validate(root)
    if report.get("state") != "pass" or report.get("product_target_oracle") != "not_run" \
            or report.get("p06_06") != "in_progress":
        errors.append("predecessor_validation")
        return "not_proven", int(report.get("evidence_files", 0))
    return "pass", int(report.get("evidence_files", 0))


def validate_evidence(root: Path, errors: list[str]) -> int:
    count = 0
    for relative, (expected_hash, expected_size) in EVIDENCE.items():
        try:
            data = bounded_bytes(root, relative)
        except (OSError, ValueError):
            errors.append("evidence_path_or_size")
            continue
        count += 1
        if len(data) != expected_size or sha256(data) != expected_hash:
            errors.append("evidence_digest")
    return count


def zip_payloads(data: bytes) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {}
    total = 0
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        if len(infos) != len(PACKAGE_PARTS):
            raise ValueError("part count")
        for info in infos:
            name = info.filename
            candidate = PurePosixPath(name)
            unix_mode = (info.external_attr >> 16) & 0o170000
            if name in payloads or name.endswith("/") or candidate.is_absolute() \
                    or ".." in candidate.parts or "\\" in name or info.flag_bits & 1 \
                    or info.file_size < 0 or info.file_size > 8 * 1024 * 1024 \
                    or unix_mode == 0o120000:
                raise ValueError("unsafe part")
            total += info.file_size
            if total > 64 * 1024 * 1024:
                raise ValueError("package limit")
            value = archive.read(info)
            if len(value) != info.file_size:
                raise ValueError("part size")
            payloads[name] = value
        mimetype = next(item for item in infos if item.filename == "mimetype")
        if mimetype.compress_type != zipfile.ZIP_STORED:
            raise ValueError("mimetype compression")
    if set(payloads) != PACKAGE_PARTS:
        raise ValueError("part names")
    return payloads


def validate_target_and_oracle(root: Path, errors: list[str]) -> None:
    try:
        publications = [bounded_bytes(root, path, 8 * 1024 * 1024) for path in TARGET_PATHS]
        if any(value != publications[0] for value in publications[1:]):
            raise ValueError("publication drift")
        target = zip_payloads(publications[0])
        oracle = zip_payloads(bounded_bytes(root, OUTPUT_PATH, 8 * 1024 * 1024))
        if any(target[name] != oracle[name] for name in UNCHANGED_PARTS):
            raise ValueError("unchanged part drift")
        changed = {name for name in PACKAGE_PARTS if target[name] != oracle[name]}
        if changed != PACKAGE_PARTS - UNCHANGED_PARTS:
            raise ValueError("changed part set")
        if target["Preview/PrvText.txt"] != TARGET_PREVIEW \
                or oracle["Preview/PrvText.txt"] != ORACLE_PREVIEW \
                or not target["Preview/PrvImage.png"].startswith(b"\x89PNG\r\n\x1a\n") \
                or not oracle["Preview/PrvImage.png"].startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("preview")
        target_section = target["Contents/section0.xml"]
        oracle_section = oracle["Contents/section0.xml"]
        if sha256(target_section) \
                != "50bcce77389351567952af296a70ccd8d2742e49b439153b887c3bb5490085cf" \
                or sha256(oracle_section) \
                != "2f7faaa8e7b8def434a1c3726aa03ddb5230e288e64fd8f7b9c21fd9a274bcb7":
            raise ValueError("section digest")
        if CACHE_PATTERN.search(target_section):
            raise ValueError("target cache")
        stripped, removed = CACHE_PATTERN.subn(b"", oracle_section)
        if removed != 10 or b"<hp:linesegarray" in stripped or stripped != target_section:
            raise ValueError("section cache strip")
        validate_table_section(target_section, expect_oracle=False)
        validate_table_section(oracle_section, expect_oracle=True)
        validate_header_relation(target["Contents/header.xml"], oracle["Contents/header.xml"])
        validate_content_relation(target["Contents/content.hpf"], oracle["Contents/content.hpf"])
        validate_settings_relation(target["settings.xml"], oracle["settings.xml"])
    except (OSError, KeyError, TypeError, ValueError, ET.ParseError, zipfile.BadZipFile):
        errors.append("target_oracle_hwpx_semantics")


def validate_table_section(section: bytes, expect_oracle: bool) -> None:
    root = ET.fromstring(section)
    if sum(1 for _ in root.iter()) > 4096:
        raise ValueError("element limit")
    tables = list(root.iter(tag(HP, "tbl")))
    if len(tables) != 1:
        raise ValueError("table count")
    table = tables[0]
    if table.get("rowCnt") != "2" or table.get("colCnt") != "4":
        raise ValueError("grid")
    sizes = [item for item in table if item.tag == tag(HP, "sz")]
    margins = [item for item in table if item.tag == tag(HP, "inMargin")]
    if len(sizes) != 1 or sizes[0].get("width") != "41952" \
            or sizes[0].get("height") != "2564" or len(margins) != 1 \
            or margins[0].attrib != {
                "left": "510", "right": "510", "top": "141", "bottom": "141",
            }:
        raise ValueError("table geometry")
    rows = [item for item in table if item.tag == tag(HP, "tr")]
    cells = [item for row in rows for item in row if item.tag == tag(HP, "tc")]
    if len(rows) != 2 or len(cells) != 8:
        raise ValueError("cells")
    addresses: list[tuple[int, int]] = []
    visible: list[str] = []
    cell_arrays: list[ET.Element] = []
    formula_owner: tuple[int, int] | None = None
    formula_begin: ET.Element | None = None
    for cell in cells:
        addresses_nodes = [item for item in cell if item.tag == tag(HP, "cellAddr")]
        sizes_nodes = [item for item in cell if item.tag == tag(HP, "cellSz")]
        spans = [item for item in cell if item.tag == tag(HP, "cellSpan")]
        if len(addresses_nodes) != 1 or len(sizes_nodes) != 1 or len(spans) != 1:
            raise ValueError("cell shape")
        address = (int(addresses_nodes[0].get("rowAddr", "-1")),
                   int(addresses_nodes[0].get("colAddr", "-1")))
        addresses.append(address)
        if sizes_nodes[0].get("width") != "10488" or sizes_nodes[0].get("height") != "282" \
                or spans[0].get("rowSpan") != "1" or spans[0].get("colSpan") != "1":
            raise ValueError("cell geometry")
        visible.append("".join((node.text or "") for node in cell.iter(tag(HP, "t"))))
        begins = list(cell.iter(tag(HP, "fieldBegin")))
        if begins:
            if len(begins) != 1 or formula_begin is not None:
                raise ValueError("formula cardinality")
            formula_begin = begins[0]
            formula_owner = address
        arrays = list(cell.iter(tag(HP, "linesegarray")))
        cell_arrays.extend(arrays)
        if expect_oracle:
            if len(arrays) != 1:
                raise ValueError("cell cache cardinality")
            validate_line_array(arrays[0], "0", "9468")
        elif arrays:
            raise ValueError("target cell cache")
    if addresses != CELL_ADDRESSES or visible != VISIBLE_VALUES \
            or formula_owner != (1, 3) or formula_begin is None:
        raise ValueError("table semantics")
    ends = list(table.iter(tag(HP, "fieldEnd")))
    if len(ends) != 1 or formula_begin.get("type") != "FORMULA" \
            or ends[0].get("beginIDRef") != formula_begin.get("id") \
            or ends[0].get("fieldid") != formula_begin.get("fieldid"):
        raise ValueError("formula identity")
    parameters = formula_begin.find(tag(HP, "parameters"))
    if parameters is None:
        raise ValueError("formula parameters")
    last_results = [item for item in parameters if item.get("name") == "LastResult"]
    if len(last_results) != 1 or (last_results[0].text or "") != "52":
        raise ValueError("formula result")
    all_arrays = list(root.iter(tag(HP, "linesegarray")))
    if not expect_oracle:
        if all_arrays:
            raise ValueError("target section cache")
        return
    if len(all_arrays) != 10 or len(cell_arrays) != 8:
        raise ValueError("section cache count")
    cell_ids = {id(item) for item in cell_arrays}
    outside = [item for item in all_arrays if id(item) not in cell_ids]
    if len(outside) != 2:
        raise ValueError("outside cache count")
    validate_line_array(outside[0], "0", "0")
    validate_line_array(outside[1], "3130", "42520")
    parents = {id(child): parent for parent in root.iter() for child in parent}
    if any(parents.get(id(item)) is None or parents[id(item)].tag != tag(HP, "p")
           for item in all_arrays):
        raise ValueError("cache parent")


def validate_line_array(array: ET.Element, vertpos: str, horzsize: str) -> None:
    if array.attrib or len(array) != 1 or array[0].tag != tag(HP, "lineseg") \
            or len(array[0]) != 0:
        raise ValueError("cache shape")
    expected = dict(COMMON_LINE_ATTRIBUTES)
    expected.update({"vertpos": vertpos, "horzsize": horzsize})
    if array[0].attrib != expected:
        raise ValueError("cache attributes")


def element_signature(element: ET.Element) -> tuple[Any, ...]:
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),
        element.text or "",
        element.tail or "",
        tuple(element_signature(child) for child in element),
    )


def validate_header_relation(target: bytes, oracle: bytes) -> None:
    left = ET.fromstring(target)
    right = ET.fromstring(oracle)
    levels: list[int] = []
    for parent in list(left.iter()):
        for index, child in list(enumerate(list(parent))):
            if child.tag != tag(HP, "switch"):
                continue
            headings = [item for item in child.iter(tag(HH, "heading"))
                        if item.get("level") in {"7", "8", "9"}]
            if not headings:
                continue
            if len(headings) != 1:
                raise ValueError("heading switch")
            defaults = [item for item in child if item.tag == tag(HP, "default")]
            if len(defaults) != 1 or len(defaults[0]) != 1:
                raise ValueError("heading fallback")
            levels.append(int(headings[0].get("level", "-1")))
            parent.remove(child)
            parent.insert(index, copy.deepcopy(defaults[0][0]))
    if sorted(levels) != [7, 8, 9] or element_signature(left) != element_signature(right):
        raise ValueError("header fallback drift")


def validate_content_relation(target: bytes, oracle: bytes) -> None:
    left = ET.fromstring(target)
    right = ET.fromstring(oracle)
    modified = [item for item in left.iter(tag(OPF, "meta"))
                if item.get("name") == "ModifiedDate"]
    oracle_modified = [item for item in right.iter(tag(OPF, "meta"))
                       if item.get("name") == "ModifiedDate"]
    header_refs = [item for item in left.iter(tag(OPF, "itemref"))
                   if item.get("idref") == "header"]
    oracle_header_refs = [item for item in right.iter(tag(OPF, "itemref"))
                          if item.get("idref") == "header"]
    if len(modified) != 1 or len(oracle_modified) != 1 or len(header_refs) != 1 \
            or len(oracle_header_refs) != 1 \
            or modified[0].get("content") != "text" \
            or oracle_modified[0].get("content") != "text" \
            or (modified[0].text or "") != "2026-09-07T10:14:37Z" \
            or (oracle_modified[0].text or "") != "2026-09-07T22:54:21Z" \
            or header_refs[0].get("linear") != "yes" \
            or oracle_header_refs[0].get("linear") != "no":
        raise ValueError("content expected change")
    modified[0].text = oracle_modified[0].text
    header_refs[0].set("linear", "no")
    if element_signature(left) != element_signature(right):
        raise ValueError("content drift")


def validate_settings_relation(target: bytes, oracle: bytes) -> None:
    left = ET.fromstring(target)
    right = ET.fromstring(oracle)
    left_caret = list(left.iter(tag(HA, "CaretPosition")))
    right_caret = list(right.iter(tag(HA, "CaretPosition")))
    if len(left_caret) != 1 or len(right_caret) != 1 \
            or left_caret[0].attrib != {"listIDRef": "4", "paraIDRef": "0", "pos": "8"} \
            or right_caret[0].attrib != {"listIDRef": "4", "paraIDRef": "0", "pos": "1"}:
        raise ValueError("caret expected change")
    left_caret[0].set("pos", "1")
    if element_signature(left) != element_signature(right):
        raise ValueError("settings drift")


def validate_historical_attempts(root: Path, errors: list[str]) -> None:
    missing_outputs = (
        "target-readback-output.hwpx", "target-readback-output.pdf",
        "target-readback-output-02.hwpx", "target-readback-output-02.pdf",
        "target-readback-output-03.hwpx", "target-readback-output-03.pdf",
    )
    try:
        for _, name, timeout, *_ in HISTORICAL:
            trace_path = f"{TARGET_DIRECTORY}/{name}"
            trace = load_json(bounded_bytes(root, trace_path, 256_000))
            watchdog = trace.get("watchdog", {})
            checks = (
                trace.get("state") == "failed",
                trace.get("error_code") == "TABLE_FORMULA_TARGET_READBACK_TIMEOUT",
                trace.get("failed_phase") == "watchdog",
                trace.get("input_sha256") == TARGET_SHA256,
                trace.get("input_unchanged") is True,
                trace.get("output_saved") is False,
                trace.get("render_pdf_saved") is False,
                watchdog.get("timeout_seconds") == timeout,
                watchdog.get("timed_out") is True,
                watchdog.get("cleaned_process_count") == 1,
                watchdog.get("remaining_hwp_process_count") == 0,
                watchdog.get("progress_event_count") == 3,
                watchdog.get("progress_last_phase") == "open_input",
                watchdog.get("progress_last_state") == "running",
            )
            if not all(checks):
                raise ValueError("historical trace")
            events = read_jsonl(root, f"{trace_path}.progress.jsonl")
            if [(item.get("sequence"), item.get("phase"), item.get("state"))
                    for item in events] != [
                        (1, "preflight", "pass"),
                        (2, "com_create", "pass"),
                        (3, "open_input", "running"),
                    ] or any(item.get("raw_document_text_present") is not False for item in events):
                raise ValueError("historical progress")
        if any(safe_path(root, f"{TARGET_DIRECTORY}/{name}").exists()
               for name in missing_outputs):
            raise ValueError("historical output exists")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("historical_attempt_semantics")


def validate_trace(root: Path, errors: list[str]) -> None:
    try:
        trace = load_json(bounded_bytes(root, TRACE_PATH, 256_000))
        expected_target = {
            "prog_id": "HWPFrame.HwpObject.2",
            "registry_view": "Registry32",
            "client": "windows_powershell_x86_sta",
            "file_version": "11.0.0.9136",
            "executable_sha256":
                "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        }
        expected_phases = {
            "com_create": "pass", "open_input": "pass", "read_input": "pass",
            "save_as_hwpx": "pass", "close_input": "pass", "reopen_output": "pass",
            "read_output": "pass", "export_pdf": "pass", "close_output": "pass",
            "quit": "pass",
        }
        watchdog = trace.get("watchdog", {})
        checks = (
            trace.get("schema_version")
            == "hwpx-agent.p06-06-hancom-2020-formula-target-readback/v1",
            trace.get("state") == "pass",
            trace.get("target") == expected_target,
            trace.get("input_sha256") == TARGET_SHA256,
            trace.get("output_sha256") == OUTPUT_SHA256,
            trace.get("input_text_sha256") == TEXT_SHA256,
            trace.get("output_text_sha256") == TEXT_SHA256,
            trace.get("input_unchanged") is True,
            trace.get("output_saved") is True,
            trace.get("render_pdf_requested") is True,
            trace.get("render_pdf_saved") is True,
            trace.get("render_pdf_sha256") == PDF_SHA256,
            trace.get("render_pdf_bytes") == 9930,
            trace.get("render_pdf_signature_valid") is True,
            trace.get("render_pdf_export_method") == "IXHwpDocument.SaveAs/PDF",
            trace.get("phases") == expected_phases,
            trace.get("error_code") is None and trace.get("failed_phase") is None,
            trace.get("exception_type") is None and trace.get("exception_hresult") is None,
            trace.get("raw_document_text_present") is False,
            trace.get("user_document_scanned") is False,
            trace.get("external_network_invoked") is False,
            trace.get("registry_or_system_setting_changed") is False,
            trace.get("computer_use_click_or_type_invoked") is False,
            trace.get("window_visible_for_user_access") is True,
            trace.get("delegated_engine_schema")
            == "hwpx-agent.p05-04-hancom-2020-tab-readback/v1",
            watchdog == {
                "timeout_seconds": 900,
                "timed_out": False,
                "child_exit_code": 0,
                "output_drained": True,
                "cleaned_process_count": 0,
                "cleanup_refused_count": 0,
                "cleanup_error_count": 0,
                "remaining_hwp_process_count": 0,
                "progress_present": True,
                "progress_valid": True,
                "progress_event_count": 21,
                "progress_last_phase": "terminal",
                "progress_last_state": "pass",
                "progress_observed_phase": "quit",
                "window_visible_for_user_access": True,
            },
        )
        if not all(checks):
            raise ValueError("trace")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("trace_semantics")


def read_jsonl(root: Path, relative: str) -> list[dict[str, Any]]:
    text = bounded_bytes(root, relative, 256_000).decode("utf-8")
    lines = text.splitlines()
    return [load_json(line.encode("utf-8")) for line in lines]


def validate_progress(root: Path, errors: list[str]) -> None:
    expected = [
        (1, "preflight", "pass"), (2, "com_create", "pass"),
        (3, "open_input", "running"), (4, "open_input", "pass"),
        (5, "read_input", "running"), (6, "read_input", "pass"),
        (7, "save_as_hwpx", "running"), (8, "save_as_hwpx", "pass"),
        (9, "close_input", "running"), (10, "close_input", "pass"),
        (11, "reopen_output", "running"), (12, "reopen_output", "pass"),
        (13, "read_output", "running"), (14, "read_output", "pass"),
        (15, "export_pdf", "running"), (16, "export_pdf", "pass"),
        (17, "close_output", "running"), (18, "close_output", "pass"),
        (19, "quit", "running"), (20, "quit", "pass"),
        (21, "terminal", "pass"),
    ]
    try:
        events = read_jsonl(root, PROGRESS_PATH)
        actual = [(item.get("sequence"), item.get("phase"), item.get("state"))
                  for item in events]
        if actual != expected or any(
            item.get("schema_version") != "hwpx-agent.p05-hancom-readback-progress/v1"
            or item.get("raw_document_text_present") is not False for item in events
        ):
            raise ValueError("progress")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("progress_semantics")


def validate_pdf(root: Path, errors: list[str]) -> None:
    try:
        data = bounded_bytes(root, PDF_PATH, 8 * 1024 * 1024)
        if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:] \
                or not re.search(rb"/Type\s*/Pages\b", data) \
                or not re.search(rb"/Count\s+1\b", data) or b"/JavaScript" in data:
            raise ValueError("pdf")
    except (OSError, ValueError):
        errors.append("pdf_semantics")


def validate_markers(root: Path, errors: list[str]) -> int:
    count = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = bounded_bytes(root, relative, 4 * 1024 * 1024).decode("utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path_or_encoding")
            continue
        count += 1
        if any(marker not in source for marker in markers):
            errors.append("implementation_markers")
    return count


def result(errors: list[str], source_locks: int, evidence_files: int,
           implementation_files: int, predecessor_state: str) -> dict[str, Any]:
    state = "pass" if not errors else "fail"
    return {
        "schema_version": "hwpx-agent.p06-06-table-formula-target-validation/v2",
        "state": state,
        "errors": errors,
        "source_locks": source_locks,
        "evidence_files": evidence_files,
        "implementation_files": implementation_files,
        "predecessor": predecessor_state,
        "row_column_structural_differential": "pass" if state == "pass" else "not_proven",
        "product_target_oracle": "pass" if state == "pass" else "not_proven",
        "p06_06": "pass" if state == "pass" else "not_proven",
        "p06": "in_progress",
    }


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_FORMULA_TARGET_V2_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"evidence_files={report['evidence_files']} "
        f"implementation_files={report['implementation_files']}"
    )
