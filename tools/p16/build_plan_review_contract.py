from __future__ import annotations
import argparse
from pathlib import Path
from typing import Any
import plan_review
import continuity

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"implementation/p16/p16-plan-review-contract-v1.json"
LOCAL_SOURCES=(
    "crates/domain-ir/src/lib.rs", "crates/domain-ir/src/semantic_diff.rs",
    "crates/domain-ir/src/semantic_summary.rs", "crates/domain-ir/tests/semantic_diff.rs",
    "crates/domain-ir/tests/semantic_summary.rs", "implementation/p16/P16-06_SOURCE_DIFF_PROJECTION.md",
    "implementation/p16/P16-06_PLAN_REVIEW_DESIGN_SPEC.md", "implementation/p16/P16-06_PLAN_REVIEW_POLICY.md",
    "implementation/p16/P16-06_VISUAL_QA.md", "implementation/p16/p16-plan-review-policy-v1.json",
    "implementation/p16/design/p16-06-plan-review-concept.png",
    "implementation/p16/visual-qa/safety-v2/p16-06-desktop-blocked.png", "implementation/p16/visual-qa/safety-v2/p16-06-desktop-confirm.png",
    "implementation/p16/visual-qa/safety-v2/p16-06-desktop-dark-submitted.png", "implementation/p16/visual-qa/safety-v2/p16-06-desktop-ready.png",
    "implementation/p16/visual-qa/safety-v2/p16-06-desktop-unconfirmed.png", "implementation/p16/visual-qa/safety-v2/p16-06-minimum-ready.png",
    "implementation/p16/visual-qa/safety-v2/p16-06-narrow-blocked.png", "implementation/p16/visual-qa/safety-v2/p16-06-narrow-confirm.png",
    "implementation/p16/visual-qa/safety-v2/p16-06-narrow-ready.png", "implementation/p16/visual-qa/safety-v2/p16-06-narrow-unconfirmed.png",
    "implementation/p16/p16-continuity-contract-v1.json",
    "protocol/mcp/p15-public-tools-v1.json", "web/plugin-widget/scripts/build-plan-review-widget.mjs",
    "web/plugin-widget/src/plan-review-component.tsx", "web/plugin-widget/src/plan-review-controller.test.ts",
    "web/plugin-widget/src/plan-review-controller.ts", "web/plugin-widget/src/plan-review-e2e-host.ts",
    "web/plugin-widget/src/plan-review-mcp-app-port.ts", "web/plugin-widget/src/plan-review-model.test.ts",
    "web/plugin-widget/src/plan-review-model.ts", "web/plugin-widget/src/plan-review-preview.tsx",
    "web/plugin-widget/src/plan-review-resource.test.ts", "web/plugin-widget/src/plan-review-resource.ts",
    "web/plugin-widget/src/plan-review-styles.css", "web/plugin-widget/src/plan-review-ui.test.tsx",
    "web/plugin-widget/src/plan-review-ui.tsx", "tools/p16/plan_review.py", "tools/p16/build_plan_review_contract.py",
    "tools/p16/run_plan_review_checks.py", "tools/p16/run_plan_review_e2e.py", "tools/p16/validate_plan_review.py",
    "tools/p16/tests/test_plan_review.py",
)
def lock(path:str)->dict[str,Any]:
    value=(ROOT/path).read_bytes();return{"path":path,"bytes":len(value),"sha256":continuity.sha256_bytes(value)}
def build()->dict[str,Any]:
    bundles,errors=plan_review.validate_all()
    if errors or bundles is None:raise RuntimeError(f"cannot build stale plan-review contract: {errors}")
    return {
        "schema_version": "hwpx-agent.p16-plan-review-contract/v1", "task": "P16-06",
        "scope": "current_pc_local_mcp_apps_bridge_component",
        "decision": "pass_scoped_local_high_risk_confirmation_component_e2e_actual_host_pending",
        "requirements": list(plan_review.EXPECTED_REQUIREMENTS),
        "predecessor": {"path": "implementation/p16/p16-continuity-contract-v1.json", "sha256": plan_review.EXPECTED_PREDECESSOR_SHA256},
        "catalog": {"path": "protocol/mcp/p15-public-tools-v1.json", "sha256": plan_review.EXPECTED_CATALOG_SHA256, "tools": ["capability_check", "document_edit"]},
        "bundles": bundles,
        "e2e": {
            "runner": "tools/p16/run_plan_review_e2e.py", "bridge": "real_ext_apps_appbridge_postmessage_iframe",
            "call_count": 5, "call_order": ["capability_check", "document_edit_dry", "capability_check", "document_edit_dry", "document_edit_execute"],
            "evidence_level": "local_browser_component_not_actual_chatgpt_or_codex_host",
        },
        "limits": {"capability_routes": 12, "diff_categories": 8, "warnings": 8, "primary_actions": 1, "secondary_actions": 1, "minimum_css_width": 320},
        "claims": {
            "actual_chatgpt_or_codex_host_tested": False, "developer_mode_tested": False,
            "registered_plugin_tested": False, "remote_mcp_tested": False,
            "hangul_or_com_invoked": False, "file_transfer_tested": False,
            "hangul_2022_2024_or_other_pc_tested": False, "public_or_production_ready": False,
            "authenticated_stored_plan_projection_integrated": False,
        },
        "source_locks": [lock(path) for path in LOCAL_SOURCES],
        "next_task": "P16-06 authenticated stored-plan projection and registered-host integration",
    }
def main()->int:
    parser=argparse.ArgumentParser();parser.add_argument("--check",action="store_true");args=parser.parse_args();expected=continuity.canonical_json_bytes(build())
    if args.check:
        if not CONTRACT.is_file() or CONTRACT.read_bytes()!=expected:raise RuntimeError("P16 plan-review contract is stale")
    else:CONTRACT.write_bytes(expected)
    print(f"P16_PLAN_REVIEW_CONTRACT_PASS source_locks={len(LOCAL_SOURCES)}");return 0
if __name__=="__main__":raise SystemExit(main())
