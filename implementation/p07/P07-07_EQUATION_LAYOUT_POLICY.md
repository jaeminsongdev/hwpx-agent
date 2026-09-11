# P07-07 equation layout policy

## Decision

P07-07 is `unit_passed / target_not_run`. The complete typed estimator, qualification format,
structural metric model, conservative fallback and HWPX binding are implemented. No qualification
is active until the exact current target supplies the required inline/display native readback and
baseline/ink-box visual evidence.

## Estimation order

1. An exact semantic/layout/base-unit sample in a trusted qualification returns its recorded target
   width, height and baseline as `target_readback`.
2. A non-exact expression inside every qualified structural envelope bound uses the fixed-point
   font model and returns `verified_estimator`.
3. With no qualification or outside its envelope, the expression uses a conservative fixed-point
   provisional estimate with no evidence digest and `render_required=true`.

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
coefficients, a structural envelope and exact samples. Admission requires at least four inline and
four display cases, exact sample-count accounting, object-extent maximum error at most 150 HWPUNIT,
baseline maximum error at most 50 HWPUNIT, zero ink overflow, clipping, overlap and silent fallback,
and inspection of every page. The validator recomputes both maximum errors from each sample's
bounded structural metrics rather than trusting the reported totals. Each ink box must be finite
and strictly inside its rendered page.

The two P07-06 display readbacks are useful candidates but have no inline or ink-box evidence, so
they do not qualify this model. The dedicated current-target calibration remains `not_run`.

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

Actual target calibration, baseline/ink-box visual PASS, active verified-estimator coverage, P07-08
corpus, P07-09 editor smoke, other Hangul versions, P07 completion, production and product
completion remain `false` / `not_run`.

Reasoning level: `max`. P07-08 remains `max` because corpus completeness and legacy preservation
must be evidence-bound without silent approximation.
