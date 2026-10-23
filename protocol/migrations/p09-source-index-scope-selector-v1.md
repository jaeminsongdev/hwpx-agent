# Original source index scope selector

`hwpx-agent.source-index-scope-selector/v1` adds four typed source search scope forms and
pre-match selection windows. These source-index coordinates are not the completed product
SearchScopeSelector. [V5 discovery/current revision and strict JSON](p09-source-scope-product-request-v5.md)
are qualified separately; review-policy integration, replacement use and Native document-flow/
visibility qualification still require connection.

## Scope identities

`SourceTextIndex::find_selector` accepts one `SourceIndexScopeSelector`:

- Document searches the index's admitted blocks and retains its skipped/unmapped counts.
  It does not relabel that partial corpus as whole-document visibility or full text coverage.
- Section takes a nonempty unique set of actual graph section IDs. The importer pairs graph
  sections with actual section-root spine parts; identical local paragraph IDs in different parts
  do not become one section. Missing, duplicate, foreign and over-limit IDs fail before matching.
- NodeSet takes actual graph NodeCommon.node_id values, not source paragraph-handle aliases.
  Each node's original authenticated source anchor resolves its XML interval. Actual table/cell
  and drawing descendants are included by original paragraph positions. Selected intervals are
  sorted and merged per part, then tested by binary search; overlapping nodes never duplicate hits.
  A known node with no indexed text yields zero matches, not guessed control semantics.
- Selection takes the exact index SHA and two boundaries, each containing paragraph_handle,
  global block_index and normalized_scalar. Handles and positions must match that index; stale
  fingerprints, foreign paragraphs, reversed/out-of-bounds ranges fail even for absent queries.

Section and node sets are canonicalized as sets but remain distinct from Document and Selection.
The receipt's selected_sections/selected_nodes count explicitly supplied IDs in those modes and
are zero in other modes; selected paragraphs/blocks/scalars describe actual admitted windows.
Scope SHA binds the profile, index fingerprint, kind, canonical IDs, boundaries and windows.
Request SHA additionally binds the original query digest. Source/document changes therefore do
not reuse an old selection. Receipts and handles do not establish service or revision authority.

## Selection windows and original coordinates

Selection is half-open in index NFC Unicode scalars, not UTF-8/XML byte offsets or current UI
positions. A boundary cannot split multiple normalized contributions of one original scalar.
Collapsed selections are allowed as zero-length windows: literal results are empty and a matching
zero-width regex yields a bounded noneditable position with no fabricated source pieces.

The chosen block interval follows source_index_blocks_not_native_document_flow. Start/end blocks
are clipped at their scalar boundaries; intermediate indexed blocks are included. Each window is
searched independently before regex anchors and Unicode whole-word checks. A match's reported
block/normalized scalar and original atom/scalar provenance remain global, not rebased to the slice.
Paragraph/control/opaque barriers are never concatenated to form a match.

The original matcher is extracted into private find_windowed. Existing callers pass None; removing
that wrapper/window branch and zero-offset arithmetic reconstructs the previous matcher exactly.
NFC/literal normalization, regex profile, declared-style filter, original contributions, response
and match caps are unchanged. No per-match source import or XML parse is added. Selected-out blocks
are excluded before match caps. Catalog traversal, depth, ID count, scope-hash bytes and the entire
response including selector wrapper are bounded; overflow returns an error rather than truncation.

## Verification

Components090 passes12 new selector cases plus24 matcher,6 paragraph-scope and8 review-search
cases:50 total,511 fresh/final511, cleanup true. Existing test bodies are unchanged. Tests cover
actual two-section identities with repeated local IDs, graph-node versus source-handle distinction,
table descendants/overlap, set canonicality/invalid IDs, clipping before regex/word boundaries,
global coordinates, cross-run Hangul NFC, barriers/multiple paragraphs, collapsed selection,
stale/foreign/out-of-bounds/partial-contribution rejection, proof/source binding and finite limits.

The initial compile reports one unused PackageLimits import in the new test. Removing only that
import leaves every test body unchanged; the closure performs cargo check for that target only.
It does not replay the50 tests. Product35, other core suites and the official249 queue are not replayed.
The original090 record, including its warning, remains unchanged.

Initial overall91.625 seconds, command25.875 and test bodies0.11+0.09+0.03+0.17 seconds. Maximum
system CPU27.93%, minimum available RAM27.0931%, peak Job private5.0637% of physical RAM. The Job
ends active0/empty/handle closed. One core, BelowNormal, CPU cap6.25%, private cap8%/stop7%,
RAM/commit95%, command300s, guard600s and input checks remain. These observations are not a
benchmark or proof that PC freezes are repaired. Evidence:
implementation/p09/evidence/p09-361-search-selector-components090.v1.json.

## Product connection still required

The generated contract's document/section/selection/node_set and revision_id/section_ids/range
remain authoritative; generated contracts are not edited. Authenticated discovery, current stored
revision/head/source binding and explicit JSON are qualified in the separate v5 product profile.
Review policy and literal editing now reuse the same exact windows through the separately qualified
[review selector stored profile](p09-stored-review-selector-candidates-v1.md). It includes actual supplemental
review node identities, explicit policy and current stored access. Separate search v6/literal v4 strict
JSON is qualified in [the product profile](p09-review-selector-product-requests.md). Existing v5 JSON semantics
are unchanged. Retained selector navigation is qualified in [its profile](p09-selector-result-navigation-v1.md).
Actual Native flow, effective visibility/style, full text coverage, match_set/semantic
diff/reopen, dispatcher/DB/CAS/execution/publication and the complete SearchScopeSelector remain open.
Source API v12 is incomplete/four unresolved/null report/exit3. Queue158/249,91 remaining,
next165, fixed CROSSREF8 NOT_RUN, Native011 unapproved/unexecuted, P09/A12/A13 OPEN, P10 not started
and the full P09–P20 goal ACTIVE remain unchanged.
