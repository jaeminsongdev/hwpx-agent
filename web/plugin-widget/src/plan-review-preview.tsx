import { useState } from "react";
import { createRoot } from "react-dom/client";
import type { PlanReviewViewState } from "./plan-review-controller.js";
import {
    PLAN_REVIEW_SNAPSHOT_SCHEMA,
    type PlanReviewSnapshot,
} from "./plan-review-model.js";
import { PlanReviewView } from "./plan-review-ui.js";
import "./plan-review-styles.css";

const params = new URLSearchParams(location.search);
const blocked = params.get("state") === "blocked";
const confirm = params.get("state") === "confirm";
const snapshot: PlanReviewSnapshot = {
    schema_version: PLAN_REVIEW_SNAPSHOT_SCHEMA,
    client_surface: "codex_local",
    locale: params.get("locale") === "en" ? "en-US" : "ko-KR",
    project_id: "prj_7pZK4mQxN9",
    source_revision_id: "rev_A91C3mQxN7",
    plan_id: "plan_G7wK2pLmQ9",
    risk_level: "high",
    estimated_page_effect: "document_wide",
    route: [
        {
            capability_id: "paragraph.text_replace",
            selected_backend: "direct_hwpx",
            support_level: "verified",
            supported: true,
        },
        {
            capability_id: "table.cell_style",
            selected_backend: "hancom_2020",
            // Synthetic preview only; this does not qualify the real table capability.
            support_level: blocked ? "unverified" : "verified",
            supported: true,
        },
        {
            capability_id: "document.semantic_validate",
            selected_backend: "hybrid",
            support_level: "verified",
            supported: true,
        },
    ],
    route_digest: "a".repeat(64),
    diff: {
        added: 4,
        modified: 7,
        removed: 0,
        categories: [
            { kind: "paragraph", count: 5 },
            { kind: "table", count: 3 },
            { kind: "style", count: 3 },
        ],
    },
    warnings: blocked
        ? [
              {
                  code: "ROUTE_UNVERIFIED",
                  severity: "blocking",
                  kind: "validation",
              },
          ]
        : [
              {
                  code: "DOCUMENT_WIDE_EFFECT",
                  severity: "warning",
                  kind: "layout",
              },
              {
                  code: "PRESERVE_UNKNOWN",
                  severity: "notice",
                  kind: "preservation",
              },
          ],
    signature_impact: "none",
    dry_run_state: "verified",
    execution_allowed: !blocked,
};
function Preview() {
    const [state, setState] = useState<PlanReviewViewState>({
        phase: "ready",
        mode: confirm ? "confirm_execution" : "view",
        locale: snapshot.locale.startsWith("ko") ? "ko-KR" : "en-US",
        theme: params.get("theme") === "dark" ? "dark" : "light",
        snapshot,
        errorCode: null,
        actionPending: false,
        acknowledged: params.get("ack") === "1",
        executionState:
            params.get("state") === "committed_unverified"
                ? "committed_unverified"
                : params.get("state") === "unconfirmed"
                  ? "unconfirmed"
                  : params.get("done") === "1"
                    ? "submitted"
                    : "none",
    });
    return (
        <PlanReviewView
            state={state}
            onBeginExecution={() =>
                setState({
                    ...state,
                    mode: "confirm_execution",
                    acknowledged: false,
                })
            }
            onCancelExecution={() =>
                setState({ ...state, mode: "view", acknowledged: false })
            }
            onAcknowledged={(value) =>
                setState({ ...state, acknowledged: value })
            }
            onConfirmExecution={() =>
                setState({
                    ...state,
                    mode: "view",
                    acknowledged: false,
                    executionState: "submitted",
                })
            }
            onRevalidate={() =>
                setState({ ...state, executionState: "revalidated" })
            }
        />
    );
}
const root = document.getElementById("root");
if (root === null) throw new Error("preview root missing");
createRoot(root).render(<Preview />);
