# Regex replacement product request profile

`hwpx-agent.product-regex-replacement-request/v1` prepares a current-source regex replacement candidate
through the [qualified capture core](p09-source-selector-regex-replacement-v1.md). It supports four original
selector scopes and explicit review-body policies. It is separate from literal requests1 through4 and
does not qualify zero-width insertion, a full transaction/dispatcher, Native or the complete SEARCH-007 contract.

## Strict request and current source

The required envelope is schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector and operation. Selector revision
must equal base_revision; original section/node identities and fingerprinted NFC selection use the existing
shared selector shape/native conversion. Discovery reuses the v6 scope_inventory JSON without a caller Form/catalog.

Operation requires kind=replace_regex, regex=true, query, replacement, case_sensitive, whole_word,
max_replacements in1..10000, run_policy=first_original_run_retain_all_runs and review_policy with both
include_hidden_explanations and include_memo_bodies Booleans. Empty replacement is valid deletion text.
Template syntax and text follow the source core; unknown references are not silently replaced with empty text.

The original v4 selector16 KiB unique JSON/object parser is shared, retaining decoded-name duplicate,
unknown/missing field, object/array/null, value and shape rejection. Schema/revision/head/source format,
mandatory mode/policy/options, template syntax and bounded canonical request are checked before source reads.
Actual pattern/group/coordinate semantics are checked by the one source compiler after current authorized
import. Existing literal schemas continue rejecting Regex combinations. Generic style_filter/include_hidden/
preview_only, caller graph, native flags and authorization bits are not silently accepted.

## Storage ownership and delivery

prepare_review_selector_regex_candidate reuses current document.write, scope/head/ACL/quarantine/AEAD,
fresh_source_reconstructed and its exact whole original proof for one capture compiler invocation.
The private result uses stored-selector-regex-candidate/v1 and the original LiteralSource Borrowed/Owned
enum. into_review_selector_regex_candidate moves the original owner and prepared output without cloning
or reimporting to transfer ownership. The strict product request retains that owned candidate after raw
request/selector buffers are dropped.

Every verify and byte delivery calls the existing fresh_source service and original writer integrity.
The final head check is inside the writer callback and precedes consumer invocation. Revoked/foreign access,
quarantine, AEAD tampering and prepare/verify/delivery head races deny output. Query, capture expansion,
review projection and lowering are not rerun to deliver a retained candidate. Complete source and output
integrity checks remain; this is not a durable access grant or constant-time operation.

The preparation profile is product-regex-replacement-preparation/v1 with capability search.replace_regex.
Receipts bind raw/canonical/provider-scoped requests, key/plan, current source/head, selector/policy/run/max,
output integrity and expansion work. Template SHA/bytes are distinct from ordered expansion SHA/bytes:
different templates can generate identical bytes but must retain different request/template identities.
The inner output replacement hash describes the expansion sequence, not one fixed literal replacement.
All source/work/scope/preservation flags are checked against the private candidate before current output.

No request claim, ingestion, revision write/CAS, dispatcher or publication is added. require_current_product_route
verifies current access and still returns RouteUnqualified. Receipts expose hashes/counts, not query,
template/capture values, raw XML, author metadata or a reusable credential.

## Verification

Components116 passes13 new product cases plus16 unchanged affected v4/v6 selector-product cases,29 total,
with586 fresh/final586 inputs, no diagnostics and confirmed cleanup. Exact inverse checks restore the
complete original literal roots and v4 parser outside the shared pure object helper. Core89, unrelated
suites and official249 queue cases are not replayed or promoted to current product support.

Coverage includes discovery JSON→all scopes, partial cross-run Hangul NFC and preserved controls,
numbered/named/optional/whole-match/dollar expansions and case/word options, all body policies and caps,
strict required fields/decoded duplicates/16 KiB, legacy schema separation, template-versus-expansion
bindings, write/five foreign scopes, source/head mismatch, ACL revoke/regrant, quarantine/AEAD,
prepare/verify/byte final-head races, cache/control/zero-width/noop/table protection, invalid patterns/
references, match/output/writer/work bounds and borrowed/owned/JSON output equivalence. The512-unit
empty-capture work boundary passes; the next match is rejected even with zero expanded output bytes.
Original source bytes, head and ingestion count remain unchanged.

Overall109.250 seconds, command34.140 seconds, libtest2.46 seconds and owned Job CPU32.062 seconds.
Maximum sampled system CPU29.55%, minimum available RAM35.8753%, peak Job private1651.39 MiB or5.1831%
of physical RAM. The owned Job uses logical CPU2/mask4 as one bit, BelowNormal, CPU cap6.25%, private
cap8%/stop7%, RAM/commit95%, command300s, guard600s and before/after input checks. It ends active0/empty/
handle closed. Other process settings and common guards are unchanged. These observations are not a
benchmark or proof of the full PC-freeze cause. Evidence:
implementation/p09/evidence/p09-361-regex-product-components116.v1.json.

## Remaining contract

The separate [v2 insertion source profile](p09-source-selector-regex-insertion-v2.md) qualifies exact
inverse-NFC text insertion, including control boundaries and original empty text. Its explicit policy/
candidate is connected to current storage and strict JSON in [the v2 product profile](p09-regex-insertion-product-request-v2.md).
This v1 core/product still rejects
an actual zero-width batch rather than skipping occurrences. Control/field/newline edits, effective style/visibility, full scope,
complete protection, target match_set/semantic_diff/reopen and transaction/dispatcher/DB/CAS/claim/
execution/publication plus required Native evidence remain open.

Reference source API v12 stays incomplete with four unresolved stages, null report and CLI exit3.
Official acceptance remains158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN; Native011
is unapproved/unexecuted. P09/A12/A13 stay OPEN, P10 is unstarted and the full P09 through P20 goal stays ACTIVE.
