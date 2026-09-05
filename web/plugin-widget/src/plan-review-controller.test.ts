import assert from "node:assert/strict";
import test from "node:test";
import {
    PlanReviewController,
    MAX_EXECUTION_BINDINGS,
    MAX_CORRELATION_IDS,
    type PlanReviewHostContext,
    type PlanReviewPort,
    type PlanReviewServerCall,
    type PlanReviewToolResultNotification,
} from "./plan-review-controller.js";
import {
    PLAN_REVIEW_REQUEST_SCHEMA,
    PLAN_REVIEW_SNAPSHOT_SCHEMA,
    PUBLIC_RESULT_SCHEMA,
} from "./plan-review-model.js";

const route = [
    {
        capability_id: "paragraph.text_replace",
        selected_backend: "direct_hwpx",
        support_level: "verified",
        supported: true,
    },
] as const;
const input = {
    schema_version: PLAN_REVIEW_REQUEST_SCHEMA,
    client_surface: "codex_local",
    locale: "ko-KR",
    project_id: "prj_abcdefgh",
    source_revision_id: "rev_abcdefgh",
    plan_id: "plan_abcdefgh",
};
const snapshot = {
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
    diff: { added: 1, modified: 2, removed: 0, categories: [] },
    warnings: [],
    signature_impact: "none",
    dry_run_state: "verified",
    execution_allowed: true,
};
function common(request_id: unknown) {
    return {
        schema_version: PUBLIC_RESULT_SCHEMA,
        request_id,
        outcome: "succeeded",
        safe_summary: "ok",
        warnings: [],
    };
}
function capability(requestId: unknown, override = {}) {
    return {
        structuredContent: {
            ...common(requestId),
            capabilities: [
                {
                    ...route[0],
                    estimated_job_class: "short",
                    constraints: [],
                    unverified_reasons: [],
                    ...override,
                },
            ],
        },
    };
}
function dryRun(requestId: unknown, override = {}) {
    return {
        structuredContent: {
            ...common(requestId),
            job_id: null,
            revision_id: null,
            artifact: null,
            commit_state: "not_started",
            validation_state: "verified",
            ...override,
        },
    };
}
function execution(requestId: unknown) {
    return {
        structuredContent: {
            ...common(requestId),
            outcome: "accepted",
            job_id: "job_abcdefgh",
            revision_id: null,
            artifact: null,
            commit_state: "pending",
            validation_state: "not_run",
        },
    };
}

class FakePort implements PlanReviewPort {
    input?: (value: unknown) => void;
    result?: (value: PlanReviewToolResultNotification) => void;
    cancelled?: () => void;
    context?: (value: PlanReviewHostContext) => void;
    teardown?: () => void;
    calls: PlanReviewServerCall[] = [];
    responses: Array<(call: PlanReviewServerCall) => unknown> = [];
    registered = 0;
    connected = false;
    closed = 0;
    private bind<T>(assign: (handler: T) => void, handler: T) {
        assign(handler);
        this.registered += 1;
        return () => {
            this.registered -= 1;
        };
    }
    onToolInput(handler: (value: unknown) => void) {
        return this.bind((x) => {
            this.input = x;
        }, handler);
    }
    onToolResult(handler: (value: PlanReviewToolResultNotification) => void) {
        return this.bind((x) => {
            this.result = x;
        }, handler);
    }
    onToolCancelled(handler: () => void) {
        return this.bind((x) => {
            this.cancelled = x;
        }, handler);
    }
    onHostContextChanged(handler: (value: PlanReviewHostContext) => void) {
        return this.bind((x) => {
            this.context = x;
        }, handler);
    }
    onTeardown(handler: () => void) {
        return this.bind((x) => {
            this.teardown = x;
        }, handler);
    }
    async connect() {
        assert.equal(this.registered, 5);
        this.connected = true;
    }
    getHostContext() {
        return { locale: "ko-KR", theme: "light" };
    }
    async callServerTool(call: PlanReviewServerCall) {
        this.calls.push(call);
        const response = this.responses.shift();
        if (response === undefined) throw new Error("missing fake response");
        return response(call);
    }
    async close() {
        this.closed += 1;
    }
}
function ids() {
    let n = 0;
    return () => `req_${String(++n).padStart(8, "0")}`;
}
function keys() {
    let n = 0;
    return () => `00000000-0000-4000-8000-${String(++n).padStart(12, "0")}`;
}
async function ready(port = new FakePort()) {
    const controller = new PlanReviewController(port, ids(), keys());
    await controller.start();
    port.input?.(input);
    port.result?.({ structuredContent: snapshot });
    assert.equal(controller.getState().phase, "ready");
    return { controller, port };
}

test("registers handlers before connecting", async () => {
    const port = new FakePort();
    const controller = new PlanReviewController(port, ids(), keys());
    await controller.start();
    assert.equal(port.connected, true);
    assert.equal(controller.getState().phase, "approval_pending");
});
test("binds render result to all opaque request identities", async () => {
    const port = new FakePort();
    const controller = new PlanReviewController(port, ids(), keys());
    await controller.start();
    port.input?.(input);
    port.result?.({
        structuredContent: { ...snapshot, plan_id: "plan_otherid1" },
    });
    assert.equal(controller.getState().phase, "recoverable_error");
    assert.equal(controller.getState().snapshot, null);
});
test("entering confirmation makes no server call", async () => {
    const { controller, port } = await ready();
    controller.beginExecution();
    assert.equal(controller.getState().mode, "confirm_execution");
    assert.equal(port.calls.length, 0);
});
test("execution requires explicit acknowledgement", async () => {
    const { controller, port } = await ready();
    controller.beginExecution();
    await controller.confirmExecution();
    assert.equal(port.calls.length, 0);
    controller.setAcknowledged(true);
    assert.equal(controller.getState().acknowledged, true);
});
test("revalidation calls exact route then dry-run", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) => dryRun(call.arguments.request_id),
    ];
    await controller.revalidate();
    assert.deepEqual(
        port.calls.map((item) => item.name),
        ["capability_check", "document_edit"],
    );
    const edit = port.calls[1];
    assert.equal(edit?.name, "document_edit");
    if (edit?.name === "document_edit") {
        assert.equal(edit.arguments.dry_run, true);
        assert.equal(edit.arguments.best_effort, false);
        assert.equal(edit.arguments.expected_revision, "rev_abcdefgh");
    }
    assert.equal(controller.getState().executionState, "revalidated");
});
test("route disagreement fails closed", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) =>
            capability(call.arguments.request_id, {
                selected_backend: "hybrid",
            }),
        (call) => dryRun(call.arguments.request_id),
    ];
    await controller.revalidate();
    assert.equal(controller.getState().phase, "recoverable_error");
    assert.equal(controller.getState().snapshot, null);
    assert.equal(port.calls.length, 1);
});
test("invalid dry-run state fails closed", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) =>
            dryRun(call.arguments.request_id, { commit_state: "pending" }),
    ];
    await controller.revalidate();
    assert.equal(controller.getState().errorCode, "REVALIDATION_FAILED");
});
test("new capability constraint fails closed", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) => ({
            structuredContent: {
                ...common(call.arguments.request_id),
                capabilities: [
                    {
                        ...route[0],
                        estimated_job_class: "short",
                        constraints: ["new server constraint"],
                        unverified_reasons: [],
                    },
                ],
            },
        }),
    ];
    await controller.revalidate();
    assert.equal(controller.getState().errorCode, "REVALIDATION_FAILED");
    assert.equal(port.calls.length, 1);
});
test("new dry-run warning fails closed", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) => ({
            structuredContent: {
                ...dryRun(call.arguments.request_id).structuredContent,
                warnings: [{ code: "NEW_WARNING", message: "bounded" }],
            },
        }),
    ];
    await controller.revalidate();
    assert.equal(controller.getState().errorCode, "REVALIDATION_FAILED");
});
test("cancellation during revalidation prevents later dry-run and write", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) => {
            port.cancelled?.();
            return capability(call.arguments.request_id);
        },
    ];
    controller.beginExecution();
    controller.setAcknowledged(true);
    await controller.confirmExecution();
    assert.equal(controller.getState().errorCode, "TOOL_CANCELLED");
    assert.equal(port.calls.length, 1);
});
test("confirmed execution revalidates then writes with a distinct key", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) => dryRun(call.arguments.request_id),
        (call) => execution(call.arguments.request_id),
    ];
    controller.beginExecution();
    controller.setAcknowledged(true);
    await controller.confirmExecution();
    assert.deepEqual(
        port.calls.map((item) => item.name),
        ["capability_check", "document_edit", "document_edit"],
    );
    const dry = port.calls[1];
    const write = port.calls[2];
    assert.equal(dry?.name, "document_edit");
    assert.equal(write?.name, "document_edit");
    if (dry?.name === "document_edit" && write?.name === "document_edit") {
        assert.equal(dry.arguments.dry_run, true);
        assert.equal(write.arguments.dry_run, false);
        assert.notEqual(
            dry.arguments.idempotency_key,
            write.arguments.idempotency_key,
        );
        assert.equal(write.arguments.allow_signature_invalidation, false);
    }
    assert.equal(controller.getState().executionState, "submitted");
});
test("malformed execution response is never promoted", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) => dryRun(call.arguments.request_id),
        (call) => dryRun(call.arguments.request_id),
    ];
    controller.beginExecution();
    controller.setAcknowledged(true);
    await controller.confirmExecution();
    assert.equal(controller.getState().errorCode, "EXECUTION_FAILED");
    assert.equal(controller.getState().snapshot, null);
});

test("submitted plan cannot execute again after review refresh", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) => dryRun(call.arguments.request_id),
        (call) => execution(call.arguments.request_id),
    ];
    controller.beginExecution();
    controller.setAcknowledged(true);
    await controller.confirmExecution();
    controller.beginExecution();
    assert.equal(controller.getState().mode, "view");
    await controller.revalidate();
    assert.equal(controller.getState().executionState, "submitted");
    port.input?.({ ...input });
    port.result?.({ structuredContent: { ...snapshot } });
    assert.equal(controller.getState().executionState, "submitted");
    controller.beginExecution();
    controller.setAcknowledged(true);
    await controller.confirmExecution();
    assert.equal(port.calls.length, 3);
});

test("late execution rejection preserves a newer approved plan", async () => {
    const { controller, port } = await ready();
    const reply = Promise.withResolvers<unknown>();
    const dispatched = Promise.withResolvers<void>();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) => dryRun(call.arguments.request_id),
        () => {
            dispatched.resolve();
            return reply.promise;
        },
    ];
    controller.beginExecution();
    controller.setAcknowledged(true);
    const pending = controller.confirmExecution();
    await dispatched.promise;
    port.input?.({ ...input, plan_id: "plan_newvalue1" });
    port.result?.({
        structuredContent: { ...snapshot, plan_id: "plan_newvalue1" },
    });
    reply.reject(new Error("untrusted transport details"));
    await pending;
    assert.equal(controller.getState().phase, "ready");
    assert.equal(controller.getState().snapshot?.plan_id, "plan_newvalue1");
    assert.equal(controller.getState().errorCode, null);
});

test("approved request identity does not alias host input", async () => {
    const port = new FakePort();
    const controller = new PlanReviewController(port, ids(), keys());
    await controller.start();
    const message = { ...input };
    port.input?.(message);
    message.plan_id = "plan_unapproved";
    port.result?.({
        structuredContent: { ...snapshot, plan_id: message.plan_id },
    });
    assert.equal(controller.getState().phase, "recoverable_error");
    assert.equal(controller.getState().snapshot, null);
});
test("blocked snapshot never enters confirmation", async () => {
    const port = new FakePort();
    const controller = new PlanReviewController(port, ids(), keys());
    await controller.start();
    port.input?.(input);
    port.result?.({
        structuredContent: {
            ...snapshot,
            warnings: [
                { code: "BLOCKED", severity: "blocking", kind: "validation" },
            ],
            execution_allowed: false,
        },
    });
    controller.beginExecution();
    assert.equal(controller.getState().mode, "view");
});

for (const outcome of [
    "lost",
    "malformed",
    "wrong_request",
    "new_warning",
] as const) {
    test(`uncertain ${outcome} execution stays non-retryable across refresh`, async () => {
        const { controller, port } = await ready();
        port.responses = [
            (call) => capability(call.arguments.request_id),
            (call) => dryRun(call.arguments.request_id),
            (call) => {
                if (outcome === "lost")
                    throw new Error("private transport detail");
                if (outcome === "malformed") return {};
                const response = execution(
                    outcome === "wrong_request"
                        ? "req_mismatch1"
                        : call.arguments.request_id,
                );
                return outcome === "new_warning"
                    ? {
                          structuredContent: {
                              ...response.structuredContent,
                              warnings: [
                                  {
                                      code: "NEW_WARNING",
                                      message: "not approved",
                                  },
                              ],
                          },
                      }
                    : response;
            },
        ];
        controller.beginExecution();
        controller.setAcknowledged(true);
        await controller.confirmExecution();
        assert.equal(controller.getState().phase, "recoverable_error");
        assert.equal(controller.getState().executionState, "unconfirmed");
        assert.equal(controller.getState().snapshot, null);
        port.input?.({
            ...input,
            locale: "en-US",
            client_surface: "codex_remote",
        });
        port.result?.({
            structuredContent: {
                ...snapshot,
                locale: "en-US",
                client_surface: "codex_remote",
            },
        });
        assert.equal(controller.getState().executionState, "unconfirmed");
        controller.beginExecution();
        controller.setAcknowledged(true);
        await controller.confirmExecution();
        await controller.revalidate();
        assert.equal(port.calls.length, 3);
    });
}

test("late accepted execution is recorded without replacing a newer plan", async () => {
    const { controller, port } = await ready();
    const reply = Promise.withResolvers<unknown>();
    const dispatched = Promise.withResolvers<PlanReviewServerCall>();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) => dryRun(call.arguments.request_id),
        (call) => {
            dispatched.resolve(call);
            return reply.promise;
        },
    ];
    controller.beginExecution();
    controller.setAcknowledged(true);
    const pending = controller.confirmExecution();
    const write = await dispatched.promise;
    port.input?.({ ...input, plan_id: "plan_newvalue1" });
    port.result?.({
        structuredContent: { ...snapshot, plan_id: "plan_newvalue1" },
    });
    reply.resolve(execution(write.arguments.request_id));
    await pending;
    assert.equal(controller.getState().snapshot?.plan_id, "plan_newvalue1");
    assert.equal(controller.getState().executionState, "none");
    controller.beginExecution();
    assert.equal(controller.getState().mode, "confirm_execution");
    controller.cancelExecution();
    port.input?.(input);
    port.result?.({ structuredContent: snapshot });
    assert.equal(controller.getState().executionState, "submitted");
    controller.beginExecution();
    assert.equal(controller.getState().mode, "view");
    assert.equal(port.calls.length, 3);
});

test("cancellation after dispatch cannot grant a second write", async () => {
    const { controller, port } = await ready();
    const reply = Promise.withResolvers<unknown>();
    const dispatched = Promise.withResolvers<void>();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) => dryRun(call.arguments.request_id),
        () => {
            dispatched.resolve();
            return reply.promise;
        },
    ];
    controller.beginExecution();
    controller.setAcknowledged(true);
    const pending = controller.confirmExecution();
    await dispatched.promise;
    port.cancelled?.();
    assert.equal(controller.getState().executionState, "unconfirmed");
    port.input?.(input);
    port.result?.({ structuredContent: snapshot });
    controller.beginExecution();
    controller.setAcknowledged(true);
    await controller.confirmExecution();
    reply.reject(new Error("lost reply"));
    await pending;
    assert.equal(controller.getState().phase, "ready");
    assert.equal(controller.getState().executionState, "unconfirmed");
    assert.equal(port.calls.length, 3);
});

test("overlapping confirm calls dispatch exactly once", async () => {
    const { controller, port } = await ready();
    port.responses = [
        (call) => capability(call.arguments.request_id),
        (call) => dryRun(call.arguments.request_id),
        (call) => execution(call.arguments.request_id),
    ];
    controller.beginExecution();
    controller.setAcknowledged(true);
    await Promise.all([
        controller.confirmExecution(),
        controller.confirmExecution(),
        controller.confirmExecution(),
    ]);
    assert.equal(port.calls.length, 3);
    assert.equal(controller.getState().executionState, "submitted");
});

for (const duplicate of ["request", "key"] as const) {
    test(`duplicate ${duplicate} correlation is rejected before write`, async () => {
        const port = new FakePort();
        const nextId = ids();
        let idCalls = 0;
        const controller = new PlanReviewController(
            port,
            duplicate === "request"
                ? () => (++idCalls === 3 ? "req_00000001" : nextId())
                : nextId,
            duplicate === "key"
                ? () => "00000000-0000-4000-8000-000000000001"
                : keys(),
        );
        await controller.start();
        port.input?.(input);
        port.result?.({ structuredContent: snapshot });
        port.responses = [
            (call) => capability(call.arguments.request_id),
            (call) => dryRun(call.arguments.request_id),
        ];
        controller.beginExecution();
        controller.setAcknowledged(true);
        await controller.confirmExecution();
        assert.equal(controller.getState().errorCode, "EXECUTION_FAILED");
        assert.equal(controller.getState().executionState, "none");
        assert.equal(port.calls.length, 2);
    });
}

test("execution cache reaches a hard bound without evicting old plans", async () => {
    const { controller, port } = await ready();
    for (let i = 0; i < MAX_EXECUTION_BINDINGS; i++) {
        const plan_id = `plan_${String(i).padStart(8, "0")}`;
        port.input?.({ ...input, plan_id });
        port.result?.({ structuredContent: { ...snapshot, plan_id } });
        port.responses = [
            (call) => capability(call.arguments.request_id),
            (call) => dryRun(call.arguments.request_id),
            (call) => execution(call.arguments.request_id),
        ];
        controller.beginExecution();
        controller.setAcknowledged(true);
        await controller.confirmExecution();
        assert.equal(controller.getState().executionState, "submitted");
    }
    port.input?.(input);
    port.result?.({ structuredContent: snapshot });
    controller.beginExecution();
    assert.equal(controller.getState().errorCode, "SESSION_LIMIT_REACHED");
    port.input?.({ ...input, plan_id: "plan_00000000" });
    port.result?.({
        structuredContent: { ...snapshot, plan_id: "plan_00000000" },
    });
    assert.equal(controller.getState().executionState, "submitted");
    controller.beginExecution();
    await controller.confirmExecution();
    assert.equal(port.calls.length, 3 * MAX_EXECUTION_BINDINGS);
});

test("correlation history has a hard bound across repeated validation", async () => {
    const { controller, port } = await ready();
    for (let i = 0; i < MAX_CORRELATION_IDS / 2; i++) {
        port.responses = [
            (call) => capability(call.arguments.request_id),
            (call) => dryRun(call.arguments.request_id),
        ];
        await controller.revalidate();
        assert.equal(controller.getState().executionState, "revalidated");
    }
    await controller.revalidate();
    assert.equal(controller.getState().errorCode, "REVALIDATION_FAILED");
    assert.equal(port.calls.length, MAX_CORRELATION_IDS);
});
test("cancellation clears authoritative data", async () => {
    const { controller, port } = await ready();
    port.cancelled?.();
    assert.equal(controller.getState().phase, "recoverable_error");
    assert.equal(controller.getState().snapshot, null);
});
test("teardown unregisters and closes exactly once", async () => {
    const { controller, port } = await ready();
    port.teardown?.();
    await new Promise((resolve) => setTimeout(resolve, 0));
    await controller.close();
    assert.equal(controller.getState().phase, "closed");
    assert.equal(port.registered, 0);
    assert.equal(port.closed, 1);
});
