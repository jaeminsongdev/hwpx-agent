# Text flow v0 to v1

`hwpx-agent.text-flow/v1` is the first executable typed paragraph text-flow contract. The P05 roadmap
description and the P04 VS-0 paragraph shape were non-executable v0 inputs; no v0 wire payload is
accepted or rewritten.

## v1 boundary

- One standalone current-profile `hp:p` is admitted only after P03 preserving XML validation.
- Ordered paragraph children distinguish typed runs from opaque elements; ordered run items
  distinguish text spans, field begins, field ends and opaque elements.
- Text spans preserve Unicode scalar content and explicit `tab`/`lineBreak` atoms. Exact current-2020
  tab occurrences carry required unsigned `width`, `leader` and `type` metadata; named tab-stop
  alignment and leader semantics are resolved through the P05-04 header definition. NFC is an explicit
  semantic comparison operation, not an in-place source rewrite.
- Paragraph/run/text/field attributes are closed typed sets. Unknown attributes on a supported shape
  reject; unsupported non-text elements become digest-only opaque records.
- Field ends close the currently active begin. Duplicate, missing, misnested, over-depth or unclosed
  identifiers reject the entire flow.
- Lowering accepts no opaque records or raw fragments, emits deterministic XML, and must re-lift to
  exact typed equality before bytes are returned.

## Compatibility and migration

The v1 executable namespace is the current-PC Hangul-2020 2011 paragraph namespace. The official
KS X 6101 2024 Appendix E schema is a structural reference, not an implicit namespace alias. A 2024
namespace, new text atom, field payload child, track-change construct, opaque-content preservation
strategy, or changed Unicode/boundary semantics requires an explicit profile/version and migration;
it must not be silently accepted as v1.

Character styles are intentionally represented only by numeric references in v1 and are resolved in
P05-02. Paragraph styles/layout, full tab definitions, lists, page/section/header/footer structures
and the VS-1 actual oracle remain later P05 tasks. This task adds no public service wire endpoint.
