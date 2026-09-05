# P05-07 v3 attempt 21: readback passes, layout acceptance fails

- Date: 2026-09-05, 21:05 KST; current licensed Hangul 2020 11.0.0.9136 x86 only.
- Trigger: a fresh user-present request to show any required access prompt now.
- Implementation: main checkout 8094b4c; unchanged bounded readback wrapper and v3 fixture.
- Result: actual open/save/reopen/text/PDF export PASS; complete P05-07 acceptance NOT PASS.
- No additional user action is currently required. Do not automatically relaunch Hangul.

## Execution and safety

The wrapper used new attempt21 output, trace and PDF names, with the existing 600-second watchdog.
Preflight found no Hwp process. Worker 31488 created Hwp 43524; the 21-event journal ends at
terminal/pass. Session 13431 terminated exit 0. Both input and saved/reopened output have the
unchanged expected two-section text digest. PDF export succeeded. Quit passed without forced
cleanup, and both wrapper and independent process queries found zero residual Hwp processes.
The original v3 input and earlier evidence remain unchanged. No Registry/security setting or
user document was changed; no Computer Use click, typing or activation was performed.

Window enumeration observed the fixture and blank-document windows. A subsequent screenshot
request failed with `foreground window did not report a process id`; no screenshot of the
permission dialog was obtained in this attempt. The execution journal establishes successful
opening, not which permission button the user clicked. No click is inferred from that journal.

## Independent checks and findings

1. The existing product fixture inspector was run using `cargo run --locked --offline -p
   hwpx-package --example p05_07_section_columns_target_fixture -- inspect <saved-output>`.
   It failed with `target multi-section spine is not linear`. Direct package inspection shows
   the original section0 itemref has explicit `linear="yes"`, while Hangul's saved section0
   itemref omits `linear`; section1 remains explicit yes. Header changes from no to yes. This
   is a confirmed serialization difference and an exact-string checker rejection, not proof
   that section0 became non-linear. Validate the format default before changing that checker.
2. The unchanged tracked PDF expectation was copied byte-for-byte into the fixture boundary.
   `verify_p05_hancom_pdf.py` failed with `PDF_PAGE_GEOMETRY_MISMATCH`. Expected dimensions are
   310 x 230 mm on each of two pages; actual PDF MediaBoxes are approximately 229.658 x 309.739 mm,
   with rotation zero. Both pages exist and each contains only its respective expected marker.
   Do not swap or relax the expectation to turn this result into a pass.
3. A separate diagnostic render using the same Poppler binary produced both pages at 96 DPI.
   Both complete images were directly viewed. They are portrait, have readable section markers
   and short colored separator strokes, and retain large blank areas. This sparse fixture does
   not prove long-text column flow, balancing or precise column positions. These diagnostic
   images are not successful output from the failed formal PDF verifier.
4. Bounded read-only XML comparison shows both saved sections retain `pagePr` values
   `landscape=WIDELY`, width 65197, height 87874 and gutterType TOP_BOTTOM. Both `colPr` structures
   retain their type/layout/count/width/gap/separator values, but their synthetic control IDs
   become empty strings. Whole typed semantic equivalence has not passed: the inspector stops
   at the earlier spine check. Investigate the page dimension/orientation model and ID contract
   without claiming these byte observations alone close preservation acceptance.

## Evidence

All files are under `fixtures/target-build/p05-07-current-2020-20260905-v3/` and remain Git-ignored.

| File | SHA-256 |
|---|---|
| p05-07-section-columns-input.hwpx | dc2d385ecdc60a396f5740d604b8ce379f25733c87bf98ed3e3baa32291e49a5 |
| p05-07-section-columns-output-attempt21.hwpx | f241e5475c9366b8eebd49245316b60bdba7cce6d29c2ffdbfbee8fdff0bb304 |
| p05-07-section-columns-render-attempt21.pdf | a19618708ea27a74f8bb8acb812cc03ba65bf06b297467b0c69a08be187db056 |
| p05-07-hancom-2020-trace-attempt21.json | 1ea790d024600bdb0c21d2bd683ec2e8b692c5bc120439152c5fe9c3b1783a39 |
| p05-07-hancom-2020-trace-attempt21.json.progress.jsonl | 320b19b69f77790fe94eda35c867b0c734a6468a2c04297391995b8e85fc9c7f |
| p05-07-pdf-verification-attempt21.json | 28bd713b62d5e2e34de2ba84815c151722dbd31c96424d4510515dfbcc6154ba |
| p05-07-attempt21-diagnostic-page-1.png | fa12ed4563f9b6b3264a38de9148deb1bcdb6ea80b4e8df64f3f0cc2e54bd20c |
| p05-07-attempt21-diagnostic-page-2.png | ca93b8e426570cae98cd5048404a1ab5ee337591513fe46d48b34cd2aa416092 |

Expected and actual normalized input/output text digest:
`92d2179169f1102d256589c2ca90b8422405076927d91c6e5ba2e91f28381d2f`.
Poppler pdftoppm SHA-256: `3f2440140fef98ddd1ef0772a10d8e58dc3564a9b15a14b4611b5bbd5bdcd37f`.

## Next bounded action

Use this saved HWPX/PDF for offline investigation first: establish the spine default, control-ID
normalization policy and page-orientation contract from locked sources and current-2020 evidence.
Repair actual implementation defects with failing-before/passing-after regressions; preserve all
expectations and failed evidence. A new actual-Hangul run needs a fresh user-present request.
P05-07 and P05 Gate stay open, and later-version/registered-host claims remain unverified.
Recommended reasoning: max for document preservation, normalization and the eventual Gate audit.
