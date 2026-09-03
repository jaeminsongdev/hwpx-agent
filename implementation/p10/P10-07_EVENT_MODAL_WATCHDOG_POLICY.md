# P10-07 event and modal watchdog policy

- Scope: current-PC licensed Hangul 2020 `11.0.0.9136` x86 only
- Public contract: immutable `windows_bridge.v1`; no new event enum or raw COM payload
- Production modal policy: `modal.fail_closed`, exact-target bound, empty expected-dialog allowlist
- Reasoning/review mode: `max`

## Automation event boundary

The Worker subscribes to the installed `_DIHwpObjectEvents` connection point identified by
`f04a09a0-f319-40d5-88ca-ca439cc6820c`. The public COM-visible sink implements all 16 installed
DispIds. Subscription failure stops session creation, and shutdown unadvises before releasing the
connection point and COM instance.

Signals enter a concurrent queue capped at 1,024 and then a command-scoped journal capped at 1,024.
Overflow, invalid identifiers and invalid carrier types are typed failures. Raw hyperlink address and
display text are discarded at the callback; only a bounded signal identifier and SHA-256 metadata
cross the sink. Because `windows_bridge.v1` is immutable, signal digests use the existing semantic
event type for the command that observed them. No private identifier or new public enum is inferred.

## Modal detection and evidence

The native probe examines only windows owned by the exact Worker-owned Hwp process. It scans bounded
top-level and child sets, recognizes dialog-class, same-process-owned or modal-frame windows, and
caps dimensions, pixels and control count. Native callbacks return normally and report failures only
after returning to managed code.

Window class, title and control structure are normalized and hashed. Pixel bytes are captured with
`BitBlt`, hashed in memory and immediately zeroed. The probe does not call `PrintWindow`, send target
messages, persist screenshot pixels, read document text, or perform mouse/keyboard input. Capture
failure is still metadata and never turns a modal into an allowed condition.

## Classification and command behavior

A policy must match the exact policy ID, target profile, product build and at most 64 immutable
fingerprints. Unknown or probe-failure observations return `UNKNOWN_MODAL`, require process recycle
and stop effectful dispatch. An exact expected fingerprint is distinguished as policy-denied and also
stops; automatic response is not implemented in this task.

The production resolver intentionally has no expected fingerprints because the observed Hangul 2020
access dialog class hash changed between runs. It remains unknown and fail-closed until a stable,
versioned fingerprint and explicit response contract have their own evidence. A background poll runs
every 100 ms, each command scans before and after execution, and watchdog shutdown is bounded to two
seconds. Any cleanup-required receipt moves the pipe session into cleanup-only dispatch.

## Deferred boundary

This policy proves event delivery and unknown-modal fail-closed behavior on the current target. It
does not prove P05-07 save/render, a registered P10-05 security module, P10-06 production action
execution, P10-08 isolation, P10-09 recycle supervision, another PC/version or production deployment.
