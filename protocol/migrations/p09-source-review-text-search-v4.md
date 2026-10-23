# P09 source review text search v4

`hwpx-agent.product-source-search-request/v4` adds `find_review_literal` and `find_review_regex`.
They search admitted original body/note paragraphs and explicitly selected hidden-explanation/MEMO
body regions. A file region is not the application's current display state or effective formatting.

## Explicit file body policy

The existing project/document/revision/head/source SHA/key/plan/scope envelope and16 KiB request
bound remain. Each new operation requires the following object, with both Boolean values present:

```json
"review_policy": {
  "include_hidden_explanations": false,
  "include_memo_bodies": false
}
```

The existing case_sensitive, whole_word and max_results options apply; operation kind chooses
literal or regex. Base mapped body/footnote/endnote paragraphs remain eligible. The two policies
independently include/exclude actual hiddenComment and MEMO subList body paragraphs.

Scope resolution first validates paragraph handles against the entire admitted corpus, even when
the query has no matches. Policy exclusions then precede match and reported-point limits. Selecting
only excluded paragraphs produces an explicit zero-result response, not a foreign-scope error.
Duplicate/empty/foreign scope selections still fail. No result is silently truncated.

V1/v2/v3 reject the new operations and any review_policy, including null. V4 requires an object
with both Booleans; arrays, null, missing/unknown/duplicate keys and wrong value types fail before
source reads. The policy is rejected on earlier operations. New review operations cannot combine
style_filter or definition_filter. Generic include_hidden remains unknown rather than being
silently equated to native visibility. Earlier operations retain their original corpus and result shapes.

## Original admission and source positions

The complete original Form reconstruction and pointer-bound proof are reused. Existing paired
field collection and ImportedDocumentReviewBodies admit original hidden/MEMO body flows.
Callers cannot supply a graph, source text, visibility flags or approval bits. Invalid envelopes,
unpaired MEMO markers and unsupported body mappings fail instead of becoming absent content.

The extended index adds admitted body paragraph anchors to the original mapped corpus. Aggregate
paragraph/block/scalar/decomposition/response limits cover the union, including excluded regions.
The original source extraction and NFC provenance rules remain. Blocks do not cross paragraph,
control, field or opaque boundaries. A single source-key pass orders blocks by spine part and first
original text-element anchor; empty blocks use the paragraph anchor. XML order is not native page
or rendered document order.

The pinned official hiddenComment model maps a subList child. Its serialization model does not
establish application visibility or formatting precedence. See the local qualified source cache:
`fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/Para/hiddenComment.cpp`.
The existing named-style/character serialization models are not an implicit cascade algorithm.

## Result identity and coverage

Extended index/results use `hwpx-agent.source-text-search/nfc-review-map-v2` and
`hwpx-agent.source-review-text-search/v1`; the new stored/product preparation variants use v4.
The index binds original source/graph plus the original review receipt and paragraph-region map.
Request identity binds the extended index, selected scope, query/options and explicit policy.

`coverage=selected_admitted_file_regions` accompanies searched_paragraphs, searched_blocks,
excluded_hidden_paragraphs and excluded_memo_paragraphs. Scope counts describe requested admitted
paragraphs, while searched counts reflect policy eligibility. `match_regions` parallels matches
one-to-one in source order with body_and_notes, hidden_explanation or memo_body. No raw text/query
is included in response or Debug. Opaque counts remain base-graph-only and are labeled accordingly.
`app_visibility_cascade_or_full_document_search_qualified=false` remains mandatory.

## Access and verification

The private stored result variant shares existing document.write, sealed current Result,
provider scope/head/ACL/quarantine/AEAD, complete original reconstruction and final consumer head
checks. It builds no unused base/style index. Retained result verification rechecks current access
and original source without rerunning the query. No unchecked result getter, source overwrite,
ingest/commit/CAS, durable key claim, CLI/server execution or publication is added.

Components056 passes eight new core cases, four affected extraction cases, six new v4 product
cases and20 affected v1/v2/v3 product cases: all38 pass,454 fresh/final454, no diagnostics and
terminal/empty/closed Jobs. The matcher/base extraction inverse and original20 product test bodies
are checked. Other old core tests, unrelated286 stored cases and the official queue are not replayed.

This is file-body corpus coverage, not full SearchScopeSelector, style/body combination,
effective cascade/visibility, target match_set/semantic_diff/reopen, Native or P09 Gate qualification.
Source API v12 remains incomplete with four unresolved stages, null report and exit3. Queue158/249,
remaining91, next165, P09/A12/A13 OPEN, fixed CROSSREF eight NOT_RUN,
Native011 unapproved/unexecuted and P10 not started remain unchanged.

Retained review results also support the additive [navigation request](p09-source-search-navigation-v1.md).
Its cursor preserves policy/region identity and rechecks current access rather than rerunning this query.
