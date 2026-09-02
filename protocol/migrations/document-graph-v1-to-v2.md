# DocumentGraph v1/design graph to validated v2

- Migration target: `hwpx-agent.document-graph/v2`
- Effective date: 2026-09-02
- Automatic in-place migration: forbidden

## Background

Before P04-01, the repository contained design vocabulary and a permissive conceptual JSON
schema, but no shipped, validated product `DocumentGraph v1` byte contract. Those design objects
must not be relabeled as validated v2 merely because some field names match.

## Explicit mapping

An adapter migrating an older graph must build a fresh `DocumentGraphDraft` and apply all current
validation. The minimum mapping is:

| Legacy/design concept | v2 target | Rule |
|---|---|---|
| document identifier | `DocumentId` | reject empty/control characters; do not reuse backend numeric IDs |
| source locator | `SourceAnchorHandle` | replace path/raw backend ID with logical opaque handle plus SHA-256 fingerprint |
| resource/style collections | `resource_catalog` / `style_catalog` | assign globally unique logical IDs and close typed references |
| blocks/controls | typed `Node` variants | reject an unknown kind or preserve it as an `OpaqueExtension`; never guess |
| notes/references/review | typed catalogs | assign unique IDs and close every target reference |
| unknown XML/backend data | `OpaqueExtension` | retain only handle, digest, length and preservation policy in the graph |
| order-insensitive catalogs | canonical ID order | sort during validated construction |
| flow content | original document order | preserve order exactly |

## Failure policy

- A direct v1 or unknown-version JSON input to `DocumentGraph::from_json` fails with
  `document_graph_unsupported_version` after bounded decoding.
- Duplicate IDs, dangling references, an incomplete/overlapping table, invalid key, exceeded
  limit or unrepresentable node fails without partial output.
- Missing raw data is not fabricated. If exact preservation cannot be proven, the adapter must
  emit a migration receipt with `lossless=false` outside the graph and require caller policy.
- Migration never edits a source HWPX in place.

## Compatibility rule

v2 readers accept only the exact v2 tag and exact known structure. v2 canonical bytes are pinned
by the golden digest in `P04-01_DOCUMENT_GRAPH_POLICY.md`. Any future structural evolution uses a
new version and a separate migration document; it does not weaken the v2 validator.

## Verification cases

- wrong version -> `document_graph_unsupported_version`
- duplicate logical/source-anchor ID -> `document_graph_duplicate_identifier`
- dangling typed reference -> `document_graph_dangling_reference`
- unknown JSON field -> `document_graph_invalid_json`
- oversized/deep/nested graph -> `document_graph_limit_exceeded`
- invalid or overlapping table -> `document_graph_invalid_table_shape`
- serialize -> deserialize -> validate -> serialize -> exact byte equality
