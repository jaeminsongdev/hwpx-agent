import type { GitApprovalState } from "./git-approval-controller.js";

function short(value: string): string {
    return `${value.slice(0, 12)}…${value.slice(-8)}`;
}

export function GitApprovalView({
    state,
    onAcknowledged,
    onConfirm,
}: {
    state: GitApprovalState;
    onAcknowledged: (value: boolean) => void;
    onConfirm: () => void;
}) {
    if (state.phase === "connecting" || state.phase === "approval_pending") {
        return (
            <main className="approval-shell centered" data-theme={state.theme}>
                <p role="status">Git 커밋 계획을 안전하게 불러오는 중입니다.</p>
            </main>
        );
    }
    if (state.phase === "closed") {
        return (
            <main className="approval-shell centered" data-theme={state.theme}>
                <p role="alert">
                    계획 정보를 신뢰할 수 없어 실행을 차단했습니다.
                </p>
            </main>
        );
    }
    const plan = state.plan;
    if (plan === null) return null;
    const finished = state.phase === "succeeded";
    const uncertain = state.phase === "unconfirmed";
    return (
        <main className="approval-shell" data-theme={state.theme}>
            <header>
                <div className="brand" aria-hidden="true">
                    H
                </div>
                <div>
                    <h1>로컬 Git 커밋 확인</h1>
                    <p>표시된 HWPX 출력 1개만 현재 브랜치에 커밋합니다.</p>
                </div>
                <span className="risk">로컬 변경</span>
            </header>
            <dl>
                <div>
                    <dt>작업공간</dt>
                    <dd>{plan.workspace_id}</dd>
                </div>
                <div>
                    <dt>출력</dt>
                    <dd>
                        <code>{plan.output_pathspec}</code>
                    </dd>
                </div>
                <div>
                    <dt>메시지</dt>
                    <dd>{plan.message}</dd>
                </div>
                <div>
                    <dt>현재 HEAD</dt>
                    <dd>
                        <code title={plan.expected_head}>
                            {short(plan.expected_head)}
                        </code>
                    </dd>
                </div>
                <div>
                    <dt>브랜치</dt>
                    <dd>
                        <code>
                            {plan.expected_head_reference ?? "detached HEAD"}
                        </code>
                    </dd>
                </div>
                <div>
                    <dt>출력 SHA-256</dt>
                    <dd>
                        <code title={plan.expected_output_sha256}>
                            {short(plan.expected_output_sha256)}
                        </code>
                    </dd>
                </div>
                <div>
                    <dt>계획 SHA-256</dt>
                    <dd>
                        <code title={plan.approval.plan_sha256}>
                            {short(plan.approval.plan_sha256)}
                        </code>
                    </dd>
                </div>
            </dl>
            <p className="notice">
                클릭 직후 서버가 HEAD·출력·계획을 다시 검증합니다. 달라졌으면
                아무것도 실행하지 않습니다.
            </p>
            {finished ? (
                <p className="success" role="status">
                    커밋 완료: <code>{short(state.receipt!.commit_oid)}</code>
                </p>
            ) : uncertain ? (
                <p className="error" role="alert">
                    결과를 확인할 수 없습니다. 이 화면에서는 다시 실행하지
                    않습니다.
                </p>
            ) : (
                <section className="confirmation">
                    <label>
                        <input
                            type="checkbox"
                            checked={state.acknowledged}
                            disabled={state.phase === "executing"}
                            onChange={(event) =>
                                onAcknowledged(event.currentTarget.checked)
                            }
                        />
                        위 경로·메시지·기준 HEAD를 확인했고 이 커밋 실행에
                        동의합니다.
                    </label>
                    <button
                        type="button"
                        disabled={
                            !state.acknowledged || state.phase === "executing"
                        }
                        onClick={onConfirm}
                    >
                        {state.phase === "executing"
                            ? "검증 및 실행 중…"
                            : "확인 후 Git 커밋"}
                    </button>
                </section>
            )}
        </main>
    );
}
