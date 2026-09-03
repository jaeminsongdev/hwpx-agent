# Paragraph style v0 to v1

hwpx-agent.paragraph-style/1 is the first executable paragraph-property and referenced
border/fill contract. The P05 roadmap prose and P04 generated header were non-executable v0 inputs;
no v0 wire payload is accepted or automatically rewritten.

## v1 boundary

- A full current-profile hh:head or a standalone hh:refList is admitted through P03 preserving XML
  before the targeted paragraph/border view is built.
- Full-header lift derives dense tab/numbering/bullet reference domains without claiming their later
  detailed semantics. Fragment lift requires the same domains explicitly.
- Paragraph IDs are dense from zero; border IDs and non-empty numbering/bullet domains are dense from
  one. Counts and every typed reference close before a catalog is returned.
- Alignment, direction, heading, breaking, automatic spacing, signed/unit-bearing current and
  fallback margins, line spacing and paragraph border values use the locked spellings and bounds.
- The 2016 layout and 2021 metatag branches are preserved independently and both participate in
  semantic identity.
- The border/fill slice supports exact current-profile line/slash values and optional winBrush.
  Unknown, gradation and image-brush alternatives reject instead of being discarded.
- Semantic deduplication excludes allocated paragraph ID, retains first occurrence and emits an
  explicit old-to-new map. Only typed P05-01 paraPrIDRef may be rewritten from that map.
- Lowering emits a deterministic typed fragment, must re-lift to exact equality, and returns a
  deterministic digest/count receipt.

## Compatibility and migration

The v1 namespace and emitted structure are bound to this PC's exact Hangul-2020 generated header.
The official KS X 6101 2024 schema is a structural reference, not an implicit cross-version runtime
pass. A different compatibility namespace, sparse-ID convention, margin/unit representation,
heading rule, fill alternative, alpha representation, semantic identity or output order requires a
new explicit profile/version and migration.

Tab and list definition semantics remain P05-04/P05-05; style records remain P05-06. Gradation/image
fills, page/section layout and visual/runtime pagination remain later P05/P08/P13 work. This task adds
no public service wire endpoint and does not authorize 2022/2024 runtime claims.
