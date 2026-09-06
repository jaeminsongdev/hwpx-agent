import assert from "node:assert/strict";
import test from "node:test";

import {
    GitApprovalController,
    type GitApprovalPort,
    type GitApprovalServerCall,
    type GitApprovalToolResultNotification,
} from "./git-approval-controller.js";

const input = {
    workspace_id: "primary",
    operation_id: "op_widget_01",
    output_id: "result_01",
    expected_sha256: "a".repeat(64),
    message: "Publish verified HWPX",
};
const plan = {
    workspace_id: "primary",
    operation_id: "op_widget_01",
    output_id: "result_01",
    output_pathspec: "output/result_01.hwpx",
    expected_output_sha256: "a".repeat(64),
    expected_head: "b".repeat(40),
    expected_head_reference: "refs/heads/main",
    message: "Publish verified HWPX",
    approval: {
        effect: "git_commit",
        target_sha256: "c".repeat(64),
        plan_sha256: "d".repeat(64),
    },
    executed: false,
};
const receipt = {
    workspace_id: "primary",
    operation_id: "op_widget_01",
    output_id: "result_01",
    commit_oid: "e".repeat(40),
    previous_head: "b".repeat(40),
    updated_reference: "refs/heads/main",
    output_sha256: "a".repeat(64),
    target_sha256: "c".repeat(64),
    plan_sha256: "d".repeat(64),
    approved_at_unix_seconds: 100,
    index_synchronized: true,
    executed: true,
};
const resultMeta = {
    "hwpx-agent/git-approval-challenge": "z".repeat(43),
};

class Port implements GitApprovalPort {
    input: ((value: unknown) => void) | null = null;
    result: ((value: GitApprovalToolResultNotification) => void) | null = null;
    cancelled: (() => void) | null = null;
    calls: GitApprovalServerCall[] = [];
    reply: unknown = { structuredContent: receipt };
    onToolInput(handler: (value: unknown) => void) {
        this.input = handler;
        return () => {
            this.input = null;
        };
    }
    onToolResult(handler: (value: GitApprovalToolResultNotification) => void) {
        this.result = handler;
        return () => {
            this.result = null;
        };
    }
    onToolCancelled(handler: () => void) {
        this.cancelled = handler;
        return () => {
            this.cancelled = null;
        };
    }
    onHostContextChanged() {
        return () => {};
    }
    onTeardown() {
        return () => {};
    }
    async connect() {}
    getHostContext() {
        return { theme: "light" as const };
    }
    async callServerTool(call: GitApprovalServerCall): Promise<unknown> {
        this.calls.push(call);
        return this.reply;
    }
    async close() {}
}

async function ready() {
    const port = new Port();
    const controller = new GitApprovalController(port);
    await controller.start();
    port.input!(input);
    port.result!({ structuredContent: plan, _meta: resultMeta });
    assert.equal(controller.getState().phase, "ready");
    return { port, controller };
}

test("confirmation cannot dispatch before explicit acknowledgement", async () => {
    const { port, controller } = await ready();
    await controller.confirm();
    assert.equal(port.calls.length, 0);
    controller.setAcknowledged(true);
    await controller.confirm();
    assert.equal(port.calls.length, 1);
    assert.equal(
        port.calls[0]!.name,
        "local_companion_confirm_and_execute_git_commit",
    );
    assert.equal("confirmation_token" in port.calls[0]!.arguments, false);
    assert.equal(port.calls[0]!.arguments.approval_challenge, "z".repeat(43));
    assert.equal(controller.getState().phase, "succeeded");
});

test("one widget instance never repeats a dispatched effect", async () => {
    const { port, controller } = await ready();
    controller.setAcknowledged(true);
    await Promise.all([
        controller.confirm(),
        controller.confirm(),
        controller.confirm(),
    ]);
    assert.equal(port.calls.length, 1);
    controller.setAcknowledged(true);
    await controller.confirm();
    assert.equal(port.calls.length, 1);
});

test("lost or invalid reply becomes terminal unconfirmed", async () => {
    const { port, controller } = await ready();
    port.reply = { isError: true };
    controller.setAcknowledged(true);
    await controller.confirm();
    assert.equal(controller.getState().phase, "unconfirmed");
    controller.setAcknowledged(true);
    await controller.confirm();
    assert.equal(port.calls.length, 1);
});

test("binding mismatch and injected fields fail closed", async () => {
    const first = new Port();
    const firstController = new GitApprovalController(first);
    await firstController.start();
    first.input!(input);
    first.result!({
        structuredContent: { ...plan, operation_id: "op_other" },
        _meta: resultMeta,
    });
    assert.equal(firstController.getState().phase, "closed");

    const second = new Port();
    const secondController = new GitApprovalController(second);
    await secondController.start();
    second.input!({ ...input, path: "D:\\private.hwpx" });
    assert.equal(secondController.getState().phase, "closed");
});
