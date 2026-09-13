#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

try:
    from tools.p06 import validate_table_structure_hwpx_contract as predecessor
except ModuleNotFoundError:
    import validate_table_structure_hwpx_contract as predecessor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-structure-target-v2.json"
REPORT = "implementation/p06/P06-09_TABLE_STRUCTURE_TARGET_READBACK_REPORT.md"
MIGRATION = "protocol/migrations/p06-table-structure-hwpx-v1-to-target-v2.md"
RECEIPT = "implementation/p06/evidence/target/p06-table-structure.current-2020.attempt01.v2.json"
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-structure-target-20260913-05"
MANIFEST = f"{TARGET_DIRECTORY}/fixture-manifest.json"

SOURCE_LOCKS = {
    "protocol/private/p06-table-structure-hwpx-v1.json": "adc72910ad5766617b454cc8f8a2e96a154871131e745831ee04dbec082e448c",
    "tools/p06/validate_table_structure_hwpx_contract.py": "f461d390f9e421fc208343b432c46e140659e44e48d1daeb55c07c3dc0d63632",
    "crates/hwpx-package/src/table_ruling_hwpx.rs": "5b37569e339dac33f7f6f1ef1c45e9deefcbc47a5a44de4a10449b628c015946",
    "crates/hwpx-package/src/table_ruling_hwpx/structure_hwpx.rs": "dd9f70ab869c48da9962885414fda96da8fb6467ff0b7e509cb9841fc88b336c",
    "crates/hwpx-package/tests/table_structure_hwpx.rs": "582687ae6fded4ae8ebe9b9b7e9f89f53a91d792c07c1b7e76af5a88f71310ea",
    "crates/hwpx-package/examples/p06_09_table_structure_target_fixture.rs": "23b6cd0d4332bdaf7391467a1e507c27a3b0b4d35e7949a75e680c689f69226b",
    "crates/hwpx-package/examples/p06_09_table_structure_target_oracle.rs": "70558b57106e6cfe535048618dc66c37917c9e5f01c9358c05c9b8f23476bf25",
    "implementation/p06/tools/run-hancom-2020-table-properties-target-readback.ps1": "3da056958e4dac341700278a158d174bbe5eb1ceff3f39dd637939264d93b6a8",
    "implementation/p06/tests/Test-Hancom2020TablePropertiesTargetReadback.ps1": "82ed78af052dab81a8963411e04b0bed447aa3547128aee253c7efd81afacf96",
}

CASE_INFO = [
    {
        "feature_id": "TABLE-012", "capability_id": "table.insert_rows",
        "stem": "table-012-insert-row-3x3",
        "input": ("0459a05b8543edb2e05c9c0117f76df999c8543bad255d06d26d4b3b57388252", 12963),
        "output": ("04f7910b122ded578975f379a7053b3dc62a0a5b73c2ea40505374500e665a0c", 15945),
        "pdf": ("b0d98861cbecba3e6807324ae928238b1db6ef62242df1f723b447e87e4dde65", 10194),
        "png": ("104bf76f03e0950d244c2b496adc7bafdc3c25e35cc80909e3636a281649d6b0", 16005),
        "trace": ("f177176dfb1b13bebbd96047e0813ecb15b56f2106575335dca88eb301471b39", 2964),
        "progress": ("fda424bdda3db8e0708f9902593d87c474d6e7db68a38fff6daf16411ce684dc", 5185),
        "text": "e90f2af9593f587921c00b8c9a4d1c3fed8ed2284bc5463a17d7f259478cdb91",
        "rows": 4, "columns": 3, "masters": 12, "payloads": 9,
        "inserted": 3, "deleted": 0, "cache_count": 15,
        "cache_sha256": "44d9a1d66c172f530f561438c38c67b6530bf994332fa4ccddd5c84982b434ad",
        "labels": ["R1C1", "R1C2", "R1C3", "", "", "", "R2C1", "R2C2", "R2C3", "R3C1", "R3C2", "R3C3"],
    },
    {
        "feature_id": "TABLE-013", "capability_id": "table.insert_columns",
        "stem": "table-013-insert-column-3x3",
        "input": ("69be89ead6a7582a80f4d98b17a87ac3908ba9e6e8d02e43e4ddcce3a615fa21", 12957),
        "output": ("1f9c5e40a164d59715547e22b858690504b3bb9895fb6a0e57d887842fe35add", 16139),
        "pdf": ("d47a771bf781a4e566055935c0242778aa96d1a6337a6fcfe0ebf8501b66d1e0", 10191),
        "png": ("245b74926a8cf754d4ba1c6dc4cfcfc1b9dcfcfa72d26bbcea88e0b6cb44381f", 15949),
        "trace": ("c99b1291119c713948ca92a1f2f6fc5b30324802216385da584ea97c95c32d44", 2964),
        "progress": ("780821bc388e1f8217d71e82f57c68bfad5c4f9fbc25b2680f5e10d580d26e7c", 5164),
        "text": "c25909bc7d17398e37fff3b4a022406d8b483035e6c27b4e4b00c42774aa3d77",
        "rows": 3, "columns": 4, "masters": 12, "payloads": 9,
        "inserted": 3, "deleted": 0, "cache_count": 15,
        "cache_sha256": "23eb6840733c3b4c748f9192ee54b9ffb88f04c85ab2eff182bb9657f347adda",
        "labels": ["R1C1", "", "R1C2", "R1C3", "R2C1", "", "R2C2", "R2C3", "R3C1", "", "R3C2", "R3C3"],
    },
    {
        "feature_id": "TABLE-014", "capability_id": "table.delete_rows",
        "stem": "table-014-delete-row-3x3",
        "input": ("abc5fd06b5f17dbbb201630b3a38a1e77bd65830f50062a7fd468cdfdb0edcea", 12883),
        "output": ("c449bb856589c78a7c80b93bc700e407cff85f3744dd266787bcf03a3fa3b0fe", 14675),
        "pdf": ("251b7d63b4379120d9e6263232e242cb9300ba70d7f299efbc6cb0e97c18b1a7", 10063),
        "png": ("30334c371715c9ee36bcb0d3b7f30b6aa93f4a26df1ab8d06a7ca03b0d938e7e", 13293),
        "trace": ("c20112d499ac0e4bfd776bc45d62033aec5d00c27b75fcaaea62571c18c28e50", 2964),
        "progress": ("8c89baa9c5f62e314c211d19dc899e9009b69f159f3e0329a9bc45d73a930ef5", 5185),
        "text": "c7b6d785a304e34c355cb6f1876575425d0f8a788bb24f2cc1ded11ba979c82f",
        "rows": 2, "columns": 3, "masters": 6, "payloads": 6,
        "inserted": 0, "deleted": 3, "cache_count": 9,
        "cache_sha256": "a5491d59a064546751144e7d9df920737505cc0698e0838acb59968aa2dd05a4",
        "labels": ["R1C1", "R1C2", "R1C3", "R3C1", "R3C2", "R3C3"],
    },
    {
        "feature_id": "TABLE-015", "capability_id": "table.delete_columns",
        "stem": "table-015-delete-column-3x3",
        "input": ("5c6669b0682f94682b3fc132cf4fc101d444cc93b7284ffb1fee0ef68ab6bb0e", 12882),
        "output": ("bd0ffb108bf35289c742bd400a74d3d95f0a69574f3279c3b363f8475a38dce1", 15157),
        "pdf": ("e4523772fb08d1f3b6edee41e6643df2564a49455bbaacd1307340dc2c09ca96", 10055),
        "png": ("dddccf97f58cd0328753a2b41a3071daac539beeb33e4293a9a39039cf5b4d10", 15053),
        "trace": ("a00aa097c876480cb8db03447f2f0213d8740d42af1aeb5cd7c975b2714ba7a0", 2964),
        "progress": ("791bd11f391d134338497a7884ecda99b1e082f894086448d5a45393994c9ef5", 5185),
        "text": "28ae2b17f7bf4fff595b325b5270ba68b09cd126fa9e31922b79bc9b673e4d93",
        "rows": 3, "columns": 2, "masters": 6, "payloads": 6,
        "inserted": 0, "deleted": 3, "cache_count": 9,
        "cache_sha256": "71928c8f51a481142c90e09243c511df8206180c297dfd656725653c13b7d927",
        "labels": ["R1C1", "R1C3", "R2C1", "R2C3", "R3C1", "R3C3"],
    },
]

EVIDENCE = {
    MANIFEST: ("4f02027b798d0c8e3c805ac9be766280421b30a941ed2fc49cfede16b1f4fa09", 12854),
    RECEIPT: ("f97a32bff69514eae0365dcf5dc2e88146a56129d5c1aa1bf8d6bb6b4dd5023b", 11317),
}
for item in CASE_INFO:
    prefix = f"{TARGET_DIRECTORY}/{item['stem']}"
    EVIDENCE[f"{prefix}.hwpx"] = item["input"]
    EVIDENCE[f"{prefix}.hancom-2020-readback.hwpx"] = item["output"]
    EVIDENCE[f"{prefix}.hancom-2020-render.pdf"] = item["pdf"]
    EVIDENCE[f"{prefix}.hancom-2020-render.png"] = item["png"]
    EVIDENCE[f"{prefix}.hancom-2020-trace.json"] = item["trace"]
    EVIDENCE[f"{prefix}.hancom-2020-trace.json.progress.jsonl"] = item["progress"]

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
FEATURES = {item["feature_id"]: item["capability_id"] for item in CASE_INFO}
TARGET = {
    "product": "Hancom Hangul 2020", "prog_id": "HWPFrame.HwpObject.2",
    "registry_view": "Registry32", "client": "windows_powershell_x86_sta",
    "build": "11.0.0.9136", "architecture": "x86", "locale": "ko-KR",
    "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce",
}
TYPED_ORACLE = {
    "state": "pass", "one_table_each": True, "source_dimensions": [3, 3],
    "target_dimensions": [[4, 3], [3, 4], [2, 3], [3, 2]],
    "inserted_empty_cells_each": 3, "preserved_payload_blocks": [9, 9, 6, 6],
    "formula_count_each": 0, "page_split": "cell", "repeat_header_rows": 0,
    "caption": False, "section_equal_after_exact_renderer_cache_strip": True,
    "native_empty_cell_run_admitted": True,
}
RENDER_ORACLE = {
    "state": "pass", "pages_each": 1, "page_size_points": [595, 841],
    "dpi": 144, "pixel_size": [1190, 1682], "inserted_bands_visibly_empty": True,
    "deleted_labels_absent": True, "all_expected_labels_visible": True,
    "clipping": False, "overlap": False, "blank_pages": False, "black_boxes": False,
}
GATE = {
    **{feature_id: "oracle_verified" for feature_id in FEATURES},
    "actual_hancom_2020_save_reopen": "pass", "target_build": "pass",
    "render_diff": "pass", "rollback_or_retry": "pass",
    "automation_runtime": "not_run", "differential": "not_run",
    "p06_09": "in_progress", "p06": "in_progress",
}
NOT_CLAIMED = {
    "formula_bearing_structure": False, "repeat_header_structure": False,
    "caption_structure": False, "automation_runtime": False,
    "differential_exact_match": False, "arbitrary_user_document_compatibility": False,
    "other_pc_or_hancom_version": False, "p06_09_complete": False,
    "p06_phase_complete": False, "production": False, "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    REPORT: ("TABLE-012", "TABLE-015", "self-closing", "completion remain unclaimed"),
    MIGRATION: ("additive evidence admission", "no automatic migration", "fail closed", "may not promote"),
    RECEIPT: ("p06.table-structure.current-2020.attempt01.20260913", "native_empty_cell_run_admitted", "product_complete"),
    "crates/hwpx-package/src/table_ruling_hwpx.rs": ("uses_native_empty_cell_run", "fn empty_cell_paragraph()", "fn native_empty_cell_paragraph()", 'pageBreak="0" columnBreak="0" merged="0"'),
    "crates/hwpx-package/src/table_ruling_hwpx/structure_hwpx.rs": ("preserved_payload_block_count: plan.domain.after_state().cells()", ".checked_add(cell.payload().len())", "TableStructureHwpxError::OutputLimit"),
    "crates/hwpx-package/tests/table_structure_hwpx.rs": ("all_four_structural_operations_lower_and_reopen_exactly", "lowered.receipt.preserved_payload_block_count", "9", "6"),
    "crates/hwpx-package/examples/p06_09_table_structure_target_fixture.rs": ("TABLE-012", "TABLE-015", "exact table-structure ancestor identity differs", "output directory already exists"),
    "crates/hwpx-package/examples/p06_09_table_structure_target_oracle.rs": ("renderer-cache boundary differs", "actual Hangul typed structure state differs", "oracle paths must be distinct"),
}


def add_error(errors: list[str], value: str) -> None:
    if value not in errors:
        errors.append(value)


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def bounded_bytes(root: Path, relative: str, maximum: int = 8 * 1024 * 1024) -> bytes:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != relative:
        raise ValueError("unsafe path")
    path = root.joinpath(*pure.parts)
    resolved_root = root.resolve()
    resolved = path.resolve(strict=True)
    if resolved_root != resolved and resolved_root not in resolved.parents:
        raise ValueError("path escape")
    if path.is_symlink() or not path.is_file():
        raise ValueError("not regular file")
    data = path.read_bytes()
    if not data or len(data) > maximum:
        raise ValueError("file bound")
    return data


def load_json(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)


def canonical_sha256(data: bytes) -> str:
    text = data.decode("utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def expected_validation_tree() -> list[str]:
    paths = set(SOURCE_LOCKS) | set(EVIDENCE) | set(IMPLEMENTATION_MARKERS)
    paths.update({CONTRACT, REPORT, MIGRATION, RECEIPT})
    paths.update(predecessor.EXPECTED_SOURCE_PATHS)
    paths.update(predecessor.IMPLEMENTATION_MARKERS)
    paths.update({predecessor.CONTRACT, predecessor.MIGRATION, predecessor.POLICY, predecessor.REPORT})
    return sorted(paths)


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json(bounded_bytes(root, CONTRACT, 512_000))
        if not isinstance(contract, dict):
            raise ValueError("contract object")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0, "not_proven")
    predecessor_state = predecessor.validate(root).get("state", "fail")
    if predecessor_state != "pass":
        add_error(errors, "predecessor_validation")
    validate_identity(contract, errors)
    source_locks = validate_source_locks(root, contract.get("source_locks"), errors)
    evidence_files = validate_evidence(root, errors)
    validate_contract_claims(contract, errors)
    validate_manifest_and_receipt(root, errors)
    validate_hwpx(root, errors)
    validate_traces_and_progress(root, errors)
    validate_pdfs(root, errors)
    implementation_files = validate_markers(root, errors)
    return result(errors, source_locks, evidence_files, implementation_files, predecessor_state)


def validate_identity(contract: dict[str, Any], errors: list[str]) -> None:
    expected_predecessors = [{
        "path": predecessor.CONTRACT,
        "sha256": SOURCE_LOCKS[predecessor.CONTRACT],
        "state": "TABLE-012 TABLE-013 TABLE-014 TABLE-015 direct_hwpx integration_passed",
    }]
    if contract.get("schema_version") != "hwpx-agent.p06-09-table-structure-target-contract/v2" \
            or contract.get("scope") != "TABLE-012 TABLE-013 TABLE-014 TABLE-015 exact current-PC Hangul 2020 combined structural batch oracle" \
            or contract.get("predecessors") != expected_predecessors \
            or contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256" \
            or contract.get("features") != FEATURES:
        add_error(errors, "contract_identity")


def validate_source_locks(root: Path, value: Any, errors: list[str]) -> int:
    if not isinstance(value, list):
        add_error(errors, "source_locks_exact")
        return 0
    declared: dict[str, str] = {}
    for entry in value:
        try:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                raise ValueError("shape")
            path, digest = entry["path"], entry["sha256"]
            if not isinstance(path, str) or not isinstance(digest, str) or path in declared:
                raise ValueError("identity")
            declared[path] = digest
            if canonical_sha256(bounded_bytes(root, path, 4 * 1024 * 1024)) != digest:
                add_error(errors, "source_lock_digest")
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "source_lock_path_or_encoding")
    if declared != SOURCE_LOCKS:
        add_error(errors, "source_locks_exact")
    return len(declared)


def validate_evidence(root: Path, errors: list[str]) -> int:
    for path, (digest, size) in EVIDENCE.items():
        try:
            data = bounded_bytes(root, path, 32 * 1024 * 1024)
            if len(data) != size or sha256(data) != digest:
                add_error(errors, "evidence_digest")
        except (OSError, ValueError):
            add_error(errors, "evidence_path_or_bound")
    return len(EVIDENCE)


def validate_contract_claims(contract: dict[str, Any], errors: list[str]) -> None:
    attempt = contract.get("successful_attempt", {})
    if contract.get("exact_target") != TARGET \
            or attempt.get("id") != "20260913-05" \
            or attempt.get("directory") != TARGET_DIRECTORY \
            or attempt.get("state") != "pass" \
            or attempt.get("manifest") != {"path": MANIFEST, "sha256": EVIDENCE[MANIFEST][0], "bytes": EVIDENCE[MANIFEST][1]} \
            or attempt.get("receipt") != {"path": RECEIPT, "sha256": EVIDENCE[RECEIPT][0], "bytes": EVIDENCE[RECEIPT][1]}:
        add_error(errors, "successful_attempt")
    if contract.get("typed_oracle") != TYPED_ORACLE:
        add_error(errors, "typed_oracle")
    if contract.get("render_oracle") != RENDER_ORACLE:
        add_error(errors, "render_oracle")
    if contract.get("retry_oracle") != {"state": "pass", "independent_builds": 2, "byte_deterministic": True, "existing_destination_rejected_without_overwrite": True}:
        add_error(errors, "retry_oracle")
    if contract.get("gate_decision") != GATE:
        add_error(errors, "gate_decision")
    if contract.get("not_claimed") != NOT_CLAIMED:
        add_error(errors, "not_claimed")
    if contract.get("migration") != MIGRATION or contract.get("report") != REPORT \
            or contract.get("evidence_receipt") != RECEIPT \
            or not isinstance(contract.get("failure_policy"), list) \
            or len(contract["failure_policy"]) != 5:
        add_error(errors, "contract_references_or_failure_policy")


def validate_manifest_and_receipt(root: Path, errors: list[str]) -> None:
    try:
        manifest = load_json(bounded_bytes(root, MANIFEST, 256_000))
        receipt = load_json(bounded_bytes(root, RECEIPT, 256_000))
        if manifest.get("schema_version") != "hwpx-agent.p06-09-table-structure-target-fixture/v1" \
                or manifest.get("source_ancestor_sha256") != receipt["source"]["ancestor_sha256"] \
                or manifest.get("prepared_source_section_sha256") != receipt["source"]["prepared_source_section_sha256"] \
                or len(manifest.get("cases", [])) != 4 \
                or manifest.get("actual_hangul_2020") is not False \
                or any(manifest.get(key) != "not_run" for key in ("render", "automation", "differential")):
            raise ValueError("manifest")
        if receipt.get("schema_version") != "hwpx-agent.p06-09-table-structure-target-evidence/v2" \
                or receipt.get("attempt_id") != "p06.table-structure.current-2020.attempt01.20260913" \
                or receipt["batch"]["manifest"] != {"path": MANIFEST, "sha256": EVIDENCE[MANIFEST][0], "bytes": EVIDENCE[MANIFEST][1]} \
                or receipt.get("typed_oracle") != TYPED_ORACLE \
                or receipt.get("render_oracle") != RENDER_ORACLE \
                or receipt.get("gate_decision") != GATE \
                or receipt.get("not_claimed") != NOT_CLAIMED \
                or receipt.get("privacy") != {"raw_document_text_present": False, "user_document_scanned": False, "external_network_invoked": False, "registry_or_system_setting_changed": False, "computer_use_click_or_type_invoked": False}:
            raise ValueError("receipt")
        for case, evidence_case, item in zip(manifest["cases"], receipt["cases"], CASE_INFO, strict=True):
            if case["feature_id"] != item["feature_id"] \
                    or case["capability_id"] != item["capability_id"] \
                    or case["sha256"] != item["input"][0] \
                    or case["rows"] != item["rows"] or case["columns"] != item["columns"] \
                    or case["master_cell_count"] != item["masters"] \
                    or case["payload_block_count"] != item["payloads"] \
                    or case["inserted_master_cell_count"] != item["inserted"] \
                    or case["deleted_master_cell_count"] != item["deleted"] \
                    or len(case["binding"]["cells"]) != item["masters"] \
                    or evidence_case["feature_id"] != item["feature_id"] \
                    or evidence_case["rows"] != item["rows"] \
                    or evidence_case["columns"] != item["columns"] \
                    or evidence_case["payload_blocks"] != item["payloads"] \
                    or evidence_case["renderer_cache_count"] != item["cache_count"] \
                    or evidence_case["renderer_cache_sha256"] != item["cache_sha256"] \
                    or evidence_case["input_text_sha256"] != item["text"] \
                    or evidence_case["output_text_sha256"] != item["text"]:
                raise ValueError(item["feature_id"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        add_error(errors, "manifest_or_receipt_semantics")


def read_zip_parts(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        if len(archive.infolist()) != len(set(archive.namelist())):
            raise ValueError("duplicate zip part")
        return {name: archive.read(name) for name in archive.namelist()}


def cell_text(cell: ET.Element, namespace: dict[str, str]) -> str:
    return "".join(value.text or "" for value in cell.findall(".//hp:t", namespace))


def validate_empty_native_cell(cell: ET.Element, namespace: dict[str, str]) -> None:
    paragraphs = cell.findall(".//hp:p", namespace)
    if len(paragraphs) != 1:
        raise ValueError("empty cell paragraph count")
    paragraph = paragraphs[0]
    if any(paragraph.attrib.get(key) != "0" for key in ("pageBreak", "columnBreak", "merged")):
        raise ValueError("empty cell paragraph flags")
    runs = paragraph.findall("./hp:run", namespace)
    if len(runs) != 1 or list(paragraph) != runs or runs[0].attrib.get("charPrIDRef") != "0" \
            or list(runs[0]):
        raise ValueError("empty cell run")


def validate_hwpx(root: Path, errors: list[str]) -> None:
    namespace = {"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}
    try:
        for item in CASE_INFO:
            prefix = f"{TARGET_DIRECTORY}/{item['stem']}"
            target = read_zip_parts(bounded_bytes(root, f"{prefix}.hwpx"))
            output = read_zip_parts(bounded_bytes(root, f"{prefix}.hancom-2020-readback.hwpx"))
            if set(target) != EXPECTED_PARTS or set(output) != EXPECTED_PARTS \
                    or any(target[path] != output[path] for path in IMMUTABLE_PARTS):
                raise ValueError("package boundary")
            target_section = target["Contents/section0.xml"]
            output_section = output["Contents/section0.xml"]
            caches = re.findall(rb"<hp:linesegarray>.*?</hp:linesegarray>", output_section, re.DOTALL)
            stripped = re.sub(rb"<hp:linesegarray>.*?</hp:linesegarray>", b"", output_section, flags=re.DOTALL)
            if len(caches) != item["cache_count"] or sha256(b"".join(caches)) != item["cache_sha256"] \
                    or stripped != target_section:
                raise ValueError("renderer cache")
            section = ET.fromstring(target_section)
            tables = section.findall(".//hp:tbl", namespace)
            if len(tables) != 1:
                raise ValueError("table count")
            table = tables[0]
            cells = table.findall("./hp:tr/hp:tc", namespace)
            labels = [cell_text(cell, namespace) for cell in cells]
            if int(table.attrib["rowCnt"]) != item["rows"] \
                    or int(table.attrib["colCnt"]) != item["columns"] \
                    or len(cells) != item["masters"] \
                    or labels != item["labels"] \
                    or labels.count("") != item["inserted"] \
                    or table.attrib.get("repeatHeader") != "0" \
                    or table.attrib.get("pageBreak") != "CELL" \
                    or target_section.count(b"<hp:fieldBegin") != 0:
                raise ValueError("table semantics")
            for cell, label in zip(cells, labels, strict=True):
                if not label:
                    validate_empty_native_cell(cell, namespace)
    except (OSError, KeyError, TypeError, ValueError, ET.ParseError, zipfile.BadZipFile):
        add_error(errors, "target_oracle_hwpx_semantics")


def validate_traces_and_progress(root: Path, errors: list[str]) -> None:
    expected_phases = {"com_create", "open_input", "read_input", "save_as_hwpx", "close_input", "reopen_output", "read_output", "export_pdf", "close_output", "quit"}
    try:
        for item in CASE_INFO:
            prefix = f"{TARGET_DIRECTORY}/{item['stem']}"
            trace = load_json(bounded_bytes(root, f"{prefix}.hancom-2020-trace.json", 256_000))
            watchdog = trace["watchdog"]
            if trace["state"] != "pass" or trace["target"]["prog_id"] != TARGET["prog_id"] \
                    or trace["target"]["registry_view"] != TARGET["registry_view"] \
                    or trace["target"]["file_version"] != TARGET["build"] \
                    or trace["target"]["executable_sha256"] != TARGET["executable_sha256"] \
                    or trace["input_sha256"] != item["input"][0] \
                    or trace["output_sha256"] != item["output"][0] \
                    or trace["input_text_sha256"] != item["text"] \
                    or trace["output_text_sha256"] != item["text"] \
                    or set(trace["phases"]) != expected_phases \
                    or set(trace["phases"].values()) != {"pass"} \
                    or trace["input_unchanged"] is not True or trace["output_saved"] is not True \
                    or trace["render_pdf_saved"] is not True \
                    or trace["render_pdf_sha256"] != item["pdf"][0] \
                    or trace["error_code"] is not None or trace["failed_phase"] is not None \
                    or any(trace[key] is not False for key in ("raw_document_text_present", "user_document_scanned", "external_network_invoked", "registry_or_system_setting_changed", "computer_use_click_or_type_invoked")) \
                    or watchdog["timed_out"] is not False \
                    or watchdog["remaining_hwp_process_count"] != 0 \
                    or watchdog["progress_event_count"] != 21 \
                    or watchdog["progress_last_phase"] != "terminal" \
                    or watchdog["progress_last_state"] != "pass":
                raise ValueError("trace")
            lines = bounded_bytes(root, f"{prefix}.hancom-2020-trace.json.progress.jsonl", 256_000).decode("utf-8").splitlines()
            events = [load_json(line.encode("utf-8")) for line in lines]
            if len(events) != 21 or [event["sequence"] for event in events] != list(range(1, 22)) \
                    or events[-1]["phase"] != "terminal" or events[-1]["state"] != "pass" \
                    or any(event["raw_document_text_present"] is not False for event in events):
                raise ValueError("progress")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        add_error(errors, "trace_or_progress_semantics")


def validate_pdfs(root: Path, errors: list[str]) -> None:
    try:
        for item in CASE_INFO:
            data = bounded_bytes(root, f"{TARGET_DIRECTORY}/{item['stem']}.hancom-2020-render.pdf", 32 * 1024 * 1024)
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
    output = {
        "schema_version": "hwpx-agent.p06-09-table-structure-target-validation/v2",
        "state": state, "errors": unique, "source_locks": source_locks,
        "evidence_files": evidence_files, "implementation_files": implementation_files,
        "predecessor": predecessor_state, "p06_09": "in_progress", "p06": "in_progress",
        "product_complete": False,
    }
    output.update({feature_id: "oracle_verified" if state == "pass" else "not_proven" for feature_id in FEATURES})
    return output


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_STRUCTURE_TARGET_V2_CONTRACT_PASS "
        f"features=4 source_locks={validation['source_locks']} "
        f"evidence_files={validation['evidence_files']}"
    )
