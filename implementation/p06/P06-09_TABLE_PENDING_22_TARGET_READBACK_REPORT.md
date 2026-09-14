# P06-09 pending 22 table target readback report

- Date: 2026-09-14
- Target: licensed Hancom Hangul 2020 `11.0.0.9136`, `ko-KR`, x86 on this PC
- Attempt: `p06-09-table-pending-22-target-20260914-21`
- State: direct evidence `oracle_verified` for 22/22 rows
- P06-09/P06 state: `in_progress`

## Result

The remaining 22 direct-table candidates passed in one HWP session after the user selected the
file-access dialog's `모두 허용` choice. That interaction is recorded only as
`user_attested_allow_all`; Computer Use did not click or type. The exact-target trace completed all
22 save, close, reopen and PDF-export lifecycles with 361 ordered progress events. All source inputs
remained byte-identical and no owned HWP process remained.

The independent typed oracle passed 22/22. Every 144-DPI page render was then inspected at original
detail. Split/merge, geometry, placement, style/transpose, numeric formatting, nested table, sort,
autofill and absolute-reference results were visible, including the nested outer/inner table and the
autofill/reference BEFORE/AFTER markers. No clipping, overlap, blank page or black box was observed.

| Evidence | SHA-256 |
|---|---|
| lifecycle trace | `df5d7bfcf79e884280a7bfad86dbcd8337f73ec3b020844eff096fe3b5429f9d` |
| typed-oracle receipt | `ca42930e285f5da6ed7e44324d571970ba0083b89be4c661f45f35bd46d227e1` |
| render manifest | `a75c0cd72a1e854ccd9ce2cfd5832544a1595697b4e1c16999e24402d5a5530f` |
| visual observations | `2bc059cad942536393449f1fc8348e061e9e2ccf90f2e82d97b9c967c05984fb` |
| final visual receipt | `b74dd57945a63179087d294c48c9592d5ef34c56c87a8957d0ecfc1cdef02148` |

Public target evidence is
`implementation/p06/evidence/target/p06-table-pending-22.current-2020.attempt21.v1.json`.

## Fix and reproducibility boundary

TABLE-054 initially exposed native Hangul serialization drift inside the nested table. The direct
adapter now normalizes only the nested semantic payload for the exact native defaults while keeping
ordinary table payload semantics strict. A regression proves that a non-default page-break value
still fails. Fresh layout/placement and remaining-table fixtures were independently rebuilt three
times with stable manifests, and merge/split was rebuilt in a clean target directory.

Attempts 01 through 20 and their failures remain preserved. Attempt 21 is a new bounded retry, and
its success retained immutable inputs, published only completed outputs, and left zero owned HWP
processes. This closes the direct target-build, typed-oracle, render and retry evidence for these 22
rows.

## Gate boundary

This report promotes only the 22 direct rows from `integration_passed` to `oracle_verified`.
Automation product-runtime qualification and the direct/automation exact differential remain
`not_run`. It does not claim P06-09 completion, P06 completion, arbitrary user-document
compatibility, another PC/version, production readiness or product completion.
