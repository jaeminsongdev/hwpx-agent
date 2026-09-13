#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

from tools.p06 import validate_table_properties_target_v2_contract as predecessor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-properties-target-v3.json"
REPORT = "implementation/p06/P06-09_TABLE_BORDERS_DIAGONAL_TARGET_READBACK_REPORT.md"
MIGRATION = "protocol/migrations/p06-table-properties-target-v2-to-v3.md"
RECEIPT = "implementation/p06/evidence/target/p06-table-borders-diagonal.current-2020.attempt01.v3.json"
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-borders-diagonal-target-20260913-08"
MANIFEST_PATH = f"{TARGET_DIRECTORY}/fixture-manifest.json"

SOURCE_LOCKS = {
    "protocol/private/p06-table-properties-target-v2.json": "c2cbf10a9b434f715b5f5ba53b7ef947c6b1213f87c8c614e7486ba5bd884692",
    "tools/p06/validate_table_properties_target_v2_contract.py": "042ecc8c4d37da5698e5022206aebb714904331780944f8806a88d4e9a0db9c6",
    "crates/hwpx-package/src/table_ruling_hwpx.rs": "48493926f7747333cb6390ed79e78a7e172ea591313d2391e2be3c74e7da2683",
    "crates/hwpx-package/src/table_ruling_hwpx/properties_hwpx.rs": "9d1ba6454817bb4cdb42779b15952b8bd5cbad5d8b3a4fb2ed34ec651620020c",
    "crates/hwpx-package/tests/table_properties_hwpx.rs": "637991f05ff6f9952309f9445c61f5b83668a714008b50d0ef69d1386244f19b",
    "crates/hwpx-package/examples/p06_09_table_properties_target_fixture.rs": "87739dc63593a94a7df4adb8d4327fcbc85ddfa1b77d2c119e75f98efa0fa19c",
    "crates/hwpx-package/examples/p06_09_table_borders_diagonal_target_fixture.rs": "7558394caba7016bba612a4f8df0ff9c43345d6d2ce74852145b02a3092fe666",
    "crates/hwpx-package/examples/p06_09_table_properties_target_oracle.rs": "b8107333e6d5db50e8e9dcd01141a565f5bbfe247409c8fb8b9007fb230890f9",
    "crates/hwpx-package/examples/p06_09_table_borders_diagonal_target_oracle.rs": "056146c16a78a727633b90bb8742924c2b49a78b016087b329dc98f53959e8ae",
    "implementation/p06/tools/run-hancom-2020-table-properties-target-readback.ps1": "3da056958e4dac341700278a158d174bbe5eb1ceff3f39dd637939264d93b6a8",
    "implementation/p06/tests/Test-Hancom2020TablePropertiesTargetReadback.ps1": "82ed78af052dab81a8963411e04b0bed447aa3547128aee253c7efd81afacf96",
}

CASE_INFO = [
    {
        "feature_id": "TABLE-008",
        "capability_id": "table.cell_border_each",
        "stem": "table-008-cell-border-each-formula-2x4",
        "input": ("5ec86c45cbb1df724827b5126220643bf37a647d58307bbb8f4840bfe89acc30", 13188),
        "output": ("d97d7c1faafc2973484fbc379db8ade16267f46f3ed6ec4b66394e94284254b9", 15281),
        "pdf": ("d089a42dfc34c5006da22b4dc011eb195f6830f9f332b20c18006fe06f1c3b3e", 11183),
        "trace": ("69a163281a492c906084ec11072e23a17ec9e24db25e8a3683490138b107fc7e", 2329),
        "progress": ("299c428b81f91e5a47fc05f5381cb8da535a8169bddf831ea74ac51455a0dd28", 5185),
        "png": ("6f569a823bcb02b1544263d7a17e540ef75ea940b725e411e61f3167eab67acf", 12763),
        "cell_refs": ["4", "4", "3", "3", "4", "4", "3", "3"],
        "target_state_sha256": "57cc129482fa6cc19c10676764b215820c1f44054ebcc278ecaffeffb29021ee",
        "counts": [4, 16, 4, 16, 0, 0, 0, 0, 4, 1],
    },
    {
        "feature_id": "TABLE-009",
        "capability_id": "table.cell_border_unified",
        "stem": "table-009-cell-border-unified-formula-2x4",
        "input": ("c83d13e508fd78cbaa3e65a01ea2d5b7b668a4dce87188c972484c2e8223b0d8", 13262),
        "output": ("546560ec33d7ab2a1a28057f377ee747ca6aa6d17491cf531e2e192a2ed42e83", 15333),
        "pdf": ("91bef76c46e8aa06ce810da465d72b1a5f820e8a492a319c23b0d37b0988ea59", 11137),
        "trace": ("725fe3485df20c6871d7f5ddf9df5a250e71ef72c5e4df9a71237da41c2b64ca", 2329),
        "progress": ("58eedf3daa3384694d77df6f18742f3284f31609282a4ff0b658bb4dfc4b8bd6", 5185),
        "png": ("01cb447d523e742d8d54d5e6d22d30661fc38ff0181c457384b09f8f85c76cdb", 12453),
        "cell_refs": ["4", "5", "3", "3", "6", "7", "3", "3"],
        "target_state_sha256": "a78cee361c05a354684849a2e47059da1280818625498f5f7b7e8795f3ef10f5",
        "counts": [4, 16, 4, 0, 8, 8, 0, 0, 4, 4],
    },
    {
        "feature_id": "TABLE-047",
        "capability_id": "table.cell_diagonal",
        "stem": "table-047-cell-diagonal-formula-2x4",
        "input": ("26ab01ea8ba2b02430afbe2173af52bf106dbb251b23ab3a320a3d78361f36ea", 13150),
        "output": ("ff831710d4a0823105578596a96e46c3a81c0040ea8d34a9e91bf269c0163262", 16412),
        "pdf": ("df6cb08c913bad949b4276b4c08588df4d610a96ae4dfe5f491fc14ac262b112", 10321),
        "trace": ("d1ce28dbcdcf6c0eedb90d3624fb73b37bc1f73a8a04b0e049de7efe9d9571db", 2329),
        "progress": ("b669d250dccadffc46cd0e1e7d90c55576365765d5dc2fe47eda2bd8c0ca6697", 5185),
        "png": ("79bf3b100ee604fdff641d171756606676603ba243a33a2bae8f655caa00c405", 13783),
        "cell_refs": ["3", "3", "4", "3", "3", "3", "3", "3"],
        "target_state_sha256": "04d5a9e5dc88e113f229af24e3c8a521dc08d8b4a68e18bf6f31549b89327e75",
        "counts": [1, 0, 0, 0, 0, 0, 1, 1, 7, 1],
    },
]

EVIDENCE = {MANIFEST_PATH: ("05387606ca02cd9e06d44556d8ea50aaf5d80d238dbdc41f68b9c9551026bab0", 13815)}
for item in CASE_INFO:
    prefix = f"{TARGET_DIRECTORY}/{item['stem']}"
    EVIDENCE[f"{prefix}.hwpx"] = item["input"]
    EVIDENCE[f"{prefix}.hancom-2020-readback.hwpx"] = item["output"]
    EVIDENCE[f"{prefix}.hancom-2020-render.pdf"] = item["pdf"]
    EVIDENCE[f"{prefix}.trace.json"] = item["trace"]
    EVIDENCE[f"{prefix}.trace.json.progress.jsonl"] = item["progress"]
    EVIDENCE[f"{prefix}.hancom-2020-render-page-1.png"] = item["png"]
EVIDENCE[RECEIPT] = ("d67da12b1d3470ee3db1d762e34c9a8e31b17f212264f9d21182a86b21ee5d8a", 10466)

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
    REPORT: ("TABLE-008", "TABLE-009", "TABLE-047", "hatchColor", "product completion remain unclaimed"),
    MIGRATION: ("no automatic migration", "Consumers must validate v2 before v3", "fails closed"),
    RECEIPT: ("p06.table-borders-diagonal.current-2020.attempt01.20260913", "native_normalization", "rollback_or_retry"),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": ("hatchStyle", "semantic identity"),
    "crates/hwpx-package/tests/table_properties_hwpx.rs": ("solid_background_identity_ignores_inert_native_hatch_color",),
    "crates/hwpx-package/examples/p06_09_table_borders_diagonal_target_fixture.rs": ("run_table_008_009_047", "too many arguments"),
    "crates/hwpx-package/examples/p06_09_table_borders_diagonal_target_oracle.rs": ("run_table_008_009_047", "TABLE-047 oracle HWPX"),
    "crates/hwpx-package/examples/p06_09_table_properties_target_oracle.rs": ("strip_standard_renderer_caches", "table_diagonal_identity_sha256", "SUM(A2:C2)"),
}


def add_error(errors: list[str], value: str) -> None:
    if value not in errors:
        errors.append(value)


def canonical_sha256(data: bytes) -> str:
    text = data.decode("utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_validation_tree() -> list[str]:
    paths = set(SOURCE_LOCKS) | set(EVIDENCE) | set(IMPLEMENTATION_MARKERS) | {
        CONTRACT, REPORT, MIGRATION, predecessor.CONTRACT, predecessor.REPORT,
        predecessor.MIGRATION, predecessor.RECEIPT,
    }
    paths.update(predecessor.expected_validation_tree())
    return sorted(paths)


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        value = predecessor.load_json(predecessor.bounded_bytes(root, CONTRACT, 512_000))
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
        "state": "TABLE-007 oracle_verified exact current-PC target contract",
    }
    if contract.get("schema_version") != "hwpx-agent.p06-09-table-properties-target-contract/v3" \
            or contract.get("scope") != "TABLE-008 TABLE-009 TABLE-047 exact current-PC Hangul 2020 border-fill-diagonal batch oracle" \
            or contract.get("predecessor") != expected_predecessor \
            or contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        add_error(errors, "contract_identity")
    source_locks = validate_source_locks(root, contract.get("source_locks"), errors)
    evidence_files = validate_evidence(root, errors)
    validate_contract_claims(contract, errors)
    validate_manifest(root, errors)
    validate_hwpx(root, errors)
    validate_traces_and_progress(root, errors)
    validate_pdfs(root, errors)
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
            actual = canonical_sha256(predecessor.bounded_bytes(root, relative, 4 * 1024 * 1024))
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
            data = predecessor.bounded_bytes(root, relative)
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
        "TABLE-007": "oracle_verified", "TABLE-008": "oracle_verified",
        "TABLE-009": "oracle_verified", "TABLE-047": "oracle_verified",
        "actual_hancom_2020_save_reopen": "pass", "target_build": "pass",
        "render_diff": "pass", "rollback_or_retry": "pass",
        "automation_runtime": "not_run", "differential": "not_run",
        "p06_09": "in_progress", "p06": "in_progress",
    }
    expected_not_claimed = {
        "automation_runtime": False, "differential_exact_match": False,
        "arbitrary_user_document_compatibility": False, "other_pc_or_hancom_version": False,
        "p06_09_complete": False, "p06_phase_complete": False,
        "production": False, "product_complete": False,
    }
    expected_typed_oracle = {
        "rows": 2, "columns": 4, "master_cells": 8, "payload_blocks": 7,
        "formula_count_each": 1, "formula_owner": {"row": 1, "column": 3},
        "formula": "SUM(A2:C2)", "page_split": "cell",
        "renderer_cache_count_each": 10,
        "renderer_cache_sha256_each": "72864168e174956d51a0f33d9e4be3226215c2993a5216644671b81e12ccecd2",
        "section_equal_after_exact_renderer_cache_strip": True,
        "native_inert_hatch_color_normalized": True,
    }
    expected_render_oracle = {
        "state": "pass", "pages_each": 1, "page_size_points": [595, 841],
        "dpi": 144, "pixel_size": [1190, 1682], "individual_edges_visible": True,
        "unified_outer_inner_edges_visible": True, "diagonal_x_visible": True,
        "all_values_visible": True, "clipping": False, "overlap": False,
        "blank_pages": False, "black_boxes": False,
    }
    expected_failure_policy = [
        "predecessor_or_source_lock_drift_rejects",
        "manifest_target_output_pdf_trace_progress_png_or_receipt_drift_rejects",
        "duplicate_json_key_path_escape_symlink_or_size_limit_rejects",
        "typed_border_fill_diagonal_formula_pagination_or_renderer_cache_drift_rejects",
        "active_hatch_color_mismatch_rejects",
        "automation_or_differential_not_promoted",
    ]
    if contract.get("exact_target") != expected_target:
        add_error(errors, "target_identity")
    if contract.get("gate_decision") != expected_gate:
        add_error(errors, "gate_decision")
    if contract.get("not_claimed") != expected_not_claimed:
        add_error(errors, "not_claimed")
    if contract.get("typed_oracle") != expected_typed_oracle:
        add_error(errors, "typed_oracle")
    if contract.get("render_oracle") != expected_render_oracle:
        add_error(errors, "render_oracle")
    if contract.get("failure_policy") != expected_failure_policy:
        add_error(errors, "failure_policy")
    if contract.get("migration") != MIGRATION or contract.get("report") != REPORT \
            or contract.get("evidence_receipt") != RECEIPT:
        add_error(errors, "contract_paths")
    attempt = contract.get("successful_attempt", {})
    if not isinstance(attempt, dict) or attempt.get("id") != "20260913-08" \
            or attempt.get("directory") != TARGET_DIRECTORY \
            or attempt.get("manifest") != {"path": MANIFEST_PATH, "sha256": EVIDENCE[MANIFEST_PATH][0], "bytes": 13815} \
            or attempt.get("receipt") != {"path": RECEIPT, "sha256": EVIDENCE[RECEIPT][0], "bytes": EVIDENCE[RECEIPT][1]} \
            or attempt.get("state") != "pass":
        add_error(errors, "successful_attempt")
    cases = attempt.get("cases", []) if isinstance(attempt, dict) else []
    if not isinstance(cases, list) or len(cases) != 3:
        add_error(errors, "successful_attempt")
    else:
        for expected, actual in zip(CASE_INFO, cases):
            prefix = f"{TARGET_DIRECTORY}/{expected['stem']}"
            required = {
                "feature_id": expected["feature_id"],
                "input": {"path": f"{prefix}.hwpx", "sha256": expected["input"][0], "bytes": expected["input"][1]},
                "output": {"path": f"{prefix}.hancom-2020-readback.hwpx", "sha256": expected["output"][0], "bytes": expected["output"][1]},
                "pdf": {"path": f"{prefix}.hancom-2020-render.pdf", "sha256": expected["pdf"][0], "bytes": expected["pdf"][1], "pages": 1},
                "trace": {"path": f"{prefix}.trace.json", "sha256": expected["trace"][0], "bytes": expected["trace"][1]},
                "progress": {"path": f"{prefix}.trace.json.progress.jsonl", "sha256": expected["progress"][0], "bytes": expected["progress"][1], "events": 21},
                "render_png": {"path": f"{prefix}.hancom-2020-render-page-1.png", "sha256": expected["png"][0], "bytes": expected["png"][1]},
            }
            if actual != required:
                add_error(errors, "successful_attempt")
    if contract.get("retry_oracle") != {
        "state": "pass", "independent_builds": 2, "byte_deterministic": True,
        "existing_destination_rejected_without_overwrite": True,
    }:
        add_error(errors, "retry_oracle")


def validate_manifest(root: Path, errors: list[str]) -> None:
    try:
        manifest = predecessor.load_json(predecessor.bounded_bytes(root, MANIFEST_PATH, 256_000))
        cases = manifest["cases"]
        if manifest["schema_version"] != "hwpx-agent.p06-09-table-borders-diagonal-target-fixture/v1" \
                or manifest["source_ancestor_sha256"] != "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5" \
                or len(cases) != 3 or manifest["actual_hangul_2020"] is not False \
                or manifest["render"] != "not_run" or manifest["automation"] != "not_run" \
                or manifest["differential"] != "not_run":
            raise ValueError("manifest boundary")
        for expected, case in zip(CASE_INFO, cases):
            counts = [case[name] for name in (
                "changed_master_cells", "border_side_change_count", "background_change_count",
                "per_cell_edge_assignment_count", "outer_edge_assignment_count",
                "inner_edge_assignment_count", "diagonal_change_count", "diagonal_assignment_count",
                "unselected_master_cell_preserved_count", "added_border_fill_count",
            )]
            if case["feature_id"] != expected["feature_id"] \
                    or case["capability_id"] != expected["capability_id"] \
                    or case["sha256"] != expected["input"][0] \
                    or case["target_state_sha256"] != expected["target_state_sha256"] \
                    or counts != expected["counts"] or case["rows"] != 2 \
                    or case["columns"] != 4 or case["master_cells"] != 8 \
                    or case["payload_blocks"] != 7 or case["formula_count"] != 1 \
                    or case["page_split"] != "cell" or case["preserved_formula_count"] != 1:
                raise ValueError("manifest case")
        if cases[2]["diagonal_apply_mode"] != "each_cell" \
                or cases[2]["diagonal"]["slash"]["slash_type"] != "center" \
                or cases[2]["diagonal"]["back_slash"]["slash_type"] != "center" \
                or cases[2]["binding"]["diagonals"][0]["region"] is not None:
            raise ValueError("diagonal")
    except (OSError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        add_error(errors, "manifest_semantics")


def local_name(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def validate_hwpx(root: Path, errors: list[str]) -> None:
    try:
        for item in CASE_INFO:
            prefix = f"{TARGET_DIRECTORY}/{item['stem']}"
            target_path = predecessor.safe_path(root, f"{prefix}.hwpx")
            output_path = predecessor.safe_path(root, f"{prefix}.hancom-2020-readback.hwpx")
            with zipfile.ZipFile(target_path) as target_zip, zipfile.ZipFile(output_path) as output_zip:
                names = target_zip.namelist()
                if len(names) != 11 or set(names) != EXPECTED_PARTS \
                        or output_zip.namelist() != names or len(set(names)) != 11 \
                        or any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts for name in names):
                    raise ValueError("package topology")
                if any(target_zip.read(name) != output_zip.read(name) for name in IMMUTABLE_PARTS):
                    raise ValueError("immutable part")
                target_section = target_zip.read("Contents/section0.xml")
                output_section = output_zip.read("Contents/section0.xml")
                stripped, count = re.subn(rb"<hp:linesegarray>.*?</hp:linesegarray>", b"", output_section, flags=re.S)
                if count != 10 or stripped != target_section or b"<hp:linesegarray>" in target_section:
                    raise ValueError("renderer cache relation")
                validate_renderer_caches(output_section)
                if target_zip.read("Preview/PrvText.txt") != b"<2><3><4><5><17><10><25><52>\r\n\r\n" \
                        or output_zip.read("Preview/PrvText.txt") != b"<2><3><4><5>\r\n<17><10><25><52>\r\n\r\n":
                    raise ValueError("preview")
                target_root = ET.fromstring(target_section)
                table = next(element for element in target_root.iter() if local_name(element) == "tbl")
                if {name: table.get(name) for name in ("rowCnt", "colCnt", "pageBreak")} \
                        != {"rowCnt": "2", "colCnt": "4", "pageBreak": "CELL"}:
                    raise ValueError("table")
                cells = [element for element in table.iter() if local_name(element) == "tc"]
                if len(cells) != 8 or [cell.get("borderFillIDRef") for cell in cells] != item["cell_refs"]:
                    raise ValueError("cell refs")
                text = ET.tostring(cells[7], encoding="unicode")
                fields = [element for element in table.iter() if local_name(element) == "fieldBegin"]
                if len(fields) != 1 or fields[0].get("type") != "FORMULA" \
                        or "=SUM(LEFT)" not in text or "52" not in text:
                    raise ValueError("formula")
                validate_native_border_fill_normalization(item, target_zip, output_zip)
    except (OSError, KeyError, TypeError, ValueError, zipfile.BadZipFile, ET.ParseError, StopIteration):
        add_error(errors, "target_oracle_hwpx_semantics")


def validate_renderer_caches(output_section: bytes) -> None:
    root = ET.fromstring(output_section)
    arrays = [element for element in root.iter() if local_name(element) == "linesegarray"]
    if len(arrays) != 10:
        raise ValueError("renderer cache count")
    lines = []
    for array in arrays:
        children = list(array)
        if len(children) != 1 or local_name(children[0]) != "lineseg":
            raise ValueError("renderer cache shape")
        lines.append(children[0].attrib)
    common = {"textpos": "0", "vertsize": "1000", "textheight": "1000",
              "spacing": "600", "horzpos": "0", "flags": "393216"}
    if any(any(line.get(key) != value for key, value in common.items()) for line in lines):
        raise ValueError("renderer cache common values")
    geometry = [(line.get("vertpos"), line.get("baseline"), line.get("horzsize")) for line in lines]
    expected = [("0", "850", "9468")] * 8 + [("0", "850", "0"), ("8566", "850", "42520")]
    if geometry != expected:
        raise ValueError("renderer cache geometry")


def validate_native_border_fill_normalization(
    item: dict[str, Any], target_zip: zipfile.ZipFile, output_zip: zipfile.ZipFile
) -> None:
    target_header = ET.fromstring(target_zip.read("Contents/header.xml"))
    output_header = ET.fromstring(output_zip.read("Contents/header.xml"))
    target_fills = {element.get("id"): element for element in target_header.iter() if local_name(element) == "borderFill"}
    output_fills = {element.get("id"): element for element in output_header.iter() if local_name(element) == "borderFill"}
    selected_ids = sorted(set(item["cell_refs"]) - {"3"})
    for fill_id in selected_ids:
        target = target_fills[fill_id]
        output = output_fills[fill_id]
        if item["feature_id"] == "TABLE-047":
            slash = next(element for element in target if local_name(element) == "slash")
            back_slash = next(element for element in target if local_name(element) == "backSlash")
            if slash.get("type") != "CENTER" or back_slash.get("type") != "CENTER":
                raise ValueError("diagonal topology")
            continue
        target_brush = next(element for element in target.iter() if local_name(element) == "winBrush")
        output_brush = next(element for element in output.iter() if local_name(element) == "winBrush")
        if target_brush.get("faceColor") != output_brush.get("faceColor") \
                or target_brush.get("hatchStyle") is not None or output_brush.get("hatchStyle") is not None \
                or target_brush.get("hatchColor") is not None \
                or output_brush.get("hatchColor") != "#000000" \
                or target_brush.get("alpha") != "255" or output_brush.get("alpha") != "255":
            raise ValueError("native solid brush normalization")


def validate_traces_and_progress(root: Path, errors: list[str]) -> None:
    expected_events = [
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
        for item in CASE_INFO:
            prefix = f"{TARGET_DIRECTORY}/{item['stem']}"
            trace = predecessor.load_json(predecessor.bounded_bytes(root, f"{prefix}.trace.json", 256_000))
            watchdog = trace["watchdog"]
            if trace["state"] != "pass" or trace["input_sha256"] != item["input"][0] \
                    or trace["output_sha256"] != item["output"][0] \
                    or trace["render_pdf_sha256"] != item["pdf"][0] \
                    or trace["input_unchanged"] is not True or trace["output_saved"] is not True \
                    or trace["render_pdf_saved"] is not True or trace["error_code"] is not None \
                    or trace["failed_phase"] is not None or trace["raw_document_text_present"] is not False \
                    or trace["external_network_invoked"] is not False \
                    or trace["registry_or_system_setting_changed"] is not False \
                    or trace["computer_use_click_or_type_invoked"] is not False \
                    or watchdog["timed_out"] is not False or watchdog["remaining_hwp_process_count"] != 0 \
                    or watchdog["progress_event_count"] != 21 or watchdog["progress_last_state"] != "pass":
                raise ValueError("trace")
            events = [predecessor.load_json(line.encode("utf-8")) for line in
                      predecessor.bounded_bytes(root, f"{prefix}.trace.json.progress.jsonl", 256_000).decode("utf-8").splitlines()]
            if [(event.get("sequence"), event.get("phase"), event.get("state")) for event in events] != expected_events:
                raise ValueError("progress")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        add_error(errors, "trace_or_progress_semantics")


def validate_pdfs(root: Path, errors: list[str]) -> None:
    try:
        for item in CASE_INFO:
            data = predecessor.bounded_bytes(root, f"{TARGET_DIRECTORY}/{item['stem']}.hancom-2020-render.pdf")
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
            text = predecessor.bounded_bytes(root, relative, 4 * 1024 * 1024).decode("utf-8")
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
        "schema_version": "hwpx-agent.p06-09-table-properties-target-validation/v3",
        "state": state,
        "errors": unique,
        "source_locks": source_locks,
        "evidence_files": evidence_files,
        "implementation_files": implementation_files,
        "predecessor": predecessor_state,
        "TABLE-007": "oracle_verified" if state == "pass" else "not_proven",
        "TABLE-008": "oracle_verified" if state == "pass" else "not_proven",
        "TABLE-009": "oracle_verified" if state == "pass" else "not_proven",
        "TABLE-047": "oracle_verified" if state == "pass" else "not_proven",
        "p06_09": "in_progress",
        "p06": "in_progress",
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_PROPERTIES_TARGET_V3_CONTRACT_PASS "
        f"source_locks={validation['source_locks']} "
        f"evidence_files={validation['evidence_files']} "
        f"implementation_files={validation['implementation_files']}"
    )
