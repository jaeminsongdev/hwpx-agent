#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-formula-hwpx-v1.json"
REPORT = "implementation/p06/P06-06_FORMULA_HWPX_ADAPTER_REPORT.md"
MIGRATION = "protocol/migrations/p06-table-formula-v1-to-hwpx-v1.md"
SOURCE_DIR = "fixtures/target-build/p06-06-formula-source-20260907-01"
SOURCE_HWPX = f"{SOURCE_DIR}/source.hwpx"
SOURCE_PDF = f"{SOURCE_DIR}/source.pdf"
TRACE = f"{SOURCE_DIR}/trace.json"
PROGRESS = f"{SOURCE_DIR}/trace.json.progress.jsonl"

SOURCE_LOCKS = {
    "protocol/private/p06-table-formula-v1.json":
        "5bec3721f4283549af8cd1e7c850600d56ddc4a02a329298cecfa5920d7db0f3",
    "implementation/p06/tools/create-hancom-2020-formula-source.ps1":
        "ff5ee4457a061e6c1dfc99ed6faa7990e8da1350b2f1b37af403da87a1e638b3",
    "implementation/p06/tools/run-hancom-2020-formula-source.ps1":
        "8088beff9f4c9652cc54c765ceada439e6d09cabef4f8fc5d789dd5ee6f2889f",
    "crates/hwpx-package/src/table_formula.rs":
        "faf2c694780a2f14fbd4f0443fd2fe2ee24be673836f935ec0e72081144332dc",
    "crates/hwpx-package/tests/table_formula.rs":
        "c279de8ab7e976071446d5fa74d7bb24fc5c39d6383f82aadf03b365eafef5f3",
    "crates/hwpx-package/examples/p06_06_table_formula_source_adapter.rs":
        "630d7efe3dbd4409378d5eea0519ba4f5131e9bcea7d8e7996f8249ccabc51ce",
}

EVIDENCE = {
    SOURCE_HWPX: ("d968cae419a3754b1dc65eb845f9d1d6bf8bbb486736359cd9b838a78e47d38f", 13828),
    SOURCE_PDF: ("adbd88f65b0a31ab769c0a277d340a1ffcb8165a93b263c557eaff4d1baeab26", 9830),
    TRACE: ("2bb67d3d53611dcbfb70ab014e5f3499bcc44885b7ce5ed024798e8abd10a1d7", 2051),
    PROGRESS: ("c2d0ce33751b53dacf688369b366c86de606c160f6e189253d7c674891cb3348", 5305),
}

IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_formula.rs": (
        "hwpx-agent.table-formula-hwpx.hancom-2020/1",
        "require_left_prefix",
        "digest_excluding",
        "UnsupportedFormula",
        "UnsupportedCache",
    ),
    "crates/hwpx-package/tests/table_formula.rs": (
        "reads_exact_hancom_2020_left_formula_as_locale_neutral_ast",
        "lowering_updates_only_command_cache_and_visible_result",
        "source_field_shape_and_identity_drift_fail_closed",
        "finite_limits_are_enforced_before_publication",
    ),
    "crates/hwpx-package/examples/p06_06_table_formula_source_adapter.rs": (
        "hwpx-agent.p06-06-source-adapter-check/1",
        "identity lowering did not preserve the exact section bytes",
        "raw_native_command_exposed",
    ),
    REPORT: (
        "actual source capture and exact adapter component",
        "P06-06 and P06 are not complete",
        EVIDENCE[SOURCE_HWPX][0],
    ),
    MIGRATION: (
        "There is no automatic migration",
        "P06-06 remains open",
        "Other PCs and Hangul versions remain unclaimed",
    ),
}

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"


def tag(local: str) -> str:
    return f"{{{HP}}}{local}"


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


def bounded_bytes(root: Path, relative: str, limit: int = 64 * 1024 * 1024) -> bytes:
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


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json(bounded_bytes(root, CONTRACT, 512_000))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0)
    validate_contract(contract, errors)
    source_count = validate_source_locks(root, contract, errors)
    evidence_count = validate_evidence(root, errors)
    validate_hwpx(root, errors)
    validate_trace(root, errors)
    implementation_count = validate_markers(root, errors)
    return result(sorted(set(errors)), source_count, evidence_count, implementation_count)


def validate_contract(contract: dict[str, Any], errors: list[str]) -> None:
    expected_keys = {
        "schema_version", "model_schema_version", "adapter_profile_id", "scope", "predecessor",
        "source_lock_canonicalization", "source_locks", "capture_evidence",
        "actual_source_semantics", "actual_capture_runtime", "adapter_policy", "gate_decision",
        "failure_policy", "migration", "report", "not_claimed",
    }
    if set(contract) != expected_keys:
        errors.append("contract_shape")
    exact = {
        "schema_version": "hwpx-agent.p06-06-table-formula-hwpx-contract/v1",
        "model_schema_version": "hwpx-agent.table-formula/v1",
        "adapter_profile_id": "hwpx-agent.table-formula-hwpx.hancom-2020/1",
        "scope": "p06_06_exact_current_pc_hancom_2020_formula_source_and_adapter_component",
        "source_lock_canonicalization": "exact_file_bytes_sha256",
        "migration": MIGRATION,
        "report": REPORT,
    }
    for key, value in exact.items():
        if contract.get(key) != value:
            errors.append(key)
    if contract.get("predecessor") != {
        "path": "protocol/private/p06-table-formula-v1.json",
        "sha256": SOURCE_LOCKS["protocol/private/p06-table-formula-v1.json"],
        "state": "immutable_pure_formula_contract",
    }:
        errors.append("predecessor")
    if contract.get("gate_decision") != {
        "actual_hancom_2020_source_capture": "pass",
        "source_identity_adapter_check": "pass",
        "adapter_component": "pass",
        "row_column_structural_differential": "not_run",
        "product_target_hancom_2020_oracle": "not_run",
        "p06_06": "in_progress",
        "p06": "in_progress",
    }:
        errors.append("gate_decision")
    not_claimed = contract.get("not_claimed")
    if not isinstance(not_claimed, dict) or set(not_claimed.values()) != {False}:
        errors.append("not_claimed")
    semantics = contract.get("actual_source_semantics")
    if not isinstance(semantics, dict) or semantics.get("locale_neutral_formula") != "SUM(A1:B1)" \
            or semantics.get("unverified_cache_value") != 42 \
            or semantics.get("identity_lowering") != "pass_exact_section_bytes" \
            or semantics.get("raw_native_command_exposed") is not False:
        errors.append("actual_source_semantics")
    policy = contract.get("adapter_policy")
    if not isinstance(policy, dict) or policy.get("cache_provenance") \
            != "unverified_until_exact_target_oracle_receipt" \
            or policy.get("unknown_shape_or_formula") != "reject" \
            or policy.get("public_native_command") != "forbidden":
        errors.append("adapter_policy")


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
    count = 0
    for path, (expected_hash, expected_size) in EVIDENCE.items():
        try:
            data = bounded_bytes(root, path)
        except (OSError, ValueError):
            errors.append("evidence_path_or_size")
            continue
        count += 1
        if len(data) != expected_size or sha256(data) != expected_hash:
            errors.append("evidence_digest")
    try:
        if not bounded_bytes(root, SOURCE_PDF).startswith(b"%PDF-"):
            errors.append("pdf_signature")
    except (OSError, ValueError):
        errors.append("pdf_signature")
    return count


def validate_hwpx(root: Path, errors: list[str]) -> None:
    try:
        with zipfile.ZipFile(safe_path(root, SOURCE_HWPX)) as archive:
            names = archive.namelist()
            if names.count("Contents/section0.xml") != 1:
                raise ValueError("section cardinality")
            section = archive.read("Contents/section0.xml")
        if sha256(section) != "5d106d507b899dbbff1f0b790e975889d88cc9974f89d4c4163b8f6f6afa0de8":
            errors.append("section_digest")
        root_element = ET.fromstring(section)
        tables = root_element.findall(f".//{tag('tbl')}")
        if len(tables) != 1 or tables[0].get("rowCnt") != "1" or tables[0].get("colCnt") != "3":
            raise ValueError("table shape")
        cells = tables[0].findall(f"./{tag('tr')}/{tag('tc')}")
        addresses = sorted(
            (int(cell.find(tag("cellAddr")).get("rowAddr")),
             int(cell.find(tag("cellAddr")).get("colAddr"))) for cell in cells
        )
        if addresses != [(0, 0), (0, 1), (0, 2)]:
            raise ValueError("cell coverage")
        begins = tables[0].findall(f".//{tag('fieldBegin')}")
        ends = tables[0].findall(f".//{tag('fieldEnd')}")
        if len(begins) != 1 or len(ends) != 1:
            raise ValueError("formula cardinality")
        begin, end = begins[0], ends[0]
        if begin.attrib != {
            "id": "1188510575", "type": "FORMULA", "name": "", "editable": "0",
            "dirty": "0", "zorder": "-1", "fieldid": "627469685",
        } or end.attrib != {"beginIDRef": "1188510575", "fieldid": "627469685"}:
            raise ValueError("field identity")
        parameters = list(begin.find(tag("parameters")))
        values = [(item.tag, item.get("name"), item.text or "") for item in parameters]
        if len(values) != 5 or values[0] != (tag("integerParam"), "Prop", "8"):
            raise ValueError("parameter shape")
        named = {name: text for _, name, text in values[1:]}
        formula = named.get("Formula")
        result_format = named.get("ResultFormat")
        last_result = named.get("LastResult")
        if formula != "=SUM(LEFT)" or result_format != "%g," or last_result != "42" \
                or named.get("Command") != f"{formula}??{result_format};;{last_result}":
            raise ValueError("formula values")
        formula_cell = next(cell for cell in cells if cell.find(tag("cellAddr")).get("colAddr") == "2")
        visible = [value.text or "" for value in formula_cell.findall(f".//{tag('t')}")]
        if visible[:2] != ["42", ""]:
            raise ValueError("visible result")
    except (OSError, KeyError, TypeError, ValueError, ET.ParseError, zipfile.BadZipFile):
        errors.append("source_hwpx_semantics")


def validate_trace(root: Path, errors: list[str]) -> None:
    try:
        trace = load_json(bounded_bytes(root, TRACE, 256_000))
        watchdog = trace.get("watchdog", {})
        checks = (
            trace.get("state") == "pass",
            trace.get("target_build") == "11.0.0.9136",
            trace.get("table_create") == "pass",
            trace.get("operand_cells_written") == 2,
            trace.get("formula_action") == "pass",
            trace.get("save_hwpx") == "pass",
            trace.get("reopen_hwpx") == "pass",
            trace.get("save_pdf") == "pass",
            trace.get("pre_save_text_sha256") == trace.get("reopen_text_sha256"),
            trace.get("raw_document_text_present") is False,
            trace.get("raw_formula_or_command_present") is False,
            trace.get("user_document_opened") is False,
            trace.get("external_network_invoked") is False,
            trace.get("registry_or_system_setting_changed") is False,
            trace.get("computer_use_click_or_type_invoked") is False,
            watchdog.get("timed_out") is False,
            watchdog.get("child_exit_code") == 0,
            watchdog.get("remaining_hwp_process_count") == 0,
        )
        if not all(checks):
            errors.append("trace_semantics")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("trace_semantics")


def validate_markers(root: Path, errors: list[str]) -> int:
    count = 0
    for path, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_bytes(root, path, 4 * 1024 * 1024).decode("utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path_or_encoding")
            continue
        count += 1
        if any(marker not in text for marker in markers):
            errors.append("implementation_markers")
    return count


def result(errors: list[str], source_locks: int, evidence_files: int,
           implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-06-table-formula-hwpx-validation/v1",
        "state": "pass" if not errors else "fail",
        "errors": errors,
        "source_locks": source_locks,
        "evidence_files": evidence_files,
        "implementation_files": implementation_files,
        "actual_source_capture": "pass" if not errors else "not_proven",
        "adapter_component": "pass" if not errors else "not_proven",
        "product_target_oracle": "not_run",
        "p06_06": "in_progress",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
