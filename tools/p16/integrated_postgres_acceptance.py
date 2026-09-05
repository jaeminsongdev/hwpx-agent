"""Exact actual PostgreSQL successor for the qualified MAIN/P16 merge candidate."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BASE = "implementation/p16/qualification/main-9cc1-p16-62542-postgres-v1"
CONTRACT_PATH = f"{BASE}/contract.json"
RECEIPT_PATH = f"{BASE}/current-db.json"
RECEIPT_SHA256 = "dac4957bacee0cde7ee59f85cffcc71cfe00dfa412c3a0d151572e91a889e117"
ORIGINAL_RECEIPT_SHA256 = "7b42b454571db49d4a71641b9ce07c46c0c7ae5e0f739acc5c4ca0a73b0c0e98"
RUN_ID = "20dff2d03ef04bb39abce731d9331565"
SOURCE_CONTRACT = "implementation/p16/qualification/main-9cc1-p16-62542-v1/contract.json"
SOURCE_CONTRACT_SHA256 = "890c72ac61c2c7d4e871958ff684de513fe1fe7e888e1264cba0eaec4bab52df"
GUARD_PATHS = (
    "tools/p16/integrated_postgres_acceptance.py",
    "tools/p16/tests/test_integrated_postgres_acceptance.py",
    "implementation/p16/P16-06_MAIN_INTEGRATED_POSTGRES_ACCEPTANCE.md",
)


class QualificationError(ValueError):
    """Closed qualification failure without candidate source or private data."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise QualificationError(code)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load(name: str, filename: str) -> Any:
    path = Path(__file__).resolve().with_name(filename)
    specification = importlib.util.spec_from_file_location(name, path)
    require(specification is not None and specification.loader is not None, "module.load")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def load_source_validator() -> Any:
    return load("p16_main_source_for_actual_postgres", "integrated_source_qualification.py")


def load_postgres_validator() -> Any:
    return load("p16_postgres_for_integrated_acceptance", "postgres_artifact_qualification.py")


def verification_paths(root: Path = ROOT) -> set[str]:
    source = load_source_validator()
    postgres = load_postgres_validator()
    paths = set(source.verification_paths(root))
    paths.update((SOURCE_CONTRACT, RECEIPT_PATH, CONTRACT_PATH, *postgres.RUNTIME_PATHS, *GUARD_PATHS))
    return paths


def expected_contract(root: Path) -> dict[str, Any]:
    source = load_source_validator()
    postgres = load_postgres_validator()
    source_raw = postgres.read_bounded(root, SOURCE_CONTRACT, 128 * 1024)
    require(digest(source_raw) == SOURCE_CONTRACT_SHA256, "source_contract.digest")
    source.verified_replacements(root)

    receipt_raw = postgres.read_bounded(root, RECEIPT_PATH, 64 * 1024)
    require(digest(receipt_raw) == RECEIPT_SHA256, "receipt.digest")
    receipt = postgres.json_value(receipt_raw)
    sources = postgres.validate_receipt(receipt, RUN_ID)
    require(set(sources) == set(postgres.RUNTIME_PATHS), "receipt.sources")
    for relative in postgres.RUNTIME_PATHS:
        require(digest(postgres.read_bounded(root, relative)) == sources[relative], "source.runtime_digest")

    return {
        "schema_version": "hwpx-agent.p16-main-integrated-postgres-acceptance/v1",
        "qualification_id": "p16.main.9cc1db3.62542b0.postgres.v1",
        "scope": "current_pc_merged_source_actual_postgres_only",
        "source_qualification": {
            "path": SOURCE_CONTRACT,
            "sha256": SOURCE_CONTRACT_SHA256,
        },
        "evidence": {
            "path": RECEIPT_PATH,
            "sha256": RECEIPT_SHA256,
            "original_receipt_sha256": ORIGINAL_RECEIPT_SHA256,
            "run_id": RUN_ID,
            "probe_sha256": receipt["probe_sha256"],
        },
        "runtime_sources": [
            {"path": relative, "sha256": sources[relative]}
            for relative in postgres.RUNTIME_PATHS
        ],
        "guard_sources": [
            {"path": relative, "sha256": digest(postgres.read_bounded(root, relative))}
            for relative in GUARD_PATHS
        ],
        "claims": {
            "actual_integrated_postgres_retested": True,
            "owned_resources_removed": True,
            "p15_phase_complete": False,
            "p16_phase_complete": False,
            "actual_hangul": False,
            "registered_host": False,
            "production": False,
            "other_pc_or_version": False,
        },
    }


def verified_acceptance(root: Path) -> dict[str, Any]:
    try:
        postgres = load_postgres_validator()
        contract = postgres.json_value(postgres.read_bounded(root, CONTRACT_PATH, 128 * 1024))
        expected = expected_contract(root)
        require(postgres.exact(contract, expected), "contract.exact")
        return expected
    except (OSError, KeyError, TypeError, RecursionError) as error:
        raise QualificationError("qualification.unavailable") from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write:
            expected = expected_contract(ROOT)
            destination = ROOT / CONTRACT_PATH
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("xb") as stream:
                stream.write((json.dumps(expected, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        contract = verified_acceptance(ROOT)
    except (QualificationError, OSError, KeyError, TypeError) as error:
        code = str(error) if isinstance(error, QualificationError) else "qualification.unavailable"
        print(json.dumps({"decision": "FAIL", "code": code}, sort_keys=True))
        return 1
    print(json.dumps({
        "decision": "PASS",
        "scope": contract["scope"],
        "runtime_sources": len(contract["runtime_sources"]),
        "actual_integrated_postgres_retested": True,
        "phase_complete": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
