# P10-04 HwpObject lifecycle report

- Generated: 2026-09-04
- Implementation commits: `c10f97c`, `b830f74`, `3281693`, `c06d12c`
- State: `pass_current_pc_local_hangul_2020_lifecycle`
- Reasoning/review mode: `max` / STRICT lifecycle, process ownership, cleanup and privacy audit

The bounded `HancomSession` lifecycle is accepted for the exact current-PC licensed Hangul 2020
`11.0.0.9136` x86 target. COM creation, open, close and quit stay on the STA worker. The session
admits only the exact target/process identity, preserves the approved input and fails closed when
cleanup cannot be proved.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Exact target admission | pass | Registry32 COM server, executable digest, file version, x86 PE machine and worker architecture match |
| STA-only lifecycle | pass | typed create/open/close/quit run through the STA handler; no public raw action surface exists |
| Source/staging preservation | pass | approved input and staged copy remained digest-exact; staging was removed after the run |
| Process ownership and cleanup | pass | actual three-cycle receipt ended with no cleanup error/refusal and zero residual `Hwp.exe` |
| Failure behavior | pass_component | open/cleanup/version/disconnect failure, cancellation, abrupt owned-process exit and repetition are covered |
| Actual current-PC lifecycle | pass | exact attempt 09 completed with terminal safe output, child exit 0 and no timeout |

## Validation evidence

- Lifecycle and cleanup smoke passed `10/10` under x64 and the installed 32-bit .NET runtime; the
  static lifecycle suite passed `24/24`.
- The two added regressions prove that server cancellation still invokes the STA cleanup hook and
  that an already-exited owned process is accepted without killing an unrelated process. The latter
  uses an isolated disposable child process, not the real Hangul executable.
- Current checkout and exact commit `c06d12c` clean checkout passed all `5/5` bootstrap lanes. The
  clean checkout remained Git-clean.
- Actual attempt 09 records `state=pass`, exact product build `11.0.0.9136`, x86 architecture,
  unchanged input and staging, removed staging, `timed_out=false`, child exit 0, drained exact-safe
  output, empty stderr and zero residual Hangul processes.
- Raw document text, user-document access, network, Registry/system changes and Computer Use
  click/type were absent.
- Earlier timed-out attempts remain failure diagnostics and are not used as success evidence.

## Strict scope boundary

This pass proves normal create/open/close/quit on this exact installation plus deterministic
component cancellation, abrupt-exit, failure and repeated-lifecycle handling. It does not prove a
forced crash of the real Hangul executable, hostile same-user isolation, an actual registered
security module, signed action execution, unknown-modal handling, another PC/version, distribution
or production use. Those broader cases remain later P10/P18 work.

## Next exact task

Complete P10-06's trusted offline builder so a verified P02 target registry can be projected into a
separately signed, exact-target execution bundle without exposing raw identifiers. P10-05 actual
module registration remains pending until an approved installed module exists. Continue at reasoning
effort `max`.
