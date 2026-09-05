from __future__ import annotations

import json
from typing import Any

import build_widget_shell_contract as builder
import widget_shell as shell


def validate(contract: Any) -> list[str]:
    errors: list[str] = []
    bundle, source_errors = shell.validate_all()
    errors.extend(source_errors)
    if not isinstance(contract, dict):
        return sorted(set(errors + ["contract.object"]))
    try:
        expected = builder.build_contract()
    except (OSError, ValueError):
        expected = None
        errors.append("contract.sources")
    if expected is not None and contract != expected:
        errors.append("contract.exact")
    if contract.get("decision") != "pass_scoped_local_widget_shell_component":
        errors.append("contract.decision")
    resource = contract.get("resource")
    if (
        not isinstance(resource, dict)
        or resource.get("uri") != "ui://hwpx-agent/document-work/v1.html"
        or resource.get("mime_type") != "text/html;profile=mcp-app"
        or resource.get("csp") != {"connectDomains": [], "frameDomains": None, "resourceDomains": []}
        or resource.get("bundle") != bundle
    ):
        errors.append("contract.resource")
    boundary = contract.get("public_tool_boundary")
    if not isinstance(boundary, dict) or boundary.get("tool_count") != 18 or boundary.get("ui_resource_metadata_count") != 0:
        errors.append("contract.public_tool_boundary")
    lifecycle = contract.get("lifecycle")
    if not isinstance(lifecycle, dict) or any(
        lifecycle.get(key) is not expected_value
        for key, expected_value in {
            "handlers_registered_before_connect": True,
            "approval_pending_is_expected": True,
            "model_input_cannot_set_ready": True,
            "approved_input_required_before_result": True,
            "result_bound_to_approved_surface_project": True,
            "strict_bridge": True,
            "unsafe_eval_allowed": False,
            "teardown_idempotent": True,
        }.items()
    ):
        errors.append("contract.lifecycle")
    claims = contract.get("claims")
    if not isinstance(claims, dict):
        errors.append("contract.claims")
    else:
        for key in (
            "actual_chatgpt_host_render_tested", "developer_mode_tested", "registered_plugin_tested",
            "hangul_or_com_invoked", "file_transfer_tested", "public_or_production_ready",
            "hangul_2022_2024_or_other_pc_tested",
        ):
            if claims.get(key) is not False:
                errors.append(f"contract.claims.{key}")
    return sorted(set(errors))


def main() -> int:
    try:
        contract = json.loads(builder.CONTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(json.dumps({"decision": "FAIL", "errors": ["contract.read"]}, sort_keys=True))
        return 1
    errors = validate(contract)
    if errors:
        print(json.dumps({"decision": "FAIL", "errors": errors}, sort_keys=True))
        return 1
    print(json.dumps({
        "decision": "PASS",
        "bundle_bytes": contract["resource"]["bundle"]["bytes"],
        "requirements": len(contract["requirements"]),
        "source_locks": len(contract["source_locks"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
