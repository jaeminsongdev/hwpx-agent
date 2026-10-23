# P09 Review Selector Search and Literal Candidates

Actual hidden explanation and MEMO source bodies now support document, section, selection and node set
windows under an explicit body policy. Source scope search and literal output are connected to the current
sealed stored document. This profile qualifies core and stored APIs. Separate strict search v6 and literal
v4 requests are qualified in [the product profile](p09-review-selector-product-requests.md); legacy request
schema meanings are unchanged.

## Source identities and windows

SourceReviewScopeIndex imports review bodies with the original field admission and derives supplemental
node IDs from their actual graph/source anchors. Inventory returns original section IDs, actual node IDs
and source handles, paragraph/global-block/NFC lengths, index fingerprint and region labels, not body or
author text. Source handles are not aliases for graph node IDs. Aggregate catalog/depth/output limits apply.

The selector resolves against the whole admitted index before the explicit include_hidden_explanations
and include_memo_bodies policy excludes regions. A valid excluded review node is a zero-result scope,
not an unknown ID. Scope receipts describe the selected windows; searched blocks and excluded paragraphs
describe the policy-filtered search. Policy binds the request hash and cannot silently widen a selector.

Selection remains index-fingerprint plus original paragraph/global-block/NFC scalar endpoints. Regex and
word boundaries see the clipped window before matching; reported coordinates retain the global and original
source positions. No paragraph/control/opaque barriers are concatenated. Native flow/visibility stays false.

## Literal output and current stored access

lower_review_selector_literal_candidate uses one original Form proof, one field collector and one review
projection for the operation. The original review writer receives only matches inside the resolved windows.
NFC source contribution/contiguity, field cache and enclosing-field protection, control preservation and
byte readback remain the qualified v3 compiler's responsibility. The new outer profile is
hwpx-agent.source-selector-literal-replacement-candidate/v1; its body_candidate retains the original v3
receipt. The outer selector scope/index hashes must agree with the body output receipt.

into_review_source_scope uses Inventory or Find with a typed selector and explicit policy. Its private
ReviewScope result uses hwpx-agent.stored-source-search/v6 and the original finish_search, fresh_json,
verify and final-consumer-head bodies. The inventory hash covers its entire bounded serialized response.
Retained delivery does not rebuild the inventory, index or query. Legacy v1 through v5 profiles keep their
existing meanings. A v6 stored profile is not a product-source-search-request/v6 schema.

prepare_review_selector_literal_candidate returns a borrowed source candidate.
into_review_selector_literal_candidate moves that already prepared output/receipt and the source owner
into the original private Borrowed/Owned storage enum. There is no source clone or ownership-transfer
reimport. The new stored profile is hwpx-agent.stored-selector-literal-candidate/v1. Current write, provider
scope, head, ACL, quarantine, AEAD and complete source proof apply at preparation. Verify and delivery
freshly recheck current access/source and original writer integrity, with the final head check inside the
writer callback before consumer access. They do not repeat query, lowering or review import.

No unchecked match/output accessor, ingest, original overwrite, revision commit/CAS, durable idempotency
claim, dispatcher or execution/publication grant is added. require_current_product_route remains denied.
Metadata and cached field results are preserved; these candidates are not privacy sanitizers.

## Verification and resource observations

Core recovery096 passes16 new plus36 affected cases:52 total,532 fresh/final532 and cleanup true.
The original094 system-CPU stop during build has no proven test completion count;095 has a new-test
u32/usize assertion compile failure. Both records remain unchanged. The recovery changes only that assertion
with a checked conversion. Bundling six existing test modules into one binary retains all52 original cases
without filters or relaxed guards. This reduces the requested binary count, not a measured CPU-cause fix.

Stored components097 passes12 new plus49 affected cases:61 total,536 fresh/final536 and cleanup true.
Coverage includes discovery JSON driving all four scopes without caller Form import, second-occurrence-only
byte-exact replacement in each of three regions, all four body policies, excluded-before-caps, valid excluded
nodes, owned transfer, stale/foreign/reversed/out-of-range selection, write/five foreign provider scopes,
ACL revoke/regrant, quarantine/AEAD, discovery/search/literal prepare/verify/final-head races, field caches,
enclosing fields, control/noop/value/output caps, source/head/ingest preservation and redacted receipts.
The49 legacy case bodies are unchanged; the52 completed core cases and official249 queue are not rerun.
Compilation retains the preexisting unused fixture package helper warning.

| Observation | Core recovery | Stored connection |
|---|---|---|
| Overall seconds | 90.062 | 269.953 |
| Cargo command seconds | 20.219 | 196.813 |
| Test body seconds | 9.39 | 25.18 |
| Maximum sampled system CPU percent | 26.92 | 26.70 |
| Minimum available RAM percent | 36.8802 | 35.6382 |
| Peak owned Job private percent of physical RAM | 1.7867 | 5.1055 |

Both Jobs end active0, empty and handle closed. One CPU, BelowNormal, CPU cap6.25%, private cap8%/stop7%,
RAM/commit95%, command300s, guard600s and before/after input checks remain. Whole-system samples are not
process attribution, a benchmark or proof that PC freezes are fixed. Evidence:

- implementation/p09/evidence/p09-361-review-selector-recovery096.v1.json
- implementation/p09/evidence/p09-361-stored-review-selector-components097.v1.json

## Remaining product boundary

Strict review-selector search and selector-literal product JSON bind selector revision, current source/head,
policy and the immutable output through the separate product profile without widening the old schemas.
Find cursor navigation is qualified in [the navigation profile](p09-selector-result-navigation-v1.md);
Inventory remains denied. [Review selector style combinations](p09-review-selector-style-core-v1.md) have a
separate [v7 stored/strict JSON/cursor qualification](p09-review-selector-style-product-v7.md).
Exact control-coordinate projection, effective visibility, full source coverage and Native flow,
full SearchScopeSelector, match_set/semantic_diff/reopen, complete protection, transaction/dispatcher/
DB/CAS/execution/publication and Native/Gate evidence remain open.

Source API v12 stays incomplete with four unresolved stages, null report and CLI exit3. Official acceptance
is158/249 with91 pending and next case165. Fixed CROSSREF8 is NOT_RUN; Native011 is unapproved/unexecuted.
P09/A12/A13 stay OPEN, P10 is unstarted and the full P09 through P20 goal remains ACTIVE.
