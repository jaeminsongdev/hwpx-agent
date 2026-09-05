import { useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { WidgetBridgeController, type WidgetViewState } from "./bridge.js";
import { detectOptionalHostExtensions } from "./host-extensions.js";
import { McpAppPort } from "./mcp-app-port.js";
import { WidgetShell } from "./ui.js";
import "./styles.css";

const INITIAL_STATE: WidgetViewState = {
    phase: "connecting",
    locale: "ko-KR",
    theme: "light",
    snapshot: null,
    errorCode: null,
    actionPending: false,
};

function requestId(): string {
    return `req_${crypto.randomUUID().replaceAll("-", "")}`;
}

function WidgetApplication() {
    const [generation, setGeneration] = useState(0);
    const [state, setState] = useState<WidgetViewState>(INITIAL_STATE);
    const [controller, setController] = useState<WidgetBridgeController | null>(
        null,
    );

    useEffect(() => {
        detectOptionalHostExtensions(window);
        const next = new WidgetBridgeController(new McpAppPort(), requestId);
        const unsubscribe = next.subscribe(setState);
        setController(next);
        void next.start();
        return () => {
            unsubscribe();
            void next.close();
        };
    }, [generation]);

    const onContinue = useCallback(
        () => void controller?.continueProject(),
        [controller],
    );
    const onRetry = useCallback(() => setGeneration((value) => value + 1), []);

    return (
        <WidgetShell state={state} onContinue={onContinue} onRetry={onRetry} />
    );
}

const root = document.getElementById("root");
if (root === null) {
    throw new Error("widget root is missing");
}
createRoot(root).render(<WidgetApplication />);
