# P05-07 v3 attempt 18: bounded open timeout

- Date: 2026-09-05; current-PC licensed Hangul 2020 `11.0.0.9136`, x86 STA.
- Result: `SECTION_COLUMNS_READBACK_TIMEOUT`, **not actual acceptance**.
- Trigger: fresh user-present request to launch an access-approval test now.
- Wrapper: unchanged `tools/run-hancom-2020-section-columns-readback.ps1`, 600-second watchdog.
- New disposable input: `fixtures/target-build/p05-07-current-2020-20260905-v3/`.

## Observed evidence

The v3 input has the repaired header count but the unchanged two-section expected normalized text
digest `92d2179169f1102d256589c2ca90b8422405076927d91c6e5ba2e91f28381d2f`. Preflight and COM creation
passed. The last of three valid progress records is `open_input/running`; no `open_input/pass`,
text readback, save, reopen or PDF evidence was produced. The watchdog expired after 600 seconds.

The owned worker exited with code -1 after the watchdog stopped it. Cleanup identified and stopped
one test-created automation Hwp process, with zero refusals, zero cleanup errors and zero remaining
Hwp processes. A separate process readback after termination also found zero Hwp processes.
No user document was scanned; no original was changed; no output HWPX or PDF was created. No UI
click/type, Registry write, system-setting change or external network call was made by the test.

While live, a process readback showed the test's Hangul main window. The final wrapper synthesized
a fallback trace because the inner worker never returned; its `window_visible_for_user_access=false`
is a fallback default, not proof that no window existed. No screenshot or access-button event was
captured. The trace therefore cannot establish whether the user saw or pressed access approval,
which modal was displayed, or whether the wait was caused by the PC or by the document importer.

## Preserved evidence identities

All paths below are under the v3 fixture directory and remain Git-ignored.

| File | SHA-256 |
|---|---|
| `p05-07-section-columns-input.hwpx` | `dc2d385ecdc60a396f5740d604b8ce379f25733c87bf98ed3e3baa32291e49a5` |
| `p05-07-hancom-2020-trace-attempt18.json` | `fb3b45ca8ac1b86d475cabac3c0e3b23ce747352cd2241c7cfd8c9c1e9813b81` |
| `p05-07-hancom-2020-trace-attempt18.json.progress.jsonl` | `a2277e2cdc34a23cd3dad4596671c2b42b108240e8746bfe482eedc961e1b89a` |

## Decision

The previous attempt's one-section text mismatch was not reached in this run. V3 readback recovery
and causality of the header-count repair remain unproven in actual Hangul. Preserve the expected
two-section text, input, failed traces and Gate criteria. Do not automatically relaunch the same
test. In the next explicitly user-present session, capture the specific blocking UI via screenshot
and collect the corresponding progress phase before deciding whether another run is useful.
User input remains manual; do not bypass file-access prompts or attach to unrelated Hwp processes.
