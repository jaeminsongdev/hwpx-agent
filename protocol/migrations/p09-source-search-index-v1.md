# P09 mapped source search index v1

The separate [original Unicode normalization profile](p09-source-unicode-normalization-v1.md) changes
actual selected source scalars using four explicit forms and minimal provenance components. It leaves
this NFC search algorithm unchanged and is not yet a stored/product normalization route.

`hwpx-agent.source-text-search/nfc-map-v1` is an additive Rust source component.
It does not change the existing product source-assessment v12 or enable a CLI/server search route.

## Source identity and normalization

Build an index from `ImportedDocumentStructure::source_text_index` with fresh complete source bytes
and finite `SourceSearchLimits`. Original source validation runs before construction. The index borrows
the imported structure and uses its XML and source anchors; the caller cannot supply a text corpus as an
equivalent source. `verify_source` checks subsequently supplied whole bytes, not current service access.

Receipts bind the source and graph hashes, profile, actual pinned Unicode normalization version,
indexed text and scalar provenance. They report indexed and skipped paragraphs, barriers and opaque
graph nodes. Hashes and receipts do not grant read, write or execution authority.

Canonical decomposition, stable combining-class ordering and composition retain each decoded source
scalar's identity. A separate streaming library NFC comparison rejects a mapping mismatch. Positions
in a `SourceSearchPiece` are decoded scalar ranges within an anchored text atom, not XML byte offsets.
Canonical reordering can yield multiple non-adjacent source pieces. Selecting only part of one scalar's
normalization image is not exact. An exact scalar selection is not necessarily a contiguous edit range.

## Search semantics

Literal queries are NFC-normalized and escaped. Regex queries are not rewritten: syntax and escapes
apply exactly as supplied to the NFC corpus. Unicode simple case folding and Unicode word boundaries
come from the pinned regex dependency, not a claim of Hancom search equivalence.

Mapped paragraphs in sections, table cells, drawing flows and notes are collected in source XML order.
Runs can form one block, but paragraph/control/field/opaque barriers are not crossed. Unmapped source
paragraphs are skipped and counted. Regex anchors apply to each indexed block, including an empty
mapped paragraph; a control split can create multiple blocks in a paragraph. Empty matches have no
fabricated editable source range. Results are leftmost non-overlapping within each block.

`complete_within_indexed_blocks=true` means all matches inside this declared partial corpus were
returned. `whole_document_visibility_and_search_qualified=false` and authority flags remain false.
This profile does not interpret hidden visibility, effective styles, native page order or opaque text.

## Bounds and client responsibilities

Limits cover paragraphs, blocks, text elements, original and globally decomposed scalars, query bytes,
compiled pattern/DFA size, result count, reported source points and serialized response bytes.
Invalid or over-ceiling limit configurations are rejected. Overflow returns an error rather than a
truncated successful result. Query text is excluded from results and Debug; its digest binds the raw
query and options. Result serialization is bounded and includes no raw source text.

The component cannot replace SearchScopeSelector or the complete SEARCH-001/002 operation schemas.
It adds no replacement/capture/template editing, style/control queries, navigation, privacy transform,
font/style conversion, durable idempotency, CAS, publication or Native result.
The separately scoped product adapter rechecks current document.write/ACL/source/head; see
`p09-source-search-product-request-v1.md`. It does not qualify the full operation schema.

## Verification and remaining work

The 24 component cases cover source run/entity/scalar maps, Hangul Jamo composition, combining marks,
canonical reordering/expansion, literal/regex semantics, controls/opaque barriers, notes, empty matches,
foreign/stale inputs, bounded compilation/results/output and non-disclosure.
Components042 preserves 23 passes and one failed compiled-limit expectation. Recovery043 changes only
that expectation to a nontrivial pattern, proves the whole-file inverse and unchanged production/other
inputs, and runs only the failed case. All 24 distinct cases are covered; the failed original is retained.
Components040/041 are retained compile failures with no executed tests.

See `implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md` and the immutable evidence receipts.
The separate [regex replacement source profile](p09-source-selector-regex-replacement-v1.md) optionally
collects captures in the same match pass and feeds the original protected atom compiler. Original
noncapture matching is preserved by exact inverse checks; this source candidate grants no stored access.
The explicit mapped-source/paragraph scopes and authenticated product adapter pass six new scope,
24 affected core and nine product cases in components045. The pure index still grants no service access.
P09 catalog coverage, whole-document search, full operation routing and match-set/semantic-diff/reopen
qualification remain open. Queue 158/249, next165, P09/A12/A13 OPEN and P10 not started are unchanged.

The separate [source-index scope selector profile](p09-source-index-scope-selector-v1.md) adds actual
section/node identities and fingerprinted pre-match NFC selection windows with50 component passes.
Existing mapped/paragraph profiles are not renamed or widened. New selector stored/revision/JSON
and Native/full SearchScopeSelector qualification remain pending.
