# Paragraph style replacement product preparation

`hwpx-agent.product-paragraph-style-replacement-request/v1` prepares a candidate from the current
sealed source, not a full SEARCH-008 implementation, effective formatting operation or revision commit.
It connects the separate [paragraph reference source profile](p09-source-paragraph-style-replacement-v1.md)
to current stored access and a strict JSON request for the two explicit paragraph axes.

## Required request and reference meaning

The envelope requires schema_version, idempotency_key, project_id, document_id, base_revision,
expected_head_generation, expected_source_package_sha256, plan_id, selector and operation. The operation
requires kind=replace_paragraph_style_reference, query, regex, case_sensitive, whole_word,
max_replacements, style_filter, replacement, extent and review_policy. No defaults manufacture a missing
axis, extent, query mode or review decision.

The replacement is a closed tagged value with axis=paragraph_property or axis=paragraph_style and an
unsigned declaration_id. The existing source typed catalog validates the original target; named styles
require exactly PARA, not CHAR or an unknown type. The required extent is
whole_matched_paragraph_within_scope. A partial query may select a whole paragraph under that policy,
but a clipped selector cannot widen to cover an unselected paragraph region.

Changing paraPrIDRef or styleIDRef preserves the other paragraph axis and every run/text reference.
It does not copy the named style's direct properties, establish inheritance from nextStyle or prove a
visible effective-style change. Missing references are introduced only on the selected paragraph axis.

## Strict parsing and request identity

The original recursive unique JSON/object parser enforces16 KiB before source reads. It rejects
missing, unknown, decoded-duplicate and wrong-shaped fields, including replacement and extent.
Selector shape/revision, positive head generation, lowercase source SHA, nonempty bounded query,
Boolean regex and case/word options, replacement count1 through10000 and a valid declared/definition
filter remain required. Source pattern, target, scope and protection checks follow current admission.

Raw bytes have a separate SHA; canonical identity covers the full typed request, including key/plan,
target/extent/filter/policy and query options. Scoped identity also binds the provider scope. Old
literal/regex/run/text/search schemas reject this operation, and this schema rejects their operations.
Prepared identities are not claimed durable idempotency keys.

## Current source and output boundary

The provider requires current document.write and the original scope/head/ACL/quarantine/AEAD checks.
One fresh source reconstruction supplies the original Form proof to one paragraph compiler. Borrowed
preparation moves into the existing owned source boundary. Ownership transfer adds no clone or reimport.

Receipt sanity binds source/output review imports, source/index SHA, target and changed references,
explicit extent, counts and preservation flags. Every verify or byte delivery independently rechecks
current access/source and writer integrity; a retained receipt never authorizes later disclosure.
The final head check is inside the integrity callback before consumer access. Search/paragraph lowering
is not repeated. Changed head, access revocation, quarantine, altered ciphertext or a foreign provider
scope deny retained output.

The preparation profile is hwpx-agent.product-paragraph-style-replacement-preparation/v1 and its
capability is search.replace_style. No candidate is ingested, no DB/revision CAS or durable key claim
is performed, and the general execution/publication route remains explicitly unqualified.

## Product qualification and failures

Components144 stopped before Cargo because the runner expected20 identities while the unchanged test
file contains21. Count recovery145 corrects only six runner count/label sites, then fails compilation
with E0433 at the independent test reader's unavailable quick_xml reference; no product test starts.
Both immutable failures and their exact inputs are preserved.

Compile recovery146 leaves product/source code, Cargo dependencies and all other inputs unchanged.
Only the independent test reader changes: it decodes decimal/hex numeric XML references without a new
dependency and checks numeric, nonnumeric and invalid-scalar cases. Whole-file inverse checks restore
the previous21 test bodies apart from that oracle repair and its own assertions.

Recovery146 passes21 new product cases with635 fresh/final635 inputs, no diagnostics/warnings and
confirmed cleanup. Original products83 and paragraph source38 are retained under their separate
evidence, not replayed or promoted to a single current combined run. Removing the three additive
module declarations restores the complete original roots and prior product test bodies.

Coverage includes both axes, four discovered selectors and dropped request ownership, clipped-scope
rejection, entities/cross-run Hangul/run/text references, declared/definition filters, regex/case/word,
four review policies with exclusion before caps, closed schemas/decoded duplicates/exact16 KiB,
reciprocal legacy rejection, raw/canonical/scoped/key/plan/filter/axis identities, current write and
five foreign scopes, ACL revoke/regrant, quarantine/AEAD, prepare/verify/delivery final-head races,
borrowed/owned/JSON equality, wrong source/head/document/project, invalid targets/noops/missing axes,
unqueried field/locked-descendant/tracking protection, match/output/pattern/exact Writer limits,
ambiguous NFC,128 matches/128 paragraphs with shared protection, aliases/native field IDs and
source/head/ingest/privacy preservation.

Overall103.156 seconds; command21.078 seconds, libtest13.91 seconds and owned Job CPU18.922 seconds.
Peak private memory749.05 MiB or2.3510% of physical RAM. Maximum sampled system CPU56.44%; minimum
available RAM24.3988%. Whole-system samples are not attribution to the Job or another process.
Logical CPU2/mask4, BelowNormal, CPU cap6.25%, private8%/stop7%, RAM/commit95%, command300s/guard600s
remain, with final active0/empty/handle closed. These are observations, not a benchmark or proof of
a PC-freeze fix. Other processes, OS and Defender settings are unchanged.

Evidence under implementation/p09/evidence:

- p09-361-paragraph-style-product-components144.v1.json
- p09-361-paragraph-style-product-count-recovery145.v1.json
- p09-361-paragraph-style-product-compile-recovery146.v1.json

## Remaining style and phase work

The separate [direct-formatting resolution core](p09-source-resolved-formatting-v1.md) now qualifies18
cases for required-axis coverage and selected-source predicates; current stored/product binding for
that query is still pending. Effective cascade/visibility and full selector/filter contracts remain
open. Complete protection,
target match_set/semantic_diff/reopen, dispatcher/storage/CAS/idempotent execution/publication and
required Native evidence remain open. Reference source API v12 stays incomplete/four unresolved
stages/null report/CLI exit3. Acceptance stays158/249 with91 pending, next case165; fixed CROSSREF8
NOT_RUN and Native011 unapproved/unexecuted. P09/A12/A13 remain OPEN, P10 is unstarted and the full
P09 through P20 goal remains ACTIVE.
