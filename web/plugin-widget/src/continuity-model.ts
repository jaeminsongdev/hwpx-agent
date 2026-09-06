import {
    resolveHostTheme,
    resolveViewLocale,
    type ClientSurface,
    type HostTheme,
    type ViewLocale,
} from "./model.js";

export const CONTINUITY_RENDER_REQUEST_SCHEMA =
    "hwpx-agent.continuity-render-request/v1" as const;
export const CONTINUITY_SNAPSHOT_SCHEMA =
    "hwpx-agent.project-continuity/v1" as const;
export const CONTINUITY_RENDER_REQUEST_V2_SCHEMA =
    "hwpx-agent.continuity-render-request/v2" as const;
export const CONTINUITY_SNAPSHOT_V2_SCHEMA =
    "hwpx-agent.project-continuity/v2" as const;
export const PUBLIC_RESULT_SCHEMA = "hwpx-agent.tool-result/v1" as const;

export type ConflictState = "none" | "locked" | "stale" | "diverged";
export type ConflictResolution =
    "rebase_operation_plan" | "branch" | "manual_merge";
export type RevisionChangeKind =
    "created" | "edited" | "transformed" | "validated" | "imported" | "unknown";

export interface ContinuityRenderRequest {
    readonly schema_version: typeof CONTINUITY_RENDER_REQUEST_SCHEMA;
    readonly client_surface: ClientSurface;
    readonly locale: string;
    readonly project_id: string;
}

export interface ContinuityRenderRequestV2 {
    readonly schema_version: typeof CONTINUITY_RENDER_REQUEST_V2_SCHEMA;
    readonly client_surface: ClientSurface;
    readonly locale: string;
    readonly project_id: string;
}

export interface ContinuityRevision {
    readonly revision_id: string;
    readonly parent_revision_ids: readonly string[];
    readonly created_at: string;
    readonly change_kind: RevisionChangeKind;
}

export interface ContinuitySnapshot {
    readonly schema_version: typeof CONTINUITY_SNAPSHOT_SCHEMA;
    readonly client_surface: ClientSurface;
    readonly locale: string;
    readonly project_id: string;
    readonly head_revision_id: string | null;
    readonly warning_count: number;
    readonly conflict_state: ConflictState;
    readonly revisions: readonly ContinuityRevision[];
    readonly next_cursor: string | null;
}

export interface StaleHeadDetail {
    readonly observed_generation: number;
    readonly current_generation: number;
    readonly delta: number;
    readonly allowed_resolutions: readonly ConflictResolution[];
}

export interface ContinuitySnapshotV2 {
    readonly schema_version: typeof CONTINUITY_SNAPSHOT_V2_SCHEMA;
    readonly client_surface: ClientSurface;
    readonly locale: string;
    readonly project_id: string;
    readonly head_revision_id: string | null;
    readonly warning_count: number;
    readonly conflict_state: ConflictState;
    readonly stale_head: StaleHeadDetail | null;
    readonly revisions: readonly ContinuityRevision[];
    readonly next_cursor: string | null;
}

export type AnyContinuityRenderRequest =
    ContinuityRenderRequest | ContinuityRenderRequestV2;
export type AnyContinuitySnapshot = ContinuitySnapshot | ContinuitySnapshotV2;

export interface ProjectOpenResult {
    readonly request_id: string;
    readonly project_id: string;
    readonly head_revision_id: string | null;
    readonly warning_count: number;
    readonly conflict_state: ConflictState;
}

export interface ProjectHistoryResult {
    readonly request_id: string;
    readonly revisions: readonly ContinuityRevision[];
    readonly next_cursor: string | null;
}

export interface ProjectCheckpointResult {
    readonly request_id: string;
    readonly checkpoint_id: string;
    readonly revision_id: string;
    readonly replayed: boolean;
}

export interface ProjectOpenResultV2 extends ProjectOpenResult {
    readonly stale_head: StaleHeadDetail | null;
}

export interface ProjectConflictResolveResult {
    readonly request_id: string;
    readonly project_id: string;
    readonly expected_revision: string;
    readonly resolution: ConflictResolution;
    readonly current_generation: number;
    readonly conflict_state: "none";
    readonly replayed: boolean;
}

const CLIENT_SURFACES = new Set<ClientSurface>([
    "chatgpt_web",
    "codex_remote",
    "codex_local",
]);
const CONFLICT_STATES = new Set<ConflictState>([
    "none",
    "locked",
    "stale",
    "diverged",
]);
const CONFLICT_RESOLUTIONS = new Set<ConflictResolution>([
    "rebase_operation_plan",
    "branch",
    "manual_merge",
]);
const CHANGE_KINDS = new Set<RevisionChangeKind>([
    "created",
    "edited",
    "transformed",
    "validated",
    "imported",
    "unknown",
]);
const OUTCOMES = new Set(["accepted", "succeeded", "partial", "unverified"]);
const PROJECT_ID_PATTERN = /^prj_[A-Za-z0-9_-]{8,120}$/;
const REVISION_ID_PATTERN = /^rev_[A-Za-z0-9_-]{8,120}$/;
const CHECKPOINT_ID_PATTERN = /^chk_[A-Za-z0-9_-]{8,120}$/;
const REQUEST_ID_PATTERN = /^req_[A-Za-z0-9_-]{8,120}$/;
const CURSOR_PATTERN = /^[A-Za-z0-9_-]+={0,2}$/;
const TIMESTAMP_PATTERN =
    /^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,9})?Z$/;
const WARNING_CODE_PATTERN = /^[A-Z][A-Z0-9_]{2,95}$/;
const LOCALE_PATTERN =
    /^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$/;

const RENDER_REQUEST_KEYS = [
    "schema_version",
    "client_surface",
    "locale",
    "project_id",
] as const;
const STALE_HEAD_KEYS = [
    "observed_generation",
    "current_generation",
    "delta",
    "allowed_resolutions",
] as const;
const SNAPSHOT_KEYS = [
    "schema_version",
    "client_surface",
    "locale",
    "project_id",
    "head_revision_id",
    "warning_count",
    "conflict_state",
    "revisions",
    "next_cursor",
] as const;
const SNAPSHOT_V2_KEYS = [
    "schema_version",
    "client_surface",
    "locale",
    "project_id",
    "head_revision_id",
    "warning_count",
    "conflict_state",
    "stale_head",
    "revisions",
    "next_cursor",
] as const;
const REVISION_KEYS = [
    "revision_id",
    "parent_revision_ids",
    "created_at",
    "change_kind",
] as const;
const PUBLIC_BASE_KEYS = [
    "schema_version",
    "request_id",
    "outcome",
    "safe_summary",
    "warnings",
] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasExactKeys(
    value: Record<string, unknown>,
    expected: readonly string[],
): boolean {
    const keys = Object.keys(value).sort();
    const expectedKeys = [...expected].sort();
    return (
        keys.length === expectedKeys.length &&
        keys.every((key, index) => key === expectedKeys[index])
    );
}

function isBoundedString(value: unknown, maximum: number): value is string {
    return (
        typeof value === "string" &&
        value.length >= 1 &&
        value.length <= maximum
    );
}

function isIdentifier(value: unknown, pattern: RegExp): value is string {
    return typeof value === "string" && pattern.test(value);
}

function isNullableIdentifier(
    value: unknown,
    pattern: RegExp,
): value is string | null {
    return value === null || isIdentifier(value, pattern);
}

function isCursor(value: unknown): value is string | null {
    return (
        value === null ||
        (typeof value === "string" &&
            value.length <= 2048 &&
            CURSOR_PATTERN.test(value))
    );
}

function isGeneration(value: unknown): value is number {
    return Number.isSafeInteger(value) && (value as number) >= 0;
}

function parseStaleHeadDetail(value: unknown): StaleHeadDetail | null {
    if (
        !isRecord(value) ||
        !hasExactKeys(value, STALE_HEAD_KEYS) ||
        !isGeneration(value.observed_generation) ||
        !isGeneration(value.current_generation) ||
        !isGeneration(value.delta) ||
        value.current_generation <= value.observed_generation ||
        value.delta !== value.current_generation - value.observed_generation ||
        !Array.isArray(value.allowed_resolutions) ||
        value.allowed_resolutions.length < 1 ||
        value.allowed_resolutions.length > CONFLICT_RESOLUTIONS.size ||
        !value.allowed_resolutions.every(
            (item) =>
                typeof item === "string" &&
                CONFLICT_RESOLUTIONS.has(item as ConflictResolution),
        ) ||
        new Set(value.allowed_resolutions).size !==
            value.allowed_resolutions.length
    ) {
        return null;
    }
    return {
        observed_generation: value.observed_generation,
        current_generation: value.current_generation,
        delta: value.delta,
        allowed_resolutions: value.allowed_resolutions as ConflictResolution[],
    };
}

function parseBasePublicResult(
    value: Record<string, unknown>,
    extraKeys: readonly string[],
): string | null {
    if (!hasExactKeys(value, [...PUBLIC_BASE_KEYS, ...extraKeys])) {
        return null;
    }
    if (
        value.schema_version !== PUBLIC_RESULT_SCHEMA ||
        !isIdentifier(value.request_id, REQUEST_ID_PATTERN) ||
        typeof value.outcome !== "string" ||
        !OUTCOMES.has(value.outcome) ||
        !isBoundedString(value.safe_summary, 1000) ||
        !Array.isArray(value.warnings) ||
        value.warnings.length > 64
    ) {
        return null;
    }
    for (const warning of value.warnings) {
        if (
            !isRecord(warning) ||
            !hasExactKeys(warning, ["code", "message"]) ||
            !isIdentifier(warning.code, WARNING_CODE_PATTERN) ||
            !isBoundedString(warning.message, 1000)
        ) {
            return null;
        }
    }
    return value.request_id;
}

function parseHistoryRevision(value: unknown): ContinuityRevision | null {
    if (
        !isRecord(value) ||
        !hasExactKeys(value, [
            "revision_id",
            "parent_revision_ids",
            "created_at",
            "summary",
        ]) ||
        !isIdentifier(value.revision_id, REVISION_ID_PATTERN) ||
        !Array.isArray(value.parent_revision_ids) ||
        value.parent_revision_ids.length > 8 ||
        !value.parent_revision_ids.every((item) =>
            isIdentifier(item, REVISION_ID_PATTERN),
        ) ||
        typeof value.created_at !== "string" ||
        !TIMESTAMP_PATTERN.test(value.created_at) ||
        !isBoundedString(value.summary, 500)
    ) {
        return null;
    }
    return {
        revision_id: value.revision_id,
        parent_revision_ids: value.parent_revision_ids,
        created_at: value.created_at,
        change_kind: classifyRevisionChange(value.summary),
    };
}

function parseContinuityRevision(value: unknown): ContinuityRevision | null {
    if (
        !isRecord(value) ||
        !hasExactKeys(value, REVISION_KEYS) ||
        !isIdentifier(value.revision_id, REVISION_ID_PATTERN) ||
        !Array.isArray(value.parent_revision_ids) ||
        value.parent_revision_ids.length > 8 ||
        !value.parent_revision_ids.every((item) =>
            isIdentifier(item, REVISION_ID_PATTERN),
        ) ||
        typeof value.created_at !== "string" ||
        !TIMESTAMP_PATTERN.test(value.created_at) ||
        typeof value.change_kind !== "string" ||
        !CHANGE_KINDS.has(value.change_kind as RevisionChangeKind)
    ) {
        return null;
    }
    return {
        revision_id: value.revision_id,
        parent_revision_ids: value.parent_revision_ids,
        created_at: value.created_at,
        change_kind: value.change_kind as RevisionChangeKind,
    };
}

export function parseContinuityRenderRequest(
    value: unknown,
): ContinuityRenderRequest | null {
    if (!isRecord(value) || !hasExactKeys(value, RENDER_REQUEST_KEYS)) {
        return null;
    }
    if (
        value.schema_version !== CONTINUITY_RENDER_REQUEST_SCHEMA ||
        typeof value.client_surface !== "string" ||
        !CLIENT_SURFACES.has(value.client_surface as ClientSurface) ||
        typeof value.locale !== "string" ||
        value.locale.length > 35 ||
        !LOCALE_PATTERN.test(value.locale) ||
        !isIdentifier(value.project_id, PROJECT_ID_PATTERN)
    ) {
        return null;
    }
    return {
        schema_version: CONTINUITY_RENDER_REQUEST_SCHEMA,
        client_surface: value.client_surface as ClientSurface,
        locale: value.locale,
        project_id: value.project_id,
    };
}

export function parseContinuityRenderRequestV2(
    value: unknown,
): ContinuityRenderRequestV2 | null {
    if (!isRecord(value) || !hasExactKeys(value, RENDER_REQUEST_KEYS)) {
        return null;
    }
    if (
        value.schema_version !== CONTINUITY_RENDER_REQUEST_V2_SCHEMA ||
        typeof value.client_surface !== "string" ||
        !CLIENT_SURFACES.has(value.client_surface as ClientSurface) ||
        typeof value.locale !== "string" ||
        value.locale.length > 35 ||
        !LOCALE_PATTERN.test(value.locale) ||
        !isIdentifier(value.project_id, PROJECT_ID_PATTERN)
    ) {
        return null;
    }
    return {
        schema_version: CONTINUITY_RENDER_REQUEST_V2_SCHEMA,
        client_surface: value.client_surface as ClientSurface,
        locale: value.locale,
        project_id: value.project_id,
    };
}

export function parseAnyContinuityRenderRequest(
    value: unknown,
): AnyContinuityRenderRequest | null {
    return (
        parseContinuityRenderRequest(value) ??
        parseContinuityRenderRequestV2(value)
    );
}

export function parseContinuitySnapshot(
    value: unknown,
): ContinuitySnapshot | null {
    if (!isRecord(value) || !hasExactKeys(value, SNAPSHOT_KEYS)) {
        return null;
    }
    if (
        value.schema_version !== CONTINUITY_SNAPSHOT_SCHEMA ||
        typeof value.client_surface !== "string" ||
        !CLIENT_SURFACES.has(value.client_surface as ClientSurface) ||
        typeof value.locale !== "string" ||
        value.locale.length > 35 ||
        !LOCALE_PATTERN.test(value.locale) ||
        !isIdentifier(value.project_id, PROJECT_ID_PATTERN) ||
        !isNullableIdentifier(value.head_revision_id, REVISION_ID_PATTERN) ||
        !Number.isInteger(value.warning_count) ||
        (value.warning_count as number) < 0 ||
        (value.warning_count as number) > 1_000_000 ||
        typeof value.conflict_state !== "string" ||
        !CONFLICT_STATES.has(value.conflict_state as ConflictState) ||
        !Array.isArray(value.revisions) ||
        value.revisions.length > 12 ||
        !isCursor(value.next_cursor)
    ) {
        return null;
    }
    const revisions = value.revisions.map(parseContinuityRevision);
    if (revisions.some((item) => item === null)) {
        return null;
    }
    const ids = revisions.map((item) => item!.revision_id);
    if (new Set(ids).size !== ids.length) {
        return null;
    }
    if (
        value.head_revision_id !== null &&
        revisions.length > 0 &&
        revisions[0]!.revision_id !== value.head_revision_id
    ) {
        return null;
    }
    return {
        schema_version: CONTINUITY_SNAPSHOT_SCHEMA,
        client_surface: value.client_surface as ClientSurface,
        locale: value.locale,
        project_id: value.project_id,
        head_revision_id: value.head_revision_id,
        warning_count: value.warning_count as number,
        conflict_state: value.conflict_state as ConflictState,
        revisions: revisions as ContinuityRevision[],
        next_cursor: value.next_cursor,
    };
}

export function parseContinuitySnapshotV2(
    value: unknown,
): ContinuitySnapshotV2 | null {
    if (!isRecord(value) || !hasExactKeys(value, SNAPSHOT_V2_KEYS)) {
        return null;
    }
    if (
        value.schema_version !== CONTINUITY_SNAPSHOT_V2_SCHEMA ||
        typeof value.client_surface !== "string" ||
        !CLIENT_SURFACES.has(value.client_surface as ClientSurface) ||
        typeof value.locale !== "string" ||
        value.locale.length > 35 ||
        !LOCALE_PATTERN.test(value.locale) ||
        !isIdentifier(value.project_id, PROJECT_ID_PATTERN) ||
        !isNullableIdentifier(value.head_revision_id, REVISION_ID_PATTERN) ||
        !Number.isInteger(value.warning_count) ||
        (value.warning_count as number) < 0 ||
        (value.warning_count as number) > 1_000_000 ||
        typeof value.conflict_state !== "string" ||
        !CONFLICT_STATES.has(value.conflict_state as ConflictState) ||
        !Array.isArray(value.revisions) ||
        value.revisions.length > 12 ||
        !isCursor(value.next_cursor)
    ) {
        return null;
    }
    const staleHead =
        value.stale_head === null
            ? null
            : parseStaleHeadDetail(value.stale_head);
    if (
        (value.conflict_state === "stale" &&
            (staleHead === null || value.head_revision_id === null)) ||
        (value.conflict_state !== "stale" && value.stale_head !== null)
    ) {
        return null;
    }
    const revisions = value.revisions.map(parseContinuityRevision);
    if (revisions.some((item) => item === null)) return null;
    const ids = revisions.map((item) => item!.revision_id);
    if (new Set(ids).size !== ids.length) return null;
    if (
        value.head_revision_id !== null &&
        revisions.length > 0 &&
        revisions[0]!.revision_id !== value.head_revision_id
    ) {
        return null;
    }
    return {
        schema_version: CONTINUITY_SNAPSHOT_V2_SCHEMA,
        client_surface: value.client_surface as ClientSurface,
        locale: value.locale,
        project_id: value.project_id,
        head_revision_id: value.head_revision_id,
        warning_count: value.warning_count as number,
        conflict_state: value.conflict_state as ConflictState,
        stale_head: staleHead,
        revisions: revisions as ContinuityRevision[],
        next_cursor: value.next_cursor,
    };
}

export function parseAnyContinuitySnapshot(
    value: unknown,
): AnyContinuitySnapshot | null {
    return parseContinuitySnapshot(value) ?? parseContinuitySnapshotV2(value);
}

export function parseProjectOpenResult(
    value: unknown,
): ProjectOpenResult | null {
    if (!isRecord(value)) return null;
    const requestId = parseBasePublicResult(value, [
        "project_id",
        "head_revision_id",
        "warning_count",
        "conflict_state",
        "recommended_actions",
    ]);
    if (
        requestId === null ||
        value.outcome !== "succeeded" ||
        !isIdentifier(value.project_id, PROJECT_ID_PATTERN) ||
        !isNullableIdentifier(value.head_revision_id, REVISION_ID_PATTERN) ||
        !Number.isInteger(value.warning_count) ||
        (value.warning_count as number) < 0 ||
        (value.warning_count as number) > 1_000_000 ||
        typeof value.conflict_state !== "string" ||
        !CONFLICT_STATES.has(value.conflict_state as ConflictState) ||
        !Array.isArray(value.recommended_actions) ||
        value.recommended_actions.length > 32 ||
        !value.recommended_actions.every((item) => isBoundedString(item, 500))
    ) {
        return null;
    }
    return {
        request_id: requestId,
        project_id: value.project_id,
        head_revision_id: value.head_revision_id,
        warning_count: value.warning_count as number,
        conflict_state: value.conflict_state as ConflictState,
    };
}

export function parseProjectOpenResultV2(
    value: unknown,
): ProjectOpenResultV2 | null {
    if (!isRecord(value)) return null;
    const requestId = parseBasePublicResult(value, [
        "project_id",
        "head_revision_id",
        "warning_count",
        "conflict_state",
        "stale_head",
        "recommended_actions",
    ]);
    if (
        requestId === null ||
        value.outcome !== "succeeded" ||
        !isIdentifier(value.project_id, PROJECT_ID_PATTERN) ||
        !isNullableIdentifier(value.head_revision_id, REVISION_ID_PATTERN) ||
        !Number.isInteger(value.warning_count) ||
        (value.warning_count as number) < 0 ||
        (value.warning_count as number) > 1_000_000 ||
        typeof value.conflict_state !== "string" ||
        !CONFLICT_STATES.has(value.conflict_state as ConflictState) ||
        !Array.isArray(value.recommended_actions) ||
        value.recommended_actions.length > 32 ||
        !value.recommended_actions.every((item) => isBoundedString(item, 500))
    ) {
        return null;
    }
    const staleHead =
        value.stale_head === null
            ? null
            : parseStaleHeadDetail(value.stale_head);
    if (
        (value.conflict_state === "stale" &&
            (staleHead === null || value.head_revision_id === null)) ||
        (value.conflict_state !== "stale" && value.stale_head !== null)
    ) {
        return null;
    }
    return {
        request_id: requestId,
        project_id: value.project_id,
        head_revision_id: value.head_revision_id,
        warning_count: value.warning_count as number,
        conflict_state: value.conflict_state as ConflictState,
        stale_head: staleHead,
    };
}

export function parseProjectHistoryResult(
    value: unknown,
): ProjectHistoryResult | null {
    if (!isRecord(value)) return null;
    const requestId = parseBasePublicResult(value, [
        "revisions",
        "next_cursor",
    ]);
    if (
        requestId === null ||
        value.outcome !== "succeeded" ||
        !Array.isArray(value.revisions) ||
        value.revisions.length > 200 ||
        !isCursor(value.next_cursor)
    ) {
        return null;
    }
    const revisions = value.revisions.map(parseHistoryRevision);
    if (revisions.some((item) => item === null)) return null;
    const ids = revisions.map((item) => item!.revision_id);
    if (new Set(ids).size !== ids.length) return null;
    return {
        request_id: requestId,
        revisions: revisions as ContinuityRevision[],
        next_cursor: value.next_cursor,
    };
}

export function parseProjectCheckpointResult(
    value: unknown,
): ProjectCheckpointResult | null {
    if (!isRecord(value)) return null;
    const requestId = parseBasePublicResult(value, [
        "checkpoint_id",
        "revision_id",
        "replayed",
    ]);
    if (
        requestId === null ||
        value.outcome !== "succeeded" ||
        !isIdentifier(value.checkpoint_id, CHECKPOINT_ID_PATTERN) ||
        !isIdentifier(value.revision_id, REVISION_ID_PATTERN) ||
        typeof value.replayed !== "boolean"
    ) {
        return null;
    }
    return {
        request_id: requestId,
        checkpoint_id: value.checkpoint_id,
        revision_id: value.revision_id,
        replayed: value.replayed,
    };
}

export function parseProjectConflictResolveResult(
    value: unknown,
): ProjectConflictResolveResult | null {
    if (!isRecord(value)) return null;
    const requestId = parseBasePublicResult(value, [
        "project_id",
        "expected_revision",
        "resolution",
        "current_generation",
        "conflict_state",
        "replayed",
    ]);
    if (
        requestId === null ||
        value.outcome !== "succeeded" ||
        !isIdentifier(value.project_id, PROJECT_ID_PATTERN) ||
        !isIdentifier(value.expected_revision, REVISION_ID_PATTERN) ||
        typeof value.resolution !== "string" ||
        !CONFLICT_RESOLUTIONS.has(value.resolution as ConflictResolution) ||
        !isGeneration(value.current_generation) ||
        value.conflict_state !== "none" ||
        typeof value.replayed !== "boolean"
    ) {
        return null;
    }
    return {
        request_id: requestId,
        project_id: value.project_id,
        expected_revision: value.expected_revision,
        resolution: value.resolution as ConflictResolution,
        current_generation: value.current_generation,
        conflict_state: "none",
        replayed: value.replayed,
    };
}

export function isContinuitySnapshotV2(
    value: AnyContinuitySnapshot,
): value is ContinuitySnapshotV2 {
    return value.schema_version === CONTINUITY_SNAPSHOT_V2_SCHEMA;
}

export function classifyRevisionChange(summary: string): RevisionChangeKind {
    const normalized = summary.trim().toLowerCase();
    if (/^(create|created|new|생성)/u.test(normalized)) return "created";
    if (/^(edit|edited|update|updated|수정|편집)/u.test(normalized))
        return "edited";
    if (/^(transform|transformed|convert|converted|변환)/u.test(normalized)) {
        return "transformed";
    }
    if (/^(validate|validated|verify|verified|검증)/u.test(normalized)) {
        return "validated";
    }
    if (/^(import|imported|upload|uploaded|가져오기)/u.test(normalized)) {
        return "imported";
    }
    return "unknown";
}

export { resolveHostTheme, resolveViewLocale };
export type { ClientSurface, HostTheme, ViewLocale };
