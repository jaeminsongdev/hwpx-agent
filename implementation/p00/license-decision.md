# P00-06 Automation License Decision

- Decision state: `approved_restricted_personal_noncommercial_local_scope`
- Current P00 Gate state: `pass_current_scope_only`
- Production release state: `disabled`
- Date: 2026-09-01

## Verified public statement

Hancom's official automation guide states that personal non-commercial use may be used freely, while commercial use in a sold solution or application requires separate approval and license acquisition from Hancom.

Official source: `https://developer.hancom.com/hwpautomation`

## Project decision

- The user confirmed on 2026-09-01 that the current implementation purpose is personal, non-commercial, and local development.
- Public documentation access does not grant a production automation license.
- `desktop_automation` and Hancom-backed `oracle` remain disabled for commercial, hosted, server, VM, or customer-facing use until a written license covers the exact deployment scope.
- Local format research and Direct HWPX development do not authorize redistribution of Hancom binaries, fonts, manuals, or security modules.
- No automation security module is downloaded, registered, or shipped under the current decision.
- The user explicitly confirmed on 2026-09-01 that the installed Hangul 2020 product seat is genuine and valid. No key, receipt, account, or license document was collected.
- Hangul 2022 and 2024 product-seat and automation scope checks are deferred with their target profiles.
- The user's authorization and seat confirmation permit bounded local synthetic-document P00 validation within the current personal non-commercial scope.
- Business/legal/technical signatures and Hancom commercial/server/VM approval are outside the current personal-local scope, but remain mandatory before any such future scope is enabled.

## Scope matrix

| Scope | Current state | Required evidence |
|---|---|---|
| Personal non-commercial local experiment | `approved_restricted` | User purpose and genuine valid installed seat confirmation recorded |
| P00 offline no-document discovery/probe | `allowed_restricted` | Bounded local run, no production/provider use, retained privacy evidence |
| P00 synthetic document smoke on Hangul 2020 | `allowed_restricted` | Generated non-user fixture, bounded project path, no security-module registration |
| Internal organization tool | `blocked` | Written Hancom scope approval and seat/server terms |
| Commercial desktop application | `blocked` | Commercial automation license and redistribution terms |
| Hosted service or VM worker | `blocked` | Server/VM/concurrency/tenant terms and approved topology |
| Customer-distributed worker | `blocked` | Distribution, update, support, and security-module terms |
| CI/oracle farm | `blocked` | Noninteractive/interactive worker licensing and concurrency terms |

## Current-scope confirmation

- Personal non-commercial local purpose: `confirmed_by_user_2026-09-01`
- Valid installed Hangul 2020 product seat: `confirmed_genuine_valid_by_user_2026-09-01`
- Evidence: `evidence/user-license-scope-confirmation.20260901.json`

## Future production approvals

- Business owner: `pending`
- Legal/license reviewer: `pending`
- Technical owner: `pending`
- Hancom written approval or contract reference: `pending`

P00-06 passes only for the current personal, non-commercial, local validation scope. Future commercial, internal organization, hosted, server, VM, customer-distributed, and CI/oracle-farm use remains disabled until the corresponding approvals are attached. This file records a fail-closed engineering decision, not legal advice or a transferable license grant.
