# P07-05 native equation HWPX policy

## Decision

P07-05 is admitted as exact-current-PC `pass / oracle_verified`. The component layer proves a
bounded typed `MathAst -> EqEdit -> native equation object` path and closed HWPX preservation. A
separate disposable fixture emitted through that lowerer then passed licensed Hangul 2020
open/save/reopen, exact semantic native readback and one-page PDF visual review.

The only target profile is licensed Hangul 2020 `11.0.0.9136`, x86, ko-KR on this PC. Other
versions require independent qualification.

## Typed boundary

- Public requests contain no XML, HAction, COM identifier or arbitrary filesystem output path.
- A request owns a normalized P07-01 `MathAst`; P07-04 compiles it to the finite exact EqEdit
  profile and reparses it before native lowering.
- The source binding covers the complete expanded package graph, exact spine part, exact top-level
  paragraph and direct run, package-wide native object-ID set and before/after document-flow SHA.
- Request admission and lowering independently repeat all source and flow checks.
- The object ID is nonzero, bounded and collision-free across equation, table and known drawing
  object IDs in every spine part. The P03 ID index adds an immutable `equation/v4` profile without
  weakening older core/table/formula profiles.

## Native object profile

The lowerer emits exactly one current-profile `equation` object with typed `id`, fixed version and
font, typed base unit/baseline/RGB, absolute extent, character anchor, zero outer margins and one
EqEdit `script`. It emits no image or plain-text fallback.

`inline` means an empty bound run in a paragraph with other visible run content. `display` means a
dedicated one-run paragraph. Both use the exact source-qualified as-character native object shape;
the reader infers the distinction from paragraph structure rather than writing private attributes
into HWPX. Hangul may add one paragraph `linesegarray` renderer cache without changing that
classification. No other direct paragraph child is admitted.

P07-07 has not qualified an estimator. P07-05 therefore admits only a positive bounded
`provisional` extent with no evidence digest and `render_required=true`. Target-readback and
estimator labels fail closed; arbitrary constants cannot be promoted to verified layout.

## Preservation and readback

- The source run must contain exactly one self-closing empty text node. Ambiguous, nonempty,
  nested or already-owned runs fail before mutation.
- The preserving patch engine inserts a single validated fragment and returns no partial package.
- The writer reuses the ID profile carried by the patch result; it never silently falls back to a
  weaker core profile during artifact validation.
- Before return, the lowerer strictly reopens the private changed section, checks every owned
  attribute and child, parses EqEdit back to `MathAst`, compares semantic/style/layout/extent/ID
  state, removes the inserted object by its exact span and requires byte identity with the source.
- Exactly one part may change; all other expanded parts retain source/output SHA equality.

## Limits and privacy

Section bytes, element/equation counts, script/result bytes, extent and object ID have finite hard
ceilings. Strict JSON rejects duplicate and unknown keys. Receipts serialize deterministically.
Debug output redacts package paths, IDs, digests, style/extent values, scripts and AST payloads.

## Target normalization and evidence boundary

The target run is bound to the exact fixture/output/trace/PDF SHA values. Hangul preserved the
EqEdit script SHA, MathAst semantic SHA, style, baseline, color, extent, anchor, margins and one
native object, while reassigning the native object ID and adding a renderer line cache. The oracle
records that remap instead of treating a caller-selected source ID as stable across native save.

The initial oracle rejected that normalization and remains failed diagnostic history. The reader
was corrected and rerun against the same immutable saved HWPX; only that later result is PASS.

This evidence does not prove arbitrary existing documents, verified layout estimation, editor
double-click/change/save, native equation insertion automation, differential parity, other Hangul
versions, P07 completion, production readiness or product completion. Those fields remain
`false` / `not_run`.

Reasoning level: `max`. P07-06 automation binding remains at `max`.
