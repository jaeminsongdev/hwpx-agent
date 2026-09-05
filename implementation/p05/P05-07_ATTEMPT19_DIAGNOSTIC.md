# P05-07 v3 attempt 19: observed manual-access prompt and bounded timeout

- Date: 2026-09-05, approximately 19:12–19:22 KST; current licensed Hangul 2020 only.
- Trigger: fresh user request to show any required access prompt immediately.
- Unchanged wrapper: `implementation/p05/tools/run-hancom-2020-section-columns-readback.ps1`.
- New attempt19 output/trace/PDF names under the existing disposable v3 fixture directory.
- Result: `SECTION_COLUMNS_READBACK_TIMEOUT`, **not actual acceptance**.

Preflight and COM creation passed. The owned worker 38380 and Hwp 9872 reached `open_input/running`.
Computer Use selected the returned `빈 문서 2 - 한글` window and captured it without accessibility
text, activation, click or typing. The capture showed the exact v3 input path and the four
file-access choices, including `접근 허용(Y)`. The user was notified immediately. A second capture
near 19:22 KST still showed the input access prompt. The progress journal retained exactly three
events and no successful open/read/save/reopen/PDF event.

The 600-second watchdog expired. Session 1788 is terminal (tool-reported shell exit 1; child -1).
The wrapper reports one owned Hwp process cleaned, zero cleanup refusal/error and zero residual
Hwp processes. A separate process query confirmed no Hwp remains. The input is unchanged and no
output HWPX or PDF exists. No original document, Registry value or system setting changed.

This run establishes that the test was blocked at the visible file-access prompt at both captured
times. It does not establish a general PC defect, the user's actions between observations or any
actual two-section readback recovery. The fallback trace's `window_visible_for_user_access=false`
is not valid visibility evidence: the worker never returned, while both screenshots show the prompt.

## Durable evidence

Under `fixtures/target-build/p05-07-current-2020-20260905-v3/`:

| File | SHA-256 |
|---|---|
| `p05-07-section-columns-input.hwpx` | `dc2d385ecdc60a396f5740d604b8ce379f25733c87bf98ed3e3baa32291e49a5` |
| `p05-07-hancom-2020-trace-attempt19.json` | `fb3b45ca8ac1b86d475cabac3c0e3b23ce747352cd2241c7cfd8c9c1e9813b81` |
| `p05-07-hancom-2020-trace-attempt19.json.progress.jsonl` | `00b1817579f495ef57d08251372f32940db3f3f335a6e54ceac6eb79ac159ce1` |

The fallback trace happens to be byte-identical to attempt18; the distinct progress journal binds
this attempt's timestamps and process identities. Screenshots are preserved as Computer Use tool
outputs in this task, not as additional repository files. Earlier failures remain intact.

Do not automatically launch another copy. Require a fresh user-present approval opportunity, use
new artifact names, and preserve both-section text, save/reopen and PDF/visual acceptance criteria.
