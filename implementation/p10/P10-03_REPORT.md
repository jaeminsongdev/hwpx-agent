# P10-03 STA worker report

- Generated: 2026-09-03
- Implementation commit: `2628174eaf50e5ef580bf0ba8c1768404446483f`
- State: `pass_component_sta_worker_current_pc_local`
- Reasoning/review mode: `max` / STRICT transport, concurrency, state-machine and privacy audit

P10-03 implements the separate C#/.NET STA worker host behind the P10-02 Windows Agent boundary. It
adds one private local named pipe, canonical bounded protobuf framing, exact assignment correlation,
a serialized command loop and a dedicated Windows STA thread with a real Win32 message pump.

This task proves the worker process/apartment boundary only. It does not instantiate `HwpObject` or
claim any actual Hangul open, save, render or semantic readback. Those lifecycle effects start at P10-04.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Separate STA host | pass | standalone host process starts with an exact five-field assignment and emits no document or path output |
| Private local pipe | pass | fresh UUID-based 32-hex job name, one instance, `CurrentUserOnly`, byte mode, async/write-through and no network listener |
| Bounded framing | pass | canonical protobuf varint length, 1 MiB ceiling, zero/noncanonical/overflow/truncation rejection before payload allocation |
| Assignment binding | pass | exact protocol 1.0, session, fence, trace and first-start profile ID checked before handler dispatch |
| Command sequencing | pass | start-first/once, close-last/once, unique IDs, queue/count/deadline limits and failed-start pipeline termination |
| STA apartment and pump | pass | one real STA thread, Win32 message queue, serialized commands, non-reentrant work dispatch and cancellation safe points |
| Unknown-outcome safety | pass | post-dispatch cancel/timeout requires effect uncertainty and cleanup; session then accepts only close |
| Receipt/privacy boundary | pass | exact correlation, terminal state, bounded outputs/events, source unchanged and all prohibited telemetry flags false |
| Current-PC x86 compatibility | pass | exact implementation built with `PlatformTarget=x86` and smoke ran through installed 32-bit .NET 10.0.8 runtime |

## Validation evidence

- Locked restore, `dotnet format --verify-no-changes` and Release builds passed with zero warnings and
  zero errors for the semantic worker, STA worker/host and Windows Agent projects.
- The P10-03 smoke passed `6/6` top-level suites. Its covered cases include same-thread STA execution,
  non-reentrant serialization, frame roundtrip/negative cases, real named-pipe cancellation, cleanup-only
  enforcement, binding rejection, duplicate/start/count failures, failed-start pipeline rejection and a
  separately launched host process.
- The smoke passed in the default x64 process and in an x86 build launched by this PC's 32-bit
  `dotnet.exe`; both paths exercised the separate worker host.
- The current checkout passed all five bootstrap lanes: `linux-core`, `windows-worker`, `widget`,
  `docs`, and `security`.
- A fresh clean checkout at exact commit `2628174` passed the same five lanes, passed the x86 STA smoke
  and remained Git-clean. Its security gate found zero secrets, vulnerable NuGet packages or forbidden
  licenses and emitted an SBOM with 317 components.
- The worker dependency graph remains locked to `Google.Protobuf` `3.36.1`; no new package was added.

## Strict self-review

- Change risk: high; this adds native Windows message dispatch, asynchronous framed I/O, cancellation
  races, command-state transitions and a new process boundary.
- Review result: APPROVE for the bounded P10-03 component scope.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review remediation added failed-start pipeline termination and a cleanup-only state after an uncertain
  effect, with regression cases proving both commands cannot reach the handler.
- Tests were not weakened and component evidence was not promoted into COM, actual Hangul, document
  mutation, isolation, production, other-PC or cross-version evidence.

## Unverified boundary

P10-03 does not prove `HwpObject` creation, owned Hancom process identity, open/close/quit cleanup,
file-path security approval, signed bindings/ParameterSet execution, event/modal watchdogs, forced
process recycle, dedicated Windows user/desktop/VM isolation, hostile same-user resistance, actual
Hangul behavior, another PC/version, distribution or production use. `CurrentUserOnly` is not a
same-user security boundary, and full target-build identity remains subject to the later runtime probe.

## Next exact task

Implement P10-04 as `HancomSession` for the exact current licensed Hangul 2020 `11.0.0.9136` x86 target.
Create and own `HwpObject` only inside the existing STA handler, bind one application/process identity,
implement deterministic create/open/close/quit and fail-closed teardown, and prove zero residual owned
processes across normal close, open failure, cancellation, crash and repeated lifecycle tests. Keep file
path approval, action execution and modal policy out of this task, at reasoning effort `max`.
