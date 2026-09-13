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
    from tools.p06 import validate_table_join_hwpx_contract as join_predecessor
    from tools.p06 import validate_table_partition_contract as component_predecessor
    from tools.p06 import validate_table_split_hwpx_contract as split_predecessor
except ModuleNotFoundError:
    import validate_table_join_hwpx_contract as join_predecessor
    import validate_table_partition_contract as component_predecessor
    import validate_table_split_hwpx_contract as split_predecessor


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-partition-target-v2.json"
REPORT = "implementation/p06/P06-09_TABLE_PARTITION_TARGET_READBACK_REPORT.md"
MIGRATION = "protocol/migrations/p06-table-partition-v1-to-target-v2.md"
RECEIPT = "implementation/p06/evidence/target/p06-table-partition.current-2020.attempt01.v2.json"
TARGET_DIRECTORY = "fixtures/target-build/p06-09-table-partition-target-20260913-15"
MANIFEST = f"{TARGET_DIRECTORY}/fixture-manifest.json"

SOURCE_LOCKS = {
    "protocol/private/p06-table-partition-v1.json": "871ef74f7c10cb34b805becda60f53f497a0e1cef2e7031cb647007561ae9334",
    "tools/p06/validate_table_partition_contract.py": "d14459201ed9ceb7d986fb9a70d10cb1e12a6b74a453655d8242c5cabc950b7a",
    "protocol/private/p06-table-split-hwpx-v1.json": "66d8f071ef9fced3c74475bd5f0646a864d616d210a749f38156bacde6a83e13",
    "tools/p06/validate_table_split_hwpx_contract.py": "1f999b19d9dfa15a37b400a07014369f66e77589e182bddbb0c8e201ac595b94",
    "protocol/private/p06-table-join-hwpx-v1.json": "856a2c87f6fa8244ef4d1f436801926b685cef5fb1f2a9ebe00f29e7137520b8",
    "tools/p06/validate_table_join_hwpx_contract.py": "77c55992480592d8df735a44b5740041ca5c8343dd414d442b1f524eaba49715",
    "crates/hwpx-package/src/table_ruling_hwpx/partition_hwpx.rs": "549299909e171f00879192dbe8efbc04bdd42aa28ba7626c88f0dc81541e9bc3",
    "crates/hwpx-package/tests/table_split_hwpx.rs": "46e05d432f3ed04335b3307334f7809d7177fc7578fce9c666741fef8a294346",
    "crates/hwpx-package/tests/table_join_hwpx.rs": "14f98e2f382329495640b8072f67bb80e7d26e750f002bc4865cd1e20283c93c",
    "crates/hwpx-package/examples/p06_09_table_partition_target_fixture.rs": "781a8b4c562a1b8c328533ccd4d9c1e29dabb01c521628fb7f2cfb817c3a18a3",
    "crates/hwpx-package/examples/p06_09_table_partition_target_oracle.rs": "e1929ff23ce80a426702df9d1f62d7a9401a71f04ed07d8a1064e77ce54828bd",
    "implementation/p06/tools/run-hancom-2020-table-properties-target-readback.ps1": "3da056958e4dac341700278a158d174bbe5eb1ceff3f39dd637939264d93b6a8",
    "implementation/p06/tests/Test-Hancom2020TablePropertiesTargetReadback.ps1": "82ed78af052dab81a8963411e04b0bed447aa3547128aee253c7efd81afacf96",
}

CASE_INFO = [
    {
        "feature_id": "TABLE-010",
        "capability_id": "table.split_table",
        "stem": "table-010-split-table-4x2",
        "input": ("8bab0736c9deb47fa577a68b40223087efcbee3560c700dc97456f777c83e9c3", 12915),
        "output": ("7229ccccd1bfb98dfa3d6a57f4575033718d3644c785103407d8e17795d8db67", 15908),
        "pdf": ("ec966fa38585ccdeeb23733f7f6e7c15348c7a0f9cc432e78fcedeabbab75c05", 10318),
        "png": ("0580fb50f77521dedd2078806f5bcf8db5a948cf216db65be1706ec6309acd1b", 17137),
        "trace": ("b04163b74f4252f79a7eaeea3263e5d47b24f97779d963ea671bb6a565b728d4", 2329),
        "progress": ("ae25f39feb7f3b2a22006ae3134622e5b54b3a4a5d9cd0a2fe5d99308ef303e7", 5185),
        "text": "deebb8102dbd1f48f6dce43d221218870043e599803f3555a8ef888432420cc3",
        "tables": 2,
        "rows": [2, 2],
        "columns": [2, 2],
        "cache_count": 13,
        "cache_sha256": "6c2aed93776177cfcd1b8935b2417f84c51bce0088d0ebcc8be24171759bbcc2",
    },
    {
        "feature_id": "TABLE-011",
        "capability_id": "table.join_table",
        "stem": "table-011-join-table-4x2",
        "input": ("a5a7a475d33fc82c729c2a39b028925a4bb4d528161f36c040d4d3c6204eeecb", 12914),
        "output": ("28fddc01a7d224f4d79b15e960483a7c754c2acbde518505148364b75c086c95", 15839),
        "pdf": ("5bd2fc0127cdb3f0da3530f0851410d62f7ecd640daee136d8264843f3ff4c0a", 10268),
        "png": ("5cfcd16d55baae0b0e42a496f5ba8da55407041003fa05689d16f38561120152", 17098),
        "trace": ("c7cf72a03c2c806b17a937181a72d3e2b3647692536118aa9f5082a441bc53d6", 2329),
        "progress": ("fe30c7efc8b8aa878ec50728236682dea5600264aaa423e2d24ff9fe47971ea3", 5185),
        "text": "b5ba4ed86fee97bc455cc50a5485937c7dbc6e7a1eb9bdb22c6078cedf7ab17c",
        "tables": 1,
        "rows": [4],
        "columns": [2],
        "cache_count": 11,
        "cache_sha256": "683f76ab4736256762f04ca371ac0206431d3f496e17b607b2daefa20358d516",
    },
]

EVIDENCE = {
    MANIFEST: ("f7c25806e82e2f809d6d6dfde0fc2620493a5cf237fbb9913c9782713db33c25", 7018),
    RECEIPT: ("3046dd4255c7ad4759bbd510d3661d3a6839a54bdb0322b8976671d546468bb1", 6898),
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
IMPLEMENTATION_MARKERS = {
    REPORT: ("TABLE-010", "TABLE-011", "native empty-run separator", "completion remain unclaimed"),
    MIGRATION: ("additive evidence admission", "no automatic migration", "fail closed", "may not promote"),
    RECEIPT: ("p06.table-partition.current-2020.attempt01.20260913", "split_join_state_chain_exact", "product_complete"),
    "crates/hwpx-package/src/table_ruling_hwpx/partition_hwpx.rs": ("character_property_id", "return Ok(0)", "UnsupportedSeparator"),
    "crates/hwpx-package/tests/table_split_hwpx.rs": ("</hp:tbl><hp:t/></hp:run></hp:p>", "charPrIDRef=\"0\"/>",),
    "crates/hwpx-package/tests/table_join_hwpx.rs": ("native_empty_run", "TableJoinSeparatorToken::ParagraphBreak"),
    "crates/hwpx-package/examples/p06_09_table_partition_target_fixture.rs": ("TABLE-010 split receipt differs", "TABLE-011 join receipt or roundtrip state differs"),
    "crates/hwpx-package/examples/p06_09_table_partition_target_oracle.rs": ("renderer-cache boundary differs", "actual Hangul typed partition state differs"),
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
    paths = set(SOURCE_LOCKS) | set(EVIDENCE) | set(IMPLEMENTATION_MARKERS) | {
        CONTRACT, REPORT, MIGRATION, RECEIPT,
        component_predecessor.CONTRACT, split_predecessor.CONTRACT, join_predecessor.CONTRACT,
    }
    paths.update(component_predecessor.IMPLEMENTATION_MARKERS)
    paths.update(split_predecessor.IMPLEMENTATION_MARKERS)
    paths.update(join_predecessor.IMPLEMENTATION_MARKERS)
    paths.add(component_predecessor.MIGRATION)
    paths.add(split_predecessor.MIGRATION)
    paths.add(join_predecessor.MIGRATION)
    return sorted(paths)


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = load_json(bounded_bytes(root, CONTRACT, 512_000))
        if not isinstance(contract, dict):
            raise ValueError("contract object")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return result(["contract_json_or_path"], 0, 0, 0, "not_proven")
    predecessor_states = {
        "component": component_predecessor.validate(root).get("state"),
        "split": split_predecessor.validate(root).get("state"),
        "join": join_predecessor.validate(root).get("state"),
    }
    predecessor_state = "pass" if set(predecessor_states.values()) == {"pass"} else "fail"
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
    expected_predecessors = [
        {"path": "protocol/private/p06-table-partition-v1.json", "sha256": SOURCE_LOCKS["protocol/private/p06-table-partition-v1.json"], "state": "TABLE-010 TABLE-011 component unit_passed"},
        {"path": "protocol/private/p06-table-split-hwpx-v1.json", "sha256": SOURCE_LOCKS["protocol/private/p06-table-split-hwpx-v1.json"], "state": "TABLE-010 direct_hwpx integration_passed"},
        {"path": "protocol/private/p06-table-join-hwpx-v1.json", "sha256": SOURCE_LOCKS["protocol/private/p06-table-join-hwpx-v1.json"], "state": "TABLE-011 direct_hwpx integration_passed"},
    ]
    if contract.get("schema_version") != "hwpx-agent.p06-09-table-partition-target-contract/v2" \
            or contract.get("scope") != "TABLE-010 TABLE-011 exact current-PC Hangul 2020 chained split-join batch oracle" \
            or contract.get("predecessors") != expected_predecessors \
            or contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256" \
            or contract.get("features") != {"TABLE-010": "table.split_table", "TABLE-011": "table.join_table"}:
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
    target = {"product": "Hancom Hangul 2020", "prog_id": "HWPFrame.HwpObject.2", "registry_view": "Registry32", "client": "windows_powershell_x86_sta", "build": "11.0.0.9136", "architecture": "x86", "locale": "ko-KR", "executable_sha256": "7f00961398802c41620f5ef32fa2d2a26f7ff71f172723be36c660ea86a72bce"}
    attempt = contract.get("successful_attempt", {})
    receipt = attempt.get("receipt", {}) if isinstance(attempt, dict) else {}
    manifest = attempt.get("manifest", {}) if isinstance(attempt, dict) else {}
    if contract.get("exact_target") != target \
            or attempt.get("id") != "20260913-15" \
            or attempt.get("directory") != TARGET_DIRECTORY \
            or attempt.get("state") != "pass" \
            or manifest != {"path": MANIFEST, "sha256": EVIDENCE[MANIFEST][0], "bytes": EVIDENCE[MANIFEST][1]} \
            or receipt != {"path": RECEIPT, "sha256": EVIDENCE[RECEIPT][0], "bytes": EVIDENCE[RECEIPT][1]}:
        add_error(errors, "successful_attempt")
    typed = contract.get("typed_oracle", {})
    render = contract.get("render_oracle", {})
    retry = contract.get("retry_oracle", {})
    gate = contract.get("gate_decision", {})
    not_claimed = contract.get("not_claimed", {})
    if typed.get("state") != "pass" or typed.get("split_tables") != 2 \
            or typed.get("join_tables") != 1 or typed.get("master_cells_each") != 8 \
            or typed.get("payload_blocks_each") != 8 or typed.get("formula_count_each") != 0 \
            or typed.get("page_split") != "cell" \
            or typed.get("section_equal_after_exact_renderer_cache_strip") is not True \
            or typed.get("split_join_state_chain_exact") is not True \
            or typed.get("native_empty_separator_run_admitted") is not True:
        add_error(errors, "typed_oracle")
    if render.get("state") != "pass" or render.get("pages_each") != 1 \
            or render.get("split_tables_visible") != 2 or render.get("joined_tables_visible") != 1 \
            or render.get("all_values_visible") is not True \
            or any(render.get(key) is not False for key in ("clipping", "overlap", "blank_pages", "black_boxes")):
        add_error(errors, "render_oracle")
    if retry != {"state": "pass", "independent_builds": 2, "byte_deterministic": True, "existing_destination_rejected_without_overwrite": True}:
        add_error(errors, "retry_oracle")
    expected_gate = {"TABLE-010": "oracle_verified", "TABLE-011": "oracle_verified", "actual_hancom_2020_save_reopen": "pass", "target_build": "pass", "render_diff": "pass", "rollback_or_retry": "pass", "automation_runtime": "not_run", "differential": "not_run", "p06_09": "in_progress", "p06": "in_progress"}
    if gate != expected_gate:
        add_error(errors, "gate_decision")
    if not isinstance(not_claimed, dict) or set(not_claimed.values()) != {False} \
            or not_claimed.get("product_complete") is not False:
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
        if manifest.get("schema_version") != "hwpx-agent.p06-09-table-partition-target-fixture/v1" \
                or manifest.get("source_ancestor_sha256") != receipt["source"]["ancestor_sha256"] \
                or manifest.get("prepared_source_section_sha256") != receipt["source"]["prepared_source_section_sha256"] \
                or len(manifest.get("cases", [])) != 2 \
                or manifest.get("actual_hangul_2020") is not False \
                or manifest.get("render") != "not_run":
            raise ValueError("manifest")
        if receipt.get("schema_version") != "hwpx-agent.p06-09-table-partition-target-evidence/v2" \
                or receipt.get("attempt_id") != "p06.table-partition.current-2020.attempt01.20260913" \
                or receipt["batch"]["manifest"] != {"path": MANIFEST, "sha256": EVIDENCE[MANIFEST][0], "bytes": EVIDENCE[MANIFEST][1]} \
                or receipt["typed_oracle"]["state"] != "pass" \
                or receipt["render_oracle"]["state"] != "pass" \
                or receipt["privacy"] != {"raw_document_text_present": False, "user_document_scanned": False, "external_network_invoked": False, "registry_or_system_setting_changed": False, "computer_use_click_or_type_invoked": False} \
                or set(receipt["not_claimed"].values()) != {False}:
            raise ValueError("receipt")
        for index, (case, evidence_case, item) in enumerate(zip(manifest["cases"], receipt["cases"], CASE_INFO)):
            if case["feature_id"] != item["feature_id"] or case["capability_id"] != item["capability_id"] \
                    or case["sha256"] != item["input"][0] or case["table_count"] != item["tables"] \
                    or case["rows_per_table"] != item["rows"] or case["columns_per_table"] != item["columns"] \
                    or case["master_cell_count"] != 8 or case["payload_block_count"] != 8 \
                    or len(case["bindings"]) != item["tables"] \
                    or evidence_case["feature_id"] != item["feature_id"] \
                    or evidence_case["renderer_cache_count"] != item["cache_count"] \
                    or evidence_case["renderer_cache_sha256"] != item["cache_sha256"] \
                    or evidence_case["input_text_sha256"] != item["text"] \
                    or evidence_case["output_text_sha256"] != item["text"]:
                raise ValueError(f"case {index}")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        add_error(errors, "manifest_or_receipt_semantics")


def read_zip_parts(data: bytes) -> dict[str, bytes]:
    from io import BytesIO
    with zipfile.ZipFile(BytesIO(data)) as archive:
        if len(archive.infolist()) != len(set(archive.namelist())):
            raise ValueError("duplicate zip part")
        return {name: archive.read(name) for name in archive.namelist()}


def validate_hwpx(root: Path, errors: list[str]) -> None:
    try:
        namespace = {"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}
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
            if len(caches) != item["cache_count"] \
                    or sha256(b"".join(caches)) != item["cache_sha256"] \
                    or stripped != target_section:
                raise ValueError("renderer cache")
            root_element = ET.fromstring(target_section)
            tables = root_element.findall(".//hp:tbl", namespace)
            if len(tables) != item["tables"]:
                raise ValueError("table count")
            observed_rows = [int(table.attrib["rowCnt"]) for table in tables]
            observed_columns = [int(table.attrib["colCnt"]) for table in tables]
            if observed_rows != item["rows"] or observed_columns != item["columns"] \
                    or sum(len(table.findall("./hp:tr/hp:tc", namespace)) for table in tables) != 8 \
                    or any(table.attrib.get("repeatHeader") != "0" or table.attrib.get("pageBreak") != "CELL" for table in tables) \
                    or target_section.count(b"<hp:fieldBegin") != 0 \
                    or target_section.count(b"</hp:tbl><hp:t/></hp:run></hp:p>") != item["tables"]:
                raise ValueError("table semantics")
            native_separator = re.findall(
                rb'<hp:p id="2002"[^>]*><hp:run charPrIDRef="0"/></hp:p>',
                target_section,
            )
            if item["feature_id"] == "TABLE-010" and len(native_separator) != 1:
                raise ValueError("native separator")
    except (OSError, KeyError, TypeError, ValueError, ET.ParseError, zipfile.BadZipFile):
        add_error(errors, "target_oracle_hwpx_semantics")


def validate_traces_and_progress(root: Path, errors: list[str]) -> None:
    expected_phases = {"com_create", "open_input", "read_input", "save_as_hwpx", "close_input", "reopen_output", "read_output", "export_pdf", "close_output", "quit"}
    try:
        for item in CASE_INFO:
            prefix = f"{TARGET_DIRECTORY}/{item['stem']}"
            trace = load_json(bounded_bytes(root, f"{prefix}.hancom-2020-trace.json", 256_000))
            watchdog = trace["watchdog"]
            if trace["state"] != "pass" or trace["input_sha256"] != item["input"][0] \
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
                    or watchdog["timed_out"] is not False or watchdog["remaining_hwp_process_count"] != 0 \
                    or watchdog["progress_event_count"] != 21 or watchdog["progress_last_phase"] != "terminal" \
                    or watchdog["progress_last_state"] != "pass":
                raise ValueError("trace")
            lines = bounded_bytes(root, f"{prefix}.hancom-2020-trace.json.progress.jsonl", 256_000).decode("utf-8").splitlines()
            events = [load_json(line.encode("utf-8")) for line in lines]
            if len(events) != 21 \
                    or [event["sequence"] for event in events] != list(range(1, 22)) \
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
    return {
        "schema_version": "hwpx-agent.p06-09-table-partition-target-validation/v2",
        "state": state,
        "errors": unique,
        "source_locks": source_locks,
        "evidence_files": evidence_files,
        "implementation_files": implementation_files,
        "predecessors": predecessor_state,
        "TABLE-010": "oracle_verified" if state == "pass" else "not_proven",
        "TABLE-011": "oracle_verified" if state == "pass" else "not_proven",
        "p06_09": "in_progress",
        "p06": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["state"] != "pass":
        raise SystemExit(1)
    print(
        "P06_TABLE_PARTITION_TARGET_V2_CONTRACT_PASS "
        f"features=2 source_locks={validation['source_locks']} "
        f"evidence_files={validation['evidence_files']}"
    )
