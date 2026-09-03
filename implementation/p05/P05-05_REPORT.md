# P05-05 list and numbering report

- Generated: 2026-09-03
- Implementation commits: 4afd8c0, 49ba92a, 25d4880, 21ec808, 31440b5, dd7ebc1, 9597db2
- State: pass_current_pc_local_lists
- Reasoning/review mode: max / target canonicalization, reference closure, sequence and fail-closed audit

`hwpx-package` now exposes the bounded `hwpx-agent.list-definition/1` model for dense numbering and
bullet definitions, ten-level numbering heads, paragraph/outline bindings, semantic deduplication and
typed reference rewriting. The sequence engine separates definition identity from instance identity
and evaluates nesting, continuity, restart, checked bullets and counter overflow without emitting raw
XML or guessing rendered glyphs.

## Acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Source/profile lock | pass | locked KS X 6101 reform-03 structures, locked Hancom OWPML model and exact current Hangul 2020 output |
| Exact current header | pass | one numbering, ten ordered levels and current section outline binding lift exactly |
| Typed definitions | pass | two numberings, one checked character bullet, 21 total heads in the disposable target fixture |
| Bindings/reference closure | pass | NUMBER/BULLET/OUTLINE paragraph headings and section outlineShapeIDRef resolve in their exact ID domains |
| Sequence semantics | pass | nesting, continuity, restart, ancestor return, checked bullets and overflow/transition rejection |
| Deterministic lower/readback | pass | bounded escaped XML, exact typed re-lift and fixed 128-case digest |
| Actual Hangul 2020 target readback | pass | open/read/save/reopen/read/close/quit, text and list semantics preserved, input unchanged, residual process 0 |

## Validation evidence

- Windows Rust 1.96.0: list-definition `14/14`, target-fixture unit tests `2/2`, complete
  `hwpx-package` `155/155`, format and Clippy with warnings denied passed.
- The fixed 128-case list-definition/sequence corpus is deterministic with aggregate SHA-256
  `b3d05ff6709d083cd938d36f163674e3711c47240eb4c10890aa6f5952b9e23a`.
- All six bounded P05 diagnostic PowerShell suites passed `153/153` in the current checkout and
  exact-commit clean checkout. They cover exact x86 PowerShell resolution, timeout and owned-process
  cleanup, progress/trace correlation, independent source rehash, explicit success exit and privacy.
- Current checkout and exact commit `9597db2` clean checkout each passed all `5/5` bootstrap lanes.
  The clean checkout remained Git-clean. Current/clean security scans found zero secrets,
  vulnerabilities or forbidden licenses; SBOM component counts were 273/231.
- Offline Linux used image
  `sha256:bfda7f1ddbf0a192699d4b02dc3dbfefabe5eb7c0dd5527ba31acdaf0e4ab37f`, network disabled,
  repository and Cargo registry read-only, and executable tmpfs only. `hwpx-package --all-targets`
  tests and Clippy `-D warnings` passed.
- Final licensed Hangul 2020 `11.0.0.9136` x86 run used disposable input SHA-256
  `4b50efb9d3030b17bb40045a5d4f0e705aa05c28bc65f9d2b0f63e64a0fda228`. The input remained
  unchanged. The saved output SHA-256 was
  `32bd8479a7854f1562a23131cd744a29a0268d12e5ce40bceddc674001654b60`.
- Hangul input/output canonical-text SHA-256 both equal
  `07713ee094fd2de1c4cf8164eb7ace9b2cd6960e270a4b81ab12166e43a029ce`. Independent product
  inspection passed both files with two numberings, one bullet, 21 heads and product visible-text
  SHA-256 `6f64a4d3e2a862b155ce2982f7678034c99c055e20f3f1e44d8dd9eec16e5d68`.
- The typed list catalogs are equal. The only byte difference inside the list-definition region is
  Hangul's order of the `useImage` and `checkedChar` attributes on `hh:bullet`; XML attribute order is
  non-semantic and no value changed.
- The final trace records 19 valid progress events, terminal pass, child exit 0, output drained,
  source unchanged, cleanup errors 0 and remaining Hwp processes 0. It records no raw document text,
  user-document scan, network, Registry/system change or Computer Use click/type.
- User documents opened or modified: 0. All runtime material was a disposable generated fixture.

## Runtime findings and remediation

The first actual probes were retained as fail-closed diagnostics rather than promoted. Missing manual
approval timed out without an output; the first successful open exposed Hangul's canonical text form;
an early-failure trace and the wrapper success exit were then corrected. A successful save finally
showed that current Hangul 2020 writes a character-bullet `paraHead` with XML level 0 and canonicalizes
the selected `ROMAN_SMALL` head's `checkable` value to true. Commit `9597db2` aligned the strict reader,
writer and fresh fixture with that executable behavior. The canonical fixture then passed without a
semantic rewrite.

## Strict self-review

- Change risk: high; paragraph numbering, outline counters and downstream layout depend on these ID,
  level and restart rules.
- Sparse/duplicate IDs, malformed levels, unknown attributes/children, image bullets, missing checked
  marks, unresolved character styles, incomplete remap tables, invalid nesting and arithmetic overflow
  fail closed.
- The public model exposes no raw XML, arbitrary path, COM/HAction name or platform fallback.
- Actual evidence proves semantic save/reopen on this exact installation. It does not prove marker
  visual placement, image bullets, arbitrary documents, another PC or Hangul 2022/2024.
- Final blocker/major/minor findings after remediation: `0/0/0`.

## Next exact task

Run the already implemented P05-06 custom landscape page-setup fixture through the same exact licensed
Hangul 2020 save/reopen boundary, verify source immutability and product semantic readback, and close
its task report at reasoning effort `max`.
