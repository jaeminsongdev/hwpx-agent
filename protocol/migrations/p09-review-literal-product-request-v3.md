# Explicit review body literal replacement product request v3

`StoredReviewLiteralProductRequest::prepare_json` binds explicit hidden explanation and MEMO
body policy to an owned source candidate under `hwpx-agent.product-literal-replacement-request/v3`.
The `hwpx-agent.product-literal-replacement-preparation/v3` receipt is preparation evidence,
not a durable execution claim or revision commit.

## Request and version boundaries

The envelope retains required schema_version, idempotency_key, plan_id, project_id, document_id,
base_revision, expected_head_generation, expected_source_package_sha256, scope and operation.
Scope is mapped_document with no handles or paragraphs with a nonempty unique set of original
handles. Operation retains replace_literal, query, replacement, case_sensitive, whole_word,
max_replacements and first_original_run_retain_all_runs. V3 requires this additional operation field:

```json
"review_policy": {
  "include_hidden_explanations": true,
  "include_memo_bodies": true
}
```

Both Booleans are mandatory and independently select actual source-file body regions. False is
not inferred application visibility. Missing, null, array, non-Boolean, unknown or duplicate policy
fields fail. Top-level policy, generic include_hidden, style/regex/control-edit options, raw source,
graph/path and caller approval or qualification flags remain unsupported rather than ignored.

The original private strict parser is split into object/unique-key and typed value validation.
Rejoining those bodies and removing the new module yields the previous v1/v2 source. V3 removes
only its named policy from the validated operation object, then uses the same typed identity,
scope/query/value/limit checks. Recursive Unicode-equivalent duplicates fail before extraction.
Raw request16KiB, query4096 bytes and maximum replacements10000 remain enforced without truncation.

Existing v1/v2 reject review_policy and v3 schema before source reads. V3 rejects v1/v2 schemas
and missing policy. Existing v1 plain-only and v2 mixed-TextSpan semantics, canonical/scoped hashes
and current access methods retain their original bodies outside the private parser extraction.

## Source ownership and current access

The provider requires document.write and original project/document/provider scope, imports the
sealed current Result and checks the requested whole source SHA. Existing v3 borrowed preparation
performs fresh whole Form reconstruction, actual body policy, cache/protection and writer checks.
The private into_review_literal_candidate adapter moves output/receipt and boxes the source in
the existing Borrowed/Owned enum. It adds no source clone or ownership-driven reimport; required
initial import and fresh reconstruction still occur.

Original current ACL/quarantine/AEAD, source and final head checks are unchanged. Retained delivery
rechecks current access/source without repeating query, lowering or review projection. The final
consumer head check remains inside the writer callback. Revocation, foreign provider scope,
source/head drift, quarantine and authentication failure prevent byte delivery.

Raw SHA distinguishes original formatting. Canonical SHA uses the bounded typed envelope with
policy restored inside operation, serialized through the JSON object map. Scoped SHA binds v3
schema, provider scope and canonical SHA. Policy/key/plan, query/options, selection, replacement
and source stay request-bound. Only the small request value is reconstructed for canonical checks;
package/output are not duplicated. Candidate Debug is redacted and receipts omit query/value/key text.

The receipt checks both nested v3 profiles, original source/head, replacement digest/length,
run policy/count, exact body policy and immutable candidate receipt. Cached-field writes, control
edits, complete protection, native author/visibility/resolution and execution flags remain closed.
No unchecked accessor, ingest, overwrite, durable key claim, revision commit/CAS, CLI/server
dispatcher, executable route or publication is added. require_current_product_route denies.

## Verification

Components088 passes10 new v3 product cases plus19 affected v1/v2 product and6 original v3 borrowed
cases:35 passes,508 fresh/final508, no diagnostics/skips/failures and cleanup true. Its focused
target imports the existing shared StoredFixture and three existing test modules without changing
their bodies. Core32, unrelated stored suites and the official249 queue are not replayed.

Tests cover all four policies and exact bytes, retained ownership after request drop, original
source/head/ingest preservation, strict fields/types/duplicates and exact16KiB boundary, request/
provider/policy/key/plan/options/value digests, authenticated review-search handles selecting hidden
and MEMO paragraphs, excluded-match caps, document.write and five foreign scopes, ACL revoke/regrant,
quarantine/AEAD, preparation/verify/final-consumer head races, cache/control/no-op and output bounds,
malformed review and precise FieldContent rejection for a valid enclosing field, and all versions.

Overall101.984 seconds, command36.234 and test10.10. Maximum system CPU46.88%, minimum available
RAM28.9834%, peak Job private2.1868% of physical RAM. The Job ends active0/empty/handle closed.
One core, BelowNormal, CPU cap6.25%, private cap8%/stop7%, RAM/commit95%, command300s, guard600s
and before/after input checks remain. These are run observations, not a benchmark or PC-freeze repair.
Evidence: implementation/p09/evidence/p09-361-review-literal-product-components088.v1.json.

## Remaining work

The [source selector core](p09-source-index-scope-selector-v1.md) qualifies four typed scope forms;
current stored/revision/JSON and replacement-window connection remain pending. The generated
contract names document/section/selection/node_set, with revision_id, section_ids and range;
the current partial profile is not silently renamed to that full selector. Effective style/
visibility, field/newline and regex/style/control replacement, complete protection, target
match_set/semantic_diff/reopen, dispatcher/DB/CAS/execution/publication and Native remain.
Source API v12 is incomplete/four unresolved/null report/exit3. Queue158/249,91 remaining,
next165, fixed CROSSREF8 NOT_RUN, Native011 unapproved/unexecuted, P09/A12/A13 OPEN, P10 not started
and the full P09–P20 goal ACTIVE remain unchanged.
