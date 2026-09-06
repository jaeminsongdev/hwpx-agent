import assert from "node:assert/strict";
import test from "node:test";

import {
    CONTINUITY_RENDER_REQUEST_SCHEMA,
    CONTINUITY_RENDER_REQUEST_V2_SCHEMA,
    CONTINUITY_SNAPSHOT_SCHEMA,
    CONTINUITY_SNAPSHOT_V2_SCHEMA,
    PUBLIC_RESULT_SCHEMA,
    classifyRevisionChange,
    parseContinuityRenderRequest,
    parseContinuityRenderRequestV2,
    parseContinuitySnapshot,
    parseContinuitySnapshotV2,
    parseProjectCheckpointResult,
    parseProjectConflictResolveResult,
    parseProjectHistoryResult,
    parseProjectOpenResult,
} from "./continuity-model.js";

const warning = { code: "SAFE_WARNING", message: "bounded" };
const base = {
    schema_version: PUBLIC_RESULT_SCHEMA,
    request_id: "req_12345678",
    outcome: "succeeded",
    safe_summary: "bounded",
    warnings: [warning],
} as const;

test("accepts exact continuity input and snapshot shapes", () => {
    assert.notEqual(
        parseContinuityRenderRequest({
            schema_version: CONTINUITY_RENDER_REQUEST_SCHEMA,
            client_surface: "chatgpt_web",
            locale: "ko-KR",
            project_id: "prj_12345678",
        }),
        null,
    );
    assert.notEqual(
        parseContinuitySnapshot({
            schema_version: CONTINUITY_SNAPSHOT_SCHEMA,
            client_surface: "codex_local",
            locale: "en-US",
            project_id: "prj_12345678",
            head_revision_id: "rev_abcdefgh",
            warning_count: 1,
            conflict_state: "none",
            revisions: [
                {
                    revision_id: "rev_abcdefgh",
                    parent_revision_ids: ["rev_parent123"],
                    created_at: "2026-09-05T00:00:00Z",
                    change_kind: "edited",
                },
            ],
            next_cursor: "cursor_12345678",
        }),
        null,
    );
});

test("rejects unknown fields, duplicated revisions and head mismatch", () => {
    assert.equal(
        parseContinuityRenderRequest({
            schema_version: CONTINUITY_RENDER_REQUEST_SCHEMA,
            client_surface: "chatgpt_web",
            locale: "ko-KR",
            project_id: "prj_12345678",
            local_path: "D:\\private",
        }),
        null,
    );
    const revision = {
        revision_id: "rev_abcdefgh",
        parent_revision_ids: [],
        created_at: "2026-09-05T00:00:00Z",
        change_kind: "edited",
    } as const;
    assert.equal(
        parseContinuitySnapshot({
            schema_version: CONTINUITY_SNAPSHOT_SCHEMA,
            client_surface: "chatgpt_web",
            locale: "ko-KR",
            project_id: "prj_12345678",
            head_revision_id: "rev_other1234",
            warning_count: 0,
            conflict_state: "none",
            revisions: [revision, revision],
            next_cursor: null,
        }),
        null,
    );
});

test("accepts exact v2 stale-head generations and rejects inconsistent successors", () => {
    assert.notEqual(
        parseContinuityRenderRequestV2({
            schema_version: CONTINUITY_RENDER_REQUEST_V2_SCHEMA,
            client_surface: "codex_local",
            locale: "ko-KR",
            project_id: "prj_12345678",
        }),
        null,
    );
    const value = {
        schema_version: CONTINUITY_SNAPSHOT_V2_SCHEMA,
        client_surface: "codex_local",
        locale: "ko-KR",
        project_id: "prj_12345678",
        head_revision_id: "rev_abcdefgh",
        warning_count: 1,
        conflict_state: "stale",
        stale_head: {
            observed_generation: 10,
            current_generation: 12,
            delta: 2,
            allowed_resolutions: [
                "rebase_operation_plan",
                "branch",
                "manual_merge",
            ],
        },
        revisions: [
            {
                revision_id: "rev_abcdefgh",
                parent_revision_ids: [],
                created_at: "2026-09-05T00:00:00Z",
                change_kind: "edited",
            },
        ],
        next_cursor: null,
    } as const;
    assert.notEqual(parseContinuitySnapshotV2(value), null);
    assert.equal(
        parseContinuitySnapshotV2({
            ...value,
            stale_head: { ...value.stale_head, delta: 1 },
        }),
        null,
    );
    assert.equal(
        parseContinuitySnapshotV2({
            ...value,
            conflict_state: "none",
        }),
        null,
    );
    assert.equal(
        parseContinuitySnapshotV2({
            ...value,
            head_revision_id: null,
            revisions: [],
        }),
        null,
    );
    assert.equal(
        parseContinuitySnapshotV2({
            ...value,
            stale_head: {
                ...value.stale_head,
                allowed_resolutions: ["branch", "branch"],
            },
        }),
        null,
    );
});

test("parses exact public open history and checkpoint results", () => {
    assert.deepEqual(
        parseProjectOpenResult({
            ...base,
            project_id: "prj_12345678",
            head_revision_id: "rev_abcdefgh",
            warning_count: 2,
            conflict_state: "stale",
            recommended_actions: ["refresh"],
        }),
        {
            request_id: "req_12345678",
            project_id: "prj_12345678",
            head_revision_id: "rev_abcdefgh",
            warning_count: 2,
            conflict_state: "stale",
        },
    );
    assert.notEqual(
        parseProjectHistoryResult({
            ...base,
            revisions: [
                {
                    revision_id: "rev_abcdefgh",
                    parent_revision_ids: [],
                    created_at: "2026-09-05T00:00:00Z",
                    summary: "edited paragraph",
                },
            ],
            next_cursor: null,
        }),
        null,
    );
    assert.notEqual(
        parseProjectCheckpointResult({
            ...base,
            checkpoint_id: "chk_abcdefgh",
            revision_id: "rev_abcdefgh",
            replayed: false,
        }),
        null,
    );
    assert.deepEqual(
        parseProjectConflictResolveResult({
            ...base,
            project_id: "prj_12345678",
            expected_revision: "rev_abcdefgh",
            resolution: "branch",
            current_generation: 12,
            conflict_state: "none",
            replayed: false,
        }),
        {
            request_id: "req_12345678",
            project_id: "prj_12345678",
            expected_revision: "rev_abcdefgh",
            resolution: "branch",
            current_generation: 12,
            conflict_state: "none",
            replayed: false,
        },
    );
});

test("rejects malformed public results without echoing their content", () => {
    assert.equal(
        parseProjectOpenResult({
            ...base,
            warnings: [{ code: "bad", message: "D:\\private" }],
            project_id: "prj_12345678",
            head_revision_id: null,
            warning_count: 0,
            conflict_state: "none",
            recommended_actions: [],
        }),
        null,
    );
    assert.equal(
        parseProjectCheckpointResult({
            ...base,
            checkpoint_id: "chk_abcdefgh",
            revision_id: "rev_abcdefgh",
            replayed: false,
            raw_error: "secret",
        }),
        null,
    );
    assert.equal(
        parseProjectHistoryResult({
            ...base,
            outcome: "partial",
            revisions: [],
            next_cursor: null,
        }),
        null,
    );
    assert.equal(
        parseProjectOpenResult({
            ...base,
            safe_summary: "",
            project_id: "prj_12345678",
            head_revision_id: null,
            warning_count: 0,
            conflict_state: "none",
            recommended_actions: [],
        }),
        null,
    );
});

test("classifies only a bounded local change-kind vocabulary", () => {
    assert.equal(classifyRevisionChange("Edited title"), "edited");
    assert.equal(classifyRevisionChange("검증 완료"), "validated");
    assert.equal(classifyRevisionChange("private document text"), "unknown");
});
