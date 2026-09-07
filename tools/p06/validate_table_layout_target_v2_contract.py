#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


def load_base_validator() -> Any:
    path = Path(__file__).resolve().with_name("validate_table_layout_contract.py")
    specification = importlib.util.spec_from_file_location("p06_table_layout_target_v2_base", path)
    if specification is None or specification.loader is None:
        raise RuntimeError("table layout target v2 base validator load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


base = load_base_validator()
ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-layout-target-v2.json")
MIGRATION_RELATIVE = PurePosixPath("protocol/migrations/p06-table-layout-target-v1-to-v2.md")
REPORT_RELATIVE = PurePosixPath("implementation/p06/P06-05_TARGET_READBACK_REPORT.md")
TARGET_DIRECTORY = "fixtures/target-build/p06-05-table-layout-20260907-05"
TARGET_FILES = ["target.hwpx", "target-repeat.hwpx", "target-current.hwpx"]
TARGET_SHA256 = "3dfcf2a185a4129989b29877b7df7dadb638071aed5ccddd1476e46f76d9bcb5"
OUTPUT_PATH = f"{TARGET_DIRECTORY}/target-readback-output-01.hwpx"
OUTPUT_SHA256 = "ec08dc8e07dfc1b18c5916b44917b00d27da9905bea26f57e9b16991396c1ec7"
PDF_PATH = f"{TARGET_DIRECTORY}/target-readback-output-01.pdf"
PDF_SHA256 = "6e929f5cf56d2ac0c36587c5bdfd60f41a4d100b35c72356d85bb3ea1cf54606"
TRACE_PATH = f"{TARGET_DIRECTORY}/target-readback-trace-01.json"
TRACE_SHA256 = "8de3eac36c748b3852b517a8e302ab5b8062d672279b1b7963dab839b4fdbf19"
BASE_TARGET_PATH = "fixtures/target-build/p06-05-table-layout-20260907-03/target.hwpx"
BASE_TARGET_SHA256 = "b2887c929cdeb81fa1f5f3bac086265e19fb92a8bbf063f75e5ab0fbfa5cb299"
CALIBRATION_PATH = (
    "fixtures/target-build/p06-05-table-layout-20260907-03/target-readback-output-02.hwpx"
)
CALIBRATION_SHA256 = "09f3e8b27167a43650d710f6338b5712655e9fd70a30cef9c97dbe28abab1954"
CALIBRATION_TRACE_PATH = (
    "fixtures/target-build/p06-05-table-layout-20260907-03/target-readback-trace-02.json"
)
CALIBRATION_TRACE_SHA256 = (
    "a0d8c28f3fd5f3fe38f460ecfb30d3610459b55f2011c3bc2d11178acfe932c6"
)
FOUR_UM_TARGET_PATH = "fixtures/target-build/p06-05-table-layout-20260907-04/target.hwpx"
FOUR_UM_TARGET_SHA256 = "0a05a32de46568bdde0eba301e719a8efcb4142167e6860124691563363b32dd"
FOUR_UM_OUTPUT_PATH = (
    "fixtures/target-build/p06-05-table-layout-20260907-04/target-readback-output-01.hwpx"
)
FOUR_UM_OUTPUT_SHA256 = "870d908666d1699f437a86bb6d53dd84023bbf64e9fe895c0903acd20a720293"
FOUR_UM_TRACE_PATH = (
    "fixtures/target-build/p06-05-table-layout-20260907-04/target-readback-trace-01.json"
)
FOUR_UM_TRACE_SHA256 = "9ccbccbeb7b5318407f821e652576a5b74064849dc0ca4a4e149e699c786b42b"
RECEIPT_PATH = (
    "artifacts/p06/font-metric-runs/4b9b0cac589946918140abc4a12c1be1/receipt.json"
)
RECEIPT_SHA256 = "c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab"
TEXT_SHA256 = "a73ff5335c34949be0d3a539eaf7d86404f2045cd9315f5f43b9e28836fd28d1"
CONTENT_SHA256 = "5542afbe344fa447f2598491ec7e0f7b473b2832402bfd203f26713d6448d86c"
EXPECTED_SOURCE_LOCKS = {
    "protocol/private/p06-table-layout-target-v1.json": (
        "6944329a8846a21960b3c1327be4124f88c0005ba3ed77eb16ec6aef012cddde"
    ),
    "crates/hwpx-package/examples/p06_05_table_layout_calibrated_target_fixture.rs": (
        "193958e8b1269895f205c18521526307acb5f9b81f86966a5c51ee8f802571f6"
    ),
    "implementation/p06/tools/run-hancom-2020-table-layout-readback.ps1": (
        "17f7b99adb0c1ba3cfaf46f6ff7067d1c16c27d3699e12b4fe4550cef782f169"
    ),
}
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/examples/p06_05_table_layout_calibrated_target_fixture.rs": (
        "hwpx-agent.p06-05-table-layout-calibrated-target/v1",
        "CALIBRATION_GUARD_MICROMETERS: i64 = 350",
        "hancom-2020-line-box-100-hwpunit-bucket/1",
        "require_layout(&target_inspection.layout, 5_200, [15_120, 4_723])",
        ".create_new(true)",
        "recheck_sources",
    ),
    MIGRATION_RELATIVE.as_posix(): (
        "100-HWPUNIT",
        "four-micrometer guard",
        "There is no automatic migration",
        "remain unclaimed",
    ),
    REPORT_RELATIVE.as_posix(): (
        "PASS for the exact current-PC Hangul 2020 P06-05 fixture",
        TARGET_SHA256,
        OUTPUT_SHA256,
        PDF_SHA256,
        "1,3,1,1",
        "no content is clipped or overlaps",
        "P06-05 is complete",
    ),
}

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"


def tag(local: str) -> str:
    return f"{{{HP}}}{local}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def exact_contract() -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-05-table-layout-target-contract/v2",
        "model_schema_version": "hwpx-agent.p06-05-table-layout-calibrated-target/v1",
        "scope": "p06_05_exact_current_pc_hancom_2020_calibrated_layout_oracle",
        "prerequisites": [
            "hwpx-agent.p06-05-table-layout-target-contract/v1",
            "hwpx-agent.table-layout-hwpx.hancom-2020/2",
            "hwpx-agent.p06-05-current-font-metric-receipt/v1",
            "exact_licensed_current_pc_hancom_2020_11.0.0.9136",
        ],
        "source_lock_canonicalization": "utf8_lf_sha256",
        "migration": MIGRATION_RELATIVE.as_posix(),
        "not_claimed": {
            "arbitrary_user_document_compatibility": False,
            "other_pc_or_hancom_version": False,
            "p06_phase_complete": False,
            "production": False,
            "product_complete": False,
        },
    }


def expected_evidence() -> dict[str, str]:
    return {
        BASE_TARGET_PATH: BASE_TARGET_SHA256,
        RECEIPT_PATH: RECEIPT_SHA256,
        CALIBRATION_PATH: CALIBRATION_SHA256,
        CALIBRATION_TRACE_PATH: CALIBRATION_TRACE_SHA256,
        FOUR_UM_TARGET_PATH: FOUR_UM_TARGET_SHA256,
        FOUR_UM_OUTPUT_PATH: FOUR_UM_OUTPUT_SHA256,
        FOUR_UM_TRACE_PATH: FOUR_UM_TRACE_SHA256,
        **{f"{TARGET_DIRECTORY}/{name}": TARGET_SHA256 for name in TARGET_FILES},
        OUTPUT_PATH: OUTPUT_SHA256,
        PDF_PATH: PDF_SHA256,
        TRACE_PATH: TRACE_SHA256,
    }


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = base.load_contract(base.bounded_file(root, CONTRACT_RELATIVE.as_posix(), 512_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0)

    for key, expected in exact_contract().items():
        if contract.get(key) != expected:
            errors.append(key)
    validate_contract_objects(contract, errors)
    source_locks = validate_source_locks(root, contract, errors)
    evidence_files = validate_evidence(root, errors)
    validate_trace(root, TRACE_PATH, target_sha=TARGET_SHA256, output_sha=OUTPUT_SHA256,
                   pdf_sha=PDF_SHA256, errors=errors)
    validate_trace(root, CALIBRATION_TRACE_PATH, target_sha=BASE_TARGET_SHA256,
                   output_sha=CALIBRATION_SHA256, pdf_sha=None, errors=errors,
                   label="historical_trace")
    validate_trace(root, FOUR_UM_TRACE_PATH, target_sha=FOUR_UM_TARGET_SHA256,
                   output_sha=FOUR_UM_OUTPUT_SHA256, pdf_sha=None, errors=errors,
                   label="historical_trace")
    validate_hwpx(root, TARGET_DIRECTORY + "/target.hwpx", 5_200, [15_120, 4_723] * 2,
                  None, None, errors, "target_hwpx")
    validate_hwpx(root, OUTPUT_PATH, 5_782, [15_120, 4_723] * 2,
                  [1, 3, 1, 1], [14_100, 3_700, 14_100, 3_700], errors, "output_hwpx")
    validate_hwpx(root, CALIBRATION_PATH, 7_364, [15_021, 4_822] * 2,
                  [1, 3, 2, 1], [14_000, 3_800, 14_000, 3_800], errors,
                  "historical_hwpx")
    validate_hwpx(root, FOUR_UM_OUTPUT_PATH, 7_364, [15_022, 4_821] * 2,
                  [1, 3, 2, 1], [14_000, 3_800, 14_000, 3_800], errors,
                  "historical_hwpx")
    validate_pdf(root, errors)
    implementation_files = validate_markers(root, errors)
    return result(sorted(set(errors)), source_locks, evidence_files, implementation_files)


def validate_contract_objects(contract: dict[str, Any], errors: list[str]) -> None:
    if set(contract) != {
        "schema_version", "model_schema_version", "scope", "predecessor", "prerequisites",
        "source_lock_canonicalization", "source_locks", "exact_inputs", "calibration_profile",
        "layout_profile", "publication", "historical_calibration_evidence", "actual_oracle",
        "gate_decision", "failure_policy", "migration", "not_claimed",
    }:
        errors.append("contract_shape")
    if contract.get("predecessor") != {
        "path": "protocol/private/p06-table-layout-target-v1.json",
        "sha256": EXPECTED_SOURCE_LOCKS["protocol/private/p06-table-layout-target-v1.json"],
        "state": "immutable_pre_calibration_target_contract",
    }:
        errors.append("predecessor")
    if contract.get("exact_inputs") != {
        "base_target_path": BASE_TARGET_PATH,
        "base_target_sha256": BASE_TARGET_SHA256,
        "font_receipt_path": RECEIPT_PATH,
        "font_receipt_sha256": RECEIPT_SHA256,
        "calibration_hwpx_path": CALIBRATION_PATH,
        "calibration_hwpx_sha256": CALIBRATION_SHA256,
    }:
        errors.append("exact_inputs")
    if contract.get("calibration_profile") != {
        "profile_id": "hwpx-agent.font-metric.hancom-2020-line-box-100-hwpunit-bucket/1",
        "guard_micrometers": 350,
        "observed_line_box_quantum_hwpunit": 100,
        "base_left_cell_width_hwpunit": 15021,
        "base_left_line_box_hwpunit": 14000,
        "calibrated_left_cell_width_hwpunit": 15120,
        "calibrated_left_line_box_hwpunit": 14100,
        "rule": "advance_the_left_content_box_to_the_next_observed_100_hwpunit_line_box_bucket",
        "evidence_binding": "exact_current_pc_hancom_2020_saved_hwpx_only",
    }:
        errors.append("calibration_profile")
    expected_layout = {
        "grid_sha256": "2c21be8ef4d42da0b4c387395a235a9978bf53c7480f4159f815795799633c49",
        "plan_sha256": "7a9c19014be2ceffb5648d62270bd42ed67ac0db46f0b16101b5174ae2218cf3",
        "content_sha256": CONTENT_SHA256,
        "table_width_hwpunit": 19843,
        "target_table_height_hwpunit": 5200,
        "column_widths_micrometers": [53340, 16660],
        "row_heights_micrometers": [13758, 4586],
        "cell_widths_hwpunit": [15120, 4723, 15120, 4723],
        "cell_heights_hwpunit": [3900, 3900, 1300, 1300],
        "inner_margin_hwpunit": [510, 510, 141, 141],
    }
    if contract.get("layout_profile") != expected_layout:
        errors.append("layout_profile")
    if contract.get("publication") != {
        "directory": TARGET_DIRECTORY,
        "files": TARGET_FILES,
        "sha256": TARGET_SHA256,
        "write_mode": "three_independent_create_new_writes",
        "byte_deterministic": True,
        "git_tracked": False,
    }:
        errors.append("publication")
    expected_history = [
        {
            "guard_micrometers": 0,
            "output_hwpx_path": CALIBRATION_PATH,
            "output_hwpx_sha256": CALIBRATION_SHA256,
            "trace_path": CALIBRATION_TRACE_PATH,
            "trace_sha256": CALIBRATION_TRACE_SHA256,
            "cell_line_counts": [1, 3, 2, 1],
            "cell_line_box_widths_hwpunit": [14000, 3800, 14000, 3800],
            "decision": "runtime_lifecycle_pass_but_expected_cell_c_wrap_failed",
        },
        {
            "guard_micrometers": 4,
            "target_path": FOUR_UM_TARGET_PATH,
            "target_sha256": FOUR_UM_TARGET_SHA256,
            "output_hwpx_path": FOUR_UM_OUTPUT_PATH,
            "output_hwpx_sha256": FOUR_UM_OUTPUT_SHA256,
            "trace_path": FOUR_UM_TRACE_PATH,
            "trace_sha256": FOUR_UM_TRACE_SHA256,
            "cell_line_counts": [1, 3, 2, 1],
            "cell_line_box_widths_hwpunit": [14000, 3800, 14000, 3800],
            "decision": "runtime_lifecycle_pass_but_guard_did_not_cross_renderer_bucket",
        },
    ]
    if contract.get("historical_calibration_evidence") != expected_history:
        errors.append("historical_calibration_evidence")
    expected_oracle = {
        "trace_path": TRACE_PATH,
        "trace_sha256": TRACE_SHA256,
        "output_hwpx_path": OUTPUT_PATH,
        "output_hwpx_sha256": OUTPUT_SHA256,
        "output_pdf_path": PDF_PATH,
        "output_pdf_sha256": PDF_SHA256,
        "output_pdf_bytes": 15421,
        "expected_text_sha256": TEXT_SHA256,
        "hancom_file_version": "11.0.0.9136",
        "hancom_executable_sha256": (
            "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
        ),
        "saved_table_height_hwpunit": 5782,
        "cell_line_counts": [1, 3, 1, 1],
        "cell_line_box_widths_hwpunit": [14100, 3700, 14100, 3700],
        "cell_line_text_positions": [[0], [0, 5, 8], [0], [0]],
        "target_cell_dimensions_preserved": True,
        "content_sha256_preserved": True,
        "input_unchanged": True,
        "save_reopen_pass": True,
        "pdf_signature_valid": True,
        "pdf_visual_review": "pass_no_clipping_no_overlap_all_four_strings_visible",
        "remaining_hwp_process_count": 0,
    }
    if contract.get("actual_oracle") != expected_oracle:
        errors.append("actual_oracle")
    if contract.get("gate_decision") != {
        "current_pc_exact_fixture_p06_05": "pass",
        "reason": (
            "verified_solver_plan_is_lowered_deterministically_and_matches_exact_Hangul_2020_"
            "wrap_and_visual_oracle"
        ),
        "aggregate_saved_table_height_note": (
            "Hangul_regenerates_the_table_aggregate_height_while_preserving_all_requested_cell_"
            "dimensions_and_semantics"
        ),
    }:
        errors.append("gate_decision")
    if contract.get("failure_policy") != [
        "wrong_input_receipt_or_calibration_digest_rejects_before_output",
        "existing_output_path_rejects_without_overwrite",
        "source_inputs_are_rehashed_after_build",
        "publication_digest_or_determinism_drift_rejects",
        "runtime_trace_failure_input_change_or_process_residue_rejects",
        "text_digest_or_target_cell_dimension_drift_rejects",
        "actual_cell_line_count_width_or_text_position_drift_rejects",
        "missing_invalid_or_digest_mismatched_pdf_rejects",
        "historical_failed_calibration_is_never_promoted_to_pass",
        "other_pc_or_version_evidence_is_never_inferred",
    ]:
        errors.append("failure_policy")


def validate_source_locks(root: Path, contract: dict[str, Any], errors: list[str]) -> int:
    locks = contract.get("source_locks")
    declared: dict[str, str] = {}
    if not isinstance(locks, list):
        errors.append("source_locks_shape")
        return 0
    for entry in locks:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        relative, expected = entry.get("path"), entry.get("sha256")
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
    return len(locks)


def validate_evidence(root: Path, errors: list[str]) -> int:
    count = 0
    for relative, expected in expected_evidence().items():
        try:
            path = base.bounded_file(root, relative, 8 * 1024 * 1024)
            count += 1
            if sha256_file(path) != expected:
                errors.append("evidence_digest")
        except (OSError, ValueError):
            errors.append("evidence_path")
    return count


def validate_trace(root: Path, relative: str, *, target_sha: str, output_sha: str,
                   pdf_sha: str | None, errors: list[str], label: str = "trace") -> None:
    try:
        trace = json.loads(base.bounded_file(root, relative, 256_000).read_text(encoding="utf-8"),
                           object_pairs_hook=base.reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append(label + "_json")
        return
    phases = trace.get("phases") if isinstance(trace, dict) else None
    watchdog = trace.get("watchdog") if isinstance(trace, dict) else None
    target = trace.get("target") if isinstance(trace, dict) else None
    valid = isinstance(trace, dict) and trace.get("state") == "pass" and (
        trace.get("schema_version") == "hwpx-agent.p06-05-hancom-2020-table-layout-readback/v1"
        and isinstance(target, dict)
        and target == {
            "prog_id": "HWPFrame.HwpObject.2",
            "registry_view": "Registry32",
            "client": "windows_powershell_x86_sta",
            "file_version": "11.0.0.9136",
            "executable_sha256": (
                "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"
            ),
        }
        and trace.get("input_sha256") == target_sha
        and trace.get("output_sha256") == output_sha
        and trace.get("input_text_sha256") == TEXT_SHA256
        and trace.get("output_text_sha256") == TEXT_SHA256
        and trace.get("input_unchanged") is True
        and trace.get("output_saved") is True
        and trace.get("raw_document_text_present") is False
        and trace.get("user_document_scanned") is False
        and trace.get("external_network_invoked") is False
        and trace.get("registry_or_system_setting_changed") is False
        and trace.get("computer_use_click_or_type_invoked") is False
        and trace.get("error_code") is None
        and trace.get("failed_phase") is None
        and isinstance(phases, dict) and phases and all(value == "pass" for value in phases.values())
        and isinstance(watchdog, dict)
        and watchdog.get("timed_out") is False
        and watchdog.get("remaining_hwp_process_count") == 0
    )
    if pdf_sha is not None:
        valid = valid and trace.get("render_pdf_saved") is True and (
            trace.get("render_pdf_signature_valid") is True
            and trace.get("render_pdf_sha256") == pdf_sha
            and trace.get("render_pdf_bytes") == 15421
        )
    if not valid:
        errors.append(label + "_semantics")


def validate_hwpx(root: Path, relative: str, table_height: int, cell_widths: list[int],
                  line_counts: list[int] | None, line_widths: list[int] | None,
                  errors: list[str], label: str) -> None:
    try:
        path = base.bounded_file(root, relative, 8 * 1024 * 1024)
        with zipfile.ZipFile(path) as archive:
            entries = [item for item in archive.infolist() if item.filename == "Contents/section0.xml"]
            if len(entries) != 1 or entries[0].file_size > 8 * 1024 * 1024:
                raise ValueError("section shape")
            section = archive.read(entries[0])
        tree = ET.fromstring(section)
        if sum(1 for _ in tree.iter()) > 131_072:
            raise ValueError("element limit")
        tables = list(tree.iter(tag("tbl")))
        if len(tables) != 1:
            raise ValueError("table count")
        table = tables[0]
        sizes = [node for node in table if node.tag == tag("sz")]
        rows = [node for node in table if node.tag == tag("tr")]
        cells = [cell for row in rows for cell in row if cell.tag == tag("tc")]
        if len(sizes) != 1 or int(sizes[0].get("width", "-1")) != 19843 or (
            int(sizes[0].get("height", "-1")) != table_height or len(cells) != 4
        ):
            raise ValueError("layout")
        actual_widths: list[int] = []
        actual_heights: list[int] = []
        actual_counts: list[int] = []
        actual_line_widths: list[int] = []
        actual_positions: list[list[int]] = []
        for cell in cells:
            cell_sizes = [node for node in cell if node.tag == tag("cellSz")]
            if len(cell_sizes) != 1:
                raise ValueError("cell size")
            actual_widths.append(int(cell_sizes[0].get("width", "-1")))
            actual_heights.append(int(cell_sizes[0].get("height", "-1")))
            arrays = list(cell.iter(tag("linesegarray")))
            segments = list(arrays[0]) if len(arrays) == 1 else []
            if line_counts is None:
                if arrays:
                    raise ValueError("target cache")
                continue
            if len(arrays) != 1 or any(segment.tag != tag("lineseg") for segment in segments):
                raise ValueError("line cache")
            widths = {int(segment.get("horzsize", "-1")) for segment in segments}
            if len(widths) != 1:
                raise ValueError("line width")
            actual_counts.append(len(segments))
            actual_line_widths.append(next(iter(widths)))
            actual_positions.append([int(segment.get("textpos", "-1")) for segment in segments])
        if actual_widths != cell_widths or actual_heights != [3900, 3900, 1300, 1300]:
            raise ValueError("cell dimensions")
        if line_counts is not None and (actual_counts != line_counts or actual_line_widths != line_widths):
            raise ValueError("line semantics")
        if relative == OUTPUT_PATH and actual_positions != [[0], [0, 5, 8], [0], [0]]:
            raise ValueError("line positions")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError):
        errors.append(label + "_semantics")


def validate_pdf(root: Path, errors: list[str]) -> None:
    try:
        payload = base.bounded_file(root, PDF_PATH, 8 * 1024 * 1024).read_bytes()
        if len(payload) != 15421 or not payload.startswith(b"%PDF-") or b"%%EOF" not in payload[-1024:]:
            errors.append("pdf_semantics")
    except (OSError, ValueError):
        errors.append("pdf_semantics")


def validate_markers(root: Path, errors: list[str]) -> int:
    count = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = base.bounded_file(root, relative, 512_000).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
            continue
        count += 1
        if any(marker not in source for marker in markers):
            errors.append("implementation_marker")
    return count


def result(errors: list[str], source_locks: int, evidence_files: int,
           implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-layout-target-v2-validation/v1",
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
        "P06_TABLE_LAYOUT_TARGET_V2_CONTRACT_PASS "
        f"source_locks={report['source_locks']} "
        f"evidence_files={report['evidence_files']} "
        f"implementation_files={report['implementation_files']}"
    )
