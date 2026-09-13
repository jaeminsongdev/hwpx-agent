#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "protocol/private/p06-table-layout-placement-target-v1.json"
EXPECTED_SCHEMA = "hwpx-agent.p06-09-table-layout-placement-target-contract/v1"
EXPECTED_MANIFEST_SCHEMA = "hwpx-agent.p06-09-table-layout-placement-target-fixture/v1"
EXPECTED_MANIFEST_SHA256 = "33c391ff2b151f815c4e2e79c9144c53547fe87d5e35d1e856e4e796b3978faf"
EXPECTED_ANCESTOR_SHA256 = "0459a05b8543edb2e05c9c0117f76df999c8543bad255d06d26d4b3b57388252"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_FEATURES = {
    "TABLE-018": "table.equal_row_height",
    "TABLE-019": "table.equal_column_width",
    "TABLE-034": "table.position",
    "TABLE-036": "table.inline_floating",
    "TABLE-037": "table.wrap",
    "TABLE-038": "table.outer_margin",
    "TABLE-050": "table.row_min_height",
    "TABLE-051": "table.column_fixed_width",
    "TABLE-052": "table.autofit_content",
    "TABLE-053": "table.autofit_page",
}
EXPECTED_CASE_FILES = {
    "TABLE-018": "table-018-equal-row-height-4x3.hwpx",
    "TABLE-019": "table-019-equal-column-width-4x3.hwpx",
    "TABLE-034": "table-034-position-4x3.hwpx",
    "TABLE-036": "table-036-inline-floating-4x3.hwpx",
    "TABLE-037": "table-037-wrap-4x3.hwpx",
    "TABLE-038": "table-038-outer-margin-4x3.hwpx",
    "TABLE-050": "table-050-row-min-height-4x3.hwpx",
    "TABLE-051": "table-051-column-fixed-width-4x3.hwpx",
    "TABLE-052": "table-052-autofit-content-4x3.hwpx",
    "TABLE-053": "table-053-autofit-page-4x3.hwpx",
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
    if not isinstance(locks, list) or len(locks) != 10:
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
    expected_top = {
        "schema_version",
        "scope",
        "features",
        "predecessors",
        "source_lock_canonicalization",
        "source_locks",
        "exact_input",
        "fixture_publication",
        "cases",
        "batch_runtime",
        "gate_decision",
        "failure_policy",
        "not_claimed",
    }
    require_exact_keys(contract, expected_top, "contract")
    if contract["schema_version"] != EXPECTED_SCHEMA or contract["features"] != EXPECTED_FEATURES:
        raise ContractError("contract identity or feature set differs")
    exact_input = contract["exact_input"]
    if (
        exact_input.get("sha256") != EXPECTED_ANCESTOR_SHA256
        or exact_input.get("origin_feature_id") != "TABLE-012"
        or exact_input.get("origin_state") != "oracle_verified"
        or [exact_input.get("rows"), exact_input.get("columns"), exact_input.get("master_cell_count")]
        != [4, 3, 12]
        or exact_input.get("payload_block_count") != 9
        or exact_input.get("formula_count") != 0
        or exact_input.get("page_split") != "cell"
    ):
        raise ContractError("exact input boundary differs")
    input_path = ROOT / exact_input["path"]
    if sha256_file(input_path) != EXPECTED_ANCESTOR_SHA256:
        raise ContractError("exact input digest differs")
    publication = contract["fixture_publication"]
    if (
        publication.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256
        or publication.get("case_count") != 10
        or publication.get("build_count") != 3
        or publication.get("write_mode") != "independent_create_new"
        or publication.get("byte_deterministic") is not True
        or publication.get("all_cases_content_preserved") is not True
    ):
        raise ContractError("fixture publication boundary differs")
    runtime = contract["batch_runtime"]
    if (
        runtime.get("case_count") != 10
        or runtime.get("state") != "failed_open_input"
        or runtime.get("failed_feature_id") != "TABLE-018"
        or runtime.get("failed_phase") != "open_input"
        or runtime.get("error_code")
        != "TABLE_PROPERTIES_TARGET_READBACK_INPUT_OPEN_RETURNED_FALSE"
        or runtime.get("input_unchanged") is not True
        or runtime.get("output_absent") is not True
        or runtime.get("remaining_hwp_process_count") != 0
    ):
        raise ContractError("batch runtime state differs")
    for field in ("batch_trace_sha256", "case_trace_sha256"):
        require_sha256(runtime.get(field), f"batch runtime {field}")
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
    for case in cases:
        require_exact_keys(
            case,
            {"feature_id", "capability_id", "file", "sha256", "semantic_sha256"},
            "contract case",
        )
        feature = case["feature_id"]
        if (
            feature in by_feature
            or EXPECTED_FEATURES.get(feature) != case["capability_id"]
            or EXPECTED_CASE_FILES.get(feature) != case["file"]
        ):
            raise ContractError(f"case identity differs: {feature}")
        require_sha256(case["sha256"], f"{feature} package")
        require_sha256(case["semantic_sha256"], f"{feature} semantic")
        by_feature[feature] = case
    if set(by_feature) != set(EXPECTED_FEATURES):
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
    packages: dict[str, list[bytes]] = {feature: [] for feature in EXPECTED_FEATURES}
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
            or manifest.get("source_ancestor_sha256") != EXPECTED_ANCESTOR_SHA256
            or manifest.get("actual_hangul_2020") is not False
            or manifest.get("render") != "not_run"
            or manifest.get("automation") != "not_run"
            or manifest.get("differential") != "not_run"
            or manifest.get("all_cases_content_preserved") is not True
        ):
            raise ContractError(f"fixture manifest state differs: {relative_directory}")
        manifest_cases = manifest.get("cases")
        if not isinstance(manifest_cases, list) or len(manifest_cases) != 10:
            raise ContractError("fixture manifest case count differs")
        manifest_by_feature = {case.get("feature_id"): case for case in manifest_cases}
        if set(manifest_by_feature) != set(EXPECTED_FEATURES):
            raise ContractError("fixture manifest feature set differs")
        for feature, contract_case in cases.items():
            manifest_case = manifest_by_feature[feature]
            if (
                manifest_case.get("capability_id") != EXPECTED_FEATURES[feature]
                or manifest_case.get("file") != contract_case["file"]
                or manifest_case.get("sha256") != contract_case["sha256"]
                or manifest_case.get("semantic_sha256") != contract_case["semantic_sha256"]
                or manifest_case.get("formula_count") != 0
                or manifest_case.get("page_split") != "cell"
            ):
                raise ContractError(f"fixture case differs: {feature}")
            package = (directory / contract_case["file"]).read_bytes()
            if hashlib.sha256(package).hexdigest() != contract_case["sha256"]:
                raise ContractError(f"fixture package digest differs: {feature}")
            packages[feature].append(package)
    if not all(value == manifests[0] for value in manifests[1:]):
        raise ContractError("independent fixture manifests are not byte-identical")
    for feature, values in packages.items():
        if not all(value == values[0] for value in values[1:]):
            raise ContractError(f"independent fixture packages differ: {feature}")


def validate_failed_runtime(contract: dict[str, Any]) -> None:
    runtime = contract["batch_runtime"]
    attempt = ROOT / runtime["attempt_directory"]
    batch_trace_path = attempt / "batch-readback-trace.json"
    case_trace_path = attempt / "table-018-equal-row-height-4x3.hancom-2020-trace.json"
    if sha256_file(batch_trace_path) != runtime["batch_trace_sha256"]:
        raise ContractError("failed batch trace digest differs")
    if sha256_file(case_trace_path) != runtime["case_trace_sha256"]:
        raise ContractError("failed case trace digest differs")
    batch_trace = load_json(batch_trace_path)
    case_trace = load_json(case_trace_path)
    if (
        batch_trace.get("state") != "failed"
        or batch_trace.get("completed_case_count") != 0
        or case_trace.get("state") != "failed"
        or case_trace.get("failed_phase") != "open_input"
        or case_trace.get("error_code")
        != "TABLE_PROPERTIES_TARGET_READBACK_INPUT_OPEN_RETURNED_FALSE"
        or case_trace.get("input_unchanged") is not True
        or case_trace.get("output_saved") is not False
        or case_trace.get("render_pdf_saved") is not False
        or case_trace.get("watchdog", {}).get("remaining_hwp_process_count") != 0
    ):
        raise ContractError("failed runtime trace boundary differs")
    if (attempt / "table-018-equal-row-height-4x3.hancom-2020-readback.hwpx").exists():
        raise ContractError("failed runtime unexpectedly published HWPX output")
    retry = ROOT / runtime["clean_retry_directory"]
    if any(retry.glob("*.hancom-2020-*")) or (retry / "batch-readback-trace.json").exists():
        raise ContractError("clean retry directory is not clean")


def validate(contract_path: Path) -> None:
    contract = load_json(contract_path)
    validate_contract_shape(contract)
    source_lock_count = validate_source_locks(contract)
    cases = validate_cases(contract)
    validate_publications(contract, cases)
    validate_failed_runtime(contract)
    print(
        "schema=hwpx-agent.p06-09-table-layout-placement-target-contract-validation/v1 "
        f"state=pass features={len(cases)} source_locks={source_lock_count} "
        "fixture_builds=3 actual_hangul_2020=failed_open_input"
    )


def main() -> int:
    contract_path = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else DEFAULT_CONTRACT
    if len(sys.argv) > 2:
        print("usage: validate_table_layout_placement_target_v1_contract.py [contract]", file=sys.stderr)
        return 2
    try:
        validate(contract_path)
    except (ContractError, OSError, KeyError, TypeError, ValueError) as error:
        print(f"validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
