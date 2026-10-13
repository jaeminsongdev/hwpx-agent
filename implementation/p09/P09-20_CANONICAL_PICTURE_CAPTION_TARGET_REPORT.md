# P09-19 target run and P09-20 canonical picture successor

Date: 2026-10-02. Goal resumed by the user; P09 Gate remains open.

## Original four-case campaign

Fresh independent COM sessions on Hangul 2020 `11.0.0.9136` x86 used the unchanged
P09-17 one-package lifecycle harness. The old directory prefix is an engine
compatibility restriction, not a P09-17 fixture or semantic qualification.

| Case | Native input | Actual lifecycle | Saved/reopened number | Public successor evidence |
|---|---|---|---|---|
| P09-19-C01 | rectangle 8101 | PASS; 2 distinct sessions; remaining Hwp=0 | 19 -> 1 -> 1; bound caption preserved | `evidence/p09-19-object-caption-target-c01-20261002-attempt01.v1.json` |
| P09-19-C02 | picture 8102, original seed | first Open failed twice; remaining Hwp=0 | NOT_RUN | `evidence/p09-19-object-caption-target-c02-20261002-attempt01.v1.json`, `...attempt02.v1.json` |
| P09-19-C03 | table 1188510574 | PASS; 2 distinct sessions; remaining Hwp=0 | 19 -> 1 -> 1; two native tables preserved in inventory | `evidence/p09-19-object-caption-target-c03-20261002-attempt01.v1.json` |
| P09-19-C04 | equation 1192022476 | PASS; 2 distinct sessions; remaining Hwp=0 | 19 -> 1 -> 1; bound equation caption preserved | `evidence/p09-19-object-caption-target-c04-20261002-attempt01.v1.json` |

All permission interaction is `user_attested` only. The public records independently
bind trace/input/output identities. The original standalone oracle continues to
report `actual_hangul=false`: it is a snapshot inspector, not a lifecycle authority.
The new qualifier adds lifecycle evidence without rewriting that oracle or its
historical claims. All five records reproduce with `--verify` against pinned hashes.

Preserved trace SHA-256 locks:

- C01 attempt01: `5aff9b74b6534685a87b353cf8e5a320716ca29b70fc95907bbc9978f25f19f1`
- C02 attempt01: `3299a2348fadd1b33d9382003bf5373a2f2a2a350eee407598764243d420c3d7`
- C02 attempt02: `7855db1d23690b1a5f1233f930c6c264a35255646acb00a74b347547aa2c24c8`
- C03 attempt01: `8517234774b1f38ac57128a76da1b1c6440cc14cb2741e64dcbe467eb80a396a`
- C04 attempt01: `d08d5fa583c81974819853f7b879e0372b66fe24add1dccc8f00f4bd3b6115f9`

## Picture failure isolation and correction candidate

The unnumbered original P08 image input failed the same Open step in a separate
control run. Control trace SHA-256:
`e720accd15af809cd54161dcca71f2eccd48a11e57cc070dd2309f04712cbc83`.
Thus the failure precedes number insertion. Exact causation is not yet proved.

The original package uses a hash-named binary part and places `img` before
`imgRect`; P08-20 attempt18's real saved picture uses `BinData/image1.png` and puts
`img` after `imgDim`. These are observed differences, not a causal conclusion or a
general format-normalization policy.

New fixture-only generator:
`crates/hwpx-package/examples/p09_20_canonical_picture_number_target_fixture.rs`.
It uses the exact captured canonical package rather than rewriting the failed
input. Native P09-18 field insertion and preserving package logic are unchanged.
The original C02 input and all three failed/control attempts remain preserved.

Three exclusive bundles under `fixtures/target-build/`:
`p09-20-canonical-picture-number-target-20261002-01`, `...-02`, `...-03`.
Each manifest SHA-256:
`6dbc3dfe553753e08292338229ce3c5a4470f5bd33f99678c05da960d07000e9`.
The third regeneration used the final rustfmt-normalized successor source.
Static source/resource reversal, all non-section parts, native identity, cached 19,
complete package graph and deterministic retry passed. No captured original was
edited. The canonical seed's old target PASS was not inherited by this new file.

Current live canonical target attempt:
`implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-20-20261002-c02-attempt01`.
The user completed permission interaction; the existing call was resumed rather
than duplicated. Two distinct exact-target COM sessions passed Open/save/PDF and
fresh reopen/save/PDF; remaining Hwp process count is zero. Computer Use only
observed the exact successor path and `접근 허용(Y)` button; no automated click,
typing, security setting or registry change occurred.

The independent successor qualifier verifies one preserved native picture and its
caption binding, with input/saved/reopened number **19 -> 1 -> 1**. Public receipt:
`evidence/p09-20-canonical-picture-caption-target-c02-20261002-attempt01.v1.json`,
SHA-256 `66504fbde191d7841aa19ea6eeb8af90c32875fb395f2bd616d1147361346e5b`.
Exclusive publication and read-only `--verify` reproduction both passed.
Trace SHA-256 `b91fbfc649cac5e8dc84185e9f21e073acf5cb2967a637e88bd4208bd7740bcb`;
saved package `747c604ada6b482854c912447089fd6bd4f53395a5a3a52421f45e43e11ca788`;
reopened package `4c4a67d829443eced941432d46e727d27da9f2d9f3ebd873c98811bb3592b002`.
This is bounded semantic evidence, not general numbering/update/render/fallback
qualification. Original failed picture inputs and receipts remain unchanged.

## Render observations, not a render Gate

Original C01/C03/C04 saved and reopened PDFs have separate lifecycle hashes.
Each reopened PDF has one A4 page and was rendered at 96 DPI with Poppler.
Model inspection observed:

- C01: number/text are present, but the original colored rectangle is not visible
  in this PDF render. Object visual fidelity is unresolved, not PASS.
- C03: the two table outlines and numeric caption are visible. No calibrated
  preservation/differential oracle exists for this candidate.
- C04: native `x+2` and the number are visible, but the copied caption text has
  narrow/broken layout. This is not acceptable full-caption render evidence.

These observations do not identify whether inherited seed layout, native print
behavior or the new caption caused a defect. Preserve the PDFs and renders for
controlled baseline comparison. `render=NOT_RUN` in machine qualifications means
the required calibrated render oracle was not run, not that no PDF was inspected.

The canonical C02 reopened PDF was also inspected at 96 DPI: the checkerboard
picture and numeric caption are visible. The caption fixture has no added spacing
between its inserted number and copied text; no general caption-layout acceptance
is claimed.

The unchanged `tools/p08/object_target_oracle.py::validate_pdf_pair` was called on
each exact hash-bound saved/reopened PDF pair with `feature=""`, which permits no
calibrated tolerance. All four pairs are one 794x1122 raster page, with **zero
changed pixels, zero channel delta and no difference bbox**. Nonwhite bboxes:
C01 `[113,133,277,328]`; canonical C02 `[113,133,278,264]`;
C03 `[117,136,677,394]`; C04 `[114,133,143,202]`.
This proves save/reopen PDF stability only: a stable missing shape or narrow
caption is still not full render acceptance, and no automation differential ran.

## Current verification

- New original-case lifecycle qualifier: 8 unit/negative tests PASS.
- New canonical preparation/lifecycle qualifier: 10 tests PASS, including
  tamper/stale/privacy/independent-session and no-false-green checks.
- Full P09 Python suite before the P09-21 addition: **137/137 PASS**;
  current suite after addition: **146/146 PASS**, no skipped test on this PC.
- Rust workspace locked/offline all-target/all-feature tests: **PASS**,
  **265 result summaries, 0 failed summaries**.
- Workspace Clippy with the same flags and `-D warnings`: **PASS**.
- `cargo fmt --check`, `git diff --check`: **PASS**.
- P09 aggregate: **PASS**, retaining 35 unit + 11 static integration,
  7 P11-deferred, 0 oracle/green. P09-19 pinned preparation still PASS (8 inputs).
- Frozen P17 v48: **PASS**. Existing P08/P17 sources and old receipts untouched.
- P09-21 exact additive-export dependency-source bridge: **PASS, non-Gate**;
  all 25 required validators execute, with nine historical full-lib-lock failures
  preserved and all other old implementation locks independently reproduced.
  See its separate source report; legacy aggregate remains a failure.

## Remaining work

The live canonical picture attempt and independent native output binding are now
complete. Compare native baseline/numbered render and derive an exact, bounded
field/render oracle, preserving the unresolved rectangle/equation observations.
The current P08 additive-export dependency source is separately qualified without
rewriting old receipts; implement the next dependency-ready P09 field family. The general update API, actual
automation fallback and direct/automation differential remain unqualified.
P09/P09~P20 are not complete and P10 remains held. No commit/push is implied.
