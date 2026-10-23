# Regex insertion product request profile

`hwpx-agent.product-regex-replacement-request/v2` connects the
[explicit source insertion policy](p09-source-selector-regex-insertion-v2.md) to the current sealed
source, four selectors and hidden/MEMO body policies. It prepares a private regex replacement candidate
that supports exact zero-width text insertions. Existing v1 regex and literal requests retain their
contracts. Candidate preparation is not the complete SEARCH-007 transaction or a Native qualification.

## Strict request and canonical identity

The envelope and existing regex operation fields are the same as
[the v1 regex request](p09-regex-replacement-product-request-v1.md). V2 additionally requires
operation.insertion_policy=`right_original_point_else_left_first_empty_text`. This closed policy has
no default; missing/null/object/array/Boolean/unknown values are rejected before source reads.

The original16 KiB unique JSON/object parser runs before extracting the required policy. The original
typed request validator then checks the remaining envelope/operation against schema v2. The extracted
policy is retained in the private request and included in canonical and provider-scoped identities;
it is not silently dropped. Canonical hashing covers `(v2 schema, policy, complete typed request)` and
scoped hashing covers `(v2 schema, provider scope, canonical hash)`. The raw request has its own digest.
Every canonical representation remains bounded by the original request limit.

Required mode, template syntax, values, selector shape/revision and head/source formats are checked
before source reads. Regex group/pattern and actual source coordinates use the one original compiler
after authorized import. Empty query remains invalid; `(?:)` is valid regex syntax for empty matches.
Generic visibility/style/native/approval/preview options are not accepted or ignored. Decoded-name
duplicates are rejected before policy extraction. V1 keeps its fixed schema and rejects the v2 policy.

## Current source ownership and delivery

prepare_review_selector_regex_insertion_candidate reuses current document.write, scope/head/ACL/
quarantine/AEAD and fresh_source_reconstructed for one whole Form proof and capture compiler call.
The stored profile is stored-selector-regex-candidate/v2. Borrowed and Owned use the original
LiteralSource enum. into_review_selector_regex_insertion_candidate transfers the original owner and
prepared output without an ownership-transfer clone or reimport.

Original regex source receipt validation is shared between v1 and v2 with explicit expected profiles.
It retains source/index/scope, expansion/work/count, preservation and denied-authority checks. Whole
file inverse checks restore the original v1 storage body outside that extraction and module declaration.
The v2 wrapper also checks the insertion policy, exact-cut/text-only/empty-text flags, original boundary
digest through private candidate equality and zero-width count against total matches.

Every retained verify or byte delivery rechecks current source/access and original writer integrity.
The final head check remains inside the writer callback before consumer invocation. Revoked/foreign
access, quarantine, AEAD tampering and prepare/verify/delivery head races deny output. Delivery does
not rerun search, capture expansion, NFC projection or lowering. Receipts do not authorize later access.

The preparation profile is product-regex-replacement-preparation/v2 with capability search.replace_regex.
It binds the complete typed request, policy, key/plan, provider scope, expected current source/head,
selector/body/run policies, match cap, template versus expansion identities and the private stored result.
The exact source insertions retain original runs/styles and control bytes. Field caches, controls as
replacement text, observed protection and ambiguous/unowned insertion points retain source rejection.

Idempotency claim, ingestion, revision write/CAS, dispatcher and publication are not added.
require_current_product_route verifies current access and returns RouteUnqualified. Receipt/Debug contain
hashes/counts, not private keys, source/replacement/capture text or raw XML.

## Product verification

Components123 reached the32 KiB diagnostic-output ceiling and was stopped with confirmed owned cleanup;
test completion was unconfirmed. Its result is preserved. The new child module preceded the original
macro definitions. Recovery124 moves only that declaration after the definitions and uses short compiler
diagnostics. Production, new test bodies and fixtures are unchanged from123, and output/resource limits
are not raised. The original v1 product/storage files and13 test bodies are restored by exact inverse checks.

Recovery124 passes18 new insertion products and29 affected original regex/selector products:47 total,
598 fresh/final598 inputs, no diagnostics and confirmed cleanup. Source v2 core and unrelated suites,
including the official249-case queue, are not replayed or promoted to this product graph.

Coverage includes discovery-to-four-selectors and clipped empty selections; right-run style and cross-run
Hangul NFC; original control boundaries and empty paired/self-closing text; ambiguous/decomposed cuts and
absent owners; review policy exclusion before caps; strict required fields/policy/decoded duplicates and
legacy rejection; exact16 KiB; raw/canonical/scoped/key/plan/version identities; write/five foreign scopes;
source/head mismatch; ACL revoke/regrant, quarantine, AEAD and all three final-head races; borrowed/owned/
JSON equivalence; boundary-versus-scope and template-versus-expansion identities; cache/control/noop/
protection/match/writer/output/work rejection;256 controls and source/head/ingestion/privacy preservation.

Overall85.266 seconds, command8.484 seconds, libtest3.79 seconds and owned Job CPU7.312 seconds.
Peak owned Job private memory is691.26 MiB or2.1696% of physical RAM. Maximum sampled system CPU is75.2%
and minimum available RAM38.2103%. The75.2% value is a whole-system sample, not an owned Job reading or an
attribution to a specific external process. It does not establish a PC-freeze cause or its resolution.

The owned Job readback proves logical CPU2/mask4, one bit, BelowNormal, hard CPU cap6.25%, private cap8%/
stop7%, RAM/commit95%, command300s and guard600s. It ends active0/empty/handle closed. Common guards,
other processes, OS and Defender settings are unchanged. Evidence under implementation/p09/evidence:

- p09-361-regex-insertion-product-components123.v1.json
- p09-361-regex-insertion-product-recovery124.v1.json

## Remaining product contract

The separate [partial character-property replacement source profile](p09-source-character-style-replacement-v1.md)
now qualifies exact selected scalar edits for the character axis of SEARCH-008. Its
[current stored and strict product binding](p09-character-style-product-request-v1.md) passes18 new
product tests with608 fresh/final608 inputs and confirmed cleanup; other style axes and the full SEARCH-008 contract remain open.
Effective style/visibility and complete SearchScopeSelector/filter combinations, control/cache/newline
edits, complete protection, target match_set/semantic_diff/reopen and transaction/dispatcher/storage/CAS/
idempotent execution/publication plus required Native evidence remain open.

Reference source API v12 stays incomplete with four unresolved stages, null report and CLI exit3.
Official acceptance remains158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN;
Native011 is unapproved/unexecuted. P09/A12/A13 stay OPEN, P10 is unstarted and the full P09 through
P20 goal remains ACTIVE.
