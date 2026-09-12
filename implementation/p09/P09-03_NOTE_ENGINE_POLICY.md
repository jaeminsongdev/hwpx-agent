# P09-03 note-engine policy

## Decision

P09-03 is `five_capability_typed_component_pass / official_model_qualified /
digest_manifest_export_only / direct_hwpx_not_run / target_not_run / task_incomplete`.
The component covers `REF-021` through `REF-025`: footnote insertion, endnote insertion,
section-specific note style replacement, note-kind conversion, and deterministic digest-manifest
projection. It does not lower or mutate an HWPX package, invoke installed Hangul, write an external
note file, or claim semantic reopen, field/reference readback, render, automation, differential,
production, P09, or product completion.

## Qualified native surface

The official Hancom `hwpx-owpml-model` source is pinned at commit
`1453388472c703a4b299a0834f425cdac16644b9`. The run-control model admits exact `footNote` and
`endNote` children backed by `NoteType`. Each note binds native `flag`, 16-bit `number`,
`userChar`, `prefixChar`, `suffixChar`, `instId`, and `subList` state. Each section independently
owns `footNotePr` and `endNotePr` with `autoNumFormat`, `noteLine`, `noteSpacing`, family-specific
numbering and placement, `newNum`, `beneathText`, and opaque remainder state.

The typed catalogs preserve all 22 official number formats, all 18 `LineType2` values and all 16
official line widths. Footnotes admit continuous/per-section/per-page numbering and each/merged/
right-most-column placement. Endnotes admit continuous/per-section numbering and end-of-document/
end-of-section placement. Cross-family numbering or placement is rejected instead of coerced.

## Complete state, operations and protection

The ordered state contains every section and note. A note binds logical/native identity, exact
paragraph/run/inline anchor, semantic kind plus native tag, marker properties, body graph and
optional plain-text digests, marker/body style digests, opaque native-payload remainder, ordered
opaque properties, and its lock. Document state additionally binds all non-note content, style,
numbering, reference, resource, protection and opaque-document digests. Every section binds both
note styles, opaque state and protection.

Insert changes only the requested ordered note slot. Style replacement changes only the selected
section and family. Convert changes semantic kind and exact native tag while preserving identity,
anchor, marker, body, styles and opaque payload. Locked documents, sections, notes and styles reject
mutation. `PrepareExport` is read-only and emits only a bounded document-ordered manifest of
identity, kind and body/plain-text digests; it neither exposes raw body content nor creates a file.

## Determinism and failure policy

Requests and builds independently recheck exact source-state and document-flow SHA-256. Plans seal
operation, capability, request, source/result state, source/result flow and optional export-manifest
digest. Duplicate or unknown JSON fields, oversized input/output, empty section inventories, zero or
colliding IDs, duplicate anchors, mismatched native tags, invalid marker characters/digests/styles,
family-incompatible numbering/placement, missing or duplicate export selections, invalid insertion
indexes, protected/no-op mutations, drift, and plan tampering fail without a partial result. Debug
output redacts identities, anchors, marker characters, body/style/opaque digests and selections.

## Evidence boundary

Focused Rust tests passed 9/9: eight public happy/boundary/negative/preservation tests and one
private sealed-plan tamper test. Private contract tests passed 5/5. These tests prove typed component
state and pinned source metadata only.

`unit_model_implemented=true`, `five_capabilities_unit_passed=true`,
`official_model_source_qualified=true`, `complete_bound_state_preserved=true`,
`note_style_and_protection_fixtures=true`, `request_and_build_drift_rejected=true`, and
`digest_manifest_export=true`. `actual_note_export=false`, `direct_hwpx=false`,
`actual_hwpx=false`, `actual_hangul=false`, `semantic_reopen=false`, `field_readback=false`,
`reference_update=false`, `hancom_open=false`, `save_reopen=false`, `render=false`,
`automation=false`, `differential=false`, `p09_03_green=false`, `p09_complete=false`,
`production_ready=false`, and `product_complete=false`.

Reasoning level: `max`. Exact HWPX lowering/readback and real note export remain `max`.
