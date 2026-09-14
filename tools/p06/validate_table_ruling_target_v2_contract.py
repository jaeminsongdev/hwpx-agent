#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from tools.p06 import validate_table_ruling_hwpx_contract as predecessor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-ruling-target-v2.json"
MIGRATION = "protocol/migrations/p06-table-ruling-hwpx-v1-to-target-v2.md"
REPORT = "implementation/p06/P06-09_TABLE_RULING_TARGET_READBACK_REPORT.md"
RECEIPT = "implementation/p06/evidence/target/p06-table-ruling.current-2020.attempt08.v2.json"
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-ruling-target-20260910-06"
MANIFEST_PATH = f"{TARGET_DIRECTORY}/fixture-manifest.json"
TRACE_PATH = f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-08.json"
PROGRESS_PATH = f"{TRACE_PATH}.progress.jsonl"

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
    "protocol/private/p06-table-ruling-hwpx-v1.json":
        "e0fcf22c9435ef2341c1dda7a5f11d2e257cfc212646151981e4ee6a1df5861e",
    "tools/p06/validate_table_ruling_hwpx_contract.py":
        "a42bd226b1e8c3889c3a4741117d708585cb76d3a39a41e635b407a3e3a9251a",
    "crates/hwpx-package/src/table_ruling_hwpx.rs":
        "96b25f546b6414f866c20b483c2539f56dbfc209934983c9631cce2fb6aa5f68",
    "crates/hwpx-package/examples/p06_09_table_ruling_target_fixture.rs":
        "152a0837a4491d5b7e0403436d8feaef99f88e6ab02824b23f55e98ab1fc776f",
    "crates/hwpx-package/examples/p06_09_table_ruling_target_oracle.rs":
        "c14ba4a18ff01b0159452026a09db064b20574791d8fc2fc92c97b5d71f24585",
    "implementation/p06/tools/run-hancom-2020-table-ruling-target-batch-engine.ps1":
        "af38ada1940600846e832a4504fa959e0f8de60bb2d4b4b2a1461355ea8ddb9a",
    "implementation/p06/tools/run-hancom-2020-table-ruling-target-batch-readback.ps1":
        "2d619d02655ee9b5544d26d1d4d36286ca025a802801ef29b3940542788942da",
    "implementation/p06/tests/Test-Hancom2020TableRulingTargetBatchReadback.ps1":
        "c815df86e664c107d60ec572275f444d02012b9106bf5c6ded7a919f96d74507",
}

CASE_SPECS = [
    {
        "case_id": "table-002-draw-outer", "feature_id": "TABLE-002",
        "capability_id": "table.draw", "stem": "table-002-draw-outer",
        "operations": ["draw_outer_rectangle"], "selected_table_ordinal": 1,
        "input_sha256": "ff83b76da99190205d07dd612b6a2c94f2947aea1071eb80453b6a0493844114",
        "input_bytes": 13159,
        "output_sha256": "aee474cc7ad6a628ca2cdcad3ded5d9429292ce61122c94566b55482b84f7eb7",
        "output_bytes": 15707,
        "output_section_sha256": "c6acf9f1ffee8055570702b35bae119471e2e5bb55eecda7fad06f9350093903",
        "pdf_sha256": "1061666c4a23e62ad10725c19bb090c59f1ac7445c63405278947a20d35d8ff0",
        "pdf_bytes": 10343,
        "state_sha256": "b699efa43f7f864d015af00cbb095b820dde1c060d78f63d5736cb7da6d48ba7",
        "grid_sha256": "d5dd345b4a53f008fb9445bbc9c122181781e31174bf603474e56e1bcff35f15",
        "rows": 1, "columns": 1, "master_cells": 1, "payload_blocks": 0,
        "formulas": 0, "document_formula_fields": 1, "table_count": 2,
        "cache_count": 11,
        "cache_sha256": "1d4d7403855b8e5baae440e1c5487d806f3bc43df54b85a8adae51922409d3de",
        "png_sha256": "7f3e8412d3edd2c82e59d3f080e028a23ac09f4b888c892a29ab1f508861edae",
        "png_bytes": 11858,
        "finding": "original_2x4_table_plus_separate_empty_outer_rectangle_visible",
    },
    {
        "case_id": "table-002-draw-topology", "feature_id": "TABLE-002",
        "capability_id": "table.draw", "stem": "table-002-draw-topology",
        "operations": ["draw_full_row", "draw_full_column", "draw_local_cell_split",
                       "draw_existing_boundary_style"], "selected_table_ordinal": 0,
        "input_sha256": "1d5b4f344616195caf90394a1ef689987f2e8d71000853e81f049044b9fc22c1",
        "input_bytes": 13098,
        "output_sha256": "db6512e8c3f73aa77b41ce63214018c3229ee5777f6429da2234d0a5d3b644ce",
        "output_bytes": 15582,
        "output_section_sha256": "80f5f8a347038b3f4b8611a9ab08668a99a088f7ec0c653b0d16771bfe80a42a",
        "pdf_sha256": "95f5daa50a95dc109d4c9cf2d295e65773f9e831ac55d3a45f25a2d7224e519c",
        "pdf_bytes": 11820,
        "state_sha256": "95775beb2c88b0e86678f79ff5a2480cd9a8821b33f3a55528ae515bc6126c3d",
        "grid_sha256": "9920e9cc1fad918371bc27be1ba5064945249b13d56903e95932a373e0b57bef",
        "rows": 3, "columns": 6, "master_cells": 16, "payload_blocks": 8,
        "formulas": 0, "document_formula_fields": 0, "table_count": 1,
        "cache_count": 18,
        "cache_sha256": "b51a3c63a181c302a3099406e5687dbf99658bde282f3804634f0256d223ee91",
        "png_sha256": "3df44988681517073c6671795268683aec78afd80ceb49d97e6ab2a2e5b822e4",
        "png_bytes": 11892,
        "finding": "3x6_lattice_full_row_and_column_strokes_local_split_and_style_change_visible",
    },
    {
        "case_id": "table-002-draw-diagonals-formula", "feature_id": "TABLE-002",
        "capability_id": "table.draw", "stem": "table-002-draw-diagonals-formula",
        "operations": ["draw_slash_on_formula_cell", "draw_back_slash_on_formula_cell"],
        "selected_table_ordinal": 0,
        "input_sha256": "165c3e047613d1436109b331dc8ad6c8510c86a06444fedaa6dbbec42db7dd41",
        "input_bytes": 13163,
        "output_sha256": "8e32478939af67bbbd423569c5d892f0f5ed2964a5bdbc04f740aac6b71dc080",
        "output_bytes": 16397,
        "output_section_sha256": "be41331b206e7b8d46e44336e2cfd5e48517158bbae7686985c45f72c2c3c3aa",
        "pdf_sha256": "2e6344f68218572c56f457f819d2a374f5055aa895a29575dc0cb092ceb4deb3",
        "pdf_bytes": 10301,
        "state_sha256": "a750ae617e1cb614b0a1039827becef629d64369b95ca9932aae11e05c49bfd3",
        "grid_sha256": "6446e6b076e686123a3abb4ab574326a95986aa35e84e95d68230fe38a11e305",
        "rows": 2, "columns": 4, "master_cells": 8, "payload_blocks": 7,
        "formulas": 1, "document_formula_fields": 1, "table_count": 1,
        "cache_count": 10,
        "cache_sha256": "d0188128d0edb1d326cb79f2a775d645315377c9ac57f07406a05c889e22e9d0",
        "png_sha256": "c34bf319b6461e4229b4e20bc808c76246d1542cca3e9c505ed172f983d6d7fe",
        "png_bytes": 14158,
        "finding": "both_directional_diagonals_visible_in_formula_cell",
    },
    {
        "case_id": "table-003-eraser-structural-merge", "feature_id": "TABLE-003",
        "capability_id": "table.eraser", "stem": "table-003-eraser-structural-merge",
        "operations": ["erase_shared_column_edge"], "selected_table_ordinal": 0,
        "input_sha256": "995f8ec498c12bc8c3f43869f907c89722cf735496b54164812e307e8338d516",
        "input_bytes": 12920,
        "output_sha256": "46506cc0b0aeb5190b2676f8e9fbc3b874ce33575d0157ea52800d9ab49dc6e9",
        "output_bytes": 14875,
        "output_section_sha256": "74813b3e33008d92e1ede51b592e42a3d9d1c2309bd7e0e1b936ceac94de1912",
        "pdf_sha256": "29d71fd623c884fdc05a214fd04f6cc802636bd1a0fd7ee6562073a32964508d",
        "pdf_bytes": 10244,
        "state_sha256": "0acc0b40bd725855a3c014f4553fd601d06eaef401a6e6d9a518e859ac4fb639",
        "grid_sha256": "95ec59d2ad44c2a1a1e3bc5ba990d28cc4a3e9585bee9f88fb7d9ec4164bf37f",
        "rows": 2, "columns": 4, "master_cells": 6, "payload_blocks": 8,
        "formulas": 0, "document_formula_fields": 0, "table_count": 1,
        "cache_count": 10,
        "cache_sha256": "88469437b52c9d59b36ea2b3ec3bde586cdf260e83c8b162370a75bb7cddc9fe",
        "png_sha256": "6a68f0ae808653d72044d3fbae0c92737d6ac083bccb9b692c5b239d893578c5",
        "png_bytes": 11992,
        "finding": "shared_vertical_edge_removed_as_two_row_structural_merges_with_payload_order_visible",
    },
    {
        "case_id": "table-003-eraser-transparent-formula", "feature_id": "TABLE-003",
        "capability_id": "table.eraser", "stem": "table-003-eraser-transparent-formula",
        "operations": ["erase_outer_edge_on_formula_cell"], "selected_table_ordinal": 0,
        "input_sha256": "c2198bba2da81c2213967d817432782281bd464ec13e3b6bf9d2a449df9c0e1e",
        "input_bytes": 13132,
        "output_sha256": "a61f86e54430e028044441a92892a15b3cf17d3fc97b2628022aedadb8ee4e77",
        "output_bytes": 15147,
        "output_section_sha256": "be41331b206e7b8d46e44336e2cfd5e48517158bbae7686985c45f72c2c3c3aa",
        "pdf_sha256": "f3ee76ca0cec1ec5765a18cf0bb2b14cf3520ef5004d52d0e8678f0fc4a50d44",
        "pdf_bytes": 10282,
        "state_sha256": "ee7623487e0fedaa7ac3dc7cf2caedf2b918df6cb07b40a6e889083ae37443b5",
        "grid_sha256": "f1a8fbc48bd5afb046de2de9343892f767a91ae8b4bf2037f1b0e39a537d78b9",
        "rows": 2, "columns": 4, "master_cells": 8, "payload_blocks": 7,
        "formulas": 1, "document_formula_fields": 1, "table_count": 1,
        "cache_count": 10,
        "cache_sha256": "d0188128d0edb1d326cb79f2a775d645315377c9ac57f07406a05c889e22e9d0",
        "png_sha256": "e286abf50e79bd7be0c307736c4f748338774696aaec34616404b41787d826aa",
        "png_bytes": 11812,
        "finding": "formula_cell_outer_bottom_and_right_lines_render_transparent_without_topology_change",
    },
]

HISTORICAL = [
    ("fixtures/target-build/p06-09-table-ruling-target-20260910-05/"
     "table-ruling-target-batch-readback-20260910-01.json",
     "e2245f4a2b83da7fe9d13dc056601be1b83610e86c6cff5de21d205ab68ac295", 5083),
    ("fixtures/target-build/p06-09-table-ruling-target-20260910-05/"
     "table-ruling-target-batch-readback-20260910-01.json.progress.jsonl",
     "6405d82fa700ebd0ebcae97f8d6a03ae3ee7267605038c83b412772ab2be6ee4", 914),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-02.json",
     "a235db11c484a4242cd6a80e646dc7db662bd58bf61a85c3eb9c7f8d8f538e33", 5164),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-02.json.progress.jsonl",
     "cfe18c6d31518bc57e3006ef684537bfa99066df4de2c3796ed527bf2d5058b0", 920),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-03.json.progress.jsonl",
     "ed4516e1c1ab0e153ee174f46bb393b0064097f05a27218a3fbe55f9d42d9c6d", 922),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-04.json",
     "a235db11c484a4242cd6a80e646dc7db662bd58bf61a85c3eb9c7f8d8f538e33", 5164),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-04.json.progress.jsonl",
     "b9136ac2ae1903e9816bc40d97aeb7452d13efe5d0d39b7f5c6ba20593efa48d", 922),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-05.json",
     "a235db11c484a4242cd6a80e646dc7db662bd58bf61a85c3eb9c7f8d8f538e33", 5164),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-05.json.progress.jsonl",
     "36c7d260f9c55bdfb79f90fafaa4865fb45e9ccbb26edf8940a13079e2401696", 922),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-06.json",
     "a235db11c484a4242cd6a80e646dc7db662bd58bf61a85c3eb9c7f8d8f538e33", 5164),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-06.json.progress.jsonl",
     "0438a1a5f63c212ecf6026f15759e891f84641724b129763b40ad33b781ff01a", 917),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-07.json",
     "dc645587ab1064103aec2b60e19fb6b3e2f37f58f518bb4cd1597ee7fea6b1e0", 5163),
    (f"{TARGET_DIRECTORY}/table-ruling-target-batch-readback-20260910-07.json.progress.jsonl",
     "8c8fe908745c8e3bf90d4d9323993f5627c9f5b56e79a3aef4f0208b42f7f6e5", 919),
]

RECEIPT_SHA256 = "be368f7ed2a9b97390773e5cb84d0529ab85eacadeca216565a14abe035fc016"
RECEIPT_BYTES = 13741
MANIFEST_SHA256 = "8296cf4057c1cb6b27c800c15694866008c31cfa290cd6863321179c1efda543"
TRACE_SHA256 = "fdc0fc426575bf6bfdf604a8910c617403d19f3f5ef6994007533cedf0aa3b77"
PROGRESS_SHA256 = "af6487eac34ffe2c642c96e036ec183d1cbd7bdbf306da8fb98dcbec240afc67"

NOT_CLAIMED = {
    "automation_runtime": False, "differential_exact_match": False,
    "arbitrary_user_document_compatibility": False,
    "structural_formula_native_lowering": False,
    "other_pc_or_hancom_version": False, "p06_09_complete": False,
    "p06_phase_complete": False, "production": False, "product_complete": False,
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
    return result(errors, source_count, evidence_count, implementation_count,
                  str(predecessor_result.get("state")))


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
        "schema_version": "hwpx-agent.p06-09-table-ruling-target-contract/v2",
        "scope": "p06_09_table_002_003_exact_current_pc_hancom_2020_save_reopen_pdf_typed_oracle",
        "predecessor": {
            "path": predecessor.CONTRACT,
            "sha256": SOURCE_LOCKS[predecessor.CONTRACT],
            "state": "immutable_static_direct_hwpx_integration_contract",
        },
        "source_lock_canonicalization": "exact_file_bytes_sha256",
        "exact_target": EXPECTED_TARGET,
        "successful_attempt": {
            "id": "20260910-08", "directory": TARGET_DIRECTORY,
            "manifest": record(MANIFEST_PATH, MANIFEST_SHA256, 19283),
            "trace": record(TRACE_PATH, TRACE_SHA256, 7778),
            "progress": {**record(PROGRESS_PATH, PROGRESS_SHA256, 28432), "events": 85},
            "receipt": record(RECEIPT, RECEIPT_SHA256, RECEIPT_BYTES),
            "case_count": 5, "operation_count": 9, "state": "pass",
        },
        "historical_attempts": {
            "failed_or_interrupted_attempt_ids": [f"20260910-{index:02}" for index in range(1, 8)],
            "evidence": [record(*item) for item in HISTORICAL],
            "promoted_to_pass": 0,
            "decision": "immutable_failed_or_interrupted_evidence",
        },
        "cases": [contract_case(case) for case in CASE_SPECS],
        "render_oracle": {
            "state": "pass", "pdf_count": 5, "pages_each": 1,
            "page_size_points": [595, 841], "producer": "Hancom PDF 1.3.0.550",
            "renderer": "pdftoppm 26.07.0", "dpi": 144,
            "pixel_size": [1190, 1682], "inspection_detail": "original",
            "clipping": False, "overlap": False, "blank_pages": [], "black_boxes": False,
        },
        "gate_decision": {
            "TABLE-002": "oracle_verified", "TABLE-003": "oracle_verified",
            "actual_hancom_2020_save_reopen": "pass",
            "actual_hancom_2020_target_build": "pass", "render_diff": "pass",
            "rollback_or_retry": "pass", "automation_runtime": "not_run",
            "differential": "not_run", "p06_09": "in_progress", "p06": "in_progress",
        },
        "migration": MIGRATION, "report": REPORT, "evidence_receipt": RECEIPT,
        "not_claimed": NOT_CLAIMED,
    }
    for key, expected in exact.items():
        if contract.get(key) != expected:
            errors.append(key)
    failure = contract.get("failure_policy")
    if not isinstance(failure, list) or len(failure) != 8 or len(set(failure)) != 8 \
            or any(not isinstance(item, str) or not item for item in failure):
        errors.append("failure_policy")


def contract_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"], "feature_id": case["feature_id"],
        "capability_id": case["capability_id"], "input_sha256": case["input_sha256"],
        "output_sha256": case["output_sha256"], "pdf_sha256": case["pdf_sha256"],
        "target_state_sha256": case["state_sha256"],
        "target_grid_sha256": case["grid_sha256"], "rows": case["rows"],
        "columns": case["columns"], "master_cells": case["master_cells"],
        "payload_blocks": case["payload_blocks"], "formulas": case["formulas"],
        "document_formula_fields": case["document_formula_fields"],
        "renderer_cache_count": case["cache_count"],
        "renderer_cache_sha256": case["cache_sha256"],
    }


def validate_source_locks(root: Path, declared: Any, errors: list[str]) -> int:
    expected = [{"path": path, "sha256": sha256} for path, sha256 in SOURCE_LOCKS.items()]
    if declared != expected:
        errors.append("source_locks_exact")
    for path, sha256 in SOURCE_LOCKS.items():
        try:
            if digest(bounded_bytes(root, path, 4 * 1024 * 1024)) != sha256:
                errors.append("source_lock_digest")
        except (OSError, ValueError):
            errors.append("source_lock_path_or_encoding")
    return len(SOURCE_LOCKS)


def evidence_records() -> list[tuple[str, str, int]]:
    values = [(MANIFEST_PATH, MANIFEST_SHA256, 19283),
              (TRACE_PATH, TRACE_SHA256, 7778),
              (PROGRESS_PATH, PROGRESS_SHA256, 28432),
              (RECEIPT, RECEIPT_SHA256, RECEIPT_BYTES)]
    for case in CASE_SPECS:
        values.extend([
            (input_path(case), case["input_sha256"], case["input_bytes"]),
            (output_path(case), case["output_sha256"], case["output_bytes"]),
            (pdf_path(case), case["pdf_sha256"], case["pdf_bytes"]),
        ])
    return values


def validate_evidence_files(root: Path, errors: list[str]) -> int:
    evidence = evidence_records() + HISTORICAL
    seen: set[str] = set()
    for path, sha256, size in evidence:
        if path in seen:
            errors.append("evidence_duplicate")
        seen.add(path)
        try:
            data = bounded_bytes(root, path)
            if len(data) != size or digest(data) != sha256:
                errors.append("evidence_digest")
        except (OSError, ValueError):
            errors.append("evidence_path")
    return len(evidence)


def validate_manifest(root: Path, errors: list[str]) -> None:
    try:
        manifest = load_json(bounded_bytes(root, MANIFEST_PATH, 256_000))
        if set(manifest) != {
            "schema_version", "source_ancestor_sha256", "cases", "actual_hangul_2020",
            "render", "automation", "differential",
        } or manifest.get("schema_version") != "hwpx-agent.p06-09-table-ruling-target-fixture/v1" \
                or manifest.get("source_ancestor_sha256") \
                != "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5" \
                or manifest.get("actual_hangul_2020") is not False \
                or manifest.get("render") != "not_run" \
                or manifest.get("automation") != "not_run" \
                or manifest.get("differential") != "not_run":
            raise ValueError("manifest root")
        cases = manifest.get("cases")
        if not isinstance(cases, list) or len(cases) != len(CASE_SPECS):
            raise ValueError("manifest cases")
        for actual, expected in zip(cases, CASE_SPECS, strict=True):
            binding = actual.get("binding", {})
            operations = actual.get("operations", [])
            if actual.get("case_id") != expected["case_id"] \
                    or actual.get("feature_id") != expected["feature_id"] \
                    or actual.get("capability_id") != expected["capability_id"] \
                    or actual.get("file") != f"{expected['stem']}.hwpx" \
                    or actual.get("sha256") != expected["input_sha256"] \
                    or actual.get("selected_table_ordinal") != expected["selected_table_ordinal"] \
                    or actual.get("target_state_sha256") != expected["state_sha256"] \
                    or actual.get("target_grid_sha256") != expected["grid_sha256"] \
                    or actual.get("target_rows") != expected["rows"] \
                    or actual.get("target_columns") != expected["columns"] \
                    or actual.get("target_master_cells") != expected["master_cells"] \
                    or actual.get("payload_block_count") != expected["payload_blocks"] \
                    or actual.get("formula_count") != expected["formulas"] \
                    or not isinstance(binding, dict) \
                    or len(binding.get("row_boundaries_hwpunit", [])) != expected["rows"] + 1 \
                    or len(binding.get("column_boundaries_hwpunit", [])) != expected["columns"] + 1 \
                    or len(binding.get("cells", [])) != expected["master_cells"] \
                    or [item.get("name") for item in operations] != expected["operations"] \
                    or any(item.get("capability_id") != expected["capability_id"] for item in operations):
                raise ValueError("manifest case")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError):
        errors.append("manifest_semantics")


def validate_trace(root: Path, errors: list[str]) -> None:
    try:
        trace = load_json(bounded_bytes(root, TRACE_PATH, 256_000))
        target = dict(EXPECTED_TARGET)
        target.pop("product")
        target.pop("build")
        target.pop("architecture")
        target.pop("locale")
        target["file_version"] = EXPECTED_TARGET["build"]
        phases = {
            "open_input": "pass", "read_input": "pass", "save_as_hwpx": "pass",
            "close_input": "pass", "reopen_output": "pass", "read_output": "pass",
            "export_pdf": "pass", "close_output": "pass",
        }
        if trace.get("schema_version") \
                != "hwpx-agent.p06-09-hancom-2020-table-ruling-target-batch-readback/v1" \
                or trace.get("state") != "pass" or trace.get("target") != target \
                or trace.get("fixture_manifest_sha256") != MANIFEST_SHA256 \
                or trace.get("case_count") != 5 or trace.get("completed_case_count") != 5 \
                or trace.get("failed_case_id") is not None \
                or trace.get("failed_feature_id") is not None \
                or trace.get("error_code") is not None or trace.get("failed_phase") is not None \
                or trace.get("exception_type") is not None \
                or trace.get("exception_hresult") is not None:
            raise ValueError("trace root")
        cases = trace.get("cases")
        if not isinstance(cases, list) or len(cases) != 5:
            raise ValueError("trace cases")
        for actual, expected in zip(cases, CASE_SPECS, strict=True):
            if actual.get("case_id") != expected["case_id"] \
                    or actual.get("feature_id") != expected["feature_id"] \
                    or actual.get("capability_id") != expected["capability_id"] \
                    or actual.get("input_sha256") != expected["input_sha256"] \
                    or actual.get("output_sha256") != expected["output_sha256"] \
                    or actual.get("render_pdf_sha256") != expected["pdf_sha256"] \
                    or actual.get("render_pdf_bytes") != expected["pdf_bytes"] \
                    or actual.get("input_unchanged") is not True \
                    or actual.get("input_text_sha256") != actual.get("output_text_sha256") \
                    or actual.get("output_saved") is not True \
                    or actual.get("render_pdf_requested") is not True \
                    or actual.get("render_pdf_saved") is not True \
                    or actual.get("render_pdf_signature_valid") is not True \
                    or actual.get("render_pdf_export_method") != "IXHwpDocument.SaveAs/PDF" \
                    or actual.get("phases") != phases \
                    or actual.get("error_code") is not None or actual.get("failed_phase") is not None:
                raise ValueError("trace case")
        watchdog = trace.get("watchdog", {})
        if watchdog != {
            "timeout_seconds": 900, "timed_out": False, "child_exit_code": 0,
            "output_drained": True, "cleaned_process_count": 0,
            "cleanup_refused_count": 0, "cleanup_error_count": 0,
            "remaining_hwp_process_count": 0, "progress_present": True,
            "progress_valid": True, "progress_event_count": 85,
            "progress_last_phase": "terminal", "progress_last_state": "pass",
            "progress_observed_phase": "quit", "progress_observed_case_id": None,
            "progress_observed_feature_id": None, "window_visible_for_user_access": True,
        } or trace.get("raw_document_text_present") is not False \
                or trace.get("user_document_scanned") is not False \
                or trace.get("external_network_invoked") is not False \
                or trace.get("registry_or_system_setting_changed") is not False \
                or trace.get("computer_use_click_or_type_invoked") is not False \
                or trace.get("window_visible_for_user_access") is not True \
                or trace.get("delegated_engine_schema") \
                != "hwpx-agent.p06-09-hancom-2020-table-ruling-target-batch-engine/v1":
            raise ValueError("trace safety")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError):
        errors.append("trace_semantics")


def validate_progress(root: Path, errors: list[str]) -> None:
    expected: list[tuple[int, int, str | None, str | None, str, str]] = [
        (1, 0, None, None, "preflight", "pass"),
        (2, 0, None, None, "com_create", "pass"),
    ]
    sequence = 3
    phases = ["open_input", "read_input", "save_as_hwpx", "close_input",
              "reopen_output", "read_output", "export_pdf", "close_output"]
    for index, case in enumerate(CASE_SPECS, start=1):
        for phase in phases:
            expected.append((sequence, index, case["case_id"], case["feature_id"], phase, "running"))
            expected.append((sequence + 1, index, case["case_id"], case["feature_id"], phase, "pass"))
            sequence += 2
    expected.extend([
        (83, 0, None, None, "quit", "running"),
        (84, 0, None, None, "quit", "pass"),
        (85, 5, CASE_SPECS[-1]["case_id"], CASE_SPECS[-1]["feature_id"], "terminal", "pass"),
    ])
    try:
        text = bounded_bytes(root, PROGRESS_PATH, 256_000).decode("utf-8")
        events = [load_json(line.encode("utf-8")) for line in text.splitlines()]
        actual = [(item.get("sequence"), item.get("case_index"), item.get("case_id"),
                   item.get("feature_id"), item.get("phase"), item.get("state"))
                  for item in events]
        worker_ids = {item.get("worker_process_id") for item in events}
        hwp_ids = {item.get("hwp_process_id") for item in events[1:]}
        if actual != expected or len(events) != 85 or len(worker_ids) != 1 \
                or not all(isinstance(item, int) and item > 0 for item in worker_ids) \
                or len(hwp_ids) != 1 or not all(isinstance(item, int) and item > 0 for item in hwp_ids) \
                or any(item.get("schema_version") \
                       != "hwpx-agent.p06-09-table-ruling-batch-progress/v1"
                       or item.get("raw_document_text_present") is not False
                       or not isinstance(item.get("recorded_at_utc"), str)
                       or not item["recorded_at_utc"].endswith("Z") for item in events):
            raise ValueError("progress")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError):
        errors.append("progress_semantics")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def validate_hwpx_and_pdf_artifacts(root: Path, errors: list[str]) -> None:
    for case in CASE_SPECS:
        try:
            validate_hwpx(root, input_path(case), case, False)
            validate_hwpx(root, output_path(case), case, True)
        except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError):
            errors.append("hwpx_semantics")
        try:
            data = bounded_bytes(root, pdf_path(case))
            if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:] \
                    or re.findall(rb"/Count\s+(\d+)\b", data) != [b"1"] \
                    or b"/Encrypt" in data or b"/JavaScript" in data \
                    or b"Hancom PDF 1.3.0.550" not in data:
                raise ValueError("pdf")
        except (OSError, ValueError):
            errors.append("pdf_semantics")


def validate_hwpx(root: Path, relative: str, case: dict[str, Any], output: bool) -> None:
    path = safe_path(root, relative)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("hwpx file")
    with zipfile.ZipFile(path) as package:
        entries = package.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != 11 or len(set(names)) != len(names) \
                or any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
                       for name in names) \
                or sum(entry.file_size for entry in entries) > 8 * 1024 * 1024:
            raise ValueError("package graph")
        section = package.read("Contents/section0.xml")
    if output and digest(section) != case["output_section_sha256"]:
        raise ValueError("section digest")
    root_element = ET.fromstring(section)
    tables = [element for element in root_element.iter() if local_name(element.tag) == "tbl"]
    if len(tables) != case["table_count"]:
        raise ValueError("table count")
    selected = tables[case["selected_table_ordinal"]]
    rows = [child for child in selected if local_name(child.tag) == "tr"]
    masters = sum(1 for row in rows for child in row if local_name(child.tag) == "tc")
    formula_fields = sum(
        1 for element in root_element.iter()
        if local_name(element.tag) == "fieldBegin" and element.get("type") == "FORMULA"
    )
    caches = sum(1 for element in root_element.iter() if local_name(element.tag) == "linesegarray")
    if output:
        if selected.get("rowCnt") != str(case["rows"]) \
                or selected.get("colCnt") != str(case["columns"]) \
                or len(rows) != case["rows"] or masters != case["master_cells"] \
                or formula_fields != case["document_formula_fields"] \
                or caches != case["cache_count"]:
            raise ValueError("typed output")
    elif caches != 0:
        raise ValueError("candidate renderer caches")


def expected_receipt_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"], "feature_id": case["feature_id"],
        "capability_id": case["capability_id"], "operations": case["operations"],
        "input": {**record(input_path(case), case["input_sha256"], case["input_bytes"]),
                  "unchanged": True},
        "output": {**record(output_path(case), case["output_sha256"], case["output_bytes"]),
                   "section_sha256": case["output_section_sha256"]},
        "pdf": {**record(pdf_path(case), case["pdf_sha256"], case["pdf_bytes"]), "pages": 1},
        "oracle": {
            "state": "pass", "target_state_sha256": case["state_sha256"],
            "target_grid_sha256": case["grid_sha256"], "rows": case["rows"],
            "columns": case["columns"], "master_cells": case["master_cells"],
            "payload_blocks": case["payload_blocks"], "formulas": case["formulas"],
            "document_formula_fields": case["document_formula_fields"],
            "renderer_cache_count": case["cache_count"],
            "renderer_cache_sha256": case["cache_sha256"],
            "typed_selected_table_and_section_exterior_equal_after_renderer_normalization": True,
        },
    }


def validate_receipt(root: Path, errors: list[str]) -> None:
    try:
        receipt = load_json(bounded_bytes(root, RECEIPT, 256_000))
        expected_keys = {"schema_version", "evidence_id", "scope", "attempt", "cases",
                         "render_review", "retry_evidence", "safety", "gate_decision",
                         "not_claimed"}
        if set(receipt) != expected_keys \
                or receipt.get("schema_version") \
                != "hwpx-agent.p06-09-table-ruling-current-2020-evidence/v2" \
                or receipt.get("evidence_id") \
                != "p06.table-ruling.current-2020.attempt08.20260910" \
                or receipt.get("scope") \
                != "exact_current_pc_hancom_2020_table_002_003_save_reopen_pdf_and_independent_oracle":
            raise ValueError("receipt root")
        expected_attempt = {
            "id": "20260910-08", "directory": TARGET_DIRECTORY,
            "manifest": record(MANIFEST_PATH, MANIFEST_SHA256, 19283),
            "trace": {**record(TRACE_PATH, TRACE_SHA256, 7778), "state": "pass"},
            "progress": {**record(PROGRESS_PATH, PROGRESS_SHA256, 28432),
                         "events": 85, "terminal": "pass"},
            "target": EXPECTED_TARGET, "completed_cases": 5, "failed_case_id": None,
            "timed_out": False, "remaining_hwp_process_count": 0,
        }
        if receipt.get("attempt") != expected_attempt \
                or receipt.get("cases") != [expected_receipt_case(case) for case in CASE_SPECS]:
            raise ValueError("receipt evidence")
        expected_pages = [
            {"case_id": case["case_id"], "png_sha256": case["png_sha256"],
             "png_bytes": case["png_bytes"], "finding": case["finding"]}
            for case in CASE_SPECS
        ]
        expected_render = {
            "state": "pass", "engine": "pdftoppm 26.07.0", "dpi": 144,
            "page_size_points": [595, 841], "pixel_size": [1190, 1682],
            "producer": "Hancom PDF 1.3.0.550", "pdf_version": "1.4",
            "all_pages_inspected": True, "inspection_detail": "original",
            "clipping": False, "overlap": False, "blank_pages": [], "black_boxes": False,
            "rendered_png_retention": "ephemeral_review_intermediate_not_product_input",
            "pages": expected_pages,
        }
        if receipt.get("render_review") != expected_render \
                or receipt.get("retry_evidence") != {
                    "state": "pass", "failed_or_interrupted_attempts_preserved": 7,
                    "successful_create_only_attempt": "20260910-08",
                    "same_manifest_and_input_digests": True,
                    "partial_output_promoted": False, "input_unchanged": True,
                    "owned_process_cleanup_bounded": True,
                } or receipt.get("safety") != {
                    "raw_document_text_retained": False, "user_document_scanned": False,
                    "external_network_invoked": False,
                    "registry_or_system_setting_changed": False,
                    "computer_use_click_or_type_invoked": False,
                    "source_packages_modified": False,
                } or receipt.get("gate_decision") != {
                    "TABLE-002": "oracle_verified", "TABLE-003": "oracle_verified",
                    "actual_hancom_2020_save_reopen": True,
                    "actual_hancom_2020_target_build": True, "render_diff": True,
                    "rollback_or_retry": True, "automation_runtime": "not_run",
                    "differential": "not_run", "p06_09": "in_progress",
                    "p06": "in_progress",
                } or receipt.get("not_claimed") != NOT_CLAIMED:
            raise ValueError("receipt decision")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError):
        errors.append("receipt_semantics")


def validate_historical_semantics(root: Path, errors: list[str]) -> None:
    try:
        for path, _, _ in HISTORICAL:
            data = bounded_bytes(root, path, 256_000)
            if path.endswith(".json"):
                value = load_json(data)
                if not isinstance(value, dict) or value.get("state") == "pass":
                    raise ValueError("historical trace promoted")
            else:
                events = [load_json(line.encode("utf-8"))
                          for line in data.decode("utf-8").splitlines()]
                if not events or any(item.get("phase") == "terminal" and item.get("state") == "pass"
                                     for item in events):
                    raise ValueError("historical progress promoted")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError):
        errors.append("historical_semantics")


def validate_markers(root: Path, errors: list[str]) -> int:
    markers = {
        MIGRATION: (
            "independent typed-oracle results", "historical failed evidence are not rewritten",
            "differential exact match",
        ),
        REPORT: (
            "Decision: **PASS for TABLE-002/003", "Attempt 08",
            "never by ignoring the", "Automation runtime",
        ),
        RECEIPT: (
            "p06.table-ruling.current-2020.attempt08.20260910",
            '"partial_output_promoted": false', '"product_complete": false',
        ),
        "crates/hwpx-package/examples/p06_09_table_ruling_target_oracle.rs": (
            "typed_selected_table_and_section_exterior_equal_after_renderer_normalization=true",
            "require_selected_table_exterior_equal",
        ),
        "crates/hwpx-package/src/table_ruling_hwpx.rs": (
            "saw_empty_content", "is_empty_scaffold",
        ),
    }
    for path, expected in markers.items():
        try:
            text = bounded_bytes(root, path, 4 * 1024 * 1024).decode("utf-8")
            if any(marker not in text for marker in expected):
                errors.append("implementation_markers")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path_or_encoding")
    return len(markers)


def expected_validation_tree() -> set[str]:
    tree = {CONTRACT, MIGRATION, REPORT, RECEIPT, MANIFEST_PATH, TRACE_PATH, PROGRESS_PATH,
            *SOURCE_LOCKS}
    tree.update(path for path, _, _ in evidence_records())
    tree.update(path for path, _, _ in HISTORICAL)
    tree.update({predecessor.CONTRACT, predecessor.MIGRATION, predecessor.POLICY,
                 predecessor.REPORT, *predecessor.EXPECTED_SOURCE_PATHS,
                 *predecessor.IMPLEMENTATION_MARKERS})
    return tree


def result(errors: list[str], source_locks: int, evidence_files: int,
           implementation_files: int, predecessor_state: str) -> dict[str, Any]:
    unique = sorted(set(errors))
    state = "pass" if not unique else "fail"
    return {
        "schema_version": "hwpx-agent.p06-table-ruling-target-validation/v2",
        "state": state, "errors": unique, "source_locks": source_locks,
        "evidence_files": evidence_files, "implementation_files": implementation_files,
        "predecessor": predecessor_state,
        "features": 2, "cases": 5, "operations": 9,
        "direct_stage": "oracle_verified" if state == "pass" else "not_proven",
        "actual_hancom_2020_save_reopen": "pass" if state == "pass" else "not_proven",
        "actual_hancom_2020_render": "pass" if state == "pass" else "not_proven",
        "rollback_or_retry": "pass" if state == "pass" else "not_proven",
        "automation_runtime": "not_run", "differential": "not_run",
        "p06_09": "in_progress", "p06": "in_progress", "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_RULING_TARGET_V2_CONTRACT_PASS "
        f"features={validation['features']} cases={validation['cases']} "
        f"source_locks={validation['source_locks']} evidence_files={validation['evidence_files']}"
    )
