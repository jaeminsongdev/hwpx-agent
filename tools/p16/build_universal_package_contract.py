from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import universal_package as package


ROOT = package.ROOT
CONTRACT_PATH = ROOT / "implementation/p16/p16-universal-package-contract-v1.json"
PREDECESSOR_PATH = ROOT / "implementation/p16/p16-official-source-contract-v1.json"
LOCAL_SOURCE_PATHS = (
    "implementation/p16/P16-02_UNIVERSAL_PACKAGE_POLICY.md",
    "plugins/hwpx-agent/.codex-plugin/plugin.json",
    "plugins/hwpx-agent/README.md",
    "plugins/hwpx-agent/assets/icon.png",
    "plugins/hwpx-agent/assets/logo.png",
    "tools/p16/universal_package.py",
    "tools/p16/build_universal_package.py",
    "tools/p16/build_universal_package_contract.py",
    "tools/p16/validate_universal_package.py",
    "tools/p16/run_universal_package_checks.py",
    "tools/p16/tests/test_universal_package.py",
)


def sha256_file(path: Path) -> str:
    return package.sha256_bytes(path.read_bytes())


def build_contract() -> dict[str, Any]:
    entries, errors = package.read_base_entries()
    if errors:
        raise ValueError(",".join(errors))
    predecessor_sha = sha256_file(PREDECESSOR_PATH)
    if predecessor_sha != "dd46a4b41f27fa5dfbd3c52e8b6ed7bc2447cddb1bac9cac516b6c36d0dadb2f":
        raise ValueError("predecessor.digest")
    return {
        "schema_version": "hwpx-agent.p16-universal-package-contract/v1",
        "task": "P16-02",
        "scope": "current_pc_hangul_2020_local_unregistered_package_base",
        "decision": "implementation_ready_actual_registration_pending",
        "predecessor": {
            "path": PREDECESSOR_PATH.relative_to(ROOT).as_posix(),
            "sha256": predecessor_sha,
        },
        "package": {
            "root": package.PACKAGE_ROOT.relative_to(ROOT).as_posix(),
            "entry_count": len(entries),
            "total_bytes": sum(len(value) for value in entries.values()),
            "entries": package.base_snapshot(entries),
            "archive_policy": "sorted_fixed_metadata_zip_stored_atomic_no_overwrite",
        },
        "requirements": ["P16-R11", "P16-R12", "P16-R13", "P16-R14", "P16-R34"],
        "registration": {
            "state": "unverified",
            "registered_app_id": None,
            "tracked_app_manifest_present": False,
            "placeholder_allowed": False,
            "actual_receipt_required": True,
            "receipt_schema": "hwpx-agent.p16-registration-receipt/v1",
            "artifact_root": "artifacts/p16",
        },
        "claims": {
            "base_manifest_valid": True,
            "base_assets_valid": True,
            "deterministic_unregistered_archive_tested": True,
            "source_preserved": True,
            "registered_app_mapping_implemented": False,
            "connected_plugin_tested": False,
            "developer_mode_tested": False,
            "public_or_production_ready": False,
            "hangul_or_com_invoked": False,
        },
        "source_locks": [
            {"path": relative, "sha256": sha256_file(ROOT / relative)}
            for relative in LOCAL_SOURCE_PATHS
        ],
        "next_task": "P16-02 actual registration receipt; P16-03 skills may proceed independently",
    }


def atomic_write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the P16-02 universal package contract.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = package.canonical_json_bytes(build_contract())
    except (OSError, ValueError) as error:
        print(json.dumps({"decision": "FAIL", "errors": [str(error)]}, sort_keys=True))
        return 1
    if args.write:
        atomic_write(CONTRACT_PATH, expected)
        print(json.dumps({"decision": "PASS", "contract": CONTRACT_PATH.relative_to(ROOT).as_posix()}, sort_keys=True))
        return 0
    if not CONTRACT_PATH.is_file() or CONTRACT_PATH.read_bytes() != expected:
        print(json.dumps({"decision": "FAIL", "errors": ["contract.drift"]}, sort_keys=True))
        return 1
    print(json.dumps({"decision": "PASS", "entries": len(package.BASE_ENTRIES), "source_locks": len(LOCAL_SOURCE_PATHS)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
