# Text style replacement product request

`hwpx-agent.product-text-style-replacement-request/v1` prepares a private text-style candidate from
the current sealed stored source. It connects exact charStyleIDRef scalar edits to strict JSON,
current access and output integrity checks. It is not a full SEARCH-008 style transaction, revision
commit, executable dispatcher, Native operation or publication route.

## Closed request and source axis

The envelope requires schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector and operation.
The operation requires kind=replace_text_character_style, query, regex, case_sensitive, whole_word,
max_replacements, style_filter, replacement and review_policy. Replacement requires the closed
axis=text_character_style and a u32 declaration_id. The existing source typed character catalog must
resolve this target; the API does not infer named styles or effective formatting.

The original recursive unique JSON/object parser enforces16 KiB before source reads. Missing/unknown/
decoded duplicate keys, wrong types/axis, selector shape/revision, source SHA and query/max limits
reject. Four selectors and explicit hidden/MEMO policy retain their original meanings. The original
source compiler validates patterns, exact scalar contributions, target definition and protection.
The [source text profile](p09-source-text-style-replacement-v1.md) keeps run/paragraph shells and
references unchanged and uses only its explicit v9 ID profile. This request does not widen that profile.

Run-character/literal/regex/search schemas reject the text operation. The new schema rejects a run
operation even with an otherwise valid envelope; changing schema names alone cannot change axes.
Raw SHA is distinct from the full canonical typed-request SHA; provider-scoped SHA additionally binds
the current service scope. Key/plan, query/options, selector, filter/body policy and target belong to
the canonical request. Fingerprints are neither access grants nor durable idempotency claims.

## Stored ownership and current access

prepare_text_style_candidate uses current document.write, original current source/head/ACL/quarantine/
AEAD and one whole Form proof with one text-style lowering. into_text_style_candidate moves the
original Borrowed/Owned source owner. Ownership transfer adds no clone or reimport; the JSON caller's
request bytes may be dropped while the private owned candidate remains valid for fresh verification.

The private stored receipt binds original import/source/index/selector, exact target declaration,
filter/policy/matches, output SHA and the source compiler's scalar/control/two-axis preservation
conditions. Candidate Debug output redacts content; public receipt metadata is not a byte handle.

Every verify/byte delivery rechecks current write/scope/head/ACL/quarantine/AEAD, original source,
private receipt/candidate consistency and writer integrity. The final head check is inside the
integrity callback before consumer access. Retained output cannot bypass revocation, quarantine,
corruption, foreign scope or a final-head race. Search/text lowering is not repeated during delivery.
require_current_product_route remains unqualified after verification. No ingest/commit/CAS/claim,
execution or publication is added.

## Product qualification

Components138 passes18 new product cases with619 fresh/final619 inputs, no diagnostics/warnings and
confirmed cleanup. Original products65 and text-style source21 are retained under their own evidence,
not replayed or promoted to the new product graph. Exact whole-file inverses restore the prior roots
and product test bodies after removing the three additive module declarations. All other declared
source/ID/profile/render/matcher/protection/writer/fixture/product inputs match the source baseline.

Coverage includes discovery JSON/four selectors, request drop/owned output, entities/cross-run Hangul/
distinct run references, declared/definition filters, regex/case/whole-word options, four body policies
and exclusion before caps, required closed schema/decoded duplicates/exact16 KiB, reciprocal legacy
rejection, raw/canonical/scoped/key/plan/filter identities, write/five foreign scopes, ACL revoke/regrant,
quarantine/AEAD, prepare/verify/delivery final-head races, borrowed/owned/JSON equality, changed source/
head/document/project, noops/invalid target/ambiguous NFC/protection, exact Writer rejection and other
limits,128 matches with one protection map, alias/native field IDs and source/head/ingest/privacy preservation.

Overall122.125 seconds; command42.844 seconds, libtest10.66 seconds and owned Job CPU40.766 seconds.
Peak private memory1672.95 MiB or5.2508% of physical RAM. Maximum sampled system CPU63.18%; minimum
available RAM29.8710%. Whole-system samples are not owned Job readings or attribution to another
process. Logical CPU2/mask4, BelowNormal, CPU cap6.25%, private8%/stop7%, RAM/commit95%, command300s/
guard600s remain, with final active0/empty/handle closed. These are run observations, not a benchmark
or proof of a PC-freeze fix. Other processes, OS and Defender settings are unchanged.
Evidence: implementation/p09/evidence/p09-361-text-style-product-components138.v1.json.

## Remaining style and phase work

The separate [paragraph/named reference source profile](p09-source-paragraph-style-replacement-v1.md)
qualifies20 new and18 affected original cases through37 retained passes and1 repaired case. Its current
separate [stored/product binding](p09-paragraph-style-product-request-v1.md) passes21 new preparation/
access cases with635 fresh/final635 inputs; it does not widen this text-axis request. Effective cascade/visibility, full selector/filter/protection,
target match_set/semantic_diff/reopen and dispatcher/storage/CAS/idempotent execution/publication plus
required Native evidence remain open. A changed explicit reference is not proof of a visible format change.
Reference source API v12 remains incomplete/four unresolved stages/null report/CLI exit3. Acceptance
stays158/249 with91 pending, next case165; fixed CROSSREF8 NOT_RUN and Native011 unapproved/unexecuted.
P09/A12/A13 remain OPEN, P10 is unstarted and the full P09 through P20 goal remains ACTIVE.
