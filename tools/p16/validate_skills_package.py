from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import build_skills_package_contract as builder
import skills_package as package


def validate(contract: Any) -> list[str]:
    errors: list[str] = []
    entries, component_errors = package.read_component_entries()
    _, routing_errors = package.load_routing_cases()
    errors.extend(component_errors)
    errors.extend(routing_errors)
    if not isinstance(contract, dict):
        return sorted(set(errors + ["contract.object"]))
    try:
        expected = builder.build_contract()
    except (OSError, ValueError):
        expected = None
        errors.append("contract.sources")
    if expected is not None and contract != expected:
        errors.append("contract.exact")
    if contract.get("decision") != "pass_scoped_local_skills_component_and_deterministic_routing":
        errors.append("contract.decision")
    component = contract.get("component")
    if not isinstance(component, dict) or component.get("skill_count") != 9 or component.get("entries") != package.component_snapshot(entries):
        errors.append("contract.component")
    routing = contract.get("routing_evaluation")
    if not isinstance(routing, dict) or routing.get("case_count") != 36 or routing.get("passed_count") != 36:
        errors.append("contract.routing")
    claims = contract.get("claims")
    if not isinstance(claims, dict):
        errors.append("contract.claims")
    else:
        for key in (
            "chatgpt_host_routing_tested", "registered_plugin_tested", "developer_mode_tested",
            "direct_print_supported", "hangul_or_com_invoked", "public_or_production_ready",
        ):
            if claims.get(key) is not False:
                errors.append(f"contract.claims.{key}")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the P16-03 skills component and contract.")
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--composed-plugin", action="store_true")
    args = parser.parse_args()
    if args.composed_plugin and args.archive is None:
        print(json.dumps({"decision": "FAIL", "errors": ["archive.required"]}, sort_keys=True))
        return 1
    try:
        contract = json.loads(builder.CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(json.dumps({"decision": "FAIL", "errors": ["contract.read"]}, sort_keys=True))
        return 1
    errors = validate(contract)
    if args.archive is not None:
        errors.extend(package.validate_archive(args.archive, composed_plugin=args.composed_plugin))
    if errors:
        print(json.dumps({"decision": "FAIL", "errors": sorted(set(errors))}, sort_keys=True))
        return 1
    print(json.dumps({"decision": "PASS", "skills": 9, "routing_cases": 36, "source_locks": len(contract["source_locks"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
