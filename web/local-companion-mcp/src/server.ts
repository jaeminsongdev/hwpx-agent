import { spawn } from "node:child_process";
import { createHmac, randomBytes, randomUUID } from "node:crypto";
import { lstat, readFile, realpath } from "node:fs/promises";
import { dirname, extname, isAbsolute } from "node:path";
import { pathToFileURL } from "node:url";
import { TextDecoder } from "node:util";

import {
    type CallToolResult,
    type JSONValue,
    McpServer,
    fromJsonSchema,
} from "@modelcontextprotocol/server";
import { serveStdio } from "@modelcontextprotocol/server/stdio";

export const TOOL_NAME = "local_companion_health";
export const PRIVATE_PROTOCOL = "hwpx-agent.local-companion-private/v1";
export const WORKFLOW_PROTOCOL = "hwpx-agent.local-companion-private/v2";
export const APPROVAL_PROTOCOL = "hwpx-agent.local-companion-private/v3";
export const EFFECT_PROTOCOL = "hwpx-agent.local-companion-private/v4";
export const MATERIALIZE_TOOL_NAME = "local_companion_materialize";
export const DIFF_TOOL_NAME = "local_companion_diff";
export const PUBLISH_TOOL_NAME = "local_companion_publish";
export const PREPARE_COMMIT_TOOL_NAME = "local_companion_prepare_git_commit";
export const PREPARE_APPROVAL_TOOL_NAME =
    "local_companion_prepare_git_commit_approval";
export const CONFIRM_COMMIT_TOOL_NAME =
    "local_companion_confirm_and_execute_git_commit";
export const GIT_APPROVAL_RESOURCE_URI =
    "ui://hwpx-agent/local-git-approval/v1.html";
export const TARGET_PROFILE = "hancom-2020-x86-11.0.0.9136";
const SESSION_ENV = "HWPX_AGENT_LOCAL_SESSION_TOKEN";
const GIT_PROGRAM_ENV = "HWPX_AGENT_GIT_PROGRAM";
const APPROVAL_STATE_ROOT_ENV = "HWPX_AGENT_APPROVAL_STATE_ROOT";
const APPROVAL_SECRET_ENV = "HWPX_AGENT_APPROVAL_SECRET";
const APPROVAL_ACTOR_ENV = "HWPX_AGENT_APPROVAL_ACTOR_SHA256";
const APPROVAL_TENANT_ENV = "HWPX_AGENT_APPROVAL_TENANT_SHA256";
const REQUEST_ID = "mcp-health";
const MAX_STDOUT_BYTES = 16_384;
const MAX_STDERR_BYTES = 4_096;
const MAX_CONFIG_BYTES = 65_536;
const MAX_WIDGET_BYTES = 800_000;
const MAX_PENDING_WIDGET_APPROVALS = 128;
const WIDGET_APPROVAL_TTL_SECONDS = 300;
const DAEMON_TIMEOUT_MS = 10_000;
const MAX_FILE_BYTES = 1_073_741_824;
const IDENTIFIER_PATTERN = "^[A-Za-z0-9_-]{1,64}$";
const DIGEST_PATTERN = "^[0-9a-f]{64}$";

type JsonRecord = Record<string, JSONValue>;

export interface RuntimeConfig {
    readonly daemonPath: string;
    readonly configPath: string;
    readonly widgetPath: string;
    readonly widgetHtml: string;
}

export interface HealthResult {
    readonly status: "ready";
    readonly target_profile: typeof TARGET_PROFILE;
    readonly automation_enabled: false;
    readonly network_enabled: false;
    readonly workspace_count: number;
    readonly config_sha256: string;
}

export type WorkflowMethod =
    | "materialize"
    | "diff"
    | "publish"
    | "prepare_git_commit";

export interface MaterializeResult {
    readonly workspace_id: string;
    readonly operation_id: string;
    readonly slot: "source" | "candidate";
    readonly sha256: string;
    readonly size_bytes: number;
}

export interface FileIdentityResult {
    readonly sha256: string;
    readonly size_bytes: number;
}

export interface DiffResult {
    readonly workspace_id: string;
    readonly operation_id: string;
    readonly identical: boolean;
    readonly source: FileIdentityResult;
    readonly candidate: FileIdentityResult;
}

export interface PublishResult {
    readonly workspace_id: string;
    readonly operation_id: string;
    readonly output_id: string;
    readonly sha256: string;
    readonly size_bytes: number;
}

export interface GitCommitPlanResult {
    readonly workspace_id: string;
    readonly output_id: string;
    readonly output_pathspec: string;
    readonly expected_output_sha256: string;
    readonly expected_head: string;
    readonly message: string;
    readonly executed: false;
}

export interface GitApprovalPlanResult {
    readonly workspace_id: string;
    readonly operation_id: string;
    readonly output_id: string;
    readonly output_pathspec: string;
    readonly expected_output_sha256: string;
    readonly expected_head: string;
    readonly expected_head_reference: string | null;
    readonly message: string;
    readonly approval: {
        readonly effect: "git_commit";
        readonly target_sha256: string;
        readonly plan_sha256: string;
    };
    readonly executed: false;
}

export interface GitCommitEffectResult {
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

export type WorkflowResult =
    | MaterializeResult
    | DiffResult
    | PublishResult
    | GitCommitPlanResult;

interface SpawnOutcome {
    readonly code: number | null;
    readonly signal: NodeJS.Signals | null;
}

interface BoundedOutput {
    readonly stdout: Buffer;
    readonly stderr: Buffer;
    readonly overflowed: boolean;
}

export function parseRuntimeArguments(argumentsValue: readonly string[]): {
    readonly daemonPath: string;
    readonly configPath: string;
    readonly widgetPath: string;
} {
    if (
        argumentsValue.length !== 6 ||
        argumentsValue[0] !== "--daemon" ||
        argumentsValue[2] !== "--config" ||
        argumentsValue[4] !== "--widget"
    ) {
        throw new Error("invalid local companion arguments");
    }
    const daemonPath = argumentsValue[1];
    const configPath = argumentsValue[3];
    const widgetPath = argumentsValue[5];
    if (
        daemonPath === undefined ||
        configPath === undefined ||
        widgetPath === undefined ||
        !isAbsolute(daemonPath) ||
        !isAbsolute(configPath) ||
        !isAbsolute(widgetPath) ||
        daemonPath.length > 1_024 ||
        configPath.length > 1_024 ||
        widgetPath.length > 1_024
    ) {
        throw new Error("invalid local companion paths");
    }
    return { daemonPath, configPath, widgetPath };
}

export async function loadRuntimeConfig(
    argumentsValue: readonly string[],
): Promise<RuntimeConfig> {
    const parsed = parseRuntimeArguments(argumentsValue);
    const [daemonMetadata, configMetadata, widgetMetadata] = await Promise.all([
        lstat(parsed.daemonPath),
        lstat(parsed.configPath),
        lstat(parsed.widgetPath),
    ]);
    if (
        !daemonMetadata.isFile() ||
        daemonMetadata.isSymbolicLink() ||
        !configMetadata.isFile() ||
        configMetadata.isSymbolicLink() ||
        !widgetMetadata.isFile() ||
        widgetMetadata.isSymbolicLink() ||
        configMetadata.size < 1 ||
        configMetadata.size > MAX_CONFIG_BYTES ||
        widgetMetadata.size < 1 ||
        widgetMetadata.size > MAX_WIDGET_BYTES ||
        (process.platform === "win32" &&
            extname(parsed.daemonPath).toLowerCase() !== ".exe")
    ) {
        throw new Error("invalid local companion files");
    }
    const [daemonPath, configPath, widgetPath] = await Promise.all([
        realpath(parsed.daemonPath),
        realpath(parsed.configPath),
        realpath(parsed.widgetPath),
    ]);
    const widgetHtml = await readFile(widgetPath, "utf8");
    if (
        Buffer.byteLength(widgetHtml, "utf8") > MAX_WIDGET_BYTES ||
        /<(?:base|embed|form|iframe|object)\b/iu.test(widgetHtml) ||
        /<meta\b[^>]*http-equiv\s*=\s*["']?refresh/iu.test(widgetHtml) ||
        /<(?:audio|img|link|script|source|track|video)\b[^>]*(?:href|poster|src|srcset)\s*=/iu.test(
            widgetHtml,
        ) ||
        /\b(?:action|href|poster|src|srcset)\s*=\s*["']?\s*(?:https?:|\/\/)/iu.test(
            widgetHtml,
        ) ||
        /@import\s|url\(\s*["']?(?:https?:|\/\/)/iu.test(widgetHtml)
    ) {
        throw new Error("invalid local companion widget");
    }
    return { daemonPath, configPath, widgetPath, widgetHtml };
}

export function childEnvironment(
    token: string,
    source: NodeJS.ProcessEnv = process.env,
): NodeJS.ProcessEnv {
    if (!/^[A-Za-z0-9_-]{43}$/.test(token)) {
        throw new Error("invalid local companion token");
    }
    const environment: NodeJS.ProcessEnv = { [SESSION_ENV]: token };
    for (const name of ["SystemRoot", "WINDIR"] as const) {
        const value = source[name];
        if (value !== undefined && value.length > 0 && value.length <= 1_024) {
            environment[name] = value;
        }
    }
    return environment;
}

export function childEffectEnvironment(
    token: string,
    source: NodeJS.ProcessEnv = process.env,
): NodeJS.ProcessEnv {
    const environment = childEnvironment(token, source);
    const gitProgram = source[GIT_PROGRAM_ENV];
    const stateRoot = source[APPROVAL_STATE_ROOT_ENV];
    const secret = source[APPROVAL_SECRET_ENV];
    if (
        gitProgram === undefined ||
        stateRoot === undefined ||
        secret === undefined ||
        !isAbsolute(gitProgram) ||
        !isAbsolute(stateRoot) ||
        gitProgram.length > 1_024 ||
        stateRoot.length > 1_024 ||
        !/^[A-Za-z0-9_-]{43,171}$/.test(secret) ||
        Buffer.from(secret, "base64url").toString("base64url") !== secret
    ) {
        throw new Error("local effect host is not configured");
    }
    const secretBytes = Buffer.from(secret, "base64url");
    try {
        if (secretBytes.length < 32 || secretBytes.length > 128) {
            throw new Error("local effect host is not configured");
        }
        environment[GIT_PROGRAM_ENV] = gitProgram;
        environment[APPROVAL_STATE_ROOT_ENV] = stateRoot;
        environment[APPROVAL_SECRET_ENV] = secret;
        environment.TEMP = stateRoot;
        environment.TMP = stateRoot;
        return environment;
    } finally {
        secretBytes.fill(0);
    }
}

export function privateHealthRequest(token: string): JsonRecord {
    if (!/^[A-Za-z0-9_-]{43}$/.test(token)) {
        throw new Error("invalid local companion token");
    }
    return {
        protocol_version: PRIVATE_PROTOCOL,
        request_id: REQUEST_ID,
        session_token: token,
        method: "health",
        params: {},
    };
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function validateHealthEnvelope(value: unknown): HealthResult {
    if (!isRecord(value)) throw new Error("invalid daemon response");
    if (
        JSON.stringify(Object.keys(value).sort()) !==
            JSON.stringify(
                ["ok", "protocol_version", "request_id", "result"].sort(),
            ) ||
        value.protocol_version !== PRIVATE_PROTOCOL ||
        value.request_id !== REQUEST_ID ||
        value.ok !== true ||
        !isRecord(value.result)
    ) {
        throw new Error("invalid daemon response");
    }
    const result = value.result;
    if (
        JSON.stringify(Object.keys(result).sort()) !==
            JSON.stringify(
                [
                    "automation_enabled",
                    "config_sha256",
                    "network_enabled",
                    "status",
                    "target_profile",
                    "workspace_count",
                ].sort(),
            ) ||
        result.status !== "ready" ||
        result.target_profile !== TARGET_PROFILE ||
        result.automation_enabled !== false ||
        result.network_enabled !== false ||
        !Number.isSafeInteger(result.workspace_count) ||
        (result.workspace_count as number) < 1 ||
        (result.workspace_count as number) > 8 ||
        typeof result.config_sha256 !== "string" ||
        !/^[0-9a-f]{64}$/.test(result.config_sha256)
    ) {
        throw new Error("invalid daemon health");
    }
    return result as unknown as HealthResult;
}

function hasExactKeys(
    value: Record<string, unknown>,
    expected: readonly string[],
): boolean {
    return (
        JSON.stringify(Object.keys(value).sort()) ===
        JSON.stringify([...expected].sort())
    );
}

function isIdentifier(value: unknown): value is string {
    return (
        typeof value === "string" && new RegExp(IDENTIFIER_PATTERN).test(value)
    );
}

function isDigest(value: unknown): value is string {
    return (
        typeof value === "string" &&
        new RegExp(DIGEST_PATTERN).test(value) &&
        value !== "0".repeat(64)
    );
}

function isSize(value: unknown): value is number {
    return (
        Number.isSafeInteger(value) &&
        (value as number) > 0 &&
        (value as number) <= MAX_FILE_BYTES
    );
}

function isCommitMessage(value: unknown): value is string {
    return (
        typeof value === "string" &&
        value.length > 0 &&
        Buffer.byteLength(value, "utf8") <= 128 &&
        value.trim() === value &&
        !/[\u0000-\u001f\u007f]/u.test(value)
    );
}

function isGitOid(value: unknown): value is string {
    return (
        typeof value === "string" &&
        /^(?!0+$)(?:[0-9a-f]{40}|[0-9a-f]{64})$/.test(value)
    );
}

function isHeadReference(value: unknown): value is string {
    return (
        typeof value === "string" &&
        /^refs\/heads\/(?!\.)(?!.*\.\.)(?!.*@\{)(?!.*\.lock(?:\/|$))[A-Za-z0-9._/-]+$/i.test(
            value,
        ) &&
        !value.endsWith("/") &&
        !value.endsWith(".")
    );
}

function isConfirmation(value: unknown): value is string {
    return (
        typeof value === "string" &&
        value.length <= 4_096 &&
        /^confirm_v1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(value)
    );
}

function isUnixSeconds(value: unknown): value is number {
    return Number.isSafeInteger(value) && (value as number) > 0;
}

function workflowRequestId(method: WorkflowMethod): string {
    return `mcp-workflow-${method}`;
}

function validateWorkflowParams(
    method: WorkflowMethod,
    params: JsonRecord,
): void {
    if (method === "materialize") {
        if (
            !hasExactKeys(params, [
                "expected_sha256",
                "fixture_id",
                "operation_id",
                "slot",
                "workspace_id",
            ]) ||
            !isIdentifier(params.workspace_id) ||
            !isIdentifier(params.operation_id) ||
            !isIdentifier(params.fixture_id) ||
            !["source", "candidate"].includes(params.slot as string) ||
            !isDigest(params.expected_sha256)
        ) {
            throw new Error("invalid workflow request");
        }
        return;
    }
    if (method === "diff") {
        if (
            !hasExactKeys(params, ["operation_id", "workspace_id"]) ||
            !isIdentifier(params.workspace_id) ||
            !isIdentifier(params.operation_id)
        ) {
            throw new Error("invalid workflow request");
        }
        return;
    }
    if (method === "publish") {
        if (
            !hasExactKeys(params, [
                "expected_sha256",
                "operation_id",
                "output_id",
                "workspace_id",
            ]) ||
            !isIdentifier(params.workspace_id) ||
            !isIdentifier(params.operation_id) ||
            !isIdentifier(params.output_id) ||
            !isDigest(params.expected_sha256)
        ) {
            throw new Error("invalid workflow request");
        }
        return;
    }
    if (
        !hasExactKeys(params, [
            "expected_sha256",
            "message",
            "output_id",
            "workspace_id",
        ]) ||
        !isIdentifier(params.workspace_id) ||
        !isIdentifier(params.output_id) ||
        !isDigest(params.expected_sha256) ||
        !isCommitMessage(params.message)
    ) {
        throw new Error("invalid workflow request");
    }
}

export function privateWorkflowRequest(
    token: string,
    method: WorkflowMethod,
    params: JsonRecord,
): JsonRecord {
    if (!/^[A-Za-z0-9_-]{43}$/.test(token)) {
        throw new Error("invalid local companion token");
    }
    validateWorkflowParams(method, params);
    return {
        protocol_version: WORKFLOW_PROTOCOL,
        request_id: workflowRequestId(method),
        session_token: token,
        method,
        params,
    };
}

function validateIdentity(value: unknown): FileIdentityResult {
    if (
        !isRecord(value) ||
        !hasExactKeys(value, ["sha256", "size_bytes"]) ||
        !isDigest(value.sha256) ||
        !isSize(value.size_bytes)
    ) {
        throw new Error("invalid daemon workflow result");
    }
    return value as unknown as FileIdentityResult;
}

export function validateWorkflowEnvelope(
    value: unknown,
    method: WorkflowMethod,
    params: JsonRecord,
): WorkflowResult {
    if (
        !isRecord(value) ||
        !hasExactKeys(value, [
            "ok",
            "protocol_version",
            "request_id",
            "result",
        ]) ||
        value.protocol_version !== WORKFLOW_PROTOCOL ||
        value.request_id !== workflowRequestId(method) ||
        value.ok !== true ||
        !isRecord(value.result)
    ) {
        throw new Error("invalid daemon workflow response");
    }
    validateWorkflowParams(method, params);
    const result = value.result;
    if (method === "materialize") {
        if (
            !hasExactKeys(result, [
                "operation_id",
                "sha256",
                "size_bytes",
                "slot",
                "workspace_id",
            ]) ||
            result.workspace_id !== params.workspace_id ||
            result.operation_id !== params.operation_id ||
            result.slot !== params.slot ||
            result.sha256 !== params.expected_sha256 ||
            !isSize(result.size_bytes)
        ) {
            throw new Error("invalid daemon materialize result");
        }
        return result as unknown as MaterializeResult;
    }
    if (method === "diff") {
        if (
            !hasExactKeys(result, [
                "candidate",
                "identical",
                "operation_id",
                "source",
                "workspace_id",
            ]) ||
            result.workspace_id !== params.workspace_id ||
            result.operation_id !== params.operation_id ||
            typeof result.identical !== "boolean"
        ) {
            throw new Error("invalid daemon diff result");
        }
        const source = validateIdentity(result.source);
        const candidate = validateIdentity(result.candidate);
        if (
            result.identical !==
            (source.sha256 === candidate.sha256 &&
                source.size_bytes === candidate.size_bytes)
        ) {
            throw new Error("inconsistent daemon diff result");
        }
        return result as unknown as DiffResult;
    }
    if (method === "publish") {
        if (
            !hasExactKeys(result, [
                "operation_id",
                "output_id",
                "sha256",
                "size_bytes",
                "workspace_id",
            ]) ||
            result.workspace_id !== params.workspace_id ||
            result.operation_id !== params.operation_id ||
            result.output_id !== params.output_id ||
            result.sha256 !== params.expected_sha256 ||
            !isSize(result.size_bytes)
        ) {
            throw new Error("invalid daemon publish result");
        }
        return result as unknown as PublishResult;
    }
    const expectedPathspec = `output/${String(params.output_id)}.hwpx`;
    if (
        !hasExactKeys(result, [
            "executed",
            "expected_head",
            "expected_output_sha256",
            "message",
            "output_id",
            "output_pathspec",
            "workspace_id",
        ]) ||
        result.workspace_id !== params.workspace_id ||
        result.output_id !== params.output_id ||
        result.output_pathspec !== expectedPathspec ||
        result.expected_output_sha256 !== params.expected_sha256 ||
        result.message !== params.message ||
        result.executed !== false ||
        typeof result.expected_head !== "string" ||
        !/^(?!0+$)(?:[0-9a-f]{40}|[0-9a-f]{64})$/.test(result.expected_head)
    ) {
        throw new Error("invalid daemon Git plan result");
    }
    return result as unknown as GitCommitPlanResult;
}

function validateApprovalParams(params: JsonRecord): void {
    if (
        !hasExactKeys(params, [
            "expected_sha256",
            "message",
            "operation_id",
            "output_id",
            "workspace_id",
        ]) ||
        !isIdentifier(params.workspace_id) ||
        !isIdentifier(params.operation_id) ||
        !isIdentifier(params.output_id) ||
        !isDigest(params.expected_sha256) ||
        !isCommitMessage(params.message)
    ) {
        throw new Error("invalid approval preparation request");
    }
}

export function privateApprovalRequest(
    token: string,
    params: JsonRecord,
): JsonRecord {
    if (!/^[A-Za-z0-9_-]{43}$/.test(token)) {
        throw new Error("invalid local companion token");
    }
    validateApprovalParams(params);
    return {
        protocol_version: APPROVAL_PROTOCOL,
        request_id: "mcp-approval-prepare_git_commit_approval",
        session_token: token,
        method: "prepare_git_commit_approval",
        params,
    };
}

export function validateApprovalEnvelope(
    value: unknown,
    params: JsonRecord,
): GitApprovalPlanResult {
    if (
        !isRecord(value) ||
        !hasExactKeys(value, [
            "ok",
            "protocol_version",
            "request_id",
            "result",
        ]) ||
        value.protocol_version !== APPROVAL_PROTOCOL ||
        value.request_id !== "mcp-approval-prepare_git_commit_approval" ||
        value.ok !== true ||
        !isRecord(value.result)
    ) {
        throw new Error("invalid approval preparation response");
    }
    validateApprovalParams(params);
    const result = value.result;
    const expectedPathspec = `output/${String(params.output_id)}.hwpx`;
    if (
        !hasExactKeys(result, [
            "approval",
            "executed",
            "expected_head",
            "expected_head_reference",
            "expected_output_sha256",
            "message",
            "operation_id",
            "output_id",
            "output_pathspec",
            "workspace_id",
        ]) ||
        result.workspace_id !== params.workspace_id ||
        result.operation_id !== params.operation_id ||
        result.output_id !== params.output_id ||
        result.output_pathspec !== expectedPathspec ||
        result.expected_output_sha256 !== params.expected_sha256 ||
        result.message !== params.message ||
        result.executed !== false ||
        !isGitOid(result.expected_head) ||
        (result.expected_head_reference !== null &&
            !isHeadReference(result.expected_head_reference)) ||
        !isRecord(result.approval) ||
        !hasExactKeys(result.approval, [
            "effect",
            "plan_sha256",
            "target_sha256",
        ]) ||
        result.approval.effect !== "git_commit" ||
        !isDigest(result.approval.target_sha256) ||
        !isDigest(result.approval.plan_sha256)
    ) {
        throw new Error("invalid approval preparation result");
    }
    return result as unknown as GitApprovalPlanResult;
}

function validateConfirmationParams(params: JsonRecord): void {
    if (
        !hasExactKeys(params, [
            "expected_head",
            "expected_head_reference",
            "expected_sha256",
            "message",
            "operation_id",
            "output_id",
            "plan_sha256",
            "target_sha256",
            "workspace_id",
        ]) ||
        !isIdentifier(params.workspace_id) ||
        !isIdentifier(params.operation_id) ||
        !isIdentifier(params.output_id) ||
        !isDigest(params.expected_sha256) ||
        !isCommitMessage(params.message) ||
        !isGitOid(params.expected_head) ||
        !(params.expected_head_reference === null ||
            isHeadReference(params.expected_head_reference)) ||
        !isDigest(params.target_sha256) ||
        !isDigest(params.plan_sha256)
    ) {
        throw new Error("invalid trusted confirmation request");
    }
}

function widgetConfirmationParams(params: JsonRecord): {
    readonly challenge: string;
    readonly confirmed: JsonRecord;
} {
    if (
        !hasExactKeys(params, [
            "approval_challenge",
            "expected_head",
            "expected_head_reference",
            "expected_sha256",
            "message",
            "operation_id",
            "output_id",
            "plan_sha256",
            "target_sha256",
            "workspace_id",
        ]) ||
        typeof params.approval_challenge !== "string" ||
        !/^[A-Za-z0-9_-]{43}$/.test(params.approval_challenge)
    ) {
        throw new Error("invalid trusted widget confirmation request");
    }
    const confirmed: JsonRecord = {
        workspace_id: params.workspace_id as JSONValue,
        operation_id: params.operation_id as JSONValue,
        output_id: params.output_id as JSONValue,
        expected_sha256: params.expected_sha256 as JSONValue,
        message: params.message as JSONValue,
        expected_head: params.expected_head as JSONValue,
        expected_head_reference: params.expected_head_reference as JSONValue,
        target_sha256: params.target_sha256 as JSONValue,
        plan_sha256: params.plan_sha256 as JSONValue,
    };
    validateConfirmationParams(confirmed);
    return { challenge: params.approval_challenge, confirmed };
}

function confirmationMatchesPlan(
    params: JsonRecord,
    plan: GitApprovalPlanResult,
): boolean {
    return (
        params.workspace_id === plan.workspace_id &&
        params.operation_id === plan.operation_id &&
        params.output_id === plan.output_id &&
        params.expected_sha256 === plan.expected_output_sha256 &&
        params.message === plan.message &&
        params.expected_head === plan.expected_head &&
        params.expected_head_reference === plan.expected_head_reference &&
        params.target_sha256 === plan.approval.target_sha256 &&
        params.plan_sha256 === plan.approval.plan_sha256 &&
        plan.executed === false
    );
}

interface ConfirmationIdentity {
    readonly actorSha256: string;
    readonly tenantSha256: string;
    readonly secret: Buffer;
}

export function loadConfirmationIdentity(
    source: NodeJS.ProcessEnv = process.env,
): ConfirmationIdentity {
    const actorSha256 = source[APPROVAL_ACTOR_ENV];
    const tenantSha256 = source[APPROVAL_TENANT_ENV];
    const encodedSecret = source[APPROVAL_SECRET_ENV];
    if (
        !isDigest(actorSha256) ||
        !isDigest(tenantSha256) ||
        encodedSecret === undefined ||
        !/^[A-Za-z0-9_-]{43,171}$/.test(encodedSecret) ||
        Buffer.from(encodedSecret, "base64url").toString("base64url") !==
            encodedSecret
    ) {
        throw new Error("trusted confirmation authority is not configured");
    }
    const secret = Buffer.from(encodedSecret, "base64url");
    if (secret.length < 32 || secret.length > 128) {
        secret.fill(0);
        throw new Error("trusted confirmation authority is not configured");
    }
    return { actorSha256, tenantSha256, secret };
}

export function mintGitConfirmation(
    plan: GitApprovalPlanResult,
    identity: ConfirmationIdentity,
    issuedAtUnixSeconds: number,
): string {
    if (
        !Number.isSafeInteger(issuedAtUnixSeconds) ||
        issuedAtUnixSeconds <= 0 ||
        identity.secret.length < 32 ||
        identity.secret.length > 128 ||
        !isDigest(identity.actorSha256) ||
        !isDigest(identity.tenantSha256)
    ) {
        throw new Error("invalid confirmation authority");
    }
    const payload = Buffer.from(
        JSON.stringify({
            schema_version: "hwpx-agent.confirmation/v1",
            token_id: `cnf_${randomUUID().replaceAll("-", "")}`,
            operation_id: plan.operation_id,
            actor_sha256: identity.actorSha256,
            tenant_sha256: identity.tenantSha256,
            effect: "git_commit",
            target_sha256: plan.approval.target_sha256,
            plan_sha256: plan.approval.plan_sha256,
            issued_at_unix_seconds: issuedAtUnixSeconds,
            expires_at_unix_seconds: issuedAtUnixSeconds + 60,
            user_confirmed: true,
        }),
        "utf8",
    );
    try {
        const signature = createHmac("sha256", identity.secret)
            .update(payload)
            .digest();
        try {
            return `confirm_v1.${payload.toString("base64url")}.${signature.toString("base64url")}`;
        } finally {
            signature.fill(0);
        }
    } finally {
        payload.fill(0);
    }
}

function validateEffectParams(params: JsonRecord): void {
    if (
        !hasExactKeys(params, [
            "actor_sha256",
            "confirmation_token",
            "expected_sha256",
            "message",
            "operation_id",
            "output_id",
            "requested_at_unix_seconds",
            "tenant_sha256",
            "workspace_id",
        ]) ||
        !isIdentifier(params.workspace_id) ||
        !isIdentifier(params.operation_id) ||
        !isIdentifier(params.output_id) ||
        !isDigest(params.expected_sha256) ||
        !isCommitMessage(params.message) ||
        !isDigest(params.actor_sha256) ||
        !isDigest(params.tenant_sha256) ||
        !isUnixSeconds(params.requested_at_unix_seconds) ||
        !isConfirmation(params.confirmation_token)
    ) {
        throw new Error("invalid Git effect request");
    }
}

export function privateEffectRequest(
    token: string,
    params: JsonRecord,
): JsonRecord {
    if (!/^[A-Za-z0-9_-]{43}$/.test(token)) {
        throw new Error("invalid local companion token");
    }
    validateEffectParams(params);
    return {
        protocol_version: EFFECT_PROTOCOL,
        request_id: "mcp-effect-execute_git_commit",
        session_token: token,
        method: "execute_git_commit",
        params,
    };
}

export function validateEffectEnvelope(
    value: unknown,
    params: JsonRecord,
): GitCommitEffectResult {
    if (
        !isRecord(value) ||
        !hasExactKeys(value, [
            "ok",
            "protocol_version",
            "request_id",
            "result",
        ]) ||
        value.protocol_version !== EFFECT_PROTOCOL ||
        value.request_id !== "mcp-effect-execute_git_commit" ||
        value.ok !== true ||
        !isRecord(value.result)
    ) {
        throw new Error("invalid Git effect response");
    }
    validateEffectParams(params);
    const result = value.result;
    if (
        !hasExactKeys(result, [
            "approved_at_unix_seconds",
            "commit_oid",
            "executed",
            "index_synchronized",
            "operation_id",
            "output_id",
            "output_sha256",
            "plan_sha256",
            "previous_head",
            "target_sha256",
            "updated_reference",
            "workspace_id",
        ]) ||
        result.workspace_id !== params.workspace_id ||
        result.operation_id !== params.operation_id ||
        result.output_id !== params.output_id ||
        result.output_sha256 !== params.expected_sha256 ||
        !isGitOid(result.commit_oid) ||
        !isGitOid(result.previous_head) ||
        result.commit_oid === result.previous_head ||
        result.commit_oid.length !== result.previous_head.length ||
        (result.updated_reference !== null &&
            !isHeadReference(result.updated_reference)) ||
        !isDigest(result.target_sha256) ||
        !isDigest(result.plan_sha256) ||
        !isUnixSeconds(result.approved_at_unix_seconds) ||
        (result.approved_at_unix_seconds as number) <
            (params.requested_at_unix_seconds as number) ||
        result.index_synchronized !== true ||
        result.executed !== true
    ) {
        throw new Error("invalid Git effect result");
    }
    return result as unknown as GitCommitEffectResult;
}

function appendBounded(
    chunks: Buffer[],
    chunk: Buffer,
    currentBytes: number,
    maximumBytes: number,
): number {
    const nextBytes = currentBytes + chunk.length;
    if (nextBytes <= maximumBytes) chunks.push(chunk);
    return nextBytes;
}

async function runDaemon(
    config: RuntimeConfig,
    token: string,
    request: JsonRecord,
    environment: NodeJS.ProcessEnv = childEnvironment(token),
): Promise<BoundedOutput & SpawnOutcome> {
    const child = spawn(config.daemonPath, ["--config", config.configPath], {
        cwd: dirname(config.configPath),
        env: environment,
        shell: false,
        stdio: ["pipe", "pipe", "pipe"],
        windowsHide: true,
    });
    const stdoutChunks: Buffer[] = [];
    const stderrChunks: Buffer[] = [];
    let stdoutBytes = 0;
    let stderrBytes = 0;
    let overflowed = false;
    child.stdout.on("data", (chunk: Buffer) => {
        stdoutBytes = appendBounded(
            stdoutChunks,
            chunk,
            stdoutBytes,
            MAX_STDOUT_BYTES,
        );
        if (stdoutBytes > MAX_STDOUT_BYTES) {
            overflowed = true;
            child.kill();
        }
    });
    child.stderr.on("data", (chunk: Buffer) => {
        stderrBytes = appendBounded(
            stderrChunks,
            chunk,
            stderrBytes,
            MAX_STDERR_BYTES,
        );
        if (stderrBytes > MAX_STDERR_BYTES) {
            overflowed = true;
            child.kill();
        }
    });
    child.stdin.on("error", () => undefined);
    const completion = new Promise<SpawnOutcome>((resolve, reject) => {
        child.once("error", () => reject(new Error("daemon spawn failed")));
        child.once("close", (code, signal) => resolve({ code, signal }));
    });
    const payload = `${JSON.stringify(request)}\n`;
    child.stdin.end(payload, "utf8");
    let timer: NodeJS.Timeout | undefined;
    try {
        const outcome = await Promise.race([
            completion,
            new Promise<never>((_resolve, reject) => {
                timer = setTimeout(() => {
                    child.kill();
                    reject(new Error("daemon timeout"));
                }, DAEMON_TIMEOUT_MS);
            }),
        ]);
        return {
            ...outcome,
            stdout: Buffer.concat(stdoutChunks),
            stderr: Buffer.concat(stderrChunks),
            overflowed,
        };
    } finally {
        if (timer !== undefined) clearTimeout(timer);
    }
}

export async function callLocalHealth(
    config: RuntimeConfig,
): Promise<HealthResult> {
    const tokenBytes = randomBytes(32);
    let token = tokenBytes.toString("base64url");
    try {
        const output = await runDaemon(
            config,
            token,
            privateHealthRequest(token),
        );
        if (
            output.code !== 0 ||
            output.signal !== null ||
            output.overflowed ||
            output.stderr.length !== 0
        ) {
            throw new Error("daemon failed");
        }
        const text = new TextDecoder("utf-8", { fatal: true }).decode(
            output.stdout,
        );
        if (
            text.includes("\r") ||
            text.includes(token) ||
            text.includes(config.daemonPath) ||
            text.includes(config.configPath)
        ) {
            throw new Error("daemon response disclosed private data");
        }
        const lines = text.split("\n");
        const line = lines[0];
        if (
            lines.length !== 2 ||
            line === undefined ||
            line === "" ||
            lines[1] !== ""
        ) {
            throw new Error("invalid daemon framing");
        }
        return validateHealthEnvelope(JSON.parse(line));
    } finally {
        token = "";
        tokenBytes.fill(0);
    }
}

export async function callLocalWorkflow(
    config: RuntimeConfig,
    method: WorkflowMethod,
    params: JsonRecord,
): Promise<WorkflowResult> {
    const tokenBytes = randomBytes(32);
    let token = tokenBytes.toString("base64url");
    try {
        const output = await runDaemon(
            config,
            token,
            privateWorkflowRequest(token, method, params),
        );
        if (
            output.code !== 0 ||
            output.signal !== null ||
            output.overflowed ||
            output.stderr.length !== 0
        ) {
            throw new Error("daemon failed");
        }
        const text = new TextDecoder("utf-8", { fatal: true }).decode(
            output.stdout,
        );
        if (
            text.includes("\r") ||
            text.includes(token) ||
            text.includes(config.daemonPath) ||
            text.includes(config.configPath)
        ) {
            throw new Error("daemon response disclosed private data");
        }
        const lines = text.split("\n");
        const line = lines[0];
        if (
            lines.length !== 2 ||
            line === undefined ||
            line === "" ||
            lines[1] !== ""
        ) {
            throw new Error("invalid daemon framing");
        }
        return validateWorkflowEnvelope(JSON.parse(line), method, params);
    } finally {
        token = "";
        tokenBytes.fill(0);
    }
}

export async function callLocalApproval(
    config: RuntimeConfig,
    params: JsonRecord,
): Promise<GitApprovalPlanResult> {
    const tokenBytes = randomBytes(32);
    let token = tokenBytes.toString("base64url");
    try {
        const output = await runDaemon(
            config,
            token,
            privateApprovalRequest(token, params),
        );
        if (
            output.code !== 0 ||
            output.signal !== null ||
            output.overflowed ||
            output.stderr.length !== 0
        ) {
            throw new Error("daemon failed");
        }
        const text = new TextDecoder("utf-8", { fatal: true }).decode(
            output.stdout,
        );
        if (
            text.includes("\r") ||
            text.includes(token) ||
            text.includes(config.daemonPath) ||
            text.includes(config.configPath)
        ) {
            throw new Error("daemon response disclosed private data");
        }
        const lines = text.split("\n");
        const line = lines[0];
        if (
            lines.length !== 2 ||
            line === undefined ||
            line === "" ||
            lines[1] !== ""
        ) {
            throw new Error("invalid daemon framing");
        }
        return validateApprovalEnvelope(JSON.parse(line), params);
    } finally {
        token = "";
        tokenBytes.fill(0);
    }
}

export async function callLocalEffect(
    config: RuntimeConfig,
    params: JsonRecord,
): Promise<GitCommitEffectResult> {
    const tokenBytes = randomBytes(32);
    let token = tokenBytes.toString("base64url");
    try {
        const output = await runDaemon(
            config,
            token,
            privateEffectRequest(token, params),
            childEffectEnvironment(token),
        );
        if (
            output.code !== 0 ||
            output.signal !== null ||
            output.overflowed ||
            output.stderr.length !== 0
        ) {
            throw new Error("daemon failed");
        }
        const text = new TextDecoder("utf-8", { fatal: true }).decode(
            output.stdout,
        );
        const confirmation = params.confirmation_token;
        if (
            text.includes("\r") ||
            text.includes(token) ||
            (typeof confirmation === "string" &&
                text.includes(confirmation)) ||
            text.includes(config.daemonPath) ||
            text.includes(config.configPath)
        ) {
            throw new Error("daemon response disclosed private data");
        }
        const lines = text.split("\n");
        const line = lines[0];
        if (
            lines.length !== 2 ||
            line === undefined ||
            line === "" ||
            lines[1] !== ""
        ) {
            throw new Error("invalid daemon framing");
        }
        return validateEffectEnvelope(JSON.parse(line), params);
    } finally {
        token = "";
        tokenBytes.fill(0);
    }
}

export async function confirmAndExecuteGitCommit(
    config: RuntimeConfig,
    params: JsonRecord,
    approval: (
        config: RuntimeConfig,
        params: JsonRecord,
    ) => Promise<GitApprovalPlanResult> = callLocalApproval,
    effect: (
        config: RuntimeConfig,
        params: JsonRecord,
    ) => Promise<GitCommitEffectResult> = callLocalEffect,
    now: () => number = () => Math.floor(Date.now() / 1_000),
    environment: NodeJS.ProcessEnv = process.env,
): Promise<GitCommitEffectResult> {
    validateConfirmationParams(params);
    const approvalParams: JsonRecord = {
        workspace_id: params.workspace_id as JSONValue,
        operation_id: params.operation_id as JSONValue,
        output_id: params.output_id as JSONValue,
        expected_sha256: params.expected_sha256 as JSONValue,
        message: params.message as JSONValue,
    };
    const currentPlan = await approval(config, approvalParams);
    if (!confirmationMatchesPlan(params, currentPlan)) {
        throw new Error("trusted confirmation no longer matches current Git state");
    }
    const identity = loadConfirmationIdentity(environment);
    let confirmationToken = "";
    try {
        const requestedAt = now();
        confirmationToken = mintGitConfirmation(
            currentPlan,
            identity,
            requestedAt,
        );
        const result = await effect(config, {
            ...approvalParams,
            actor_sha256: identity.actorSha256,
            tenant_sha256: identity.tenantSha256,
            requested_at_unix_seconds: requestedAt,
            confirmation_token: confirmationToken,
        });
        if (
            result.target_sha256 !== currentPlan.approval.target_sha256 ||
            result.plan_sha256 !== currentPlan.approval.plan_sha256 ||
            result.previous_head !== currentPlan.expected_head ||
            result.updated_reference !== currentPlan.expected_head_reference ||
            result.output_sha256 !== currentPlan.expected_output_sha256 ||
            result.approved_at_unix_seconds < requestedAt
        ) {
            throw new Error("Git effect receipt did not match the confirmed plan");
        }
        return result;
    } finally {
        confirmationToken = "";
        identity.secret.fill(0);
    }
}

const IDENTIFIER_SCHEMA: JsonRecord = {
    type: "string",
    pattern: IDENTIFIER_PATTERN,
};
const DIGEST_SCHEMA: JsonRecord = {
    type: "string",
    pattern: DIGEST_PATTERN,
};
const SIZE_SCHEMA: JsonRecord = {
    type: "integer",
    minimum: 1,
    maximum: MAX_FILE_BYTES,
};
const IDENTITY_SCHEMA: JsonRecord = {
    type: "object",
    properties: {
        sha256: DIGEST_SCHEMA,
        size_bytes: SIZE_SCHEMA,
    },
    required: ["sha256", "size_bytes"],
    additionalProperties: false,
};

function registerWorkflowTool(
    server: McpServer,
    config: RuntimeConfig,
    workflow: (
        config: RuntimeConfig,
        method: WorkflowMethod,
        params: JsonRecord,
    ) => Promise<WorkflowResult>,
    descriptor: {
        readonly name: string;
        readonly method: WorkflowMethod;
        readonly title: string;
        readonly description: string;
        readonly inputSchema: JsonRecord;
        readonly outputSchema: JsonRecord;
        readonly annotations: {
            readonly readOnlyHint: boolean;
            readonly destructiveHint: boolean;
            readonly idempotentHint: boolean;
            readonly openWorldHint: false;
        };
    },
): void {
    server.registerTool(
        descriptor.name,
        {
            title: descriptor.title,
            description: descriptor.description,
            inputSchema: fromJsonSchema<JsonRecord>(descriptor.inputSchema),
            outputSchema: fromJsonSchema<JsonRecord>(descriptor.outputSchema),
            annotations: descriptor.annotations,
        },
        async (argumentsValue): Promise<CallToolResult> => {
            try {
                const result = await workflow(
                    config,
                    descriptor.method,
                    argumentsValue,
                );
                return {
                    content: [
                        {
                            type: "text",
                            text: "Local workflow step completed.",
                        },
                    ],
                    structuredContent: result as unknown as JsonRecord,
                    isError: false,
                };
            } catch {
                return {
                    content: [
                        {
                            type: "text",
                            text: "Local workflow step was rejected.",
                        },
                    ],
                    isError: true,
                };
            }
        },
    );
}

function registerWorkflowTools(
    server: McpServer,
    config: RuntimeConfig,
    workflow: (
        config: RuntimeConfig,
        method: WorkflowMethod,
        params: JsonRecord,
    ) => Promise<WorkflowResult>,
): void {
    registerWorkflowTool(server, config, workflow, {
        name: MATERIALIZE_TOOL_NAME,
        method: "materialize",
        title: "Materialize a verified local HWPX fixture",
        description:
            "Copy a checksum-bound fixture ID into a create-new private operation slot. Paths are not accepted.",
        inputSchema: {
            type: "object",
            properties: {
                workspace_id: IDENTIFIER_SCHEMA,
                operation_id: IDENTIFIER_SCHEMA,
                slot: { type: "string", enum: ["source", "candidate"] },
                fixture_id: IDENTIFIER_SCHEMA,
                expected_sha256: DIGEST_SCHEMA,
            },
            required: [
                "workspace_id",
                "operation_id",
                "slot",
                "fixture_id",
                "expected_sha256",
            ],
            additionalProperties: false,
        },
        outputSchema: {
            type: "object",
            properties: {
                workspace_id: IDENTIFIER_SCHEMA,
                operation_id: IDENTIFIER_SCHEMA,
                slot: { type: "string", enum: ["source", "candidate"] },
                sha256: DIGEST_SCHEMA,
                size_bytes: SIZE_SCHEMA,
            },
            required: [
                "workspace_id",
                "operation_id",
                "slot",
                "sha256",
                "size_bytes",
            ],
            additionalProperties: false,
        },
        annotations: {
            readOnlyHint: false,
            destructiveHint: false,
            idempotentHint: false,
            openWorldHint: false,
        },
    });
    registerWorkflowTool(server, config, workflow, {
        name: DIFF_TOOL_NAME,
        method: "diff",
        title: "Compare local HWPX identities",
        description:
            "Compare source and candidate digests and sizes without returning document content.",
        inputSchema: {
            type: "object",
            properties: {
                workspace_id: IDENTIFIER_SCHEMA,
                operation_id: IDENTIFIER_SCHEMA,
            },
            required: ["workspace_id", "operation_id"],
            additionalProperties: false,
        },
        outputSchema: {
            type: "object",
            properties: {
                workspace_id: IDENTIFIER_SCHEMA,
                operation_id: IDENTIFIER_SCHEMA,
                identical: { type: "boolean" },
                source: IDENTITY_SCHEMA,
                candidate: IDENTITY_SCHEMA,
            },
            required: [
                "workspace_id",
                "operation_id",
                "identical",
                "source",
                "candidate",
            ],
            additionalProperties: false,
        },
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: false,
        },
    });
    registerWorkflowTool(server, config, workflow, {
        name: PUBLISH_TOOL_NAME,
        method: "publish",
        title: "Publish a verified local HWPX output",
        description:
            "Create a new output ID from the verified candidate. Existing outputs are never replaced.",
        inputSchema: {
            type: "object",
            properties: {
                workspace_id: IDENTIFIER_SCHEMA,
                operation_id: IDENTIFIER_SCHEMA,
                output_id: IDENTIFIER_SCHEMA,
                expected_sha256: DIGEST_SCHEMA,
            },
            required: [
                "workspace_id",
                "operation_id",
                "output_id",
                "expected_sha256",
            ],
            additionalProperties: false,
        },
        outputSchema: {
            type: "object",
            properties: {
                workspace_id: IDENTIFIER_SCHEMA,
                operation_id: IDENTIFIER_SCHEMA,
                output_id: IDENTIFIER_SCHEMA,
                sha256: DIGEST_SCHEMA,
                size_bytes: SIZE_SCHEMA,
            },
            required: [
                "workspace_id",
                "operation_id",
                "output_id",
                "sha256",
                "size_bytes",
            ],
            additionalProperties: false,
        },
        annotations: {
            readOnlyHint: false,
            destructiveHint: true,
            idempotentHint: false,
            openWorldHint: false,
        },
    });
    registerWorkflowTool(server, config, workflow, {
        name: PREPARE_COMMIT_TOOL_NAME,
        method: "prepare_git_commit",
        title: "Prepare a bound local Git commit plan",
        description:
            "Read the current local HEAD and prepare a digest-bound plan. This tool never executes Git.",
        inputSchema: {
            type: "object",
            properties: {
                workspace_id: IDENTIFIER_SCHEMA,
                output_id: IDENTIFIER_SCHEMA,
                expected_sha256: DIGEST_SCHEMA,
                message: {
                    type: "string",
                    minLength: 1,
                    maxLength: 128,
                    pattern: "^[^\\u0000-\\u001F\\u007F]+$",
                },
            },
            required: [
                "workspace_id",
                "output_id",
                "expected_sha256",
                "message",
            ],
            additionalProperties: false,
        },
        outputSchema: {
            type: "object",
            properties: {
                workspace_id: IDENTIFIER_SCHEMA,
                output_id: IDENTIFIER_SCHEMA,
                output_pathspec: {
                    type: "string",
                    pattern: "^output/[A-Za-z0-9_-]{1,64}\\.hwpx$",
                },
                expected_output_sha256: DIGEST_SCHEMA,
                expected_head: {
                    type: "string",
                    pattern: "^(?:[0-9a-f]{40}|[0-9a-f]{64})$",
                },
                message: { type: "string", minLength: 1, maxLength: 128 },
                executed: { type: "boolean", const: false },
            },
            required: [
                "workspace_id",
                "output_id",
                "output_pathspec",
                "expected_output_sha256",
                "expected_head",
                "message",
                "executed",
            ],
            additionalProperties: false,
        },
        annotations: {
            readOnlyHint: true,
            destructiveHint: false,
            idempotentHint: true,
            openWorldHint: false,
        },
    });
}

function registerApprovalTools(
    server: McpServer,
    config: RuntimeConfig,
    approval: (
        config: RuntimeConfig,
        params: JsonRecord,
    ) => Promise<GitApprovalPlanResult>,
    effect: (
        config: RuntimeConfig,
        params: JsonRecord,
    ) => Promise<GitCommitEffectResult>,
): void {
    const pendingApprovals = new Map<
        string,
        {
            readonly plan: GitApprovalPlanResult;
            readonly expiresAtUnixSeconds: number;
        }
    >();
    const nowSeconds = (): number => Math.floor(Date.now() / 1_000);
    const mintChallenge = (): string => {
        let challenge = randomBytes(32).toString("base64url");
        while (pendingApprovals.has(challenge))
            challenge = randomBytes(32).toString("base64url");
        return challenge;
    };
    const commitMessageSchema: JsonRecord = {
        type: "string",
        minLength: 1,
        maxLength: 128,
        pattern: "^[^\\u0000-\\u001F\\u007F]+$",
    };
    const gitOidSchema: JsonRecord = {
        type: "string",
        pattern: "^(?!0+$)(?:[0-9a-f]{40}|[0-9a-f]{64})$",
    };
    const headReferenceSchema: JsonRecord = {
        anyOf: [
            {
                type: "string",
                pattern:
                    "^refs/heads/(?!\\.)(?!.*\\.\\.)(?!.*@\\{)(?!.*\\.[lL][oO][cC][kK](?:/|$))[A-Za-z0-9._/-]+$",
            },
            { type: "null" },
        ],
    };
    const approvalInputSchema: JsonRecord = {
        type: "object",
        properties: {
            workspace_id: IDENTIFIER_SCHEMA,
            operation_id: IDENTIFIER_SCHEMA,
            output_id: IDENTIFIER_SCHEMA,
            expected_sha256: DIGEST_SCHEMA,
            message: commitMessageSchema,
        },
        required: [
            "workspace_id",
            "operation_id",
            "output_id",
            "expected_sha256",
            "message",
        ],
        additionalProperties: false,
    };
    server.registerTool(
        PREPARE_APPROVAL_TOOL_NAME,
        {
            title: "Prepare an approval-bound local Git commit",
            description:
                "Read the exact local Git state and return target and plan digests for trusted user confirmation. This tool never executes Git or creates a confirmation token.",
            inputSchema: fromJsonSchema<JsonRecord>(approvalInputSchema),
            outputSchema: fromJsonSchema<JsonRecord>({
                type: "object",
                properties: {
                    workspace_id: IDENTIFIER_SCHEMA,
                    operation_id: IDENTIFIER_SCHEMA,
                    output_id: IDENTIFIER_SCHEMA,
                    output_pathspec: {
                        type: "string",
                        pattern: "^output/[A-Za-z0-9_-]{1,64}\\.hwpx$",
                    },
                    expected_output_sha256: DIGEST_SCHEMA,
                    expected_head: gitOidSchema,
                    expected_head_reference: headReferenceSchema,
                    message: commitMessageSchema,
                    approval: {
                        type: "object",
                        properties: {
                            effect: { type: "string", const: "git_commit" },
                            target_sha256: DIGEST_SCHEMA,
                            plan_sha256: DIGEST_SCHEMA,
                        },
                        required: [
                            "effect",
                            "target_sha256",
                            "plan_sha256",
                        ],
                        additionalProperties: false,
                    },
                    executed: { type: "boolean", const: false },
                },
                required: [
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
                ],
                additionalProperties: false,
            }),
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
            _meta: {
                ui: { resourceUri: GIT_APPROVAL_RESOURCE_URI },
            },
        },
        async (argumentsValue): Promise<CallToolResult> => {
            try {
                const result = await approval(config, argumentsValue);
                const now = nowSeconds();
                for (const [challenge, pending] of pendingApprovals) {
                    if (pending.expiresAtUnixSeconds < now)
                        pendingApprovals.delete(challenge);
                }
                if (pendingApprovals.size >= MAX_PENDING_WIDGET_APPROVALS)
                    throw new Error("pending trusted confirmations are full");
                const challenge = mintChallenge();
                pendingApprovals.set(challenge, {
                    plan: result,
                    expiresAtUnixSeconds: now + WIDGET_APPROVAL_TTL_SECONDS,
                });
                return {
                    content: [
                        {
                            type: "text",
                            text: "Approval-bound Git plan prepared; no effect executed.",
                        },
                    ],
                    structuredContent: result as unknown as JsonRecord,
                    _meta: {
                        "hwpx-agent/git-approval-challenge": challenge,
                    },
                    isError: false,
                };
            } catch {
                return {
                    content: [
                        {
                            type: "text",
                            text: "Approval-bound Git plan was rejected.",
                        },
                    ],
                    isError: true,
                };
            }
        },
    );

    server.registerTool(
        CONFIRM_COMMIT_TOOL_NAME,
        {
            title: "Confirm and execute one local Git commit",
            description:
                "App-only action for the trusted local confirmation widget. It revalidates the displayed Git plan, internally mints a signed single-use confirmation, and executes only that exact commit.",
            inputSchema: fromJsonSchema<JsonRecord>({
                type: "object",
                properties: {
                    workspace_id: IDENTIFIER_SCHEMA,
                    operation_id: IDENTIFIER_SCHEMA,
                    output_id: IDENTIFIER_SCHEMA,
                    expected_sha256: DIGEST_SCHEMA,
                    message: commitMessageSchema,
                    expected_head: gitOidSchema,
                    expected_head_reference: headReferenceSchema,
                    target_sha256: DIGEST_SCHEMA,
                    plan_sha256: DIGEST_SCHEMA,
                    approval_challenge: {
                        type: "string",
                        minLength: 43,
                        maxLength: 43,
                        pattern: "^[A-Za-z0-9_-]{43}$",
                    },
                },
                required: [
                    "workspace_id",
                    "operation_id",
                    "output_id",
                    "expected_sha256",
                    "message",
                    "expected_head",
                    "expected_head_reference",
                    "target_sha256",
                    "plan_sha256",
                    "approval_challenge",
                ],
                additionalProperties: false,
            }),
            outputSchema: fromJsonSchema<JsonRecord>({
                type: "object",
                properties: {
                    workspace_id: IDENTIFIER_SCHEMA,
                    operation_id: IDENTIFIER_SCHEMA,
                    output_id: IDENTIFIER_SCHEMA,
                    commit_oid: gitOidSchema,
                    previous_head: gitOidSchema,
                    updated_reference: headReferenceSchema,
                    output_sha256: DIGEST_SCHEMA,
                    target_sha256: DIGEST_SCHEMA,
                    plan_sha256: DIGEST_SCHEMA,
                    approved_at_unix_seconds: {
                        type: "integer",
                        minimum: 1,
                    },
                    index_synchronized: { type: "boolean", const: true },
                    executed: { type: "boolean", const: true },
                },
                required: [
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
                ],
                additionalProperties: false,
            }),
            annotations: {
                readOnlyHint: false,
                destructiveHint: true,
                idempotentHint: false,
                openWorldHint: false,
            },
            _meta: {
                ui: { visibility: ["app"] },
            },
        },
        async (argumentsValue): Promise<CallToolResult> => {
            try {
                const { challenge, confirmed } =
                    widgetConfirmationParams(argumentsValue);
                const pending = pendingApprovals.get(challenge);
                // Consume before any asynchronous work. Failure and lost replies are non-retryable.
                pendingApprovals.delete(challenge);
                if (
                    pending === undefined ||
                    pending.expiresAtUnixSeconds < nowSeconds() ||
                    !confirmationMatchesPlan(confirmed, pending.plan)
                ) {
                    throw new Error("trusted widget confirmation was rejected");
                }
                const result = await confirmAndExecuteGitCommit(
                    config,
                    confirmed,
                    approval,
                    effect,
                );
                return {
                    content: [
                        {
                            type: "text",
                            text: "The exact confirmed local Git commit was executed.",
                        },
                    ],
                    structuredContent: result as unknown as JsonRecord,
                    isError: false,
                };
            } catch {
                return {
                    content: [
                        {
                            type: "text",
                            text: "The confirmed local Git commit was rejected.",
                        },
                    ],
                    isError: true,
                };
            }
        },
    );
}

export function createLocalCompanionServer(
    config: RuntimeConfig,
    health: (config: RuntimeConfig) => Promise<HealthResult> = callLocalHealth,
    workflow: (
        config: RuntimeConfig,
        method: WorkflowMethod,
        params: JsonRecord,
    ) => Promise<WorkflowResult> = callLocalWorkflow,
    approval: (
        config: RuntimeConfig,
        params: JsonRecord,
    ) => Promise<GitApprovalPlanResult> = callLocalApproval,
    effect: (
        config: RuntimeConfig,
        params: JsonRecord,
    ) => Promise<GitCommitEffectResult> = callLocalEffect,
): McpServer {
    const server = new McpServer({
        name: "hwpx-agent-local-companion",
        version: "0.4.0",
    });
    server.registerResource(
        "local-git-approval-v1",
        GIT_APPROVAL_RESOURCE_URI,
        {
            title: "HWPX Agent local Git approval",
            description:
                "Self-contained trusted confirmation interface for one exact local Git commit.",
            mimeType: "text/html;profile=mcp-app",
        },
        async () => ({
            contents: [
                {
                    uri: GIT_APPROVAL_RESOURCE_URI,
                    mimeType: "text/html;profile=mcp-app",
                    text: config.widgetHtml,
                    _meta: {
                        ui: {
                            csp: {
                                connectDomains: [],
                                resourceDomains: [],
                            },
                            prefersBorder: true,
                        },
                    },
                },
            ],
        }),
    );
    server.registerTool(
        TOOL_NAME,
        {
            title: "Check HWPX Agent local companion",
            description:
                "Check the bounded local HWPX Agent companion without opening a document or Hangul.",
            inputSchema: fromJsonSchema<JsonRecord>({
                type: "object",
                properties: {},
                required: [],
                additionalProperties: false,
            }),
            outputSchema: fromJsonSchema<JsonRecord>({
                type: "object",
                properties: {
                    status: { type: "string", const: "ready" },
                    target_profile: { type: "string", const: TARGET_PROFILE },
                    automation_enabled: { type: "boolean", const: false },
                    network_enabled: { type: "boolean", const: false },
                    workspace_count: {
                        type: "integer",
                        minimum: 1,
                        maximum: 8,
                    },
                    config_sha256: {
                        type: "string",
                        pattern: "^[0-9a-f]{64}$",
                    },
                },
                required: [
                    "status",
                    "target_profile",
                    "automation_enabled",
                    "network_enabled",
                    "workspace_count",
                    "config_sha256",
                ],
                additionalProperties: false,
            }),
            annotations: {
                readOnlyHint: true,
                destructiveHint: false,
                idempotentHint: true,
                openWorldHint: false,
            },
        },
        async (): Promise<CallToolResult> => {
            try {
                const result = await health(config);
                return {
                    content: [
                        { type: "text", text: "Local companion is ready." },
                    ],
                    structuredContent: result as unknown as JsonRecord,
                    isError: false,
                };
            } catch {
                return {
                    content: [
                        {
                            type: "text",
                            text: "Local companion is unavailable.",
                        },
                    ],
                    isError: true,
                };
            }
        },
    );
    registerWorkflowTools(server, config, workflow);
    registerApprovalTools(server, config, approval, effect);
    return server;
}

export async function main(
    argumentsValue: readonly string[] = process.argv.slice(2),
): Promise<void> {
    const config = await loadRuntimeConfig(argumentsValue);
    const handle = serveStdio(() => createLocalCompanionServer(config), {
        legacy: "serve",
        onerror: () => {
            process.stderr.write("local companion transport error\n");
        },
    });
    const close = (): void => {
        void handle.close().finally(() => process.exit(0));
    };
    process.once("SIGINT", close);
    process.once("SIGTERM", close);
}

const invokedPath = process.argv[1];
if (
    invokedPath !== undefined &&
    import.meta.url === pathToFileURL(invokedPath).href
) {
    void main().catch(() => {
        process.stderr.write("local companion startup failed\n");
        process.exitCode = 1;
    });
}
