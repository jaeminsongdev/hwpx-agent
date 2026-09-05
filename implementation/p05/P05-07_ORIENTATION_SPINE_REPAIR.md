# P05-06/07 current-2020 orientation and saved-spine repair

- Date: 2026-09-05; parent main checkpoint d354aa2.
- Review: STRICT / HIGH, recommended reasoning max.
- State: component tests pass; FULL/independent/Linux audits and actual repaired render remain open.
- Scope: current PC's licensed Hangul 2020 only. No new Hangul launch or UI input occurred.

## Findings and implementation

Attempt21 establishes that the WIDELY source/saved page settings produce portrait PDF pages.
The old reader and writer both reversed the direction token mapping, so their mutual roundtrip
test could pass while disagreeing with the external renderer. The preserved original input/output,
actual trace and PDF identities are in `P05-07_ATTEMPT21_DIAGNOSTIC.md`.

The correction maps Portrait to WIDELY and Landscape to NARROWLY in this current-2020 profile.
Physical sheet dimensions remain unrotated and only the existing explicit orientation determines
effective dimensions. Preset conversion, margins, bounded XML admission, source immutability and
preserving byte-span replacement are unchanged. New receipts use `hwpx-agent.page-setup/2`; see
`protocol/migrations/page-setup-v1-to-v2.md` from the repository root. Old receipts are not upgraded.
The P05-06 historical report is annotated: its actual save/reopen/text observations remain valid,
but the erroneous landscape/effective-body interpretation no longer qualifies orientation.

The raw-string P05-07 spine check had two defects: legitimate serialization differences were
rejected, and alternate-prefix non-linear items could be concealed by yes-itemref text inside
comments. The inspector now consumes admitted `PackageGraph` spine relationships. It still
requires each actual section relationship to be linear, closed and unique, plus the exact package
spine order and header/body count correlation. The graph's existing default-yes interpretation
matches [OPF itemref semantics](https://www.w3.org/publishing/epub32/epub-packages.html#sec-itemref-elem)
and attempt21's saved section0 omission. No XML parser rule or graph failure was weakened.

## Evidence-driven validation

| Check | Result |
|---|---|
| New orientation/profile regressions before implementation | 4/4 fail against version 1 |
| New saved-spine/comment-decoy regressions before implementation | 3 failures, 7 pre-existing successes |
| Orientation regressions after implementation | 4/4 pass |
| Final target-fixture tests | 11/11 pass |
| Package all-target tests | 193/193 pass, no ignored tests |
| Package all-target/all-feature Clippy, warnings denied | PASS |
| Deterministic 128-case corpus | v2 hash independently reproduced; v1 hash still checked after token-only inverse substitution |
| Actual attempt21 saved HWPX through corrected inspector | Correctly rejects page-setup semantic mismatch after admitting the valid spine |
| Current checkout FULL audit | Not yet run at this checkpoint |
| Exact clean-checkout FULL / actual offline Linux | Not yet run at this checkpoint |
| Fresh corrected 2020 save/reopen/PDF/visual acceptance | Not run; requires a fresh user-present launch request |

Logs are Git-ignored under `artifacts/p05-orientation-repair/`: `orientation-before.log`,
`spine-before.log`, `orientation-spine-after.log`, `package-first.log`, `package-after.log`,
`package-final.log`, `clippy-final.log` and `actual-saved-after.log`. Earlier failed logs remain.
The initial package run failed only on its predecessor corpus pin. An independent integer-only
Python calculation reproduced both old and new hashes; the Rust test now checks both, rather
than discarding the predecessor. New hash and migration details are in the version-2 migration.

The saved HWPX still contains WIDELY and synthetic column IDs normalized to empty values. Neither
is silently accepted as the requested landscape/identity. The saved file's error is now
`target section page-setup semantic readback mismatch`, not the old lexical spine failure.

## Source and qualification limits

The locked KS X 6101 machine-readable source SHA-256 was reverified as
`c4a8bdb082cf8610fa2b3f6e709ca9058ab256a2371e9a779b9b323ca82638e4`.
Section 10.6.6.1 and Appendix E supply the vocabulary but do not establish the installed 2020
runtime mapping from English token names. The 2024 schema default is not transplanted into 2020.
The primary evidence for the diagnosed mapping defect is this PC's actual source/save/PDF result.
The repaired NARROWLY landscape writer still needs its own actual run; pure tests are not that proof.

This is not P05-06/07 or full-product completion. Column control-ID normalization, dense text flow,
balancing, precise separators, exact page geometry and downstream P05-08/09 remain open. Do not
weaken expected PDF orientation or change original evidence to produce a pass. Preserve the
uncommitted PostgreSQL work in the separate P16 worktree; its prior checks do not qualify this repair.

## Next actions

Run current and exact clean-checkout FULL audits and actual offline Linux package tests/Clippy.
Then complete the column identity policy from bounded saved-document and authoritative source
evidence before preparing a corrected actual test. No blind or automatic Hangul relaunch.
