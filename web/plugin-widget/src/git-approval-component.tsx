import { useCallback, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
    GitApprovalController,
    type GitApprovalState,
} from "./git-approval-controller.js";
import { GitApprovalMcpAppPort } from "./git-approval-mcp-app-port.js";
import { GitApprovalView } from "./git-approval-ui.js";
import "./git-approval-styles.css";

const INITIAL: GitApprovalState = {
    phase: "connecting",
    theme: "light",
    acknowledged: false,
    plan: null,
    receipt: null,
};

function GitApprovalApplication() {
    const [state, setState] = useState(INITIAL);
    const [controller, setController] = useState<GitApprovalController | null>(null);
    useEffect(() => {
        const next = new GitApprovalController(new GitApprovalMcpAppPort());
        const unsubscribe = next.subscribe(setState);
        setController(next);
        void next.start();
        return () => {
            unsubscribe();
            void next.close();
        };
    }, []);
    return (
        <GitApprovalView
            state={state}
            onAcknowledged={useCallback(
                (value) => controller?.setAcknowledged(value),
                [controller],
            )}
            onConfirm={useCallback(() => void controller?.confirm(), [controller])}
        />
    );
}

const root = document.getElementById("root");
if (root === null) throw new Error("Git approval root is missing");
createRoot(root).render(<GitApprovalApplication />);
