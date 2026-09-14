# P07-07 equation layout policy

## Decision

P07-07 is `target_passed_exact_samples / general_estimator_inactive`. The complete typed estimator,
qualification format, structural metric model, conservative fallback and HWPX binding are
implemented. The exact current target supplied four inline and four display native readbacks,
structural raster evidence and the user's original-detail `user_attested` review. Those exact
samples are qualified; the fitted general model is not.

The target toolchain is also implementation-complete. A hash-pinned plan selects exactly four
Tier B semantics in both inline and display contexts. One bounded x86 STA session creates, reads,
saves, reopens and reads all eight native objects, exports one PDF per sample, and then a separate
Rust oracle reopens each HWPX through the closed package graph. Inline admission requires both the
documented `LineMode` request and an adjacent visible run; `LineMode` alone cannot relabel a
single-run display paragraph as inline.

## Estimation order

1. An exact semantic/layout/base-unit sample in a trusted qualification returns its recorded target
   width, height and baseline as `target_readback`.
2. A non-exact expression inside every qualified structural envelope bound uses the fixed-point
   font model and returns `verified_estimator` only when the calibration's recomputed extent and
   baseline errors meet the 150/50 HWPUNIT thresholds.
3. With no qualification, outside its envelope, or when the measured model error exceeds either
   threshold, the expression uses a conservative fixed-point provisional estimate with no evidence
   digest and `render_required=true`. Exact target-readback samples remain usable in that case.

No floating-point arithmetic, saturation, silent clamping, text/image fallback or arbitrary
caller assertion is used.

## Structural model

The analyzer traverses the normalized `MathAst` and accounts for nodes, depth, horizontal advance,
above/below baseline levels and matrix rows/columns. Fractions, scripts, roots, accents,
annotations, large operators, derivatives, delimiters, matrices, cases, aligned rows,
combinatorics and set builders have explicit checked rules. Every count and fixed-point operation
has a finite limit and checked overflow path.

## Qualification boundary

A target qualification is strict JSON pinned by its exact byte SHA. It binds current build,
architecture, locale, font name, font-metric digest, semantic corpus digest, evidence digest, model
coefficients, a structural envelope and exact samples. Exact-sample admission requires at least four
inline and four display cases, exact sample-count accounting, zero ink overflow, clipping, overlap
and silent fallback, and inspection of every page. The validator recomputes both maximum errors from
each sample's bounded structural metrics rather than trusting the reported totals. A model is active
only when object-extent error is at most 150 HWPUNIT and baseline error is at most 50 HWPUNIT;
otherwise it is retained as measured rejected calibration and all non-exact shapes stay provisional.
Each ink box must be finite and strictly inside its rendered page.

The earlier two P07-06 display readbacks were useful candidates but had no inline or ink-box
evidence and were never promoted. The dedicated eight-sample current-target run now closes that
evidence gap. Its maximum extent error is 1868 HWPUNIT and maximum baseline error is 105 HWPUNIT,
both above the locked 150/50 thresholds. Accordingly, exact samples use target readback while every
unknown shape remains provisional and render-required.

PDF export is not visual PASS. A separately hash-pinned `pdftoppm` pass rasterizes every one-page
PDF and measures only bounded, non-edge-touching ink boxes. Its result stays
`structural_pass_manual_not_run`. Qualification construction additionally requires a strict manual
review record for all eight original-detail PNGs with zero clipping, overlap and silent fallback,
then deterministically fits the fixed-point width, height and mode-specific baseline coefficients.
If the recomputed 150/50 HWPUNIT thresholds are not met, the exact samples may still be qualified,
but the fitted model is not activated and every non-exact shape remains render-required.

The estimator exposes the same bounded typed structural metrics used internally by provisional and
qualified models. Calibration tooling therefore cannot substitute a second metric implementation
or silently diverge on advance, vertical levels, node/depth or matrix envelope accounting.

## HWPX binding

Legacy P07-05 JSON construction remains provisional-only. A verified or target-readback extent can
enter the lowerer only alongside an opaque `EquationLayoutEstimate`. The request builder rechecks
profile, semantic SHA, inline/display mode, base unit, baseline, dimensions, evidence SHA, source
kind and render-required state. Raw extent JSON cannot promote itself.

## Privacy and non-claims

Qualification and estimate Debug output redact semantic, metric and evidence values. Estimate
receipts are deterministic and bounded. No font file, document text, private path or raw
automation identifier is recorded.

Actual target calibration and the bounded baseline/ink-box visual review are `pass` for these eight
samples. Active verified-estimator coverage remains `false`; P07-08 and P07-09 are owned by their
separate contracts. Other Hangul versions, arbitrary equations/documents, production and product
completion remain `false` / `not_run`. P07 phase completion is decided only by the aggregate Gate.

Reasoning level: `max`. Native readback, raster identity, original-detail review and model admission
remain one exact hash-bound chain.
