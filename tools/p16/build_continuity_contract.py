from __future__ import annotations

import argparse
from pathlib import Path

import continuity


ROOT = continuity.ROOT
CONTRACT_PATH = ROOT / "implementation/p16/p16-continuity-contract-v1.json"
LOCAL_SOURCE_PATHS = (
    "implementation/p16/P16-05_CONTINUITY_DESIGN_SPEC.md",
    "implementation/p16/P16-05_CONTINUITY_POLICY.md",
    "implementation/p16/P16-05_VISUAL_QA.md",
    "implementation/p16/p16-continuity-policy-v1.json",
    "implementation/p16/design/p16-05-continuity-concept.png",
    "implementation/p16/visual-qa/p16-05-desktop-confirm.png",
    "implementation/p16/visual-qa/p16-05-desktop-conflict.png",
    "implementation/p16/visual-qa/p16-05-desktop-dark-saved.png",
    "implementation/p16/visual-qa/p16-05-desktop-ready.png",
    "implementation/p16/visual-qa/p16-05-narrow-confirm.png",
    "implementation/p16/visual-qa/p16-05-narrow-conflict.png",
    "implementation/p16/visual-qa/p16-05-narrow-ready.png",
    "implementation/p16/p16-widget-shell-contract-v1.json",
    "protocol/mcp/p15-public-tools-v1.json",
    "web/plugin-widget/scripts/build-continuity-widget.mjs",
    "web/plugin-widget/src/continuity-component.tsx",
    "web/plugin-widget/src/continuity-controller.test.ts",
    "web/plugin-widget/src/continuity-controller.ts",
    "web/plugin-widget/src/continuity-e2e-host.ts",
    "web/plugin-widget/src/continuity-mcp-app-port.ts",
    "web/plugin-widget/src/continuity-model.test.ts",
    "web/plugin-widget/src/continuity-model.ts",
    "web/plugin-widget/src/continuity-preview.tsx",
    "web/plugin-widget/src/continuity-resource.test.ts",
    "web/plugin-widget/src/continuity-resource.ts",
    "web/plugin-widget/src/continuity-styles.css",
    "web/plugin-widget/src/continuity-ui.test.tsx",
    "web/plugin-widget/src/continuity-ui.tsx",
    "tools/p16/continuity.py",
    "tools/p16/build_continuity_contract.py",
    "tools/p16/run_continuity_checks.py",
    "tools/p16/run_continuity_e2e.py",
    "tools/p16/validate_continuity.py",
    "tools/p16/tests/test_continuity.py",
)


def source_lock(path: Path) -> dict[str, object]:
    value = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(value),
        "sha256": continuity.sha256_bytes(value),
    }


def build_contract() -> dict[str, object]:
    bundles, errors = continuity.validate_all()
    if errors or bundles is None:
        raise RuntimeError("continuity validation failed: " + ",".join(errors))
    return {
        "schema_version": "hwpx-agent.p16-continuity-contract/v1",
        "task": "P16-05",
        "scope": "current_pc_local_mcp_apps_bridge_component",
        "decision": "pass_scoped_local_mcp_apps_bridge_component_e2e_actual_host_pending",
        "requirements": list(continuity.EXPECTED_REQUIREMENTS),
        "predecessor": {
            "path": continuity.PREDECESSOR_PATH.relative_to(ROOT).as_posix(),
            "sha256": continuity.EXPECTED_PREDECESSOR_SHA256,
        },
        "catalog": {
            "path": continuity.CATALOG_PATH.relative_to(ROOT).as_posix(),
            "sha256": continuity.EXPECTED_CATALOG_SHA256,
            "tools": sorted(continuity.EXPECTED_CALLS),
        },
        "bundles": bundles,
        "limits": {
            "snapshot_revisions": 12,
            "rendered_revisions": 6,
            "primary_actions": 1,
            "secondary_actions": 1,
            "minimum_css_width": 320,
        },
        "e2e": {
            "runner": "tools/p16/run_continuity_e2e.py",
            "bridge": "real_ext_apps_appbridge_postmessage_iframe",
            "call_count": 3,
            "call_order": ["project_open", "project_history", "project_checkpoint"],
            "evidence_level": "local_browser_component_not_actual_chatgpt_or_codex_host",
        },
        "claims": {
            "actual_chatgpt_or_codex_host_tested": False,
            "developer_mode_tested": False,
            "registered_plugin_tested": False,
            "remote_mcp_tested": False,
            "hangul_or_com_invoked": False,
            "file_transfer_tested": False,
            "public_or_production_ready": False,
            "hangul_2022_2024_or_other_pc_tested": False,
        },
        "source_locks": [source_lock(ROOT / relative) for relative in LOCAL_SOURCE_PATHS],
        "next_task": "P16-06 Plan/diff UI",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the P16-05 continuity contract.")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = continuity.canonical_json_bytes(build_contract())
    if args.check:
        if not CONTRACT_PATH.is_file() or CONTRACT_PATH.read_bytes() != expected:
            raise RuntimeError("P16 continuity contract is stale")
    else:
        CONTRACT_PATH.write_bytes(expected)
    print(f"P16_CONTINUITY_CONTRACT_PASS source_locks={len(LOCAL_SOURCE_PATHS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
