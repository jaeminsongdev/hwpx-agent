# P06-04 product target Hangul 2020 readback report

Date: 2026-09-07

## Result

P06-04 passes its bounded current-PC product-target Gate on the licensed Hangul 2020
`11.0.0.9136` x86 installation. This report does not claim another build, Hangul 2022/2024,
arbitrary user documents, P06 completion, production, or product completion.

## Bound target and runtime evidence

- Product input SHA-256:
  `264b062c8a2477cf4167cef5b9db7d51a83594ed024b572d7ff2ea533a48d28a`
- Canonical visible-text SHA-256 before and after save/reopen:
  `bb08e74666ab920d5e264bf930ead508c1d83de73a5f0c54890c694038f04037`
- Hangul-resaved HWPX SHA-256:
  `b00268f091ab6c6c7474b270c9fab428e75cca1844350ada24d6dedb5e6d6906`
- Exported PDF SHA-256:
  `9afc50ba71742798f9ae8953fbd12e2b1ae3e625fcd80466b0e4453bcf4f3d12`
- PDF size: 10,554 bytes; `%PDF` signature valid; one A4 page; creator is the exact Hangul build.
- Trace: `fixtures/target-build/p06-04-cell-style-source-20260907-04/target-readback-trace-04.json`

The bounded x86 STA worker passed COM creation, input open, input text read, create-new HWPX save,
input close, output reopen, output text read, PDF export, output close and quit. The input digest was
unchanged, no raw document text was written to the trace, no user document was scanned, no network,
registry or system-setting change occurred, and the remaining Hwp process count was zero.

## Semantic and visual review

The table-cell style/content digest is
`7025569f26b2efe253f1e41a1e404093fa288be46af6e199e786bc91561621c6` both before and after the
Hangul round trip. The PDF displays all four synthetic markers without clipping or overlap and
matches the deliberately varied target combinations: horizontal/top, vertical/center,
vertical-all/bottom and horizontal/center. The differing border, margin and protection fixtures do
not alter the marker text.

Attempts 01-03 remain failed diagnostic evidence only because they timed out at the user-controlled
open-input access prompt. They are not counted as PASS and were not deleted or rewritten.
