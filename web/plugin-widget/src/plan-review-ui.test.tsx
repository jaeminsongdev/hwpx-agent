import assert from "node:assert/strict";
import test from "node:test";
import { renderToStaticMarkup } from "react-dom/server";
import {
    PLAN_REVIEW_SNAPSHOT_SCHEMA,
    type PlanReviewSnapshot,
} from "./plan-review-model.js";
import type { PlanReviewViewState } from "./plan-review-controller.js";
import { PlanReviewView } from "./plan-review-ui.js";
const snapshot = {
    schema_version: PLAN_REVIEW_SNAPSHOT_SCHEMA,
    client_surface: "codex_local",
    locale: "ko-KR",
    project_id: "prj_abcdefgh",
    source_revision_id: "rev_abcdefgh",
    plan_id: "plan_abcdefgh",
    risk_level: "high",
    estimated_page_effect: "document_wide",
    route: [
        {
            capability_id: "paragraph.text_replace",
            selected_backend: "direct_hwpx",
            support_level: "verified",
            supported: true,
        },
    ],
    route_digest: "a".repeat(64),
    diff: {
        added: 4,
        modified: 7,
        removed: 0,
        categories: [{ kind: "paragraph", count: 11 }],
    },
    warnings: [{ code: "LAYOUT_CHECK", severity: "warning", kind: "layout" }],
    signature_impact: "none",
    dry_run_state: "verified",
    execution_allowed: true,
} as const;
const handlers = {
    onBeginExecution() {},
    onCancelExecution() {},
    onAcknowledged(_value: boolean) {},
    onConfirmExecution() {},
    onRevalidate() {},
};
function render(patch: Partial<PlanReviewViewState> = {}) {
    const state: PlanReviewViewState = {
        phase: "ready",
        mode: "view",
        locale: "ko-KR",
        theme: "light",
        snapshot,
        errorCode: null,
        actionPending: false,
        acknowledged: false,
        executionState: "none",
        ...patch,
    };
    return renderToStaticMarkup(<PlanReviewView state={state} {...handlers} />);
}
test("renders risk, route, diff and local warning copy", () => {
    const html = render();
    for (const text of [
        "변경 계획 검토",
        "고위험",
        "paragraph.text_replace",
        "추가",
        "4",
        "LAYOUT_CHECK",
        "레이아웃에 문서 전체 영향",
    ])
        assert.match(html, new RegExp(text));
});
test("does not render full opaque identifiers", () => {
    const html = render();
    assert.doesNotMatch(html, /rev_abcdefgh/);
    assert.doesNotMatch(html, /plan_abcdefgh/);
});
test("confirmation is disabled before acknowledgement", () => {
    const html = render({ mode: "confirm_execution" });
    assert.match(html, /type="checkbox"/);
    assert.match(html, /disabled=""[^>]*>확인 후 실행|>확인 후 실행<\/button>/);
});
test("blocked snapshot has no enabled primary action", () => {
    const blocked: PlanReviewSnapshot = {
        ...snapshot,
        warnings: [
            { code: "BLOCKED", severity: "blocking", kind: "validation" },
        ],
        execution_allowed: false,
    };
    const html = render({ snapshot: blocked });
    assert.match(html, /현재 계획은 실행할 수 없습니다/);
    assert.match(html, /disabled=""[^>]*>실행 검토/);
});
test("renders status with live semantics", () =>
    assert.match(render({ executionState: "submitted" }), /role="status"/));
test("renders approval state without plan data", () => {
    const html = render({ phase: "approval_pending", snapshot: null });
    assert.match(html, /승인된 계획 결과/);
    assert.doesNotMatch(html, /기능 경로/);
});
