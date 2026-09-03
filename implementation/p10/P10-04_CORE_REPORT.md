# P10-04 HwpObject lifecycle core report

- Generated: 2026-09-03
- Implementation commit: `c10f97cf0035205b322122fd6c0fd5c90ec42eae`
- State: `core_ready_actual_hangul_pending`
- Reasoning/review mode: `max` / STRICT lifecycle, process-ownership, cleanup and privacy audit

P10-04 implements the bounded `HancomSession` lifecycle for the exact current-PC Hangul 2020
`11.0.0.9136` x86 target. COM creation, document open/close and application quit remain on the
existing STA thread. The session owns one newly created process identity and revalidates that exact
identity before any forced termination.

This is not the final P10-04 task report. Static, fake-runtime and clean-checkout evidence passed, but
the current-PC actual run timed out while waiting for the user to approve Hangul's access dialog.
Therefore actual `HwpObject` create/open/close/quit remains `unverified`, the roadmap checkbox stays
open and no actual behavior is promoted from component tests.

## Core acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Exact target admission | pass_component | Registry32 COM server, executable digest, file version, x86 PE machine and worker architecture must all match |
| STA-only lifecycle | pass_component | typed start/open/close commands execute through the P10-03 STA handler; no raw generic action surface exists |
| Source preservation | pass_component | approved input size/SHA is checked before open, immediately after open and after close |
| Process ownership | pass_component | refuses pre-existing Hangul processes, binds one newly created same-session exact-path process and records PID/start ticks/session/path |
| Fail-closed cleanup | pass_component | close, quit, COM release and owned-process cleanup continue independently; uncertain cleanup becomes `UNKNOWN_OUTCOME` |
| Production open boundary | pass_component | default host denies document open until P10-05 supplies an approved-document resolver |
| Actual current-PC lifecycle | actual_pending | attempt 01 timed out before access approval; input/staging unchanged, temporary staging removed, one owned process cleaned, zero remained |

## Validation evidence

- Lifecycle and cleanup smoke passed `8/8` under the default Windows lane and under an exact x86
  build launched by the installed 32-bit .NET runtime.
- The static lifecycle harness test passed `24/24`.
- The current checkout at exact commit `c10f97c` passed all five lanes: `linux-core`,
  `windows-worker`, `widget`, `docs`, and `security`.
- A fresh clean checkout at the same exact commit passed all five lanes, passed the x86 `8/8`
  lifecycle smoke and remained Git-clean. Its security report found no failed checks and produced an
  SBOM with 348 components.
- The actual-attempt evidence reports `timed_out=true`, `input_unchanged=true`,
  `staged_input_unchanged=true`, `staged_input_removed=true`, `cleaned_process_count=1`,
  `cleanup_refused_count=0`, `cleanup_error_count=0` and `remaining_hwp_process_count=0`.
- No user document was scanned, no document text was emitted, no network was invoked, no registry or
  system setting changed, and no Computer Use click/type action was used.

## Strict self-review

- Change risk: high; this is the first code path that can create and terminate an actual Hangul COM
  application process.
- Review result: APPROVE for the bounded component/core scope only.
- Final blocker/major/minor findings after remediation: `0/0/0` for that component scope.
- Remediation covered failed-start cleanup, continued teardown after independent failures, source
  rehashing around open/close, cleanup-required unknown state and process-identity revalidation.
- Actual current-PC behavior is still a required blocking acceptance result for final P10-04 closure.

## Unverified boundary

The core evidence does not prove successful access approval, actual document open/close/quit, actual
COM cleanup after a completed open, crash injection into the real Hangul process, hostile same-user
isolation, file-path approval, signed action bindings, modal handling, timeout supervision, another PC
or Hangul version, distribution or production use.

## Next exact task

When the user is immediately ready, rerun the bounded current-PC actual lifecycle harness and require
the exact safe terminal receipt, unchanged source digest and zero residual Hangul processes. In the
meantime P10-05 may proceed independently: connect a single-use, immutable approved-document lease to
the handler and prove allowed/denied path cases without widening the public command surface. Continue
at reasoning effort `max`.
