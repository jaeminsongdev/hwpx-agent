# P05-07 dense automatic column-flow policy

- Scope: fixed synthetic fixture on the current licensed Hangul 2020 `11.0.0.9136` x86 target.
- Product profile: `hwpx-agent.hancom-2020-dense-column-flow/v1`.
- Render expectation: `hwpx-agent.p05-render-expectation/v2`.
- Reasoning/review mode: MAX / HIGH-STRICT.

## Purpose and separation

Attempt23 proves the exact two-section sparse fixture's landscape page, column values, save/reopen,
PDF export and bounded logical identity rebinding. Its one short marker per page cannot prove that
ordinary text automatically flows from the first column into the second or that a balanced column
section finishes at comparable vertical positions.

This successor is a separate single-section fixture. It does not alter or replace attempt23 and
does not reuse its identity exception. It contains one fixed balanced two-column section, 31 bounded
paragraphs, zero explicit column-break paragraphs, a unique start anchor in the title and a unique
end anchor in the final body paragraph. The column control ID is empty at source because that is the
exact current Hangul 2020 baseline shape. The earlier nonempty-ID fixture remains the authoritative
evidence for backend identifier removal and logical rebinding.

## Typed source contract

`Hancom2020ColumnFlowPolicy` keeps `ExplicitMidpointBreak` and `AutomaticBalanced` distinct.
The existing P05-09 constructor still selects the midpoint-break profile and keeps its nonempty
fixture control ID. `new_automatic_balanced` selects a separate profile, lowers no column-break
paragraph, uses the current-target empty control ID, and is admitted only when semantic readback
finds exactly zero explicit breaks. More than one break, a profile/ID mismatch, page/column drift,
text drift, dangling IDs or an incomplete package graph fails closed.

The deterministic prepared fixture is ignored local evidence at
`fixtures/target-build/p05-07-dense-current-2020-20260906-v1/`:

| Artifact | SHA-256 |
|---|---|
| input HWPX | `eee4e18ec85f51592b574d02c21bbf59d20143f0ef78db9704b773724654ec23` |
| initial one-page expectation used by failed PDF verification | `785fe01f866f6b4a7db024447f6aecfeac9a88325fe9576af86596e9c9aabd1c` |
| corrected two-page expectation prepared for the next run | `6ca7926efb1b9e6f9c1c8b0b5cce97cb8ae69ae91640b1bcc3cdbc62f67d0ad3` |
| canonical visible text | `21c67a1e9786886923a8d803cee9cd46d2881967e1f17f91f5f93f872f838b83` |

Build and independent semantic inspection both report 31 paragraphs, zero explicit column breaks,
body width 80,220 HWPUNIT, two equal columns and a 1,700 HWPUNIT gap. These are source-fixture facts,
not Hangul execution or render evidence.

## PDF position and balance contract

Render expectation v1 remains byte-compatible for prior P05 evidence. Version 2 adds one exact
`column_flow` object per expected page. The verifier composes each nonempty PDF text fragment's text
and content matrices, converts its origin to milli-mm, and fails closed on non-finite matrices,
off-page coordinates, missing or duplicate anchors, underfilled columns, wrong anchor sides or an
excessive bottom-baseline delta.

For each fixed landscape page:

- the split is 156,000 milli-mm with a 3,000 milli-mm exclusion guard;
- each side requires at least eight positioned text fragments;
- the start anchor must be left of the guarded split and the end anchor right of it;
- the lowest left/right text baselines may differ by at most 12,000 milli-mm;
- only hashes, counts and coordinates enter the verification receipt; raw text is not emitted.

The first actual execution preserved the source and saved semantics but the first PDF verification
failed closed with `PDF_PAGE_COUNT_MISMATCH`: the 30 body paragraphs occupy two balanced pages, not
the one page assumed by the initial expectation. That failed trace and its original expectation are
preserved. Coordinate-only calibration found both pages populated on both sides. The successor
expectation therefore declares two pages before a fresh execution: page 1 binds start/line 20 and
page 2 binds line 21/end across opposite columns, with cross-page forbidden markers. This is not a
retroactive PASS for the first attempt.

The v2 contract is not a general PDF layout engine. It supports rotation zero only, checks text
origins rather than glyph bounding boxes, and is qualified only for this fixed target profile.

## Acceptance boundary

The dense-flow subgate remains open until the exact prepared input is run through the bounded
Hangul 2020 open/save/reopen/text/PDF lifecycle, the saved HWPX passes the dense semantic inspector,
the v2 PDF verifier passes, and the rendered PNG is visually checked. Source immutability, exact
binary/build identity, progress journal completion, process cleanup and artifact hashes remain
mandatory. A failure or permission timeout is preserved as evidence and is never rewritten into a
PASS. This work does not qualify Hangul 2022/2024, arbitrary documents, P05-08/P05-09, or the full
P05 phase Gate.
