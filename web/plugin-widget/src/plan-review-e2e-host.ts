import {
    AppBridge,
    PostMessageTransport,
} from "@modelcontextprotocol/ext-apps/app-bridge";
import {
    PLAN_REVIEW_REQUEST_SCHEMA,
    PLAN_REVIEW_SNAPSHOT_SCHEMA,
    PUBLIC_RESULT_SCHEMA,
} from "./plan-review-model.js";

type JsonRecord = Record<string, unknown>;
const calls: Array<{ name: string; arguments: JsonRecord }> = [];
const result = document.getElementById("e2e-result");
const frame = document.getElementById(
    "plan-review-frame",
) as HTMLIFrameElement | null;
function fail(code: string): never {
    if (result !== null) {
        result.dataset.state = "fail";
        result.textContent = code;
    }
    throw new Error(code);
}
function base(requestId: unknown) {
    if (typeof requestId !== "string") fail("invalid_request_id");
    return {
        schema_version: PUBLIC_RESULT_SCHEMA,
        request_id: requestId,
        outcome: "succeeded",
        safe_summary: "bounded",
        warnings: [],
    } as const;
}
function waitFor(predicate: () => boolean, code: string): Promise<void> {
    const deadline = performance.now() + 6000;
    return new Promise((resolve, reject) => {
        const poll = () => {
            if (predicate()) {
                resolve();
                return;
            }
            if (performance.now() >= deadline) {
                reject(new Error(code));
                return;
            }
            setTimeout(poll, 20);
        };
        poll();
    });
}
function findButton(label: string): HTMLButtonElement | undefined {
    const match = [
        ...(frame?.contentDocument?.querySelectorAll("button") ?? []),
    ].find((item) => item.textContent?.trim() === label);
    return match?.tagName === "BUTTON"
        ? (match as HTMLButtonElement)
        : undefined;
}
function button(label: string): HTMLButtonElement {
    return findButton(label) ?? fail(`button_missing:${label}`);
}
function requireCallCount(expected: number, code: string): void {
    if (calls.length !== expected) fail(code);
}

async function runFlow() {
    await waitFor(
        () => findButton("계획 다시 검증") !== undefined,
        "initial_render_timeout",
    );
    button("계획 다시 검증").click();
    await waitFor(() => calls.length === 2, "revalidate_calls_timeout");
    await waitFor(
        () =>
            frame?.contentDocument?.body.textContent?.includes(
                "다시 검증했습니다",
            ) === true,
        "revalidate_render_timeout",
    );
    button("실행 검토").click();
    await waitFor(
        () => findButton("확인 후 실행") !== undefined,
        "confirm_render_timeout",
    );
    const checkbox = frame?.contentDocument?.querySelector(
        'input[type="checkbox"]',
    ) as HTMLInputElement | null;
    if (checkbox === null) fail("acknowledgement_missing");
    if (!button("확인 후 실행").disabled)
        fail("execution_enabled_before_acknowledgement");
    requireCallCount(2, "execution_before_acknowledgement");
    button("확인 후 실행").click();
    requireCallCount(2, "early_execution_dispatched");
    checkbox.click();
    await waitFor(
        () => button("확인 후 실행").disabled === false,
        "acknowledgement_timeout",
    );
    button("확인 후 실행").click();
    await waitFor(() => calls.length === 5, "execution_calls_timeout");
    await waitFor(
        () =>
            frame?.contentDocument?.body.textContent?.includes(
                "작업을 제출했습니다",
            ) === true,
        "execution_render_timeout",
    );
    const names = calls.map((item) => item.name).join(",");
    if (
        names !==
        "capability_check,document_edit,capability_check,document_edit,document_edit"
    )
        fail("call_order_mismatch");
    const [checkOne, dryOne, checkTwo, dryTwo, execute] = calls;
    if (
        checkOne?.arguments.revision_id !== "rev_e2ebase123" ||
        checkTwo?.arguments.revision_id !== "rev_e2ebase123" ||
        dryOne?.arguments.dry_run !== true ||
        dryTwo?.arguments.dry_run !== true ||
        execute?.arguments.dry_run !== false ||
        execute?.arguments.expected_revision !== "rev_e2ebase123" ||
        execute?.arguments.plan_id !== "plan_e2ereview1" ||
        execute?.arguments.best_effort !== false ||
        execute?.arguments.allow_signature_invalidation !== false ||
        typeof execute?.arguments.idempotency_key !== "string" ||
        dryTwo?.arguments.idempotency_key === execute?.arguments.idempotency_key
    )
        fail("call_contract_mismatch");
    if (!button("실행 검토").disabled || !button("계획 다시 검증").disabled)
        fail("submitted_plan_can_be_rearmed");
    button("실행 검토").click();
    button("계획 다시 검증").click();
    await new Promise((resolve) => setTimeout(resolve, 50));
    requireCallCount(5, "submitted_plan_dispatched_again");
    if (findButton("확인 후 실행") !== undefined)
        fail("submitted_plan_dispatched_again");
    if (result !== null) {
        result.dataset.state = "pass";
        result.textContent =
            "PASS calls=5 order=capability_check,document_edit(dry),capability_check,document_edit(dry),document_edit(execute)";
    }
}

async function main() {
    if (frame === null || result === null || frame.contentWindow === null)
        fail("harness_dom_missing");
    const route = [
        {
            capability_id: "paragraph.text_replace",
            selected_backend: "direct_hwpx",
            support_level: "verified",
            supported: true,
        },
        {
            capability_id: "table.cell_style",
            selected_backend: "hancom_2020",
            // Synthetic bridge fixture, not an actual Hangul capability receipt.
            support_level: "verified",
            supported: true,
        },
        {
            capability_id: "document.semantic_validate",
            selected_backend: "hybrid",
            support_level: "verified",
            supported: true,
        },
    ];
    const bridge = new AppBridge(
        null,
        { name: "HWPX Agent local plan review E2E host", version: "1.0.0" },
        { serverTools: {} },
        {
            hostContext: {
                locale: "ko-KR",
                theme: "light",
                displayMode: "inline",
            },
        },
    );
    bridge.oncalltool = async (params) => {
        const args = (params.arguments ?? {}) as JsonRecord;
        calls.push({ name: params.name, arguments: args });
        const common = base(args.request_id);
        if (params.name === "capability_check")
            return {
                content: [],
                structuredContent: {
                    ...common,
                    capabilities: route.map((item) => ({
                        ...item,
                        estimated_job_class: "short",
                        constraints: [],
                        unverified_reasons: [],
                    })),
                },
            };
        if (params.name === "document_edit") {
            if (args.dry_run === true)
                return {
                    content: [],
                    structuredContent: {
                        ...common,
                        job_id: null,
                        revision_id: null,
                        artifact: null,
                        commit_state: "not_started",
                        validation_state: "verified",
                    },
                };
            return {
                content: [],
                structuredContent: {
                    ...common,
                    outcome: "accepted",
                    job_id: "job_e2equeued12",
                    revision_id: null,
                    artifact: null,
                    commit_state: "pending",
                    validation_state: "not_run",
                },
            };
        }
        fail("unexpected_tool_call");
    };
    bridge.oninitialized = () => {
        void bridge.sendToolInput({
            arguments: {
                schema_version: PLAN_REVIEW_REQUEST_SCHEMA,
                client_surface: "codex_local",
                locale: "ko-KR",
                project_id: "prj_e2eproject1",
                source_revision_id: "rev_e2ebase123",
                plan_id: "plan_e2ereview1",
            },
        });
        void bridge.sendToolResult({
            content: [],
            structuredContent: {
                schema_version: PLAN_REVIEW_SNAPSHOT_SCHEMA,
                client_surface: "codex_local",
                locale: "ko-KR",
                project_id: "prj_e2eproject1",
                source_revision_id: "rev_e2ebase123",
                plan_id: "plan_e2ereview1",
                risk_level: "high",
                estimated_page_effect: "document_wide",
                route,
                route_digest: "a".repeat(64),
                diff: {
                    added: 4,
                    modified: 7,
                    removed: 0,
                    categories: [
                        { kind: "paragraph", count: 5 },
                        { kind: "table", count: 3 },
                        { kind: "style", count: 3 },
                    ],
                },
                warnings: [
                    {
                        code: "DOCUMENT_WIDE_EFFECT",
                        severity: "warning",
                        kind: "layout",
                    },
                ],
                signature_impact: "none",
                dry_run_state: "verified",
                execution_allowed: true,
            },
        });
        setTimeout(
            () =>
                void runFlow().catch((error: unknown) =>
                    fail(
                        error instanceof Error ? error.message : "flow_failed",
                    ),
                ),
            100,
        );
    };
    const connection = bridge.connect(
        new PostMessageTransport(frame.contentWindow, frame.contentWindow),
    );
    frame.src = "plan-review-widget-v1.html";
    await connection;
}
void main().catch((error: unknown) =>
    fail(error instanceof Error ? error.message : "harness_failed"),
);
