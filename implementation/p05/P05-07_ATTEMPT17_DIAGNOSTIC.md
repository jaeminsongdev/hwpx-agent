# P05-07 actual Hangul 2020 attempt 17

- Date: 2026-09-05; implementation checkout 9360c47fc6c8958f6f9a16b954491579d774342d.
- Trigger: the user offered to handle any needed access prompt now.
- Scope: one disposable fixture, current licensed Hangul 2020 11.0.0.9136 x86.
- Result: FAILED_INPUT_TEXT_MISMATCH, not render acceptance.

## Execution and evidence

The unchanged run-hancom-2020-section-columns-readback.ps1 wrapper ran once with a 600-second
watchdog, the v2 fixture and fresh attempt-17 output/trace/PDF names. The expected normalized
text remained the two section markers separated by LF; it was not changed to match the result.

Unlike attempts 10–16, attempt 17 passed com_create and open_input. It then failed at read_input
with SECTION_COLUMNS_READBACK_INPUT_TEXT_MISMATCH. The journal records seven events and a failed
terminal state. This proves that document opening returned successfully, not that the whole
document was correctly imported or that any particular approval button was clicked.

The actual normalized text digest matches the fixture's first section marker alone. Empty text,
the second marker alone and both markers separated by one LF, two LFs or a form feed do not match.
This narrows the issue to missing second-section readback; it does not yet distinguish an import
problem from a text-extraction/API coverage problem.

Evidence remains Git-ignored under fixtures/target-build/p05-07-current-2020-20260904-v2/:

| File | SHA-256 |
|---|---|
| p05-07-section-columns-input.hwpx | 3ace06ddf744f089a42884b11c0c5a9996f08aac99eee3af91753a6581a2c6f0 |
| p05-07-section-columns-hancom-attempt-17-trace.json | 278001ffb5b0561316baf2e0f2d23fae4028fdb5ffcc6e089b78296b486d38c7 |
| p05-07-section-columns-hancom-attempt-17-trace.json.progress.jsonl | a56290667b21af981566cf30438d76cfa00a7137dbc106606bcd3c63a1a75197 |

## Safety and validation limits

- Input unchanged; output HWPX and PDF were not saved.
- Quit passed; no owned process needed forced cleanup; no Hwp process remained.
- No timeout, UI click/type, user-document scan, network call or Registry/system change occurred.
- Existing traces and earlier fixtures were preserved. No implementation or test was changed.
- Gate remains open: save/reopen, semantic preservation, PDF checks and visual review are not run.

## Next bounded action

Inspect the two-section fixture's package/spine and the current text-extraction contract first.
Do not simply accept the observed single-section digest or lower the two-section requirement.
If a further actual-Hangul diagnostic is needed, prepare a focused read-only probe before another
user-present approval session. Do not repeatedly relaunch the unchanged failing wrapper.
Recommended reasoning: max for multi-section data preservation and the eventual Gate audit.
