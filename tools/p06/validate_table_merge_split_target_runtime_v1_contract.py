#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = ROOT / "protocol/private/p06-table-merge-split-target-runtime-v1.json"
EXPECTED_SCHEMA = "hwpx-agent.p06-09-table-merge-split-target-runtime-contract/v1"
EXPECTED_MANIFEST_SCHEMA = "hwpx-agent.p06-09-table-merge-split-target-fixture/v1"
EXPECTED_MANIFEST_SHA256 = "682635284ae5686832dfd89598ea6c106c6b110119e0d54a8e8a24b63e9f3f97"
EXPECTED_INPUT_SHA256 = "6514a69b8c8c9d320bc19a032b16f2b71d59a38f164c690bc9e3d320a93320e5"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_CASES = {
    "TABLE-016": (
        "table.split_cell",
        "split",
        "table-016-split-cells-4x3.hwpx",
        "0459a05b8543edb2e05c9c0117f76df999c8543bad255d06d26d4b3b57388252",
        9,
        12,
    ),
    "TABLE-017": (
        "table.merge_cells",
        "merge",
        "table-017-merge-cells-4x3.hwpx",
        "0b5e3a68d2525fffa5aba7c728849c8ace604b54eb115fe5fddf808037316884",
        12,
        9,
    ),
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
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_object_pairs
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"cannot read JSON: {path}: {error}") from error
    if not isinstance(value, dict):
        raise ContractError(f"JSON root is not an object: {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_normalized_text(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ContractError(f"{label} is not lowercase SHA-256")
    return value


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise ContractError(f"{label} keys differ")


def validate_source_locks(contract: dict[str, Any]) -> int:
    if contract.get("source_lock_canonicalization") != "utf8_text_crlf_to_lf_sha256":
        raise ContractError("source lock canonicalization differs")
    locks = contract.get("source_locks")
    if not isinstance(locks, list) or len(locks) != 6:
        raise ContractError("source lock set differs")
    seen: set[str] = set()
    for index, lock in enumerate(locks):
        require_exact_keys(lock, {"path", "sha256"}, f"source lock {index}")
        relative = lock["path"]
        if not isinstance(relative, str) or relative in seen:
            raise ContractError(f"source lock {index} path differs")
        seen.add(relative)
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"source lock is not a regular file: {relative}")
        if sha256_normalized_text(path) != require_sha256(
            lock["sha256"], f"source lock {index}"
        ):
            raise ContractError(f"source lock digest differs: {relative}")
    return len(locks)


def validate_shape(contract: dict[str, Any]) -> None:
    require_exact_keys(
        contract,
        {
            "schema_version",
            "scope",
            "features",
            "source_lock_canonicalization",
            "source_locks",
            "exact_input",
            "fixture_publication",
            "cases",
            "batch_runtime",
            "gate_decision",
            "not_claimed",
        },
        "contract",
    )
    if contract.get("schema_version") != EXPECTED_SCHEMA or contract.get("features") != {
        feature: values[0] for feature, values in EXPECTED_CASES.items()
    }:
        raise ContractError("contract identity or features differ")
    exact_input = contract["exact_input"]
    if (
        exact_input.get("sha256") != EXPECTED_INPUT_SHA256
        or sha256_file(ROOT / exact_input["path"]) != EXPECTED_INPUT_SHA256
    ):
        raise ContractError("exact input differs")
    publication = contract["fixture_publication"]
    if (
        publication.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256
        or publication.get("case_count") != 2
        or publication.get("build_count") != 3
        or publication.get("write_mode") != "independent_create_new"
        or publication.get("byte_deterministic") is not True
        or publication.get("inverse_roundtrip_exact") is not True
    ):
        raise ContractError("fixture publication differs")
    runtime = contract["batch_runtime"]
    if (
        runtime.get("state") != "failed_open_input_timeout"
        or runtime.get("attempted_case_count") != 2
        or runtime.get("probed_case_count") != 0
        or runtime.get("completed_case_count") != 0
        or runtime.get("failed_case_count") != 2
        or runtime.get("failed_feature_ids") != list(EXPECTED_CASES)
        or runtime.get("failed_phase") != "open_input"
        or runtime.get("error_code") != "TABLE_PROPERTIES_TARGET_READBACK_TIMEOUT"
        or runtime.get("timeout_seconds_per_invocation") != 30
        or runtime.get("input_unchanged_count") != 2
        or runtime.get("output_absent_count") != 2
        or runtime.get("cleaned_process_count") != 2
        or runtime.get("remaining_hwp_process_count") != 0
        or not isinstance(runtime.get("failure_traces"), list)
        or len(runtime["failure_traces"]) != 2
    ):
        raise ContractError("batch runtime state differs")
    require_sha256(runtime.get("batch_trace_sha256"), "batch trace")
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
    cases = contract.get("cases")
    if not isinstance(cases, list) or len(cases) != 2:
        raise ContractError("case set differs")
    expected_keys = {
        "feature_id",
        "capability_id",
        "operation",
        "file",
        "sha256",
        "target_state_sha256",
        "target_grid_sha256",
        "target_content_sha256",
        "source_master_cell_count",
        "target_master_cell_count",
        "payload_block_count",
    }
    by_feature: dict[str, dict[str, Any]] = {}
    for case in cases:
        require_exact_keys(case, expected_keys, "contract case")
        feature = case["feature_id"]
        expected = EXPECTED_CASES.get(feature)
        if expected is None or feature in by_feature:
            raise ContractError(f"case identity differs: {feature}")
        if (
            case["capability_id"] != expected[0]
            or case["operation"] != expected[1]
            or case["file"] != expected[2]
            or case["sha256"] != expected[3]
            or case["source_master_cell_count"] != expected[4]
            or case["target_master_cell_count"] != expected[5]
            or case["payload_block_count"] != 9
        ):
            raise ContractError(f"case binding differs: {feature}")
        for field in (
            "sha256",
            "target_state_sha256",
            "target_grid_sha256",
            "target_content_sha256",
        ):
            require_sha256(case[field], f"{feature} {field}")
        by_feature[feature] = case
    return by_feature


def validate_publications(
    contract: dict[str, Any], cases: dict[str, dict[str, Any]]
) -> None:
    publication = contract["fixture_publication"]
    directories = [
        publication["directory"],
        publication["independent_retry_directory"],
        publication["current_source_rebuild_directory"],
    ]
    manifests: list[bytes] = []
    packages: dict[str, list[bytes]] = {feature: [] for feature in EXPECTED_CASES}
    for relative in directories:
        directory = ROOT / relative
        manifest_path = directory / publication["manifest_file"]
        if sha256_file(manifest_path) != EXPECTED_MANIFEST_SHA256:
            raise ContractError(f"fixture manifest digest differs: {relative}")
        manifests.append(manifest_path.read_bytes())
        manifest = load_json(manifest_path)
        if (
            manifest.get("schema_version") != EXPECTED_MANIFEST_SCHEMA
            or manifest.get("source_ancestor_sha256") != EXPECTED_INPUT_SHA256
            or manifest.get("inverse_roundtrip_exact") is not True
            or manifest.get("actual_hangul_2020") is not False
            or manifest.get("render") != "not_run"
            or manifest.get("automation") != "not_run"
            or manifest.get("differential") != "not_run"
        ):
            raise ContractError(f"fixture manifest state differs: {relative}")
        manifest_cases = manifest.get("cases")
        if not isinstance(manifest_cases, list) or len(manifest_cases) != 2:
            raise ContractError("fixture manifest cases differ")
        for feature, manifest_case in zip(EXPECTED_CASES, manifest_cases, strict=True):
            case = cases[feature]
            for field in (
                "feature_id",
                "capability_id",
                "operation",
                "file",
                "sha256",
                "target_state_sha256",
                "target_grid_sha256",
                "target_content_sha256",
                "source_master_cell_count",
                "target_master_cell_count",
                "payload_block_count",
            ):
                if manifest_case.get(field) != case[field]:
                    raise ContractError(f"fixture case differs: {feature}")
            package = (directory / case["file"]).read_bytes()
            if hashlib.sha256(package).hexdigest() != case["sha256"]:
                raise ContractError(f"fixture package digest differs: {feature}")
            packages[feature].append(package)
    if not all(value == manifests[0] for value in manifests[1:]):
        raise ContractError("fixture manifests are not byte-identical")
    for feature, values in packages.items():
        if not all(value == values[0] for value in values[1:]):
            raise ContractError(f"fixture packages differ: {feature}")


def validate_runtime(contract: dict[str, Any], cases: dict[str, dict[str, Any]]) -> None:
    runtime = contract["batch_runtime"]
    attempt = ROOT / runtime["attempt_directory"]
    batch_path = attempt / runtime["batch_trace_file"]
    if sha256_file(batch_path) != runtime["batch_trace_sha256"]:
        raise ContractError("batch trace digest differs")
    batch = load_json(batch_path)
    if (
        batch.get("schema_version")
        != "hwpx-agent.p06-09-table-merge-split-target-batch-readback-failure/v1"
        or batch.get("state") != "failed"
        or batch.get("fixture_manifest_sha256") != EXPECTED_MANIFEST_SHA256
        or batch.get("target") is not None
        or batch.get("attempted_case_count") != 2
        or batch.get("probed_case_count") != 0
        or batch.get("completed_case_count") != 0
        or batch.get("failed_case_count") != 2
        or batch.get("text_probes") != []
        or batch.get("cases") != []
        or batch.get("remaining_hwp_process_count") != 0
        or batch.get("actual_hangul_2020") is not True
    ):
        raise ContractError("batch trace state differs")
    failures = batch.get("failures")
    traces = runtime["failure_traces"]
    if not isinstance(failures, list) or len(failures) != 2:
        raise ContractError("batch failure set differs")
    for feature, failure, trace_contract in zip(
        EXPECTED_CASES, failures, traces, strict=True
    ):
        case = cases[feature]
        stem = Path(case["file"]).stem
        if (
            trace_contract.get("feature_id") != feature
            or trace_contract.get("case_id") != stem
        ):
            raise ContractError(f"failure trace identity differs: {feature}")
        trace_path = attempt / trace_contract["trace_file"]
        progress_path = attempt / trace_contract["progress_file"]
        if sha256_file(trace_path) != require_sha256(
            trace_contract.get("trace_sha256"), f"{feature} trace"
        ):
            raise ContractError(f"failure trace digest differs: {feature}")
        if sha256_file(progress_path) != require_sha256(
            trace_contract.get("progress_sha256"), f"{feature} progress"
        ):
            raise ContractError(f"failure progress digest differs: {feature}")
        if (
            failure.get("case_id") != stem
            or failure.get("feature_id") != feature
            or failure.get("stage") != "text_probe"
            or failure.get("child_exit_code") != 2
            or failure.get("error_code") != "TABLE_PROPERTIES_TARGET_READBACK_TIMEOUT"
            or failure.get("failed_phase") != "open_input"
            or failure.get("input_sha256") != case["sha256"]
            or failure.get("input_unchanged") is not True
            or failure.get("output_absent") is not True
            or failure.get("trace_path") != trace_contract["trace_file"]
            or failure.get("trace_sha256") != trace_contract["trace_sha256"]
            or failure.get("progress_path") != trace_contract["progress_file"]
            or failure.get("progress_sha256") != trace_contract["progress_sha256"]
            or failure.get("remaining_hwp_process_count") != 0
        ):
            raise ContractError(f"batch failure entry differs: {feature}")
        trace = load_json(trace_path)
        watchdog = trace.get("watchdog", {})
        if (
            trace.get("state") != "failed"
            or trace.get("input_sha256") != case["sha256"]
            or trace.get("input_unchanged") is not True
            or trace.get("output_saved") is not False
            or trace.get("failed_phase") != "open_input"
            or trace.get("error_code") != "TABLE_PROPERTIES_TARGET_READBACK_TIMEOUT"
            or watchdog.get("timeout_seconds") != 30
            or watchdog.get("timed_out") is not True
            or watchdog.get("cleaned_process_count") != 1
            or watchdog.get("cleanup_error_count") != 0
            or watchdog.get("remaining_hwp_process_count") != 0
            or watchdog.get("progress_valid") is not True
            or watchdog.get("progress_observed_phase") != "open_input"
        ):
            raise ContractError(f"failure runtime differs: {feature}")
        for suffix in (
            ".hancom-2020-text-probe-unused.hwpx",
            ".hancom-2020-readback.hwpx",
            ".hancom-2020-render.pdf",
            ".hancom-2020-trace.json",
        ):
            if (attempt / f"{stem}{suffix}").exists():
                raise ContractError(f"failure output exists: {feature}")
    clean = ROOT / runtime["clean_retry_directory"]
    if any(clean.glob("*.hancom-2020-*")) or any(clean.glob("batch-readback*.json")):
        raise ContractError("clean retry directory is not clean")


def validate(contract_path: Path) -> None:
    contract = load_json(contract_path)
    validate_shape(contract)
    source_lock_count = validate_source_locks(contract)
    cases = validate_cases(contract)
    validate_publications(contract, cases)
    validate_runtime(contract, cases)
    print(
        "schema=hwpx-agent.p06-09-table-merge-split-target-runtime-contract-validation/v1 "
        f"state=pass features={len(cases)} source_locks={source_lock_count} "
        "fixture_builds=3 actual_hangul_2020=failed_open_input_timeout"
    )


def main() -> int:
    contract_path = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else DEFAULT_CONTRACT
    if len(sys.argv) > 2:
        print(
            "usage: validate_table_merge_split_target_runtime_v1_contract.py [contract]",
            file=sys.stderr,
        )
        return 2
    try:
        validate(contract_path)
    except (ContractError, OSError, KeyError, TypeError, ValueError) as error:
        print(f"validation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
