# P10-03 STA worker policy

- Component: `HwpxAgent.WindowsWorker.Host` and `HwpxAgent.WindowsWorker.StaSmoke`
- Scope: private local named-pipe transport, bounded protobuf command loop and real Windows STA message pump
- Current target: licensed local Hangul 2020 `11.0.0.9136` x86 profile
- Reasoning effort: `max`

## Process and pipe boundary

The Windows Agent creates one fresh UUID-based 32-hex job pipe name and starts one separate worker host.
The host accepts exactly one byte-mode server connection with `CurrentUserOnly`, asynchronous I/O,
write-through behavior and one server instance. It has no public network listener. Command-line input is
an exact five-key assignment consisting of pipe name, session UUID, fencing token, trace UUID and
target-profile ID; duplicates, omissions and extra arguments fail before the worker begins listening.

`CurrentUserOnly` prevents cross-user access but does not isolate another hostile process running as the
same Windows user. The random pipe name and exact assignment binding are defense in depth, not a claim
of a distinct job-user ACL. Per-job user/profile, desktop and VM isolation remain P10-08 work.

## Frame and assignment boundary

Every local message uses the P10-01 protobuf contract inside a canonical unsigned-varint length frame.
The reader rejects zero, over-1-MiB, noncanonical, overflowing and truncated frames before allocating a
payload. The writer measures the protobuf before allocation and refuses an empty or oversized message.

The command loop validates exact protocol 1.0, canonical identifiers, nonzero fence, bounded deadline,
typed command payload and the declared deny-by-default security policy. It then requires exact session,
fence and trace binding. The first command must be one matching `StartSession`; command IDs are unique,
the start and close commands are single-use, no command follows close, queue depth is bounded to 16 by
default, and a connection accepts at most 1,024 commands. Receipt fields, outputs, ordered events,
privacy flags and command correlation are validated before bytes are written.

## STA and state transition boundary

All command handlers run serially on one dedicated thread whose apartment is set to `STA`. The thread
creates a Win32 message queue and runs `GetMessage`/`TranslateMessage`/`DispatchMessage`. A handler can
pump pending Windows messages and check cancellation through `StaExecutionContext`. Worker-dispatch
messages are excluded from handler pumping, so pumping cannot execute a second command reentrantly.

Start failure closes the connection before any pipelined command can run. A command deadline is at most
900 seconds. Cancellation before dispatch returns `CANCELLED` without a handler effect; cancellation or timeout after handler entry is
reported as `UNKNOWN_OUTCOME` with cleanup required. After an unknown outcome the session is cleanup-only:
ordinary commands are rejected and only `CloseSession` can run. Close is terminal even when cleanup
fails. The message loop must stop at a cancellation safe point within ten seconds or disposal fails.

## P10-03 command surface

The P10-03 boundary handler implements only `StartSession` and `CloseSession`, producing typed safe events
from the real STA thread. Open, execute, save and render deliberately return `UNKNOWN_BINDING`; there is
no `HwpObject`, raw action string, ParameterSet invocation, document open, save, render, screenshot,
clipboard, Registry mutation or external-network action in this task. `HancomSession` and owned-process
lifecycle begin at P10-04.

## Validation boundary

The smoke executable proves the real Windows message loop, serialized/non-reentrant dispatch, canonical
framing, malformed-frame rejection, real `CurrentUserOnly` named-pipe I/O, cancellation reconciliation,
cleanup-only state, binding rejection before handler invocation, sequence/count limits, failed-start
pipelining rejection and a separately launched worker host. It passes under both the normal x64 runtime
and this PC's installed x86 .NET runtime.

This is component evidence for P10-03. It does not prove COM creation, installed Hangul automation,
file-path approval, modal handling, process-tree cleanup, desktop/user/VM isolation, hostile same-user
resistance, actual HWPX behavior, another PC or Hangul 2022/2024.
