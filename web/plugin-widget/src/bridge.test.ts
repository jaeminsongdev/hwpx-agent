import assert from "node:assert/strict";
import test from "node:test";

import {
    WidgetBridgeController,
    type HostContextInput,
    type ProjectOpenCall,
    type ToolResultInput,
    type WidgetPort,
} from "./bridge.js";
import {
    WIDGET_RENDER_REQUEST_SCHEMA,
    WIDGET_SNAPSHOT_SCHEMA,
} from "./model.js";

const SNAPSHOT = {
    schema_version: WIDGET_SNAPSHOT_SCHEMA,
    client_surface: "chatgpt_web",
    locale: "ko-KR",
    project_id: "prj_12345678",
    revision_id: "rev_abcdefgh",
    validation_state: "verified",
} as const;
const RENDER_REQUEST = {
    schema_version: WIDGET_RENDER_REQUEST_SCHEMA,
    client_surface: "chatgpt_web",
    locale: "ko-KR",
    project_id: "prj_12345678",
} as const;

class FakePort implements WidgetPort {
    readonly order: string[] = [];
    readonly calls: ProjectOpenCall[] = [];
    closed = 0;
    context: HostContextInput = { locale: "en-US", theme: "dark" };
    failConnect = false;
    callResult: unknown = {};
    toolInput: ((value: unknown) => void) | undefined = undefined;
    toolResult: ((value: ToolResultInput) => void) | undefined = undefined;
    toolCancelled: (() => void) | undefined = undefined;
    hostContextChanged: ((value: HostContextInput) => void) | undefined =
        undefined;
    teardown: (() => void) | undefined = undefined;

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
    onToolResult(handler: (value: ToolResultInput) => void): () => void {
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
        handler: (value: HostContextInput) => void,
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
        if (this.failConnect) {
            throw new Error("private transport detail");
        }
    }
    getHostContext(): HostContextInput {
        return this.context;
    }
    async callServerTool(call: ProjectOpenCall): Promise<unknown> {
        this.calls.push(call);
        return this.callResult;
    }
    async close(): Promise<void> {
        this.closed += 1;
    }
}

test("registers every lifecycle handler before connect and treats missing input as approval pending", async () => {
    const port = new FakePort();
    const controller = new WidgetBridgeController(port, () => "req_12345678");
    await controller.start();
    assert.deepEqual(port.order, [
        "toolinput",
        "toolresult",
        "toolcancelled",
        "hostcontextchanged",
        "teardown",
        "connect",
    ]);
    assert.deepEqual(controller.getState(), {
        phase: "approval_pending",
        locale: "en-US",
        theme: "dark",
        snapshot: null,
        errorCode: null,
        actionPending: false,
    });
});

test("uses approved input only as a pending signal and trusts only the server result", async () => {
    const port = new FakePort();
    const controller = new WidgetBridgeController(port, () => "req_12345678");
    await controller.start();
    port.toolInput?.(RENDER_REQUEST);
    assert.equal(controller.getState().phase, "approval_pending");
    assert.equal(controller.getState().snapshot, null);
    port.toolResult?.({ structuredContent: SNAPSHOT });
    assert.equal(controller.getState().phase, "ready");
    await controller.continueProject();
    assert.deepEqual(port.calls, [
        {
            name: "project_open",
            arguments: {
                client_surface: "chatgpt_web",
                locale: "ko-KR",
                request_id: "req_12345678",
                project_id: "prj_12345678",
                include: [
                    "head",
                    "warnings",
                    "conflicts",
                    "target",
                    "recent_artifacts",
                    "recommended_actions",
                ],
            },
        },
    ]);
});

test("rejects a server result that does not match the approved project", async () => {
    const port = new FakePort();
    const controller = new WidgetBridgeController(port, () => "req_12345678");
    await controller.start();
    port.toolInput?.(RENDER_REQUEST);
    port.toolResult?.({
        structuredContent: { ...SNAPSHOT, project_id: "prj_other1234" },
    });
    assert.equal(controller.getState().errorCode, "INVALID_TOOL_RESULT");
});

test("rejects a server result that arrives without approved input", async () => {
    const port = new FakePort();
    const controller = new WidgetBridgeController(port, () => "req_12345678");
    await controller.start();
    port.toolResult?.({ structuredContent: SNAPSHOT });
    assert.equal(controller.getState().errorCode, "INVALID_TOOL_RESULT");
    assert.equal(controller.getState().snapshot, null);
});

test("fails closed on malformed request IDs and explicit tool errors", async () => {
    const badIdPort = new FakePort();
    const badId = new WidgetBridgeController(badIdPort, () => "D:\\private");
    await badId.start();
    badIdPort.toolInput?.(RENDER_REQUEST);
    badIdPort.toolResult?.({ structuredContent: SNAPSHOT });
    await badId.continueProject();
    assert.equal(badId.getState().errorCode, "TOOL_CALL_FAILED");
    assert.equal(badIdPort.calls.length, 0);

    const errorPort = new FakePort();
    errorPort.callResult = { isError: true, content: [{ text: "private" }] };
    const error = new WidgetBridgeController(errorPort, () => "req_12345678");
    await error.start();
    errorPort.toolInput?.(RENDER_REQUEST);
    errorPort.toolResult?.({ structuredContent: SNAPSHOT });
    await error.continueProject();
    assert.equal(error.getState().errorCode, "TOOL_CALL_FAILED");
});

test("maps malformed data, cancellation and connection failure to bounded local codes", async () => {
    const malformedPort = new FakePort();
    const malformed = new WidgetBridgeController(
        malformedPort,
        () => "req_12345678",
    );
    await malformed.start();
    malformedPort.toolInput?.({ path: "D:\\private" });
    assert.equal(malformed.getState().errorCode, "INVALID_TOOL_INPUT");

    const cancelledPort = new FakePort();
    const cancelled = new WidgetBridgeController(
        cancelledPort,
        () => "req_12345678",
    );
    await cancelled.start();
    cancelledPort.toolCancelled?.();
    assert.equal(cancelled.getState().errorCode, "TOOL_CANCELLED");

    const failedPort = new FakePort();
    failedPort.failConnect = true;
    const failed = new WidgetBridgeController(failedPort, () => "req_12345678");
    await failed.start();
    assert.equal(failed.getState().errorCode, "CONNECT_FAILED");
});

test("teardown removes handlers, closes the port and leaves a terminal state", async () => {
    const port = new FakePort();
    const controller = new WidgetBridgeController(port, () => "req_12345678");
    await controller.start();
    port.teardown?.();
    await new Promise<void>((resolve) => queueMicrotask(() => resolve()));
    assert.equal(controller.getState().phase, "closed");
    assert.equal(port.toolInput, undefined);
    assert.equal(port.closed, 1);
    await controller.close();
    assert.equal(port.closed, 1);
});
