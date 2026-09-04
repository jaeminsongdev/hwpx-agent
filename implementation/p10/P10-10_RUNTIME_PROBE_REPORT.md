# P10-10 runtime probe report

- Date: 2026-09-04
- Implementation commit: `57b0656`
- Target: current licensed Hangul 2020 `11.0.0.9136` x86 PC
- Decision: `pass_scoped_current_pc_local`
- Review: `STRICT / max`, blocker/major/minor `0/0/0`

## Delivered

- A mandatory, bounded `RuntimeProbePolicyPin` and `IRuntimeProbeCollector` dependency for every
  Windows Agent instance.
- Lease admission that performs isolation attestation, materializes and uploads a content-addressed
  redacted probe artifact, reports the exact receipt, and requires accepted+routable status before
  the first `AcquireLease` call.
- A five-minute bounded admission cache. Expired, future-dated, malformed, privacy-violating or
  internally contradictory observations fail closed and never acquire a lease.
- Deterministic capability-set hashing over sorted typed observations. The materializer requires
  target identity, Registry32 COM registration, the capability registry, file-path security module
  and zero-Hangul-process observations as lease-critical capabilities.
- A read-only current-PC collector that checks the exact executable digest/version/PE architecture,
  `HWPFrame.HwpObject.2` Registry32 binding, capability registry and pinned P00 evidence hashes,
  Registry32 security-module registration, and running `Hwp.exe` count. It accepts only local-drive
  paths and does not instantiate COM or start Hangul.
- Draft 2020-12 policy/audit schemas, negative tests, a bounded no-overwrite exact-commit audit and
  complete Windows CI integration.

## Actual current-PC evidence

The authoritative Git-ignored audit is
`implementation/p10/evidence/p10-10-current-runtime-probe-audit-20260904T014339193Z.json`:

- bytes: `3256`
- SHA-256: `59e682a801a735d9109bb514259c7d63914fc32e64570235b90ff4b55791dcbc`
- exact source revision: `57b0656b4384506f7c4238cce5c495e90a109040`
- Release Agent smoke assembly SHA-256:
  `f1f0cda7566c7ecf747442f5ef30c59feb632994a7e9ecd6cab4809788db9b98`
- runtime-probe policy SHA-256:
  `808223a7b4365d7f3beb0eb3a3fea4e466560ca27cd4ea240a740ead037470f8`
- capability-set SHA-256:
  `c5f207f548f51b7708f1b52e2121ccbaabb26ea8ae0287856031d3708fd40439`
- P00 host-baseline digest:
  `7fbf6559fc3372b9da6c0b0ca53d9f4eb78b76a79df248c37ff009c13376adc0`

The actual collector verified eight of nine observations. The exact target, COM registration,
capability registry and four prior P00 evidence pins matched; no `Hwp.exe` was present. The one
unavailable lease-critical capability was `agent.security_file_path_module`, because the approved
module is not registered on this PC. The report was therefore honestly classified `unroutable`.
The control-plane adapter received exactly one probe receipt, while `AcquireLease`, executor and
Hangul-process start counts all remained zero.

This is the desired fail-closed result, not a failed P10-10 implementation. P10-10 owns truthful
health reporting and pre-lease enforcement; P10-05 owns supplying and validating an approved
security module. Once that dependency exists, a new no-overwrite audit must independently establish
a routable result.

## Validation

| Check | Result |
|---|---|
| Agent Release build | pass, warnings 0 / errors 0 |
| Existing Agent regression | pass, 28/28 |
| P10-10 admission/profile/privacy smoke | pass, 4/4; total Agent 32/32 |
| P10-10 static invariants | pass, 29/29 |
| Runtime-probe policy/audit negative tests | pass, 11/11 |
| All P10 Python tests | pass, 40/40 |
| Runtime-probe policy validation | pass, Draft 2020-12 and all pinned file digests |
| Exact current-host audit | pass, exact policy/source/target/baseline binding |
| Complete Windows Worker lane on exact implementation commit | pass, `59.625s` |
| Residual `Hwp.exe` before/after actual probe | pass, 0 / 0 |
| User document, COM object, network or system-setting access | none |

## Strict Gate decision

P10-10's probe agent exists and its required `profile mismatch no lease` behavior is proven: a
mismatched collected target generates zero report and lease RPCs, while a matching but unroutable
target reports once and stops before lease acquisition. The P10-10 roadmap checkbox may be checked
for the stated current-PC local-development scope.

This does not close P10. P10-05 remains `core_ready_actual_module_pending`, P10-06 actual production
COM execution remains dependent on P10-05, and P10-08 dedicated production isolation remains
unqualified. It does not claim another PC, Hangul 2022/2024, provider operation or production
readiness. P05-07 through P05-09 actual render acceptance also remains independent and pending.

