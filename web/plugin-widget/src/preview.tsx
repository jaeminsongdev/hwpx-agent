import { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";

import type {
    WidgetErrorCode,
    WidgetPhase,
    WidgetViewState,
} from "./bridge.js";
import { WIDGET_SNAPSHOT_SCHEMA, type ViewLocale } from "./model.js";
import { WidgetShell } from "./ui.js";
import "./styles.css";

const PHASES: WidgetPhase[] = [
    "ready",
    "approval_pending",
    "recoverable_error",
];

const query = new URLSearchParams(window.location.search);
const requestedPhase = query.get("phase");
const initialPhase: WidgetPhase = PHASES.includes(requestedPhase as WidgetPhase)
    ? (requestedPhase as WidgetPhase)
    : "ready";
const initialLocale: ViewLocale =
    query.get("locale") === "en-US" ? "en-US" : "ko-KR";
const initialTheme = query.get("theme") === "dark" ? "dark" : "light";
const showControls = query.get("controls") !== "0";
document.documentElement.dataset.previewTheme = initialTheme;

function Preview() {
    const [phase, setPhase] = useState<WidgetPhase>(initialPhase);
    const [locale, setLocale] = useState<ViewLocale>(initialLocale);
    const state = useMemo<WidgetViewState>(
        () => ({
            phase,
            locale,
            theme: initialTheme,
            snapshot:
                phase === "ready"
                    ? {
                          schema_version: WIDGET_SNAPSHOT_SCHEMA,
                          client_surface: "chatgpt_web",
                          locale,
                          project_id: "prj_preview1234",
                          revision_id: "rev_preview1234",
                          validation_state: "verified",
                      }
                    : null,
            errorCode:
                phase === "recoverable_error"
                    ? ("CONNECT_FAILED" as WidgetErrorCode)
                    : null,
            actionPending: false,
        }),
        [locale, phase],
    );
    return (
        <div className="preview-canvas">
            {showControls && (
                <div
                    className="preview-controls"
                    aria-label="Local visual QA controls"
                >
                    {PHASES.map((value) => (
                        <button
                            key={value}
                            type="button"
                            onClick={() => setPhase(value)}
                        >
                            {value}
                        </button>
                    ))}
                    <button
                        type="button"
                        onClick={() =>
                            setLocale(locale === "ko-KR" ? "en-US" : "ko-KR")
                        }
                    >
                        {locale}
                    </button>
                </div>
            )}
            <WidgetShell
                state={state}
                onContinue={() => undefined}
                onRetry={() => undefined}
            />
        </div>
    );
}

const root = document.getElementById("root");
if (root === null) throw new Error("preview root is missing");
createRoot(root).render(<Preview />);
