import { createHash } from "node:crypto";
import { readFile, stat } from "node:fs/promises";
import type { IncomingMessage, ServerResponse } from "node:http";
import { createServer as createHttpsServer } from "node:https";
import { isAbsolute, join, resolve } from "node:path";
import { spawn } from "node:child_process";
import type { ChildProcessWithoutNullStreams } from "node:child_process";
import { pathToFileURL } from "node:url";

import {
    localhostHostValidation,
    localhostOriginValidation,
    toNodeHandler,
} from "@modelcontextprotocol/node";
import {
    type AuthInfo,
    type CallToolResult,
    type JSONValue,
    McpServer,
    createMcpHandler,
    fromJsonSchema,
} from "@modelcontextprotocol/server";
import { generate } from "selfsigned";

const RESOURCE = "https://mcp.hwpx-agent.example";
const RESOURCE_METADATA = `${RESOURCE}/.well-known/oauth-protected-resource`;
const MAX_BODY_BYTES = 300_000;
const MAX_DRIVER_STDOUT_BYTES = 1_048_576;
const MAX_DRIVER_STDERR_BYTES = 4_096;
const DRIVER_TIMEOUT_MS = 15_000;
const MAX_CONCURRENT_DRIVER_REQUESTS = 4;
const DEFAULT_LIFETIME_SECONDS = 300;
const PLAN_REVIEW_HTML = join(
    "web",
    "plugin-widget",
    "dist",
    "plan-review-widget-v1.html",
);
const CLOCK_ENV = "HWPX_AGENT_PLAN_REVIEW_CLOCK_UNIX_SECONDS";
const REQUIRED_DRIVER_ENVIRONMENT = [
    "HWPX_AGENT_PLAN_REVIEW_HMAC_KEY_B64",
    "HWPX_AGENT_PLAN_REVIEW_TENANT_ID",
    "HWPX_AGENT_PLAN_REVIEW_PROJECT_ID",
    "HWPX_AGENT_PLAN_REVIEW_SUBJECT",
    "HWPX_AGENT_PLAN_REVIEW_PG_PORT",
    "HWPX_AGENT_PLAN_REVIEW_PG_DATABASE",
    "HWPX_AGENT_PLAN_REVIEW_SOURCE_PG_USER",
    "HWPX_AGENT_PLAN_REVIEW_SOURCE_PG_PASSWORD",
    "HWPX_AGENT_PLAN_REVIEW_PLAN_PG_USER",
    "HWPX_AGENT_PLAN_REVIEW_PLAN_PG_PASSWORD",
    "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PG_USER",
    "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PG_PASSWORD",
    "HWPX_AGENT_PLAN_REVIEW_PLAN_ACTIVE_KEY_REF",
    "HWPX_AGENT_PLAN_REVIEW_PLAN_ACTIVE_KEY_B64",
    "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_ACTIVE_KEY_REF",
    "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_ACTIVE_KEY_B64",
] as const;
const OPTIONAL_DRIVER_ENVIRONMENT = [
    "HWPX_AGENT_PLAN_REVIEW_PLAN_PREVIOUS_KEY_REF",
    "HWPX_AGENT_PLAN_REVIEW_PLAN_PREVIOUS_KEY_B64",
    "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PREVIOUS_KEY_REF",
    "HWPX_AGENT_PLAN_REVIEW_EVIDENCE_PREVIOUS_KEY_B64",
] as const;

type JsonRecord = Record<string, JSONValue>;

interface PlanReviewResource {
    readonly contents: readonly [
        {
            readonly uri: string;
            readonly mimeType: string;
            readonly text: string;
            readonly _meta: JsonRecord;
        },
    ];
}

interface PlanReviewDescriptor {
    readonly name: string;
    readonly title: string;
    readonly description: string;
    readonly annotations: {
        readonly readOnlyHint: boolean;
        readonly destructiveHint: boolean;
        readonly idempotentHint: boolean;
        readonly openWorldHint: boolean;
    };
    readonly inputSchema: JsonRecord;
    readonly outputSchema: JsonRecord;
    readonly _meta: JsonRecord;
}

interface PlanReviewModule {
    readonly PLAN_REVIEW_RENDER_TOOL_DESCRIPTOR: PlanReviewDescriptor;
    readonly PLAN_REVIEW_RESOURCE_URI: string;
    readonly createPlanReviewResource: (html: string) => PlanReviewResource;
    readonly createPlanReviewToolResult: (value: unknown) => {
        readonly structuredContent: JsonRecord;
        readonly _meta: JsonRecord;
    };
}

interface LoadedPlanReview {
    readonly resource: PlanReviewResource;
    readonly descriptor: PlanReviewDescriptor;
    readonly createToolResult: PlanReviewModule["createPlanReviewToolResult"];
    readonly sha256: string;
    readonly bytes: number;
}

interface RuntimeConfig {
    readonly repoRoot: string;
    readonly driverPath: string;
    readonly lifetimeSeconds: number;
    readonly fixedClockUnixSeconds?: number;
    readonly driverEnvironment: Readonly<Record<string, string>>;
}

interface DriverRequest {
    readonly mode: "ready" | "auth" | "plan_review";
    readonly now_unix_seconds: number;
    readonly authorization_header?: string;
    readonly tool_name?: string;
    readonly arguments?: JsonRecord;
}

interface PendingDriverRequest {
    readonly resolve: (value: unknown) => void;
    readonly reject: (error: Error) => void;
    readonly timer: NodeJS.Timeout;
}

interface DriverEnvelope {
    readonly driver_request_id: number;
    readonly ok: boolean;
    readonly result?: unknown;
}

export function parseBearerHeader(
    value: string | string[] | undefined,
): string | undefined {
    if (typeof value !== "string" || value.length < 8 || value.length > 8_199) {
        return undefined;
    }
    return /^Bearer ([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$/.exec(
        value,
    )?.[1];
}

export function boundedLifetime(value: string | undefined): number {
    if (value === undefined) return DEFAULT_LIFETIME_SECONDS;
    const parsed = Number(value);
    if (!Number.isSafeInteger(parsed) || parsed < 30 || parsed > 900) {
        throw new Error("invalid staging lifetime");
    }
    return parsed;
}

export function boundedFixedClock(
    value: string | undefined,
): number | undefined {
    if (value === undefined) return undefined;
    const parsed = Number(value);
    if (
        !Number.isSafeInteger(parsed) ||
        parsed < 1_700_000_000 ||
        parsed > 4_000_000_000
    ) {
        throw new Error("invalid staging clock");
    }
    return parsed;
}

export function validateOptionalKeyPairs(
    environment: Readonly<Record<string, string>>,
): void {
    for (const prefix of ["PLAN", "EVIDENCE"] as const) {
        const reference =
            environment[`HWPX_AGENT_PLAN_REVIEW_${prefix}_PREVIOUS_KEY_REF`];
        const key =
            environment[`HWPX_AGENT_PLAN_REVIEW_${prefix}_PREVIOUS_KEY_B64`];
        if ((reference === undefined) !== (key === undefined)) {
            throw new Error("incomplete previous key configuration");
        }
    }
}

async function loadConfig(): Promise<RuntimeConfig> {
    const repoRootValue = process.env.HWPX_AGENT_ROOT;
    const driverPathValue = process.env.HWPX_AGENT_PLAN_REVIEW_DRIVER;
    if (
        repoRootValue === undefined ||
        driverPathValue === undefined ||
        !isAbsolute(repoRootValue) ||
        !isAbsolute(driverPathValue)
    ) {
        throw new Error("missing or invalid staging configuration");
    }
    const driverEnvironment: Record<string, string> = {};
    for (const name of REQUIRED_DRIVER_ENVIRONMENT) {
        const value = process.env[name];
        if (value === undefined || value.length === 0 || value.length > 2_048) {
            throw new Error("missing or invalid driver configuration");
        }
        driverEnvironment[name] = value;
    }
    for (const name of OPTIONAL_DRIVER_ENVIRONMENT) {
        const value = process.env[name];
        if (value !== undefined) {
            if (value.length === 0 || value.length > 2_048) {
                throw new Error("invalid optional driver configuration");
            }
            driverEnvironment[name] = value;
        }
    }
    validateOptionalKeyPairs(driverEnvironment);
    const repoRoot = resolve(repoRootValue);
    const driverPath = resolve(driverPathValue);
    if (!(await stat(driverPath)).isFile()) {
        throw new Error("plan review driver is not a file");
    }
    const fixedClockUnixSeconds = boundedFixedClock(process.env[CLOCK_ENV]);
    return {
        repoRoot,
        driverPath,
        driverEnvironment,
        lifetimeSeconds: boundedLifetime(
            process.env.HWPX_AGENT_PLAN_REVIEW_LIFETIME_SECONDS,
        ),
        ...(fixedClockUnixSeconds === undefined
            ? {}
            : { fixedClockUnixSeconds }),
    };
}

async function loadPlanReviewResource(
    repoRoot: string,
): Promise<LoadedPlanReview> {
    const modulePath = join(
        repoRoot,
        "web",
        "plugin-widget",
        "dist",
        "plan-review-resource.js",
    );
    const candidate = (await import(pathToFileURL(modulePath).href)) as unknown;
    if (!isPlanReviewModule(candidate)) {
        throw new Error("plan review contract module mismatch");
    }
    const html = await readFile(join(repoRoot, PLAN_REVIEW_HTML), "utf8");
    const bytes = Buffer.byteLength(html, "utf8");
    return {
        resource: candidate.createPlanReviewResource(html),
        descriptor: candidate.PLAN_REVIEW_RENDER_TOOL_DESCRIPTOR,
        createToolResult: candidate.createPlanReviewToolResult,
        sha256: createHash("sha256").update(html, "utf8").digest("hex"),
        bytes,
    };
}

function createPlanReviewMcpServer(
    loaded: LoadedPlanReview,
    driver: PlanReviewDriver,
    authInfo: AuthInfo | undefined,
    now: () => number,
): McpServer {
    if (
        authInfo === undefined ||
        authInfo.resource?.origin !== RESOURCE ||
        authInfo.resource.pathname !== "/"
    ) {
        throw new Error("validated authentication context is missing");
    }
    const resource = loaded.resource;
    const server = new McpServer({
        name: "hwpx-agent-plan-review",
        version: "0.1.0",
    });
    server.registerResource(
        "plan-review-v1",
        resource.contents[0].uri,
        {
            title: "HWPX Agent plan review",
            description: "Self-contained read-only plan review interface.",
            mimeType: resource.contents[0].mimeType,
        },
        async () => ({
            contents: [
                {
                    uri: resource.contents[0].uri,
                    mimeType: resource.contents[0].mimeType,
                    text: resource.contents[0].text,
                    _meta: resource.contents[0]._meta as unknown as JsonRecord,
                },
            ],
        }),
    );
    const descriptor = loaded.descriptor;
    server.registerTool(
        descriptor.name,
        {
            title: descriptor.title,
            description: descriptor.description,
            inputSchema: fromJsonSchema<JsonRecord>(
                descriptor.inputSchema as unknown as JsonRecord,
            ),
            outputSchema: fromJsonSchema<JsonRecord>(
                descriptor.outputSchema as unknown as JsonRecord,
            ),
            annotations: descriptor.annotations,
            _meta: descriptor._meta as unknown as JsonRecord,
        },
        async (argumentsValue): Promise<CallToolResult> => {
            const snapshot = await driver.call({
                mode: "plan_review",
                now_unix_seconds: now(),
                authorization_header: `Bearer ${authInfo.token}`,
                tool_name: descriptor.name,
                arguments: argumentsValue,
            });
            const result = loaded.createToolResult(snapshot);
            return {
                structuredContent:
                    result.structuredContent as unknown as JsonRecord,
                content: [{ type: "text", text: "Plan review is ready." }],
                _meta: { ...result._meta },
                isError: false,
            };
        },
    );
    return server;
}

async function authenticate(
    driver: PlanReviewDriver,
    authorizationHeader: string,
    now: () => number,
): Promise<boolean> {
    try {
        const result = await driver.call({
            mode: "auth",
            now_unix_seconds: now(),
            authorization_header: authorizationHeader,
        });
        return isRecord(result) && result.authenticated === true;
    } catch {
        return false;
    }
}

class PlanReviewDriver {
    readonly #child: ChildProcessWithoutNullStreams;
    readonly #pending = new Map<number, PendingDriverRequest>();
    #nextRequestId = 1;
    #stdoutBuffer = Buffer.alloc(0);
    #stderrBytes = 0;
    #closed = false;

    private constructor(config: RuntimeConfig) {
        this.#child = spawn(config.driverPath, [], {
            env: {
                ...config.driverEnvironment,
                RUST_BACKTRACE: "0",
                SystemRoot: process.env.SystemRoot,
                WINDIR: process.env.WINDIR,
            },
            shell: false,
            windowsHide: true,
            stdio: ["pipe", "pipe", "pipe"],
        });
        this.#child.stdout.on("data", (chunk: Buffer) =>
            this.#handleStdout(chunk),
        );
        this.#child.stderr.on("data", (chunk: Buffer) =>
            this.#handleStderr(chunk),
        );
        this.#child.on("error", () =>
            this.#failAll("plan review driver launch failed"),
        );
        this.#child.on("close", () =>
            this.#failAll("plan review driver closed"),
        );
        this.#child.stdin.on("error", () =>
            this.#failAll("plan review driver input failed"),
        );
    }

    static async start(config: RuntimeConfig): Promise<PlanReviewDriver> {
        const driver = new PlanReviewDriver(config);
        await new Promise<void>((resolvePromise, rejectPromise) => {
            const onSpawn = (): void => {
                driver.#child.off("error", onError);
                resolvePromise();
            };
            const onError = (): void => {
                driver.#child.off("spawn", onSpawn);
                rejectPromise(new Error("plan review driver launch failed"));
            };
            driver.#child.once("spawn", onSpawn);
            driver.#child.once("error", onError);
        });
        return driver;
    }

    async call(request: DriverRequest): Promise<unknown> {
        if (
            this.#closed ||
            this.#pending.size >= MAX_CONCURRENT_DRIVER_REQUESTS
        ) {
            throw new Error("plan review driver is unavailable");
        }
        const requestId = this.#nextRequestId;
        if (
            !Number.isSafeInteger(requestId) ||
            requestId >= Number.MAX_SAFE_INTEGER
        ) {
            this.#child.kill();
            this.#failAll("plan review driver request identifier exhausted");
            throw new Error("plan review driver request identifier exhausted");
        }
        this.#nextRequestId = requestId + 1;
        const line = Buffer.from(
            `${JSON.stringify({ ...request, driver_request_id: requestId })}\n`,
            "utf8",
        );
        if (line.length > MAX_BODY_BYTES)
            throw new Error("plan review driver input exceeded limit");
        return new Promise<unknown>((resolvePromise, rejectPromise) => {
            const timer = setTimeout(() => {
                this.#child.kill();
                this.#failAll("plan review driver timed out");
            }, DRIVER_TIMEOUT_MS);
            this.#pending.set(requestId, {
                resolve: resolvePromise,
                reject: rejectPromise,
                timer,
            });
            this.#child.stdin.write(line, (error) => {
                if (error !== null && error !== undefined) {
                    this.#child.kill();
                    this.#failAll("plan review driver input failed");
                }
            });
        });
    }

    async close(): Promise<void> {
        if (this.#child.exitCode !== null || this.#child.signalCode !== null) {
            if (this.#child.exitCode !== 0)
                throw new Error("plan review driver did not exit cleanly");
            return;
        }
        this.#closed = true;
        this.#child.stdin.end();
        await new Promise<void>((resolvePromise) => {
            const timer = setTimeout(() => this.#child.kill(), 1_000);
            this.#child.once("close", () => {
                clearTimeout(timer);
                resolvePromise();
            });
        });
        if (this.#child.exitCode !== 0)
            throw new Error("plan review driver did not exit cleanly");
    }

    #handleStdout(chunk: Buffer): void {
        this.#stdoutBuffer = Buffer.concat([this.#stdoutBuffer, chunk]);
        if (this.#stdoutBuffer.length > MAX_DRIVER_STDOUT_BYTES) {
            this.#child.kill();
            this.#failAll("plan review driver response exceeded limit");
            return;
        }
        while (true) {
            const newline = this.#stdoutBuffer.indexOf(0x0a);
            if (newline < 0) return;
            const line = this.#stdoutBuffer.subarray(0, newline);
            this.#stdoutBuffer = this.#stdoutBuffer.subarray(newline + 1);
            let value: unknown;
            try {
                value = JSON.parse(line.toString("utf8")) as unknown;
            } catch {
                this.#child.kill();
                this.#failAll("plan review driver returned malformed response");
                return;
            }
            if (!isDriverEnvelope(value)) {
                this.#child.kill();
                this.#failAll("plan review driver response shape mismatch");
                return;
            }
            const pending = this.#pending.get(value.driver_request_id);
            if (pending === undefined) {
                this.#child.kill();
                this.#failAll(
                    "plan review driver response correlation mismatch",
                );
                return;
            }
            this.#pending.delete(value.driver_request_id);
            clearTimeout(pending.timer);
            if (!value.ok || value.result === undefined) {
                pending.reject(
                    new Error("plan review driver rejected request"),
                );
            } else {
                pending.resolve(value.result);
            }
        }
    }

    #handleStderr(chunk: Buffer): void {
        this.#stderrBytes += chunk.length;
        if (this.#stderrBytes > MAX_DRIVER_STDERR_BYTES) {
            this.#child.kill();
            this.#failAll("plan review driver diagnostics exceeded limit");
        }
    }

    #failAll(message: string): void {
        this.#closed = true;
        for (const pending of this.#pending.values()) {
            clearTimeout(pending.timer);
            pending.reject(new Error(message));
        }
        this.#pending.clear();
    }
}

function applySecurityHeaders(response: ServerResponse): void {
    response.setHeader("Cache-Control", "no-store");
    response.setHeader("Content-Security-Policy", "default-src 'none'");
    response.setHeader("Referrer-Policy", "no-referrer");
    response.setHeader("X-Content-Type-Options", "nosniff");
}

function reject(
    response: ServerResponse,
    status: number,
    body: string,
    headers: Record<string, string> = {},
): void {
    applySecurityHeaders(response);
    response.writeHead(status, {
        "Content-Type": "application/json; charset=utf-8",
        ...headers,
    });
    response.end(JSON.stringify({ error: body }));
}

async function readBoundedJson(request: IncomingMessage): Promise<unknown> {
    const chunks: Buffer[] = [];
    let total = 0;
    for await (const value of request) {
        const chunk = Buffer.isBuffer(value)
            ? value
            : Buffer.from(value as Uint8Array);
        total += chunk.length;
        if (total > MAX_BODY_BYTES) throw new BodyTooLargeError();
        chunks.push(chunk);
    }
    if (total === 0) throw new MalformedBodyError();
    try {
        return JSON.parse(Buffer.concat(chunks).toString("utf8")) as unknown;
    } catch {
        throw new MalformedBodyError();
    }
}

class BodyTooLargeError extends Error {}
class MalformedBodyError extends Error {}

async function serve(): Promise<void> {
    const config = await loadConfig();
    const loaded = await loadPlanReviewResource(config.repoRoot);
    const certificate = await generate(
        [{ name: "commonName", value: "localhost" }],
        {
            algorithm: "sha256",
            keyType: "ec",
            curve: "P-256",
            notBeforeDate: new Date(Date.now() - 60_000),
            notAfterDate: new Date(
                Date.now() + (config.lifetimeSeconds + 300) * 1_000,
            ),
            extensions: [
                { name: "basicConstraints", cA: false, critical: true },
                { name: "keyUsage", digitalSignature: true, critical: true },
                { name: "extKeyUsage", serverAuth: true },
                {
                    name: "subjectAltName",
                    altNames: [
                        { type: 2, value: "localhost" },
                        { type: 7, ip: "127.0.0.1" },
                    ],
                },
            ],
        },
    );
    const privateKey = Buffer.from(certificate.private, "utf8");
    const certificatePem = certificate.cert;
    certificate.private = "";
    certificate.public = "";
    const now = (): number =>
        config.fixedClockUnixSeconds ?? Math.floor(Date.now() / 1_000);
    const driver = await PlanReviewDriver.start(config);
    const ready = await driver.call({ mode: "ready", now_unix_seconds: now() });
    if (!isRecord(ready) || ready.ready !== true) {
        await driver.close();
        throw new Error("plan review driver readiness mismatch");
    }
    const handler = createMcpHandler(
        ({ authInfo }) =>
            createPlanReviewMcpServer(loaded, driver, authInfo, now),
        { responseMode: "json", legacy: "stateless", onerror: () => undefined },
    );
    const nodeHandler = toNodeHandler(handler, { onerror: () => undefined });
    const validateHost = localhostHostValidation();
    const validateOrigin = localhostOriginValidation();
    const server = createHttpsServer(
        {
            key: privateKey,
            cert: certificatePem,
            maxHeaderSize: 16_384,
            requestTimeout: 30_000,
            headersTimeout: 10_000,
            keepAliveTimeout: 5_000,
        },
        (request, response) => {
            void (async () => {
                applySecurityHeaders(response);
                if (
                    !validateHost(request, response) ||
                    !validateOrigin(request, response)
                )
                    return;
                if (request.url !== "/mcp") {
                    reject(response, 404, "not_found");
                    return;
                }
                if (!["POST", "GET", "DELETE"].includes(request.method ?? "")) {
                    reject(response, 405, "method_not_allowed", {
                        Allow: "POST, GET, DELETE",
                    });
                    return;
                }
                const token = parseBearerHeader(request.headers.authorization);
                if (
                    token === undefined ||
                    !(await authenticate(driver, `Bearer ${token}`, now))
                ) {
                    reject(response, 401, "unauthorized", {
                        "WWW-Authenticate": `Bearer resource_metadata="${RESOURCE_METADATA}"`,
                    });
                    return;
                }
                const authenticatedRequest = request as IncomingMessage & {
                    auth?: AuthInfo;
                };
                authenticatedRequest.auth = {
                    token,
                    clientId: "p16-plan-review-staging",
                    scopes: ["project.read"],
                    resource: new URL(RESOURCE),
                };
                if (request.method === "POST") {
                    try {
                        const body = await readBoundedJson(request);
                        await nodeHandler(
                            authenticatedRequest as Parameters<
                                typeof nodeHandler
                            >[0],
                            response,
                            body,
                        );
                    } catch (error) {
                        reject(
                            response,
                            error instanceof BodyTooLargeError ? 413 : 400,
                            error instanceof BodyTooLargeError
                                ? "request_too_large"
                                : "malformed_request",
                        );
                    }
                } else {
                    await nodeHandler(
                        authenticatedRequest as Parameters<
                            typeof nodeHandler
                        >[0],
                        response,
                    );
                }
            })().catch(() => {
                if (!response.headersSent)
                    reject(response, 500, "internal_error");
                else response.destroy();
            });
        },
    );
    privateKey.fill(0);
    server.maxConnections = 32;
    server.on("clientError", (_error, socket) => socket.destroy());
    await new Promise<void>((resolvePromise, rejectPromise) => {
        server.once("error", rejectPromise);
        server.listen(0, "127.0.0.1", resolvePromise);
    });
    const address = server.address();
    if (address === null || typeof address === "string") {
        throw new Error("plan review listener did not expose a TCP port");
    }
    process.stdout.write(
        `${JSON.stringify({
            state: "ready",
            url: `https://127.0.0.1:${address.port}/mcp`,
            certificate_pem_base64: Buffer.from(
                certificatePem,
                "utf8",
            ).toString("base64"),
            tool_count: 1,
            resource_count: 1,
            resource_sha256: loaded.sha256,
            resource_bytes: loaded.bytes,
            protocol_eras: ["2026-07-28", "2025-stateless"],
            driver_lifecycle: "persistent_per_server_run",
            clock_mode:
                config.fixedClockUnixSeconds === undefined
                    ? "system"
                    : "server_fixture",
        })}\n`,
    );
    let lifetimeTimer: NodeJS.Timeout | undefined;
    let shuttingDown = false;
    const shutdown = async (): Promise<void> => {
        if (shuttingDown) return;
        shuttingDown = true;
        clearTimeout(lifetimeTimer);
        await handler.close();
        await new Promise<void>((resolvePromise) =>
            server.close(() => resolvePromise()),
        );
        await driver.close();
    };
    lifetimeTimer = setTimeout(
        () => void shutdown(),
        config.lifetimeSeconds * 1_000,
    );
    const requestShutdown = (): void => {
        void shutdown().catch(() => {
            process.exitCode = 1;
        });
    };
    process.stdin.resume();
    process.stdin.once("end", requestShutdown);
    for (const signal of ["SIGINT", "SIGTERM"] as const)
        process.once(signal, requestShutdown);
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isDriverEnvelope(value: unknown): value is DriverEnvelope {
    return (
        isRecord(value) &&
        typeof value.driver_request_id === "number" &&
        Number.isSafeInteger(value.driver_request_id) &&
        value.driver_request_id > 0 &&
        typeof value.ok === "boolean"
    );
}

function isPlanReviewModule(value: unknown): value is PlanReviewModule {
    if (!isRecord(value)) return false;
    const descriptor = value.PLAN_REVIEW_RENDER_TOOL_DESCRIPTOR;
    if (!isRecord(descriptor) || !isRecord(descriptor.annotations))
        return false;
    return (
        value.PLAN_REVIEW_RESOURCE_URI ===
            "ui://hwpx-agent/plan-review/v1.html" &&
        typeof value.createPlanReviewResource === "function" &&
        typeof value.createPlanReviewToolResult === "function" &&
        descriptor.name === "render_plan_review_widget" &&
        typeof descriptor.title === "string" &&
        typeof descriptor.description === "string" &&
        isRecord(descriptor.inputSchema) &&
        isRecord(descriptor.outputSchema) &&
        isRecord(descriptor._meta) &&
        descriptor.annotations.readOnlyHint === true &&
        descriptor.annotations.destructiveHint === false &&
        descriptor.annotations.idempotentHint === true &&
        descriptor.annotations.openWorldHint === false
    );
}

const invokedPath = process.argv[1];
if (
    invokedPath !== undefined &&
    import.meta.url === pathToFileURL(resolve(invokedPath)).href
) {
    serve().catch(() => {
        process.stderr.write("plan-review-staging: startup failed closed\n");
        process.exitCode = 1;
    });
}
