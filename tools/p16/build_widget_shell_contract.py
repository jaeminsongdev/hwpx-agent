from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import widget_shell as shell


ROOT = shell.ROOT
CONTRACT_PATH = ROOT / "implementation/p16/p16-widget-shell-contract-v1.json"
LOCAL_SOURCE_PATHS = (
    "implementation/p16/P16-04_WIDGET_DESIGN_SPEC.md",
    "implementation/p16/P16-04_WIDGET_SHELL_POLICY.md",
    "implementation/p16/P16-04_VISUAL_QA.md",
    "implementation/p16/p16-widget-shell-policy-v1.json",
    "implementation/p16/design/p16-04-widget-shell-desktop-concept.png",
    "implementation/p16/design/p16-04-widget-shell-narrow-concept.png",
    "implementation/p16/visual-qa/p16-04-desktop-approval.png",
    "implementation/p16/visual-qa/p16-04-desktop-dark-ready.png",
    "implementation/p16/visual-qa/p16-04-desktop-error.png",
    "implementation/p16/visual-qa/p16-04-desktop-ready.png",
    "implementation/p16/visual-qa/p16-04-narrow-approval.png",
    "implementation/p16/visual-qa/p16-04-narrow-error.png",
    "implementation/p16/visual-qa/p16-04-narrow-ready.png",
    "package.json",
    "pnpm-lock.yaml",
    "pnpm-workspace.yaml",
    "implementation/p15/p15-inspector-staging-contract-v1.json",
    "tools/p15/validate_inspector_staging_contract.py",
    "tools/p15/tests/test_inspector_staging_contract.py",
    "web/plugin-widget/package.json",
    "web/plugin-widget/tsconfig.json",
    "web/plugin-widget/scripts/build-widget.mjs",
    "web/plugin-widget/src/bridge.ts",
    "web/plugin-widget/src/bridge.test.ts",
    "web/plugin-widget/src/component.tsx",
    "web/plugin-widget/src/global.d.ts",
    "web/plugin-widget/src/host-extensions.ts",
    "web/plugin-widget/src/host-extensions.test.ts",
    "web/plugin-widget/src/index.ts",
    "web/plugin-widget/src/index.test.ts",
    "web/plugin-widget/src/mcp-app-port.ts",
    "web/plugin-widget/src/model.ts",
    "web/plugin-widget/src/model.test.ts",
    "web/plugin-widget/src/preview.css",
    "web/plugin-widget/src/preview.tsx",
    "web/plugin-widget/src/resource.ts",
    "web/plugin-widget/src/resource.test.ts",
    "web/plugin-widget/src/styles.css",
    "web/plugin-widget/src/ui.tsx",
    "web/plugin-widget/src/ui.test.tsx",
    "tools/p16/widget_shell.py",
    "tools/p16/build_widget_shell_contract.py",
    "tools/p16/validate_widget_shell.py",
    "tools/p16/run_widget_shell_checks.py",
    "tools/p16/tests/test_widget_shell.py",
)


def sha256_file(path: Path) -> str:
    return shell.sha256_bytes(path.read_bytes())


def build_contract() -> dict[str, Any]:
    bundle, errors = shell.validate_all()
    if errors or bundle is None:
        raise ValueError(",".join(errors or ["bundle.missing"]))
    predecessor_sha = sha256_file(shell.PREDECESSOR_PATH)
    if predecessor_sha != shell.EXPECTED_PREDECESSOR_SHA256:
        raise ValueError("predecessor.digest")
    policy = json.loads(shell.POLICY_PATH.read_text(encoding="utf-8"))
    return {
        "schema_version": "hwpx-agent.p16-widget-shell-contract/v1",
        "task": "P16-04",
        "scope": "current_pc_hangul_2020_local_widget_shell_component",
        "decision": "pass_scoped_local_widget_shell_component",
        "predecessor": {
            "path": shell.PREDECESSOR_PATH.relative_to(ROOT).as_posix(),
            "sha256": predecessor_sha,
        },
        "official_source_contract": {
            "path": "implementation/p16/p16-official-source-contract-v1.json",
            "sha256": sha256_file(ROOT / "implementation/p16/p16-official-source-contract-v1.json"),
        },
        "p15_staging_compatibility": {
            "audited_revision": "7ea2f84c244fe5bbd7926ba3f176dc5acafcf624",
            "contract_path": "implementation/p15/p15-inspector-staging-contract-v1.json",
            "contract_sha256": sha256_file(
                ROOT / "implementation/p15/p15-inspector-staging-contract-v1.json"
            ),
            "superseded_paths": [
                "package.json",
                "pnpm-lock.yaml",
                "pnpm-workspace.yaml",
                "tools/p15/validate_inspector_staging_contract.py",
                "tools/p15/tests/test_inspector_staging_contract.py",
            ],
        },
        "policy": {
            "path": shell.POLICY_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(shell.POLICY_PATH),
        },
        "resource": {
            "uri": policy["resource_uri"],
            "mime_type": policy["mime_type"],
            "csp": policy["csp"],
            "render_tool": policy["render_tool"],
            "display_mode": policy["display_mode"],
            "bundle": bundle,
        },
        "dependencies": policy["dependencies"],
        "design_sources": policy["design_sources"],
        "visual_qa": policy["visual_qa"],
        "public_tool_boundary": {
            "path": shell.CATALOG_PATH.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(shell.CATALOG_PATH),
            "tool_count": 18,
            "ui_resource_metadata_count": 0,
            "continue_tool": "project_open",
            "continue_tool_read_only": True,
        },
        "lifecycle": {
            "handlers_registered_before_connect": True,
            "approval_pending_is_expected": True,
            "model_input_cannot_set_ready": True,
            "approved_input_required_before_result": True,
            "result_bound_to_approved_surface_project": True,
            "strict_bridge": True,
            "unsafe_eval_allowed": False,
            "teardown_idempotent": True,
            "host_detection": "capability_methods_only_no_hostname_branch",
        },
        "requirements": list(shell.EXPECTED_REQUIREMENTS),
        "claims": {
            "react_widget_shell_implemented": True,
            "mcp_apps_bridge_implemented": True,
            "versioned_self_contained_resource_implemented": True,
            "closed_csp_component_tested": True,
            "responsive_concept_sources_locked": True,
            "p15_tools_remain_ui_independent": True,
            "actual_chatgpt_host_render_tested": False,
            "developer_mode_tested": False,
            "registered_plugin_tested": False,
            "hangul_or_com_invoked": False,
            "file_transfer_tested": False,
            "public_or_production_ready": False,
            "hangul_2022_2024_or_other_pc_tested": False,
        },
        "source_locks": [
            {"path": relative, "sha256": sha256_file(ROOT / relative)}
            for relative in LOCAL_SOURCE_PATHS
        ],
        "next_task": "P16-05 core document workflow UI",
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
    parser = argparse.ArgumentParser(description="Build the P16-04 widget shell contract.")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        expected = shell.canonical_json_bytes(build_contract())
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
    contract = json.loads(expected)
    print(json.dumps({
        "decision": "PASS",
        "bundle_bytes": contract["resource"]["bundle"]["bytes"],
        "source_locks": len(contract["source_locks"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
