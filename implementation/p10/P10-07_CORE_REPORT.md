# P10-07 event and modal watchdog report

- Generated: 2026-09-04
- Implementation commit: `b0f3b6f`
- Supporting P05 fixture correction: `9096502`
- State: `pass_scoped_current_pc_local`
- Review: `STRICT / max`, blocker/major/minor `0/0/0`

## Delivered

- Exact installed `_DIHwpObjectEvents` connection-point subscription, 16-DispId COM-visible sink,
  bounded redacted signal queue, deterministic journal and ordered semantic carrier events.
- Exact-process native modal scanning across top-level and child windows, bounded hashed fingerprints,
  in-memory-only pixel SHA-256 and typed capture-failure metadata.
- Exact-target modal policies, unknown and fingerprint-drift fail-closed classification, no automatic
  response, two-second bounded watchdog stop and cleanup-only server dispatch after recycle-required
  receipts.
- Lifecycle integration that attaches events and starts the watchdog on session creation, scans before
  and after commands, preserves modal evidence in failure receipts and releases event/watchdog/COM
  resources on all tested cleanup paths.
- Locked smoke project, 23 static invariants and inclusion in the Windows CI lane.

## Actual current-PC evidence

The installed 32-bit COM registry points the event IID to the Hangul 2020 `HwpObject.tlb`. A generated
blank document, not a user file, produced six callback signals through the production event connection;
the document and application closed with zero remaining `Hwp.exe` processes.

The actual Hangul access dialog produced by the disposable P05-07 v2 fixture was observed by the final
native probe as one 683x196 modal. It was classified `unknown_fail_closed`; automatic response was
false, raw dialog text was not logged and screenshot pixels were not persisted. The paired 30-second
harness trace records unchanged input, no output/PDF, one owned process cleaned, zero cleanup errors
and zero remaining processes.

| Private Git-ignored evidence | Bytes | SHA-256 |
|---|---:|---|
| `p10-07-actual-event-delivery-final.txt` | 108 | `df4b4debe593f0ca175bf72e2075adbd4a4b6d3848bf703fec1d4aa9d509c5a9` |
| `p10-07-actual-modal-probe-callbacksafe-final.txt` | 535 | `73a8f032520c9ca7c9aa394552fe0e4a5a541429e6cad48cdffddb9215fbbb45` |
| `p05-07-section-columns-hancom-modal-callbacksafe-final-trace.json` | 1,365 | `92140f493dd3354c51a3a4f803b5b0ce955659cccdfa624e07a937209a1e483d` |

The modal title and pixel hashes were stable in the final diagnostics, but the class hash changed
across runs. That drift is retained as negative evidence; no expected-dialog allowlist entry was
created from it.

## Validation

- P10-07 event/modal smoke passed `13/13`; static policy/integration checks passed `23/23`.
- Windows Worker lane passed locked restore, format verification, Release build and execution for all
  seven Worker/Agent smoke projects. Existing STA, lifecycle, security, binding and Agent regressions
  remained `6/6`, `10/10`, `10/10`, `14/14` and `13/13` respectively.
- Existing P10 static suites remained `24/24`, `29/29` and `41/41`; binding schemas accepted two valid
  fixtures and rejected all six negative fixtures.
- Exact commit `b4c7a54` clean clone passed all five CI lanes and remained Git-clean after validation.
  The clone contained none of the Git-ignored actual target evidence.
- P05 section/column tests passed `14/14`; the corrected target builder passed four example tests and
  independently inspected the v2 fixture as two sections, one break, spans `[1, 1]`, body width 80,220
  and the exact expected text digest.
- `cargo fmt --check`, generated protocol drift check and Git diff whitespace checks passed. No public
  protocol change was made.

## Failed checks retained

The first actual subscription attempt failed with `CONNECT_E_CANNOTCONNECT` because the managed sink
interface and class were not COM-visible public types; that was corrected before acceptance. A later
check showed that an empty `Start→Quit` session proves connection only, not delivery. The actual mode
was strengthened to create and close a disposable blank document and now requires at least one signal;
the accepted run received six.

Earlier capture code used `PrintWindow`, which can synchronously message a hung target. It was replaced
with `BitBlt`, and the bitmap is deselected before `GetDIBits`. Managed exceptions are no longer allowed
to unwind through native enumeration callbacks. All actual evidence above was regenerated after these
changes.

## Strict boundary and next task

P10-07 is complete for the exact current-PC 2020 scope and its roadmap checkbox may be checked. This
does not close P10: P10-05 actual module registration and dependent P10-06 production execution remain
unverified, while P10-08 through P10-10 are not implemented. P05-07 actual save/reopen/PDF acceptance
also remains pending a user-approved access prompt. Proceed with P10-08 isolation at reasoning effort
`max`; rerun P05-07 only when the user can immediately approve the visible prompt.
