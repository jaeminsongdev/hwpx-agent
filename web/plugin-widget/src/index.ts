export type ValidationState = "passed" | "failed" | "unverified";

export interface ArtifactStatus {
    readonly artifactSha256: string;
    readonly validation: ValidationState;
}

export function summarizeArtifact(status: ArtifactStatus): string {
    if (!/^[0-9a-f]{64}$/.test(status.artifactSha256)) {
        throw new Error("artifactSha256 must be lowercase SHA-256 hex");
    }
    return `${status.validation}:${status.artifactSha256.slice(0, 12)}`;
}

export {
    createRenderToolResult,
    createWidgetResource,
    RESOURCE_MIME_TYPE,
    WIDGET_CSP,
    WIDGET_RENDER_INPUT_SCHEMA,
    WIDGET_RENDER_OUTPUT_SCHEMA,
    WIDGET_RENDER_TOOL_DESCRIPTOR,
    WIDGET_RENDER_TOOL_NAME,
    WIDGET_RESOURCE_URI,
} from "./resource.js";
export {
    parseWidgetRenderRequest,
    parseWidgetSnapshot,
    WIDGET_RENDER_REQUEST_SCHEMA,
    WIDGET_SNAPSHOT_SCHEMA,
} from "./model.js";
