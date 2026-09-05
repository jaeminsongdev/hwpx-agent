# P16-06 MAIN integration audit

- Date: 2026-09-06; review STRICT / risk HIGH; recommended reasoning `max`.
- Audited commit: merge commit `0512883fbae9503a22fcd0a0950d13029656176b`.
- Decision: source composition, local service components and current-PC disposable PostgreSQL PASS.
  P16-06, registered-host, real document execution and the complete product remain open.

## Exact integration boundary

The merge has exactly two parents: MAIN `9cc1db3b222a8e8f2b79ebf9ade7e3c8d6813a98` and the
qualified P16 implementation `62542b0e0126f0687f97fcb2c1357c3600d87fdf`. The explicit
integration successor validates all declared predecessor/current replacement pairs and retains
`phase_complete: false`, `actual_hangul: false`, `registered_host: false` and `production: false`.

The current checkout actual PostgreSQL run `20dff2d03ef04bb39abce731d9331565` passed all 25 ordered
migration, rollback, encrypted-blob, restart, ACL, quarantine, role, RLS, privilege, tenant-isolation
and final-readback checks. Its 21 runtime sources are exact-bound and its UUID-owned resources were
removed. The portable successor records the LF-normalized receipt separately from the original
Windows receipt so Git line-ending conversion cannot manufacture a clean-checkout failure.

## Current and detached clean-checkout evidence

| Check | Current MAIN | Detached `0512883` |
|---|---:|---:|
| Integrated source qualification | PASS, 6 replacements | PASS, 6 replacements |
| Integrated PostgreSQL qualification | PASS, 21 runtime sources | PASS, 21 runtime sources |
| Actual disposable PostgreSQL | PASS, 25/25 | PASS, 25/25 |
| P14 Python regression | PASS, 132/132 | PASS, 132/132 |
| P15 Python regression | PASS, 84/84 | PASS, 84/84 |
| P16 Python regression | PASS, 144/144 | PASS, 144/144 |
| Plan-review widget | PASS, 126/126 | PASS, 126/126 |
| Repository CI lanes | PASS, 5/5 | PASS, 5/5 |
| Security failed/forbidden | 0/0 | 0/0 |

The independent checkout is `D:\개발\hwpx-agent-audit-main-0512883`. Only the four exact,
hash-pinned P10 JSON records required by repository validation were hydrated. No HWPX/PDF/user
document, private signing key, database or browser profile was copied. Dependency restore reused the
local pnpm store with zero downloads. Its actual PostgreSQL report is run
`827b7df672264573a69f80993db50921`, SHA-256
`02813ab115bcd180320b79511932e42a9f94117e569352b86c4b25859fcbab91`; all owned resources were
removed. Its five CI lanes passed in 53.045, 75.023, 11.446, 2102.818 and 17.357 seconds. Security
run `f50aaa24160940468ad752fedd4f0eb0` had zero failed checks, zero forbidden licenses and 813 SBOM
components. The independent Git tree remained clean and detached at the exact audited commit.

## Preserved limits and next implementation

No validation above launched Hangul or crossed the COM boundary. It does not prove a registered
ChatGPT/Codex host, remote MCP, production IdP, durable production authorization/idempotency,
assistive technology, another PC or Hangul 2022/2024. The compiler-plan registry remains
process-local and its `PlanSourceRepository` has only a test adapter; the actual renderer is not
wired to an authoritative durable source/plan lookup. Implement that bounded service path next,
then rerun target, current and detached validation before any P16-06 closure claim.
