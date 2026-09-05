import assert from "node:assert/strict";
import test from "node:test";
import {
    PLAN_REVIEW_REQUEST_SCHEMA,
    PLAN_REVIEW_SNAPSHOT_SCHEMA,
    PUBLIC_RESULT_SCHEMA,
    isAcceptedExecution,
    isVerifiedDryRun,
    parseCapabilityCheckResult,
    parseDocumentEditResult,
    parsePlanReviewRenderRequest,
    parsePlanReviewSnapshot,
    routeMatches,
    type PlanReviewSnapshot,
    warningsCovered,
} from "./plan-review-model.js";

const route = [
    {
        capability_id: "paragraph.text_replace",
        selected_backend: "direct_hwpx",
        support_level: "verified",
        supported: true,
    },
] as const;
const request = {
    schema_version: PLAN_REVIEW_REQUEST_SCHEMA,
    client_surface: "codex_local",
    locale: "ko-KR",
    project_id: "prj_abcdefgh",
    source_revision_id: "rev_abcdefgh",
    plan_id: "plan_abcdefgh",
};
const snapshot: PlanReviewSnapshot = {
    schema_version: PLAN_REVIEW_SNAPSHOT_SCHEMA,
    client_surface: "codex_local",
    locale: "ko-KR",
    project_id: "prj_abcdefgh",
    source_revision_id: "rev_abcdefgh",
    plan_id: "plan_abcdefgh",
    risk_level: "high",
    estimated_page_effect: "local",
    route,
    route_digest: "a".repeat(64),
    diff: {
        added: 1,
        modified: 2,
        removed: 0,
        categories: [{ kind: "paragraph", count: 3 }],
    },
    warnings: [{ code: "LAYOUT_CHECK", severity: "warning", kind: "layout" }],
    signature_impact: "none",
    dry_run_state: "verified",
    execution_allowed: true,
};
const base = {
    schema_version: PUBLIC_RESULT_SCHEMA,
    request_id: "req_abcdefgh",
    outcome: "succeeded",
    safe_summary: "ok",
    warnings: [],
};

test("accepts exact render request", () =>
    assert.deepEqual(parsePlanReviewRenderRequest(request), request));
test("rejects extra render input", () =>
    assert.equal(
        parsePlanReviewRenderRequest({ ...request, path: "x" }),
        null,
    ));
test("rejects malformed identifiers", () =>
    assert.equal(
        parsePlanReviewRenderRequest({ ...request, plan_id: "bad" }),
        null,
    ));
test("accepts executable snapshot", () =>
    assert.equal(parsePlanReviewSnapshot(snapshot)?.execution_allowed, true));
test("rejects duplicate route IDs", () =>
    assert.equal(
        parsePlanReviewSnapshot({ ...snapshot, route: [...route, ...route] }),
        null,
    ));
test("rejects duplicate diff kinds", () =>
    assert.equal(
        parsePlanReviewSnapshot({
            ...snapshot,
            diff: {
                ...snapshot.diff,
                categories: [
                    ...snapshot.diff.categories,
                    ...snapshot.diff.categories,
                ],
            },
        }),
        null,
    ));
test("rejects duplicate warning codes", () =>
    assert.equal(
        parsePlanReviewSnapshot({
            ...snapshot,
            warnings: [...snapshot.warnings, ...snapshot.warnings],
        }),
        null,
    ));
test("rejects executable snapshot with blocking warning", () =>
    assert.equal(
        parsePlanReviewSnapshot({
            ...snapshot,
            warnings: [
                { code: "BLOCKED", severity: "blocking", kind: "validation" },
            ],
        }),
        null,
    ));
test("accepts consistently blocked snapshot", () =>
    assert.equal(
        parsePlanReviewSnapshot({
            ...snapshot,
            warnings: [
                { code: "BLOCKED", severity: "blocking", kind: "validation" },
            ],
            execution_allowed: false,
        })?.execution_allowed,
        false,
    ));
test("rejects invalid signature execution", () =>
    assert.equal(
        parsePlanReviewSnapshot({
            ...snapshot,
            signature_impact: "invalidates",
        }),
        null,
    ));
test("rejects unsupported route marked supported", () =>
    assert.equal(
        parsePlanReviewSnapshot({
            ...snapshot,
            route: [{ ...route[0], support_level: "unsupported" }],
        }),
        null,
    ));
test("accepts strict capability result", () =>
    assert.equal(
        parseCapabilityCheckResult({
            ...base,
            capabilities: [
                {
                    ...route[0],
                    estimated_job_class: "short",
                    constraints: [],
                    unverified_reasons: [],
                },
            ],
        })?.capabilities.length,
        1,
    ));
test("rejects partial capability outcome", () =>
    assert.equal(
        parseCapabilityCheckResult({
            ...base,
            outcome: "partial",
            capabilities: [
                {
                    ...route[0],
                    estimated_job_class: "short",
                    constraints: [],
                    unverified_reasons: [],
                },
            ],
        }),
        null,
    ));
test("route comparison ignores order but not backend", () => {
    assert.equal(routeMatches(route, [...route]), true);
    assert.equal(
        routeMatches(route, [{ ...route[0], selected_backend: "hybrid" }]),
        false,
    );
});
test("accepts verified dry run", () => {
    const parsed = parseDocumentEditResult({
        ...base,
        job_id: null,
        revision_id: null,
        artifact: null,
        commit_state: "not_started",
        validation_state: "verified",
    });
    assert.ok(parsed);
    assert.equal(isVerifiedDryRun(parsed), true);
});
test("rejects dry run carrying artifact", () =>
    assert.equal(
        parseDocumentEditResult({
            ...base,
            job_id: null,
            revision_id: null,
            artifact: {},
            commit_state: "not_started",
            validation_state: "verified",
        }),
        null,
    ));
test("accepts queued execution", () => {
    const parsed = parseDocumentEditResult({
        ...base,
        outcome: "accepted",
        job_id: "job_abcdefgh",
        revision_id: null,
        artifact: null,
        commit_state: "pending",
        validation_state: "not_run",
    });
    assert.ok(parsed);
    assert.equal(isAcceptedExecution(parsed), true);
});
test("accepts committed execution", () => {
    const parsed = parseDocumentEditResult({
        ...base,
        revision_id: "rev_newvalue1",
        job_id: null,
        artifact: null,
        commit_state: "committed",
        validation_state: "verified",
    });
    assert.ok(parsed);
    assert.equal(isAcceptedExecution(parsed), true);
});
test("rejects inconsistent execution state", () => {
    const parsed = parseDocumentEditResult({
        ...base,
        job_id: null,
        revision_id: null,
        artifact: null,
        commit_state: "pending",
        validation_state: "verified",
    });
    assert.ok(parsed);
    assert.equal(isAcceptedExecution(parsed), false);
});
test("accepted execution requires not-run validation", () => {
    const parsed = parseDocumentEditResult({
        ...base,
        outcome: "accepted",
        job_id: "job_abcdefgh",
        revision_id: null,
        artifact: null,
        commit_state: "pending",
        validation_state: "failed",
    });
    assert.ok(parsed);
    assert.equal(isAcceptedExecution(parsed), false);
});
test("only pre-approved warning codes are covered", () => {
    assert.equal(warningsCovered(snapshot.warnings, ["LAYOUT_CHECK"]), true);
    assert.equal(warningsCovered(snapshot.warnings, ["NEW_WARNING"]), false);
});
