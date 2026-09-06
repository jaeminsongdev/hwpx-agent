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
export const TARGET_PROFILE = "hancom-2020-x86-11.0.0.9136";
const SESSION_ENV = "HWPX_AGENT_LOCAL_SESSION_TOKEN";
const REQUEST_ID = "mcp-health";
const MAX_STDOUT_BYTES = 16_384;
const MAX_STDERR_BYTES = 4_096;
const MAX_CONFIG_BYTES = 65_536;
const DAEMON_TIMEOUT_MS = 10_000;

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

export function createLocalCompanionServer(
    config: RuntimeConfig,
    health: (config: RuntimeConfig) => Promise<HealthResult> = callLocalHealth,
): McpServer {
    const server = new McpServer({
        name: "hwpx-agent-local-companion",
        version: "0.1.0",
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
