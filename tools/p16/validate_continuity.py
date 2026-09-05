from __future__ import annotations

import json

import build_continuity_contract as builder
import continuity


def validate(contract: object) -> list[str]:
    if not isinstance(contract, dict):
        return ["contract.object"]
    errors: list[str] = []
    if contract.get("schema_version") != "hwpx-agent.p16-continuity-contract/v1" or contract.get("task") != "P16-05":
        errors.append("contract.identity")
    if contract.get("decision") != "pass_scoped_local_mcp_apps_bridge_component_e2e_actual_host_pending":
        errors.append("contract.decision")
    claims = contract.get("claims")
    if not isinstance(claims, dict) or any(value is not False for value in claims.values()):
        errors.append("contract.claims")
    locks = contract.get("source_locks")
    if not isinstance(locks, list) or len(locks) != len(builder.LOCAL_SOURCE_PATHS):
        errors.append("contract.source_locks")
    else:
        for item in locks:
            if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
                errors.append("contract.source_lock.fields")
                continue
            path = continuity.ROOT / item["path"]
            try:
                value = path.read_bytes()
            except OSError:
                errors.append(f"contract.source_lock.read:{item['path']}")
                continue
            if item["bytes"] != len(value) or item["sha256"] != continuity.sha256_bytes(value):
                errors.append(f"contract.source_lock.digest:{item['path']}")
    _, implementation_errors = continuity.validate_all()
    errors.extend(f"implementation:{error}" for error in implementation_errors)
    return sorted(set(errors))


def main() -> int:
    contract = json.loads(builder.CONTRACT_PATH.read_text(encoding="utf-8"))
    expected = builder.build_contract()
    errors = validate(contract)
    if contract != expected:
        errors.append("contract.generated")
    if errors:
        raise RuntimeError("P16 continuity validation failed: " + ",".join(sorted(set(errors))))
    print(
        "P16_CONTINUITY_VALIDATION_PASS "
        f"source_locks={len(contract['source_locks'])} "
        f"bundle_bytes={contract['bundles']['resource']['bytes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
