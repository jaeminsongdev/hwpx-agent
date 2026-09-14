#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any
import zipfile

try:
    from tools.p06 import validate_table_table_to_text_hwpx_contract as table_to_text
    from tools.p06 import validate_table_text_to_table_hwpx_contract as text_to_table
except ModuleNotFoundError:
    import validate_table_table_to_text_hwpx_contract as table_to_text
    import validate_table_text_to_table_hwpx_contract as text_to_table


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-text-conversion-target-v2.json"
MIGRATION = "protocol/migrations/p06-table-text-conversion-hwpx-v1-to-target-v2.md"
REPORT = "implementation/p06/P06-09_TABLE_TEXT_CONVERSION_TARGET_READBACK_REPORT.md"
RECEIPT = "implementation/p06/evidence/target/p06-table-text-conversion.current-2020.attempt06.v2.json"
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-text-conversion-target-20260913-06"
MANIFEST_PATH = f"{TARGET_DIRECTORY}/fixture-manifest.json"
TRACE_PATH = f"{TARGET_DIRECTORY}/target-batch-readback-20260913-01.json"
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
    "protocol/private/p06-table-text-to-table-hwpx-v1.json":
        "ef4a67621d327d2e9fd49729a24ef23e937821bff5fcd4f498f856302e1cc3b2",
    "tools/p06/validate_table_text_to_table_hwpx_contract.py":
        "c47c4377c46a5589b4358fa2d33286e57cd80253924c8bebe0bc04b697f1252e",
    "protocol/private/p06-table-table-to-text-hwpx-v1.json":
        "789bbf9c59c36c2ad1eb6046dff959130d19e4ba1824c06a8412adc0eaae1809",
    "tools/p06/validate_table_table_to_text_hwpx_contract.py":
        "9ced2316a04928966db941441eb74032d5c37f02a8f7b06aba989f87aa8a2fe0",
    "crates/hwpx-package/src/table_ruling_hwpx/create_hwpx.rs":
        "ebd710a2409612eebbe30951f8e738a71b4ab615be8eba1a0579a08ad2b718f3",
    "crates/hwpx-package/src/table_ruling_hwpx/text_conversion_hwpx.rs":
        "127d9f58d6d20a190b5c018ae6e850465e45054b99f76d38c35b8d2ba304c5cf",
    "crates/hwpx-package/src/table_ruling_hwpx/table_to_text_hwpx.rs":
        "8b1e7976185ed839e2bee62ce6cc51d750d515a866de2783e5785fb3e89f71a2",
    "crates/hwpx-package/examples/p06_09_table_text_conversion_target_fixture.rs":
        "ab4b6ec9657698cb8ef1dfb8bb35b65c79864ef0910e98501a00c878c6919335",
    "crates/hwpx-package/examples/p06_09_table_text_conversion_target_oracle.rs":
        "01230724b2a6fd0f064aefdccd5e1f6f574b0a9c6ade672b6c1fd143e5f5d09b",
    "implementation/p06/tools/run-hancom-2020-table-text-conversion-target-batch-engine.ps1":
        "29fc0add143a797d18c3f27d108dd15ddf55a2ed4c3ba650d85b96743152d3d4",
    "implementation/p06/tools/run-hancom-2020-table-text-conversion-target-batch-readback.ps1":
        "2c874a63112616dafc7190e5f723a513f992d167afa9158c14b2d2d152d04020",
    "implementation/p06/tests/Test-Hancom2020TableTextConversionTargetBatchReadback.ps1":
        "80759c8c51b7161533f0d6dc4558a1ca1d8e3550d6dbcb0654c044dd442ffe6c",
}

STATIC_RECORDS = {
    MANIFEST_PATH: ("6c32f7ccdaad74ad62a2e32257e203ce2c61dc74dafc11026d9ddfe0f045220a", 10176),
    TRACE_PATH: ("eb01b39ffc8fe951ff2bd865957ed173a82c2d3a0b989f5938429a254efbfa37", 9141),
    PROGRESS_PATH: ("eee6cb1b0284b76bcff71cdc4d2acaaaed6104921a046c1619fe5ba848582822", 20886),
    RECEIPT: ("b494039e0c2f7617854d50a008a69963667c2581318d138fe8b4ac94b093f36e", 12109),
}

CASE_SPECS = [
    {
        "case_id": "table-004-quoted-multiline-3x2", "feature_id": "TABLE-004",
        "capability_id": "table.text_to_table", "stem": "table-004-text-to-table-quoted-multiline-3x2",
        "input_sha256": "deea6a65f7d379a388f9c9687f1e1ec03ccec9b7a71c8cd9fa4c651e8112058e", "input_bytes": 13280,
        "output_sha256": "06943bbd7cfa3b9d074272069771977eb188b74e75f0028155f43c88b8e530fb", "output_bytes": 17042,
        "output_section_sha256": "98efe78dd2b3419d836c6582c4e3ca1e9e269da7e803579f6c9f451b204d60d4",
        "pdf_sha256": "ee5b9438709a421942e1d0ce59cabeed2be1511b6d7f887e3c70f2683a03b27a", "pdf_bytes": 12753,
        "state_sha256": "9dc54871c6f686f47c136c1c89d7ac0e62a38c1ce69aeee91b65c450f554fe9b",
        "grid_sha256": "69fa2b24266bd3e1466b2bfd3d8ecb55a58a76fc3aa355d183b24ff6d36beacc",
        "text_grid_sha256": "3e3c169b265ad05c7cecdd779a38dfd8e3234053db3f1d2428c0a099be7624eb",
        "rows": 3, "columns": 2, "master_cells": 6, "payload_blocks": 5,
        "cache_count": 16, "cache_sha256": "7a6110d20a9fafd6a42a5c6f849b76c450c2af67b2a6a512c4693f35dcc1cd9d",
    },
    {
        "case_id": "table-005-quoted-multiline-3x2", "feature_id": "TABLE-005",
        "capability_id": "table.table_to_text", "stem": "table-005-table-to-text-quoted-multiline-3x2",
        "input_sha256": "6ac06c31dfe34bff7f6541757d321833fe281d73740f3ed7ba5c1d3a9f70d752", "input_bytes": 13170,
        "output_sha256": "9a9350e3fa7bff3844b540257ffadba7064ddb340f3ccbf0b5325be49ba20900", "output_bytes": 15342,
        "output_section_sha256": "3778a733603a350eb9c3974ec7fde9e6f8feedc8399b6f44193b6285e8bed1be",
        "pdf_sha256": "ab4e6838e30d1a088c45e51f542b5bbc5236be1301e4bd809b25fe903944fa22", "pdf_bytes": 12658,
        "state_sha256": "9dc54871c6f686f47c136c1c89d7ac0e62a38c1ce69aeee91b65c450f554fe9b",
        "grid_sha256": "69fa2b24266bd3e1466b2bfd3d8ecb55a58a76fc3aa355d183b24ff6d36beacc",
        "text_grid_sha256": "3e3c169b265ad05c7cecdd779a38dfd8e3234053db3f1d2428c0a099be7624eb",
        "rows": 3, "columns": 2, "master_cells": 6, "payload_blocks": 5,
        "cache_count": 10, "cache_sha256": "e71e89cd24fee40f0b9c21b447dcec1cb702baf337c262cda4cd04b6a32b8d44",
    },
    {
        "case_id": "table-004-boundary-1x1", "feature_id": "TABLE-004",
        "capability_id": "table.text_to_table", "stem": "table-004-text-to-table-boundary-1x1",
        "input_sha256": "f5e2aae18e6bf31b7f60eed688b3dc26f6ad99e7744faba9420cf352db51cc84", "input_bytes": 13162,
        "output_sha256": "3a087f02b23a65c777c61da8737fd0fd1ae07ad03f516ba1e8f79b62be51d641", "output_bytes": 14960,
        "output_section_sha256": "b6fff79d8c2f215edb33b0ef1d1d58b760a870bc893260a60c46b6977a6e040e",
        "pdf_sha256": "3cd4b9d50273fdeac8ac274fb1bfb6e62176b0843b30637a5c0fd766151f26fe", "pdf_bytes": 10560,
        "state_sha256": "9c10cca05be8e9ae31fb8b8423636465900301337c002d010477f7f4446394f1",
        "grid_sha256": "e6f177fd2d4d7d38e326fda013d9b156297b6db67ce1ba66b88f6370c80af82a",
        "text_grid_sha256": "0f0a5541d5ec01973a5fad8e9690708e405331d1550391255df45505871e7fe6",
        "rows": 1, "columns": 1, "master_cells": 1, "payload_blocks": 1,
        "cache_count": 11, "cache_sha256": "5f27694ccd7d258c83e5a9f2c4b62c55e6a848f6002d80913c729f0f69007c69",
    },
    {
        "case_id": "table-005-boundary-1x1", "feature_id": "TABLE-005",
        "capability_id": "table.table_to_text", "stem": "table-005-table-to-text-boundary-1x1",
        "input_sha256": "267a9b326f87c92142a235369ae0638844b9b9245cfdc11df64db651c82eba72", "input_bytes": 13111,
        "output_sha256": "881ed36689fce30637c87619407c7be9719317937f7cddedb79d628e3bb41f8a", "output_bytes": 14375,
        "output_section_sha256": "2676972863fa263dbe759a752fe99060f303e91d16ddd057f97fbf7ffe5e776b",
        "pdf_sha256": "966b706751d8d5e620144b704209f12a0ddf6b5f5ed4b1ee87a9c5f59cc2c8ac", "pdf_bytes": 10486,
        "state_sha256": "9c10cca05be8e9ae31fb8b8423636465900301337c002d010477f7f4446394f1",
        "grid_sha256": "e6f177fd2d4d7d38e326fda013d9b156297b6db67ce1ba66b88f6370c80af82a",
        "text_grid_sha256": "0f0a5541d5ec01973a5fad8e9690708e405331d1550391255df45505871e7fe6",
        "rows": 1, "columns": 1, "master_cells": 1, "payload_blocks": 1,
        "cache_count": 10, "cache_sha256": "4d689bc912eb2385bc8a0a10d46f1076436ba2ed07c0466dabab792213a3064f",
    },
]

HISTORICAL = [
    ("fixtures/target-build/p06-09-table-text-conversion-target-20260913-02/target-batch-readback-20260913-01.json", "35468b344db4164ade71d23c1695b61ba56a8718d08ee416620eb423478a2380", 5970),
    ("fixtures/target-build/p06-09-table-text-conversion-target-20260913-02/target-batch-readback-20260913-01.json.progress.jsonl", "bdcf92b73554dcf2489fd37440deb1e6057300caf47aa340ad25242eac85aa51", 10292),
    ("fixtures/target-build/p06-09-table-text-conversion-target-20260913-03/engine-direct-20260913-01.progress.jsonl", "582b76ceb77a4d2fc368eacf8d52a9d3cb51e5d80219407660c0928b7b4080a5", 10292),
    ("fixtures/target-build/p06-09-table-text-conversion-target-20260913-04/target-batch-readback-20260913-01.json", "033e4a9b49bcfa4f6b95ce212c088a4b6cbf6e881cdef499757a3f9cb9b1ca7b", 9141),
    ("fixtures/target-build/p06-09-table-text-conversion-target-20260913-04/target-batch-readback-20260913-01.json.progress.jsonl", "8c10b9d9997399184a200a07c9e6cd1c23569557c5c0ab8ab1fb1c820978574d", 20886),
    ("fixtures/target-build/p06-09-table-text-conversion-target-20260913-05/target-batch-readback-20260913-01.json", "b9fc44ea1795b644080d2e9befa69fd4ec620c932b1a70bbe611bdbe21e4d8e3", 9141),
    ("fixtures/target-build/p06-09-table-text-conversion-target-20260913-05/target-batch-readback-20260913-01.json.progress.jsonl", "48bbe67a710c1c52c5754f7807a6163ba8e6a9b60799f6f04694832512e8435e", 20886),
]

NOT_CLAIMED = {
    "automation_runtime": False, "differential_exact_match": False,
    "merged_or_formula_source_conversion": False, "field_or_opaque_content_flattening": False,
    "arbitrary_native_template_or_wrapper": False, "arbitrary_user_document_compatibility": False,
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


def canonical_digest(data: bytes) -> str:
    text = data.decode("utf-8").replace("\r\n", "\n")
    return digest(text.encode("utf-8"))


def input_path(case: dict[str, Any]) -> str:
    return f"{TARGET_DIRECTORY}/{case['stem']}.hwpx"


def output_path(case: dict[str, Any]) -> str:
    return f"{TARGET_DIRECTORY}/{case['stem']}.hancom-2020-readback.hwpx"


def pdf_path(case: dict[str, Any]) -> str:
    return f"{TARGET_DIRECTORY}/{case['stem']}.hancom-2020-render.pdf"


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    predecessor_states = {
        "TABLE-004": text_to_table.validate(root).get("state"),
        "TABLE-005": table_to_text.validate(root).get("state"),
    }
    if set(predecessor_states.values()) != {"pass"}:
        errors.append("predecessors")
    try:
        contract = load_json(bounded_bytes(root, CONTRACT, 512_000))
        if not isinstance(contract, dict):
            raise ValueError("contract root")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0, predecessor_states)

    validate_contract(contract, errors)
    source_count = validate_source_locks(root, contract.get("source_locks"), errors)
    evidence_count = validate_evidence(root, errors)
    validate_manifest(root, errors)
    validate_trace(root, errors)
    validate_progress(root, errors)
    validate_artifacts(root, errors)
    validate_receipt(root, errors)
    validate_history(root, errors)
    implementation_count = validate_markers(root, errors)
    return result(errors, source_count, evidence_count, implementation_count, predecessor_states)


def validate_contract(contract: dict[str, Any], errors: list[str]) -> None:
    expected_keys = {
        "schema_version", "scope", "predecessors", "source_lock_canonicalization",
        "source_locks", "exact_target", "successful_attempt", "historical_attempts",
        "cases", "render_oracle", "gate_decision", "failure_policy", "migration",
        "report", "evidence_receipt", "not_claimed",
    }
    if set(contract) != expected_keys:
        errors.append("contract_shape")
    if contract.get("schema_version") != "hwpx-agent.p06-09-table-text-conversion-target-contract/v2":
        errors.append("schema_version")
    if contract.get("scope") != "p06_09_table_004_005_exact_current_pc_hancom_2020_save_reopen_pdf_typed_oracle":
        errors.append("scope")
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        errors.append("source_lock_canonicalization")
    predecessors = contract.get("predecessors")
    expected_predecessors = [
        {"path": path, "sha256": SOURCE_LOCKS[path], "state": "static_direct_hwpx_integration_contract"}
        for path in (
            "protocol/private/p06-table-text-to-table-hwpx-v1.json",
            "protocol/private/p06-table-table-to-text-hwpx-v1.json",
        )
    ]
    if predecessors != expected_predecessors:
        errors.append("predecessors")
    if contract.get("exact_target") != EXPECTED_TARGET:
        errors.append("exact_target")
    attempt = contract.get("successful_attempt")
    if not isinstance(attempt, dict) or attempt.get("id") != "20260913-06" or attempt.get("state") != "pass" or attempt.get("case_count") != 4:
        errors.append("successful_attempt")
    if contract.get("cases") != CASE_SPECS:
        errors.append("cases")
    history = contract.get("historical_attempts")
    if not isinstance(history, dict) or history.get("promoted_to_pass") != 0 or history.get("decision") != "immutable_failed_or_superseded_evidence_not_promoted":
        errors.append("historical_attempts")
    render = contract.get("render_oracle")
    if not isinstance(render, dict) or render.get("state") != "pass" or render.get("pdf_count") != 4 or render.get("blank_pages") != [] or any(render.get(key) is not False for key in ("clipping", "overlap", "black_boxes")):
        errors.append("render_oracle")
    gate = contract.get("gate_decision")
    expected_gate = {
        "TABLE-004": "oracle_verified", "TABLE-005": "oracle_verified",
        "actual_hancom_2020_save_reopen": "pass", "actual_hancom_2020_target_build": "pass",
        "render_diff": "pass", "rollback_or_retry": "pass", "automation_runtime": "not_run",
        "differential": "not_run", "p06_09": "in_progress", "p06": "in_progress",
    }
    if gate != expected_gate:
        errors.append("gate_decision")
    if contract.get("not_claimed") != NOT_CLAIMED:
        errors.append("not_claimed")
    if contract.get("migration") != MIGRATION or contract.get("report") != REPORT or contract.get("evidence_receipt") != RECEIPT:
        errors.append("document_paths")
    failure_policy = contract.get("failure_policy")
    if not isinstance(failure_policy, list) or len(failure_policy) != 8 or len(set(failure_policy)) != 8:
        errors.append("failure_policy")


def validate_source_locks(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        errors.append("source_locks_shape")
        return 0
    declared: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("source_lock_shape")
            continue
        path, expected = item.get("path"), item.get("sha256")
        if not isinstance(path, str) or not isinstance(expected, str) or path in declared:
            errors.append("source_lock_identity")
            continue
        declared[path] = expected
        try:
            actual = canonical_digest(bounded_bytes(root, path, 4_000_000))
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("source_lock_path")
            continue
        if actual != expected:
            errors.append("source_lock_digest")
    if declared != SOURCE_LOCKS:
        errors.append("source_locks_exact")
    return len(declared)


def validate_evidence(root: Path, errors: list[str]) -> int:
    records = dict(STATIC_RECORDS)
    for case in CASE_SPECS:
        records[input_path(case)] = (case["input_sha256"], case["input_bytes"])
        records[output_path(case)] = (case["output_sha256"], case["output_bytes"])
        records[pdf_path(case)] = (case["pdf_sha256"], case["pdf_bytes"])
    for path, expected, size in HISTORICAL:
        records[path] = (expected, size)
    for path, (expected, size) in records.items():
        try:
            payload = bounded_bytes(root, path)
        except (OSError, ValueError):
            errors.append("evidence_path")
            continue
        if len(payload) != size or digest(payload) != expected:
            errors.append("evidence_digest")
    return len(records)


def validate_manifest(root: Path, errors: list[str]) -> None:
    try:
        manifest = load_json(bounded_bytes(root, MANIFEST_PATH))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("manifest_semantics")
        return
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "hwpx-agent.p06-09-table-text-conversion-target-fixture/v1" or manifest.get("source_ancestor_sha256") != "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5" or manifest.get("actual_hangul_2020") is not False or manifest.get("render") != "not_run":
        errors.append("manifest_semantics")
        return
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        errors.append("manifest_semantics")
        return
    for actual, expected in zip(cases, CASE_SPECS, strict=True):
        if not isinstance(actual, dict) or actual.get("case_id") != expected["case_id"] or actual.get("feature_id") != expected["feature_id"] or actual.get("capability_id") != expected["capability_id"] or actual.get("file") != f"{expected['stem']}.hwpx" or actual.get("sha256") != expected["input_sha256"] or actual.get("rows") != expected["rows"] or actual.get("columns") != expected["columns"] or actual.get("state_sha256") != expected["state_sha256"] or actual.get("grid_sha256") != expected["grid_sha256"] or actual.get("text_grid_sha256") != expected["text_grid_sha256"]:
            errors.append("manifest_semantics")


def validate_trace(root: Path, errors: list[str]) -> None:
    try:
        trace = load_json(bounded_bytes(root, TRACE_PATH))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("trace_semantics")
        return
    target = trace.get("target") if isinstance(trace, dict) else None
    expected_trace_target = {"prog_id": EXPECTED_TARGET["prog_id"], "registry_view": "Registry32", "client": "windows_powershell_x86_sta", "file_version": EXPECTED_TARGET["build"], "executable_sha256": EXPECTED_TARGET["executable_sha256"]}
    watchdog = trace.get("watchdog") if isinstance(trace, dict) else None
    if not isinstance(trace, dict) or trace.get("state") != "pass" or trace.get("fixture_manifest_sha256") != STATIC_RECORDS[MANIFEST_PATH][0] or trace.get("case_count") != 4 or trace.get("completed_case_count") != 4 or target != expected_trace_target or trace.get("raw_document_text_present") is not False or trace.get("external_network_invoked") is not False or trace.get("registry_or_system_setting_changed") is not False or trace.get("computer_use_click_or_type_invoked") is not False or not isinstance(watchdog, dict) or watchdog.get("timed_out") is not False or watchdog.get("child_exit_code") != 0 or watchdog.get("remaining_hwp_process_count") != 0 or watchdog.get("progress_event_count") != 69 or watchdog.get("progress_last_phase") != "terminal" or watchdog.get("progress_last_state") != "pass":
        errors.append("trace_semantics")
        return
    cases = trace.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        errors.append("trace_semantics")
        return
    required_phases = {"open_input", "read_input", "save_as_hwpx", "close_input", "reopen_output", "read_output", "export_pdf", "close_output"}
    for actual, expected in zip(cases, CASE_SPECS, strict=True):
        phases = actual.get("phases") if isinstance(actual, dict) else None
        if not isinstance(actual, dict) or actual.get("feature_id") != expected["feature_id"] or actual.get("capability_id") != expected["capability_id"] or actual.get("input_sha256") != expected["input_sha256"] or actual.get("output_sha256") != expected["output_sha256"] or actual.get("render_pdf_sha256") != expected["pdf_sha256"] or actual.get("input_unchanged") is not True or actual.get("output_saved") is not True or actual.get("render_pdf_saved") is not True or not isinstance(phases, dict) or set(phases) != required_phases or set(phases.values()) != {"pass"}:
            errors.append("trace_semantics")


def validate_progress(root: Path, errors: list[str]) -> None:
    try:
        lines = bounded_bytes(root, PROGRESS_PATH).decode("utf-8").splitlines()
        events = [json.loads(line, object_pairs_hook=reject_duplicate_keys) for line in lines]
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("progress_semantics")
        return
    if len(events) != 69 or [event.get("sequence") for event in events] != list(range(1, 70)) or events[-1].get("phase") != "terminal" or events[-1].get("state") != "pass" or any(event.get("raw_document_text_present") is not False for event in events):
        errors.append("progress_semantics")


def validate_artifacts(root: Path, errors: list[str]) -> None:
    required = {"mimetype", "META-INF/manifest.xml", "Contents/header.xml", "Contents/section0.xml"}
    for case in CASE_SPECS:
        for path in (input_path(case), output_path(case)):
            try:
                with zipfile.ZipFile(safe_path(root, path)) as package:
                    names = set(package.namelist())
                    if not required.issubset(names) or package.testzip() is not None:
                        raise ValueError("package")
                    if path == output_path(case):
                        section = package.read("Contents/section0.xml")
                        if digest(section) != case["output_section_sha256"]:
                            raise ValueError("section")
            except (OSError, ValueError, zipfile.BadZipFile, KeyError):
                errors.append("hwpx_semantics")
        try:
            pdf = bounded_bytes(root, pdf_path(case))
            if not pdf.startswith(b"%PDF-1.4") or b"%%EOF" not in pdf[-1024:] or b"/Encrypt" in pdf or b"/JavaScript" in pdf:
                raise ValueError("pdf")
        except (OSError, ValueError):
            errors.append("pdf_semantics")


def validate_receipt(root: Path, errors: list[str]) -> None:
    try:
        receipt = load_json(bounded_bytes(root, RECEIPT))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("receipt_semantics")
        return
    attempt = receipt.get("attempt") if isinstance(receipt, dict) else None
    if not isinstance(receipt, dict) or receipt.get("schema_version") != "hwpx-agent.p06-09-table-text-conversion-current-2020-evidence/v2" or not isinstance(attempt, dict) or attempt.get("id") != "20260913-06" or attempt.get("target") != EXPECTED_TARGET or attempt.get("completed_cases") != 4 or attempt.get("timed_out") is not False or attempt.get("remaining_hwp_process_count") != 0 or receipt.get("not_claimed") != NOT_CLAIMED:
        errors.append("receipt_semantics")
        return
    contract_gate = {
        "TABLE-004": "oracle_verified", "TABLE-005": "oracle_verified",
        "actual_hancom_2020_save_reopen": "pass", "actual_hancom_2020_target_build": "pass",
        "render_diff": "pass", "rollback_or_retry": "pass", "automation_runtime": "not_run",
        "differential": "not_run", "p06_09": "in_progress", "p06": "in_progress",
    }
    if receipt.get("gate_decision") != contract_gate:
        errors.append("receipt_semantics")
    cases = receipt.get("cases")
    if not isinstance(cases, list) or len(cases) != 4:
        errors.append("receipt_semantics")
        return
    for actual, expected in zip(cases, CASE_SPECS, strict=True):
        oracle = actual.get("oracle") if isinstance(actual, dict) else None
        if not isinstance(actual, dict) or actual.get("case_id") != expected["case_id"] or actual.get("feature_id") != expected["feature_id"] or actual.get("input", {}).get("sha256") != expected["input_sha256"] or actual.get("output", {}).get("sha256") != expected["output_sha256"] or actual.get("pdf", {}).get("sha256") != expected["pdf_sha256"] or not isinstance(oracle, dict) or oracle.get("state") != "pass" or oracle.get("target_state_sha256") != expected["state_sha256"] or oracle.get("target_grid_sha256") != expected["grid_sha256"] or oracle.get("target_text_grid_sha256") != expected["text_grid_sha256"] or oracle.get("renderer_cache_sha256") != expected["cache_sha256"]:
            errors.append("receipt_semantics")
    render = receipt.get("render_review")
    if not isinstance(render, dict) or render.get("state") != "pass" or render.get("all_pages_inspected") is not True or len(render.get("pages", [])) != 4:
        errors.append("receipt_semantics")


def validate_history(root: Path, errors: list[str]) -> None:
    try:
        failed = load_json(bounded_bytes(root, HISTORICAL[0][0]))
        progress_02 = bounded_bytes(root, HISTORICAL[1][0]).decode("utf-8").splitlines()
        progress_03 = bounded_bytes(root, HISTORICAL[2][0]).decode("utf-8").splitlines()
        pass_04 = load_json(bounded_bytes(root, HISTORICAL[3][0]))
        pass_05 = load_json(bounded_bytes(root, HISTORICAL[5][0]))
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        errors.append("historical_semantics")
        return
    if failed.get("state") != "failed" or failed.get("completed_case_count") != 0 or len(progress_02) != 34 or len(progress_03) != 34 or pass_04.get("state") != "pass" or pass_05.get("state") != "pass":
        errors.append("historical_semantics")


def validate_markers(root: Path, errors: list[str]) -> int:
    markers = {
        MIGRATION: ("adds evidence, not broader conversion semantics", "may not be promoted", "does not enable automation routing"),
        REPORT: ("Decision: **PASS for TABLE-004 and TABLE-005", "69-event progress stream", "Attempts 01-05 remain immutable", "Automation runtime and direct/automation"),
        "crates/hwpx-package/examples/p06_09_table_text_conversion_target_oracle.rs": ("TABLE-004", "TABLE-005", "linesegarray"),
        "implementation/p06/tools/run-hancom-2020-table-text-conversion-target-batch-readback.ps1": ("Registry32", "remaining_hwp_process_count", "progress_event_count"),
    }
    for path, expected in markers.items():
        try:
            text = bounded_bytes(root, path, 4_000_000).decode("utf-8")
        except (OSError, UnicodeDecodeError, ValueError):
            errors.append("implementation_path")
            continue
        if any(marker not in text for marker in expected):
            errors.append("implementation_marker")
    return len(markers)


def result(errors: list[str], source_locks: int, evidence_files: int, implementation_files: int, predecessors: dict[str, Any]) -> dict[str, Any]:
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-text-conversion-target-v2-validation/v1",
        "state": "pass" if not unique else "fail", "errors": unique,
        "source_locks": source_locks, "evidence_files": evidence_files,
        "implementation_files": implementation_files, "predecessors": predecessors,
        "actual_hangul": not unique, "render": "pass" if not unique else "not_proven",
        "rollback_or_retry": "pass" if not unique else "not_proven",
        "automation_runtime": "not_run", "differential": "not_run",
        "p06_09": "in_progress", "p06": "in_progress", "product_complete": False,
    }


def expected_validation_tree() -> list[str]:
    paths = {CONTRACT, MIGRATION, REPORT, RECEIPT, MANIFEST_PATH, TRACE_PATH, PROGRESS_PATH}
    paths.update(SOURCE_LOCKS)
    paths.update(path for path, _, _ in HISTORICAL)
    for case in CASE_SPECS:
        paths.update((input_path(case), output_path(case), pdf_path(case)))
    for module in (text_to_table, table_to_text):
        paths.update((module.CONTRACT, module.MIGRATION, module.POLICY, module.REPORT))
        paths.update(module.EXPECTED_SOURCE_PATHS)
        paths.update(module.IMPLEMENTATION_MARKERS)
    return sorted(paths)


def main() -> int:
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        return 1
    print(
        "P06_TABLE_TEXT_CONVERSION_TARGET_V2_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} evidence_files={validation['evidence_files']} "
        f"implementation_files={validation['implementation_files']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
