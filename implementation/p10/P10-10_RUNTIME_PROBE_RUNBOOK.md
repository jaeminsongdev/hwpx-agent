# P10-10 runtime probe runbook

- Component: Windows Agent pre-lease health and capability probe
- Current target: licensed local Hangul 2020 `11.0.0.9136` x86
- Current scope: personal, noncommercial, current-PC local development only
- Policy: `probe.current_pc_local_v1`
- Reasoning effort: `max`

## Startup and lease order

The normal service is constructed with an isolation attestor and a runtime-probe collector. Every
Agent process follows this order:

1. verify current worker isolation and residue state;
2. collect a fresh typed runtime observation when no unexpired routable receipt is cached;
3. require the exact policy, target profile and capability-registry identities;
4. reject privacy flags, missing core observations and health/capability contradictions;
5. create and upload one content-addressed redacted evidence artifact;
6. report the probe to the control plane and validate its accepted receipt digest;
7. call `AcquireLease` only when the report is both accepted and routable.

The current cache lifetime is 300 seconds. It is only an optimization within one Agent instance;
process restart, expiry or any observation failure requires a new report. A profile mismatch fails
before artifact upload or any control-plane RPC.

## Health classification

| Observation | Health | Lease behavior |
|---|---|---|
| Every required and optional capability is verified | `healthy` | control plane may route |
| All lease-critical capabilities are verified but an optional capability is unavailable/unverified | `degraded` | control plane decides route; local acceptance still requires `routable=true` |
| Any lease-critical capability is unavailable, unverified or drifted | `unroutable` | report once, then no lease |
| Profile/policy/registry identity mismatch, stale/future timestamp, privacy flag or contradiction | rejected locally | no report and no lease |

The current PC is `unroutable` because the approved file-path security module is not configured.
Do not change the health mapping or mark the module verified to make a test pass.

## Evidence contents and privacy

The evidence artifact contains only target identity hashes, capability IDs, typed states, safe codes
and observation hashes. It does not contain absolute paths, registry values, document text, user
filenames, process command lines or pixel data. Collection reads bounded local-drive files and
Registry32 only. It does not open a user document, instantiate HwpObject, start Hangul, use the
clipboard, make a network request or change a registry/system setting.

The current policy pins:

- the exact Hangul 2020 executable identity;
- `HWPFrame.HwpObject.2` and its Registry32 CLSID/server binding;
- `specs/capability-contracts.generated.json`;
- the P00 current-host baseline, automation lifecycle, document open/save and font/printer evidence;
- the P10-08 isolation policy.

## Current-PC verification

Run the complete Windows lane and then create a fresh exact-commit audit. The source tree must be
clean and the output name must not already exist.

```powershell
python tools/p01/run_ci.py --lane windows-worker

pwsh -NoProfile -File implementation/p10/tools/audit-current-runtime-probe.ps1 `
  -OutputPath implementation/p10/evidence/p10-10-current-runtime-probe-audit-<run>.json
```

The audit rebuilds the Agent, executes all 32 Agent tests, verifies the live P00 host baseline, runs
the read-only current-host collector, validates the policy and final audit with Draft 2020-12, and
requires zero `Hwp.exe` before and after. Its evidence is intentionally Git-ignored and referenced by
digest from the report.

## Another PC or Hangul version

Do not copy this PC's healthy/unroutable conclusion to another machine. On the Hangul 2022 or 2024
PC, create a separate policy and evidence set with a new stable profile ID, then collect these items:

1. exact product build, x86/x64 PE architecture and executable SHA-256;
2. Registry32 or Registry64 ProgID, CLSID and exact local-server binding;
3. new current-host baseline and isolation identity;
4. target-specific capability registry/binding bundle and their hashes;
5. independently generated lifecycle, disposable document open/save, font and printer evidence;
6. approved file-path security-module registration name, DLL architecture and SHA-256;
7. a clean-source, no-overwrite runtime-probe audit from that machine.

Keep raw paths and machine/user identifiers out of the transferable report. A remote diagnostic
bundle should carry safe codes, hashes, build/architecture, bounded tool logs and the exact source
revision. It must preserve the local raw evidence separately so Codex can compare policy, observation
and implementation without remote UI control. A mismatched build or host stays unroutable until its
own evidence passes.

## Handoff

P10-10 is complete for its current scope. The next P10 unblock is P10-05: obtain or implement an
approved file-path security module, pin its DLL and registration, and rerun P10-05, P10-06 and this
P10-10 audit. P10-08 still needs a separately qualified dedicated worker environment for production.
The next independent non-UI product task is P14-01 metadata schema at reasoning effort `max`; the
next UI-dependent task remains P05-07 actual save/reopen/PDF acceptance, also at `max`.
