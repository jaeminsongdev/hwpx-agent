import {
    CONFIRM_GIT_APPROVAL_TOOL_NAME,
    confirmationArguments,
    inputMatchesPlan,
    parseApprovalChallenge,
    parseGitApprovalInput,
    parseGitApprovalPlan,
    parseGitEffectReceipt,
    type GitApprovalInput,
    type GitApprovalPlan,
    type GitEffectReceipt,
} from "./git-approval-model.js";

export type GitApprovalPhase =
    | "connecting"
    | "approval_pending"
    | "ready"
    | "executing"
    | "succeeded"
    | "unconfirmed"
    | "closed";

export interface GitApprovalState {
    readonly phase: GitApprovalPhase;
    readonly theme: "light" | "dark";
    readonly acknowledged: boolean;
    readonly plan: GitApprovalPlan | null;
    readonly receipt: GitEffectReceipt | null;
}

export interface GitApprovalServerCall {
    readonly name: typeof CONFIRM_GIT_APPROVAL_TOOL_NAME;
    readonly arguments: ReturnType<typeof confirmationArguments>;
}

export interface GitApprovalToolResultNotification {
    readonly structuredContent?: unknown | undefined;
    readonly isError?: boolean | undefined;
    readonly _meta?: Record<string, unknown> | undefined;
}

export interface GitApprovalPort {
    onToolInput(handler: (value: unknown) => void): () => void;
    onToolResult(
        handler: (value: GitApprovalToolResultNotification) => void,
    ): () => void;
    onToolCancelled(handler: () => void): () => void;
    onHostContextChanged(
        handler: (value: { readonly theme?: unknown }) => void,
    ): () => void;
    onTeardown(handler: () => void): () => void;
    connect(): Promise<void>;
    getHostContext(): { readonly theme?: unknown } | undefined;
    callServerTool(call: GitApprovalServerCall): Promise<unknown>;
    close(): Promise<void>;
}

type Listener = (state: GitApprovalState) => void;

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

export class GitApprovalController {
    private state: GitApprovalState = {
        phase: "connecting",
        theme: "light",
        acknowledged: false,
        plan: null,
        receipt: null,
    };
    private input: GitApprovalInput | null = null;
    private readonly listeners = new Set<Listener>();
    private unregister: Array<() => void> = [];
    private started = false;
    private effectDispatched = false;
    private approvalChallenge: string | null = null;
    private closeStarted = false;

    constructor(private readonly port: GitApprovalPort) {}

    getState(): GitApprovalState {
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
        this.unregister = [
            this.port.onToolInput((value) => this.receiveInput(value)),
            this.port.onToolResult((value) => this.receiveResult(value)),
            this.port.onToolCancelled(() => this.closeFailClosed()),
            this.port.onHostContextChanged((value) => this.applyTheme(value)),
            this.port.onTeardown(() => this.finish()),
        ];
        try {
            await this.port.connect();
            this.applyTheme(this.port.getHostContext());
            if (this.state.phase === "connecting")
                this.setState({ phase: "approval_pending" });
        } catch {
            this.closeFailClosed();
        }
    }

    setAcknowledged(value: boolean): void {
        if (this.state.phase === "ready" && !this.effectDispatched)
            this.setState({ acknowledged: value });
    }

    async confirm(): Promise<void> {
        const plan = this.state.plan;
        if (
            this.state.phase !== "ready" ||
            !this.state.acknowledged ||
            plan === null ||
            this.approvalChallenge === null ||
            this.effectDispatched
        )
            return;
        // Reserve before dispatch. A lost reply must never enable a retry from this widget.
        this.effectDispatched = true;
        const approvalChallenge = this.approvalChallenge;
        this.approvalChallenge = null;
        this.setState({ phase: "executing", acknowledged: false });
        try {
            const result = await this.port.callServerTool({
                name: CONFIRM_GIT_APPROVAL_TOOL_NAME,
                arguments: confirmationArguments(plan, approvalChallenge),
            });
            const receipt = parseGitEffectReceipt(
                structuredContent(result),
                plan,
            );
            if (receipt === null) {
                this.setState({ phase: "unconfirmed" });
                return;
            }
            this.setState({ phase: "succeeded", receipt });
        } catch {
            this.setState({ phase: "unconfirmed" });
        }
    }

    async close(): Promise<void> {
        this.finish();
        if (this.closeStarted) return;
        this.closeStarted = true;
        await this.port.close();
    }

    private receiveInput(value: unknown): void {
        if (this.effectDispatched || this.state.phase === "closed") return;
        const input = parseGitApprovalInput(value);
        if (input === null || this.input !== null) {
            this.closeFailClosed();
            return;
        }
        this.input = input;
    }

    private receiveResult(value: GitApprovalToolResultNotification): void {
        if (this.effectDispatched || this.state.phase === "closed") return;
        const plan = parseGitApprovalPlan(
            value.isError === true ? null : value.structuredContent,
        );
        const challenge = parseApprovalChallenge(
            value._meta?.["hwpx-agent/git-approval-challenge"],
        );
        if (
            this.input === null ||
            plan === null ||
            challenge === null ||
            !inputMatchesPlan(this.input, plan)
        ) {
            this.closeFailClosed();
            return;
        }
        this.approvalChallenge = challenge;
        this.setState({ phase: "ready", plan, acknowledged: false });
    }

    private applyTheme(value: { readonly theme?: unknown } | undefined): void {
        if (value?.theme === "light" || value?.theme === "dark")
            this.setState({ theme: value.theme });
    }

    private closeFailClosed(): void {
        this.finish();
    }

    private finish(): void {
        if (this.state.phase === "closed") return;
        for (const unregister of this.unregister.splice(0)) unregister();
        this.approvalChallenge = null;
        this.setState({ phase: "closed", acknowledged: false });
    }

    private setState(change: Partial<GitApprovalState>): void {
        this.state = { ...this.state, ...change };
        for (const listener of this.listeners) listener(this.state);
    }
}
