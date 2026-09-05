import {
    AppBridge,
    PostMessageTransport,
} from "@modelcontextprotocol/ext-apps/app-bridge";

import {
    CONTINUITY_RENDER_REQUEST_SCHEMA,
    CONTINUITY_SNAPSHOT_SCHEMA,
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
    const doc = frame?.contentDocument;
    const match = [...(doc?.querySelectorAll("button") ?? [])].find(
        (item) => item.textContent?.trim() === label,
    );
    return match?.tagName === "BUTTON"
        ? (match as HTMLButtonElement)
        : undefined;
}

function button(label: string): HTMLButtonElement {
    return findButton(label) ?? fail(`button_missing:${label}`);
}

async function runFlow() {
    await waitFor(
        () => findButton("새로고침") !== undefined,
        "initial_render_timeout",
    );
    button("새로고침").click();
    await waitFor(() => calls.length === 2, "refresh_calls_timeout");
    await waitFor(
        () => frame?.contentDocument?.body.textContent?.includes("1") === true,
        "refresh_render_timeout",
    );
    button("체크포인트 만들기").click();
    await waitFor(
        () => findButton("확인 후 만들기") !== undefined,
        "checkpoint_confirm_render_timeout",
    );
    button("확인 후 만들기").click();
    await waitFor(() => calls.length === 3, "checkpoint_call_timeout");
    await waitFor(
        () =>
            frame?.contentDocument?.body.textContent?.includes(
                "체크포인트를 만들었습니다.",
            ) === true,
        "checkpoint_render_timeout",
    );

    const [open, history, checkpoint] = calls;
    if (
        open?.name !== "project_open" ||
        history?.name !== "project_history" ||
        checkpoint?.name !== "project_checkpoint" ||
        open.arguments.project_id !== "prj_e2eproject1" ||
        history.arguments.page_size !== 12 ||
        checkpoint.arguments.expected_revision !== "rev_e2ehead123" ||
        checkpoint.arguments.revision_id !== "rev_e2ehead123" ||
        checkpoint.arguments.label !== "HWPX Agent checkpoint" ||
        typeof checkpoint.arguments.idempotency_key !== "string"
    ) {
        fail("call_contract_mismatch");
    }
    if (result !== null) {
        result.dataset.state = "pass";
        result.textContent =
            "PASS calls=3 order=project_open,project_history,project_checkpoint";
    }
}

async function main() {
    if (frame === null || result === null) fail("harness_dom_missing");
    if (frame.contentWindow === null) fail("frame_window_missing");

    const bridge = new AppBridge(
        null,
        { name: "HWPX Agent local E2E host", version: "1.0.0" },
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
        if (params.name === "project_open") {
            return {
                content: [],
                structuredContent: {
                    ...base,
                    project_id: "prj_e2eproject1",
                    head_revision_id: "rev_e2ehead123",
                    warning_count: 1,
                    conflict_state: "none",
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
                        {
                            revision_id: "rev_e2eparent1",
                            parent_revision_ids: [],
                            created_at: "2026-09-04T03:20:00Z",
                            summary: "created",
                        },
                    ],
                    next_cursor: null,
                },
            };
        }
        if (params.name === "project_checkpoint") {
            return {
                content: [],
                structuredContent: {
                    ...base,
                    checkpoint_id: "chk_e2echeck123",
                    revision_id: "rev_e2ehead123",
                    replayed: false,
                },
            };
        }
        fail("unexpected_tool_call");
    };
    bridge.oninitialized = () => {
        void bridge.sendToolInput({
            arguments: {
                schema_version: CONTINUITY_RENDER_REQUEST_SCHEMA,
                client_surface: "codex_local",
                locale: "ko-KR",
                project_id: "prj_e2eproject1",
            },
        });
        void bridge.sendToolResult({
            content: [],
            structuredContent: {
                schema_version: CONTINUITY_SNAPSHOT_SCHEMA,
                client_surface: "codex_local",
                locale: "ko-KR",
                project_id: "prj_e2eproject1",
                head_revision_id: "rev_e2ehead123",
                warning_count: 0,
                conflict_state: "none",
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
    frame.src = "continuity-widget-v1.html";
    await connection;
}

void main().catch((error: unknown) => {
    fail(error instanceof Error ? error.message : "harness_failed");
});
