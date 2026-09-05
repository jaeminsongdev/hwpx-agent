import type {
    DiffKind,
    PlanReviewSnapshot,
    PlanWarning,
    RiskLevel,
    SelectedBackend,
} from "./plan-review-model.js";
import type {
    PlanReviewErrorCode,
    PlanReviewViewState,
} from "./plan-review-controller.js";

interface Copy {
    title: string;
    subtitle: string;
    base: string;
    route: string;
    diff: string;
    warnings: string;
    added: string;
    modified: string;
    removed: string;
    review: string;
    revalidate: string;
    cancel: string;
    acknowledge: string;
    execute: string;
    blocked: string;
    connecting: string;
    approval: string;
    failed: string;
    revalidated: string;
    submitted: string;
    committed: string;
    noWarnings: string;
}

const COPY: Record<"ko-KR" | "en-US", Copy> = {
    "ko-KR": {
        title: "변경 계획 검토",
        subtitle: "실행 전 기능 경로와 의미 단위 변경을 확인하세요.",
        base: "기준 리비전",
        route: "기능 경로",
        diff: "의미 단위 변경",
        warnings: "주의 사항",
        added: "추가",
        modified: "수정",
        removed: "삭제",
        review: "실행 검토",
        revalidate: "계획 다시 검증",
        cancel: "취소",
        acknowledge: "위험과 변경 범위를 확인했으며 실행에 동의합니다.",
        execute: "확인 후 실행",
        blocked: "현재 계획은 실행할 수 없습니다.",
        connecting: "안전한 검토 화면을 연결하는 중입니다.",
        approval: "서버에서 승인된 계획 결과를 기다리고 있습니다.",
        failed: "계획 정보를 신뢰할 수 없어 닫았습니다.",
        revalidated: "계획과 기능 경로를 다시 검증했습니다.",
        submitted: "검증된 작업을 제출했습니다.",
        committed: "새 리비전을 만들었습니다.",
        noWarnings: "추가 경고가 없습니다.",
    },
    "en-US": {
        title: "Review change plan",
        subtitle:
            "Review capability routing and semantic changes before execution.",
        base: "Base revision",
        route: "Capability route",
        diff: "Semantic changes",
        warnings: "Warnings",
        added: "Added",
        modified: "Modified",
        removed: "Removed",
        review: "Review execution",
        revalidate: "Revalidate plan",
        cancel: "Cancel",
        acknowledge:
            "I understand the risk and change scope and agree to execute.",
        execute: "Confirm and execute",
        blocked: "This plan cannot be executed.",
        connecting: "Connecting the secure review surface.",
        approval: "Waiting for an approved plan result from the server.",
        failed: "Plan data was not trustworthy, so the view was closed.",
        revalidated: "The plan and capability route were revalidated.",
        submitted: "The validated job was submitted.",
        committed: "A new revision was created.",
        noWarnings: "No additional warnings.",
    },
};

const RISK: Record<RiskLevel, { ko: string; en: string }> = {
    low: { ko: "낮은 위험", en: "Low risk" },
    medium: { ko: "중간 위험", en: "Medium risk" },
    high: { ko: "고위험", en: "High risk" },
};
const BACKEND: Record<SelectedBackend, { ko: string; en: string }> = {
    direct_hwpx: { ko: "HWPX 직접", en: "Direct HWPX" },
    hancom_2020: { ko: "한글 2020", en: "Hangul 2020" },
    hybrid: { ko: "혼합 경로", en: "Hybrid" },
    none: { ko: "사용 불가", en: "Unavailable" },
};
const KIND: Record<DiffKind, { ko: string; en: string }> = {
    paragraph: { ko: "문단", en: "Paragraph" },
    table: { ko: "표", en: "Table" },
    style: { ko: "스타일", en: "Style" },
    image: { ko: "이미지", en: "Image" },
    field: { ko: "필드", en: "Field" },
    section: { ko: "구역", en: "Section" },
    metadata: { ko: "메타데이터", en: "Metadata" },
    other: { ko: "기타", en: "Other" },
};

function shortId(value: string): string {
    return `${value.slice(0, 10)}…`;
}
function warningText(item: PlanWarning, korean: boolean): string {
    const map: Record<PlanWarning["kind"], [string, string]> = {
        validation: [
            "추가 검증이 필요한 변경입니다.",
            "This change needs additional validation.",
        ],
        preservation: [
            "보존 범위를 다시 확인해야 합니다.",
            "The preservation boundary needs review.",
        ],
        layout: [
            "레이아웃에 문서 전체 영향이 있을 수 있습니다.",
            "Layout may have document-wide impact.",
        ],
        signature: [
            "서명 보존을 확인할 수 없습니다.",
            "Signature preservation is not confirmed.",
        ],
        permission: [
            "실행 권한을 다시 확인해야 합니다.",
            "Execution permission needs revalidation.",
        ],
        other: [
            "서버가 검토 필요 항목으로 분류했습니다.",
            "The server classified this item for review.",
        ],
    };
    return map[item.kind][korean ? 0 : 1];
}
function errorText(_code: PlanReviewErrorCode | null, copy: Copy): string {
    return copy.failed;
}

function SpinnerState({
    state,
    copy,
}: {
    state: PlanReviewViewState;
    copy: Copy;
}) {
    const text =
        state.phase === "connecting"
            ? copy.connecting
            : state.phase === "approval_pending"
              ? copy.approval
              : errorText(state.errorCode, copy);
    return (
        <main className="plan-shell plan-centered" data-theme={state.theme}>
            <div
                className="plan-state"
                role={state.phase === "recoverable_error" ? "alert" : "status"}
            >
                <span className="plan-spinner" aria-hidden="true" />
                {text}
            </div>
        </main>
    );
}

function Route({
    snapshot,
    korean,
}: {
    snapshot: PlanReviewSnapshot;
    korean: boolean;
}) {
    return (
        <section className="plan-section" aria-labelledby="route-title">
            <div className="section-heading">
                <h2 id="route-title">
                    {COPY[korean ? "ko-KR" : "en-US"].route}
                </h2>
                <code>{snapshot.route_digest.slice(0, 8)}</code>
            </div>
            <ol className="route-list">
                {snapshot.route.map((item, index) => (
                    <li
                        key={item.capability_id}
                        className={`route-item route-${item.support_level}`}
                    >
                        <span className="route-index">{index + 1}</span>
                        <span className="route-copy">
                            <strong>{item.capability_id}</strong>
                            <small>
                                {
                                    BACKEND[item.selected_backend][
                                        korean ? "ko" : "en"
                                    ]
                                }
                            </small>
                        </span>
                        <span className="route-state">
                            {item.support_level}
                        </span>
                    </li>
                ))}
            </ol>
        </section>
    );
}

function Diff({
    snapshot,
    copy,
    korean,
}: {
    snapshot: PlanReviewSnapshot;
    copy: Copy;
    korean: boolean;
}) {
    return (
        <section className="plan-section" aria-labelledby="diff-title">
            <div className="section-heading">
                <h2 id="diff-title">{copy.diff}</h2>
                <span>
                    {snapshot.estimated_page_effect.replaceAll("_", " ")}
                </span>
            </div>
            <div className="diff-stats">
                <div className="diff-card added">
                    <span>{copy.added}</span>
                    <strong>{snapshot.diff.added}</strong>
                </div>
                <div className="diff-card modified">
                    <span>{copy.modified}</span>
                    <strong>{snapshot.diff.modified}</strong>
                </div>
                <div className="diff-card removed">
                    <span>{copy.removed}</span>
                    <strong>{snapshot.diff.removed}</strong>
                </div>
            </div>
            {snapshot.diff.categories.length > 0 && (
                <ul className="category-list">
                    {snapshot.diff.categories.map((item) => (
                        <li key={item.kind}>
                            <span>{KIND[item.kind][korean ? "ko" : "en"]}</span>
                            <strong>{item.count}</strong>
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}

function Warnings({
    snapshot,
    copy,
    korean,
}: {
    snapshot: PlanReviewSnapshot;
    copy: Copy;
    korean: boolean;
}) {
    return (
        <section
            className="plan-section warning-section"
            aria-labelledby="warning-title"
        >
            <div className="section-heading">
                <h2 id="warning-title">{copy.warnings}</h2>
                <span>{snapshot.warnings.length}</span>
            </div>
            {snapshot.warnings.length === 0 ? (
                <p className="empty-warning">{copy.noWarnings}</p>
            ) : (
                <ul className="warning-list">
                    {snapshot.warnings.map((item) => (
                        <li
                            key={item.code}
                            className={`warning-${item.severity}`}
                            role={
                                item.severity === "blocking"
                                    ? "alert"
                                    : undefined
                            }
                        >
                            <span className="warning-mark" aria-hidden="true">
                                !
                            </span>
                            <span>
                                <strong>{item.code}</strong>
                                <small>{warningText(item, korean)}</small>
                            </span>
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}

export function PlanReviewView({
    state,
    onBeginExecution,
    onCancelExecution,
    onAcknowledged,
    onConfirmExecution,
    onRevalidate,
}: {
    state: PlanReviewViewState;
    onBeginExecution: () => void;
    onCancelExecution: () => void;
    onAcknowledged: (value: boolean) => void;
    onConfirmExecution: () => void;
    onRevalidate: () => void;
}) {
    const copy = COPY[state.locale];
    if (state.phase !== "ready" || state.snapshot === null)
        return <SpinnerState state={state} copy={copy} />;
    const snapshot = state.snapshot;
    const korean = state.locale === "ko-KR";
    const status =
        state.executionState === "revalidated"
            ? copy.revalidated
            : state.executionState === "submitted"
              ? copy.submitted
              : state.executionState === "committed"
                ? copy.committed
                : null;
    return (
        <main className="plan-shell" data-theme={state.theme}>
            <header className="plan-header">
                <div className="plan-brand">
                    <span className="plan-logo" aria-hidden="true">
                        H
                    </span>
                    <div>
                        <h1>{copy.title}</h1>
                        <p>{copy.subtitle}</p>
                    </div>
                </div>
                <span className={`risk-badge risk-${snapshot.risk_level}`}>
                    {RISK[snapshot.risk_level][korean ? "ko" : "en"]}
                </span>
            </header>
            <div className="base-row">
                <span>{copy.base}</span>
                <code>{shortId(snapshot.source_revision_id)}</code>
                <span
                    className="lock"
                    aria-label={korean ? "고정됨" : "Locked"}
                >
                    ●
                </span>
                <span className="plan-id">{shortId(snapshot.plan_id)}</span>
            </div>
            <div className="plan-grid">
                <Route snapshot={snapshot} korean={korean} />
                <Diff snapshot={snapshot} copy={copy} korean={korean} />
            </div>
            <Warnings snapshot={snapshot} copy={copy} korean={korean} />
            {status !== null && (
                <p className="action-status" role="status">
                    {status}
                </p>
            )}
            {!snapshot.execution_allowed && (
                <p className="blocked-message" role="alert">
                    {copy.blocked}
                </p>
            )}
            {state.mode === "confirm_execution" ? (
                <div className={`confirmation risk-${snapshot.risk_level}`}>
                    <label className="acknowledgement">
                        <input
                            type="checkbox"
                            checked={state.acknowledged}
                            onChange={(event) =>
                                onAcknowledged(event.currentTarget.checked)
                            }
                            disabled={state.actionPending}
                        />
                        <span>{copy.acknowledge}</span>
                    </label>
                    <div className="action-row">
                        <button
                            className="secondary"
                            type="button"
                            onClick={onCancelExecution}
                            disabled={state.actionPending}
                        >
                            {copy.cancel}
                        </button>
                        <button
                            className="danger"
                            type="button"
                            onClick={onConfirmExecution}
                            disabled={
                                !state.acknowledged || state.actionPending
                            }
                        >
                            {state.actionPending ? "…" : copy.execute}
                        </button>
                    </div>
                </div>
            ) : (
                <div className="action-row">
                    <button
                        className="secondary"
                        type="button"
                        onClick={onRevalidate}
                        disabled={state.actionPending}
                    >
                        {state.actionPending ? "…" : copy.revalidate}
                    </button>
                    <button
                        className="primary"
                        type="button"
                        onClick={onBeginExecution}
                        disabled={
                            state.actionPending || !snapshot.execution_allowed
                        }
                    >
                        {copy.review}
                    </button>
                </div>
            )}
        </main>
    );
}
