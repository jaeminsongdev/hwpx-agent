import { RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";

import { parseWidgetSnapshot } from "./model.js";

export const WIDGET_RESOURCE_URI =
    "ui://hwpx-agent/document-work/v1.html" as const;
export const WIDGET_RENDER_TOOL_NAME = "render_document_work_widget" as const;
export const WIDGET_MAX_HTML_BYTES = 700_000;
export const WIDGET_CSP = Object.freeze({
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
    oneOf: [
        {
            type: "string",
            minLength: 12,
            maxLength: 124,
            pattern: "^prj_[A-Za-z0-9_-]{8,120}$",
        },
        { type: "null" },
    ],
});

export const WIDGET_RENDER_INPUT_SCHEMA = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        schema_version: { const: "hwpx-agent.widget-render-request/v1" },
        client_surface: {
            type: "string",
            enum: ["chatgpt_web", "codex_remote", "codex_local"],
        },
        locale: LOCALE_SCHEMA,
        project_id: PROJECT_ID_SCHEMA,
    },
    required: ["schema_version", "client_surface", "locale", "project_id"],
});

export const WIDGET_RENDER_OUTPUT_SCHEMA = Object.freeze({
    type: "object",
    additionalProperties: false,
    properties: {
        schema_version: { const: "hwpx-agent.widget-shell/v1" },
        client_surface: {
            type: "string",
            enum: ["chatgpt_web", "codex_remote", "codex_local"],
        },
        locale: LOCALE_SCHEMA,
        project_id: PROJECT_ID_SCHEMA,
        revision_id: {
            oneOf: [
                {
                    type: "string",
                    minLength: 12,
                    maxLength: 124,
                    pattern: "^rev_[A-Za-z0-9_-]{8,120}$",
                },
                { type: "null" },
            ],
        },
        validation_state: {
            type: "string",
            enum: [
                "queued",
                "running",
                "verified",
                "partial",
                "failed",
                "unverified",
            ],
        },
    },
    required: [
        "schema_version",
        "client_surface",
        "locale",
        "project_id",
        "revision_id",
        "validation_state",
    ],
});

export function createWidgetResource(html: string) {
    if (Buffer.byteLength(html, "utf8") > WIDGET_MAX_HTML_BYTES) {
        throw new Error("widget HTML exceeds the bounded resource size");
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
        throw new Error(
            "widget HTML must not contain external network references",
        );
    }
    return {
        contents: [
            {
                uri: WIDGET_RESOURCE_URI,
                mimeType: RESOURCE_MIME_TYPE,
                text: html,
                _meta: {
                    ui: {
                        csp: WIDGET_CSP,
                        prefersBorder: true,
                    },
                },
            },
        ],
    } as const;
}

export const WIDGET_RENDER_TOOL_DESCRIPTOR = Object.freeze({
    name: WIDGET_RENDER_TOOL_NAME,
    title: "Render document work widget",
    description:
        "Render a bounded document-work status shell. This read-only tool does not open or modify a document.",
    annotations: Object.freeze({
        readOnlyHint: true,
        destructiveHint: false,
        idempotentHint: true,
        openWorldHint: false,
    }),
    inputSchema: WIDGET_RENDER_INPUT_SCHEMA,
    outputSchema: WIDGET_RENDER_OUTPUT_SCHEMA,
    securitySchemes: Object.freeze([PROJECT_READ_SECURITY]),
    _meta: Object.freeze({
        securitySchemes: Object.freeze([PROJECT_READ_SECURITY]),
        ui: Object.freeze({ resourceUri: WIDGET_RESOURCE_URI }),
    }),
});

export function createRenderToolResult(value: unknown) {
    const snapshot = parseWidgetSnapshot(value);
    if (snapshot === null) {
        throw new Error("invalid widget snapshot");
    }
    return {
        structuredContent: snapshot,
        content: [{ type: "text", text: "Document work status is ready." }],
        _meta: {
            "hwpx-agent/widget-shell-version": "1",
            "hwpx-agent/preferred-display-mode": "inline",
        },
    } as const;
}

export { RESOURCE_MIME_TYPE };
