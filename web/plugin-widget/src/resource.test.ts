import assert from "node:assert/strict";
import test from "node:test";

import { WIDGET_SNAPSHOT_SCHEMA } from "./model.js";
import {
    createRenderToolResult,
    createWidgetResource,
    RESOURCE_MIME_TYPE,
    WIDGET_CSP,
    WIDGET_RENDER_INPUT_SCHEMA,
    WIDGET_RENDER_OUTPUT_SCHEMA,
    WIDGET_RENDER_TOOL_DESCRIPTOR,
    WIDGET_RESOURCE_URI,
} from "./resource.js";

test("constructs the immutable versioned MCP App resource with a closed CSP", () => {
    const resource = createWidgetResource(
        "<!doctype html><main>bounded</main>",
    );
    assert.equal(resource.contents[0].uri, WIDGET_RESOURCE_URI);
    assert.equal(RESOURCE_MIME_TYPE, "text/html;profile=mcp-app");
    assert.deepEqual(resource.contents[0]._meta.ui.csp, WIDGET_CSP);
    assert.equal(resource.contents[0]._meta.ui.prefersBorder, true);
});

test("rejects oversized or externally referenced HTML", () => {
    assert.throws(() => createWidgetResource("x".repeat(700_001)), /bounded/);
    assert.throws(
        () =>
            createWidgetResource(
                '<script src="https://example.test/private.js"></script>',
            ),
        /external/,
    );
    assert.throws(
        () => createWidgetResource("<style>@import '//cdn.test/x.css'</style>"),
        /external/,
    );
    assert.throws(
        () => createWidgetResource('<a href="https://example.test/">x</a>'),
        /external/,
    );
    assert.throws(
        () => createWidgetResource('<form action="/submit"></form>'),
        /external/,
    );
    assert.throws(
        () =>
            createWidgetResource(
                '<meta http-equiv="refresh" content="0;url=/next">',
            ),
        /external/,
    );
});

test("keeps UI metadata on a dedicated read-only render tool", () => {
    assert.equal(
        WIDGET_RENDER_TOOL_DESCRIPTOR.name,
        "render_document_work_widget",
    );
    assert.deepEqual(WIDGET_RENDER_TOOL_DESCRIPTOR._meta, {
        securitySchemes: [{ type: "oauth2", scopes: ["project.read"] }],
        ui: { resourceUri: WIDGET_RESOURCE_URI },
    });
    assert.equal(WIDGET_RENDER_TOOL_DESCRIPTOR.annotations.readOnlyHint, true);
    assert.equal(WIDGET_RENDER_INPUT_SCHEMA.additionalProperties, false);
    assert.equal(WIDGET_RENDER_OUTPUT_SCHEMA.additionalProperties, false);
    assert.deepEqual(
        WIDGET_RENDER_TOOL_DESCRIPTOR.securitySchemes,
        WIDGET_RENDER_TOOL_DESCRIPTOR._meta.securitySchemes,
    );
});

test("returns bounded structured content and component-only metadata", () => {
    const result = createRenderToolResult({
        schema_version: WIDGET_SNAPSHOT_SCHEMA,
        client_surface: "chatgpt_web",
        locale: "ko-KR",
        project_id: null,
        revision_id: null,
        validation_state: "unverified",
    });
    assert.equal(result.content.length, 1);
    assert.deepEqual(Object.keys(result._meta).sort(), [
        "hwpx-agent/preferred-display-mode",
        "hwpx-agent/widget-shell-version",
    ]);
    assert.throws(
        () =>
            createRenderToolResult({
                ...result.structuredContent,
                local_path: "D:\\private",
            }),
        /invalid/,
    );
});
