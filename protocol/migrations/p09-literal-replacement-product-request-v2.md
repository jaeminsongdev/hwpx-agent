# Mixed text literal replacement product request

## Request contract

StoredLiteralTextAtomProductRequest::prepare_json binds an actual v2 source literal candidate to
hwpx-agent.product-literal-replacement-request/v2. This explicit schema admits text around retained
tab/lineBreak controls; it does not admit editing those controls. Existing v1 remains plain-only.

The required envelope fields are schema_version, idempotency_key, project_id, document_id,
base_revision, expected_head_generation, expected_source_package_sha256, plan_id, scope and operation.
Scope is mapped_document with an empty paragraph_handles list or paragraphs with a nonempty unique
list of source handles. Operation requires kind=replace_literal, query, replacement, case_sensitive,
whole_word, max_replacements and run_policy=first_original_run_retain_all_runs. Empty replacement
means deletion; empty query is invalid. All fields are required, not inferred from the environment.

The original strict Request parser is shared through a private schema parameter. The two public
entry points supply closed v1/v2 constants and reject each other's schemas before artifact reads.
16 KiB, recursive duplicate keys including escaped spellings, unknown/missing keys, non-object
envelopes/scope/operations, invalid enums/types and the original identity/digest/scope/query/value
bounds remain. The original plain-text replacement policy rejects controls/noncharacters.
Regex, style/hidden/control-policy fields, approval/verification bits and output paths are rejected,
not ignored even when false. No v2 policy flag silently overrides field or protection rejection.

The original scoped-hash body is shared with an explicit schema parameter. V1 continues to supply
its original constant, preserving its canonical/provider-scope identity and plain-only semantics.
V2 binds its own schema, raw/canonical request hashes, provider scope and all key/plan/source/query/
scope/replacement/options/run-policy values. Different whitespace can change raw hash without
changing canonical identity. A different key or plan changes request identity, not execution authority.

## Source ownership and current access

The provider's document.write/product-scope gate and sealed current Result import bind the explicit
head and source SHA. The v2 stored candidate reuses the existing private Borrowed/Owned source enum.
into_literal_text_atom_candidate calls the existing preparation once, moves its output/receipt and
boxes the original source. It neither clones the source nor adds an import for ownership handoff.
Required initial import and fresh source/Form reconstruction are retained; the whole JSON call is
not described as only one original import.

The existing v2 preparation/current-source/ACL/quarantine/AEAD/writer-integrity/final-head method
bodies are unchanged outside the source wrapper. Verify and byte delivery retain fresh access and
source checks without rerunning the query or lowering. The final head check remains inside the
writer callback immediately before the consumer. Product checks bind the v2 receipt/profile,
control preservation and unqualified control editing to the private original request/candidate.
Receipt copies or saved keys do not grant access; there is no caller-defined trusted-output trait.

Preparation receipts use hwpx-agent.product-literal-replacement-preparation/v2 and
capability_id=search.replace_literal. idempotency_key_claimed and
full_search_native_cas_execution_publication_authority remain false. require_current_product_route
still denies after fresh verification. No CLI/server dispatcher, ingest, source overwrite, revision
commit/CAS, durable key claim, execution or publication route is added.

## Verification

Components079 passes ten new v2 product and fifteen affected cases: nine original v1 product and
six existing v2 borrowed-service cases. All25 pass,492 fresh/final492, cleanup confirmed. The original
v1 strict parser/scoped hash and product access bodies are exact-inverse checked outside helper
extraction; existing v2 access/writer/final-head bodies are inverse checked outside source wrapping.
The ownership handoff body matches the qualified v1 move/box pattern. Existing test bodies and
core/scalar/readers/other providers stay exact; core/patch and unrelated stored tests are not replayed.

Coverage includes actual mixed cross-run/control bytes, authenticated search handles for selected
deletion, strict JSON and exact16 KiB boundary, key/plan/raw/canonical/options/value bindings,
all five foreign provider scopes, ACL revoke/regrant, quarantine/AEAD, preparation/verify/final
consumer head races, match/response/writer/field/control/no-op limits, schema cross-rejection and
unchanged plain-only v1 behavior. The original search_review_fixture package helper warning remains.
The official249 queue, Hancom/COM and Native are not executed.

Overall215.344 seconds, new product command140.359/test13.24 and affected command10.797/test10.07.
Maximum system CPU33.16%, minimum available RAM27.2722%, peak Job private3.0762% of physical RAM.
Both Jobs end active0/empty/handle closed. One core, BelowNormal, CPU cap6.25%, private cap8%/stop7%,
RAM/commit95% and before/after input checks remain. These observations do not establish a benchmark
or a fix for PC freezes.

## Remaining work

Explicit hidden/MEMO source candidates and borrowed storage are qualified in
[the v3 source profile](p09-source-review-literal-output-v3.md). Its
[strict v3 product JSON and owned handoff](p09-review-literal-product-request-v3.md) are qualified
separately, without broadening existing v1/v2 field-cache or control guards.
Full SearchScopeSelector, field/newline replacement, complete protection, target match_set/
semantic_diff/reopen, dispatcher/DB/CAS/execution/publication and Native remain unqualified.
Source API v12 remains incomplete/four unresolved/null report/exit3. Queue158/249,91 remaining,
next165, fixed CROSSREF8 NOT_RUN, Native011 unapproved/unexecuted, P09/A12/A13 OPEN, P10 not started
and the full P09–P20 goal ACTIVE remain unchanged.
