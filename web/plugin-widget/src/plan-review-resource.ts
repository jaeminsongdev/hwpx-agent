import { RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";
import {
    PLAN_REVIEW_REQUEST_SCHEMA,
    PLAN_REVIEW_SNAPSHOT_SCHEMA,
    parsePlanReviewSnapshot,
} from "./plan-review-model.js";

export const PLAN_REVIEW_RESOURCE_URI =
    "ui://hwpx-agent/plan-review/v1.html" as const;
export const PLAN_REVIEW_RENDER_TOOL_NAME =
    "render_plan_review_widget" as const;
export const PLAN_REVIEW_MAX_HTML_BYTES = 800_000;
export const PLAN_REVIEW_CSP = Object.freeze({
    connectDomains: Object.freeze([] as string[]),
    resourceDomains: Object.freeze([] as string[]),
});
const READ_SECURITY = Object.freeze({
    type: "oauth2",
    scopes: Object.freeze(["project.read"]),
});
const id = (pattern: string, maxLength = 124) =>
    Object.freeze({ type: "string", minLength: 1, maxLength, pattern });
const LOCALE = id(
    "^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$",
    35,
);
const PROJECT = id("^prj_[A-Za-z0-9_-]{8,120}$");
const REVISION = id("^rev_[A-Za-z0-9_-]{8,120}$");
const PLAN = id("^plan_[A-Za-z0-9_-]{8,120}$");
const CAPABILITY = id("^[a-z][a-z0-9_]*(?:\\.[a-z][a-z0-9_]*)+$", 160);
const CODE = id("^[A-Z][A-Z0-9_]{2,95}$", 96);
const SHA = id("^[0-9a-f]{64}$", 64);
const SURFACE = Object.freeze({
    type: "string",
    enum: ["chatgpt_web", "codex_remote", "codex_local"],
});

export const PLAN_REVIEW_RENDER_INPUT_SCHEMA = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        schema_version: { const: PLAN_REVIEW_REQUEST_SCHEMA },
        client_surface: SURFACE,
        locale: LOCALE,
        project_id: PROJECT,
        source_revision_id: REVISION,
        plan_id: PLAN,
    },
    required: [
        "schema_version",
        "client_surface",
        "locale",
        "project_id",
        "source_revision_id",
        "plan_id",
    ],
});
const ROUTE = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        capability_id: CAPABILITY,
        selected_backend: {
            type: "string",
            enum: ["direct_hwpx", "hancom_2020", "hybrid", "none"],
        },
        support_level: {
            type: "string",
            enum: ["verified", "partial", "unverified", "unsupported"],
        },
        supported: { type: "boolean" },
    },
    required: [
        "capability_id",
        "selected_backend",
        "support_level",
        "supported",
    ],
});
const CATEGORY = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        kind: {
            type: "string",
            enum: [
                "paragraph",
                "table",
                "style",
                "image",
                "field",
                "section",
                "metadata",
                "other",
            ],
        },
        count: { type: "integer", minimum: 0, maximum: 100000 },
    },
    required: ["kind", "count"],
});
const WARNING = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        code: CODE,
        severity: { type: "string", enum: ["notice", "warning", "blocking"] },
        kind: {
            type: "string",
            enum: [
                "validation",
                "preservation",
                "layout",
                "signature",
                "permission",
                "other",
            ],
        },
    },
    required: ["code", "severity", "kind"],
});
export const PLAN_REVIEW_RENDER_OUTPUT_SCHEMA = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        schema_version: { const: PLAN_REVIEW_SNAPSHOT_SCHEMA },
        client_surface: SURFACE,
        locale: LOCALE,
        project_id: PROJECT,
        source_revision_id: REVISION,
        plan_id: PLAN,
        risk_level: { type: "string", enum: ["low", "medium", "high"] },
        estimated_page_effect: {
            type: "string",
            enum: ["none", "local", "document_wide", "unknown"],
        },
        route: { type: "array", minItems: 1, maxItems: 12, items: ROUTE },
        route_digest: SHA,
        diff: {
            type: "object",
            additionalProperties: false,
            properties: {
                added: { type: "integer", minimum: 0, maximum: 100000 },
                modified: { type: "integer", minimum: 0, maximum: 100000 },
                removed: { type: "integer", minimum: 0, maximum: 100000 },
                categories: { type: "array", maxItems: 8, items: CATEGORY },
            },
            required: ["added", "modified", "removed", "categories"],
        },
        warnings: { type: "array", maxItems: 8, items: WARNING },
        signature_impact: {
            type: "string",
            enum: ["none", "invalidates", "unknown"],
        },
        dry_run_state: {
            type: "string",
            enum: ["verified", "partial", "failed", "not_run"],
        },
        execution_allowed: { type: "boolean" },
    },
    required: [
        "schema_version",
        "client_surface",
        "locale",
        "project_id",
        "source_revision_id",
        "plan_id",
        "risk_level",
        "estimated_page_effect",
        "route",
        "route_digest",
        "diff",
        "warnings",
        "signature_impact",
        "dry_run_state",
        "execution_allowed",
    ],
});

export function createPlanReviewResource(html: string) {
    if (Buffer.byteLength(html, "utf8") > PLAN_REVIEW_MAX_HTML_BYTES)
        throw new Error("plan review HTML exceeds the bounded resource size");
    if (
        /<(?:base|embed|form|iframe|object)\b/iu.test(html) ||
        /<meta\b[^>]*http-equiv\s*=\s*["']?refresh/iu.test(html) ||
        /<(?:audio|img|link|script|source|track|video)\b[^>]*(?:href|poster|src|srcset)\s*=/iu.test(
            html,
        ) ||
        /\b(?:action|href|poster|src|srcset)\s*=\s*["']?\s*(?:https?:|\/\/)/iu.test(
            html,
        ) ||
        /@import\s|url\(\s*["']?(?:https?:|\/\/)/iu.test(html)
    )
        throw new Error(
            "plan review HTML must not contain external references",
        );
    return {
        contents: [
            {
                uri: PLAN_REVIEW_RESOURCE_URI,
                mimeType: RESOURCE_MIME_TYPE,
                text: html,
                _meta: { ui: { csp: PLAN_REVIEW_CSP, prefersBorder: true } },
            },
        ],
    } as const;
}
export const PLAN_REVIEW_RENDER_TOOL_DESCRIPTOR = Object.freeze({
    name: PLAN_REVIEW_RENDER_TOOL_NAME,
    title: "Render plan and semantic diff review",
    description:
        "Render a bounded authoritative plan, capability route, semantic diff, warning and explicit execution review. Rendering creates no state.",
    annotations: Object.freeze({
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
    }),
    inputSchema: PLAN_REVIEW_RENDER_INPUT_SCHEMA,
    outputSchema: PLAN_REVIEW_RENDER_OUTPUT_SCHEMA,
    securitySchemes: Object.freeze([READ_SECURITY]),
    _meta: Object.freeze({
        securitySchemes: Object.freeze([READ_SECURITY]),
        ui: Object.freeze({ resourceUri: PLAN_REVIEW_RESOURCE_URI }),
    }),
});
export function createPlanReviewToolResult(value: unknown) {
    const snapshot = parsePlanReviewSnapshot(value);
    if (snapshot === null) throw new Error("invalid plan review snapshot");
    return {
        structuredContent: snapshot,
        content: [{ type: "text", text: "Plan review is ready." }],
        _meta: {
            "hwpx-agent/plan-review-version": "1",
            "hwpx-agent/preferred-display-mode": "inline",
        },
    } as const;
}
export { RESOURCE_MIME_TYPE };
