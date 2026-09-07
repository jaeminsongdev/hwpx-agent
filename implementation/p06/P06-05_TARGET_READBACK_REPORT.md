# P06-05 calibrated target readback report

Date: 2026-09-07

Decision: **PASS for the exact current-PC Hangul 2020 P06-05 fixture**.

## Bound target

The calibrated builder consumes only the repaired target SHA-256
`b2887c929cdeb81fa1f5f3bac086265e19fb92a8bbf063f75e5ab0fbfa5cb299`, installed-font receipt
SHA-256 `c4755f99ebf1e49010bf26425d61f77c496fa713d86404004348027acfc1d2ab`, and exact prior Hangul
save SHA-256 `09f3e8b27167a43650d710f6338b5712655e9fd70a30cef9c97dbe28abab1954`.
It applies a 350-micrometer left-column guard to cross the observed 100-HWPUNIT Hangul line-box
bucket. Three create-new outputs are byte-identical at SHA-256
`3dfcf2a185a4129989b29877b7df7dadb638071aed5ccddd1476e46f76d9bcb5`.

The calibrated verified plan is 70,000 micrometers wide with columns `53340,16660`, estimated rows
`13758,4586`, grid SHA-256 `2c21be8ef4d42da0b4c387395a235a9978bf53c7480f4159f815795799633c49`,
and plan SHA-256 `7a9c19014be2ceffb5648d62270bd42ed67ac0db46f0b16101b5174ae2218cf3`.
Pre-runtime target readback is table `19843 x 5200` HWPUNIT, cell widths
`15120,4723,15120,4723`, cell heights `3900,3900,1300,1300`, inherited margins
`510,510,141,141`, and content digest
`5542afbe344fa447f2598491ec7e0f7b473b2832402bfd203f26713d6448d86c`.

## Calibration history

The zero-guard target opened and completed its lifecycle, but actual cell line counts were
`1,3,2,1`; cell C did not match the one-line intent. A four-micrometer guard produced the same line
counts and the same `14000,3800` HWPUNIT line-box widths. These runs are preserved as failed semantic
calibration evidence and are not promoted to PASS.

## Actual Hangul 2020 oracle

The exact licensed x86 Hangul 2020 build `11.0.0.9136` opened the calibrated target after the user
approved file access. Every bounded phase passed: COM creation, input open/read, create-new HWPX
save, close, output reopen/read, PDF export, close, and quit. The input remained unchanged, visible
text SHA-256 stayed
`a73ff5335c34949be0d3a539eaf7d86404f2045cd9315f5f43b9e28836fd28d1`, and no Hwp process
remained.

The saved HWPX SHA-256 is
`ec08dc8e07dfc1b18c5916b44917b00d27da9905bea26f57e9b16991396c1ec7`. Actual regenerated cell
line counts are `1,3,1,1`, line-box widths are `14100,3700,14100,3700`, and line text positions are
`[0]`, `[0,5,8]`, `[0]`, `[0]`. All target cell widths/heights, margins, row/column topology, and the
content digest remain exact. Hangul regenerated only the aggregate table height from `5200` to
`5782`; this is renderer-owned derived geometry and not a requested cell-dimension drift.

The exact PDF SHA-256 is
`6e929f5cf56d2ac0c36587c5bdfd60f41a4d100b35c72356d85bb3ea1cf54606`, size 15,421 bytes, with a
valid PDF signature. Visual review of the rendered page confirms that all four intended strings are
visible, cell C stays on one line, cell B wraps to three lines, and no content is clipped or overlaps
a border.

The trace SHA-256 is
`8de3eac36c748b3852b517a8e302ab5b8062d672279b1b7963dab839b4fdbf19`. It records no raw document
text, user-document scan, network action, registry/system-setting change, or Computer Use click/type.

## Gate boundary

Contract `hwpx-agent.p06-05-table-layout-target-contract/v2` binds the builder, immutable v1
predecessor, calibration history, exact artifacts, trace semantics, HWPX line-cache oracle, and PDF.
Within the requested current-PC scope, P06-05 is complete. This report does not claim arbitrary user
documents, another PC or Hangul version, P06 phase completion, production, or product completion.
