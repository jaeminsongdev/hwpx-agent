# P09-102: one source-selected review paragraph output

## Intent and evidence boundary

Implement complete typed replacement of one paragraph inside an actual existing MEMO or hiddenComment body. Other paragraphs, rich tables, opaque sibling elements, paired markers, main-document content and unrelated expanded package parts remain byte-exact. This is not new rich-object/table/comment insertion, native author/time/state binding, protection qualification or full comment acceptance. P09 Gate remains OPEN; no P10 work.

Selection is two immutable source anchors: the actual review marker and its actual paragraph. Caller XML, offsets, graph, numeric identity or author/time defaults are not accepted. The paragraph must be an actual namespace-qualified `p` directly under a `subList`, in the same source part and below that review body. Main-document, other review, foreign document/version, non-paragraph and stale selections fail closed. The source-derived ancestry path is private.

Original nested-review prohibitions remain unchanged. Such inputs are rejected by the original body reader before this route. The paragraph selector additionally refuses an intervening different observed review body; it does not qualify new nested semantics.

## Shared original implementation

Whole-body and whole-cell APIs still delegate through the original content replacement mode. A private Paragraph mode reuses original TextFlowWriter, PatchIntent::ReplaceSubtree, FormulaV3 ID validation, PreviewTextV2 preservation, PreservingWriter and complete source/body reimport. No alternative XML writer or relaxed parser was added. Exactly one target paragraph is compared against full typed readback. Its outer span, rather than body content span, defines the byte-exact outside-preservation check.

The supplied TextFlow is a COMPLETE paragraph replacement: the old contents and attributes inside that selected paragraph are not promised unchanged. This is not a text-only edit or a guarantee to preserve rich objects inside the selected paragraph. Rich siblings outside the selected paragraph remain exact. New opaque output remains rejected by the original writer; dangling styles/IDs, invalid values, no-op, source drift and finite writer limits remain enforced.

Observed protection flags on every containing table/cell, including outer ancestors of nested tables, reuse the unchanged P100 guard. A nonzero or unknown observed flag rejects. Missing flags are not fabricated as zero or claimed as complete document protection. Full native protection/policy acceptance stays unqualified.

## Stored product path

ReviewParagraphReplacement supplies only the two actual anchors and typed content. prepare_paragraph, verify and with_verified_bytes all use original fresh source/service checks and deterministic output replay. Existing tenant/subject/project/branch/document scope, ACL, AEAD, scan/quarantine, digest and head checks are preserved. Failed verification never invokes the callback. READ audit activity is not artifact ingest or revision publication.

Repeated reads are not a held execution lease, atomic CAS or publication authority. require_current_product_route remains RouteUnqualified after verification until full comment metadata/protection/compiler/issuer requirements are genuinely satisfied.

## Preservation and validation

Six modified parents have exact whole preimages. Declared transforms add two module exports, one test module declaration, one test-fixture visibility change, shared private target selection and three private helper visibility changes. No original guard or historical assertion was removed. The unmodified P101 audit executes against the exact prior read-view, while every current parent must match the declared whole-byte transform.

Original captured HWPX is read-only negative evidence (no review target), not a positive native review test. Synthetic rich packages, stored in-memory service fixtures, original component validators and Rust/Python tests remain separate from actual SQL, Hangul save/reopen, rendering and Gate acceptance. No access popup, Hwp/COM/UI, SQL, installation/settings, commit/push, delete or move is authorized or performed here.
