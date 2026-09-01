# P00-01 Target Profile Decision

- Decision date: 2026-09-01
- Decision state: `accepted_current_pc_2020_only`
- P00-01 Gate state: `pass` (current exact 2020 scope only)
- Current use scope: `personal_noncommercial_local_development`

## Current decision

- Current primary development target: Hancom Hangul 2020 exact build `11.0.0.9136` x86 on the current local PC.
- The immutable profile ID remains `hancom-hangul-2020-secondary`. The word `secondary` is historical; renaming it would break correlation with the accepted runtime receipts and diagnostic bundles. Role is now carried separately as `primary_development`.
- Hancom Hangul 2022 build `12.0.0.4605` and Hangul 2024 build `13.0.0.4049` are `deferred_compatibility`. Their profiles, official sources, and pending offline requests are preserved, but they are not blockers for the current 2020-only P00 Gate.
- The target-family architecture remains open-ended for every Hangul desktop release from 2020 onward. Deferral is not qualification: 2022, 2024, and future builds remain unsupported claims until each exact build on its installed PC independently passes discovery, runtime, document, font, and license gates.
- Every capability binding, fixture result, runtime receipt, render/oracle result, and release state remains keyed by `target_profile_id`. Evidence from 2020 must not be promoted to another release.

The official update data retrieved on 2026-09-01 lists `13.0.0.4049` for Hangul 2024, `12.0.0.4605` for Hangul 2022, and `11.0.0.9136` for Hangul 2020. The current host has the exact 2020 x86 executable, accepted identity/document roundtrip evidence, and a verified current-host baseline. The user directed implementation and debugging to use this PC only and to resume 2022/2024 qualification when their installed PCs become available.

## P00-01 evidence

| Target | Current Gate role | Product/file evidence | Runtime probe | Current state |
|---|---|---|---|---|
| `hancom-hangul-2020-secondary` | required primary | Exact version/bitness/SHA-256 observed and official build matched | x86/STA COM version readback, `Quit()`, clean child exit, zero remaining process | `pass` |
| `hancom-hangul-2022-compatibility` | deferred | Official desired build only | not run | `hold_unqualified` |
| `hancom-hangul-2024-primary` | deferred | Official desired build only | not run | `hold_unqualified` |

P00-01 is pass for the current exact 2020 implementation baseline. Separate P00 evidence proves document save/reopen/readback, PDF export, and substitution 0 on this PC. It does not prove clean-image readiness, another PC, or any 2022/2024 behavior.

## Fail-closed policy

- `desktop_automation` is allowed only for bounded personal non-commercial local validation on the current 2020 profile. Purpose and genuine valid product-seat scope were confirmed by the user on 2026-09-01. Production, hosted, server, VM, customer-facing, and distributed use remain disabled.
- Bounded personal-local `oracle` validation passed for this current PC. Production, portable worker, another PC, and clean-image claims remain disabled and are outside the current development Gate.
- `direct_hwpx` may be implemented against the source baseline, but its own writer compatibility remains `unverified` until target-specific P03/P13 evidence exists.
- No target is silently substituted when a requested target is unavailable.
- Deferred profiles cannot lease work or appear as supported until independently qualified.

## Decision history

- Earlier P00 execution selected 2024 as primary with 2022 and 2020 anchors. The completed v6 Gate audit correctly reported that earlier aggregate scope as blocked.
- The 2026-09-01 user rebaseline changes the current implementation schedule and required initial target set; it does not rewrite or invalidate historical evidence.
- The later 2026-09-01 current-PC-only directive replaces the separate-clean-image blocker for local development with a hashed current-host baseline. Historical v9 remains the accurate result under the earlier clean-image Gate.

## Sources

- Official 2024 update data: `https://help.hancom.com/updates/hoffice130/ko-KR/app.js`
- Official 2022 update data: `https://help.hancom.com/updates/hoffice120/ko-KR/app.js`
- Official 2020 update data: `https://help.hancom.com/updates/hoffice110/ko-KR/app.js`
- Official automation scope: `https://developer.hancom.com/hwpautomation`
