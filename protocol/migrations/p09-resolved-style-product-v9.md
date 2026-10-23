# Resolved source formatting product search

`hwpx-agent.product-source-search-request/v9` connects the
[selected direct-formatting resolution core](p09-source-resolved-formatting-v1.md) to current stored
source access and retained-result navigation. It is not complete SEARCH-003 effective formatting,
Native cascade/visibility, general execution or a revision transaction.

## Required request

The closed envelope requires schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector and operation. Operation
requires kind=find_resolved_style, query, regex, case_sensitive, whole_word, max_results, style_filter
and review_policy. None of the mode/filter/policy fields has an inferred default.

The nonempty filter supports bold, italic, height_hwpunit, text_rgb and alignment through the source
resolution contract. It does not accept caller-selected declared/definition axes, approval flags or
Native visibility claims. False is a property predicate. A required selected source axis that cannot
be resolved returns the original typed Resolution/Unresolved error, even for an absent query; no
successful empty candidate is substituted. Unrequested axes and excluded regions keep their source
contract meanings. Missing references and text-style precedence are not guessed.

The optional [character-detail extension](p09-character-detail-search-v1.md) is carried by the same strict
request, current source check and retained cursor. It is absent from legacy canonical serialization when
unused; new predicates are bound into the request and result identity. No new execution route is granted.

The optional [paragraph-detail extension](p09-paragraph-detail-search-v1.md) adds27 predicates on the same typed
paragraph declaration. Layout measurements retain explicit units; current/fallback layout and direct/meta_tag
heading declarations remain distinct. It requires the selected direct paragraph axis before searching,
preserves legacy canonical bytes when absent and keeps all current-source and cursor bindings below.

The [control-context correction](p09-control-style-context-v1.md) also rejects required character axes
under admitted hidden-control style contexts. Original styled-MEMO Import/Body rejection is retained;
it is not relabelled as a successful or source-resolved candidate. The v9 request/receipt shapes and
all current access/final-head boundaries remain unchanged.

The original recursive unique JSON/object parser enforces16 KiB before source reads. Missing,
unknown, decoded-duplicate and wrong-shaped fields reject. Original four-selector shape/revision,
positive head generation, lowercase source SHA, query1 through4096 bytes and max_results1 through10000
remain required. The old v1 through v8 schemas reject the new operation, and v9 rejects their operations.

Raw bytes, the full canonical typed request and provider-scoped canonical identity have distinct
digests. Key/plan, query options, filter, policy, selector, expected source and head remain bound.
These identities are not a claimed durable idempotency key or authority to read retained data.

## Current source and result verification

One fresh whole Form proof creates one review scope/index and resolution search. A private v9 result
variant shares the original finish_search, fresh_json, verify and with_verified_json methods. The
source owner moves into the existing prepared result; no clone/reimport is added for ownership.

The original document.write/scope/head/ACL/quarantine/AEAD source checks, result SHA, index/graph/scope
bindings, authority flags and final head before consumer access remain. Retained-result delivery
does not repeat query or resolution. Wrong scope, changed head/source, access revocation, quarantine
or ciphertext tampering deny old results and new preparation. The stored profile is
hwpx-agent.stored-source-search/v9, and product preparation uses
hwpx-agent.product-source-search-preparation/v9 with capability search.find_style.

## Retained navigation

The original strict next parser accepts hwpx-agent.product-source-search-next-request/v1 and binds
the immutable full product receipt as context. Direction/wrap/cursor stay explicit. The existing
source navigation handles forward/backward, exhaustion and wrap; it does not run a fresh search.
Every continuation still performs the original fresh source/access/result check and a final head
check before JSON disclosure. Receipt hashes and cursors are not access credentials.

Different key/plan/request receipts cannot reuse a continuation context; changing the outer receipt
hash does not rebind a foreign result cursor. Full result and selected navigation responses obey
their original byte bounds. There is no unchecked result accessor, ingest, CAS, durable key claim,
general dispatcher, Native execution or publication route.

## Qualification and original preservation

Components150 passes20 new product cases with639 fresh/final639 inputs, no diagnostics/warnings and
confirmed cleanup. Original products104 and resolution source18 remain under their own evidence;
they are not replayed or promoted to one combined current run. Removing the added private result
variant/arms, typed error and module declarations restores the complete original stored v1-v8,
navigation, selector-parser and prior product test bodies. All other declared source/fixture/guard/
writer/product inputs match the preceding source baseline.

Coverage includes four discovered scopes and owned request drop, combined/false direct values,
typed unresolved errors even with absent query, required-axis/outside-scope separation, four review
policies and exclusion before caps, closed schemas/decoded duplicates/exact16 KiB/reciprocal legacy
rejection, raw/canonical/scoped/key/plan/filter/policy identities, current write and five foreign
scopes, ACL revoke/regrant/quarantine/AEAD, prepare/verify/JSON/next final-head races, direct-stored/
product receipt and byte equality, forward/backward/exhaustion/wrap, strict next and receipt/cursor
binding, wrong source/head/document/project/index, exact output and query/match/pattern limits,
entities/cross-run NFC/all contributors,128 segments/matches, privacy and original/head/ingest/closed
route preservation, empty selections and zero-width results.

Overall121.843 seconds; command39.422 seconds, libtest6.42 seconds and owned Job CPU37.875 seconds.
Peak private memory1694.85 MiB or5.3195% of physical RAM. Maximum sampled system CPU41.02%; minimum
available RAM23.9416%. Whole-system samples are not process attribution. Logical CPU2/mask4,
BelowNormal, CPU cap6.25%, private8%/stop7%, RAM/commit95%, command300s/guard600s remain, with final
active0/empty/handle closed. These observations are not a benchmark or proof of a PC-freeze fix.
Other processes, OS and Defender settings are unchanged.

Evidence: implementation/p09/evidence/p09-361-resolved-style-product-components150.v1.json.

## Remaining style and phase work

Next is authoritative text-style precedence/missing-axis/Native visibility binding and complete
selector/filter contracts. This assessed direct-source request does not substitute for full effective
cascade, complete protection, match_set/semantic_diff/reopen, dispatcher/storage/CAS/idempotent
execution/publication or required Native evidence. The separate reference source API v12 stays
incomplete/four unresolved stages/null report/CLI exit3. Acceptance stays158/249 with91 pending, next
case165; fixed CROSSREF8 NOT_RUN and Native011 unapproved/unexecuted. P09/A12/A13 remain OPEN, P10 is
unstarted and the full P09 through P20 goal remains ACTIVE.
