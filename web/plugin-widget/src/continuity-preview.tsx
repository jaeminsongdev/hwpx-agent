import { createRoot } from "react-dom/client";

import type { ContinuityViewState } from "./continuity-controller.js";
import { CONTINUITY_SNAPSHOT_V2_SCHEMA } from "./continuity-model.js";
import { ContinuityView } from "./continuity-ui.js";
import "./continuity-styles.css";

const params = new URLSearchParams(window.location.search);
const narrow = params.get("layout") === "narrow";
const conflict = params.get("state") === "conflict";
const confirm = params.get("state") === "confirm";
const dark = params.get("theme") === "dark";
const state: ContinuityViewState = {
    phase: "ready",
    mode: confirm ? "confirm_checkpoint" : "view",
    locale: params.get("locale") === "en" ? "en-US" : "ko-KR",
    theme: dark ? "dark" : "light",
    errorCode: null,
    actionPending: false,
    checkpointState: params.get("state") === "saved" ? "saved" : "none",
    selectedResolution: null,
    resolutionState: "none",
    snapshot: {
        schema_version: CONTINUITY_SNAPSHOT_V2_SCHEMA,
        client_surface: "chatgpt_web",
        locale: "ko-KR",
        project_id: "prj_preview1234",
        head_revision_id: "rev_current1234",
        warning_count: conflict ? 2 : 0,
        conflict_state: conflict ? "stale" : "none",
        stale_head: conflict
            ? {
                  observed_generation: 12,
                  current_generation: 14,
                  delta: 2,
                  allowed_resolutions: [
                      "rebase_operation_plan",
                      "branch",
                      "manual_merge",
                  ],
              }
            : null,
        revisions: [
            {
                revision_id: "rev_current1234",
                parent_revision_ids: ["rev_middle1234"],
                created_at: "2026-09-05T03:20:00Z",
                change_kind: "edited",
            },
            {
                revision_id: "rev_middle1234",
                parent_revision_ids: ["rev_first12345"],
                created_at: "2026-09-04T11:10:00Z",
                change_kind: "validated",
            },
            {
                revision_id: "rev_first12345",
                parent_revision_ids: [],
                created_at: "2026-09-03T08:00:00Z",
                change_kind: "created",
            },
        ],
        next_cursor: narrow ? "cursor_preview1234" : null,
    },
};

document.body.dataset.previewTheme = state.theme;
document.documentElement.style.background = dark ? "#111722" : "#ffffff";
document.body.style.minHeight = "100vh";
document.body.style.background = dark ? "#111722" : "#ffffff";
createRoot(document.getElementById("root")!).render(
    <ContinuityView
        state={state}
        onBeginCheckpoint={() => undefined}
        onConfirmCheckpoint={() => undefined}
        onCancelCheckpoint={() => undefined}
        onRefresh={() => undefined}
        onBeginResolution={() => undefined}
        onConfirmResolution={() => undefined}
        onCancelResolution={() => undefined}
    />,
);
