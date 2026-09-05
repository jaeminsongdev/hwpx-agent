# P05-06 page-setup report

> 2026-09-05 correction: the historical acceptance below used the reversed version-1 orientation
> mapping. Its actual save/reopen/text observations remain evidence, but its landscape/effective
> geometry interpretation is invalidated by attempt21's portrait PDF. P05-06 orientation acceptance
> is reopened. Version 2 repairs the mapping; its actual landscape render acceptance is pending.
> See `P05-07_ATTEMPT21_DIAGNOSTIC.md` and `protocol/migrations/page-setup-v1-to-v2.md` from repo root.

- Generated: 2026-09-04
- Implementation commits: `35b6d2c`, `453e1d4`, `d3ccd05`
- Historical state: `pass_current_pc_local_page_setup` (orientation claim superseded as noted above)
- Reasoning/review mode: `max` / exact-target save/reopen, semantic readback and fail-closed audit

`hwpx-package` now exposes the bounded `hwpx-agent.page-setup/1` model and preserving lowerer for
typed presets/custom millimetres, orientation, margins and gutter axis. Invalid dimensions,
impossible printable areas, malformed XML shapes and bounded-resource failures are rejected instead
of guessed, clamped or partially written.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Typed page setup | pass | unrotated dimensions, independent orientation, margins and gutter type lift/lower exactly |
| Impossible-layout rejection | pass | zero/oversized paper, consumed body, invalid header/footer distance, overflow and malformed shapes fail closed |
| Preserving lowerer | pass | only the exact `pagePr` span is replaced; source bytes remain unchanged and typed readback must match |
| Deterministic fixture | pass | disposable custom 230×310 mm landscape fixture with `TOP_BOTTOM` gutter is bounded and independently inspectable |
| Actual Hangul 2020 save/reopen | pass | exact current target opened, read, saved as HWPX, closed, reopened, read and quit with semantic equality |

## Validation evidence

- Windows Rust target tests passed: page-setup `12/12`, target-fixture `2/2`, `cargo fmt --check`,
  and package Clippy with warnings denied.
- The PowerShell actual-boundary/static suite passed `27/27`, including exact ProgID/build/Registry32,
  STA, fixed input digest, no-overwrite, progress journal, timeout, owned cleanup and privacy checks.
- The successful licensed Hangul 2020 `11.0.0.9136` x86 run used disposable input SHA-256
  `c76816ca35352168955f47cb656ad2cb1ff049192fc10ce46db1465f7f43f0bc`; the input remained unchanged.
- The saved output SHA-256 is
  `795f27e18c2466837445e4afe9e4bcfad7f44468d70af95c925941f47ed2199b`.
- Input and output visible-text SHA-256 both equal
  `cdd685b4d4d8975af196e36a14c3ba12dd7e0f87774e0b51169f0ea63b46ed20`.
- Independent product inspection of the output passed with stored dimensions `65197×87874`, effective
  landscape dimensions `87874×65197`, printable body `80220×53859`, and the same text digest.
- The terminal trace contains 19 valid progress events. Every required phase from COM creation through
  save/reopen/read/quit passed; timeout is false, child exit is 0, cleanup errors are 0 and residual
  `Hwp.exe` count is 0.
- The failed retry 08 remains diagnostic evidence only: it timed out at `open_input`, preserved the
  source, produced no output and cleaned its owned process. It was not promoted into the pass.
- Raw document text, user-document access, network, Registry/system changes and Computer Use
  click/type were all absent. Only the disposable generated fixture was used.

## Strict scope boundary

This pass proves typed page-setup preservation across actual save/reopen on this exact current-PC
Hangul 2020 installation. It does not prove printer feasibility, PDF/render geometry, arbitrary user
documents, multi-section layout, another PC, Hangul 2022/2024, distribution or production use.

## Next exact task

Run the already implemented P05-07 section/column fixture through the exact licensed Hangul 2020
save/reopen and required PDF/render boundary. Require source immutability, semantic section/column
readback, valid PDF evidence, terminal trace closure and zero residual Hangul processes. Continue at
reasoning effort `max`.
