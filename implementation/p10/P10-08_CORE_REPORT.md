# P10-08 isolation core report

- Date: 2026-09-04
- Target: current licensed Hangul 2020 `11.0.0.9136` x86 PC
- Decision: `core_ready_current_pc_development_audit_pass_dedicated_controls_unqualified`
- Reasoning effort: `max`

## Outcome

The Windows Agent now requires an exact worker-isolation policy and a live attestor. Host/policy
drift, a noninteractive or Session-0 host, an unmarked workspace, stale job sandbox, a pre-existing
Hangul process or a target-process residue fails closed. Admission is serialized to one active job.
Post-job identity/session/desktop/profile/temp drift or residue is checked after sandbox disposal and
before the terminal receipt is written; a failure after executor entry becomes
`UNKNOWN_OUTCOME + CLEANUP_FAILED`.

The current-PC policy explicitly remains a mutable, local-development-only image. It cannot claim
production isolation. A dedicated policy has hard requirements for a dedicated identity/profile,
private window station, OS outbound deny, isolated clipboard and clean profile/recovery/printer
residue audits. The current-PC attestor reports these controls false rather than inferring them.

## Validation

| Evidence | Result |
|---|---|
| Agent build | pass, warnings 0 / errors 0 |
| Agent smoke | pass, 18/18 including P10-08 drift, dedicated-control, post-residue and stale-workspace tests |
| Isolation policy unit tests | pass, 8 tests including overclaim, target drift, executable/host-identity digest drift, unknown field and duplicate-key rejection |
| P10-08 static checks | pass, 24/24 |
| Policy schema validation | pass, Draft 2020-12 |
| Actual current-host audit schema validation | pass |
| Existing P00 live host baseline verification | pass, exact baseline digest `7fbf6559fc3372b9da6c0b0ca53d9f4eb78b76a79df248c37ff009c13376adc0` |
| Actual current-host live observation | pass for local development: interactive Session 1, private marked job workspace, `Hwp.exe=0`, raw identity/document absent |
| Active firewall observation | complete, 3 profiles, all-default-outbound-block is false |
| Current checkout Windows lane | pass, `51.746s` on the final reviewed source |
| Current checkout Linux core lane | pass, `10.606s` |
| Current checkout widget lane | pass, `3.644s` |
| Current checkout docs lane | pass, `7.875s` on the final reviewed docs; P10 Python tests 19/19 |
| Current checkout security lane | pass, `47.520s`; findings/vulnerabilities/failed checks 0 |

The first audit-tool attempt stopped before publication because it treated the in-process PowerShell
baseline verifier like a native process and read an unset `$LASTEXITCODE`. The script now captures
`$?` for that step. No final evidence was created by the failed attempt; its temporary file was
removed in `finally`. The corrected no-overwrite `attempt01` passed.

## Private actual evidence

The authoritative ignored evidence file is
`implementation/p10/evidence/p10-08-current-host-isolation-audit-20260904-attempt04.json`:

- bytes: `2957`
- SHA-256: `976ece67948691e81bd3d18383a0c841a69a484ab0219fde8a9bf09f7b623716`
- policy-manifest SHA-256: `0abaddd0032214a6d7c71dbb14526cf0da56de274654ecd1eef8b78c0fdfe188`
- privacy: no raw user identity/path/document text, no user-document or clipboard-content scan

`attempt01` is retained only as superseded diagnostic evidence. Self-review found that the first
policy compared identity/session digests only before versus after a run. The corrected policy pins a
composite host-isolation identity derived from the P00 machine binding and the hashed current
identity/window-station/desktop/profile/temp tuple. `attempt02` proved that binding; it is superseded
by `attempt03`, which also requires the read-only active-firewall observation to complete before the
development-only audit can pass. `attempt04` is authoritative after self-review replaced recursive
temporary-root deletion with a bounded, prefix-checked cleanup that never follows reparse points.

## Strict boundary

This is real current-PC evidence for the development-only isolation boundary. It does not prove an
immutable image, dedicated user/profile, independent window station, OS-level network deny,
clipboard isolation, profile-wide Recent/recovery/printer cleanup, hostile same-user resistance,
production/provider operation, another PC or Hangul 2022/2024. Those facts are false or unobserved in
the actual audit, so the P10-08 roadmap hard-gate checkbox remains open.

The next non-UI implementation is P10-09 timeout/recycle and unknown-outcome reconciliation at
reasoning effort `max`. P05-07 actual render remains a separate user-approval dependency.

## Exact-commit clean-clone follow-up

The clean clone at exact P10-08 commit `aee2818` passed `linux-core` (`39.513s`), `windows-worker`
(`54.548s`), `widget` (`4.009s`) and `docs` (`7.695s`). Its security lane did not pass because only
`pnpm audit` timed out; all other security checks passed. A second security run produced the same
single failed check. Consequently, this report does not claim an exact-commit clean-clone FULL pass.
The bounded, no-overwrite security-harness remediation and its still-failing actual audit are tracked
separately in `../p01/P01_SECURITY_REVALIDATION_20260904.md`.
