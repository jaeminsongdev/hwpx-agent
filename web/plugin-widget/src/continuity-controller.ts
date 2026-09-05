import {
    CONTINUITY_SNAPSHOT_SCHEMA,
    parseContinuityRenderRequest,
    parseContinuitySnapshot,
    parseProjectCheckpointResult,
    parseProjectHistoryResult,
    parseProjectOpenResult,
    resolveHostTheme,
    resolveViewLocale,
    type ContinuityRenderRequest,
    type ContinuitySnapshot,
    type HostTheme,
    type ViewLocale,
} from "./continuity-model.js";

export type ContinuityPhase =
    | "connecting"
    | "approval_pending"
    | "ready"
    | "recoverable_error"
    | "closed";
export type ContinuityMode = "view" | "confirm_checkpoint";
export type CheckpointState = "none" | "saved" | "replayed";
export type ContinuityErrorCode =
    | "CONNECT_FAILED"
    | "INVALID_TOOL_INPUT"
    | "INVALID_TOOL_RESULT"
    | "TOOL_CANCELLED"
    | "REFRESH_FAILED"
    | "CHECKPOINT_FAILED";

export interface ContinuityHostContext {
    readonly locale?: unknown;
    readonly theme?: unknown;
}

export interface ContinuityToolResultNotification {
    readonly structuredContent?: unknown | undefined;
    readonly isError?: boolean | undefined;
}

type CallContext = {
    readonly client_surface: ContinuitySnapshot["client_surface"];
    readonly locale: string;
    readonly request_id: string;
    readonly project_id: string;
};

export interface ProjectOpenCall {
    readonly name: "project_open";
    readonly arguments: CallContext & {
        readonly include: readonly [
            "head",
            "checkpoints",
            "warnings",
            "conflicts",
            "recommended_actions",
        ];
    };
}

export interface ProjectHistoryCall {
    readonly name: "project_history";
    readonly arguments: CallContext & {
        readonly include_diff_summary: true;
        readonly page_size: 12;
    };
}

export interface ProjectCheckpointCall {
    readonly name: "project_checkpoint";
    readonly arguments: CallContext & {
        readonly expected_revision: string;
        readonly idempotency_key: string;
        readonly revision_id: string;
        readonly label: "HWPX Agent checkpoint";
    };
}

export type ContinuityServerCall =
    ProjectOpenCall | ProjectHistoryCall | ProjectCheckpointCall;

export interface ContinuityPort {
    onToolInput(handler: (value: unknown) => void): () => void;
    onToolResult(
        handler: (value: ContinuityToolResultNotification) => void,
    ): () => void;
    onToolCancelled(handler: () => void): () => void;
    onHostContextChanged(
        handler: (value: ContinuityHostContext) => void,
    ): () => void;
    onTeardown(handler: () => void): () => void;
    connect(): Promise<void>;
    getHostContext(): ContinuityHostContext | undefined;
    callServerTool(call: ContinuityServerCall): Promise<unknown>;
    close(): Promise<void>;
}

export interface ContinuityViewState {
    readonly phase: ContinuityPhase;
    readonly mode: ContinuityMode;
    readonly locale: ViewLocale;
    readonly theme: HostTheme;
    readonly snapshot: ContinuitySnapshot | null;
    readonly errorCode: ContinuityErrorCode | null;
    readonly actionPending: boolean;
    readonly checkpointState: CheckpointState;
}

type Listener = (state: ContinuityViewState) => void;

const OPEN_INCLUDE = [
    "head",
    "checkpoints",
    "warnings",
    "conflicts",
    "recommended_actions",
] as const;
const REQUEST_ID_PATTERN = /^req_[A-Za-z0-9_-]{8,120}$/;
const IDEMPOTENCY_KEY_PATTERN =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

function structuredContent(value: unknown): unknown | null {
    if (
        typeof value !== "object" ||
        value === null ||
        Array.isArray(value) ||
        (value as Record<string, unknown>).isError === true ||
        !("structuredContent" in value)
    ) {
        return null;
    }
    return (value as Record<string, unknown>).structuredContent;
}

export class ContinuityController {
    private state: ContinuityViewState = {
        phase: "connecting",
        mode: "view",
        locale: "ko-KR",
        theme: "light",
        snapshot: null,
        errorCode: null,
        actionPending: false,
        checkpointState: "none",
    };
    private readonly listeners = new Set<Listener>();
    private unregister: Array<() => void> = [];
    private started = false;
    private closeStarted = false;
    private approvedRequest: ContinuityRenderRequest | null = null;

    constructor(
        private readonly port: ContinuityPort,
        private readonly requestId: () => string,
        private readonly idempotencyKey: () => string,
    ) {}

    getState(): ContinuityViewState {
        return this.state;
    }

    subscribe(listener: Listener): () => void {
        this.listeners.add(listener);
        listener(this.state);
        return () => this.listeners.delete(listener);
    }

    async start(): Promise<void> {
        if (this.started) return;
        this.started = true;
        this.registerHandlers();
        try {
            await this.port.connect();
            this.applyHostContext(this.port.getHostContext());
            if (this.state.phase === "connecting") {
                this.setState({ phase: "approval_pending" });
            }
        } catch {
            this.fail("CONNECT_FAILED");
        }
    }

    beginCheckpoint(): void {
        const snapshot = this.state.snapshot;
        if (
            this.state.phase !== "ready" ||
            this.state.actionPending ||
            this.state.mode !== "view" ||
            snapshot === null ||
            snapshot.head_revision_id === null ||
            snapshot.conflict_state !== "none"
        ) {
            return;
        }
        this.setState({ mode: "confirm_checkpoint", checkpointState: "none" });
    }

    cancelCheckpoint(): void {
        if (
            this.state.phase === "ready" &&
            this.state.mode === "confirm_checkpoint" &&
            !this.state.actionPending
        ) {
            this.setState({ mode: "view" });
        }
    }

    async confirmCheckpoint(): Promise<void> {
        const snapshot = this.state.snapshot;
        if (
            this.state.phase !== "ready" ||
            this.state.mode !== "confirm_checkpoint" ||
            this.state.actionPending ||
            snapshot === null ||
            snapshot.head_revision_id === null ||
            snapshot.conflict_state !== "none"
        ) {
            return;
        }
        const requestId = this.nextRequestId();
        const idempotencyKey = this.nextIdempotencyKey();
        if (requestId === null || idempotencyKey === null) {
            this.fail("CHECKPOINT_FAILED");
            return;
        }
        this.setState({ actionPending: true });
        const call: ProjectCheckpointCall = {
            name: "project_checkpoint",
            arguments: {
                client_surface: snapshot.client_surface,
                locale: snapshot.locale,
                request_id: requestId,
                project_id: snapshot.project_id,
                expected_revision: snapshot.head_revision_id,
                idempotency_key: idempotencyKey,
                revision_id: snapshot.head_revision_id,
                label: "HWPX Agent checkpoint",
            },
        };
        try {
            const result = parseProjectCheckpointResult(
                structuredContent(await this.port.callServerTool(call)),
            );
            if (
                result === null ||
                result.request_id !== requestId ||
                result.revision_id !== snapshot.head_revision_id
            ) {
                this.fail("CHECKPOINT_FAILED");
                return;
            }
            this.setState({
                mode: "view",
                actionPending: false,
                checkpointState: result.replayed ? "replayed" : "saved",
            });
        } catch {
            this.fail("CHECKPOINT_FAILED");
        }
    }

    async refresh(): Promise<void> {
        const snapshot = this.state.snapshot;
        if (
            this.state.phase !== "ready" ||
            this.state.mode !== "view" ||
            this.state.actionPending ||
            snapshot === null
        ) {
            return;
        }
        const openRequestId = this.nextRequestId();
        const historyRequestId = this.nextRequestId();
        if (
            openRequestId === null ||
            historyRequestId === null ||
            openRequestId === historyRequestId
        ) {
            this.fail("REFRESH_FAILED");
            return;
        }
        this.setState({ actionPending: true, checkpointState: "none" });
        const context = {
            client_surface: snapshot.client_surface,
            locale: snapshot.locale,
            project_id: snapshot.project_id,
        } as const;
        const openCall: ProjectOpenCall = {
            name: "project_open",
            arguments: {
                ...context,
                request_id: openRequestId,
                include: OPEN_INCLUDE,
            },
        };
        const historyCall: ProjectHistoryCall = {
            name: "project_history",
            arguments: {
                ...context,
                request_id: historyRequestId,
                include_diff_summary: true,
                page_size: 12,
            },
        };
        try {
            const open = parseProjectOpenResult(
                structuredContent(await this.port.callServerTool(openCall)),
            );
            const history = parseProjectHistoryResult(
                structuredContent(await this.port.callServerTool(historyCall)),
            );
            if (
                open === null ||
                history === null ||
                open.request_id !== openRequestId ||
                history.request_id !== historyRequestId ||
                open.project_id !== snapshot.project_id
            ) {
                this.fail("REFRESH_FAILED");
                return;
            }
            const revisions = [...history.revisions]
                .sort((left, right) =>
                    right.created_at.localeCompare(left.created_at),
                )
                .slice(0, 12);
            if (
                open.head_revision_id !== null &&
                revisions.length > 0 &&
                revisions[0]!.revision_id !== open.head_revision_id
            ) {
                this.fail("REFRESH_FAILED");
                return;
            }
            this.setState({
                actionPending: false,
                snapshot: {
                    schema_version: CONTINUITY_SNAPSHOT_SCHEMA,
                    client_surface: snapshot.client_surface,
                    locale: snapshot.locale,
                    project_id: open.project_id,
                    head_revision_id: open.head_revision_id,
                    warning_count: open.warning_count,
                    conflict_state: open.conflict_state,
                    revisions,
                    next_cursor: history.next_cursor,
                },
            });
        } catch {
            this.fail("REFRESH_FAILED");
        }
    }

    async close(): Promise<void> {
        this.finish();
        await this.closePortOnce();
    }

    private registerHandlers(): void {
        this.unregister = [
            this.port.onToolInput((value) => this.acceptRenderRequest(value)),
            this.port.onToolResult((value) => {
                if (value.isError === true) {
                    this.fail("INVALID_TOOL_RESULT");
                    return;
                }
                this.acceptSnapshot(value.structuredContent);
            }),
            this.port.onToolCancelled(() => this.fail("TOOL_CANCELLED")),
            this.port.onHostContextChanged((value) =>
                this.applyHostContext(value),
            ),
            this.port.onTeardown(() => {
                this.finish();
                queueMicrotask(() => void this.closePortOnce());
            }),
        ];
    }

    private acceptRenderRequest(value: unknown): void {
        if (this.state.phase === "closed") return;
        const request = parseContinuityRenderRequest(value);
        if (request === null) {
            this.fail("INVALID_TOOL_INPUT");
            return;
        }
        this.approvedRequest = request;
        this.setState({
            phase: "approval_pending",
            mode: "view",
            locale: resolveViewLocale(request.locale, this.state.locale),
            snapshot: null,
            errorCode: null,
            actionPending: false,
            checkpointState: "none",
        });
    }

    private acceptSnapshot(value: unknown): void {
        if (this.state.phase === "closed") return;
        const snapshot = parseContinuitySnapshot(value);
        const approved = this.approvedRequest;
        if (
            snapshot === null ||
            approved === null ||
            snapshot.client_surface !== approved.client_surface ||
            snapshot.project_id !== approved.project_id
        ) {
            this.fail("INVALID_TOOL_RESULT");
            return;
        }
        this.state = {
            ...this.state,
            phase: "ready",
            mode: "view",
            locale: resolveViewLocale(snapshot.locale, this.state.locale),
            snapshot,
            errorCode: null,
            actionPending: false,
            checkpointState: "none",
        };
        this.emit();
    }

    private applyHostContext(value: ContinuityHostContext | undefined): void {
        if (value === undefined || this.state.phase === "closed") return;
        this.setState({
            locale: resolveViewLocale(value.locale, this.state.locale),
            theme: resolveHostTheme(value.theme),
        });
    }

    private nextRequestId(): string | null {
        try {
            const value = this.requestId();
            return REQUEST_ID_PATTERN.test(value) ? value : null;
        } catch {
            return null;
        }
    }

    private nextIdempotencyKey(): string | null {
        try {
            const value = this.idempotencyKey();
            return IDEMPOTENCY_KEY_PATTERN.test(value) ? value : null;
        } catch {
            return null;
        }
    }

    private fail(code: ContinuityErrorCode): void {
        if (this.state.phase === "closed") return;
        this.setState({
            phase: "recoverable_error",
            mode: "view",
            snapshot: null,
            errorCode: code,
            actionPending: false,
            checkpointState: "none",
        });
    }

    private finish(): void {
        if (this.state.phase === "closed") return;
        for (const remove of this.unregister.splice(0)) remove();
        this.setState({
            phase: "closed",
            mode: "view",
            snapshot: null,
            errorCode: null,
            actionPending: false,
            checkpointState: "none",
        });
    }

    private async closePortOnce(): Promise<void> {
        if (this.closeStarted) return;
        this.closeStarted = true;
        try {
            await this.port.close();
        } catch {
            // Teardown is terminal and never exposes raw transport details.
        }
    }

    private setState(patch: Partial<ContinuityViewState>): void {
        this.state = { ...this.state, ...patch };
        this.emit();
    }

    private emit(): void {
        for (const listener of this.listeners) listener(this.state);
    }
}
