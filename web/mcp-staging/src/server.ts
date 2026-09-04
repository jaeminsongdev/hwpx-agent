import { createHash } from "node:crypto";
import { readFile, stat } from "node:fs/promises";
import { createServer as createHttpsServer } from "node:https";
import type { IncomingMessage, ServerResponse } from "node:http";
import { isAbsolute, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { spawn } from "node:child_process";
import type { ChildProcessWithoutNullStreams } from "node:child_process";

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
const CATALOG_SHA256 =
    "94e6d24563bff94ca05283a9434887b2b2622c61789ce42fb6a8cdd1568f7001";
const EXPECTED_TOOL_COUNT = 18;
const MAX_BODY_BYTES = 300_000;
const MAX_DRIVER_STDOUT_BYTES = 1_048_576;
const MAX_DRIVER_STDERR_BYTES = 4_096;
const DRIVER_TIMEOUT_MS = 15_000;
const MAX_CONCURRENT_DRIVERS = 4;
const DEFAULT_LIFETIME_SECONDS = 300;

const ALL_SCOPES = [
    "artifact.read",
    "artifact.write",
    "job.cancel",
    "job.submit",
    "mirror.sync",
    "project.read",
    "project.write",
    "retention.manage",
] as const;

type JsonRecord = Record<string, JSONValue>;

interface ToolDescriptor {
    name: string;
    description: string;
    inputSchema: JsonRecord;
    outputSchema: JsonRecord;
    annotations: {
        readOnlyHint: boolean;
        destructiveHint: boolean;
        idempotentHint: boolean;
        openWorldHint: boolean;
    };
    _meta: JsonRecord;
}

interface PublicCatalog {
    schema_version: string;
    descriptor_count: number;
    tools: ToolDescriptor[];
}

interface RuntimeConfig {
    repoRoot: string;
    driverPath: string;
    hmacSecret: string;
    lifetimeSeconds: number;
}

interface DriverRequest {
    mode: "auth" | "tool";
    authorization_header: string;
    now_unix_seconds: number;
    tool_name?: string;
    arguments?: JsonRecord;
}

interface PendingDriverRequest {
    resolve: (value: unknown) => void;
    reject: (error: Error) => void;
    timer: NodeJS.Timeout;
}

interface DriverEnvelope {
    driver_request_id: number;
    ok: boolean;
    result?: unknown;
}

export function parseBearerHeader(
    value: string | string[] | undefined,
): string | undefined {
    if (typeof value !== "string" || value.length < 8 || value.length > 8_199) {
        return undefined;
    }
    const match =
        /^Bearer ([A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$/.exec(value);
    return match?.[1];
}

export function boundedLifetime(value: string | undefined): number {
    if (value === undefined) {
        return DEFAULT_LIFETIME_SECONDS;
    }
    const parsed = Number(value);
    if (!Number.isSafeInteger(parsed) || parsed < 30 || parsed > 900) {
        throw new Error("invalid staging lifetime");
    }
    return parsed;
}

export function validateCatalog(value: unknown): PublicCatalog {
    if (!isRecord(value)) {
        throw new Error("catalog is not an object");
    }
    const tools = value.tools;
    if (
        value.schema_version !== "hwpx-agent.mcp-public-tools/v1" ||
        value.descriptor_count !== EXPECTED_TOOL_COUNT ||
        !Array.isArray(tools) ||
        tools.length !== EXPECTED_TOOL_COUNT
    ) {
        throw new Error("catalog header mismatch");
    }
    const names = new Set<string>();
    const descriptors: ToolDescriptor[] = [];
    for (const candidate of tools) {
        if (!isToolDescriptor(candidate) || names.has(candidate.name)) {
            throw new Error("catalog tool mismatch");
        }
        names.add(candidate.name);
        descriptors.push(candidate);
    }
    return {
        schema_version: value.schema_version,
        descriptor_count: value.descriptor_count,
        tools: descriptors,
    };
}

async function loadConfig(): Promise<RuntimeConfig> {
    const repoRootValue = process.env.HWPX_AGENT_ROOT;
    const driverPathValue = process.env.HWPX_AGENT_STAGING_DRIVER;
    const hmacSecret = process.env.HWPX_AGENT_STAGING_HMAC_KEY_B64;
    if (
        repoRootValue === undefined ||
        driverPathValue === undefined ||
        hmacSecret === undefined ||
        !isAbsolute(repoRootValue) ||
        !isAbsolute(driverPathValue) ||
        !/^[A-Za-z0-9_-]{43}$/.test(hmacSecret)
    ) {
        throw new Error("missing or invalid staging configuration");
    }
    const repoRoot = resolve(repoRootValue);
    const driverPath = resolve(driverPathValue);
    const driverMetadata = await stat(driverPath);
    if (!driverMetadata.isFile()) {
        throw new Error("staging driver is not a file");
    }
    return {
        repoRoot,
        driverPath,
        hmacSecret,
        lifetimeSeconds: boundedLifetime(
            process.env.HWPX_AGENT_STAGING_LIFETIME_SECONDS,
        ),
    };
}

async function loadCatalog(repoRoot: string): Promise<PublicCatalog> {
    const catalogPath = join(
        repoRoot,
        "protocol",
        "mcp",
        "p15-public-tools-v1.json",
    );
    const bytes = await readFile(catalogPath);
    const digest = createHash("sha256").update(bytes).digest("hex");
    if (digest !== CATALOG_SHA256) {
        throw new Error("catalog digest mismatch");
    }
    return validateCatalog(JSON.parse(bytes.toString("utf8")) as unknown);
}

function createMcpServer(
    catalog: PublicCatalog,
    driver: StagingDriver,
    authInfo: AuthInfo | undefined,
): McpServer {
    if (
        authInfo === undefined ||
        authInfo.resource?.origin !== RESOURCE ||
        authInfo.resource.pathname !== "/"
    ) {
        throw new Error("validated authentication context is missing");
    }
    const authorizationHeader = `Bearer ${authInfo.token}`;
    const server = new McpServer({ name: "hwpx-agent", version: "0.1.0" });
    for (const descriptor of catalog.tools) {
        server.registerTool(
            descriptor.name,
            {
                title: descriptor.name,
                description: descriptor.description,
                inputSchema: fromJsonSchema<JsonRecord>(descriptor.inputSchema),
                outputSchema: fromJsonSchema<JsonRecord>(
                    descriptor.outputSchema,
                ),
                annotations: descriptor.annotations,
                _meta: descriptor._meta,
            },
            async (argumentsValue): Promise<CallToolResult> =>
                invokeTool(
                    driver,
                    authorizationHeader,
                    descriptor.name,
                    argumentsValue,
                ),
        );
    }
    return server;
}

async function invokeTool(
    driver: StagingDriver,
    authorizationHeader: string,
    toolName: string,
    argumentsValue: JsonRecord,
): Promise<CallToolResult> {
    const result = await driver.call({
        mode: "tool",
        authorization_header: authorizationHeader,
        now_unix_seconds: unixSeconds(),
        tool_name: toolName,
        arguments: argumentsValue,
    });
    if (!isCallToolResult(result)) {
        throw new Error("driver response shape mismatch");
    }
    return result;
}

async function authenticate(
    driver: StagingDriver,
    authorizationHeader: string,
): Promise<boolean> {
    try {
        const result = await driver.call({
            mode: "auth",
            authorization_header: authorizationHeader,
            now_unix_seconds: unixSeconds(),
        });
        return isRecord(result) && result.authenticated === true;
    } catch {
        return false;
    }
}

class StagingDriver {
    readonly #child: ChildProcessWithoutNullStreams;
    readonly #pending = new Map<number, PendingDriverRequest>();
    #nextRequestId = 1;
    #stdoutBuffer = Buffer.alloc(0);
    #stderrBytes = 0;
    #closed = false;

    private constructor(config: RuntimeConfig) {
        this.#child = spawn(config.driverPath, [], {
            env: {
                HWPX_AGENT_STAGING_HMAC_KEY_B64: config.hmacSecret,
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
            this.#failAll("staging driver launch failed"),
        );
        this.#child.on("close", () => this.#failAll("staging driver closed"));
        this.#child.stdin.on("error", () =>
            this.#failAll("staging driver input failed"),
        );
    }

    static async start(config: RuntimeConfig): Promise<StagingDriver> {
        const driver = new StagingDriver(config);
        await new Promise<void>((resolvePromise, rejectPromise) => {
            const onSpawn = (): void => {
                driver.#child.off("error", onError);
                resolvePromise();
            };
            const onError = (): void => {
                driver.#child.off("spawn", onSpawn);
                rejectPromise(new Error("staging driver launch failed"));
            };
            driver.#child.once("spawn", onSpawn);
            driver.#child.once("error", onError);
        });
        return driver;
    }

    async call(request: DriverRequest): Promise<unknown> {
        if (this.#closed) {
            throw new Error("staging driver is closed");
        }
        if (this.#pending.size >= MAX_CONCURRENT_DRIVERS) {
            throw new Error("staging driver capacity exhausted");
        }
        const requestId = this.#nextRequestId;
        if (
            !Number.isSafeInteger(requestId) ||
            requestId >= Number.MAX_SAFE_INTEGER
        ) {
            this.#child.kill();
            this.#failAll("staging driver request identifier exhausted");
            throw new Error("staging driver request identifier exhausted");
        }
        this.#nextRequestId = requestId + 1;
        const line = Buffer.from(
            `${JSON.stringify({ ...request, driver_request_id: requestId })}\n`,
            "utf8",
        );
        if (line.length > MAX_BODY_BYTES) {
            throw new Error("staging driver input exceeded limit");
        }
        return new Promise<unknown>((resolvePromise, rejectPromise) => {
            const timer = setTimeout(() => {
                this.#child.kill();
                this.#failAll("staging driver timed out");
            }, DRIVER_TIMEOUT_MS);
            this.#pending.set(requestId, {
                resolve: resolvePromise,
                reject: rejectPromise,
                timer,
            });
            this.#child.stdin.write(line, (error) => {
                if (error !== null && error !== undefined) {
                    this.#child.kill();
                    this.#failAll("staging driver input failed");
                }
            });
        });
    }

    async close(): Promise<void> {
        if (this.#child.exitCode !== null || this.#child.signalCode !== null) {
            if (this.#child.exitCode !== 0) {
                throw new Error("staging driver did not exit cleanly");
            }
            return;
        }
        this.#closed = true;
        this.#child.stdin.end();
        if (this.#child.exitCode !== null) {
            return;
        }
        await new Promise<void>((resolvePromise) => {
            const timer = setTimeout(() => this.#child.kill(), 1_000);
            this.#child.once("close", () => {
                clearTimeout(timer);
                resolvePromise();
            });
        });
        if (this.#child.exitCode !== 0) {
            throw new Error("staging driver did not exit cleanly");
        }
    }

    #handleStdout(chunk: Buffer): void {
        this.#stdoutBuffer = Buffer.concat([this.#stdoutBuffer, chunk]);
        if (this.#stdoutBuffer.length > MAX_DRIVER_STDOUT_BYTES) {
            this.#child.kill();
            this.#failAll("staging driver response exceeded limit");
            return;
        }
        while (true) {
            const newline = this.#stdoutBuffer.indexOf(0x0a);
            if (newline < 0) {
                return;
            }
            const line = this.#stdoutBuffer.subarray(0, newline);
            this.#stdoutBuffer = this.#stdoutBuffer.subarray(newline + 1);
            if (line.length === 0) {
                this.#child.kill();
                this.#failAll("staging driver returned an empty response");
                return;
            }
            let value: unknown;
            try {
                value = JSON.parse(line.toString("utf8")) as unknown;
            } catch {
                this.#child.kill();
                this.#failAll("staging driver returned malformed response");
                return;
            }
            if (!isDriverEnvelope(value)) {
                this.#child.kill();
                this.#failAll("staging driver response shape mismatch");
                return;
            }
            const pending = this.#pending.get(value.driver_request_id);
            if (pending === undefined) {
                this.#child.kill();
                this.#failAll("staging driver response correlation mismatch");
                return;
            }
            this.#pending.delete(value.driver_request_id);
            clearTimeout(pending.timer);
            if (!value.ok || value.result === undefined) {
                pending.reject(new Error("staging driver rejected request"));
            } else {
                pending.resolve(value.result);
            }
        }
    }

    #handleStderr(chunk: Buffer): void {
        this.#stderrBytes += chunk.length;
        if (this.#stderrBytes > MAX_DRIVER_STDERR_BYTES) {
            this.#child.kill();
            this.#failAll("staging driver diagnostics exceeded limit");
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
        if (total > MAX_BODY_BYTES) {
            throw new BodyTooLargeError();
        }
        chunks.push(chunk);
    }
    if (total === 0) {
        throw new MalformedBodyError();
    }
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
    const catalog = await loadCatalog(config.repoRoot);
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
    const driver = await StagingDriver.start(config);

    const handler = createMcpHandler(
        ({ authInfo }) => createMcpServer(catalog, driver, authInfo),
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
                ) {
                    return;
                }
                if (request.url !== "/mcp") {
                    reject(response, 404, "not_found");
                    return;
                }
                if (
                    request.method !== "POST" &&
                    request.method !== "GET" &&
                    request.method !== "DELETE"
                ) {
                    reject(response, 405, "method_not_allowed", {
                        Allow: "POST, GET, DELETE",
                    });
                    return;
                }
                const token = parseBearerHeader(request.headers.authorization);
                if (token === undefined) {
                    reject(response, 401, "unauthorized", {
                        "WWW-Authenticate": `Bearer resource_metadata="${RESOURCE_METADATA}"`,
                    });
                    return;
                }
                const authorizationHeader = `Bearer ${token}`;
                if (!(await authenticate(driver, authorizationHeader))) {
                    reject(response, 401, "unauthorized", {
                        "WWW-Authenticate": `Bearer resource_metadata="${RESOURCE_METADATA}"`,
                    });
                    return;
                }
                const auth: AuthInfo = {
                    token,
                    clientId: "p15-inspector-staging",
                    scopes: [...ALL_SCOPES],
                    resource: new URL(RESOURCE),
                };
                const authenticatedRequest = request as IncomingMessage & {
                    auth?: AuthInfo;
                };
                authenticatedRequest.auth = auth;
                if (request.method === "POST") {
                    try {
                        const parsedBody = await readBoundedJson(request);
                        await nodeHandler(
                            authenticatedRequest as Parameters<
                                typeof nodeHandler
                            >[0],
                            response,
                            parsedBody,
                        );
                    } catch (error) {
                        if (error instanceof BodyTooLargeError) {
                            reject(response, 413, "request_too_large");
                        } else {
                            reject(response, 400, "malformed_request");
                        }
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
                if (!response.headersSent) {
                    reject(response, 500, "internal_error");
                } else {
                    response.destroy();
                }
            });
        },
    );
    privateKey.fill(0);

    server.maxConnections = 32;
    server.on("clientError", (_error, socket) => socket.destroy());
    await new Promise<void>((resolvePromise, rejectPromise) => {
        server.once("error", rejectPromise);
        server.listen(0, "127.0.0.1", () => resolvePromise());
    });
    const address = server.address();
    if (address === null || typeof address === "string") {
        throw new Error("staging listener did not expose a TCP port");
    }
    process.stdout.write(
        `${JSON.stringify({
            state: "ready",
            url: `https://127.0.0.1:${address.port}/mcp`,
            certificate_pem_base64: Buffer.from(
                certificatePem,
                "utf8",
            ).toString("base64"),
            catalog_sha256: CATALOG_SHA256,
            tool_count: EXPECTED_TOOL_COUNT,
            protocol_eras: ["2026-07-28", "2025-stateless"],
            driver_lifecycle: "persistent_per_server_run",
        })}\n`,
    );

    let lifetimeTimer: NodeJS.Timeout | undefined;
    let shuttingDown = false;
    const shutdown = async (): Promise<void> => {
        if (shuttingDown) {
            return;
        }
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
    for (const signal of ["SIGINT", "SIGTERM"] as const) {
        process.once(signal, requestShutdown);
    }
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

function isJsonRecord(value: unknown): value is JsonRecord {
    return isRecord(value);
}

function isToolDescriptor(value: unknown): value is ToolDescriptor {
    if (!isRecord(value)) {
        return false;
    }
    const annotations = value.annotations;
    return (
        typeof value.name === "string" &&
        /^[a-z][a-z0-9_]{2,63}$/.test(value.name) &&
        typeof value.description === "string" &&
        value.description.length > 0 &&
        isJsonRecord(value.inputSchema) &&
        isJsonRecord(value.outputSchema) &&
        isJsonRecord(value._meta) &&
        isRecord(annotations) &&
        typeof annotations.readOnlyHint === "boolean" &&
        typeof annotations.destructiveHint === "boolean" &&
        typeof annotations.idempotentHint === "boolean" &&
        typeof annotations.openWorldHint === "boolean"
    );
}

function isCallToolResult(value: unknown): value is CallToolResult {
    if (
        !isRecord(value) ||
        !Array.isArray(value.content) ||
        typeof value.isError !== "boolean"
    ) {
        return false;
    }
    if (!isJsonRecord(value.structuredContent) || !isJsonRecord(value._meta)) {
        return false;
    }
    return value.content.every(
        (entry) =>
            isRecord(entry) &&
            entry.type === "text" &&
            typeof entry.text === "string",
    );
}

function unixSeconds(): number {
    return Math.floor(Date.now() / 1_000);
}

const invokedPath = process.argv[1];
if (
    invokedPath !== undefined &&
    import.meta.url === pathToFileURL(resolve(invokedPath)).href
) {
    serve().catch(() => {
        process.stderr.write("mcp-staging: startup failed closed\n");
        process.exitCode = 1;
    });
}
