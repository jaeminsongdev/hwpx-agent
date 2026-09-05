import assert from "node:assert/strict";
import test from "node:test";
import {
    PLAN_REVIEW_REQUEST_SCHEMA,
    PLAN_REVIEW_SNAPSHOT_SCHEMA,
    PUBLIC_RESULT_SCHEMA,
    isAcceptedExecution,
    isCommittedUnverifiedExecution,
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
test("plan identifiers stop at the public total length of 124", () => {
    for (const length of [12, 13, 124, 125, 1000]) {
        const plan_id = `plan_${"a".repeat(length - 5)}`;
        const valid = length >= 13 && length <= 124;
        assert.equal(
            parsePlanReviewRenderRequest({ ...request, plan_id }) !== null,
            valid,
        );
        assert.equal(
            parsePlanReviewSnapshot({ ...snapshot, plan_id }) !== null,
            valid,
        );
    }
});
test("accepts executable snapshot", () =>
    assert.equal(parsePlanReviewSnapshot(snapshot)?.execution_allowed, true));

test("capability identifiers obey the public 160-character bound", () => {
    for (const length of [160, 161]) {
        const capability_id = `a.${"b".repeat(length - 2)}`;
        const parsed = parsePlanReviewSnapshot({
            ...snapshot,
            route: [{ ...route[0], capability_id }],
        });
        assert.equal(parsed !== null, length === 160);
        const result = parseCapabilityCheckResult({
            ...base,
            capabilities: [
                {
                    ...route[0],
                    capability_id,
                    estimated_job_class: "short",
                    constraints: [],
                    unverified_reasons: [],
                },
            ],
        });
        assert.equal(result !== null, length === 160);
    }
});
test("partial capability route cannot authorize execution", () => {
    const partial = {
        ...snapshot,
        route: [{ ...route[0], support_level: "partial" }],
    };
    assert.equal(parsePlanReviewSnapshot(partial), null);
    assert.equal(
        parsePlanReviewSnapshot({ ...partial, execution_allowed: false })
            ?.execution_allowed,
        false,
    );
});
test("server may deny execution even when component checks pass", () => {
    assert.equal(
        parsePlanReviewSnapshot({ ...snapshot, execution_allowed: false })
            ?.execution_allowed,
        false,
    );
});
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
const artifact = {
    artifact_id: "art_abcdefgh",
    media_type: "application/hwp+zip",
    bytes: 1234,
    sha256: "b".repeat(64),
};
const committed = {
    ...base,
    revision_id: "rev_newvalue1",
    job_id: null,
    artifact,
    commit_state: "committed",
    validation_state: "verified",
};
test("accepts the public artifact-bearing committed response", () => {
    const parsed = parseDocumentEditResult(committed);
    assert.ok(parsed);
    assert.equal(isAcceptedExecution(parsed), true);
});
test("artifact metadata obeys every public boundary and exact keys", () => {
    for (const valid of [
        { ...artifact, bytes: 0 },
        { ...artifact, bytes: 10_737_418_240 },
        { ...artifact, artifact_id: `art_${"x".repeat(120)}` },
        { ...artifact, media_type: `a/${"b".repeat(125)}` },
    ])
        assert.ok(parseDocumentEditResult({ ...committed, artifact: valid }));
    for (const invalid of [
        {},
        { ...artifact, url: "private" },
        { ...artifact, bytes: -1 },
        { ...artifact, bytes: 10_737_418_241 },
        { ...artifact, bytes: 1.5 },
        { ...artifact, bytes: NaN },
        { ...artifact, sha256: "A".repeat(64) },
        { ...artifact, artifact_id: `art_${"x".repeat(121)}` },
        { ...artifact, media_type: `a/${"b".repeat(126)}` },
        { ...artifact, media_type: "text/plain; charset=utf-8" },
    ])
        assert.equal(
            parseDocumentEditResult({ ...committed, artifact: invalid }),
            null,
        );
});
test("dry-run and queued acceptance cannot carry a published artifact", () => {
    const dry = parseDocumentEditResult({
        ...committed,
        revision_id: null,
        commit_state: "not_started",
    });
    assert.ok(dry);
    assert.equal(isVerifiedDryRun(dry), false);
    const queued = parseDocumentEditResult({
        ...committed,
        outcome: "accepted",
        job_id: "job_abcdefgh",
        revision_id: null,
        commit_state: "pending",
        validation_state: "not_run",
    });
    assert.ok(queued);
    assert.equal(isAcceptedExecution(queued), false);
});
test("partial committed validation is not a fully verified execution", () => {
    const parsed = parseDocumentEditResult({
        ...committed,
        artifact: null,
        validation_state: "partial",
    });
    assert.ok(parsed);
    assert.equal(isAcceptedExecution(parsed), false);
});
test("public partial and unverified outcomes remain parseable", () => {
    for (const outcome of ["partial", "unverified"]) {
        const parsed = parseDocumentEditResult({ ...committed, outcome });
        assert.ok(parsed);
        assert.equal(isAcceptedExecution(parsed), false);
    }
});
test("committed classification preserves partial outcomes without claiming verified success", () => {
    for (const outcome of [
        "accepted",
        "succeeded",
        "partial",
        "unverified",
    ] as const) {
        for (const validation_state of [
            "not_run",
            "verified",
            "partial",
            "failed",
        ] as const) {
            const parsed = parseDocumentEditResult({
                ...committed,
                outcome,
                validation_state,
            });
            assert.ok(parsed);
            const verified =
                outcome === "succeeded" && validation_state === "verified";
            assert.equal(isAcceptedExecution(parsed), verified);
            assert.equal(
                isCommittedUnverifiedExecution(parsed),
                outcome !== "accepted" && !verified,
            );
            assert.equal(isVerifiedDryRun(parsed), false);
        }
    }
});
test("artifact projection does not alias the original host payload", () => {
    const payload = { ...committed, artifact: { ...artifact } };
    const parsed = parseDocumentEditResult(payload);
    assert.ok(parsed?.artifact);
    payload.artifact.artifact_id = "art_changed1";
    payload.artifact.bytes = -1;
    assert.deepEqual(parsed.artifact, artifact);
});
test("public summary and warning bounds count Unicode characters, not UTF-16 units", () => {
    for (const length of [1000, 1001]) {
        const text = "😀".repeat(length);
        assert.equal(
            parseDocumentEditResult({ ...committed, safe_summary: text }) !==
                null,
            length === 1000,
        );
        assert.equal(
            parseDocumentEditResult({
                ...committed,
                warnings: [{ code: "SAFE_WARNING", message: text }],
            }) !== null,
            length === 1000,
        );
    }
});
test("capability detail bounds count Unicode characters without displaying content", () => {
    for (const length of [500, 501]) {
        const detail = "😀".repeat(length);
        for (const key of ["constraints", "unverified_reasons"]) {
            const parsed = parseCapabilityCheckResult({
                ...base,
                capabilities: [
                    {
                        ...route[0],
                        estimated_job_class: "short",
                        constraints: [],
                        unverified_reasons: [],
                        [key]: [detail],
                    },
                ],
            });
            assert.equal(parsed !== null, length === 500);
            if (parsed !== null) {
                assert.equal(parsed.detail_count, 1);
                assert.doesNotMatch(JSON.stringify(parsed), /😀/u);
            }
        }
    }
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
