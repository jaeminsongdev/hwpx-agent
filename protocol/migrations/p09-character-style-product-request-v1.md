# Character property replacement product request

`hwpx-agent.product-character-style-replacement-request/v1` prepares a private partial character-property
candidate from the current sealed stored HWPX source. It connects the qualified source compiler to
strict product JSON and current access checks. It is not a full SEARCH-008 style transaction or a
revision commit, executable dispatcher, Native operation or publication route.

## Required request and definition binding

The envelope requires schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector and operation.
The operation requires kind=replace_character_property, query, regex, case_sensitive, whole_word,
max_replacements, style_filter, replacement and review_policy. Replacement requires the closed
axis=run_character_property and a u32 declaration_id. The target must exist in the same original
typed catalog used by the source matcher, not in caller-supplied XML or a foreign source definition.

The four selectors are document, section, selection and node_set. The request retains their original
revision and shape checks and requires both hidden-explanation and MEMO-body policy Booleans.
Filters use the existing declared-reference or typed-definition predicate; an omitted reference is
not property0. Source scalar/protection/namespace/readback rules are unchanged from the
[source profile](p09-source-character-style-replacement-v1.md).

The original recursive unique JSON/object parser enforces16 KiB before source reads. Missing, unknown,
duplicate decoded keys, wrong types/axis, invalid selector shapes, source SHA, query and replacement
caps reject the request. Pattern semantics, the target definition, exact original contributions and
protection are checked against the authorized actual source. Literal/regex requests keep their old
schemas and reject this new operation; the new schema rejects legacy requests.

Raw request SHA is distinct from the canonical typed-request SHA. Provider-scoped SHA additionally
binds the current provider scope; key, plan, selector, query/options, filter, policy and target belong
to the canonical request. These fingerprints do not claim an idempotency key or authorize execution.

## Current stored source and retained candidates

prepare_character_style_candidate performs current document.write and original source checks, one
whole Form proof and one style lowering for the batch. into_character_style_candidate moves the
original owner using the same Borrowed/Owned source representation. Ownership transfer adds no clone
or reimport. The strict JSON path retains that owned source after the caller's request bytes are dropped.

The private stored receipt binds the original import, source/selector/index, exact target declaration,
filter/body policy, matches, output digest and source compiler's preservation/readback conditions.
Stored and product Debug output redact private content. Public receipt metadata is not a byte handle.

Every verify and byte delivery checks current write/scope/head/ACL/quarantine/AEAD and original source,
private receipt/candidate consistency and writer integrity. Byte delivery checks the final head inside
the integrity callback before calling the consumer. It does not repeat search or style lowering.
Revocation, foreign scope, quarantine, source corruption and final-head movement deny retained output.
require_current_product_route remains unqualified after these checks; no ingest/commit/CAS is added.

## Product qualification

Components129 passes18 new product tests with608 fresh/final608 inputs, no diagnostics or warnings and
confirmed cleanup. Original products47 and source core59 are retained from their own evidence, not
reexecuted or promoted to this new product graph. Whole-file inverse checks preserve the original
literal/regex roots and prior product tests outside the three additive module declarations.

Coverage includes four selectors, entity spelling and cross-run Hangul, declared/definition filters,
regex/case/whole-word options, four body policies and exclusion before caps, required closed schema,
decoded duplicates, exact16 KiB, old schema rejection, canonical/scoped identities, current write and
five foreign scopes, ACL revoke/regrant, quarantine/AEAD, prepare/verify/delivery final-head races,
borrowed/owned/JSON equivalence, changed source/head, cache/control/tracked/table protection,
ambiguous NFC, missing references, invalid/noop targets, match/writer/output/pattern limits,128 matches,
original field/namespace IDs and source/head/ingestion/privacy preservation.

Overall time is120.844 seconds; command42.610 seconds and libtest10.31 seconds. Owned Job CPU is40.516
seconds; peak private memory1668.69 MiB or5.2374% of physical RAM. Maximum sampled system CPU is28.12%
and minimum available RAM28.3665%. Logical CPU2/mask4, BelowNormal, hard CPU cap6.25%, private cap8%/
stop7%, RAM/commit95%, command300s and guard600s remain. The Job ends active0/empty/handle closed.
These are run observations, not a benchmark or proof of a PC-freeze fix. Other processes, OS and
Defender settings are unchanged. Evidence: implementation/p09/evidence/p09-361-style-product-components129.v1.json.

## Remaining style and phase work

The separate [text-style source profile](p09-source-text-style-replacement-v1.md) now qualifies exact
text reference edits with17 current cases and4 retained negative cases. Its separate
[stored/product binding](p09-text-style-product-request-v1.md) passes18 new cases with619 fresh/final619
inputs and confirmed cleanup; this does not widen the run-axis request. The separate
[paragraph/named source profile](p09-source-paragraph-style-replacement-v1.md) now qualifies reference
edits with38 distinct source cases. Its separate
[stored/product binding](p09-paragraph-style-product-request-v1.md) passes21 new preparation/access cases
with635 fresh/final635 inputs; it does not widen this run-axis request.
Effective formatting/cascade/visibility, full selector/
filter combinations, complete protection, target match_set/semantic_diff/reopen and dispatcher/storage/
CAS/idempotent execution/publication plus required Native evidence remain open. A changed declared
run reference alone does not prove a changed visible effective style.

Reference source API v12 remains incomplete with four unresolved stages, null report and CLI exit3.
Official acceptance stays158/249 with91 pending, next case165. Fixed CROSSREF8 is NOT_RUN; Native011
is unapproved/unexecuted. P09/A12/A13 remain OPEN, P10 is unstarted and the full P09 through P20 goal
remains ACTIVE.
