from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_universal_package_contract as builder  # noqa: E402
import universal_package as package  # noqa: E402


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(contract: Any) -> list[str]:
    errors: list[str] = []
    entries, package_errors = package.read_base_entries()
    errors.extend(package_errors)
    if not isinstance(contract, dict):
        return sorted(set(errors + ["contract.object"]))
    try:
        expected = builder.build_contract()
    except (OSError, ValueError):
        expected = None
        errors.append("contract.sources")
    if expected is not None and contract != expected:
        errors.append("contract.exact")
    if contract.get("decision") != "implementation_ready_actual_registration_pending":
        errors.append("contract.decision")
    registration = contract.get("registration")
    if not isinstance(registration, dict):
        errors.append("contract.registration")
    else:
        if registration.get("state") != "unverified" or registration.get("registered_app_id") is not None:
            errors.append("contract.registration.state")
        if registration.get("tracked_app_manifest_present") is not False:
            errors.append("contract.registration.tracked_app_manifest_present")
        if registration.get("placeholder_allowed") is not False or registration.get("actual_receipt_required") is not True:
            errors.append("contract.registration.admission")
    claims = contract.get("claims")
    if not isinstance(claims, dict):
        errors.append("contract.claims")
    else:
        for key in (
            "registered_app_mapping_implemented",
            "connected_plugin_tested",
            "developer_mode_tested",
            "public_or_production_ready",
            "hangul_or_com_invoked",
        ):
            if claims.get(key) is not False:
                errors.append(f"contract.claims.{key}")
    if entries and contract.get("package", {}).get("entries") != package.base_snapshot(entries):
        errors.append("contract.package.snapshot")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the P16-02 universal package base and contract.")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--registered", action="store_true")
    args = parser.parse_args()
    if args.registered and args.archive is None:
        print(json.dumps({"decision": "FAIL", "errors": ["archive.required"]}, sort_keys=True))
        return 1
    try:
        contract = read_json(builder.CONTRACT_PATH)
    except (OSError, json.JSONDecodeError):
        print(json.dumps({"decision": "FAIL", "errors": ["contract.read"]}, sort_keys=True))
        return 1
    errors = validate(contract)
    if args.archive is not None:
        errors.extend(package.validate_archive(args.archive, registered=args.registered))
    if errors:
        print(json.dumps({"decision": "FAIL", "errors": errors}, sort_keys=True))
        return 1
    print(
        json.dumps(
            {
                "decision": "PASS",
                "entries": len(package.BASE_ENTRIES),
                "registered": args.registered,
                "source_locks": len(contract["source_locks"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
