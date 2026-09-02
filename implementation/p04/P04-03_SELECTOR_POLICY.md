# P04-03 Selector policy

- Effective date: 2026-09-02
- Contract ID: `hwpx-agent.selector/v1`
- Implementation: `crates/domain-ir/src/selector.rs`

## Snapshot boundary

A `SelectorSnapshot` is built only from an already validated immutable `DocumentGraph` and a typed
`RevisionId`. The snapshot pins both the revision ID and canonical graph SHA-256. Every resolution
must provide a `SelectorExpectation`; revision or digest mismatch returns `selector_stale` before
any candidate lookup. A selector is never silently replayed against a newer graph.

The index covers nodes in section bodies and note bodies, including table-cell and drawing-child
flows. It does not index backend IDs, XML positions, HAction values, cursor state or UI sessions.

## Resolution order and cardinality

The v1 typed variants follow the design priority:

1. stable `LogicalId`;
2. exact named template slot, field or bookmark;
3. structural path plus expected canonical node fingerprint;
4. exact NFC-normalized text query plus neighboring context hashes.

Each selector instance has exactly one variant, so there is no implicit fallback from a stronger
selector to a weaker one. `resolve_one` succeeds only for exactly one target. Zero candidates return
`selector_not_found`, multiple candidates return `selector_ambiguous`, and exceeding the candidate
bound returns `selector_limit_exceeded`. Deterministic traversal order is not permission to select
the first candidate.

## Named metadata

The reserved backend-neutral properties are:

| Selector | Graph location | Reserved property |
|---|---|---|
| slot | `NodeCommon.semantics` | `slot_name` |
| field | `FieldNode.properties` or its `Reference.properties` | `field_name` |
| bookmark | bookmark `Reference.properties` | `bookmark_name` |

Names are exact, case-sensitive and NFC-normalized. Empty, control-character, oversized or
non-text reserved values fail snapshot construction. Conflicting local/reference field names fail
instead of choosing one. Duplicate names remain distinct candidates and therefore become
`selector_ambiguous`.

## Structural and text anchors

A structural path is rooted in a section or note and contains typed `flow_child(index, kind)` and
`table_cell(row, column)` steps. The expected node kind is part of each child step. Missing steps,
kind drift or a changed final node fingerprint returns `selector_stale`.

Paragraph search text is NFC-normalized and preserves visible text, tab and line-break characters;
equation, field, bookmark and control boundaries are represented by U+FFFC. A text selector stores
no bare offset. It requires a query and at least one `TextContextAnchor`, whose normalized context
is represented only by scalar count and SHA-256. Offsets are returned as Unicode-scalar ranges only
after resolution. Inserting unrelated text before an unchanged anchor pair remains resolvable;
matching query text with changed context returns `selector_stale`.

## Finite and privacy rules

Default bounds are path 64 steps, name 512 bytes, query 4 KiB, context 256 Unicode scalars,
candidate count 4,096, indexed nodes 250,000 and indexed normalized text 16 MiB. Hard ceilings reject
unsafe caller-provided limits. Text occurrence scanning is streaming and candidate accumulation is
checked before publication.

`Debug` and errors redact logical IDs, revision IDs, names, query text, context hashes, offsets and
fingerprints. Structured serialization is an explicit operation-plan artifact and remains subject
to the normal document privacy policy.

## Scope

This is a pure deterministic selector contract. It does not deserialize the public OperationPlan
wire schema, mutate a graph, route capabilities, execute Hancom, resolve page positions or use
cursor/session state. Those responsibilities remain in P04-04/P04-05/P04-06 and the automation
backend phases.
