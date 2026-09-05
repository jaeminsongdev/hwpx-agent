import {
    parseCapabilityCheckResult,
    parseDocumentEditResult,
    parsePlanReviewRenderRequest,
    parsePlanReviewSnapshot,
    isAcceptedExecution,
    isVerifiedDryRun,
    routeMatches,
    warningsCovered,
    resolveHostTheme,
    resolveViewLocale,
    type HostTheme,
    type PlanReviewRenderRequest,
    type PlanReviewSnapshot,
    type ViewLocale,
} from "./plan-review-model.js";

export type PlanReviewPhase =
    | "connecting"
    | "approval_pending"
    | "ready"
    | "recoverable_error"
    | "closed";
export type PlanReviewMode = "view" | "confirm_execution";
export type ExecutionState =
    "none" | "revalidated" | "unconfirmed" | "submitted" | "committed";
type DispatchedState = Extract<
    ExecutionState,
    "unconfirmed" | "submitted" | "committed"
>;
export type PlanReviewErrorCode =
    | "CONNECT_FAILED"
    | "INVALID_TOOL_INPUT"
    | "INVALID_TOOL_RESULT"
    | "TOOL_CANCELLED"
    | "REVALIDATION_FAILED"
    | "EXECUTION_FAILED"
    | "SESSION_LIMIT_REACHED";

export interface PlanReviewHostContext {
    readonly locale?: unknown;
    readonly theme?: unknown;
}
export interface PlanReviewToolResultNotification {
    readonly structuredContent?: unknown | undefined;
    readonly isError?: boolean | undefined;
}

type CallContext = {
    readonly client_surface: PlanReviewSnapshot["client_surface"];
    readonly locale: string;
    readonly request_id: string;
    readonly project_id: string;
};

export interface CapabilityCheckCall {
    readonly name: "capability_check";
    readonly arguments: CallContext & {
        readonly target_profile: "hancom-hangul-2020-secondary";
        readonly revision_id: string;
        readonly capabilities: readonly string[];
        readonly requirements: {
            readonly native_editability: true;
            readonly preserve_unknown: true;
            readonly required_validation: readonly ["semantic", "reopen"];
        };
    };
}

export interface DocumentEditCall {
    readonly name: "document_edit";
    readonly arguments: CallContext & {
        readonly target_profile: "hancom-hangul-2020-secondary";
        readonly expected_revision: string;
        readonly idempotency_key: string;
        readonly source_revision_id: string;
        readonly plan_id: string;
        readonly dry_run: boolean;
        readonly best_effort: false;
        readonly allow_signature_invalidation: false;
    };
}

export type PlanReviewServerCall = CapabilityCheckCall | DocumentEditCall;

export interface PlanReviewPort {
    onToolInput(handler: (value: unknown) => void): () => void;
    onToolResult(
        handler: (value: PlanReviewToolResultNotification) => void,
    ): () => void;
    onToolCancelled(handler: () => void): () => void;
    onHostContextChanged(
        handler: (value: PlanReviewHostContext) => void,
    ): () => void;
    onTeardown(handler: () => void): () => void;
    connect(): Promise<void>;
    getHostContext(): PlanReviewHostContext | undefined;
    callServerTool(call: PlanReviewServerCall): Promise<unknown>;
    close(): Promise<void>;
}

export interface PlanReviewViewState {
    readonly phase: PlanReviewPhase;
    readonly mode: PlanReviewMode;
    readonly locale: ViewLocale;
    readonly theme: HostTheme;
    readonly snapshot: PlanReviewSnapshot | null;
    readonly errorCode: PlanReviewErrorCode | null;
    readonly actionPending: boolean;
    readonly acknowledged: boolean;
    readonly executionState: ExecutionState;
}

type Listener = (state: PlanReviewViewState) => void;
const REQUEST_ID = /^req_[A-Za-z0-9_-]{8,120}$/;
const IDEMPOTENCY_KEY =
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
export const MAX_EXECUTION_BINDINGS = 128;
export const MAX_CORRELATION_IDS = 1024;

function executionBinding(snapshot: PlanReviewSnapshot): string {
    return JSON.stringify([
        snapshot.project_id,
        snapshot.source_revision_id,
        snapshot.plan_id,
    ]);
}

function structuredContent(value: unknown): unknown | null {
    if (
        typeof value !== "object" ||
        value === null ||
        Array.isArray(value) ||
        (value as Record<string, unknown>).isError === true ||
        !("structuredContent" in value)
    )
        return null;
    return (value as Record<string, unknown>).structuredContent;
}

export class PlanReviewController {
    private state: PlanReviewViewState = {
        phase: "connecting",
        mode: "view",
        locale: "ko-KR",
        theme: "light",
        snapshot: null,
        errorCode: null,
        actionPending: false,
        acknowledged: false,
        executionState: "none",
    };
    private readonly listeners = new Set<Listener>();
    private unregister: Array<() => void> = [];
    private started = false;
    private closeStarted = false;
    private approvedRequest: PlanReviewRenderRequest | null = null;
    // Session-local duplicate suppression, not server authorization or cross-widget deduplication.
    // Entries are never evicted to make room: eviction could re-enable a dispatched write.
    private readonly dispatchedExecutions = new Map<string, DispatchedState>();
    private readonly usedRequestIds = new Set<string>();
    private readonly usedIdempotencyKeys = new Set<string>();

    constructor(
        private readonly port: PlanReviewPort,
        private readonly requestId: () => string,
        private readonly idempotencyKey: () => string,
    ) {}

    getState(): PlanReviewViewState {
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
            if (this.state.phase === "connecting")
                this.setState({ phase: "approval_pending" });
        } catch {
            this.fail("CONNECT_FAILED");
        }
    }

    beginExecution(): void {
        if (
            this.state.phase !== "ready" ||
            this.state.mode !== "view" ||
            this.state.actionPending ||
            this.state.snapshot?.execution_allowed !== true ||
            this.executionFor(this.state.snapshot) !== undefined
        )
            return;
        if (this.dispatchedExecutions.size >= MAX_EXECUTION_BINDINGS) {
            this.fail("SESSION_LIMIT_REACHED");
            return;
        }
        this.setState({
            mode: "confirm_execution",
            acknowledged: false,
            executionState: "none",
        });
    }

    cancelExecution(): void {
        if (
            this.state.phase === "ready" &&
            this.state.mode === "confirm_execution" &&
            !this.state.actionPending
        )
            this.setState({ mode: "view", acknowledged: false });
    }

    setAcknowledged(value: boolean): void {
        if (
            this.state.phase === "ready" &&
            this.state.mode === "confirm_execution" &&
            !this.state.actionPending
        )
            this.setState({ acknowledged: value });
    }

    async revalidate(): Promise<void> {
        const snapshot = this.state.snapshot;
        if (
            this.state.phase !== "ready" ||
            this.state.mode !== "view" ||
            this.state.actionPending ||
            snapshot === null ||
            this.executionFor(snapshot) !== undefined
        )
            return;
        this.setState({ actionPending: true, executionState: "none" });
        const verified = await this.verifySnapshot(snapshot);
        if (!this.isOperationCurrent(snapshot, "view")) return;
        if (verified) {
            this.setState({
                actionPending: false,
                executionState: "revalidated",
            });
        } else {
            this.fail("REVALIDATION_FAILED");
        }
    }

    async confirmExecution(): Promise<void> {
        const snapshot = this.state.snapshot;
        if (
            this.state.phase !== "ready" ||
            this.state.mode !== "confirm_execution" ||
            this.state.actionPending ||
            !this.state.acknowledged ||
            snapshot?.execution_allowed !== true ||
            this.executionFor(snapshot) !== undefined
        )
            return;
        this.setState({ actionPending: true });
        const verified = await this.verifySnapshot(snapshot);
        if (!this.isOperationCurrent(snapshot, "confirm_execution")) return;
        if (!verified) {
            this.fail("EXECUTION_FAILED");
            return;
        }
        const requestId = this.nextRequestId();
        const key = this.nextIdempotencyKey();
        if (requestId === null || key === null) {
            this.fail("EXECUTION_FAILED");
            return;
        }
        if (this.executionFor(snapshot) !== undefined) return;
        if (this.dispatchedExecutions.size >= MAX_EXECUTION_BINDINGS) {
            this.fail("SESSION_LIMIT_REACHED");
            return;
        }
        const binding = executionBinding(snapshot);
        // Reserve BEFORE dispatch: a throw, lost reply, cancellation or new render must not
        // convert an unknown external effect into permission to send the same plan again.
        this.dispatchedExecutions.set(binding, "unconfirmed");
        try {
            const result = parseDocumentEditResult(
                structuredContent(
                    await this.port.callServerTool(
                        this.editCall(snapshot, requestId, key, false),
                    ),
                ),
            );
            if (
                result === null ||
                result.request_id !== requestId ||
                !warningsCovered(snapshot.warnings, result.warning_codes) ||
                !isAcceptedExecution(result)
            ) {
                if (this.isOperationCurrent(snapshot, "confirm_execution"))
                    this.fail("EXECUTION_FAILED");
                return;
            }
            const executionState =
                result.commit_state === "committed" ? "committed" : "submitted";
            this.dispatchedExecutions.set(binding, executionState);
            if (!this.isOperationCurrent(snapshot, "confirm_execution")) return;
            this.setState({
                mode: "view",
                actionPending: false,
                acknowledged: false,
                executionState,
            });
        } catch {
            if (this.isOperationCurrent(snapshot, "confirm_execution"))
                this.fail("EXECUTION_FAILED");
        }
    }

    async close(): Promise<void> {
        this.finish();
        await this.closePortOnce();
    }

    private async verifySnapshot(
        snapshot: PlanReviewSnapshot,
    ): Promise<boolean> {
        const capabilityRequestId = this.nextRequestId();
        const dryRunRequestId = this.nextRequestId();
        const dryRunKey = this.nextIdempotencyKey();
        if (
            capabilityRequestId === null ||
            dryRunRequestId === null ||
            dryRunKey === null ||
            capabilityRequestId === dryRunRequestId
        )
            return false;
        try {
            const capability = parseCapabilityCheckResult(
                structuredContent(
                    await this.port.callServerTool({
                        name: "capability_check",
                        arguments: {
                            client_surface: snapshot.client_surface,
                            locale: snapshot.locale,
                            request_id: capabilityRequestId,
                            project_id: snapshot.project_id,
                            target_profile: "hancom-hangul-2020-secondary",
                            revision_id: snapshot.source_revision_id,
                            capabilities: snapshot.route.map(
                                (item) => item.capability_id,
                            ),
                            requirements: {
                                native_editability: true,
                                preserve_unknown: true,
                                required_validation: ["semantic", "reopen"],
                            },
                        },
                    }),
                ),
            );
            if (
                capability === null ||
                capability.request_id !== capabilityRequestId ||
                capability.detail_count !== 0 ||
                !warningsCovered(snapshot.warnings, capability.warning_codes) ||
                !routeMatches(snapshot.route, capability.capabilities)
            )
                return false;
            if (!this.isOperationCurrent(snapshot)) return false;
            const dryRun = parseDocumentEditResult(
                structuredContent(
                    await this.port.callServerTool(
                        this.editCall(
                            snapshot,
                            dryRunRequestId,
                            dryRunKey,
                            true,
                        ),
                    ),
                ),
            );
            return (
                this.isOperationCurrent(snapshot) &&
                dryRun !== null &&
                dryRun.request_id === dryRunRequestId &&
                warningsCovered(snapshot.warnings, dryRun.warning_codes) &&
                isVerifiedDryRun(dryRun)
            );
        } catch {
            return false;
        }
    }

    private editCall(
        snapshot: PlanReviewSnapshot,
        requestId: string,
        key: string,
        dryRun: boolean,
    ): DocumentEditCall {
        return {
            name: "document_edit",
            arguments: {
                client_surface: snapshot.client_surface,
                locale: snapshot.locale,
                request_id: requestId,
                project_id: snapshot.project_id,
                target_profile: "hancom-hangul-2020-secondary",
                expected_revision: snapshot.source_revision_id,
                idempotency_key: key,
                source_revision_id: snapshot.source_revision_id,
                plan_id: snapshot.plan_id,
                dry_run: dryRun,
                best_effort: false,
                allow_signature_invalidation: false,
            },
        };
    }

    private isOperationCurrent(
        snapshot: PlanReviewSnapshot,
        mode?: PlanReviewMode,
    ): boolean {
        return (
            this.state.phase === "ready" &&
            this.state.actionPending &&
            this.state.snapshot === snapshot &&
            (mode === undefined || this.state.mode === mode)
        );
    }

    private executionFor(
        snapshot: PlanReviewSnapshot | null,
    ): DispatchedState | undefined {
        return snapshot === null
            ? undefined
            : this.dispatchedExecutions.get(executionBinding(snapshot));
    }

    private registerHandlers(): void {
        this.unregister = [
            this.port.onToolInput((value) => this.acceptRenderRequest(value)),
            this.port.onToolResult((value) =>
                value.isError === true
                    ? this.fail("INVALID_TOOL_RESULT")
                    : this.acceptSnapshot(value.structuredContent),
            ),
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
        const request = parsePlanReviewRenderRequest(value);
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
            acknowledged: false,
            executionState: "none",
        });
    }

    private acceptSnapshot(value: unknown): void {
        if (this.state.phase === "closed") return;
        const snapshot = parsePlanReviewSnapshot(value);
        const request = this.approvedRequest;
        if (
            snapshot === null ||
            request === null ||
            snapshot.client_surface !== request.client_surface ||
            snapshot.project_id !== request.project_id ||
            snapshot.source_revision_id !== request.source_revision_id ||
            snapshot.plan_id !== request.plan_id
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
            acknowledged: false,
            executionState: this.executionFor(snapshot) ?? "none",
        };
        this.emit();
    }

    private applyHostContext(value: PlanReviewHostContext | undefined): void {
        if (value === undefined || this.state.phase === "closed") return;
        this.setState({
            locale: resolveViewLocale(value.locale, this.state.locale),
            theme: resolveHostTheme(value.theme),
        });
    }

    private nextRequestId(): string | null {
        try {
            const value = this.requestId();
            if (
                typeof value !== "string" ||
                !REQUEST_ID.test(value) ||
                this.usedRequestIds.has(value) ||
                this.usedRequestIds.size >= MAX_CORRELATION_IDS
            )
                return null;
            this.usedRequestIds.add(value);
            return value;
        } catch {
            return null;
        }
    }

    private nextIdempotencyKey(): string | null {
        try {
            const value = this.idempotencyKey();
            if (
                typeof value !== "string" ||
                !IDEMPOTENCY_KEY.test(value) ||
                this.usedIdempotencyKeys.has(value) ||
                this.usedIdempotencyKeys.size >= MAX_CORRELATION_IDS
            )
                return null;
            this.usedIdempotencyKeys.add(value);
            return value;
        } catch {
            return null;
        }
    }

    private fail(code: PlanReviewErrorCode): void {
        if (this.state.phase === "closed") return;
        const executionState =
            this.executionFor(this.state.snapshot) ??
            (this.state.executionState === "unconfirmed" ||
            this.state.executionState === "submitted" ||
            this.state.executionState === "committed"
                ? this.state.executionState
                : "none");
        this.setState({
            phase: "recoverable_error",
            mode: "view",
            snapshot: null,
            errorCode: code,
            actionPending: false,
            acknowledged: false,
            executionState,
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
            acknowledged: false,
            executionState: "none",
        });
    }

    private async closePortOnce(): Promise<void> {
        if (this.closeStarted) return;
        this.closeStarted = true;
        try {
            await this.port.close();
        } catch {
            /* terminal and redacted */
        }
    }

    private setState(patch: Partial<PlanReviewViewState>): void {
        this.state = { ...this.state, ...patch };
        this.emit();
    }
    private emit(): void {
        for (const listener of this.listeners) listener(this.state);
    }
}
