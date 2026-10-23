# P09 Selector Result Navigation

Retained v5 and v6 Find preparations now support forward/backward selection, explicit wrap and reversal
after exhaustion over document, section, selection and node set results. The operation preserves exact
source windows and review policy/region annotations without rerunning the query or rebuilding an index.
It selects source occurrences, not a live Hangul caret or Native page/layout position.

## Product entry and cursor binding

PreparedStoredSourceScopeProduct and PreparedStoredReviewScopeProduct expose navigation_receipt_sha256
and with_next_verified_json. Both accept the existing
hwpx-agent.product-source-search-next-request/v1 shape described in the original navigation profile.
No new query, raw graph/source, output path or approval flag is accepted. Strict16 KiB, decoded duplicate
keys, unknown fields, types, direction/wrap and cursor-shape checks remain the original parser's body.

The product receipt context binds original source/document/revision/head, raw/canonical/provider-scope
request hashes, key/plan, selector and explicit policy. The core cursor also binds the full immutable result,
ordinal and selected-occurrence fingerprint. Another scope, policy, profile, query option, raw encoding,
key/plan or provider context cannot reuse a cursor. These unsigned coordinates are not access credentials,
durable idempotency claims, write permission or execution receipts.

Inventory is not a Find result. Its receipt getter rejects Request, and even a manually assembled valid
next envelope is rejected before artifact access. The stored variant separately rejects Cursor for Inventory.
Find navigation keeps source and selected global scalar coordinates, NFC source pieces and review regions.
Missing/null cursor starts at the first or last retained occurrence. An exhausted non-wrapping result keeps
its prior cursor for reversal; wrap is explicit. Empty results have no cursor, and zero-width matches move
by ordinal without manufacturing editable pieces.

## Current authorization and cost

New source-result methods are thin wrappers over the original navigation engine. Scope/ReviewScope Find
dispatch is added to stored navigation; original v1-v4 dispatch is unchanged. Product helpers reuse the
unchanged next parser and compute the immutable receipt context once per new continuation call.
The v5/v6 preparation/verification/parsing bodies, legacy next methods, navigation engine and original
stored fresh_json/result checks and final-consumer-head body reconstruct exactly after removing additions.

Each call still checks current document.write, provider scope/head/ACL/quarantine/AEAD, fresh original
source and retained-result integrity. Full-result validation bytes are dropped before constructing the
selected response, and final head is checked before the consumer. Query/index creation is not repeated,
but bounded full-result serialization and identity hashing remain. Overall navigation is not constant-time;
only selection/cloning of one occurrence follows identity validation. No full-vector clone is added.

All existing source/response bounds and authority-false flags remain. There is no original overwrite,
ingest, commit/CAS, dispatcher, durable key claim or execution/publication grant, and the full-product
route remains denied. Generated contracts and all preparation request schemas are unchanged.

## Verification and resource observations

Components101 passes6 new core plus10 original core navigation cases, and10 new product plus7 original
product navigation cases:33 total,548 fresh/final548 and cleanup true. Tests cover four scopes in v5/v6,
original selections/regions, both directions/wrap/exhaustion/reversal, partial regex and zero-width/empty
results, NFC pieces, context/profile/policy/scope/request drift, cursor tampering, strict/exact16 KiB,
write/five foreign provider scopes, ACL revoke/regrant, quarantine/AEAD, final-head races, Inventory denial
before reads and source/head/ingest preservation. Original navigation test bodies are unchanged.
The prior52 core,61 stored,36 product and official249 queue cases are not replayed.

Core diagnostics are empty; product compilation retains the existing unused fixture package helper warning.
Overall139.547 seconds. Core command38.343/test0.25 seconds; product command30.266/test2.66 seconds.
Maximum sampled system CPU25.19%, minimum available RAM37.1637%, peak Job private5.1099% of physical RAM.
Both Jobs end active0/empty/handle closed. One CPU affinity1, BelowNormal, CPU cap6.25%, private cap8%/stop7%,
RAM/commit95%, command300s, guard600s and before/after input checks remain unchanged. These are observations,
not a performance benchmark, process attribution or proof that PC freezes are fixed. Evidence:
implementation/p09/evidence/p09-361-selector-navigation-components101.v1.json.

## Remaining contract

Selector/style combinations and core cursor binding are qualified in [their core profile](p09-review-selector-style-core-v1.md).
Their stored/strict JSON/cursor binding is qualified in [the v7 product profile](p09-review-selector-style-product-v7.md).
Exact control-coordinate projection and region-bound core cursor are qualified in
[the control core profile](p09-review-selector-control-core-v1.md); current storage/strict JSON/next is qualified in
[the v8 product profile](p09-review-selector-control-product-v8.md).
Effective visibility/style, complete source
coverage/Native flow, full SearchScopeSelector and SEARCH-005, actual app selection/page movement,
match_set/semantic_diff/reopen, complete protection, transaction/dispatcher/DB/CAS/execution/publication and
Native/Gate evidence remain open.

Source API v12 stays incomplete with four unresolved stages, null report and CLI exit3. Official acceptance
is158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN; Native011 is unapproved/unexecuted.
P09/A12/A13 remain OPEN, P10 is unstarted and the full P09 through P20 goal stays ACTIVE.
