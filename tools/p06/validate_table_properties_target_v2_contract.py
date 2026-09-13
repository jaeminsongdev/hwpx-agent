#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from tools.p06 import validate_table_properties_hwpx_contract as predecessor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-properties-target-v2.json"
REPORT = "implementation/p06/P06-09_TABLE_PROPERTIES_TARGET_READBACK_REPORT.md"
MIGRATION = "protocol/migrations/p06-table-properties-hwpx-v1-to-target-v2.md"
RECEIPT = "implementation/p06/evidence/target/p06-table-properties.current-2020.attempt01.v2.json"
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-properties-target-20260913-07"
MANIFEST_PATH = f"{TARGET_DIRECTORY}/fixture-manifest.json"
TARGET_PATH = f"{TARGET_DIRECTORY}/table-007-properties-formula-2x4.hwpx"
OUTPUT_PATH = f"{TARGET_DIRECTORY}/target-readback-output-01.hwpx"
PDF_PATH = f"{TARGET_DIRECTORY}/target-readback-output-01.pdf"
TRACE_PATH = f"{TARGET_DIRECTORY}/hancom-2020-trace-attempt01.json"
PROGRESS_PATH = f"{TRACE_PATH}.progress.jsonl"
PNG_PATH = f"{TARGET_DIRECTORY}/target-readback-output-01-page-1.png"

SOURCE_LOCKS = {
    "protocol/private/p06-table-properties-hwpx-v1.json": "2a93f9f0e05d392d8c552f750468b72b366955b27ecc87473875dbb2cc669a6b",
    "tools/p06/validate_table_properties_hwpx_contract.py": "6da77705c4e319847bdc7c258394592dc8a45358a5028f504b733872e1904772",
    "crates/hwpx-package/src/table_ruling_hwpx/properties_hwpx.rs": "9d1ba6454817bb4cdb42779b15952b8bd5cbad5d8b3a4fb2ed34ec651620020c",
    "crates/hwpx-package/tests/table_properties_hwpx.rs": "637991f05ff6f9952309f9445c61f5b83668a714008b50d0ef69d1386244f19b",
    "crates/hwpx-package/examples/p06_09_table_properties_target_fixture.rs": "87739dc63593a94a7df4adb8d4327fcbc85ddfa1b77d2c119e75f98efa0fa19c",
    "crates/hwpx-package/examples/p06_09_table_properties_target_oracle.rs": "b8107333e6d5db50e8e9dcd01141a565f5bbfe247409c8fb8b9007fb230890f9",
    "implementation/p05/tools/invoke-hancom-2020-bounded-readback.ps1": "f13474940e14754a483409d428c814c2c05c6ca9428143aff73337a82f5fcf18",
    "implementation/p05/tools/run-hancom-2020-tab-readback.ps1": "e27582f85f2fd17824b9c8afd8b3cda922a448590104982266fc5b7f6bcd6d72",
    "implementation/p06/tools/run-hancom-2020-table-properties-target-readback.ps1": "3da056958e4dac341700278a158d174bbe5eb1ceff3f39dd637939264d93b6a8",
    "implementation/p06/tests/Test-Hancom2020TablePropertiesTargetReadback.ps1": "82ed78af052dab81a8963411e04b0bed447aa3547128aee253c7efd81afacf96",
}
EVIDENCE = {
    MANIFEST_PATH: ("2eee896adddc9435ea04da26af35040fe92417cb0d35f8a304b146f083e41a0c", 4274),
    TARGET_PATH: ("940804c73f6cf83b5f1b37821dd18a731f6ad4927c95fb615d68fa4f48829924", 13167),
    OUTPUT_PATH: ("91ee296a57a4db0933c8f1b870d3c57872b7c75c131adb8e93d45c8a270f225d", 15198),
    PDF_PATH: ("ea7cab8718d3442d3c60a13ec65c9a16ca864a7704808a17d2c9b33bdc4221c7", 10291),
    TRACE_PATH: ("0d8cfa92b2e5cc2edd49e7ab26e6be123ee61b1e5d71187774b026919fc81af5", 2964),
    PROGRESS_PATH: ("e8cfbbba1b5ed845404b9be441449be82ee1d23a0b915809cb877d682c34c49f", 5164),
    PNG_PATH: ("59c90a5dbad92e26c74381f179a21f0af393a10abb592d16dd65227f7a120821", 11876),
    RECEIPT: ("f71d95ee607c17f4b4960e1feab2926497e3b0cd9fc12e896b36b0021666895a", 6151),
}
EXPECTED_PARTS = {
    "mimetype", "version.xml", "Contents/header.xml", "Contents/section0.xml",
    "Preview/PrvText.txt", "settings.xml", "Preview/PrvImage.png",
    "META-INF/container.rdf", "Contents/content.hpf", "META-INF/container.xml",
    "META-INF/manifest.xml",
}
IMMUTABLE_PARTS = {
    "mimetype", "version.xml", "META-INF/container.rdf",
    "META-INF/container.xml", "META-INF/manifest.xml",
}
IMPLEMENTATION_MARKERS = {
    REPORT: ("TABLE-007", "ReadbackMismatch", "oracle_verified", "product completion are not"),
    MIGRATION: ("no automatic migration", "TABLE-007", "fails closed"),
    RECEIPT: ("p06.table-properties.current-2020.attempt01.20260913", "rollback_or_retry", "combined_table_and_cell_single_request"),
    "crates/hwpx-package/examples/p06_09_table_properties_target_fixture.rs": ("set_table_properties", "set_cell_properties", "output directory already exists"),
    "crates/hwpx-package/examples/p06_09_table_properties_target_oracle.rs": ("strip_renderer_caches", "section_equal_after_renderer_cache_strip", "SUM(A2:C2)"),
    "implementation/p06/tools/run-hancom-2020-table-properties-target-readback.ps1": ("TABLE_PROPERTIES_TARGET_READBACK", "HWPFrame.HwpObject.2", "TimeoutSeconds"),
    "implementation/p06/tests/Test-Hancom2020TablePropertiesTargetReadback.ps1": ("preflight_fails_before_com", "no_ui_input", "no_registry_write"),
}


def add_error(errors: list[str], value: str) -> None:
    if value not in errors:
        errors.append(value)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def load_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)


def safe_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("unsafe path")
    target = root.joinpath(*pure.parts)
    resolved_root = root.resolve()
    resolved = target.resolve(strict=False)
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError("path escape")
    cursor = root
    for part in pure.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("symlink")
    return target


def bounded_bytes(root: Path, relative: str, limit: int = 8 * 1024 * 1024) -> bytes:
    path = safe_path(root, relative)
    if not path.is_file() or path.stat().st_size > limit:
        raise ValueError("missing or oversized")
    return path.read_bytes()


def canonical_sha256(data: bytes) -> str:
    text = data.decode("utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_validation_tree() -> list[str]:
    paths = set(SOURCE_LOCKS) | set(EVIDENCE) | set(IMPLEMENTATION_MARKERS) | {
        CONTRACT, REPORT, MIGRATION, predecessor.CONTRACT, predecessor.MIGRATION,
        predecessor.POLICY, predecessor.REPORT,
    }
    paths.update(predecessor.EXPECTED_SOURCE_PATHS)
    paths.update(predecessor.IMPLEMENTATION_MARKERS)
    return sorted(paths)


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    contract: dict[str, Any] = {}
    try:
        value = load_json(bounded_bytes(root, CONTRACT, 512_000))
        if not isinstance(value, dict):
            raise ValueError("contract object")
        contract = value
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0, "not_proven")

    predecessor_report = predecessor.validate(root)
    predecessor_state = predecessor_report.get("state", "not_proven")
    if predecessor_state != "pass":
        add_error(errors, "predecessor_validation")

    expected_predecessor = {
        "path": predecessor.CONTRACT,
        "sha256": SOURCE_LOCKS[predecessor.CONTRACT],
        "state": "static_direct_hwpx_integration_contract",
    }
    if contract.get("schema_version") != "hwpx-agent.p06-09-table-properties-target-contract/v2" \
            or contract.get("scope") != "TABLE-007 exact current-PC Hangul 2020 save-reopen-PDF typed oracle" \
            or contract.get("predecessor") != expected_predecessor \
            or contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        add_error(errors, "contract_identity")

    source_locks = validate_source_locks(root, contract.get("source_locks"), errors)
    evidence_files = validate_evidence(root, errors)
    validate_contract_claims(contract, errors)
    validate_manifest(root, errors)
    validate_hwpx(root, errors)
    validate_trace(root, errors)
    validate_progress(root, errors)
    validate_pdf(root, errors)
    implementation_files = validate_markers(root, errors)
    return result(errors, source_locks, evidence_files, implementation_files, predecessor_state)


def validate_source_locks(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        add_error(errors, "source_locks_exact")
        return 0
    declared: dict[str, str] = {}
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"} \
                or not isinstance(entry.get("path"), str) or not isinstance(entry.get("sha256"), str):
            add_error(errors, "source_locks_exact")
            continue
        relative, digest = entry["path"], entry["sha256"]
        if relative in declared:
            add_error(errors, "source_locks_exact")
        declared[relative] = digest
        try:
            actual = canonical_sha256(bounded_bytes(root, relative, 4 * 1024 * 1024))
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "source_lock_path_or_encoding")
            continue
        if actual != digest:
            add_error(errors, "source_lock_digest")
    if declared != SOURCE_LOCKS:
        add_error(errors, "source_locks_exact")
    return len(declared)


def validate_evidence(root: Path, errors: list[str]) -> int:
    for relative, (expected_sha, expected_bytes) in EVIDENCE.items():
        try:
            data = bounded_bytes(root, relative)
            if len(data) != expected_bytes or sha256(data) != expected_sha:
                raise ValueError("digest")
        except (OSError, ValueError):
            add_error(errors, "evidence_digest")
    return len(EVIDENCE)


def validate_contract_claims(contract: dict[str, Any], errors: list[str]) -> None:
    expected_target = {
        "product": "Hancom Hangul 2020", "prog_id": "HWPFrame.HwpObject.2",
        "registry_view": "Registry32", "client": "windows_powershell_x86_sta",
        "build": "11.0.0.9136", "architecture": "x86", "locale": "ko-KR",
        "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
    }
    expected_gate = {
        "TABLE-007": "oracle_verified", "TABLE-008": "integration_passed",
        "TABLE-009": "integration_passed", "TABLE-047": "integration_passed",
        "actual_hancom_2020_save_reopen": "pass", "target_build": "pass",
        "render_diff": "pass", "rollback_or_retry": "pass",
        "automation_runtime": "not_run", "differential": "not_run",
        "p06_09": "in_progress", "p06": "in_progress",
    }
    expected_not_claimed = {
        "combined_table_and_cell_single_request": False, "automation_runtime": False,
        "differential_exact_match": False, "arbitrary_user_document_compatibility": False,
        "other_pc_or_hancom_version": False, "p06_09_complete": False,
        "p06_phase_complete": False, "production": False, "product_complete": False,
    }
    attempt = contract.get("successful_attempt", {})
    expected_attempt = {
        "manifest": (MANIFEST_PATH, EVIDENCE[MANIFEST_PATH]),
        "target": (TARGET_PATH, EVIDENCE[TARGET_PATH]),
        "output": (OUTPUT_PATH, EVIDENCE[OUTPUT_PATH]),
        "pdf": (PDF_PATH, EVIDENCE[PDF_PATH]),
        "trace": (TRACE_PATH, EVIDENCE[TRACE_PATH]),
        "progress": (PROGRESS_PATH, EVIDENCE[PROGRESS_PATH]),
        "render_png": (PNG_PATH, EVIDENCE[PNG_PATH]),
        "receipt": (RECEIPT, EVIDENCE[RECEIPT]),
    }
    if contract.get("exact_target") != expected_target:
        add_error(errors, "target_identity")
    if not isinstance(attempt, dict) or attempt.get("id") != "20260913-07" \
            or attempt.get("directory") != TARGET_DIRECTORY or attempt.get("state") != "pass":
        add_error(errors, "successful_attempt")
    for key, (path, (digest, size)) in expected_attempt.items():
        entry = attempt.get(key, {}) if isinstance(attempt, dict) else {}
        if not isinstance(entry, dict) or entry.get("path") != path \
                or entry.get("sha256") != digest or entry.get("bytes") != size:
            add_error(errors, "successful_attempt")
    if isinstance(attempt.get("pdf"), dict) and attempt["pdf"].get("pages") != 1:
        add_error(errors, "successful_attempt")
    if isinstance(attempt.get("progress"), dict) and attempt["progress"].get("events") != 21:
        add_error(errors, "successful_attempt")
    if contract.get("gate_decision") != expected_gate:
        add_error(errors, "gate_decision")
    if contract.get("not_claimed") != expected_not_claimed:
        add_error(errors, "not_claimed")
    if contract.get("migration") != MIGRATION or contract.get("report") != REPORT \
            or contract.get("evidence_receipt") != RECEIPT:
        add_error(errors, "contract_paths")
    retry = contract.get("retry_oracle", {})
    if retry != {"state": "pass", "independent_builds": 2, "byte_deterministic": True,
                 "existing_destination_rejected_without_overwrite": True}:
        add_error(errors, "retry_oracle")


def validate_manifest(root: Path, errors: list[str]) -> None:
    try:
        manifest = load_json(bounded_bytes(root, MANIFEST_PATH))
        case = manifest["case"]
        operations = case["operations"]
        checks = (
            manifest["schema_version"] == "hwpx-agent.p06-09-table-properties-target-fixture/v1",
            manifest["source_ancestor_sha256"] == "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5",
            case["feature_id"] == "TABLE-007", case["capability_id"] == "table.properties",
            case["sha256"] == EVIDENCE[TARGET_PATH][0], case["selected_cell"] == {"row": 1, "column": 0},
            case["target_state_sha256"] == "f284c77467278ff219de2bcd1d9ff5a9fc7bf29ef6cc2ae9f7a6efad005d0095",
            case["target_grid_sha256"] == "27d0379ec87ad07e5f80ef5e01f5c03fe6db104d8e186a80b132f03e1fdaad61",
            case["rows"] == 2, case["columns"] == 4, case["master_cells"] == 8,
            case["payload_blocks"] == 7, case["formula_count"] == 1,
            case["page_split"] == "cell", case["table_lock"] is True,
            case["table_no_adjust"] is True, case["changed_master_cells"] == 1,
            case["preserved_formula_count"] == 1,
            [item["name"] for item in operations] == ["set_table_properties", "set_cell_properties"],
            [item["changed_master_cells"] for item in operations] == [0, 1],
            [item["preserved_formula_count"] for item in operations] == [1, 1],
            manifest["actual_hangul_2020"] is False, manifest["render"] == "not_run",
            manifest["automation"] == "not_run", manifest["differential"] == "not_run",
        )
        if not all(checks):
            raise ValueError("manifest semantics")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        add_error(errors, "manifest_semantics")


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def first_descendant(element: ET.Element, name: str) -> ET.Element:
    return next(item for item in element.iter() if local_name(item) == name)


def validate_hwpx(root: Path, errors: list[str]) -> None:
    try:
        target_data = bounded_bytes(root, TARGET_PATH)
        output_data = bounded_bytes(root, OUTPUT_PATH)
        with zipfile.ZipFile(Path(safe_path(root, TARGET_PATH))) as target_zip, \
                zipfile.ZipFile(Path(safe_path(root, OUTPUT_PATH))) as output_zip:
            target_names = target_zip.namelist()
            output_names = output_zip.namelist()
            if len(target_names) != 11 or set(target_names) != EXPECTED_PARTS \
                    or output_names != target_names or len(set(target_names)) != 11:
                raise ValueError("package topology")
            if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
                   for name in target_names):
                raise ValueError("unsafe zip name")
            if any(target_zip.read(name) != output_zip.read(name) for name in IMMUTABLE_PARTS):
                raise ValueError("immutable part")
            target_section = target_zip.read("Contents/section0.xml")
            output_section = output_zip.read("Contents/section0.xml")
            stripped, count = re.subn(
                rb"<hp:linesegarray>.*?</hp:linesegarray>", b"", output_section, flags=re.S
            )
            if count != 10 or stripped != target_section \
                    or b"<hp:linesegarray>" in target_section:
                raise ValueError("renderer cache relation")
            if target_zip.read("Preview/PrvText.txt") != b"<2><3><4><5><17><10><25><52>\r\n\r\n" \
                    or output_zip.read("Preview/PrvText.txt") != b"<2><3><4><5>\r\n<17><10><25><52>\r\n\r\n":
                raise ValueError("preview relation")
        if sha256(target_data) != EVIDENCE[TARGET_PATH][0] \
                or sha256(output_data) != EVIDENCE[OUTPUT_PATH][0]:
            raise ValueError("outer digest")
        root_element = ET.fromstring(output_section)
        tables = [item for item in root_element.iter() if local_name(item) == "tbl"]
        if len(tables) != 1:
            raise ValueError("table count")
        table = tables[0]
        required_table = {"lock": "1", "noAdjust": "1", "pageBreak": "CELL",
                          "rowCnt": "2", "colCnt": "4", "borderFillIDRef": "3"}
        if any(table.get(key) != value for key, value in required_table.items()):
            raise ValueError("table properties")
        cells = [item for item in table.iter() if local_name(item) == "tc"]
        if len(cells) != 8:
            raise ValueError("cell count")
        selected = cells[4]
        if any(selected.get(key) != value for key, value in
               {"hasMargin": "1", "protect": "1", "editable": "1",
                "borderFillIDRef": "3"}.items()):
            raise ValueError("selected cell")
        margin = first_descendant(selected, "cellMargin")
        sublist = first_descendant(selected, "subList")
        paragraph = first_descendant(selected, "p")
        if margin.attrib != {"left": "1200", "right": "200", "top": "900", "bottom": "100"} \
                or sublist.get("textDirection") != "VERTICALALL" \
                or sublist.get("vertAlign") != "BOTTOM" or paragraph.get("paraPrIDRef") != "0":
            raise ValueError("selected cell detail")
        fields = [item for item in table.iter() if local_name(item) == "fieldBegin"]
        formula_cell = cells[7]
        formula_text = ET.tostring(formula_cell, encoding="unicode")
        if len(fields) != 1 or fields[0].get("type") != "FORMULA" \
                or fields[0] not in list(formula_cell.iter()) \
                or "=SUM(LEFT)" not in formula_text or "52" not in formula_text:
            raise ValueError("formula")
        caches = [item for item in root_element.iter() if local_name(item) == "linesegarray"]
        lines = [first_descendant(item, "lineseg").attrib for item in caches]
        common = {"textpos": "0", "vertsize": "1000", "textheight": "1000",
                  "spacing": "600", "horzpos": "0", "flags": "393216"}
        if any(any(line.get(key) != value for key, value in common.items()) for line in lines):
            raise ValueError("cache common")
        normal = sum(line.get("vertpos") == "0" and line.get("baseline") == "850"
                     and line.get("horzsize") == "9468" for line in lines)
        selected_cache = sum(line.get("vertpos") == "0" and line.get("baseline") == "500"
                             and line.get("horzsize") == "3000" for line in lines)
        outer_zero = sum(line.get("vertpos") == "0" and line.get("baseline") == "850"
                         and line.get("horzsize") == "0" for line in lines)
        outer_page = sum(line.get("vertpos") == "8566" and line.get("baseline") == "850"
                         and line.get("horzsize") == "42520" for line in lines)
        if (normal, selected_cache, outer_zero, outer_page) != (7, 1, 1, 1):
            raise ValueError("cache profiles")
    except (OSError, UnicodeDecodeError, ValueError, zipfile.BadZipFile, ET.ParseError, StopIteration):
        add_error(errors, "target_oracle_hwpx_semantics")


def validate_trace(root: Path, errors: list[str]) -> None:
    try:
        trace = load_json(bounded_bytes(root, TRACE_PATH, 256_000))
        expected_target = {
            "prog_id": "HWPFrame.HwpObject.2", "registry_view": "Registry32",
            "client": "windows_powershell_x86_sta", "file_version": "11.0.0.9136",
            "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
        }
        expected_phases = {name: "pass" for name in (
            "com_create", "open_input", "read_input", "save_as_hwpx", "close_input",
            "reopen_output", "read_output", "export_pdf", "close_output", "quit",
        )}
        watchdog = trace.get("watchdog", {})
        checks = (
            trace.get("schema_version") == "hwpx-agent.p06-09-hancom-2020-table-properties-target-readback/v1",
            trace.get("state") == "pass", trace.get("target") == expected_target,
            trace.get("input_sha256") == EVIDENCE[TARGET_PATH][0],
            trace.get("output_sha256") == EVIDENCE[OUTPUT_PATH][0],
            trace.get("input_text_sha256") == "ff9c3868c05d5171931304c7fdc722ad8f99278af1d83e4abb4662a6026f3a3e",
            trace.get("output_text_sha256") == "ff9c3868c05d5171931304c7fdc722ad8f99278af1d83e4abb4662a6026f3a3e",
            trace.get("input_unchanged") is True, trace.get("output_saved") is True,
            trace.get("render_pdf_requested") is True, trace.get("render_pdf_saved") is True,
            trace.get("render_pdf_sha256") == EVIDENCE[PDF_PATH][0],
            trace.get("render_pdf_bytes") == EVIDENCE[PDF_PATH][1],
            trace.get("render_pdf_signature_valid") is True,
            trace.get("render_pdf_export_method") == "IXHwpDocument.SaveAs/PDF",
            trace.get("phases") == expected_phases, trace.get("error_code") is None,
            trace.get("failed_phase") is None, trace.get("exception_type") is None,
            trace.get("exception_hresult") is None, trace.get("raw_document_text_present") is False,
            trace.get("user_document_scanned") is False, trace.get("external_network_invoked") is False,
            trace.get("registry_or_system_setting_changed") is False,
            trace.get("computer_use_click_or_type_invoked") is False,
            watchdog.get("timeout_seconds") == 600, watchdog.get("timed_out") is False,
            watchdog.get("child_exit_code") == 0, watchdog.get("remaining_hwp_process_count") == 0,
            watchdog.get("progress_valid") is True, watchdog.get("progress_event_count") == 21,
            watchdog.get("progress_last_phase") == "terminal", watchdog.get("progress_last_state") == "pass",
        )
        if not all(checks):
            raise ValueError("trace")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "trace_semantics")


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
        (19, "quit", "running"), (20, "quit", "pass"), (21, "terminal", "pass"),
    ]
    try:
        events = [load_json(line.encode("utf-8")) for line in
                  bounded_bytes(root, PROGRESS_PATH, 256_000).decode("utf-8").splitlines()]
        actual = [(item.get("sequence"), item.get("phase"), item.get("state")) for item in events]
        if actual != expected or any(
            item.get("schema_version") != "hwpx-agent.p05-hancom-readback-progress/v1"
            or item.get("raw_document_text_present") is not False for item in events
        ):
            raise ValueError("progress")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "progress_semantics")


def validate_pdf(root: Path, errors: list[str]) -> None:
    try:
        data = bounded_bytes(root, PDF_PATH)
        if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:] \
                or not re.search(rb"/Type\s*/Pages\b", data) \
                or not re.search(rb"/Count\s+1\b", data) \
                or b"/Encrypt" in data or b"/JavaScript" in data:
            raise ValueError("pdf")
    except (OSError, ValueError):
        add_error(errors, "pdf_semantics")


def validate_markers(root: Path, errors: list[str]) -> int:
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_bytes(root, relative, 4 * 1024 * 1024).decode("utf-8")
            if any(marker not in text for marker in markers):
                raise ValueError("marker")
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "implementation_markers")
    return len(IMPLEMENTATION_MARKERS)


def result(errors: list[str], source_locks: int, evidence_files: int,
           implementation_files: int, predecessor_state: str) -> dict[str, Any]:
    unique = sorted(set(errors))
    state = "pass" if not unique else "fail"
    return {
        "schema_version": "hwpx-agent.p06-09-table-properties-target-validation/v2",
        "state": state,
        "errors": unique,
        "source_locks": source_locks,
        "evidence_files": evidence_files,
        "implementation_files": implementation_files,
        "predecessor": predecessor_state,
        "TABLE-007": "oracle_verified" if state == "pass" else "not_proven",
        "TABLE-008": "integration_passed",
        "TABLE-009": "integration_passed",
        "TABLE-047": "integration_passed",
        "p06_09": "in_progress",
        "p06": "in_progress",
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_PROPERTIES_TARGET_V2_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"evidence_files={validation['evidence_files']} "
        f"implementation_files={validation['implementation_files']}"
    )
