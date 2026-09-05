import assert from "node:assert/strict";
import test from "node:test";
import { renderToStaticMarkup } from "react-dom/server";

import type { ContinuityViewState } from "./continuity-controller.js";
import { CONTINUITY_SNAPSHOT_SCHEMA } from "./continuity-model.js";
import { ContinuityView } from "./continuity-ui.js";

const state: ContinuityViewState = {
    phase: "ready",
    mode: "view",
    locale: "ko-KR",
    theme: "light",
    errorCode: null,
    actionPending: false,
    checkpointState: "none",
    snapshot: {
        schema_version: CONTINUITY_SNAPSHOT_SCHEMA,
        client_surface: "chatgpt_web",
        locale: "ko-KR",
        project_id: "prj_12345678",
        head_revision_id: "rev_abcdefgh",
        warning_count: 1,
        conflict_state: "none",
        revisions: [
            {
                revision_id: "rev_abcdefgh",
                parent_revision_ids: [],
                created_at: "2026-09-05T00:00:00Z",
                change_kind: "edited",
            },
        ],
        next_cursor: null,
    },
};
const handlers = {
    onBeginCheckpoint: () => undefined,
    onConfirmCheckpoint: () => undefined,
    onCancelCheckpoint: () => undefined,
    onRefresh: () => undefined,
};

test("renders bounded project continuity with two actions and no raw IDs", () => {
    const html = renderToStaticMarkup(
        <ContinuityView state={state} {...handlers} />,
    );
    assert.match(html, /최근 리비전/);
    assert.match(html, /체크포인트 만들기/);
    assert.match(html, /새로고침/);
    assert.match(html, /prj_12…/);
    assert.match(html, /rev_ab…/);
    assert.doesNotMatch(html, /prj_12345678/);
    assert.equal((html.match(/<button/g) ?? []).length, 2);
});

test("renders one conflict action and suppresses checkpoint write", () => {
    const html = renderToStaticMarkup(
        <ContinuityView
            state={{
                ...state,
                snapshot: { ...state.snapshot!, conflict_state: "diverged" },
            }}
            {...handlers}
        />,
    );
    assert.match(html, /리비전이 갈라졌습니다/);
    assert.doesNotMatch(html, /체크포인트 만들기/);
    assert.equal((html.match(/<button/g) ?? []).length, 1);
});

test("renders an explicit checkpoint confirmation with primary and secondary actions", () => {
    const html = renderToStaticMarkup(
        <ContinuityView
            state={{ ...state, mode: "confirm_checkpoint" }}
            {...handlers}
        />,
    );
    assert.match(html, /변경 불가능한 체크포인트/);
    assert.match(html, /확인 후 만들기/);
    assert.match(html, /취소/);
    assert.equal((html.match(/<button/g) ?? []).length, 2);
});

test("renders bounded local error copy without private details", () => {
    const html = renderToStaticMarkup(
        <ContinuityView
            state={{
                ...state,
                phase: "recoverable_error",
                locale: "en-US",
                snapshot: null,
                errorCode: "CHECKPOINT_FAILED",
            }}
            {...handlers}
        />,
    );
    assert.match(html, /checkpoint could not be created/i);
    assert.doesNotMatch(html, /D:\\|secret|raw/i);
});
