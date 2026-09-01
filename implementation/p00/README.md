# P00 Execution Ledger

- Phase: `P00_SOURCE_LICENSE_TARGET_FREEZE`
- Overall state: `complete_current_pc_local_development_scope`
- Gate state: `pass_scoped_current_pc`
- Started: 2026-09-01

## Target strategy

- Target family: [Hancom Hangul desktop 2020+](target-family-policy.yaml), open-ended exact-build qualification.
- Current primary: [Hancom Hangul 2020](target-profile.yaml), exact installed build `11.0.0.9136` x86. Its historical profile ID is retained for evidence correlation.
- Deferred compatibility: [Hancom Hangul 2022](target-profile.2022-compatibility.yaml) `12.0.0.4605` and [Hancom Hangul 2024](target-profile.2024-deferred.yaml) `13.0.0.4049`. Their profiles and requests are preserved but they are not current P00 blockers.
- Current use scope: personal, non-commercial, local development; production remains disabled.
- Decision records: [target profile](target-profile-decision.md) and [current-PC development scope](current-host-development-decision.md).

## Task status and reasoning effort

| Task | State | Current evidence | Next exact action | Next reasoning effort |
|---|---|---|---|---|
| P00-01 target baseline | `pass` | 2020 exact build/hash/x86/STA runtime probe PASS; scope is exact 2020 only | Reopen only if primary target changes | completed |
| P00-02 environment baseline | `accepted_scoped_deviation` | Current PC baseline digest + live verifier PASS; clean image explicitly not claimed | Reopen only for another PC, portable worker, or production | completed for current scope |
| P00-03 font/printer | `pass` | HCR Batang substitution 0, embedded PDF, Hancom PDF exact profile | Reopen on font/printer/scope change | completed |
| P00-04 official sources | `pass` | KS reform 03 521-record response, rights and attribution locked | Reopen on source/scope change | completed |
| P00-05 source lock | `pass` | Final current-scope 40/40 local and 24/24 remote | Reopen on source set change | completed |
| P00-06 automation license | `pass` | Valid seat and personal non-commercial local scope confirmed; production disabled | Reopen before wider use | completed |
| P00-07 provider license | `passed_disabled` | Explicit user approval of all-production-providers-disabled decision | Reopen only if a provider is selected | completed |
| P00-08 feature baseline | `pass` | Canonical contracts, full validation, STRICT review | None | completed |
| P00-09 Gate | `pass_scoped` | v10 current-PC audit; P01 local scaffold authorized | Start P01 on this PC only | `xhigh` |

## Evidence rules

- `pass` requires target-specific actual evidence.
- Missing another-host, another-version, portable-worker, production, or distribution evidence remains `unverified`, `deferred`, or disabled.
- The design ZIP baseline and downloaded source originals are immutable inputs.
- Security-module binaries are not downloaded, registered, or executed during P00 source collection.
- Commercial or provider features remain disabled until explicit approval exists.

## Key artifacts

- [Windows image decision](windows-image-decision.md)
- [Current-PC development scope decision](current-host-development-decision.md)
- [Current-PC baseline](evidence/current-host-baseline.20260901.json)
- [Current-PC baseline verification](evidence/current-host-baseline-verification.20260901.json)
- [Font and printer manifest](font-printer-manifest.yaml)
- [Source inventory](source-archive-inventory.md)
- [Source lock](source-lock.json)
- [Automation license decision](license-decision.md)
- [Official source and attribution decision](attribution-decision.md)
- [Provider license matrix](provider-license-matrix.md)
- [Feature baseline report](feature-baseline-report.md)
- [Initial P00 Gate report](P00_GATE_REPORT.md)
- [2020 runtime probe evidence](evidence/runtime-probe.2020.20260901.json)
- [2020 bounded v2 probe evidence](evidence/runtime-probe.2020.20260901.v2.json)
- [2020 successful v3 probe evidence](evidence/runtime-probe.2020.20260901.v3.json)
- [2020 runtime diagnosis](evidence/runtime-diagnosis.2020.20260901.md)
- [Remote diagnostic kit](remote-diagnostics/README.md)
- [Remote diagnostic kit validation](evidence/remote-diagnostic-kit-validation.20260901.json)
- [Current source-lock verification](evidence/source-lock-verification.20260901.v9.json)
- [Windows PowerShell 5.1 source-lock verification](evidence/source-lock-verification.20260901.v9.windows-powershell.json)
- [Accepted 2020 document smoke](evidence/document-smoke-runs/98798b1801314a5e9bebf0f2505bc763/receipt.json)
- [Font/printer reference evidence](evidence/font-printer-reference-smoke.20260901.json)
- [Official source rights evidence](evidence/official-source-rights.20260901.json)
- [Historical pre-rebaseline final Gate audit](evidence/p00-gate-audit.20260901.v6.json)
- [Scope-rebaseline interim Gate audit](evidence/p00-gate-audit.20260901.v7.json)
- [Prior current-scope Gate rerun](evidence/p00-gate-audit.20260901.v8.json)
- [Current-scope final Gate rerun](evidence/p00-gate-audit.20260901.v9.json)
- [Current-PC scoped Gate audit](evidence/p00-gate-audit.20260901.v10.json)

## Current next task

At reasoning effort `xhigh`, start P01 repository/CI/security scaffolding for this current PC and exact Hangul 2020 scope. Do not enable another version, another PC, production, server/VM, customer, CI oracle, or provider path without reopening its own Gate.
