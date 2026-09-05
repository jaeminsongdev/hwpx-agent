import assert from "node:assert/strict";
import test from "node:test";
import { PLAN_REVIEW_SNAPSHOT_SCHEMA } from "./plan-review-model.js";
import {
    PLAN_REVIEW_CSP,
    PLAN_REVIEW_RENDER_TOOL_DESCRIPTOR,
    PLAN_REVIEW_RESOURCE_URI,
    RESOURCE_MIME_TYPE,
    createPlanReviewResource,
    createPlanReviewToolResult,
} from "./plan-review-resource.js";
const value = {
    schema_version: PLAN_REVIEW_SNAPSHOT_SCHEMA,
    client_surface: "codex_local",
    locale: "ko-KR",
    project_id: "prj_abcdefgh",
    source_revision_id: "rev_abcdefgh",
    plan_id: "plan_abcdefgh",
    risk_level: "low",
    estimated_page_effect: "local",
    route: [
        {
            capability_id: "paragraph.text_replace",
            selected_backend: "direct_hwpx",
            support_level: "verified",
            supported: true,
        },
    ],
    route_digest: "a".repeat(64),
    diff: { added: 1, modified: 0, removed: 0, categories: [] },
    warnings: [],
    signature_impact: "none",
    dry_run_state: "verified",
    execution_allowed: true,
};
test("descriptor binds immutable resource and read scope", () => {
    assert.equal(
        PLAN_REVIEW_RENDER_TOOL_DESCRIPTOR._meta.ui.resourceUri,
        PLAN_REVIEW_RESOURCE_URI,
    );
    assert.equal(
        PLAN_REVIEW_RENDER_TOOL_DESCRIPTOR.annotations.readOnlyHint,
        true,
    );
    assert.deepEqual(PLAN_REVIEW_RENDER_TOOL_DESCRIPTOR.securitySchemes, [
        { type: "oauth2", scopes: ["project.read"] },
    ]);
});
test("resource has MCP Apps MIME and closed CSP", () => {
    const resource = createPlanReviewResource("<!doctype html>\n<p>safe</p>");
    assert.equal(resource.contents[0].mimeType, RESOURCE_MIME_TYPE);
    assert.deepEqual(resource.contents[0]._meta.ui.csp, PLAN_REVIEW_CSP);
});
test("resource rejects remote source and nested iframe", () => {
    assert.throws(() =>
        createPlanReviewResource('<img src="https://example.invalid/a">'),
    );
    assert.throws(() => createPlanReviewResource("<iframe></iframe>"));
});
test("tool result requires strict snapshot", () => {
    assert.deepEqual(
        createPlanReviewToolResult(value).structuredContent,
        value,
    );
    assert.throws(() => createPlanReviewToolResult({ ...value, path: "x" }));
});
