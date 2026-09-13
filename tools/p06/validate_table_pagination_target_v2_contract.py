#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from tools.p06 import validate_table_pagination_hwpx_contract as predecessor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-pagination-target-v2.json"
REPORT = "implementation/p06/P06-07_TARGET_READBACK_REPORT.md"
DIAGNOSTIC = "implementation/p06/P06-07_TARGET_ATTEMPTS_DIAGNOSTIC.md"
MIGRATION = "protocol/migrations/p06-table-pagination-hwpx-v1-to-target-v2.md"
TARGET_DIRECTORY = "fixtures/target-build/p06-07-table-pagination-target-20260909-04"
SOURCE_PATH = (
    "fixtures/target-build/p06-05-table-layout-20260907-05/"
    "target-readback-output-01.hwpx"
)
TARGET_PATH = f"{TARGET_DIRECTORY}/target.hwpx"
OUTPUT_PATH = f"{TARGET_DIRECTORY}/target-readback-output-01.hwpx"
PDF_PATH = f"{TARGET_DIRECTORY}/target-readback-output-01.pdf"
TRACE_PATH = f"{TARGET_DIRECTORY}/target-readback-trace-01.json"
PROGRESS_PATH = f"{TRACE_PATH}.progress.jsonl"
VISUAL_RECEIPT_PATH = f"{TARGET_DIRECTORY}/target-readback-pdf-visual-oracle-01.json"

SOURCE_SHA256 = "ec08dc8e07dfc1b18c5916b44917b00d27da9905bea26f57e9b16991396c1ec7"
TARGET_SHA256 = "44cfcd14d867e6b53f4a015061666fe3b9ac990d3b3c321faae863d172fe8316"
OUTPUT_SHA256 = "8e32f37df5af2b8aaee70cbd0c5cbed30150528f2022952c4dbb012fd58106ed"
PDF_SHA256 = "249ad3e14716b9a55898c03ae424a34419cfbb7db8a2d3ab12ad7b362d70da1a"
TEXT_SHA256 = "19e2e32f32ce5238e72ffafdca368a7ebba92bb60b9ed514a40719305b5a8855"
TARGET_SECTION_SHA256 = (
    "e252881632e066080d9fd3db2b97f630f80c34201e8033815311ff5df8bc00f1"
)
OUTPUT_SECTION_SHA256 = (
    "62059a8ad174e39863e24ab381bfd9dbd1ac62b2b773617b0f85afd529d63788"
)

SOURCE_LOCKS = {
    "protocol/private/p06-table-pagination-hwpx-v1.json":
        "2120fd97b4cf969d1c9fb2ce0be349ddc45eb27aac2c278e7d7b4b7c95f3c603",
    "tools/p06/validate_table_pagination_hwpx_contract.py":
        "0c930dcf7df061d944d614d623a7be3f2831d612b53588a79c8b08155fddd12a",
    "crates/hwpx-package/src/table_pagination.rs":
        "d667a4e34248379c6139ac62d1e0b385541d6dd959aeb8444b143077c6578e04",
    "crates/hwpx-package/examples/p06_07_table_pagination_target_fixture.rs":
        "2772ec0953b2fe188b3ef4f302522e9ffc0c3f33a769d90f67b8b1647fdfe2a0",
    "crates/hwpx-package/examples/p06_07_table_pagination_target_oracle.rs":
        "9df4d0eaebe9f19d6e5a449a76ee498d359b8ada28a1ea9539428c8d6016cb5c",
    "implementation/p05/tools/invoke-hancom-2020-bounded-readback.ps1":
        "f13474940e14754a483409d428c814c2c05c6ca9428143aff73337a82f5fcf18",
    "implementation/p05/tools/run-hancom-2020-tab-readback.ps1":
        "e27582f85f2fd17824b9c8afd8b3cda922a448590104982266fc5b7f6bcd6d72",
    "implementation/p06/tools/run-hancom-2020-table-pagination-target-readback.ps1":
        "3e03680e2dd3b7138da9d31aa25df33a3672e9c37bc63536fa7559fdb8757c55",
    "implementation/p06/tests/Test-Hancom2020TablePaginationReadback.ps1":
        "82e707a342412142b58617d8a077d003dc4ced0a13e8d0c30796f9453b911c1e",
    DIAGNOSTIC:
        "6e9d7c52321c127eb6f90e286e28a3ef7e860ae01617972eac3cd7353b543425",
}

HISTORICAL_EVIDENCE = {
    "fixtures/target-build/p06-07-table-pagination-target-20260908-01/calibration-trace-01.json":
        ("32d77c11e2e0e2ae1590b48ae2c4d085f2883756914dbb38219fa595099b7de7", 2247),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-01/calibration-trace-01.json.progress.jsonl":
        ("d69c6d80fece8297d16e9abe579135e6f92b5023954e219092a8a876f0013025", 1720),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-01/target-readback-output-02.hwpx":
        ("6dc4e4c8e99c2ddc1c92ee4f5e05e66ec121f2fde59f6a765cd90de726c6d251", 48172),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-01/target-readback-output-02.pdf":
        ("20fc6eca4179bfb869fe7c685fd18b2447729f99cfbe653c0b708676415c6826", 34128),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-01/target-readback-trace-01.json":
        ("d0648416b0622fbaff546f7e33f71e9d272ff43b9d013a4dbea3aee3050203d4", 1460),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-01/target-readback-trace-01.json.progress.jsonl":
        ("4e329a34c47db2b2a3be2af3cbe76cd7aa97cf45ef8e9c979513ba6509a9dfa3", 735),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-01/target-readback-trace-02.json":
        ("f71daabfcf41b46f0fc69d8e2dd01d45910a8022db1dd7615b1f3bf0cf65e442", 2322),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-01/target-readback-trace-02.json.progress.jsonl":
        ("83419e1176fcc55c2634ffe14732c0df03502af5efb88c1a05d97fa66bc84d8e", 5164),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-01/target.hwpx":
        ("2f20e831ef8b23df9470762f6d8f70a0859a20cde38e262fba6b2add1ea3848d", 16692),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-02/calibration-trace-01.json":
        ("a6e1fd33475ed9a81fdf268027b8141df0505ecf4cebff4514991d52b09840e7", 1461),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-02/calibration-trace-01.json.progress.jsonl":
        ("a0b8e49469795a8ac1152f3a543f66522ced98b5fd4505a702007b593b7adf4a", 735),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-02/target-readback-trace-01.json":
        ("6118707060ac91b518797e793dd9da970c08bf6beb949dd1ab921ecde7ae4a80", 1460),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-02/target-readback-trace-01.json.progress.jsonl":
        ("7b053528a48968a1234001f0b8bf9d9b5d89153d4311f28e4fcee460eeb10419", 735),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-02/target.hwpx":
        ("98aab83ffb874c32cd339cbf4aa8966f20d36a02dedd9b05e23bbf1888d9eb33", 17084),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-02/text-calibration-trace-02.json":
        ("81e32cafd8b388e7ce060e3724ba66115782482c84ef78cc6060d18cb8fbeb82", 2247),
    "fixtures/target-build/p06-07-table-pagination-target-20260908-02/text-calibration-trace-02.json.progress.jsonl":
        ("5311ece306889455254b710481864aedfba53fe70886d76ad9e31c1c1b18244a", 1720),
    "fixtures/target-build/p06-07-table-pagination-target-20260909-03/target-readback-output-01.hwpx":
        ("3b46ba1b4f4484cc77190276cef9d6724f1982b3a8206b9960e3f585eab5b9f5", 49077),
    "fixtures/target-build/p06-07-table-pagination-target-20260909-03/target-readback-output-01.pdf":
        ("b38fbb2489a3d15f7033e676b032ed285a3d97a64c831b15707211b7df2114f1", 28225),
    "fixtures/target-build/p06-07-table-pagination-target-20260909-03/target-readback-trace-01.json":
        ("19c8daded887303198a6cfe5554af29dbd2a9ee036b9742b176a955c020f1708", 2322),
    "fixtures/target-build/p06-07-table-pagination-target-20260909-03/target-readback-trace-01.json.progress.jsonl":
        ("9350c5a338988a1716dfca010d39d81c2e10c2f18e9a2ee70a75fa05d7cb593d", 5185),
    "fixtures/target-build/p06-07-table-pagination-target-20260909-03/target.hwpx":
        ("98aab83ffb874c32cd339cbf4aa8966f20d36a02dedd9b05e23bbf1888d9eb33", 17084),
}

PAGE_EVIDENCE = (
    (1, "bdd6583c9ef98193449b562c7027ae43dbb54936209f4333809485f9aee93173", 142644),
    (2, "84fab442c7fe10e0ccf473c738274d74bf903a72f7563e1f87e88880ff9439c9", 147860),
    (3, "63993346024ccb7e2a4df40f6eefe59e127da11823837c31f76c7575e13b0e76", 149418),
    (4, "6019c957beaeb5916f668a87807035cb284bebc7e42c7587bcea92ad7dba1244", 58799),
    (5, "c27b4c325e82d8671f017f71d76193cc7411904dead821ca4b725b5c07214dd8", 156473),
    (6, "fda267b85f84a65906826a470a2a78f39abe3059dcedc1fdbe00b124f020eabb", 59887),
    (7, "fdd581e46fde6f39ce9e255d7bddf43121abf3ad589d524b55cae4d5e33c958c", 159305),
    (8, "0d80255b953313283cf8798563b2c473042993ae824b986ab28d74ff507f910d", 170954),
    (9, "90b8ceabd96b006cdec1e7990a9c8f0836572472bcee8ea6d3ab12496222647e", 147553),
    (10, "82bb22056fd12a0c1268303ef05eec7e99277040e4804fd9d7e7b1b06a47d9d0", 17736),
)

EVIDENCE = {
    SOURCE_PATH: (SOURCE_SHA256, 16110),
    TARGET_PATH: (TARGET_SHA256, 17171),
    OUTPUT_PATH: (OUTPUT_SHA256, 44597),
    PDF_PATH: (PDF_SHA256, 38042),
    TRACE_PATH: ("31468f372d89810c096514265fc6b7be91fdf3f1e4b5b5dcc8d9d50a19ac58ca", 2322),
    PROGRESS_PATH: ("0d8a49fb5c63b95f713166ed78a5b57529c1c3c036c1fe6c2acf5df5f8dc083b", 5185),
    VISUAL_RECEIPT_PATH: ("295083fab3436471134e5363a523042d76642949651755d71d66033f1b32ebdc", 5435),
    **HISTORICAL_EVIDENCE,
    **{
        f"{TARGET_DIRECTORY}/rendered/page-{page:02}.png": (digest, size)
        for page, digest, size in PAGE_EVIDENCE
    },
}

IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/examples/p06_07_table_pagination_target_fixture.rs": (
        "treat_as_char: bool",
        "u8::from(treat_as_char)",
        "table(id, 1, 1, 2_000, true, None, &row)",
        "write_create_new",
    ),
    "crates/hwpx-package/examples/p06_07_table_pagination_target_oracle.rs": (
        TARGET_SHA256,
        "target has stale line caches",
        "readback has no renderer-produced line cache",
    ),
    "implementation/p06/tools/run-hancom-2020-table-pagination-target-readback.ps1": (
        "hwpx-agent.p06-07-hancom-2020-table-pagination-readback/v1",
        "TABLE_PAGINATION_READBACK",
        "invoke-hancom-2020-bounded-readback.ps1",
    ),
    "implementation/p06/tests/Test-Hancom2020TablePaginationReadback.ps1": (
        "all_scripts_parse",
        "no_ui_input",
        "no_network",
        "no_registry_write",
    ),
    REPORT: (
        "PASS for the exact current-PC Hangul 2020 P06-07 target",
        TARGET_SHA256,
        OUTPUT_SHA256,
        PDF_SHA256,
        "P06-07 is complete",
    ),
    DIAGNOSTIC: (
        "lifecycle PASS, renderer layout FAIL",
        "treatAsChar=\"1\"",
        "does not modify or erase any attempt",
    ),
    MIGRATION: (
        "There is no automatic migration",
        "five top-level tables use native `treatAsChar=0`",
        "separate versioned evidence",
    ),
}

PACKAGE_PARTS = {
    "mimetype", "version.xml", "Contents/header.xml", "Contents/section0.xml",
    "Preview/PrvText.txt", "settings.xml", "Preview/PrvImage.png",
    "META-INF/container.rdf", "Contents/content.hpf", "META-INF/container.xml",
    "META-INF/manifest.xml",
}
UNCHANGED_PARTS = {
    "mimetype", "version.xml", "settings.xml", "META-INF/container.rdf",
    "META-INF/container.xml", "META-INF/manifest.xml",
}
TARGET_PREVIEW = (
    b"P06-07 ALLOW TOP\r\n"
    b"P06-07 A HEADER 1\tP06-07 A HEADER 2\r\n"
    b"P06-07 A LONG CELL 001..064\r\n"
    b"P06-07 AVOID-ROW BOTTOM\r\n"
    b"P06-07 B MERGED\r\n"
    b"P06-07 B NESTED\r\n"
    b"P06-07 B EQUATION\r\n"
    b"P06-07 BEFORE\r\nP06-07 EXACT\r\nP06-07 AFTER\r\n\r\n"
)
HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
HH = "http://www.hancom.co.kr/hwpml/2011/head"
OPF = "http://www.idpf.org/2007/opf/"


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("duplicate JSON key")
        output[key] = value
    return output


def safe_path(root: Path, relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or "\\" in relative:
        raise ValueError("unsafe path")
    path = (root / Path(*candidate.parts)).resolve()
    if root.resolve() not in path.parents:
        raise ValueError("outside root")
    return path


def bounded_bytes(root: Path, relative: str, limit: int = 8 * 1024 * 1024) -> bytes:
    path = safe_path(root, relative)
    size = path.stat().st_size
    if size <= 0 or size > limit:
        raise ValueError("file size")
    data = path.read_bytes()
    if len(data) != size:
        raise ValueError("file changed while reading")
    return data


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_pairs)


def tag(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json(bounded_bytes(root, CONTRACT, 512_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0, "not_proven")
    validate_contract(contract, errors)
    predecessor_state = validate_predecessor(root, errors)
    source_count = validate_source_locks(root, contract, errors)
    evidence_count = validate_evidence(root, errors)
    validate_target_and_oracle(root, errors)
    validate_trace(root, errors)
    validate_progress(root, errors)
    validate_pdf_and_visual_receipt(root, errors)
    implementation_count = validate_markers(root, errors)
    return result(
        sorted(set(errors)), source_count, evidence_count, implementation_count,
        predecessor_state,
    )


def validate_contract(contract: dict[str, Any], errors: list[str]) -> None:
    expected_keys = {
        "schema_version", "model_schema_version", "observation_schema_version",
        "adapter_profile_id", "scope", "predecessor", "prerequisites",
        "source_lock_canonicalization", "source_locks", "exact_source",
        "structural_target", "historical_attempts", "actual_oracle", "gate_decision",
        "failure_policy", "migration", "report", "not_claimed",
    }
    if set(contract) != expected_keys:
        errors.append("contract_shape")
    exact = {
        "schema_version": "hwpx-agent.p06-07-table-pagination-target-contract/v2",
        "model_schema_version": "hwpx-agent.table-pagination/v1",
        "observation_schema_version": "hwpx-agent.table-pagination-observation/v1",
        "adapter_profile_id": "hwpx-agent.table-pagination-hwpx.hancom-2020/1",
        "scope": "p06_07_exact_current_pc_hancom_2020_target_and_external_pdf_oracle",
        "source_lock_canonicalization": "exact_file_bytes_sha256",
        "migration": MIGRATION,
        "report": REPORT,
    }
    for key, value in exact.items():
        if contract.get(key) != value:
            errors.append(key)
    if contract.get("predecessor") != {
        "path": "protocol/private/p06-table-pagination-hwpx-v1.json",
        "sha256": SOURCE_LOCKS["protocol/private/p06-table-pagination-hwpx-v1.json"],
        "state": "immutable_static_hwpx_adapter_component_contract",
    }:
        errors.append("predecessor")
    if contract.get("prerequisites") != [
        "hwpx-agent.p06-07-table-pagination-hwpx-contract/v1",
        "hwpx-agent.table-pagination/v1",
        "hwpx-agent.table-pagination-observation/v1",
        "hwpx-agent.table-pagination-hwpx.hancom-2020/1",
        "exact_licensed_current_pc_hancom_2020_11.0.0.9136",
    ]:
        errors.append("prerequisites")
    if contract.get("exact_source") != {
        "path": SOURCE_PATH, "sha256": SOURCE_SHA256, "bytes": 16110,
        "state": "immutable_exact_current_pc_hancom_2020_layout_output",
    }:
        errors.append("exact_source")
    validate_contract_target(contract.get("structural_target"), errors)
    validate_contract_history(contract.get("historical_attempts"), errors)
    validate_contract_oracle(contract.get("actual_oracle"), errors)
    if contract.get("gate_decision") != {
        "pure_pagination_validator": "pass",
        "static_hwpx_adapter_component": "pass",
        "actual_hancom_2020_boundary_page_suite": "pass",
        "actual_hancom_2020_save_reopen_pdf_oracle": "pass",
        "p06_07": "pass",
        "p06": "in_progress",
    }:
        errors.append("gate_decision")
    not_claimed = contract.get("not_claimed")
    expected_not_claimed = {
        "arbitrary_user_document_compatibility", "caption_creation_or_removal",
        "left_or_right_caption", "other_pc_or_hancom_version",
        "full_table_matrix_green", "p06_complete", "production", "product_complete",
    }
    if not isinstance(not_claimed, dict) or set(not_claimed) != expected_not_claimed \
            or set(not_claimed.values()) != {False}:
        errors.append("not_claimed")


def validate_contract_target(value: Any, errors: list[str]) -> None:
    expected = {
        "execution_base_commit": "2f04480", "directory": TARGET_DIRECTORY,
        "path": TARGET_PATH, "sha256": TARGET_SHA256, "bytes": 17171,
        "write_mode": "create_new", "package_parts": 11,
        "section_sha256": TARGET_SECTION_SHA256, "visible_text_sha256": TEXT_SHA256,
        "top_level_tables": 5, "nested_tables": 1, "captions": 5,
        "equation_objects": 1, "renderer_line_caches": 0,
        "top_level_treat_as_char": False, "nested_treat_as_char": True,
        "native_page_breaks": ["CELL", "TABLE", "NONE", "NONE", "NONE"],
        "repeat_header_prefixes": [1, 1, 1, 1, 1],
        "boundary_filler_lines": [34, 35, 36],
    }
    if value != expected:
        errors.append("structural_target")


def validate_contract_history(value: Any, errors: list[str]) -> None:
    expected = {
        "directories": [
            "fixtures/target-build/p06-07-table-pagination-target-20260908-01",
            "fixtures/target-build/p06-07-table-pagination-target-20260908-02",
            "fixtures/target-build/p06-07-table-pagination-target-20260909-03",
        ],
        "evidence_files": 21, "access_timeout_or_calibration_only": 4,
        "lifecycle_pass_visual_fail": 2, "promoted_to_pass": 0,
        "decision": "immutable_failed_or_superseded_evidence",
    }
    if value != expected:
        errors.append("historical_attempts")


def validate_contract_oracle(value: Any, errors: list[str]) -> None:
    expected = {
        "output_hwpx_path": OUTPUT_PATH, "output_hwpx_sha256": OUTPUT_SHA256,
        "output_hwpx_bytes": 44597, "output_section_sha256": OUTPUT_SECTION_SHA256,
        "renderer_line_caches": 115, "trace_path": TRACE_PATH,
        "trace_sha256": EVIDENCE[TRACE_PATH][0], "trace_bytes": 2322,
        "progress_path": PROGRESS_PATH, "progress_sha256": EVIDENCE[PROGRESS_PATH][0],
        "progress_bytes": 5185, "output_pdf_path": PDF_PATH,
        "output_pdf_sha256": PDF_SHA256, "output_pdf_bytes": 38042,
        "pdf_page_count": 10, "visual_receipt_path": VISUAL_RECEIPT_PATH,
        "visual_receipt_sha256": EVIDENCE[VISUAL_RECEIPT_PATH][0],
        "visual_receipt_bytes": 5435, "rendered_png_files": 10,
        "rendered_dpi": 144, "page_pixel_size": [1190, 1682],
        "hancom_file_version": "11.0.0.9136",
        "hancom_executable_sha256":
            "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        "save_reopen_pass": True, "input_unchanged": True,
        "visible_text_preserved": True, "repeat_header_pages": [2, 3, 4, 6],
        "caption_pages": {
            "allow_top": 1, "avoid_row_bottom": 6, "before_top": 7,
            "exact_top": 8, "after_bottom": 10,
        },
        "boundary_result": {
            "before": "same_page", "exact": "same_page", "after": "next_page",
        },
        "blank_pages": [], "outside_page_glyphs": 0,
        "remaining_hwp_process_count": 0,
        "computer_use_click_or_type_invoked": False,
        "section_normalization":
            "115_line_caches_two_paginated_table_heights_nested_width_and_two_empty_text_sentinels_only",
        "header_normalization":
            "unused_para_property_ids_20_21_removed_item_count_22_to_20",
        "content_hpf_normalization": "modified_time_and_spine_linear_values_only",
        "unchanged_package_parts": 6,
    }
    if value != expected:
        errors.append("actual_oracle")


def validate_predecessor(root: Path, errors: list[str]) -> str:
    report = predecessor.validate(root)
    if report.get("state") != "pass" \
            or report.get("actual_hancom_2020_boundary_page_suite") != "not_run" \
            or report.get("p06_07") != "in_progress":
        errors.append("predecessor_validation")
        return "not_proven"
    return "pass"


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
            if sha256(bounded_bytes(root, path, 4 * 1024 * 1024)) != digest:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_path_or_encoding")
    if actual != SOURCE_LOCKS:
        errors.append("source_locks_exact")
    return len(actual)


def validate_evidence(root: Path, errors: list[str]) -> int:
    for path, (digest, size) in EVIDENCE.items():
        try:
            data = bounded_bytes(root, path)
            if len(data) != size or sha256(data) != digest:
                errors.append("evidence_digest")
        except (OSError, ValueError):
            errors.append("evidence_path_or_size")
    return len(EVIDENCE)


def zip_payloads(data: bytes) -> dict[str, bytes]:
    from io import BytesIO

    output: dict[str, bytes] = {}
    with zipfile.ZipFile(BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) != 11 or entries[0].filename != "mimetype" \
                or entries[0].compress_type != zipfile.ZIP_STORED:
            raise ValueError("zip entry shape")
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or ".." in path.parts or entry.is_dir() \
                    or entry.filename in output or entry.file_size > 4 * 1024 * 1024:
                raise ValueError("unsafe zip entry")
            output[entry.filename] = archive.read(entry)
    if set(output) != PACKAGE_PARTS:
        raise ValueError("package parts")
    return output


def validate_target_and_oracle(root: Path, errors: list[str]) -> None:
    try:
        target = zip_payloads(bounded_bytes(root, TARGET_PATH))
        oracle = zip_payloads(bounded_bytes(root, OUTPUT_PATH))
        if any(target[name] != oracle[name] for name in UNCHANGED_PARTS):
            raise ValueError("unchanged parts")
        changed = {name for name in PACKAGE_PARTS if target[name] != oracle[name]}
        if changed != PACKAGE_PARTS - UNCHANGED_PARTS:
            raise ValueError("changed parts")
        if target["Preview/PrvText.txt"] != TARGET_PREVIEW \
                or sha256(oracle["Preview/PrvText.txt"]) \
                != "03efe81b44b2ab185a2d04f3b00a2c846ce9b7211a6c1da6ce1c50cb3dc6fa9a" \
                or not target["Preview/PrvImage.png"].startswith(b"\x89PNG\r\n\x1a\n") \
                or not oracle["Preview/PrvImage.png"].startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("preview")
        target_section = target["Contents/section0.xml"]
        oracle_section = oracle["Contents/section0.xml"]
        if sha256(target_section) != TARGET_SECTION_SHA256 \
                or sha256(oracle_section) != OUTPUT_SECTION_SHA256:
            raise ValueError("section digest")
        validate_table_section(target_section, False)
        validate_table_section(oracle_section, True)
        if normalize_oracle_section(oracle_section) != target_section:
            raise ValueError("section normalization")
        validate_header_relation(target["Contents/header.xml"], oracle["Contents/header.xml"])
        validate_content_relation(target["Contents/content.hpf"], oracle["Contents/content.hpf"])
    except (OSError, KeyError, TypeError, ValueError, ET.ParseError, zipfile.BadZipFile):
        errors.append("target_oracle_hwpx_semantics")


def direct_child(element: ET.Element, local: str) -> ET.Element:
    values = [child for child in element if child.tag == tag(HP, local)]
    if len(values) != 1:
        raise ValueError(f"direct child {local}")
    return values[0]


def element_text(element: ET.Element) -> str:
    return "".join((item.text or "") for item in element.iter(tag(HP, "t")))


def validate_table_section(section: bytes, oracle: bool) -> None:
    root = ET.fromstring(section)
    if sum(1 for _ in root.iter()) > 100_000:
        raise ValueError("element limit")
    tables = list(root.iter(tag(HP, "tbl")))
    ids = [item.get("id") for item in tables]
    expected_ids = [str(2_100_000_000 + value) for value in range(1, 7)]
    if ids != expected_ids:
        raise ValueError("table ids")
    expected = {
        expected_ids[0]: ("CELL", "1", "2", "2", "0", "TOP", "P06-07 ALLOW TOP"),
        expected_ids[1]: ("TABLE", "1", "34", "2", "0", "BOTTOM", "P06-07 AVOID-ROW BOTTOM"),
        expected_ids[2]: ("NONE", "0", "1", "1", "1", None, None),
        expected_ids[3]: ("NONE", "1", "2", "1", "0", "TOP", "P06-07 BEFORE"),
        expected_ids[4]: ("NONE", "1", "2", "1", "0", "TOP", "P06-07 EXACT"),
        expected_ids[5]: ("NONE", "1", "2", "1", "0", "BOTTOM", "P06-07 AFTER"),
    }
    for table in tables:
        page_break, repeat, rows, columns, treat, caption_side, caption_text = expected[
            table.get("id", "")
        ]
        if (table.get("pageBreak"), table.get("repeatHeader"), table.get("rowCnt"),
                table.get("colCnt")) != (page_break, repeat, rows, columns):
            raise ValueError("table policy")
        if direct_child(table, "pos").get("treatAsChar") != treat:
            raise ValueError("treat as char")
        captions = [child for child in table if child.tag == tag(HP, "caption")]
        if caption_side is None:
            if captions:
                raise ValueError("caption absent")
        elif len(captions) != 1 or captions[0].get("side") != caption_side \
                or element_text(captions[0]) != caption_text:
            raise ValueError("caption")
        row_elements = [child for child in table if child.tag == tag(HP, "tr")]
        if len(row_elements) != int(rows):
            raise ValueError("row count")
        first_cells = [child for child in row_elements[0] if child.tag == tag(HP, "tc")]
        expected_header = "1" if repeat == "1" else "0"
        if not first_cells or any(cell.get("header") != expected_header for cell in first_cells):
            raise ValueError("header row")
        if any(cell.get("header") != "0" for row in row_elements[1:]
               for cell in row if cell.tag == tag(HP, "tc")):
            raise ValueError("body header")
    size_by_id = {table.get("id"): direct_child(table, "sz") for table in tables}
    heights = (
        ("61764", "61264") if oracle else ("2700", "86400")
    )
    if size_by_id[expected_ids[0]].get("height") != heights[0] \
            or size_by_id[expected_ids[1]].get("height") != heights[1] \
            or size_by_id[expected_ids[2]].get("width") != ("15000" if oracle else "19843"):
        raise ValueError("renderer geometry")
    text = section.decode("utf-8")
    marker_counts = {
        "P06-07 A LONG CELL": 64, "P06-07 B MERGED": 18,
        "P06-07 B ROW": 30, "P06-07 B NESTED": 1,
        "P06-07 NESTED TABLE CELL": 1, "P06-07 B EQUATION": 1,
        "P06-07 BEFORE PAGE START": 1, "P06-07 EXACT PAGE START": 1,
        "P06-07 AFTER PAGE START": 1,
    }
    if any(text.count(marker) != count for marker, count in marker_counts.items()):
        raise ValueError("markers")
    caches = list(root.iter(tag(HP, "linesegarray")))
    if len(caches) != (115 if oracle else 0):
        raise ValueError("line cache count")


def replace_once(data: bytes, old: bytes, new: bytes) -> bytes:
    if data.count(old) != 1:
        raise ValueError("normalization cardinality")
    return data.replace(old, new, 1)


def normalize_oracle_section(section: bytes) -> bytes:
    stripped, count = re.subn(
        rb"<hp:linesegarray>.*?</hp:linesegarray>", b"", section, flags=re.DOTALL
    )
    if count != 115 or b"<hp:linesegarray" in stripped:
        raise ValueError("cache strip")
    stripped = replace_once(stripped, b'height="61764"', b'height="2700"')
    stripped = replace_once(stripped, b'height="61264"', b'height="86400"')
    stripped = replace_once(
        stripped,
        b'<hp:sz width="15000" widthRelTo="ABSOLUTE" height="2000"',
        b'<hp:sz width="19843" widthRelTo="ABSOLUTE" height="2000"',
    )
    stripped = replace_once(
        stripped,
        b'</hp:tbl><hp:t/></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="0" rowAddr="32"',
        b'</hp:tbl></hp:run></hp:p></hp:subList><hp:cellAddr colAddr="0" rowAddr="32"',
    )
    return replace_once(
        stripped, b"</hp:equation><hp:t/></hp:run>", b"</hp:equation></hp:run>"
    )


def element_signature(element: ET.Element) -> tuple[Any, ...]:
    return (
        element.tag, tuple(sorted(element.attrib.items())), element.text or "",
        element.tail or "", tuple(element_signature(child) for child in element),
    )


def validate_header_relation(target: bytes, oracle: bytes) -> None:
    left = ET.fromstring(target)
    right = ET.fromstring(oracle)
    properties = list(left.iter(tag(HH, "paraProperties")))
    if len(properties) != 1 or properties[0].get("itemCnt") != "22":
        raise ValueError("target para properties")
    removed: list[str] = []
    for parent in left.iter():
        for child in list(parent):
            if child.tag == tag(HH, "paraPr") and child.get("id") in {"20", "21"}:
                removed.append(child.get("id", ""))
                parent.remove(child)
    properties[0].set("itemCnt", "20")
    if sorted(removed) != ["20", "21"] or element_signature(left) != element_signature(right):
        raise ValueError("header normalization")


def validate_content_relation(target: bytes, oracle: bytes) -> None:
    left = ET.fromstring(target)
    right = ET.fromstring(oracle)
    left_modified = [item for item in left.iter(tag(OPF, "meta"))
                     if item.get("name") == "ModifiedDate"]
    right_modified = [item for item in right.iter(tag(OPF, "meta"))
                      if item.get("name") == "ModifiedDate"]
    left_refs = {item.get("idref"): item for item in left.iter(tag(OPF, "itemref"))}
    right_refs = {item.get("idref"): item for item in right.iter(tag(OPF, "itemref"))}
    if len(left_modified) != 1 or len(right_modified) != 1 \
            or (left_modified[0].text or "") != "2026-09-07T09:46:31Z" \
            or (right_modified[0].text or "") != "2026-09-08T15:58:02Z" \
            or left_refs.get("header") is None or right_refs.get("header") is None \
            or left_refs.get("section0") is None or right_refs.get("section0") is None \
            or left_refs["header"].get("linear") != "yes" \
            or left_refs["section0"].get("linear") is not None \
            or right_refs["header"].get("linear") != "no" \
            or right_refs["section0"].get("linear") != "yes":
        raise ValueError("content expected normalization")
    left_modified[0].text = right_modified[0].text
    left_refs["header"].set("linear", "no")
    left_refs["section0"].set("linear", "yes")
    if element_signature(left) != element_signature(right):
        raise ValueError("content normalization")


def validate_trace(root: Path, errors: list[str]) -> None:
    try:
        trace = load_json(bounded_bytes(root, TRACE_PATH, 256_000))
        expected_target = {
            "prog_id": "HWPFrame.HwpObject.2", "registry_view": "Registry32",
            "client": "windows_powershell_x86_sta", "file_version": "11.0.0.9136",
            "executable_sha256":
                "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        }
        expected_phases = {
            "com_create": "pass", "open_input": "pass", "read_input": "pass",
            "save_as_hwpx": "pass", "close_input": "pass", "reopen_output": "pass",
            "read_output": "pass", "export_pdf": "pass", "close_output": "pass",
            "quit": "pass",
        }
        expected_watchdog = {
            "timeout_seconds": 900, "timed_out": False, "child_exit_code": 0,
            "output_drained": True, "cleaned_process_count": 0,
            "cleanup_refused_count": 0, "cleanup_error_count": 0,
            "remaining_hwp_process_count": 0, "progress_present": True,
            "progress_valid": True, "progress_event_count": 21,
            "progress_last_phase": "terminal", "progress_last_state": "pass",
            "progress_observed_phase": "quit", "window_visible_for_user_access": True,
        }
        checks = (
            trace.get("schema_version")
            == "hwpx-agent.p06-07-hancom-2020-table-pagination-readback/v1",
            trace.get("state") == "pass", trace.get("target") == expected_target,
            trace.get("input_sha256") == TARGET_SHA256,
            trace.get("output_sha256") == OUTPUT_SHA256,
            trace.get("input_text_sha256") == TEXT_SHA256,
            trace.get("output_text_sha256") == TEXT_SHA256,
            trace.get("input_unchanged") is True, trace.get("output_saved") is True,
            trace.get("render_pdf_requested") is True,
            trace.get("render_pdf_saved") is True,
            trace.get("render_pdf_sha256") == PDF_SHA256,
            trace.get("render_pdf_bytes") == 38042,
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
            trace.get("watchdog") == expected_watchdog,
        )
        if not all(checks):
            raise ValueError("trace")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("trace_semantics")


def read_jsonl(root: Path, relative: str) -> list[dict[str, Any]]:
    text = bounded_bytes(root, relative, 256_000).decode("utf-8")
    return [load_json(line.encode("utf-8")) for line in text.splitlines()]


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


def validate_pdf_and_visual_receipt(root: Path, errors: list[str]) -> None:
    try:
        pdf = bounded_bytes(root, PDF_PATH)
        if not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1024:] \
                or not re.search(rb"/Type\s*/Pages\b", pdf) \
                or re.findall(rb"/Count\s+(\d+)\b", pdf) != [b"10"] \
                or b"/JavaScript" in pdf or b"/Encrypt" in pdf:
            raise ValueError("pdf")
        receipt = load_json(bounded_bytes(root, VISUAL_RECEIPT_PATH, 128_000))
        if receipt.get("schema_version") \
                != "hwpx-agent.p06-07-table-pagination-pdf-visual-oracle/v1" \
                or receipt.get("state") != "pass" \
                or receipt.get("scope") != "exact_current_pc_hancom_2020_11.0.0.9136_pdf":
            raise ValueError("receipt identity")
        pdf_record = receipt.get("pdf", {})
        if pdf_record.get("path") != PDF_PATH or pdf_record.get("sha256") != PDF_SHA256 \
                or pdf_record.get("bytes") != 38042 or pdf_record.get("pages") != 10 \
                or pdf_record.get("page_size_points") != [595, 841] \
                or pdf_record.get("encrypted") is not False \
                or pdf_record.get("javascript") is not False:
            raise ValueError("receipt pdf")
        render = receipt.get("render", {})
        expected_pages = [
            {
                "page": page,
                "path": f"{TARGET_DIRECTORY}/rendered/page-{page:02}.png",
                "sha256": digest,
                "bytes": size,
            }
            for page, digest, size in PAGE_EVIDENCE
        ]
        if render.get("engine") != "pdftoppm 26.07.0" or render.get("dpi") != 144 \
                or render.get("pixel_size") != [1190, 1682] \
                or render.get("color_mode") != "RGB" \
                or render.get("pages") != expected_pages:
            raise ValueError("receipt render")
        for item in expected_pages:
            validate_png(bounded_bytes(root, item["path"]))
        visual = receipt.get("visual_review", {})
        if visual.get("all_pages_inspected") is not True \
                or visual.get("inspection_detail") != "original" \
                or visual.get("clipping") is not False \
                or visual.get("overlap") is not False or visual.get("blank_pages") != [] \
                or visual.get("repeat_header_pages") != [2, 3, 4, 6] \
                or visual.get("caption_pages") != {
                    "allow_top": 1, "avoid_row_bottom": 6, "before_top": 7,
                    "exact_top": 8, "after_bottom": 10,
                } or visual.get("boundary_result") != {
                    "before": "same_page", "exact": "same_page", "after": "next_page",
                } or len(visual.get("page_findings", [])) != 10:
            raise ValueError("visual result")
        geometry = receipt.get("text_geometry", {})
        pages = geometry.get("pages", [])
        if geometry.get("engine") != "pdfplumber 0.11.9" \
                or geometry.get("outside_page_glyphs") != 0 or len(pages) != 10 \
                or [item.get("page") for item in pages] != list(range(1, 11)) \
                or any(item.get("chars", 0) <= 0 or len(item.get("bbox", [])) != 4
                       for item in pages):
            raise ValueError("text geometry")
        safety = receipt.get("safety", {})
        if safety != {
            "computer_use_click_or_type_invoked": False,
            "user_document_scanned": False, "external_network_invoked_by_runner": False,
            "input_unchanged": True, "remaining_hwp_process_count": 0,
        }:
            raise ValueError("visual safety")
        not_claimed = receipt.get("not_claimed", {})
        if set(not_claimed) != {
            "arbitrary_document", "other_pc_or_hancom_version", "production",
            "product_complete",
        } or set(not_claimed.values()) != {False}:
            raise ValueError("visual not claimed")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("pdf_visual_semantics")


def validate_png(data: bytes) -> None:
    if len(data) < 33 or not data.startswith(b"\x89PNG\r\n\x1a\n") \
            or data[12:16] != b"IHDR":
        raise ValueError("png signature")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height, data[24], data[25]) != (1190, 1682, 8, 2):
        raise ValueError("png geometry")


def validate_markers(root: Path, errors: list[str]) -> int:
    count = 0
    for path, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = bounded_bytes(root, path, 4 * 1024 * 1024).decode("utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path_or_encoding")
            continue
        count += 1
        if any(marker not in source for marker in markers):
            errors.append("implementation_markers")
    return count


def expected_validation_tree() -> set[str]:
    return {
        CONTRACT, REPORT, DIAGNOSTIC, MIGRATION,
        *SOURCE_LOCKS, *EVIDENCE, *IMPLEMENTATION_MARKERS,
        predecessor.CONTRACT, predecessor.REPORT, predecessor.MIGRATION,
        *predecessor.SOURCE_LOCKS, *predecessor.IMPLEMENTATION_MARKERS,
    }


def result(errors: list[str], source_locks: int, evidence_files: int,
           implementation_files: int, predecessor_state: str) -> dict[str, Any]:
    state = "pass" if not errors else "fail"
    return {
        "schema_version": "hwpx-agent.p06-07-table-pagination-target-validation/v2",
        "state": state, "errors": errors, "source_locks": source_locks,
        "evidence_files": evidence_files, "implementation_files": implementation_files,
        "predecessor": predecessor_state,
        "actual_hancom_2020_boundary_page_suite": "pass" if state == "pass" else "not_proven",
        "actual_hancom_2020_save_reopen_pdf_oracle": "pass" if state == "pass" else "not_proven",
        "p06_07": "pass" if state == "pass" else "not_proven",
        "p06": "in_progress",
    }


if __name__ == "__main__":
    report = validate()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    if report["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_PAGINATION_TARGET_V2_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"evidence_files={report['evidence_files']} "
        f"implementation_files={report['implementation_files']}"
    )
