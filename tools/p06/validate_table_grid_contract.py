#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_RELATIVE = PurePosixPath("protocol/private/p06-table-grid-v1.json")
EXPECTED_SOURCE_PATHS = {
    "docs/03_document_model/06_table_model.md",
    "docs/04_feature_catalog/contracts/07_table_contracts.md",
    "docs/09_roadmap/P06_table_engine.md",
    "docs/12_implementation_guides/05_page_table_layout_algorithms.md",
}
EXPECTED_DEFAULT_LIMITS = {
    "rows": 10_000,
    "columns": 1_024,
    "slots": 1_000_000,
    "master_cells": 1_000_000,
    "identifier_bytes": 256,
    "serialized_bytes": 32 * 1024 * 1024,
}
IMPLEMENTATION_MARKERS = {
    "crates/domain-ir/src/table_grid.rs": (
        'pub const TABLE_GRID_SCHEMA_VERSION: &str = "hwpx-agent.table-grid/v1";',
        "pub struct TableGrid",
        "pub struct TableCellSpan",
        "pub fn from_covered_slots",
        "pub fn master_cell_at",
        "pub fn canonical_json",
        "table_grid_non_rectangular_span",
        "table_grid_overlapping_span",
        "table_grid_uncovered_slot",
    ),
    "crates/domain-ir/src/lib.rs": (
        "mod table_grid;",
        "TableGridError",
        "TableGridLimits",
    ),
    "crates/domain-ir/tests/table_grid.rs": (
        "fixed_seed_partition_corpus_preserves_all_grid_properties",
        "explicit_coverage_requires_one_complete_rectangle",
        "gaps_overlaps_bounds_and_identifiers_fail_closed",
    ),
}


class DuplicateKeyError(ValueError):
    pass


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def load_contract(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    if not isinstance(value, dict):
        raise ValueError("contract root")
    return value


def bounded_file(root: Path, relative: str) -> Path:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise ValueError("unbounded path")
    path = root.joinpath(*candidate.parts)
    resolved_root = root.resolve()
    resolved_path = path.resolve()
    if not resolved_path.is_relative_to(resolved_root) or path.is_symlink() or not path.is_file():
        raise ValueError("invalid bounded file")
    return path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract_path = bounded_file(root, CONTRACT_RELATIVE.as_posix())
        contract = load_contract(contract_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return result(errors=["contract_json_or_path"], source_locks=0, implementation_files=0)

    if contract.get("schema_version") != "hwpx-agent.table-grid-contract/v1":
        errors.append("contract_schema_version")
    if contract.get("model_schema_version") != "hwpx-agent.table-grid/v1":
        errors.append("model_schema_version")
    if contract.get("scope") != "p06_01_pure_logical_grid_current_pc_local_development":
        errors.append("scope")
    if contract.get("default_limits") != EXPECTED_DEFAULT_LIMITS:
        errors.append("default_limits")
    if contract.get("migration") != "protocol/migrations/p06-table-grid-v0-to-v1.md":
        errors.append("migration_reference")

    source_locks = contract.get("source_locks")
    source_count = len(source_locks) if isinstance(source_locks, list) else 0
    declared_paths: set[str] = set()
    if not isinstance(source_locks, list):
        errors.append("source_locks_shape")
    else:
        for entry in source_locks:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                errors.append("source_lock_shape")
                continue
            relative = entry.get("path")
            expected_digest = entry.get("sha256")
            if not isinstance(relative, str) or not isinstance(expected_digest, str):
                errors.append("source_lock_types")
                continue
            if relative in declared_paths:
                errors.append("source_lock_duplicate")
                continue
            declared_paths.add(relative)
            try:
                path = bounded_file(root, relative)
            except (OSError, ValueError):
                errors.append("source_lock_path")
                continue
            if sha256(path) != expected_digest:
                errors.append("source_lock_digest")
        if declared_paths != EXPECTED_SOURCE_PATHS:
            errors.append("source_lock_paths_exact")

    try:
        migration = bounded_file(root, "protocol/migrations/p06-table-grid-v0-to-v1.md").read_text(
            encoding="utf-8"
        )
        for marker in ("hwpx-agent.table-grid/v1", "DocumentGraph", "fail closed", "P06-02"):
            if marker not in migration:
                errors.append("migration_marker")
    except (OSError, ValueError):
        errors.append("migration_path")

    implementation_files = 0
    for relative, markers in IMPLEMENTATION_MARKERS.items():
        try:
            source = bounded_file(root, relative).read_text(encoding="utf-8")
        except (OSError, ValueError):
            errors.append("implementation_path")
            continue
        implementation_files += 1
        if any(marker not in source for marker in markers):
            errors.append("implementation_marker")

    not_claimed = contract.get("not_claimed")
    if not isinstance(not_claimed, dict) or not not_claimed or any(not value is False for value in not_claimed.values()):
        errors.append("not_claimed")

    return result(
        errors=sorted(errors),
        source_locks=source_count,
        implementation_files=implementation_files,
    )


def result(*, errors: list[str], source_locks: int, implementation_files: int) -> dict[str, Any]:
    return {
        "schema_version": "hwpx-agent.p06-table-grid-validation/v1",
        "state": "pass" if not errors else "fail",
        "source_locks": source_locks,
        "implementation_files": implementation_files,
        "errors": errors,
    }


def main() -> int:
    validation = validate()
    print(json.dumps(validation, ensure_ascii=False, sort_keys=True))
    if validation["errors"]:
        return 1
    print("P06_TABLE_GRID_CONTRACT_PASS source_locks=4 implementation_files=3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
