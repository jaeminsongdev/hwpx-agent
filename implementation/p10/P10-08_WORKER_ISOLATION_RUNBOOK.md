# P10-08 worker isolation runbook

- Component: `HwpxAgent.WindowsAgent` worker isolation boundary
- Current target: licensed local Hangul 2020 `11.0.0.9136` x86
- Current scope: personal, noncommercial, current-PC interactive development only
- Current policy: `isolation.current_pc_local_v1`
- Reasoning effort: `max`

## Two isolation scopes

The checked-in current-PC policy is not a portable or production worker-image claim. It binds the
exact P00 host-baseline digest, exact target profile and exact policy-manifest digest, requires a
nonzero interactive session, one active job, a marked empty job workspace and zero `Hwp.exe`
processes before and after a run. It also preserves the existing read-only input, separate
no-overwrite output, and request-level network/clipboard/macro/OLE denial.

The live attestor also recomputes one pinned `host_isolation_identity_sha256` from the P00
machine-binding hash plus the current SID, window station, desktop, profile-root and temp-root
hashes. None of the raw inputs is emitted or persisted. Copying the policy to another machine,
identity, desktop or profile therefore fails before lease acquisition.

`DedicatedWorkerImage` is a separate fail-closed scope. It additionally requires every live
attestation below; none can be disabled by a configuration flag:

1. dedicated job identity and profile;
2. private window station;
3. OS-enforced default outbound network deny;
4. isolated clipboard;
5. clean profile/Recent-file residue audit;
6. clean recovery/temp residue audit; and
7. clean printer-spool residue audit.

The current-PC attestor deliberately reports all seven as false. It refuses construction for a
dedicated policy and therefore cannot be reused to promote this machine into production isolation.

## Current-PC startup

The operator keeps Hangul closed, then runs the live P00 host verifier and the P10-08 audit. The
audit output must use a fresh named path below the ignored `implementation/p10/evidence/` directory.

```powershell
dotnet build --configuration Release `
  workers/windows-hancom-agent/tests/HwpxAgent.WindowsAgent.Smoke/HwpxAgent.WindowsAgent.Smoke.csproj

pwsh -NoProfile -File implementation/p10/tools/audit-current-worker-isolation.ps1 `
  -OutputPath implementation/p10/evidence/p10-08-current-host-isolation-audit-<run>.json
```

The audit is read-only. It does not inspect a user document, clipboard contents, Recent-file names,
recovery-file names, printer jobs, raw user identity or raw profile paths. Identity, window station,
desktop, profile root, temp root and firewall state are emitted only as SHA-256 values. It writes the
final audit atomically and never overwrites an existing result.

`state=pass_current_pc_development_only` permits only the exact current local development profile.
It is invalid evidence for another PC, Hangul 2022/2024, a VM, provider, hosted service, customer or
release worker.

## Runtime order

1. Construct `WindowsAgentConfiguration` with a mandatory `WorkerIsolationPolicyPin` whose target
   profile and host-baseline digest equal the configured target identity.
2. Construct the Agent with a non-null `IWorkerIsolationAttestor`. Construction refuses stale job
   sandbox residue and an unqualified host before any outbound RPC.
3. `RunOnceAsync` admits exactly one active run. A second local caller receives `Busy` without
   acquiring another lease.
4. Immediately before `AcquireLease`, re-observe the host and require the exact policy/profile/image
   pins, interactive session, privacy flags, private marked workspace and zero target processes.
5. Stage only declared read-only artifacts, execute one job and upload separately addressed outputs.
6. After sandbox disposal and before publishing the terminal journal receipt, require the workspace
   to be empty, the target-process count to be zero and the identity/session/desktop/profile/temp
   digests to match the pre-lease snapshot.
7. Any post-effect drift or residue replaces an apparent success with
   `UNKNOWN_OUTCOME + CLEANUP_FAILED`; it is never retried in the same session.

## Failure handling

- `IsolationNotReady` before lease: make no RPC and run no executor. Do not bypass the attestor.
- `CleanupResidue` at startup: quarantine the Agent workspace. Do not recursively delete an
  unverified path; P10-09 owns bounded reconciliation and recycle.
- `CLEANUP_FAILED` after executor entry: retain the terminal failure receipt and do not repeat the
  action. P10-09 must reconcile process/output state in a fresh worker.
- Existing user-launched Hangul: stop admission. The tool never terminates a process it did not own.
- Host/image/policy digest drift: regenerate independent evidence and review it; never edit the
  receipt to match the machine.

## Dedicated-worker admission

A future dedicated worker uses a new immutable manifest and an independently verified attestor. It
must reproduce P00 target/oracle evidence on that host, enforce all seven dedicated controls, prove
source/output-only residue, and pass the full P10-08 suite. Current-PC hashes or this policy file may
not be copied as proof. License and production Gates remain independent even after technical
isolation succeeds.

## Handoff

P10-09 must consume `IsolationNotReady`, `CleanupResidue` and `CLEANUP_FAILED` as recycle/quarantine
signals, reconcile unknown outcomes without duplicate effects, and preserve this pre-lease/post-job
ordering. Continue at reasoning effort `max`.
