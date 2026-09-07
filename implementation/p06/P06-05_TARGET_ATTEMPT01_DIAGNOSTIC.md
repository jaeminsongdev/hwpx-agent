# P06-05 target attempt 01 diagnostic

Date: 2026-09-07

## Exact attempt result

The first licensed current-PC Hangul 2020 run used exact target SHA-256
`a678588188593c250b33205f1660fef6c301280cd5ae30deb4b6a03f185055bc`, `HWPFrame.HwpObject.2`,
32-bit Windows PowerShell STA, Hangul file version `11.0.0.9136`, and the hash-bound executable.
The user completed the visible file-access approval. COM creation passed, but `Open` returned
`false` and the bounded runner emitted `TABLE_LAYOUT_READBACK_INPUT_OPEN_RETURNED_FALSE` at
`open_input`.

The input digest remained unchanged. Text readback, save-as HWPX, reopen, geometry/wrapping review,
and PDF export were not run. Quit passed, the watchdog did not time out, output was drained, and no
`Hwp.exe` process remained. The trace is preserved at
`fixtures/target-build/p06-05-table-layout-20260907-02/target-text-discovery-trace-01.json` with
SHA-256 `42a15b0f44fd34c2a46466ff81b6108f661f04f09fcc395aa5e8212583bd06fa`.

## Root cause and disposition

The rejected target had changed cell texts and geometry while retaining source-generated
`hp:linesegarray` caches. Their cached text positions no longer matched the edited text lengths;
for example, one four-character target cell retained positions extending through seven. This is
the concrete package defect consistent with the exact `Open=false` boundary.

The rejected bytes and trace remain immutable failed evidence. They are not a PASS and provide no
semantic or visual claim. Builder `/v2` supersedes them by deleting the exact stale cache elements
and requiring Hangul to regenerate layout. That new target still needs its own licensed runtime
Gate.
