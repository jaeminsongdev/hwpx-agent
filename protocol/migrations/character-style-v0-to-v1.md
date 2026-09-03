# Character style v0 to v1

hwpx-agent.character-style/1 is the first executable fontface and character-property contract. The
P05 roadmap text and the P04 generated header were non-executable v0 inputs; no v0 wire payload is
accepted or automatically rewritten.

## v1 boundary

- One current-profile full hh:head or standalone hh:refList is admitted through P03 preserving XML
  before the targeted font/style view is built.
- Exactly seven ordered, language-local font ID domains are required. IDs are unique and dense within
  each domain; equal numeric IDs in different language domains are valid.
- Character-property IDs are unique and dense. Every language font reference must resolve in its
  matching domain.
- Size, ratio, spacing, relative-size, offset, color, enum and effect values use the locked current
  profile bounds and spellings.
- Semantic deduplication excludes allocated style ID, retains first occurrence and emits an explicit
  old-to-new map. Only typed text-flow references may be rewritten from that map.
- Lowering emits a deterministic typed fragment, must re-lift to exact equality, and returns a
  deterministic digest/count receipt.
- Unknown content within the typed sections rejects. Unrelated full-header sections are not claimed
  by this targeted reader and remain under the existing preservation/package contracts.

## Compatibility and migration

The v1 namespace and emitted shape are the current-PC Hangul-2020 2011 head profile. The official
KS X 6101 2024 schema is a structural reference, not an implicit alias or cross-version runtime pass.
A new namespace, language domain, font kind, effect, range, sparse-ID rule, color form, embedded-font
payload rule, or different semantic identity requires a new explicit profile/version and migration.

Binary-item and border-fill references are external to the standalone fragment. Complete-package
integration must continue to pass the P03 ID/reference index before publication. Paragraph styles,
tab definitions, numbering, page/section/header/footer structures and visual/runtime oracles remain
later P05/P13 work. This task adds no public service wire endpoint.
