#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

try:
    from tools.p06 import validate_table_aggregate_hwpx_contract as predecessor
except ModuleNotFoundError:
    import validate_table_aggregate_hwpx_contract as predecessor  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-aggregate-target-v2.json"
MIGRATION = "protocol/migrations/p06-table-aggregate-hwpx-v1-to-target-v2.md"
REPORT = "implementation/p06/P06-09_TABLE_AGGREGATE_TARGET_READBACK_REPORT.md"
RECEIPT = (
    "implementation/p06/evidence/target/"
    "p06-table-aggregate.current-2020.attempt02.v2.json"
)
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-aggregate-target-20260909-05"
MANIFEST_PATH = f"{TARGET_DIRECTORY}/fixture-manifest.json"
TRACE_PATH = f"{TARGET_DIRECTORY}/target-batch-readback-20260910-02.json"
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
    "protocol/private/p06-table-aggregate-hwpx-v1.json":
        "48ef162f3d52231b92946240323283a8d6a4320715efc84e9ef243fb8cb35f87",
    "tools/p06/validate_table_aggregate_hwpx_contract.py":
        "2093c62cb0f8d5435a3c0ca2e66758d7e36cd8a13600fff48f465187ea40b230",
    "crates/hwpx-package/src/table_ruling_hwpx/aggregate_hwpx.rs":
        "76c0f88e0a7bdabdcf346b861676760a54a6d98508acc1ad622070993c8644ed",
    "crates/hwpx-package/examples/p06_09_table_aggregate_target_fixture.rs":
        "ff32a964932cc839cfd6131ebb2e673d69e5cd844687b2abc18737b513e1b445",
    "crates/hwpx-package/examples/p06_09_table_aggregate_target_oracle.rs":
        "7da6a25631e8c432492c66c9d20a06b54adb4ee885e9ab1402517c3367785f34",
    "implementation/p06/tools/run-hancom-2020-table-aggregate-target-batch-engine.ps1":
        "acdcc2ff660f42864fd3756e4b6919a7d2171e42194b97ff7cb0f3a71e5fc9d0",
    "implementation/p06/tools/run-hancom-2020-table-aggregate-target-batch-readback.ps1":
        "ce7b28184208412d21bfb4e54ec6eeeb30589e7f3b8e17f121b5302b18c41047",
    "implementation/p06/tests/Test-Hancom2020TableAggregateTargetBatchReadback.ps1":
        "f05f7dc566d3472ad7eec006549b81a0b8775c543edeb8ca505cd6f2e29c9308",
}

COMMON_GRID_SHA256 = "43701eb0fb59acabc92c7be276b739d37f4ad49d0a42a4423e187b9d87396d63"
RENDERER_CACHE_SHA256 = "4fe319c0a83442032c4e5b7c176866991236faf1654dfba27d564d06e62b9c8d"
FIELD_IDENTITY_SHA256 = "68bbc31e68d48accd4fe3ecbc8bc9811345550c489a386d77e2d75b507e03bb0"

CASE_SPECS = [
    {
        "feature_id": "TABLE-022", "capability_id": "table.block_sum",
        "stem": "table-022-block-sum", "formula": "SUM(A1:B2)", "cache": "32",
        "input_sha256": "56942277d33e114e6d6a960751b337b715903d0fec82018a7eb22c8fcbd4773c",
        "input_bytes": 13111,
        "text_sha256": "29d0e12d32973afa8d18e75d9765abf375f9f92cb211fa6d444708367d2addc2",
        "output_sha256": "91735b23a3b3ef528df1f6c411cb1cc1e7aaa895cb2f8de75be1f9eed331dadc",
        "output_bytes": 14384,
        "section_sha256": "14ec26994339672962cb75c320280b641a3324964b7d882baa45ba2e176e4452",
        "pdf_sha256": "2df0188f99e7a15eb534edbb60a70ba51ebe1f26fa620b3f6d3ad688b685ac2e",
        "pdf_bytes": 10275,
        "state_sha256": "46cb8be768008bab7d575ca4d3be0aaccbec0060ca16944973f7d56de05e5500",
        "png_sha256": "1642d378f34dc2f1edda9f3f0d31cc2375b54ebd954e9a95d6f229dcedceee6d",
        "png_bytes": 11845,
    },
    {
        "feature_id": "TABLE-023", "capability_id": "table.block_average",
        "stem": "table-023-block-average", "formula": "AVG(A1:B2)", "cache": "8",
        "input_sha256": "f41282f85af76278259d3b08a947c6afa73b58c8598d5cc1f4c042a8cfa7d79a",
        "input_bytes": 13108,
        "text_sha256": "6eae3d0fe0cbdd9cedb3c0dc584739db1ae0b3280b8d9164dc2cc60396705328",
        "output_sha256": "fca2c3f28cf6c6f399843d83972e9ccf97b4d54774eff4adbd45e9b70f2a6783",
        "output_bytes": 14376,
        "section_sha256": "e362cc505518b120bad4644c0a12a8c2c3e5396f89211593091e8c64b2443aeb",
        "pdf_sha256": "17922dd2797b194d735cd16bf2389f1202fa37bba518d5882f4acfc76188d4df",
        "pdf_bytes": 10481,
        "state_sha256": "28d2f00da19838a13c98f92873cf06861308956c6edb3471a07d4c83e8a2490e",
        "png_sha256": "100a952c9855c0734c9c4533e7965d59b471d152faf093ae50a0362c69e9921f",
        "png_bytes": 11618,
    },
    {
        "feature_id": "TABLE-024", "capability_id": "table.block_product",
        "stem": "table-024-block-product", "formula": "PRODUCT(A1:B2)", "cache": "1020",
        "input_sha256": "a87247142a5ae9699adfbf931e2be81ce1957f2cc985fb40ce1b63efee8b13c1",
        "input_bytes": 13115,
        "text_sha256": "eed6d1c92e34c978f60cfe8ec5bef79dc5995a18687174929d9510e586699426",
        "output_sha256": "d1a3dde89982bcbc67e153ffd1b02d76566f91f5343736098afa34d25de4dd53",
        "output_bytes": 14413,
        "section_sha256": "f970938309fb8e75a210f1ee23025c45b5952f513039156f5c3b1c00e235dd41",
        "pdf_sha256": "2c19e098a513f8c86935b4f787469255122b26c820c3af97ac46a5ae6981d804",
        "pdf_bytes": 10276,
        "state_sha256": "608af33e448f832d1e70b83134a7d59a69f0ca0f0b60197742068e4f66796eb3",
        "png_sha256": "e73491de78160570d32a8bf7a77cdb9c178ac3a9f6085b30c2239854acf654cd",
        "png_bytes": 11866,
    },
    {
        "feature_id": "TABLE-026", "capability_id": "table.vertical_sum",
        "stem": "table-026-vertical-sum", "formula": "SUM(D1:D1)", "cache": "5",
        "input_sha256": "f48fa45a4cd107a086ea6a0411f5102141d8e90317e775944bf5bf0eedd588cf",
        "input_bytes": 13105,
        "text_sha256": "7931430cae18afda32f05c77a6a61d571d653a3dbbc4cf75361e0a1c97e2b405",
        "output_sha256": "0f7dfd81666d393d1ad41f363f8f88c7e199696ad50865629431599d2ab0abc6",
        "output_bytes": 14332,
        "section_sha256": "6a746bc5c2960ae66dd01cfa506ff61b1935657c378413c75f0fcc6bc230adce",
        "pdf_sha256": "f2a49d6cce926465fa6f9fc613abbd109d53887f3d2554756e3d099629b573f3",
        "pdf_bytes": 10271,
        "state_sha256": "b5ddd2cd2ab6f68efab8b80e59a31090c3eb852fff31ced918a03020c08f38b0",
        "png_sha256": "c5c54bd7664ed4fdf249ab96cd9f3889d716ef85618c8306631803d4d69bfb56",
        "png_bytes": 11519,
    },
    {
        "feature_id": "TABLE-027", "capability_id": "table.horizontal_average",
        "stem": "table-027-horizontal-average", "formula": "AVG(A2:B2)", "cache": "13.5",
        "input_sha256": "2a693e1d09a14cea67c2f27c3d81bfa1574bc8938aafdba7933bedffb38dd84c",
        "input_bytes": 13112,
        "text_sha256": "2d6fed1eb9de3d87534b74b82dd93ac43fae719a18bb51559be7cc674c20d79c",
        "output_sha256": "46ef052d32d3760035cb4943d14838420d22dfe5a0bb16eb2c3e0f152c33dcd1",
        "output_bytes": 14423,
        "section_sha256": "a0cc093ba154980825357d7edecdfb6aee950c000e1d11f524dcb688a13a7061",
        "pdf_sha256": "476051b5c7bc9911a6281c25274c85ccc3456ecf375552494bf9ab0432e18e67",
        "pdf_bytes": 10364,
        "state_sha256": "bb8147c15114f3192808c1831f9de9f9cade3cde8341c7ffafe1ca58d013333e",
        "png_sha256": "f0dc02c5716a0c008c58e797777484fc71168be05d66b66b11c2be0e2d5b186e",
        "png_bytes": 11889,
    },
    {
        "feature_id": "TABLE-028", "capability_id": "table.vertical_average",
        "stem": "table-028-vertical-average", "formula": "AVG(D1:D1)", "cache": "5",
        "input_sha256": "7129fb774e5e12c0e320cfffdb2394776078c3be2c2065555b1720873dcb0788",
        "input_bytes": 13105,
        "text_sha256": "7931430cae18afda32f05c77a6a61d571d653a3dbbc4cf75361e0a1c97e2b405",
        "output_sha256": "54b43642023cae916d3e3358ddcdd459ccd8c4b6e59808b2d76dbe262f1fb855",
        "output_bytes": 14332,
        "section_sha256": "482733aca5c0a7d533c73ff73d4ae69287073ee061edc7b78a54adb2fe6a2c8f",
        "pdf_sha256": "e119bf6719d6f726f6b1832afdfddaec2da2a9652fccf6750c2d732c8ac1f4e6",
        "pdf_bytes": 10271,
        "state_sha256": "0f4cc1136ae667890637c5ba8e0153ecc22c082ad505947a24f8868d6f78fe7b",
        "png_sha256": "c5c54bd7664ed4fdf249ab96cd9f3889d716ef85618c8306631803d4d69bfb56",
        "png_bytes": 11519,
    },
    {
        "feature_id": "TABLE-029", "capability_id": "table.horizontal_product",
        "stem": "table-029-horizontal-product", "formula": "PRODUCT(A2:B2)", "cache": "170",
        "input_sha256": "186af7b72b812a5bbf3ee2b0d8756cd1e617ab0606be3a6a53b5a17db88f9f96",
        "input_bytes": 13112,
        "text_sha256": "63765b84745b82bc91b5b5b82860611c74648402a0caad8fa520ae174edcaf1c",
        "output_sha256": "784d90c6126de61ffd889b784e9cce9478978a210a4b1a11cc1bddd901ec1ba0",
        "output_bytes": 14408,
        "section_sha256": "57e0c1cef6b7fa84ccc2ae833edb6a2e134bee7cbaf85b7016ed5980caf2e797",
        "pdf_sha256": "18ffdf62d58184931df692d189dd76921db0dc1af2cbf98d712553214588b04e",
        "pdf_bytes": 10273,
        "state_sha256": "a53001e1f9596044141c0466e5ce1d8ca62725c299422256a07afc9505fdec09",
        "png_sha256": "3dfe480c6cb5af30fc99f608fa9228f200660ec608163787bdcef3f06350ed86",
        "png_bytes": 11573,
    },
    {
        "feature_id": "TABLE-030", "capability_id": "table.vertical_product",
        "stem": "table-030-vertical-product", "formula": "PRODUCT(D1:D1)", "cache": "5",
        "input_sha256": "403e4645923362719262f142a9c59b904a058f8d009d7a57b0b772d1cfe62a14",
        "input_bytes": 13108,
        "text_sha256": "7931430cae18afda32f05c77a6a61d571d653a3dbbc4cf75361e0a1c97e2b405",
        "output_sha256": "da1db8967f3f1d0d29836996c65a785469e55cc9af1752b771dc0aabba8bb793",
        "output_bytes": 14336,
        "section_sha256": "6e0e2d33623de56d310487f5d3471ca58c0ed951b47f85f78f7488ab490acd2d",
        "pdf_sha256": "994f3cd69405641cf52494cc584b8d0b6a519c33673d35d929de640414422b05",
        "pdf_bytes": 10271,
        "state_sha256": "56b138d854b36c2a8f4db44bb68435264fbc1486af5fbc9ccad9b42916123afe",
        "png_sha256": "c5c54bd7664ed4fdf249ab96cd9f3889d716ef85618c8306631803d4d69bfb56",
        "png_bytes": 11519,
    },
]

MANIFEST_SHA256 = "b58c3b68d156550512674d894427bc94dcb26d014f687d3e32e8918a37acc363"
TRACE_SHA256 = "b5712fbff5b604e06c44962512763c2a24fb16c61892428b205c7793891ee786"
PROGRESS_SHA256 = "9d79a4172f3d0e799437ec3b55b381902ccfdf41f98e232a624a717a0b74ed47"
RECEIPT_SHA256 = "edc71d554e0975d511ffe6f0de1b140a30ca932d0bf2b9c7b70517c5e8674fc5"
RECEIPT_BYTES = 22336
HISTORICAL = [
    (f"{TARGET_DIRECTORY}/target-batch-readback-20260910-01.json",
     "6370f13826299975d6d1951937d0d790ba58bd7a13a7454bf7caed1d784bd31b", 6929),
    (f"{TARGET_DIRECTORY}/target-batch-readback-20260910-01.json.progress.jsonl",
     "8c9f5d7b4bdeaed996390731a11ee532087e6b0926bb0f0775c10563bd96d7ef", 864),
]

NOT_CLAIMED = {
    "formula_evaluation_or_verified_cache": False,
    "automation_runtime": False,
    "differential_exact_match": False,
    "arbitrary_user_document_compatibility": False,
    "merged_or_existing_formula_source": False,
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
    if path.is_symlink() or not path.is_file() or stat.st_size == 0 or stat.st_size > limit:
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
    validate_artifacts(root, errors)
    validate_receipt(root, errors)
    validate_historical(root, errors)
    implementation_count = validate_markers(root, errors)
    return result(errors, source_count, evidence_count, implementation_count,
                  str(predecessor_result.get("state")))


def contract_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "feature_id": case["feature_id"], "capability_id": case["capability_id"],
        "formula": case["formula"], "unverified_cache": case["cache"],
        "input_sha256": case["input_sha256"], "output_sha256": case["output_sha256"],
        "pdf_sha256": case["pdf_sha256"], "target_state_sha256": case["state_sha256"],
        "target_grid_sha256": COMMON_GRID_SHA256,
        "section_equal_after_exact_renderer_normalization": True,
    }


def gate_decision(boolean_values: bool) -> dict[str, Any]:
    decision: dict[str, Any] = {case["feature_id"]: "oracle_verified" for case in CASE_SPECS}
    decision.update({
        "actual_hancom_2020_save_reopen": boolean_values if boolean_values else "pass",
        "actual_hancom_2020_target_build": boolean_values if boolean_values else "pass",
        "render_diff": boolean_values if boolean_values else "pass",
        "rollback_or_retry": boolean_values if boolean_values else "pass",
        "automation_runtime": "not_run", "differential": "not_run",
        "p06_09": "in_progress", "p06": "in_progress",
    })
    return decision


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
        "schema_version": "hwpx-agent.p06-09-table-aggregate-target-contract/v2",
        "scope": (
            "p06_09_eight_aggregate_rows_exact_current_pc_hancom_2020_"
            "save_reopen_pdf_typed_oracle"
        ),
        "predecessor": {
            "path": predecessor.CONTRACT, "sha256": SOURCE_LOCKS[predecessor.CONTRACT],
            "state": "immutable_static_direct_hwpx_integration_contract",
        },
        "source_lock_canonicalization": "exact_file_bytes_sha256",
        "exact_target": EXPECTED_TARGET,
        "successful_attempt": {
            "id": "20260910-02", "directory": TARGET_DIRECTORY,
            "manifest": record(MANIFEST_PATH, MANIFEST_SHA256, 8197),
            "trace": record(TRACE_PATH, TRACE_SHA256, 11054),
            "progress": {**record(PROGRESS_PATH, PROGRESS_SHA256, 39554), "events": 133},
            "receipt": record(RECEIPT, RECEIPT_SHA256, RECEIPT_BYTES),
            "case_count": 8, "state": "pass",
        },
        "historical_attempts": {
            "failed_attempt_ids": ["20260910-01"],
            "evidence": [record(*item) for item in HISTORICAL],
            "promoted_to_pass": 0, "decision": "immutable_failed_evidence",
        },
        "cases": [contract_case(case) for case in CASE_SPECS],
        "render_oracle": {
            "state": "pass", "pdf_count": 8, "pages_each": 1,
            "page_size_points": [595, 841], "producer": "Hancom PDF 1.3.0.550",
            "renderer": "pdftoppm 26.07.0", "dpi": 144,
            "pixel_size": [1190, 1682], "inspection_detail": "original",
            "clipping": False, "overlap": False, "blank_pages": [], "black_boxes": False,
        },
        "gate_decision": gate_decision(False),
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
    values = [
        (MANIFEST_PATH, MANIFEST_SHA256, 8197),
        (TRACE_PATH, TRACE_SHA256, 11054),
        (PROGRESS_PATH, PROGRESS_SHA256, 39554),
        (RECEIPT, RECEIPT_SHA256, RECEIPT_BYTES),
    ]
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
            "schema_version", "source_ancestor_sha256", "source_file", "source_sha256",
            "source_section_sha256", "cases", "actual_hangul_2020", "render",
            "automation", "differential",
        } or manifest.get("schema_version") \
                != "hwpx-agent.p06-09-table-aggregate-target-fixture/v1" \
                or manifest.get("source_ancestor_sha256") \
                != "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5" \
                or manifest.get("source_file") != "source.hwpx" \
                or manifest.get("actual_hangul_2020") is not False \
                or manifest.get("render") != "not_run" \
                or manifest.get("automation") != "not_run" \
                or manifest.get("differential") != "not_run":
            raise ValueError("manifest root")
        cases = manifest.get("cases")
        if not isinstance(cases, list) or len(cases) != 8:
            raise ValueError("manifest cases")
        for actual, expected in zip(cases, CASE_SPECS, strict=True):
            if set(actual) != {
                "feature_id", "capability_id", "file", "sha256", "formula",
                "unverified_cache", "expected_hangul_text_sha256", "source_state_sha256",
                "target_state_sha256", "source_grid_sha256", "target_grid_sha256",
                "request_sha256", "plan_sha256",
            } or actual.get("feature_id") != expected["feature_id"] \
                    or actual.get("capability_id") != expected["capability_id"] \
                    or actual.get("file") != f"{expected['stem']}.hwpx" \
                    or actual.get("sha256") != expected["input_sha256"] \
                    or actual.get("formula") != expected["formula"] \
                    or actual.get("unverified_cache") != expected["cache"] \
                    or actual.get("expected_hangul_text_sha256") != expected["text_sha256"] \
                    or actual.get("target_state_sha256") != expected["state_sha256"] \
                    or actual.get("source_grid_sha256") != COMMON_GRID_SHA256 \
                    or actual.get("target_grid_sha256") != COMMON_GRID_SHA256 \
                    or not all(isinstance(actual.get(key), str)
                               and re.fullmatch(r"[0-9a-f]{64}", actual[key])
                               for key in ("source_state_sha256", "request_sha256", "plan_sha256")):
                raise ValueError("manifest case")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError):
        errors.append("manifest_semantics")


def validate_trace(root: Path, errors: list[str]) -> None:
    try:
        trace = load_json(bounded_bytes(root, TRACE_PATH, 256_000))
        target = {
            "prog_id": EXPECTED_TARGET["prog_id"], "registry_view": "Registry32",
            "client": "windows_powershell_x86_sta", "file_version": EXPECTED_TARGET["build"],
            "executable_sha256": EXPECTED_TARGET["executable_sha256"],
        }
        if trace.get("schema_version") \
                != "hwpx-agent.p06-09-hancom-2020-table-aggregate-target-batch-readback/v1" \
                or trace.get("state") != "pass" or trace.get("target") != target \
                or trace.get("fixture_manifest_sha256") != MANIFEST_SHA256 \
                or trace.get("case_count") != 8 or trace.get("completed_case_count") != 8 \
                or trace.get("failed_feature_id") is not None \
                or trace.get("error_code") is not None or trace.get("failed_phase") is not None \
                or trace.get("exception_type") is not None \
                or trace.get("exception_hresult") is not None:
            raise ValueError("trace root")
        phases = {
            "open_input": "pass", "read_input": "pass", "save_as_hwpx": "pass",
            "close_input": "pass", "reopen_output": "pass", "read_output": "pass",
            "export_pdf": "pass", "close_output": "pass",
        }
        cases = trace.get("cases")
        if not isinstance(cases, list) or len(cases) != 8:
            raise ValueError("trace cases")
        for actual, expected in zip(cases, CASE_SPECS, strict=True):
            if actual.get("feature_id") != expected["feature_id"] \
                    or actual.get("capability_id") != expected["capability_id"] \
                    or actual.get("input_sha256") != expected["input_sha256"] \
                    or actual.get("input_text_sha256") != expected["text_sha256"] \
                    or actual.get("output_sha256") != expected["output_sha256"] \
                    or actual.get("output_text_sha256") != expected["text_sha256"] \
                    or actual.get("render_pdf_sha256") != expected["pdf_sha256"] \
                    or actual.get("render_pdf_bytes") != expected["pdf_bytes"] \
                    or actual.get("input_unchanged") is not True \
                    or actual.get("output_saved") is not True \
                    or actual.get("render_pdf_requested") is not True \
                    or actual.get("render_pdf_saved") is not True \
                    or actual.get("render_pdf_signature_valid") is not True \
                    or actual.get("render_pdf_export_method") != "IXHwpDocument.SaveAs/PDF" \
                    or actual.get("phases") != phases \
                    or actual.get("error_code") is not None \
                    or actual.get("failed_phase") is not None:
                raise ValueError("trace case")
        if trace.get("watchdog") != {
            "timeout_seconds": 1800, "timed_out": False, "child_exit_code": 0,
            "output_drained": True, "cleaned_process_count": 0,
            "cleanup_refused_count": 0, "cleanup_error_count": 0,
            "remaining_hwp_process_count": 0, "progress_present": True,
            "progress_valid": True, "progress_event_count": 133,
            "progress_last_phase": "terminal", "progress_last_state": "pass",
            "progress_observed_phase": "quit", "progress_observed_feature_id": None,
            "window_visible_for_user_access": True,
        } or trace.get("raw_document_text_present") is not False \
                or trace.get("user_document_scanned") is not False \
                or trace.get("external_network_invoked") is not False \
                or trace.get("registry_or_system_setting_changed") is not False \
                or trace.get("computer_use_click_or_type_invoked") is not False \
                or trace.get("window_visible_for_user_access") is not True \
                or trace.get("delegated_engine_schema") \
                != "hwpx-agent.p06-09-hancom-2020-table-aggregate-target-batch-engine/v1":
            raise ValueError("trace safety")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError):
        errors.append("trace_semantics")


def validate_progress(root: Path, errors: list[str]) -> None:
    expected: list[tuple[int, int, str | None, str, str]] = [
        (1, 0, None, "preflight", "pass"),
        (2, 0, None, "com_create", "pass"),
    ]
    sequence = 3
    phases = ["open_input", "read_input", "save_as_hwpx", "close_input",
              "reopen_output", "read_output", "export_pdf", "close_output"]
    for index, case in enumerate(CASE_SPECS, start=1):
        for phase in phases:
            expected.append((sequence, index, case["feature_id"], phase, "running"))
            expected.append((sequence + 1, index, case["feature_id"], phase, "pass"))
            sequence += 2
    expected.extend([
        (131, 0, None, "quit", "running"),
        (132, 0, None, "quit", "pass"),
        (133, 8, "TABLE-030", "terminal", "pass"),
    ])
    try:
        text = bounded_bytes(root, PROGRESS_PATH, 256_000).decode("utf-8")
        events = [load_json(line.encode("utf-8")) for line in text.splitlines()]
        actual = [(item.get("sequence"), item.get("case_index"), item.get("feature_id"),
                   item.get("phase"), item.get("state")) for item in events]
        worker_ids = {item.get("worker_process_id") for item in events}
        hwp_ids = {item.get("hwp_process_id") for item in events[1:]}
        if actual != expected or len(events) != 133 or len(worker_ids) != 1 \
                or not all(isinstance(item, int) and item > 0 for item in worker_ids) \
                or len(hwp_ids) != 1 \
                or not all(isinstance(item, int) and item > 0 for item in hwp_ids) \
                or any(item.get("schema_version") \
                       != "hwpx-agent.p06-09-table-aggregate-batch-progress/v1"
                       or item.get("raw_document_text_present") is not False
                       or not isinstance(item.get("recorded_at_utc"), str)
                       or not item["recorded_at_utc"].endswith("Z") for item in events):
            raise ValueError("progress")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError):
        errors.append("progress_semantics")


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def validate_artifacts(root: Path, errors: list[str]) -> None:
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
        raise ValueError("hwpx")
    with zipfile.ZipFile(path) as package:
        entries = package.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != 11 or len(set(names)) != len(names) \
                or any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
                       for name in names) \
                or sum(entry.file_size for entry in entries) > 8 * 1024 * 1024:
            raise ValueError("package graph")
        section = package.read("Contents/section0.xml")
    if output and digest(section) != case["section_sha256"]:
        raise ValueError("section digest")
    document = ET.fromstring(section)
    tables = [item for item in document.iter() if local_name(item.tag) == "tbl"]
    rows = [item for item in tables[0] if local_name(item.tag) == "tr"] if len(tables) == 1 else []
    masters = sum(1 for row in rows for item in row if local_name(item.tag) == "tc")
    fields = [item for item in document.iter()
              if local_name(item.tag) == "fieldBegin" and item.get("type") == "FORMULA"]
    ends = [item for item in document.iter() if local_name(item.tag) == "fieldEnd"]
    caches = sum(1 for item in document.iter() if local_name(item.tag) == "linesegarray")
    if len(tables) != 1 or tables[0].get("rowCnt") != "2" \
            or tables[0].get("colCnt") != "4" or len(rows) != 2 or masters != 8 \
            or len(fields) != 1 or len(ends) != 1:
        raise ValueError("typed table")
    begin_id = fields[0].get("fieldid")
    end_id = ends[0].get("fieldid")
    if not begin_id or not begin_id.isdigit() or int(begin_id) <= 0 or end_id != begin_id:
        raise ValueError("field identity")
    parameters = {item.get("name"): item.text for item in fields[0].iter()
                  if local_name(item.tag) == "stringParam"}
    if parameters != {
        "Command": f"={case['formula']}??%g,;;{case['cache']}",
        "Formula": f"={case['formula']}", "ResultFormat": "%g,",
        "LastResult": case["cache"],
    } or caches != (10 if output else 0):
        raise ValueError("formula or renderer profile")


def expected_receipt_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "feature_id": case["feature_id"], "capability_id": case["capability_id"],
        "formula": case["formula"], "unverified_cache": case["cache"],
        "input": {**record(input_path(case), case["input_sha256"], case["input_bytes"]),
                  "text_sha256": case["text_sha256"], "unchanged": True},
        "output": {**record(output_path(case), case["output_sha256"], case["output_bytes"]),
                   "section_sha256": case["section_sha256"],
                   "text_sha256": case["text_sha256"]},
        "pdf": {**record(pdf_path(case), case["pdf_sha256"], case["pdf_bytes"]), "pages": 1},
        "oracle": {
            "state": "pass", "target_state_sha256": case["state_sha256"],
            "target_grid_sha256": COMMON_GRID_SHA256, "rows": 2, "columns": 4,
            "master_cells": 8, "payload_blocks": 7, "formulas": 1,
            "renderer_cache_count": 10, "cell_renderer_cache_count": 8,
            "renderer_cache_sha256": RENDERER_CACHE_SHA256,
            "renderer_field_identity_sha256": FIELD_IDENTITY_SHA256,
            "target_table_height_hwpunit": 564, "output_table_height_hwpunit": 2564,
            "section_equal_after_exact_renderer_normalization": True,
        },
    }


def validate_receipt(root: Path, errors: list[str]) -> None:
    try:
        receipt = load_json(bounded_bytes(root, RECEIPT, 512_000))
        if set(receipt) != {
            "schema_version", "evidence_id", "scope", "attempt", "cases",
            "render_review", "retry_evidence", "safety", "gate_decision", "not_claimed",
        } or receipt.get("schema_version") \
                != "hwpx-agent.p06-09-table-aggregate-current-2020-evidence/v2" \
                or receipt.get("evidence_id") \
                != "p06.table-aggregate.current-2020.attempt02.20260910" \
                or receipt.get("scope") \
                != "exact_current_pc_hancom_2020_table_aggregate_save_reopen_pdf_and_independent_oracle":
            raise ValueError("receipt root")
        expected_attempt = {
            "id": "20260910-02", "directory": TARGET_DIRECTORY,
            "manifest": record(MANIFEST_PATH, MANIFEST_SHA256, 8197),
            "trace": {**record(TRACE_PATH, TRACE_SHA256, 11054), "state": "pass"},
            "progress": {**record(PROGRESS_PATH, PROGRESS_SHA256, 39554),
                         "events": 133, "terminal": "pass"},
            "target": EXPECTED_TARGET, "completed_cases": 8, "failed_feature_id": None,
            "timed_out": False, "remaining_hwp_process_count": 0,
        }
        if receipt.get("attempt") != expected_attempt \
                or receipt.get("cases") != [expected_receipt_case(case) for case in CASE_SPECS]:
            raise ValueError("receipt evidence")
        pages = receipt.get("render_review", {}).get("pages")
        if receipt.get("render_review", {}).get("state") != "pass" \
                or receipt["render_review"].get("engine") != "pdftoppm 26.07.0" \
                or receipt["render_review"].get("dpi") != 144 \
                or receipt["render_review"].get("page_size_points") != [595, 841] \
                or receipt["render_review"].get("pixel_size") != [1190, 1682] \
                or receipt["render_review"].get("producer") != "Hancom PDF 1.3.0.550" \
                or receipt["render_review"].get("pdf_version") != "1.4" \
                or receipt["render_review"].get("all_pages_inspected") is not True \
                or receipt["render_review"].get("inspection_detail") != "original" \
                or receipt["render_review"].get("clipping") is not False \
                or receipt["render_review"].get("overlap") is not False \
                or receipt["render_review"].get("blank_pages") != [] \
                or receipt["render_review"].get("black_boxes") is not False \
                or receipt["render_review"].get("rendered_png_retention") \
                != "ephemeral_review_intermediate_not_product_input" \
                or not isinstance(pages, list) or len(pages) != 8:
            raise ValueError("render review")
        for page, case in zip(pages, CASE_SPECS, strict=True):
            if page.get("feature_id") != case["feature_id"] \
                    or page.get("png_sha256") != case["png_sha256"] \
                    or page.get("png_bytes") != case["png_bytes"] \
                    or not isinstance(page.get("finding"), str) \
                    or "no_layout_defect" not in page["finding"]:
                raise ValueError("render page")
        if receipt.get("retry_evidence") != {
            "state": "pass", "failed_attempts_preserved": 1,
            "successful_create_only_attempt": "20260910-02",
            "same_manifest_and_input_digests": True, "partial_output_promoted": False,
            "input_unchanged": True, "owned_process_cleanup_bounded": True,
        } or receipt.get("safety") != {
            "raw_document_text_retained": False, "user_document_scanned": False,
            "external_network_invoked": False, "registry_or_system_setting_changed": False,
            "computer_use_click_or_type_invoked": False, "source_packages_modified": False,
        } or receipt.get("gate_decision") != gate_decision(True) \
                or receipt.get("not_claimed") != NOT_CLAIMED:
            raise ValueError("receipt decision")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError, KeyError):
        errors.append("receipt_semantics")


def validate_historical(root: Path, errors: list[str]) -> None:
    try:
        failed = load_json(bounded_bytes(root, HISTORICAL[0][0], 256_000))
        if failed.get("state") != "failed" or failed.get("completed_case_count") != 0 \
                or failed.get("error_code") != "TABLE_AGGREGATE_TARGET_BATCH_READBACK_TIMEOUT" \
                or failed.get("watchdog", {}).get("timed_out") is not True \
                or failed.get("watchdog", {}).get("remaining_hwp_process_count") != 0 \
                or any(case.get("output_saved") is not False
                       or case.get("render_pdf_saved") is not False
                       or case.get("input_unchanged") is not True
                       for case in failed.get("cases", [])):
            raise ValueError("failed trace")
        events = [load_json(line.encode("utf-8")) for line in
                  bounded_bytes(root, HISTORICAL[1][0], 256_000).decode("utf-8").splitlines()]
        if any(item.get("phase") == "terminal" and item.get("state") == "pass"
               for item in events):
            raise ValueError("historical progress promoted")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError, TypeError):
        errors.append("historical_semantics")


def validate_markers(root: Path, errors: list[str]) -> int:
    markers = {
        MIGRATION: (
            "complete section byte-identical", "historical failed evidence are not rewritten",
            "verified cache refresh are not claimed",
        ),
        REPORT: (
            "Decision: **PASS for the eight aggregate rows", "133-event progress journal",
            "The resulting complete `section0.xml` equals the", "Automation runtime",
        ),
        RECEIPT: (
            "p06.table-aggregate.current-2020.attempt02.20260910",
            '"partial_output_promoted": false', '"product_complete": false',
        ),
        "crates/hwpx-package/examples/p06_09_table_aggregate_target_oracle.rs": (
            "section_equal_after_exact_renderer_normalization=true",
            "normalize_renderer_field_identity", "renderer_field_identity_sha256",
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
        "schema_version": "hwpx-agent.p06-table-aggregate-target-validation/v2",
        "state": state, "errors": unique, "source_locks": source_locks,
        "evidence_files": evidence_files, "implementation_files": implementation_files,
        "predecessor": predecessor_state, "features": 8, "cases": 8,
        "direct_stage": "oracle_verified" if state == "pass" else "not_proven",
        "actual_hancom_2020_save_reopen": "pass" if state == "pass" else "not_proven",
        "actual_hancom_2020_render": "pass" if state == "pass" else "not_proven",
        "rollback_or_retry": "pass" if state == "pass" else "not_proven",
        "formula_evaluation": "not_claimed", "automation_runtime": "not_run",
        "differential": "not_run", "p06_09": "in_progress", "p06": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_AGGREGATE_TARGET_V2_CONTRACT_PASS "
        f"features={validation['features']} cases={validation['cases']} "
        f"source_locks={validation['source_locks']} evidence_files={validation['evidence_files']}"
    )
