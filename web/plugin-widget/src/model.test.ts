import assert from "node:assert/strict";
import test from "node:test";

import {
    displayOpaqueId,
    parseWidgetRenderRequest,
    parseWidgetSnapshot,
    resolveHostTheme,
    resolveViewLocale,
    WIDGET_RENDER_REQUEST_SCHEMA,
    WIDGET_SNAPSHOT_SCHEMA,
} from "./model.js";

const VALID = {
    schema_version: WIDGET_SNAPSHOT_SCHEMA,
    client_surface: "chatgpt_web",
    locale: "ko-KR",
    project_id: "prj_12345678",
    revision_id: "rev_abcdefgh",
    validation_state: "verified",
} as const;

test("accepts the exact bounded snapshot", () => {
    assert.deepEqual(parseWidgetSnapshot(VALID), VALID);
});

test("keeps model-originated render requests separate from server snapshots", () => {
    const request = {
        schema_version: WIDGET_RENDER_REQUEST_SCHEMA,
        client_surface: "chatgpt_web",
        locale: "ko-KR",
        project_id: "prj_12345678",
    } as const;
    assert.deepEqual(parseWidgetRenderRequest(request), request);
    assert.equal(parseWidgetRenderRequest(VALID), null);
    assert.equal(
        parseWidgetRenderRequest({
            ...request,
            validation_state: "verified",
        }),
        null,
    );
});

test("rejects unknown keys, paths, URLs and malformed identifiers without echo", () => {
    assert.equal(
        parseWidgetSnapshot({ ...VALID, document_text: "private" }),
        null,
    );
    assert.equal(
        parseWidgetSnapshot({ ...VALID, project_id: "D:\\private\\file.hwpx" }),
        null,
    );
    assert.equal(
        parseWidgetSnapshot({
            ...VALID,
            revision_id: "https://example.test/private",
        }),
        null,
    );
});

test("sanitizes locale and theme to the two presentation variants", () => {
    assert.equal(resolveViewLocale("ko-KR"), "ko-KR");
    assert.equal(resolveViewLocale("fr-FR"), "en-US");
    assert.equal(resolveViewLocale("../../private"), "ko-KR");
    assert.equal(resolveHostTheme("dark"), "dark");
    assert.equal(resolveHostTheme("host-secret-theme"), "light");
});

test("displays only an opaque six-character prefix", () => {
    assert.equal(displayOpaqueId("prj_12345678"), "prj_12…");
    assert.equal(displayOpaqueId(null), "—");
});
