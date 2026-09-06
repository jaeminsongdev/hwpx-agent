import { spawn } from "node:child_process";
import { randomBytes } from "node:crypto";
import { lstat, realpath } from "node:fs/promises";
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
export const MATERIALIZE_TOOL_NAME = "local_companion_materialize";
export const DIFF_TOOL_NAME = "local_companion_diff";
export const PUBLISH_TOOL_NAME = "local_companion_publish";
export const PREPARE_COMMIT_TOOL_NAME = "local_companion_prepare_git_commit";
export const TARGET_PROFILE = "hancom-2020-x86-11.0.0.9136";
const SESSION_ENV = "HWPX_AGENT_LOCAL_SESSION_TOKEN";
const REQUEST_ID = "mcp-health";
const MAX_STDOUT_BYTES = 16_384;
const MAX_STDERR_BYTES = 4_096;
const MAX_CONFIG_BYTES = 65_536;
const DAEMON_TIMEOUT_MS = 10_000;
const MAX_FILE_BYTES = 1_073_741_824;
const IDENTIFIER_PATTERN = "^[A-Za-z0-9_-]{1,64}$";
const DIGEST_PATTERN = "^[0-9a-f]{64}$";

type JsonRecord = Record<string, JSONValue>;

export interface RuntimeConfig {
    readonly daemonPath: string;
    readonly configPath: string;
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
} {
    if (
        argumentsValue.length !== 4 ||
        argumentsValue[0] !== "--daemon" ||
        argumentsValue[2] !== "--config"
    ) {
        throw new Error("invalid local companion arguments");
    }
    const daemonPath = argumentsValue[1];
    const configPath = argumentsValue[3];
    if (
        daemonPath === undefined ||
        configPath === undefined ||
        !isAbsolute(daemonPath) ||
        !isAbsolute(configPath) ||
        daemonPath.length > 1_024 ||
        configPath.length > 1_024
    ) {
        throw new Error("invalid local companion paths");
    }
    return { daemonPath, configPath };
}

export async function loadRuntimeConfig(
    argumentsValue: readonly string[],
): Promise<RuntimeConfig> {
    const parsed = parseRuntimeArguments(argumentsValue);
    const [daemonMetadata, configMetadata] = await Promise.all([
        lstat(parsed.daemonPath),
        lstat(parsed.configPath),
    ]);
    if (
        !daemonMetadata.isFile() ||
        daemonMetadata.isSymbolicLink() ||
        !configMetadata.isFile() ||
        configMetadata.isSymbolicLink() ||
        configMetadata.size < 1 ||
        configMetadata.size > MAX_CONFIG_BYTES ||
        (process.platform === "win32" &&
            extname(parsed.daemonPath).toLowerCase() !== ".exe")
    ) {
        throw new Error("invalid local companion files");
    }
    const [daemonPath, configPath] = await Promise.all([
        realpath(parsed.daemonPath),
        realpath(parsed.configPath),
    ]);
    return { daemonPath, configPath };
}

export function childEnvironment(token: string): NodeJS.ProcessEnv {
    if (!/^[A-Za-z0-9_-]{43}$/.test(token)) {
        throw new Error("invalid local companion token");
    }
    const environment: NodeJS.ProcessEnv = { [SESSION_ENV]: token };
    for (const name of ["SystemRoot", "WINDIR"] as const) {
        const value = process.env[name];
        if (value !== undefined && value.length > 0 && value.length <= 1_024) {
            environment[name] = value;
        }
    }
    return environment;
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
): Promise<BoundedOutput & SpawnOutcome> {
    const child = spawn(config.daemonPath, ["--config", config.configPath], {
        cwd: dirname(config.configPath),
        env: childEnvironment(token),
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

export function createLocalCompanionServer(
    config: RuntimeConfig,
    health: (config: RuntimeConfig) => Promise<HealthResult> = callLocalHealth,
    workflow: (
        config: RuntimeConfig,
        method: WorkflowMethod,
        params: JsonRecord,
    ) => Promise<WorkflowResult> = callLocalWorkflow,
): McpServer {
    const server = new McpServer({
        name: "hwpx-agent-local-companion",
        version: "0.2.0",
    });
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
