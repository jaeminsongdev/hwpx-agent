# P10-02 Windows Agent report

- Generated: 2026-09-03
- Implementation commit: `731f32aa0b9c1ea7b47ea1e58629c4d200ac4a39`
- State: `pass_component_lease_fencing_current_pc_local`
- Reasoning/review mode: `max` / STRICT concurrency, filesystem, network and security audit

P10-02 implements the outbound Windows Agent component that consumes the P10-01 protocol. It leases
one exact target-profile assignment, validates its fencing and policy boundary, claims the execution
in an append-only journal, stages checksum-addressed inputs into a private job sandbox, invokes an
opaque-handle executor, uploads bounded outputs and commits a durable terminal receipt.

This task is the Agent-side component boundary. It does not expose a public listener and does not yet
implement the local named-pipe STA process, COM automation or actual Hangul execution. Those begin at
P10-03 and remain independently gated.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Outbound authenticated client | pass | exact four unary RPC paths, HTTPS-only endpoint, bounded bearer metadata, deadlines and 1 MiB messages |
| Lease/profile/policy validation | pass | UUID, expiry, nonzero fence, current profile, three read-only artifacts, finite limits and deny flags fail closed |
| No-duplicate execution | pass | exclusive journal ownership returns `Busy`; terminal receipts replay byte-identically without executor reuse |
| Fencing/recovery | pass | assignment drift is rejected before effect/commit; abandoned claims become durable `UNKNOWN_OUTCOME` |
| Staging and source preservation | pass | three inputs are copied with exact size/SHA-256, published read-only and source input is independently rehashed after execution |
| Sandbox boundary | pass | opaque handles only, marked non-root directories, reparse refusal and non-following cleanup |
| Output/upload boundary | pass | write-time aggregate quota, complete-result preflight, rehash, content-addressed no-overwrite publication and validated idempotent retry |
| Terminal commit | pass | flushed atomic terminal receipt precedes commit; control-plane receipt digest must match exactly |
| Privacy/security | pass | no document text, path, token or exception message enters receipts; no execution-side network or Registry mutation is accepted |

## Validation evidence

- The focused C# Release build passed with zero warnings and zero errors. Locked restore and
  `dotnet format --verify-no-changes` passed.
- The Windows Agent smoke executable passed `11/11` component E2E scenarios: successful lease and
  replay, concurrent duplicate ownership, stale heartbeat, unfinished recovery, fencing drift,
  input mismatch, commit digest recovery, aggregate output quota, idempotent validated upload,
  no-work/profile/probe-evidence rejection, and transport/root boundaries.
- The existing semantic Windows Worker compatibility smoke remained green in the same CI lane.
- The current checkout passed all five bootstrap lanes: `linux-core`, `windows-worker`, `widget`,
  `docs`, and `security`.
- A fresh clean checkout at exact commit `731f32a` passed the same five lanes and remained Git-clean.
  Its security gate found zero secrets, vulnerable NuGet packages or forbidden licenses and emitted
  an SBOM with 279 components.
- `Grpc.Core.Api` and `Grpc.Net.Client` are locked at `2.83.0`; the NuGet vulnerability scan includes
  the Agent project and returned no vulnerable packages.
- The P05 PowerShell 5.1 progress-parser compatibility fix is a separate commit `d3ccd05` and is not
  part of the P10-02 implementation claim.

## Strict self-review

- Change risk: high; this adds authenticated network, concurrency, journal and filesystem runtime
  boundaries plus two locked dependencies.
- Review result: APPROVE for the bounded P10-02 component scope.
- Final blocker/major/minor findings after remediation: `0/0/0`.
- Review remediation added write-time aggregate output enforcement, full receipt output accounting,
  source and probe-evidence revalidation, bounded journal reads, reparse checks and a verified-stream
  handoff that avoids artifact-store reopen races.
- Tests were not weakened and component evidence was not promoted into live TLS, cloud storage,
  Windows Service, STA/COM, actual Hangul, production, other-PC or cross-version evidence.

## Unverified boundary

P10-02 does not prove a live remote TLS control plane, production credential provisioning, cloud
artifact storage, Windows Service installation, named-pipe transport/ACLs, STA apartment/message
pump behavior, HwpObject lifecycle, sandbox ACL/encryption or secure deletion, desktop/VM isolation,
actual Hangul behavior, another PC/version, process recycling, distribution or production use.

## Next exact task

Implement P10-03 as a local C#/.NET named-pipe STA worker command loop. Enforce one private per-job
pipe, exact protocol/version/assignment binding, bounded length-delimited frames, a real STA thread
with a Windows message pump, serialized commands, cancellation and fail-closed cleanup. Prove the COM
apartment and command-loop boundary without claiming HwpObject lifecycle yet, at reasoning effort
`max`.
