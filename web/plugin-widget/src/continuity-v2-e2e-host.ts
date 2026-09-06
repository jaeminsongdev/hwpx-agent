import {
    AppBridge,
    PostMessageTransport,
} from "@modelcontextprotocol/ext-apps/app-bridge";

import {
    CONTINUITY_RENDER_REQUEST_V2_SCHEMA,
    CONTINUITY_SNAPSHOT_V2_SCHEMA,
    PUBLIC_RESULT_SCHEMA,
} from "./continuity-model.js";

type JsonRecord = Record<string, unknown>;

const calls: Array<{ name: string; arguments: JsonRecord }> = [];
const result = document.getElementById("e2e-result");
const frame = document.getElementById(
    "continuity-frame",
) as HTMLIFrameElement | null;

function fail(code: string): never {
    if (result !== null) {
        result.dataset.state = "fail";
        result.textContent = code;
    }
    throw new Error(code);
}

function publicBase(requestId: unknown) {
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
    const deadline = performance.now() + 5_000;
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
    ].find((item) => item.textContent?.includes(label));
    return match?.tagName === "BUTTON"
        ? (match as HTMLButtonElement)
        : undefined;
}

function button(label: string): HTMLButtonElement {
    return findButton(label) ?? fail(`button_missing:${label}`);
}

async function runFlow() {
    await waitFor(
        () => findButton("새 브랜치로 분리") !== undefined,
        "stale_render_timeout",
    );
    button("새 브랜치로 분리").click();
    await waitFor(
        () => findButton("확인 후 해결") !== undefined,
        "resolution_confirm_timeout",
    );
    if (calls.length !== 0) fail("selection_caused_tool_call");
    button("확인 후 해결").click();
    await waitFor(() => calls.length === 3, "resolution_calls_timeout");
    await waitFor(
        () =>
            frame?.contentDocument?.body.textContent?.includes(
                "충돌 해결 후 최신 상태를 다시 확인했습니다.",
            ) === true,
        "resolution_render_timeout",
    );

    const [resolveCall, open, history] = calls;
    const requestIds = [
        resolveCall?.arguments.request_id,
        open?.arguments.request_id,
        history?.arguments.request_id,
    ];
    if (
        resolveCall?.name !== "project_conflict_resolve" ||
        open?.name !== "project_open" ||
        history?.name !== "project_history" ||
        resolveCall.arguments.project_id !== "prj_e2eproject1" ||
        resolveCall.arguments.expected_revision !== "rev_e2ehead123" ||
        resolveCall.arguments.expected_generation !== 4 ||
        resolveCall.arguments.resolution !== "branch" ||
        typeof resolveCall.arguments.idempotency_key !== "string" ||
        open.arguments.project_id !== "prj_e2eproject1" ||
        history.arguments.page_size !== 12 ||
        !requestIds.every((value) => typeof value === "string") ||
        new Set(requestIds).size !== 3
    ) {
        fail("call_contract_mismatch");
    }
    if (result !== null) {
        result.dataset.state = "pass";
        result.textContent =
            "PASS calls=3 order=project_conflict_resolve,project_open,project_history";
    }
}

async function main() {
    if (frame === null || result === null) fail("harness_dom_missing");
    if (frame.contentWindow === null) fail("frame_window_missing");

    const bridge = new AppBridge(
        null,
        { name: "HWPX Agent continuity v2 local E2E host", version: "1.0.0" },
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
        const base = publicBase(args.request_id);
        if (params.name === "project_conflict_resolve") {
            return {
                content: [],
                structuredContent: {
                    ...base,
                    project_id: "prj_e2eproject1",
                    expected_revision: "rev_e2ehead123",
                    resolution: "branch",
                    current_generation: 4,
                    conflict_state: "none",
                    replayed: false,
                },
            };
        }
        if (params.name === "project_open") {
            return {
                content: [],
                structuredContent: {
                    ...base,
                    project_id: "prj_e2eproject1",
                    head_revision_id: "rev_e2ehead123",
                    warning_count: 0,
                    conflict_state: "none",
                    stale_head: null,
                    recommended_actions: [],
                },
            };
        }
        if (params.name === "project_history") {
            return {
                content: [],
                structuredContent: {
                    ...base,
                    revisions: [
                        {
                            revision_id: "rev_e2ehead123",
                            parent_revision_ids: ["rev_e2eparent1"],
                            created_at: "2026-09-05T03:20:00Z",
                            summary: "edited heading",
                        },
                    ],
                    next_cursor: null,
                },
            };
        }
        fail("unexpected_tool_call");
    };
    bridge.oninitialized = () => {
        void bridge.sendToolInput({
            arguments: {
                schema_version: CONTINUITY_RENDER_REQUEST_V2_SCHEMA,
                client_surface: "codex_local",
                locale: "ko-KR",
                project_id: "prj_e2eproject1",
            },
        });
        void bridge.sendToolResult({
            content: [],
            structuredContent: {
                schema_version: CONTINUITY_SNAPSHOT_V2_SCHEMA,
                client_surface: "codex_local",
                locale: "ko-KR",
                project_id: "prj_e2eproject1",
                head_revision_id: "rev_e2ehead123",
                warning_count: 1,
                conflict_state: "stale",
                stale_head: {
                    observed_generation: 2,
                    current_generation: 4,
                    delta: 2,
                    allowed_resolutions: [
                        "rebase_operation_plan",
                        "branch",
                        "manual_merge",
                    ],
                },
                revisions: [
                    {
                        revision_id: "rev_e2ehead123",
                        parent_revision_ids: ["rev_e2eparent1"],
                        created_at: "2026-09-05T03:20:00Z",
                        change_kind: "edited",
                    },
                ],
                next_cursor: null,
            },
        });
        setTimeout(
            () =>
                void runFlow().catch((error: unknown) => {
                    fail(
                        error instanceof Error ? error.message : "flow_failed",
                    );
                }),
            100,
        );
    };
    const connection = bridge.connect(
        new PostMessageTransport(frame.contentWindow, frame.contentWindow),
    );
    frame.src = "continuity-widget-v2.html";
    await connection;
}

void main().catch((error: unknown) => {
    fail(error instanceof Error ? error.message : "harness_failed");
});
