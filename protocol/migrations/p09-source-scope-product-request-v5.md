# Authenticated source scope discovery and search v5

`StoredSourceScopeProductRequest::prepare_json` accepts
`hwpx-agent.product-source-search-request/v5`. It connects actual source selector discovery and
document/section/selection/node_set search to current sealed storage, requested revision/head,
whole source identity and the existing authorization boundary. It does not qualify review-policy
scope, replacement windows, full Native document flow or the complete SearchScopeSelector contract.

## Strict request and selector revision

The required envelope fields are schema_version, idempotency_key, project_id, document_id,
base_revision, expected_head_generation, expected_source_package_sha256, plan_id, selector and
operation. selector.revision_id is mandatory and must equal base_revision before any source read.
The provider then checks that exact current revision/head/source, not merely a caller revision label.
Raw size is16KiB; unique-key parsing rejects recursive and Unicode-equivalent duplicates. Unknown,
missing, array/null object, bad enum/type, irrelevant selector fields and approval/path flags fail.
Legacy scope is not silently translated into selector; v1-v4 and v5 requests reject one another.

Selector rules are closed for this explicit source-index range profile:

- document permits only revision_id and scope.
- section additionally requires a nonempty unique section_ids array and no range.
- node_set requires range containing only a nonempty unique node_ids array and no section_ids.
- selection requires range containing coordinate_space=index_nfc_unicode_scalars, a lowercase
 64-hex index_sha256, start and end. Each boundary contains only paragraph_handle, block_index
 and normalized_scalar. Unknown fields fail before reads; actual stale/foreign/out-of-bounds or
 reversed positions fail against the current index even for queries with zero matches.

Sets admit at most50000 IDs; query is nonempty and at most4096 bytes, max_results1..10000.
Selection semantics and finite source catalogs follow the [source selector profile](p09-source-index-scope-selector-v1.md).
The generated SearchScopeSelector contract is unchanged; actual Native/UI positions are not inferred.

## Discovery and search operations

scope_inventory has no query/options and requires document scope. It is preparatory discovery
under the existing search.find_literal/document.write boundary, not a new registered capability.
The source inventory emits the original index receipt, actual section IDs, graph node IDs with
their source handles, and paragraph-handle/block-index/NFC-length descriptors. No body, query,
style value, raw XML, native defaults or caller graph is returned. One operation-local index is
built from the existing whole Form proof; the inventory walker uses actual source anchors and
bounded depth/node count. Response/hash exhaustion rejects the complete inventory, never truncates it.

find_literal and find_regex require query, case_sensitive, whole_word and max_results. A client can
construct all four scopes directly from discovery JSON without importing Form/graph on its side.
Node descriptors relate actual node IDs to source paragraph handles; those IDs are not aliases.
Selection clips the real search windows before regex/word-boundary matching and reports global
coordinates. Document is still the admitted indexed corpus with its original unmapped counts.
Generic hidden/style options and review_policy are unsupported in v5 rather than ignored.

Raw/canonical/provider-scoped request digests bind the version, current identity, key/plan,
selector revision, IDs/range and operation. Wire ordering of ID arrays remains in request identity;
source set semantics and result digests canonicalize the selected ID set. Discovery digests bind
source/index metadata rather than pretending to be a query or access token.

## Current stored boundary

into_source_scope performs original document.write, fresh source/whole Form proof and one index
construction, then uses the original finish_search/fresh_json/verify/final consumer-head methods.
A private result variant contains discovery or source selector results plus a derived legacy scope
summary. Its stored profile is v5 and result JSON retains the full inventory/selector information.
Removing that variant/accessor arms reconstructs the old service exactly. The old product parser
and v1-v4 navigation bodies remain unchanged outside additive module/variant dispatch.

Every retained delivery rechecks provider scope, ACL, quarantine/AEAD, source and final head without
rebuilding the inventory or query. Receipt copies are not authority. V5 Find cursor navigation is qualified
in [the selector navigation profile](p09-selector-result-navigation-v1.md); Inventory remains denied.
Existing v1-v4 cursor
behavior is separately regressed. No unchecked accessor, source overwrite, ingest, durable key
claim, revision commit/CAS, CLI/server dispatcher, execution or publication is added; route denial remains.

## Verification

Components092 passes4 new inventory core,10 new v5 product and33 affected existing search/navigation
cases:47 total,522 fresh/final522, cleanup true. Discovery JSON drives all four scope requests,
including two real sections with equal local paragraph IDs, graph/source handle distinction and
anchored regex selection. Tests cover bounded/non-disclosing metadata, source-bound discovery SHA,
strict request/boundary fields and duplicate keys, exact16KiB, selector revision mismatch, key/plan
digests, current write scope/five foreign provider scopes, ACL revoke/regrant, quarantine/AEAD,
prepare/verify/final-consumer head races for both discovery/search, bad selection/set inputs,
selected-before-match caps, output limits, original head/ingest preservation and legacy separation.

The prior50 source cases are retained by code/test equality and the exact additive inverse; they
are not rerun. Existing26 search and7 navigation test bodies are unchanged in a focused target.
Core diagnostics are empty. Product compilation retains the known unused fixture package helper
warning; no warning-free workspace claim is made. Official249 queue and Hancom/COM are not run.

Overall158.266 seconds, inventory command57.735/test0.03 and product command33.093/test4.28.
Maximum system CPU70.10%, minimum available RAM26.7706%, peak Job private5.0981% of physical RAM.
Both Jobs end active0/empty/handle closed. One core, BelowNormal, CPU cap6.25%, private cap8%/stop7%,
RAM/commit95%, command300s, guard600s and before/after inputs remain. The whole-system CPU sample
does not attribute the load to a process or prove that PC freezes are fixed.
Evidence: implementation/p09/evidence/p09-361-source-scope-product-components092.v1.json.

## Remaining work

Explicit review-policy and literal-replacement reuse of exact selection windows is qualified at core
and stored-service level in the separate [review selector profile](p09-stored-review-selector-candidates-v1.md).
Separate strict search v6/literal v4 JSON is qualified in [the product profile](p09-review-selector-product-requests.md).
This v5 schema still rejects review policy and preserves its original meaning.
Style/control filtering, full text/visibility and
Native flow, match_set/semantic_diff/reopen, dispatcher/DB/CAS/execution/publication remain open.
Source API v12 is incomplete/four unresolved/null report/exit3. Queue158/249,91 remaining,
next165, fixed CROSSREF8 NOT_RUN, Native011 unapproved/unexecuted, P09/A12/A13 OPEN, P10 not started
and the full P09–P20 goal ACTIVE remain unchanged.
