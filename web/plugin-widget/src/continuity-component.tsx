import { useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import {
    ContinuityController,
    type ContinuityViewState,
} from "./continuity-controller.js";
import { ContinuityMcpAppPort } from "./continuity-mcp-app-port.js";
import { ContinuityView } from "./continuity-ui.js";
import "./continuity-styles.css";

const INITIAL_STATE: ContinuityViewState = {
    phase: "connecting",
    mode: "view",
    locale: "ko-KR",
    theme: "light",
    snapshot: null,
    errorCode: null,
    actionPending: false,
    checkpointState: "none",
    selectedResolution: null,
    resolutionState: "none",
};

function requestId(): string {
    return `req_${crypto.randomUUID().replaceAll("-", "")}`;
}

function idempotencyKey(): string {
    return crypto.randomUUID();
}

function ContinuityApplication() {
    const [state, setState] = useState<ContinuityViewState>(INITIAL_STATE);
    const [controller, setController] = useState<ContinuityController | null>(
        null,
    );

    useEffect(() => {
        const next = new ContinuityController(
            new ContinuityMcpAppPort(),
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

    const onBeginCheckpoint = useCallback(
        () => controller?.beginCheckpoint(),
        [controller],
    );
    const onConfirmCheckpoint = useCallback(
        () => void controller?.confirmCheckpoint(),
        [controller],
    );
    const onCancelCheckpoint = useCallback(
        () => controller?.cancelCheckpoint(),
        [controller],
    );
    const onRefresh = useCallback(
        () => void controller?.refresh(),
        [controller],
    );
    const onBeginResolution = useCallback(
        (resolution: Parameters<ContinuityController["beginResolution"]>[0]) =>
            controller?.beginResolution(resolution),
        [controller],
    );
    const onConfirmResolution = useCallback(
        () => void controller?.confirmResolution(),
        [controller],
    );
    const onCancelResolution = useCallback(
        () => controller?.cancelResolution(),
        [controller],
    );

    return (
        <ContinuityView
            state={state}
            onBeginCheckpoint={onBeginCheckpoint}
            onConfirmCheckpoint={onConfirmCheckpoint}
            onCancelCheckpoint={onCancelCheckpoint}
            onRefresh={onRefresh}
            onBeginResolution={onBeginResolution}
            onConfirmResolution={onConfirmResolution}
            onCancelResolution={onCancelResolution}
        />
    );
}

const root = document.getElementById("root");
if (root === null) throw new Error("continuity root is missing");
createRoot(root).render(<ContinuityApplication />);
