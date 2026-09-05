# P05-07 v3 attempt 20: user-present access opportunity

- Date: 2026-09-05, 19:44–19:54 KST; current licensed Hangul 2020 only.
- Trigger: the user asked to show any required access prompt immediately.
- Unchanged wrapper: `implementation/p05/tools/run-hancom-2020-section-columns-readback.ps1`.
- Exact same v3 input; unique attempt20 output, trace and PDF paths. No previous evidence overwritten.
- Result: `SECTION_COLUMNS_READBACK_TIMEOUT`, not actual acceptance.

The worker 35804 and owned Hwp 30084 passed preflight/COM creation and reached `open_input/running`.
Two Computer Use captures showed the exact input path and access choices. No click, activation,
typing or accessibility-text read was used. The user was immediately asked to click the access
button; at the later capture the first input prompt remained visible. This does not establish
what the user did between captures or a general PC defect.

The 600-second watchdog expired. Session 63850 is terminal: shell exit 1, child exit -1. Cleanup
removed one owned Hwp process with zero refusal/error and zero residual Hwp processes. A separate
process query found no Hwp. The input is unchanged and no saved HWPX or PDF exists. The progress
journal has exactly three records, ending at open_input/running; no read, save, reopen or PDF PASS.

## Evidence

All files are under `fixtures/target-build/p05-07-current-2020-20260905-v3/`.

| File | SHA-256 |
|---|---|
| `p05-07-section-columns-input.hwpx` | `dc2d385ecdc60a396f5740d604b8ce379f25733c87bf98ed3e3baa32291e49a5` |
| `p05-07-hancom-2020-trace-attempt20.json` | `fb3b45ca8ac1b86d475cabac3c0e3b23ce747352cd2241c7cfd8c9c1e9813b81` |
| `p05-07-hancom-2020-trace-attempt20.json.progress.jsonl` | `14e9fb14e295b50c38e5288860d1bda06216d488a8898c425eec3a3ff6ed9ed9` |

The fallback trace is byte-identical to the earlier timeout traces; it contains no run identity.
The distinct progress journal binds this attempt to its timestamps and process identities. The
fallback `window_visible_for_user_access=false` is not a visibility measurement: two screenshots
showed the prompt. Those captures remain Computer Use outputs in the task, not repository files.

No automatic relaunch. Require a fresh user-present request for another attempt. Preserve both-section
text, save/reopen and actual PDF/visual acceptance requirements. No Registry or security setting changed.
