import assert from "node:assert/strict";
import test from "node:test";

import {
    ContinuityController,
    type ContinuityHostContext,
    type ContinuityPort,
    type ContinuityServerCall,
    type ContinuityToolResultNotification,
} from "./continuity-controller.js";
import {
    CONTINUITY_RENDER_REQUEST_SCHEMA,
    CONTINUITY_SNAPSHOT_SCHEMA,
    PUBLIC_RESULT_SCHEMA,
} from "./continuity-model.js";

const RENDER_REQUEST = {
    schema_version: CONTINUITY_RENDER_REQUEST_SCHEMA,
    client_surface: "chatgpt_web",
    locale: "ko-KR",
    project_id: "prj_12345678",
} as const;
const SNAPSHOT = {
    schema_version: CONTINUITY_SNAPSHOT_SCHEMA,
    client_surface: "chatgpt_web",
    locale: "ko-KR",
    project_id: "prj_12345678",
    head_revision_id: "rev_abcdefgh",
    warning_count: 0,
    conflict_state: "none",
    revisions: [
        {
            revision_id: "rev_abcdefgh",
            parent_revision_ids: ["rev_parent123"],
            created_at: "2026-09-05T00:00:00Z",
            change_kind: "edited",
        },
    ],
    next_cursor: null,
} as const;

function publicBase(requestId: string) {
    return {
        schema_version: PUBLIC_RESULT_SCHEMA,
        request_id: requestId,
        outcome: "succeeded",
        safe_summary: "bounded",
        warnings: [],
    } as const;
}

class FakePort implements ContinuityPort {
    readonly order: string[] = [];
    readonly calls: ContinuityServerCall[] = [];
    readonly results: unknown[] = [];
    context: ContinuityHostContext = { locale: "en-US", theme: "dark" };
    failConnect = false;
    closed = 0;
    toolInput: ((value: unknown) => void) | undefined;
    toolResult: ((value: ContinuityToolResultNotification) => void) | undefined;
    toolCancelled: (() => void) | undefined;
    hostContextChanged: ((value: ContinuityHostContext) => void) | undefined;
    teardown: (() => void) | undefined;

    private set<T>(
        name: string,
        assign: (handler: T | undefined) => void,
        handler: T,
    ): () => void {
        this.order.push(name);
        assign(handler);
        return () => assign(undefined);
    }

    onToolInput(handler: (value: unknown) => void): () => void {
        return this.set(
            "toolinput",
            (value) => (this.toolInput = value),
            handler,
        );
    }
    onToolResult(
        handler: (value: ContinuityToolResultNotification) => void,
    ): () => void {
        return this.set(
            "toolresult",
            (value) => (this.toolResult = value),
            handler,
        );
    }
    onToolCancelled(handler: () => void): () => void {
        return this.set(
            "toolcancelled",
            (value) => (this.toolCancelled = value),
            handler,
        );
    }
    onHostContextChanged(
        handler: (value: ContinuityHostContext) => void,
    ): () => void {
        return this.set(
            "hostcontextchanged",
            (value) => (this.hostContextChanged = value),
            handler,
        );
    }
    onTeardown(handler: () => void): () => void {
        return this.set(
            "teardown",
            (value) => (this.teardown = value),
            handler,
        );
    }
    async connect(): Promise<void> {
        this.order.push("connect");
        if (this.failConnect) throw new Error("private transport detail");
    }
    getHostContext(): ContinuityHostContext {
        return this.context;
    }
    async callServerTool(call: ContinuityServerCall): Promise<unknown> {
        this.calls.push(call);
        return this.results.shift() ?? { isError: true };
    }
    async close(): Promise<void> {
        this.closed += 1;
    }
}

function controller(
    port: FakePort,
    requestIds = ["req_open1234", "req_history1", "req_check123"],
) {
    let index = 0;
    return new ContinuityController(
        port,
        () => requestIds[index++] ?? "req_fallback1",
        () => "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
    );
}

async function ready(port: FakePort, value: unknown = SNAPSHOT) {
    const valueController = controller(port);
    await valueController.start();
    port.toolInput?.(RENDER_REQUEST);
    port.toolResult?.({ structuredContent: value });
    return valueController;
}

test("registers lifecycle handlers before connect and waits for approved input", async () => {
    const port = new FakePort();
    const value = controller(port);
    await value.start();
    assert.deepEqual(port.order, [
        "toolinput",
        "toolresult",
        "toolcancelled",
        "hostcontextchanged",
        "teardown",
        "connect",
    ]);
    assert.equal(value.getState().phase, "approval_pending");
    assert.equal(value.getState().locale, "en-US");
    assert.equal(value.getState().theme, "dark");
});

test("requires matching approved identity before becoming ready", async () => {
    const port = new FakePort();
    const value = controller(port);
    await value.start();
    port.toolResult?.({ structuredContent: SNAPSHOT });
    assert.equal(value.getState().errorCode, "INVALID_TOOL_RESULT");

    const otherPort = new FakePort();
    const other = controller(otherPort);
    await other.start();
    otherPort.toolInput?.(RENDER_REQUEST);
    otherPort.toolResult?.({
        structuredContent: { ...SNAPSHOT, project_id: "prj_other1234" },
    });
    assert.equal(other.getState().errorCode, "INVALID_TOOL_RESULT");
});

test("refreshes open and history through exact read-only calls", async () => {
    const port = new FakePort();
    const value = await ready(port);
    port.results.push(
        {
            structuredContent: {
                ...publicBase("req_open1234"),
                project_id: "prj_12345678",
                head_revision_id: "rev_newhead12",
                warning_count: 2,
                conflict_state: "stale",
                recommended_actions: ["refresh"],
            },
        },
        {
            structuredContent: {
                ...publicBase("req_history1"),
                revisions: [
                    {
                        revision_id: "rev_older1234",
                        parent_revision_ids: [],
                        created_at: "2026-09-04T00:00:00Z",
                        summary: "created",
                    },
                    {
                        revision_id: "rev_newhead12",
                        parent_revision_ids: ["rev_older1234"],
                        created_at: "2026-09-05T00:00:00Z",
                        summary: "edited heading",
                    },
                ],
                next_cursor: "cursor_12345678",
            },
        },
    );
    await value.refresh();
    assert.deepEqual(
        port.calls.map((call) => call.name),
        ["project_open", "project_history"],
    );
    assert.deepEqual(port.calls[0], {
        name: "project_open",
        arguments: {
            client_surface: "chatgpt_web",
            locale: "ko-KR",
            request_id: "req_open1234",
            project_id: "prj_12345678",
            include: [
                "head",
                "checkpoints",
                "warnings",
                "conflicts",
                "recommended_actions",
            ],
        },
    });
    assert.equal(value.getState().snapshot?.head_revision_id, "rev_newhead12");
    assert.equal(
        value.getState().snapshot?.revisions[0]?.change_kind,
        "edited",
    );
    assert.equal(value.getState().snapshot?.conflict_state, "stale");
});

test("checkpoint requires a second explicit click and exact head revision", async () => {
    const port = new FakePort();
    const value = await ready(port);
    value.beginCheckpoint();
    assert.equal(value.getState().mode, "confirm_checkpoint");
    assert.equal(port.calls.length, 0);
    port.results.push({
        structuredContent: {
            ...publicBase("req_open1234"),
            checkpoint_id: "chk_abcdefgh",
            revision_id: "rev_abcdefgh",
            replayed: false,
        },
    });
    await value.confirmCheckpoint();
    assert.deepEqual(port.calls, [
        {
            name: "project_checkpoint",
            arguments: {
                client_surface: "chatgpt_web",
                locale: "ko-KR",
                request_id: "req_open1234",
                project_id: "prj_12345678",
                expected_revision: "rev_abcdefgh",
                idempotency_key: "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
                revision_id: "rev_abcdefgh",
                label: "HWPX Agent checkpoint",
            },
        },
    ]);
    assert.equal(value.getState().checkpointState, "saved");
    assert.equal(value.getState().mode, "view");
});

test("conflicts disable checkpoint and cancellation causes no server call", async () => {
    const port = new FakePort();
    const value = await ready(port, {
        ...SNAPSHOT,
        conflict_state: "diverged",
    });
    value.beginCheckpoint();
    await value.confirmCheckpoint();
    assert.equal(value.getState().mode, "view");
    assert.equal(port.calls.length, 0);

    const cleanPort = new FakePort();
    const clean = await ready(cleanPort);
    clean.beginCheckpoint();
    clean.cancelCheckpoint();
    assert.equal(clean.getState().mode, "view");
    assert.equal(cleanPort.calls.length, 0);
});

test("fails closed on mismatched response IDs and raw tool errors", async () => {
    const port = new FakePort();
    const value = await ready(port);
    port.results.push({
        structuredContent: {
            ...publicBase("req_wrong123"),
            project_id: "prj_12345678",
            head_revision_id: "rev_abcdefgh",
            warning_count: 0,
            conflict_state: "none",
            recommended_actions: [],
        },
    });
    await value.refresh();
    assert.equal(value.getState().errorCode, "REFRESH_FAILED");
    assert.equal(value.getState().snapshot, null);

    const duplicatePort = new FakePort();
    const duplicate = controller(duplicatePort, [
        "req_duplicate1",
        "req_duplicate1",
    ]);
    await duplicate.start();
    duplicatePort.toolInput?.(RENDER_REQUEST);
    duplicatePort.toolResult?.({ structuredContent: SNAPSHOT });
    await duplicate.refresh();
    assert.equal(duplicate.getState().errorCode, "REFRESH_FAILED");
    assert.equal(duplicatePort.calls.length, 0);
});

test("teardown removes handlers and closes only once", async () => {
    const port = new FakePort();
    const value = controller(port);
    await value.start();
    port.teardown?.();
    await new Promise<void>((resolve) => queueMicrotask(() => resolve()));
    assert.equal(value.getState().phase, "closed");
    assert.equal(port.toolInput, undefined);
    assert.equal(port.closed, 1);
    await value.close();
    assert.equal(port.closed, 1);
});
