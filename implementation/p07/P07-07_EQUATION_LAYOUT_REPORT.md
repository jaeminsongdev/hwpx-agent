# P07-07 equation layout report

## Result

Result: `target_passed_exact_samples / general_estimator_inactive`.

`equation-engine` provides exact-sample, qualified-model and conservative-provisional layout paths.
`hwpx-package` accepts a non-provisional extent only when it matches an opaque estimator result. The
exact current Hangul 2020 target now qualifies four inline and four display samples after native
save/reopen readback, one-page PDF export, structural raster verification and the user's
original-detail `user_attested` review.

The fitted model does not meet the locked 150 HWPUNIT extent and 50 HWPUNIT baseline thresholds.
Observed maxima are 1868 and 105 HWPUNIT. The loader therefore retains the eight exact target
samples but does not activate the general estimator. Unknown shapes remain provisional with no
evidence digest and `render_required=true`.

## Exact evidence

- Plan SHA-256: `7244cf6c336533763918b44280129ab10f07f0c6279e8416f706e4a9058e5cc8`.
- Target evidence SHA-256: `f0c4088efe397e792399913fc14ed01d6a37de29c3910b667bed9ccf7525e048`.
- Raster evidence SHA-256: `e5eff31859c7a083bd158f087668a09879c41443b82dea1419191d8106dc7ced`.
- User-attested manual review SHA-256: `8f42081b7251ab69b3a43cd1442ac3cfd3abd3d206d7d4fd6c09a3ce1e7158be`.
- Public qualification SHA-256: `dff15f942fceb3a4b4f967fe13de07c800768649c6e5f76342c6f3f98b729381`.
- The run covered 8/8 samples: four inline and four display; native readback, PDF generation and
  structural rasterization passed with zero edge contact.
- The user inspected all eight displayed original-detail samples and reported zero clipping,
  overlap and silent fallback. Computer Use did not click or type.
- The lifecycle used three bounded HWP sessions and left zero owned `Hwp.exe` processes.

Private HWPX, PDF, PNG, traces and absolute paths remain outside tracked public evidence. The public
qualification contains only bounded typed measurements and cryptographic identities.

## Validation

- Layout Rust tests: 10/10 PASS, including the high-error-model regression that preserves exact
  target samples while forcing unknown shapes through the render-required fallback.
- Native HWPX tests: 14/14 PASS, including strict current-2020 inline/display readback shapes.
- Layout target tooling tests: 7/7 PASS, including manual-review gating and deterministic fitting.
- Qualification builder: `candidate_pass`, 8 samples, `verified_estimator_candidate=false`.
- Rust qualification oracle: `pass`, exact-sample qualification true,
  `verified_estimator_active=false`.
- Focused Rust format, tests and Clippy with `-D warnings`, PowerShell parse and Python bytecode/tests
  are required again by the aggregate P07 Gate after this evidence promotion.

## Scope and non-claims

This is an exact current-PC Hangul 2020 `11.0.0.9136` x86, eight-sample layout result. It does not
qualify a general estimator, arbitrary equations/documents, Hangul 2022/2024, production, P08 or the
whole product. P07-08, P07-09 and direct/automation differential results remain separate inputs to
the P07 aggregate Gate. Failed predecessor attempts remain failures.

## Next exact task

Rerun the P07-07 contract, refresh dependent P07-08 and aggregate source locks, then execute all ten
P07 validators. Only a passing aggregate Gate may close P07 and authorize P08.
