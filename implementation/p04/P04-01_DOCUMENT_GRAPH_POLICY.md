# P04-01 DocumentGraph v2 implementation policy

- Effective date: 2026-09-02
- Contract ID: `hwpx-agent.document-graph/v2`
- Implementation authority: `crates/domain-ir/src/document_graph.rs`
- Scope: pure backend-neutral in-memory graph and its deterministic internal JSON form

## Authority and boundary

`DocumentGraphDraft` is untrusted mutable input. Only `DocumentGraph::from_draft` or
`DocumentGraph::from_json` may create a validated immutable `DocumentGraph`. Callers MUST NOT
treat a deserialized draft, the design-only schema, raw HWPX XML, a COM object or a backend action
name as a validated graph.

`specs/document-graph-v2.schema.json` remains the product-design vocabulary source. Its broad
`additionalProperties` regions are not a runtime admission rule. The Rust validator narrows that
design with typed fields, `deny_unknown_fields`, finite limits, reference closure and shape checks.
The canonical JSON keeps the design top-level names `resource_catalog`, `style_catalog` and
`artifact_ref`, while the executable Rust contract is authoritative until a generated public wire
schema is introduced by a separately gated task.

This task does not read, write or launch HWPX, Hangul, COM, HAction or a provider. It does not
claim compatibility with user documents or another Hangul version.

## Model contract

- A graph contains an exact schema version, redacted document/source identity, metadata,
  settings, security, accessibility, resource/style catalogs, one or more sections, notes,
  references, review entries and opaque preservation handles.
- Required node kinds are paragraph, table, equation, drawing, chart, field, form control, break
  and embedded object. Backend identifiers and source locations are represented only by logical
  IDs and opaque fingerprinted handles.
- Every section, node, table cell, resource, style, note, reference, review entry, source anchor
  and opaque extension ID is globally unique.
- Style/resource/reference/review/node references must close against a matching typed catalog.
- A table must have non-zero dimensions, remain within the configured cell budget, cover its grid
  exactly once and contain no overlapping span.
- Unknown document semantics may be preserved in bounded `Properties` or by a digest/length
  opaque handle. Raw opaque bytes are not stored in the graph.

## Finite admission

Every constructor requires `DocumentGraphLimits`. Zero, internally inconsistent or ceiling-
exceeding limit configurations fail before graph validation. Counts cover sections, nodes,
inlines, resources, styles, nested properties, expanded table cells, notes, references, review
entries and opaque extensions. Depth, per-string bytes, aggregate string bytes and canonical
serialized bytes are also bounded.

Programmatic drafts are checked with a non-retaining bounded JSON writer before publication.
Untrusted JSON is length-checked before deserialization and then passes the same validation. A
failure returns a stable typed error and no partial `DocumentGraph`.

## Canonical serialization

- Catalog-like collections are sorted by logical ID before validation.
- Document order in sections, flows and inlines is preserved.
- Map-like properties use `BTreeMap` key ordering.
- Compact UTF-8 JSON and the exact schema tag are required.
- The v2 golden digest is
  `2ab9ffef0263e14609afa148e412ba2915820e54e365c9a420c734f908a6f3c6`.
- A deserialize -> validate -> serialize cycle must be byte-identical. Windows and Linux must
  produce the same bytes and SHA-256 for the same synthetic graph.

## Privacy and diagnostics

Public `Debug` output for graph values redacts IDs, body text, paths, formulas, properties and
opaque handles. Stable errors expose only a fixed message and `document_graph_*` code. New error
variants MUST follow the same rule. Logs MUST record counts, codes or digests, never document
text, source paths or opaque bytes.

## Versioning

The committed v2 field names, enum tags, canonical ordering and golden bytes are frozen. New
optional semantics SHOULD use an existing bounded `Properties` extension point when their
meaning is unambiguous. A structural field, changed meaning, relaxed identity rule, new enum tag
needed by an old reader, or serialization change requires a new schema version, migration note,
negative test and new golden digest.

Legacy or future versions fail with `document_graph_unsupported_version`; they are not silently
coerced. Migration must occur in an explicit adapter before `DocumentGraph::from_draft` and must
produce a receipt when identity or opaque preservation cannot be exact.

## Required validation

- `cargo test --locked -p domain-ir`
- `cargo clippy --locked -p domain-ir --all-targets -- -D warnings`
- Windows/Linux byte-identical golden digest
- current checkout and exact-commit clean-clone full bootstrap
- repository secret, dependency and license regression

No runtime or source-artifact evidence may be inferred from these pure synthetic tests.
