#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any
import xml.etree.ElementTree as ET
import zipfile

try:
    from tools.p06.validate_table_geometry_contract import (
        add_error,
        bounded_file,
        canonical_sha256,
        reject_duplicate_keys,
    )
except ModuleNotFoundError:
    from validate_table_geometry_contract import (  # type: ignore[no-redef]
        add_error,
        bounded_file,
        canonical_sha256,
        reject_duplicate_keys,
    )


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = "protocol/private/p06-table-chart-hwpx-v1.json"
PREDECESSOR = "protocol/private/p06-table-chart-v1.json"
MIGRATION = "protocol/migrations/p06-table-chart-v1-to-hwpx-v1.md"
POLICY = "implementation/p06/P06-09_TABLE_CHART_HWPX_POLICY.md"
REPORT = "implementation/p06/P06-09_TABLE_CHART_HWPX_REPORT.md"
RECEIPT = (
    "implementation/p06/evidence/target/"
    "p06-table-chart.current-2020.attempt01.v1.json"
)
DIRECT_EVIDENCE = "implementation/p06/p06-09-current-2020-direct-evidence.json"

FEATURE = {"feature_id": "TABLE-006", "capability_id": "table.chart_from_table"}
TARGET = {
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
    PREDECESSOR: "25ff72a14743f4a98c88f2281abe08fcc122d73cf6db31b2dc4600e0e2d1bf43",
    "crates/domain-ir/src/table_chart.rs": (
        "e951f0f3c705246233991ca490c244c2b8ab0ccf9b9b15e8e6836c5decce70d2"
    ),
    "crates/hwpx-package/src/table_chart_hwpx.rs": (
        "9a713ded59ccf6848b11ccf632310350e9bff56a6025feb6aeaa58d7f46d9d70"
    ),
    "crates/hwpx-package/src/patch.rs": (
        "95b261f8376a39be9827a4a33f51ebc4bf3cbe2f8a7e26e5c37d71583711c9ad"
    ),
    "crates/hwpx-package/src/writer.rs": (
        "d4fb6e247e411d6100fd54da52d73221d13bc7df1c3e9f1f789115b9cf44f765"
    ),
    "crates/hwpx-package/src/id_index.rs": (
        "207c2302c6be7828d1ea8a5cacb668e590d493375681c1f1780361e1b2638ac9"
    ),
    "crates/hwpx-package/src/lib.rs": (
        "5c7d538880cc26259c8981a69df51fce54b795f1bd1b0204717fc860718fc37b"
    ),
    "crates/hwpx-package/tests/table_chart_hwpx.rs": (
        "85f82d195e6aa98822aab800c3ca1c25d1b67c5c7b01ae318c4945d600e42b77"
    ),
    "crates/hwpx-package/examples/p06_09_table_chart_target_fixture.rs": (
        "a0dff592f182525ba658a42048f960911521b96238de0fc6139a7874a3fdb7ba"
    ),
    "implementation/p06/tools/create-hancom-2020-table-chart-source.ps1": (
        "d0ceeacc267a23ef7105653790a13e7d5b14fba90da2df4cdea16dc4b41a5ec5"
    ),
    "implementation/p06/tools/run-hancom-2020-table-chart-source.ps1": (
        "b9d747ef62ce83634aeaf249e84eeffeff8fbbb54e3b21d9805e3bc8a01a17fc"
    ),
    "implementation/p06/tests/Test-Hancom2020TableChartSource.ps1": (
        "f8b7c7b5395b8ae70a03344c3cba5e7784de2e4215f7a05e5afc08de9ebd0b58"
    ),
    "implementation/p06/tools/validate-hancom-2020-table-chart-product.ps1": (
        "af73cb83c2badc261760f3572e0b971abf30750ae4f1fa260f185291a820ed8a"
    ),
    "implementation/p06/tools/run-hancom-2020-table-chart-product.ps1": (
        "6434b431a2e4ad52aa42d7c0f21600f5e389ca52a1c54456d29a7d5ce03142ba"
    ),
    "implementation/p06/tests/Test-Hancom2020TableChartProduct.ps1": (
        "60a1a883746d42a91d9057ce22070caecaed4a22044b48d11ed5842fa5e1b8dc"
    ),
}
ARTIFACTS = {
    "native_before": {
        "path": "fixtures/target-build/p06-09-table-chart-source-20260913-04/before.hwpx",
        "sha256": "7ed2006c862be671eba82c1a3648c2a30ce7176fef8a6ceb58469b167a5e4929",
        "bytes": 15140,
    },
    "native_after": {
        "path": "fixtures/target-build/p06-09-table-chart-source-20260913-04/after.hwpx",
        "sha256": "454901d38967f3b2a92b407fd09c0ad9f0a3a12d291c8849dfc02257db8bf40a",
        "bytes": 49614,
    },
    "native_watchdog": {
        "path": "fixtures/target-build/p06-09-table-chart-source-20260913-04/trace.json",
        "sha256": "c167be699dbeb7053be56e274d62b4bb4e73fd951de1aa88f5d7b2a397da457f",
        "bytes": 2107,
    },
    "native_inner_trace": {
        "path": (
            "fixtures/target-build/p06-09-table-chart-source-20260913-04/"
            "trace.json.inner.21984.json"
        ),
        "sha256": "b1a7a9d6f8dfa5ba4b908cb9d6d15d1e48168df1cddfccaf70f116d43c636a6d",
        "bytes": 1538,
    },
    "native_progress": {
        "path": (
            "fixtures/target-build/p06-09-table-chart-source-20260913-04/"
            "trace.json.progress.jsonl"
        ),
        "sha256": "2718aecc94409ad699fdec5baac44f10435d2c8b55088002b3c192a3ce498133",
        "bytes": 5298,
        "events": 18,
    },
    "normalized_source": {
        "path": (
            "fixtures/target-build/p06-09-table-chart-product-20260913-01/output/"
            "p06-09-table-chart-source-normalized.hwpx"
        ),
        "sha256": "f0a4015b621bd956b40fe5787d573bb9da6578bc26c6e3d31a7818f74f46449c",
        "bytes": 14294,
    },
    "direct_product": {
        "path": (
            "fixtures/target-build/p06-09-table-chart-product-20260913-01/output/"
            "p06-09-table-chart-product.hwpx"
        ),
        "sha256": "f9f7baa1f2aa975bd2d7fd63f268176e4cfa6121772e95b1893b9873b05bcf12",
        "bytes": 15327,
    },
    "saved_product": {
        "path": (
            "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-01/"
            "saved.hwpx"
        ),
        "sha256": "28faf18103332b617cc9f3706b003bd0d927e5ac67cf91fde776130cf8c31af4",
        "bytes": 49750,
    },
    "render_pdf": {
        "path": (
            "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-01/"
            "render.pdf"
        ),
        "sha256": "3ce33525182f07417d0aa1126e5d96feddab1cde8713b3da7c80eabec3a7a7fe",
        "bytes": 98655,
    },
    "product_watchdog": {
        "path": (
            "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-01/"
            "trace.json"
        ),
        "sha256": "0d2509bc10817d5f24d5e08280a431980d4437775ffbf5be09875f7ead5c63e5",
        "bytes": 2867,
    },
    "product_inner_trace": {
        "path": (
            "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-01/"
            "trace.json.inner.44824.json"
        ),
        "sha256": "73ad8ab7b67f612973667731125655bf3be6453f8f638031962a7a06d1759550",
        "bytes": 1922,
    },
    "product_progress": {
        "path": (
            "fixtures/target-build/p06-09-table-chart-product-hancom-20260913-01/"
            "trace.json.progress.jsonl"
        ),
        "sha256": "1a30b23715177302a05669682770e4c970e2d7ebbc043e228d6f7b92ec38f254",
        "bytes": 3597,
        "events": 12,
    },
}
ORDERED_VALUES = [
    "Series-A", "Category-A", "Category-B", "1", "3",
    "Series-B", "Category-A", "Category-B", "2", "4",
]
VERIFICATION = {
    "domain_tests": 12,
    "adapter_tests": 6,
    "native_source_static_tests": 24,
    "product_lifecycle_static_tests": 19,
    "contract_tests": 4,
    "fixture_classes": [
        "boundary", "happy_path", "negative", "preservation", "target_build"
    ],
    "validations": ["formula_readback", "page_split", "schema", "semantic_reopen"],
}
GATE_DECISION = {
    "TABLE-006": "integration_passed",
    "actual_hancom_2020_native_source": "pass",
    "direct_hwpx_build": "pass",
    "direct_output_package_save_reopen": "pass",
    "direct_output_pdf_export": "pass",
    "direct_output_render_review": "pass",
    "required_render_diff": "not_run",
    "rollback_or_retry": "not_run",
    "automation_runtime": "not_run",
    "release_differential": "not_run",
    "p06_09": "in_progress",
    "p06": "in_progress",
}
NOT_CLAIMED = {
    "required_render_diff": False,
    "rollback_or_retry": False,
    "product_automation_route_runtime": False,
    "release_differential": False,
    "merged_cell_chart_semantics": False,
    "arbitrary_user_document_compatibility": False,
    "other_pc_or_hancom_version": False,
    "p06_09_complete": False,
    "p06_phase_complete": False,
    "production": False,
    "product_complete": False,
}
IMPLEMENTATION_MARKERS = {
    "crates/hwpx-package/src/table_chart_hwpx.rs": (
        'TABLE_CHART_HWPX_SCHEMA_VERSION: &str = "hwpx-agent.table-chart-hwpx/v1"',
        'TABLE_CHART_HWPX_PROFILE_ID: &str =',
        "pub struct TableChartHwpxRequestDraft",
        "pub struct TableChartHwpxLoweringReceipt",
        "pub struct TableChartHwpxLowerer",
        "apply_with_limits_and_preservation_profile",
        "PreservationRuleProfile::Hangul2020PreviewTextV2",
        "fn validate_plan_cells",
        "verify_manifest_and_preservation",
    ),
    "crates/hwpx-package/src/patch.rs": (
        "apply_with_limits_and_preservation_profile",
        "preservation_profile: PreservationRuleProfile",
    ),
    "crates/hwpx-package/src/writer.rs": (
        "preservation_profile: PreservationRuleProfile",
        "patch.preservation_profile",
    ),
    "crates/hwpx-package/tests/table_chart_hwpx.rs": (
        "direct_chart_lowering_is_closed_strict_and_preserves_the_source_table",
        "source_inspection_requires_the_native_table_to_be_inside_a_run",
        "source_inspection_rejects_cell_digest_or_formula_provenance_drift",
        "request_json_rejects_duplicate_unknown_and_allocation_tampering",
        "lowering_rechecks_document_flow_and_emits_no_partial_result",
        "custom_domain_limits_are_used_consistently_during_lowering",
        "PreservingWriter::build",
    ),
    "crates/hwpx-package/examples/p06_09_table_chart_target_fixture.rs": (
        "p06-09-table-chart-source-normalized.hwpx",
        "p06-09-table-chart-product.hwpx",
        "TableChartHwpxLowerer::lower",
        "PreservingWriter::build",
        "AtomicPackagePublisher::publish",
    ),
    "implementation/p06/tools/validate-hancom-2020-table-chart-product.ps1": (
        "INPUT_DIGEST_MISMATCH",
        "$document.Open($input, 'HWPX'",
        "$document.SaveAs($output, 'HWPX'",
        "$document.Open($output, 'HWPX'",
        "$document.SaveAs($pdf, 'PDF'",
        "automation_differential = 'not_run'",
    ),
    "implementation/p06/tools/run-hancom-2020-table-chart-product.ps1": (
        "Read-ProgressJournal",
        "Stop-OwnedHancomProcess",
        "$progress.worker_process_id -eq [long]$child.Id",
        "TABLE_CHART_PRODUCT_PROCESS_CLEANUP_UNVERIFIED",
    ),
    "implementation/p06/tests/Test-Hancom2020TableChartProduct.ps1": (
        "total = $checks.Count",
        "wrong_digest_fails_before_com",
        "pdf_is_export_only_until_reviewed",
        "differential_not_promoted",
    ),
    POLICY: (
        "direct_hwpx / integration_passed",
        "Attempt `20260913-01`",
        "separately exported native-reference PDF",
    ),
    REPORT: (
        "Result: `integration_pass`",
        "6/6 PASS",
        "19/19 PASS",
        "`integration_passed`: 35 to 36",
        "required native-reference geometry/text/object `render_diff`",
    ),
}


def load_json_bytes(data: bytes) -> Any:
    return json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicate_keys)


def exact_bytes(root: Path, relative: str, maximum: int = 64_000_000) -> bytes:
    return bounded_file(root, relative, maximum).read_bytes()


def digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def read_chart_package(root: Path, artifact: str) -> dict[str, Any]:
    data = exact_bytes(root, ARTIFACTS[artifact]["path"], 20_000_000)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate archive path")
        section_names = [
            name for name in names
            if re.fullmatch(r"Contents/section\d+\.xml", name)
        ]
        chart_names = [
            name for name in names
            if re.fullmatch(r"Chart/chart\d+\.xml", name)
        ]
        if len(section_names) != 1 or len(chart_names) != 1:
            raise ValueError("chart package cardinality")
        section = archive.read(section_names[0]).decode("utf-8")
        chart = ET.fromstring(archive.read(chart_names[0]))
    values = [
        (node.text or "").strip()
        for node in chart.iter()
        if local_name(node.tag) == "v" and (node.text or "").strip()
    ]
    bar_dirs = [
        node.attrib.get("val")
        for node in chart.iter()
        if local_name(node.tag) == "barDir"
    ]
    return {
        "entries": len(names),
        "table_count": len(re.findall(r"<hp:tbl\b", section)),
        "cell_count": len(re.findall(r"<hp:tc\b", section)),
        "chart_anchor_count": len(re.findall(r"<hp:chart\b", section)),
        "chart_part_count": len(chart_names),
        "bar_3d_count": sum(
            1 for node in chart.iter() if local_name(node.tag) == "bar3DChart"
        ),
        "bar_dirs": bar_dirs,
        "source_labels_present": all(
            value in section
            for value in ("Series-A", "Series-B", "Category-A", "Category-B")
        ),
        "values": values,
    }


def validate_artifacts(root: Path, errors: list[str]) -> None:
    for expected in ARTIFACTS.values():
        try:
            data = exact_bytes(root, expected["path"])
            if len(data) != expected["bytes"] or digest_bytes(data) != expected["sha256"]:
                add_error(errors, "evidence_digest")
        except (OSError, ValueError):
            add_error(errors, "evidence_path")
    try:
        native_trace = load_json_bytes(exact_bytes(root, ARTIFACTS["native_watchdog"]["path"]))
        if (
            native_trace.get("schema_version")
            != "hwpx-agent.p06-09-hancom-2020-table-chart-source-watchdog/v1"
            or native_trace.get("state") != "pass"
            or native_trace.get("chart_action") != "pass"
            or native_trace.get("source_cells_written") != 8
            or native_trace.get("watchdog", {}).get("progress_event_count") != 18
            or native_trace.get("watchdog", {}).get("remaining_hwp_process_count") != 0
        ):
            add_error(errors, "native_trace")
        product_trace = load_json_bytes(exact_bytes(root, ARTIFACTS["product_watchdog"]["path"]))
        if (
            product_trace.get("schema_version")
            != "hwpx-agent.p06-09-hancom-2020-table-chart-product-watchdog/v1"
            or product_trace.get("state") != "pass"
            or product_trace.get("input_open") != "pass"
            or product_trace.get("hwp_save_as") != "pass"
            or product_trace.get("saved_reopen") != "pass"
            or product_trace.get("pdf_export") != "pass"
            or product_trace.get("input_visible_text_sha256")
            != product_trace.get("output_visible_text_sha256")
            or not product_trace.get("source_text_preserved")
            or not product_trace.get("actual_hangul_2020")
            or product_trace.get("automation_differential") != "not_run"
            or product_trace.get("watchdog", {}).get("progress_event_count") != 12
            or product_trace.get("watchdog", {}).get("remaining_hwp_process_count") != 0
        ):
            add_error(errors, "product_trace")
        for key in ("native_trace", "product_trace"):
            trace = native_trace if key == "native_trace" else product_trace
            if trace.get("raw_document_text_present") is not False or trace.get(
                "raw_chart_payload_present"
            ) is not False:
                add_error(errors, "trace_privacy")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "trace_json")

    for key, schema, events in (
        (
            "native_progress",
            "hwpx-agent.p06-09-hancom-2020-table-chart-progress/v1",
            18,
        ),
        (
            "product_progress",
            "hwpx-agent.p06-09-hancom-2020-table-chart-product-progress/v1",
            12,
        ),
    ):
        try:
            lines = exact_bytes(root, ARTIFACTS[key]["path"], 128_000).decode("utf-8").splitlines()
            rows = [load_json_bytes(line.encode("utf-8")) for line in lines]
            if (
                len(rows) != events
                or [row.get("sequence") for row in rows] != list(range(1, events + 1))
                or any(row.get("schema_version") != schema for row in rows)
                or rows[-1].get("phase") != "terminal"
                or rows[-1].get("state") != "pass"
                or any(row.get("raw_document_text_present") is not False for row in rows)
                or any(row.get("raw_chart_payload_present") is not False for row in rows)
            ):
                add_error(errors, "progress_sequence")
        except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
            add_error(errors, "progress_json")

    try:
        native = read_chart_package(root, "native_after")
        direct = read_chart_package(root, "direct_product")
        saved = read_chart_package(root, "saved_product")
        for name, package, entries in (
            ("direct", direct, 12),
            ("saved", saved, 13),
        ):
            if package != {
                "entries": entries,
                "table_count": 1,
                "cell_count": 9,
                "chart_anchor_count": 1,
                "chart_part_count": 1,
                "bar_3d_count": 1,
                "bar_dirs": ["col"],
                "source_labels_present": True,
                "values": ORDERED_VALUES,
            }:
                add_error(errors, f"{name}_package_semantics")
        if native["values"] != ORDERED_VALUES or native["values"] != saved["values"]:
            add_error(errors, "native_saved_semantic_match")
    except (OSError, UnicodeDecodeError, ValueError, ET.ParseError, zipfile.BadZipFile):
        add_error(errors, "chart_package_readback")

    try:
        pdf = exact_bytes(root, ARTIFACTS["render_pdf"]["path"])
        if (
            not pdf.startswith(b"%PDF-1.4")
            or b"Hwp 2020 11.0.0.9136" not in pdf
            or b"Hancom PDF 1.3.0.550" not in pdf
            or not re.search(rb"/Count\s+1\b", pdf)
            or not re.search(rb"/MediaBox\s*\[\s*0\s+0\s+595\s+841\s*\]", pdf)
        ):
            add_error(errors, "pdf_identity")
    except (OSError, ValueError):
        add_error(errors, "pdf_path")


def validate_contract(root: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        contract = load_json_bytes(exact_bytes(root, CONTRACT, 256_000))
        if not isinstance(contract, dict):
            raise ValueError("contract root")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "contract_json_or_path")
        return None
    expected_keys = {
        "schema_version", "profile_id", "predecessor", "scope", "feature",
        "source_lock_canonicalization", "source_locks", "exact_target",
        "successful_attempts", "native_profile", "binding", "lowering",
        "preservation", "target_oracle", "expected_evidence", "failure_policy",
        "receipt", "migration", "policy", "report", "gate_decision", "not_claimed",
    }
    if set(contract) != expected_keys:
        add_error(errors, "contract_shape")
    if (
        contract.get("schema_version") != "hwpx-agent.table-chart-hwpx-contract/v1"
        or contract.get("profile_id")
        != "hwpx-agent.table-chart-hwpx.hancom-2020/1"
        or contract.get("feature") != FEATURE
        or contract.get("exact_target") != TARGET
        or contract.get("receipt") != RECEIPT
        or contract.get("migration") != MIGRATION
        or contract.get("policy") != POLICY
        or contract.get("report") != REPORT
    ):
        add_error(errors, "contract_semantics")
    predecessor = contract.get("predecessor")
    if predecessor != {
        "path": PREDECESSOR,
        "sha256": SOURCE_LOCKS[PREDECESSOR],
        "state": "immutable_pure_planner_contract",
    }:
        add_error(errors, "predecessor")
    locks = contract.get("source_locks")
    expected_locks = [
        {"path": path, "sha256": digest} for path, digest in SOURCE_LOCKS.items()
    ]
    if locks != expected_locks:
        add_error(errors, "source_locks_exact")
    if contract.get("expected_evidence") != {
        **VERIFICATION,
        "feature_count": 1,
        "backend": "direct_hwpx",
        "direct_stage": "integration_passed",
    }:
        add_error(errors, "expected_evidence")
    if contract.get("gate_decision") != GATE_DECISION:
        add_error(errors, "gate_decision")
    if contract.get("not_claimed") != NOT_CLAIMED:
        add_error(errors, "not_claimed")
    if contract.get("target_oracle", {}).get("required_render_diff") != (
        "not_run_until_native_reference_pdf_is_exported_and_compared"
    ):
        add_error(errors, "target_oracle")
    return contract


def validate_sources_and_markers(root: Path, errors: list[str]) -> None:
    for relative, expected in SOURCE_LOCKS.items():
        try:
            if canonical_sha256(bounded_file(root, relative, 5_000_000)) != expected:
                add_error(errors, "source_lock_digest")
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "source_lock_path")
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            text = bounded_file(root, relative, 5_000_000).read_text(encoding="utf-8")
            if any(marker not in text for marker in markers):
                add_error(errors, "implementation_marker")
        except (OSError, UnicodeDecodeError, ValueError):
            add_error(errors, "implementation_path")
    try:
        migration = bounded_file(root, MIGRATION, 256_000).read_text(encoding="utf-8")
        for marker in (
            "Before this profile",
            "source artifact is never rewritten",
            "may not be inferred",
            "direct_hwpx / integration_passed",
            "release exact differential remain separate Gates",
        ):
            if marker not in migration:
                add_error(errors, "migration_marker")
    except (OSError, UnicodeDecodeError, ValueError):
        add_error(errors, "migration_path")


def validate_receipt(root: Path, errors: list[str]) -> None:
    try:
        receipt = load_json_bytes(exact_bytes(root, RECEIPT, 512_000))
        if not isinstance(receipt, dict):
            raise ValueError("receipt root")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "evidence_receipt")
        return
    expected_keys = {
        "schema_version", "evidence_id", "scope", "feature", "target", "artifacts",
        "direct_readback", "target_lifecycle", "render_review", "verification",
        "historical_attempts", "privacy", "gate_decision", "not_claimed",
    }
    if set(receipt) != expected_keys:
        add_error(errors, "evidence_receipt_shape")
    if (
        receipt.get("schema_version")
        != "hwpx-agent.p06-09-table-chart-current-2020-evidence/v1"
        or receipt.get("feature") != FEATURE
        or receipt.get("target") != TARGET
        or receipt.get("artifacts") != ARTIFACTS
        or receipt.get("verification") != VERIFICATION
        or receipt.get("gate_decision") != GATE_DECISION
        or receipt.get("not_claimed") != NOT_CLAIMED
    ):
        add_error(errors, "evidence_receipt")
    direct = receipt.get("direct_readback", {})
    if (
        direct.get("ordered_chart_cache_values") != ORDERED_VALUES
        or direct.get("native_and_saved_chart_cache_values_exact_match") is not True
        or direct.get("chart_type") != "three_dimensional_vertical_bar"
        or direct.get("bar_direction") != "column"
    ):
        add_error(errors, "evidence_direct_readback")
    lifecycle = receipt.get("target_lifecycle", {})
    if (
        lifecycle.get("state") != "pass"
        or lifecycle.get("product_input_open") != "pass"
        or lifecycle.get("product_save_as") != "pass"
        or lifecycle.get("saved_product_reopen") != "pass"
        or lifecycle.get("visible_source_text_sha256_equal") is not True
        or lifecycle.get("pdf_export") != "pass"
        or lifecycle.get("remaining_hwp_process_count") != 0
    ):
        add_error(errors, "evidence_lifecycle")
    render = receipt.get("render_review", {})
    if (
        render.get("pdf_pages") != 1
        or render.get("page_size") != "A4"
        or render.get("three_dimensional_vertical_bars_visible") is not True
        or render.get("clipping_or_overlap_observed") is not False
        or render.get("native_reference_render_comparison") != "not_run"
        or render.get("photo_or_user_screenshot_required") is not False
    ):
        add_error(errors, "evidence_render_review")
    privacy = receipt.get("privacy")
    if not isinstance(privacy, dict) or any(value is not False for value in privacy.values()):
        add_error(errors, "evidence_privacy")


def validate_direct_evidence(root: Path, errors: list[str]) -> None:
    try:
        evidence = load_json_bytes(exact_bytes(root, DIRECT_EVIDENCE, 2_000_000))
        records = evidence.get("records") if isinstance(evidence, dict) else None
        if not isinstance(records, list):
            raise ValueError("records")
        matches = [record for record in records if record.get("feature_ids") == ["TABLE-006"]]
        if len(matches) != 1:
            raise ValueError("feature record")
        record = matches[0]
        paths = [item.get("path") for item in record.get("evidence_files", [])]
        if (
            record.get("backend") != "direct_hwpx"
            or record.get("stage") != "integration_passed"
            or record.get("validations_passed")
            != ["formula_readback", "page_split", "schema", "semantic_reopen"]
            or record.get("fixture_classes_passed")
            != ["boundary", "happy_path", "negative", "preservation", "target_build"]
            or record.get("negative_passed") is not True
            or record.get("rollback_or_retry_passed") is not False
            or record.get("differential_state") != "not_run"
            or paths != [
                "implementation/p06/P06-09_TABLE_CHART_REPORT.md",
                REPORT,
                RECEIPT,
            ]
        ):
            add_error(errors, "direct_evidence")
        for item in record.get("evidence_files", []):
            path = item.get("path")
            if not isinstance(path, str) or item.get("sha256") != canonical_sha256(
                bounded_file(root, path, 1_000_000)
            ):
                add_error(errors, "direct_evidence_digest")
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, "direct_evidence")


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    validate_contract(root, errors)
    validate_sources_and_markers(root, errors)
    validate_artifacts(root, errors)
    validate_receipt(root, errors)
    validate_direct_evidence(root, errors)
    unique = sorted(set(errors))
    return {
        "schema_version": "hwpx-agent.p06-table-chart-hwpx-validation/v1",
        "state": "pass" if not unique else "fail",
        "errors": unique,
        "source_locks": len(SOURCE_LOCKS),
        "evidence_files": len(ARTIFACTS),
        "implementation_files": len(IMPLEMENTATION_MARKERS),
        "features": 1,
        "direct_stage": "integration_passed" if not unique else "not_proven",
        "actual_hancom_2020": not unique,
        "direct_output_package_save_reopen": not unique,
        "direct_output_pdf_export": not unique,
        "required_render_diff": "not_run",
        "automation_runtime": "not_run",
        "p06_09": "in_progress",
        "product_complete": False,
    }


if __name__ == "__main__":
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True))
    raise SystemExit(0 if validation["state"] == "pass" else 1)
