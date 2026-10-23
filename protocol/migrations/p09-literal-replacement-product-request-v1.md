# P09 literal replacement product request v1

`hwpx-agent.product-literal-replacement-request/v1` prepares the actual original-bound plain-text
candidate through the current authenticated provider. It binds source/head/key/plan/scope and uses
the existing literal compiler, protection, readback and fresh stored byte boundaries. It does not
commit a revision or qualify the complete SEARCH-006 capability.

## Strict input

The envelope requires schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, scope and operation.
Source SHA is lowercase64 hex, head generation is positive and the document ID bound is1024 bytes.
No caller artifact/path/Form graph/source mapping, validator verdict or approval bit is accepted.

Scope is mapped_document with an empty paragraph_handles array, or paragraphs with a nonempty,
unique array of original handles. Actual handle membership is checked against the current source
even for no matches. The existing authenticated search response can supply these handles.

Operation requires kind=replace_literal, query, replacement, case_sensitive, whole_word,
max_replacements and run_policy=first_original_run_retain_all_runs. Query is nonempty and at most
4096 bytes. Replacement may be empty for deletion. max_replacements is1..10000 and selects the
existing complete match bound: extra matches fail instead of truncating success. Other underlying
scalar-range/writer limits remain stricter where applicable.

The entire request is limited to16 KiB. Duplicate/unknown/missing keys, array envelopes/operations/
scopes, wrong types/enums and malformed identity values fail before original artifact reads. Shared
validate_literal_replacement applies exactly the original XML/plain-HWPX value policy before reads
and again at lowering. This pure validator is not source verification or an authorization receipt.
Its1 MiB semantic-value ceiling remains; the request envelope is independently smaller.

regex, style_filter, include_hidden, preview_only, native_verified, output paths and approval fields
are rejected, even when false or empty. This profile always prepares an in-memory candidate and
does not reinterpret optional flags from the full SEARCH contract as a supported execute path.
The prior search/note/form request profiles retain their original shapes and behavior.

## Source ownership and current authorization

Document.write and the existing authenticated search-provider scope gate precede source access.
Project/document must match that trusted provider; tenant/subject/project/branch/document enter
the provider-scope request binding. The provider selects only its sealed current Result at the
explicit revision/head, checks source SHA, and runs the unchanged literal candidate preparation.

The prepared source then moves into the candidate's private Owned variant rather than cloning or
performing an additional import for ownership handoff. The existing Borrowed variant remains for
the previous Rust API. Both dereference the same immutable source and share all original preparation,
fresh access, writer integrity and final-head method bodies. Mandatory initial import/reconstruction
checks are retained; ownership transfer does not remove a fresh authorization boundary.

Receipts use hwpx-agent.product-literal-replacement-preparation/v1 and capability_id=search.replace_literal.
Raw/canonical/provider-scope request digests bind all identities, key/plan/query/replacement/options/
scope. Different JSON encoding can change raw SHA without changing canonical SHA; key/plan changes
change request identity even when output is identical. The output SHA/receipt remains separately bound.
The typed request/source/candidate stay private and immutable; metadata getters do not expose bytes.

Retained verify/with_verified_bytes repeat current document.write/provider scope/source/head/ACL/
quarantine/AEAD/writer checks without rerunning the query or building the candidate again. The final
head check is inside the writer callback immediately before consumer delivery. Retained receipts,
output bytes and caller-edited receipt copies do not reauthorize access.

idempotency_key_claimed=false and full_search_native_cas_execution_publication_authority=false
remain mandatory. A client key is bound request data, not a durable reservation. There is no source
overwrite, ingest/revision commit/CAS, CLI/server dispatcher or executable/publication route; the
full-route method continues to fail after fresh verification.

## Verification and remaining work

Components070 passes nine new strict product cases and six affected Borrowed candidate cases:
15 pass,475 fresh/final475, terminal/empty/closed Jobs. The old core compiler/value policy and all
stored access methods are checked by exact inverse transformations. Previous ten core cases and
other search/patch/stored suites are preserved, not replayed as fresh product verification.

Coverage includes missing/unknown/duplicate/escaped keys and unsupported values before read audits,
the exact16 KiB boundary, the original pure value policy, key/plan/query/replacement digests, public
search handles for selected deletion, wrong head/source and all five foreign provider scopes,
ACL revoke/regrant, quarantine/AEAD and prepare/verify/final consumer head races. The existing
reusable fixture package helper warning is disclosed. The official249 queue is not run.

Full SearchScopeSelector, hidden/MEMO replacement, field/mixed-control/newline semantics, complete
protection, target match_set/semantic_diff/reopen, dispatcher/DB/CAS/execution/publication and Native
remain unqualified. Source API v12 stays incomplete/four unresolved/null report/exit3. Queue158/249,
remaining91, next165, P09/A12/A13 OPEN, fixed CROSSREF eight NOT_RUN,
Native011 unapproved/unexecuted, P10 not started and goal ACTIVE remain unchanged.

The separate [v2 source candidate and stored Rust API](p09-source-literal-text-atom-output-v2.md)
supports Text atoms around retained controls. It does not widen this v1 JSON request. The separate
[strict v2 JSON request](p09-literal-replacement-product-request-v2.md) and ownership handoff are now
qualified; v1/v2 schemas reject each other before source reads and v1 remains plain-only.
