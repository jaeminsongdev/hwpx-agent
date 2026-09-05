export const WIDGET_SNAPSHOT_SCHEMA = "hwpx-agent.widget-shell/v1" as const;
export const WIDGET_RENDER_REQUEST_SCHEMA =
    "hwpx-agent.widget-render-request/v1" as const;

export type ClientSurface = "chatgpt_web" | "codex_remote" | "codex_local";
export type ValidationState =
    "queued" | "running" | "verified" | "partial" | "failed" | "unverified";
export type ViewLocale = "ko-KR" | "en-US";
export type HostTheme = "light" | "dark";

export interface WidgetSnapshot {
    readonly schema_version: typeof WIDGET_SNAPSHOT_SCHEMA;
    readonly client_surface: ClientSurface;
    readonly locale: string;
    readonly project_id: string | null;
    readonly revision_id: string | null;
    readonly validation_state: ValidationState;
}

export interface WidgetRenderRequest {
    readonly schema_version: typeof WIDGET_RENDER_REQUEST_SCHEMA;
    readonly client_surface: ClientSurface;
    readonly locale: string;
    readonly project_id: string | null;
}

const SNAPSHOT_KEYS = [
    "schema_version",
    "client_surface",
    "locale",
    "project_id",
    "revision_id",
    "validation_state",
] as const;
const CLIENT_SURFACES = new Set<ClientSurface>([
    "chatgpt_web",
    "codex_remote",
    "codex_local",
]);
const VALIDATION_STATES = new Set<ValidationState>([
    "queued",
    "running",
    "verified",
    "partial",
    "failed",
    "unverified",
]);
const LOCALE_PATTERN =
    /^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$/;
const PROJECT_ID_PATTERN = /^prj_[A-Za-z0-9_-]{8,120}$/;
const REVISION_ID_PATTERN = /^rev_[A-Za-z0-9_-]{8,120}$/;
const RENDER_REQUEST_KEYS = [
    "schema_version",
    "client_surface",
    "locale",
    "project_id",
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(
    value: Record<string, unknown>,
    expected: readonly string[],
): boolean {
    const keys = Object.keys(value).sort();
    const sortedExpected = [...expected].sort();
    return (
        keys.length === sortedExpected.length &&
        keys.every((key, index) => key === sortedExpected[index])
    );
}

function isNullableIdentifier(
    value: unknown,
    pattern: RegExp,
): value is string | null {
    return value === null || (typeof value === "string" && pattern.test(value));
}

export function parseWidgetSnapshot(value: unknown): WidgetSnapshot | null {
    if (!isRecord(value) || !hasExactKeys(value, SNAPSHOT_KEYS)) {
        return null;
    }
    const surface = value.client_surface;
    const validation = value.validation_state;
    if (
        value.schema_version !== WIDGET_SNAPSHOT_SCHEMA ||
        typeof surface !== "string" ||
        !CLIENT_SURFACES.has(surface as ClientSurface) ||
        typeof value.locale !== "string" ||
        value.locale.length > 35 ||
        !LOCALE_PATTERN.test(value.locale) ||
        !isNullableIdentifier(value.project_id, PROJECT_ID_PATTERN) ||
        !isNullableIdentifier(value.revision_id, REVISION_ID_PATTERN) ||
        typeof validation !== "string" ||
        !VALIDATION_STATES.has(validation as ValidationState)
    ) {
        return null;
    }
    return {
        schema_version: WIDGET_SNAPSHOT_SCHEMA,
        client_surface: surface as ClientSurface,
        locale: value.locale,
        project_id: value.project_id,
        revision_id: value.revision_id,
        validation_state: validation as ValidationState,
    };
}

export function parseWidgetRenderRequest(
    value: unknown,
): WidgetRenderRequest | null {
    if (!isRecord(value) || !hasExactKeys(value, RENDER_REQUEST_KEYS)) {
        return null;
    }
    const surface = value.client_surface;
    if (
        value.schema_version !== WIDGET_RENDER_REQUEST_SCHEMA ||
        typeof surface !== "string" ||
        !CLIENT_SURFACES.has(surface as ClientSurface) ||
        typeof value.locale !== "string" ||
        value.locale.length > 35 ||
        !LOCALE_PATTERN.test(value.locale) ||
        !isNullableIdentifier(value.project_id, PROJECT_ID_PATTERN)
    ) {
        return null;
    }
    return {
        schema_version: WIDGET_RENDER_REQUEST_SCHEMA,
        client_surface: surface as ClientSurface,
        locale: value.locale,
        project_id: value.project_id,
    };
}

export function resolveViewLocale(
    value: unknown,
    fallback: ViewLocale = "ko-KR",
): ViewLocale {
    if (
        typeof value !== "string" ||
        value.length > 35 ||
        !LOCALE_PATTERN.test(value)
    ) {
        return fallback;
    }
    return value.toLowerCase().startsWith("ko") ? "ko-KR" : "en-US";
}

export function resolveHostTheme(value: unknown): HostTheme {
    return value === "dark" ? "dark" : "light";
}

export function displayOpaqueId(value: string | null): string {
    return value === null ? "—" : `${value.slice(0, 6)}…`;
}
