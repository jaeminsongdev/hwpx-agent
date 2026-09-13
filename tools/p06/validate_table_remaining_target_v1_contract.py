#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "protocol/private/p06-table-remaining-target-v1.json"
EXPECTED_SCHEMA = "hwpx-agent.p06-09-table-remaining-target-contract/v1"
EXPECTED_MANIFEST_SCHEMA = "hwpx-agent.p06-09-table-remaining-target-fixture/v1"
EXPECTED_MANIFEST_SHA256 = "1aeddc699c91c4878242a64e7674d1689a86b8abeda704370eeaac337bf95a8e"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_CASES = {
    "TABLE-020": ("table.table_style", "table_style_hwpx", "common", "table-020-style.hwpx", 0, 1),
    "TABLE-021": ("table.transpose", "table_transpose_hwpx", "common", "table-021-transpose.hwpx", 0, 1),
    "TABLE-032": ("table.thousands_add", "table_thousands_hwpx", "thousands_removed", "table-032-thousands-add.hwpx", 1, 1),
    "TABLE-033": ("table.thousands_remove", "table_thousands_hwpx", "thousands_baseline", "table-033-thousands-remove.hwpx", 1, 1),
    "TABLE-049": ("table.number_format", "table_number_format_hwpx", "number_baseline", "table-049-number-format.hwpx", 6, 1),
    "TABLE-054": ("table.nested_table", "table_nested_table_hwpx", "common_envelope_with_inline_nested_template", "table-054-nested-table.hwpx", 1, 2),
    "TABLE-056": ("table.sort_cells", "table_sort_hwpx", "common", "table-056-sort.hwpx", 0, 1),
    "TABLE-057": ("table.auto_fill", "table_auto_fill_hwpx", "common_envelope_with_inline_auto_fill_section", "table-057-auto-fill.hwpx", 0, 1),
    "TABLE-058": ("table.auto_fill_series", "table_auto_fill_hwpx", "common_envelope_with_inline_auto_fill_section", "table-058-auto-fill-series.hwpx", 0, 1),
    "TABLE-060": ("table.formula_absolute_ref", "table_absolute_reference_hwpx", "common_envelope_with_inline_absolute_formula_section", "table-060-absolute-reference.hwpx", 2, 1),
}
EXPECTED_SOURCES = {
    "common": ("fixtures/target-build/p06-09-table-structure-target-20260913-05/table-012-insert-row-3x3.hwpx", "0459a05b8543edb2e05c9c0117f76df999c8543bad255d06d26d4b3b57388252"),
    "thousands_baseline": ("fixtures/target-build/p06-09-table-thousands-source-20260913-11/baseline.hwpx", "8b125fd14e69612b7896f22f7a8e93180709ae41c675aba5166a03820aa1ff7c"),
    "thousands_removed": ("fixtures/target-build/p06-09-table-thousands-source-20260913-11/removed.hwpx", "985e5a87f4396cc113203e00acae2b2868b515c409c07b51d167dc496081519a"),
    "thousands_added": ("fixtures/target-build/p06-09-table-thousands-source-20260913-11/added.hwpx", "15166fd74bc5f9cee21df4833b3d994e78edec2c700a4a612bc63e3be987a419"),
    "number_baseline": ("fixtures/target-build/p06-09-table-number-format-source-20260913-05/baseline.hwpx", "9f862bb2772c95271d3e97089c3ca29b88aa138e7fae524e8461bcf77ddac042"),
    "number_ungrouped": ("fixtures/target-build/p06-09-table-number-format-source-20260913-05/ungrouped.hwpx", "fa859aaff54cdc7faa8c5d55639040f0e6cc450691d61889356a59db4abbced9"),
    "number_grouped": ("fixtures/target-build/p06-09-table-number-format-source-20260913-05/grouped.hwpx", "c5f0a1881f0c7d4b4fc0105bd76f3929a3f0b4d64da756dd124a4cd66d122027"),
}


class ContractError(RuntimeError):
    pass


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ContractError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"cannot read JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise ContractError(f"JSON root is not an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_normalized_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ContractError(f"{label} keys differ")


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ContractError(f"{label} is not lowercase SHA-256")
    return value


def validate_source_locks(contract: dict[str, Any]) -> int:
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        raise ContractError("source lock canonicalization differs")
    locks = contract.get("source_locks")
    if not isinstance(locks, list) or len(locks) != 14:
        raise ContractError("source lock set differs")
    seen: set[str] = set()
    for index, lock in enumerate(locks):
        if not isinstance(lock, dict):
            raise ContractError(f"source lock {index} is not an object")
        require_exact_keys(lock, {"path", "sha256"}, f"source lock {index}")
        relative = lock["path"]
        if not isinstance(relative, str) or relative in seen:
            raise ContractError(f"source lock {index} path differs")
        seen.add(relative)
        expected = require_sha256(lock["sha256"], f"source lock {index}")
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"source lock path is not a regular file: {relative}")
        if sha256_normalized_text(path) != expected:
            raise ContractError(f"source lock digest differs: {relative}")
    return len(locks)


def validate_contract_shape(contract: dict[str, Any]) -> None:
    require_exact_keys(
        contract,
        {
            "schema_version",
            "scope",
            "features",
            "predecessors",
            "source_lock_canonicalization",
            "source_locks",
            "exact_sources",
            "fixture_publication",
            "cases",
            "batch_runtime",
            "gate_decision",
            "failure_policy",
            "not_claimed",
        },
        "contract",
    )
    expected_features = {feature: values[0] for feature, values in EXPECTED_CASES.items()}
    if contract.get("schema_version") != EXPECTED_SCHEMA or contract.get("features") != expected_features:
        raise ContractError("contract identity or feature set differs")
    if contract.get("exact_sources") != [
        {"role": role, "path": path, "sha256": digest}
        for role, (path, digest) in EXPECTED_SOURCES.items()
    ]:
        raise ContractError("exact source set differs")
    for role, (relative, digest) in EXPECTED_SOURCES.items():
        if sha256_file(ROOT / relative) != digest:
            raise ContractError(f"exact source digest differs: {role}")
    publication = contract["fixture_publication"]
    if (
        publication.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256
        or publication.get("case_count") != 10
        or publication.get("build_count") != 3
        or publication.get("write_mode") != "independent_create_new"
        or publication.get("byte_deterministic") is not True
    ):
        raise ContractError("fixture publication boundary differs")
    runtime = contract["batch_runtime"]
    if (
        runtime.get("case_count") != 10
        or runtime.get("state") != "failed_open_input_timeout"
        or runtime.get("attempted_case_count") != 10
        or runtime.get("probed_case_count") != 0
        or runtime.get("completed_case_count") != 0
        or runtime.get("failed_case_count") != 10
        or runtime.get("failed_feature_ids") != list(EXPECTED_CASES)
        or runtime.get("failed_phase") != "open_input"
        or runtime.get("error_code") != "TABLE_PROPERTIES_TARGET_READBACK_TIMEOUT"
        or runtime.get("timeout_seconds_per_invocation") != 30
        or runtime.get("input_unchanged_count") != 10
        or runtime.get("output_absent_count") != 10
        or runtime.get("cleaned_process_count") != 10
        or runtime.get("remaining_hwp_process_count") != 0
    ):
        raise ContractError("batch runtime state differs")
    require_sha256(runtime.get("batch_trace_sha256"), "batch runtime batch_trace_sha256")
    failure_traces = runtime.get("failure_traces")
    if not isinstance(failure_traces, list) or len(failure_traces) != 10:
        raise ContractError("batch runtime failure trace set differs")
    gate = contract["gate_decision"]
    if (
        gate.get("fixture_preparation") != "pass"
        or gate.get("actual_target_lifecycle") != "failed"
        or gate.get("direct_stage_change") != "none"
    ):
        raise ContractError("gate decision differs")
    if any(value is not False for value in contract["not_claimed"].values()):
        raise ContractError("not-claimed boundary differs")


def validate_cases(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    cases = contract["cases"]
    if not isinstance(cases, list) or len(cases) != 10:
        raise ContractError("case count differs")
    by_feature: dict[str, dict[str, Any]] = {}
    expected_keys = {
        "feature_id", "capability_id", "adapter", "source_role", "file", "sha256",
        "target_header_sha256", "target_section_sha256", "semantic_sha256",
        "formula_count", "table_count",
    }
    for case in cases:
        if not isinstance(case, dict):
            raise ContractError("contract case is not an object")
        require_exact_keys(case, expected_keys, "contract case")
        feature = case["feature_id"]
        expected = EXPECTED_CASES.get(feature)
        if expected is None or feature in by_feature:
            raise ContractError(f"case identity differs: {feature}")
        if (
            case["capability_id"] != expected[0]
            or case["adapter"] != expected[1]
            or case["source_role"] != expected[2]
            or case["file"] != expected[3]
            or case["formula_count"] != expected[4]
            or case["table_count"] != expected[5]
        ):
            raise ContractError(f"case binding differs: {feature}")
        for field in ("sha256", "target_header_sha256", "target_section_sha256", "semantic_sha256"):
            require_sha256(case[field], f"{feature} {field}")
        by_feature[feature] = case
    if set(by_feature) != set(EXPECTED_CASES):
        raise ContractError("case feature set differs")
    return by_feature


def validate_publications(contract: dict[str, Any], cases: dict[str, dict[str, Any]]) -> None:
    publication = contract["fixture_publication"]
    directories = [
        publication["directory"],
        publication["independent_retry_directory"],
        publication["current_source_rebuild_directory"],
    ]
    manifests: list[bytes] = []
    packages: dict[str, list[bytes]] = {feature: [] for feature in EXPECTED_CASES}
    for relative_directory in directories:
        directory = ROOT / relative_directory
        manifest_path = directory / publication["manifest_file"]
        if sha256_file(manifest_path) != EXPECTED_MANIFEST_SHA256:
            raise ContractError(f"fixture manifest digest differs: {relative_directory}")
        manifest_bytes = manifest_path.read_bytes()
        manifests.append(manifest_bytes)
        manifest = load_json(manifest_path)
        if (
            manifest.get("schema_version") != EXPECTED_MANIFEST_SCHEMA
            or manifest.get("source_artifacts") != [
                {"role": role, "path": path, "sha256": digest}
                for role, (path, digest) in EXPECTED_SOURCES.items()
            ]
            or manifest.get("actual_hangul_2020") is not False
            or manifest.get("render") != "not_run"
            or manifest.get("automation") != "not_run"
            or manifest.get("differential") != "not_run"
        ):
            raise ContractError(f"fixture manifest state differs: {relative_directory}")
        manifest_cases = manifest.get("cases")
        if not isinstance(manifest_cases, list) or len(manifest_cases) != 10:
            raise ContractError("fixture manifest case count differs")
        manifest_by_feature = {item.get("feature_id"): item for item in manifest_cases}
        if set(manifest_by_feature) != set(EXPECTED_CASES):
            raise ContractError("fixture manifest feature set differs")
        for feature, contract_case in cases.items():
            manifest_case = manifest_by_feature[feature]
            expected = EXPECTED_CASES[feature]
            for field in (
                "capability_id", "adapter", "source_role", "file", "sha256",
                "target_header_sha256", "target_section_sha256", "semantic_sha256",
                "formula_count", "table_count",
            ):
                if manifest_case.get(field) != contract_case[field]:
                    raise ContractError(f"fixture case differs: {feature}")
            if manifest_case.get("formula_count") != expected[4] or manifest_case.get("table_count") != expected[5]:
                raise ContractError(f"fixture cardinality differs: {feature}")
            package = (directory / contract_case["file"]).read_bytes()
            if hashlib.sha256(package).hexdigest() != contract_case["sha256"]:
                raise ContractError(f"fixture package digest differs: {feature}")
            packages[feature].append(package)
    if not all(value == manifests[0] for value in manifests[1:]):
        raise ContractError("independent fixture manifests are not byte-identical")
    for feature, values in packages.items():
        if not all(value == values[0] for value in values[1:]):
            raise ContractError(f"independent fixture packages differ: {feature}")


def validate_failed_runtime(
    contract: dict[str, Any], cases: dict[str, dict[str, Any]]
) -> None:
    runtime = contract["batch_runtime"]
    attempt = ROOT / runtime["attempt_directory"]
    batch_trace_path = attempt / runtime["batch_trace_file"]
    if sha256_file(batch_trace_path) != runtime["batch_trace_sha256"]:
        raise ContractError("failed batch trace digest differs")
    batch_trace = load_json(batch_trace_path)
    require_exact_keys(
        batch_trace,
        {
            "schema_version",
            "state",
            "fixture_manifest_sha256",
            "target",
            "attempted_case_count",
            "probed_case_count",
            "completed_case_count",
            "failed_case_count",
            "failures",
            "text_probes",
            "cases",
            "remaining_hwp_process_count",
            "actual_hangul_2020",
        },
        "failed batch trace",
    )
    if (
        batch_trace.get("schema_version")
        != "hwpx-agent.p06-09-table-remaining-target-batch-readback-failure/v1"
        or batch_trace.get("state") != "failed"
        or batch_trace.get("fixture_manifest_sha256") != EXPECTED_MANIFEST_SHA256
        or batch_trace.get("target") is not None
        or batch_trace.get("attempted_case_count") != 10
        or batch_trace.get("probed_case_count") != 0
        or batch_trace.get("completed_case_count") != 0
        or batch_trace.get("failed_case_count") != 10
        or batch_trace.get("text_probes") != []
        or batch_trace.get("cases") != []
        or batch_trace.get("remaining_hwp_process_count") != 0
        or batch_trace.get("actual_hangul_2020") is not True
    ):
        raise ContractError("failed runtime trace boundary differs")

    failures = batch_trace.get("failures")
    trace_contracts = runtime["failure_traces"]
    if not isinstance(failures, list) or len(failures) != 10:
        raise ContractError("failed runtime result set differs")
    for feature, failure, trace_contract in zip(
        EXPECTED_CASES, failures, trace_contracts, strict=True
    ):
        contract_case = cases[feature]
        expected_case_id = Path(contract_case["file"]).stem
        require_exact_keys(
            trace_contract,
            {
                "feature_id",
                "case_id",
                "trace_file",
                "trace_sha256",
                "progress_file",
                "progress_sha256",
            },
            f"{feature} failure trace contract",
        )
        if (
            trace_contract["feature_id"] != feature
            or trace_contract["case_id"] != expected_case_id
        ):
            raise ContractError(f"failure trace identity differs: {feature}")
        require_exact_keys(
            failure,
            {
                "case_id",
                "feature_id",
                "stage",
                "child_exit_code",
                "error_code",
                "failed_phase",
                "input_sha256",
                "input_unchanged",
                "output_absent",
                "trace_path",
                "trace_sha256",
                "progress_path",
                "progress_sha256",
                "remaining_hwp_process_count",
            },
            f"{feature} batch failure entry",
        )
        trace_path = attempt / trace_contract["trace_file"]
        progress_path = attempt / trace_contract["progress_file"]
        if sha256_file(trace_path) != require_sha256(
            trace_contract["trace_sha256"], f"{feature} trace_sha256"
        ):
            raise ContractError(f"failed case trace digest differs: {feature}")
        if sha256_file(progress_path) != require_sha256(
            trace_contract["progress_sha256"], f"{feature} progress_sha256"
        ):
            raise ContractError(f"failed case progress digest differs: {feature}")
        if (
            failure.get("case_id") != expected_case_id
            or failure.get("feature_id") != feature
            or failure.get("stage") != "text_probe"
            or failure.get("child_exit_code") != 2
            or failure.get("error_code") != "TABLE_PROPERTIES_TARGET_READBACK_TIMEOUT"
            or failure.get("failed_phase") != "open_input"
            or failure.get("input_sha256") != contract_case["sha256"]
            or failure.get("input_unchanged") is not True
            or failure.get("output_absent") is not True
            or failure.get("trace_path") != trace_contract["trace_file"]
            or failure.get("trace_sha256") != trace_contract["trace_sha256"]
            or failure.get("progress_path") != trace_contract["progress_file"]
            or failure.get("progress_sha256") != trace_contract["progress_sha256"]
            or failure.get("remaining_hwp_process_count") != 0
        ):
            raise ContractError(f"batch failure entry differs: {feature}")
        case_trace = load_json(trace_path)
        watchdog = case_trace.get("watchdog", {})
        if (
            case_trace.get("schema_version")
            != "hwpx-agent.p06-09-hancom-2020-table-properties-target-readback/v1"
            or "target" in case_trace
            or case_trace.get("delegated_engine_schema") is not None
            or case_trace.get("state") != "failed"
            or case_trace.get("input_sha256") != contract_case["sha256"]
            or case_trace.get("failed_phase") != "open_input"
            or case_trace.get("error_code") != "TABLE_PROPERTIES_TARGET_READBACK_TIMEOUT"
            or case_trace.get("input_unchanged") is not True
            or case_trace.get("input_text_sha256") is not None
            or case_trace.get("output_sha256") is not None
            or case_trace.get("output_text_sha256") is not None
            or case_trace.get("output_saved") is not False
            or case_trace.get("render_pdf_requested") is not False
            or case_trace.get("render_pdf_saved") is not False
            or case_trace.get("render_pdf_sha256") is not None
            or case_trace.get("render_pdf_signature_valid") is not False
            or case_trace.get("raw_document_text_present") is not False
            or case_trace.get("user_document_scanned") is not False
            or case_trace.get("external_network_invoked") is not False
            or case_trace.get("registry_or_system_setting_changed") is not False
            or case_trace.get("computer_use_click_or_type_invoked") is not False
            or case_trace.get("window_visible_for_user_access") is not True
            or watchdog.get("timeout_seconds") != 30
            or watchdog.get("timed_out") is not True
            or watchdog.get("child_exit_code") != -1
            or watchdog.get("cleaned_process_count") != 1
            or watchdog.get("cleanup_refused_count") != 0
            or watchdog.get("cleanup_error_count") != 0
            or watchdog.get("remaining_hwp_process_count") != 0
            or watchdog.get("progress_valid") is not True
            or watchdog.get("progress_event_count") != 3
            or watchdog.get("progress_last_phase") != "open_input"
            or watchdog.get("progress_last_state") != "running"
            or watchdog.get("progress_observed_phase") != "open_input"
            or watchdog.get("window_visible_for_user_access") is not True
        ):
            raise ContractError(f"failed case runtime boundary differs: {feature}")
        for suffix in (
            ".hancom-2020-text-probe-unused.hwpx",
            ".hancom-2020-readback.hwpx",
            ".hancom-2020-render.pdf",
            ".hancom-2020-trace.json",
        ):
            if (attempt / f"{expected_case_id}{suffix}").exists():
                raise ContractError(
                    f"failed runtime unexpectedly published output: {feature}"
                )
    clean_retry = ROOT / runtime["clean_retry_directory"]
    if any(clean_retry.glob("*.hancom-2020-*")) or any(clean_retry.glob("batch-trace*.json")):
        raise ContractError("clean retry directory is not clean")


def validate(contract_path: Path) -> None:
    contract = load_json(contract_path)
    validate_contract_shape(contract)
    source_lock_count = validate_source_locks(contract)
    cases = validate_cases(contract)
    validate_publications(contract, cases)
    validate_failed_runtime(contract, cases)
    print(
        "schema=hwpx-agent.p06-09-table-remaining-target-contract-validation/v1 "
        f"state=pass features={len(cases)} source_locks={source_lock_count} "
        "fixture_builds=3 actual_hangul_2020=failed_open_input_timeout"
    )


def main() -> int:
    contract_path = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else DEFAULT_CONTRACT
    if len(sys.argv) > 2:
        print("usage: validate_table_remaining_target_v1_contract.py [contract]", file=sys.stderr)
        return 2
    try:
        validate(contract_path)
    except (ContractError, OSError, KeyError, TypeError, ValueError) as error:
        print(f"validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
