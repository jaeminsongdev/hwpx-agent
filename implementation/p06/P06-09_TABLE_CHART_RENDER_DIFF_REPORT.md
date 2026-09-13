# P06-09 TABLE-006 render-diff calibration report

- Result: `calibration_fit_pass`
- Required `render_diff`: `not_run`
- Rollback/retry: `not_run`
- TABLE-006: `integration_passed`
- P06-09/P06: `in_progress`
- Product complete: `false`

## Calibration result

The exact native-reference and direct-product lifecycle outputs each reopen as one table, nine
cells, one 3D vertical-bar chart, two series and the same ordered ten cache values. Chart anchor
size, placement, wrapping and margins are equal after excluding the deliberately distinct object
ID. Neither package contains explicit chart-title text.

Both PDFs identify Hangul 2020 `11.0.0.9136` and Hancom PDF `1.3.0.550`, are unencrypted one-page
A4 documents, and extract the same eight table words at exactly equal positions. At 150 DPI their
ink bounding boxes are equal. Pixel differences are confined to the automatic default-title area;
the observed differing-pixel ratio is below 0.001 and mean absolute channel delta is below 0.05.

## Decision

The deterministic profile and tamper checks are frozen, but this attempt is calibration rather than
qualification. The machine matrix therefore remains unchanged at 0 cataloged, 0 unit, 36
integration, 25 oracle and 0/61 green. A new native/product pair and a separate retry must pass the
unchanged profile before TABLE-006 may advance.
