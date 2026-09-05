import assert from "node:assert/strict";
import test from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import type { WidgetViewState } from "./bridge.js";
import { WIDGET_SNAPSHOT_SCHEMA } from "./model.js";
import { WidgetShell } from "./ui.js";

const READY: WidgetViewState = {
    phase: "ready",
    locale: "ko-KR",
    theme: "light",
    snapshot: {
        schema_version: WIDGET_SNAPSHOT_SCHEMA,
        client_surface: "chatgpt_web",
        locale: "ko-KR",
        project_id: "prj_12345678",
        revision_id: "rev_abcdefgh",
        validation_state: "verified",
    },
    errorCode: null,
    actionPending: false,
};

test("renders the ready shell with bounded identifiers and semantic metadata", () => {
    const html = renderToStaticMarkup(
        <WidgetShell
            state={READY}
            onContinue={() => undefined}
            onRetry={() => undefined}
        />,
    );
    assert.match(html, /준비됨/);
    assert.match(html, /prj_12…/);
    assert.match(html, /rev_ab…/);
    assert.doesNotMatch(html, /prj_12345678/);
    assert.match(html, /<dl/);
    assert.match(html, /<button/);
});

test("renders a bounded English recovery state without raw errors", () => {
    const html = renderToStaticMarkup(
        <WidgetShell
            state={{
                ...READY,
                phase: "recoverable_error",
                locale: "en-US",
                snapshot: null,
                errorCode: "CONNECT_FAILED",
            }}
            onContinue={() => undefined}
            onRetry={() => undefined}
        />,
    );
    assert.match(html, /connection could not be completed/i);
    assert.match(html, />Retry</);
    assert.doesNotMatch(html, /private transport detail/);
});
