#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

try:
    from tools.p06 import validate_table_create_hwpx_contract as predecessor
except ModuleNotFoundError:
    import validate_table_create_hwpx_contract as predecessor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-create-target-v2.json"
MIGRATION = "protocol/migrations/p06-table-create-hwpx-v1-to-target-v2.md"
REPORT = "implementation/p06/P06-09_TABLE_CREATE_TARGET_READBACK_REPORT.md"
RECEIPT = "implementation/p06/evidence/target/p06-table-create.current-2020.attempt05.v2.json"
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-create-target-20260913-06"
MANIFEST_PATH = f"{TARGET_DIRECTORY}/fixture-manifest.json"
TRACE_PATH = f"{TARGET_DIRECTORY}/target-batch-readback-20260913-05.json"
PROGRESS_PATH = f"{TRACE_PATH}.progress.jsonl"
MANIFEST_SHA256 = "6595f8fa69798459f58aea01a18c954f8c39852be5c5b310aef4f5efa3c61263"
TRACE_SHA256 = "4bdefce382bf859cb01214606c5ca8fc15966333c884b21fa25dc3f2298b1da3"
PROGRESS_SHA256 = "df75d4207e88301750f98220d192b18b94d228fbe6e6a80e8a2c102e52562494"
RECEIPT_SHA256 = "ed30dd347471c184dd9efc8292fbfa974a08d40209aa1d48c195adab4878d1dc"

EXPECTED_TARGET = {
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

SOURCE_LOCKS = {
    "protocol/private/p06-table-create-hwpx-v1.json":
        "c7389decf37b2563c7221b5e65cc359190eb6d835331a7d2837acf9d98bc1d5f",
    "tools/p06/validate_table_create_hwpx_contract.py":
        "2a6c590c25501d740cfa3f3d99133c44e66fb22b108406f9f64d1a320163d7c2",
    "crates/hwpx-package/src/table_ruling_hwpx/create_hwpx.rs":
        "ebd710a2409612eebbe30951f8e738a71b4ab615be8eba1a0579a08ad2b718f3",
    "crates/hwpx-package/examples/p06_09_table_create_target_fixture.rs":
        "90b733813b4c3ebc70690792db7fd35a8cb6db0adf76136735e5f902180a5d3c",
    "crates/hwpx-package/examples/p06_09_table_create_target_oracle.rs":
        "e53c6816e65c725ccabb89c8bf7a69a40c33e7d7c4f73b8e133aca174438bb27",
    "implementation/p06/tools/run-hancom-2020-table-create-target-batch-engine.ps1":
        "20255bcc0492ca82c122f4b5ff5823e96ca4afa38ac1cde1b68f69d7f3404d4d",
    "implementation/p06/tools/run-hancom-2020-table-create-target-batch-readback.ps1":
        "d77d30e4404403f9144a58a5f0806f4e222b83beb317c12ad707619f16f495d6",
    "implementation/p06/tests/Test-Hancom2020TableCreateTargetBatchReadback.ps1":
        "adc1faf66fa0a4cbb024acf02ddeb84187555d19d0afef98cb08c4ecef2cacfb",
}

CASE_SPECS = [
    {
        "case_id": "arbitrary-3x4-nonuniform",
        "feature_id": "TABLE-001",
        "capability_id": "table.create",
        "stem": "table-001-create-3x4-nonuniform",
        "input_sha256": "b6d000efb0076f3b63ea7247601e8efc366f215f91c5d35927ca92de5c7b8021",
        "input_bytes": 13287,
        "output_sha256": "95dbabfa7035073141d185df709b0900b24a1f139ad21a08926fcf2c8bca743e",
        "output_bytes": 17013,
        "output_section_sha256": "14b04e84bfe85210ac193d5d079667d250552fcd4e9adf824830930ed302cfa2",
        "pdf_sha256": "8f4dac281bed163fed66399744c52bca601316caaf9f9ef2aeaaeedf7d3f8d6a",
        "pdf_bytes": 10210,
        "state_sha256": "68b06e75f952731c9d466e403adbfbbce7a879d98459308b1311171df481fb4f",
        "grid_sha256": "5855c019ffe32cc9d0b63ceef7d575a19e659e1f97bc0927b310ea13248cdd28",
        "rows": 3,
        "columns": 4,
        "master_cells": 12,
        "row_heights": [4000, 5000, 6000],
        "column_widths": [7000, 9000, 11000, 13000],
        "cache_count": 22,
        "cache_sha256": "ec530ea7db51254826f4c8f0873ce944f3c9e683e20aa7f9fa2de60d5a6d336d",
        "png_sha256": "3f1e12ad3563928b62e620d5de4fce3b9f0b6bcdc68903bf8e3a85bf7972b242",
        "png_bytes": 11687,
    },
    {
        "case_id": "boundary-1x1",
        "feature_id": "TABLE-001",
        "capability_id": "table.create",
        "stem": "table-001-create-1x1",
        "input_sha256": "2347898eef3bb0e2c0d17d58adcb93a4c0e1591138def2171772962553632cf2",
        "input_bytes": 13160,
        "output_sha256": "6d37e47b31aaa7e02bb45b96860e480083b3b5604f95378e88ef7ab0ce879d06",
        "output_bytes": 14746,
        "output_section_sha256": "8e25af52ccf2b2118cd0ba9bb58ce2098defef361f7b45e73b30f3ea2396f3ed",
        "pdf_sha256": "f860b1f7fd0e60610695fe1a5032ca91cee3c79007e8f83d8228e3927c6e7e06",
        "pdf_bytes": 9998,
        "state_sha256": "8065ba312660dfab51158fdf8ac1474d433499bdebcb2f197c35e50e0f602a8f",
        "grid_sha256": "e6f177fd2d4d7d38e326fda013d9b156297b6db67ce1ba66b88f6370c80af82a",
        "rows": 1,
        "columns": 1,
        "master_cells": 1,
        "row_heights": [6000],
        "column_widths": [12000],
        "cache_count": 11,
        "cache_sha256": "39be4fbba289d41cb9f088c90cb3b857025eb2cf7ae9416efc1348af5d696f59",
        "png_sha256": "23528890bc49e169a98fed1b73de7c28a2adbe44eeb1bcf4ed7c3a11dfe1fcca",
        "png_bytes": 11600,
    },
]

HISTORICAL = [
    ("fixtures/target-build/p06-09-table-create-target-20260913-02/"
     "target-batch-readback-20260913-01.json",
     "e8a9a1e0bcf10b1ace7e3272238c43158132a4c6fa8dd53269041db21195debd", 3721),
    ("fixtures/target-build/p06-09-table-create-target-20260913-02/"
     "target-batch-readback-20260913-01.json.progress.jsonl",
     "8d385a52197eadae49cb8554f86a3c710697ad1db2ae585471d986cc4509cfa3", 1443),
    ("fixtures/target-build/p06-09-table-create-target-20260913-03/"
     "target-batch-readback-20260913-02.json",
     "081850f250d8c4619730ad5652a962b9e2be9c2c9d0b843b8af766e4f6f00471", 3721),
    ("fixtures/target-build/p06-09-table-create-target-20260913-03/"
     "target-batch-readback-20260913-02.json.progress.jsonl",
     "d074436932a0d48bd9c09a1f75bc8708c6e4b9f94dde7a3d8a0e65abe38e3dc8", 1443),
    ("fixtures/target-build/p06-09-table-create-target-20260913-04/"
     "target-batch-readback-20260913-03.json",
     "393300ffef41cc1793d0a4638e3f6ede820b914c2c65c8707c239b7daba9a526", 5644),
    ("fixtures/target-build/p06-09-table-create-target-20260913-04/"
     "target-batch-readback-20260913-03.json.progress.jsonl",
     "552e6413923984d7773a374fd2335380b568c3d099f58ecad2d38d004321afaa", 10837),
    ("fixtures/target-build/p06-09-table-create-target-20260913-05/"
     "target-batch-readback-20260913-04.json",
     "5cff75e7a1976e3521048e0eb6352d2be16fd5b8c63c48731c7c831f39914631", 5598),
    ("fixtures/target-build/p06-09-table-create-target-20260913-05/"
     "target-batch-readback-20260913-04.json.progress.jsonl",
     "39c63368d5a1c13f4760600645dcade1a578404d6f3c1ee3349a121268843921", 8484),
]

NOT_CLAIMED = {
    "automation_runtime": False,
    "differential_exact_match": False,
    "nonblank_or_merged_initial_table": False,
    "repeat_header_or_caption_creation": False,
    "arbitrary_native_template": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_hancom_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def safe_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError("unsafe path")
    candidate = root.joinpath(*pure.parts)
    resolved_root = root.resolve()
    resolved_parent = candidate.parent.resolve()
    if resolved_parent != resolved_root and resolved_root not in resolved_parent.parents:
        raise ValueError("path escape")
    return candidate


def bounded_bytes(root: Path, relative: str, limit: int = 8 * 1024 * 1024) -> bytes:
    path = safe_path(root, relative)
    stat = path.lstat()
    if path.is_symlink() or not path.is_file() or stat.st_size > limit:
        raise ValueError("not a bounded regular file")
    return path.read_bytes()


def load_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def record(path: str, sha256: str, size: int) -> dict[str, Any]:
    return {"path": path, "sha256": sha256, "bytes": size}


def input_path(case: dict[str, Any]) -> str:
    return f"{TARGET_DIRECTORY}/{case['stem']}.hwpx"


def output_path(case: dict[str, Any]) -> str:
    return f"{TARGET_DIRECTORY}/{case['stem']}.hancom-2020-readback.hwpx"


def pdf_path(case: dict[str, Any]) -> str:
    return f"{TARGET_DIRECTORY}/{case['stem']}.hancom-2020-render.pdf"


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    predecessor_result = predecessor.validate(root)
    if predecessor_result.get("state") != "pass":
        errors.append("predecessor")
    try:
        contract = load_json(bounded_bytes(root, CONTRACT, 512_000))
        if not isinstance(contract, dict):
            raise ValueError("contract root")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0, "fail")

    validate_contract(contract, errors)
    source_count = validate_source_locks(root, contract.get("source_locks"), errors)
    evidence_count = validate_evidence_files(root, errors)
    validate_manifest(root, errors)
    validate_trace(root, errors)
    validate_progress(root, errors)
    validate_hwpx_and_pdf_artifacts(root, errors)
    validate_receipt(root, errors)
    validate_historical_semantics(root, errors)
    implementation_count = validate_markers(root, errors)
    return result(
        errors, source_count, evidence_count, implementation_count,
        str(predecessor_result.get("state")),
    )


def validate_contract(contract: dict[str, Any], errors: list[str]) -> None:
    expected_keys = {
        "schema_version", "scope", "predecessor", "source_lock_canonicalization",
        "source_locks", "exact_target", "successful_attempt", "historical_attempts",
        "cases", "render_oracle", "gate_decision", "failure_policy", "migration",
        "report", "evidence_receipt", "not_claimed",
    }
    if set(contract) != expected_keys:
        errors.append("contract_shape")
    exact = {
        "schema_version": "hwpx-agent.p06-09-table-create-target-contract/v2",
        "scope": "p06_09_table_001_exact_current_pc_hancom_2020_save_reopen_pdf_typed_oracle",
        "predecessor": {
            "path": predecessor.CONTRACT,
            "sha256": SOURCE_LOCKS[predecessor.CONTRACT],
            "state": "immutable_static_direct_hwpx_integration_contract",
        },
        "source_lock_canonicalization": "utf8_text_crlf_to_lf_sha256",
        "exact_target": EXPECTED_TARGET,
        "successful_attempt": {
            "id": "20260913-05",
            "directory": TARGET_DIRECTORY,
            "manifest": record(MANIFEST_PATH, MANIFEST_SHA256, 5261),
            "trace": record(TRACE_PATH, TRACE_SHA256, 5582),
            "progress": {**record(PROGRESS_PATH, PROGRESS_SHA256, 10837), "events": 37},
            "receipt": record(RECEIPT, RECEIPT_SHA256, 7431),
            "case_count": 2,
            "state": "pass",
        },
        "historical_attempts": {
            "failed_attempt_ids": [f"20260913-{index:02}" for index in range(1, 5)],
            "evidence": [record(*item) for item in HISTORICAL],
            "promoted_to_pass": 0,
            "decision": "immutable_failed_evidence_not_promoted",
        },
        "cases": [contract_case(case) for case in CASE_SPECS],
        "render_oracle": {
            "state": "pass", "pdf_count": 2, "pages_each": 1,
            "page_size_points": [595, 841], "producer": "Hancom PDF 1.3.0.550",
            "renderer": "pdftoppm 26.07.0", "dpi": 144,
            "pixel_size": [1190, 1682], "inspection_detail": "original",
            "review_actor": "assistant_visual_review", "clipping": False,
            "overlap": False, "blank_pages": [], "black_boxes": False,
        },
        "gate_decision": {
            "TABLE-001": "oracle_verified",
            "actual_hancom_2020_save_reopen": "pass",
            "actual_hancom_2020_target_build": "pass",
            "render_diff": "pass", "rollback_or_retry": "pass",
            "automation_runtime": "not_run", "differential": "not_run",
            "p06_09": "in_progress", "p06": "in_progress",
        },
        "migration": MIGRATION,
        "report": REPORT,
        "evidence_receipt": RECEIPT,
        "not_claimed": NOT_CLAIMED,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            errors.append(key)
    failure = contract.get("failure_policy")
    if (
        not isinstance(failure, list)
        or len(failure) != 8
        or len(set(failure)) != 8
        or any(not isinstance(item, str) or not item for item in failure)
    ):
        errors.append("failure_policy")


def contract_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"], "feature_id": case["feature_id"],
        "capability_id": case["capability_id"], "input_sha256": case["input_sha256"],
        "output_sha256": case["output_sha256"], "pdf_sha256": case["pdf_sha256"],
        "target_state_sha256": case["state_sha256"],
        "target_grid_sha256": case["grid_sha256"], "rows": case["rows"],
        "columns": case["columns"], "master_cells": case["master_cells"],
        "payload_blocks": 0, "formulas": 0, "preexisting_formula_fields": 1,
        "renderer_cache_count": case["cache_count"],
        "renderer_cache_sha256": case["cache_sha256"],
    }


def validate_source_locks(root: Path, declared: Any, errors: list[str]) -> int:
    expected = [{"path": path, "sha256": sha256} for path, sha256 in SOURCE_LOCKS.items()]
    if declared != expected:
        errors.append("source_locks_exact")
    for path, sha256 in SOURCE_LOCKS.items():
        try:
            source = bounded_bytes(root, path, 4_000_000).decode("utf-8")
            if "\r" in source.replace("\r\n", ""):
                raise ValueError("bare CR")
            canonical = source.replace("\r\n", "\n").encode("utf-8")
            if digest(canonical) != sha256:
                errors.append("source_lock_digest")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("source_lock_path")
    return len(SOURCE_LOCKS)


def evidence_records() -> list[tuple[str, str, int]]:
    records = [
        (MANIFEST_PATH, MANIFEST_SHA256, 5261),
        (TRACE_PATH, TRACE_SHA256, 5582),
        (PROGRESS_PATH, PROGRESS_SHA256, 10837),
        (RECEIPT, RECEIPT_SHA256, 7431),
    ]
    records.extend(HISTORICAL)
    for case in CASE_SPECS:
        records.extend([
            (input_path(case), case["input_sha256"], case["input_bytes"]),
            (output_path(case), case["output_sha256"], case["output_bytes"]),
            (pdf_path(case), case["pdf_sha256"], case["pdf_bytes"]),
        ])
    return records


def validate_evidence_files(root: Path, errors: list[str]) -> int:
    for path, sha256, size in evidence_records():
        try:
            data = bounded_bytes(root, path, 16 * 1024 * 1024)
            if len(data) != size or digest(data) != sha256:
                errors.append("evidence_digest")
        except (OSError, ValueError):
            errors.append("evidence_path")
    return len(evidence_records())


def validate_manifest(root: Path, errors: list[str]) -> None:
    try:
        manifest = load_json(bounded_bytes(root, MANIFEST_PATH, 256_000))
        cases = manifest["cases"]
        if (
            manifest["schema_version"] != "hwpx-agent.p06-09-table-create-target-fixture/v1"
            or manifest["source_ancestor_sha256"]
            != "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5"
            or manifest["actual_hangul_2020"] is not False
            or [manifest[key] for key in ("render", "automation", "differential")]
            != ["not_run", "not_run", "not_run"]
            or len(cases) != 2
        ):
            raise ValueError("manifest root")
        for actual, spec in zip(cases, CASE_SPECS, strict=True):
            if (
                actual["case_id"] != spec["case_id"]
                or actual["feature_id"] != "TABLE-001"
                or actual["capability_id"] != "table.create"
                or actual["file"] != f"{spec['stem']}.hwpx"
                or actual["sha256"] != spec["input_sha256"]
                or actual["selected_table_ordinal"] != 1
                or actual["rows"] != spec["rows"]
                or actual["columns"] != spec["columns"]
                or actual["row_heights_hwpunit"] != spec["row_heights"]
                or actual["column_widths_hwpunit"] != spec["column_widths"]
                or actual["target_state_sha256"] != spec["state_sha256"]
                or actual["target_grid_sha256"] != spec["grid_sha256"]
                or actual["created_master_cell_count"] != spec["master_cells"]
                or actual["payload_block_count"] != 0
                or actual["formula_count"] != 0
                or actual["page_split_preserved"] is not True
                or len(actual["binding"]["cells"]) != spec["master_cells"]
                or any(cell["payload_block_ids"] for cell in actual["binding"]["cells"])
            ):
                raise ValueError("manifest case")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        errors.append("manifest_semantics")


def validate_trace(root: Path, errors: list[str]) -> None:
    try:
        trace = load_json(bounded_bytes(root, TRACE_PATH, 256_000))
        target = trace["target"]
        if (
            trace["schema_version"]
            != "hwpx-agent.p06-09-hancom-2020-table-create-target-batch-readback/v1"
            or trace["state"] != "pass"
            or trace["fixture_manifest_sha256"] != MANIFEST_SHA256
            or trace["case_count"] != 2
            or trace["completed_case_count"] != 2
            or trace["error_code"] is not None
            or trace["failed_phase"] is not None
            or target["prog_id"] != EXPECTED_TARGET["prog_id"]
            or target["registry_view"] != EXPECTED_TARGET["registry_view"]
            or target["client"] != EXPECTED_TARGET["client"]
            or target["file_version"] != EXPECTED_TARGET["build"]
            or target["executable_sha256"] != EXPECTED_TARGET["executable_sha256"]
            or any(trace[key] is not False for key in (
                "raw_document_text_present", "user_document_scanned",
                "external_network_invoked", "registry_or_system_setting_changed",
                "computer_use_click_or_type_invoked",
            ))
        ):
            raise ValueError("trace root")
        phases = {
            "open_input", "read_input", "save_as_hwpx", "close_input",
            "reopen_output", "read_output", "export_pdf", "close_output",
        }
        for actual, spec in zip(trace["cases"], CASE_SPECS, strict=True):
            if (
                actual["feature_id"] != "TABLE-001"
                or actual["capability_id"] != "table.create"
                or actual["input_sha256"] != spec["input_sha256"]
                or actual["input_unchanged"] is not True
                or actual["input_text_sha256"] != actual["output_text_sha256"]
                or actual["output_sha256"] != spec["output_sha256"]
                or actual["output_saved"] is not True
                or actual["render_pdf_saved"] is not True
                or actual["render_pdf_sha256"] != spec["pdf_sha256"]
                or actual["render_pdf_bytes"] != spec["pdf_bytes"]
                or actual["render_pdf_signature_valid"] is not True
                or actual["render_pdf_export_method"] != "IXHwpDocument.SaveAs/PDF"
                or set(actual["phases"]) != phases
                or any(state != "pass" for state in actual["phases"].values())
                or actual["error_code"] is not None
                or actual["failed_phase"] is not None
            ):
                raise ValueError("trace case")
        watchdog = trace["watchdog"]
        if (
            watchdog["timed_out"] is not False
            or watchdog["child_exit_code"] != 0
            or watchdog["output_drained"] is not True
            or watchdog["cleanup_refused_count"] != 0
            or watchdog["cleanup_error_count"] != 0
            or watchdog["remaining_hwp_process_count"] != 0
            or watchdog["progress_valid"] is not True
            or watchdog["progress_event_count"] != 37
            or watchdog["progress_last_phase"] != "terminal"
            or watchdog["progress_last_state"] != "pass"
        ):
            raise ValueError("watchdog")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        errors.append("trace_semantics")


def validate_progress(root: Path, errors: list[str]) -> None:
    try:
        lines = bounded_bytes(root, PROGRESS_PATH, 256_000).decode("utf-8").splitlines()
        if len(lines) != 37:
            raise ValueError("progress count")
        events = [load_json(line.encode("utf-8")) for line in lines]
        for index, event in enumerate(events, 1):
            if (
                event["schema_version"]
                != "hwpx-agent.p06-09-table-create-batch-progress/v1"
                or event["sequence"] != index
                or event["raw_document_text_present"] is not False
            ):
                raise ValueError("progress event")
        if events[-1]["phase"] != "terminal" or events[-1]["state"] != "pass":
            raise ValueError("progress terminal")
    except (OSError, KeyError, TypeError, ValueError, UnicodeDecodeError, json.JSONDecodeError):
        errors.append("progress_semantics")


def validate_hwpx_and_pdf_artifacts(root: Path, errors: list[str]) -> None:
    for spec in CASE_SPECS:
        try:
            validate_hwpx(bounded_bytes(root, input_path(spec)), spec, False)
            validate_hwpx(bounded_bytes(root, output_path(spec)), spec, True)
        except (OSError, KeyError, ValueError, ET.ParseError, zipfile.BadZipFile):
            errors.append("hwpx_semantics")
        try:
            validate_pdf(root, pdf_path(spec), spec)
        except (OSError, ValueError, ImportError):
            errors.append("pdf_semantics")


def validate_hwpx(data: bytes, spec: dict[str, Any], output: bool) -> None:
    paragraph_ns = "http://www.hancom.co.kr/hwpml/2011/paragraph"
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if (
            len(names) != 11
            or len(names) != len(set(names))
            or any(item.flag_bits & 1 for item in infos)
            or any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names)
        ):
            raise ValueError("package entries")
        section = archive.read("Contents/section0.xml")
    if output and digest(section) != spec["output_section_sha256"]:
        raise ValueError("output section")
    root = ET.fromstring(section)
    tables = root.findall(f".//{{{paragraph_ns}}}tbl")
    if len(tables) != 2:
        raise ValueError("table count")
    selected = tables[1]
    cells = selected.findall(f".//{{{paragraph_ns}}}tc")
    formulas = [
        element for element in root.findall(f".//{{{paragraph_ns}}}fieldBegin")
        if element.attrib.get("type") == "FORMULA"
    ]
    if (
        selected.attrib.get("rowCnt") != str(spec["rows"])
        or selected.attrib.get("colCnt") != str(spec["columns"])
        or len(cells) != spec["master_cells"]
        or len(formulas) != 1
    ):
        raise ValueError("typed shape")
    for cell in cells:
        span = cell.find(f"{{{paragraph_ns}}}cellSpan")
        if span is None or span.attrib != {"colSpan": "1", "rowSpan": "1"}:
            raise ValueError("cell span")


def validate_pdf(root: Path, relative: str, spec: dict[str, Any]) -> None:
    from pypdf import PdfReader

    data = bounded_bytes(root, relative, 32 * 1024 * 1024)
    if not data.startswith(b"%PDF-"):
        raise ValueError("pdf signature")
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise ValueError("pdf parse") from exc
    if reader.is_encrypted or len(reader.pages) != 1 or reader.pdf_header != "%PDF-1.4":
        raise ValueError("pdf profile")
    page = reader.pages[0]
    if [float(page.mediabox.width), float(page.mediabox.height)] != [595.0, 841.0]:
        raise ValueError("pdf page")
    names = reader.trailer["/Root"].get("/Names", {})
    if "/JavaScript" in names:
        raise ValueError("pdf javascript")
    metadata = reader.metadata or {}
    if (
        str(metadata.get("/Producer", "")) != "Hancom PDF 1.3.0.550"
        or str(metadata.get("/Creator", "")) != "Hwp 2020 11.0.0.9136"
        or len(data) != spec["pdf_bytes"]
    ):
        raise ValueError("pdf metadata")


def validate_receipt(root: Path, errors: list[str]) -> None:
    try:
        receipt = load_json(bounded_bytes(root, RECEIPT, 512_000))
        attempt = receipt["attempt"]
        if (
            receipt["schema_version"]
            != "hwpx-agent.p06-09-table-create-current-2020-evidence/v2"
            or attempt["id"] != "20260913-05"
            or attempt["target"] != EXPECTED_TARGET
            or attempt["completed_cases"] != 2
            or attempt["failed_case_id"] is not None
            or attempt["timed_out"] is not False
            or attempt["remaining_hwp_process_count"] != 0
            or attempt["user_access_prompt_action"] != "not_recorded"
            or receipt["not_claimed"] != NOT_CLAIMED
        ):
            raise ValueError("receipt root")
        for actual, spec in zip(receipt["cases"], CASE_SPECS, strict=True):
            oracle = actual["oracle"]
            if (
                actual["case_id"] != spec["case_id"]
                or actual["input"] != {
                    **record(input_path(spec), spec["input_sha256"], spec["input_bytes"]),
                    "unchanged": True,
                }
                or actual["output"] != {
                    **record(output_path(spec), spec["output_sha256"], spec["output_bytes"]),
                    "section_sha256": spec["output_section_sha256"],
                }
                or actual["pdf"] != {
                    **record(pdf_path(spec), spec["pdf_sha256"], spec["pdf_bytes"]),
                    "pages": 1,
                }
                or oracle["state"] != "pass"
                or oracle["target_state_sha256"] != spec["state_sha256"]
                or oracle["target_grid_sha256"] != spec["grid_sha256"]
                or oracle["rows"] != spec["rows"]
                or oracle["columns"] != spec["columns"]
                or oracle["master_cells"] != spec["master_cells"]
                or oracle["renderer_cache_count"] != spec["cache_count"]
                or oracle["renderer_cache_sha256"] != spec["cache_sha256"]
                or oracle["typed_selected_table_pagination_and_exterior_preserved"] is not True
            ):
                raise ValueError("receipt case")
        review = receipt["render_review"]
        if (
            review["state"] != "pass"
            or review["all_pages_inspected"] is not True
            or review["inspection_detail"] != "original"
            or review["review_actor"] != "assistant_visual_review"
            or any(review[key] is not False for key in (
                "encrypted", "javascript", "clipping", "overlap", "black_boxes"
            ))
            or review["blank_pages"] != []
            or [page["png_sha256"] for page in review["pages"]]
            != [case["png_sha256"] for case in CASE_SPECS]
            or [page["png_bytes"] for page in review["pages"]]
            != [case["png_bytes"] for case in CASE_SPECS]
        ):
            raise ValueError("render review")
        gate = receipt["gate_decision"]
        if (
            gate["TABLE-001"] != "oracle_verified"
            or gate["render_diff"] != "pass"
            or gate["rollback_or_retry"] != "pass"
            or gate["automation_runtime"] != "not_run"
            or gate["differential"] != "not_run"
            or gate["p06"] != "in_progress"
        ):
            raise ValueError("receipt gate")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        errors.append("receipt_semantics")


def validate_historical_semantics(root: Path, errors: list[str]) -> None:
    try:
        states = []
        for path, _, _ in HISTORICAL:
            if path.endswith(".json"):
                trace = load_json(bounded_bytes(root, path, 256_000))
                states.append(trace["state"])
        if len(states) != 4 or any(state == "pass" for state in states):
            raise ValueError("historical promotion")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        errors.append("historical_semantics")


def validate_markers(root: Path, errors: list[str]) -> int:
    markers = {
        MIGRATION: (
            "hwpx-agent.p06-09-table-create-target-contract/v2",
            "run-direct native table wrapper",
            "Attempts 01-04 remain failed evidence",
            "Automation runtime",
        ),
        REPORT: (
            "PASS for TABLE-001 direct HWPX creation",
            "37 bounded progress events",
            "Both exact outputs passed",
            "Neither page has clipping",
            "Attempts 01-04 remain immutable failed evidence",
            "P06-09/P06 completion",
        ),
    }
    for relative, expected in markers.items():
        try:
            text = bounded_bytes(root, relative, 256_000).decode("utf-8")
            if any(marker not in text for marker in expected):
                errors.append("implementation_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
    return len(markers)


def expected_validation_tree() -> list[str]:
    paths = {
        CONTRACT, MIGRATION, REPORT, RECEIPT, predecessor.CONTRACT,
        predecessor.MIGRATION, predecessor.POLICY, predecessor.REPORT,
        *SOURCE_LOCKS.keys(),
        *(path for path, _, _ in evidence_records()),
        *predecessor.EXPECTED_SOURCE_PATHS,
        *predecessor.IMPLEMENTATION_MARKERS.keys(),
    }
    return sorted(paths)


def result(
    errors: list[str],
    source_locks: int,
    evidence_files: int,
    implementation_files: int,
    predecessor_state: str,
) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-create-target-v2-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "predecessor": predecessor_state,
        "source_locks": source_locks,
        "evidence_files": evidence_files,
        "implementation_files": implementation_files,
        "features": 1,
        "cases": 2,
        "actual_hangul": not unique,
        "render": "pass" if not unique else "not_promoted",
        "rollback_or_retry": "pass" if not unique else "not_promoted",
        "automation_runtime": "not_run",
        "differential": "not_run",
        "p06_09": "in_progress",
        "p06": "in_progress",
        "product_complete": False,
    }


def main() -> int:
    report = validate(ROOT)
    print(json.dumps(report, sort_keys=True))
    if report["state"] == "pass":
        print(
            "P06_TABLE_CREATE_TARGET_V2_CONTRACT_PASS "
            f"cases={report['cases']} evidence_files={report['evidence_files']}"
        )
        return 0
    print("P06_TABLE_CREATE_TARGET_V2_CONTRACT_FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
