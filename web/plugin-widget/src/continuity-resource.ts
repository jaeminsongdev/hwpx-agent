import { RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";

import {
    CONTINUITY_RENDER_REQUEST_SCHEMA,
    CONTINUITY_SNAPSHOT_SCHEMA,
    parseContinuitySnapshot,
} from "./continuity-model.js";

export const CONTINUITY_RESOURCE_URI =
    "ui://hwpx-agent/project-continuity/v1.html" as const;
export const CONTINUITY_RENDER_TOOL_NAME =
    "render_project_continuity_widget" as const;
export const CONTINUITY_MAX_HTML_BYTES = 800_000;
export const CONTINUITY_CSP = Object.freeze({
    connectDomains: Object.freeze([] as string[]),
    resourceDomains: Object.freeze([] as string[]),
});
const PROJECT_READ_SECURITY = Object.freeze({
    type: "oauth2",
    scopes: Object.freeze(["project.read"]),
});

const LOCALE_SCHEMA = Object.freeze({
    type: "string",
    minLength: 1,
    maxLength: 35,
    pattern: "^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$",
});
const PROJECT_ID_SCHEMA = Object.freeze({
    type: "string",
    minLength: 12,
    maxLength: 124,
    pattern: "^prj_[A-Za-z0-9_-]{8,120}$",
});
const REVISION_ID_SCHEMA = Object.freeze({
    type: "string",
    minLength: 12,
    maxLength: 124,
    pattern: "^rev_[A-Za-z0-9_-]{8,120}$",
});
const NULLABLE_REVISION_ID_SCHEMA = Object.freeze({
    oneOf: [REVISION_ID_SCHEMA, { type: "null" }],
});
const CURSOR_SCHEMA = Object.freeze({
    oneOf: [
        {
            type: "string",
            minLength: 1,
            maxLength: 2048,
            pattern: "^[A-Za-z0-9_-]+={0,2}$",
        },
        { type: "null" },
    ],
});

export const CONTINUITY_RENDER_INPUT_SCHEMA = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        schema_version: { const: CONTINUITY_RENDER_REQUEST_SCHEMA },
        client_surface: {
            type: "string",
            enum: ["chatgpt_web", "codex_remote", "codex_local"],
        },
        locale: LOCALE_SCHEMA,
        project_id: PROJECT_ID_SCHEMA,
    },
    required: ["schema_version", "client_surface", "locale", "project_id"],
});

const REVISION_SCHEMA = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        revision_id: REVISION_ID_SCHEMA,
        parent_revision_ids: {
            type: "array",
            maxItems: 8,
            items: REVISION_ID_SCHEMA,
        },
        created_at: {
            type: "string",
            maxLength: 40,
            pattern:
                "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\\.[0-9]{1,9})?Z$",
        },
        change_kind: {
            type: "string",
            enum: [
                "created",
                "edited",
                "transformed",
                "validated",
                "imported",
                "unknown",
            ],
        },
    },
    required: [
        "revision_id",
        "parent_revision_ids",
        "created_at",
        "change_kind",
    ],
});

export const CONTINUITY_RENDER_OUTPUT_SCHEMA = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        schema_version: { const: CONTINUITY_SNAPSHOT_SCHEMA },
        client_surface: {
            type: "string",
            enum: ["chatgpt_web", "codex_remote", "codex_local"],
        },
        locale: LOCALE_SCHEMA,
        project_id: PROJECT_ID_SCHEMA,
        head_revision_id: NULLABLE_REVISION_ID_SCHEMA,
        warning_count: { type: "integer", minimum: 0, maximum: 1_000_000 },
        conflict_state: {
            type: "string",
            enum: ["none", "locked", "stale", "diverged"],
        },
        revisions: { type: "array", maxItems: 12, items: REVISION_SCHEMA },
        next_cursor: CURSOR_SCHEMA,
    },
    required: [
        "schema_version",
        "client_surface",
        "locale",
        "project_id",
        "head_revision_id",
        "warning_count",
        "conflict_state",
        "revisions",
        "next_cursor",
    ],
});

export function createContinuityResource(html: string) {
    if (Buffer.byteLength(html, "utf8") > CONTINUITY_MAX_HTML_BYTES) {
        throw new Error("continuity HTML exceeds the bounded resource size");
    }
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
    ) {
        throw new Error("continuity HTML must not contain external references");
    }
    return {
        contents: [
            {
                uri: CONTINUITY_RESOURCE_URI,
                mimeType: RESOURCE_MIME_TYPE,
                text: html,
                _meta: {
                    ui: {
                        csp: CONTINUITY_CSP,
                        prefersBorder: true,
                    },
                },
            },
        ],
    } as const;
}

export const CONTINUITY_RENDER_TOOL_DESCRIPTOR = Object.freeze({
    name: CONTINUITY_RENDER_TOOL_NAME,
    title: "Render project continuity widget",
    description:
        "Render bounded project head, revision, warning, conflict, and checkpoint controls. Rendering creates no state.",
    annotations: Object.freeze({
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
    }),
    inputSchema: CONTINUITY_RENDER_INPUT_SCHEMA,
    outputSchema: CONTINUITY_RENDER_OUTPUT_SCHEMA,
    securitySchemes: Object.freeze([PROJECT_READ_SECURITY]),
    _meta: Object.freeze({
        securitySchemes: Object.freeze([PROJECT_READ_SECURITY]),
        ui: Object.freeze({ resourceUri: CONTINUITY_RESOURCE_URI }),
    }),
});

export function createContinuityToolResult(value: unknown) {
    const snapshot = parseContinuitySnapshot(value);
    if (snapshot === null) throw new Error("invalid continuity snapshot");
    return {
        structuredContent: snapshot,
        content: [{ type: "text", text: "Project continuity is ready." }],
        _meta: {
            "hwpx-agent/continuity-version": "1",
            "hwpx-agent/preferred-display-mode": "inline",
        },
    } as const;
}

export { RESOURCE_MIME_TYPE };
