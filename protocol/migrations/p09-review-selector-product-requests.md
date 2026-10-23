# P09 Strict Review Selector Product Requests

Review-aware source scope discovery/search and selector-window literal candidates now accept strict
product JSON over the provider's current sealed Result. Search uses
hwpx-agent.product-source-search-request/v6; literal replacement uses
hwpx-agent.product-literal-replacement-request/v4. These are candidate/preparation APIs, not an executable
dispatcher or a stored revision commit. Existing search v1 through v5 and literal v1 through v3 keep their
meanings and reject the new fields/schemas rather than ignoring them.

## Envelope and selector

Both requests require schema_version, idempotency_key, plan_id, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, selector and operation. Selector revision_id
must equal base_revision before any source read. Current head, original source SHA and provider scope
then bind the actual sealed source. SHA strings are64 lowercase hexadecimal characters.

Selector uses the existing document/section/selection/node_set shape and finite validation. Document
has no section_ids or range. Section requires a nonempty unique section_ids array and no range. Node set
requires range.node_ids, a nonempty unique array of actual graph IDs. Selection requires
range.coordinate_space=index_nfc_unicode_scalars, index_sha256 and start/end boundaries, each containing
paragraph_handle, block_index and normalized_scalar. The revision and index fingerprint are not interchangeable.

Search discovery returns the review inventory and actual supplemental node/source-handle identities with
region labels, not author/body text. Clients build subsequent requests using this JSON without importing
Form/graph separately. Convert the returned32-byte index fingerprint to lowercase hexadecimal for selection.
Source handles are not graph node IDs. Stale/foreign/reversed/out-of-range selections and partial original
NFC-contribution cuts remain rejected. Regex sees the clipped window; scalar positions remain global.

## Operations and policy

| Request | Operation | Required fields and policy |
|---|---|---|
| Search v6 | scope_inventory | Document selector only; no query, options or review_policy |
| Search v6 | find_literal or find_regex | query, case_sensitive, whole_word, max_results and review_policy |
| Literal v4 | replace_literal | query, replacement, case_sensitive, whole_word, max_replacements, run_policy and review_policy |

review_policy must be an object with both Boolean fields include_hidden_explanations and include_memo_bodies,
and no unknown keys. Search policy is not inferred from the scope or an old include_hidden option.
An excluded actual review node is valid but returns zero matches; literal output rejects NoMatches.
Selected-out and policy-excluded content is removed before match caps. Exceeding admitted match/output
limits is an error, not a truncated successful batch. Partial selections never expand into whole paragraphs.

Literal run_policy is first_original_run_retain_all_runs. Only ReplaceLiteral is admitted; regex/template,
style/control/newline editing and allow_protected/cache flags remain unsupported. The original shared
literal replacement value policy rejects control and forbidden Unicode values. An empty replacement
is deletion; a no-change batch remains rejected.

Requests are bounded at16 KiB, queries at4096 bytes and matches at1 through10000. Existing50k unique-ID
and core source/scope/regex/result/writer bounds remain. Empty requests and over-limit raw requests fail.
Duplicate decoded keys including escaped names, trailing data, missing/unknown fields, arrays/null instead
of objects, wrong types and malformed ranges are rejected before source reads. A legacy scope field is
not accepted in place of selector. Paths, supplied graph/proof or approval/native verdicts are not accepted.

## Shared parsing and immutable output

The v5 object/value parser stages and Scope shape/native conversion are extracted for internal reuse.
Removing that extraction reconstructs the entire prior v5 file exactly, including validation, canonical
digests and authorization bodies. Literal v4 uses the original literal Operation/Kind/run-policy and value
validator, plus the shared selector. The v1/v2/v3 parser file changes only by adding a module declaration.
Generated feature contracts are unchanged.

Raw request SHA binds wire bytes. Canonical SHA binds the typed request including policy, selector, key,
plan and operation; provider-scoped SHA also binds tenant/subject/project/branch/document context. ID-array
wire order remains request identity while core set/scope and result hashes canonicalize semantic sets.
Key/plan changes do not manufacture another source mutation or authorize access.

Prepared search uses product-source-search-preparation/v6 with stored-source-search/v6. Prepared literal
uses product-literal-replacement-preparation/v4 with stored-selector-literal-candidate/v1. Its outer selector
receipt retains the qualified v3 body receipt; they are not mislabeled legacy product outputs. Scope/index,
policy, source, replacement and output receipt checks remain bound to the immutable retained request.

Both products share the qualified current stored access/source/head and whole Form proof. Literal output
and source ownership move without cloning or an ownership-transfer reimport. Verify/delivery recheck
write/scope/ACL/quarantine/AEAD/source/writer integrity and final consumer head, not inventory/query/lowering
or review projection. require_current_product_route remains denied. No unchecked byte accessor, durable
idempotency claim, ingest, original overwrite, revision commit/CAS or execution/publication grant is added.

## Verification and resource observations

Components099 passes16 new combined product cases plus10 unchanged v5 scope and10 unchanged v3 literal
cases:36 total,542 fresh/final542, diagnostics empty and cleanup true. Actual discovery JSON builds all four
search and literal scope shapes. Tests verify second-match-only byte-exact replacement in three regions,
regex clipping before caps, all four policies, excluded-node zero/NoMatches, strict fields/types/duplicates,
exact16 KiB, raw/canonical/key/plan/value hashes, provider write and five foreign scopes, source/head binding,
ACL revoke/regrant, quarantine/AEAD, discovery/search/literal prepare/verify/final-head races, invalid selections,
response/writer limits, cache/outer-field/control/noop rejection, legacy separation and overlapping sets.
Source/head/ingest are preserved. Core52, stored61 and the official249 queue are not replayed.

Overall311.547 seconds; Cargo command239.813 seconds; test body6.50 seconds; cumulative owned Job CPU12.531
seconds. Maximum sampled system CPU26.43%, minimum available RAM39.8378%, peak Job private2.2072% of
physical RAM. The Job ends active0/empty/handle closed. One CPU affinity1, BelowNormal, CPU cap6.25%,
private cap8%/stop7%, RAM/commit95%, command300s, guard600s and before/after inputs remain unchanged.
The observer waits up to0.5 seconds per capture check; elapsed build time and Job CPU time differ.
Post-run core-load samples cannot establish the earlier scheduling/I/O/Defender cause. No CPU-cause fix,
benchmark or PC-freeze resolution is claimed. Evidence:
implementation/p09/evidence/p09-361-review-selector-product-components099.v1.json.

## Remaining contract

The strict v4 selector object parser is shared with the separate
[regex candidate product profile](p09-regex-replacement-product-request-v1.md). Its29 product/affected
passes qualify current source and exact output delivery, not Regex support inside the v4 literal schema.
The original v4 parser/body is preserved by exact inverse checks and16 affected current product cases.

Selector-result cursor navigation is qualified in [the navigation profile](p09-selector-result-navigation-v1.md)
for v5/v6 Find without changing this request schema. Style combinations reuse
[the core](p09-review-selector-style-core-v1.md) through a separate
[v7 stored/strict JSON/cursor path](p09-review-selector-style-product-v7.md). Exact control-coordinate
projection/current storage/next are qualified in [the v8 control profile](p09-review-selector-control-product-v8.md). Full effective
visibility/style, full source coverage/Native flow, complete SearchScopeSelector, regex/style/control
replacement, conversion operations, complete protection, match_set/semantic_diff/reopen and transaction/
dispatcher/DB/CAS/execution/publication and Native/Gate evidence remain open.

Source API v12 stays incomplete with four unresolved stages, null report and CLI exit3. Official acceptance
is158/249,91 pending, next case165. Fixed CROSSREF8 is NOT_RUN; Native011 is unapproved/unexecuted.
P09/A12/A13 stay OPEN, P10 is unstarted and the full P09 through P20 goal remains ACTIVE.
