import type { ReactNode } from "react";

import type {
    CheckpointState,
    ContinuityErrorCode,
    ContinuityPhase,
    ContinuityViewState,
} from "./continuity-controller.js";
import {
    type ConflictState,
    type RevisionChangeKind,
} from "./continuity-model.js";
import { displayOpaqueId } from "./model.js";

type Copy = {
    product: string;
    surface: string;
    phase: Record<ContinuityPhase, string>;
    message: Record<ContinuityPhase, string>;
    project: string;
    head: string;
    warnings: string;
    history: string;
    noHistory: string;
    conflict: Record<ConflictState, string>;
    conflictMessage: Record<Exclude<ConflictState, "none">, string>;
    change: Record<RevisionChangeKind, string>;
    checkpoint: string;
    checkpointConfirm: string;
    checkpointSaved: Record<Exclude<CheckpointState, "none">, string>;
    createCheckpoint: string;
    confirmCreate: string;
    cancel: string;
    refresh: string;
    error: Record<ContinuityErrorCode, string>;
};

const COPY: Record<ContinuityViewState["locale"], Copy> = {
    "ko-KR": {
        product: "HWPX Agent",
        surface: "프로젝트 기록",
        phase: {
            connecting: "연결 중",
            approval_pending: "승인 대기",
            ready: "현재 상태",
            recoverable_error: "복구 필요",
            closed: "종료됨",
        },
        message: {
            connecting: "안전한 프로젝트 기록을 연결하고 있습니다.",
            approval_pending: "승인된 프로젝트 입력을 기다리고 있습니다.",
            ready: "현재 리비전과 최근 기록을 확인했습니다.",
            recoverable_error: "이 화면을 새로 열어 다시 시도해 주세요.",
            closed: "프로젝트 기록 연결이 종료되었습니다.",
        },
        project: "프로젝트",
        head: "현재 리비전",
        warnings: "주의 항목",
        history: "최근 리비전",
        noHistory: "표시할 리비전이 없습니다.",
        conflict: {
            none: "충돌 없음",
            locked: "잠금 확인 필요",
            stale: "새 상태 확인 필요",
            diverged: "리비전 분기 확인 필요",
        },
        conflictMessage: {
            locked: "다른 작업이 사용 중입니다. 새로고침 후 다시 확인하세요.",
            stale: "표시된 리비전이 최신이 아닙니다. 새로고침이 필요합니다.",
            diverged: "리비전이 갈라졌습니다. 쓰기 작업을 중지했습니다.",
        },
        change: {
            created: "생성",
            edited: "편집",
            transformed: "변환",
            validated: "검증",
            imported: "가져오기",
            unknown: "변경",
        },
        checkpoint: "체크포인트",
        checkpointConfirm: "현재 리비전에 변경 불가능한 체크포인트를 만들까요?",
        checkpointSaved: {
            saved: "체크포인트를 만들었습니다.",
            replayed: "동일 요청의 기존 체크포인트를 확인했습니다.",
        },
        createCheckpoint: "체크포인트 만들기",
        confirmCreate: "확인 후 만들기",
        cancel: "취소",
        refresh: "새로고침",
        error: {
            CONNECT_FAILED: "프로젝트 기록에 연결하지 못했습니다.",
            INVALID_TOOL_INPUT: "승인된 프로젝트 입력을 확인할 수 없습니다.",
            INVALID_TOOL_RESULT: "프로젝트 결과 형식이 안전하지 않습니다.",
            TOOL_CANCELLED: "요청이 취소되었습니다.",
            REFRESH_FAILED: "최신 프로젝트 기록을 확인하지 못했습니다.",
            CHECKPOINT_FAILED: "체크포인트를 만들지 못했습니다.",
        },
    },
    "en-US": {
        product: "HWPX Agent",
        surface: "Project history",
        phase: {
            connecting: "Connecting",
            approval_pending: "Approval pending",
            ready: "Current state",
            recoverable_error: "Recovery needed",
            closed: "Closed",
        },
        message: {
            connecting: "Connecting secure project history.",
            approval_pending: "Waiting for approved project input.",
            ready: "The current revision and recent history are available.",
            recoverable_error: "Open this view again to retry.",
            closed: "The project history connection is closed.",
        },
        project: "Project",
        head: "Current revision",
        warnings: "Warnings",
        history: "Recent revisions",
        noHistory: "No revisions are available.",
        conflict: {
            none: "No conflict",
            locked: "Lock review needed",
            stale: "Refresh needed",
            diverged: "Revision divergence",
        },
        conflictMessage: {
            locked: "Another operation holds the project. Refresh before continuing.",
            stale: "The displayed revision is stale. Refresh is required.",
            diverged: "The revision graph diverged. Write actions are stopped.",
        },
        change: {
            created: "Created",
            edited: "Edited",
            transformed: "Transformed",
            validated: "Validated",
            imported: "Imported",
            unknown: "Changed",
        },
        checkpoint: "Checkpoint",
        checkpointConfirm:
            "Create an immutable checkpoint on the current revision?",
        checkpointSaved: {
            saved: "Checkpoint created.",
            replayed: "The existing checkpoint for this request was confirmed.",
        },
        createCheckpoint: "Create checkpoint",
        confirmCreate: "Confirm and create",
        cancel: "Cancel",
        refresh: "Refresh",
        error: {
            CONNECT_FAILED: "Project history could not be connected.",
            INVALID_TOOL_INPUT: "Approved project input could not be verified.",
            INVALID_TOOL_RESULT:
                "The project result did not match the safe format.",
            TOOL_CANCELLED: "The request was cancelled.",
            REFRESH_FAILED: "Current project history could not be verified.",
            CHECKPOINT_FAILED: "The checkpoint could not be created.",
        },
    },
};

function Icon({ children }: { readonly children: ReactNode }) {
    return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            {children}
        </svg>
    );
}

function StatusIcon({ phase }: { readonly phase: ContinuityPhase }) {
    if (phase === "ready") {
        return (
            <Icon>
                <path d="M6 5h12v14H6zM9 9h6M9 13h4" />
                <path d="M4 8H2m20 0h-2M4 16H2m20 0h-2" />
            </Icon>
        );
    }
    if (phase === "connecting") {
        return (
            <Icon>
                <circle
                    className="continuity-spinner-track"
                    cx="12"
                    cy="12"
                    r="8"
                />
                <path
                    className="continuity-spinner-head"
                    d="M12 4a8 8 0 0 1 7.6 5.5"
                />
            </Icon>
        );
    }
    return (
        <Icon>
            <circle cx="12" cy="12" r="8" />
            <path d="M12 7.5v5.2M12 16h.01" />
        </Icon>
    );
}

function formatDate(
    value: string,
    locale: ContinuityViewState["locale"],
): string {
    const date = new Date(value);
    return new Intl.DateTimeFormat(locale, {
        year: "numeric",
        month: "short",
        day: "numeric",
        timeZone: "UTC",
    }).format(date);
}

export interface ContinuityViewProps {
    readonly state: ContinuityViewState;
    readonly onBeginCheckpoint: () => void;
    readonly onConfirmCheckpoint: () => void;
    readonly onCancelCheckpoint: () => void;
    readonly onRefresh: () => void;
}

export function ContinuityView({
    state,
    onBeginCheckpoint,
    onConfirmCheckpoint,
    onCancelCheckpoint,
    onRefresh,
}: ContinuityViewProps) {
    const copy = COPY[state.locale];
    const snapshot = state.snapshot;
    const error = state.phase === "recoverable_error";
    const message =
        error && state.errorCode !== null
            ? copy.error[state.errorCode]
            : copy.message[state.phase];
    const conflict = snapshot?.conflict_state ?? "none";
    const checkpointAllowed =
        state.phase === "ready" &&
        state.mode === "view" &&
        snapshot?.head_revision_id !== null &&
        conflict === "none";
    const refreshAllowed = state.phase === "ready" && state.mode === "view";

    return (
        <main
            className="continuity-shell"
            data-phase={state.phase}
            data-theme={state.theme}
            data-conflict={conflict}
            lang={state.locale}
            aria-busy={state.phase === "connecting" || state.actionPending}
        >
            <header className="continuity-header">
                <span className="continuity-product-mark" aria-hidden="true">
                    H
                </span>
                <span>{copy.product}</span>
                <span className="continuity-surface-label">{copy.surface}</span>
            </header>

            <section className="continuity-summary" aria-live="polite">
                <div className="continuity-status-mark">
                    <StatusIcon phase={state.phase} />
                </div>
                <div className="continuity-summary-copy">
                    <p className="continuity-state-label">
                        {copy.phase[state.phase]}
                    </p>
                    <h1>{message}</h1>
                </div>
                {snapshot !== null && (
                    <span className="continuity-conflict-pill">
                        {copy.conflict[conflict]}
                    </span>
                )}
            </section>

            {snapshot !== null && (
                <>
                    {conflict !== "none" && (
                        <aside className="continuity-conflict" role="alert">
                            <strong>{copy.conflict[conflict]}</strong>
                            <span>{copy.conflictMessage[conflict]}</span>
                        </aside>
                    )}

                    <section className="continuity-grid">
                        <dl
                            className="continuity-metadata"
                            aria-label={copy.project}
                        >
                            <div>
                                <dt>{copy.project}</dt>
                                <dd>{displayOpaqueId(snapshot.project_id)}</dd>
                            </div>
                            <div>
                                <dt>{copy.head}</dt>
                                <dd>
                                    {displayOpaqueId(snapshot.head_revision_id)}
                                </dd>
                            </div>
                            <div>
                                <dt>{copy.warnings}</dt>
                                <dd>
                                    {snapshot.warning_count.toLocaleString(
                                        state.locale,
                                    )}
                                </dd>
                            </div>
                        </dl>

                        <section
                            className="continuity-history"
                            aria-labelledby="history-heading"
                        >
                            <h2 id="history-heading">{copy.history}</h2>
                            {snapshot.revisions.length === 0 ? (
                                <p className="continuity-empty">
                                    {copy.noHistory}
                                </p>
                            ) : (
                                <ol>
                                    {snapshot.revisions
                                        .slice(0, 6)
                                        .map((revision) => (
                                            <li key={revision.revision_id}>
                                                <span
                                                    className="continuity-node"
                                                    aria-hidden="true"
                                                />
                                                <div>
                                                    <strong>
                                                        {
                                                            copy.change[
                                                                revision
                                                                    .change_kind
                                                            ]
                                                        }
                                                    </strong>
                                                    <span>
                                                        {displayOpaqueId(
                                                            revision.revision_id,
                                                        )}{" "}
                                                        ·{" "}
                                                        {formatDate(
                                                            revision.created_at,
                                                            state.locale,
                                                        )}
                                                    </span>
                                                </div>
                                            </li>
                                        ))}
                                </ol>
                            )}
                        </section>
                    </section>

                    {state.mode === "confirm_checkpoint" && (
                        <section
                            className="continuity-confirm"
                            aria-labelledby="checkpoint-heading"
                        >
                            <h2 id="checkpoint-heading">{copy.checkpoint}</h2>
                            <p>{copy.checkpointConfirm}</p>
                            <span>
                                {displayOpaqueId(snapshot.head_revision_id)}
                            </span>
                        </section>
                    )}

                    {state.checkpointState !== "none" && (
                        <p className="continuity-success" role="status">
                            {copy.checkpointSaved[state.checkpointState]}
                        </p>
                    )}
                </>
            )}

            {state.phase === "ready" && snapshot !== null && (
                <footer className="continuity-actions">
                    {state.mode === "confirm_checkpoint" ? (
                        <>
                            <button
                                type="button"
                                className="continuity-secondary"
                                onClick={onCancelCheckpoint}
                                disabled={state.actionPending}
                            >
                                {copy.cancel}
                            </button>
                            <button
                                type="button"
                                onClick={onConfirmCheckpoint}
                                disabled={state.actionPending}
                            >
                                {copy.confirmCreate}
                            </button>
                        </>
                    ) : conflict === "none" ? (
                        <>
                            <button
                                type="button"
                                className="continuity-secondary"
                                onClick={onRefresh}
                                disabled={
                                    !refreshAllowed || state.actionPending
                                }
                            >
                                {copy.refresh}
                            </button>
                            <button
                                type="button"
                                onClick={onBeginCheckpoint}
                                disabled={
                                    !checkpointAllowed || state.actionPending
                                }
                            >
                                {copy.createCheckpoint}
                            </button>
                        </>
                    ) : (
                        <button
                            type="button"
                            onClick={onRefresh}
                            disabled={!refreshAllowed || state.actionPending}
                        >
                            {copy.refresh}
                        </button>
                    )}
                </footer>
            )}
        </main>
    );
}
