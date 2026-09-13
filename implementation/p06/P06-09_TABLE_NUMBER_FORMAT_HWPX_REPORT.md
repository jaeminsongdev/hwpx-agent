# P06-09 table number-format HWPX report

- Generated: 2026-09-13
- Adapter schema: `hwpx-agent.table-number-format-hwpx/v1`
- Native profile: `hwpx-agent.table-number-format-hwpx.hancom-2020/1`
- Exact target: Hangul 2020 `11.0.0.9136` x86 `ko-KR`
- Result: `integration_pass`
- Recommended next-step reasoning: `max`

## Result

TABLE-049 now has an exact preserving section adapter for current-target native general, integer,
and one through four decimal-place formats. It reads the complete unmerged grid and exact selected
formula owners, maps native result-format grammar to typed state, and changes only `Command`,
`ResultFormat`, `LastResult` and visible-result text.

Request creation binds section, selected formula/native-grouping state, grid, semantic document
flow and domain-plan digests. Build repeats every check, applies bounded edits, performs independent
typed readback and verifies that all unowned section bytes remain identical. Strict JSON rejects
duplicate and unknown keys, and Debug redacts formula values, native metadata and hashes.

## Exact-source evidence

Attempt `20260913-05` passed the licensed target watchdog with 50 ordered events and terminal
`pass`. It completed six formula actions, six user-owned dialog choices, six grouping removals and
six grouping additions; all three immutable HWPX artifacts and their receipts are present. The run
left zero Hwp processes and had no user-document, network, registry/system-setting or Computer Use
click/type effect.

Offline readback found 11 entries, one 6-by-3 grid and six formula fields in all packages. The
native tokens are `%g,`, `%.0f,`, `%.1f,`, `%.2f,`, `%.3f,` and `%.4f,`. Formula ASTs, normalized
numeric caches and grid state are preserved. Save metadata and an explicit/default `linear=yes`
spelling differ in `content.hpf`; the semantic spine/manifest flow is equal and all three raw flow
hashes are retained separately.

Five direct number-format plans produce the grouped native section with 18 owned-text edits. After
one separately qualified TABLE-033 general-grouping edit, five number-format plans produce the
ungrouped native section with 19 owned-text edits. Both full sections match Hangul output exactly.

## Verification

| Check | Result |
|---|---:|
| Dedicated HWPX adapter tests | 6/6 PASS |
| Private contract and tamper tests | 4/4 PASS |
| Source harness static tests, PowerShell 7 | 24/24 PASS |
| Source harness static tests, x86 Windows PowerShell 5.1 | 24/24 PASS |
| Exact grouped native section differential | PASS |
| Exact ungrouped native section differential | PASS |
| Request/build section-state-grid-flow-plan drift | fail closed |
| Unsupported token/value/format and ambiguous grouping | fail closed |
| Bounded strict JSON and redacted Debug | PASS |

## Conformance impact

The direct-stage matrix changes only as follows:

- `unit_passed`: 2 to 1
- `integration_passed`: 34 to 35
- `cataloged`: remains 0
- `oracle_verified`: remains 25
- green rows: remains 0/61

Direct-output package save/reopen, PDF/render, rollback/retry, product automation runtime and
release differential are not run. No P06-09, P06, production or product-complete claim is made.
