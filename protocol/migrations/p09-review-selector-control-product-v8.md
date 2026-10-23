# Review selector control product request profile

`hwpx-agent.product-source-search-request/v8` connects the exact control-anchor source scope to current
sealed storage, strict JSON and retained-result navigation. It uses the [original control core](p09-review-selector-control-core-v1.md),
without changing its source coordinate semantics or the meanings of request versions1 through7.

## Strict request

The required envelope is schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector and operation. The schema
version must be v8 and selector.revision_id must equal base_revision. Existing selector shape/native
conversion supports document, section, selection and node_set; original identities, index fingerprints
and actual source boundaries are checked against the current imported source.

Operation requires kind=find_control, query as a closed SourceControlKind, regex=false, case_sensitive=true,
whole_word=false, max_results in1..10000 and review_policy with both include_hidden_explanations and
include_memo_bodies Booleans. Options are explicit and unsupported values are rejected, not ignored.
Raw QName/action strings, regex patterns, style filters and generic include_hidden are not accepted.

The original16 KiB unique JSON/object parser rejects duplicate decoded names and unknown/missing fields,
arrays/null and malformed typed values. Envelope/selector shape/revision, kind/fixed options/policy,
head and bounded canonical request validation happen before any source read. Current source-dependent
identity and NFC projection checks then run in the original core; ambiguous NFC source boundaries fail.

Scope discovery reuses v6 scope_inventory JSON. An actual table control's returned original source handle
can be joined to the inventory's node handle without importing a caller-side Form/catalog or guessing
that the enclosing paragraph must be selected. Discovery is not a v8 operation or a control execution.

## Current storage and cursor boundary

into_review_control_search uses current document.write, provider scope/head/ACL/quarantine/AEAD, the
whole original Form reconstruction proof and one review index/control query. A private ReviewControl
variant supplies typed receipt/JSON/navigation getters to the original finish_search/fresh_json/verify
and final consumer head checks. The stored profile is stored-source-search/v8 and the preparation profile
is product-source-search-preparation/v8 with capability search.find_control. No unchecked byte accessor
or caller-supplied trusted result is added.

The receipt binds current source/index/scope/policy/kind/cap and raw/canonical/provider-scoped request
digests plus key/plan. The existing strict next/v1 parser binds its complete immutable preparation receipt.
Retained controls preserve original source order and review regions; cursor context differs for a
changed kind, selector, policy, raw request or key even when positions happen to match.

Each verify, JSON delivery and next selection reauthorizes the current source and checks the final head
before consumer invocation. Revoked access, foreign scope, quarantine, AEAD tampering and head races
deny delivery. Retained result delivery does not rerun the query/index, but complete bounded result
serialization/integrity checks remain, so the total operation is not constant time. These are not CAS,
atomic revocation after delivery, a durable key claim or permission to execute/publish.

## Verification

Components110 passes thirteen new v8 cases plus26 unchanged search and7 unchanged navigation cases,
46 total with571 fresh/final571 inputs and confirmed cleanup. The one new target shares the original
stored fixture and includes the original33 test bodies. Exact inverse checks preserve common source,
freshness/authentication, final-head, old request/parser and navigation code outside additive variants
and modules. The core59, previous v7 product45 and official249 queue cases are not replayed.

Coverage includes v6 JSON discovery for all four scopes, actual object-start membership and typed stored
equivalence, partial atoms and a zero-text source gap, all four body policies and exclusion-before-cap,
strict required/fixed options/decoded duplicates and exact16 KiB, old-schema rejection, request bindings,
write/five foreign scopes, ACL revoke/regrant, quarantine/AEAD, prepare/verify/JSON/next final-head races,
region cursor/context/wrap/exhaustion, cross-run Hangul NFC, ambiguous reordered/stale/foreign coordinates,
finite output limits, privacy, owned retained candidates and original/head/ingest preservation.

One existing unused fixture package helper warning remains. Overall177.953 seconds, command103.079 seconds,
libtest5.19 seconds and owned Job CPU36.844 seconds. Maximum sampled system CPU23.83%, minimum available
RAM36.9131%, peak Job private1644.05 MiB or5.1601% of physical RAM. The Job ends active0/empty/handle closed.
One CPU affinity1, BelowNormal, CPU cap6.25%, private cap8%/stop7%, RAM/commit95%, command300s, guard600s
and before/after input checks remain. These observations do not establish a benchmark or PC-freeze cause.
Evidence: implementation/p09/evidence/p09-361-selector-control-product-components110.v1.json.

## Remaining full contract

V2 keeps its original paragraph-based find_control scope and v5/v6/v7 do not silently accept this new
combination. Effective cascade/visibility, complete source coverage/Native flow, control parameter
semantics, whole SearchScopeSelector, regex/style/control replacement and conversions, complete protection,
match_set/semantic_diff/reopen and transaction/dispatcher/DB/CAS/execution/publication remain open.
require_current_product_route still verifies current access and returns RouteUnqualified.

Source API v12 remains incomplete with four unresolved stages, a null report and CLI exit3. Official
acceptance stays158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN; Native011 is
unapproved/unexecuted. P09/A12/A13 remain OPEN, P10 is unstarted and the full P09 through P20 goal stays ACTIVE.
