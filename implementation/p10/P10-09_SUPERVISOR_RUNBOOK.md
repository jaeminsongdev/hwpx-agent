# P10-09 timeout, reconciliation and recycle runbook

- Component: Windows Agent supervisor and owned STA-worker process boundary
- Current target: licensed local Hangul 2020 `11.0.0.9136` x86
- Current scope: personal, noncommercial, current-PC local development only
- Policy: `supervisor.current_pc_local_v1`
- Reasoning effort: `max`

## Admission and deadline model

`WindowsAgentConfiguration` requires both the P10-08 isolation pin and the P10-09 supervisor pin.
Command and job deadlines are distinct and strictly ordered: `command_timeout < job_timeout`. The
Agent marks executor entry exactly once, never automatically repeats an execution ID, and stores one
terminal journal receipt before a control-plane retry can replay it.

The cooperative cancellation window, reconciliation window and hard recycle window are independently
bounded to 1–60 seconds. A timeout or caller cancellation first requests cooperative stop, then probes
source/output/process/action-trace/readback state, and finally recycles the owned worker. A valid
recycle receipt must bind the exact execution ID, assignment digest and recycle reason.

## Outcome classification

| Observation after interruption | Terminal result | Retry rule |
|---|---|---|
| Complete probe proves no action started, source unchanged, no output and no trace | `FAILED + TIMEOUT/CANCELLED` | retryable only as a new orchestration decision |
| Any effect, output or trace exists, or the probe is incomplete | `UNKNOWN_OUTCOME` | not retryable for the same execution |
| A completed success lacks terminal trace, output digest or semantic readback | `UNKNOWN_OUTCOME + CLEANUP_FAILED` | not retryable |
| Recycle fails, times out or returns a mismatched receipt | `UNKNOWN_OUTCOME + CLEANUP_FAILED` | not retryable |
| Worker reaches job-count or memory threshold | preserve valid terminal result, then force fresh worker | next job uses a new worker |

Contradictory observations are protocol failures. Examples include a verified digest without an
output, a terminal trace without a trace, readback without a terminal effect, or nonzero process
memory while the worker is reported stopped.

## Process ownership

`WindowsOwnedWorkerProcess` verifies the exact executable SHA-256, constructs the process with
`CREATE_SUSPENDED`, assigns it to a private Windows Job Object configured with
`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`, rechecks the launched image path and digest, and only then
resumes its primary thread. This removes the pre-assignment child-spawn race.

Recycle calls `TerminateJobObject` and does not succeed until Job Object accounting reports zero
active processes. The Agent never enumerates and kills processes by name and never terminates a
user-launched Hangul process. Worker command lines may exist transiently in process memory but are
not placed in receipts, logs or evidence.

## Startup recovery and residue

Use `WindowsAgentService.CreateRecoveredAsync` for normal startup. It performs bounded worker
recovery before constructing the strict service and before any lease RPC. Only a plain directory
named `job-<canonical-lowercase-uuid>` with the exact `.hwpx-agent-sandbox` marker can move to the
marked quarantine directory. All candidates are validated before the first move. An unmarked,
ambiguous or reparse-point entry stops startup; the Agent does not recursively delete it.

An existing unfinished journal claim is reconciled and recycled. It is never submitted to the
executor again. If absence of effect is not fully proven, the stored terminal result is
`UNKNOWN_OUTCOME`.

## Current-PC verification

Build and run the complete Windows lane, then create a fresh no-overwrite audit:

```powershell
python tools/p01/run_ci.py --lane windows-worker

pwsh -NoProfile -File implementation/p10/tools/audit-current-worker-supervisor.ps1 `
  -OutputPath implementation/p10/evidence/p10-09-current-worker-supervisor-audit-<run>.json
```

The audit requires a clean Git source tree, builds the Release Agent without restore, binds the exact
commit and assembly digest, verifies the P00 host baseline, runs the 28-test Agent smoke under an
outer 120-second watchdog, and requires zero `Hwp.exe` before and after. Its integrated hard-timeout
test starts a real root-plus-descendant process tree, lets the executor ignore cooperative
cancellation, reconciles the uncertain effect, recycles through the Job Object, verifies both PIDs
are gone, and then proves the same execution replays byte-identical terminal evidence without a
second executor call.

## Scope boundary and handoff

This current evidence proves P10-09 supervision mechanics on this PC. It does not claim production
worker-image isolation, provider operation, another PC, Hangul 2022/2024, or a destructive timeout
against a real user document. P10-05 module registration and P10-06 licensed COM production
execution remain separate open evidence. Other machines must use a new policy, host baseline and
no-overwrite audit rather than copying this result.

Proceed to P10-10 runtime probe at reasoning effort `max`. P05-07 actual save/reopen/PDF acceptance
remains a separate user-approval run and must not be inferred from this supervisor evidence.
