# P09-36 r03 partial native PDF stability — non-green

Date: 2026-10-03. Scope: ONLY the six trace-valid cases from the historical
`p09-35-20261003-r03` batch. This is not the live r05 batch, an input-to-native
comparison, direct-versus-automation differential, form semantics acceptance,
visual acceptance or P09 Gate. User originals and all failed attempts are intact.

## Actual method and outcome

The unchanged original strict binder rechecked each of the six traces, input
identity, exact target/build/module, two independent sessions, zero remaining
processes and all four artifact hashes/sizes. The frozen r04 admission and all
eight source pins were checked. All seven old attempts/35 files, including the
strictly rejected C07 remainingHwp1 trace, were raw-identical before and after.
C08-C15 remain NOT_RUN in that old batch; C07 is not promoted by this report.

Bundled Poppler `pdfinfo.exe` checked both PDFs' page counts. `pdftoppm.exe`
rendered EVERY saved/reopened page at96dpi; PIL12.2.0 compared RGB pixels with
NO masks, tolerance, crop or normalization. Page sizes must match; blank pages
are rejected. Executable hashes and all16 generated PNG hashes are recorded.
Only separate derived PNGs were created, outside the native attempt directories;
no source PDF was edited or re-exported. The16 PNGs total129458 bytes on D:.

| Case | Pages per PDF | Changed pixels | Absolute RGB delta sum |
|---|---:|---:|---:|
| P09-35-C01 | 2 | 0 | 0 |
| P09-35-C02 | 2 | 0 | 0 |
| P09-35-C03 | 1 | 0 | 0 |
| P09-35-C04 | 1 | 0 | 0 |
| P09-35-C05 | 1 | 0 | 0 |
| P09-35-C06 | 1 | 0 | 0 |

Publication AND independent fresh --verify each actually rendered all16 pages
and reproduced the entire17979-byte receipt, SHA
`50838d87059287ce6274f68744ba3ea2ebc34c8101abfb8d211730e871f9022b`:
`evidence/p09-36-native-form-r03-six-pdf-stability.v1.json`.
Five new guards PASS: frozen receipt/six raw sources; all35 files/C07 rejection;
unmasked one-pixel change counted; blank/size mismatch rejected; all eight page
pairs/16 PNGs bound. Initial new tool AttributeError from a nonexistent oracle
export was corrected BEFORE publication; no prior code/pins/receipts changed.

All eight saved page images were visually inspected after rendering. Reopened
images have independently verified byte-identical PNG hashes. The two-section
text/radio fixtures have two visible pages; four other fixtures have one. The
foreground-only fixtures display dark masked text, while the existing-blue-style
fixtures display blue masked text split over two lines. These observations do
not establish expected input appearance or correct form properties. Existing
C01 public reader failure and C02-C06 whole-state/package binding failures stay
FAIL; zero saved/reopened pixel drift cannot conceal them. No human visual
acceptance or permission-click attestation is inferred.

## Source PDFs

- C01 saved/reopened: :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c01-attempt01\saved.pdf" purpose="source"} and :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c01-attempt01\reopened.pdf" purpose="source"}.
- C02 saved/reopened: :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c02-attempt01\saved.pdf" purpose="source"} and :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c02-attempt01\reopened.pdf" purpose="source"}.
- C03 saved/reopened: :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c03-attempt01\saved.pdf" purpose="source"} and :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c03-attempt01\reopened.pdf" purpose="source"}.
- C04 saved/reopened: :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c04-attempt01\saved.pdf" purpose="source"} and :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c04-attempt01\reopened.pdf" purpose="source"}.
- C05 saved/reopened: :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c05-attempt01\saved.pdf" purpose="source"} and :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c05-attempt01\reopened.pdf" purpose="source"}.
- C06 saved/reopened: :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c06-attempt01\saved.pdf" purpose="source"} and :codex-file-citation{path="D:\개발\hwpx-agent\implementation\p09\evidence\private\p09-17-field-auto-number-target-p09-35-20261003-r03-c06-attempt01\reopened.pdf" purpose="source"}.

## Exact next boundary

Continue the SAME live whole15-case r05 native batch/user-owned permissions.
After terminal results, publish/fresh-verify its whole bound evidence, then
perform whole-state/readback, complete projection, render and product differential
against the actual intended operation. This old partial stability receipt is NOT
reused as new r05 acceptance. Green rows remain0; P09 and P10 boundary unchanged.
