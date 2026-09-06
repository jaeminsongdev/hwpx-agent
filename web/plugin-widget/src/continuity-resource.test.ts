import assert from "node:assert/strict";
import test from "node:test";

import {
    CONTINUITY_RENDER_REQUEST_SCHEMA,
    CONTINUITY_RENDER_REQUEST_V2_SCHEMA,
    CONTINUITY_SNAPSHOT_SCHEMA,
    CONTINUITY_SNAPSHOT_V2_SCHEMA,
} from "./continuity-model.js";
import {
    CONTINUITY_CSP,
    CONTINUITY_RENDER_INPUT_SCHEMA,
    CONTINUITY_RENDER_OUTPUT_SCHEMA,
    CONTINUITY_RENDER_TOOL_DESCRIPTOR,
    CONTINUITY_RENDER_V2_INPUT_SCHEMA,
    CONTINUITY_RENDER_V2_OUTPUT_SCHEMA,
    CONTINUITY_RENDER_V2_TOOL_DESCRIPTOR,
    CONTINUITY_RESOURCE_URI,
    CONTINUITY_RESOURCE_V2_URI,
    RESOURCE_MIME_TYPE,
    createContinuityResource,
    createContinuityResourceV2,
    createContinuityToolResult,
    createContinuityToolResultV2,
} from "./continuity-resource.js";

const snapshot = {
    schema_version: CONTINUITY_SNAPSHOT_SCHEMA,
    client_surface: "chatgpt_web",
    locale: "ko-KR",
    project_id: "prj_12345678",
    head_revision_id: "rev_abcdefgh",
    warning_count: 0,
    conflict_state: "none",
    revisions: [],
    next_cursor: null,
} as const;

test("constructs a self-contained immutable resource with closed CSP", () => {
    const resource = createContinuityResource(
        "<!doctype html><main>bounded</main>",
    );
    assert.equal(resource.contents[0].uri, CONTINUITY_RESOURCE_URI);
    assert.equal(RESOURCE_MIME_TYPE, "text/html;profile=mcp-app");
    assert.deepEqual(resource.contents[0]._meta.ui.csp, CONTINUITY_CSP);
    assert.equal(
        createContinuityResourceV2("<!doctype html><main>bounded</main>")
            .contents[0].uri,
        CONTINUITY_RESOURCE_V2_URI,
    );
});

test("publishes a distinct v2 render contract without changing v1", () => {
    assert.equal(
        CONTINUITY_RENDER_V2_TOOL_DESCRIPTOR.name,
        "render_project_continuity_widget_v2",
    );
    assert.equal(
        CONTINUITY_RENDER_V2_INPUT_SCHEMA.properties.schema_version.const,
        CONTINUITY_RENDER_REQUEST_V2_SCHEMA,
    );
    assert.equal(
        CONTINUITY_RENDER_V2_OUTPUT_SCHEMA.properties.schema_version.const,
        CONTINUITY_SNAPSHOT_V2_SCHEMA,
    );
    assert.equal(
        CONTINUITY_RENDER_V2_TOOL_DESCRIPTOR._meta.ui.resourceUri,
        CONTINUITY_RESOURCE_V2_URI,
    );
    assert.equal(
        CONTINUITY_RENDER_TOOL_DESCRIPTOR._meta.ui.resourceUri,
        CONTINUITY_RESOURCE_URI,
    );
});

test("rejects oversized and externally referenced continuity HTML", () => {
    assert.throws(
        () => createContinuityResource("x".repeat(800_001)),
        /bounded/,
    );
    assert.throws(
        () => createContinuityResource('<iframe src="/private"></iframe>'),
        /external/,
    );
    assert.throws(
        () => createContinuityResource('<a href="https://example.test">x</a>'),
        /external/,
    );
});

test("keeps UI metadata on a dedicated read-only render tool", () => {
    assert.equal(
        CONTINUITY_RENDER_TOOL_DESCRIPTOR.name,
        "render_project_continuity_widget",
    );
    assert.equal(
        CONTINUITY_RENDER_TOOL_DESCRIPTOR.annotations.readOnlyHint,
        true,
    );
    assert.deepEqual(CONTINUITY_RENDER_TOOL_DESCRIPTOR.securitySchemes, [
        { type: "oauth2", scopes: ["project.read"] },
    ]);
    assert.equal(
        CONTINUITY_RENDER_INPUT_SCHEMA.properties.schema_version.const,
        CONTINUITY_RENDER_REQUEST_SCHEMA,
    );
    assert.equal(CONTINUITY_RENDER_OUTPUT_SCHEMA.additionalProperties, false);
});

test("returns safe structured content and component-only metadata", () => {
    const result = createContinuityToolResult(snapshot);
    assert.deepEqual(Object.keys(result._meta).sort(), [
        "hwpx-agent/continuity-version",
        "hwpx-agent/preferred-display-mode",
    ]);
    assert.throws(
        () => createContinuityToolResult({ ...snapshot, raw_xml: "<hp:t/>" }),
        /invalid/,
    );
});

test("returns only validated v2 stale-head structured content", () => {
    const result = createContinuityToolResultV2({
        ...snapshot,
        schema_version: CONTINUITY_SNAPSHOT_V2_SCHEMA,
        conflict_state: "stale",
        stale_head: {
            observed_generation: 2,
            current_generation: 4,
            delta: 2,
            allowed_resolutions: ["branch"],
        },
    });
    assert.equal(result._meta["hwpx-agent/continuity-version"], "2");
    assert.throws(
        () =>
            createContinuityToolResultV2({
                ...result.structuredContent,
                stale_head: {
                    ...result.structuredContent.stale_head!,
                    local_path: "D:\\private",
                },
            }),
        /invalid/,
    );
});
