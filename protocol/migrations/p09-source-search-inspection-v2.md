# P09 declared source search inspection v2

`hwpx-agent.product-source-search-request/v2` adds declared style-reference and structural-control
search to the existing authenticated mapped-source search adapter. It does not qualify effective
formatting, hidden visibility, complete SEARCH-003/004, Native behavior or the P09 Gate.

## Version and strict input

The existing v1 envelope identity, bounds, explicit mapped_document/paragraph scopes and literal/regex
operations retain their meaning. V1 still rejects new operations and any style_filter, including null.
V2 accepts `find_declared_style` with the existing nonempty text query, case_sensitive, whole_word,
max_results and a nonempty style_filter object. Its only fields are optional u32 paragraph_property,
paragraph_style, run_character_property and text_character_style. At least one must be specified.
Arrays, null filters, duplicate/unknown keys and out-of-range references are rejected before source reads.

`find_control` interprets query as one closed SourceControlKind enum, never a raw QName, XML or action.
It requires case_sensitive=true and whole_word=false and rejects style_filter. Unsupported options are
not ignored. Existing 16 KiB/request, 4096-byte/query, 10000-match and tighter trusted index bounds remain.
Raw/canonical/provider-scoped request identities bind schema version, operation and filter/kind.

V2 preparation receipts use `hwpx-agent.product-source-search-preparation/v2`. Inspection results use
`hwpx-agent.source-search-inspection/v1` and the stored inspection variant uses
`hwpx-agent.stored-source-search/v2`. Legacy text results keep their original source/scoped result shapes.
Stored query_sha256 for inspection is the complete inspection request digest, including inspection
identity, scope and filter or control kind/max_results, rather than only the text query digest.

## Declared style matching

The index reads paragraph paraPrIDRef/styleIDRef, parent run charPrIDRef and text charStyleIDRef from
the exact anchored source. Missing values remain missing; no zero/default/cascade is manufactured.
Every decoded original scalar contributing to a normalized match must satisfy all specified axes.
Canonical composition/reordering can involve several source scalars. Empty matches have no scalar
formatting and do not match a style filter. Filtering precedes accepted-result/point limits, so unrelated
style candidates cannot consume the accepted result budget. Overflow still rejects the whole response.

Numeric source references are not resolved definitions or proof of effective appearance. Receipt fields
style_definitions_resolved and effective_style_or_hidden_visibility_qualified remain false.

## Structural control matching

The closed classification maps are compared with the local pinned-model cache's runType.cpp, ctrl.cpp
and t.cpp: 28 run-site, 15 ctrl-site and 14 text-site tag placements. Shared markpen tags have separate
run/text placements. A recognized local name in a foreign namespace or wrong parent site is not a match.

Only direct items of actual mapped source paragraphs are inspected. Direct known child atoms of hp:t
may be located even when that text span remains opaque to the text reader. Unknown wrappers are not
traversed, and unmapped paragraphs are excluded. This inventory can therefore include structurally
observed tags outside searchable text without claiming whole-document interpretation.

Results bind original paragraph/control anchors, source and text-index identities, inspection inventory,
scope and request digests. These are structural occurrences, not repaired controls or qualified native
parameter/ID/semantic behavior. control_parameter_or_execution_semantics_qualified remains false.
Metadata hashing streams through a bounded writer; result serialization is independently bounded.

## Current access and verification

A private Text/Inspection enum shares current document.write/scope/head/ACL/quarantine/AEAD/whole
Form reconstruction and final consumer checks. It adds no unchecked result accessor. Verification
reauthorizes the current source but does not rerun the search or grant durable authority. No artifact
ingest, edit, revision commit, CAS, key claim, CLI/server dispatch or publication path is added.

Components048 passes nine new core cases, 30 affected core cases and 14 product cases (five v2 and
nine v1), with 449 fresh/final449, no diagnostics and terminal/empty/closed owned Jobs. Existing 39
test bodies are unchanged; unrelated 286 stored cases and the official queue are not replayed.
The 047 preflight failure preserves zero executed commands/tests and the original failed result.
The recovery separates only the newly appended blank separator before proving the original prefix hash.

Full catalog match_set/semantic_diff/reopen, style definition/cascade/visibility semantics, whole
SearchScopeSelector, navigation/replacement/conversion and Native qualification remain open.
Queue158/249, remaining91, next165, P09/A12/A13 OPEN, fixed CROSSREF eight NOT_RUN,
Native011 unapproved/unexecuted and P10 not started are unchanged.

The additive v3 definition profile is described in `p09-source-definition-style-search-v3.md`.
It resolves present source references using the original typed header catalogs and explicit source axes.
V2 retains declared-ID semantics and rejects the v3 operation/filter; implicit cascade and visibility
remain unqualified in both profiles.

The separate [review selector style core](p09-review-selector-style-core-v1.md) reuses these original point
predicates with four exact selector windows and explicit body policy. Its stored/strict JSON connection is
qualified in [the v7 product profile](p09-review-selector-style-product-v7.md). Exact control-anchor selection
is qualified separately in [the control core profile](p09-review-selector-control-core-v1.md), with current
storage/strict JSON/next in [the v8 product profile](p09-review-selector-control-product-v8.md).
V2 keeps its original paragraph-based control scope.
