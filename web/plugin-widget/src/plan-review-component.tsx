import { useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
    PlanReviewController,
    type PlanReviewViewState,
} from "./plan-review-controller.js";
import { PlanReviewMcpAppPort } from "./plan-review-mcp-app-port.js";
import { PlanReviewView } from "./plan-review-ui.js";
import "./plan-review-styles.css";

const INITIAL: PlanReviewViewState = {
    phase: "connecting",
    mode: "view",
    locale: "ko-KR",
    theme: "light",
    snapshot: null,
    errorCode: null,
    actionPending: false,
    acknowledged: false,
    executionState: "none",
};
function requestId(): string {
    return `req_${crypto.randomUUID().replaceAll("-", "")}`;
}
function idempotencyKey(): string {
    return crypto.randomUUID();
}

function PlanReviewApplication() {
    const [state, setState] = useState(INITIAL);
    const [controller, setController] = useState<PlanReviewController | null>(
        null,
    );
    useEffect(() => {
        const next = new PlanReviewController(
            new PlanReviewMcpAppPort(),
            requestId,
            idempotencyKey,
        );
        const unsubscribe = next.subscribe(setState);
        setController(next);
        void next.start();
        return () => {
            unsubscribe();
            void next.close();
        };
    }, []);
    return (
        <PlanReviewView
            state={state}
            onBeginExecution={useCallback(
                () => controller?.beginExecution(),
                [controller],
            )}
            onCancelExecution={useCallback(
                () => controller?.cancelExecution(),
                [controller],
            )}
            onAcknowledged={useCallback(
                (value) => controller?.setAcknowledged(value),
                [controller],
            )}
            onConfirmExecution={useCallback(
                () => void controller?.confirmExecution(),
                [controller],
            )}
            onRevalidate={useCallback(
                () => void controller?.revalidate(),
                [controller],
            )}
        />
    );
}

const root = document.getElementById("root");
if (root === null) throw new Error("plan review root is missing");
createRoot(root).render(<PlanReviewApplication />);
