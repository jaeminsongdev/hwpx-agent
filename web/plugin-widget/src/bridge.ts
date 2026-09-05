import {
    parseWidgetRenderRequest,
    parseWidgetSnapshot,
    resolveHostTheme,
    resolveViewLocale,
    type HostTheme,
    type ViewLocale,
    type WidgetRenderRequest,
    type WidgetSnapshot,
} from "./model.js";

export type WidgetPhase =
    | "connecting"
    | "approval_pending"
    | "ready"
    | "recoverable_error"
    | "closed";
export type WidgetErrorCode =
    | "CONNECT_FAILED"
    | "INVALID_TOOL_INPUT"
    | "INVALID_TOOL_RESULT"
    | "TOOL_CANCELLED"
    | "TOOL_CALL_FAILED";

export interface HostContextInput {
    readonly locale?: unknown;
    readonly theme?: unknown;
}

export interface ToolResultInput {
    readonly structuredContent?: unknown | undefined;
    readonly isError?: boolean | undefined;
}

export interface ProjectOpenCall {
    readonly name: "project_open";
    readonly arguments: {
        readonly client_surface: WidgetSnapshot["client_surface"];
        readonly locale: string;
        readonly request_id: string;
        readonly project_id: string;
        readonly include: readonly [
            "head",
            "warnings",
            "conflicts",
            "target",
            "recent_artifacts",
            "recommended_actions",
        ];
    };
}

export interface WidgetPort {
    onToolInput(handler: (value: unknown) => void): () => void;
    onToolResult(handler: (value: ToolResultInput) => void): () => void;
    onToolCancelled(handler: () => void): () => void;
    onHostContextChanged(
        handler: (value: HostContextInput) => void,
    ): () => void;
    onTeardown(handler: () => void): () => void;
    connect(): Promise<void>;
    getHostContext(): HostContextInput | undefined;
    callServerTool(call: ProjectOpenCall): Promise<unknown>;
    close(): Promise<void>;
}

export interface WidgetViewState {
    readonly phase: WidgetPhase;
    readonly locale: ViewLocale;
    readonly theme: HostTheme;
    readonly snapshot: WidgetSnapshot | null;
    readonly errorCode: WidgetErrorCode | null;
    readonly actionPending: boolean;
}

type Listener = (state: WidgetViewState) => void;

const INCLUDE_FIELDS = [
    "head",
    "warnings",
    "conflicts",
    "target",
    "recent_artifacts",
    "recommended_actions",
] as const;
const REQUEST_ID_PATTERN = /^req_[A-Za-z0-9_-]{8,120}$/;

function isErrorToolResult(value: unknown): boolean {
    return (
        typeof value === "object" &&
        value !== null &&
        !Array.isArray(value) &&
        (value as Record<string, unknown>).isError === true
    );
}

export class WidgetBridgeController {
    private state: WidgetViewState = {
        phase: "connecting",
        locale: "ko-KR",
        theme: "light",
        snapshot: null,
        errorCode: null,
        actionPending: false,
    };
    private readonly listeners = new Set<Listener>();
    private unregister: Array<() => void> = [];
    private started = false;
    private closeStarted = false;
    private approvedRequest: WidgetRenderRequest | null = null;

    constructor(
        private readonly port: WidgetPort,
        private readonly requestId: () => string,
    ) {}

    getState(): WidgetViewState {
        return this.state;
    }

    subscribe(listener: Listener): () => void {
        this.listeners.add(listener);
        listener(this.state);
        return () => this.listeners.delete(listener);
    }

    async start(): Promise<void> {
        if (this.started) {
            return;
        }
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

    async continueProject(): Promise<void> {
        const snapshot = this.state.snapshot;
        if (
            this.state.phase !== "ready" ||
            this.state.actionPending ||
            snapshot?.project_id === null ||
            snapshot === null
        ) {
            return;
        }
        let requestId: string;
        try {
            requestId = this.requestId();
        } catch {
            this.fail("TOOL_CALL_FAILED");
            return;
        }
        if (!REQUEST_ID_PATTERN.test(requestId)) {
            this.fail("TOOL_CALL_FAILED");
            return;
        }
        this.setState({ actionPending: true });
        const call: ProjectOpenCall = {
            name: "project_open",
            arguments: {
                client_surface: snapshot.client_surface,
                locale: snapshot.locale,
                request_id: requestId,
                project_id: snapshot.project_id,
                include: INCLUDE_FIELDS,
            },
        };
        try {
            const result = await this.port.callServerTool(call);
            if (isErrorToolResult(result)) {
                this.fail("TOOL_CALL_FAILED");
                return;
            }
            if (this.state.phase === "ready") {
                this.setState({ actionPending: false });
            }
        } catch {
            this.fail("TOOL_CALL_FAILED");
        }
    }

    async close(): Promise<void> {
        this.finish();
        await this.closePortOnce();
    }

    private async closePortOnce(): Promise<void> {
        if (this.closeStarted) {
            return;
        }
        this.closeStarted = true;
        try {
            await this.port.close();
        } catch {
            // Teardown is terminal. Never surface raw transport errors.
        }
    }

    private registerHandlers(): void {
        this.unregister = [
            this.port.onToolInput((value) => this.acceptRenderRequest(value)),
            this.port.onToolResult((value) => {
                if (value.isError === true) {
                    this.fail("INVALID_TOOL_RESULT");
                    return;
                }
                this.acceptSnapshot(
                    value.structuredContent,
                    "INVALID_TOOL_RESULT",
                );
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
        if (this.state.phase === "closed") {
            return;
        }
        const request = parseWidgetRenderRequest(value);
        if (request === null) {
            this.fail("INVALID_TOOL_INPUT");
            return;
        }
        this.approvedRequest = request;
        this.setState({
            phase: "approval_pending",
            locale: resolveViewLocale(request.locale, this.state.locale),
            snapshot: null,
            errorCode: null,
            actionPending: false,
        });
    }

    private acceptSnapshot(value: unknown, code: WidgetErrorCode): void {
        if (this.state.phase === "closed") {
            return;
        }
        const snapshot = parseWidgetSnapshot(value);
        const approvedRequest = this.approvedRequest;
        if (snapshot === null || approvedRequest === null) {
            this.fail(code);
            return;
        }
        if (
            snapshot.client_surface !== approvedRequest.client_surface ||
            snapshot.project_id !== approvedRequest.project_id
        ) {
            this.fail(code);
            return;
        }
        this.state = {
            ...this.state,
            phase: "ready",
            locale: resolveViewLocale(snapshot.locale, this.state.locale),
            snapshot,
            errorCode: null,
            actionPending: false,
        };
        this.emit();
    }

    private applyHostContext(value: HostContextInput | undefined): void {
        if (value === undefined || this.state.phase === "closed") {
            return;
        }
        this.setState({
            locale: resolveViewLocale(value.locale, this.state.locale),
            theme: resolveHostTheme(value.theme),
        });
    }

    private fail(code: WidgetErrorCode): void {
        if (this.state.phase === "closed") {
            return;
        }
        this.setState({
            phase: "recoverable_error",
            snapshot: null,
            errorCode: code,
            actionPending: false,
        });
    }

    private finish(): void {
        if (this.state.phase === "closed") {
            return;
        }
        for (const remove of this.unregister.splice(0)) {
            remove();
        }
        this.setState({
            phase: "closed",
            snapshot: null,
            errorCode: null,
            actionPending: false,
        });
    }

    private setState(patch: Partial<WidgetViewState>): void {
        this.state = { ...this.state, ...patch };
        this.emit();
    }

    private emit(): void {
        for (const listener of this.listeners) {
            listener(this.state);
        }
    }
}
