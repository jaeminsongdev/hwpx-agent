import type { ReactNode } from "react";

import { displayOpaqueId, type ValidationState } from "./model.js";
import type {
    WidgetErrorCode,
    WidgetPhase,
    WidgetViewState,
} from "./bridge.js";

type Copy = {
    product: string;
    surface: string;
    state: Record<WidgetPhase, string>;
    message: Record<WidgetPhase, string>;
    project: string;
    revision: string;
    validation: string;
    validationValue: Record<ValidationState, string>;
    continue: string;
    retry: string;
    error: Record<WidgetErrorCode, string>;
};

const COPY: Record<WidgetViewState["locale"], Copy> = {
    "ko-KR": {
        product: "HWPX Agent",
        surface: "문서 작업",
        state: {
            connecting: "연결 중",
            approval_pending: "승인 대기",
            ready: "준비됨",
            recoverable_error: "복구 필요",
            closed: "종료됨",
        },
        message: {
            connecting: "안전한 작업 환경을 연결하고 있습니다.",
            approval_pending: "호스트의 승인된 작업 입력을 기다리고 있습니다.",
            ready: "현재 프로젝트 정보를 확인했습니다.",
            recoverable_error: "연결을 새로 시작하면 다시 시도할 수 있습니다.",
            closed: "이 작업 화면의 연결이 종료되었습니다.",
        },
        project: "프로젝트",
        revision: "현재 리비전",
        validation: "검증 상태",
        validationValue: {
            queued: "검증 대기",
            running: "검증 중",
            verified: "검증됨",
            partial: "부분 검증",
            failed: "검증 실패",
            unverified: "검증 전",
        },
        continue: "계속",
        retry: "다시 시도",
        error: {
            CONNECT_FAILED: "연결을 완료하지 못했습니다.",
            INVALID_TOOL_INPUT: "승인된 입력을 확인할 수 없습니다.",
            INVALID_TOOL_RESULT: "안전한 결과 형식이 아닙니다.",
            TOOL_CANCELLED: "작업이 취소되었습니다.",
            TOOL_CALL_FAILED: "프로젝트를 다시 열지 못했습니다.",
        },
    },
    "en-US": {
        product: "HWPX Agent",
        surface: "Document work",
        state: {
            connecting: "Connecting",
            approval_pending: "Approval pending",
            ready: "Ready",
            recoverable_error: "Recovery needed",
            closed: "Closed",
        },
        message: {
            connecting: "Connecting a safe work environment.",
            approval_pending: "Waiting for approved tool input from the host.",
            ready: "The current project information is available.",
            recoverable_error: "Start a fresh connection to try again.",
            closed: "This work view is no longer connected.",
        },
        project: "Project",
        revision: "Current revision",
        validation: "Validation",
        validationValue: {
            queued: "Validation queued",
            running: "Validating",
            verified: "Validated",
            partial: "Partially validated",
            failed: "Validation failed",
            unverified: "Not validated",
        },
        continue: "Continue",
        retry: "Retry",
        error: {
            CONNECT_FAILED: "The connection could not be completed.",
            INVALID_TOOL_INPUT: "Approved input could not be verified.",
            INVALID_TOOL_RESULT: "The result did not match the safe format.",
            TOOL_CANCELLED: "The operation was cancelled.",
            TOOL_CALL_FAILED: "The project could not be reopened.",
        },
    },
};

function IconFrame({ children }: { readonly children: ReactNode }) {
    return (
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            {children}
        </svg>
    );
}

export function StatusMark({ phase }: { readonly phase: WidgetPhase }) {
    if (phase === "connecting") {
        return (
            <IconFrame>
                <circle
                    className="status-spinner-track"
                    cx="12"
                    cy="12"
                    r="8"
                />
                <path
                    className="status-spinner-head"
                    d="M12 4a8 8 0 0 1 7.6 5.5"
                />
            </IconFrame>
        );
    }
    if (phase === "approval_pending") {
        return (
            <IconFrame>
                <circle cx="12" cy="12" r="8" />
                <path d="M12 7v5l3 2" />
            </IconFrame>
        );
    }
    if (phase === "ready") {
        return (
            <IconFrame>
                <path d="M7 3.8h7l3 3V20H7z" />
                <path d="M14 3.8V7h3M9.5 13l1.8 1.8 3.7-4" />
            </IconFrame>
        );
    }
    return (
        <IconFrame>
            <circle cx="12" cy="12" r="8" />
            <path d="M12 7.5v5.2M12 16h.01" />
        </IconFrame>
    );
}

function MetadataRows({
    state,
    copy,
}: {
    readonly state: WidgetViewState;
    readonly copy: Copy;
}) {
    const snapshot = state.snapshot;
    return (
        <dl className="metadata" aria-label={copy.validation}>
            <div>
                <dt>{copy.project}</dt>
                <dd>{displayOpaqueId(snapshot?.project_id ?? null)}</dd>
            </div>
            <div>
                <dt>{copy.revision}</dt>
                <dd>{displayOpaqueId(snapshot?.revision_id ?? null)}</dd>
            </div>
            <div>
                <dt>{copy.validation}</dt>
                <dd>
                    {snapshot === null
                        ? "—"
                        : copy.validationValue[snapshot.validation_state]}
                </dd>
            </div>
        </dl>
    );
}

export interface WidgetShellProps {
    readonly state: WidgetViewState;
    readonly onContinue: () => void;
    readonly onRetry: () => void;
}

export function WidgetShell({ state, onContinue, onRetry }: WidgetShellProps) {
    const copy = COPY[state.locale];
    const isError = state.phase === "recoverable_error";
    const canContinue =
        state.phase === "ready" &&
        state.snapshot !== null &&
        state.snapshot.project_id !== null;
    const message =
        isError && state.errorCode !== null
            ? copy.error[state.errorCode]
            : copy.message[state.phase];
    return (
        <main
            className="widget-shell"
            data-phase={state.phase}
            data-theme={state.theme}
            lang={state.locale}
            aria-busy={state.phase === "connecting" || state.actionPending}
        >
            <header className="widget-header">
                <span className="product-mark" aria-hidden="true">
                    H
                </span>
                <span>{copy.product}</span>
                <span className="surface-label">{copy.surface}</span>
            </header>
            <section className="widget-body" aria-live="polite">
                <div className="state-summary">
                    <div className="status-mark">
                        <StatusMark phase={state.phase} />
                    </div>
                    <div>
                        <p className="state-label">{copy.state[state.phase]}</p>
                        <h1>{message}</h1>
                    </div>
                </div>
                <MetadataRows state={state} copy={copy} />
            </section>
            {(canContinue || isError) && (
                <footer className="widget-footer">
                    <button
                        type="button"
                        onClick={isError ? onRetry : onContinue}
                        disabled={
                            !isError && (!canContinue || state.actionPending)
                        }
                    >
                        {isError ? copy.retry : copy.continue}
                    </button>
                </footer>
            )}
        </main>
    );
}
