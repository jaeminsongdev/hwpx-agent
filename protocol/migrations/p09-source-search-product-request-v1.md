# P09 source search product request v1

`hwpx-agent.product-source-search-request/v1` connects explicitly scoped mapped-source search
to the authenticated sealed current stored Result. It is a separate additive Rust request profile,
not a replacement for the full SEARCH-001/002 operation schema or a new CLI/server route.

## Request and scope

The envelope requires schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, scope and operation.
Source SHA is lowercase hex of exactly 64 bytes, generation is positive, document ID is bounded.
The whole request is at most 16 KiB. Duplicate keys, including escaped aliases, unknown fields,
non-object envelope/operation/scope, missing fields and trailing values are rejected before source reads.

Scope is an object with kind and paragraph_handles. `mapped_document` requires an empty handle list;
`paragraphs` requires a nonempty unique list. Only handles of actual indexed source paragraphs are
accepted, even if the query yields zero matches. No filesystem path, caller graph, artifact selector,
validator outcome or approval bit is accepted. Handle selections are source/graph/index-bound.

Operation requires kind (`find_literal` or `find_regex`), query, case_sensitive, whole_word and
max_results. Query is 1 through 4096 UTF-8 bytes and max_results is 1 through 10000; caller-trusted
index limits can be tighter, and exhaustion is an error, never silent truncation. This profile does
not accept include_hidden, style_filter or a separate regex flag. It does not silently ignore
unqualified options from the broader catalog schema.

`find_scoped` returns `hwpx-agent.scoped-source-text-search/v1`, including the partial original index,
selected paragraph/block counts, scope digest and ordinary source matches. Scope digest includes
the index identity and canonical handle set. Selecting all mapped content is distinct from explicitly
selecting the same paragraphs. Match block indices remain global to the index. Whole-document
visibility remains unqualified and the wrapper counts toward the existing result byte ceiling.

## Current service access and result delivery

The authenticated provider requires document.write, as specified by the search catalog, before
reading source content. Project and document must match its trusted scope. The unchanged sealed
head/node/descriptor/tenant/ACL/quarantine/AEAD/digest chain selects the source; the request cannot
provide a substitute archive. Preparation binds raw/canonical/provider-scoped request digests,
including tenant/subject/project/branch/document, key/plan, operation and requested scope.

The existing fresh whole Form reconstruction is reused within that operation. Its pointer-bound
proof builds the search index from the exact original instead of repeating ZIP/XML/Form import.
Proofs, receipts and source hashes are not service access grants. Foreign original models are rejected.

Stored results are immutable and private. verify and with_verified_json recheck current write scope,
original read/source/head checks, result/source/scope/query receipt bindings and response integrity.
They do not rerun the query or rebuild the search index. A final head read precedes the consumer.
There is no unchecked match or result-byte getter. These reads do not claim an atomic CAS or revoke
data already delivered under earlier valid authorization.

No artifact ingest, document edit, revision commit, durable idempotency claim, issuer, execution,
publication or Native path is added. require_current_product_route still denies the full route after
fresh verification. The existing source-assessment v12 and other product schemas stay unchanged.

## Verification

`p09-361-scoped-search-product-components045.v1.json` passes six new scope cases, 24 affected search
cases and nine new authenticated product cases, with 444 fresh/final444, no diagnostics and confirmed
terminal/empty/closed owned Jobs. All 24 prior test bodies are unchanged. Unrelated 286 stored cases
and the official queue are not replayed. Cases include literal/regex and paragraph scopes, exact request
size, strict parsing, foreign/stale identities, five provider-scope substitutions, write-scope denial,
ACL revoke/regrant, quarantine, AEAD tamper, resource/pattern limits and final consumer head races.

Full SearchScopeSelector, native visibility/effective styles and page order, style/control search,
navigation, replacements/conversions and catalog match_set/semantic_diff/reopen remain unqualified.
Queue 158/249, remaining91, next165, P09/A12/A13 OPEN, fixed CROSSREF eight NOT_RUN,
Native011 unapproved/unexecuted and P10 not started are unchanged.

The additive v2 profile in `p09-source-search-inspection-v2.md` supplies declared style-reference and
structural tag searches through the same current-access boundary. V1 continues to reject those new
operations/options, and the v2 source observations do not qualify complete style/control semantics.
