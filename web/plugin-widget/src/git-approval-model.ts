export const GIT_APPROVAL_RESOURCE_URI =
    "ui://hwpx-agent/local-git-approval/v1.html" as const;
export const PREPARE_GIT_APPROVAL_TOOL_NAME =
    "local_companion_prepare_git_commit_approval" as const;
export const CONFIRM_GIT_APPROVAL_TOOL_NAME =
    "local_companion_confirm_and_execute_git_commit" as const;

export interface GitApprovalInput {
    readonly workspace_id: string;
    readonly operation_id: string;
    readonly output_id: string;
    readonly expected_sha256: string;
    readonly message: string;
}

export interface GitApprovalPlan extends GitApprovalInput {
    readonly output_pathspec: string;
    readonly expected_output_sha256: string;
    readonly expected_head: string;
    readonly expected_head_reference: string | null;
    readonly approval: {
        readonly effect: "git_commit";
        readonly target_sha256: string;
        readonly plan_sha256: string;
    };
    readonly executed: false;
}

export interface GitEffectReceipt {
    readonly workspace_id: string;
    readonly operation_id: string;
    readonly output_id: string;
    readonly commit_oid: string;
    readonly previous_head: string;
    readonly updated_reference: string | null;
    readonly output_sha256: string;
    readonly target_sha256: string;
    readonly plan_sha256: string;
    readonly approved_at_unix_seconds: number;
    readonly index_synchronized: true;
    readonly executed: true;
}

const IDENTIFIER = /^[A-Za-z0-9_-]{1,64}$/;
const DIGEST = /^(?!0+$)[0-9a-f]{64}$/;
const OID = /^(?!0+$)(?:[0-9a-f]{40}|[0-9a-f]{64})$/;
const HEAD_REFERENCE =
    /^refs\/heads\/(?!\.)(?!.*\.\.)(?!.*@\{)(?!.*\.lock(?:\/|$))[A-Za-z0-9._/-]+$/i;
const APPROVAL_CHALLENGE = /^[A-Za-z0-9_-]{43}$/;

function record(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exact(value: Record<string, unknown>, expected: readonly string[]) {
    const actual = Object.keys(value).sort();
    const keys = [...expected].sort();
    return (
        actual.length === keys.length &&
        actual.every((key, index) => key === keys[index])
    );
}

function identifier(value: unknown): value is string {
    return typeof value === "string" && IDENTIFIER.test(value);
}

function digest(value: unknown): value is string {
    return typeof value === "string" && DIGEST.test(value);
}

function oid(value: unknown): value is string {
    return typeof value === "string" && OID.test(value);
}

function headReference(value: unknown): value is string | null {
    return value === null || (typeof value === "string" && HEAD_REFERENCE.test(value));
}

function message(value: unknown): value is string {
    return (
        typeof value === "string" &&
        value.length > 0 &&
        new TextEncoder().encode(value).byteLength <= 128 &&
        value.trim() === value &&
        !/[\u0000-\u001f\u007f]/u.test(value)
    );
}

export function parseGitApprovalInput(value: unknown): GitApprovalInput | null {
    if (
        !record(value) ||
        !exact(value, [
            "workspace_id",
            "operation_id",
            "output_id",
            "expected_sha256",
            "message",
        ]) ||
        !identifier(value.workspace_id) ||
        !identifier(value.operation_id) ||
        !identifier(value.output_id) ||
        !digest(value.expected_sha256) ||
        !message(value.message)
    )
        return null;
    return value as unknown as GitApprovalInput;
}

export function parseGitApprovalPlan(value: unknown): GitApprovalPlan | null {
    if (
        !record(value) ||
        !exact(value, [
            "workspace_id",
            "operation_id",
            "output_id",
            "output_pathspec",
            "expected_output_sha256",
            "expected_head",
            "expected_head_reference",
            "message",
            "approval",
            "executed",
        ]) ||
        !identifier(value.workspace_id) ||
        !identifier(value.operation_id) ||
        !identifier(value.output_id) ||
        value.output_pathspec !== `output/${String(value.output_id)}.hwpx` ||
        !digest(value.expected_output_sha256) ||
        !oid(value.expected_head) ||
        !headReference(value.expected_head_reference) ||
        !message(value.message) ||
        !record(value.approval) ||
        !exact(value.approval, ["effect", "target_sha256", "plan_sha256"]) ||
        value.approval.effect !== "git_commit" ||
        !digest(value.approval.target_sha256) ||
        !digest(value.approval.plan_sha256) ||
        value.executed !== false
    )
        return null;
    return value as unknown as GitApprovalPlan;
}

export function inputMatchesPlan(
    input: GitApprovalInput,
    plan: GitApprovalPlan,
): boolean {
    return (
        input.workspace_id === plan.workspace_id &&
        input.operation_id === plan.operation_id &&
        input.output_id === plan.output_id &&
        input.expected_sha256 === plan.expected_output_sha256 &&
        input.message === plan.message
    );
}

export function parseGitEffectReceipt(
    value: unknown,
    plan: GitApprovalPlan,
): GitEffectReceipt | null {
    if (
        !record(value) ||
        !exact(value, [
            "workspace_id",
            "operation_id",
            "output_id",
            "commit_oid",
            "previous_head",
            "updated_reference",
            "output_sha256",
            "target_sha256",
            "plan_sha256",
            "approved_at_unix_seconds",
            "index_synchronized",
            "executed",
        ]) ||
        value.workspace_id !== plan.workspace_id ||
        value.operation_id !== plan.operation_id ||
        value.output_id !== plan.output_id ||
        !oid(value.commit_oid) ||
        !oid(value.previous_head) ||
        value.commit_oid === value.previous_head ||
        (value.commit_oid as string).length !== (value.previous_head as string).length ||
        !headReference(value.updated_reference) ||
        value.output_sha256 !== plan.expected_output_sha256 ||
        value.target_sha256 !== plan.approval.target_sha256 ||
        value.plan_sha256 !== plan.approval.plan_sha256 ||
        !Number.isSafeInteger(value.approved_at_unix_seconds) ||
        (value.approved_at_unix_seconds as number) <= 0 ||
        value.index_synchronized !== true ||
        value.executed !== true
    )
        return null;
    return value as unknown as GitEffectReceipt;
}

export function parseApprovalChallenge(value: unknown): string | null {
    return typeof value === "string" && APPROVAL_CHALLENGE.test(value)
        ? value
        : null;
}

export function confirmationArguments(plan: GitApprovalPlan, challenge: string) {
    const approvalChallenge = parseApprovalChallenge(challenge);
    if (approvalChallenge === null) throw new Error("invalid approval challenge");
    return {
        workspace_id: plan.workspace_id,
        operation_id: plan.operation_id,
        output_id: plan.output_id,
        expected_sha256: plan.expected_output_sha256,
        message: plan.message,
        expected_head: plan.expected_head,
        expected_head_reference: plan.expected_head_reference,
        target_sha256: plan.approval.target_sha256,
        plan_sha256: plan.approval.plan_sha256,
        approval_challenge: approvalChallenge,
    } as const;
}
