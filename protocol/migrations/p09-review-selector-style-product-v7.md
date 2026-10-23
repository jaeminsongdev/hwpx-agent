# P09 Authenticated Review Selector Style Search v7

StoredSelectorStyleProductRequest::prepare_json connects the qualified review-aware style core to the
provider's current sealed Result through hwpx-agent.product-source-search-request/v7. Both declared
source-reference and typed-definition predicates support four source scopes, explicit body policy,
literal/regex queries and retained cursor navigation. This is a bounded preparation/result path, not
effective-style resolution, Native behavior or a dispatcher/commit qualification.

The [detail definition extension](p09-detail-definition-product-v1.md) also binds24 character and27 paragraph
predicates through the same four scopes, explicit axes, review policy and retained cursor. It adds no Native
precedence/default rule and keeps the original current-access boundaries.

## Strict request and discovery

The envelope requires schema_version, idempotency_key, plan_id, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, selector and operation. The original shared
Scope shape/native validator applies to document/section/selection/node_set. selector.revision_id must
equal base_revision before any source read; current revision/head, provider scope and source SHA then
bind the actual sealed source. Original index-fingerprint/NFC endpoints and actual node IDs remain required.

Operation kind is find_style. Required fields are query, regex, case_sensitive, whole_word, max_results,
style_filter and review_policy. regex is an explicit Boolean; it selects the original literal or regex
matcher without changing style or scope meaning. Capability remains search.find_style.

style_filter is an object containing kind=declared or kind=definition and a filter object with the
corresponding original typed fields. Declared axes are nonempty explicit p/run/t references. Definition
requires used character/paragraph source axes for its values. Both body-policy Booleans are mandatory.
No default effective style, implicit cascade, missing-reference zero or named-style fallback is inferred.

This request has no discovery operation. Use the existing v6 scope_inventory JSON to obtain real section
IDs, node/source-handle pairs and paragraph/block/NFC/index coordinates without a client Form/graph/catalog
import. Node IDs are not source-handle aliases. A raw path, supplied graph/proof, approval or Native verdict
is not admitted. Old v1-v6 requests reject the new operation/combination rather than silently ignoring fields.

The original16 KiB unique JSON/object parser rejects decoded duplicate keys, trailing data and non-object
envelopes/selector/operation. Typed parsing rejects missing/unknown fields, null/array filters or policy,
wrong types/kinds and invalid/unused style axes before source reads. Query4096-byte, matches1-10000,
unique-ID, scope/index and complete response bounds remain. Requests are canonical-size checked as well.
Scope, policy and predicate exclusions happen before match caps; regex sees the clipped window and
every NFC source contributor must pass the selected style predicate. Zero-width matches are not style matches.

## Current stored source and cursor

into_review_style_search checks current document.write, provider scope/head/ACL/quarantine/AEAD and one
whole original Form proof. A single review index performs the query and, only for Definition, builds its
typed lookup once for the operation. Private ReviewStyle adds stored-source-search/v7 while sharing the
original finish_search, fresh_json, verify and final-consumer-head bodies.

PreparedStoredSelectorStyleProduct returns product-source-search-preparation/v7. Raw, canonical and
provider-scoped request hashes bind original key/plan, scope/revision/source, query/options, policy and
style filter to the immutable stored result. The original v5 parser and v1-v6 service/product meanings
reconstruct exactly after removing the added module/private result arms.

navigation_receipt_sha256 and with_next_verified_json use the unchanged next/v1 parser and original
receipt-context helper. Core navigation binds the whole style result, preserving original global positions
and region labels. Verify, JSON delivery and next recheck current access/source/result integrity and final
head. They do not repeat query/index/definition lookup, but bounded whole-result serialization/hashing
remains; total continuation is not claimed constant-time.

Receipts/cursors are not authority or durable idempotency claims. require_current_product_route remains
denied. No unchecked result getter, source overwrite, ingest, revision commit/CAS, dispatcher or execution/
publication grant is added. Metadata is preserved, not sanitized by this read-only search.

## Verification and resource observations

Components105 passes12 new product and33 unchanged affected cases:26 legacy search plus7 legacy navigation,
45 total with559 fresh/final559 and cleanup true. Real discovery JSON builds both filter families over
all four scopes without a caller import. Tests cover partial regex/zero-width, four policies and caps,
strict fields/shapes/axes/duplicates, exact16 KiB, raw/canonical/key/plan/filter/policy digests, v1-v6 separation,
write/five foreign scopes and expected source/head, ACL revoke/regrant, quarantine/AEAD, both families'
prepare/verify/output/next final-head races, cursor context/regions, missing axes, excluded dangling refs,
invalid headers, limits, private receipts and source/head/ingest preservation.

The new style specimen's body is exactly the qualified core specimen, with an additional unstyled package
case proving missing references do not become zero. Core35, other completed suites and official249 cases
are not replayed. The existing unused fixture package helper warning remains; no warning-free workspace
claim is made. Existing legacy test bodies and all core production code are unchanged.

Overall112.203 seconds, command40.344 seconds, test body10.71 seconds, owned Job CPU38.250 seconds.
Maximum sampled system CPU18.01%, minimum available RAM33.8018%, peak Job private5.1125% of physical RAM.
The Job ends active0/empty/handle closed. One CPU affinity1, BelowNormal, CPU cap6.25%, private cap8%/stop7%,
RAM/commit95%, command300s, guard600s and before/after input checks remain. These observations are not a
benchmark, process attribution or PC-freeze resolution. Evidence:
implementation/p09/evidence/p09-361-selector-style-product-components105.v1.json.

## Remaining contract

The separate [v9 resolved-style product](p09-resolved-style-product-v9.md) adds assessed direct-source
predicates with explicit unresolved-axis errors and current stored/next checks. It does not broaden
this v7 schema or infer Native cascade/visibility.

Exact control_anchor position and selection-boundary projection are qualified separately in
[the control core profile](p09-review-selector-control-core-v1.md), with its current storage/strict JSON/next
connection in [the v8 product profile](p09-review-selector-control-product-v8.md).
Paragraph membership alone must not widen control selection. Effective cascade/visibility, full source coverage/Native flow, complete
SearchScopeSelector, regex/style/control replacement, conversion, complete protection, match_set/semantic_diff/
reopen, transaction/dispatcher/DB/CAS/execution/publication and Native/Gate evidence remain open.

This search schema is separate from the reference source API v12, which stays incomplete with four unresolved
stages, null report and CLI exit3. Official acceptance is158/249 with91 pending, next case165. Fixed CROSSREF8
is NOT_RUN; Native011 is unapproved/unexecuted. P09/A12/A13 stay OPEN, P10 is unstarted and the full P09
through P20 goal stays ACTIVE.
