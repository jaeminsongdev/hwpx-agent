import {
    resolveHostTheme,
    resolveViewLocale,
    type ClientSurface,
    type HostTheme,
    type ViewLocale,
} from "./model.js";

export const PLAN_REVIEW_REQUEST_SCHEMA =
    "hwpx-agent.plan-review-render-request/v1" as const;
export const PLAN_REVIEW_SNAPSHOT_SCHEMA = "hwpx-agent.plan-review/v1" as const;
export const PUBLIC_RESULT_SCHEMA = "hwpx-agent.tool-result/v1" as const;

export type RiskLevel = "low" | "medium" | "high";
export type SupportLevel =
    "verified" | "partial" | "unverified" | "unsupported";
export type SelectedBackend = "direct_hwpx" | "hancom_2020" | "hybrid" | "none";
export type PageEffect = "none" | "local" | "document_wide" | "unknown";
export type SignatureImpact = "none" | "invalidates" | "unknown";
export type DryRunState = "verified" | "partial" | "failed" | "not_run";
export type WarningSeverity = "notice" | "warning" | "blocking";
export type WarningKind =
    | "validation"
    | "preservation"
    | "layout"
    | "signature"
    | "permission"
    | "other";
export type DiffKind =
    | "paragraph"
    | "table"
    | "style"
    | "image"
    | "field"
    | "section"
    | "metadata"
    | "other";

export interface PlanReviewRenderRequest {
    readonly schema_version: typeof PLAN_REVIEW_REQUEST_SCHEMA;
    readonly client_surface: ClientSurface;
    readonly locale: string;
    readonly project_id: string;
    readonly source_revision_id: string;
    readonly plan_id: string;
}

export interface CapabilityRoute {
    readonly capability_id: string;
    readonly selected_backend: SelectedBackend;
    readonly support_level: SupportLevel;
    readonly supported: boolean;
}

export interface DiffCategory {
    readonly kind: DiffKind;
    readonly count: number;
}

export interface PlanWarning {
    readonly code: string;
    readonly severity: WarningSeverity;
    readonly kind: WarningKind;
}

export interface PlanReviewSnapshot {
    readonly schema_version: typeof PLAN_REVIEW_SNAPSHOT_SCHEMA;
    readonly client_surface: ClientSurface;
    readonly locale: string;
    readonly project_id: string;
    readonly source_revision_id: string;
    readonly plan_id: string;
    readonly risk_level: RiskLevel;
    readonly estimated_page_effect: PageEffect;
    readonly route: readonly CapabilityRoute[];
    readonly route_digest: string;
    readonly diff: {
        readonly added: number;
        readonly modified: number;
        readonly removed: number;
        readonly categories: readonly DiffCategory[];
    };
    readonly warnings: readonly PlanWarning[];
    readonly signature_impact: SignatureImpact;
    readonly dry_run_state: DryRunState;
    readonly execution_allowed: boolean;
}

export interface CapabilityCheckResult {
    readonly request_id: string;
    readonly capabilities: readonly CapabilityRoute[];
    readonly warning_codes: readonly string[];
    readonly detail_count: number;
}

export interface DocumentEditResult {
    readonly request_id: string;
    readonly outcome: "accepted" | "succeeded";
    readonly job_id: string | null;
    readonly revision_id: string | null;
    readonly commit_state: "not_started" | "pending" | "committed";
    readonly validation_state: "not_run" | "verified" | "partial" | "failed";
    readonly warning_codes: readonly string[];
}

const CLIENT_SURFACES = new Set<ClientSurface>([
    "chatgpt_web",
    "codex_remote",
    "codex_local",
]);
const RISK_LEVELS = new Set<RiskLevel>(["low", "medium", "high"]);
const SUPPORT_LEVELS = new Set<SupportLevel>([
    "verified",
    "partial",
    "unverified",
    "unsupported",
]);
const BACKENDS = new Set<SelectedBackend>([
    "direct_hwpx",
    "hancom_2020",
    "hybrid",
    "none",
]);
const PAGE_EFFECTS = new Set<PageEffect>([
    "none",
    "local",
    "document_wide",
    "unknown",
]);
const SIGNATURE_IMPACTS = new Set<SignatureImpact>([
    "none",
    "invalidates",
    "unknown",
]);
const DRY_RUN_STATES = new Set<DryRunState>([
    "verified",
    "partial",
    "failed",
    "not_run",
]);
const WARNING_SEVERITIES = new Set<WarningSeverity>([
    "notice",
    "warning",
    "blocking",
]);
const WARNING_KINDS = new Set<WarningKind>([
    "validation",
    "preservation",
    "layout",
    "signature",
    "permission",
    "other",
]);
const DIFF_KINDS = new Set<DiffKind>([
    "paragraph",
    "table",
    "style",
    "image",
    "field",
    "section",
    "metadata",
    "other",
]);
const PROJECT_ID = /^prj_[A-Za-z0-9_-]{8,120}$/;
const REVISION_ID = /^rev_[A-Za-z0-9_-]{8,120}$/;
const PLAN_ID = /^plan_[A-Za-z0-9_-]{8,120}$/;
const REQUEST_ID = /^req_[A-Za-z0-9_-]{8,120}$/;
const JOB_ID = /^job_[A-Za-z0-9_-]{8,120}$/;
const CAPABILITY_ID = /^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$/;
const WARNING_CODE = /^[A-Z][A-Z0-9_]{2,95}$/;
const SHA256 = /^[0-9a-f]{64}$/;
const LOCALE = /^[a-z]{2,3}(?:-[A-Z][a-z]{3})?(?:-[A-Z]{2}|-[0-9]{3})?$/;

function record(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exact(
    value: Record<string, unknown>,
    keys: readonly string[],
): boolean {
    const actual = Object.keys(value).sort();
    const expected = [...keys].sort();
    return (
        actual.length === expected.length &&
        actual.every((key, index) => key === expected[index])
    );
}

function identifier(value: unknown, pattern: RegExp): value is string {
    return typeof value === "string" && pattern.test(value);
}

function boundedInteger(value: unknown, maximum = 100_000): value is number {
    return (
        Number.isInteger(value) &&
        (value as number) >= 0 &&
        (value as number) <= maximum
    );
}

function parseRoute(value: unknown): CapabilityRoute | null {
    if (
        !record(value) ||
        !exact(value, [
            "capability_id",
            "selected_backend",
            "support_level",
            "supported",
        ])
    )
        return null;
    if (
        !identifier(value.capability_id, CAPABILITY_ID) ||
        typeof value.selected_backend !== "string" ||
        !BACKENDS.has(value.selected_backend as SelectedBackend) ||
        typeof value.support_level !== "string" ||
        !SUPPORT_LEVELS.has(value.support_level as SupportLevel) ||
        typeof value.supported !== "boolean"
    )
        return null;
    const supported = value.supported;
    const supportLevel = value.support_level as SupportLevel;
    const backend = value.selected_backend as SelectedBackend;
    if (
        supported !== (supportLevel !== "unsupported") ||
        (supported && backend === "none") ||
        (!supported && backend !== "none")
    )
        return null;
    return {
        capability_id: value.capability_id,
        selected_backend: backend,
        support_level: supportLevel,
        supported,
    };
}

function parseDiffCategory(value: unknown): DiffCategory | null {
    if (!record(value) || !exact(value, ["kind", "count"])) return null;
    if (
        typeof value.kind !== "string" ||
        !DIFF_KINDS.has(value.kind as DiffKind) ||
        !boundedInteger(value.count)
    )
        return null;
    return { kind: value.kind as DiffKind, count: value.count as number };
}

function parseWarning(value: unknown): PlanWarning | null {
    if (!record(value) || !exact(value, ["code", "severity", "kind"]))
        return null;
    if (
        !identifier(value.code, WARNING_CODE) ||
        typeof value.severity !== "string" ||
        !WARNING_SEVERITIES.has(value.severity as WarningSeverity) ||
        typeof value.kind !== "string" ||
        !WARNING_KINDS.has(value.kind as WarningKind)
    )
        return null;
    return {
        code: value.code,
        severity: value.severity as WarningSeverity,
        kind: value.kind as WarningKind,
    };
}

export function parsePlanReviewRenderRequest(
    value: unknown,
): PlanReviewRenderRequest | null {
    if (
        !record(value) ||
        !exact(value, [
            "schema_version",
            "client_surface",
            "locale",
            "project_id",
            "source_revision_id",
            "plan_id",
        ])
    )
        return null;
    if (
        value.schema_version !== PLAN_REVIEW_REQUEST_SCHEMA ||
        typeof value.client_surface !== "string" ||
        !CLIENT_SURFACES.has(value.client_surface as ClientSurface) ||
        typeof value.locale !== "string" ||
        !LOCALE.test(value.locale) ||
        !identifier(value.project_id, PROJECT_ID) ||
        !identifier(value.source_revision_id, REVISION_ID) ||
        !identifier(value.plan_id, PLAN_ID)
    )
        return null;
    return value as unknown as PlanReviewRenderRequest;
}

export function parsePlanReviewSnapshot(
    value: unknown,
): PlanReviewSnapshot | null {
    if (
        !record(value) ||
        !exact(value, [
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
        ])
    )
        return null;
    if (
        value.schema_version !== PLAN_REVIEW_SNAPSHOT_SCHEMA ||
        typeof value.client_surface !== "string" ||
        !CLIENT_SURFACES.has(value.client_surface as ClientSurface) ||
        typeof value.locale !== "string" ||
        !LOCALE.test(value.locale) ||
        !identifier(value.project_id, PROJECT_ID) ||
        !identifier(value.source_revision_id, REVISION_ID) ||
        !identifier(value.plan_id, PLAN_ID) ||
        typeof value.risk_level !== "string" ||
        !RISK_LEVELS.has(value.risk_level as RiskLevel) ||
        typeof value.estimated_page_effect !== "string" ||
        !PAGE_EFFECTS.has(value.estimated_page_effect as PageEffect) ||
        !Array.isArray(value.route) ||
        value.route.length < 1 ||
        value.route.length > 12 ||
        !identifier(value.route_digest, SHA256) ||
        !record(value.diff) ||
        !exact(value.diff, ["added", "modified", "removed", "categories"]) ||
        !boundedInteger(value.diff.added) ||
        !boundedInteger(value.diff.modified) ||
        !boundedInteger(value.diff.removed) ||
        !Array.isArray(value.diff.categories) ||
        value.diff.categories.length > 8 ||
        !Array.isArray(value.warnings) ||
        value.warnings.length > 8 ||
        typeof value.signature_impact !== "string" ||
        !SIGNATURE_IMPACTS.has(value.signature_impact as SignatureImpact) ||
        typeof value.dry_run_state !== "string" ||
        !DRY_RUN_STATES.has(value.dry_run_state as DryRunState) ||
        typeof value.execution_allowed !== "boolean"
    )
        return null;
    const route = value.route.map(parseRoute);
    const categories = value.diff.categories.map(parseDiffCategory);
    const warnings = value.warnings.map(parseWarning);
    if (
        route.some((item) => item === null) ||
        categories.some((item) => item === null) ||
        warnings.some((item) => item === null)
    )
        return null;
    const routeIds = route.map((item) => item!.capability_id);
    const categoryKinds = categories.map((item) => item!.kind);
    const warningCodes = warnings.map((item) => item!.code);
    if (
        new Set(routeIds).size !== routeIds.length ||
        new Set(categoryKinds).size !== categoryKinds.length ||
        new Set(warningCodes).size !== warningCodes.length
    )
        return null;
    const canExecute =
        route.every(
            (item) =>
                item!.supported &&
                (item!.support_level === "verified" ||
                    item!.support_level === "partial"),
        ) &&
        value.signature_impact === "none" &&
        value.dry_run_state === "verified" &&
        warnings.every((item) => item!.severity !== "blocking");
    if (value.execution_allowed !== canExecute) return null;
    return {
        ...(value as unknown as PlanReviewSnapshot),
        route: route as CapabilityRoute[],
        diff: {
            added: value.diff.added as number,
            modified: value.diff.modified as number,
            removed: value.diff.removed as number,
            categories: categories as DiffCategory[],
        },
        warnings: warnings as PlanWarning[],
    };
}

function parsePublicBase(
    value: Record<string, unknown>,
    extras: readonly string[],
): { request_id: string; warning_codes: string[] } | null {
    if (
        !exact(value, [
            "schema_version",
            "request_id",
            "outcome",
            "safe_summary",
            "warnings",
            ...extras,
        ])
    )
        return null;
    if (
        value.schema_version !== PUBLIC_RESULT_SCHEMA ||
        !identifier(value.request_id, REQUEST_ID) ||
        typeof value.outcome !== "string" ||
        !["accepted", "succeeded", "partial", "unverified"].includes(
            value.outcome,
        ) ||
        typeof value.safe_summary !== "string" ||
        value.safe_summary.length < 1 ||
        value.safe_summary.length > 1000 ||
        !Array.isArray(value.warnings) ||
        value.warnings.length > 64
    )
        return null;
    for (const warning of value.warnings) {
        if (
            !record(warning) ||
            !exact(warning, ["code", "message"]) ||
            !identifier(warning.code, WARNING_CODE) ||
            typeof warning.message !== "string" ||
            warning.message.length < 1 ||
            warning.message.length > 1000
        )
            return null;
    }
    const warningCodes = value.warnings.map(
        (warning) => (warning as Record<string, unknown>).code as string,
    );
    if (new Set(warningCodes).size !== warningCodes.length) return null;
    return { request_id: value.request_id, warning_codes: warningCodes };
}

export function parseCapabilityCheckResult(
    value: unknown,
): CapabilityCheckResult | null {
    if (!record(value)) return null;
    const base = parsePublicBase(value, ["capabilities"]);
    if (
        base === null ||
        value.outcome !== "succeeded" ||
        !Array.isArray(value.capabilities) ||
        value.capabilities.length < 1 ||
        value.capabilities.length > 128
    )
        return null;
    const routes: CapabilityRoute[] = [];
    let detailCount = 0;
    for (const candidate of value.capabilities) {
        if (
            !record(candidate) ||
            !exact(candidate, [
                "capability_id",
                "supported",
                "support_level",
                "selected_backend",
                "estimated_job_class",
                "constraints",
                "unverified_reasons",
            ])
        )
            return null;
        const route = parseRoute({
            capability_id: candidate.capability_id,
            supported: candidate.supported,
            support_level: candidate.support_level,
            selected_backend: candidate.selected_backend,
        });
        if (
            route === null ||
            typeof candidate.estimated_job_class !== "string" ||
            !["inline", "short", "long", "unavailable"].includes(
                candidate.estimated_job_class,
            ) ||
            !Array.isArray(candidate.constraints) ||
            candidate.constraints.length > 32 ||
            !Array.isArray(candidate.unverified_reasons) ||
            candidate.unverified_reasons.length > 32
        )
            return null;
        if (
            ![...candidate.constraints, ...candidate.unverified_reasons].every(
                (item) =>
                    typeof item === "string" &&
                    item.length >= 1 &&
                    item.length <= 500,
            )
        )
            return null;
        detailCount +=
            candidate.constraints.length + candidate.unverified_reasons.length;
        routes.push(route);
    }
    if (
        new Set(routes.map((item) => item.capability_id)).size !== routes.length
    )
        return null;
    return {
        request_id: base.request_id,
        capabilities: routes,
        warning_codes: base.warning_codes,
        detail_count: detailCount,
    };
}

export function parseDocumentEditResult(
    value: unknown,
): DocumentEditResult | null {
    if (!record(value)) return null;
    const base = parsePublicBase(value, [
        "job_id",
        "revision_id",
        "artifact",
        "commit_state",
        "validation_state",
    ]);
    if (
        base === null ||
        (value.outcome !== "accepted" && value.outcome !== "succeeded") ||
        !(value.job_id === null || identifier(value.job_id, JOB_ID)) ||
        !(
            value.revision_id === null ||
            identifier(value.revision_id, REVISION_ID)
        ) ||
        value.artifact !== null ||
        typeof value.commit_state !== "string" ||
        !["not_started", "pending", "committed"].includes(value.commit_state) ||
        typeof value.validation_state !== "string" ||
        !["not_run", "verified", "partial", "failed"].includes(
            value.validation_state,
        )
    )
        return null;
    return {
        request_id: base.request_id,
        outcome: value.outcome,
        job_id: value.job_id as string | null,
        revision_id: value.revision_id as string | null,
        commit_state: value.commit_state as DocumentEditResult["commit_state"],
        validation_state:
            value.validation_state as DocumentEditResult["validation_state"],
        warning_codes: base.warning_codes,
    };
}

export function routeMatches(
    expected: readonly CapabilityRoute[],
    actual: readonly CapabilityRoute[],
): boolean {
    if (expected.length !== actual.length) return false;
    const byId = new Map(actual.map((item) => [item.capability_id, item]));
    return expected.every((item) => {
        const found = byId.get(item.capability_id);
        return (
            found !== undefined &&
            found.supported === item.supported &&
            found.support_level === item.support_level &&
            found.selected_backend === item.selected_backend
        );
    });
}

export function isVerifiedDryRun(result: DocumentEditResult): boolean {
    return (
        result.outcome === "succeeded" &&
        result.job_id === null &&
        result.revision_id === null &&
        result.commit_state === "not_started" &&
        result.validation_state === "verified"
    );
}

export function isAcceptedExecution(result: DocumentEditResult): boolean {
    return (
        (result.outcome === "accepted" &&
            result.job_id !== null &&
            result.revision_id === null &&
            result.commit_state === "pending" &&
            result.validation_state === "not_run") ||
        (result.outcome === "succeeded" &&
            result.revision_id !== null &&
            result.commit_state === "committed" &&
            (result.validation_state === "verified" ||
                result.validation_state === "partial"))
    );
}

export function warningsCovered(
    approved: readonly PlanWarning[],
    observedCodes: readonly string[],
): boolean {
    const approvedCodes = new Set(approved.map((item) => item.code));
    return observedCodes.every((code) => approvedCodes.has(code));
}

export { resolveHostTheme, resolveViewLocale };
export type { ClientSurface, HostTheme, ViewLocale };
